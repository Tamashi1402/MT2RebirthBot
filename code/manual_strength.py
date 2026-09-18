# ============================================================
# Manual Strength upgrader
# Used when dashboard Auto Strength is OFF.
# ============================================================
import time
import threading
import ctypes

import cv2
import numpy as np

import config as _cfg
from logger import get_logger, debug_every
from macro_runner import (
    _key_press, _mouse_left_click, _mouse_move_abs,
    _mouse_left_down, _mouse_left_up,
)
from screen import grab_region

log = get_logger()


_ROWS = [
    ("row5", (("row5_left", "MANUAL_STR_ROW5_LEFT"), ("row5_right", "MANUAL_STR_ROW5_RIGHT"))),
    ("row4", (("row4_left", "MANUAL_STR_ROW4_LEFT"), ("row4_right", "MANUAL_STR_ROW4_RIGHT"))),
    ("row3", (("row3_left", "MANUAL_STR_ROW3_LEFT"), ("row3_right", "MANUAL_STR_ROW3_RIGHT"))),
    ("row2", (("row2_left", "MANUAL_STR_ROW2_LEFT"), ("row2_right", "MANUAL_STR_ROW2_RIGHT"))),
    ("row1", (("row1_left", "MANUAL_STR_ROW1_LEFT"), ("row1_right", "MANUAL_STR_ROW1_RIGHT"))),
]

_BUTTONS = [button for _, row_buttons in _ROWS for button in row_buttons]

_ROW_BURST_CLICKS = 10
# Lowered from 0.45 to 0.25: close button is ~25% transparent after map update
_CLOSE_YELLOW_THRESH = float(getattr(_cfg, "MANUAL_STR_CLOSE_YELLOW_THRESH", 0.25))
_close_lock = threading.Lock()


def _move_settle_delay() -> float:
    return 0.0


# Click pacing is hardcoded: down -> 1ms -> up -> 1ms -> next click.
# The up->next-down gap is required: without it the game can eat clicks
# (a click needs a beat between release and the next press to register).
# The old 50ms left-mouse hold was a bot-side bug, not a per-PC/internet
# thing, so none of this is a config fine-tune value.
_DOWNUP_PACE = 0.001
_CLICK_GAP   = 0.001

def _click_method() -> str:
    """Clicking method (Fine-Tuning -> Manual Strength -> Clicking method)."""
    try:
        m = str(getattr(_cfg, "MANUAL_STR_CLICK_METHOD", "default") or "default").strip().lower()
        return m if m in ("default", "classic", "compat") else "default"
    except Exception:
        return "default"


def _is_compat_pacing() -> bool:
    """True when clicks must be paced with a guaranteed 12ms spin-wait.

    time.sleep(0.001) is only a REAL 1ms on machines where the game raises
    the Windows timer to 1ms - the game's UI drops nearly all near-1ms
    clicks there. On the default ~15.6ms timer the same sleep stretches to
    ~15ms and clicks register fine. The spin-wait paces both machines
    identically."""
    return _click_method() == "compat"


def _spin_wait(stop_event, seconds: float) -> bool:
    """Busy-wait a guaranteed real delay (perf_counter), stop-event aware."""
    end = time.perf_counter() + max(0.0, seconds)
    while time.perf_counter() < end:
        if stop_event is not None and stop_event.is_set():
            return False
        time.sleep(0.0005)
    return True


# Bottom-row spam pattern: N right-side buys, then M left-side unlock.
# The right side holds ~5 affordable upgrades and one click on the left
# re-unlocks it - a 1:1 L/R ping-pong wastes half its taps on a locked
# left button. N/M are user-configurable (5/1 by default, 1/1 = plain
# alternation).
def _bottom_right_clicks() -> int:
    try:
        return max(1, int(getattr(_cfg, "MANUAL_STR_BOTTOM_RIGHT_CLICKS", 5) or 5))
    except Exception:
        return 5


def _bottom_left_clicks() -> int:
    try:
        return max(1, int(getattr(_cfg, "MANUAL_STR_BOTTOM_LEFT_CLICKS", 1) or 1))
    except Exception:
        return 1


def _bottom_row_pattern(names: list) -> tuple:
    """Click order for the bottom-row spam: N right-side buys, then M left unlocks.

    Buttons are named *_left / *_right (row5_left, row5_right). If the
    naming scheme ever changes, fall back to plain alternation.
    """
    right = [i for i, n in enumerate(names) if n.lower().endswith("_right")]
    left = [i for i, n in enumerate(names) if n.lower().endswith("_left")]
    if right and left:
        pattern = [right[i % len(right)] for i in range(_bottom_right_clicks())]
        pattern += [left[i % len(left)] for i in range(_bottom_left_clicks())]
        return tuple(pattern)
    return tuple(range(len(names)))


def _click_delay() -> float:
    """Gap between one click's LEFTUP and the next LEFTDOWN.

    Configurable via MANUAL_STR_CLICK_DELAY_MS (Fine-Tuning -> Manual
    Strength -> Click delay, default 1ms). Compat mode forces the guaranteed
    12ms spin-wait instead."""
    if _is_compat_pacing():
        return 0.012
    try:
        # floor at 1ms: 0ms pacing makes the game merge/eat every click
        return max(1, int(getattr(_cfg, "MANUAL_STR_CLICK_DELAY_MS", 1))) / 1000.0
    except Exception:
        return _CLICK_GAP

def _downup_delay() -> float:
    """Hold time between LEFTDOWN and LEFTUP.

    Configurable via MANUAL_STR_CLICK_HOLD_MS (Fine-Tuning -> Manual
    Strength -> Click hold, default 1ms). Compat mode forces 12ms."""
    if _is_compat_pacing():
        return 0.012
    try:
        return max(1, int(getattr(_cfg, "MANUAL_STR_CLICK_HOLD_MS", 1))) / 1000.0
    except Exception:
        return _DOWNUP_PACE


def _pace_wait(stop_event, seconds: float) -> bool:
    """Sleep a click-pacing delay: spin-wait in compat mode, plain sleep otherwise."""
    if _is_compat_pacing():
        return _spin_wait(stop_event, seconds)
    if stop_event is not None:
        return _sleep_or_stop(stop_event, seconds)
    time.sleep(seconds)
    return False


def _post_click_delay() -> float:
    return 0.0


def _active_rows():
    if bool(getattr(_cfg, "MANUAL_STR_ONLY_LAST_ROW", True)):
        return _ROWS[:1]
    return _ROWS


def _center(region: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = [int(v) for v in region]
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    cx = int((x1 + x2) // 2)
    cy = int((y1 + y2) // 2)
    sw = int(ctypes.windll.user32.GetSystemMetrics(0) or 1920)
    sh = int(ctypes.windll.user32.GetSystemMetrics(1) or 1080)
    cx = max(0, min(max(0, sw - 1), cx))
    cy = max(0, min(max(0, sh - 1), cy))
    return (cx, cy)


def _buyable_percent(img) -> float:
    """Buyable buttons show green price text; red/grey/white/blue UI streaks are not buyable."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    green = cv2.inRange(
        hsv,
        np.array([45, 65, 115], dtype=np.uint8),
        np.array([82, 255, 255], dtype=np.uint8),
    )
    mask = green
    total = img.shape[0] * img.shape[1]
    return float(np.sum(mask > 0)) / total if total else 0.0


def _is_buyable(region: tuple[int, int, int, int]) -> bool:
    try:
        img = grab_region(region)
        pct = _buyable_percent(img)
        log.debug(f"[MANUAL_STR] buyable pct={pct:.1%} region={region}")
        return pct >= 0.020
    except Exception as e:
        log.warning(f"[MANUAL_STR] button scan failed for {region}: {e}")
        return False


def _is_window_open() -> bool:
    """The strength window is present when the yellow CLOSE button is visible.

    F4 dest-list uses the same yellow family and can fill this crop (~65%) —
    that is not the shop. If the teleport menu is up, this is closed.
    """
    try:
        from screen import _f4_menu_probably_open
        if _f4_menu_probably_open():
            return False
    except Exception:
        pass
    try:
        region = getattr(_cfg, "MANUAL_STR_CLOSE_REGION")
        img = grab_region(region)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 65, 100], dtype=np.uint8),  # widened val floor 120->100 for semi-transparent close
            np.array([45, 255, 255], dtype=np.uint8),
        )
        pct = float(np.sum(yellow > 0)) / float(img.shape[0] * img.shape[1])
        debug_every(
            "ms_open",
            2.0,
            f"[MANUAL_STR] window yellow={pct:.1%} open={pct >= _CLOSE_YELLOW_THRESH}",
        )
        return pct >= _CLOSE_YELLOW_THRESH
    except Exception as e:
        log.warning(f"[MANUAL_STR] window-open check failed: {e}")
        return True


def is_window_open() -> bool:
    """Public helper for recovery code that needs to detect a stray menu."""
    return _is_window_open()


def _sleep_or_stop(stop_event: threading.Event, seconds: float) -> bool:
    return stop_event.wait(max(0.0, seconds))


def _fast_left_click(stop_event: threading.Event | None = None):
    # Down, short hold, up — NOT _mouse_left_click() (which hard-holds 50ms).
    hold = _downup_delay()
    _mouse_left_down()
    if hold:
        _pace_wait(stop_event, hold)
    _mouse_left_up()


def _click_button_raw(
    name: str,
    region: tuple[int, int, int, int],
    stop_event: threading.Event | None = None,
    reason: str = "refresh",
) -> bool:
    if stop_event and stop_event.is_set():
        return False
    # Guard against accidental world clicks if menu closes between checks.
    if not _is_window_open():
        log.debug(f"[MANUAL_STR] skipped {reason} click {name}; strength window not open")
        return False
    x, y = _center(region)
    _mouse_move_abs(x, y)
    log.debug(f"[MANUAL_STR] {reason} click {name}")
    _fast_left_click(stop_event)
    _fast = _click_delay()
    if _fast > 0:
        _pace_wait(stop_event, _fast)
    return True



def _click_if_still_buyable(
    name: str,
    region: tuple[int, int, int, int],
    stop_event: threading.Event | None = None,
) -> bool:
    """Scan immediately before moving, then click only if the button is buyable."""
    if stop_event and stop_event.is_set():
        return False
    if not _is_buyable(region):
        log.debug(f"[MANUAL_STR] skipped {name}; not buyable before click")
        return False
    return _click_button_raw(name, region, stop_event, reason="buy")


def _refresh_row_prices(
    row_name: str,
    row_buttons,
    clicks: int,
    stop_event: threading.Event | None = None,
    stop_fn=None,
) -> int:
    """Click non-buyable buttons to force the strength menu to refresh prices."""
    clicked = 0
    if clicks <= 0:
        return 0
    for idx in range(clicks):
        if stop_event and stop_event.is_set():
            break
        if stop_fn and stop_fn():
            break
        if not _is_window_open():
            log.info("[MANUAL_STR] strength window closed while refreshing row")
            break
        name, attr = row_buttons[idx % len(row_buttons)]
        region = getattr(_cfg, attr)
        if _click_button_raw(name, region, stop_event, reason=f"price-refresh {row_name}"):
            clicked += 1
    if clicked:
        log.debug(f"[MANUAL_STR] refreshed {row_name} with {clicked} red/non-buyable clicks")
    return clicked


def _spam_bottom_row(
    row_name: str,
    row_buttons,
    deadline: float,
    stop_event: threading.Event | None = None,
    stop_fn=None,
    activity_callback=None,
) -> int:
    """Bottom-row-only: N right clicks then M left, as fast as possible. No OCR.

    N/M come from config (default 5 right / 1 left - see _bottom_row_pattern).
    Window-open is checked every few clicks so we do not screenshot every tap.
    """
    points = []
    names = []
    for name, attr in row_buttons:
        try:
            points.append(_center(getattr(_cfg, attr)))
            names.append(name)
        except Exception:
            continue
    if not points:
        return 0
    delay_s = _click_delay()
    clicked = 0
    last_open_check = 0.0
    pattern = _bottom_row_pattern(names)
    pattern_pos = 0
    while time.time() < deadline:
        if stop_event and stop_event.is_set():
            break
        if stop_fn and stop_fn():
            break
        now = time.time()
        if clicked == 0 or (clicked % 10 == 0) or (now - last_open_check >= 0.30):
            if not _is_window_open():
                log.info("[MANUAL_STR] strength window closed while spamming bottom row")
                break
            last_open_check = now
        side = pattern[pattern_pos % len(pattern)]
        pattern_pos += 1
        x, y = points[side]
        name = names[side]
        _mouse_move_abs(x, y)
        _fast_left_click(stop_event)
        clicked += 1
        if activity_callback:
            try:
                activity_callback(row_name, name)
            except Exception:
                pass
        if delay_s:
            if _pace_wait(stop_event, delay_s):
                break
    if clicked:
        log.debug(f"[MANUAL_STR] bottom-row spam clicked {clicked} times")
    return clicked



def _drain_row(
    row_name: str,
    row_buttons,
    stop_event: threading.Event | None = None,
    stop_fn=None,
    max_clicks: int = _ROW_BURST_CLICKS,
    confirm_empty: bool = True,
    activity_callback=None,
) -> int:
    """Quickly alternate left/right in a row, checking buyability before every click.

    When confirm_empty is enabled, if 3 consecutive full passes yield no buyable
    button, do 8 OCR re-checks (50 ms apart) before confirming the row is empty.
    """
    bought = 0
    _no_click_passes = 0          # consecutive passes with zero clicks
    _OCR_CONFIRM_THRESHOLD = 3    # passes before triggering extra OCR confirms
    _OCR_CONFIRM_CHECKS    = 8    # extra OCR checks before accepting "empty row"
    _OCR_CONFIRM_DELAY     = 0.05

    while bought < max_clicks:
        clicked_this_pass = False
        for name, attr in row_buttons:
            if stop_event and stop_event.is_set():
                return bought
            if stop_fn and stop_fn():
                return bought
            if not _is_window_open():
                log.info("[MANUAL_STR] strength window closed while draining row")
                return bought
            region = getattr(_cfg, attr)
            if not _is_buyable(region):
                continue
            log.debug(f"[MANUAL_STR] buying {name}")
            if not _click_if_still_buyable(name, region, stop_event):
                continue
            bought += 1
            if activity_callback:
                try:
                    activity_callback(row_name, name)
                except Exception:
                    pass
            clicked_this_pass = True
            _no_click_passes = 0   # reset on any successful click
            if bought >= max_clicks:
                break

        if not clicked_this_pass:
            if not confirm_empty:
                break
            _no_click_passes += 1
            if _no_click_passes >= _OCR_CONFIRM_THRESHOLD:
                # Before giving up, do extra OCR sweeps to rule out transient glitch
                confirmed_empty = True
                for _chk in range(_OCR_CONFIRM_CHECKS):
                    if stop_event and stop_event.is_set():
                        if bought:
                            log.debug(f"[MANUAL_STR] drained {bought} clicks from {row_name}")
                        return bought
                    time.sleep(_OCR_CONFIRM_DELAY)
                    for name, attr in row_buttons:
                        region = getattr(_cfg, attr)
                        if _is_buyable(region):
                            confirmed_empty = False
                            log.debug(f"[MANUAL_STR] OCR confirm check {_chk+1}/{_OCR_CONFIRM_CHECKS}: {name} buyable — continuing row")
                            break
                    if not confirmed_empty:
                        break
                if confirmed_empty:
                    log.debug(f"[MANUAL_STR] row {row_name} confirmed empty after {_OCR_CONFIRM_CHECKS} checks")
                    break
                _no_click_passes = 0  # a button became buyable, reset and continue
            # else: just a single empty pass — loop back and retry

    if bought:
        log.debug(f"[MANUAL_STR] drained {bought} clicks from {row_name}")
    return bought


def _buy_available_manual_strength(
    deadline: float,
    idle_wait: float,
    stop_event: threading.Event | None = None,
    stop_fn=None,
    close_on_idle: bool = True,
    activity_callback=None,
) -> int:
    """Buy manual strength rows.

    Bottom-row-only mode keeps row5 refresh behavior. Buy-all mode walks upward
    from the current row and only resets to bottom after no rows are buyable.
    """
    bought = 0
    idle_deadline = time.time() + idle_wait
    rows = _active_rows()
    bottom_only = len(rows) == 1
    if bottom_only:
        log.info("[MANUAL_STR] bottom-row-only: L/R spam, no button OCR")
        row_name, row_buttons = rows[0]
        bought = _spam_bottom_row(
            row_name,
            row_buttons,
            deadline,
            stop_event,
            stop_fn,
            activity_callback=activity_callback,
        )
        return bought
    next_side_by_row = {row_name: 0 for row_name, _ in rows}
    row_cursor = 0

    while time.time() < deadline:
        if stop_event and stop_event.is_set():
            break
        if stop_fn and stop_fn():
            log.debug("[MANUAL_STR] stop requested; closing window")
            break
        if not _is_window_open():
            log.info("[MANUAL_STR] strength window missing; reopening")
            if not _open_window(stop_event, attempts=3):
                log.info("[MANUAL_STR] strength window still missing; stopping buy loop")
                break
            continue

        # Buy-all mode: walk upward. Do not keep clicking/refreshing row5 when
        # it is not buyable; reset to bottom only after every row was checked.
        clicked_any = False
        scan_rows = rows if bottom_only else rows[row_cursor:]
        for scan_offset, (row_name, row_buttons) in enumerate(scan_rows):
            absolute_row_idx = scan_offset if bottom_only else row_cursor + scan_offset
            start_idx = next_side_by_row.get(row_name, 0) % len(row_buttons)
            rotated_buttons = row_buttons[start_idx:] + row_buttons[:start_idx]
            clicked_button = None

            def _mark_activity(activity_row, activity_button):
                nonlocal clicked_button
                clicked_button = activity_button
                if activity_callback:
                    activity_callback(activity_row, activity_button)

            row_bought = _drain_row(
                row_name,
                rotated_buttons,
                stop_event,
                stop_fn,
                max_clicks=1,
                confirm_empty=False,
                activity_callback=_mark_activity,
            )
            if row_bought:
                button_names = [name for name, _ in row_buttons]
                if clicked_button in button_names:
                    next_side_by_row[row_name] = (button_names.index(clicked_button) + 1) % len(row_buttons)
                else:
                    next_side_by_row[row_name] = (start_idx + 1) % len(row_buttons)
                bought += row_bought
                idle_deadline = time.time() + idle_wait
                clicked_any = True
                if not bottom_only:
                    row_cursor = absolute_row_idx
                break
            if not bottom_only:
                continue
            refresh_clicks = 10
            if _refresh_row_prices(row_name, rotated_buttons, refresh_clicks, stop_event, stop_fn):
                button_names = [name for name, _ in row_buttons]
                next_side_by_row[row_name] = (start_idx + refresh_clicks) % len(button_names)
                clicked_any = True
                break

        if clicked_any:
            continue

        if not bottom_only:
            row_cursor = 0

        if close_on_idle and time.time() >= idle_deadline:
            log.debug(f"[MANUAL_STR] idle for {idle_wait:.1f}s; done")
            break
        if stop_event:
            stop_event.wait(0.12)
        else:
            time.sleep(0.12)

    return bought

def _bot_may_open_window() -> bool:
    """Manual Strength Open checkbox (default on). Off = the bot never opens
    the strength window itself — a macro must do it; the loop waits instead."""
    try:
        return bool(getattr(_cfg, "MANUAL_STR_OPEN", True))
    except Exception:
        return True


def _open_window(stop_event: threading.Event | None = None, attempts: int = 5) -> bool:
    if stop_event and stop_event.is_set():
        return False
    if _is_window_open():
        return True
    if not _bot_may_open_window():
        # MANUAL_STR_OPEN is off: do NOT press 2 / click — wait for the macro
        # to open the window, polling for the same total time the active path
        # would spend.
        log.info("[MANUAL_STR] auto-open disabled (Manual Strength Open) — waiting for macro to open the window")
        for _ in range(max(1, attempts) * 8):
            if stop_event and stop_event.is_set():
                return False
            if stop_event:
                if _sleep_or_stop(stop_event, 0.20):
                    return False
            else:
                time.sleep(0.20)
            if _is_window_open():
                log.debug("[MANUAL_STR] strength window open (opened externally)")
                return True
        log.warning("[MANUAL_STR] strength window never appeared (Manual Strength Open disabled)")
        return False
    for attempt in range(1, max(1, attempts) + 1):
        if stop_event and stop_event.is_set():
            return False
        log.debug(f"[MANUAL_STR] opening strength window (attempt {attempt}/{attempts})")
        _key_press(0x32)  # 2
        if stop_event and _sleep_or_stop(stop_event, 0.30):
            return False
        elif not stop_event:
            time.sleep(0.30)
        _mouse_left_click()
        for _ in range(6):
            if stop_event and _sleep_or_stop(stop_event, 0.20):
                return False
            elif not stop_event:
                time.sleep(0.20)
            if _is_window_open():
                log.debug(f"[MANUAL_STR] strength window confirmed after attempt {attempt}")
                return True
    log.warning("[MANUAL_STR] failed to confirm strength window after retries")
    return False


def close_window_verified(attempts: int = 5, stop_event: threading.Event | None = None) -> bool:
    """Click CLOSE until the strength window is confirmed gone."""
    with _close_lock:
        if not _is_window_open():
            return True
        center = getattr(_cfg, "MANUAL_STR_CLOSE_CENTER", None)
        if not center:
            center = _center(getattr(_cfg, "MANUAL_STR_CLOSE_REGION"))
        for attempt in range(1, max(1, attempts) + 1):
            if stop_event and stop_event.is_set():
                return False
            if not _is_window_open():
                return True
            log.debug(f"[MANUAL_STR] closing strength window at {center} (attempt {attempt}/{attempts})")
            _mouse_move_abs(int(center[0]), int(center[1]))
            _mouse_left_click()
            for _ in range(10):
                if stop_event and _sleep_or_stop(stop_event, 0.05):
                    return False
                elif not stop_event:
                    time.sleep(0.05)
                if not _is_window_open():
                    log.debug(f"[MANUAL_STR] strength window closed after attempt {attempt}")
                    return True
        log.warning("[MANUAL_STR] failed to confirm strength window closed after retries")
        return not _is_window_open()




class ManualStrengthHandle:
    def __init__(self, thread: threading.Thread, stop_event: threading.Event):
        self._thread = thread
        self._stop_event = stop_event

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def stop(self) -> bool:
        self._stop_event.set()
        self._thread.join(timeout=5.0)
        return not self._thread.is_alive()


def start_manual_strength_loop(
    reason: str = "",
    min_hit_seconds: float = 2.0,
    max_hit_wait_seconds: float = 6.0,
    wait_for_hit_fn=None,
    stop_fn=None,
    activity_callback=None,
) -> ManualStrengthHandle:
    """Open strength after the rock has been hit, then keep buying until stopped."""
    stop_event = threading.Event()

    def _worker():
        bought = 0
        opened = False
        try:
            if min_hit_seconds > 0:
                if stop_event.wait(min_hit_seconds):
                    return
            wait_started = time.time()
            while not stop_event.is_set() and not (stop_fn and stop_fn()):
                if wait_for_hit_fn is None or wait_for_hit_fn():
                    break
                if time.time() - wait_started >= max(0.0, max_hit_wait_seconds - min_hit_seconds):
                    log.debug("[MANUAL_STR] opening after max hit wait; stone movement not confirmed")
                    break
                stop_event.wait(0.2)
            if stop_fn and stop_fn():
                return
            opened = _open_window(stop_event, attempts=6)
            if not opened:
                return
            log.info(f"[MANUAL_STR] live loop started{f' ({reason})' if reason else ''}")

            deadline = float("inf")
            idle_wait = float(getattr(_cfg, "MANUAL_STR_IDLE_WAIT", 3.0))
            bought = _buy_available_manual_strength(
                deadline,
                idle_wait,
                stop_event,
                stop_fn,
                close_on_idle=False,
                activity_callback=activity_callback,
            )
            if not _is_window_open():
                opened = False
        except Exception as e:
            log.warning(f"[MANUAL_STR] live loop failed: {e}")
        finally:
            if opened:
                close_window_verified()
            log.info(f"[MANUAL_STR] live loop stopped; bought={bought}")

    t = threading.Thread(target=_worker, daemon=True, name="manual-strength")
    t.start()
    return ManualStrengthHandle(t, stop_event)
