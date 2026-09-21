# ============================================================
# MACRO FORGE - MACRO RUNNER
# Plays converted .macro text files directly — no JJibit /
# MacroRecorder needed. All input is sent via pure ctypes
# Win32 (same approach as before, no pywin32 required).
# ============================================================
import os
import threading
import time
import ctypes
import ctypes.wintypes
import re

from logger import get_logger
from config import MACROS_DIR
from macro_engine.macro_logic import (
    _macro_res_scale,
    branch_active,
    define_variable,
    scan_loop_background,
    handle_else,
    handle_else_if,
    handle_end_if,
    handle_end_while,
    handle_if,
    handle_while,
    parse_payload,
    run_image_check,
    set_variable,
    start_background_loop,
    start_watcher,
    stop_all_watchers,
    stop_watcher,
)

def _config_float(name: str, default: float) -> float:
    try:
        import config as _cfg
        return float(getattr(_cfg, name, default))
    except Exception:
        return default


def _macro_sensitivity_from_lines(lines: list[str]) -> dict[str, float]:
    """Read recorded sensitivity from the macro file and user sensitivity from bot config."""
    sensitivity = {
        "recorded_h": _config_float("RECORDED_SENS_H", 17.0),
        "recorded_v": _config_float("RECORDED_SENS_V", 17.0),
        "user_h": _config_float("USER_SENS_H", 17.0),
        "user_v": _config_float("USER_SENS_V", 17.0),
    }
    for raw in lines:
        line = raw.strip()
        try:
            if line.startswith("# SENS_RECORDED_H:"):
                sensitivity["recorded_h"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("# SENS_RECORDED_V:"):
                sensitivity["recorded_v"] = float(line.split(":", 1)[1].strip())
        except Exception:
            continue
    return sensitivity


def _smooth_ratios(sensitivity: dict[str, float]) -> tuple[float, float]:
    user_h = float(sensitivity.get("user_h") or 17.0)
    user_v = float(sensitivity.get("user_v") or 17.0)
    if user_h <= 0 or user_v <= 0:
        return 1.0, 1.0
    return (
        float(sensitivity.get("recorded_h") or 17.0) / user_h,
        float(sensitivity.get("recorded_v") or 17.0) / user_v,
    )


def _scale_smooth_move(dx: int, dy: int) -> tuple[int, int]:
    """Compatibility scaler for non-file one-off aim moves."""
    rx, ry = _smooth_ratios(_macro_sensitivity_from_lines([]))
    return int(round(dx * rx)), int(round(dy * ry))


log = get_logger()
_MACRO_COORD_BASE_W = 1920
_MACRO_COORD_BASE_H = 1080
_BOT_ROOT = os.path.dirname(MACROS_DIR)
_macro_preset = ""
_active_path = ""


def _read_macro_lines(path: str) -> list[str]:
    """Read a .macro's canonical lines — v3 container OR legacy text."""
    from macro_engine import container as _c
    with open(path, "rb") as f:
        data = f.read()
    if _c.is_container_bytes(data):
        data = _c.read_generated_text(data).encode("utf-8", errors="replace")
    return [ln.strip() for ln in data.decode("utf-8", errors="replace").splitlines()]


def _resolve_macro_path(name: str) -> str:
    """Resolve a macro path, name or resource path to a .macro file.

    Workspace-relative first, legacy fallbacks always kept:
      - res:// / ws:// paths → relative to the RUNNING workspace root
      - plain relative paths → checked against the running workspace root
      - then the full legacy resolution (absolute paths, BOT_DIR relative,
        short names under the global macros/ folders) — unchanged from 2.1.157
    """
    raw = str(name or "").strip().strip('"').replace("\\", "/")
    low = raw.lower()

    def _as_macro(path: str) -> str:
        return path if path.lower().endswith(".macro") else path + ".macro"

    if raw:
        if low.startswith("res://") or low.startswith("ws://"):
            try:
                from engine import pcr_runtime as rt
            except Exception:
                import pcr_runtime as rt
            # res:// is relative to the workspace RESOURCES folder — same
            # semantics as _pcr_resloc and the "resource" block. An optional
            # leading "resources/" is accepted and normalized away.
            # (split, not [6:] — ws:// is 5 chars, res:// is 6; the old slice
            # ate the first letter of ws:// paths)
            rel = raw.split("://", 1)[1].strip("/")
            if rel.lower().startswith("resources/"):
                rel = rel[len("resources/"):]
            return _as_macro(os.path.join(rt.workspace_dir(), "resources", *rel.split("/")))
        if not (os.path.isabs(raw) or (len(raw) > 1 and raw[1] == ":")):
            try:
                from engine import pcr_runtime as rt
                ws_root = rt.workspace_dir()
            except Exception:
                ws_root = ""
            if ws_root:
                cand = os.path.abspath(os.path.join(ws_root, *raw.split("/")))
                if os.path.isfile(_as_macro(cand)):
                    return _as_macro(cand)
                if os.path.isfile(cand):
                    return cand

    return _resolve_macro_path_legacy(name)


def _resolve_macro_path_legacy(name: str) -> str:
    """Resolve a macro name or resource path to a .macro file.

    Accepts:
      - absolute paths (with or without .macro)
      - paths relative to the running location / BOT_DIR
      - short names looked up under MACROS_DIR
    """
    raw = str(name or "").strip().replace("\\", "/")
    if not raw:
        return os.path.join(MACROS_DIR, ".macro")

    direct: list[str] = []
    if os.path.isabs(raw) or (len(raw) > 1 and raw[1] == ":"):
        direct.append(raw)
        if not raw.lower().endswith(".macro"):
            direct.append(raw + ".macro")
    else:
        if os.path.isfile(raw):
            direct.append(os.path.abspath(raw))
        elif os.path.isfile(raw + ".macro"):
            direct.append(os.path.abspath(raw + ".macro"))
        bot_rel = os.path.join(_BOT_ROOT, raw.replace("/", os.sep))
        direct.append(bot_rel)
        if not raw.lower().endswith(".macro"):
            direct.append(bot_rel + ".macro")
        # running location / macros / name
        if not raw.lower().startswith("macros/"):
            under_macros = os.path.join(MACROS_DIR, os.path.basename(raw))
            direct.append(under_macros if raw.lower().endswith(".macro") else under_macros if os.path.splitext(under_macros)[1] else under_macros + ".macro")

    for candidate in direct:
        if candidate and os.path.isfile(candidate):
            return candidate

    stem = raw[:-6] if raw.lower().endswith(".macro") else raw

    rel_candidates: list[str] = []
    if "/" in stem:
        rel_candidates.append(stem)
    else:
        rel_candidates.append(stem)
        rel_candidates.append(f"teleports/{stem}")
        rel_candidates.append(f"engine/{stem}")
        m_short = re.match(r"^a(\d+)_(.+)$", stem)
        if stem.startswith(("base_to_", "teleport_to_")):
            rel_candidates.append(f"teleports/{stem}")

    seen: set[str] = set()
    candidates: list[str] = []
    for rel in rel_candidates:
        rel = rel.strip("/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        candidates.append(os.path.join(MACROS_DIR, f"{rel}.macro"))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    if "/" not in stem:
        target = f"{stem}.macro".lower()
        matches: list[str] = []
        for root, _dirs, files in os.walk(MACROS_DIR):
            for file_name in files:
                if file_name.lower() == target:
                    matches.append(os.path.join(root, file_name))
        if matches:
            return sorted(matches, key=lambda p: (len(os.path.relpath(p, MACROS_DIR)), p.lower()))[0]

    return candidates[0] if candidates else os.path.join(MACROS_DIR, f"{stem}.macro")


def macro_exists(name: str) -> bool:
    return os.path.isfile(_resolve_macro_path(name))


def is_any_macro_playing() -> bool:
    with _active_lock:
        t = _active_thread
        ev = _active_stop_event
    if t is not None and t.is_alive():
        return True
    return ev is not None and not ev.is_set()


def is_macro_playing(name: str | None = None) -> bool:
    if not is_any_macro_playing():
        return False
    if not name:
        return True
    want = os.path.normcase(os.path.abspath(_resolve_macro_path(str(name))))
    with _active_lock:
        current = _active_path
    if not current:
        return True
    return os.path.normcase(os.path.abspath(current)) == want


def get_playing_macro() -> str:
    with _active_lock:
        path = _active_path
    if not path:
        return ""
    base = os.path.basename(path)
    return base[:-6] if base.lower().endswith(".macro") else base


def _sleep_until(deadline: float, stop_check):
    """Wait until `deadline` (perf_counter). Spin the last 2ms so a coarse
    Win11 timer cannot overshoot an 8ms DELAY into 15ms — or, after catch-up,
    collapse the next DELAY to 0."""
    while True:
        stop_check()
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return
        if remaining <= 0.002:
            while time.perf_counter() < deadline:
                stop_check()
            return
        time.sleep(min(0.001, remaining - 0.002))


def _boost_playback_timing() -> None:
    """Keep 1ms timer resolution and stop Win11 EcoQoS from stretching SendInput.

    The game is foreground while we play, so the bot is a background process.
    Win11 then EcoQoS-throttles us: each SMOOTH_MOVE takes 10–20ms, DELAY:8
    catch-up becomes 0, and W-holds (walks) get eaten — 'stops halfway'.
    """
    try:
        ctypes.WinDLL("winmm").timeBeginPeriod(1)
    except Exception:
        pass
    try:
        ntdll = ctypes.WinDLL("ntdll")
        actual = ctypes.c_ulong()
        ntdll.NtSetTimerResolution(10000, 1, ctypes.byref(actual))
    except Exception:
        pass
    try:
        k32 = ctypes.windll.kernel32
        handle = k32.GetCurrentProcess()
        k32.SetPriorityClass(handle, 0x00000080)  # HIGH_PRIORITY_CLASS
        class _PPT(ctypes.Structure):
            _fields_ = [
                ("Version", ctypes.c_ulong),
                ("ControlMask", ctypes.c_ulong),
                ("StateMask", ctypes.c_ulong),
            ]
        st = _PPT()
        st.Version = 1
        st.ControlMask = 0x1  # PROCESS_POWER_THROTTLING_EXECUTION_SPEED
        st.StateMask = 0      # disable throttling
        k32.SetProcessInformation(handle, 4, ctypes.byref(st), ctypes.sizeof(st))
    except Exception:
        pass


_boost_playback_timing()

# ── Win32 constants ─────────────────────────────────────────
INPUT_MOUSE            = 0
INPUT_KEYBOARD         = 1

MOUSEEVENTF_MOVE       = 0x0001   # relative move
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_XDOWN      = 0x0080
MOUSEEVENTF_XUP        = 0x0100
MOUSEEVENTF_WHEEL      = 0x0800
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_ABSOLUTE   = 0x8000   # absolute coords (in screen coords)
MOUSEEVENTF_MOVE_ABS   = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE

KEYEVENTF_KEYDOWN  = 0x0000
KEYEVENTF_KEYUP    = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

PUL = ctypes.POINTER(ctypes.c_ulong)
ULONG_PTR = ctypes.c_size_t

# ── Win32 structs ────────────────────────────────────────────

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.c_ulong),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.c_ushort),
        ("wScan",       ctypes.c_ushort),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", _INPUT_UNION)]


_SendInput            = ctypes.windll.user32.SendInput
_GetSystemMetrics     = ctypes.windll.user32.GetSystemMetrics
_MapVirtualKeyW       = ctypes.windll.user32.MapVirtualKeyW

SM_CXSCREEN = 0
SM_CYSCREEN = 1

# Camera playback. mouse_event is the v1.5 API (extraInfo=0, no NOCOALESCE).
# SendInput MOVE|NOCOALESCE is the later path. Same SMOOTH_MOVE packets either way.
_mouse_event_fn = ctypes.windll.user32.mouse_event
_mouse_event_fn.restype = None
# last arg is ULONG_PTR extraInfo (a VALUE, usually 0) — not a pointer.
_mouse_event_fn.argtypes = [
    ctypes.c_uint, ctypes.c_int, ctypes.c_int,
    ctypes.c_uint, ctypes.c_size_t,
]

SPI_GETMOUSE = 0x0003
SPI_GETMOUSESPEED = 0x0070
_mouse_environment_warned = False


def _get_windows_mouse_settings() -> tuple[tuple[int, int, int], int] | None:
    """Return ((threshold1, threshold2, acceleration), pointer_speed)."""
    try:
        values = (ctypes.c_int * 3)()
        speed = ctypes.c_int()
        spi = ctypes.windll.user32.SystemParametersInfoW
        if not spi(SPI_GETMOUSE, 0, ctypes.byref(values), 0):
            return None
        if not spi(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0):
            return None
        return (int(values[0]), int(values[1]), int(values[2])), int(speed.value)
    except Exception:
        return None


def _set_windows_mouse_settings(mouse: tuple[int, int, int], speed: int) -> bool:
    """Intentionally a no-op. Changing SPI mouse settings pops a Windows UI."""
    return False


def _prepare_windows_mouse_compatibility() -> tuple[tuple[int, int, int], int] | None:
    """Never writes Windows settings."""
    global _mouse_environment_warned
    current = _get_windows_mouse_settings()
    if current is None:
        return None
    mouse, speed = current
    if not _mouse_environment_warned:
        _mouse_environment_warned = True
        log.info(
            "[INPUT] Windows pointer speed=%s accel(EPP)=%s. "
            "Camera inject=SendInput. Windows mouse settings are never changed.",
            speed, mouse[2],
        )
    return None


def _restore_windows_mouse_settings(snapshot: tuple[tuple[int, int, int], int] | None):
    return


def _inject_method() -> str:
    return "sendinput"


def _raw_mouse_move_rel(dx: int, dy: int):
    """Relative camera. Same SMOOTH_MOVE numbers; only the Win32 call changes.

    mouse_event        — v1.5 API, extraInfo=0, no NOCOALESCE
    sendinput          — SendInput MOVE|NOCOALESCE extraInfo=0
    sendinput_plain    — SendInput MOVE (coalesce allowed)
    """
    dx, dy = int(dx), int(dy)
    if not (dx or dy):
        return
    method = _inject_method()
    if method in ("mouse_event", "legacy", "mouseevent", "v15", "v1.5"):
        _mouse_event_fn(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        return
    flags = MOUSEEVENTF_MOVE
    if method not in ("sendinput_plain", "plain", "coalesce"):
        flags |= MOUSEEVENTF_MOVE_NOCOALESCE
    inp = _make_mouse(flags, dx, dy)
    sent = 0
    try:
        sent = int(_SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)))
    except Exception:
        sent = 0
    if sent:
        return
    _mouse_event_fn(MOUSEEVENTF_MOVE, dx, dy, 0, 0)


# ── Low-level input helpers ──────────────────────────────────

def _send_input(*inputs: INPUT):
    if not inputs:
        return 0
    arr = (INPUT * len(inputs))(*inputs)
    return int(_SendInput(len(inputs), arr, ctypes.sizeof(INPUT)))


def _make_mouse(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> INPUT:
    union = _INPUT_UNION()
    union.mi = MOUSEINPUT(dx=int(dx), dy=int(dy), mouseData=int(data), dwFlags=int(flags),
                          time=0, dwExtraInfo=0)
    return INPUT(INPUT_MOUSE, union)


def _is_extended_vk(vk: int) -> bool:
    return vk in {
        0x21, 0x22, 0x23, 0x24,  # PgUp/PgDn/End/Home
        0x25, 0x26, 0x27, 0x28,  # Arrows
        0x2D, 0x2E,              # Insert/Delete
        0xA3, 0xA5,              # Right Ctrl / Right Alt
    }


def _vk_to_scancode(vk: int) -> int:
    if vk == 0xA0:  # VK_LSHIFT
        return 0x2A
    if vk == 0xA1:  # VK_RSHIFT
        return 0x36
    if vk in (0xA2, 0xA3):  # L/R CTRL
        return 0x1D
    if vk in (0xA4, 0xA5):  # L/R ALT
        return 0x38
    return _MapVirtualKeyW(vk, 0)


def _make_key(vk: int, is_key_up: bool) -> INPUT:
    scan = _vk_to_scancode(vk)
    flags = KEYEVENTF_SCANCODE
    if is_key_up:
        flags |= KEYEVENTF_KEYUP
    if _is_extended_vk(vk):
        flags |= KEYEVENTF_EXTENDEDKEY

    extra = ctypes.c_ulong(0)
    union = _INPUT_UNION()
    union.ki = KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags,
                          time=0, dwExtraInfo=0)
    return INPUT(INPUT_KEYBOARD, union)


# ── Mouse primitives ─────────────────────────────────────────

def _mouse_move_abs(x: int, y: int):
    """Move cursor to absolute screen position (pixels)."""
    sw = _GetSystemMetrics(SM_CXSCREEN) or 1920
    sh = _GetSystemMetrics(SM_CYSCREEN) or 1080
    x = max(0, min(max(0, int(sw) - 1), int(x)))
    y = max(0, min(max(0, int(sh) - 1), int(y)))
    # SendInput ABSOLUTE coords are in the range 0..65535
    norm_x = int(x * 65535 / sw)
    norm_y = int(y * 65535 / sh)
    inp = _make_mouse(MOUSEEVENTF_MOVE_ABS, norm_x, norm_y)
    _send_input(inp)


def _scale_macro_abs_xy(x: int, y: int) -> tuple[int, int]:
    """Scale macro ABS coordinates from 1920x1080 record base to current runtime resolution."""
    sw = _GetSystemMetrics(SM_CXSCREEN) or 1920
    sh = _GetSystemMetrics(SM_CYSCREEN) or 1080
    sx = float(sw) / float(_MACRO_COORD_BASE_W)
    sy = float(sh) / float(_MACRO_COORD_BASE_H)
    nx = int(round(int(x) * sx))
    ny = int(round(int(y) * sy))
    nx = max(0, min(max(0, sw - 1), nx))
    ny = max(0, min(max(0, sh - 1), ny))
    return nx, ny


def _resolve_macro_number(value, vars_state: dict) -> tuple[float, bool]:
    text = str(value or "").strip()
    if not text:
        return 0.0, False
    var_name = text
    if text.startswith("${") and text.endswith("}"):
        var_name = text[2:-1].strip()
    if var_name in vars_state:
        try:
            return float(vars_state.get(var_name) or 0), True
        except Exception:
            return 0.0, True
    try:
        return float(text), False
    except Exception:
        return 0.0, False


def _mouse_move_rel(dx: int, dy: int):
    """Move cursor by relative delta (pixels) using mouse_event (legacy API)."""
    _raw_mouse_move_rel(dx, dy)


# down→up gap for a synthesized click: 1ms (was 50ms). 50ms burned
# 100ms per WHILE/UNTIL pass in two-click loops and made game macros
# feel laggy — 1ms is what the hardware wheel of a real fast click does.
_CLICK_PRESS_SECONDS = 0.001


def _mouse_left_down():
    _send_input(_make_mouse(MOUSEEVENTF_LEFTDOWN))


def _mouse_left_up():
    _send_input(_make_mouse(MOUSEEVENTF_LEFTUP))


def _mouse_left_click():
    _send_input(_make_mouse(MOUSEEVENTF_LEFTDOWN))
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_input(_make_mouse(MOUSEEVENTF_LEFTUP))


def _smooth_move_rel(dx: int, dy: int, duration_ms: int,
                     stop_event: threading.Event | None = None):
    """Smoothly move mouse by (dx, dy) over duration_ms (10ms steps, mouse_event)."""
    dx, dy = int(dx), int(dy)
    duration_ms = max(0, int(duration_ms))
    if duration_ms <= 0:
        if dx or dy:
            _raw_mouse_move_rel(dx, dy)
        return
    steps = max(1, duration_ms // 10)
    acc_x = acc_y = 0.0
    for _ in range(steps):
        if stop_event is not None and stop_event.is_set():
            return
        acc_x += dx / steps
        acc_y += dy / steps
        ix = int(acc_x)
        iy = int(acc_y)
        if ix or iy:
            _raw_mouse_move_rel(ix, iy)
            acc_x -= ix
            acc_y -= iy
        time.sleep(0.010)


# ── Keyboard primitives ──────────────────────────────────────

def _key_down(vk: int):
    _send_input(_make_key(vk, False))


def _key_up(vk: int):
    _send_input(_make_key(vk, True))


def _key_press(vk: int, hold_ms: int = 30):
    _key_down(vk)
    time.sleep(hold_ms / 1000.0)
    _key_up(vk)


_BINDING_ALIASES = {
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "SPACE": 0x20,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "SHIFT": 0x10,
    "L_SHIFT": 0xA0,
    "R_SHIFT": 0xA1,
    "LSHIFT": 0xA0,
    "RSHIFT": 0xA1,
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "L_CTRL": 0xA2,
    "R_CTRL": 0xA3,
    "LCTRL": 0xA2,
    "RCTRL": 0xA3,
    "ALT": 0x12,
    "L_ALT": 0xA4,
    "R_ALT": 0xA5,
    "LALT": 0xA4,
    "RALT": 0xA5,
    "LEFT_SHIFT": 0xA0,
    "RIGHT_SHIFT": 0xA1,
    "LEFT_CTRL": 0xA2,
    "RIGHT_CTRL": 0xA3,
    "LEFT_ALT": 0xA4,
    "RIGHT_ALT": 0xA5,
    "CAPSLOCK": 0x14,
    "CAPS_LOCK": 0x14,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGE_UP": 0x21,
    "PAGEDOWN": 0x22,
    "PAGE_DOWN": 0x22,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "WIN": 0x5B,
    "WINDOWS": 0x5B,
    "LWIN": 0x5B,
    "RWIN": 0x5C,
    "MENU": 0x5D,
    "APPS": 0x5D,
    "PRINTSCREEN": 0x2C,
    "PRINT_SCREEN": 0x2C,
    "PAUSE": 0x13,
    "NUMLOCK": 0x90,
    "NUM_LOCK": 0x90,
    "SCROLLLOCK": 0x91,
    "SCROLL_LOCK": 0x91,
    "COMMA": 0xBC,
    "PERIOD": 0xBE,
    "SLASH": 0xBF,
    "SEMICOLON": 0xBA,
    "QUOTE": 0xDE,
    "BRACKET_LEFT": 0xDB,
    "BRACKET_RIGHT": 0xDD,
    "BACKSLASH": 0xDC,
    "MINUS": 0xBD,
    "EQUALS": 0xBB,
    "GRAVE": 0xC0,
    "NUM_ADD": 0x6B,
    "NUM_SUBTRACT": 0x6D,
    "NUM_MULTIPLY": 0x6A,
    "NUM_DIVIDE": 0x6F,
    "NUM_DECIMAL": 0x6E,
    "NUM_ENTER": 0x0D,
}


def _binding_to_vk(binding: str) -> int | None:
    raw = str(binding or "").strip()
    if not raw:
        return None
    name = raw.upper().replace("-", "_").replace(" ", "_")
    name = re.sub(r"_+", "_", name)

    if name in _BINDING_ALIASES:
        return _BINDING_ALIASES[name]

    if re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", name):
        n = int(name[1:])
        return 0x70 + (n - 1)

    if re.fullmatch(r"[A-Z]", name):
        return ord(name)

    if re.fullmatch(r"[0-9]", name):
        return ord(name)

    if re.fullmatch(r"NUMPAD_[0-9]", name) or re.fullmatch(r"NUMPAD[0-9]", name) or re.fullmatch(r"NUM_[0-9]", name):
        digit = int(name[-1])
        return 0x60 + digit

    if name in {"NUMPAD_MULTIPLY", "NUMPAD_*"}:
        return 0x6A
    if name in {"NUMPAD_ADD", "NUMPAD_+", "NUMPAD_PLUS"}:
        return 0x6B
    if name in {"NUMPAD_SUBTRACT", "NUMPAD_-", "NUMPAD_MINUS"}:
        return 0x6D
    if name in {"NUMPAD_DECIMAL", "NUMPAD_DOT", "NUMPAD_."}:
        return 0x6E
    if name in {"NUMPAD_DIVIDE", "NUMPAD_/"}:
        return 0x6F

    if name.startswith("0X"):
        try:
            return int(name, 16)
        except ValueError:
            return None

    return None


def trigger_binding_action(binding: str, *, hold_ms: int = 30) -> bool:
    """Trigger keyboard/mouse action from configured binding string."""
    raw = str(binding or "").strip()
    if not raw:
        return False
    name = raw.upper().replace("-", "_").replace(" ", "_")
    name = re.sub(r"_+", "_", name)

    if name in {"MOUSE_LEFT", "LEFT_MOUSE", "LMB", "MOUSE1"}:
        _mouse_left_click()
        return True
    if name in {"MOUSE_RIGHT", "RIGHT_MOUSE", "RMB", "MOUSE2"}:
        right_click()
        return True
    if name in {"MOUSE_MIDDLE", "MIDDLE_MOUSE", "MMB", "MOUSE3", "SCROLL_CLICK"}:
        middle_click()
        return True
    if name in {"MOUSE4", "XBUTTON1", "MB4", "MOUSE_X1"}:
        xbutton1_click()
        return True
    if name in {"MOUSE5", "XBUTTON2", "MB5", "MOUSE_X2"}:
        xbutton2_click()
        return True

    vk = _binding_to_vk(name)
    if vk is None:
        return False
    _key_press(vk, hold_ms=hold_ms)
    return True


def log_input_environment() -> None:
    """Dump Windows pointer / DPI / playback facts at F8 / Start (every mode)."""
    bits: list[str] = []
    try:
        class _OSV(ctypes.Structure):
            _fields_ = [
                ("dwOSVersionInfoSize", ctypes.c_ulong),
                ("dwMajorVersion", ctypes.c_ulong),
                ("dwMinorVersion", ctypes.c_ulong),
                ("dwBuildNumber", ctypes.c_ulong),
                ("dwPlatformId", ctypes.c_ulong),
                ("szCSDVersion", ctypes.c_wchar * 128),
            ]
        vi = _OSV()
        vi.dwOSVersionInfoSize = ctypes.sizeof(vi)
        ctypes.windll.ntdll.RtlGetVersion(ctypes.byref(vi))
        bits.append(
            f"windows={vi.dwMajorVersion}.{vi.dwMinorVersion} build={vi.dwBuildNumber}"
        )
    except Exception as e:
        bits.append(f"windows=? ({e})")

    cur = _get_windows_mouse_settings()
    if cur is None:
        bits.append("pointer_speed=?  enhance_pointer_precision=?")
    else:
        mouse, speed = cur
        epp = "ON" if int(mouse[2]) else "OFF"
        bits.append(
            f"pointer_speed={speed}/20 (10=default)  "
            f"enhance_pointer_precision={epp}  "
            f"accel_thresholds={mouse[0]},{mouse[1]}"
        )

    try:
        cx = int(_GetSystemMetrics(0) or 0)
        cy = int(_GetSystemMetrics(1) or 0)
        vx = int(_GetSystemMetrics(78) or 0)
        vy = int(_GetSystemMetrics(79) or 0)
        mons = int(_GetSystemMetrics(80) or 0)
        bits.append(f"primary={cx}x{cy}  virtual={vx}x{vy}  monitors={mons}")
    except Exception as e:
        bits.append(f"screen=? ({e})")

    sys_dpi = 0
    try:
        sys_dpi = int(ctypes.windll.user32.GetDpiForSystem())
    except Exception:
        try:
            hdc = ctypes.windll.user32.GetDC(None)
            sys_dpi = int(ctypes.windll.gdi32.GetDeviceCaps(hdc, 88))
            ctypes.windll.user32.ReleaseDC(None, hdc)
        except Exception:
            sys_dpi = 0
    if sys_dpi:
        bits.append(f"dpi_system={sys_dpi}  display_scale={round(sys_dpi * 100 / 96)}%")
    else:
        bits.append("dpi_system=?")

    try:
        awareness = ctypes.c_int(-1)
        ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness))
        names = {0: "unaware", 1: "system", 2: "per-monitor"}
        bits.append(f"dpi_awareness={names.get(int(awareness.value), awareness.value)}")
    except Exception:
        pass

    method = _inject_method()
    if method in ("mouse_event", "legacy", "mouseevent", "v15", "v1.5"):
        bits.append("rel_move=mouse_event extraInfo=0 (v1.5 API)")
    elif method in ("sendinput_plain", "plain", "coalesce"):
        bits.append("rel_move=sendinput_plain (MOVE, coalesce on)")
    else:
        bits.append("rel_move=sendinput_nocoalesce extraInfo=0")
    try:
        import config as _cfg_env
        uh = getattr(_cfg_env, "USER_SENS_H", "?")
        uv = getattr(_cfg_env, "USER_SENS_V", "?")
        rh = getattr(_cfg_env, "RECORDED_SENS_H", "?")
        rv = getattr(_cfg_env, "RECORDED_SENS_V", "?")
        bits.append(f"user_sens={uh}/{uv}  recorded_sens={rh}/{rv}")
    except Exception as e:
        bits.append(f"sens/keybinds=? ({e})")

    try:
        klid = int(ctypes.windll.user32.GetKeyboardLayout(0)) & 0xFFFF
        bits.append(f"keyboard_layout=0x{klid:04X} (0x0409=US  0x0413=NL  0x0407=DE)")
    except Exception:
        pass

    import sys as _sys
    bits.append(
        f"frozen_exe={bool(getattr(_sys, 'frozen', False))}  "
        f"python={_sys.version.split()[0]}"
    )
    try:
        pri = int(ctypes.windll.kernel32.GetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess()
        ))
        bits.append(f"priority_class=0x{pri:X} (0x80=HIGH)")
    except Exception:
        pass

    log.info("[INPUT] --- playback environment ---")
    for line in bits:
        log.info(f"[INPUT] {line}")


def prime_game_mouse_capture() -> None:
    """Burn a dummy relative move so the first recorded camera turn is not skipped.

    When the game window is not yet capturing the mouse, Windows (and the game)
    consume the first relative-move as focus/capture instead of a camera turn.
    That used to drop the first SMOOTH_MOVE in a macro, especially on the
    Recorder's first play. Send a canceling +1/-1 pair.
    """
    try:
        _raw_mouse_move_rel(0, 0)
        time.sleep(0.03)
        _raw_mouse_move_rel(1, 0)
        time.sleep(0.015)
        _raw_mouse_move_rel(-1, 0)
        time.sleep(0.08)
    except Exception as e:
        log.debug(f"prime_game_mouse_capture() warning: {e}")


# ── Middle-mouse click ───────────────────────────────────────

# ── Click pacing guard ─────────────────────────────────────────
# Fortnite-verified (user-tested): a click registers only when
#   1) the button is held >= 1ms between DOWN and UP, AND
#   2) >= 1ms passes after UP before the next DOWN.
# 0ms in either slot and the game merges/eats the click entirely.
# mouse_click()/right_click()/… already sleep 1ms between their own
# down/up — but nothing guaranteed the GAP after an UP before the NEXT
# DOWN, and mouse_down()/mouse_up() blocks could fire back-to-back with
# a 0ms hold. This guard enforces both floors for every synthesized
# mouse event no matter which API path emitted it.
_MOUSE_MIN_HOLD_S = 0.001   # DOWN -> UP floor
_MOUSE_MIN_GAP_S = 0.001    # UP  -> next DOWN floor
_MOUSE_DOWN2BTN = {
    MOUSEEVENTF_LEFTDOWN: ("left", None),
    MOUSEEVENTF_RIGHTDOWN: ("right", None),
    MOUSEEVENTF_MIDDLEDOWN: ("middle", None),
    MOUSEEVENTF_XDOWN: ("x", lambda d: str(int(d or 0))),
}
_MOUSE_UP2BTN = {
    MOUSEEVENTF_LEFTUP: ("left", None),
    MOUSEEVENTF_RIGHTUP: ("right", None),
    MOUSEEVENTF_MIDDLEUP: ("middle", None),
    MOUSEEVENTF_XUP: ("x", lambda d: str(int(d or 0))),
}
_mouse_last_down_ts = {}    # button key -> perf_counter of its DOWN
_mouse_last_up_ts = {}      # button key -> perf_counter of its UP
_mouse_pace_lock = threading.Lock()


def _mouse_btn_key(table, flags, data):
    hit = table.get(flags)
    if hit is None:
        return None
    name, mk = hit
    return name + (":" + mk(data) if mk else "")


def _send_mouse_event(flags: int, data: int = 0):
    """SendInput mouse event with the 1ms hold / 1ms inter-click gap guard.

    DOWN waits until 1ms has passed since that button's last UP; UP waits
    until the button was held 1ms since its last DOWN. Wheels (WHEEL flags)
    and pure moves pass straight through."""
    btn = _mouse_btn_key(_MOUSE_DOWN2BTN, flags, data)
    if btn is not None:
        with _mouse_pace_lock:
            last_up = _mouse_last_up_ts.get(btn)
            if last_up is not None:
                wait = _MOUSE_MIN_GAP_S - (time.perf_counter() - last_up)
                if wait > 0:
                    time.sleep(wait)
            _mouse_last_down_ts[btn] = time.perf_counter()
    elif flags in _MOUSE_UP2BTN:
        btn = _mouse_btn_key(_MOUSE_UP2BTN, flags, data)
        with _mouse_pace_lock:
            last_down = _mouse_last_down_ts.get(btn)
            if last_down is not None:
                wait = _MOUSE_MIN_HOLD_S - (time.perf_counter() - last_down)
                if wait > 0:
                    time.sleep(wait)
            _mouse_last_up_ts[btn] = time.perf_counter()
    union = _INPUT_UNION()
    union.mi = MOUSEINPUT(dx=0, dy=0, mouseData=data, dwFlags=flags,
                          time=0, dwExtraInfo=0)
    inp = INPUT(INPUT_MOUSE, union)
    _send_input(inp)


def middle_click():
    _send_mouse_event(MOUSEEVENTF_MIDDLEDOWN)
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_mouse_event(MOUSEEVENTF_MIDDLEUP)


def right_click():
    _send_mouse_event(MOUSEEVENTF_RIGHTDOWN)
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_mouse_event(MOUSEEVENTF_RIGHTUP)


def xbutton1_click():
    _send_mouse_event(MOUSEEVENTF_XDOWN, data=0x0001)
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_mouse_event(MOUSEEVENTF_XUP, data=0x0001)


def xbutton2_click():
    _send_mouse_event(MOUSEEVENTF_XDOWN, data=0x0002)
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_mouse_event(MOUSEEVENTF_XUP, data=0x0002)


# ── Public input API ─────────────────────────────────────────
# Block-referenced surface (pcr_key_press / pcr_key_hold / pcr_mouse_* /
# pcr_wait_key generators emit macro_engine.<fn>). Game-agnostic raw input —
# no binding remapping, no titles.

_MOUSE_FLAGS = {
    # name: (down flag, up flag, X-button data)
    "left":   (MOUSEEVENTF_LEFTDOWN,   MOUSEEVENTF_LEFTUP,   0x0000),
    "right":  (MOUSEEVENTF_RIGHTDOWN,  MOUSEEVENTF_RIGHTUP,  0x0000),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0x0000),
    "x1":     (MOUSEEVENTF_XDOWN,      MOUSEEVENTF_XUP,      0x0001),
    "x2":     (MOUSEEVENTF_XDOWN,      MOUSEEVENTF_XUP,      0x0002),
}

_MOUSE_VK = {"left": 0x01, "right": 0x02, "middle": 0x04, "x1": 0x05, "x2": 0x06}


def _mouse_button(button: str) -> str:
    name = str(button or "left").strip().lower()
    if name.startswith("mouse:"):
        name = name[6:].strip()
    if name.startswith("mouse_"):
        name = name[6:].strip()
    aliases = {
        "left click": "left", "right click": "right", "middle click": "middle",
        "middle (wheel)": "middle", "wheel": "middle",
        "mouse 4": "x1", "mouse 5": "x2", "mouse 4 (x1)": "x1", "mouse 5 (x2)": "x2",
        "wheel up": "wheel_up", "wheeldown": "wheel_down", "wheel down": "wheel_down",
        "wheelup": "wheel_up",
    }
    name = aliases.get(name, name)
    if name in _MOUSE_FLAGS or name in ("wheel_up", "wheel_down"):
        return name
    return "left"


def _combo_parts(key) -> list[str]:
    s = str(key or "").strip()
    if not s:
        return []
    low = s.lower()
    if low in ("+", "plus", "num add", "num +", "numadd"):
        return [s]
    if "+" not in s:
        return [s]
    parts = [p.strip() for p in s.split("+") if p.strip()]
    return parts or [s]


def _vks_from_combo(key) -> list[int]:
    out: list[int] = []
    for part in _combo_parts(key):
        vk = _binding_to_vk(part)
        if vk is not None:
            out.append(vk)
    return out


def press_key(key, hold_ms: int = 30):
    """Press and release a key by name ('a', 'enter', 'space', 'f5', 'ctrl+c')."""
    vks = _vks_from_combo(key)
    if not vks:
        return False
    for vk in vks:
        _key_down(vk)
    time.sleep(max(int(hold_ms), 1) / 1000.0)
    for vk in reversed(vks):
        _key_up(vk)
    return True


def key_down(key):
    """Hold a key (or combination) down (pair with key_up)."""
    vks = _vks_from_combo(key)
    if not vks:
        return False
    for vk in vks:
        _key_down(vk)
    return True


def key_up(key):
    """Release a held key (or combination)."""
    vks = _vks_from_combo(key)
    if not vks:
        return False
    for vk in reversed(vks):
        _key_up(vk)
    return True


def mouse_down(button="left"):
    """Hold a mouse button down (pair with mouse_up)."""
    down, _up, data = _MOUSE_FLAGS[_mouse_button(button)]
    _send_mouse_event(down, data=data)
    return True


def mouse_up(button="left"):
    """Release a held mouse button."""
    _down, up, data = _MOUSE_FLAGS[_mouse_button(button)]
    _send_mouse_event(up, data=data)
    return True


def mouse_click(button="left"):
    """Press and release a mouse button ('left','right','middle','x1','x2').

    The pcr_mouse_click block generates macro_engine.mouse_click(...) — this
    is the block-referenced surface. 'x1'/'x2' are the side buttons.
    """
    name = _mouse_button(button)
    if name == "wheel_up":
        return scroll(1)
    if name == "wheel_down":
        return scroll(-1)
    if name == "x1":
        xbutton1_click()
        return True
    if name == "x2":
        xbutton2_click()
        return True
    down, up, data = _MOUSE_FLAGS[name]
    _send_mouse_event(down, data=data)
    time.sleep(_CLICK_PRESS_SECONDS)
    _send_mouse_event(up, data=data)
    return True


def scroll(delta: int = 1):
    """Scroll the mouse wheel. Positive = away from user, negative = toward."""
    try:
        notches = int(delta)
    except (TypeError, ValueError):
        return False
    if notches:
        _send_mouse_event(MOUSEEVENTF_WHEEL, data=notches * 120)
    return True


def is_mouse_pressed(button="left") -> bool:
    """True while the given physical mouse button is held."""
    try:
        state = ctypes.windll.user32.GetAsyncKeyState(_MOUSE_VK[_mouse_button(button)])
        return bool(state & 0x8000)
    except Exception:
        return False


# ── .macro file player ───────────────────────────────────────
# .macro format (one instruction per line):
#   LABEL:<name>
#   GOTO:<name>
#   DELAY:<ms>
#   PRINT:<text>            ${var} interpolated, one line in the app console
#   KEY_DOWN:<vk_hex>
#   KEY_UP:<vk_hex>
#   KEY_PRESS:<vk_hex>
#   MOUSE_MOVE_ABS:<x>,<y>
#   MOUSE_MOVE_ABS:scale(<x>,<y>,<rw>,<rh>,<dw>,<dh>)  (scaled to screen)
#   MOUSE_LEFT_DOWN
#   MOUSE_LEFT_UP
#   MOUSE_LEFT_CLICK
#   MOUSE_REL:<dx>,<dy>
#   SMOOTH_MOVE:<dx>,<dy>               (new raw mouse format)
#   SMOOTH_MOVE:<dx>,<dy>,<duration_ms> (legacy format)
#   REPEAT:<n>
#   ENDREPEAT
#   # comment lines

class _MacroStopped(Exception):
    pass


def _print_console(text: str, vars_state: dict, bot_root: str = "",
                   macro_dir: str | None = None) -> None:
    """PRINT:<text> — ${var} interpolation from macro variables, then one
    line in the unified app console (the dashboard Console panel; same
    buffer the flow editor's print block and engine logs feed).

    ${name} reads a macro variable; anything else inside ${...} is parsed
    and evaluated as a full expression — grab_at(...), screen_color(...),
    image/color comparisons, arithmetic — so "create text with" can print
    any value the editor can compose. Unparsable text stays as-is."""
    from macro_engine.macro_text import expr_from_str
    from macro_engine.macro_logic import eval_expr

    def _fmt(v) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        if isinstance(v, (tuple, list)):
            return ", ".join(_fmt(x) for x in v)
        return str(v)

    def _sub(m):
        inner = m.group(1).strip()
        if inner in vars_state:
            return _fmt(vars_state.get(inner))
        # not a plain variable — a full expression (screen reads, image /
        # color checks, arithmetic); evaluation failure keeps the raw text.
        # A bare ${ident} for an undeclared variable also stays raw so
        # typos stay visible in the console (the editor's getter path
        # treats it the same way).
        try:
            node = expr_from_str(inner)
        except Exception:
            return m.group(0)
        if isinstance(node, dict) and list(node.keys()) == ["get"]:
            return m.group(0)
        try:
            return _fmt(eval_expr(node, vars_state, bot_root, macro_dir))
        except Exception:
            return m.group(0)
    msg = re.sub(r"\$\{([^}]*)\}", _sub, str(text))
    try:
        from run import console_buffer
        console_buffer.log(msg, source="macro", level="print")
    except Exception:
        # console_buffer unreachable (frozen EXE / odd sys.path) — the
        # root logger is bridged into the SAME console buffer at INFO+,
        # so route through it instead of bare print(), which a GUI app
        # swallows. The [MACRO] tag lands in the console's source slot.
        log.info("[MACRO] %s", msg)


class MacroPlayer:
    """
    Plays a .macro file synchronously in the calling thread.
    Set player.stop_event to interrupt mid-run.
    """

    def __init__(self, macro_path: str, stop_event: threading.Event | None = None):
        self.macro_path = macro_path
        self.stop_event = stop_event or threading.Event()
        self._sensitivity = _macro_sensitivity_from_lines([])
        self._smooth_carry_x = 0.0
        self._smooth_carry_y = 0.0

    def _check_stop(self):
        if self.stop_event.is_set():
            raise _MacroStopped()

    def _scale_smooth_delta(self, dx: int, dy: int) -> tuple[int, int]:
        rx, ry = _smooth_ratios(self._sensitivity)
        self._smooth_carry_x += dx * rx
        self._smooth_carry_y += dy * ry
        sdx = int(self._smooth_carry_x)
        sdy = int(self._smooth_carry_y)
        self._smooth_carry_x -= sdx
        self._smooth_carry_y -= sdy
        return sdx, sdy

    def _exec_smooth_move(self, raw: str) -> bool:
        parts = [p.strip() for p in raw[12:].split(",")]
        if len(parts) < 2:
            return False
        dx = int(round(_resolve_macro_number(parts[0], getattr(self, "_vars_state", {}))[0]))
        dy = int(round(_resolve_macro_number(parts[1], getattr(self, "_vars_state", {}))[0]))
        duration_ms = 0
        if len(parts) >= 3 and parts[2]:
            try:
                duration_ms = max(0, int(float(parts[2])))
            except Exception:
                duration_ms = 0
        dx, dy = self._scale_smooth_delta(dx, dy)
        if duration_ms > 0:
            _smooth_move_rel(dx, dy, duration_ms, stop_event=self.stop_event)
            return True
        elif dx or dy:
            _mouse_move_rel(dx, dy)
        return False

    def play(self):
        src = self.macro_path
        try:
            from macro_engine import container as _c
            if _c.is_container_file(src):
                src = _c.extract_for_playback(src)   # clean temp + unzip (images/)
        except Exception:
            src = self.macro_path
        with open(src, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip("\n") for l in f.readlines()]
        # v2 pretty .macro files (IF (hp < 20) { … }) are normalized to the
        # v1 line format here; v1 input passes through unchanged
        from macro_engine.macro_text import canonicalize_lines
        lines = canonicalize_lines(lines)
        self._sensitivity = _macro_sensitivity_from_lines(lines)
        self._smooth_carry_x = 0.0
        self._smooth_carry_y = 0.0

        # Do NOT prime_game_mouse_capture() here. That dummy +1/-1 was meant
        # only for the Recorder's first play. On some PCs it knocks the game
        # out of mouse-capture and every following SMOOTH_MOVE turns wrong.

        # Build label index
        labels: dict[str, int] = {}
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("LABEL:"):
                labels[stripped[6:].strip()] = idx

        # Execution loop
        pc = 0                     # program counter
        repeat_stack: list[tuple[int, int, int]] = []  # (start_pc, count, remaining)
        next_due = time.perf_counter()  # accumulated deadline — prevents drift accumulation

        vars_state: dict = {}
        self._vars_state = vars_state
        if_stack: list[dict] = []
        while_stack: list[int] = []   # body-start pc per active WHILE/UNTIL loop
        macro_dir = os.path.dirname(os.path.abspath(src))
        loop_bg: dict = {}            # body-start pc -> BackgroundLoop (WHILE/UNTIL arm)
        watchers: dict = {}           # var name -> BackgroundWatcher (WATCH lines)

        def _arm_bg(lines: list, body_pc: int, registry: dict) -> None:
            """WHILE:/UNTIL: entered and the loop carries a BACKGROUND arm:
            start the arm's thread once (pass 2+ hits the same body-pc key,
            so nothing re-arms)."""
            if body_pc in registry:
                return
            arm = scan_loop_background(lines, body_pc)
            if not arm:
                return
            registry[body_pc] = start_background_loop(
                arm, vars_state, self.stop_event,
                bot_root=_BOT_ROOT, macro_dir=macro_dir,
                print_cb=lambda text, vs: _print_console(text, vs, _BOT_ROOT, macro_dir))

        while pc < len(lines):
            self._check_stop()

            raw = lines[pc].strip()
            pc += 1

            if not raw or raw.startswith("#"):
                continue
            # LOCK { ... } is a re-record envelope, not playback: skip the
            # markers, the steps inside execute normally
            if raw == "LOCK:" or raw == "LOCK_END:":
                continue
            # BACKGROUND arm markers of a WHILE/UNTIL loop — the arm runs on
            # its own thread armed at the WHILE:/UNTIL: line; the main
            # thread never walks the arm's steps: jump the whole arm
            # section (the arm sits AFTER the loop's END marker in v1 order)
            if raw == "BG_BEGIN:":
                j = pc
                while j < len(lines) and lines[j] != "BG_END:":
                    j += 1
                pc = j + 1   # resume after the arm
                continue
            if raw == "BG_END:" or raw.startswith("BG_END:"):
                continue
            # LOOK is the legacy alias of SMOOTH_MOVE (old recordings):
            # rewrites to the modern keyword so the dispatch below runs it
            if raw.startswith("LOOK:"):
                raw = "SMOOTH_MOVE:" + raw[5:]

            if raw.startswith("VARIABLE:"):
                if branch_active(if_stack):
                    define_variable(vars_state, parse_payload(raw, "VARIABLE"))
                continue
            if raw.startswith("SET_VARIABLE:"):
                if branch_active(if_stack):
                    set_variable(vars_state, parse_payload(raw, "SET_VARIABLE"), _BOT_ROOT, macro_dir)
                continue
            # WATCH <var> WHEN (<cond>) EVERY <ms> — keeps <var> at 1/0 on a
            # background thread until macro end or STOP WATCH
            if raw.startswith("WATCH:"):
                if branch_active(if_stack):
                    start_watcher(parse_payload(raw, "WATCH"), vars_state,
                                  self.stop_event, watchers, _BOT_ROOT, macro_dir)
                continue
            if raw.startswith("STOP_WATCH:"):
                if branch_active(if_stack):
                    stop_watcher(raw[11:], watchers)
                continue
            if raw.startswith("IMAGE:"):
                if branch_active(if_stack):
                    run_image_check(vars_state, parse_payload(raw, "IMAGE"), _BOT_ROOT, macro_dir)
                continue
            if raw.startswith("IF:"):
                handle_if(if_stack, vars_state, parse_payload(raw, "IF"), _BOT_ROOT, macro_dir)
                continue
            if raw.startswith("ELSE_IF:"):
                handle_else_if(if_stack, vars_state, parse_payload(raw, "ELSE_IF"), _BOT_ROOT, macro_dir)
                continue
            if raw == "ELSE" or raw.startswith("ELSE:"):
                handle_else(if_stack)
                continue
            if raw == "END_IF" or raw.startswith("END_IF:"):
                handle_end_if(if_stack)
                continue
            # --- WHILE / UNTIL loops (same stack as IF branches) ---
            if raw.startswith("WHILE:"):
                handle_while(if_stack, vars_state, parse_payload(raw, "WHILE"), _BOT_ROOT, macro_dir)
                if if_stack[-1]["active"]:
                    while_stack.append(pc)   # body start (pc already past WHILE line)
                    _arm_bg(lines, pc, loop_bg)
                continue
            if raw.startswith("UNTIL:"):
                handle_while(if_stack, vars_state, parse_payload(raw, "UNTIL"), _BOT_ROOT, macro_dir,
                             invert=True)
                if if_stack[-1]["active"]:
                    while_stack.append(pc)
                    _arm_bg(lines, pc, loop_bg)
                continue
            if raw == "END_WHILE" or raw.startswith("END_WHILE:") or raw == "END_UNTIL" or raw.startswith("END_UNTIL:"):
                pre_body_pc = while_stack[-1] if while_stack else None
                pre_ws = len(while_stack)
                jump = handle_end_while(if_stack, while_stack, vars_state, _BOT_ROOT, macro_dir)
                if jump is not None:
                    pc = jump
                    # fresh DELAY budget for the next pass: the drift
                    # accumulator is per-iteration, so a long pass (image
                    # checks, key holds) can never eat the next pass's
                    # first DELAY down to 0ms — and looping back itself
                    # costs nothing (no hidden pacing delay).
                    next_due = time.perf_counter()
                elif pre_ws > 0 and len(while_stack) < pre_ws and pre_body_pc in loop_bg:
                    # the loop ran and exited — retire its BACKGROUND arm
                    loop_bg.pop(pre_body_pc).stop()
                continue
            if not branch_active(if_stack):
                continue

            # --- LABEL ---
            if raw.startswith("LABEL:"):
                continue  # labels are just markers

            # --- GOTO ---
            if raw.startswith("GOTO:"):
                target = raw[5:].strip()
                if target in labels:
                    pc = labels[target]
                else:
                    log.warning(f"GOTO: unknown label '{target}'")
                continue

            # --- DELAY ---
            if raw.startswith("DELAY:"):
                ms = int(round(_resolve_macro_number(raw[6:].strip(), vars_state)[0]))
                next_due += ms / 1000.0
                _sleep_until(next_due, self._check_stop)
                continue

            # --- PRINT (app console) ---
            # bare "PRINT" (empty text, e.g. a hand-edited file or the
            # pretty printer with an empty value) prints an empty line —
            # it is never silently dropped
            if raw == "PRINT" or raw.startswith("PRINT:"):
                _print_console(raw[6:] if raw.startswith("PRINT:") else "",
                               vars_state, _BOT_ROOT, macro_dir)
                continue

            # --- REPEAT ---
            if raw.startswith("REPEAT:"):
                count = int(round(_resolve_macro_number(raw[7:].strip(), vars_state)[0]))
                repeat_stack.append((pc, count, count))
                continue

            if raw == "ENDREPEAT":
                if repeat_stack:
                    start_pc, total, remaining = repeat_stack[-1]
                    remaining -= 1
                    if remaining > 0:
                        repeat_stack[-1] = (start_pc, total, remaining)
                        pc = start_pc
                        # fresh DELAY budget per pass (same as WHILE/UNTIL)
                        next_due = time.perf_counter()
                    else:
                        repeat_stack.pop()
                continue

            # --- KEY ---
            if raw.startswith("KEY_DOWN:"):
                _key_down(int(raw[9:].strip(), 16))
                continue
            if raw.startswith("KEY_UP:"):
                _key_up(int(raw[7:].strip(), 16))
                continue
            if raw.startswith("KEY_PRESS:"):
                _key_press(int(raw[10:].strip(), 16))
                next_due = max(next_due, time.perf_counter())
                continue

            # --- MOUSE ---
            if raw.startswith("MOUSE_MOVE_ABS:"):
                rest = raw[15:].strip()
                if rest.startswith("scale("):
                    # scale(x, y, rw, rh, dw, dh) — a point recorded at
                    # dw x dh (content ratio rw:rh), mapped into the current
                    # screen's centered content area (1:1 with the flow
                    # editor's scale block). Vars work in every slot.
                    args = rest[len("scale("):-1].split(",")
                    vals = []
                    for a in args:
                        v, _ = _resolve_macro_number(a.strip(), vars_state)
                        vals.append(int(round(v)))
                    if len(vals) >= 6:
                        spec = (vals[2], vals[3], vals[4], vals[5])
                    elif len(vals) >= 2:
                        spec = (16, 9, 1920, 1080)
                    else:
                        vals = [0, 0]
                        spec = (16, 9, 1920, 1080)
                    sx, sy = _macro_res_scale((vals[0], vals[1]), spec)[:2]
                    _mouse_move_abs(sx, sy)
                    continue
                parts = rest.split(",")
                x_raw, x_from_var = _resolve_macro_number(parts[0], vars_state)
                y_raw, y_from_var = _resolve_macro_number(parts[1], vars_state)
                x, y = _scale_macro_abs_xy(int(round(x_raw)), int(round(y_raw)))
                if x_from_var:
                    x = int(round(x_raw))
                if y_from_var:
                    y = int(round(y_raw))
                _mouse_move_abs(x, y)
                continue
            if raw == "MOUSE_LEFT_DOWN":
                _mouse_left_down()
                continue
            if raw == "MOUSE_LEFT_UP":
                _mouse_left_up()
                continue
            if raw == "MOUSE_LEFT_CLICK":
                _mouse_left_click()
                next_due = max(next_due, time.perf_counter())
                continue
            if raw == "MOUSE_RIGHT_DOWN":
                _send_mouse_event(MOUSEEVENTF_RIGHTDOWN)
                continue
            if raw == "MOUSE_RIGHT_UP":
                _send_mouse_event(MOUSEEVENTF_RIGHTUP)
                continue
            if raw == "MOUSE_RIGHT_CLICK":
                right_click()
                next_due = max(next_due, time.perf_counter())
                continue
            if raw == "MOUSE_MIDDLE_DOWN":
                _send_mouse_event(MOUSEEVENTF_MIDDLEDOWN)
                continue
            if raw == "MOUSE_MIDDLE_UP":
                _send_mouse_event(MOUSEEVENTF_MIDDLEUP)
                continue
            if raw == "MOUSE_MIDDLE_CLICK":
                middle_click()
                next_due = max(next_due, time.perf_counter())
                continue
            if raw.startswith("PLAY_MACRO:"):
                target = raw[11:].strip()
                if target:
                    sub_path = target
                    if not os.path.isabs(sub_path):
                        base_dir = os.path.dirname(os.path.abspath(self.macro_path))
                        sub_path = os.path.join(base_dir, sub_path)
                        if not os.path.isfile(sub_path):
                            sub_path = os.path.join(MACROS_DIR, target)
                    if os.path.isfile(sub_path):
                        from macro_engine import container as _c
                        if _c.is_container_file(sub_path):
                            sub_path = _c.extract_for_playback(sub_path)
                        sub = MacroPlayer(sub_path, stop_event=self.stop_event)
                        sub.play()
                    else:
                        log.warning(f"PLAY_MACRO: file not found '{target}'")
                continue
            if raw.startswith("MOUSE_REL:"):
                parts = raw[10:].split(",")
                dx = int(round(_resolve_macro_number(parts[0], vars_state)[0]))
                dy = int(round(_resolve_macro_number(parts[1], vars_state)[0]))
                _mouse_move_rel(dx, dy)
                continue
            if raw.startswith("SMOOTH_MOVE:"):
                # Instant camera packets still take wall time (SendInput). If we
                # leave next_due in the past, the following DELAY:8 / walk DELAY
                # catch-up-shrinks to 0 → 'stops halfway' / 'hits the air'.
                self._exec_smooth_move(raw)
                next_due = max(next_due, time.perf_counter())
                continue

            log.debug(f"MacroPlayer: unknown instruction '{raw}'")

        # macro done — nothing outlives it: BACKGROUND arms already stopped
        # with their loops (or with the stop_event); WATCH watchers live
        # until this line
        try:
            stop_all_watchers(watchers)
            for bg in list(loop_bg.values()):
                bg.stop()
        except Exception:
            pass


# ── Legacy compatibility ─────────────────────────────────────

_active_stop_event: threading.Event | None = None
_active_thread:     threading.Thread | None = None
_active_lock = threading.RLock()


def _release_held_inputs_now():
    """Best-effort emergency key/mouse release."""
    try:
        _mouse_left_up()
    except Exception:
        pass
    for vk in _HELD_KEYS:
        try:
            _key_up(vk)
        except Exception:
            pass


def _request_stop_active(wait_timeout: float = 0.0) -> bool:
    """Signal active macro stop; optionally wait for thread exit.
    Returns True when no active thread remains."""
    with _active_lock:
        stop_ev = _active_stop_event
        t = _active_thread
    if stop_ev is not None:
        stop_ev.set()
    if wait_timeout > 0 and t is not None and t.is_alive():
        t.join(timeout=max(0.0, wait_timeout))
    with _active_lock:
        alive = (_active_thread is not None and _active_thread.is_alive())
        return not alive


def run_macro(name: str, wait: bool = True):
    """
    Run a .macro file by name (without extension).
    If wait=True, blocks until done.  If wait=False, runs in a daemon thread.
    Returns bool (wait=True) or a handle with .wait()/.poll() (wait=False).
    """
    global _active_stop_event, _active_thread, _active_path

    path = _resolve_macro_path(name)
    if not os.path.exists(path):
        log.error(f"Macro not found: {path}")
        return None

    # Kill any running macro first — but only if one is actually active.
    # If nothing is running (_active_stop_event is None), calling stop_macro()
    # would fire a spurious MOUSE_LEFT_UP which interrupts baserock farming
    # between consecutive macro iterations (each wait=True run already
    # finished cleanly, so there is nothing to kill).
    if not _request_stop_active(wait_timeout=1.5):
        log.error(f"Could not start macro '{name}': previous macro thread still active")
        return None
    _release_held_inputs_now()
    mouse_settings_snapshot = _prepare_windows_mouse_compatibility()
    _boost_playback_timing()

    stop_ev = threading.Event()
    player  = MacroPlayer(path, stop_ev)

    if wait:
        # Register the stop event so stop_macro() / F9 can interrupt even a
        # blocking (wait=True) macro run.
        with _active_lock:
            _active_stop_event = stop_ev
            _active_thread = None
            _active_path = path
        _ok = True
        try:
            player.play()
        except _MacroStopped:
            log.debug(f"Macro '{name}' stopped early by kill signal")
            _ok = False
        finally:
            # Clear registration when done (whether normal exit or interrupted)
            with _active_lock:
                if _active_stop_event is stop_ev:
                    _active_stop_event = None
                _active_thread = None
                if _active_path == path:
                    _active_path = ""
            _restore_windows_mouse_settings(mouse_settings_snapshot)
        try:
            try:
                from run.overlay import notify_macro_end       # forge build layout
            except ImportError:
                from overlay import notify_macro_end            # bot layout (code/overlay.py)
            notify_macro_end(name)
        except Exception:
            pass
        return _ok

    else:
        # Run in a daemon background thread
        def _runner():
            global _active_stop_event, _active_thread, _active_path
            try:
                player.play()
            except _MacroStopped:
                log.debug(f"Macro '{name}' stopped early by kill signal")
            finally:
                with _active_lock:
                    if _active_stop_event is stop_ev:
                        _active_stop_event = None
                    if _active_thread is t:
                        _active_thread = None
                    if _active_path == path:
                        _active_path = ""
                _restore_windows_mouse_settings(mouse_settings_snapshot)
            try:
                try:
                    from run.overlay import notify_macro_end       # forge build layout
                except ImportError:
                    from overlay import notify_macro_end            # bot layout (code/overlay.py)
                notify_macro_end(name)
            except Exception:
                pass

        t = threading.Thread(target=_runner, daemon=True, name=f"macro-{name}")
        with _active_lock:
            _active_stop_event = stop_ev
            _active_thread = t
            _active_path = path
        t.start()

        # Return a thin handle so callers can do proc.wait() like before
        class _Handle:
            def wait(self):
                t.join()
            def poll(self):
                return None if t.is_alive() else 0

        return _Handle()


# Keys that macros may hold down.
_HELD_KEYS = [
    0x57, 0x41, 0x53, 0x44,  # W A S D
    0xA2,                    # Left Ctrl
    0xA0,                    # Left Shift
]

def stop_macro():
    """Signal the currently running macro (if any) to stop — INSTANT.
    Sets the stop event and releases all held keys immediately.
    Does NOT join/wait for the thread — returns in microseconds."""
    _request_stop_active(wait_timeout=0.0)
    _release_held_inputs_now()


# Backwards-compatibility alias — bot.py imports this name
kill_macro_recorder = stop_macro
