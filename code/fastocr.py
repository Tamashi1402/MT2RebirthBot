"""FastDigits — template-match OCR for fixed-position HUD numbers.

Replaces the tesseract subprocess (~100-300ms per read) with numpy glyph
matching (~1ms) once per-glyph templates have been harvested.

How it works
------------
1. SLOW PATH (identical to the old code): tesseract reads the region —
   one subprocess, nothing extra. If the raw string is clean (matches
   `clean_pattern`), its characters are mapped one-to-one onto the image's
   glyph segments (icons dropped by size) and each bitmap becomes a
   candidate. A candidate only becomes a template when a DIFFERENT read
   produces the same character with a near-identical bitmap
   (double confirmation — a one-off tesseract misread can never poison
   the cache) and the resulting templates reproduce the confirmed value
   on the source image (self-verification).
2. FAST PATH: the preprocessed binary image is segmented into glyphs by
   column-ink profile; each glyph is matched against stored templates
   (strict size gate + XOR-distance). If every glyph-sized segment matches
   and the assembled string is clean, the value returns in ~0.1ms. Large
   unmatched segments (icons, decorations) are skipped, not failed.
3. Any doubt — unknown glyph, no template yet, ambiguous match, dirty
   string — returns None and the caller falls back to tesseract. The fast
   path can only ever be a shortcut, never a source of wrong values.

Templates persist in data/fastocr/<name>_screen<WxH>.npz — ONE FILE PER
runtime resolution/ratio (default ship: Full HD 1920x1080). Regions are
runtime-scaled, so glyphs render at different pixel sizes per resolution;
each resolution harvests (and caches) its own file. A resolution change
just starts a fresh file — the old one stays on disk for next time.
"""

import os
import re
import threading

import numpy as np
import pytesseract

try:
    from logger import get_logger
    log = get_logger(__name__)
except Exception:  # pragma: no cover - standalone import safety
    import logging
    log = logging.getLogger("fastocr")


class FastDigits:
    """One instance per on-screen number region (e.g. stone, surge)."""

    def __init__(self, name: str, whitelist: str, clean_pattern: str,
                 res_key: tuple, match_tol: float = 0.15):
        self.name = name
        self.whitelist = whitelist
        self.clean_re = re.compile(clean_pattern)  # matched with .fullmatch()
        self.res_key = (int(res_key[0]), int(res_key[1]))
        self.match_tol = float(match_tol)
        self.lock = threading.Lock()
        self.templates: dict[str, list[np.ndarray]] = {}
        self._pending: dict[str, tuple] = {}   # char -> (bitmap, harvest_seq)
        self._harvest_seq = 0
        self.stats = {"fast": 0, "slow": 0}
        self._first_fast_logged = False
        self._root = os.path.dirname(os.path.abspath(__file__))
        # v2023: per-resolution caches live in data/fastocr/ as
        # <name>_screen<WxH>.npz (public bot — every resolution/ratio gets
        # its own file; Full HD is the shipped default).
        self._dir = os.path.join(self._root, "..", "data", "fastocr")
        self._res_tag = f"{self.res_key[0]}x{self.res_key[1]}"
        self._path = os.path.join(self._dir, f"{name}_screen{self._res_tag}.npz")
        # Legacy pre-v2023 cache (data/fastdigits_<name>.npz) — migrated
        # automatically to the new per-resolution file when its resolution
        # still matches the runtime one.
        self._legacy_path = os.path.join(self._root, "..", "data", f"fastdigits_{name}.npz")
        self._load()

    # ── persistence ────────────────────────────────────────────
    def _load(self):
        for path in (self._path, self._legacy_path):
            try:
                if not os.path.isfile(path):
                    continue
                data = np.load(path, allow_pickle=False)
                meta = str(data["meta"]) if "meta" in data.files else ""
                if meta != self._res_tag:
                    log.debug(f"[FASTOCR:{self.name}] cache {os.path.basename(path)} "
                             f"was harvested at {meta} (now {self._res_tag}) — rebuilding")
                    continue
                for key in data.files:
                    if key == "meta":
                        continue
                    # key format: "<ord(char)>__<variant>"
                    try:
                        o, _v = key.split("__", 1)
                        ch = chr(int(o))
                    except Exception:
                        continue
                    self.templates.setdefault(ch, []).append(data[key].astype(bool))
                n = sum(len(v) for v in self.templates.values())
                log.debug(f"[FASTOCR:{self.name}] loaded {n} glyph templates "
                         f"({len(self.templates)} chars) from {os.path.basename(path)}")
                if path == self._legacy_path and self.templates:
                    # migrate legacy cache to the new per-resolution file
                    self._save()
                    try:
                        os.remove(path)
                        log.info(f"[FASTOCR:{self.name}] migrated legacy cache to "
                                 f"data/fastocr/{self.name}_screen{self._res_tag}.npz")
                    except Exception:
                        pass
                return
            except Exception as e:
                log.debug(f"[FASTOCR:{self.name}] cache load failed ({path}): {e}")
                self.templates = {}

    def _save(self):
        try:
            os.makedirs(self._dir, exist_ok=True)
            payload = {"meta": np.array(self._res_tag)}
            for ch, variants in self.templates.items():
                for i, arr in enumerate(variants):
                    payload[f"{ord(ch)}__{i}"] = arr
            np.savez_compressed(self._path, **payload)
        except Exception as e:
            log.debug(f"[FASTOCR:{self.name}] cache save failed: {e}")

    # ── segmentation ───────────────────────────────────────────
    @staticmethod
    def _segments(proc: np.ndarray) -> list:
        """Split the binary image into tight glyph segments.

        Returns list of (x0, x1, y0, y1, bool_array), left to right.
        """
        ink = proc > 0
        if not ink.any():
            return []
        col_ink = ink.any(axis=0)
        segs = []
        W = col_ink.shape[0]
        x = 0
        while x < W:
            if col_ink[x]:
                x0 = x
                while x < W and col_ink[x]:
                    x += 1
                sub = ink[:, x0:x]
                rows = np.where(sub.any(axis=1))[0]
                y0, y1 = int(rows[0]), int(rows[-1]) + 1
                segs.append((x0, x, y0, y1, sub[y0:y1, :]))
            else:
                x += 1
        return segs

    # ── matching ────────────────────────────────────────────────
    @staticmethod
    def _xor_dist(g1: np.ndarray, g2: np.ndarray) -> float:
        """Padded XOR distance between two glyph bitmaps (0 = identical)."""
        H = max(g1.shape[0], g2.shape[0])
        W = max(g1.shape[1], g2.shape[1])
        a = np.zeros((H, W), dtype=bool); a[:g1.shape[0], :g1.shape[1]] = g1
        b = np.zeros((H, W), dtype=bool); b[:g2.shape[0], :g2.shape[1]] = g2
        union = int(np.count_nonzero(a | b))
        if union == 0:
            return 0.0
        return float(np.count_nonzero(a != b)) / union

    def _match_one(self, glyph: np.ndarray) -> tuple[str, float] | None:
        """Best template match for a single glyph, or None."""
        best = None
        best_d = 1e9
        h, w = glyph.shape
        for ch, variants in self.templates.items():
            for tmpl in variants:
                th, tw = tmpl.shape
                if abs(int(tw) - w) > 1 or abs(int(th) - h) > 1:
                    continue
                # Sizes may differ by 1px (subpixel rendering) — pad both
                # to the union shape (top-left anchored) before comparing.
                H = max(h, th)
                W = max(w, tw)
                g = np.zeros((H, W), dtype=bool)
                g[:h, :w] = glyph
                t = np.zeros((H, W), dtype=bool)
                t[:th, :tw] = tmpl
                union = int(np.count_nonzero(g | t))
                if union == 0:
                    continue
                d = float(np.count_nonzero(g != t)) / union
                if d < best_d:
                    best_d = d
                    best = ch
        if best is not None and best_d <= self.match_tol:
            return best, best_d
        return None

    def _widest_template_w(self) -> int:
        w = 0
        for variants in self.templates.values():
            for tmpl in variants:
                w = max(w, int(tmpl.shape[1]))
        return w

    def _read_segment(self, seg: tuple) -> tuple[str, float] | None:
        """Match one segment; split wide merged glyphs if needed."""
        x0, x1, y0, y1, glyph = seg
        m = self._match_one(glyph)
        if m is not None:
            return m
        widest = self._widest_template_w()
        if widest > 0 and glyph.shape[1] > widest + 2:
            # Merged glyphs (touching digits): try splitting at local
            # ink minima. Wrong cuts simply fail the match → tesseract.
            col_ink = np.count_nonzero(glyph, axis=0).astype(float)
            W = glyph.shape[1]
            mid_lo = max(1, W // 5)
            mid_hi = W - max(1, W // 5)
            cands = []
            for x in range(1, W - 1):
                if mid_lo <= x <= mid_hi and col_ink[x] <= col_ink[x - 1] and col_ink[x] <= col_ink[x + 1]:
                    cands.append((float(col_ink[x]), x))
            cands.sort()
            cands = [x for _d, x in cands[:8]]
            if not cands:
                cands = sorted(int(c) for c in np.argsort(col_ink)[:3])
            widths = [int(t.shape[1]) for v in self.templates.values() for t in v]
            minw = max(2, min(widths))

            def _try_parts(bounds):
                chars, dists = [], []
                for a, b in zip(bounds[:-1], bounds[1:]):
                    if b - a < 2:
                        return None
                    part = glyph[:, a:b]
                    prows = np.where(part.any(axis=1))[0]
                    if prows.size == 0:
                        return None
                    pm = self._match_one(part[prows[0]: prows[-1] + 1, :])
                    if pm is None:
                        return None
                    chars.append(pm[0])
                    dists.append(pm[1])
                return "".join(chars), float(sum(dists) / len(dists))

            # try 2-part and 3-part splits; width must be plausible for k glyphs
            for k in (2, 3):
                if W > k * widest + 4 or W < k * minw - 4:
                    continue
                if k == 2:
                    combos = [[0, x, W] for x in cands]
                else:
                    combos = [[0, a, b, W] for i, a in enumerate(cands) for b in cands[i + 1:]]
                for bounds in combos:
                    r = _try_parts(bounds)
                    if r is not None:
                        return r
        return None

    # ── public: fast read ───────────────────────────────────────
    def read_fast(self, proc: np.ndarray) -> str | None:
        """Assemble the string by template matching, or None to fall back."""
        if not any(self.templates.values()):
            return None
        try:
            with self.lock:
                return self._read_fast_impl(proc)
        except Exception as e:
            log.debug(f"[FASTOCR:{self.name}] fast read error: {e}")
            return None

    def _read_fast_impl(self, proc: np.ndarray) -> str | None:
        """Lock-free core — caller must hold self.lock."""
        try:
            segs = self._segments(proc)
            if not segs:
                return None
            seg_results = []
            for seg in segs:
                seg_results.append(self._read_segment(seg))
            matched = [r for r in seg_results if r is not None]
            if not matched:
                return None
            # Size reference: median INK of matched glyph segments.
            # Unmatched segments clearly bigger (icons, decorations) are
            # skipped; glyph-sized unknowns fail the read so the caller
            # harvests them via tesseract.
            match_ink = [
                float(np.count_nonzero(s[4])) for s, r in zip(segs, seg_results) if r is not None
            ]
            median_ink = float(np.median(match_ink)) if match_ink else 0.0
            for s, r in zip(segs, seg_results):
                if r is not None:
                    continue
                if float(np.count_nonzero(s[4])) > 3.0 * max(1.0, median_ink):
                    continue  # big blob — icon/noise, skip it
                return None    # glyph-sized unknown — needs harvest
            s = "".join(r[0] for r in seg_results if r is not None)
            if not self.clean_re.fullmatch(s):
                return None
            self.stats["fast"] += 1
            if not self._first_fast_logged:
                self._first_fast_logged = True
                log.debug(f"[FASTOCR:{self.name}] fast template reads active "
                         f"({len(self.templates)} chars cached)")
            return s
        except Exception as e:
            log.debug(f"[FASTOCR:{self.name}] fast read error: {e}")
            return None

    # ── public: harvest from a confirmed tesseract read ─────────
    def harvest(self, proc: np.ndarray, raw: str, tess_config: str = "") -> None:
        """Store glyph templates from a clean tesseract read.

        Uses NO extra tesseract call: the clean string's characters map
        one-to-one (left to right) onto the image's glyph segments, after
        dropping icon-sized blobs. Templates are only kept if they
        reproduce the confirmed value when read back from the same image.
        """
        try:
            text = (raw or "").strip()
            if not text or not self.clean_re.fullmatch(text):
                return
            known = {ch for ch, v in self.templates.items() if v}
            if known and not any(ch not in known for ch in text):
                return  # nothing new to learn
            with self.lock:
                self._harvest_seq += 1
                seq = self._harvest_seq
                segs = self._segments(proc)
                if not segs:
                    return
                # Drop icon-sized blobs before the 1:1 char mapping.
                # Two filters: ink area (glowing icons have far more ink
                # than glyphs) and glyph-height deviation (icons are taller
                # or shorter than the digit row).
                inks = [float(np.count_nonzero(s[4])) for s in segs]
                med = float(np.median(inks))
                by_ink = [s for s, ink in zip(segs, inks)
                          if ink <= 3.0 * max(1.0, med)]
                if len(by_ink) != len(text):
                    hts = [float(s[3] - s[2]) for s in by_ink]
                    med_h = float(np.median(hts)) if hts else 0.0
                    keep = [s for s, h in zip(by_ink, hts)
                            if med_h <= 0 or abs(h - med_h) <= 0.35 * med_h]
                    if len(keep) != len(text):
                        return  # merged/ambiguous rendering — skip this read
                else:
                    keep = by_ink
                new_chars = []
                for ch, seg in zip(text, keep):
                    if len(ch) != 1 or ch not in self.whitelist:
                        return
                    glyph = seg[4]
                    variants = self.templates.get(ch, [])
                    if any(t.shape == glyph.shape and not np.any(t != glyph)
                           for t in variants):
                        continue  # exact duplicate of a committed template
                    # Double confirmation: a NEW bitmap only becomes a
                    # template after tesseract produces the same character
                    # with a near-identical bitmap twice. A one-off misread
                    # never poisons the cache.
                    cand = self._pending.get(ch)
                    if (cand is not None and cand[1] != seq
                            and self._xor_dist(cand[0], glyph) <= 0.12):
                        # Confirmed by a DIFFERENT tesseract read: repeated
                        # digits inside one read cannot confirm themselves.
                        variants = self.templates.setdefault(ch, [])
                        if len(variants) >= 4:
                            variants.pop(0)
                        variants.append(glyph)
                        new_chars.append(ch)
                        del self._pending[ch]
                    else:
                        self._pending[ch] = (glyph, seq)
                if not new_chars:
                    return
                # Self-verification: the freshly built templates must
                # reproduce the confirmed tesseract value on this very
                # image, or they are discarded.
                if self._read_fast_impl(proc) != text:
                    for ch in new_chars:
                        variants = self.templates.get(ch)
                        if variants:
                            variants.pop()
                            if not variants:
                                del self.templates[ch]
                    log.debug(f"[FASTOCR:{self.name}] harvest self-check failed for {raw!r} — discarded")
                    return
                log.debug(f"[FASTOCR:{self.name}] harvested {len(new_chars)} glyph(s) "
                         f"({new_chars}) — {len(self.templates)} chars templated")
                self._save()
        except Exception as e:
            log.debug(f"[FASTOCR:{self.name}] harvest error: {e}")
