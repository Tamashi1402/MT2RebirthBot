# ============================================================
# FARM METEOR - MAIN LOOP
# Own package. Engine (bot.py) only dispatches run_farm_meteor().
# Does not call rebirth/delve/kraken/zytos/crater mode functions.
#
# Areas (dashboard "Meteor" dropdown):
#   a6       : teleport A6 -> area6_to_node -> hold LMB 1s (break node)
#              -> teleport A6 -> area6_to_meteor -> farm 10 minutes
#              (node despawns) -> repeat from teleport + node break
#   a7 / a8  : teleport -> farm forever, crouch in/out every 19s (anti-AFK)
#
# Anti-AFK: crouch binding pressed twice (1s apart) every 19s while
# holding LMB.
#
# On failure (nav fail / macro fail / stone lost / lag abort):
#   - Force Restart ON  -> engine recovery (force_restart.macro /
#     menu resume), re-select Meteor Rewards loadout, restart the area
#     flow from the top (A6 restarts at break node).
#   - Force Restart OFF -> stop and wait for Start.
# ============================================================
import time

from logger import get_logger
from overlay import set_overlay
from macro_runner import trigger_binding_action, _mouse_left_down, _mouse_left_up

log = get_logger()

# Area 6: minutes of meteor farming before the node despawns and the
# flow must teleport back and break the node again.
METEOR_FARM_SECONDS = 600.0
# Anti-AFK cadence: crouch twice every ~20s.
ANTI_AFK_EVERY = 19.0


def _bot():
    import bot as b
    return b


def _stop_requested() -> bool:
    """F9 kill OR Down-Arrow test failure — abort everything."""
    b = _bot()
    return bool(getattr(b, "_KILLED", False) or getattr(b, "_TEST_FORCE_FAILURE", False))


def _must_exit() -> bool:
    """Stop requested OR stone lost (watcher fired — engine recovers)."""
    return _stop_requested() or bool(getattr(_bot(), "_STONE_LOST", False))


def _is_test_fail() -> bool:
    b = _bot()
    return bool(getattr(b, "_TEST_FORCE_FAILURE", False)) and not bool(getattr(b, "_KILLED", False))


def _clear_test_fail():
    try:
        _bot()._TEST_FORCE_FAILURE = False
    except Exception:
        pass


def _get_area() -> str:
    try:
        from dashboard import get_state as _ds
        area = str(_ds().get("farm_meteor_area") or "a6").strip().lower()
        return area if area in ("a6", "a7", "a8") else "a6"
    except Exception:
        return "a6"


def _get_force_restart() -> bool:
    try:
        from dashboard import get_state as _ds
        return bool(_ds().get("force_restart", False))
    except Exception:
        return False


def _dash(status, goal, **kw):
    try:
        from dashboard import update_state
        update_state(status=status, goal=goal, **kw)
    except Exception:
        pass


def _status(status, goal):
    _dash(status, goal)
    try:
        set_overlay(status=status, goal=goal)
    except Exception:
        pass


def _try_bot_recovery(reason: str) -> bool:
    """Engine recovery: force_restart.macro + verification, then menu resume."""
    b = _bot()
    try:
        recovered = b._try_force_restart_after_failure(reason)
        if recovered:
            log.info("[FARM_METEOR] force_restart succeeded — game reloaded")
            return True
    except Exception as e:
        log.error(f"[FARM_METEOR] force_restart failed: {e}")
    log.warning("[FARM_METEOR] force_restart verification failed — trying menu_resume")
    try:
        recovered = b._do_menu_resume()
    except Exception as e:
        log.error(f"[FARM_METEOR] menu_resume failed: {e}")
        recovered = False
    if recovered:
        log.info("[FARM_METEOR] menu_resume succeeded — game reloaded")
        return True
    log.error("[FARM_METEOR] all recovery attempts failed")
    return False


def _hold_lag_ok() -> bool:
    """Net guard: freeze during lag. False only when the bot is stopping."""
    try:
        from net_guard import hold_if_needed
        return hold_if_needed()
    except Exception:
        return True


def _anti_afk_crouch():
    """Press the crouch binding twice with ~1s gap (anti-AFK).

    Called while LMB is held — crouch does not release the mouse button.
    """
    try:
        import config as _cfg
        binding = str(getattr(_cfg, "CROUCH_BINDING", "CTRL") or "CTRL").strip()
        trigger_binding_action(binding)
        time.sleep(1.0)
        if _must_exit():
            return
        trigger_binding_action(binding)
    except Exception as e:
        log.debug(f"[FARM_METEOR] anti-AFK crouch failed: {e}")


def _hold_left(seconds: float, anti_afk: bool = True) -> bool:
    """Hold LMB for `seconds`. Anti-AFK: crouch twice every ~20s.

    Returns False when the hold was aborted (kill / stone lost / stop),
    True when the full duration elapsed.
    """
    if _must_exit():
        return False
    log.info(f"[FARM_METEOR] holding LMB for {seconds:.0f}s (anti_afk={anti_afk})")
    _mouse_left_down()
    try:
        deadline = time.monotonic() + max(0.05, float(seconds))
        next_afk = time.monotonic() + ANTI_AFK_EVERY
        while time.monotonic() < deadline:
            if _must_exit():
                return False
            if not _hold_lag_ok():
                return False
            if anti_afk and time.monotonic() >= next_afk:
                _anti_afk_crouch()
                next_afk = time.monotonic() + ANTI_AFK_EVERY
            time.sleep(0.10)
        return True
    finally:
        try:
            _mouse_left_up()
        except Exception:
            pass


def _hold_left_forever() -> bool:
    """Hold LMB in chunks until stopped. False = aborted/failed."""
    while not _must_exit():
        if not _hold_lag_ok():
            return False
        if not _hold_left(60.0, anti_afk=True):
            return False
    return False


def _nav(macro_name: str, goal: str) -> bool:
    """Run a nav macro through the engine's net-redo-aware wrapper."""
    b = _bot()
    _status("RUNNING", goal)
    r = b._nav_or_redo(macro_name)
    if r == "kill":
        log.info(f"[FARM_METEOR] {macro_name}: stopped")
        return False
    if r == "redo":
        log.warning(f"[FARM_METEOR] {macro_name}: lag during walk — session failed")
        return False
    if r != "ok":
        log.warning(f"[FARM_METEOR] {macro_name}: macro failed")
        return False
    log.info(f"[FARM_METEOR] {macro_name}: ok")
    return True


def _teleport(destination: str) -> bool:
    """Teleport via the engine's safe teleport (F4 menu, retries, verify)."""
    b = _bot()
    _status("RUNNING", f"Teleport {destination}")
    if not b._builtin_teleport_safe(destination, attempts=10, wait_seconds=3.5):
        log.warning(f"[FARM_METEOR] teleport to {destination} failed")
        return False
    return True


# ── Area 6: break node -> farm meteor 10 min -> repeat ───────
def _farm_area6() -> bool:
    # Node must be broken first (respawns every 10 min).
    if not _teleport("area6"):
        return False
    if not _nav("area6_to_node", "Meteor: A6 node"):
        return False
    _status("RUNNING", "Meteor: A6 breaking node")
    log.info("[FARM_METEOR] breaking node (1s LMB)")
    if not _hold_left(1.0, anti_afk=False):
        return False

    if not _teleport("area6"):
        return False
    if not _nav("area6_to_meteor", "Meteor: A6 meteor"):
        return False

    _status("RUNNING", "Meteor: A6 meteor (10 min)")
    log.info("[FARM_METEOR] farming A6 meteor for 10 minutes")
    if not _hold_left(METEOR_FARM_SECONDS, anti_afk=True):
        return False
    log.info("[FARM_METEOR] A6 session complete — repeating node break")
    return True


def _farm_area78(area: str) -> bool:
    dest = "area7" if area == "a7" else "area8"
    if not _teleport(dest):
        return False
    # Optional walk. A7/A8 meteor is on the pad — dummy/missing macro is skipped.
    walk = "area7_to_meteor" if area == "a7" else "area8_to_meteor"
    try:
        from macro_runner import macro_exists
        has_walk = macro_exists(walk)
    except Exception:
        has_walk = False
    if has_walk:
        if not _nav(walk, f"Meteor: {area.upper()} meteor"):
            return False
    else:
        log.info(f"[FARM_METEOR] no {walk}.macro — farming from teleport pad")
    _status("RUNNING", f"Meteor: {area.upper()} meteor (AFK)")
    log.info(f"[FARM_METEOR] farming {area.upper()} meteor forever, crouch every {ANTI_AFK_EVERY:.0f}s")
    return _hold_left_forever()


# ── Main loop ────────────────────────────────────────────────
def run_farm_meteor():
    log.info("[FARM_METEOR] mode start")
    _status("RUNNING", "Meteor")
    failure_streak = 0
    while not _stop_requested():
        try:
            if not _hold_lag_ok():
                break
        except Exception:
            pass

        area = _get_area()
        _dash(status="RUNNING", goal=f"Meteor: {area}")

        ok = False
        try:
            if area == "a6":
                ok = _farm_area6()
            elif area in ("a7", "a8"):
                ok = _farm_area78(area)
            else:
                log.warning(f"[FARM_METEOR] unknown area {area!r} — stopping")
                break
        except Exception as e:
            log.exception(f"[FARM_METEOR] {area} error: {e}")
            ok = False

        if _stop_requested():
            break
        if _is_test_fail():
            _clear_test_fail()
            ok = False

        if ok:
            failure_streak = 0
            continue

        # ── Failure path: recover or stop ──
        failure_streak += 1
        log.warning(f"[FARM_METEOR] {area} session failed (streak={failure_streak})")
        # Dead-loop guard: same dashboard strike limit as the other modes.
        # After the limit, stop instead of force-restarting forever.
        try:
            _strike_limit = _bot()._route_redo_limit()
        except Exception:
            _strike_limit = 5
        if failure_streak >= _strike_limit:
            log.error(
                f"[FARM_METEOR] {failure_streak} consecutive failures — strike out, "
                "stopping (dead-loop guard)"
            )
            try:
                _bot()._rec_set_failure(f"strike_out:farm_meteor:{area}")
            except Exception:
                pass
            try:
                from screen import save_debug_fullscreen
                save_debug_fullscreen("farm_meteor_strike_out")
            except Exception as e:
                log.debug(f"[FARM_METEOR] strike-out screenshot failed: {e}")
            _status("STOPPED", "Meteor: strike out")
            break
        _status("RECOVERING", "Meteor: recovering")
        if not _get_force_restart():
            log.info("[FARM_METEOR] Force Restart off — stopping. Enable Force Restart to keep going.")
            break
        recovered = _try_bot_recovery(f"farm_meteor_{area}_session_failed")
        if not recovered:
            log.error("[FARM_METEOR] recovery failed — stopping")
            break
        # Re-select the Meteor Rewards loadout after the restart
        try:
            if not _bot()._apply_fresh_start_loadout():
                log.warning("[FARM_METEOR] Meteor Rewards loadout re-select failed after restart")
        except Exception as e:
            log.debug(f"[FARM_METEOR] loadout re-select error: {e}")
        time.sleep(1.0)

    _dash(status="WAITING", goal="Meteor", waiting_for_start=True)
    try:
        set_overlay(status="WAITING", goal="Meteor")
    except Exception:
        pass
    log.info("[FARM_METEOR] mode loop ended")
