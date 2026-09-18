"""Smooth Move helper (Recorder)

Hold-key X-axis movement tracker for the Recorder tab.

While armed (Recorder tab open, not playing/recording), holding the
configured key (default L) with Fortnite focused:

- The hold key is swallowed (Windows / the game never sees it).
- Mouse movement is NOT blocked — the game and cursor behave normally.
- Movement is measured as RAW input counts on both axes — exactly like
  the recorder does — and accumulated as a NET displacement: right
  5,1,2, back a few px (not through 0), then right again still records
  +; only crossing back through the 0 point flips the sign. Same for Y.
- Releasing the key produces the signed net (x, y) delta, which app.py
  converts to the open macro's recorded-sensitivity equivalent.

The result is delivered via the on_result callback:
    on_result(x, y, elapsed_ms)   # signed ints
"""
import ctypes
import ctypes.wintypes
import logging
import threading

log = logging.getLogger(__name__)

try:
    from .macro_engine import (
        HC_ACTION, LLKHF_INJECTED,
        WH_KEYBOARD_LL,
        WM_INPUT, WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP,
        RIDEV_INPUTSINK, HID_USAGE_PAGE_GENERIC, HID_USAGE_GENERIC_MOUSE,
        RAWINPUTDEVICE, RAWINPUTHEADER, WNDCLASSW, WNDPROC, HOOKPROC,
        KBDLLHOOKSTRUCT, MSG,
        _GetMessageW, _PeekMessageW, PM_REMOVE, _PostThreadMessageW, WM_QUIT,
        _GetCurrentThreadId, _GetModuleHandleW,
        _SetWindowsHookExW, _CallNextHookEx, _UnhookWindowsHookEx,
        _RegisterClassW, _CreateWindowExW, _DefWindowProcW, _DestroyWindow,
        _RegisterRawInputDevices, _raw_mouse_delta,
        _GetRawInputData, RID_INPUT,
        _TranslateMessage, _DispatchMessageW,
    )
except ImportError:
    from macro_engine import (
        HC_ACTION, LLKHF_INJECTED,
        WH_KEYBOARD_LL,
        WM_INPUT, WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP,
        RIDEV_INPUTSINK, HID_USAGE_PAGE_GENERIC, HID_USAGE_GENERIC_MOUSE,
        RAWINPUTDEVICE, RAWINPUTHEADER, WNDCLASSW, WNDPROC, HOOKPROC,
        KBDLLHOOKSTRUCT, MSG,
        _GetMessageW, _PeekMessageW, PM_REMOVE, _PostThreadMessageW, WM_QUIT,
        _GetCurrentThreadId, _GetModuleHandleW,
        _SetWindowsHookExW, _CallNextHookEx, _UnhookWindowsHookEx,
        _RegisterClassW, _CreateWindowExW, _DefWindowProcW, _DestroyWindow,
        _RegisterRawInputDevices, _raw_mouse_delta,
        _GetRawInputData, RID_INPUT,
        _TranslateMessage, _DispatchMessageW,
    )

_GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
_GetWindowTextW = ctypes.windll.user32.GetWindowTextW


def _foreground_is_game() -> bool:
    """True when the foreground window looks like the game (permissive)."""
    try:
        hwnd = _GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(256)
        if not _GetWindowTextW(hwnd, buf, 256):
            return True  # can't read the title — don't block the tool
        return "fortnite" in buf.value.lower()
    except Exception:
        return True


def _raw_input_is_injected(l_param) -> bool:
    """SendInput-injected raw input carries no device handle (hDevice=0)."""
    try:
        size = ctypes.wintypes.UINT(0)
        header_size = ctypes.sizeof(RAWINPUTHEADER)
        _GetRawInputData(l_param, RID_INPUT, None, ctypes.byref(size), header_size)
        if size.value <= 0:
            return True
        buf = ctypes.create_string_buffer(size.value)
        copied = _GetRawInputData(l_param, RID_INPUT, buf, ctypes.byref(size), header_size)
        if copied in (0, ctypes.wintypes.UINT(-1).value):
            return True
        header = ctypes.cast(buf, ctypes.POINTER(RAWINPUTHEADER)).contents
        return not int(header.hDevice or 0)
    except Exception:
        return True


class SmoothMoveTracker:
    """Global hold-key smooth-move tracker (own thread + hooks).

    While the hold key is down in-game: the key is swallowed for
    Windows/the game, mouse movement is untouched (nothing is blocked),
    and the raw deltas are accumulated as a net displacement on both
    axes, exactly like the recorder captures SMOOTH_MOVE events.
    """

    def __init__(self):
        self._thread = None
        self._thread_id = None
        self._stopped = threading.Event()
        self._stopped.set()
        self._hold_vk = 0
        self._is_busy = None      # callable -> bool (recording/playing)
        self._on_result = None    # callable(x, elapsed_ms)
        self._tracking = False
        # capture state
        self._pos_x = 0.0         # net x movement since hold start
        self._pos_y = 0.0         # net y movement since hold start
        self._hold_started = 0.0

    # ── public API ────────────────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._thread is not None and not self._stopped.is_set()

    def start(self, hold_vk: int, is_busy, on_result) -> bool:
        """Install hooks. Idempotent — restarts only when hold_vk changes."""
        hold_vk = int(hold_vk or 0)
        if self.running and hold_vk == self._hold_vk:
            self._is_busy = is_busy or (lambda: False)
            self._on_result = on_result
            return True
        self.stop()
        if not hold_vk:
            return False
        self._hold_vk = hold_vk
        self._is_busy = is_busy or (lambda: False)
        self._on_result = on_result
        self._stopped.clear()
        self._thread = threading.Thread(
            target=self._listener, daemon=True, name="smooth-move-tracker"
        )
        self._thread.start()
        return True

    def stop(self, timeout: float = 1.0) -> None:
        if self._thread is None:
            return
        tid = self._thread_id
        if tid:
            try:
                _PostThreadMessageW(tid, WM_QUIT, 0, 0)
            except Exception:
                pass
        self._stopped.wait(timeout=timeout)
        self._thread = None
        self._thread_id = None
        self._tracking = False

    # ── internals ─────────────────────────────────────────────────────────

    def _begin(self) -> None:
        self._tracking = True
        self._pos_x = 0.0
        self._pos_y = 0.0
        import time as _time
        self._hold_started = _time.perf_counter()
        log.debug("[SMOOTH_MOVE] capture start")

    def _feed(self, dx: float, dy: float) -> None:
        """Accumulate NET movement on both axes.

        Net displacement gives exactly the smart behavior needed:
        right 5,1,2 then back a few px (not through 0) then right
        again still records +; only crossing back through the 0 point
        flips the sign, and the magnitude is always the true camera
        rotation the macro must replay. Same independently for Y.
        """
        self._pos_x += dx
        self._pos_y += dy

    def _end(self) -> None:
        import time as _time
        self._tracking = False
        x = int(round(self._pos_x))
        y = int(round(self._pos_y))
        elapsed_ms = int((_time.perf_counter() - self._hold_started) * 1000)
        log.debug(f"[SMOOTH_MOVE] capture end x={x} y={y} elapsed={elapsed_ms}ms")
        cb = self._on_result
        if cb:
            try:
                cb(x, y, elapsed_ms)
            except Exception as e:
                log.error(f"[SMOOTH_MOVE] result callback failed: {e}")

    def _listener(self) -> None:
        hooked_kb = False
        raw_hwnd = None
        raw_class_name = None
        keyboard_hook = None
        keyboard_cb = None
        raw_cb = None
        try:
            self._thread_id = int(_GetCurrentThreadId())
            module_handle = _GetModuleHandleW(None)

            def raw_wnd_proc(hwnd, msg, w_param, l_param):
                if msg == WM_INPUT and self._tracking:
                    # focus lost mid-hold — stop the capture
                    if not _foreground_is_game():
                        self._end()
                        return 0
                    if not _raw_input_is_injected(l_param):
                        # true hardware movement — measure both axes
                        try:
                            dx, dy = _raw_mouse_delta(l_param)
                        except Exception:
                            dx, dy = 0, 0
                        if dx or dy:
                            self._feed(dx, dy)
                    return 0
                return _DefWindowProcW(hwnd, msg, w_param, l_param)

            class_name = f"SmoothMoveRawInputWindow_{self._thread_id}_{id(self)}"
            raw_cb = WNDPROC(raw_wnd_proc)
            wnd_class = WNDCLASSW()
            wnd_class.lpfnWndProc = raw_cb
            wnd_class.hInstance = module_handle
            wnd_class.lpszClassName = class_name
            if _RegisterClassW(ctypes.byref(wnd_class)):
                raw_class_name = class_name
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
                    _RegisterRawInputDevices(
                        ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)
                    )

            def keyboard_proc(n_code, w_param, l_param):
                if n_code == HC_ACTION:
                    info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                    vk = int(info.vkCode)
                    injected = bool(info.flags & LLKHF_INJECTED)
                    if not injected and vk == self._hold_vk:
                        is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                        is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)
                        if self._tracking:
                            # swallow every hold-key event while capturing
                            if is_up:
                                self._end()
                            return 1
                        if is_down:
                            try:
                                busy = bool(self._is_busy())
                            except Exception:
                                busy = False
                            if not busy and _foreground_is_game():
                                self._begin()
                                return 1  # the game never sees the key
                return _CallNextHookEx(None, n_code, w_param, l_param)

            keyboard_cb = HOOKPROC(keyboard_proc)
            keyboard_hook = _SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_cb, module_handle, 0)
            if not keyboard_hook:
                log.warning("[SMOOTH_MOVE] keyboard hook install failed")
                return
            hooked_kb = True

            msg = MSG()
            while True:
                ret = _GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret in (0, -1):
                    break
                _TranslateMessage(ctypes.byref(msg))
                _DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._tracking:
                try:
                    self._end()
                except Exception:
                    pass
            if hooked_kb and keyboard_hook:
                try:
                    _UnhookWindowsHookEx(keyboard_hook)
                except Exception:
                    pass
            if raw_hwnd:
                try:
                    _DestroyWindow(raw_hwnd)
                except Exception:
                    pass
            if raw_class_name:
                try:
                    ctypes.windll.user32.UnregisterClassW(
                        raw_class_name, ctypes.wintypes.HINSTANCE(module_handle)
                    )
                except Exception:
                    pass
            self._thread_id = None
            self._tracking = False
            self._stopped.set()
