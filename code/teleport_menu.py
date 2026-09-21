# F4 teleport + rebirth confirm clicks. Pixel-detect, no teleport macros.
import random
import time

import cv2
import numpy as np

import config as _cfg
from logger import get_logger
from macro_runner import _mouse_left_click, _mouse_move_abs, trigger_binding_action
from screen import grab_region

log = get_logger()

_killed_fn = None

_DEST_POINT_ATTR = {
    "base": "TELEPORT_DEST_BASE",
    "area1": "TELEPORT_DEST_AREA1",
    "area2": "TELEPORT_DEST_AREA2",
    "area3": "TELEPORT_DEST_AREA3",
    "area4": "TELEPORT_DEST_AREA4",
    "area5": "TELEPORT_DEST_AREA5",
    "area6": "TELEPORT_DEST_AREA6",
    "area7": "TELEPORT_DEST_AREA7",
    "area8": "TELEPORT_DEST_AREA8",
    "cosmic": "TELEPORT_DEST_COSMIC",
}

_DEST_SAMPLE_ATTR = {
    "area1": "TELEPORT_SAMPLE_AREA1",
    "area2": "TELEPORT_SAMPLE_AREA2",
    "area3": "TELEPORT_SAMPLE_AREA3",
    "area4": "TELEPORT_SAMPLE_AREA4",
    "area5": "TELEPORT_SAMPLE_AREA5",
    "area6": "TELEPORT_SAMPLE_AREA6",
    "cosmic": "TELEPORT_SAMPLE_COSMIC",
    "base": "TELEPORT_SAMPLE_BASE",
}
# TODO: Area 7 / Area 8 color samples — user could not pick them yet.
# Until then those dests wait 500ms after the Teleport click (no % check).
_DEST_FIXED_DELAY = {"area7": 0.50, "area8": 0.50}

_CLOSE_YELLOW = (247, 255, 26)   # #f7ff1a
# ── Semi-transparent close button support (map update 2026-09) ──
# The close button is now ~25% transparent, so exact RGB matching fails.
# We detect yellow via HSV inRange with a generous range, and require
# at least this fraction of pixels in the sample window to be yellow.
_CLOSE_YELLOW_MIN_PCT = float(getattr(_cfg, "CLOSE_YELLOW_MIN_PCT", 0.30))
_REBIRTH2_GRAY = (191, 196, 200)  # #bfc4c8
# Semi-transparent dest buttons sit around #bbc0c5 vs dark panel #31363b.
# Match by luma %, not a single hex.
_DEST_LUMA_MIN = 130
_DEST_READY_PCT = 0.25
_DEST_SAMPLE_W = 14
_DEST_SAMPLE_H = 10
_BTN_SETTLE = 0.05          # extra after a button is seen, before click
_STEP_SETTLE = 0.15         # after F4 and after every click (uniform)


def _step_settle() -> float:
    try:
        return float(_cfg.ui_click_settle())
    except Exception:
        return _STEP_SETTLE


def _btn_settle() -> float:
    try:
        return float(_cfg.ui_btn_settle())
    except Exception:
        return _BTN_SETTLE


def set_killed_fn(fn):
    global _killed_fn
    _killed_fn = fn


def _is_killed() -> bool:
    try:
        return bool(_killed_fn()) if _killed_fn else False
    except Exception:
        return False


def _sleep_with_kill_abort(seconds: float, step: float = 0.02) -> bool:
    seconds = max(0.0, float(seconds))
    if seconds <= 0.0:
        return not _is_killed()
    try:
        from net_guard import hold_if_needed
        if not hold_if_needed():
            return False
    except Exception:
        pass
    deadline = time.time() + seconds
    while time.time() < deadline:
        if _is_killed():
            return False
        rem = deadline - time.time()
        time.sleep(min(max(0.005, step), max(0.0, rem)))
    return not _is_killed()


def _scale_xy(pt: tuple[int, int]) -> tuple[int, int]:
    """Map a 1920x1080 authoring point onto the current screen."""
    try:
        w = int(getattr(_cfg, "RUNTIME_WIDTH", 1920) or 1920)
        h = int(getattr(_cfg, "RUNTIME_HEIGHT", 1080) or 1080)
        sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0) or 1.0)
        sy = float(getattr(_cfg, "REGION_SCALE_Y", 1.0) or 1.0)
        return _cfg._scale_point_2d(pt, w, h, sx, sy)
    except Exception:
        return int(pt[0]), int(pt[1])


def _patch_wh(base_w: int, base_h: int) -> tuple[int, int]:
    """Scale a sample window so 4K / ultrawide keep the same % coverage."""
    sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0) or 1.0)
    sy = float(getattr(_cfg, "REGION_SCALE_Y", 1.0) or 1.0)
    return max(3, int(round(base_w * sx))), max(3, int(round(base_h * sy)))


def _pt(attr: str, fallback: tuple[int, int]) -> tuple[int, int]:
    val = getattr(_cfg, attr, None)
    try:
        if val is not None:
            return int(val[0]), int(val[1])
    except Exception:
        pass
    return _scale_xy(fallback)


def _region(attr: str, fallback: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    val = getattr(_cfg, attr, None)
    try:
        if val is not None and len(val) == 4:
            return int(val[0]), int(val[1]), int(val[2]), int(val[3])
    except Exception:
        pass
    try:
        w = int(getattr(_cfg, "RUNTIME_WIDTH", 1920) or 1920)
        h = int(getattr(_cfg, "RUNTIME_HEIGHT", 1080) or 1080)
        sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0) or 1.0)
        sy = float(getattr(_cfg, "REGION_SCALE_Y", 1.0) or 1.0)
        return _cfg._scale_region_2d(fallback, w, h, sx, sy)
    except Exception:
        return tuple(int(v) for v in fallback)


def _click_xy(x: int, y: int, attempt: int = 1) -> bool:
    if _is_killed():
        return False
    ox, oy = int(x), int(y)
    if int(attempt) >= 2:
        base = 3 + min(5, int(attempt))
        span_x, span_y = _patch_wh(base, base)
        ox += random.randint(-span_x, span_x)
        oy += random.randint(-span_y, span_y)
        log.info(f"[CLICK] retry offset ({x},{y}) → ({ox},{oy}) attempt={attempt}")
    _mouse_move_abs(ox, oy)
    # Hover dwell: the move is one instant SendInput, and a click fired in the
    # same instant can be ignored by the game (hit-test/hover not updated
    # yet). Give the UI a couple of frames to register the cursor on the
    # button before clicking.
    time.sleep(0.12)
    _mouse_left_click()
    return True


def _read_rgb(xy: tuple[int, int]) -> tuple[int, int, int] | None:
    x, y = int(xy[0]), int(xy[1])
    try:
        img = grab_region((x, y, x + 1, y + 1))
    except Exception:
        return None
    if img is None or getattr(img, "size", 0) == 0:
        return None
    b, g, r = [int(v) for v in img[0, 0][:3]]
    return r, g, b


def _fmt_rgb(rgb: tuple[int, int, int] | None) -> str:
    if not rgb:
        return "unreadable"
    r, g, b = rgb
    return f"RGB({r},{g},{b}) #{r:02x}{g:02x}{b:02x}"


def _log_color_miss(tag: str, xy: tuple[int, int], need: str, rgb=None, tol: int = 55) -> None:
    colors = (rgb,) if rgb is not None else ((0, 0, 0),)
    pct, center, w, h = _color_window_stats(xy, colors, tol=tol, base=12)
    got = center or _read_rgb(xy)
    log.warning(
        f"{tag} at ({int(xy[0])},{int(xy[1])}) win={w}x{h} match={pct:.0%} "
        f"got {_fmt_rgb(got)}  need {need}"
    )


def _color_window_stats(xy, colors, *, tol: int = 55, base: int = 12) -> tuple[float, tuple[int, int, int] | None, int, int]:
    """Match % of a scaled window around xy. Used for 4K / ratio logs."""
    colors = colors if colors and isinstance(colors[0], (tuple, list)) else (colors,)
    w, h = _patch_wh(base, base)
    x, y = int(xy[0]), int(xy[1])
    x1, y1 = max(0, x - w // 2), max(0, y - h // 2)
    try:
        img = grab_region((x1, y1, x1 + w, y1 + h))
    except Exception:
        return 0.0, None, w, h
    if img is None or getattr(img, "size", 0) == 0:
        return 0.0, _read_rgb(xy), w, h
    b = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    r = img[:, :, 2].astype(np.int16)
    mask = np.zeros(r.shape, dtype=bool)
    for rgb in colors:
        if not rgb:
            continue
        tr, tg, tb = int(rgb[0]), int(rgb[1]), int(rgb[2])
        dist = np.abs(r - tr) + np.abs(g - tg) + np.abs(b - tb)
        mask |= dist <= int(tol)
    pct = float(np.mean(mask)) if mask.size else 0.0
    cy, cx = min(img.shape[0] - 1, h // 2), min(img.shape[1] - 1, w // 2)
    center = (int(r[cy, cx]), int(g[cy, cx]), int(b[cy, cx]))
    return pct, center, w, h


def _close_yellow_pct(xy, win: int = 12) -> float:
    """Percentage of yellow pixels in a window around xy (HSV, semi-transparent safe).

    The close button is ~25% transparent after the map update, so exact RGB
    Manhattan distance fails. HSV hue stays stable under transparency; we use
    a generous sat/val floor to catch blended colors.
    """
    x, y = int(xy[0]), int(xy[1])
    w, h = _patch_wh(win, win)
    x1, y1 = max(0, x - w // 2), max(0, y - h // 2)
    try:
        img = grab_region((x1, y1, x1 + w, y1 + h))
    except Exception:
        return 0.0
    if img is None or getattr(img, "size", 0) == 0:
        return 0.0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Generous yellow range: hue 18-45, sat ≥ 65, val ≥ 100
    # Handles up to ~60% transparency over a dark background.
    yellow = cv2.inRange(
        hsv,
        np.array([18, 65, 100], dtype=np.uint8),
        np.array([45, 255, 255], dtype=np.uint8),
    )
    total = img.shape[0] * img.shape[1]
    return float(np.sum(yellow > 0)) / total if total > 0 else 0.0


def _close_yellow_at(xy, min_pct=None) -> bool:
    """True if the yellow close button is visible at xy (HSV %, semi-transparent safe)."""
    thresh = min_pct if min_pct is not None else _CLOSE_YELLOW_MIN_PCT
    return _close_yellow_pct(xy) >= thresh


def _wait_close_yellow(xy, timeout: float = 2.0, interval: float = 0.10, min_pct=None) -> bool:
    """Poll for the yellow close button using HSV percentage (semi-transparent safe).

    Replaces _wait_color() for all close-button checks.  _wait_color() and
    _pixel_matches() still exist for non-yellow colour checks (e.g. rebirth2 gray).
    """
    deadline = time.time() + max(0.0, float(timeout))
    thresh = min_pct if min_pct is not None else _CLOSE_YELLOW_MIN_PCT
    while True:
        if _is_killed():
            return False
        pct = _close_yellow_pct(xy)
        if pct >= thresh:
            log.debug(f"[CLOSE] yellow seen pct={pct:.0%} at ({int(xy[0])},{int(xy[1])})")
            return True
        if time.time() >= deadline:
            got = _read_rgb(xy)
            log.warning(
                f"[COLOR] close-yellow miss at ({int(xy[0])},{int(xy[1])}) "
                f"yellow_pct={pct:.0%} need>={thresh:.0%} "
                f"got {_fmt_rgb(got)}"
            )
            return False
        if not _sleep_with_kill_abort(interval):
            return False


def _pixel_matches(xy: tuple[int, int], rgb: tuple[int, int, int], tol: int = 55) -> bool:
    w, h = _patch_wh(3, 3)
    x, y = int(xy[0]), int(xy[1])
    x1, y1 = max(0, x - w // 2), max(0, y - h // 2)
    try:
        img = grab_region((x1, y1, x1 + w, y1 + h))
    except Exception:
        return False
    if img is None or getattr(img, "size", 0) == 0:
        return False
    tr, tg, tb = int(rgb[0]), int(rgb[1]), int(rgb[2])
    b = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    r = img[:, :, 2].astype(np.int16)
    dist = np.abs(r - tr) + np.abs(g - tg) + np.abs(b - tb)
    return bool(np.min(dist) <= int(tol))


def _wait_color(xy: tuple[int, int], rgb: tuple[int, int, int], timeout: float, interval: float = 0.1, tol: int = 55) -> bool:
    deadline = time.time() + max(0.0, float(timeout))
    while True:
        if _is_killed():
            return False
        if _pixel_matches(xy, rgb, tol=tol):
            return True
        if time.time() >= deadline:
            need = _fmt_rgb((int(rgb[0]), int(rgb[1]), int(rgb[2]))) + f" tol={tol}"
            _log_color_miss("[COLOR] miss", xy, need, rgb=rgb, tol=tol)
            return False
        if not _sleep_with_kill_abort(interval):
            return False


def _dest_ready_pct(xy: tuple[int, int]) -> float:
    """Fraction of pixels in a small box that look like the light-gray dest button.

    Buttons are semi-transparent (#bbc0c5-ish) over a dark panel (#31363b).
    Exact hex is useless; luma vs the dark background is the gate.
    """
    x, y = int(xy[0]), int(xy[1])
    w, h = _patch_wh(_DEST_SAMPLE_W, _DEST_SAMPLE_H)
    x1 = max(0, x - w // 2)
    y1 = max(0, y - h // 2)
    try:
        img = grab_region((x1, y1, x1 + w, y1 + h))
    except Exception:
        return 0.0
    if img is None or getattr(img, "size", 0) == 0:
        return 0.0
    b = img[:, :, 0].astype(np.float32)
    g = img[:, :, 1].astype(np.float32)
    r = img[:, :, 2].astype(np.float32)
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return float(np.mean(luma >= _DEST_LUMA_MIN))


def _wait_dest_ready(destination: str, shift_dx: float = 0.0) -> bool:
    if destination in _DEST_FIXED_DELAY:
        wait = max(0.0, float(getattr(_cfg, "MAP_LOAD_FIXED_SECONDS", 0.5) or 0.5))
        log.info(f"[TELEPORT] {destination}: no color sample yet — fixed settle {wait*1000:.0f}ms")
        return _sleep_with_kill_abort(wait)
    attr = _DEST_SAMPLE_ATTR.get(destination)
    if not attr:
        return _sleep_with_kill_abort(0.10)
    sample = _pt(attr, (810, 500))
    if shift_dx:
        sample = _shift_pt(sample, shift_dx)
    deadline = time.time() + 2.0
    while True:
        if _is_killed():
            return False
        pct = _dest_ready_pct(sample)
        if pct >= _DEST_READY_PCT:
            log.debug(f"[TELEPORT] {destination} dest ready luma_pct={pct:.0%} at {sample}")
            return True
        if time.time() >= deadline:
            got = _read_rgb(sample)
            luma = 0.0
            if got:
                luma = 0.2126 * got[0] + 0.7152 * got[1] + 0.0722 * got[2]
            log.warning(
                f"[TELEPORT] {destination} dest button not ready "
                f"(luma_pct={pct:.0%} need {_DEST_READY_PCT:.0%} at {sample} "
                f"win={_patch_wh(_DEST_SAMPLE_W, _DEST_SAMPLE_H)[0]}x{_patch_wh(_DEST_SAMPLE_W, _DEST_SAMPLE_H)[1]}) "
                f"got {_fmt_rgb(got)} luma={luma:.0f} need>={_DEST_LUMA_MIN}"
            )
            return False
        if not _sleep_with_kill_abort(0.10):
            return False


def _close_if_open(
    sample_xy: tuple[int, int],
    click_xy: tuple[int, int],
    close_rgb: tuple[int, int, int],
    tag: str,
    *,
    tries: int = 3,
    wait: float = 0.15,
) -> bool:
    """If the yellow close is still on screen after the menu should have gone, click it.

    `wait` is the delay after the action so the UI can close on its own first (150ms).
    """
    if wait and not _sleep_with_kill_abort(float(wait)):
        return False
    closed = 0
    for n in range(1, tries + 1):
        if _is_killed():
            return False
        if not _close_yellow_at(sample_xy):
            if closed:
                log.info(f"{tag} stall close gone after {closed} click(s)")
            return True
        log.warning(
            f"{tag} menu still open after done — clicking close "
            f"({int(click_xy[0])},{int(click_xy[1])}) ({n}/{tries})"
        )
        if not _click_xy(*click_xy):
            return False
        closed += 1
        if not _sleep_with_kill_abort(max(_step_settle(), 0.22)):
            return False
    still = _close_yellow_at(sample_xy)
    if still:
        log.warning(f"{tag} close still visible after {tries} clicks")
    return not still


def _force_close_menu(
    sample_xy: tuple[int, int],
    click_xy: tuple[int, int],
    close_rgb: tuple[int, int, int],
    tag: str,
) -> bool:
    """Always dismiss F4/loadout. Click close even if yellow isn't sampled.

    Dest-list miss leaves the menu open with no yellow at the sample point,
    so _close_if_open thinks it's already gone. Next F4 then toggles the
    leftover menu instead of opening a fresh one.
    """
    log.info(f"{tag} forcing menu close ({int(click_xy[0])},{int(click_xy[1])})")
    if not _click_xy(*click_xy):
        return False
    if not _sleep_with_kill_abort(max(_step_settle(), 0.22)):
        return False
    if not _close_yellow_at(sample_xy):
        return True
    log.warning(f"{tag} still open after force close — click again")
    if not _click_xy(*click_xy):
        return False
    if not _sleep_with_kill_abort(max(_step_settle(), 0.22)):
        return False
    if _close_yellow_at(sample_xy):
        log.warning(f"{tag} still open — F4 toggle")
        if not _press_f4():
            return False
        if not _sleep_with_kill_abort(max(_step_settle(), 0.22)):
            return False
    return True


def _redo_limit() -> int:
    try:
        return max(1, int(getattr(_cfg, "ROUTE_REDO_LIMIT", 5) or 5))
    except Exception:
        return 5


def _press_f4() -> bool:
    binding = getattr(_cfg, "MENU_TOGGLE_BINDING", "F4")
    if not trigger_binding_action(binding, hold_ms=35):
        log.warning(f"[TELEPORT] invalid MENU_TOGGLE_BINDING={binding!r}; using F4")
        trigger_binding_action("F4", hold_ms=35)
    return not _is_killed()


def _menu_shift_dx() -> float:
    """Runtime-scaled magnitude of the F4 menu left-shift bug (0 = disabled)."""
    try:
        base = float(getattr(_cfg, "TELEPORT_MENU_SHIFT_DX", 663) or 0)
    except Exception:
        base = 663.0
    if base <= 0:
        return 0.0
    try:
        sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0) or 1.0)
    except Exception:
        sx = 1.0
    return base * sx


def _shift_pt(pt: tuple[int, int], dx: float) -> tuple[int, int]:
    """Same point, shifted dx pixels to the left (y unchanged - bug is x-only)."""
    if not dx:
        return int(pt[0]), int(pt[1])
    return int(round(pt[0] - dx)), int(pt[1])


def teleport(destination: str, attempts: int | None = None, wait_seconds: float = 0.0) -> bool:
    """Open F4, wait for close-yellow, click Teleport, click destination."""
    destination = str(destination or "").strip().lower()
    attr = _DEST_POINT_ATTR.get(destination)
    if not attr:
        log.warning(f"[TELEPORT] unsupported destination: {destination!r}")
        return False
    dest_xy = _pt(attr, (960, 540))
    panel_xy = _pt("TELEPORT_PANEL_CLICK", (997, 836))
    close_sample = _pt("TELEPORT_CLOSE_SAMPLE", (1001, 957))
    close_click = _pt("TELEPORT_CLOSE_CLICK", (1001, 939))
    close_rgb = tuple(int(x) for x in getattr(_cfg, "TELEPORT_CLOSE_COLOR", _CLOSE_YELLOW))
    max_tries = _redo_limit() if attempts is None else max(1, int(attempts))
    # Consecutive opens where the menu opened fine and the Teleport panel was
    # clicked, but the dest button sample stayed dark. A dark button means the
    # destination is LOCKED (not unlocked yet in-game) — re-opening the menu
    # can never fix that, so after 2 consecutive dark reads we abort the
    # remaining attempts instead of spamming F4 (callers treat this like any
    # other teleport failure and take their unlock/redo path).
    dest_dark_streak = 0
    shift_dx = _menu_shift_dx()

    for attempt in range(1, max_tries + 1):
        if _is_killed():
            return False
        log.info(f"[TELEPORT] {destination} attempt {attempt}/{max_tries}")
        if not _press_f4():
            return False
        if not _sleep_with_kill_abort(_step_settle()):
            return False

        use_shift = False
        shifted_close_sample = _shift_pt(close_sample, shift_dx) if shift_dx else None
        if not _wait_close_yellow(close_sample, timeout=2.0, interval=0.10):
            # Menu-shift bug: the whole F4 panel can render further left than
            # normal. Check the shifted spot before assuming a stuck leftover
            # menu — if it's there, the menu opened fine, just shifted; work
            # this whole attempt with every F4-menu coordinate shifted the
            # same amount instead of force-closing + reopening.
            if shifted_close_sample and _close_yellow_at(shifted_close_sample):
                log.info(f"[TELEPORT] menu shifted left ~{shift_dx:.0f}px — using shifted coords, no reopen needed")
                use_shift = True
            else:
                # Not shifted, and not open at the normal spot either. Could
                # just be a slow render rather than a genuinely stuck leftover
                # menu — re-press F4 once (skip the blind force-close click,
                # which can misfire if the game is actually on a different
                # page) before falling back to the disruptive path.
                log.warning(f"[TELEPORT] F4 close-yellow not seen ({attempt}/{max_tries}) — quick re-press before force-close")
                if not _press_f4():
                    return False
                if not _sleep_with_kill_abort(_step_settle()):
                    return False
                if _wait_close_yellow(close_sample, timeout=1.0, interval=0.10):
                    use_shift = False
                elif shifted_close_sample and _close_yellow_at(shifted_close_sample):
                    log.info(f"[TELEPORT] menu shifted left ~{shift_dx:.0f}px after re-press — using shifted coords")
                    use_shift = True
                else:
                    log.warning(f"[TELEPORT] still not open after re-press ({attempt}/{max_tries}) — dismiss leftover menu, wait 4s")
                    _force_close_menu(close_sample, close_click, close_rgb, "[TELEPORT]")
                    if not _sleep_with_kill_abort(4.0):
                        return False
                    continue

        eff_close_sample = shifted_close_sample if use_shift else close_sample
        eff_close_click  = _shift_pt(close_click, shift_dx) if use_shift else close_click
        eff_panel_xy      = _shift_pt(panel_xy, shift_dx) if use_shift else panel_xy
        eff_dest_xy       = _shift_pt(dest_xy, shift_dx) if use_shift else dest_xy
        eff_shift_for_sample = shift_dx if use_shift else 0.0

        if not _sleep_with_kill_abort(_btn_settle()):
            return False
        log.info(f"[TELEPORT] F4 open — clicking panel {eff_panel_xy}")
        if not _click_xy(*eff_panel_xy, attempt=attempt):
            _force_close_menu(eff_close_sample, eff_close_click, close_rgb, "[TELEPORT]")
            return False
        if not _sleep_with_kill_abort(_step_settle()):
            return False
        if not _wait_dest_ready(destination, shift_dx=eff_shift_for_sample):
            log.warning(f"[TELEPORT] dest list not ready ({attempt}/{max_tries})")
            _force_close_menu(eff_close_sample, eff_close_click, close_rgb, "[TELEPORT]")
            dest_dark_streak += 1
            if dest_dark_streak >= 2:
                log.warning(
                    f"[TELEPORT] {destination} button dark on {dest_dark_streak} consecutive "
                    f"opens — destination appears LOCKED (not unlocked); aborting remaining attempts"
                )
                break
            continue
        dest_dark_streak = 0
        if not _sleep_with_kill_abort(_btn_settle()):
            return False
        log.info(f"[TELEPORT] clicking {destination} {eff_dest_xy}")
        if not _click_xy(*eff_dest_xy, attempt=attempt):
            _force_close_menu(eff_close_sample, eff_close_click, close_rgb, "[TELEPORT]")
            return False
        _close_if_open(eff_close_sample, eff_close_click, close_rgb, "[TELEPORT]", wait=0.15)
        log.info(f"[TELEPORT] {destination} clicked")
        return True

    _force_close_menu(close_sample, close_click, close_rgb, "[TELEPORT]")
    if shift_dx and _close_yellow_at(_shift_pt(close_sample, shift_dx)):
        _force_close_menu(_shift_pt(close_sample, shift_dx), _shift_pt(close_click, shift_dx), close_rgb, "[TELEPORT]")
    log.warning(f"[TELEPORT] {destination} failed after {max_tries} attempts")
    return False


def _wait_luma_at(xy: tuple[int, int], timeout: float = 2.0) -> bool:
    deadline = time.time() + max(0.0, float(timeout))
    last = 0.0
    while True:
        if _is_killed():
            return False
        last = _dest_ready_pct(xy)
        if last >= _DEST_READY_PCT:
            return True
        if time.time() >= deadline:
            got = _read_rgb(xy)
            luma = 0.0
            if got:
                luma = 0.2126 * got[0] + 0.7152 * got[1] + 0.0722 * got[2]
            log.warning(
                f"[COLOR] luma miss at ({int(xy[0])},{int(xy[1])}) "
                f"got {_fmt_rgb(got)} luma={luma:.0f} luma_pct={last:.0%} "
                f"need luma>={_DEST_LUMA_MIN} pct>={_DEST_READY_PCT:.0%}"
            )
            return False
        if not _sleep_with_kill_abort(0.10):
            return False


def select_loadout(slot: int, attempts: int | None = None) -> bool:
    """F4 → Loadouts → slot N. Same detect pattern as teleport."""
    try:
        n = int(slot)
    except Exception:
        return False
    if n < 1 or n > 6:
        log.warning(f"[LOADOUT] invalid slot {slot!r}")
        return False
    panel_click = _pt("LOADOUT_PANEL_CLICK", (1001, 659))
    panel_sample = _pt("LOADOUT_PANEL_SAMPLE", (853, 679))
    f4_close = _pt("TELEPORT_CLOSE_SAMPLE", (999, 958))
    f4_close_click = _pt("TELEPORT_CLOSE_CLICK", (1001, 939))
    panel_close = _pt("LOADOUT_CLOSE_SAMPLE", (959, 1054))
    panel_close_click = _pt("LOADOUT_CLOSE_CLICK", (958, 1028))
    slot_click = _pt(f"LOADOUT_SLOT_{n}", (960, 540))
    slot_sample = _pt(f"LOADOUT_SAMPLE_{n}", (960, 540))
    close_rgb = tuple(int(x) for x in getattr(_cfg, "TELEPORT_CLOSE_COLOR", _CLOSE_YELLOW))
    max_tries = _redo_limit() if attempts is None else max(1, int(attempts))

    def _unstick_loadout(*, wait: float = 0.15) -> bool:
        _close_if_open(panel_close, panel_close_click, close_rgb, "[LOADOUT]", wait=wait)
        return _close_if_open(f4_close, f4_close_click, close_rgb, "[LOADOUT]", wait=0.0)

    for attempt in range(1, max_tries + 1):
        if _is_killed():
            return False
        log.info(f"[LOADOUT] slot {n} attempt {attempt}/{max_tries}")
        if not _press_f4():
            return False
        if not _sleep_with_kill_abort(_step_settle()):
            return False
        if not _wait_close_yellow(f4_close, timeout=2.0, interval=0.10):
            log.warning(f"[LOADOUT] F4 close-yellow not seen ({attempt}/{max_tries})")
            continue
        if not _wait_luma_at(panel_sample, timeout=2.0):
            log.warning(f"[LOADOUT] loadouts button not ready ({attempt}/{max_tries})")
            _unstick_loadout()
            continue
        if not _sleep_with_kill_abort(_btn_settle()):
            return False
        _pc = (panel_click[0] + random.randint(-5, 5), panel_click[1] + random.randint(-3, 3))
        log.info(f"[LOADOUT] clicking loadouts {_pc}")
        if not _click_xy(*_pc, attempt=attempt):
            return False
        if not _sleep_with_kill_abort(_step_settle()):
            return False
        if not _wait_close_yellow(panel_close, timeout=1.2, interval=0.10):
            # First Loadouts click after start is often eaten. Re-click the button.
            _panel_ok = False
            for _rc in (2, 3):
                if _is_killed():
                    return False
                log.info(f"[LOADOUT] loadout panel not open — re-clicking loadouts (try {_rc})")
                if not _click_xy(panel_click[0] + random.randint(-5, 5),
                                 panel_click[1] + random.randint(-3, 3), attempt=_rc):
                    return False
                if _sleep_with_kill_abort(_step_settle()) and _wait_close_yellow(
                    panel_close, timeout=1.0, interval=0.10
                ):
                    _panel_ok = True
                    break
            if not _panel_ok:
                log.warning(f"[LOADOUT] loadout-panel close not seen ({attempt}/{max_tries})")
                _unstick_loadout()
                continue
        if not _wait_luma_at(slot_sample, timeout=2.0):
            log.warning(f"[LOADOUT] slot {n} button not ready ({attempt}/{max_tries})")
            _unstick_loadout()
            continue
        if not _sleep_with_kill_abort(_btn_settle()):
            return False
        _sc = (slot_click[0] + random.randint(-5, 5), slot_click[1] + random.randint(-3, 3))
        log.info(f"[LOADOUT] clicking slot {n} {_sc}")
        if not _click_xy(*_sc, attempt=attempt):
            return False
        # Selecting a slot closes the whole F4 menu by itself. Poll until both
        # close buttons are actually gone before considering any close click —
        # a sample taken mid-close still shows yellow, and that stray "close"
        # click lands in-game (absolute move + click = camera turn).
        # If the close buttons never disappear, the slot click was eaten —
        # re-click the slot (the panel is still open) before giving up.
        _slot_taken = False
        for _rc in range(3):
            if _is_killed():
                return False
            _gone_deadline = time.time() + 1.2
            while time.time() < _gone_deadline:
                if _is_killed():
                    return False
                if not _close_yellow_at(panel_close) and not _close_yellow_at(f4_close):
                    _slot_taken = True
                    break
                if not _sleep_with_kill_abort(0.10):
                    return False
            if _slot_taken:
                break
            if _close_yellow_at(panel_close) or _close_yellow_at(f4_close):
                log.info(f"[LOADOUT] slot {n} click not taken — re-clicking slot (try {_rc + 2})")
                if not _click_xy(slot_click[0] + random.randint(-5, 5),
                                 slot_click[1] + random.randint(-3, 3), attempt=_rc + 2):
                    return False
            else:
                _slot_taken = True
                break
        _unstick_loadout(wait=0.0)
        if not _slot_taken:
            log.warning(f"[LOADOUT] slot {n} click not taken ({attempt}/{max_tries}) — retrying")
            continue
        log.info(f"[LOADOUT] slot {n} selected")
        return True

    log.warning(f"[LOADOUT] slot {n} failed after {max_tries} attempts")
    return False


def wait_map_loaded(area: str, timeout: float | None = None) -> bool:
    """Single fixed settle after a teleport / map load.

    The old per-area load detection (base / A5 / A6 box colors, 5s timeout,
    Detect Map Loading toggle) is gone - every area now gets the same short
    MAP_LOAD_FIXED_SECONDS settle (default 0.5s).
    """
    key = str(area or "").strip().lower().replace(" ", "") or "map"
    try:
        settle = max(0.0, float(getattr(_cfg, "MAP_LOAD_FIXED_SECONDS", 0.5) or 0.5))
    except Exception:
        settle = 0.5
    log.info(f"[MAP] {key} settle {settle:.2f}s")
    return _sleep_with_kill_abort(settle)


def _black_screen_pct(*, wide: bool) -> float:
    """Near-black fraction. wide=True = fade-in (bigger crop, softer luma)."""
    if wide:
        region = _region("MAP_BLACK_REGION", (360, 90, 1560, 960))
        cut = 32.0
    else:
        region = _region("MAP_BLACK_OUT_REGION", (560, 250, 1360, 800))
        cut = 18.0
    try:
        x1, y1, x2, y2 = [int(v) for v in region]
        if x2 <= x1 or y2 <= y1:
            return 1.0
        img = grab_region((x1, y1, x2, y2))
    except Exception:
        return 1.0
    if img is None or getattr(img, "size", 0) == 0:
        return 1.0
    sample = img[::3, ::3]
    b = sample[:, :, 0].astype(np.float32)
    g = sample[:, :, 1].astype(np.float32)
    r = sample[:, :, 2].astype(np.float32)
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return float(np.mean(luma <= cut))


def wait_black_screen_gone(timeout: float = 8.0, settle: float = 1.0) -> bool:
    """After rebirth2: new fade-IN window, old fade-OUT (center crop, stricter black).

    Never skip just because the wide window looks 'visible' — that fired teleport
    while still respawning. Fade-out uses the old 45% / 2-hit rule.
    """
    timeout = max(1.0, float(timeout))
    settle = max(0.0, float(settle))
    t0 = time.time()
    deadline = t0 + timeout
    black_hits = 0
    gone_hits = 0
    phase = "wait_fade_in"
    last_in = 1.0
    last_out = 1.0
    min_alive = 2.0

    log.info("[MAP] rebirth fade watch start (new fade-in, old fade-out)")
    while True:
        if _is_killed():
            return False
        elapsed = time.time() - t0
        if phase == "wait_fade_in":
            last_in = _black_screen_pct(wide=True)
            log.info(f"[MAP] rebirth fade {phase}  t={elapsed:.2f}s  black_in={last_in:.0%}")
            if last_in >= 0.40:
                black_hits += 1
                if black_hits >= 1:
                    phase = "wait_fade_out"
                    gone_hits = 0
                    log.info(f"[MAP] rebirth fade-in seen (black={last_in:.0%}) — now wait fade-out")
            else:
                black_hits = 0
                if elapsed >= 2.5:
                    phase = "wait_fade_out"
                    gone_hits = 0
                    log.info(
                        f"[MAP] rebirth fade-in not seen ({elapsed:.1f}s, black_in={last_in:.0%}) "
                        f"— wait old fade-out"
                    )
        else:
            last_out = _black_screen_pct(wide=False)
            log.info(f"[MAP] rebirth fade {phase}  t={elapsed:.2f}s  black_out={last_out:.0%}")
            if last_out < 0.45:
                gone_hits += 1
                if gone_hits >= 2 and elapsed >= min_alive:
                    log.info(
                        f"[MAP] rebirth fade-out seen (black={last_out:.0%}) — wait {settle*1000:.0f}ms"
                    )
                    return _sleep_with_kill_abort(settle)
            else:
                gone_hits = 0

        if time.time() >= deadline:
            log.info(
                f"[MAP] rebirth fade timeout {timeout:.1f}s phase={phase} "
                f"in={last_in:.0%} out={last_out:.0%} — continuing"
            )
            return _sleep_with_kill_abort(settle)
        if not _sleep_with_kill_abort(0.08):
            return False


def confirm_rebirth_ui() -> tuple[bool, str]:
    """After base_to_rebirth walk/E: wait close-yellow, click rebirth1, wait rebirth2, click it.

    Returns (ok, reason). reason is 'ok', 'menu_missing', 'no_confirm' (meteor not broken), or 'killed'.
    """
    close_sample = _pt("REBIRTH_CLOSE_SAMPLE", (381, 960))
    close_click = _pt("REBIRTH_CLOSE_CLICK", (381, 940))
    btn1 = _pt("REBIRTH_BTN1_CLICK", (955, 938))
    btn2_sample = _pt("REBIRTH_BTN2_SAMPLE", (1366, 966))
    btn2 = _pt("REBIRTH_BTN2_CLICK", (1548, 940))
    close_rgb = tuple(int(x) for x in getattr(_cfg, "TELEPORT_CLOSE_COLOR", _CLOSE_YELLOW))
    btn2_rgb = tuple(int(x) for x in getattr(_cfg, "REBIRTH_BTN2_COLOR", _REBIRTH2_GRAY))

    if not _sleep_with_kill_abort(_step_settle()):
        return False, "killed"
    if not _wait_close_yellow(close_sample, timeout=2.0, interval=0.10):
        log.warning("[REBIRTH] close-yellow not seen after walk — menu missing")
        return False, "menu_missing"

    if not _sleep_with_kill_abort(_step_settle()):
        return False, "killed"
    if not _sleep_with_kill_abort(_btn_settle()):
        return False, "killed"
    log.info(f"[REBIRTH] menu open — clicking rebirth1 {btn1}")
    if not _click_xy(*btn1):
        return False, "killed"

    if not _sleep_with_kill_abort(_step_settle()):
        return False, "killed"
    btn2_tol = int(getattr(_cfg, "REBIRTH_BTN2_TOL", 120) or 120)
    btn2_timeout = float(getattr(_cfg, "REBIRTH_BTN2_TIMEOUT", 4.0) or 4.0)
    if not _wait_color(btn2_sample, btn2_rgb, timeout=btn2_timeout, interval=0.10, tol=btn2_tol):
        close_still = _close_yellow_at(close_sample)
        if not close_still:
            log.warning("[REBIRTH] rebirth2 missing and close gone — meteor not broken / invalid rebirth")
        else:
            log.warning("[REBIRTH] rebirth2 missing — meteor not broken")
        _close_if_open(close_sample, close_click, close_rgb, "[REBIRTH]")
        return False, "no_confirm"

    if not _sleep_with_kill_abort(_btn_settle()):
        return False, "killed"
    log.info(f"[REBIRTH] clicking rebirth2 {btn2}")
    if not _click_xy(*btn2):
        return False, "killed"
    _close_if_open(close_sample, close_click, close_rgb, "[REBIRTH]", wait=0.15)
    return True, "ok"
