import logging
import re
import ctypes
import ctypes.wintypes
import os
import sys
import threading
import time
from dataclasses import dataclass

_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.append(_CODE_DIR)

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

try:
    from win_dpi import enable_dpi_awareness
except Exception:
    def enable_dpi_awareness() -> None:
        try:
            user32 = ctypes.windll.user32
        except Exception:
            return
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return
        except Exception:
            pass
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass

enable_dpi_awareness()

# ── Win32 constants ──────────────────────────────────────────────────────────
INPUT_MOUSE            = 0
INPUT_KEYBOARD         = 1
MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_ABSOLUTE   = 0x8000
MOUSEEVENTF_MOVE_ABS   = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
KEYEVENTF_KEYUP        = 0x0002
KEYEVENTF_SCANCODE     = 0x0008
KEYEVENTF_EXTENDEDKEY  = 0x0001
WM_HOTKEY              = 0x0312
WM_QUIT                = 0x0012
log = logging.getLogger(__name__)
MOD_NOREPEAT           = 0x4000
VK_F5                  = 0x74
VK_F6                  = 0x75
WH_KEYBOARD_LL         = 13
WH_MOUSE_LL            = 14
HC_ACTION              = 0
WM_KEYDOWN             = 0x0100
WM_KEYUP               = 0x0101
WM_SYSKEYDOWN          = 0x0104
WM_SYSKEYUP            = 0x0105
WM_MOUSEMOVE           = 0x0200
WM_LBUTTONDOWN         = 0x0201
WM_LBUTTONUP           = 0x0202
LLMHF_INJECTED         = 0x00000001
LLKHF_INJECTED         = 0x00000010
PM_REMOVE              = 0x0001
WM_INPUT               = 0x00FF
RID_INPUT              = 0x10000003
RIM_TYPEMOUSE          = 0
RIDEV_INPUTSINK        = 0x00000100
RIDEV_REMOVE           = 0x00000001
HID_USAGE_PAGE_GENERIC = 0x01
HID_USAGE_GENERIC_MOUSE = 0x02

PUL = ctypes.POINTER(ctypes.c_ulong)
ULONG_PTR = ctypes.c_size_t


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


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


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam",  ctypes.c_size_t),
        ("lParam",  ctypes.c_size_t),
        ("time",    ctypes.c_uint),
        ("pt_x",    ctypes.c_long),
        ("pt_y",    ctypes.c_long),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          POINT),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode",      ctypes.wintypes.DWORD),
        ("scanCode",    ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style",         ctypes.wintypes.UINT),
        ("lpfnWndProc",   WNDPROC),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",     ctypes.wintypes.HINSTANCE),
        ("hIcon",         ctypes.wintypes.HANDLE),
        ("hCursor",       ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HANDLE),
        ("lpszMenuName",  ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", ctypes.wintypes.USHORT),
        ("usUsage",     ctypes.wintypes.USHORT),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("hwndTarget",  ctypes.wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType",  ctypes.wintypes.DWORD),
        ("dwSize",  ctypes.wintypes.DWORD),
        ("hDevice", ctypes.wintypes.HANDLE),
        ("wParam",  ctypes.wintypes.WPARAM),
    ]


class _RAWMOUSE_BUTTONS(ctypes.Structure):
    _fields_ = [
        ("usButtonFlags", ctypes.wintypes.USHORT),
        ("usButtonData",  ctypes.wintypes.USHORT),
    ]


class _RAWMOUSE_BUTTON_UNION(ctypes.Union):
    _fields_ = [
        ("ulButtons", ctypes.wintypes.ULONG),
        ("buttons",   _RAWMOUSE_BUTTONS),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags",            ctypes.wintypes.USHORT),
        ("button_union",       _RAWMOUSE_BUTTON_UNION),
        ("ulRawButtons",       ctypes.wintypes.ULONG),
        ("lLastX",             ctypes.wintypes.LONG),
        ("lLastY",             ctypes.wintypes.LONG),
        ("ulExtraInformation", ctypes.wintypes.ULONG),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode",         ctypes.wintypes.USHORT),
        ("Flags",            ctypes.wintypes.USHORT),
        ("Reserved",         ctypes.wintypes.USHORT),
        ("VKey",             ctypes.wintypes.USHORT),
        ("Message",          ctypes.wintypes.UINT),
        ("ExtraInformation", ctypes.wintypes.ULONG),
    ]


class RAWHID(ctypes.Structure):
    _fields_ = [
        ("dwSizeHid", ctypes.wintypes.DWORD),
        ("dwCount",   ctypes.wintypes.DWORD),
        ("bRawData",  ctypes.c_byte * 1),
    ]


class _RAWINPUT_DATA(ctypes.Union):
    _fields_ = [
        ("mouse",    RAWMOUSE),
        ("keyboard", RAWKEYBOARD),
        ("hid",      RAWHID),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data",   _RAWINPUT_DATA),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


_SendInput        = ctypes.windll.user32.SendInput
_GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics
_GetCursorPos     = ctypes.windll.user32.GetCursorPos
_RegisterHotKey   = ctypes.windll.user32.RegisterHotKey
_UnregisterHotKey = ctypes.windll.user32.UnregisterHotKey
_GetMessageW      = ctypes.windll.user32.GetMessageW
_PeekMessageW     = ctypes.windll.user32.PeekMessageW
_TranslateMessage = ctypes.windll.user32.TranslateMessage
_DispatchMessageW = ctypes.windll.user32.DispatchMessageW
_MapVirtualKeyW   = ctypes.windll.user32.MapVirtualKeyW
_PostThreadMessageW = ctypes.windll.user32.PostThreadMessageW
_GetCurrentThreadId = ctypes.windll.kernel32.GetCurrentThreadId
_GetModuleHandleW = ctypes.windll.kernel32.GetModuleHandleW
_SetWindowsHookExW = ctypes.windll.user32.SetWindowsHookExW
_CallNextHookEx = ctypes.windll.user32.CallNextHookEx
_UnhookWindowsHookEx = ctypes.windll.user32.UnhookWindowsHookEx
_RegisterClassW = ctypes.windll.user32.RegisterClassW
_CreateWindowExW = ctypes.windll.user32.CreateWindowExW
_DestroyWindow = ctypes.windll.user32.DestroyWindow
_DefWindowProcW = ctypes.windll.user32.DefWindowProcW
_RegisterRawInputDevices = ctypes.windll.user32.RegisterRawInputDevices
_GetRawInputData = ctypes.windll.user32.GetRawInputData

_GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
_GetCursorPos.restype = ctypes.wintypes.BOOL
_GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]
_GetModuleHandleW.restype = ctypes.wintypes.HMODULE
_SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.wintypes.HMODULE, ctypes.wintypes.DWORD]
_SetWindowsHookExW.restype = ctypes.c_void_p
_CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
_CallNextHookEx.restype = ctypes.c_long
_UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
_UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL
_RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
_RegisterClassW.restype = ctypes.wintypes.ATOM
_CreateWindowExW.argtypes = [
    ctypes.wintypes.DWORD,
    ctypes.wintypes.LPCWSTR,
    ctypes.wintypes.LPCWSTR,
    ctypes.wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.wintypes.HWND,
    ctypes.wintypes.HMENU,
    ctypes.wintypes.HINSTANCE,
    ctypes.c_void_p,
]
_CreateWindowExW.restype = ctypes.wintypes.HWND
_DestroyWindow.argtypes = [ctypes.wintypes.HWND]
_DestroyWindow.restype = ctypes.wintypes.BOOL
_DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
_DefWindowProcW.restype = ctypes.c_ssize_t
_RegisterRawInputDevices.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICE),
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
]
_RegisterRawInputDevices.restype = ctypes.wintypes.BOOL
_GetRawInputData.argtypes = [
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.wintypes.UINT),
    ctypes.wintypes.UINT,
]
_GetRawInputData.restype = ctypes.wintypes.UINT

# 1 ms timer resolution — required for accurate sleep/smooth-move timing
try:
    ctypes.WinDLL("winmm").timeBeginPeriod(1)
except Exception:
    pass


@dataclass
class Sensitivity:
    recorded_h: float = 17.0
    recorded_v: float = 17.0
    user_h: float = 17.0
    user_v: float = 17.0

    def scale(self, dx: int, dy: int) -> tuple[int, int]:
        if self.user_h <= 0 or self.user_v <= 0:
            return dx, dy
        return (
            int(round(dx * self.recorded_h / self.user_h)),
            int(round(dy * self.recorded_v / self.user_v)),
        )

    def ratios(self) -> tuple[float, float]:
        if self.user_h <= 0 or self.user_v <= 0:
            return 1.0, 1.0
        return self.recorded_h / self.user_h, self.recorded_v / self.user_v


def _make_mouse(flags: int, dx: int = 0, dy: int = 0) -> INPUT:
    union = _INPUT_UNION()
    union.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=flags, time=0,
                          dwExtraInfo=0)
    return INPUT(INPUT_MOUSE, union)


def _is_extended_vk(vk: int) -> bool:
    return vk in {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                  0x2D, 0x2E, 0xA3, 0xA5}


def _vk_to_scancode(vk: int) -> int:
    if vk == 0xA0: return 0x2A
    if vk == 0xA1: return 0x36
    if vk in (0xA2, 0xA3): return 0x1D
    if vk in (0xA4, 0xA5): return 0x38
    return _MapVirtualKeyW(vk, 0)


def _make_key(vk: int, is_key_up: bool) -> INPUT:
    scan  = _vk_to_scancode(vk)
    flags = KEYEVENTF_SCANCODE
    if is_key_up:      flags |= KEYEVENTF_KEYUP
    if _is_extended_vk(vk): flags |= KEYEVENTF_EXTENDEDKEY
    extra = ctypes.c_ulong(0)
    union = _INPUT_UNION()
    union.ki = KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0,
                          dwExtraInfo=0)
    return INPUT(INPUT_KEYBOARD, union)


def _send_input(*inputs: INPUT) -> None:
    arr = (INPUT * len(inputs))(*inputs)
    _SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _mouse_move_abs(x: int, y: int) -> None:
    sw = _GetSystemMetrics(0) or 1920
    sh = _GetSystemMetrics(1) or 1080
    _send_input(_make_mouse(MOUSEEVENTF_MOVE_ABS, int(x * 65535 / sw), int(y * 65535 / sh)))


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


def _mouse_move_rel(dx: int, dy: int) -> None:
    try:
        from macro_runner import _raw_mouse_move_rel
        _raw_mouse_move_rel(int(dx), int(dy))
        return
    except Exception:
        pass
    extra = ctypes.c_ulong(0)
    try:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)
    except Exception:
        _send_input(_make_mouse(MOUSEEVENTF_MOVE, int(dx), int(dy)))


def _mouse_left_down()  -> None: _send_input(_make_mouse(MOUSEEVENTF_LEFTDOWN))
def _mouse_left_up()    -> None: _send_input(_make_mouse(MOUSEEVENTF_LEFTUP))
def _mouse_left_click() -> None:
    _mouse_left_down(); time.sleep(0.05); _mouse_left_up()


def _key_down(vk: int)  -> None: _send_input(_make_key(vk, False))
def _key_up(vk: int)    -> None: _send_input(_make_key(vk, True))
def _key_press(vk: int) -> None:
    _key_down(vk); time.sleep(0.03); _key_up(vk)


def _release_all_keys() -> None:
    """Release common held keys — called immediately on F6 stop."""
    vks = [0xA0, 0xA1, 0xA2, 0xA3, 0x57, 0x41, 0x53, 0x44, 0x20]
    try:
        from macro_runner import remapped_movement_vks
        vks = list(dict.fromkeys(vks + remapped_movement_vks()))
    except Exception:
        pass
    for vk in vks:
        try:
            _key_up(vk)
        except Exception:
            pass
    try:
        _mouse_left_up()
    except Exception:
        pass


def _get_cursor_pos() -> tuple[int, int]:
    pt = POINT()
    if _GetCursorPos(ctypes.byref(pt)):
        return int(pt.x), int(pt.y)
    return 0, 0


_PLAY_MACRO_MAX_DEPTH = 16


_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _is_rooted_path(p: str) -> bool:
    """True for Windows drive-letter paths, UNC paths, or any OS-absolute path."""
    return bool(_DRIVE_LETTER_RE.match(p)) or p.startswith("\\\\") or os.path.isabs(p)


def _resolve_nested_macro(target: str, macros_dir: str):
    """Resolve a PLAY_MACRO target to a .macro file.

    Accepts either a full path picked via the Windows file dialog (used as-is,
    anywhere on disk), or a "name" / "folder/name" resolved inside macros/
    with directory-traversal guarded. Returns None if not found / not allowed.
    """
    if not target:
        return None
    target = str(target).strip()
    if _is_rooted_path(target):
        path = os.path.normpath(target)
        if os.path.isfile(path):
            return path
        if os.path.isfile(path + ".macro"):
            return path + ".macro"
        return None
    target = target.replace("\\", "/").strip("/")
    if target.lower().endswith(".macro"):
        target = target[:-6]
    if not target:
        return None
    base = os.path.abspath(macros_dir)
    path = os.path.normpath(os.path.join(base, target))
    if not (path == base or path.startswith(base + os.sep)):
        return None
    if os.path.isfile(path):
        return path
    if os.path.isfile(path + ".macro"):
        return path + ".macro"
    return None


def _raw_mouse_delta(l_param) -> tuple[int, int]:
    size = ctypes.wintypes.UINT(0)
    header_size = ctypes.sizeof(RAWINPUTHEADER)
    _GetRawInputData(l_param, RID_INPUT, None, ctypes.byref(size), header_size)
    if size.value <= 0:
        return 0, 0
    buf = ctypes.create_string_buffer(size.value)
    copied = _GetRawInputData(l_param, RID_INPUT, buf, ctypes.byref(size), header_size)
    if copied in (0, ctypes.wintypes.UINT(-1).value):
        return 0, 0
    raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
    if raw.header.dwType != RIM_TYPEMOUSE:
        return 0, 0
    return int(raw.data.mouse.lLastX), int(raw.data.mouse.lLastY)


class MacroEngine:
    def __init__(self, macros_dir: str, on_state=None):
        self.macros_dir = macros_dir
        self.current_path: str | None = None
        self.current_macro: str | None = None
        self.sensitivity = Sensitivity()
        self._stop_event  = threading.Event()
        self._play_thread: threading.Thread | None = None
        self._record_stop_event = threading.Event()
        self._record_thread: threading.Thread | None = None
        self._record_thread_id: int | None = None
        self._record_ready = threading.Event()
        self._record_lock = threading.Lock()
        self._record_events: list[tuple[float, str, str]] = []
        self._record_keys_down: set[int] = set()
        self._record_mouse_down = False
        self._record_start = 0.0
        self._record_sensitivity = Sensitivity()
        self._hotkey_thread_id: int | None = None
        self._hotkey_stopped = threading.Event()
        self._hotkey_stopped.set()
        self._record_toggle_vk = VK_F5
        self._on_state    = on_state
        self._state_lock  = threading.Lock()
        self.state = {
            "running":   False,
            "recording": False,
            "macro":     None,
            "elapsed":   0.0,
            "estimated": 0.0,
            "progress":  0.0,
            "record_version": 0,
            "record_path": "",
            "play_binding": "F6",
            "record_binding": "F5",
        }

    # ── public API ──────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Signal stop immediately and release all held inputs."""
        self._stop_event.set()
        _release_all_keys()
        self._set_state(running=False)

    def is_running(self) -> bool:
        return bool(self._play_thread and self._play_thread.is_alive())

    def is_recording(self) -> bool:
        return bool(self._record_thread and self._record_thread.is_alive())

    def start_recording(self, macro_name: str, sensitivity: Sensitivity | None = None) -> bool:
        """Start capturing input events. Returns False if play/record is already active."""
        if self.is_running() or self.is_recording():
            return False
        self._record_stop_event = threading.Event()
        self._record_ready = threading.Event()
        self._record_thread_id = None
        self._record_events = []
        self._record_keys_down = set()
        self._record_mouse_down = False
        self._record_start = time.perf_counter()
        self._record_sensitivity = sensitivity or Sensitivity()
        self.current_macro = macro_name
        self._record_thread = threading.Thread(
            target=self._record_loop, args=(macro_name,), daemon=True, name="macro-record"
        )
        self._record_thread.start()
        self._record_ready.wait(1.0)
        return self.is_recording()

    def stop_recording(self) -> list[dict]:
        """Stop recording and return editor blocks."""
        if not self.is_recording():
            return []
        self._record_stop_event.set()
        if self._record_thread_id:
            try:
                _PostThreadMessageW(self._record_thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._record_thread:
            self._record_thread.join(timeout=2.0)
        return self._record_events_to_blocks()

    def play_path_once(
        self,
        path: str,
        macro_name: str,
        repeat_count: int = 1,
        sensitivity_override: Sensitivity | None = None,
    ) -> bool:
        """Start playing a macro file. Returns False if already running or file missing."""
        if self.is_running() or self.is_recording():
            return False
        if not os.path.exists(path):
            return False
        _release_all_keys()
        self.current_path  = path
        self.current_macro = macro_name
        self._stop_event   = threading.Event()
        self._play_thread  = threading.Thread(
            target=self._play_file, args=(path, macro_name, repeat_count, sensitivity_override), daemon=True
        )
        self._play_thread.start()
        return True

    # ── internal ────────────────────────────────────────────────────────────

    def _append_record_event(self, event_type: str, value: str = "") -> None:
        ts = time.perf_counter() - self._record_start
        with self._record_lock:
            self._record_events.append((ts, event_type, value))

    def _record_loop(self, macro_name: str) -> None:
        self._record_thread_id = int(_GetCurrentThreadId())
        self._set_state(
            running=False, recording=True, macro=macro_name,
            elapsed=0.0, estimated=0.0, progress=0.0,
        )

        last_x, last_y = _get_cursor_pos()
        last_state_update = 0.0
        module_handle = _GetModuleHandleW(None)
        raw_mouse_enabled = False
        raw_hwnd = None
        raw_cb = None

        def raw_wnd_proc(hwnd, msg, w_param, l_param):
            if msg == WM_INPUT:
                dx, dy = _raw_mouse_delta(l_param)
                if dx or dy:
                    self._append_record_event("SMOOTH_MOVE", f"{dx},{dy}")
                return 0
            return _DefWindowProcW(hwnd, msg, w_param, l_param)

        try:
            class_name = f"MacroEngineRawInputWindow_{self._record_thread_id}_{id(self)}"
            raw_cb = WNDPROC(raw_wnd_proc)
            wc = WNDCLASSW()
            wc.lpfnWndProc = raw_cb
            wc.hInstance = module_handle
            wc.lpszClassName = class_name
            if _RegisterClassW(ctypes.byref(wc)):
                raw_hwnd = _CreateWindowExW(
                    0, class_name, class_name, 0,
                    0, 0, 0, 0, None, None, module_handle, None,
                )
                if raw_hwnd:
                    rid = RAWINPUTDEVICE(
                        HID_USAGE_PAGE_GENERIC,
                        HID_USAGE_GENERIC_MOUSE,
                        RIDEV_INPUTSINK,
                        raw_hwnd,
                    )
                    raw_mouse_enabled = bool(
                        _RegisterRawInputDevices(
                            ctypes.byref(rid),
                            1,
                            ctypes.sizeof(RAWINPUTDEVICE),
                        )
                    )
        except Exception:
            raw_mouse_enabled = False

        def mouse_proc(n_code, w_param, l_param):
            nonlocal last_x, last_y
            if n_code == HC_ACTION:
                info = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                injected = bool(info.flags & LLMHF_INJECTED)
                if w_param == WM_MOUSEMOVE:
                    x, y = int(info.pt.x), int(info.pt.y)
                    dx, dy = x - last_x, y - last_y
                    last_x, last_y = x, y
                    if (dx or dy) and not injected and not raw_mouse_enabled:
                        self._append_record_event("SMOOTH_MOVE", f"{dx},{dy}")
                elif not injected and w_param == WM_LBUTTONDOWN:
                    self._record_mouse_down = True
                    self._append_record_event("MOUSE_LEFT_DOWN")
                elif not injected and w_param == WM_LBUTTONUP:
                    self._record_mouse_down = False
                    self._append_record_event("MOUSE_LEFT_UP")
            return _CallNextHookEx(None, n_code, w_param, l_param)

        def keyboard_proc(n_code, w_param, l_param):
            if n_code == HC_ACTION:
                info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = int(info.vkCode)
                injected = bool(info.flags & LLKHF_INJECTED)
                if not injected and vk not in (self._record_toggle_vk,):
                    is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)
                    if is_down and vk not in self._record_keys_down:
                        self._record_keys_down.add(vk)
                        self._append_record_event("KEY_DOWN", f"0x{vk:02X}")
                    elif is_up and vk in self._record_keys_down:
                        self._record_keys_down.discard(vk)
                        self._append_record_event("KEY_UP", f"0x{vk:02X}")
            return _CallNextHookEx(None, n_code, w_param, l_param)

        mouse_cb = HOOKPROC(mouse_proc)
        keyboard_cb = HOOKPROC(keyboard_proc)
        mouse_hook = _SetWindowsHookExW(WH_MOUSE_LL, mouse_cb, module_handle, 0)
        keyboard_hook = _SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_cb, module_handle, 0)
        self._record_ready.set()

        try:
            msg = MSG()
            while not self._record_stop_event.is_set():
                while _PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    if msg.message == WM_QUIT:
                        self._record_stop_event.set()
                        break
                    _TranslateMessage(ctypes.byref(msg))
                    _DispatchMessageW(ctypes.byref(msg))

                now = time.perf_counter()
                if now - last_state_update >= 0.05:
                    last_state_update = now
                    self._set_state(elapsed=now - self._record_start, progress=0.0)
                time.sleep(0.001)
        finally:
            if self._record_mouse_down:
                self._append_record_event("MOUSE_LEFT_UP")
                self._record_mouse_down = False
            for vk in sorted(self._record_keys_down):
                self._append_record_event("KEY_UP", f"0x{vk:02X}")
            self._record_keys_down.clear()
            if mouse_hook:
                _UnhookWindowsHookEx(mouse_hook)
            if keyboard_hook:
                _UnhookWindowsHookEx(keyboard_hook)
            if raw_mouse_enabled:
                try:
                    rid = RAWINPUTDEVICE(
                        HID_USAGE_PAGE_GENERIC,
                        HID_USAGE_GENERIC_MOUSE,
                        RIDEV_REMOVE,
                        None,
                    )
                    _RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE))
                except Exception:
                    pass
            if raw_hwnd:
                try:
                    _DestroyWindow(raw_hwnd)
                except Exception:
                    pass
            elapsed = time.perf_counter() - self._record_start
            self._set_state(recording=False, elapsed=elapsed, progress=1.0)

    def _record_events_to_blocks(self) -> list[dict]:
        with self._record_lock:
            events = list(self._record_events)
        blocks: list[dict] = []
        prev = 0.0
        carry_ms = 0.0
        for ts, event_type, value in events:
            delta_ms = max(0.0, (ts - prev) * 1000.0)
            prev = ts
            carry_ms += delta_ms
            delay_ms = int(round(carry_ms))
            if delay_ms > 0:
                blocks.append({"type": "DELAY", "value": str(delay_ms)})
                carry_ms -= delay_ms
            blocks.append({"type": event_type, "value": value})
        return blocks

    def _set_state(self, **kwargs):
        with self._state_lock:
            self.state.update(kwargs)
            snap = dict(self.state)
        if self._on_state:
            try:
                self._on_state(snap)
            except Exception:
                pass

    def _estimate_runtime_seconds(self, lines: list[str], visited: set | None = None) -> float:
        est = 0.0
        if visited is None:
            visited = set()
        repeat_stack: list[tuple[int, int]] = []
        pc = 0
        safety = 0
        while pc < len(lines) and safety < 300_000:
            safety += 1
            raw = lines[pc].strip()
            pc += 1
            if not raw or raw.startswith("#") or raw.startswith("LABEL:"):
                continue
            if raw.startswith("PLAY_MACRO:"):
                target = raw[11:].strip()
                inner_path = _resolve_nested_macro(target, self.macros_dir) if target else None
                if inner_path:
                    key = os.path.abspath(inner_path)
                    if key not in visited:
                        try:
                            with open(inner_path, "r", encoding="utf-8", errors="replace") as f:
                                inner_lines = [ln.strip() for ln in f]
                            est += self._estimate_runtime_seconds(inner_lines, visited | {key})
                        except Exception:
                            pass
                continue
            if raw.startswith("DELAY:"):
                try: est += max(0, int(raw[6:])) / 1000.0
                except Exception: pass
                continue
            if raw.startswith("KEY_PRESS:"):
                est += 0.03; continue
            if raw == "MOUSE_LEFT_CLICK":
                est += 0.05; continue
            if raw.startswith("REPEAT:"):
                try: repeat_stack.append((pc, max(0, int(raw[7:]))))
                except Exception: pass
                continue
            if raw == "ENDREPEAT" and repeat_stack:
                start, rem = repeat_stack[-1]
                rem -= 1
                if rem > 0:
                    repeat_stack[-1] = (start, rem)
                    pc = start
                else:
                    repeat_stack.pop()
        return max(0.1, est)

    def _update_runtime(self, t0: float, est_total: float) -> None:
        elapsed  = time.perf_counter() - t0
        progress = min(1.0, elapsed / est_total) if est_total > 0 else 0.0
        self._set_state(elapsed=elapsed, progress=progress)

    def _play_file(
        self,
        path: str,
        macro_name: str,
        repeat_count: int = 1,
        sensitivity_override: Sensitivity | None = None,
    ) -> None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw_lines = [ln.strip() for ln in f]
        except Exception:
            self._set_state(running=False)
            return

        # Load sensitivity from macro comments
        for line in raw_lines:
            if line.startswith("# SENS_RECORDED_H:"):
                try: self.sensitivity.recorded_h = float(line.split(":")[1])
                except Exception: pass
            elif line.startswith("# SENS_RECORDED_V:"):
                try: self.sensitivity.recorded_v = float(line.split(":")[1])
                except Exception: pass
            elif line.startswith("# SENS_USER_H:"):
                try: self.sensitivity.user_h = float(line.split(":")[1])
                except Exception: pass
            elif line.startswith("# SENS_USER_V:"):
                try: self.sensitivity.user_v = float(line.split(":")[1])
                except Exception: pass
        if sensitivity_override:
            self.sensitivity.recorded_h = sensitivity_override.recorded_h
            self.sensitivity.recorded_v = sensitivity_override.recorded_v
            self.sensitivity.user_h = sensitivity_override.user_h
            self.sensitivity.user_v = sensitivity_override.user_v

        try:
            repeat_count = int(repeat_count)
        except Exception:
            repeat_count = 1
        repeat_count = max(0, repeat_count)
        est_one = self._estimate_runtime_seconds(raw_lines)
        est_total = est_one if repeat_count == 0 else max(0.1, est_one * max(1, repeat_count))
        self._set_state(running=True, macro=macro_name,
                        elapsed=0.0, estimated=est_total, progress=0.0)
        t0 = time.perf_counter()
        next_due = t0
        last_runtime_update = 0.0
        try:
            from macro_runner import (
                prime_game_mouse_capture,
                _prepare_windows_mouse_compatibility,
                _boost_playback_timing,
            )
            _prepare_windows_mouse_compatibility()
            _boost_playback_timing()
            prime_game_mouse_capture()
        except Exception:
            pass

        def update_runtime(force: bool = False) -> None:
            nonlocal last_runtime_update
            now = time.perf_counter()
            if force or now - last_runtime_update >= 0.05:
                last_runtime_update = now
                self._update_runtime(t0, est_total)

        def sleep_until(deadline: float) -> bool:
            while True:
                if self._stop_event.is_set():
                    return False
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    update_runtime()
                    return True
                if remaining <= 0.002:
                    while time.perf_counter() < deadline:
                        if self._stop_event.is_set():
                            return False
                    update_runtime()
                    return True
                time.sleep(min(0.001, remaining - 0.002))
                update_runtime()

        loop_index = 0
        smooth_carry_x = 0.0
        smooth_carry_y = 0.0
        vars_state: dict = {}
        macro_dir = os.path.dirname(os.path.abspath(path))
        bot_root = os.path.dirname(os.path.abspath(self.macros_dir))

        def run_lines(lines: list[str], m_dir: str, depth: int = 0) -> bool:
            """Execute one macro's lines to completion.

            Returns False when playback was stopped. Variables, timing
            and the smooth-move carry are shared across nested PLAY_MACRO
            calls; labels and IF / REPEAT scopes are local to each file.
            """
            nonlocal next_due, smooth_carry_x, smooth_carry_y
            labels: dict[str, int] = {
                ln[6:].strip(): i
                for i, ln in enumerate(lines)
                if ln.startswith("LABEL:")
            }
            pc = 0
            repeat_stack: list[tuple[int, int]] = []
            if_stack: list[dict] = []
            while pc < len(lines):
                update_runtime()

                if self._stop_event.is_set():
                    return False

                raw = lines[pc]
                pc += 1
                if not raw or raw.startswith("#"):
                    continue

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
                        run_image_check(vars_state, parse_payload(raw, "IMAGE"), bot_root, m_dir)
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

                if raw.startswith("LABEL:"):
                    continue
                if raw.startswith("GOTO:"):
                    pc = labels.get(raw[5:].strip(), pc); continue

                if raw.startswith("DELAY:"):
                    ms = max(0, int(round(_resolve_macro_number(raw[6:], vars_state)[0])))
                    next_due += ms / 1000.0
                    if not sleep_until(next_due):
                        return False
                    continue

                if raw.startswith("REPEAT:"):
                    try: repeat_stack.append((pc, max(1, int(round(_resolve_macro_number(raw[7:], vars_state)[0])))))
                    except Exception: pass
                    continue
                if raw == "ENDREPEAT":
                    if repeat_stack:
                        start, rem = repeat_stack[-1]
                        rem -= 1
                        if rem > 0:
                            repeat_stack[-1] = (start, rem); pc = start
                        else:
                            repeat_stack.pop()
                    continue

                if raw.startswith("KEY_DOWN:"):
                    try:
                        from macro_runner import remap_macro_vk as _remap_vk
                        _key_down(_remap_vk(int(raw[9:].strip(), 16)))
                    except Exception:
                        _key_down(int(raw[9:].strip(), 16))
                    continue
                if raw.startswith("KEY_UP:"):
                    try:
                        from macro_runner import remap_macro_vk as _remap_vk
                        _key_up(_remap_vk(int(raw[7:].strip(), 16)))
                    except Exception:
                        _key_up(int(raw[7:].strip(), 16))
                    continue
                if raw.startswith("KEY_PRESS:"):
                    try:
                        from macro_runner import remap_macro_vk as _remap_vk
                        _key_press(_remap_vk(int(raw[10:].strip(), 16)))
                    except Exception:
                        _key_press(int(raw[10:].strip(), 16))
                    continue

                if raw.startswith("MOUSE_MOVE_ABS:"):
                    x, y = raw[15:].split(",")
                    xv = int(round(_resolve_macro_number(x, vars_state)[0]))
                    yv = int(round(_resolve_macro_number(y, vars_state)[0]))
                    _mouse_move_abs(xv, yv);  continue
                if raw == "MOUSE_LEFT_DOWN":
                    _mouse_left_down();  continue
                if raw == "MOUSE_LEFT_UP":
                    _mouse_left_up();    continue
                if raw == "MOUSE_LEFT_CLICK":
                    _mouse_left_click(); continue
                if raw.startswith("MOUSE_REL:"):
                    dx, dy = raw[10:].split(",")
                    dxv = int(round(_resolve_macro_number(dx, vars_state)[0]))
                    dyv = int(round(_resolve_macro_number(dy, vars_state)[0]))
                    _mouse_move_rel(dxv, dyv); continue

                if raw.startswith("SMOOTH_MOVE:"):
                    parts = [p.strip() for p in raw[12:].split(",")]
                    if len(parts) < 2:
                        continue
                    dx = int(round(_resolve_macro_number(parts[0], vars_state)[0]))
                    dy = int(round(_resolve_macro_number(parts[1], vars_state)[0]))
                    rx, ry = self.sensitivity.ratios()
                    smooth_carry_x += dx * rx
                    smooth_carry_y += dy * ry
                    sdx = int(smooth_carry_x)
                    sdy = int(smooth_carry_y)
                    smooth_carry_x -= sdx
                    smooth_carry_y -= sdy
                    if sdx or sdy:
                        _mouse_move_rel(sdx, sdy)
                    next_due = max(next_due, time.perf_counter())
                    continue

                if raw.startswith("PLAY_MACRO:"):
                    target = raw[11:].strip()
                    if not target:
                        continue
                    if depth >= _PLAY_MACRO_MAX_DEPTH:
                        log.warning(f"[PLAY_MACRO] max nesting depth ({_PLAY_MACRO_MAX_DEPTH}) reached; skipping {target!r}")
                        continue
                    inner_path = _resolve_nested_macro(target, self.macros_dir)
                    if not inner_path:
                        log.warning(f"[PLAY_MACRO] macro not found: {target!r}")
                        continue
                    try:
                        with open(inner_path, "r", encoding="utf-8", errors="replace") as f:
                            inner_lines = [ln.strip() for ln in f]
                    except Exception as e:
                        log.warning(f"[PLAY_MACRO] cannot read {target!r}: {e}")
                        continue
                    old_rh = self.sensitivity.recorded_h
                    old_rv = self.sensitivity.recorded_v
                    try:
                        for ln in inner_lines:
                            if ln.startswith("# SENS_RECORDED_H:"):
                                try: self.sensitivity.recorded_h = float(ln.split(":", 1)[1])
                                except Exception: pass
                            elif ln.startswith("# SENS_RECORDED_V:"):
                                try: self.sensitivity.recorded_v = float(ln.split(":", 1)[1])
                                except Exception: pass
                        if not run_lines(inner_lines, os.path.dirname(os.path.abspath(inner_path)), depth + 1):
                            return False
                    finally:
                        self.sensitivity.recorded_h = old_rh
                        self.sensitivity.recorded_v = old_rv
                    continue
            return True

        try:
            while repeat_count == 0 or loop_index < repeat_count:
                loop_index += 1
                if not run_lines(raw_lines, macro_dir, 0):
                    return

        finally:
            _release_all_keys()
            elapsed = time.perf_counter() - t0
            self._set_state(running=False, elapsed=elapsed, progress=1.0)

    # ── F6 hotkey listener ───────────────────────────────────────────────────

    def stop_hotkeys(self, timeout: float = 1.0) -> None:
        """Uninstall the F5/F6 low-level hook and wait until it is gone."""
        tid = self._hotkey_thread_id
        if not tid:
            return
        try:
            _PostThreadMessageW(tid, WM_QUIT, 0, 0)
        except Exception:
            pass
        ev = getattr(self, "_hotkey_stopped", None)
        if ev is not None:
            ev.wait(timeout=timeout)

    def start_hotkeys(self, on_f6_toggle, on_f5_toggle=None, *, play_vk: int = VK_F6, record_vk: int = VK_F5) -> threading.Thread:
        """Listen for configurable system-wide hotkeys with a low-level keyboard hook.

        Returns after the hook is installed (or failed), so callers can await
        arming before flipping the Recorder tab.
        """
        self.stop_hotkeys()
        if self._hotkey_thread_id:
            return None
        ready = threading.Event()
        stopped = threading.Event()
        self._hotkey_stopped = stopped

        def _listener():
            hooked = False
            keyboard_hook = None
            try:
                self._hotkey_thread_id = int(_GetCurrentThreadId())
                self._record_toggle_vk = int(record_vk)
                down_keys: set[int] = set()

                def dispatch(callback) -> None:
                    threading.Thread(target=callback, daemon=True, name="macro-hotkey-action").start()

                def keyboard_proc(n_code, w_param, l_param):
                    if n_code == HC_ACTION:
                        info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                        vk = int(info.vkCode)
                        injected = bool(info.flags & LLKHF_INJECTED)
                        is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                        is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)
                        if not injected and is_down and vk not in down_keys:
                            down_keys.add(vk)
                            if vk == int(play_vk):
                                dispatch(on_f6_toggle)
                            elif vk == int(record_vk) and on_f5_toggle:
                                dispatch(on_f5_toggle)
                        elif is_up and vk in down_keys:
                            down_keys.discard(vk)
                    return _CallNextHookEx(None, n_code, w_param, l_param)

                keyboard_cb = HOOKPROC(keyboard_proc)
                module_handle = _GetModuleHandleW(None)
                keyboard_hook = _SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_cb, module_handle, 0)
                if not keyboard_hook:
                    return
                hooked = True
                ready.set()
                msg = MSG()
                while _GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    _TranslateMessage(ctypes.byref(msg))
                    _DispatchMessageW(ctypes.byref(msg))
            finally:
                if hooked:
                    try:
                        _UnhookWindowsHookEx(keyboard_hook)
                    except Exception:
                        pass
                self._hotkey_thread_id = None
                stopped.set()
                ready.set()

        t = threading.Thread(target=_listener, daemon=True, name="hotkey-f5-f6")
        t.start()
        ready.wait(timeout=1.0)
        return t
