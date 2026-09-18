"""Macro Engine (no-preset edition)

Key changes vs old version:
- No preset system.  Macros live flat in <BOT_ROOT>/macros/ by default.
- "Open" button lets the user pick ANY .macro file from disk.
- "Save" writes back to the file that is currently open.
- "Save As" lets the user choose a new location.
- "Import" lets the user open and immediately edit a .macro from anywhere.
- Macro list is populated from the flat macros/ folder.
- F6 = toggle play / HARD stop (releases all held keys immediately).
"""

import json
import ctypes
import ctypes.wintypes
import atexit
import base64
import logging
import os
import subprocess
import sys
import threading
import time
import re
import urllib.parse
import urllib.request

from flask import Blueprint, Flask, jsonify, render_template, request
from werkzeug.serving import WSGIRequestHandler

try:
    from .macro_engine import MacroEngine, Sensitivity
    from .overlay import MacroOverlay
    from .smooth_move import SmoothMoveTracker
except ImportError:
    from macro_engine import MacroEngine, Sensitivity
    from overlay import MacroOverlay
    from smooth_move import SmoothMoveTracker

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, "frozen", False):
    BOT_ROOT = os.path.dirname(sys.executable)
else:
    _code_dir = os.path.dirname(ROOT)
    BOT_ROOT = (
        os.path.dirname(_code_dir)
        if os.path.basename(_code_dir).lower() == "code"
        else _code_dir
    )

MACROS_DIR = os.path.join(BOT_ROOT, "macros")
DATA_DIR = os.path.join(BOT_ROOT, "data")
MACRO_IMAGES_DIR = os.path.join(MACROS_DIR, "images")
LEGACY_MACRO_IMAGES_DIR = os.path.join(DATA_DIR, "macro_images")
STATE_PATH = os.path.join(DATA_DIR, "macro_engine_state.json")
LEGACY_STATE_PATH = os.path.join(BOT_ROOT, "macro_engine_state.json")

os.makedirs(MACROS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MACRO_IMAGES_DIR, exist_ok=True)
if (not os.path.exists(STATE_PATH)) and os.path.exists(LEGACY_STATE_PATH):
    try:
        os.replace(LEGACY_STATE_PATH, STATE_PATH)
    except Exception:
        try:
            with open(LEGACY_STATE_PATH, "rb") as _src, open(STATE_PATH, "wb") as _dst:
                _dst.write(_src.read())
        except Exception:
            pass

# ── App / engine / overlay ───────────────────────────────────────────────────

overlay = MacroOverlay()
engine  = MacroEngine(MACROS_DIR, on_state=overlay.update)
log = logging.getLogger("macro_engine_app")
logging.getLogger("werkzeug").disabled = True
WSGIRequestHandler.log = lambda self, type, message, *args: None

bp = Blueprint(
    "macro_engine",
    __name__,
    template_folder=os.path.join(ROOT, "templates"),
    static_folder=os.path.join(ROOT, "static"),
    url_prefix="/me",
)
# Standalone Flask kept only so `python macro_engine/app.py` still works.
# Blueprint is registered in attach_macro_engine() / __main__, never at import,
# so the same Blueprint object can mount on the bot dashboard app.
app = Flask(__name__)



# ── State ────────────────────────────────────────────────────────────────────
# current_path  = absolute path of the macro file that is open in the editor
# current_macro = display name (basename without .macro)

current_path:  str = ""
current_macro: str = ""
record_binding: str = "F5"
play_binding: str = "F6"
smooth_binding: str = "L"
_smooth_move = {"seq": 0, "x": 0, "y": 0, "elapsed_ms": 0}
smooth_tracker = SmoothMoveTracker()


def _smooth_move_result_cb(x: int, y: int, elapsed_ms: int) -> None:
    """Called by the smooth-move tracker when the hold key is released.

    The tracker reports raw mouse counts captured at the user's CURRENT
    in-game sensitivity. A SMOOTH_MOVE block replays scaled by
    recorded/user, so to behave exactly like a value recorded into the
    open macro, the raw count must be converted the other way:
    value = raw * user / recorded  (= raw / ratios()). X uses the H
    sensitivity pair, Y the V pair.
    """
    try:
        x = int(x)
        y = int(y)
    except Exception:
        return
    try:
        rx, ry = engine.sensitivity.ratios()  # recorded / user
        if rx > 0:
            x = int(round(x / rx))
        if ry > 0:
            y = int(round(y / ry))
    except Exception:
        pass
    log.info(f"[SmoothMove] captured -> block value ({x}, {y})")
    with _state_lock:
        _smooth_move["x"] = x
        _smooth_move["y"] = y
        _smooth_move["elapsed_ms"] = int(elapsed_ms)
        _smooth_move["seq"] = int(_smooth_move.get("seq", 0)) + 1


def _smooth_is_busy() -> bool:
    try:
        return bool(engine.is_recording() or engine.is_running())
    except Exception:
        return False


def _restart_smooth_tracker() -> None:
    try:
        smooth_tracker.start(
            _binding_to_vk(smooth_binding, "L"),
            _smooth_is_busy,
            _smooth_move_result_cb,
        )
    except Exception as e:
        log.warning(f"[SmoothMove] tracker start failed: {e}")


def _stop_smooth_tracker() -> None:
    try:
        smooth_tracker.stop()
    except Exception:
        pass
playback_repeat: int = 1
playback_times: int = 5
_last_f6_toggle_ts = 0.0
_last_f5_toggle_ts = 0.0
_state_lock = threading.Lock()
_recording_sensitivity: dict = {}
_record_locked_blocks: list[dict] = []


def _current_locked_blocks() -> list[dict]:
    """Locked blocks of the macro file currently on disk (they survive re-recording)."""
    try:
        if current_path and os.path.isfile(current_path):
            with open(current_path, "r", encoding="utf-8", errors="replace") as f:
                parsed = _parse_macro_text(f.read())
            return [dict(b) for b in parsed.get("blocks", []) if b.get("locked")]
    except Exception:
        pass
    return []
_webview_process: subprocess.Popen | None = None
_hotkey_thread = None
_picker_wait_lock = threading.Lock()
_picker_wait_token = 0

_BINDING_VK = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46,
    "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52,
    "S": 0x53, "T": 0x54, "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A, "SPACE": 0x20,
}


def _binding_to_vk(binding: str, fallback: str) -> int:
    value = str(binding or fallback).strip().upper().replace(" ", "_")
    if value.startswith("0X"):
        try:
            return int(value, 16)
        except Exception:
            pass
    return _BINDING_VK.get(value, _BINDING_VK[fallback])


def _repeat_value(value, fallback: int = 1) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return max(0, int(fallback))


def _times_value(value, fallback: int = 5) -> int:
    try:
        return max(1, int(value))
    except Exception:
        return max(1, int(fallback))


def _restart_hotkeys() -> None:
    global _hotkey_thread
    try:
        engine.stop_hotkeys()
    except Exception:
        pass
    if not _recorder_tab_open:
        _hotkey_thread = None
        _stop_smooth_tracker()
        return
    _hotkey_thread = engine.start_hotkeys(
        _toggle_f6,
        _toggle_f5,
        play_vk=_binding_to_vk(play_binding, "F6"),
        record_vk=_binding_to_vk(record_binding, "F5"),
    )
    engine._set_state(play_binding=play_binding, record_binding=record_binding)
    _restart_smooth_tracker()


def apply_recorder_bindings_from_config() -> None:
    """Use the bot Config panel F5/F6/L bindings for Recorder."""
    global record_binding, play_binding, smooth_binding
    try:
        import config as _cfg
        rec = str(getattr(_cfg, "RECORDER_RECORD_BINDING", record_binding) or "F5").strip().upper() or "F5"
        play = str(getattr(_cfg, "RECORDER_PLAY_BINDING", play_binding) or "F6").strip().upper() or "F6"
        smooth = str(getattr(_cfg, "RECORDER_SMOOTH_MOVE_KEY", smooth_binding) or "L").strip().upper() or "L"
    except Exception:
        rec, play, smooth = "F5", "F6", "L"
    record_binding = rec
    play_binding = play
    smooth_binding = smooth
    try:
        engine._set_state(play_binding=play_binding, record_binding=record_binding)
    except Exception:
        pass
    if _recorder_tab_open:
        _restart_hotkeys()
    _save_state()


def _macro_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _macro_dir_for_images() -> str:
    os.makedirs(MACRO_IMAGES_DIR, exist_ok=True)
    return MACRO_IMAGES_DIR


def _image_rel_path(path: str) -> str:
    path = os.path.abspath(path)
    images_dir = os.path.abspath(MACRO_IMAGES_DIR)
    try:
        rel = os.path.relpath(path, images_dir).replace("\\", "/")
        if not rel.startswith("../") and rel != "..":
            return f"images/{rel}"
    except Exception:
        pass
    try:
        return os.path.relpath(path, BOT_ROOT).replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def _normalize_save_path(path: str, name: str) -> str:
    path = str(path or "").strip().strip('"')
    name = str(name or "").strip() or "macro"
    if not path:
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ")).strip() or "macro"
        path = os.path.join(MACROS_DIR, safe + ".macro")
    root, ext = os.path.splitext(path)
    if ext == "":
        path = path + ".macro"
    return os.path.abspath(path)


def _load_state() -> None:
    global current_path, current_macro, record_binding, play_binding, playback_repeat, playback_times
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        p = str(data.get("path", "")).strip()
        if p and os.path.isfile(p):
            current_path  = p
            current_macro = os.path.splitext(os.path.basename(p))[0]
        record_binding = str(data.get("record_binding", record_binding) or "F5").strip().upper()
        play_binding = str(data.get("play_binding", play_binding) or "F6").strip().upper()
        playback_repeat = _repeat_value(data.get("playback_repeat", playback_repeat), playback_repeat)
        playback_times = _times_value(data.get("playback_times", playback_times if playback_repeat <= 1 else playback_repeat), playback_times)
        if playback_repeat > 1:
            playback_times = playback_repeat
        if isinstance(data.get("sensitivity"), dict):
            try:
                _set_engine_sens(data["sensitivity"])
            except Exception:
                pass
    except Exception:
        pass
    apply_recorder_bindings_from_config()


def _save_state() -> None:
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "path": current_path,
                "macro": current_macro,
                "record_binding": record_binding,
                "play_binding": play_binding,
                "playback_repeat": playback_repeat,
                "playback_times": playback_times,
                "sensitivity": _engine_sensitivity_dict(),
            }, f, indent=2)
    except Exception:
        pass


# ── Macro list ───────────────────────────────────────────────────────────────

def _list_macros() -> list[dict]:
    """Return [{name, path, rel, folder}] for every .macro under MACROS_DIR."""
    out = []
    skip_dirs = {"images", "__pycache__", ".git"}
    try:
        for root, dirs, files in os.walk(MACROS_DIR):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fn in files:
                if not fn.lower().endswith(".macro"):
                    continue
                full = os.path.abspath(os.path.join(root, fn))
                rel = os.path.relpath(full, MACROS_DIR).replace("\\", "/")
                if rel.lower().endswith(".macro"):
                    rel_key = rel[:-6]
                else:
                    rel_key = rel
                out.append({
                    "name": os.path.splitext(fn)[0],
                    "rel": rel_key,
                    "folder": os.path.dirname(rel).replace("\\", "/"),
                    "path": full,
                })
        out.sort(key=lambda m: str(m.get("rel") or "").lower())
    except Exception:
        pass
    return out


def _drive_roots() -> list[str]:
    if os.name == "nt":
        return [f"{chr(c)}:\\" for c in range(ord("A"), ord("Z") + 1) if os.path.exists(f"{chr(c)}:\\")]
    return ["/"]


def _list_directory(path: str) -> dict:
    path = os.path.abspath(str(path or "").strip().strip('"') or MACROS_DIR)
    if not os.path.isdir(path):
        path = os.path.dirname(path) if path else MACROS_DIR
    if not os.path.isdir(path):
        path = MACROS_DIR

    entries = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    is_dir = entry.is_dir()
                    is_macro = entry.is_file() and entry.name.lower().endswith(".macro")
                    if not is_dir and not is_macro:
                        continue
                    entries.append({
                        "name": entry.name,
                        "path": os.path.abspath(entry.path),
                        "is_dir": is_dir,
                        "is_macro": is_macro,
                    })
                except Exception:
                    continue
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "path": path,
            "parent": os.path.dirname(path),
            "roots": _drive_roots(),
            "entries": [],
        }

    entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    parent = os.path.dirname(path.rstrip("\\/"))
    if parent == path:
        parent = ""
    return {
        "ok": True,
        "path": path,
        "parent": parent,
        "roots": _drive_roots(),
        "entries": entries,
    }


# ── Macro text helpers ───────────────────────────────────────────────────────

def _parse_macro_text(text: str) -> dict:
    meta   = {}
    blocks = []
    locked_indices: set[int] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# LOCKED:"):
            for part in line.split(":", 1)[1].split(","):
                part = part.strip()
                if part.isdigit():
                    locked_indices.add(int(part))
            continue
        if line.startswith("# SENS_"):
            try:
                k, v = line[2:].split(":", 1)
                meta[k.strip()] = float(v.strip())
            except Exception:
                pass
            continue
        if line.startswith("#"):
            continue
        t, _, rest = line.partition(":")
        btype = t.strip()
        val = rest.strip()
        if btype in ("SMOOTH_MOVE", "LOOK"):
            parts = [p.strip() for p in val.split(",")]
            if len(parts) >= 3:
                val = f"{parts[0]},{parts[1]},{parts[2]}"
            elif len(parts) >= 2:
                val = f"{parts[0]},{parts[1]}"
        blocks.append({"type": btype, "value": val})
    for idx in locked_indices:
        if 0 <= idx < len(blocks):
            blocks[idx]["locked"] = True
    return {"meta": meta, "blocks": blocks}


def _normalize_blocks(blocks: list[dict]) -> list[dict]:
    normalized = []
    for block in blocks or []:
        btype = str(block.get("type", "")).strip()
        val = str(block.get("value", "")).strip()
        if not btype:
            continue
        if btype in ("SMOOTH_MOVE", "LOOK"):
            parts = [p.strip() for p in val.split(",")]
            if len(parts) >= 3:
                val = f"{parts[0]},{parts[1]},{parts[2]}"
            elif len(parts) >= 2:
                val = f"{parts[0]},{parts[1]}"
        elif btype == "DELAY":
            try:
                val = str(max(0, int(float(val or 0))))
            except Exception:
                val = "0"
        normalized.append({"type": btype, "value": val, "locked": bool(block.get("locked"))})
    return normalized


def _normalize_sensitivity(sensitivity: dict) -> dict:
    out = {}
    for key in ("SENS_RECORDED_H", "SENS_RECORDED_V", "SENS_USER_H", "SENS_USER_V"):
        try:
            out[key] = float(sensitivity.get(key, 17.0))
        except Exception:
            out[key] = 17.0
    return out


def _build_macro_text(name: str, sensitivity: dict, blocks: list[dict]) -> str:
    lines = [f"# Macro: {name}"]
    sensitivity = _normalize_sensitivity(sensitivity)
    blocks = _normalize_blocks(blocks)
    for key in ("SENS_RECORDED_H", "SENS_RECORDED_V", "SENS_USER_H", "SENS_USER_V"):
        lines.append(f"# {key}:{sensitivity[key]}")
    locked = [str(i) for i, b in enumerate(blocks) if b.get("locked")]
    if locked:
        lines.append(f"# LOCKED:{','.join(locked)}")
    for block in blocks:
        btype = str(block.get("type", "")).strip()
        val   = str(block.get("value", "")).strip()
        if not btype:
            continue
        lines.append(f"{btype}:{val}" if val else btype)
    return "\n".join(lines) + "\n"


def _write_macro_atomic(path: str, text: str) -> None:
    folder = os.path.dirname(path) or MACROS_DIR
    os.makedirs(folder, exist_ok=True)
    tmp_path = os.path.join(folder, f".{os.path.basename(path)}.{os.getpid()}.tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _save_macro_file(path: str, name: str, blocks: list[dict], sensitivity: dict) -> dict:
    global current_path, current_macro
    path = _normalize_save_path(path, name)
    name = str(name or _macro_name_from_path(path) or "macro").strip() or "macro"
    sensitivity = _normalize_sensitivity(sensitivity)
    blocks = _normalize_blocks(blocks)
    text = _build_macro_text(name, sensitivity, blocks)
    _write_macro_atomic(path, text)

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        saved_text = f.read()
    parsed = _parse_macro_text(saved_text)

    current_path = path
    current_macro = _macro_name_from_path(path)
    _set_engine_sens(parsed["meta"] or sensitivity)
    _save_state()
    return {
        "ok": True,
        "path": current_path,
        "name": current_macro,
        "blocks": parsed["blocks"],
        "meta": parsed["meta"],
        "block_count": len(parsed["blocks"]),
    }


def _bot_user_sensitivity() -> dict:
    """Live Fortnite mouse sensitivity from the bot's shared Config panel."""
    try:
        import config as _cfg
        uh = float(getattr(_cfg, "USER_SENS_H", 17.0) or 17.0)
        uv = float(getattr(_cfg, "USER_SENS_V", 17.0) or 17.0)
    except Exception:
        uh, uv = 17.0, 17.0
    return {"SENS_USER_H": uh, "SENS_USER_V": uv}


def _apply_bot_user_sensitivity() -> dict:
    user = _bot_user_sensitivity()
    current = _engine_sensitivity_dict()
    merged = {**current, **user}
    _set_engine_sens(merged)
    return merged


def _set_engine_sens(sensitivity: dict) -> None:
    engine.sensitivity = Sensitivity(
        recorded_h=float(sensitivity.get("SENS_RECORDED_H", 17.0)),
        recorded_v=float(sensitivity.get("SENS_RECORDED_V", 17.0)),
        user_h=float(sensitivity.get("SENS_USER_H",    17.0)),
        user_v=float(sensitivity.get("SENS_USER_V",    17.0)),
    )


def _set_engine_recorded_sens(sensitivity: dict) -> None:
    user = _bot_user_sensitivity()
    engine.sensitivity = Sensitivity(
        recorded_h=float(sensitivity.get("SENS_RECORDED_H", 17.0)),
        recorded_v=float(sensitivity.get("SENS_RECORDED_V", 17.0)),
        user_h=user["SENS_USER_H"],
        user_v=user["SENS_USER_V"],
    )


def _recording_header_sensitivity(sensitivity: dict) -> dict:
    s = _normalize_sensitivity(sensitivity)
    return {
        "SENS_RECORDED_H": s["SENS_USER_H"],
        "SENS_RECORDED_V": s["SENS_USER_V"],
        "SENS_USER_H": s["SENS_USER_H"],
        "SENS_USER_V": s["SENS_USER_V"],
    }


def _engine_sensitivity_dict() -> dict:
    return {
        "SENS_RECORDED_H": engine.sensitivity.recorded_h,
        "SENS_RECORDED_V": engine.sensitivity.recorded_v,
        "SENS_USER_H": engine.sensitivity.user_h,
        "SENS_USER_V": engine.sensitivity.user_v,
    }


def _macro_meta_for_path(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return _parse_macro_text(f.read())["meta"]
    except Exception:
        return {}


def _sensitivity_override(data: dict | None, path: str = "") -> Sensitivity | None:
    file_meta = _normalize_sensitivity(_macro_meta_for_path(path)) if path else _engine_sensitivity_dict()
    user = _bot_user_sensitivity()
    return Sensitivity(
        recorded_h=file_meta["SENS_RECORDED_H"],
        recorded_v=file_meta["SENS_RECORDED_V"],
        user_h=user["SENS_USER_H"],
        user_v=user["SENS_USER_V"],
    )


def _minimize_webview_window() -> None:
    if os.name != "nt":
        return
    try:
        SW_MINIMIZE = 6
        hwnd = ctypes.windll.user32.FindWindowW(None, "Macro Engine")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
    except Exception:
        pass


def _next_picker_wait_token() -> int:
    global _picker_wait_token
    with _picker_wait_lock:
        _picker_wait_token += 1
        return _picker_wait_token


def _picker_wait_token_active(token: int) -> bool:
    with _picker_wait_lock:
        return token == _picker_wait_token


def _sanitize_region(values) -> tuple[int, int, int, int] | None:
    try:
        x1, y1, x2, y2 = [int(round(float(v))) for v in values]
    except Exception:
        return None
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _wait_for_f2_sample(timeout_s: float = 60.0, token: int | None = None) -> tuple[int, int] | None:
    if os.name != "nt":
        return None
    user32 = ctypes.windll.user32
    user32.GetCursorPos.argtypes = [ctypes.POINTER(ctypes.wintypes.POINT)]
    user32.GetCursorPos.restype = ctypes.wintypes.BOOL
    VK_F2 = 0x71
    deadline = time.time() + max(1.0, float(timeout_s))
    while time.time() < deadline and (token is None or _picker_wait_token_active(token)) and (user32.GetAsyncKeyState(VK_F2) & 0x8000):
        time.sleep(0.02)
    while time.time() < deadline and (token is None or _picker_wait_token_active(token)):
        if user32.GetAsyncKeyState(VK_F2) & 0x8000:
            pt = ctypes.wintypes.POINT()
            user32.GetCursorPos(ctypes.pointer(pt))
            while time.time() < deadline and (token is None or _picker_wait_token_active(token)) and (user32.GetAsyncKeyState(VK_F2) & 0x8000):
                time.sleep(0.02)
            return int(pt.x), int(pt.y)
        time.sleep(0.02)
    return None


def _wait_for_f2_region(timeout_s: float = 120.0, token: int | None = None) -> tuple[int, int, int, int] | None:
    first = _wait_for_f2_sample(timeout_s, token)
    if first is None:
        return None
    second = _wait_for_f2_sample(timeout_s, token)
    if second is None:
        return None
    return _sanitize_region((first[0], first[1], second[0], second[1]))


def _screen_size_for_filename() -> tuple[int, int]:
    try:
        import mss
        with mss.mss() as sct:
            mon = sct.monitors[0]
            return int(mon["width"]), int(mon["height"])
    except Exception:
        return 1920, 1080


def _image_filename(name: str = "", base_w: int | None = None, base_h: int | None = None) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name or "image")).strip("._") or "image"
    safe_name = re.sub(r"^\d{3,5}x\d{3,5}_", "", safe_name, flags=re.I)
    if not safe_name.lower().endswith(".png"):
        safe_name += ".png"
    if not base_w or not base_h:
        base_w, base_h = _screen_size_for_filename()
    return f"{int(base_w)}x{int(base_h)}_{safe_name}"


def _unique_image_path(images_dir: str, filename: str) -> str:
    root, ext = os.path.splitext(filename)
    path = os.path.join(images_dir, filename)
    suffix = 1
    while os.path.exists(path):
        path = os.path.join(images_dir, f"{root}_{suffix}{ext}")
        suffix += 1
    return path


def _prefix_unversioned_macro_images(images_dir: str) -> int:
    if not os.path.isdir(images_dir):
        return 0
    base_w, base_h = _screen_size_for_filename()
    prefix = f"{base_w}x{base_h}_"
    renamed = 0
    try:
        entries = sorted(os.scandir(images_dir), key=lambda e: e.name.lower())
    except Exception:
        return 0
    for entry in entries:
        if not entry.is_file():
            continue
        name = entry.name
        if not name.lower().endswith(".png"):
            continue
        if re.match(r"^\d{3,5}x\d{3,5}_", name, flags=re.I):
            continue
        target = _unique_image_path(images_dir, prefix + name)
        try:
            os.replace(entry.path, target)
            renamed += 1
        except Exception:
            pass
    return renamed


def _capture_region_png(region: tuple[int, int, int, int], name: str = "", base_w: int | None = None, base_h: int | None = None) -> tuple[str, str]:
    import cv2
    import mss
    import numpy as np

    x1, y1, x2, y2 = region
    images_dir = _macro_dir_for_images()
    path = _unique_image_path(images_dir, _image_filename(name, base_w, base_h))
    with mss.mss() as sct:
        raw = sct.grab({"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1})
        img = np.array(raw)
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    if not cv2.imwrite(path, bgr):
        raise RuntimeError("Could not write image sample.")
    rel = _image_rel_path(path)
    return path, rel


def _save_sample_png_bytes(raw_png: bytes, name: str = "", base_w: int | None = None, base_h: int | None = None) -> tuple[str, str]:
    images_dir = _macro_dir_for_images()
    path = _unique_image_path(images_dir, _image_filename(name, base_w, base_h))
    with open(path, "wb") as f:
        f.write(raw_png)
    rel = _image_rel_path(path)
    return path, rel


def _capture_fullscreen_png() -> dict:
    import cv2
    import mss
    import numpy as np

    with mss.mss() as sct:
        mon = sct.monitors[0]
        raw = sct.grab(mon)
        img = np.array(raw)
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise RuntimeError("Could not encode screenshot.")
    return {
        "left": int(mon.get("left", 0)),
        "top": int(mon.get("top", 0)),
        "width": int(mon["width"]),
        "height": int(mon["height"]),
        "image": base64.b64encode(buf.tobytes()).decode("ascii"),
    }



def _countdown_overlay(mode: str, seconds: int = 3) -> None:
    for value in range(seconds, 0, -1):
        overlay.update({
            "countdown": value,
            "mode": mode,
            "macro": current_macro or "untitled",
            "running": False,
            "recording": False,
            "play_binding": play_binding,
            "record_binding": record_binding,
        })
        time.sleep(1.0)
    overlay.update({"countdown": 0, "mode": mode})


def _start_recording(sensitivity: dict | None = None) -> bool:
    global _recording_sensitivity
    if engine.is_running() or engine.is_recording():
        return False
    sens = _recording_header_sensitivity(_bot_user_sensitivity())
    _recording_sensitivity = sens
    _set_engine_sens(sens)
    macro_name = current_macro or "recorded_macro"
    return engine.start_recording(macro_name, engine.sensitivity)


def _stop_recording_and_save() -> dict:
    global _record_locked_blocks
    blocks = list(_record_locked_blocks) + list(engine.stop_recording() or [])
    _record_locked_blocks = []
    name = current_macro or "recorded_macro"
    path = current_path or _normalize_save_path("", name)
    result = _save_macro_file(path, name, blocks, _recording_sensitivity or _engine_sensitivity_dict())
    prev_version = int(engine.state.get("record_version") or 0)
    engine._set_state(
        macro=result["name"],
        record_path=result["path"],
        record_version=prev_version + 1,
        recording=False,
    )
    return result


def _windows_file_dialog(kind: str, *, initial_path: str = "", suggested_name: str = "") -> tuple[str, str]:
    initial_path = os.path.abspath(initial_path or current_path or MACROS_DIR)
    initial_dir = initial_path if os.path.isdir(initial_path) else os.path.dirname(initial_path)
    env = os.environ.copy()
    env["MACRO_DIALOG_INITIALDIR"] = initial_dir or MACROS_DIR
    env["MACRO_DIALOG_FILENAME"] = suggested_name or os.path.basename(initial_path)
    dialog_class = "SaveFileDialog" if kind == "save" else "OpenFileDialog"
    script = rf"""
Add-Type -AssemblyName System.Windows.Forms
$owner = New-Object System.Windows.Forms.Form
$owner.StartPosition = 'CenterScreen'
$owner.Width = 1
$owner.Height = 1
$owner.Opacity = 0
$owner.ShowInTaskbar = $false
$owner.TopMost = $true
$dlg = New-Object System.Windows.Forms.{dialog_class}
$dlg.Filter = 'Macro files (*.macro)|*.macro|All files (*.*)|*.*'
$dlg.DefaultExt = 'macro'
$dlg.AddExtension = $true
if ($env:MACRO_DIALOG_INITIALDIR -and (Test-Path -LiteralPath $env:MACRO_DIALOG_INITIALDIR)) {{
  $dlg.InitialDirectory = $env:MACRO_DIALOG_INITIALDIR
}}
if ($env:MACRO_DIALOG_FILENAME) {{ $dlg.FileName = $env:MACRO_DIALOG_FILENAME }}
try {{
  $owner.Show()
  $owner.Activate()
  $result = $dlg.ShowDialog($owner)
  if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{ [Console]::Out.Write($dlg.FileName) }}
}} finally {{
  $owner.Close()
  $owner.Dispose()
  $dlg.Dispose()
}}
"""
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        if completed.returncode == 0:
            return completed.stdout.strip().strip('"'), ""
        error = (completed.stderr or completed.stdout or f"PowerShell exited {completed.returncode}").strip()
        log.warning(f"file dialog failed: {error}")
        return "", error
    except Exception as e:
        log.warning(f"file dialog error: {e}")
        return "", str(e)


# ── F6 toggle ────────────────────────────────────────────────────────────────

_recorder_tab_open = False
_hotkey_arm_lock = threading.Lock()


def set_recorder_tab_active(active: bool) -> None:
    """Install F5/F6 only while the dashboard Recorder tab is open.

    Leaving the tab uninstalls the low-level hook so those keys stay
    available to the game / Run panel / Editor.
    """
    global _recorder_tab_open
    want = bool(active)
    with _hotkey_arm_lock:
        if want == _recorder_tab_open:
            return
        _recorder_tab_open = want
        if not _recorder_tab_open:
            try:
                if engine.is_recording():
                    _stop_recording_and_save()
            except Exception:
                pass
            try:
                engine.stop()
            except Exception:
                pass
            try:
                engine.stop_hotkeys()
            except Exception:
                pass
            _stop_smooth_tracker()
        else:
            _apply_bot_user_sensitivity()
            _restart_hotkeys()


def _toggle_f6() -> None:
    global _last_f6_toggle_ts
    if not _recorder_tab_open:
        return
    now = time.time()
    if now - _last_f6_toggle_ts < 0.25:
        return
    _last_f6_toggle_ts = now
    if engine.is_recording():
        return
    if engine.is_running():
        engine.stop()          # instant hard stop + key release already done in engine
        return
    if not current_path or not os.path.isfile(current_path):
        return
    override = _sensitivity_override({
        "SENS_USER_H": engine.sensitivity.user_h,
        "SENS_USER_V": engine.sensitivity.user_v,
    }, current_path)
    engine.play_path_once(current_path, current_macro, playback_repeat, override)


def _toggle_f5() -> None:
    global _last_f5_toggle_ts
    if not _recorder_tab_open:
        return
    now = time.time()
    if now - _last_f5_toggle_ts < 0.25:
        return
    _last_f5_toggle_ts = now
    with _state_lock:
        if engine.is_recording():
            try:
                _stop_recording_and_save()
            except Exception as e:
                log.warning(f"record stop/save failed: {e}")
            return
        global _record_locked_blocks
        _record_locked_blocks = _current_locked_blocks()
        _start_recording()


# ── Flask routes ─────────────────────────────────────────────────────────────



@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/bootstrap")
def bootstrap():
    macros = _list_macros()
    return jsonify({
        "macros_dir": MACROS_DIR,
        "macros":     macros,
        "current_path":  current_path,
        "current_macro": current_macro,
        "record_binding": record_binding,
        "play_binding": play_binding,
        "smooth_binding": smooth_binding,
        "playback_repeat": playback_repeat,
        "playback_times": playback_times,
        "sensitivity": {**_engine_sensitivity_dict(), **_bot_user_sensitivity()},
        "state":         engine.state,
    })


@bp.get("/api/macro/open")
def macro_open():
    """Load a macro file by absolute path."""
    global current_path, current_macro
    path = os.path.abspath(request.args.get("path", "").strip().strip('"'))
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    parsed        = _parse_macro_text(text)
    current_path  = path
    current_macro = _macro_name_from_path(path)
    if parsed["meta"]:
        _set_engine_recorded_sens(parsed["meta"])
    _save_state()
    return jsonify({
        "ok":     True,
        "name":   current_macro,
        "path":   current_path,
        "blocks": parsed["blocks"],
        "meta":   parsed["meta"],
    })


@bp.post("/api/macro/save")
def macro_save():
    """Save blocks to an explicit path (or current_path if omitted)."""
    data       = request.get_json(force=True) or {}
    path       = str(data.get("path", current_path)).strip()
    name       = str(data.get("name", current_macro)).strip() or "macro"
    blocks     = data.get("blocks", [])
    sensitivity = data.get("sensitivity", {})

    try:
        result = _save_macro_file(path, name, blocks, sensitivity)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify(result)


@bp.post("/api/macro/new")
def macro_new():
    """Create a blank unsaved macro in the editor."""
    global current_path, current_macro
    data = request.get_json(silent=True) or {}
    current_path = ""
    current_macro = str(data.get("name", "untitled")).strip() or "untitled"
    _save_state()
    return jsonify({
        "ok": True,
        "name": current_macro,
        "path": current_path,
        "blocks": [],
        "meta": {
            "SENS_RECORDED_H": 17.0,
            "SENS_RECORDED_V": 17.0,
            "SENS_USER_H": engine.sensitivity.user_h,
            "SENS_USER_V": engine.sensitivity.user_v,
        },
    })


@bp.get("/api/macro/list")
def macro_list():
    return jsonify({"ok": True, "macros": _list_macros(), "macros_dir": MACROS_DIR})


@bp.get("/api/fs/list")
def fs_list():
    return jsonify(_list_directory(request.args.get("path", "") or current_path or MACROS_DIR))


@bp.post("/api/tools/picker")
def tools_picker():
    data = request.get_json(silent=True) or {}
    token = _next_picker_wait_token()
    point = _wait_for_f2_sample(float(data.get("timeout", 60.0)), token)
    if point is None:
        if not _picker_wait_token_active(token):
            return jsonify({"ok": False, "error": "Picker cancelled."}), 409
        return jsonify({"ok": False, "error": "Timed out waiting for F2."}), 408
    sx, sy = point
    return jsonify({
        "ok": True,
        "x": sx,
        "y": sy,
        "screen_x": sx,
        "screen_y": sy,
        "mode": "screen",
    })


@bp.post("/api/tools/picker/cancel")
def tools_picker_cancel():
    _next_picker_wait_token()
    return jsonify({"ok": True})


@bp.post("/api/tools/region")
def tools_region():
    data = request.get_json(silent=True) or {}
    token = _next_picker_wait_token()
    region = _wait_for_f2_region(float(data.get("timeout", 120.0)), token)
    if region is None:
        if not _picker_wait_token_active(token):
            return jsonify({"ok": False, "error": "Region picker cancelled."}), 409
        return jsonify({"ok": False, "error": "Timed out waiting for two F2 samples."}), 408
    x1, y1, x2, y2 = region
    return jsonify({"ok": True, "x1": x1, "y1": y1, "x2": x2, "y2": y2})


@bp.post("/api/tools/image/capture")
def tools_image_capture():
    data = request.get_json(silent=True) or {}
    region = _sanitize_region((data.get("x1"), data.get("y1"), data.get("x2"), data.get("y2")))
    if region is None:
        return jsonify({"ok": False, "error": "Invalid capture region."}), 400
    try:
        path, rel = _capture_region_png(region, str(data.get("name") or "image"), data.get("base_w"), data.get("base_h"))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    x1, y1, x2, y2 = region
    return jsonify({"ok": True, "path": path, "rel_path": rel, "x1": x1, "y1": y1, "x2": x2, "y2": y2})


@bp.post("/api/tools/image/save-sample")
def tools_image_save_sample():
    data = request.get_json(silent=True) or {}
    image = str(data.get("image") or "")
    if "," in image:
        image = image.split(",", 1)[1]
    try:
        raw = base64.b64decode(image, validate=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid PNG sample data."}), 400
    if len(raw) < 16 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return jsonify({"ok": False, "error": "Sample is not a PNG."}), 400
    try:
        import cv2
        import numpy as np

        decoded = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None or decoded.size == 0:
            return jsonify({"ok": False, "error": "PNG sample could not be decoded."}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"PNG validation failed: {e}"}), 400
    region = _sanitize_region((data.get("x1"), data.get("y1"), data.get("x2"), data.get("y2")))
    if region is None:
        return jsonify({"ok": False, "error": "Invalid sample region."}), 400
    try:
        path, rel = _save_sample_png_bytes(raw, str(data.get("name") or "image"), data.get("base_w"), data.get("base_h"))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    x1, y1, x2, y2 = region
    return jsonify({"ok": True, "path": path, "rel_path": rel, "x1": x1, "y1": y1, "x2": x2, "y2": y2})


@bp.get("/api/tools/image/list")
def tools_image_list():
    image_dir = _macro_dir_for_images()
    items = []
    for root_dir in (image_dir, MACRO_IMAGES_DIR, LEGACY_MACRO_IMAGES_DIR):
        if not os.path.isdir(root_dir):
            continue
        try:
            for entry in sorted(os.scandir(root_dir), key=lambda e: e.name.lower()):
                if not entry.is_file() or not entry.name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                    continue
                rel = _image_rel_path(entry.path)
                if not any(item["path"].lower() == rel.lower() for item in items):
                    items.append({"name": entry.name, "path": rel})
        except Exception:
            continue
    return jsonify({"ok": True, "images_dir": image_dir, "images": items})


@bp.post("/api/tools/image/test")
def tools_image_test():
    try:
        from macro_logic import effective_region, image_match_result, truthy

        data = request.get_json(silent=True) or {}
        macro_dir = os.path.dirname(os.path.abspath(current_path)) if current_path else MACROS_DIR
        match = image_match_result(data, BOT_ROOT, macro_dir)
        score = float(match.get("score", 0.0) or 0.0)
        threshold = max(0.0, min(100.0, float(data.get("threshold", 85) or 85))) / 100.0
        fixed = truthy(data.get("fixed", True))
        effective = effective_region(data) or (0, 0, 0, 0)
        coords = {"x1": effective[0], "y1": effective[1], "x2": effective[2], "y2": effective[3]}
        return jsonify({
            "ok": True,
            "score": score,
            "score_percent": round(score * 100.0, 2),
            "threshold": round(threshold * 100.0, 2),
            "matched": bool(match.get("matched")),
            "x": match.get("x"),
            "y": match.get("y"),
            "box": match.get("box"),
            "mode": "sample region" if fixed else "search region",
            "region": coords,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.get("/api/tools/screenshot")
def tools_screenshot():
    try:
        shot = _capture_fullscreen_png()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    shot["ok"] = True
    return jsonify(shot)


@bp.get("/api/dialog/open")
def dialog_open():
    path, error = _windows_file_dialog("open", initial_path=request.args.get("initial", "") or current_path or MACROS_DIR)
    return jsonify({"ok": not bool(error), "path": path, "cancelled": not bool(path) and not bool(error), "error": error})


@bp.get("/api/dialog/save-as")
def dialog_save_as():
    name = str(request.args.get("name", "") or current_macro or "macro").strip()
    if name and not name.lower().endswith(".macro"):
        name += ".macro"
    path, error = _windows_file_dialog("save", initial_path=current_path or MACROS_DIR, suggested_name=name)
    return jsonify({"ok": not bool(error), "path": path, "cancelled": not bool(path) and not bool(error), "error": error})


@bp.post("/api/play")
def play_macro():
    global current_path, current_macro
    if not _recorder_tab_open:
        return jsonify({"ok": False, "error": "Open the Recorder tab first."}), 409
    data = request.get_json(force=True) or {}
    path = str(data.get("path", current_path)).strip()
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    if engine.is_running() or engine.is_recording():
        return jsonify({"ok": False, "error": "Already busy"}), 409

    current_path  = path
    current_macro = os.path.splitext(os.path.basename(path))[0]
    _save_state()
    if data.get("dashboard"):
        _minimize_webview_window()
        _countdown_overlay("play")
    repeat = _repeat_value(data.get("repeat", playback_repeat), playback_repeat)
    override = _sensitivity_override(data.get("sensitivity"), path)
    ok = engine.play_path_once(path, current_macro, repeat, override)
    return jsonify({"ok": bool(ok)})


@bp.post("/api/stop")
def stop_macro():
    engine.stop()
    return jsonify({"ok": True})


@bp.post("/api/settings")
def save_settings():
    global record_binding, play_binding, smooth_binding, playback_repeat, playback_times
    data = request.get_json(force=True) or {}
    sensitivity = data.get("sensitivity") or {}
    record_binding = str(data.get("record_binding") or record_binding or "F5").strip().upper()
    play_binding = str(data.get("play_binding") or play_binding or "F6").strip().upper()
    smooth_binding = str(data.get("smooth_binding") or smooth_binding or "L").strip().upper()
    playback_repeat = _repeat_value(data.get("playback_repeat", playback_repeat), playback_repeat)
    playback_times = _times_value(data.get("playback_times", playback_times if playback_repeat <= 1 else playback_repeat), playback_times)
    if playback_repeat > 1:
        playback_times = playback_repeat
    _set_engine_sens(sensitivity)
    _save_state()
    if _recorder_tab_open:
        _restart_hotkeys()
    return jsonify({
        "ok": True,
        "record_binding": record_binding,
        "play_binding": play_binding,
        "smooth_binding": smooth_binding,
        "playback_repeat": playback_repeat,
        "playback_times": playback_times,
    })


@bp.post("/api/record/start")
def record_start():
    if not _recorder_tab_open:
        return jsonify({"ok": False, "error": "Open the Recorder tab first."}), 409
    data = request.get_json(silent=True) or {}
    with _state_lock:
        if engine.is_running():
            return jsonify({"ok": False, "error": "Stop playback before recording."}), 409
        if engine.is_recording():
            return jsonify({"ok": True, "recording": True})
        if data.get("dashboard"):
            _minimize_webview_window()
        global _record_locked_blocks
        _record_locked_blocks = _current_locked_blocks()
        ok = _start_recording(data.get("sensitivity") or {})
    return jsonify({"ok": bool(ok), "recording": bool(ok), "path": current_path, "name": current_macro})


@bp.post("/api/record/stop")
def record_stop():
    with _state_lock:
        if not engine.is_recording():
            return jsonify({"ok": False, "error": "Not recording."}), 409
        try:
            result = _stop_recording_and_save()
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
    result["recording"] = False
    return jsonify(result)


@bp.get("/api/state")
def get_state():
    with _state_lock:
        smooth = dict(_smooth_move)
    return jsonify({
        "ok": True,
        "state": engine.state,
        "tab_armed": _recorder_tab_open,
        "smooth_move": smooth,
    })


@bp.post("/api/tab")
def recorder_tab():
    data = request.get_json(silent=True) or {}
    set_recorder_tab_active(bool(data.get("active")))
    return jsonify({"ok": True, "active": _recorder_tab_open})



def attach_macro_engine(dash_app) -> None:
    """Mount Recorder routes on the bot dashboard Flask app."""
    if "macro_engine" not in dash_app.blueprints:
        dash_app.register_blueprint(bp)
    _load_state()
    if not current_path:
        macros = _list_macros()
        if macros:
            globals()["current_path"] = macros[0]["path"]
            globals()["current_macro"] = macros[0]["name"]
    set_recorder_tab_active(False)
    log.info("Macro Engine attached at /me (F5/F6 hook only while Recorder tab is open)")



# ── Entry point ───────────────────────────────────────────────────────────────

def _run_flask() -> None:
    print("===== Macro Engine =====", flush=True)
    print("Dashboard: http://127.0.0.1:5050", flush=True)
    print("Logs: request spam hidden", flush=True)
    print("============================", flush=True)
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False, threaded=True)


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    SYNCHRONIZE = 0x00100000
    WAIT_TIMEOUT = 0x00000102
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
    if not handle:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _monitor_parent(parent_pid: int) -> None:
    while _process_is_alive(parent_pid):
        time.sleep(0.5)
    os._exit(0)


def _monitor_webview(proc: subprocess.Popen) -> None:
    proc.wait()
    os._exit(0)


def _terminate_webview() -> None:
    proc = _webview_process
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _launch_webview_process():
    create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    if getattr(sys, "frozen", False):
        return subprocess.Popen(
            [sys.executable, "--webview", "--parent-pid", str(os.getpid())],
            creationflags=create_no_window,
        )
    script = """
import ctypes
import os
import sys
import threading
import time
import webview

parent_pid = int(sys.argv[1])

def alive(pid):
    handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)
    if not handle:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 0x00000102
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)

def watch_parent():
    while alive(parent_pid):
        time.sleep(0.5)
    os._exit(0)

threading.Thread(target=watch_parent, daemon=True).start()
webview.create_window(
    'Macro Engine',
    'http://127.0.0.1:5050',
    width=1280,
    height=860,
    resizable=True,
    min_size=(980, 620),
)
webview.start()
"""
    return subprocess.Popen(
        [sys.executable, "-c", script, str(os.getpid())],
        creationflags=create_no_window,
    )


def _run_webview_window() -> None:
    import webview
    webview.create_window(
        "Macro Engine", "http://127.0.0.1:5050",
        width=1280, height=860, resizable=True, min_size=(980, 620),
    )
    webview.start()


if __name__ == "__main__":
    if "--webview" in sys.argv:
        if "--parent-pid" in sys.argv:
            try:
                parent_pid = int(sys.argv[sys.argv.index("--parent-pid") + 1])
                threading.Thread(target=_monitor_parent, args=(parent_pid,), daemon=True).start()
            except Exception:
                pass
        time.sleep(0.6)
        _run_webview_window()
        sys.exit(0)

    if "macro_engine" not in app.blueprints:
        app.register_blueprint(bp)
    renamed_images = _prefix_unversioned_macro_images(MACRO_IMAGES_DIR)
    if renamed_images:
        log.info("Renamed %s macro image(s) with current resolution prefix.", renamed_images)
    _load_state()
    # If no previous state or file gone, default to first macro in folder
    if not current_path:
        macros = _list_macros()
        if macros:
            current_path  = macros[0]["path"]
            current_macro = macros[0]["name"]

    # Standalone window is the Recorder, so F5/F6 start armed.
    set_recorder_tab_active(True)

    threading.Thread(target=_run_flask, daemon=True, name="macro-flask").start()
    time.sleep(0.4)

    _webview_process = _launch_webview_process()
    atexit.register(_terminate_webview)
    threading.Thread(target=_monitor_webview, args=(_webview_process,), daemon=True, name="webview-watch").start()

    # Keep main thread alive (hotkey listener runs in daemon thread)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
