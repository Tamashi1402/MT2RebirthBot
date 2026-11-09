"""Pick-metadata for image-block crops (point + box), embedded in the PNG.

When an image is picked from the screen with the pipette (F2 → drag a
region → crop saved), the dragged region's coordinates are embedded
INSIDE the saved PNG as a tEXt chunk (keyword "mfmeta"):

    {"box": [x1, y1, x2, y2],   # the dragged region, screen px
     "point": [x1, y1],         # top-left corner
     "screen": [w, h],          # screen res at pick time
     "ts": 1700000000}

One PNG file carries its own origin — no <image>.meta.json sidecar
scattered next to it, so packing a macro (zip-style .macro container,
image attached to an email, copy/paste of a single file) never loses
the "where did I pick this from" data.

Old sidecars (<image>.meta.json from earlier versions) are still read
back if the PNG has no embedded chunk. write_meta() embeds into the
PNG and only falls back to a sidecar when the file is not a PNG.

The image block's "get" icon reads this back and drops a point block
and a box block with these coordinates into the editor.
"""
import json
import os
import struct
import time
import zlib

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_KEYWORD = b"mfmeta"          # PNG tEXt keyword carrying the metadata
_KEYWORD_SFX = ".meta.json"   # legacy sidecar suffix


# ── PNG chunk codec (pure python — no PIL dependency) ─────────────

def _iter_chunks(raw):
    """Yield (start_offset, type, payload) for every chunk. Raises on
    signature/CRC/truncation errors — a half-written PNG must never be
    silently rewritten."""
    if len(raw) < 8 or raw[:8] != _PNG_SIG:
        raise ValueError("not a png")
    pos = 8
    n = len(raw)
    while pos + 8 <= n:
        (length,) = struct.unpack(">I", raw[pos:pos + 4])
        ctype = raw[pos + 4:pos + 8]
        end = pos + 8 + length
        if end + 4 > n:
            raise ValueError("truncated png chunk")
        payload = raw[pos + 8:end]
        (crc,) = struct.unpack(">I", raw[end:end + 4])
        if zlib.crc32(ctype + payload) & 0xFFFFFFFF != crc:
            raise ValueError("png crc mismatch")
        yield pos, ctype, payload
        pos = end + 4


def _text_chunk(data_dict):
    """Build an mfmeta tEXt chunk (keyword + NUL + JSON)."""
    text = json.dumps(data_dict, ensure_ascii=True, separators=(",", ":"))
    payload = _KEYWORD + b"\x00" + text.encode("ascii")
    return (struct.pack(">I", len(payload)) + b"tEXt" + payload +
            struct.pack(">I", zlib.crc32(b"tEXt" + payload) & 0xFFFFFFFF))


def _read_png_text(path, keyword=_KEYWORD):
    """Return the text of the first tEXt chunk matching `keyword`, else None."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
        for _, ctype, payload in _iter_chunks(raw):
            if ctype != b"tEXt":
                continue
            nul = payload.find(b"\x00")
            if nul <= 0 or payload[:nul] != keyword:
                continue
            return payload[nul + 1:].decode("ascii", "replace")
        return None
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        return None


def _write_png_text(path, data_dict):
    """Embed/replace the mfmeta tEXt chunk, keeping every other chunk
    byte-for-byte. Atomic — writes a temp file then os.replace()."""
    with open(path, "rb") as f:
        raw = f.read()
    chunks = [(ctype, payload) for _, ctype, payload in _iter_chunks(raw)]
    new = bytearray(raw[:8])
    tEXt = _text_chunk(data_dict)
    wrote_ihdr = False
    for ctype, payload in chunks:
        # drop any previous mfmeta tEXt — the new one replaces it
        if ctype == b"tEXt":
            nul = payload.find(b"\x00")
            if nul > 0 and payload[:nul] == _KEYWORD:
                continue
        new += (struct.pack(">I", len(payload)) + ctype + payload +
                struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF))
        if ctype == b"IHDR":
            wrote_ihdr = True
            new += tEXt   # metadata goes right after IHDR
    if not wrote_ihdr:
        raise ValueError("png has no IHDR")
    tmp = str(path) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(new)
    os.replace(tmp, str(path))


def _valid_meta(d):
    """Shape check: {"box": [x1,y1,x2,y2], ...} with real numbers."""
    if not isinstance(d, dict):
        return False
    box = d.get("box")
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return False
    try:
        [float(v) for v in box]
    except (TypeError, ValueError):
        return False
    return True


def _normalize(box, screen=None):
    try:
        x1, y1, x2, y2 = (int(round(float(v))) for v in box)
    except Exception:
        return None
    return {
        "box": [x1, y1, x2, y2],
        "point": [x1, y1],
        "screen": [int(s) for s in (screen or []) if str(s).strip().isdigit()][:2],
        "ts": int(time.time()),
    }


def write_meta(image_path, box, screen=None):
    """Embed the pick metadata in the PNG itself (mfmeta tEXt chunk).
    Best effort — never raises: a failed embed must not break the crop.
    Falls back to the legacy sidecar only when the target is not a PNG.
    Returns the metadata dict, or None when nothing could be written."""
    data = _normalize(box, screen)
    if not data:
        return None
    path = str(image_path)
    is_png = os.path.isfile(path) and path.lower().endswith(".png")
    if is_png:
        try:
            _write_png_text(path, data)
            return data
        except (ValueError, OSError):
            pass
    try:
        with open(path + _KEYWORD_SFX, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data
    except Exception:
        return None


def read_meta(image_path):
    """Read pick metadata: PNG-embedded chunk first, legacy sidecar second.
    None when missing or broken."""
    path = str(image_path)
    if path.lower().endswith(".png"):
        text = _read_png_text(path)
        if text:
            try:
                d = json.loads(text)
                if _valid_meta(d):
                    return d
            except (ValueError, TypeError):
                pass
    p = path + _KEYWORD_SFX
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            if _valid_meta(d):
                return d
        except Exception:
            pass
    return None
