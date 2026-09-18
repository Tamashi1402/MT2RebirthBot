# ============================================================
# MT2 BOT - SCREEN / OCR  (v3)
# Reads regions from config at call-time.
# ============================================================
import re
import os
import time
import numpy as np
import cv2
import mss
import pytesseract
import sys as _sys
import os as _os

# ── Auto-detect bundled Tesseract (no PATH / install required) ───────────────
# Used by EVERY mode (rebirth / delve / kraken / zytos / crater / dashboard).
# pytesseract.tesseract_cmd is process-wide, so one setup covers all OCR calls.
_TESSERACT_CMD = ""

def _candidate_tess_roots():
    roots = []
    if getattr(_sys, "frozen", False):
        # onefile: tess is packed inside the exe and extracted to _MEIPASS
        meipass = getattr(_sys, "_MEIPASS", None)
        if meipass:
            roots.append(meipass)
            roots.append(_os.path.join(meipass, "tesseract-ocr"))
        roots.append(_os.path.dirname(_os.path.abspath(_sys.executable)))
    here = _os.path.dirname(_os.path.abspath(__file__))
    roots.append(here)
    roots.append(_os.path.dirname(here))
    try:
        roots.append(_os.getcwd())
    except Exception:
        pass
    extra = []
    for base in list(roots):
        cur = _os.path.abspath(base)
        for _ in range(5):
            parent = _os.path.dirname(cur)
            if not parent or parent == cur:
                break
            extra.append(parent)
            cur = parent
    roots.extend(extra)
    return roots

def _apply_tess(tess):
    global _TESSERACT_CMD
    pytesseract.pytesseract.tesseract_cmd = tess
    tess_dir = _os.path.dirname(tess)
    _os.environ["PATH"] = tess_dir + _os.pathsep + _os.environ.get("PATH", "")
    tessdata = _os.path.join(tess_dir, "tessdata")
    if _os.path.isdir(tessdata):
        _os.environ["TESSDATA_PREFIX"] = tessdata
    _TESSERACT_CMD = tess
    return tess

def ensure_tesseract():
    """Point pytesseract at bundled tesseract-ocr/tesseract.exe. Idempotent."""
    global _TESSERACT_CMD
    current = getattr(pytesseract.pytesseract, "tesseract_cmd", "") or ""
    if current and current != "tesseract" and _os.path.isfile(current):
        _TESSERACT_CMD = current
        return _TESSERACT_CMD
    if _TESSERACT_CMD and _os.path.isfile(_TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
        return _TESSERACT_CMD

    names = ("tesseract-ocr", "tesseract", "Tesseract-OCR")
    seen = set()
    tried = []
    for base in _candidate_tess_roots():
        base = _os.path.abspath(base)
        if base in seen:
            continue
        seen.add(base)
        direct = _os.path.join(base, "tesseract.exe")
        tried.append(direct)
        if _os.path.isfile(direct):
            return _apply_tess(direct)
        for name in names:
            tess = _os.path.join(base, name, "tesseract.exe")
            tried.append(tess)
            if _os.path.isfile(tess):
                return _apply_tess(tess)
    for pf in (
        _os.path.join(_os.environ.get("ProgramFiles", r"C:\Program Files"), "Tesseract-OCR"),
        _os.path.join(_os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Tesseract-OCR"),
        r"C:\Program Files\Tesseract-OCR",
    ):
        tess = _os.path.join(pf, "tesseract.exe")
        tried.append(tess)
        if _os.path.isfile(tess):
            return _apply_tess(tess)
    try:
        from logger import get_logger as _gl
        _gl().warning("[OCR] tesseract.exe not found. looked in: " + " | ".join(tried[:12]))
    except Exception:
        pass
    return ""

def _setup_tesseract():
    return ensure_tesseract()

_setup_tesseract()

from logger import get_logger, debug_on_change, debug_every
import config as _cfg

log = get_logger()
if _TESSERACT_CMD:
    log.info(f"[OCR] using tesseract: {_TESSERACT_CMD}")
else:
    log.warning("[OCR] tesseract.exe not found — expected tesseract-ocr/ next to the bot (all modes use this)")

def _crater_debug():
    """Check if crater debug logging is enabled."""
    try:
        import config as _cfg_dbg
        return bool(getattr(_cfg_dbg, "CRATER_DEBUG", True))
    except Exception:
        return True
_last_menu_play_region = None

# ── Debug screenshot directory ───────────────────────────────
_BOT_DIR  = os.path.dirname(os.path.abspath(__file__))
DEBUG_DIR = os.path.join(_BOT_DIR, "debug_crops")
# Folder is created on first use only — not at startup
_last_debug_save_by_label: dict[str, float] = {}
_label_debug_interval_override = {
    "stone_fail": 12.0,
    "manual_str_strength_fail": 15.0,
    "manual_str_stone_fail": 6.0,
}

def _is_failure_debug_label(label: str) -> bool:
    s = str(label or "").strip().lower()
    if not s:
        return False
    # Quest calibration crops (quest_panel*/quest_gain*/quest_total) must
    # always save while SAVE_DEBUG_CROPS is on — they are how the user
    # verifies what the OCR actually saw and re-tunes the regions.
    if s.startswith("quest_"):
        return True
    # Keep debug crops focused on failure evidence only.
    failure_tokens = ("fail", "failed", "error", "missing", "lost", "invalid", "timeout")
    return any(tok in s for tok in failure_tokens)

def _save_debug(label: str, img: np.ndarray, extra: np.ndarray = None):
    if not _cfg.SAVE_DEBUG_CROPS:
        return
    if not _is_failure_debug_label(label):
        return
    now = time.time()
    throttle_s = max(0.0, float(getattr(_cfg, "DEBUG_CROP_MIN_INTERVAL_SECONDS", 1.0)))
    throttle_s = max(throttle_s, float(_label_debug_interval_override.get(str(label), 0.0)))
    last = float(_last_debug_save_by_label.get(label, 0.0))
    if throttle_s > 0.0 and (now - last) < throttle_s:
        return
    _last_debug_save_by_label[label] = now
    os.makedirs(DEBUG_DIR, exist_ok=True)
    ts = time.strftime("%H%M%S")
    ms = int((now % 1.0) * 1000)
    path = os.path.join(DEBUG_DIR, f"{ts}_{ms:03d}_{label}.png")
    cv2.imwrite(path, img)
    log.debug(f"Debug crop → {path}")
    if extra is not None:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{ts}_{ms:03d}_{label}_proc.png"), extra)

def save_debug_image(label: str, img: np.ndarray, extra: np.ndarray = None):
    """Public helper for failure crop saves from other modules."""
    _save_debug(label, img, extra)

def save_debug_region(label: str, region: tuple[int, int, int, int], extra: np.ndarray = None):
    """Capture and save a failure crop for a specific screen region."""
    if not _cfg.SAVE_DEBUG_CROPS or not _is_failure_debug_label(label):
        return
    try:
        img = grab_region(region)
        _save_debug(label, img, extra)
    except Exception as e:
        log.debug(f"save_debug_region failed: {e}")

def save_debug_fullscreen(label: str) -> str | None:
    """Save a full-screen debug screenshot when SAVE_DEBUG_CROPS is enabled."""
    if not _cfg.SAVE_DEBUG_CROPS:
        return None
    try:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(label or "failure"))
        ts = time.strftime("%H%M%S")
        ms = int((time.time() % 1.0) * 1000)
        path = os.path.join(DEBUG_DIR, f"{ts}_{ms:03d}_fullscreen_{safe}.png")
        img = grab_full_screen()
        cv2.imwrite(path, img)
        log.debug(f"Debug fullscreen -> {path}")
        return path
    except Exception as e:
        log.debug(f"save_debug_fullscreen failed: {e}")
        return None

# ── Screenshot helper ────────────────────────────────────────
def grab_region(region: tuple) -> np.ndarray:
    """Grab screen region (x1,y1,x2,y2) → BGR numpy array."""
    x1, y1, x2, y2 = region
    with mss.mss() as sct:
        mon = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        raw = sct.grab(mon)
        img = np.array(raw)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def grab_full_screen() -> np.ndarray:
    """Grab the primary monitor as a BGR numpy array."""
    with mss.mss() as sct:
        mon = sct.monitors[1]
        raw = sct.grab(mon)
        img = np.array(raw)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

# ── Stone value parser — handles both eN and suffix formats ─────────────────
# Scientific / engineering notation:  "4.53e123",  "856.09e12"
_SCI_RE = re.compile(
    r"(\d[\d,\.]*)"
    r"\s*[eEхХ×xX]\s*"
    r"(\d+)",
    re.UNICODE,
)

# Suffix notation — sorted longest-first so "QaDc" matches before "Qa", etc.
# Full table matches the in-game HUD — K(e3) through DDd(e306).
_SUFFIX_MAP = [
    ("SpNn", 1e294), ("SxNn", 1e291), ("QtNn", 1e288), ("QaNn", 1e285),
    ("SpOg", 1e264), ("SxOg", 1e261), ("QtOg", 1e258), ("QaOg", 1e255),
    ("SpSt", 1e234), ("SxSt", 1e231), ("QtSt", 1e228), ("QaSt", 1e225),
    ("SpSe", 1e204), ("SxSe", 1e201), ("QtSe", 1e198), ("QaSe", 1e195),
    ("SpQi", 1e174), ("SxQi", 1e171), ("QtQi", 1e168), ("QaQi", 1e165),
    ("SpQd", 1e144), ("SxQd", 1e141), ("QtQd", 1e138), ("QaQd", 1e135),
    ("SpTg", 1e114), ("SxTg", 1e111), ("QtTg", 1e108), ("QaTg", 1e105),
    ("SpVg", 1e84),  ("SxVg", 1e81),  ("QtVg", 1e78),  ("QaVg", 1e75),
    ("SpDc", 1e54),  ("SxDc", 1e51),  ("QtDc", 1e48),  ("QaDc", 1e45),
    ("DDd",  1e306), ("NNn",  1e300), ("ONn",  1e297), ("TNn",  1e282),
    ("DNn",  1e279), ("UNn",  1e276), ("NOg",  1e270), ("OOg",  1e267),
    ("TOg",  1e252), ("DOg",  1e249), ("UOg",  1e246), ("NSt",  1e240),
    ("OSt",  1e237), ("TSt",  1e222), ("DSt",  1e219), ("USt",  1e216),
    ("NSe",  1e210), ("OSe",  1e207), ("TSe",  1e192), ("DSe",  1e189),
    ("USe",  1e186), ("NQi",  1e180), ("OQi",  1e177), ("TQi",  1e162),
    ("DQi",  1e159), ("UQi",  1e156), ("NQd",  1e150), ("OQd",  1e147),
    ("TQd",  1e132), ("DQd",  1e129), ("UQd",  1e126), ("NTg",  1e120),
    ("OTg",  1e117), ("TTg",  1e102), ("DTg",  1e99),  ("UTg",  1e96),
    ("NVg",  1e90),  ("OVg",  1e87),  ("TVg",  1e72),  ("DVg",  1e69),
    ("UVg",  1e66),  ("NDc",  1e60),  ("ODc",  1e57),  ("TDc",  1e42),
    ("DDc",  1e39),  ("UDc",  1e36),  ("Dd",   1e303), ("Nn",   1e273),
    ("Og",   1e243), ("St",   1e213), ("Se",   1e183), ("Qi",   1e153),
    ("Qd",   1e123), ("Tg",   1e93),  ("Vg",   1e63),  ("Dc",   1e33),
    ("No",   1e30),  ("Oc",   1e27),  ("Sp",   1e24),  ("Sx",   1e21),
    ("Qt",   1e18),  ("Qa",   1e15),  ("T",    1e12),  ("B",    1e9),
    ("M",    1e6),   ("K",    1e3),
]
# Regex: number (with optional decimal) followed immediately by a suffix
_SUFFIX_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)"
    r"\s*(" + "|".join(re.escape(s) for s, _ in _SUFFIX_MAP) + r")"
    r"\b",
    re.IGNORECASE,
)

def parse_stone(text: str) -> float | None:
    """Parse a stone value string — supports both eN notation and suffix format.

    Pass 1: try suffix notation on raw text (preserves 'O' so suffixes like
            Og, ODc, OVg, OTg, ONn match correctly).
    Pass 2: apply OCR digit fixes (O→0, l→1, I→1) then try eN notation.
    Pass 3: plain integer / decimal fallback.

    Examples:
        "4.53e123"   → 4.53e123
        "856.09e12"  → 8.5609e14
        "1.5T"       → 1.5e12
        "3.3Og"      → 3.3e243
        "9.9ODc"     → 9.9e57

    NOTE: returns None for any value that overflows to inf/nan (e.g. OCR
    misreads like '61.68e381' where a stray digit inflates the exponent).
    Python floats cap at ~1.8e308; anything beyond is an OCR artifact.
    """
    import math as _math

    # Light normalization — keep letter case and 'O' intact for suffix matching
    text_raw = text.strip().replace(",", ".").replace(" ", "")

    # Common user/OCR variant. The game suffix is "Sx"; OCR/shorthand can show
    # up as "Stx" / "stx", which otherwise falls through to a plain number.
    text_raw = re.sub(r"(?i)(\d+(?:\.\d+)?)stx\b", r"\1Sx", text_raw)

    # ── Exponent sanity guard (eN notation only) ─────────────────────────────
    # The game's highest suffix is DDd = 1e306. Any exponent > 308 in raw OCR
    # text is guaranteed to be a misread (e.g. '61.68e381' instead of '61.68e81').
    # Reject the entire read so the bot doesn't act on a phantom inf value.
    _exp_check = re.search(r'[eExX]\s*(\d+)', text_raw)
    if _exp_check and int(_exp_check.group(1)) > 308:
        log.debug(f"parse_stone: exponent {_exp_check.group(1)} > 308 — OCR artifact, rejecting: {text_raw!r}")
        return None

    # 1. Try suffix notation FIRST (before any O→0 substitution)
    for suffix, multiplier in _SUFFIX_MAP:
        pat = re.compile(
            r"(\d+(?:\.\d+)?)" + re.escape(suffix) + r"(?:[^a-zA-Z]|$)",
            re.IGNORECASE,
        )
        m = pat.search(text_raw)
        if m:
            try:
                v = float(m.group(1)) * multiplier
                if _math.isfinite(v):
                    return v
            except (ValueError, OverflowError):
                pass

    # 2. Apply OCR digit-correction, then try scientific/engineering notation
    text_fixed = (text_raw
                  .replace("O", "0").replace("o", "0")
                  .replace("l", "1").replace("I", "1"))
    m = _SCI_RE.search(text_fixed)
    if m:
        try:
            v = float(f"{m.group(1)}e{m.group(2)}")
            if _math.isfinite(v):
                return v
        except (ValueError, OverflowError):
            pass

    # 3. Plain integer / decimal fallback (e.g. small values at run start)
    plain = re.search(r"\d+(?:\.\d+)?", text_fixed)
    if plain:
        try:
            v = float(plain.group())
            if _math.isfinite(v):
                return v
        except (ValueError, OverflowError):
            pass

    return None

# Keep old name as alias so anything still calling parse_scientific works
parse_scientific = parse_stone


def _manual_strength_window_open() -> bool:
    try:
        from manual_strength import is_window_open as _is_window_open
        return bool(_is_window_open())
    except Exception:
        return False


def _f4_menu_probably_open() -> bool:
    """Best-effort fast check for teleport menu visibility via yellow CLOSE button."""
    try:
        sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0))
        sy = float(getattr(_cfg, "REGION_SCALE_Y", 1.0))
        x1 = int(round(300 * sx))
        x2 = int(round(1600 * sx))
        y1 = int(round(805 * sy))
        y2 = int(round(1015 * sy))
        img = grab_region((x1, y1, x2, y2))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 65, 100], dtype=np.uint8),  # widened for semi-transparent close button
            np.array([45, 255, 255], dtype=np.uint8),
        )
        pct = float(np.sum(yellow > 0)) / float(max(1, yellow.size))
        return pct >= 0.05
    except Exception:
        return False

# ── OCR preprocess ───────────────────────────────────────────
def _preprocess(img: np.ndarray) -> np.ndarray:
    """Upscale + threshold — isolate bright HUD text on dark panel."""
    scale = 3
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return thresh


def _preprocess_crater_timer(img: np.ndarray) -> list:
    """Dedicated preprocessing for the crater timer HUD ("M:SS").

    The shared _preprocess() uses a fixed threshold of 150 which only
    works when the HUD text brightness happens to straddle that value.
    When the game background shifts (effects, lighting, animation frames)
    the fixed threshold either nukes the text to black or drowns it in
    white — making the OCR fail entirely.  That causes the timer tracker
    to accumulate consecutive misses, the bot to think it left the
    crater, and rapid in/out cycling.

    Returns multiple preprocessed variants using methods that adapt to
    the actual pixel data instead of a magic constant:

    1. Otsu auto-threshold (picks the optimal split from the histogram)
    2. Otsu inverted (in case text is dark-on-light)
    3. Adaptive Gaussian (local contrast — robust to gradients)

    No morphological opening is applied — the 2x2 kernel in _preprocess
    can eat the thin colon strokes, making Tesseract drop the ':' and
    causing the M:SS regex to miss.
    """
    scale = 4  # 4x upscale for better colon resolution
    img_u = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_u, cv2.COLOR_BGR2GRAY)

    variants = []

    # 1. Otsu auto-threshold
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", otsu))

    # 2. Otsu inverted (dark-on-light text)
    _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    variants.append(("otsu_inv", otsu_inv))

    # 3. Adaptive Gaussian (local threshold, robust to gradients)
    block = max(11, (gray.shape[1] // 8) | 1)  # odd block size
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, block, 2)
    variants.append(("adaptive", adaptive))

    return variants

# ── Crater countdown timer (top-center HUD "M:SS") ──────────
_CRATER_TIMER_RE = re.compile(r"(\d{1,2})\s*[:;.]\s*(\d{2})")
# Fallback for when Tesseract drops the colon entirely (e.g. "100" instead of "1:00")
_CRATER_TIMER_DIGITS_RE = re.compile(r"^(\d{1,2})(\d{2})$")

def parse_crater_timer(text: str) -> int | None:
    """Parse the crater countdown HUD text (e.g. '1:00', '0:45') into total
    seconds. Returns None if it doesn't look like a plausible mm:ss timer —
    callers should treat None as a miss, not as proof we've left the crater
    (a single bad OCR read is common; see crater/timer_tracker.py).

    Colon-repair: if Tesseract drops the ':' (common when the morphological
    opening eats the thin colon strokes), we try to reconstruct M:SS from
    the digit-only output (e.g. "100" → 1:00 = 60s, "059" → 0:59 = 59s)."""
    if not text:
        return None
    text = text.strip()
    m = _CRATER_TIMER_RE.search(text)
    if m:
        minutes = int(m.group(1))
        seconds = int(m.group(2))
        if minutes > 99 or seconds > 59:
            return None
        return minutes * 60 + seconds

    # Colon-repair: strip non-digits and try to reconstruct M:SS
    digits = re.sub(r"[^0-9]", "", text)
    m2 = _CRATER_TIMER_DIGITS_RE.match(digits)
    if m2:
        minutes = int(m2.group(1))
        seconds = int(m2.group(2))
        if minutes > 9 or seconds > 59:
            return None
        return minutes * 60 + seconds

    return None

def read_crater_timer() -> int | None:
    """Read the crater countdown timer HUD element (top-center "M:SS").
    Used ONLY to confirm we're still inside the crater mining area — the
    timer counts DOWN while in the crater and jumps back up to its start
    value when it resets. Returns total seconds, or None if unreadable.

    Tries multiple preprocessing approaches (Otsu auto-threshold, adaptive
    Gaussian, and the original fixed-threshold) × multiple PSM modes, taking
    the first successful parse.  This is far more robust than the old
    single-fixed-threshold approach which failed whenever game brightness
    shifted away from the magic constant of 150."""
    import os as _os_crater
    import time as _time_crater
    _crater_debug = bool(getattr(_cfg, "CRATER_TIMER_DEBUG", True))
    _crater_debug_dir = os.path.join(_BOT_DIR, "debug_crops")
    try:
        region = _cfg.CRATER_TIMER_REGION
        img = grab_region(region)

        # ── Build the list of (label, preprocessed_image, psm_config) to try ──
        # Order: most-likely-to-succeed first so we break early.
        psm_configs = [
            ("7",  "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789:"),   # single line
            ("8",  "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789:"),   # single word
            ("13", "--psm 13 --oem 3 -c tessedit_char_whitelist=0123456789:"), # raw line
            ("6",  "--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789:"),   # uniform block
        ]

        # New adaptive preprocessing variants (Otsu + adaptive threshold)
        timer_variants = _preprocess_crater_timer(img)

        attempts = []
        # Try each Otsu/adaptive variant with PSM 7 first (most likely to work)
        for vlabel, vimg in timer_variants:
            attempts.append((vlabel, vimg, psm_configs[0]))
        # Then try Otsu with remaining PSM modes
        for psm_label, psm_cfg in psm_configs[1:]:
            attempts.append((timer_variants[0][0], timer_variants[0][1], (psm_label, psm_cfg)))
        # Finally try the original fixed-threshold _preprocess with all PSM modes
        proc_orig = _preprocess(img)
        for psm_label, psm_cfg in psm_configs:
            attempts.append(("orig", proc_orig, (psm_label, psm_cfg)))

        results = []
        for vlabel, vimg, (psm_label, psm_cfg) in attempts:
            raw_i = pytesseract.image_to_string(vimg, config=psm_cfg)
            parsed_i = parse_crater_timer(raw_i)
            results.append((f"{vlabel}/PSM{psm_label}", raw_i.strip(), parsed_i))
            if parsed_i is not None:
                break  # first hit wins

        result = next((p for _, _, p in results if p is not None), None)
        used_label = next((lbl for lbl, _, p in results if p is not None), "?")
        raw_best = results[0][1] if result is None else next(r for l, r, p in results if p is not None)

        # ── Verbose logging ──
        if _crater_debug:
            log.debug(f"Crater timer region: {region}")
            for lbl, raw_i, parsed_i in results:
                tag = "OK" if parsed_i is not None else "miss"
                log.debug(f"  {lbl}: {raw_i!r} -> {tag} ({parsed_i})")

        if result is not None:
            log.debug(f"Crater timer OCR: {raw_best!r} -> {result}s ({used_label})")
        else:
            log.info(f"Crater timer OCR ALL MISS — raw best: {raw_best!r} (tried {len(results)} variants)")

        # ── Save debug crops on miss ──
        if _crater_debug and (result is None):
            try:
                os.makedirs(_crater_debug_dir, exist_ok=True)
                ts = _time_crater.strftime("%H%M%S")
                cv2.imwrite(os.path.join(_crater_debug_dir, f"crater_timer_raw_{ts}.png"), img)
                # Save the Otsu variant for debugging
                if timer_variants:
                    cv2.imwrite(os.path.join(_crater_debug_dir, f"crater_timer_otsu_{ts}.png"), timer_variants[0][1])
                log.info(f"  Saved crops: crater_timer_raw_{ts}.png + crater_timer_otsu_{ts}.png")
            except Exception as _save_e:
                log.warning(f"  Failed to save crater timer debug crops: {_save_e}")

        return result
    except Exception as e:
        log.warning(f"read_crater_timer() failed: {e}")
        return None



def read_crater_pet_drop() -> bool:
    """OCR-scan the crater pet-drop notification region for 'Received' text.

    Returns True if the word 'Received' (case-insensitive) is found in the
    OCR output, indicating a pet just dropped.  The caller applies a
    cooldown to avoid double-counting the same drop.
    """
    _debug = bool(getattr(_cfg, "CRATER_PET_DROP_DEBUG", True))
    _debug_dir = os.path.join(_BOT_DIR, "debug_crops")
    try:
        region = _cfg.CRATER_PET_DROP_REGION
        img = grab_region(region)

        # Preprocess: upscale + threshold for better text recognition
        proc = _preprocess(img)

        # Try sparse text first (most likely to catch it), only fall back if needed
        configs = [
            "--psm 11 --oem 3",   # sparse text — best for finding words anywhere
        ]

        for cfg_str in configs:
            raw = pytesseract.image_to_string(proc, config=cfg_str)
            text_lower = raw.strip().lower()
            if "received" in text_lower:
                log.info(f"Crater pet drop detected! OCR text: {raw.strip()!r}")
                if _debug:
                    try:
                        os.makedirs(_debug_dir, exist_ok=True)
                        import time as _t_pd
                        ts = _t_pd.strftime("%H%M%S")
                        cv2.imwrite(os.path.join(_debug_dir, f"crater_pet_drop_raw_{ts}.png"), img)
                        cv2.imwrite(os.path.join(_debug_dir, f"crater_pet_drop_proc_{ts}.png"), proc)
                        log.info(f"  Saved pet drop crops: crater_pet_drop_raw_{ts}.png + crater_pet_drop_proc_{ts}.png")
                    except Exception as _save_e:
                        log.warning(f"  Failed to save pet drop debug crops: {_save_e}")
                return True

        return False
    except Exception as e:
        log.warning(f"read_crater_pet_drop() failed: {e}")
        return False


# ── Color helpers ────────────────────────────────────────────
def color_match_percent(img, target_hsv, hue_tol=8, sat_tol=30, val_tol=50):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = target_hsv
    lo = np.array([max(0,   h - hue_tol), max(0,   s - sat_tol), max(0,   v - val_tol)], dtype=np.uint8)
    hi = np.array([min(180, h + hue_tol), min(255, s + sat_tol), min(255, v + val_tol)], dtype=np.uint8)
    if lo[0] > hi[0]:
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, np.array([lo[0], lo[1], lo[2]]), np.array([180, hi[1], hi[2]])),
            cv2.inRange(hsv, np.array([0,     lo[1], lo[2]]), hi),
        )
    else:
        mask = cv2.inRange(hsv, lo, hi)
    total = img.shape[0] * img.shape[1]
    return float(np.sum(mask > 0)) / total if total > 0 else 0.0

def white_percent(img, sat_max=60, val_min=180):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,
        np.array([0, 0, val_min], dtype=np.uint8),
        np.array([180, sat_max, 255], dtype=np.uint8))
    total = img.shape[0] * img.shape[1]
    return float(np.sum(mask > 0)) / total if total > 0 else 0.0

def red_percent(img, sat_min=80, val_min=120):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lo1 = np.array([0, sat_min, val_min], dtype=np.uint8)
    hi1 = np.array([12, 255, 255], dtype=np.uint8)
    lo2 = np.array([170, sat_min, val_min], dtype=np.uint8)
    hi2 = np.array([180, 255, 255], dtype=np.uint8)
    mask = cv2.bitwise_or(cv2.inRange(hsv, lo1, hi1), cv2.inRange(hsv, lo2, hi2))
    total = img.shape[0] * img.shape[1]
    return float(np.sum(mask > 0)) / total if total > 0 else 0.0

# ── Public API ───────────────────────────────────────────────

def read_stone() -> float | None:
    try:
        img  = grab_region(_cfg.STONE_REGION)
        proc = _preprocess(img)
        # Whitelist includes letters for suffix format (K/M/B/T/Qa/Qi/Dc etc.)
        raw  = pytesseract.image_to_string(
            proc, config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.eExXkKmMbBtTqQiIsSpPaAnNoOdDcCuUgGvV")
        debug_on_change("stone_ocr", f"Stone OCR raw: {raw.strip()!r}")
        result = parse_stone(raw)
        if result is not None:
            # Auto-detect display mode from the raw OCR text so the overlay
            # mirrors whatever format the game HUD is currently showing.
            _update_display_mode(raw)
        if result is not None:
            _save_debug("stone_read", img, proc)
        else:
            # Ignore expected OCR misses while major menus are open.
            if _manual_strength_window_open() or _f4_menu_probably_open():
                log.debug("Stone OCR miss ignored while menu is open")
            else:
                _save_debug("stone_fail", img, proc)
        return result
    except Exception as e:
        log.warning(f"read_stone() failed: {e}")
        return None


def _find_stone_icon_right_edge(img: np.ndarray) -> int:
    """Return the x-coordinate (in original image pixels) just after the
    orange/brown brick icon in the manual-strength stone region.

    The brick icon is an orange-brown colour — completely different from the
    white HUD number text.  We locate it via HSV colour masking rather than
    brightness thresholding so the detection is resolution-independent and
    never accidentally chops digits.

    Strategy
    --------
    1. Build a mask of orange/brown pixels (the brick).
    2. Find the rightmost column that contains any masked pixels.
    3. Return that column + a small gap margin.
    Returns 0 if no icon is found (caller will use the full region).
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Orange-brown hue range: roughly 5-25 in OpenCV (0-180 scale)
    lo = np.array([4,  80,  60], dtype=np.uint8)
    hi = np.array([28, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lo, hi)
    cols_with_icon = np.where(mask.any(axis=0))[0]
    if len(cols_with_icon) == 0:
        return 0
    rightmost = int(cols_with_icon[-1])
    # IMPORTANT: only trust orange detection if the icon is in the LEFT 45% of
    # the region. When the manual strength window is CLOSED the game's HUD stone
    # icon (also orange) bleeds in from the right side of the region (~col 205 of
    # 225px), causing a massive over-crop.  The real brick icon (window open) is
    # always in the left portion, typically col 6-40.
    max_icon_col = int(img.shape[1] * 0.45)
    if rightmost > max_icon_col:
        return 0  # it's the HUD stone icon, not the strength-menu brick
    # Add a 3px gap so no icon edge bleeds into the OCR crop
    return min(rightmost + 3, img.shape[1] - 20)


def read_manual_strength_stone() -> float | None:
    try:
        img = grab_region(_cfg.MANUAL_STR_STONE_REGION)
        h, w = img.shape[:2]

        # Build OCR candidates ordered from most reliable to least.
        candidates: list[tuple[str, np.ndarray]] = []
        icon_right = _find_stone_icon_right_edge(img)
        if icon_right > 0 and icon_right < (w - 12):
            candidates.append(("icon", img[:, icon_right:]))

        # Fallback crop for cases where icon color mask misses at some resolutions.
        fallback_crop = max(int(w * 0.18), min(int(h * 1.4), int(w * 0.35)))
        if fallback_crop > 0 and fallback_crop < (w - 12):
            if not candidates or abs(fallback_crop - icon_right) >= 8:
                candidates.append(("fallback", img[:, fallback_crop:]))

        candidates.append(("full", img))

        result = None
        raw = ""
        used_mode = "full"
        used_img = img
        used_proc = _preprocess(img)
        for mode, ocr_img in candidates:
            proc = _preprocess(ocr_img)
            cur_raw = pytesseract.image_to_string(
                proc,
                config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.eExXkKmMbBtTqQiIsSpPaAnNoOdDcCuUgGvV",
            )
            cur_result = parse_stone(cur_raw)
            log.debug(f"Manual strength stone OCR ({mode}) raw: {cur_raw.strip()!r}")
            used_mode, used_img, used_proc, raw = mode, ocr_img, proc, cur_raw
            if cur_result is not None:
                result = cur_result
                break

        if result is not None:
            _update_display_mode(raw)
        log.debug(f"Manual strength stone OCR mode selected: {used_mode}")
        _save_debug("manual_str_stone_read" if (result is not None) else "manual_str_stone_fail", used_img, used_proc)
        return result
    except Exception as e:
        log.warning(f"read_manual_strength_stone() failed: {e}")
        return None

def _update_display_mode(raw: str):
    """Detect whether the game is showing suffix (K/M/T/Qa...) or eN format
    and tell the overlay to match it. Called after every successful read."""
    try:
        from overlay import set_stone_display_mode
        # If the raw text contains an 'e' followed by digits it's eN format.
        # If it contains any known suffix letter cluster, it's suffix format.
        stripped = raw.strip().replace(" ", "")
        if re.search(r"[eExX]\d+", stripped):
            set_stone_display_mode("eng")
        elif re.search(r"[KkMmBbTtQqIiSsDdNnOoUuGg]{1,4}$", stripped):
            set_stone_display_mode("suffix")
        # else: ambiguous (plain number) — keep current mode
    except Exception:
        pass

def read_strength() -> float | None:
    try:
        img  = grab_region(_cfg.STRENGTH_REGION)
        proc = _preprocess(img)
        raw  = pytesseract.image_to_string(
            proc, config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.eExX")
        debug_on_change("str_ocr", f"Strength OCR raw: {raw.strip()!r}")
        result = parse_scientific(raw)
        _save_debug("strength_read" if (result is not None) else "strength_fail", img, proc)
        return result
    except Exception as e:
        log.warning(f"read_strength() failed: {e}")
        return None

def read_manual_strength_strength() -> float | None:
    try:
        if not _manual_strength_window_open():
            debug_on_change("ms_skip", "Manual strength OCR skipped: window closed")
            return None
        img  = grab_region(_cfg.MANUAL_STR_STRENGTH_REGION)
        # Read full configured manual-strength strength region directly.
        proc = _preprocess(img)
        raw  = pytesseract.image_to_string(
            proc, config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.eExXkKmMbBtTqQiIsSpPaAnNoOdDcCuUgGvV")
        debug_on_change("ms_str_ocr", f"Manual strength OCR raw: {raw.strip()!r}")
        result = parse_stone(raw)
        _save_debug("manual_str_strength_read" if (result is not None) else "manual_str_strength_fail", img, proc)
        return result
    except Exception as e:
        log.warning(f"read_manual_strength_strength() failed: {e}")
        return None

def read_manual_strength_surge() -> int | None:
    """Read the bottom-row Surge level (0-999) from the manual strength window.

    The level is shown on the bottom row only, so this is only meaningful
    when the bot buys bottom-row-only. Returns None when the window is
    closed or the number cannot be read.
    """
    try:
        if not _manual_strength_window_open():
            return None
        img  = grab_region(_cfg.MANUAL_STR_SURGE_REGION)
        proc = _preprocess(img)
        raw  = pytesseract.image_to_string(
            proc, config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789")
        debug_on_change("ms_surge_ocr", f"Manual strength surge OCR raw: {raw.strip()!r}")
        digits = re.sub(r"[^0-9]", "", raw)
        if not digits:
            _save_debug("manual_str_surge_fail", img, proc)
            return None
        val = int(digits)
        if not (0 <= val <= 999):
            _save_debug("manual_str_surge_fail", img, proc)
            return None
        _save_debug("manual_str_surge_read", img, proc)
        return val
    except Exception as e:
        log.warning(f"read_manual_strength_surge() failed: {e}")
        return None


def _horizontal_health_bar_metrics(
    img,
    thresh: float,
    debug_label: str,
    *,
    min_span_frac: float = 0.035,
    min_span_px: int = 24,
    max_span_frac: float = 1.0,
    max_height_frac: float = 1.0,
    min_aspect: float = 0.0,
):
    """Return (seen, color_pct, longest_span_px) for a horizontal red/orange bar."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red1 = cv2.inRange(hsv, np.array([0, 70, 80], dtype=np.uint8), np.array([14, 255, 255], dtype=np.uint8))
    red2 = cv2.inRange(hsv, np.array([170, 70, 80], dtype=np.uint8), np.array([179, 255, 255], dtype=np.uint8))
    orange = cv2.inRange(hsv, np.array([15, 80, 90], dtype=np.uint8), np.array([28, 255, 255], dtype=np.uint8))
    mask = cv2.bitwise_or(cv2.bitwise_or(red1, red2), orange)
    pct = float(np.count_nonzero(mask)) / float(max(1, mask.size))
    components, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    min_span = max(int(min_span_px), int(mask.shape[1] * float(min_span_frac)))
    max_span = max(min_span, int(mask.shape[1] * float(max_span_frac)))
    max_h = max(4, int(mask.shape[0] * float(max_height_frac)))
    longest_span = 0
    for index in range(1, components):
        x, y, width, height, area = (int(v) for v in stats[index])
        if height < 2 or height > max_h:
            continue
        if width < min_span or width > max_span:
            continue
        if area < max(20, min_span):
            continue
        if min_aspect and width < float(min_aspect) * height:
            continue
        longest_span = max(longest_span, width)
    seen = pct >= float(thresh) and longest_span >= min_span
    debug_every(
        f"hbar_{debug_label}",
        2.0,
        f"{debug_label} health bar: color={pct:.1%} span={longest_span}px need>={float(thresh):.1%} seen={seen}",
    )
    _save_debug(f"{debug_label}_health_seen" if seen else f"{debug_label}_health_missing", img)
    return seen, pct, longest_span


def _horizontal_health_bar_seen(img, thresh: float, debug_label: str) -> bool:
    """True only for a long horizontal red/orange health-bar fill.

    Shared by Kraken and meteor/rock. A simple red-pixel percentage is held
    above threshold by unrelated HUD noise after the bar vanishes.
    """
    seen, _pct, _span = _horizontal_health_bar_metrics(img, thresh, debug_label)
    return seen


def rock_health_red_percent() -> float:
    """Return red-fill ratio from the calibrated rock health bar region."""
    try:
        img = grab_region(_cfg.ROCK_HEALTH_BAR_REGION)
        pct = red_percent(img)
        log.debug(f"Rock health red fill: {pct:.1%}")
        _save_debug("rock_health_bar", img)
        return pct
    except Exception as e:
        log.warning(f"rock_health_red_percent() failed: {e}")
        return 1.0


def meteor_health_bar_metrics():
    """Stricter bar check for meteor first-break.

    The shared 1.5% / 25px rock detector treats leftover HUD orange as still
    alive, so meteor_hit never stops and the next meteor spawns. A real meteor
    bar in logs is ~13–30% fill and ~120–320px wide; remnants sit at 2–5%.
    """
    try:
        img = grab_region(_cfg.ROCK_HEALTH_BAR_REGION)
        thresh = float(getattr(_cfg, "METEOR_HEALTH_BAR_SEEN_THRESH", 0.06))
        return _horizontal_health_bar_metrics(
            img,
            thresh,
            "meteor",
            min_span_frac=0.10,
            min_span_px=56,
            max_span_frac=0.88,
            max_height_frac=0.55,
            min_aspect=3.0,
        )
    except Exception as e:
        log.warning(f"meteor_health_bar_metrics() failed: {e}")
        return True, 1.0, 0


def meteor_health_bar_seen() -> bool:
    return bool(meteor_health_bar_metrics()[0])


def rock_health_bar_metrics():
    """(seen, color_pct, span_px) for the meteor/rock boss bar."""
    try:
        img = grab_region(_cfg.ROCK_HEALTH_BAR_REGION)
        thresh = float(getattr(_cfg, "ROCK_HEALTH_BAR_SEEN_THRESH", 0.015))
        return _horizontal_health_bar_metrics(img, thresh, "rock")
    except Exception as e:
        log.warning(f"rock_health_bar_metrics() failed: {e}")
        return True, 1.0, 0


def rock_health_bar_seen() -> bool:
    """Meteor/rock break detection — same method as Kraken/Zytos boss bars."""
    return bool(rock_health_bar_metrics()[0])


def kraken_health_bar_seen() -> bool:
    """Return True only for a horizontal Kraken health-bar fill, not UI color noise."""
    try:
        img = grab_region(_cfg.KRAKEN_HEALTH_BAR_REGION)
        thresh = float(getattr(_cfg, "KRAKEN_HEALTH_BAR_SEEN_THRESH", 0.015))
        return _horizontal_health_bar_seen(img, thresh, "kraken")
    except Exception as e:
        log.warning(f"kraken_health_bar_seen() failed: {e}")
        return True



def zytos_health_bar_seen() -> bool:
    """Delegate to the zytos module so health-bar logic is not shared with kraken."""
    from zytos.detector import health_bar_seen
    return health_bar_seen()


def is_stone_icon_visible() -> bool:
    try:
        img = grab_region(_cfg.STONE_ICON_REGION)
        pct = color_match_percent(img,
            target_hsv=_cfg.STONE_ICON_HSV_TARGET,
            hue_tol=_cfg.STONE_ICON_HUE_TOL,
            sat_tol=_cfg.STONE_ICON_SAT_TOL,
            val_tol=_cfg.STONE_ICON_VAL_TOL,
        )
        debug_every(
            "stone_icon",
            3.0,
            f"Stone icon orange={pct:.1%} visible={pct >= _cfg.STONE_ICON_THRESH}",
        )
        visible = pct >= _cfg.STONE_ICON_THRESH
        _save_debug("stone_icon_ok" if visible else "stone_icon_fail", img)
        return visible
    except Exception as e:
        log.warning(f"is_stone_icon_visible() failed: {e}")
        # Treat capture failures as "not visible" so recovery logic can run.
        return False

def is_auto_strength_active() -> bool:
    try:
        img = grab_region(_cfg.AUTO_STR_REGION)
        pct = white_percent(img, sat_max=_cfg.AUTO_STR_SAT_MAX, val_min=_cfg.AUTO_STR_VAL_MIN)
        debug_on_change("auto_str", f"Auto-strength white={pct:.1%} active={pct >= _cfg.AUTO_STR_WHITE_THRESH}")
        active = pct >= _cfg.AUTO_STR_WHITE_THRESH
        _save_debug("auto_str_active" if active else "auto_str_off", img)
        return active
    except Exception as e:
        log.warning(f"is_auto_strength_active() failed: {e}")
        return False


def is_drill_active() -> bool:
    """True when the bottom-left cyan drill timer is on screen."""
    try:
        region = getattr(_cfg, "DRILL_ACTIVE_REGION", (28, 697, 124, 728))
        img = grab_region(region)
        pct = color_match_percent(
            img,
            target_hsv=getattr(_cfg, "DRILL_ACTIVE_HSV_TARGET", (90, 255, 255)),
            hue_tol=int(getattr(_cfg, "DRILL_ACTIVE_HUE_TOL", 12)),
            sat_tol=int(getattr(_cfg, "DRILL_ACTIVE_SAT_TOL", 90)),
            val_tol=int(getattr(_cfg, "DRILL_ACTIVE_VAL_TOL", 90)),
        )
        thresh = float(getattr(_cfg, "DRILL_ACTIVE_THRESH", 0.10))
        active = pct >= thresh
        debug_on_change("drill", f"[DRILLS] cyan={pct:.1%} active={active}")
        _save_debug("drill_active" if active else "drill_idle", img)
        return active
    except Exception as e:
        log.debug(f"is_drill_active() failed: {e}")
        return False

def is_in_area5() -> bool:
    """Pink-sky detection removed. Kept for compatibility with legacy callers."""
    return False

def is_rebirth_screen() -> bool:
    """All-black screen = respawning after rebirth. Uses full-screen detection."""
    try:
        img  = grab_full_screen()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        total = gray.shape[0] * gray.shape[1]
        if total <= 0:
            return False

        # Classic strict full-black detector.
        black_ratio_strict = float(np.sum(gray < 30)) / float(total)

        # More tolerant dark-screen detector for death/respawn transitions
        # where UI glow/noise keeps the frame from being "pure black".
        dark_ratio = float(np.sum(gray < 55)) / float(total)
        low_sat_ratio = float(np.sum(hsv[:, :, 1] < 50)) / float(total)
        mean_v = float(np.mean(hsv[:, :, 2]))

        strict_hit = black_ratio_strict > 0.75
        soft_hit = (dark_ratio >= 0.38 and low_sat_ratio >= 0.62 and mean_v <= 72.0)
        hit = bool(strict_hit or soft_hit)

        log.debug(
            "Rebirth screen check: strict_black=%.2f dark=%.2f low_sat=%.2f mean_v=%.1f hit=%s",
            black_ratio_strict, dark_ratio, low_sat_ratio, mean_v, hit,
        )
        return hit
    except Exception as e:
        log.warning(f"is_rebirth_screen() failed: {e}")
        return False

# ── Menu OCR helpers ─────────────────────────────────────────

def _preprocess_menu(img) -> 'np.ndarray':
    """Upscale + threshold for menu text (PLAY button — bright yellow on dark).

    Uses OTSU thresholding. The result may need inversion depending on whether
    Tesseract expects dark-on-light or light-on-dark.
    """
    scale = 3
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _preprocess_bramble_mode(img) -> 'np.ndarray':
    """Bramble INFO-card subtitle (Easy / Normal / Hard / Ex).

    The word sits under the boss name as dim gray (~30) on a ~22 card.
    Percentile-stretch + CLAHE so Tesseract sees dark text on white.
    """
    scale = 4
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lo, hi = np.percentile(gray, (5, 99.5))
    if float(hi) <= float(lo) + 1.0:
        hi = float(lo) + 1.0
    stretched = np.clip(
        (gray.astype(np.float32) - float(lo)) * (255.0 / (float(hi) - float(lo))),
        0, 255,
    ).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    boosted = clahe.apply(stretched)
    _, thresh = cv2.threshold(boosted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if float(np.mean(thresh)) < 127.0:
        thresh = cv2.bitwise_not(thresh)
    return thresh


def _preprocess_privacy(img) -> 'np.ndarray':
    """Upscale + threshold for the privacy button text ("Private" / "Public").

    The privacy button has light grey/white text on a dark blue-grey background.
    Tesseract needs dark text on white background → invert after thresholding.
    Uses a fixed threshold (180) instead of OTSU to avoid unpredictable
    inversion on dark-dominated regions.
    """
    scale = 4   # extra upscale for small text
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Fixed threshold: pixels brighter than 160 → white (text), rest → black
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    # Invert: text goes dark on white background for Tesseract
    thresh = cv2.bitwise_not(thresh)
    return thresh



def _play_color_hit(img) -> bool:
    """Return True if the PLAY button region contains enough yellow pixels."""
    pct = color_match_percent(
        img,
        target_hsv=_cfg.MENU_PLAY_HSV_TARGET,
        hue_tol=_cfg.MENU_PLAY_HUE_TOL,
        sat_tol=_cfg.MENU_PLAY_SAT_TOL,
        val_tol=_cfg.MENU_PLAY_VAL_TOL,
    )
    log.debug(f"[MENU] PLAY color pct={pct:.3f} (need>={_cfg.MENU_PLAY_COLOR_THRESH})")
    return pct >= _cfg.MENU_PLAY_COLOR_THRESH


def _find_play_button_region() -> tuple[int, int, int, int] | None:
    """Find the lobby PLAY button by yellow fill instead of fixed coordinates."""
    try:
        img = grab_full_screen()
        h, w = img.shape[:2]
        y1 = int(h * 0.42)
        y2 = h
        x1 = 0
        x2 = int(w * 0.62)
        crop = img[y1:y2, x1:x2]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 120, 170], dtype=np.uint8),
            np.array([40, 255, 255], dtype=np.uint8),
        )
        yellow = cv2.morphologyEx(yellow, cv2.MORPH_CLOSE, np.ones((9, 21), dtype=np.uint8))
        contours, _ = cv2.findContours(yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for contour in contours:
            bx, by, bw, bh = cv2.boundingRect(contour)
            area = bw * bh
            if area < max(1800, int(w * h * 0.0012)):
                continue
            if bw < int(w * 0.06) or bh < int(h * 0.035):
                continue
            aspect = bw / float(max(1, bh))
            if aspect < 1.8 or aspect > 8.0:
                continue
            abs_x1, abs_y1 = x1 + bx, y1 + by
            abs_x2, abs_y2 = abs_x1 + bw, abs_y1 + bh
            # Lobby PLAY is normally the large yellow call-to-action in the
            # lower-left area; prefer wider/lower candidates.
            score = area + (abs_y1 * 3) - abs_x1
            candidates.append((score, (abs_x1, abs_y1, abs_x2, abs_y2)))
        if not candidates:
            return None
        candidates.sort(reverse=True, key=lambda item: item[0])
        rx1, ry1, rx2, ry2 = candidates[0][1]
        pad_x = max(8, int((rx2 - rx1) * 0.08))
        pad_y = max(5, int((ry2 - ry1) * 0.18))
        region = (
            max(0, rx1 - pad_x),
            max(0, ry1 - pad_y),
            min(w, rx2 + pad_x),
            min(h, ry2 + pad_y),
        )
        log.debug(f"[MENU] dynamic PLAY region={region}")
        return region
    except Exception as e:
        log.debug(f"[MENU] dynamic PLAY search failed: {e}")
        return None


def get_menu_play_center() -> tuple[int, int]:
    """Return current PLAY center, preferring dynamic yellow-button detection."""
    global _last_menu_play_region
    region = _find_play_button_region() or _last_menu_play_region or _cfg.MENU_PLAY_REGION
    _last_menu_play_region = region
    return (int((region[0] + region[2]) // 2), int((region[1] + region[3]) // 2))


def _ocr_play_once() -> tuple:
    """Single pass: grab PLAY region, run color check + OCR.

    Returns (hit, color_hit, ocr_hit, raw, text, img, proc).
    hit = True if EITHER color OR OCR confirms PLAY.
    """
    import re as _re
    global _last_menu_play_region
    region = _find_play_button_region() or _cfg.MENU_PLAY_REGION
    _last_menu_play_region = region
    img  = grab_region(region)
    proc = _preprocess_menu(img)
    raw  = pytesseract.image_to_string(
        proc,
        config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    )
    text = raw.strip().upper()
    ocr_hit = bool(
        "PLAY" in text or
        _re.search(r"P[A-Z]AY", text) or
        _re.search(r"PL[A-Z]Y", text) or
        _re.search(r"PLA[A-Z]", text) or
        _re.search(r"\bPAY\b", text) or
        _re.search(r"\bPLY\b", text) or
        _re.search(r"\bPLA\b", text) or
        _re.search(r"\bLAY\b", text)
    )
    color_hit = _play_color_hit(img)
    hit = ocr_hit or color_hit
    return hit, color_hit, ocr_hit, raw, text, img, proc


def read_bramble_mode_text() -> str:
    """OCR the boss-fight mode name (SOLO / NORMAL / HARD / EX).

    Crop is BRAMBLE_MODE_REGION (scaled) — the subtitle under the boss
    name on the left INFO card, not the center Queued Players panel.
    Returns uppercase stripped text, empty string on failure.
    """
    try:
        region = tuple(int(v) for v in getattr(_cfg, "BRAMBLE_MODE_REGION", (182, 270, 701, 331)))
        img = grab_region(region)
        if img is None or img.size == 0:
            return ""
        proc = _preprocess_bramble_mode(img)
        raw = pytesseract.image_to_string(
            proc,
            config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )
        text = raw.strip().upper()
        safe = re.sub(r"[^A-Z0-9]+", "_", text)[:24] or "empty"
        _save_debug(f"bramble_mode_{safe}", img, proc)
        log.debug(f"[BRAMBLE] mode OCR raw={raw.strip()!r} -> {text!r}")
        return text
    except Exception as e:
        log.warning(f"[BRAMBLE] mode OCR failed: {e}")
        return ""


def bramble_mode_matches(ocr_text: str, aliases) -> bool:
    """True if OCR text contains any alias (spaces/punctuation ignored)."""
    t = re.sub(r"[^A-Z0-9]", "", str(ocr_text or "").upper())
    if not t:
        return False
    for item in (aliases or []):
        n = re.sub(r"[^A-Z0-9]", "", str(item or "").upper())
        if n and (n in t or t in n):
            return True
    return False

def is_in_menu() -> bool:
    """Return True if the Fortnite main menu PLAY button is visible via OCR.

    Runs 10 OCR passes, 0.1 s apart. Returns True as soon as 3 hits
    accumulate (>=30%). Lenient threshold + dropped-char patterns cover
    reads like PAY (L missing), PLY (A missing), LAY (P missing) as well
    as substitution misreads like PUAY, PIAY.
    """
    try:
        hits = 0
        PASSES    = 8
        THRESHOLD = 2
        for attempt in range(PASSES):
            if attempt > 0:
                time.sleep(0.08)
            hit, color_hit, ocr_hit, raw, text, img, proc = _ocr_play_once()
            if hit:
                hits += 1
            safe_text = text[:20].replace(" ", "_").replace("/", "")
            log.debug(f"[MENU] is_in_menu pass {attempt+1}/{PASSES} raw: {raw.strip()!r}  -> {text!r}  ocr={ocr_hit}  color={color_hit}  hit={hit}  hits={hits}")
            _save_debug(f"menu_play_p{attempt+1}_{'ok' if hit else 'fail'}_{safe_text}", img, proc)
            if hits >= THRESHOLD:
                log.debug(f"[MENU] is_in_menu -> True ({hits}+ hits after {attempt+1} passes)")
                return True
        log.debug(f"[MENU] is_in_menu -> False ({hits}/{PASSES} hits)")
        return False
    except Exception as e:
        log.warning(f"is_in_menu() failed: {e}")
        return False

def _ocr_privacy_once() -> tuple:
    """Single OCR pass for privacy button. Returns (result: str, raw, text, img, proc).

    Uses _preprocess_privacy (fixed threshold + invert) instead of the OTSU
    _preprocess_menu — OTSU was unpredictable on the dark blue-grey background
    and produced empty strings or garbage like 'sew'.
    """
    img  = grab_region(_cfg.MENU_PRIVACY_REGION)
    proc = _preprocess_privacy(img)
    raw  = pytesseract.image_to_string(
        proc,
        config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
    )
    text = raw.strip().upper()
    if "PRIV" in text:
        result = "PRIVATE"
    elif "PUB" in text:
        result = "PUBLIC"
    else:
        result = "NONE"
    return result, raw, text, img, proc


def read_privacy_state() -> 'str | None':
    """Return "PRIVATE", "PUBLIC", or None if unreadable.

    Runs 10 OCR passes, 0.1 s apart. Returns whichever state first
    reaches 3 votes (>=30%). If none reaches threshold, returns best or None.
    """
    try:
        votes = {"PRIVATE": 0, "PUBLIC": 0, "NONE": 0}
        PASSES    = 8
        THRESHOLD = 2
        for attempt in range(PASSES):
            if attempt > 0:
                time.sleep(0.08)
            result, raw, text, img, proc = _ocr_privacy_once()
            votes[result] += 1
            safe_text = text[:20].replace(" ", "_").replace("/", "")
            log.debug(f"[MENU] read_privacy_state pass {attempt+1}/{PASSES} raw: {raw.strip()!r}  -> {text!r}  -> {result}  votes={dict(votes)}")
            _save_debug(f"menu_privacy_p{attempt+1}_{result}_{safe_text}", img, proc)
            if votes["PRIVATE"] >= THRESHOLD:
                log.debug(f"[MENU] read_privacy_state -> PRIVATE (votes={votes})")
                return "PRIVATE"
            if votes["PUBLIC"] >= THRESHOLD:
                log.debug(f"[MENU] read_privacy_state -> PUBLIC (votes={votes})")
                return "PUBLIC"
        best = max(votes, key=lambda k: votes[k])
        final = None if best == "NONE" else best
        log.debug(f"[MENU] read_privacy_state -> {final!r} (votes={votes})")
        return final
    except Exception as e:
        log.warning(f"read_privacy_state() failed: {e}")
        return None
