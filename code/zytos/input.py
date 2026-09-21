# ============================================================
# ZYTOS - input
# Fight strafe uses the SAME hold method as Kraken's working W/S loop:
#   keyboard.press(key) every 50ms (hold, not tap), keyboard.release others.
# Macro engine KEY_DOWN/KEY_UP (SendInput scan-code) is also asserted so
# the game sees both injection paths.
#
# linear (from zytos.mcr):
#   D 1750ms once, then loop A 1750 / D 1750
# square:
#   W/D/S/A at ZYTOS_SQUARE_HOLD_SECONDS each
# ============================================================
import time
import threading

from logger import get_logger

log = get_logger()

_VK = {"w": 0x57, "a": 0x41, "s": 0x53, "d": 0x44}
_ALL_KEYS = ("w", "a", "s", "d")


def _live_wasd_map():
    try:
        from macro_runner import live_wasd
        return live_wasd()
    except Exception:
        return {k: (k, _VK[k]) for k in _ALL_KEYS}


def _key_name(letter: str) -> str:
    return _live_wasd_map().get(letter, (letter, _VK.get(letter, 0x57)))[0]


def _key_vk(letter: str) -> int:
    return _live_wasd_map().get(letter, (letter, _VK.get(letter, 0x57)))[1]


def _cfg():
    import config as _c
    return _c


def _macro_key_down(vk: int):
    try:
        from macro_runner import _key_down
        _key_down(vk)
    except Exception:
        pass


def _macro_key_up(vk: int):
    try:
        from macro_runner import _key_up
        _key_up(vk)
    except Exception:
        pass


def release_movement_keys():
    """Release W/A/S/D via keyboard lib AND macro-engine SendInput (same as kraken)."""
    wasd = _live_wasd_map()
    try:
        import keyboard as _kb
        for k in _ALL_KEYS:
            name = wasd.get(k, (k, 0))[0]
            try:
                _kb.release(k)
            except Exception:
                pass
            try:
                if name and name != k:
                    _kb.release(name)
            except Exception:
                pass
        for extra in ("shift", "ctrl"):
            try:
                _kb.release(extra)
            except Exception:
                pass
    except Exception:
        pass
    for k in _ALL_KEYS:
        _macro_key_up(wasd.get(k, (k, _VK[k]))[1])
        _macro_key_up(_VK[k])


def _assert_key(held: str):
    """Hold `held`, release the other WASD keys. Mirrors kraken _walk_loop."""
    import keyboard as _kb
    held = str(held or "").strip().lower()
    wasd = _live_wasd_map()
    for k in _ALL_KEYS:
        name, vk = wasd.get(k, (k, _VK[k]))
        if k == held:
            try:
                _kb.press(name)
            except Exception:
                pass
            _macro_key_down(vk)
        else:
            try:
                _kb.release(name)
            except Exception:
                pass
            _macro_key_up(vk)


def run_strafe_loop(stop_event: threading.Event, movement_mode: str = "linear"):
    """Background walk until stop_event is set.

    Same structure as kraken's working W/S loop in bot.py:
      while not stopped:
          press current key, release others
          every 50ms re-assert (keyboard.press holds; it does NOT tap)
          after hold_s, switch key
    """
    cfg = _cfg()
    hold_s = max(0.05, float(getattr(cfg, "ZYTOS_STRAFE_HOLD_MS", 1750)) / 1000.0)
    initial_key = str(getattr(cfg, "ZYTOS_STRAFE_INITIAL_KEY", "d")).strip().lower()
    if initial_key not in _VK:
        initial_key = "d"
    other = "a" if initial_key == "d" else "d"
    square_s = max(0.05, float(getattr(cfg, "ZYTOS_SQUARE_HOLD_SECONDS", 2.0)))
    mode = str(movement_mode or "linear").strip().lower()
    if mode not in {"linear", "square"}:
        mode = "linear"

    if mode == "square":
        pattern = [("w", square_s), ("d", square_s), ("s", square_s), ("a", square_s)]
    else:
        # D 1750 first (edge prep), then A 1750 / D 1750 forever.
        pattern = [(initial_key, hold_s), (other, hold_s)]

    log.info(
        "[ZYTOS] walk loop started mode=%s pattern=%s (keyboard.press hold + macro KEY_DOWN, same as kraken W/S)",
        mode,
        " -> ".join(f"{k.upper()} {int(s * 1000)}ms" for k, s in pattern),
    )
    idx = 0
    phase_start = time.time()
    last_logged = None
    try:
        while not stop_event.is_set():
            key, phase_secs = pattern[idx]
            if last_logged != (idx, key):
                log.info("[ZYTOS] strafe HOLD %s for %.0fms", key.upper(), phase_secs * 1000.0)
                last_logged = (idx, key)
            _assert_key(key)
            if (time.time() - phase_start) >= phase_secs:
                idx = (idx + 1) % len(pattern)
                phase_start = time.time()
            time.sleep(0.05)
    finally:
        release_movement_keys()
        log.info("[ZYTOS] walk loop stopped")


def click_join_twice():
    from macro_runner import _mouse_left_click, _mouse_move_abs
    cfg = _cfg()
    x, y = getattr(cfg, "ZYTOS_JOIN_CENTER")
    gap = max(0.0, float(getattr(cfg, "ZYTOS_JOIN_CLICK_GAP_SECONDS", 0.5)))
    for idx in range(2):
        _mouse_move_abs(int(x), int(y))
        time.sleep(0.06)
        _mouse_left_click()
        log.debug(f"[ZYTOS] JOIN click {idx + 1}/2 at ({x},{y})")
        if idx == 0:
            time.sleep(gap)


def prepare_weapon():
    from macro_runner import trigger_binding_action
    cfg = _cfg()
    wait_s = max(0.0, float(getattr(cfg, "ZYTOS_POST_JOIN_WAIT_SECONDS", 1.0)))
    binding = str(getattr(cfg, "ZYTOS_WEAPON_BINDING", None) or getattr(cfg, "WEAPON_1_BINDING", "1"))
    time.sleep(wait_s)
    for idx in range(3):
        if not trigger_binding_action(binding, hold_ms=45):
            trigger_binding_action("1", hold_ms=45)
        log.debug(f"[ZYTOS] weapon binding press {idx + 1}/3 ({binding})")
        time.sleep(0.12)


def aim_fight():
    """Fight aim from zytos.mcr: SmoothMouseMove(-75, -50, 50)."""
    from macro_runner import _smooth_move_rel, _scale_smooth_move
    aim_dx, aim_dy = _scale_smooth_move(-75, -50)
    log.info("[ZYTOS] smooth mouse aim: raw(-75,-50) scaled(%d,%d) over 50ms", aim_dx, aim_dy)
    _smooth_move_rel(aim_dx, aim_dy, 50)


def look_left_post_fight():
    """Post-fight look left from zytos.mcr: SmoothMouseMove(-150, 0, 50)."""
    from macro_runner import _smooth_move_rel, _scale_smooth_move
    aim_dx, aim_dy = _scale_smooth_move(-150, 0)
    log.info("[ZYTOS] post-fight look left: raw(-150,0) scaled(%d,%d) over 50ms", aim_dx, aim_dy)
    _smooth_move_rel(aim_dx, aim_dy, 50)


def walk_forward(duration_s: float, stop_check) -> bool:
    """Hold W for duration_s the same way kraken reward-walk does. Returns False if killed."""
    release_movement_keys()
    time.sleep(0.08)
    fwd_name, fwd_vk = _live_wasd_map().get("w", ("w", 0x57))
    try:
        import keyboard as _kb
        _kb.press(fwd_name)
    except Exception:
        pass
    _macro_key_down(fwd_vk)
    t0 = time.perf_counter()
    try:
        while (time.perf_counter() - t0) < duration_s:
            if stop_check():
                return False
            try:
                import keyboard as _kb
                _kb.press(fwd_name)
            except Exception:
                pass
            _macro_key_down(fwd_vk)
            time.sleep(0.05)
        return True
    finally:
        release_movement_keys()
