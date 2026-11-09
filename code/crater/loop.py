# ============================================================
# CRATER - MAIN LOOP
# Flow:
#   teleport_to_cosmic.macro → cosmic_to_crater.macro
#   → crater ESP/detection loop (HSV rock detection + timer-OCR validity check)
#   → on timer-loss (confidently no longer in crater): redo from teleport
#   → after 5 consecutive failures: if force_restart enabled,
#     run force_restart.macro; otherwise stop
#
# "Timer-loss" is decided by CraterTimerTracker (see timer_tracker.py) —
# it debounces single bad OCR reads so a transient miss never triggers a
# teleport retry while we're actually still in the crater (that would
# fully break positioning).
#
# ── SAFETY: Stone-icon detection + post-restart verification ──
# When the timer tracker fires "no longer in crater area", we also check
# the stone HUD icon (is_stone_icon_visible).  If the stone icon is gone
# we've been kicked from the game entirely (server death, disconnect),
# not just drifted out of the crater.  In that case we use the bot's full
# recovery path (_try_force_restart_after_failure + _do_menu_resume) which
# verifies the game actually reloaded — instead of blindly re-running
# navigation macros that would click around the main menu.
# Even in the "just left crater" case (stone icon still visible) we verify
# the game loaded after force_restart and fall back to menu_resume if not.
# A consecutive-restart counter (MAX_CONSECUTIVE_RESTARTS) stops the bot
# if recovery keeps failing, preventing infinite blind-click loops.
# ============================================================
import time
import threading

from logger import get_logger, cprint

# ── Background OCR workers (threaded to never block the detection loop) ──
# Sentinel for "no result yet" (distinct from None which means "OCR miss")
_TIMER_NO_RESULT = object()

_timer_ocr_active = False
_timer_ocr_result = None
_timer_ocr_ready = False
_timer_ocr_lock = threading.Lock()

_pet_ocr_active = False
_pet_ocr_latest = None
_pet_ocr_lock = threading.Lock()


def _crater_debug():
    """Check if crater debug logging is enabled."""
    try:
        import config as _cfg
        return bool(getattr(_cfg, "CRATER_DEBUG", True))
    except Exception:
        return True


def _start_timer_ocr():
    global _timer_ocr_active, _timer_ocr_result, _timer_ocr_ready
    with _timer_ocr_lock:
        if _timer_ocr_active:
            return
        _timer_ocr_active = True
        _timer_ocr_ready = False

    def _worker():
        global _timer_ocr_active, _timer_ocr_result, _timer_ocr_ready
        try:
            result = _read_crater_timer()
        except Exception:
            result = None
        finally:
            with _timer_ocr_lock:
                _timer_ocr_result = result
                _timer_ocr_ready = True
                _timer_ocr_active = False

    threading.Thread(target=_worker, daemon=True).start()


def _poll_timer_ocr():
    """Return the latest timer OCR result, or _TIMER_NO_RESULT if not ready.
    This distinguishes 'no result yet' from 'result is None (OCR miss)'."""
    global _timer_ocr_ready, _timer_ocr_result
    with _timer_ocr_lock:
        if not _timer_ocr_ready:
            return _TIMER_NO_RESULT
        r = _timer_ocr_result
        _timer_ocr_ready = False
    return r


def _start_pet_ocr():
    global _pet_ocr_active, _pet_ocr_latest
    with _pet_ocr_lock:
        if _pet_ocr_active:
            return
        _pet_ocr_active = True

    def _worker():
        global _pet_ocr_active, _pet_ocr_latest
        try:
            from screen import read_crater_pet_drop
            result = read_crater_pet_drop()
        except Exception:
            result = False
        finally:
            with _pet_ocr_lock:
                _pet_ocr_latest = result
                _pet_ocr_active = False

    threading.Thread(target=_worker, daemon=True).start()


def _poll_pet_ocr():
    global _pet_ocr_latest
    with _pet_ocr_lock:
        r = _pet_ocr_latest
        _pet_ocr_latest = None
    return r


from . import detector as _det
from . import input as _inp
from . import overlay as _esp
from .timer_tracker import CraterTimerTracker

log = get_logger()

_overlay_enabled = True
_force_restart_enabled = False
_failure_count = 0

# Crater stats — cumulative across sessions, persisted to crater_stats.json
_crater_total_elapsed = 0.0   # accumulated seconds from previous sessions
_crater_session_start = 0.0   # epoch when current session started
_crater_pet_drops = 0         # cumulative pet drops across all sessions

import json as _crater_json
import os as _crater_os

def _crater_stats_path():
    try:
        from config import DATA_DIR
        import os as _os
        return _os.path.join(DATA_DIR, "crater_stats.json")
    except Exception:
        return None

def _load_crater_stats():
    """Load cumulative crater stats from file."""
    global _crater_total_elapsed, _crater_pet_drops
    path = _crater_stats_path()
    if not path:
        return
    try:
        if _crater_os.path.exists(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                data = _crater_json.load(f)
            _crater_total_elapsed = float(data.get("total_elapsed_secs", 0.0) or 0.0)
            _crater_pet_drops = int(data.get("pet_drops", 0) or 0)
            log.info(f"Crater stats loaded: {_fmt_crater_elapsed()} elapsed, {_crater_pet_drops} pet drops")
    except Exception as e:
        log.debug(f"Crater stats load failed: {e}")

def _save_crater_stats():
    """Persist cumulative crater stats to file."""
    global _crater_total_elapsed, _crater_session_start
    # Add current session time to accumulated total
    if _crater_session_start > 0:
        _crater_total_elapsed += (time.time() - _crater_session_start)
        _crater_session_start = time.time()  # reset session clock so we don't double-count
    path = _crater_stats_path()
    if not path:
        return
    try:
        _crater_os.makedirs(_crater_os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _crater_json.dump({
                "total_elapsed_secs": _crater_total_elapsed,
                "pet_drops": _crater_pet_drops,
            }, f, indent=2)
        _crater_os.replace(tmp, path)
    except Exception as e:
        log.debug(f"Crater stats save failed: {e}")

def _crater_current_elapsed():
    """Total elapsed time: previous sessions + current session."""
    global _crater_session_start
    if _crater_session_start > 0:
        return _crater_total_elapsed + (time.time() - _crater_session_start)
    return _crater_total_elapsed

def _fmt_crater_elapsed():
    """Format elapsed seconds as 'Xh Ym' string."""
    secs = int(_crater_current_elapsed())
    h, m = divmod(secs // 60, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

_crater_last_dash_push = 0.0

def _push_crater_dash(force=False):
    """Update in-memory crater stats on dashboard (throttled to every 5s, no disk write)."""
    global _crater_last_dash_push
    now = time.time()
    if not force and (now - _crater_last_dash_push) < 5.0:
        return
    _crater_last_dash_push = now
    try:
        from dashboard import _lock, _state
        with _lock:
            _state["crater_elapsed_secs"] = _crater_current_elapsed()
            _state["crater_pet_drops"] = _crater_pet_drops
    except Exception:
        pass

# Safety: stop after this many consecutive force_restart cycles where the
# detection loop never had a successful timer read.  Prevents infinite
# blind-click loops if the game won't rejoin.


def reset_crater_stats():
    """Reset all cumulative crater stats to zero (called from dashboard)."""
    global _crater_total_elapsed, _crater_session_start, _crater_pet_drops
    _crater_total_elapsed = 0.0
    _crater_pet_drops = 0
    _crater_session_start = time.time()  # restart session clock
    _save_crater_stats()
    _push_crater_dash(force=True)
    log.info("Crater stats reset to zero")

MAX_CONSECUTIVE_RESTARTS = 5


def _get_cfg(key, default=None):
    try:
        import config as _cfg
        return getattr(_cfg, key, default)
    except Exception:
        return default


def _is_killed():
    """Check if the crater loop should stop — F9 kill OR test force failure."""
    try:
        import bot as _bot
        return _bot._KILLED or _bot._TEST_FORCE_FAILURE
    except Exception:
        return True

def _is_f9_killed():
    """Only checks F9 kill — NOT test force failure.
    Used after the detection loop so test fail falls through to force restart."""
    try:
        import bot as _bot
        return bool(_bot._KILLED)
    except Exception:
        return True

def _is_test_fail():
    """True if Down Arrow test-force-failure was triggered (not F9 kill)."""
    try:
        import bot as _bot
        return bool(_bot._TEST_FORCE_FAILURE) and not bool(_bot._KILLED)
    except Exception:
        return False

def _clear_test_fail():
    """Clear the test force failure flag so macros can run."""
    try:
        import bot as _bot
        _bot._TEST_FORCE_FAILURE = False
    except Exception:
        pass


def _set_overlay(status, goal="", **kw):
    try:
        from overlay import set_overlay
        set_overlay(status=status, goal=goal, **kw)
    except Exception:
        pass


def _dash(status, goal, **kw):
    try:
        from dashboard import update_state
        update_state(status=status, goal=goal, **kw)
    except Exception:
        pass


def _run_macro(name, wait=True):
    try:
        from macro_runner import run_macro
        return run_macro(name, wait=wait)
    except Exception as e:
        log.error(f"Crater: macro {name} failed: {e}")
        return None


def _read_crater_timer():
    try:
        from screen import read_crater_timer
        return read_crater_timer()
    except Exception:
        return None


def _timer_region_screen():
    """Absolute screen coords of the crater timer HUD region, for the ESP box."""
    try:
        import config as _cfg
        x1, y1, x2, y2 = _cfg.CRATER_TIMER_REGION
        return (x1, y1, x2, y2)
    except Exception:
        return None



# ── Recovery helpers (imported lazily from bot.py to avoid circular imports) ──

def _check_stone_icon():
    """Layer 1: Check if the stone HUD icon is visible.
    Returns True if visible (still in-game), False if not (kicked/menu).
    On error, returns True (optimistic — don't trigger false recovery)."""
    try:
        from screen import is_stone_icon_visible
        return is_stone_icon_visible()
    except Exception as e:
        log.debug(f"Crater: stone icon check failed ({e}), assuming in-game")
        return True


def _verify_game_loaded():
    """Layer 2: Verify the game actually loaded after a restart attempt.
    Uses the same in-game image template as force_restart.macro."""
    try:
        from bot import _stone_icon_visible_restart_image
        return _stone_icon_visible_restart_image()
    except Exception as e:
        log.debug(f"Crater: game-loaded verification failed ({e})")
        return True  # optimistic — don't block recovery on a check error


def _try_bot_recovery(reason):
    """Use bot.py's full recovery path: force_restart.macro + verification,
    then fall back to menu_resume (checks is_in_menu, clicks PLAY).
    Returns True if the game reloaded, False if all recovery failed."""
    try:
        from bot import _try_force_restart_after_failure, _do_menu_resume
    except Exception as e:
        log.error(f"Crater: cannot import recovery functions from bot.py: {e}")
        return False

    # Step 1: Try force_restart (runs macro + verifies via stone-icon image)
    recovered = _try_force_restart_after_failure(reason)
    if recovered:
        log.info("Crater: force_restart succeeded — game reloaded")
        return True

    # Step 2: force_restart failed verification — try menu_resume
    log.warning("Crater: force_restart verification failed — trying menu_resume")
    try:
        recovered = _do_menu_resume()
    except Exception as e:
        log.error(f"Crater: menu_resume failed: {e}")
        recovered = False

    if recovered:
        log.info("Crater: menu_resume succeeded — game reloaded")
        return True

    log.error("Crater: all recovery attempts failed")
    return False


def _pick_sticky(rocks, lock_min_area, last_cx, switch_ratio, now, last_switch, switch_cd):
    valid = [r for r in rocks if r["area"] >= lock_min_area]
    if not valid:
        return None, False
    if last_cx is None:
        return _det.pick_target(valid), False
    current = min(valid, key=lambda r: abs(r["screen_cx"] - last_cx))
    biggest = max(valid, key=lambda r: r["area"])
    if (biggest is not current
            and biggest["area"] > current["area"] * switch_ratio
            and (now - last_switch) >= switch_cd):
        return biggest, True
    return current, False



# Rock ID tracking — assigns stable IDs to detected rocks based on
# position proximity. IDs persist across frames so the ESP overlay can
# show consistent labels for each rock. (No counting — visual only.)
_rock_id_next = 1
_rock_id_map = []       # current frame: {"id", "cx", "cy"}
_ROCK_MATCH_DISTANCE = 60


def _set_rock_tracking_scale(scale_x: float, scale_y: float):
    """Scale rock matching distance to the live screen."""
    global _ROCK_MATCH_DISTANCE
    _ROCK_MATCH_DISTANCE = max(2, int(round(60 * max(scale_x, scale_y))))


def _assign_rock_ids(rocks):
    """Match detected rocks to previous frame's IDs by position proximity.
    Returns a list of IDs (one per rock) for ESP display."""
    global _rock_id_next, _rock_id_map

    if not rocks:
        _rock_id_map = []
        return []

    ids = []
    new_map = []
    used_prev = set()

    for r in rocks:
        cx = r.get("screen_cx", 0)
        cy = r.get("screen_cy", 0)

        best_dist = 999
        best_idx = -1
        for i, prev in enumerate(_rock_id_map):
            if i in used_prev:
                continue
            dist = abs(cx - prev["cx"]) + abs(cy - prev["cy"])
            if dist < best_dist and dist < _ROCK_MATCH_DISTANCE:
                best_dist = dist
                best_idx = i

        if best_idx >= 0:
            rid = _rock_id_map[best_idx]["id"]
            used_prev.add(best_idx)
        else:
            rid = _rock_id_next
            _rock_id_next += 1

        ids.append(rid)
        new_map.append({"id": rid, "cx": cx, "cy": cy})

    _rock_id_map = new_map
    return ids


def _detection_loop():
    """Main crater rock detection + targeting loop.
    Returns True if we exited because the bot was stopped/killed,
    False if we exited because the crater-timer tracker confirmed we've
    left the crater area (caller should redo the teleport chain)."""
    try:
        from net_guard import take_redo, set_path_redo
        if take_redo():
            log.warning("[NET] lag during crater travel — redo cosmic path")
            return True
        set_path_redo(False)
    except Exception:
        pass
    global _crater_pet_drops
    # The detector was calibrated at 1920x1080.  Keep its *field of view*
    # constant in game-space at any 16:9 resolution; otherwise 4K captures a
    # tiny centre slice and 720p captures too much.  Area and pixel-distance
    # thresholds must follow the same scale or small/large rocks are filtered
    # inconsistently.
    try:
        import config as _crater_cfg
        scale_x = float(getattr(_crater_cfg, "REGION_SCALE_X", 1.0) or 1.0)
        scale_y = float(getattr(_crater_cfg, "REGION_SCALE_Y", 1.0) or 1.0)
    except Exception:
        scale_x = scale_y = 1.0
    cap_w = max(1, int(round(_get_cfg("CRATER_CAPTURE_W", 500) * scale_x)))
    cap_h = max(1, int(round(_get_cfg("CRATER_CAPTURE_H", 350) * scale_y)))
    _set_rock_tracking_scale(scale_x, scale_y)
    hsv_low = [140, 80, 80]
    hsv_high = _get_cfg("CRATER_HSV_HIGH", [180, 255, 255])
    use_wrap = _get_cfg("CRATER_USE_HUE_WRAP", True)
    hsv_low2 = [0, 80, 80]
    hsv_high2 = _get_cfg("CRATER_HSV_HIGH2", [10, 255, 255])
    area_scale = max(0.01, scale_x * scale_y)
    min_area = max(1, int(round(800 * area_scale)))
    lock_min = max(1, int(round(3000 * area_scale)))
    smooth_x = _get_cfg("CRATER_AIM_SMOOTH_X", 0.55)
    deadzone = max(1, int(round(_get_cfg("CRATER_AIM_DEADZONE_X", 20) * scale_x)))
    search_spd = max(1, float(_get_cfg("CRATER_SEARCH_SPEED_PX_PER_MS", 10)) * scale_x)
    loss_cd = _get_cfg("CRATER_TARGET_LOSS_COOLDOWN_MS", 50) / 1000.0
    sw_ratio = _get_cfg("CRATER_TARGET_SWITCH_RATIO", 1.3)
    sw_cd = _get_cfg("CRATER_TARGET_SWITCH_COOLDOWN_MS", 2000) / 1000.0
    loop_ms = _get_cfg("CRATER_LOOP_SLEEP_MS", 10)
    loop_sleep = loop_ms / 1000.0
    startup = _get_cfg("CRATER_STARTUP_DELAY_MS", 1000) / 1000.0
    hit_binding = _get_cfg("CRATER_HIT_BINDING", "MOUSE_LEFT")
    # CRATER NEVER SPRINTS: the sprint key is never touched in crater mode
    # (sprinting overshoots the rock rows). Walk key only.
    walk_key = str(_get_cfg("FORWARD_BINDING", None) or _get_cfg("CRATER_WALK_KEY", "W") or "W")

    y_drift_deadzone = _get_cfg("CRATER_Y_DRIFT_DEADZONE_PX", 2)

    timer_check_ms = _get_cfg("CRATER_TIMER_CHECK_INTERVAL_MS", 1000)
    timer_miss_threshold = _get_cfg("CRATER_TIMER_MISS_THRESHOLD", 8)
    timer_reset_grace = _get_cfg("CRATER_TIMER_RESET_GRACE_SECONDS", 5)
    timer_box = _timer_region_screen()
    tracker = CraterTimerTracker(miss_threshold=timer_miss_threshold,
                                 reset_grace_seconds=timer_reset_grace)

    # Pet-drop detection (OCR "Received" scan with cooldown)
    pet_drop_cooldown = _get_cfg("CRATER_PET_DROP_COOLDOWN_MS", 15000) / 1000.0
    last_pet_drop_t = 0.0
    last_pet_drop_ocr_t = 0.0

    search_dx = max(1, int(search_spd * loop_ms))
    walk_vk = _inp.binding_to_vk(walk_key)
    last_cx = None
    last_switch_t = time.time()
    last_target_t = 0.0
    centered = False
    last_timer_check_t = 0.0
    lost_crater = False
    still_in_crater = True  # set True so first iteration doesn't NameError before timer check fires
    w_held = False

    def hold_w():
        nonlocal w_held
        if walk_vk is not None and not w_held:
            _inp.key_down(walk_vk)
            w_held = True

    def release_w():
        nonlocal w_held
        if walk_vk is not None and w_held:
            _inp.key_up(walk_vk)
            w_held = False

    # ── Hit spam ─────────────────────────────────────────────────────
    # ALWAYS spam the hit button (left mouse) while actively farming -
    # not just while a rock is targeted. A held button only registers
    # the initial press; rapid down/up cycles keep the pickaxe swinging
    # nonstop, even while rotating/searching between rocks.
    _hit_spam_on = threading.Event()
    _hit_spam_on.set()
    hit_gap_s = max(0.02, _get_cfg("CRATER_HIT_INTERVAL_MS", 100) / 1000.0)

    def _hit_spam_loop():
        while not _is_killed() and _hit_spam_on.is_set():
            _inp.hold_binding_down(hit_binding)
            time.sleep(0.04)
            _inp.release_binding(hit_binding)
            time.sleep(hit_gap_s)

    def stop_hit_spam():
        _hit_spam_on.clear()
        try:
            _inp.release_binding(hit_binding)
        except Exception:
            pass

    if startup > 0:
        _set_overlay("FARMING", "Crater Rocks")
        end = time.time() + startup
        while not _is_killed() and time.time() < end:
            _set_overlay("FARMING", "Crater Rocks")
            time.sleep(0.05)

    if _is_killed():
        release_w(); stop_hit_spam()
        return True

    _set_overlay("FARMING", "Crater Rocks")

    # Baseline Y for this navigate cycle -- captured fresh every time we
    # (re-)enter the detection loop, right after teleporting in. Nothing in
    # this loop is ever supposed to move Y (see input.py) -- so if the
    # cursor's Y ever drifts from this baseline it's external (game
    # recoil/camera-kick, OS mouse smoothing, etc.) and gets corrected
    # back every tick below, before it can accumulate into a visible shift.
    y_baseline = _inp.get_cursor_y()

    hit_spam_thread = threading.Thread(target=_hit_spam_loop, daemon=True, name="crater_hit_spam")
    hit_spam_thread.start()

    while not _is_killed():
        try:
            from net_guard import hold_if_needed
            if not hold_if_needed():
                break
        except Exception:
            pass
        try:
            _inp.correct_y_drift(y_baseline, y_drift_deadzone)
            img, cap_rect = _det.grab_capture(cap_w, cap_h)
            rocks, mask = _det.detect_rocks(img, hsv_low, hsv_high, use_wrap,
                                            hsv_low2, hsv_high2, min_area)
            rocks = _det.rocks_to_screen(rocks, cap_rect)
            now = time.time()

            target, did_switch = _pick_sticky(rocks, lock_min, last_cx,
                                              sw_ratio, now, last_switch_t, sw_cd)
            if did_switch:
                last_switch_t = now
                if _crater_debug():
                    log.debug(f"Crater: TARGET SWITCH to area={target['area']:.0f} cx={target['screen_cx']} (rocks={len(rocks)})")

            rock_boxes = [(r["screen_bx1"], r["screen_by1"],
                          r["screen_bx2"], r["screen_by2"]) for r in rocks]
            target_box = None
            scr_cx = (cap_rect[0] + cap_rect[2]) // 2

            if target is not None:
                target_box = (target["screen_bx1"], target["screen_by1"],
                             target["screen_bx2"], target["screen_by2"])
                dx = target["screen_cx"] - scr_cx
                hold_w()

                if abs(dx) > deadzone:
                    move_dx = int(dx * smooth_x)
                    if move_dx != 0:
                        # Smooth: break into tiny sub-steps of max 3px each
                        # with 1ms sleep between steps for fluid motion
                        remaining = move_dx
                        step_dir = 1 if move_dx > 0 else -1
                        while abs(remaining) >= 3:
                            _inp.mouse_move_rel(step_dir * 3, 0)
                            remaining -= step_dir * 3
                            time.sleep(0.001)
                        if remaining != 0:
                            _inp.mouse_move_rel(int(remaining), 0)
                    if _crater_debug():
                        log.debug(f"Crater: aiming dx={dx} area={target['area']:.0f} rocks={len(rocks)}")
                else:
                    # Target is centered (within deadzone) — just hit.
                    # NEVER call center_mouse_x here: it uses mouse_move_abs
                    # which JUMPS the cursor to an absolute position, causing
                    # the camera to snap back. Only relative moves are safe.
                    centered = True
                    _set_overlay("FARMING", "Crater Rocks")

                last_cx = target["screen_cx"]
                last_target_t = now
            else:
                centered = False
                if _crater_debug() and len(rocks) > 0:
                    log.debug(f"Crater: {len(rocks)} rocks detected but none >= lock_min_area={lock_min} (max area={max(r['area'] for r in rocks):.0f})")
                if (now - last_target_t) < loss_cd and last_cx is not None:
                    hold_w()
                    _set_overlay("FARMING", "Crater Rocks")
                else:
                    release_w()
                    # Cap rotation to avoid crazy spinning (max 100px/tick)
                    rot_dx = min(search_dx, 100)
                    # Smooth rotation: 3px sub-steps with 1ms delay
                    remaining = rot_dx
                    while remaining >= 3:
                        _inp.mouse_move_rel(3, 0)
                        remaining -= 3
                        time.sleep(0.001)
                    if remaining > 0:
                        _inp.mouse_move_rel(int(remaining), 0)
                    if _crater_debug():
                        log.debug(f"Crater: rotating right (dx={rot_dx}, no target for {now-last_target_t:.2f}s)")
                    _set_overlay("FARMING", "Crater Rocks")

            # ── Timer OCR (threaded — never blocks the loop) ─────────────
            # Start a background timer OCR read when interval hits.
            # Poll the result every iteration (~10ms).
            if (now - last_timer_check_t) * 1000.0 >= timer_check_ms:
                last_timer_check_t = now
                _start_timer_ocr()

            timer_result = _poll_timer_ocr()
            if timer_result is not _TIMER_NO_RESULT:
                # We got a result (int for success, None for miss) — feed to tracker
                still_in_crater = tracker.update(timer_result)
                if _crater_debug():
                    log.debug(f"Crater: timer OCR result={timer_result} in_crater={still_in_crater} bad_streak={tracker.consecutive_bad}")
                if timer_result is not None:
                    mm, ss = divmod(timer_result, 60)
                    _dash("RUNNING", f"Crater: farming (timer={mm}:{ss:02d})")

            # ── Pet drop OCR (threaded — never blocks the loop) ───────
            if (now - last_pet_drop_t) >= pet_drop_cooldown and (now - last_pet_drop_ocr_t) >= 3.0:
                last_pet_drop_ocr_t = now
                _start_pet_ocr()

            pet_hit = _poll_pet_ocr()
            if _crater_debug() and pet_hit is not None:
                log.debug(f"Crater: pet drop OCR result={pet_hit}")
            if pet_hit:
                last_pet_drop_t = now
                _crater_pet_drops += 1
                log.info(f"Crater: PET DROP #{_crater_pet_drops} detected!")
                _dash("RUNNING", f"Crater: PET DROP #{_crater_pet_drops}!")
                _save_crater_stats()
                _push_crater_dash(force=True)

            # Push updated stats (elapsed time) to dashboard every check
            _push_crater_dash()

            if _overlay_enabled and timer_box:
                if not still_in_crater:
                    tstate = "lost"
                elif tracker.consecutive_bad > 0:
                    tstate = "warn"
                else:
                    tstate = "ok"
                _esp.set_esp(timer_box=timer_box, timer_state=tstate)

            if not still_in_crater:
                # Grace period: scan every 0.25s for up to 6 seconds
                # before declaring failure. The timer might flicker
                # due to dust particles, dropped frames, or brief
                # obstructions. Only fail if it doesn't recover.
                grace_deadline = now + 6.0
                recovered = False
                log.warning(
                    f"Crater: timer OCR lost for {tracker.consecutive_bad} consecutive "
                    f"checks — starting 6s grace period (scan every 0.25s)")
                while not _is_killed() and time.time() < grace_deadline:
                    _set_overlay("FARMING", "Crater Rocks")
                    time.sleep(0.25)
                    if _is_killed():
                        break
                    grace_secs = _read_crater_timer()
                    if tracker.update(grace_secs):
                        recovered = True
                        log.info(f"Crater: timer recovered during grace period ({grace_secs}s)")
                        break
                if _is_killed():
                    break
                if recovered:
                    # Timer came back — resume detection loop normally
                    last_timer_check_t = time.time()
                    continue
                # Timer didn't recover within 6 seconds — actual failure
                try:
                    from screen import save_debug_fullscreen
                    save_debug_fullscreen("crater_timer_lost")
                except Exception as _dbg_e:
                    log.debug(f"Crater: timer-loss debug screenshot failed: {_dbg_e}")
                log.warning(
                    "Crater: timer not recovered after 6s grace period — "
                    "no longer in crater area")
                _set_overlay("LOST", "Crater: lost — retreating to retry")
                lost_crater = True
                break

            # Rock IDs are visual-only (ESP display)
            rock_ids = _assign_rock_ids(rocks)
            if _overlay_enabled:
                _esp.set_esp(cap_rect, rock_boxes, target_box, rock_ids=rock_ids)

            time.sleep(loop_sleep)
        except Exception as e:
            log.debug(f"Crater loop error: {e}")
            time.sleep(0.05)

    release_w(); stop_hit_spam()
    if _overlay_enabled:
        _esp.clear_esp()
    # If the loop broke because of Down Arrow (test force failure),
    # treat it as a crater failure so run_crater runs force_restart.
    if _is_test_fail():
        log.info("Crater: test force failure detected — treating as timer lost")
        lost_crater = True
    return not lost_crater


def run_crater():
    """Main entry point called from bot.py when crater mode is started."""
    global _overlay_enabled, _force_restart_enabled, _failure_count

    global _crater_session_start
    global _crater_pet_drops
    _failure_count = 0

    # Load cumulative stats from file, then start new session
    _load_crater_stats()
    _crater_session_start = time.time()
    log.info(f"Crater session started — cumulative: {_fmt_crater_elapsed()}, {_crater_pet_drops} pets")

    _push_crater_dash()

    try:
        from dashboard import get_state as _ds
        ds = _ds()
        _force_restart_enabled = bool(ds.get("force_restart", False))
        _overlay_enabled = bool(ds.get("crater_overlay", True))
    except Exception:
        _force_restart_enabled = False
        _overlay_enabled = True

    log.info(f"Crater mode: overlay={_overlay_enabled}, force_restart={_force_restart_enabled}")
    cprint("CRATER MODE | start", "ok")

    if _overlay_enabled:
        _esp.start_esp_overlay()
        time.sleep(0.5)

    try:
        while not _is_killed():
            try:
                from net_guard import hold_if_needed, take_redo
                if not hold_if_needed():
                    break
                if take_redo():
                    log.warning("[NET] lag — redo crater path (cosmic → crater)")
                    continue
            except Exception:
                pass
            _set_overlay("NAVIGATING", "Crater: teleport to cosmic...")
            _dash("RUNNING", "Crater: teleport to cosmic")
            log.info("Crater: F4 teleport to cosmic")
            try:
                from bot import _builtin_teleport_safe
                if not _builtin_teleport_safe("cosmic"):
                    log.warning("Crater: teleport to cosmic failed")
                    break
            except Exception as e:
                log.warning(f"Crater: teleport to cosmic failed: {e}")
                break
            if _is_killed(): break

            _set_overlay("NAVIGATING", "Crater: travelling to crater...")
            _dash("RUNNING", "Crater: travelling to crater")
            log.info("Crater: cosmic_to_crater.macro")
            _run_macro("cosmic_to_crater", wait=True)
            if _is_killed(): break

            _set_overlay("RUNNING", "Crater: detection active")
            _dash("RUNNING", "Crater: detection active")
            log.info("Crater: entering detection loop")
            still_running = _detection_loop()
            try:
                from net_guard import set_path_redo
                set_path_redo(True)
            except Exception:
                pass
            if _is_f9_killed(): break  # F9 stops everything; test fail → force restart

            if not still_running:
                # Timer lost (or test fail) — stop or force restart immediately.
                log.warning("Crater: timer lost — checking game state before recovery")

                # FULLY STOP the crater ESP overlay before doing anything else
                if _overlay_enabled:
                    try:
                        _esp.clear_esp()
                        _esp.stop_esp_overlay()
                    except Exception:
                        pass

                # ── Layer 1: Stone-icon detection ───────────────────────
                # Distinguish "left the crater area" (just re-teleport) from
                # "kicked from game / in main menu" (needs full recovery).
                # Other bot modes use the always-on stone watcher for this;
                # crater mode checks inline because it has its own loop.
                stone_visible = _check_stone_icon()
                kicked_from_game = not stone_visible

                if kicked_from_game:
                    log.warning(
                        "Crater: stone icon not visible — kicked from game "
                        "(server death / disconnect / in main menu)")
                else:
                    log.info("Crater: stone icon still visible — left crater area, still in-game")

                # Save debug screenshot before any recovery attempt
                try:
                    from screen import save_debug_fullscreen
                    save_debug_fullscreen(
                        "crater_kicked" if kicked_from_game else "crater_left_area")
                except Exception as e:
                    log.debug(f"Crater: pre-restart debug screenshot failed: {e}")

                # ── Consecutive restart counter (safety net) ───────────
                _failure_count += 1
                try:
                    from bot import _route_redo_limit
                    _max_fails = _route_redo_limit()
                except Exception:
                    _max_fails = 5
                if _failure_count > _max_fails:
                    log.error(
                        f"Crater: {_max_fails} consecutive restart cycles "
                        f"without successful detection — stopping to prevent blind clicking")
                    _clear_test_fail()
                    _set_overlay("STOPPED", "Crater: too many restart failures")
                    _dash("STOPPED", "Crater: too many restart failures")
                    try:
                        from screen import save_debug_fullscreen
                        save_debug_fullscreen("crater_max_restarts")
                    except Exception as e:
                        log.debug(f"Crater: max-restart debug screenshot failed: {e}")
                    break

                if _force_restart_enabled:
                    if kicked_from_game:
                        # ── Kicked from game: full recovery with verification ──
                        # Uses bot.py's _try_force_restart_after_failure which
                        # runs force_restart.macro AND verifies the game loaded
                        # via stone-icon image match.  If that fails, falls
                        # through to _do_menu_resume (checks is_in_menu, clicks
                        # PLAY, verifies).  If both fail → STOP (no blind clicks).
                        _set_overlay("RECOVERY", "Crater: kicked from game, recovering...")
                        _dash("RUNNING", "Crater: kicked from game, recovering")
                        _recovered = _try_bot_recovery("crater: kicked from game (stone icon gone)")

                        if not _recovered:
                            log.error(
                                "Crater: all recovery failed (force_restart + menu_resume) "
                                "— stopping to prevent blind clicking in main menu")
                            _clear_test_fail()
                            _set_overlay("STOPPED", "Crater: recovery failed")
                            _dash("STOPPED", "Crater: recovery failed")
                            try:
                                from screen import save_debug_fullscreen
                                save_debug_fullscreen("crater_recovery_failed")
                            except Exception as e:
                                log.debug(f"Crater: recovery-failed debug screenshot failed: {e}")
                            break

                        if _is_f9_killed(): break
                        _clear_test_fail()
                        log.info("Crater: recovery successful — re-navigating from top")

                    else:
                        # ── Just left crater area: force_restart + verify ──
                        # Stone icon is still visible so we're in-game but not
                        # in the crater.  Run force_restart and verify the game
                        # is still loaded afterwards.
                        log.info("Crater: left crater — lobby force restart")
                        _set_overlay("FORCE_RESTART", "Crater: force restart...")
                        _dash("RUNNING", "Crater: force restart")
                        _recovered = _try_bot_recovery("crater: left crater")
                        if _is_f9_killed(): break
                        _clear_test_fail()
                        if not _recovered:
                            log.error("Crater: recovery failed after leaving crater — stopping")
                            _set_overlay("STOPPED", "Crater: recovery failed")
                            _dash("STOPPED", "Crater: recovery failed")
                            break
                        log.info("Crater: recovery successful — re-navigating from top")
                        continue

                    # Restart ESP overlay for the next navigation+detection cycle
                    if _overlay_enabled:
                        try:
                            _esp.start_esp_overlay()
                            time.sleep(0.3)
                        except Exception:
                            pass
                    continue  # re-navigate from top
                else:
                    log.info("Crater: force_restart disabled — stopping")
                    _clear_test_fail()
                    _set_overlay("STOPPED", "Crater: timer lost, stopped")
                    _dash("STOPPED", "Crater: timer lost")
                    try:
                        from screen import save_debug_fullscreen
                        save_debug_fullscreen("crater_failure_stopped")
                    except Exception as e:
                        log.debug(f"Crater: failure debug screenshot failed: {e}")
                    break

            # Success: a full detection cycle completed - clear the
            # consecutive-failure streak so it only counts real failures.
            _failure_count = 0
            continue
    except Exception as _crater_e:
        log.error(f"Crater: unhandled error in run_crater: {_crater_e}")
    finally:
        try:
            from net_guard import set_path_redo
            set_path_redo(True)
        except Exception:
            pass
        # GUARANTEE: ESP overlay is always stopped, even on crash or F9
        if _overlay_enabled:
            try:
                _esp.stop_esp_overlay()
            except Exception:
                pass
        try:
            _esp.clear_esp()
        except Exception:
            pass

    # Save cumulative crater stats (keeps displaying on dashboard)
    _save_crater_stats()
    _crater_session_start = 0.0  # stop session clock
    _push_crater_dash()
    _set_overlay("WAITING", "Crater: stopped")
    _dash("WAITING", "Crater: stopped", waiting_for_start=True)
    cprint("CRATER MODE | stop", "warn")
