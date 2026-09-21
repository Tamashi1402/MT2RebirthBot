# ============================================================
# ZYTOS - MAIN LOOP
# Own package. Engine (bot.py) only dispatches run_zytos().
# Does not call kraken/delve/rebirth mode functions.
#
# Flow:
#   F4 Area 8 -> a8_to_zytos.macro (walk only) -> E to open NPC
#   OCR mode (same Solo/Normal/Hard/Ex setting as Bramble) + HARD pill until match
#   JOIN x2 -> weapon -> 1s settle -> aim -> drill -> fight
#   Fight strafe: D 1750ms, then loop A 1750 / D 1750
#   (keyboard.press hold + macro KEY_DOWN, same method as kraken W/S)
#   After kill: look left, W 1.35s, E
#   Force restart / stone-lost: exit loop, engine owns recovery
# ============================================================
import time
import threading

from logger import get_logger
from overlay import set_overlay
from macro_runner import trigger_binding_action, _mouse_left_down, _mouse_left_up
from screen import is_rebirth_screen, is_in_menu

from . import detector as _det
from . import input as _inp
from .dodge import stop_zytos_dodge

log = get_logger()


def _bot():
    import bot as b
    return b


def _stop_requested() -> bool:
    """F9 / test-fail — abort everything."""
    b = _bot()
    return bool(getattr(b, "_KILLED", False) or getattr(b, "_TEST_FORCE_FAILURE", False))


def _must_exit() -> bool:
    """Stop requested OR stone lost (engine will force-restart)."""
    return _stop_requested() or bool(getattr(_bot(), "_STONE_LOST", False))


def _try_menu_resume(reason: str) -> bool:
    """Only when stone is already lost. Engine menu-resume helper."""
    b = _bot()
    if not getattr(b, "_STONE_LOST", False):
        return False
    try:
        from dashboard import get_state as _ds
        if not b._menu_resume_enabled(_ds()):
            return False
    except Exception:
        return False
    try:
        if not is_in_menu():
            return False
    except Exception:
        return False
    log.warning(f"[ZYTOS] menu detected during {reason}; attempting menu resume")
    if b._do_menu_resume():
        log.info("[ZYTOS] menu resume succeeded")
        return True
    log.warning("[ZYTOS] menu resume failed")
    return False


def _open_menu_via_a8() -> bool:
    import config as cfg
    b = _bot()
    try:
        from bot import _route_redo_limit
        attempts = _route_redo_limit()
    except Exception:
        attempts = max(1, int(getattr(cfg, "ZYTOS_ROUTE_ATTEMPTS", 5)))
    wait_s = max(0.0, float(getattr(cfg, "ZYTOS_MENU_WAIT_SECONDS", 0.5)))
    for attempt in range(1, attempts + 1):
        if _stop_requested():
            return False
        if _try_menu_resume("route"):
            continue
        if getattr(b, "_STONE_LOST", False):
            return False
        b._console_status("ZYTOS", f"Teleport {attempt}/{attempts}")
        b._dash_update(status="ZYTOS", goal="Teleport")
        set_overlay(status="ZYTOS", goal="Teleport", run_start_time=0)
        if not b._builtin_teleport_safe("area8", attempts=10, wait_seconds=3.5):
            log.warning(f"[ZYTOS] F4 Area 8 teleport failed before zytos macro ({attempt}/{attempts})")
            continue
        b._console_status("ZYTOS", f"Navigation {attempt}/{attempts}")
        b._dash_update(status="ZYTOS", goal="Navigation")
        set_overlay(status="ZYTOS", goal="Navigation", run_start_time=0)
        if not b._run_macro("a8_to_zytos"):
            log.warning(f"[ZYTOS] a8_to_zytos macro failed ({attempt}/{attempts})")
            continue
        # a8_to_zytos is walk-only (no E). Press E in code so the nav macro
        # does not need to be re-recorded.
        log.info("[ZYTOS] pressing E to open boss menu after a8_to_zytos")
        trigger_binding_action("e", hold_ms=80)
        time.sleep(max(0.4, wait_s))
        close_ok = _det.close_visible()
        if not close_ok:
            trigger_binding_action("e", hold_ms=80)
            time.sleep(max(0.4, wait_s))
            close_ok = _det.close_visible()
        join_ok = _det.join_visible()
        if close_ok:
            if not join_ok:
                log.warning("[ZYTOS] CLOSE found but JOIN OCR missed; clicking configured JOIN center anyway")
            return True
        log.warning(f"[ZYTOS] boss menu not confirmed after route attempt {attempt}/{attempts}")
    try:
        b._rec_set_failure("redo_limit:zytos")
    except Exception:
        pass
    return False


def _reopen_menu_after_kill():
    """Post-kill approach: look left, walk forward, press E (from hand-made zytos.mcr).

    Returns True (reward menu visible), False (fallback route result), or
    the string "death" if the black/respawn screen appeared during the approach.
    Same model as Kraken: the kill was confirmed without a black screen, but a
    late respawn screen can still show up - so every step is death-guarded.
    """
    import config as cfg
    b = _bot()
    walk_s = 1.35
    wait_s = max(0.0, float(getattr(cfg, "ZYTOS_REWARD_OPEN_WAIT_SECONDS", 1.0)))

    state = {"death": False}

    def _death_or_exit() -> bool:
        if is_rebirth_screen():
            state["death"] = True
            return True
        return _must_exit()

    def _death_abort() -> bool:
        if state["death"]:
            log.info("[ZYTOS] death screen during post-fight approach - treating as death")
            return True
        return False

    _inp.release_movement_keys()
    time.sleep(0.08)
    if _must_exit():
        return False

    log.info("[ZYTOS] post-fight approach started (look left, W %.2fs, E)", walk_s)
    _inp.look_left_post_fight()
    # 0.5s settle after the look, checked in 0.05s steps so a death screen wins
    _look_deadline = time.time() + 0.50
    while time.time() < _look_deadline:
        if _death_or_exit():
            break
        time.sleep(0.05)
    if _death_abort():
        return "death"
    if _must_exit():
        return False

    _inp.walk_forward(walk_s, _death_or_exit)
    if _death_abort():
        return "death"
    if _must_exit():
        return False

    time.sleep(0.15)
    trigger_binding_action("e", hold_ms=80)
    # Settle while still watching for a late respawn screen
    _settle_deadline = time.time() + max(0.5, wait_s)
    while time.time() < _settle_deadline:
        if _death_or_exit():
            break
        time.sleep(0.05)
    if _death_abort():
        return "death"
    ok = _det.close_visible()
    if ok:
        log.info("[ZYTOS] reward menu confirmed after look-left + W + E")
        return ok

    log.warning("[ZYTOS] reward menu not visible after post-fight approach - fallback to full teleport route")
    b._console_status("ZYTOS", "Reward fallback")
    b._dash_update(status="ZYTOS", goal="Teleport")
    set_overlay(status="ZYTOS", goal="Teleport", run_start_time=0)
    return _open_menu_via_a8()


def run_zytos():
    """Zytos mode entry point. Called from bot.py dispatch only."""
    import config as cfg
    b = _bot()

    b._dash_update(run_active=True, status="ZYTOS", goal="Navigation", waiting_for_start=False)
    set_overlay(status="ZYTOS", goal="Navigation", run_start_time=0)
    log.info("[ZYTOS] loop started (own module: walk loop + mouse aim, no kraken calls)")
    menu_ready = False

    while not _must_exit():
        if not menu_ready:
            if not _open_menu_via_a8():
                if _must_exit():
                    break
                b._console_status("ZYTOS", "Menu retry")
                b._wait_polling(1.0, "Zytos retry", freeze=False)
                continue
        menu_ready = False

        b._console_status("ZYTOS", "Mode")
        b._dash_update(status="ZYTOS", goal="Mode")
        set_overlay(status="ZYTOS", goal="Mode", run_start_time=0)
        if not b._select_bramble_fight_mode(tag="ZYTOS"):
            log.warning("[ZYTOS] mode select failed — joining anyway")
        if _must_exit():
            break

        b._console_status("ZYTOS", "Navigation")
        b._dash_update(status="ZYTOS", goal="Navigation", run_start_time=None)
        set_overlay(status="ZYTOS", goal="Navigation", run_start_time=0)
        _inp.click_join_twice()
        _inp.prepare_weapon()

        log.info("[ZYTOS] waiting 1s after join before aiming/shooting/walking")
        b._wait_polling(1.0, "Zytos post-join settle", freeze=False)
        if _must_exit():
            break

        _inp.aim_fight()

        try:
            from dashboard import get_state as _ds_zytosdrill
            drill_on = bool(_ds_zytosdrill().get("zytos_activate_drills", True))
        except Exception:
            drill_on = bool(getattr(cfg, "ZYTOS_ACTIVATE_DRILLS", True))
        if drill_on:
            log.info("[ZYTOS] activating drill at fight start")
            b._trigger_drill_binding()

        boss_start = time.time()
        boss_end_reason = "ended"
        b._console_status("ZYTOS", "Fight")
        b._dash_update(status="ZYTOS", goal="Fight", run_start_time=boss_start)
        set_overlay(status="ZYTOS", goal="Fight", run_start_time=boss_start)
        try:
            from net_guard import set_path_redo as _set_zytos_redo
            _set_zytos_redo(False)
        except Exception:
            pass
        try:
            from dashboard import get_state as _ds_zytos_move
            movement_mode = str(_ds_zytos_move().get("zytos_movement_mode", "linear")).strip().lower()
        except Exception:
            movement_mode = str(getattr(cfg, "ZYTOS_MOVEMENT_MODE", "linear")).strip().lower()
        if movement_mode not in {"linear", "square"}:
            movement_mode = "linear"
        log.info("[ZYTOS] movement mode: %s", movement_mode)

        poll_s = max(0.03, float(getattr(cfg, "ZYTOS_SHOOT_POLL_SECONDS", 0.1)))
        reassert_s = max(poll_s, float(getattr(cfg, "ZYTOS_SHOOT_REASSERT_SECONDS", 0.5)))
        death_wait = max(0.0, float(getattr(cfg, "ZYTOS_DEATH_WAIT_SECONDS", 5)))
        hb_confirm_window_s = max(0.5, float(getattr(cfg, "ZYTOS_HB_CONFIRM_WINDOW_SECONDS", 3.5)))
        hb_post_loss_shoot_s = max(0.0, float(getattr(cfg, "ZYTOS_POST_HB_LOSS_SHOOT_SECONDS", 1.5)))
        first_hb_timeout_s = max(3.0, float(getattr(cfg, "ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", 8.0)))

        shooting = False
        kill_detected_at: float | None = None
        walk_stop = threading.Event()
        walk_thread = threading.Thread(
            target=_inp.run_strafe_loop,
            args=(walk_stop, movement_mode),
            daemon=True,
            name="zytos_walk_loop",
        )

        try:
            next_reassert = 0.0
            health_missing_since = None
            health_seen_once = False
            shooting = True
            walk_thread.start()

            while not _must_exit():
                now = time.time()

                if is_rebirth_screen():
                    log.info("[ZYTOS] black screen detected - death; restarting")
                    if shooting:
                        _mouse_left_up()
                        shooting = False
                    boss_end_reason = "death"
                    break

                if (not health_seen_once) and ((now - boss_start) >= first_hb_timeout_s):
                    log.warning(
                        "[ZYTOS] no health bar seen after %.1fs - treating as join failure and retrying",
                        now - boss_start,
                    )
                    if shooting:
                        _mouse_left_up()
                        shooting = False
                    walk_stop.set()
                    boss_end_reason = "join_failed"
                    break

                hb_seen_now = _det.health_bar_seen()
                if health_missing_since is None:
                    if hb_seen_now:
                        health_seen_once = True
                    elif health_seen_once:
                        health_missing_since = now
                        log.info(
                            "[ZYTOS] health bar gone — watching for %.1fs to confirm kill vs death",
                            hb_confirm_window_s,
                        )
                        if shooting and hb_post_loss_shoot_s > 0:
                            log.info("[ZYTOS] keeping fire for %.1fs after health bar loss", hb_post_loss_shoot_s)
                        elif shooting:
                            _mouse_left_up()
                            shooting = False
                        walk_stop.set()
                else:
                    elapsed = now - health_missing_since
                    if shooting and elapsed >= hb_post_loss_shoot_s:
                        _mouse_left_up()
                        shooting = False
                        log.info("[ZYTOS] post-loss fire window ended at %.2fs", elapsed)
                    if is_rebirth_screen():
                        log.info("[ZYTOS] black screen during confirm window (%.2fs) → death", elapsed)
                        if shooting:
                            _mouse_left_up()
                            shooting = False
                        boss_end_reason = "death"
                        break
                    elif elapsed >= hb_confirm_window_s:
                        kill_detected_at = health_missing_since
                        log.info(
                            "[ZYTOS] %.1fs confirm window passed, no black screen → boss killed",
                            elapsed,
                        )
                        if shooting:
                            _mouse_left_up()
                            shooting = False
                        boss_end_reason = "killed"
                        break

                if health_missing_since is None:
                    if now >= next_reassert:
                        _mouse_left_down()
                        next_reassert = now + reassert_s
                        log.debug("[ZYTOS] left mouse down asserted")

                time.sleep(poll_s)
        finally:
            try:
                from net_guard import set_path_redo as _set_zytos_redo
                _set_zytos_redo(True)
            except Exception:
                pass
            if shooting:
                _mouse_left_up()
            walk_stop.set()
            walk_thread.join(timeout=1.5)
            _inp.release_movement_keys()
            if getattr(b, "_KILLED", False):
                boss_end_reason = "stopped"
            elif getattr(b, "_STONE_LOST", False) and boss_end_reason not in {"killed", "death", "join_failed"}:
                boss_end_reason = "stone_lost"
            elif getattr(b, "_TEST_FORCE_FAILURE", False) and boss_end_reason not in {"killed", "death", "join_failed"}:
                boss_end_reason = "test_force_failure"
            b._dash_update(status="ZYTOS", goal="Finish", run_start_time=None)
            set_overlay(status="ZYTOS", goal="Finish", run_start_time=0)
            b._console_status("ZYTOS", "Finish")
            if boss_end_reason in {"killed", "death"} and boss_start:
                fight_duration = (kill_detected_at or time.time()) - boss_start
                try:
                    b._dash_record_zytos_run(fight_duration, boss_end_reason)
                    log.info(f"[ZYTOS] run recorded: {fight_duration:.1f}s ({boss_end_reason})")
                except Exception as e:
                    log.debug(f"[ZYTOS] timing record failed: {e}")

        if getattr(b, "_KILLED", False) or getattr(b, "_TEST_FORCE_FAILURE", False) or getattr(b, "_STONE_LOST", False):
            break
        if boss_end_reason in {"stone_lost", "test_force_failure"}:
            break
        if boss_end_reason == "join_failed":
            b._dash_update(status="ZYTOS", goal="Navigation", run_start_time=None)
            set_overlay(status="ZYTOS", goal="Navigation", run_start_time=0)
            continue
        if boss_end_reason == "killed":
            b._dash_update(status="ZYTOS", goal="Post Fight", run_start_time=None)
            set_overlay(status="ZYTOS", goal="Post Fight", run_start_time=0)
            b._console_status("ZYTOS", "Post Fight")
            # Walk to re-enter the fight right away - no extra settle wait.
            outcome = _reopen_menu_after_kill()
            if outcome == "death":
                log.info("[ZYTOS] late death after kill - waiting for respawn")
            elif outcome:
                menu_ready = True
                b._dash_update(status="ZYTOS", goal="Navigation", run_start_time=None)
                set_overlay(status="ZYTOS", goal="Navigation", run_start_time=0)
                continue
        b._dash_update(status="ZYTOS", goal="Finish", run_start_time=None)
        set_overlay(status="ZYTOS", goal="Finish", run_start_time=0)
        b._wait_polling(death_wait, "Zytos respawn", freeze=True)

    b._dash_update(run_active=False, run_start_time=None, waiting_for_start=True, status="WAITING", goal="Ready")
    set_overlay(status="WAITING", goal="Ready", run_start_time=0)
    stop_zytos_dodge()
    log.info("[ZYTOS] loop stopped")
