# ============================================================
# CRATER - INPUT (Win32 ctypes)
# Raw mouse_event for relative moves, SendInput for keys/clicks.
# ============================================================
import ctypes
import ctypes.wintypes
import time
import re

from logger import get_logger
log = get_logger()

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_ABSOLUTE   = 0x8000
MOUSEEVENTF_MOVE_ABS   = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
KEYEVENTF_SCANCODE     = 0x0008
KEYEVENTF_KEYUP        = 0x0002
KEYEVENTF_EXTENDEDKEY  = 0x0001
ULONG_PTR = ctypes.c_size_t

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR)]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ULONG_PTR)]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", _INPUT_UNION)]

_SendInput        = ctypes.windll.user32.SendInput
_GetSystemMetrics  = ctypes.windll.user32.GetSystemMetrics
_MapVirtualKeyW    = ctypes.windll.user32.MapVirtualKeyW
_mouse_event_fn   = ctypes.windll.user32.mouse_event
_mouse_event_fn.restype = None
_mouse_event_fn.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                           ctypes.c_uint, ctypes.POINTER(ctypes.c_ulong)]
try:
    ctypes.WinDLL("winmm").timeBeginPeriod(1)
except Exception:
    pass

def _send_input(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    _SendInput(len(inputs), arr, ctypes.sizeof(INPUT))

def _make_mouse(flags, dx=0, dy=0, data=0):
    u = _INPUT_UNION()
    u.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags,
                      time=0, dwExtraInfo=0)
    return INPUT(INPUT_MOUSE, u)

def _is_extended_vk(vk):
    return vk in {0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x2D,0x2E,0xA3,0xA5}

def _make_key(vk, is_up):
    scan = _MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE
    if is_up: flags |= KEYEVENTF_KEYUP
    if _is_extended_vk(vk): flags |= KEYEVENTF_EXTENDEDKEY
    extra = ctypes.c_ulong(0)
    u = _INPUT_UNION()
    u.ki = KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags,
                     time=0, dwExtraInfo=0)
    return INPUT(INPUT_KEYBOARD, u)

def mouse_move_rel(dx, dy):
    try:
        from macro_runner import _raw_mouse_move_rel
        _raw_mouse_move_rel(int(dx), int(dy))
        return
    except Exception:
        pass
    _send_input(_make_mouse(MOUSEEVENTF_MOVE | MOUSEEVENTF_MOVE_NOCOALESCE, int(dx), int(dy)))

def mouse_move_abs(x, y):
    sw = _GetSystemMetrics(0) or 1920
    sh = _GetSystemMetrics(1) or 1080
    x = max(0, min(sw-1, int(x))); y = max(0, min(sh-1, int(y)))
    _send_input(_make_mouse(MOUSEEVENTF_MOVE_ABS, int(x*65535/sw), int(y*65535/sh)))

def center_mouse():
    sw = _GetSystemMetrics(0) or 1920
    sh = _GetSystemMetrics(1) or 1080
    mouse_move_abs(sw//2, sh//2)

class _CursorPoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


_GetCursorPos = ctypes.windll.user32.GetCursorPos
_GetCursorPos.argtypes = [ctypes.POINTER(_CursorPoint)]
_GetCursorPos.restype = ctypes.c_bool


def get_cursor_pos():
    """Return the current (x, y) OS cursor position."""
    pt = _CursorPoint()
    if not _GetCursorPos(ctypes.byref(pt)):
        raise ctypes.WinError()
    return pt.x, pt.y


def get_cursor_y():
    return get_cursor_pos()[1]

def correct_y_drift(baseline_y, deadzone=2):
    """Pull the cursor's Y back toward baseline_y, preserving X.

    Crater's own aim/search code only ever moves X (see crater/loop.py --
    every mouse_move_rel() call there passes dy=0). If Y has moved anyway,
    it did NOT come from the bot -- it's external drift (game recoil/
    camera-kick from sustained clicking, OS-level mouse smoothing/
    acceleration, etc.) creeping in over a long unattended session, since
    nothing was ever actively correcting it. This undoes that drift every
    tick, before it has a chance to build up and break the fixed capture
    region crater's rock/timer detection is calibrated against.
    """
    x, y = get_cursor_pos()
    if abs(y - baseline_y) > deadzone:
        mouse_move_abs(x, baseline_y)
        return True
    return False

def center_mouse_x(target_x):
    """Move mouse to target_x on screen, preserving the current Y position.
    Used by crater mode — moving Y would break the rock detection capture
    region which is calibrated for a fixed vertical position."""
    sw = _GetSystemMetrics(0) or 1920
    sh = _GetSystemMetrics(1) or 1080
    _x, y = get_cursor_pos()
    x = max(0, min(sw-1, int(target_x)))
    y = max(0, min(sh-1, int(y)))
    mouse_move_abs(x, y)

def mouse_left_down(): _send_input(_make_mouse(MOUSEEVENTF_LEFTDOWN))
def mouse_left_up():   _send_input(_make_mouse(MOUSEEVENTF_LEFTUP))

def key_down(vk): _send_input(_make_key(vk, False))
def key_up(vk):   _send_input(_make_key(vk, True))

_ALIASES = {"TAB":0x09,"ENTER":0x0D,"RETURN":0x0D,"SPACE":0x20,"ESC":0x1B,"ESCAPE":0x1B,
    "SHIFT":0x10,"CTRL":0x11,"CONTROL":0x11,"ALT":0x12,"UP":0x26,"DOWN":0x28,"LEFT":0x25,"RIGHT":0x27}

def binding_to_vk(binding):
    raw = str(binding or "").strip()
    if not raw: return None
    name = raw.upper().replace("-","_").replace(" ","_")
    name = re.sub(r"_+","_",name)
    if name in _ALIASES: return _ALIASES[name]
    if re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])",name): return 0x70+(int(name[1:])-1)
    if re.fullmatch(r"[A-Z]",name): return ord(name)
    if re.fullmatch(r"[0-9]",name): return ord(name)
    return None

def hold_binding_down(binding):
    name = str(binding or "").strip().upper().replace("-","_").replace(" ","_")
    if name in {"MOUSE_LEFT","LEFT_MOUSE","LMB","MOUSE1"}: mouse_left_down(); return True
    vk = binding_to_vk(name)
    if vk is not None: key_down(vk); return True
    return False

def release_binding(binding):
    name = str(binding or "").strip().upper().replace("-","_").replace(" ","_")
    if name in {"MOUSE_LEFT","LEFT_MOUSE","LMB","MOUSE1"}: mouse_left_up(); return True
    vk = binding_to_vk(name)
    if vk is not None: key_up(vk); return True
    return False

def screen_size():
    return int(_GetSystemMetrics(0)) or 1920, int(_GetSystemMetrics(1)) or 1080
