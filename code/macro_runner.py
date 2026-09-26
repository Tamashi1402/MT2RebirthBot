# ============================================================
# MT2 REBIRTH BOT - MACRO RUNNER  (native .macro player)
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
from config import MACROS_DIR, FOCUS_RECHECK_DELAY
from macro_logic import (
    branch_active,
    define_variable,
    handle_else_if,
    handle_end_if,
    handle_if,
    parse_payload,
    run_image_check,
    set_variable,
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


def _resolve_macro_path(name: str) -> str:
    """Macros live flat in MACROS_DIR — no preset subdirectories."""
    raw = str(name or "").strip().replace("\\", "/")
    if not raw:
        return os.path.join(MACROS_DIR, ".macro")
    if raw.lower().endswith(".macro"):
        raw = raw[:-6]

    rel_candidates: list[str] = []
    if "/" in raw:
        rel_candidates.append(raw)
    else:
        rel_candidates.append(raw)
        rel_candidates.append(f"teleports/{raw}")
        rel_candidates.append(f"engine/{raw}")
        rel_candidates.append(f"rebirth_mode/{raw}")
        rel_candidates.append(f"rebirth_mode/quests/{raw}")
        rel_candidates.append(f"meteor_mode/{raw}")
        rel_candidates.append(f"crater_mode/{raw}")
        m_short = re.match(r"^a(\d+)_(.+)$", raw)
        if m_short:
            alt = f"area{m_short.group(1)}_{m_short.group(2)}"
            rel_candidates.append(alt)
            rel_candidates.append(f"meteor_mode/{alt}")
            rel_candidates.append(f"rebirth_mode/area{m_short.group(1)}/{alt}")
        for area in range(1, 9):
            if raw.startswith(f"area{area}_") or raw.startswith(f"a{area}_"):
                rel_candidates.append(f"rebirth_mode/area{area}/{raw}")
            if raw.startswith(f"base_to_a{area}_") or raw.startswith(f"base_to_a{area}.") or raw == "base_to_area6":
                rel_candidates.append(f"rebirth_mode/area{area}/{raw}")
        if raw.startswith(("base_to_", "teleport_to_")):
            rel_candidates.append(f"teleports/{raw}")
        if raw.startswith(("area7_", "kraken_", "fight_kraken")):
            rel_candidates.append(f"kraken_mode/{raw}")
        if raw.startswith(("area8_", "zytos_", "fight_zytos", "a8_to_zytos")):
            rel_candidates.append(f"zytos_mode/{raw}")
        if raw.startswith(("delve_", "area5_to_delve")):
            rel_candidates.append(f"delve_mode/{raw}")

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

    if "/" not in raw:
        target = f"{raw}.macro".lower()
        matches: list[str] = []
        for root, _dirs, files in os.walk(MACROS_DIR):
            for file_name in files:
                if file_name.lower() == target:
                    matches.append(os.path.join(root, file_name))
        if matches:
            return sorted(matches, key=lambda p: (len(os.path.relpath(p, MACROS_DIR)), p.lower()))[0]

    return candidates[0] if candidates else os.path.join(MACROS_DIR, f"{raw}.macro")


def macro_exists(name: str) -> bool:
    return os.path.isfile(_resolve_macro_path(name))


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

    Fortnite is foreground while we play, so the bot is a background process.
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
_GetForegroundWindow  = ctypes.windll.user32.GetForegroundWindow
_GetWindowTextW       = ctypes.windll.user32.GetWindowTextW
_GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
_ShowWindow           = ctypes.windll.user32.ShowWindow
_SetForegroundWindow  = ctypes.windll.user32.SetForegroundWindow
_EnumWindows          = ctypes.windll.user32.EnumWindows
_GetSystemMetrics     = ctypes.windll.user32.GetSystemMetrics
_MapVirtualKeyW       = ctypes.windll.user32.MapVirtualKeyW
_GetCurrentThreadId   = ctypes.windll.kernel32.GetCurrentThreadId
_GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
_GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
_GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
_AttachThreadInput    = ctypes.windll.user32.AttachThreadInput
_AttachThreadInput.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.c_bool]
_AttachThreadInput.restype = ctypes.c_bool
SW_RESTORE = 9

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


def _attach_fortnite_input() -> tuple[int, int] | None:
    """Attach our thread to Fortnite's so SetForegroundWindow is allowed.

    Win10/11 blocks focus steal unless the threads share input state.
    This is only for focusing the game — detach immediately after.
    Keeping it attached during SMOOTH_MOVE shares key/mouse state with
    Fortnite and can eat or double camera packets (Raw Input game).
    """
    try:
        hwnd = _find_fortnite_hwnd()
        if not hwnd:
            return None
        pid = ctypes.wintypes.DWORD(0)
        their = int(_GetWindowThreadProcessId(hwnd, ctypes.byref(pid)))
        ours = int(_GetCurrentThreadId())
        if not their or their == ours:
            return None
        if _AttachThreadInput(ours, their, True):
            return ours, their
    except Exception:
        pass
    return None


def _detach_fortnite_input(pair: tuple[int, int] | None) -> None:
    if not pair:
        return
    try:
        _AttachThreadInput(int(pair[0]), int(pair[1]), False)
    except Exception:
        pass


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


# down->up gap for a synthesized click: 1ms (was 50ms). Identical to the
# blockly/MacroEngine playback path (macro_engine/playback.py uses
# _CLICK_PRESS_S = 0.001 and routes every button event through the 1ms
# pacing guard in _send_mouse_event). 50ms stretched run-mode playback
# well past the recorded wall-clock and made clicks feel nothing like
# editor playback.
_CLICK_PRESS_SECONDS = 0.001


def _mouse_left_down():
    _send_mouse_event(MOUSEEVENTF_LEFTDOWN)


def _mouse_left_up():
    _send_mouse_event(MOUSEEVENTF_LEFTUP)


def _mouse_left_click():
    _mouse_left_down()
    time.sleep(_CLICK_PRESS_SECONDS)
    _mouse_left_up()


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

    if re.fullmatch(r"NUMPAD_[0-9]", name) or re.fullmatch(r"NUMPAD[0-9]", name):
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


# Recorded-macro key interception. Macros were authored on default Fortnite
# binds (WASD / Space / Shift / Ctrl / 1 / 2 / F). If the user remaps those in
# Config, every KEY_DOWN / KEY_UP / KEY_PRESS of the recorded default vk is
# replaced with the live bind at playback time.
_MACRO_REMAP_SPECS = (
    ("FORWARD_BINDING", "W", (0x57,)),
    ("BACKWARD_BINDING", "S", (0x53,)),
    ("LEFT_BINDING", "A", (0x41,)),
    ("RIGHT_BINDING", "D", (0x44,)),
    ("JUMP_BINDING", "SPACE", (0x20,)),
    ("SPRINT_BINDING", "SHIFT", (0xA0, 0x10, 0xA1)),
    ("CROUCH_BINDING", "CTRL", (0xA2, 0x11, 0xA3)),
    ("WEAPON_1_BINDING", "1", (0x31,)),
    ("MONITOR_ITEM_BINDING", "2", (0x32,)),
    ("PICKAXE_EQUIP_BINDING", "F", (0x46,)),
)


def _live_binding(cfg_key: str, default: str) -> str:
    try:
        import config as _cfg
        raw = getattr(_cfg, cfg_key, default)
    except Exception:
        raw = default
    return str(raw or default).strip() or default


def macro_vk_remap_table() -> dict[int, int]:
    table: dict[int, int] = {}
    # Generic SHIFT/CTRL (0x10/0x11) are the same keys as LSHIFT/LCTRL.
    # Never rewrite 0xA0→0x10 on default Config — that changes scan codes.
    same_family = {
        0x10: {0x10, 0xA0, 0xA1},
        0xA0: {0x10, 0xA0, 0xA1},
        0xA1: {0x10, 0xA0, 0xA1},
        0x11: {0x11, 0xA2, 0xA3},
        0xA2: {0x11, 0xA2, 0xA3},
        0xA3: {0x11, 0xA2, 0xA3},
    }
    for cfg_key, default, sources in _MACRO_REMAP_SPECS:
        dest = _binding_to_vk(_live_binding(cfg_key, default))
        if dest is None:
            continue
        for src in sources:
            src = int(src)
            dest_i = int(dest)
            if dest_i == src:
                continue
            if dest_i in same_family.get(src, set()):
                continue
            table[src] = dest_i
    return table


def remap_macro_vk(vk: int) -> int:
    """Map a recorded default vk to the user's current Config bind."""
    try:
        vk = int(vk)
    except Exception:
        return vk
    return macro_vk_remap_table().get(vk, vk)


def remapped_movement_vks() -> list[int]:
    """Default WASD/jump/sprint/crouch vks plus whatever they remap to."""
    vks = [0x57, 0x41, 0x53, 0x44, 0x20, 0xA0, 0xA1, 0xA2, 0xA3, 0x10, 0x11]
    table = macro_vk_remap_table()
    vks.extend(table.values())
    vks.extend(table.keys())
    out = []
    seen = set()
    for vk in vks:
        if vk in seen:
            continue
        seen.add(vk)
        out.append(int(vk))
    return out


def binding_to_keyboard_name(binding: str, fallback: str = "") -> str:
    """keyboard-lib key name for a Config binding (letters, space, shift, ...)."""
    from config import normalize_binding_name
    b = normalize_binding_name(binding) or normalize_binding_name(fallback)
    if not b:
        return str(fallback or "").strip().lower()
    alias = {
        "ESC": "esc", "ESCAPE": "esc", "SPACE": "space", "TAB": "tab",
        "ENTER": "enter", "RETURN": "enter",
        "SHIFT": "shift", "LSHIFT": "shift", "LEFT_SHIFT": "shift", "L_SHIFT": "shift",
        "CTRL": "ctrl", "CONTROL": "ctrl", "LCTRL": "ctrl", "LEFT_CTRL": "ctrl", "L_CTRL": "ctrl",
        "ALT": "alt", "LALT": "alt", "LEFT_ALT": "alt",
    }
    if b in alias:
        return alias[b]
    return b.lower()


def live_wasd() -> dict[str, tuple[str, int]]:
    """Map recorded WASD letters to (keyboard_name, vk) using live Config."""
    specs = {
        "w": ("FORWARD_BINDING", "W"),
        "a": ("LEFT_BINDING", "A"),
        "s": ("BACKWARD_BINDING", "S"),
        "d": ("RIGHT_BINDING", "D"),
    }
    out = {}
    for letter, (cfg_key, default) in specs.items():
        binding = _live_binding(cfg_key, default)
        vk = _binding_to_vk(binding) or _binding_to_vk(default) or ord(default)
        out[letter] = (binding_to_keyboard_name(binding, default), int(vk))
    return out


# ── Window helpers ───────────────────────────────────────────

def _get_window_title(hwnd: int) -> str:
    length = _GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    _GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _find_fortnite_hwnd():
    result = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

    def _cb(hwnd, _):
        if "Fortnite" in _get_window_title(hwnd):
            result.append(hwnd)
        return True

    _EnumWindows(EnumWindowsProc(_cb), 0)
    return result[0] if result else None


# ── Focus helpers ────────────────────────────────────────────

def is_fortnite_focused() -> bool:
    hwnd = _GetForegroundWindow()
    title = _get_window_title(hwnd)
    result = "Fortnite" in title
    from logger import debug_on_change
    debug_on_change("fg", f"Foreground: {title!r} focused={result}")
    return result


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

    hwnd = _find_fortnite_hwnd()
    if hwnd:
        try:
            fn_dpi = int(ctypes.windll.user32.GetDpiForWindow(hwnd))
            bits.append(
                f"dpi_fortnite={fn_dpi} ({round(fn_dpi * 100 / 96)}%) hwnd=0x{int(hwnd):X}"
            )
        except Exception:
            bits.append(f"dpi_fortnite=? hwnd=0x{int(hwnd):X}")
        try:
            title = _get_window_title(hwnd)
            fg = _GetForegroundWindow()
            bits.append(f"fortnite_title={title!r}  focused={int(fg) == int(hwnd)}")
        except Exception:
            pass
        try:
            class _RECT(ctypes.Structure):
                _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                            ("r", ctypes.c_long), ("b", ctypes.c_long)]
            rc = _RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rc))
            bits.append(
                f"fortnite_rect={rc.l},{rc.t},{rc.r},{rc.b}  "
                f"size={rc.r - rc.l}x{rc.b - rc.t}"
            )
        except Exception:
            pass
    else:
        bits.append("fortnite_window=not_found")

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
        kb = [
            ("W", "FORWARD_BINDING"),
            ("S", "BACKWARD_BINDING"),
            ("A", "LEFT_BINDING"),
            ("D", "RIGHT_BINDING"),
            ("SPACE", "JUMP_BINDING"),
            ("SHIFT", "SPRINT_BINDING"),
            ("CTRL", "CROUCH_BINDING"),
            ("F", "PICKAXE_EQUIP_BINDING"),
        ]
        mapped = []
        for default, key in kb:
            val = str(getattr(_cfg_env, key, default) or default).strip().upper()
            mark = "" if val == default else "!"
            mapped.append(f"{key.split('_')[0].lower()}={val}{mark}")
        bits.append("keybinds " + " ".join(mapped) + "  (! = not default)")
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


def focus_fortnite():
    """Force Fortnite to the foreground. Always tries, even if already 'focused'.

    Dashboard Start / overlay can steal focus; the first F4/loadout click then
    lands on the wrong window. AttachThreadInput is only used for this steal
    and is detached immediately after.
    """
    hwnd = _find_fortnite_hwnd()
    if not hwnd:
        log.warning("Could not find Fortnite window handle")
        return False
    already = False
    try:
        already = is_fortnite_focused()
    except Exception:
        already = False
    pair = _attach_fortnite_input()
    try:
        if not already:
            # Alt pulse: Win10/11 allows SetForegroundWindow after a key event
            # from this process. Skip if Fortnite already has focus (don't
            # toggle the in-game Alt overlay).
            try:
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
            except Exception:
                pass
        _ShowWindow(hwnd, SW_RESTORE)
        try:
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except Exception:
            pass
        _SetForegroundWindow(hwnd)
        time.sleep(0.20)
        ok = False
        try:
            ok = is_fortnite_focused()
        except Exception:
            ok = False
        log.debug(f"[FOCUS] Fortnite hwnd=0x{int(hwnd):X} focused={ok} (was={already})")
        return ok
    except Exception as e:
        log.debug(f"focus_fortnite() warning: {e}")
        return False
    finally:
        _detach_fortnite_input(pair)


def prime_game_mouse_capture() -> None:
    """Burn a dummy relative move so the first recorded camera turn is not skipped.

    When the game window is not yet capturing the mouse, Windows (and Fortnite)
    consume the first relative-move as focus/capture instead of a camera turn.
    That used to drop the first SMOOTH_MOVE in a macro, especially on the
    Recorder's first play. Focus the game, then send a canceling +1/-1 pair.
    """
    try:
        if not is_fortnite_focused():
            focus_fortnite()
    except Exception:
        pass
    try:
        _raw_mouse_move_rel(0, 0)
        time.sleep(0.03)
        _raw_mouse_move_rel(1, 0)
        time.sleep(0.015)
        _raw_mouse_move_rel(-1, 0)
        time.sleep(0.08)
    except Exception as e:
        log.debug(f"prime_game_mouse_capture() warning: {e}")


def wait_for_fortnite_focus(timeout: float = 300) -> bool:
    log.debug("Waiting for Fortnite to be focused...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_fortnite_focused():
            log.debug(f"Fortnite focused — waiting {FOCUS_RECHECK_DELAY}s before proceeding")
            time.sleep(FOCUS_RECHECK_DELAY)
            return True
        time.sleep(1)
    return False


# ── Middle-mouse click ───────────────────────────────────────

# -- Click pacing guard (identical to macro_engine/macro_runner) ----------
# Fortnite-verified: a click registers only when 1) the button is held
# >= 1ms between DOWN and UP, AND 2) >= 1ms passes after UP before the
# next DOWN. 0ms in either slot and the game merges/eats the click.
# Blockly playback routes ALL button events through this guard, so run
# mode must too - shared state, same rule.
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


def enable_auto_strength():
    from screen import is_auto_strength_active
    if not is_auto_strength_active():
        import config as _cfg
        binding = getattr(_cfg, "AUTO_STRENGTH_TOGGLE_BINDING", "MOUSE_MIDDLE")
        log.debug(f"Enabling auto-strength ({binding})")
        trigger_binding_action(binding, hold_ms=30)
        time.sleep(0.5)


def disable_auto_strength():
    from screen import is_auto_strength_active
    if is_auto_strength_active():
        import config as _cfg
        binding = getattr(_cfg, "AUTO_STRENGTH_TOGGLE_BINDING", "MOUSE_MIDDLE")
        log.debug(f"Disabling auto-strength ({binding})")
        trigger_binding_action(binding, hold_ms=30)
        time.sleep(0.5)


# ── .macro file player ───────────────────────────────────────
# .macro format (one instruction per line):
#   LABEL:<name>
#   GOTO:<name>
#   DELAY:<ms>
#   KEY_DOWN:<vk_hex>
#   KEY_UP:<vk_hex>
#   KEY_PRESS:<vk_hex>
#   MOUSE_MOVE_ABS:<x>,<y>
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
        # .macro v3 containers unzip to a clean temp first - mirrors the
        # blockly/MacroEngine playback path (macro_engine/playback.py)
        try:
            from macro_engine import container as _c
            if _c.is_container_file(src):
                src = _c.extract_for_playback(src)
        except Exception:
            src = self.macro_path
        with open(src, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip("\n") for l in f.readlines()]
        # v2 pretty .macro files (IF (hp < 20) { ... }) normalize to the v1
        # engine line format - same canonicalization blockly playback does;
        # v1 input passes through unchanged
        try:
            from macro_engine.macro_text import canonicalize_lines
            lines = canonicalize_lines(lines)
        except Exception:
            pass
        self._sensitivity = _macro_sensitivity_from_lines(lines)
        self._smooth_carry_x = 0.0
        self._smooth_carry_y = 0.0

        # Priming (dummy +1/-1 capture pair) is NOT done here - it happens
        # once per run in run_macro(), matching blockly/MacroEngine playback
        # (macro_engine/playback.py primes before every play).

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
        macro_dir = os.path.dirname(os.path.abspath(src))

        while pc < len(lines):
            self._check_stop()

            raw = lines[pc].strip()
            pc += 1

            if not raw or raw.startswith("#"):
                continue
            # LOCK { ... } is a re-record envelope, not playback: skip the
            # markers, the steps inside execute normally (blockly parity)
            if raw == "LOCK:" or raw.startswith("LOCK_END:"):
                continue
            # BACKGROUND arm markers of a WHILE/UNTIL loop - the arm runs on
            # its own thread in the editor; run mode has no arm support, so
            # jump the whole section exactly like blockly's main thread does
            if raw == "BG_BEGIN:":
                j = pc
                while j < len(lines) and lines[j] != "BG_END:":
                    j += 1
                pc = j + 1   # resume after the arm
                continue
            if raw == "BG_END:" or raw.startswith("BG_END:"):
                continue
            # LOOK is the legacy alias of SMOOTH_MOVE (old recordings)
            if raw.startswith("LOOK:"):
                raw = "SMOOTH_MOVE:" + raw[5:]

            if raw.startswith("VARIABLE:"):
                if branch_active(if_stack):
                    define_variable(vars_state, parse_payload(raw, "VARIABLE"))
                continue
            if raw.startswith("SET_VARIABLE:"):
                if branch_active(if_stack):
                    set_variable(vars_state, parse_payload(raw, "SET_VARIABLE"))
                continue
            if raw.startswith("IMAGE:"):
                if branch_active(if_stack):
                    run_image_check(vars_state, parse_payload(raw, "IMAGE"), _BOT_ROOT, macro_dir)
                continue
            if raw.startswith("IF:"):
                handle_if(if_stack, vars_state, parse_payload(raw, "IF"))
                continue
            if raw.startswith("ELSE_IF:"):
                handle_else_if(if_stack, vars_state, parse_payload(raw, "ELSE_IF"))
                continue
            if raw == "END_IF" or raw.startswith("END_IF:"):
                handle_end_if(if_stack)
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
                    else:
                        repeat_stack.pop()
                continue

            # --- KEY ---
            if raw.startswith("KEY_DOWN:"):
                _key_down(remap_macro_vk(int(raw[9:].strip(), 16)))
                continue
            if raw.startswith("KEY_UP:"):
                _key_up(remap_macro_vk(int(raw[7:].strip(), 16)))
                continue
            if raw.startswith("KEY_PRESS:"):
                # no next_due push: the blockly/MacroEngine player lets the
                # 30ms hold overlap into the next DELAY (accumulated-deadline
                # catch-up), so total timing equals the recording exactly
                _key_press(remap_macro_vk(int(raw[10:].strip(), 16)))
                continue

            # --- MOUSE ---
            if raw.startswith("MOUSE_MOVE_ABS:"):
                parts = raw[15:].split(",")
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
                # no next_due push - blocky parity (see KEY_PRESS note)
                _mouse_left_click()
                continue
            if raw == "MOUSE_RIGHT_DOWN":
                _send_mouse_event(MOUSEEVENTF_RIGHTDOWN)
                continue
            if raw == "MOUSE_RIGHT_UP":
                _send_mouse_event(MOUSEEVENTF_RIGHTUP)
                continue
            if raw == "MOUSE_RIGHT_CLICK":
                right_click()
                continue
            if raw == "MOUSE_MIDDLE_DOWN":
                _send_mouse_event(MOUSEEVENTF_MIDDLEDOWN)
                continue
            if raw == "MOUSE_MIDDLE_UP":
                _send_mouse_event(MOUSEEVENTF_MIDDLEUP)
                continue
            if raw == "MOUSE_MIDDLE_CLICK":
                middle_click()
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
    global _active_stop_event, _active_thread

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
    # Prime game mouse capture with the canceling +1/-1 pair before every
    # run - blockly/MacroEngine playback primes before every play, and
    # without it the game can swallow the first SMOOTH_MOVE, which made
    # run-mode camera turns land short ('tight') vs editor playback.
    prime_game_mouse_capture()

    stop_ev = threading.Event()
    player  = MacroPlayer(path, stop_ev)

    if wait:
        # Register the stop event so stop_macro() / F9 can interrupt even a
        # blocking (wait=True) macro run.
        with _active_lock:
            _active_stop_event = stop_ev
            _active_thread = None
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
            _restore_windows_mouse_settings(mouse_settings_snapshot)
        try:
            from overlay import notify_macro_end
            notify_macro_end(name)
        except Exception:
            pass
        return _ok

    else:
        # Run in a daemon background thread
        def _runner():
            global _active_stop_event, _active_thread
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
                _restore_windows_mouse_settings(mouse_settings_snapshot)
            try:
                from overlay import notify_macro_end
                notify_macro_end(name)
            except Exception:
                pass

        t = threading.Thread(target=_runner, daemon=True, name=f"macro-{name}")
        with _active_lock:
            _active_stop_event = stop_ev
            _active_thread = t
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
