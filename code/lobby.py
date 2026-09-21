# Fortnite lobby / force-restart detect clicks (scaled 1920x1080 points).
from __future__ import annotations

import time

import config as _cfg
from logger import get_logger
from teleport_menu import (
    _click_xy,
    _color_window_stats,
    _fmt_rgb,
    _pixel_matches,
    _pt,
    _read_rgb,
)
from macro_runner import _mouse_left_click, _mouse_move_abs

log = get_logger()

_READY_WAIT = 300.0
_SHARD_WAIT = 300.0
_POLL = 0.50


def _killed() -> bool:
    try:
        import bot as _bot
        return bool(getattr(_bot, "_KILLED", False))
    except Exception:
        return False


def _sleep(seconds: float) -> bool:
    deadline = time.time() + max(0.0, float(seconds))
    while time.time() < deadline:
        if _killed():
            return False
        time.sleep(min(0.05, max(0.0, deadline - time.time())))
    return not _killed()


def _press_esc() -> None:
    from macro_runner import _key_press
    _key_press(0x1B, hold_ms=40)


def _as_colors(colors):
    if not colors:
        return ()
    if not isinstance(colors[0], (tuple, list)):
        return (colors,)
    return colors


def _need_str(colors) -> str:
    colors = _as_colors(colors)
    return "/".join(f"#{int(r):02x}{int(g):02x}{int(b):02x}" for r, g, b in colors)


def _dump(label: str, xy, colors, *, tol: int) -> bool:
    colors = _as_colors(colors)
    got = _read_rgb(xy)
    matched = any(_pixel_matches(xy, tuple(int(c) for c in rgb), tol=tol) for rgb in colors)
    pct, center, w, h = _color_window_stats(xy, colors, tol=tol, base=12)
    log.info(
        f"[LOBBY] {label}  xy=({int(xy[0])},{int(xy[1])})  "
        f"win={w}x{h} match={pct:.0%}  "
        f"got {_fmt_rgb(center or got)}  need {_need_str(colors)}  "
        f"tol={tol}  match={'YES' if matched else 'NO'}"
    )
    return matched


def _wait_color(xy, colors, timeout: float, *, pause_lag: bool, label: str, tol: int = 55) -> bool:
    colors = _as_colors(colors)
    _dump(f"{label} start", xy, colors, tol=tol)
    deadline = time.time() + float(timeout)
    last_dump = 0.0
    while time.time() < deadline:
        if _killed():
            return False
        if pause_lag:
            t0 = time.time()
            try:
                from net_guard import hold_if_needed, set_path_redo
                set_path_redo(False)
                if not hold_if_needed():
                    return False
            except Exception:
                pass
            deadline += max(0.0, time.time() - t0)
        if any(_pixel_matches(xy, tuple(int(c) for c in rgb), tol=tol) for rgb in colors):
            _dump(f"{label} seen", xy, colors, tol=tol)
            return True
        now = time.time()
        if now - last_dump >= 5.0:
            _dump(f"{label} waiting", xy, colors, tol=tol)
            last_dump = now
        if not _sleep(_POLL):
            return False
    _dump(f"{label} timeout", xy, colors, tol=tol)
    return False


def _step() -> float:
    try:
        return float(_cfg.lobby_step_delay())
    except Exception:
        return 0.50


def _click_slow(xy, label: str, attempt: int = 1) -> bool:
    step = _step()
    x, y = int(xy[0]), int(xy[1])
    if attempt >= 2:
        import random
        from teleport_menu import _patch_wh
        span_x, span_y = _patch_wh(4 + min(6, attempt), 4 + min(6, attempt))
        x += random.randint(-span_x, span_x)
        y += random.randint(-span_y, span_y)
    _dump(f"before {label} click", (x, y), ((255, 255, 255),), tol=999)
    _mouse_move_abs(x, y)
    if not _sleep(step):
        return False
    _mouse_left_click()
    log.info(f"[LOBBY] clicked {label} ({x}, {y})")
    if not _sleep(step):
        return False
    return True


def _overlay(status: str, goal: str) -> None:
    try:
        from overlay import set_overlay
        set_overlay(status=status, goal=goal)
    except Exception:
        pass
    try:
        import bot as _bot
        if hasattr(_bot, "_console_status"):
            _bot._console_status(status, goal)
    except Exception:
        pass


def _ready_pt():
    return _pt("FORCE_READY_SAMPLE", (252, 940)), getattr(_cfg, "FORCE_READY_COLOR", (247, 255, 26))


def _shard_pt():
    return _pt("FORCE_SHARD_SAMPLE", (1668, 773)), getattr(_cfg, "FORCE_SHARD_COLORS", ((111, 21, 192), (108, 15, 193)))


def _shard_now() -> bool:
    xy, colors = _shard_pt()
    return any(
        _pixel_matches(xy, tuple(int(c) for c in rgb), tol=60)
        for rgb in _as_colors(colors)
    )


def _wait_ready_or_shard(timeout: float) -> str | None:
    """Ready = lobby. Shard only if it vanished first (loading → new match)."""
    ready_xy, ready_rgb = _ready_pt()
    shard_xy, shard_rgbs = _shard_pt()
    deadline = time.time() + float(timeout)
    last = 0.0
    saw_no_shard = False
    _overlay("Restarting", "Waiting for lobby")
    log.info(f"[LOBBY] waiting Ready or new-load shard (max {timeout:.0f}s)")
    while time.time() < deadline:
        if _killed():
            return None
        t0 = time.time()
        try:
            from net_guard import hold_if_needed, set_path_redo
            set_path_redo(False)
            if not hold_if_needed():
                return None
        except Exception:
            pass
        deadline += max(0.0, time.time() - t0)
        if _pixel_matches(ready_xy, tuple(int(c) for c in ready_rgb), tol=70):
            _dump("ready", ready_xy, ready_rgb, tol=70)
            return "ready"
        shard = _shard_now()
        if not shard:
            if not saw_no_shard:
                log.info("[LOBBY] shard HUD gone — loading screen")
            saw_no_shard = True
        elif saw_no_shard:
            _dump("shard after loading", shard_xy, shard_rgbs, tol=60)
            return "shard"
        now = time.time()
        if now - last >= 5.0:
            _dump("ready (loading)", ready_xy, ready_rgb, tol=70)
            _dump("shard (loading)", shard_xy, shard_rgbs, tol=60)
            last = now
        if not _sleep(_POLL):
            return None
    log.warning("[LOBBY] Ready not seen after wait")
    return None


def _wait_new_shard(timeout: float) -> bool:
    """After Ready: shard must vanish (load) then come back."""
    shard_xy, shard_rgbs = _shard_pt()
    deadline = time.time() + float(timeout)
    saw_no = False
    last = 0.0
    log.info("[LOBBY] waiting for shard after Ready (must leave then reappear)")
    while time.time() < deadline:
        if _killed():
            return False
        t0 = time.time()
        try:
            from net_guard import hold_if_needed, set_path_redo
            set_path_redo(False)
            if not hold_if_needed():
                return False
        except Exception:
            pass
        deadline += max(0.0, time.time() - t0)
        if not _shard_now():
            if not saw_no:
                log.info("[LOBBY] shard gone after Ready — loading")
            saw_no = True
        elif saw_no:
            _dump("shard after Ready", shard_xy, shard_rgbs, tol=60)
            return True
        now = time.time()
        if now - last >= 5.0:
            _dump("shard after Ready", shard_xy, shard_rgbs, tol=60)
            last = now
        if not _sleep(_POLL):
            return False
    _dump("shard after Ready timeout", shard_xy, shard_rgbs, tol=60)
    return False


def _ready_and_join() -> bool:
    ready_click = _pt("FORCE_READY_CLICK", (255, 910))
    ready_settle = float(_cfg.lobby_ready_settle())
    shard_settle = float(_cfg.lobby_settle())
    step = _step()

    which = _wait_ready_or_shard(_READY_WAIT)
    if which == "shard":
        log.info("[LOBBY] loaded in-game after loading — skip Ready")
        return bool(_sleep(shard_settle))
    if which != "ready":
        log.warning("[LOBBY] Ready not found after wait — stopping")
        return False
    log.info(f"[LOBBY] Ready seen — waiting {ready_settle:.0f}s before click")
    if not _sleep(ready_settle):
        return False
    _click_xy(*ready_click)
    log.info(f"[LOBBY] clicked Ready {ready_click}")
    if not _sleep(step):
        return False

    _overlay("Restarting", "Joining match")
    if not _wait_new_shard(_SHARD_WAIT):
        log.warning("[LOBBY] shard did not reappear after Ready — stopping")
        return False
    if not _sleep(shard_settle):
        return False
    log.info("[LOBBY] in-game (shard) — continue")
    return True


def _join() -> bool:
    """Rejoin MT2 from the lobby menu: OCR flow v2 (fr_flow).

    Finds the lobby (PLAY OCR + scroll-up drift protection), verifies the
    selected game is Miner Tycoon 2 (wrong game -> island-code map search),
    presses PLAY, then waits for the picked in-game HUD image.
    Falls back to the legacy pixel Ready/shard flow if fr_flow is missing."""
    try:
        from fr_flow import menu_join_flow
        return bool(menu_join_flow("lobby join"))
    except Exception as e:
        log.warning(f"[LOBBY] fr_flow join failed ({e}) â legacy fallback")
        return _join()


def _pause_menu_open() -> bool:
    xy = _pt("FORCE_ESC_SAMPLE", (1622, 149))
    rgb = getattr(_cfg, "FORCE_ESC_COLOR", (5, 14, 38))
    return _pixel_matches(xy, tuple(int(c) for c in rgb), tol=40)


def _dismiss_game_menus() -> None:
    """Close F4 / loadout / rebirth if their yellow X is on screen.

    Those menus eat the first ESC (close themselves instead of opening pause).
    """
    try:
        from teleport_menu import _close_yellow_at, _click_xy
    except Exception:
        return
    pairs = (
        ("F4", _pt("TELEPORT_CLOSE_SAMPLE", (1001, 957)), _pt("TELEPORT_CLOSE_CLICK", (1001, 939))),
        ("loadout", _pt("LOADOUT_CLOSE_SAMPLE", (959, 1054)), _pt("LOADOUT_CLOSE_CLICK", (958, 1028))),
        ("rebirth", _pt("REBIRTH_CLOSE_SAMPLE", (381, 960)), _pt("REBIRTH_CLOSE_CLICK", (381, 940))),
    )
    for name, sample, click in pairs:
        try:
            if not _close_yellow_at(sample):
                continue
            log.info(f"[FORCE_RESTART] {name} menu open — clicking close before ESC")
            _click_xy(*click)
            if not _sleep(0.25):
                return
        except Exception as e:
            log.debug(f"[FORCE_RESTART] dismiss {name}: {e}")


def _esc_open_pause_menu(step: float, ready_xy, ready_rgb) -> str:
    """ESC until pause menu or lobby Ready.

    First ESC often only closes map/F4/rebirth/loading UI. If the pause-menu
    color is missing, press ESC again.
    Returns 'ready' | 'pause' | 'none'.
    """
    esc_xy = _pt("FORCE_ESC_SAMPLE", (1622, 149))
    esc_rgb = getattr(_cfg, "FORCE_ESC_COLOR", (5, 14, 38))
    for n in range(1, 4):
        if _killed():
            return "none"
        if _dump("ready mid-leave", ready_xy, ready_rgb, tol=70):
            return "ready"
        if _dump("pause menu", esc_xy, esc_rgb, tol=40):
            log.info(f"[FORCE_RESTART] pause menu open (ESC x{n - 1})")
            return "pause"
        _press_esc()
        log.info(f"[FORCE_RESTART] ESC press {n}/3")
        if not _sleep(step):
            return "none"
        if _dump("ready after ESC", ready_xy, ready_rgb, tol=70):
            return "ready"
        if _dump("pause menu", esc_xy, esc_rgb, tol=40):
            log.info("[FORCE_RESTART] pause menu open")
            return "pause"
        log.info("[FORCE_RESTART] pause menu not seen — ESC again (leftover menu ate the last one)")
    return "none"


def force_restart() -> bool:
    """Leave to the lobby (ESC -> Menu -> Return to lobby), then rejoin MT2.

    The rejoin is the OCR flow: lobby PLAY detection, Miner Tycoon 2 title
    verification (wrong game -> island-code map search), PLAY, in-game HUD
    image wait. In-match shard HUD is ignored during the leave."""
    try:
        from net_guard import set_path_redo
        set_path_redo(False)
    except Exception:
        pass
    try:
        _overlay("Restarting", "Leaving To Menu")
        ready_xy, ready_rgb = _ready_pt()
        if _dump("ready already", ready_xy, ready_rgb, tol=70):
            log.info("[FORCE_RESTART] already in lobby (Ready) — skip ESC")
            return _join()

        step = _step()
        menu_xy = _pt("FORCE_MENU_CLICK", (1677, 66))
        exit_xy = _pt("FORCE_EXIT_SAMPLE", (1800, 779))
        exit_rgb = getattr(_cfg, "FORCE_EXIT_COLOR", (247, 255, 26))
        lobby_xy = _pt("FORCE_LOBBY_CLICK", (1567, 170))
        log.info(f"[FORCE_RESTART] try ESC → Menu → lobby  step={step:.2f}s")
        if not _sleep(step):
            return False

        panel_open = False
        if _killed():
            return False
        if _dump("ready mid-leave", ready_xy, ready_rgb, tol=70):
            log.info("[FORCE_RESTART] Ready appeared — skip ESC")
            return _join()
        _dismiss_game_menus()
        which = _esc_open_pause_menu(step, ready_xy, ready_rgb)
        if which == "ready":
            log.info("[FORCE_RESTART] Ready appeared during ESC — skip Menu")
            return _join()
        log.info("[FORCE_RESTART] wait then click Menu")
        if _click_slow(menu_xy, "Menu", 1):
            if _wait_color(exit_xy, exit_rgb, 8.0, pause_lag=False, label="exit panel", tol=70):
                panel_open = True
        if panel_open:
            if not _sleep(step):
                return False
            _click_slow(lobby_xy, "return to lobby")
        else:
            log.warning("[FORCE_RESTART] exit panel not seen — wait Ready 5 min")
        return _join()
    finally:
        try:
            from net_guard import set_path_redo
            set_path_redo(True)
        except Exception:
            pass


def menu_resume() -> bool:
    try:
        from net_guard import set_path_redo
        set_path_redo(False)
    except Exception:
        pass
    try:
        return _join()
    finally:
        try:
            from net_guard import set_path_redo
            set_path_redo(True)
        except Exception:
            pass
