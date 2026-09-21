# ============================================================
# MT2 BOT - MAIN STATE MACHINE  (v19.0 Ã¢â‚¬â€ fixes: fast-tp fallback, glitch guard, OCR seed guard, manual-str icon crop, F-key before F4, orange-crop HUD guard, baserock auto-str peak-freeze)
# ============================================================
import time
import sys
import threading
import os
import ctypes
import keyboard   # pip install keyboard

# When this file is launched directly it runs as __main__. Dashboard routes later
# import "bot"; point that import at this live module instead of a shadow copy.
if __name__ == "__main__":
    sys.modules.setdefault("bot", sys.modules[__name__])

from logger        import get_logger, cprint
from config        import (
    STONE_STALL_TIMEOUT, SMART_FAILURE_TIMEOUT,
    REBIRTH_POST_CONFIRM_WAIT,
    STONE_FOR_A5_STAGE1, STONE_FOR_A5_STAGE2,
    STONE_FOR_A5_STAGE3, STONE_FOR_A5_STAGE4, STONE_FOR_METEOR,
    STONE_FOR_AREA6_SHORTCUT,
    STONE_FOR_A1_STAGE2, STONE_FOR_A1_STAGE3, STONE_FOR_A1_STAGE4,
    STONE_FOR_A2_STAGE1, STONE_FOR_A2_STAGE2, STONE_FOR_A2_STAGE3, STONE_FOR_A2_STAGE4,
    STONE_FOR_A3_STAGE1, STONE_FOR_A3_STAGE2, STONE_FOR_A3_STAGE3, STONE_FOR_A3_STAGE4,
    STONE_FOR_A4_STAGE1, STONE_FOR_A4_STAGE2, STONE_FOR_A4_STAGE3, STONE_FOR_A4_STAGE4,
    STAGE_TOPUP_SECONDS, TOPUP_TIMEOUT, BOT_HANDLES_AUTO_STRENGTH,
    MANUAL_STR_MAX_SECONDS, MANUAL_STR_NO_STRENGTH_TIMEOUT, MANUAL_STR_STRENGTH_POLL_SECONDS, MANUAL_STR_STRENGTH_MIN_REL_CHANGE,
    MANUAL_STR_POST_CLOSE_SETTLE_SECONDS, MANUAL_STR_POST_CLOSE_TOPUP_SECONDS,
    MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS,
    STONE_FOR_UNLOCK_DRILLS, ACTIVATE_DRILLS as _CFG_ACTIVATE_DRILLS,
    USE_DRILL_ON_A5_METEOR as _CFG_USE_DRILL_ON_A5_METEOR,
    USE_DRILL_ON_ROCK as _CFG_USE_DRILL_ON_ROCK,
    USE_DRILL_ON_BASEROCK as _CFG_USE_DRILL_ON_BASEROCK,
    AUTO_ROCK_MAX_GRIND_SECONDS,
    normalize_binding_name,
    BOSS_FIGHT_A1_BASEROCK_THRESHOLD,
    BOSS_FIGHT_A1_AMOUNT,
    BOSS_FIGHT_A1_METEOR_GRIND_SECONDS,
    BOSS_FIGHT_A1_LOADOUT_FIGHTING,
    BOSS_FIGHT_A1_LOADOUT_FARMING,

)
from macro_runner  import (
    run_macro, kill_macro_recorder, stop_macro, macro_exists,
    is_fortnite_focused, wait_for_fortnite_focus,
    enable_auto_strength, disable_auto_strength, trigger_binding_action, _binding_to_vk,
)
from screen        import (
    read_stone,
    read_manual_strength_stone, read_manual_strength_strength,
    rock_health_red_percent,
    rock_health_bar_seen,
    rock_health_bar_metrics,
    meteor_health_bar_metrics,
    meteor_health_bar_seen,
    is_auto_strength_active,
    is_in_menu, is_rebirth_screen, grab_region, get_menu_play_center, kraken_health_bar_seen, save_debug_fullscreen,
    read_bramble_mode_text, bramble_mode_matches,
)
from stats         import StatsTracker
from overlay       import start_overlay, set_overlay
# auth: login only, no suspension checks
from teleport_menu import (
    teleport as _builtin_teleport,
    set_killed_fn as _teleport_set_killed_fn,
    confirm_rebirth_ui as _confirm_rebirth_ui,
    wait_map_loaded as _wait_map_loaded,
    select_loadout as _select_loadout_ui,
)

from dashboard     import start_dashboard, update_state as _dash_update, record_delve_run as _dash_record_delve_run, record_kraken_run as _dash_record_kraken_run, record_zytos_run as _dash_record_zytos_run
from run_recorder  import get_recorder as _get_recorder
from kraken_dodge import stop_kraken_dodge
from zytos.dodge import stop_zytos_dodge


def stop_kraken_esp():
    """No-op. AI/ESP was removed from every mode."""
    return None


def _run_crater_loop():
    """Crater mode entry point."""
    try:
        from crater.loop import run_crater
        run_crater()
    except Exception as e:
        cprint(f"Crater mode error: {e}", "err")
        log.error(f"Crater mode error: {e}")
        import traceback
        traceback.print_exc()


def _run_farm_meteor_loop():
    """Meteor mode entry point."""
    try:
        from farm_meteor.loop import run_farm_meteor
        run_farm_meteor()
    except Exception as e:
        cprint(f"Meteor mode error: {e}", "err")
        log.error(f"Meteor mode error: {e}")
        import traceback
        traceback.print_exc()




log   = get_logger()
stats = StatsTracker()


def _fmt_stone(v) -> str:
    """Format stone with readable suffix (k/M/B/T/Qa/Qi/Sx/Sp/Oc/No/Dc...).
    Falls back to engineering notation for very large exponents (>57)."""
    if v is None:
        return "?"
    try:
        import math
        v = float(v)
        if v <= 0:
            return "0"
        exp = int(math.floor(math.log10(abs(v))))
        _SUFFIXES = [
            (3,  "k"),   (6,  "M"),    (9,  "B"),    (12, "T"),
            (15, "Qa"),  (18, "Qi"),   (21, "Sx"),   (24, "Sp"),
            (27, "Oc"),  (30, "No"),   (33, "Dc"),   (36, "UDc"),
            (39, "DDc"), (42, "TDc"),  (45, "QaDc"), (48, "QiDc"),
            (51, "SxDc"),(54, "SpDc"), (57, "OcDc"),
        ]
        chosen_suffix, chosen_exp = None, 0
        for _exp, _suf in _SUFFIXES:
            if exp >= _exp:
                chosen_suffix, chosen_exp = _suf, _exp
        if chosen_suffix and exp <= 59:
            mantissa = v / (10 ** chosen_exp)
            return f"{mantissa:.2f}{chosen_suffix}"
        if exp < 3:
            return f"{v:.2f}"
        # Engineering notation fallback (exp divisible by 3)
        eng_exp  = (exp // 3) * 3
        mantissa = v / (10 ** eng_exp)
        return f"{mantissa:.2f}e{eng_exp}"
    except Exception:
        return str(v)

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Stone freeze flag ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
_stone_frozen: bool = False
_stone_freeze_depth: int = 0

def _freeze_stone(frozen: bool):
    """Nestable freeze. True increments; False decrements.

    The stone watcher stays suppressed while depth > 0 so an inner nav
    macro / teleport cannot re-enable it during a covering parent phase
    (Bramble menu + arena, F4 teleports, etc.). Previously a boolean
    toggle meant fight_bramble_open.macro un-froze the watcher while the
    boss menu still covered the HUD, which fired Force Restart.
    """
    global _stone_frozen, _stone_freeze_depth
    if frozen:
        _stone_freeze_depth += 1
    else:
        _stone_freeze_depth = max(0, _stone_freeze_depth - 1)
    now_frozen = _stone_freeze_depth > 0
    if now_frozen == _stone_frozen:
        return
    _stone_frozen = now_frozen
    # Notify overlay so it doesn't need to import bot (avoids PyInstaller circular import)
    try:
        from overlay import set_overlay as _so
        _so(stone_frozen=now_frozen)
    except Exception:
        pass

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Navigation macros that cover the stone HUD ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â watcher suppressed during these ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# Hit macros (rock_hit, meteor_hit, baserock_hit) are intentionally NOT listed here;
# those are the long-running ones where we DO want the watcher active.
_NAV_MACROS: frozenset = frozenset({
    "base_to_a5_teleport",
    "base_to_a1_teleport",
    "base_to_a2_teleport",
    "base_to_a3_teleport",
    "base_to_a4_teleport",
    "base_to_meteor_shortcut_p1",
    "base_to_meteor_shortcut_p1_shortcut",
    "base_to_meteor_shortcut_p3",
    "area5_to_delve",
    "area7_to_kraken",
    "a8_to_zytos",
    "base_to_rebirth",
    "force_restart",
    "menu_resume",
    "base_to_baserock",
    "unlock_drills",
    "area5_to_meteor",
    "quest_menu",
    "hatch_pets",
    "break_1_star_rocks",
    "break_2_star_rocks",
    "break_3_star_rocks",
    "area1_to_meteor",
    "area1_to_bramble",
    "fight_bramble",
    "fight_bramble_open",
    "fight_bramble_join",
    "area1_to_stage1_rock",
    "area1_to_stage2_rock",
    "area1_to_stage3_rock",
    "area1_to_stage4_rock",
    "area2_to_stage1_rock",
    "area2_to_stage2_rock",
    "area2_to_stage3_rock",
    "area2_to_stage4_rock",
    "area3_to_stage1_rock",
    "area3_to_stage2_rock",
    "area3_to_stage3_rock",
    "area3_to_stage4_rock",
    "area4_to_stage1_rock",
    "area4_to_stage2_rock",
    "area4_to_stage3_rock",
    "area4_to_stage4_rock",
    "area5_to_stage1_rock",
    "area5_to_stage2_rock",
    "area5_to_stage3_rock",
    "area5_to_stage4_rock",
    "area6_to_node",
    "area6_to_meteor",
    "area7_to_meteor",
    "area8_to_meteor",
})

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ At-base tracking ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
_at_base: bool = False
_CURRENT_STAGE_POINT: tuple[int, int] | None = None
_LOADOUT_BLOCKED = False
_LOADOUT_BLOCK_SEQ = 0

def _mark_left_base():
    global _at_base
    _at_base = False
    _clear_current_stage_point("left base")


def _clear_current_stage_point(reason: str = ""):
    global _CURRENT_STAGE_POINT
    if _CURRENT_STAGE_POINT is not None and reason:
        log.debug(f"[SHORTCUT] clearing current rock position ({reason})")
    _CURRENT_STAGE_POINT = None


def _mark_current_stage_point(area: int, stage: int):
    global _CURRENT_STAGE_POINT
    _CURRENT_STAGE_POINT = (int(area), int(stage))
def _mark_area5_unlocked(reason: str = ""):
    """Remember that Area 5 has been reached, including shortcut-macro landings."""
    global _A5_UNLOCKED_THIS_RUN
    if not _A5_UNLOCKED_THIS_RUN:
        suffix = f" via {reason}" if reason else ""
        log.info(f"[A5] reached{suffix}; marking Area 5 unlocked for this run")
        try:
            _rec_log_action("area5_detected", source=reason or "unknown")
        except Exception:
            pass
    _A5_UNLOCKED_THIS_RUN = True
    _mark_left_base()


def _mark_area5_unlocked_if_visible(reason: str = "", attempts: int = 5, delay: float = 0.25) -> bool:
    """Pink-sky detection removed: assume success when caller reached Area 5 flow."""
    _mark_area5_unlocked(reason or "assumed")
    return True

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Hotkey / run state ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
_KILLED             = False   # F9 sets ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ bot soft-resets to fresh start
_TEST_FORCE_FAILURE = False   # Down Arrow simulates a non-user run failure for Force Restart testing
_WAITING_FOR_START  = True    # True until dashboard Start button is pressed
_DRILLS_UNLOCKED    = False   # reset each run; True after drills macro fires once
_A5_UNLOCKED_THIS_RUN = False # True after first manual baseÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢A5 teleport this run
_QUESTS_DONE_THIS_RUN = False  # reset each run; True once the quest phase ran
_QUESTS_STARTED_THIS_RUN = False  # True once quests were accepted at run start
_QUEST_PLAN = None  # run-start plan: quest panels/kinds for the end-of-run phase
_RUN_MODE           = "a1s1"  # explicit start point key, e.g. a1s1..a5s4 / a5meteor
_ACTIVATE_DRILLS    = _CFG_ACTIVATE_DRILLS  # press I before every hit macro ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â toggled via dashboard
# _suspended_flag removed — no suspension checks
_STONE_LOST         = False   # set by watcher thread when stone icon missing; cleared after recovery
_ACTIVE_HIT_MACRO   = None    # name of the hit macro (rock_hit/meteor_hit/baserock_hit) currently
                               # running via _run_hit_macro(wait=False); closed by _close_hit_macro().
_REBIRTH_IN_PROGRESS = False # suppress stone-lost/Menu Resume checks during rebirth flow
_menu_resume_fresh_start = False  # True after successful menu resume ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â forces run to start from base
_watcher_thread     = None    # background stone-icon watcher thread handle
_watcher_stop_ev    = None    # threading.Event to stop the watcher thread
_manual_strength_active = False
_active_manual_strength_handle = None
_last_live_stone = None
_last_f8_start_ts = 0.0
_f9_lock = threading.Lock()
_f9_in_progress = False
_last_f9_stop_ts = 0.0
_f9_started_ts = 0.0
_hotkey_f8_handle = None
_hotkey_f9_handle = None
_hotkey_test_fail_handle = None
_f9_poll_started = False
_win_hotkey_poll_started = False
_last_failure_ss_ts = 0.0
_last_status_line = None

# Guard against rare stale-stop states after hook/poller races.
_F9_STALE_TIMEOUT_SECONDS = 2.5


def _hotkey_binding_from_config(cfg_key: str, default: str) -> str:
    try:
        import config as _cfg_hotkey
        raw = getattr(_cfg_hotkey, cfg_key, default)
    except Exception:
        raw = default
    normalized = normalize_binding_name(str(raw or default))
    return normalized or normalize_binding_name(default)


def _hotkey_binding_to_keyboard_key(binding: str) -> str:
    b = normalize_binding_name(binding)
    if not b:
        return ""
    alias = {
        "ESC": "esc",
        "SPACE": "space",
        "TAB": "tab",
        "ENTER": "enter",
        "SHIFT": "shift",
        "CTRL": "ctrl",
        "ALT": "alt",
    }
    if b in alias:
        return alias[b]
    if b.startswith("MOUSE_"):
        # keyboard.is_pressed supports these names for our usage.
        return b.lower()
    return b.lower()


def _hotkey_binding_to_event_name(binding: str) -> str:
    key = _hotkey_binding_to_keyboard_key(binding)
    if not key:
        return ""
    return key.replace("_", " ")


def _start_binding() -> str:
    return _hotkey_binding_from_config("BOT_START_BINDING", "F8")


def _stop_binding() -> str:
    return _hotkey_binding_from_config("BOT_STOP_BINDING", "F9")


def _is_f9_stop_in_progress() -> bool:
    global _f9_in_progress, _f9_started_ts
    with _f9_lock:
        if _f9_in_progress and _f9_started_ts > 0:
            age = time.time() - float(_f9_started_ts)
            if age > float(_F9_STALE_TIMEOUT_SECONDS):
                log.warning(f"[F9] stale stop state detected ({age:.2f}s) - auto-clearing")
                _f9_in_progress = False
                _f9_started_ts = 0.0
        return bool(_f9_in_progress)

def _state_stone_snapshot():
    """Return the most recently read stone value (thread-safe read)."""
    global _last_live_stone
    return _last_live_stone

def _mark_rebirth_zero_confirmed(reason: str = ""):
    """Rebirth is the one moment where stone=0 is authoritative, not a glitch."""
    global _last_live_stone, _A5_UNLOCKED_THIS_RUN, _AREA_UNLOCKED_THIS_RUN, _DRILLS_UNLOCKED
    global _QUESTS_DONE_THIS_RUN, _QUESTS_STARTED_THIS_RUN, _QUEST_PLAN
    _last_live_stone = 0.0
    _A5_UNLOCKED_THIS_RUN = False
    _AREA_UNLOCKED_THIS_RUN = {1: False, 2: False, 3: False, 4: False, 5: False}
    _DRILLS_UNLOCKED = False
    _QUESTS_DONE_THIS_RUN = False
    _QUESTS_STARTED_THIS_RUN = False
    _QUEST_PLAN = None
    log.debug(f"Post-rebirth state reset: stone=0{f' ({reason})' if reason else ''}")
    try:
        _dash_update(cur_stone=0.0, stone=0.0)
    except Exception:
        pass

# Current farming stage Ã¢â‚¬â€ updated at each stage transition, read by recorder
_current_stage: str = "unknown"
_drill_binding_warned = False

def _set_stage(stage: str):
    """Update the current stage and notify recorder for per-frame annotations."""
    global _current_stage
    _current_stage = stage
    _dash_update(stage=stage)
    try:
        _get_recorder().log_stage(stage, stone=_last_live_stone)
    except Exception as _e:
        log.debug(f"[Recorder] log_stage error: {_e}")


def _rec_log_action(action_type: str, **fields):
    try:
        payload = {"type": action_type}
        payload.update(fields)
        _get_recorder().log_action(payload)
    except Exception as _e:
        log.debug(f"[Recorder] log_action error: {_e}")


def _rec_log_macro(name: str, event: str, **fields):
    try:
        _get_recorder().log_macro_event(name, event, **fields)
    except Exception as _e:
        log.debug(f"[Recorder] log_macro_event error: {_e}")


def _rec_set_failure(reason: str):
    try:
        _get_recorder().set_failure_reason(reason)
    except Exception as _e:
        log.debug(f"[Recorder] set_failure_reason error: {_e}")

def _capture_failure_fullscreen(reason: str):
    """Capture a full-screen failure frame (non-F9 diagnostics), throttled."""
    global _last_failure_ss_ts
    try:
        if _KILLED:
            return
        now = time.time()
        if (now - float(_last_failure_ss_ts)) < 1.0:
            return
        _last_failure_ss_ts = now
        from dashboard import get_state as _ds_get
        _mode = str(_ds_get().get("bot_mode", "rebirth")).lower()
        _stage = str(_current_stage or "unknown")
        _label = f"{_mode}_{_stage}_{reason}"
        path = save_debug_fullscreen(_label)
        if path:
            log.info(f"[FAILSHOT] saved: {path}")
    except Exception as _e:
        log.debug(f"[FAILSHOT] capture failed: {_e}")


def _trigger_drill_binding(stop_ev=None, check_active: bool = True) -> bool:
    global _drill_binding_warned
    if stop_ev is not None and stop_ev.is_set():
        return False
    if check_active:
        try:
            from screen import is_drill_active
            if is_drill_active():
                log.debug("[DRILLS] already active (cyan timer) — skip press")
                return True
        except Exception as e:
            log.debug(f"[DRILLS] active-check failed, pressing anyway: {e}")
    import config as _cfg_runtime
    binding = str(getattr(_cfg_runtime, "DRILL_ACTIVATE_BINDING", "I") or "").strip()
    auto_toggle = str(getattr(_cfg_runtime, "AUTO_STRENGTH_TOGGLE_BINDING", "MOUSE_MIDDLE") or "").strip()
    if binding.upper().replace("-", "_").replace(" ", "_") == auto_toggle.upper().replace("-", "_").replace(" ", "_"):
        binding = "I"
        if not _drill_binding_warned:
            log.warning("[DRILLS] drill binding matched auto-strength toggle; using default I for drill activation")
            _drill_binding_warned = True
    ok = trigger_binding_action(binding, hold_ms=30)
    used = binding
    if not ok:
        used = "I"
        ok = trigger_binding_action(used, hold_ms=30)
        if not _drill_binding_warned:
            log.warning(f"[DRILLS] invalid DRILL_ACTIVATE_BINDING={binding!r}; using fallback {used}")
            _drill_binding_warned = True
    if ok:
        _rec_log_action("drill_binding_press", binding=used, stage=_current_stage)
    return ok


def _auto_strength_enabled() -> bool:
    """Live dashboard setting: ON uses game auto-strength, OFF uses manual upgrades."""
    try:
        from dashboard import get_state as _ds
        return bool(_ds().get("auto_strength", BOT_HANDLES_AUTO_STRENGTH))
    except Exception:
        return bool(BOT_HANDLES_AUTO_STRENGTH)

def _manual_strength_enabled() -> bool:
    return not _auto_strength_enabled()


def _manual_str_detection() -> str:
    """Manual strength stop detection: "stone" (default) or "surge"."""
    try:
        import config as _cfg_det
        d = str(getattr(_cfg_det, "MANUAL_STR_DETECTION", "stone") or "stone").strip().lower()
        return d if d in ("stone", "surge") else "stone"
    except Exception:
        return "stone"


def _manual_surge_detection() -> bool:
    """Surge-level detection only works in bottom-row-only mode - the surge
    level is read from the bottom row display. Anywhere else (or with
    detection=stone), the bot uses the old stone detection."""
    if not _manual_strength_enabled():
        return False
    if _manual_str_detection() != "surge":
        return False
    try:
        import config as _cfg_det
        return bool(getattr(_cfg_det, "MANUAL_STR_ONLY_LAST_ROW", True))
    except Exception:
        return True


def _manual_surge_target() -> int:
    try:
        import config as _cfg_det
        return max(1, int(float(getattr(_cfg_det, "MANUAL_STR_SURGE_TARGET", 160) or 160)))
    except Exception:
        return 160


def _read_surge_level_live() -> int | None:
    """OCR the bottom-row surge level; None when unreadable/window closed."""
    try:
        from screen import read_manual_strength_surge
        return read_manual_strength_surge()
    except Exception as e:
        log.debug(f"[BASEROCK] surge OCR unavailable: {e}")
        return None


def _route_redo_limit() -> int:
    try:
        import config as _cfg_rr
        return max(1, int(getattr(_cfg_rr, "ROUTE_REDO_LIMIT", 5) or 5))
    except Exception:
        return 5


def _manual_hud_stall_seconds() -> float:
    try:
        import config as _cfg_ms
        return max(1.0, float(getattr(_cfg_ms, "MANUAL_STR_HUD_STALL_SECONDS", 5.0) or 5.0))
    except Exception:
        return 5.0


def _farm_env_bits() -> str:
    """One-line HUD/input snapshot for stall / force-restart logs."""
    bits: list[str] = []
    try:
        from macro_runner import is_fortnite_focused
        bits.append(f"focus={'ok' if is_fortnite_focused() else 'NO'}")
    except Exception:
        pass
    try:
        # click pacing in the stall dump — 0ms pacing eats every click and
        # looks exactly like a dead farm (Sep 17 09:27 baserock stall)
        import config as _cfg_pace
        bits.append(
            f"pace={int(getattr(_cfg_pace, 'MANUAL_STR_CLICK_DELAY_MS', 1))}/"
            f"{int(getattr(_cfg_pace, 'MANUAL_STR_CLICK_HOLD_MS', 1))}ms"
        )
    except Exception:
        pass
    try:
        bits.append(f"ingame={'yes' if _stone_icon_visible_restart_image() else 'NO'}")
    except Exception:
        pass
    try:
        from screen import _manual_strength_window_open
        bits.append(f"menu={'open' if _manual_strength_window_open() else 'closed'}")
    except Exception:
        pass
    try:
        import ctypes
        dpi = int(ctypes.windll.user32.GetDpiForSystem())
        bits.append(f"dpi={dpi} scale={round(dpi * 100 / 96)}%")
    except Exception:
        pass
    try:
        bits.append(f"stone={_fmt_stone(_last_live_stone) if _last_live_stone is not None else '?'}")
    except Exception:
        pass
    return "  ".join(bits) if bits else "-"

_STONE_LOW_GLITCH_RATIO = 0.10
_STONE_HIGH_GLITCH_RATIO = 1_000_000.0

def _stone_glitch_reason(
    v: float | None,
    reference: float | None,
    *,
    check_high: bool = True,
) -> str | None:
    """Return 'low', 'high', or None.

    check_high=False disables the upper-bound check.  Pass this when the
    reference is a *local* peak tracker (e.g. inside _do_base_rock) rather
    than the global _last_live_stone.  With auto-strength ON the stone can
    legitimately multiply by >1e6 per macro cycle, which would otherwise
    freeze the peak and block every subsequent real read as a 'high glitch'.
    The low-glitch check (catches OCR artefacts like "7") is always applied.
    """
    if v is None or reference is None or reference <= 0:
        return None
    if v < reference * _STONE_LOW_GLITCH_RATIO:
        return "low"
    # FIX 2: Only apply the HIGH glitch check when the reference value is
    # large enough to be meaningful (>= 1e6). At run start _last_live_stone
    # can be tiny (e.g. 7.12M from the previous run tail) causing every real
    # mid-run value like 78e156 to look like a 1e148x spike and get rejected.
    # FIX 5 (baserock auto-str peak freeze): check_high=False bypasses this
    # for local peak trackers where legitimate >1e6x growth is possible.
    if check_high and reference >= 1e6 and v > reference * _STONE_HIGH_GLITCH_RATIO:
        return "high"
    return None


def _make_manual_strength_watchdog(label: str):
    timeout_s = max(0.0, float(MANUAL_STR_NO_STRENGTH_TIMEOUT))
    if timeout_s <= 0:
        return None
    return {
        "label": label,
        "timeout_s": timeout_s,
        "poll_s": max(0.12, float(MANUAL_STR_STRENGTH_POLL_SECONDS)),
        "min_rel": max(0.0, float(MANUAL_STR_STRENGTH_MIN_REL_CHANGE)),
        "next_poll": 0.0,
        "last_val": None,
        "last_change_at": time.time(),
        "seen_valid": False,
        "pending_stall_since": 0.0,
        "recent_activity_grace_s": max(2.0, min(timeout_s * 0.35, 10.0)),
        "stall_confirm_s": max(1.5, min(timeout_s * 0.20, 6.0)),
    }


def _manual_strength_watchdog_stalled(
    state,
    *,
    recent_activity_at: float | None = None,
) -> bool:
    if not state:
        return False
    if not (_manual_strength_enabled() and _manual_strength_active):
        return False

    now = time.time()
    if now >= float(state["next_poll"]):
        state["next_poll"] = now + float(state["poll_s"])
        sval = read_manual_strength_strength()
        if sval is not None:
            ref = state["last_val"]
            glitch_reason = _stone_glitch_reason(sval, ref)
            if glitch_reason:
                log.debug(
                    f"[{state['label']}] manual strength OCR {glitch_reason} glitch ignored: "
                    f"{_fmt_stone(sval)} (last={_fmt_stone(ref)})"
                )
            else:
                if ref is None:
                    state["last_val"] = sval
                    state["last_change_at"] = now
                    state["seen_valid"] = True
                    state["pending_stall_since"] = 0.0
                    log.debug(f"[{state['label']}] manual strength baseline: {_fmt_stone(sval)}")
                else:
                    threshold = ref * (1.0 + float(state["min_rel"]))
                    if sval >= threshold:
                        state["last_val"] = sval
                        state["last_change_at"] = now
                        state["pending_stall_since"] = 0.0
                        log.debug(f"[{state['label']}] manual strength progress: {_fmt_stone(sval)}")
                    elif sval > ref:
                        # Keep monotonic best read without resetting the stall timer.
                        state["last_val"] = sval

    if bool(state["seen_valid"]):
        stalled_for = now - float(state["last_change_at"])
        if stalled_for >= float(state["timeout_s"]):
            if recent_activity_at is not None:
                recent_age = now - float(recent_activity_at)
                if recent_age <= float(state.get("recent_activity_grace_s", 5.0)):
                    state["last_change_at"] = now
                    state["pending_stall_since"] = 0.0
                    log.debug(
                        f"[{state['label']}] suppressing strength-timeout ({stalled_for:.1f}s) "
                        f"due to recent farming activity {recent_age:.1f}s ago"
                    )
                    return False

            pending_since = float(state.get("pending_stall_since") or 0.0)
            if pending_since <= 0.0:
                state["pending_stall_since"] = now
                log.warning(
                    f"[{state['label']}] possible manual strength stall after {stalled_for:.1f}s; "
                    f"confirming for {float(state.get('stall_confirm_s', 4.0)):.1f}s"
                )
                return False
            if (now - pending_since) < float(state.get("stall_confirm_s", 4.0)):
                return False

            log.warning(
                f"[{state['label']}] no manual strength change for {stalled_for:.1f}s "
                f"(timeout {state['timeout_s']:.1f}s) - re-navigate needed"
            )
            return True
    else:
        state["pending_stall_since"] = 0.0
    return False

def _read_stone_live(
    *,
    update_last: bool = True,
    allow_stale: bool = False,
    check_glitch: bool = True,
) -> float | None:
    """Read stone from HUD normally, or from the strength menu while it is open."""
    global _last_live_stone
    def _accept(v: float | None, source: str) -> float | None:
        global _last_live_stone
        if v is None:
            return None
        if check_glitch:
            reason = _stone_glitch_reason(v, _last_live_stone)
            if reason:
                log.debug(f"{source} OCR rejected as {reason} glitch: {_fmt_stone(v)} (last={_fmt_stone(_last_live_stone)})")
                return None
        if update_last:
            _last_live_stone = v
        return v

    if _manual_strength_active:
        manual_window_open = True
        try:
            from manual_strength import is_window_open as _manual_window_open_fn
            manual_window_open = bool(_manual_window_open_fn())
        except Exception:
            manual_window_open = True
        if manual_window_open:
            v = read_manual_strength_stone()
            accepted = _accept(v, "[MANUAL_STR] menu stone")
            if accepted is not None:
                return accepted
        else:
            log.debug("[MANUAL_STR] menu OCR skipped: strength window not visible")

    accepted = _accept(read_stone(), "HUD stone")
    if accepted is not None:
        return accepted

    if allow_stale and _manual_strength_active and _last_live_stone is not None:
        return _last_live_stone
    return None

def _read_stone_checked(
    label: str,
    *,
    attempts: int = 6,
    delay: float = 0.18,
    min_reads: int = 2,
    min_expected: float | None = None,
    fallback_to_last_if_plausible: bool = False,
) -> float | None:
    """Read several fresh OCR samples and return a conservative median value."""
    global _last_live_stone
    values: list[float] = []
    reference = _last_live_stone
    attempts = max(1, int(attempts))
    for attempt in range(attempts):
        if _KILLED or _STONE_LOST:
            log.debug(f"{label}: aborted checked read due to stop signal")
            break
        v = _read_stone_live(update_last=False, check_glitch=False)
        if v is not None:
            values.append(v)
        if attempt < attempts - 1:
            if _KILLED or _STONE_LOST:
                break
            time.sleep(max(0.0, delay))

    if not values:
        log.debug(f"{label}: OCR checked 0/{attempts} valid reads")
        return None

    # FIX 3: Filter out glitch values relative to the known-good reference.
    # OCR artifacts like "153" (parsed as 153.0) are 10^100+ below real stone
    # values and will be caught by _stone_glitch_reason as "low" glitch.
    # Only filter if we have a meaningful reference (>= 1e6) so early-run
    # reads aren't discarded when _last_live_stone is still tiny/None.
    if reference is not None and reference >= 1e6:
        clean = [v for v in values if _stone_glitch_reason(v, reference) is None]
        if clean:
            if len(clean) < len(values):
                log.debug(f"{label}: filtered {len(values)-len(clean)} glitch value(s) from checked read")
            values = clean
        else:
            threshold_hits = []
            if min_expected is not None:
                threshold_hits = [v for v in values if v >= min_expected]
            if len(threshold_hits) >= max(2, min_reads):
                log.debug(
                    f"{label}: all samples differ from last trusted stone, "
                    f"but {len(threshold_hits)} meet expected threshold"
                )
                values = threshold_hits
            elif fallback_to_last_if_plausible and min_expected is not None and reference >= min_expected:
                log.debug(
                    f"{label}: all {len(values)} OCR sample(s) rejected as glitches; "
                    f"keeping trusted {_fmt_stone(reference)}"
                )
                return reference
            else:
                log.debug(
                    f"{label}: all {len(values)} OCR sample(s) rejected as glitches "
                    f"against trusted {_fmt_stone(reference)}"
                )
                return None
    # else: keep all values (no trustworthy reference yet)

    ordered = sorted(values)
    chosen = ordered[(len(ordered) - 1) // 2]
    if min_expected is not None:
        threshold_hits = [v for v in ordered if v >= min_expected]
        if len(threshold_hits) >= max(2, min_reads):
            chosen = min(threshold_hits)
            log.debug(
                f"{label}: using threshold-confirmed OCR cluster "
                f"{_fmt_stone(chosen)}+ ({len(threshold_hits)} hits, need {_fmt_stone(min_expected)})"
            )
            _last_live_stone = chosen
            return chosen

    if len(ordered) >= max(2, min_reads):
        high = ordered[-1]
        high_cluster = [v for v in ordered if high > 0 and v >= high * 0.75]
        if len(high_cluster) >= max(2, min_reads):
            chosen = min(high_cluster)
            log.debug(
                f"{label}: using high-confidence OCR cluster "
                f"{_fmt_stone(chosen)}-{_fmt_stone(high)}"
            )
    _last_live_stone = chosen
    if len(values) < min_reads:
        log.debug(f"{label}: OCR only {len(values)}/{attempts} valid read(s); using {_fmt_stone(chosen)}")
    else:
        log.debug(
            f"{label}: OCR checked {len(values)}/{attempts}; "
            f"using {_fmt_stone(chosen)} (range {_fmt_stone(ordered[0])}-{_fmt_stone(ordered[-1])})"
        )
    return chosen

def _confirm_stone_at_least(
    threshold: float,
    label: str,
    *,
    first_value: float | None = None,
    attempts: int = 6,
    required_hits: int = 4, #2
    delay: float = 0.15,
) -> tuple[bool, float | None]:
    """Require multiple fresh OCR samples at/above a threshold before acting."""
    values: list[float] = []
    if first_value is not None:
        values.append(first_value)

    attempts = max(1, int(attempts))
    remaining = attempts - (1 if first_value is not None else 0)
    for _ in range(max(0, remaining)):
        time.sleep(max(0.0, delay))
        v = _read_stone_live(update_last=False, check_glitch=False)
        if v is not None:
            values.append(v)
        hits = [x for x in values if x >= threshold]
        if len(hits) >= required_hits:
            confirmed = max(hits)
            log.debug(
                f"{label}: OCR threshold confirmed with {len(hits)} hits "
                f"(stone={_fmt_stone(confirmed)}, need {_fmt_stone(threshold)})"
            )
            return True, confirmed

    hits = [x for x in values if x >= threshold]
    below = [x for x in values if x < threshold]
    fallback = max(below) if below else None
    log.debug(
        f"{label}: OCR threshold not confirmed "
        f"({len(hits)}/{required_hits} hits, need {_fmt_stone(threshold)})"
    )
    return False, fallback

def _disable_auto_strength_for_manual(reason: str = ""): ##?
    """Manual-strength mode must not touch the in-game auto-strength toggle."""
    if _auto_strength_enabled():
        return
    try:
        set_overlay(auto_str=None, show_auto_str=False)
    except Exception:
        pass

def _start_manual_strength_live(
    reason: str,
    activity_callback=None,
):
    """Open the manual strength window right away and buy until stopped.

    No pre-open stone checks — the buying loop's own HUD stall watchdog
    (MANUAL_STR_HUD_STALL_SECONDS, ~5s) already detects a dead grind, and
    every skipped OCR read is ~0.5-1s less standing around.
    """
    global _manual_strength_active, _active_manual_strength_handle
    if _KILLED or _STONE_LOST:
        return None
    if not _manual_strength_enabled():
        return None
    try:
        from manual_strength import start_manual_strength_loop
        _disable_auto_strength_for_manual(reason)
        set_overlay(show_auto_str=False, manual_position=True)
        _manual_strength_active = True
        handle = start_manual_strength_loop(
            reason=reason,
            min_hit_seconds=0.0,
            max_hit_wait_seconds=0.0,
            wait_for_hit_fn=None,
            stop_fn=lambda: _KILLED or _STONE_LOST,
            activity_callback=activity_callback,
        )
        if handle is None:
            _manual_strength_active = False
            set_overlay(manual_position=False)
            return None
        _active_manual_strength_handle = handle
        _rec_log_action("manual_strength_flow", phase="start")
        return handle
    except Exception as e:
        _manual_strength_active = False
        _active_manual_strength_handle = None
        set_overlay(manual_position=False)
        log.warning(f"[MANUAL_STR] {reason}: live loop failed to start: {e}")
        return None

def _stop_manual_strength_live(handle):
    global _manual_strength_active, _active_manual_strength_handle
    _rec_log_action("manual_strength_flow", phase="end")
    closed_ok = True
    if handle is None:
        if _active_manual_strength_handle is None:
            _manual_strength_active = False
            set_overlay(manual_position=False)
            if _manual_strength_enabled():
                try:
                    from manual_strength import close_window_verified
                    closed_ok = bool(close_window_verified(attempts=8))
                except Exception as e:
                    log.debug(f"[MANUAL_STR] verified close without handle failed: {e}")
                    closed_ok = False
        return closed_ok
    try:
        if not handle.stop():
            log.warning("[MANUAL_STR] live loop did not stop before timeout")
            closed_ok = False
    except Exception as e:
        log.warning(f"[MANUAL_STR] live loop stop failed: {e}")
        closed_ok = False
    finally:
        try:
            from manual_strength import close_window_verified
            if not close_window_verified(attempts=8):
                log.warning("[MANUAL_STR] window may still be open after stop")
                closed_ok = False
        except Exception as e:
            log.debug(f"[MANUAL_STR] verified close after stop failed: {e}")
            closed_ok = False
        if _active_manual_strength_handle is handle:
            _active_manual_strength_handle = None
        _manual_strength_active = False
        set_overlay(manual_position=False)
    return closed_ok

def _stop_active_manual_strength_for_action(reason: str):
    """Close the manual strength window before navigation/action macros take over."""
    handle = _active_manual_strength_handle
    if handle is None:
        closed_ok = True
        try:
            from manual_strength import close_window_verified
            closed_ok = bool(close_window_verified(attempts=8))
        except Exception as e:
            log.debug(f"[MANUAL_STR] verified close before {reason} failed: {e}")
            closed_ok = False
        set_overlay(manual_position=False)
        if not closed_ok:
            log.warning(f"[MANUAL_STR] strength window still open before {reason}; blocking action")
            return closed_ok
        _equip_pickaxe(f"after {reason}")
        return True
    log.info(f"[MANUAL_STR] stopping active manual strength before {reason}")
    closed_ok = _stop_manual_strength_live(handle)
    if not closed_ok:
        log.warning(f"[MANUAL_STR] strength window still open before {reason}; blocking action")
        return closed_ok
    _equip_pickaxe(f"after {reason}")
    return True

def _manual_post_threshold_topup(label: str, target: float, confirmed_cur: float | None, hit_macro: str) -> float:
    """Manual strength already proves the live threshold; do not run extra topup."""
    global _last_live_stone
    trusted = confirmed_cur if confirmed_cur is not None and confirmed_cur >= target else target
    _last_live_stone = max(_last_live_stone or 0, trusted)
    log.debug(f"[{label}] manual threshold trusted at {_fmt_stone(trusted)}; post-threshold topup skipped")
    _last_live_stone = trusted
    set_overlay(stone=trusted)
    _dash_update(cur_stone=trusted)
    return trusted

def _maybe_unlock_drills():
    """Fire unlock_drills macro once per run when stone threshold is met."""
    global _DRILLS_UNLOCKED, _last_live_stone
    from dashboard import get_state as _ds
    _ds_snap = _ds()
    if not _ds_snap.get("unlock_drills", True) or _DRILLS_UNLOCKED:
        return False
    cur = _read_stone_live(update_last=False, check_glitch=False)
    _unlock_threshold = _ds_snap.get("stone_for_unlock_drills", STONE_FOR_UNLOCK_DRILLS)
    if cur is None or cur < _unlock_threshold:
        return False
    _unlock_confirmed, _confirmed_cur = _confirm_stone_at_least(
        _unlock_threshold,
        "[DRILLS] unlock threshold",
        first_value=cur,
        attempts=5,
        required_hits=2,
        delay=0.12,
    )
    if not _unlock_confirmed:
        return False
    cur = _confirmed_cur or cur
    _last_live_stone = cur

    log.info(f"[DRILLS] Stone {cur:.2e} >= threshold {_unlock_threshold:.2e} ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â unlocking drills")
    _stop_active_manual_strength_for_action("unlock drills")
    _stop_drill_loop()
    stop_macro()

    if _auto_strength_enabled():
        disable_auto_strength()
        set_overlay(auto_str=False)

    # Only teleport to base if not already there ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â avoids a redundant round trip
    # when _maybe_unlock_drills is called right after _do_base_rock's initial teleport.
    if not _at_base:
        _console_status("ACTION", "Base")
        if not _teleport_to_base():
            log.warning("[DRILLS] could not reach base for drill unlock")
            return False
    else:
        log.debug("[DRILLS] Already at base ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â skipping pre-drill teleport")

    _DRILLS_UNLOCKED = True
    _mark_left_base()
    _console_status("ACTION", "Unlocking drills")
    # _run_macro auto-freezes watcher for unlock_drills (it's in _NAV_MACROS)
    _rec_log_macro("unlock_drills", "start")
    _drills_proc = run_macro("unlock_drills", wait=False)
    if _drills_proc is None:
        log.error("[DRILLS] unlock_drills macro failed to start")
        _rec_log_macro("unlock_drills", "error", error="macro_start_failed")
        _rec_set_failure("macro_start_failed:unlock_drills")
        return False
    _drills_deadline = time.time() + 300
    while _drills_proc.poll() is None:
        if time.time() > _drills_deadline:
            log.warning("[DRILLS] unlock_drills macro exceeded 5-minute timeout ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â killing and continuing")
            stop_macro()
            _rec_log_macro("unlock_drills", "error", error="macro_timeout")
            _rec_set_failure("macro_timeout:unlock_drills")
            break
        time.sleep(0.5)
    _drills_rc = _drills_proc.poll()
    if _drills_rc in (0, None):
        _rec_log_macro("unlock_drills", "end", return_code=0 if _drills_rc is None else _drills_rc)
    else:
        _rec_log_macro("unlock_drills", "error", return_code=_drills_rc, error="macro_return_nonzero")
        _rec_set_failure(f"macro_return_nonzero:unlock_drills:{_drills_rc}")
    log.info("[DRILLS] unlock_drills macro finished")

    _console_status("ACTION", "Base")
    if not _teleport_to_base():
        log.warning("[DRILLS] unlock finished, but base return was not confirmed")
        return False

    if _auto_strength_enabled():
        enable_auto_strength()
        set_overlay(auto_str=True)

    log.info("[DRILLS] Drill unlock done ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â back at base, resuming farming")
    _console_status("FARMING", "Base Rock")
    return True



def hard_quit():
    """Dashboard Quit button ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stop macros, save stats, kill the process."""
    global _KILLED, _watcher_stop_ev, _watcher_thread
    _KILLED = True
    try: stop_macro()
    except Exception: pass
    try: _stop_drill_loop()
    except Exception: pass
    try:
        stats.save()
    except Exception: pass
    import os, sys
    os._exit(0)

def _on_f9():
    """F9 = immediate hard kill. Stops EVERYTHING: macros, dodge/esp threads,
    drill loop, auto/manual strength, mouse, and all keyboard keys.
    The overlay and dashboard are updated immediately."""
    global _KILLED, _WAITING_FOR_START, _active_manual_strength_handle, _manual_strength_active, _f9_in_progress, _last_f9_stop_ts, _f9_started_ts
    _now = time.time()
    with _f9_lock:
        if (_now - float(_last_f9_stop_ts)) < 0.20:
            _KILLED = True
            _WAITING_FOR_START = True
            return
        _last_f9_stop_ts = _now
        if _f9_in_progress:
            _KILLED = True
            _WAITING_FOR_START = True
            return
        _f9_in_progress = True
        _f9_started_ts = _now
    _KILLED = True
    _WAITING_FOR_START = True
    cprint("Hotkey F9 | IMMEDIATE STOP - press Start to run again", "warn")
    log.info("Hotkey F9: immediate kill triggered")

    try:
        # 1. Stop macro runner (sets stop event + releases _HELD_KEYS via SendInput)
        try:
            import macro_runner as _mr
            if getattr(_mr, "_active_stop_event", None) is not None:
                _mr._active_stop_event.set()
        except Exception:
            pass
        try:
            stop_macro()
        except Exception:
            pass

        # 2. Stop drill loop
        try:
            _stop_drill_loop()
        except Exception:
            pass

        # 3. Stop watcher and bot workers
        try:
            _stop_stone_watcher()
        except Exception:
            pass
        try:
            stop_kraken_esp()
        except Exception:
            pass
        try:
            # Non-blocking on hotkey thread: direct stop signal, no join wait here.
            stop_kraken_dodge(wait=False, timeout=0.0)
        except Exception:
            pass
        try:
            stop_zytos_dodge(wait=False, timeout=0.0)
        except Exception:
            pass

        # Stop crater ESP overlay (transparent window with boxes/timer)
        try:
            from crater.overlay import stop_esp_overlay as _stop_crater_esp
            _stop_crater_esp()
        except Exception:
            pass
        # 4. Stop auto-strength + signal manual strength stop (non-blocking).
        try:
            disable_auto_strength()
        except Exception:
            pass
        try:
            _h = _active_manual_strength_handle
            if _h is not None:
                _sev = getattr(_h, "_stop_event", None)
                if _sev is not None:
                    _sev.set()
            _active_manual_strength_handle = None
            _manual_strength_active = False
            set_overlay(manual_position=False)
        except Exception:
            pass

        # 5. Release mouse (left button held during kraken/delve shoot loop)
        try:
            from macro_runner import _mouse_left_up
            _mouse_left_up()
        except Exception:
            pass

        try:
            kill_macro_recorder()
        except Exception:
            pass

        # 6. Release all keyboard keys that could be held
        # Via keyboard lib (covers keyboard.press("w") used in kraken reward walk)
        _release_names = ["w", "a", "s", "d", "e", "space", "shift", "ctrl", "lshift", "lctrl", "f", "1", "2"]
        try:
            from macro_runner import live_wasd, binding_to_keyboard_name
            import config as _cfg_rel
            for _letter, (_name, _vk) in live_wasd().items():
                if _name:
                    _release_names.append(_name)
            for _ck, _df in (
                ("SPRINT_BINDING", "SHIFT"),
                ("CROUCH_BINDING", "CTRL"),
                ("JUMP_BINDING", "SPACE"),
                ("WEAPON_1_BINDING", "1"),
                ("MONITOR_ITEM_BINDING", "2"),
                ("PICKAXE_EQUIP_BINDING", "F"),
            ):
                _release_names.append(binding_to_keyboard_name(getattr(_cfg_rel, _ck, _df), _df))
        except Exception:
            pass
        for _key in dict.fromkeys(_release_names):
            try:
                keyboard.release(_key)
            except Exception:
                pass
        # Via SendInput VK codes (covers macro _key_down calls)
        try:
            import macro_runner as _mr2
            for _vk in _mr2._HELD_KEYS:
                try:
                    _mr2._key_up(_vk)
                except Exception:
                    pass
        except Exception:
            pass

        # 7. Update overlay and dashboard immediately
        if _auto_strength_enabled():
            set_overlay(status="STOPPED", goal="Press Start to begin", show_auto_str=True, run_start_time=0)
        else:
            set_overlay(status="STOPPED", goal="Press Start to begin", auto_str=None, show_auto_str=False, run_start_time=0)
        from dashboard import update_state as _du
        _du(
            status="STOPPED",
            goal="Press Start to begin",
            waiting_for_start=True,
            run_active=False,
            run_start_time=None,
        )
    finally:
        with _f9_lock:
            _f9_in_progress = False
            _f9_started_ts = 0.0

def _on_f9_hotkey():
    """Dispatch F9 stop on a worker thread so keyboard hook thread never blocks."""
    if not _run_panel_active():
        return
    try:
        threading.Thread(target=_on_f9, daemon=True, name="hotkey-f9-stop").start()
    except Exception:
        # Last-chance fallback: run inline if thread creation fails.
        _on_f9()

def _on_test_force_failure():
    """Down Arrow = test-only non-user failure, so Force Restart can be verified live."""
    global _TEST_FORCE_FAILURE, _active_manual_strength_handle, _manual_strength_active
    if _TEST_FORCE_FAILURE:
        return
    _TEST_FORCE_FAILURE = True
    cprint("Hotkey Down | simulated run failure for Force Restart test", "warn")
    log.warning("[TEST_FAIL] Down Arrow requested a simulated non-user run failure")
    try:
        stop_macro()
    except Exception:
        pass
    try:
        _stop_drill_loop()
    except Exception:
        pass
    try:
        from macro_runner import _mouse_left_up as _tf_mouse_up
        _tf_mouse_up()
    except Exception:
        pass
    try:
        stop_kraken_dodge(wait=False, timeout=0.0)
    except Exception:
        pass
    try:
        stop_zytos_dodge(wait=False, timeout=0.0)
    except Exception:
        pass
    try:
        _h = _active_manual_strength_handle
        if _h is not None:
            _sev = getattr(_h, "_stop_event", None)
            if _sev is not None:
                _sev.set()
        _active_manual_strength_handle = None
        _manual_strength_active = False
        set_overlay(manual_position=False)
    except Exception:
        pass
    try:
        _rec_set_failure("test_force_restart_hotkey")
    except Exception:
        pass
    set_overlay(status="TEST FAIL", goal="Force Restart test")
    try:
        _dash_update(status="TEST FAIL", goal="Force Restart test")
    except Exception:
        pass

def _on_test_force_failure_hotkey():
    try:
        threading.Thread(target=_on_test_force_failure, daemon=True, name="hotkey-test-force-failure").start()
    except Exception:
        _on_test_force_failure()

def _on_f8_start():
    """F8 = same start signal as the dashboard Start button, guarded against ghost starts."""
    global _WAITING_FOR_START, _last_f8_start_ts, _KILLED, _STONE_LOST, _TEST_FORCE_FAILURE

    now = time.time()
    if now - _last_f8_start_ts < 0.75:
        return
    _last_f8_start_ts = now

    if _is_f9_stop_in_progress():
        log.info("Hotkey F8 ignored: F9 stop still in progress")
        return

    try:
        from dashboard import get_state as _dash_get_state
        state = _dash_get_state()
    except Exception as e:
        log.warning(f"Hotkey F8 ignored: dashboard state unavailable: {e}")
        return



    if not bool(state.get("waiting_for_start", True)):
        log.info("Hotkey start ignored: bot already running")
        return

    missing = missing_required_loadouts()
    if missing:
        _block_for_missing_loadouts(missing)
        cprint("Hotkey F8  |  loadouts not set", "warn")
        log.info("Hotkey F8 ignored: loadouts not set")
        return

    if missing_game_detection():
        _block_for_missing_game_detection()
        cprint("Hotkey F8  |  in-game image detection not set", "warn")
        log.info("Hotkey F8 ignored: Force Restart needs In-Game image detection")
        return

    # Force start state from hotkey even if dashboard flags are slightly stale.
    _KILLED = False
    _STONE_LOST = False
    _TEST_FORCE_FAILURE = False
    _WAITING_FOR_START = False
    run_start_time = time.time()
    if _auto_strength_enabled():
        set_overlay(status="STARTING", goal="Initialising...", show_auto_str=True, run_start_time=run_start_time)
    else:
        set_overlay(status="STARTING", goal="Initialising...", auto_str=None, show_auto_str=False, run_start_time=run_start_time)
    _dash_update(
        waiting_for_start=False,
        status="STARTING",
        goal="Initialising...",
        run_active=True,
        run_start_time=run_start_time,
        run_steps=0,
        run_errors=0,
        run_quests_completed=0,
    )
    cprint("Hotkey F8  |  start", "ok")
    log.info("Hotkey F8: start triggered")

def _run_panel_active() -> bool:
    """Start/stop hotkeys only while the Run tab is the active panel."""
    try:
        from dashboard import get_state
        snap = get_state() or {}
        if str(snap.get("active_app_tab") or "run") != "run":
            return False
        if snap.get("recorder_busy"):
            return False
    except Exception:
        pass
    return True


def _on_f8_hotkey():
    """Dispatch F8 start on a worker thread to avoid hook callback stalls."""
    if not _run_panel_active():
        return
    try:
        threading.Thread(target=_on_f8_start, daemon=True, name="hotkey-f8-start").start()
    except Exception:
        _on_f8_start()


_FORCE_RESTART_STONE_ICON_IMAGE = {
    "var": "inGame",
    "path": "images/1920x1080_inGame.png",
    "threshold": 90,
    "fixed": False,
    "base_w": 1920,
    "base_h": 1080,
    "x1": 1667,
    "y1": 663,
    "x2": 1703,
    "y2": 721,
    "search_x1": 0,
    "search_y1": 0,
    "search_x2": 1920,
    "search_y2": 1080,
    "result_mode": "bool",
    "x_var": "image_found_x",
    "y_var": "image_found_y",
}


def _stone_icon_visible_restart_image() -> bool:
    """In-game HUD verification for force restart / menu resume / crater.

    Primary: Game Detection — the user-picked always-visible HUD image
    (Force Restart tab), compared against the live region with a mean
    image-difference check (default 5% max difference counts as in game).
    Fallback when nothing is picked: the legacy fixed 90% template check
    (images/1920x1080_inGame.png), same as force_restart.macro used.
    """
    try:
        from game_detect import game_detect_result
        res = game_detect_result()
        if res.get("set"):
            ok = res.get("ok")
            if ok is not None:
                _diff = res.get("diff")
                log.debug(
                    f"[GAME_DETECT] diff={_diff:.2f}% thresh={res.get('threshold')}% ok={ok}"
                )
                return bool(ok)
            log.warning("[GAME_DETECT] check could not run (capture/template) — falling back")
    except Exception as _e:
        log.debug(f"[GAME_DETECT] result failed: {_e}")
    try:
        from macro_logic import image_match_result
        bot_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        macro_dir = os.path.join(bot_root, "macros", "rebirth_mode")
        result = image_match_result(_FORCE_RESTART_STONE_ICON_IMAGE, bot_root, macro_dir)
        score = float(result.get("score", 0.0) or 0.0)
        matched = bool(result.get("matched"))
        log.debug(f"[STONE_ICON_IMAGE] force-restart template score={score:.1%} matched={matched}")
        return matched
    except Exception as e:
        log.warning(f"[STONE_ICON_IMAGE] check failed: {e}")
        return False


def _in_game_ready_for_macros() -> bool:
    """True only in a real match. The inGame template alone can match a
    loading screen, so this is the full check: the user-picked in-game
    HUD image when set, else the legacy inGame template."""
    try:
        return bool(_stone_icon_visible_restart_image())
    except Exception as e:
        log.warning(f"[MENU_RESUME] in-game check failed: {e}")
        return False


def _do_menu_resume(debug: bool = False) -> bool:
    """Attempt to resume the game from the Fortnite main menu.

    Flow:
      1. Wait 250 ms ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â confirm PLAY button visible (bail if not in menu)
      2. Wait 500 ms for UI to settle
      3. Click PLAY
      4. Wait MENU_RESUME_JOIN_WAIT s for game to load
      5. Check stone icon ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ return True / False

    Just confirm menu and hit PLAY.

    Returns True if a new game was started, False otherwise.
    """
    if _in_game_ready_for_macros():
        log.info("[MENU_RESUME] already in-game (stone icon); no resume needed")
        return True

    log.info("[MENU_RESUME] detect Ready → shard")
    _console_status("MENU RESUME", "Waiting Ready")
    set_overlay(status="MENU RESUME", goal="Waiting Ready")
    try:
        from lobby import menu_resume as _lobby_resume
        ok = bool(_lobby_resume())
    except Exception as e:
        log.warning(f"[MENU_RESUME] failed: {e}")
        ok = False
    if ok:
        log.info("[MENU_RESUME] Ready + shard OK")
        return True
    log.warning("[MENU_RESUME] Ready/shard failed — stopping")
    return False

    if macro_exists("menu_resume"):
        log.info("[MENU_RESUME] Running menu_resume.macro")
        _console_status("MENU RESUME", "Running macro")
        set_overlay(status="MENU RESUME", goal="Running macro")
        if not _run_macro("menu_resume"):
            log.warning("[MENU_RESUME] menu_resume.macro failed")
            return False
        if _stone_icon_visible_restart_image():
            log.info("[MENU_RESUME] menu_resume.macro completed and in-game image matched")
            return True
        log.warning("[MENU_RESUME] menu_resume.macro finished but in-game image was not detected")
        return False

    from macro_runner import _mouse_move_abs, _mouse_left_click

    log.info("[MENU_RESUME] Starting menu resume procedure")
    _console_status("MENU RESUME", "...")

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Step 1: brief wait then confirm menu ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    time.sleep(0.12)
    if not is_in_menu():
        log.warning("[MENU_RESUME] PLAY button not detected ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â aborting menu resume")
        _console_status("MENU RESUME", "Not in menu")
        return False
    log.info("[MENU_RESUME] Menu confirmed (PLAY button visible)")
    _console_status("MENU RESUME", "Pressing Play...")

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Step 2: let UI settle then click PLAY ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    time.sleep(0.25)
    import config as _cfg_mr
    play_cx, play_cy = get_menu_play_center()
    _mouse_move_abs(play_cx, play_cy)
    time.sleep(0.05)
    _mouse_left_click()
    log.info(f"[MENU_RESUME] Clicked PLAY at ({play_cx}, {play_cy})")
    join_wait = _cfg_mr.MENU_RESUME_JOIN_WAIT
    _console_status("MENU RESUME", "...")

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Step 3: wait for new game to start ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    _join_deadline = time.time() + float(join_wait)
    while time.time() < _join_deadline and not _KILLED:
        if _stone_icon_visible_restart_image():
            break
        _wait_polling(0.25, "...", freeze=True)

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Step 4: check stone icon ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    if _stone_icon_visible_restart_image():
        log.info("[MENU_RESUME] Stone icon visible ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â new game started successfully!")
        _console_status("MENU RESUME", "Resuming...")
        if debug:
            cprint("[MENU_RESUME] Complete ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stone icon visible, game started!", "ok")
        return True
    else:
        log.warning(f"[MENU_RESUME] Stone icon still not visible after {join_wait} s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â menu resume failed")
        _console_status("MENU RESUME", "Stopping...")
        if debug:
            cprint(f"[MENU_RESUME] Stone icon NOT visible after {join_wait} s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â resume failed", "warn")
        return False


def _soft_reset_state():
    """Reset all per-run globals. Called at the start of each outer loop iteration."""
    global _KILLED, _WAITING_FOR_START, _A5_UNLOCKED_THIS_RUN, _AREA_UNLOCKED_THIS_RUN, _at_base, _DRILLS_UNLOCKED, _STONE_LOST, _TEST_FORCE_FAILURE, _last_live_stone
    try:
        _stop_active_manual_strength_for_action("soft reset")
    except Exception:
        pass
    _KILLED = False
    _STONE_LOST = False
    _TEST_FORCE_FAILURE = False
    _WAITING_FOR_START = True
    _A5_UNLOCKED_THIS_RUN = False
    _AREA_UNLOCKED_THIS_RUN = {1: False, 2: False, 3: False, 4: False, 5: False}
    _at_base = False
    _DRILLS_UNLOCKED = False
    _last_live_stone = None

def _register_hotkeys():
    """Register start/stop hotkeys. Called on every soft-reset so they survive game focus loss.
    Uses both add_hotkey (high-level) AND a low-level hook so at least one always fires."""
    global _hotkey_f8_handle, _hotkey_f9_handle, _hotkey_test_fail_handle
    start_binding = _start_binding()
    stop_binding = _stop_binding()
    start_key = _hotkey_binding_to_keyboard_key(start_binding)
    stop_key = _hotkey_binding_to_keyboard_key(stop_binding)
    try:
        if _hotkey_f8_handle is not None:
            keyboard.remove_hotkey(_hotkey_f8_handle)
    except Exception:
        pass
    try:
        if _hotkey_f9_handle is not None:
            keyboard.remove_hotkey(_hotkey_f9_handle)
    except Exception:
        pass
    try:
        if _hotkey_test_fail_handle is not None:
            keyboard.remove_hotkey(_hotkey_test_fail_handle)
    except Exception:
        pass
    _hotkey_f8_handle = keyboard.add_hotkey(start_key, _on_f8_hotkey, suppress=False)
    _hotkey_f9_handle = keyboard.add_hotkey(stop_key, _on_f9_hotkey, suppress=False)
    _hotkey_test_fail_handle = keyboard.add_hotkey("down", _on_test_force_failure_hotkey, suppress=False)
    log.debug(f"Hotkeys registered: {start_binding}=start, {stop_binding}=soft-reset, Down=test failure")

# Low-level keyboard hook â€” survives game window focus steal
def _low_level_key_hook(event):
    """Fires on every key event. Intercept configured start/stop keys regardless of focus."""
    try:
        if event.event_type != "down":
            return
        key_name = str(event.name or "").lower().strip()
        start_name = _hotkey_binding_to_event_name(_start_binding())
        stop_name = _hotkey_binding_to_event_name(_stop_binding())
        if key_name == start_name:
            _on_f8_hotkey()
        elif key_name == stop_name:
            _on_f9_hotkey()
        elif key_name in ("down", "arrow down"):
            _on_test_force_failure_hotkey()
    except Exception:
        pass

_ll_hook_registered = False
def _ensure_low_level_hook():
    global _ll_hook_registered
    if not _ll_hook_registered:
        try:
            keyboard.hook(_low_level_key_hook, suppress=False)
            _ll_hook_registered = True
            log.debug("Low-level F8/F9 hook registered")
        except Exception as e:
            log.warning(f"Low-level hook failed: {e}")

def _ensure_hotkey_poll_failsafe():
    """Extra safety: detect configured start/stop keys via polling if keyboard hooks get flaky."""
    global _f9_poll_started
    if _f9_poll_started:
        return

    def _poll():
        last_start_down = False
        last_stop_down = False
        last_test_down = False
        while True:
            start_key = _hotkey_binding_to_keyboard_key(_start_binding())
            stop_key = _hotkey_binding_to_keyboard_key(_stop_binding())
            try:
                start_down = bool(start_key and keyboard.is_pressed(start_key))
            except Exception:
                start_down = False
            if start_down and not last_start_down:
                _on_f8_hotkey()
            last_start_down = start_down

            try:
                stop_down = bool(stop_key and keyboard.is_pressed(stop_key))
            except Exception:
                stop_down = False
            if stop_down and not last_stop_down:
                _on_f9_hotkey()
            last_stop_down = stop_down
            try:
                test_down = bool(keyboard.is_pressed("down"))
            except Exception:
                test_down = False
            if test_down and not last_test_down:
                _on_test_force_failure_hotkey()
            last_test_down = test_down
            time.sleep(0.03)

    try:
        threading.Thread(target=_poll, daemon=True, name="hotkey-failsafe-poll").start()
        _f9_poll_started = True
        log.debug("Start/Stop failsafe poller started")
    except Exception as e:
        log.warning(f"Start/Stop failsafe poller failed: {e}")


def _ensure_win_hotkey_poll_failsafe():
    """OS-level fallback (independent from keyboard lib hooks/is_pressed)."""
    global _win_hotkey_poll_started
    if _win_hotkey_poll_started:
        return

    def _poll_vk():
        try:
            _user32 = ctypes.windll.user32
        except Exception as e:
            log.warning(f"WinVK Start/Stop poller init failed: {e}")
            return

        last_start = False
        last_stop = False
        last_test = False
        while True:
            start_vk = _binding_to_vk(_start_binding())
            stop_vk = _binding_to_vk(_stop_binding())
            test_vk = _binding_to_vk("DOWN") or 0x28
            try:
                start_down = bool(start_vk is not None and (_user32.GetAsyncKeyState(start_vk) & 0x8000))
            except Exception:
                start_down = False
            if start_down and not last_start:
                _on_f8_hotkey()
            last_start = start_down

            try:
                stop_down = bool(stop_vk is not None and (_user32.GetAsyncKeyState(stop_vk) & 0x8000))
            except Exception:
                stop_down = False
            if stop_down and not last_stop:
                _on_f9_hotkey()
            last_stop = stop_down
            try:
                test_down = bool(test_vk is not None and (_user32.GetAsyncKeyState(test_vk) & 0x8000))
            except Exception:
                test_down = False
            if test_down and not last_test:
                _on_test_force_failure_hotkey()
            last_test = test_down
            time.sleep(0.02)

    try:
        threading.Thread(target=_poll_vk, daemon=True, name="hotkey-winvk-poll").start()
        _win_hotkey_poll_started = True
        log.debug("WinVK Start/Stop poller started")
    except Exception as e:
        log.warning(f"WinVK Start/Stop poller failed: {e}")


def _wait_for_start():
    """Block until dashboard Start button is pressed."""
    global _WAITING_FOR_START
    if not _WAITING_FOR_START:
        return
    log.debug("Waiting for dashboard Start button...")
    if _auto_strength_enabled():
        set_overlay(status="WAITING", goal="Ready", show_auto_str=True)
    else:
        set_overlay(status="WAITING", goal="Ready", auto_str=None, show_auto_str=False)
    _dash_update(status="WAITING", goal="Ready", waiting_for_start=True)
    while _WAITING_FOR_START and not _KILLED:
        from dashboard import get_state as _ds
        if not _ds()["waiting_for_start"]:
            _WAITING_FOR_START = False
            break
        time.sleep(0.1)
    log.debug("Start button pressed — beginning run loop")
    try:
        from macro_runner import log_input_environment, _boost_playback_timing
        _boost_playback_timing()
        log_input_environment()
    except Exception as e:
        log.debug(f"[INPUT] environment dump failed: {e}")


def _run_macro(name: str):
    """Run a named macro. Raises nothing on kill ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â bot checks _KILLED after return.

    Navigation macros (those in _NAV_MACROS) briefly cover the stone HUD, so the
    watcher is paused for their duration and resumed immediately after.  Hit macros
    are NOT in _NAV_MACROS, so the watcher stays active during long farming loops.
    """
    if _KILLED or _STONE_LOST or _TEST_FORCE_FAILURE:
        return False

    _is_nav = (
        name in _NAV_MACROS
        or name.endswith("_shortcut")
        or name.startswith("select_loadout_")
    )
    if _is_nav:
        _freeze_stone(True)   # suppress watcher for this nav macro
        log.debug(f"[WATCHER] paused for nav macro: {name}")

    _rec_log_macro(name, "start")
    handle = run_macro(name, wait=False)
    if handle is None:
        log.error(f"Required macro failed to start: {name}")
        _console_status("ERROR", f"Macro failed: {name}")
        _rec_log_macro(name, "error", error="macro_start_failed")
        _rec_set_failure(f"macro_start_failed:{name}")
        if _is_nav:
            _freeze_stone(False)
        return False

    while handle.poll() is None:
        if _KILLED or _TEST_FORCE_FAILURE:
            stop_macro()
            _rec_log_macro(name, "error", error="macro_killed" if _KILLED else "test_force_failure")
            if _is_nav:
                _freeze_stone(False)
            return False
        try:
            from net_guard import hold_if_needed, peek_redo
            if not hold_if_needed():
                stop_macro()
                if _is_nav:
                    _freeze_stone(False)
                return False
            if peek_redo():
                stop_macro()
                _rec_log_macro(name, "error", error="net_pause_redo")
                if _is_nav:
                    _freeze_stone(False)
                    log.debug(f"[WATCHER] resumed after nav macro: {name}")
                return False
        except Exception:
            pass
        time.sleep(0.005)

    rc = handle.poll()
    if rc not in (0, None):
        _rec_log_macro(name, "error", return_code=rc, error="macro_return_nonzero")
        _rec_set_failure(f"macro_return_nonzero:{name}:{rc}")
        if _is_nav:
            _freeze_stone(False)
            log.debug(f"[WATCHER] resumed after nav macro: {name}")
        return False
    _rec_log_macro(name, "end", return_code=0)

    if _is_nav:
        _freeze_stone(False)
        log.debug(f"[WATCHER] resumed after nav macro: {name}")
    _map_area = {
        "base_to_a5_teleport": "area5",
        "base_to_meteor_shortcut_p1": "area6",
        "base_to_meteor_shortcut_p1_shortcut": "area6",
        "base_to_area6": "area6",
    }.get(name)
    if _map_area:
        # Best-effort settle after the walk. Never fail the nav on a miss —
        # F4 A5 is the real unlock check; dest missing redos P1 from base.
        _wait_map_loaded(_map_area)
    return True
    # Macro finished ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â check if a pause arrived at the exact finish moment


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Console status printer ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _overlay_goal_text(goal: str) -> str:
    text = str(goal or "")
    low = text.lower()
    if "topup" not in low:
        return text
    if "base" in low or "baserock" in low:
        return "Base Rock"
    import re
    area_stage = re.search(r"\b(a\d+s\d+)\b", text, re.IGNORECASE)
    if area_stage:
        return f"{area_stage.group(1).upper()} Rock"
    stage = re.search(r"\bstage\s+(\d+)\b", text, re.IGNORECASE)
    if stage:
        return f"Stage {stage.group(1)} Rock"
    if "rock" in low:
        return text[:low.find("topup")].rstrip(" -\u2013\u2014").strip() or text
    return text


def _console_status(status: str, goal: str, stone=None, next_steps: str = ""):
    _auto_mode = _auto_strength_enabled()
    _astr_active = is_auto_strength_active() if _auto_mode else None
    _focused     = is_fortnite_focused()
    stone_str = _fmt_stone(stone)
    astr      = ("on" if _astr_active else "off") if _auto_mode else "manual"
    focused   = "ok" if _focused else "UNFOCUSED"
    level     = "warn" if not _focused else "info"
    line = f"[{status}] {goal} | stone={stone_str} | str={astr} | focus={focused}"
    if next_steps:
        line += f" | next={next_steps}"
    global _last_status_line
    if line != _last_status_line:
        _last_status_line = line
        cprint(line, level)
    set_overlay(status=status, goal=_overlay_goal_text(goal), next_steps=next_steps, show_auto_str=_auto_mode)
    if stone is not None:
        set_overlay(stone=stone)


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Polling wait helper ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _wait_polling(seconds: float, goal: str, freeze: bool = True):
    """Sleep for `seconds` in short ticks, updating overlay & checking pause/kill."""
    overlay_goal = _overlay_goal_text(goal)
    deadline = time.time() + seconds
    if freeze:
        _freeze_stone(True)
    while deadline is None or time.time() < deadline:
        if _KILLED or _TEST_FORCE_FAILURE or (_STONE_LOST and not freeze):
            break
        remaining = max(0.0, deadline - time.time())
        set_overlay(goal=overlay_goal)
        try:
            from net_guard import hold_if_needed
            if not hold_if_needed():
                break
        except Exception:
            pass
        time.sleep(min(0.1, remaining))
    if freeze:
        _freeze_stone(False)
    set_overlay(goal=overlay_goal)


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Stone icon watcher (always-on background thread) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _start_stone_watcher():
    """Start the background thread that checks stone icon every 1 s.

    Five consecutive misses (5 s) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ triggers _stone_lost_handler() which:
      - stops macros immediately
      - stops drill loop
      - sets _STONE_LOST = True  (interrupts all run loops via _check_alive)
      - updates overlay / dashboard

    The thread is suppressed during phases where stone icon is expected to
    be hidden: while _stone_frozen is True (rebirth animation, menu resume
    join-wait, etc.).  Callers must set _stone_frozen before those phases.
    """
    global _watcher_thread, _watcher_stop_ev, _STONE_LOST
    _stop_stone_watcher()   # kill any previous instance
    _STONE_LOST = False
    _watcher_stop_ev = threading.Event()

    def _watcher_loop(stop_ev: threading.Event):
        miss_count = 0
        while not stop_ev.wait(0.5):   # fires every 0.5s
            if stop_ev.is_set():
                break
            # Ã¢â€â‚¬Ã¢â€â‚¬ Feed recorder one frame per second (= ~30 game frames) Ã¢â€â‚¬Ã¢â€â‚¬
            try:
                _rec = _get_recorder()
                if _rec.is_active():
                    from dashboard import get_state as _ds_rec
                    _ds_rec_snap = _ds_rec()
                    _rec.record_frame(
                        stone=_last_live_stone,
                        status=_ds_rec_snap.get("status", "RUNNING"),
                        goal=_ds_rec_snap.get("goal", ""),
                        stage=_current_stage,
                        run_number=_ds_rec_snap.get("run_number", 0),
                        auto_str=bool(_ds_rec_snap.get("auto_strength", True)),
                        activate_drills=bool(_ds_rec_snap.get("activate_drills", True)),
                    )
            except Exception as _rec_e:
                log.debug(f"[Recorder] record_frame error: {_rec_e}")
            if _KILLED or _stone_frozen or _REBIRTH_IN_PROGRESS:
                miss_count = 0   # reset while frozen/killed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â don't falsely trigger
                continue
            if _stone_icon_visible_restart_image():
                miss_count = 0
            else:
                try:
                    from manual_strength import is_window_open as _manual_window_open
                    if _manual_window_open():
                        # Strength window (close button visible) = manual strength
                        # legitimately running — the HUD image may be covered.
                        # Never close it from the watcher — closing it mid-tag
                        # froze the bot at the rock (window opened, watcher closed it).
                        # Window CLOSED + image missing = stuck outside game ->
                        # the miss counts and recovery takes over.
                        log.debug("[WATCHER] strength window up — ignore in-game miss")
                        miss_count = 0
                        continue
                except Exception as e:
                    log.debug(f"[WATCHER] manual strength stray-menu check failed: {e}")
                miss_count += 1
                log.debug(f"[WATCHER] stone icon miss {miss_count}/8")
                if miss_count >= 8:
                    miss_count = 0
                    log.warning("[WATCHER] stone icon missing 5s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â triggering stone-lost handler")
                    _stone_lost_handler()
                    # After handler sets _STONE_LOST we stop watching ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â outer loop owns recovery
                    break

    _watcher_thread = threading.Thread(target=_watcher_loop, args=(_watcher_stop_ev,), daemon=True)
    _watcher_thread.start()
    log.debug("[WATCHER] stone icon watcher started")

def _stop_stone_watcher():
    """Stop the background stone-icon watcher thread."""
    global _watcher_thread, _watcher_stop_ev
    _t = _watcher_thread
    if _watcher_stop_ev is not None:
        _watcher_stop_ev.set()
        _watcher_stop_ev = None
    if _t is not None and _t.is_alive():
        _t.join(timeout=0.6)
    _watcher_thread = None

def _stone_lost_handler():
    """Called by watcher thread when stone icon has been missing for 3 s.
    Stops macros/drills immediately and signals the run loop via _STONE_LOST."""
    global _STONE_LOST
    if _STONE_LOST or _KILLED:
        return   # already handling
    _STONE_LOST = True
    log.warning("[WATCHER] Stone icon lost ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stopping macros and drills")
    try: stop_macro()
    except Exception: pass
    try: _stop_drill_loop()
    except Exception: pass
    if _auto_strength_enabled():
        try: disable_auto_strength()
        except Exception: pass
        try: set_overlay(auto_str=False)
        except Exception: pass
    set_overlay(status="STONE LOST", goal="Recovering...")
    _dash_update(status="STONE LOST", goal="Recovering...")
    cprint("[WATCHER] Stone icon lost ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â waiting for recovery", "warn")

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Alive check ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _check_alive() -> bool:
    """Returns False if the watcher flagged stone lost, or if F9 was pressed.

    The heavy stone-icon polling is now done by the always-on watcher thread
    (_start_stone_watcher).  _check_alive() is a lightweight gate used inside
    polling loops to break out as soon as either flag is set.
    """
    if _KILLED:
        log.debug("_check_alive: killed")
        return False

    if _STONE_LOST:
        log.debug("_check_alive: stone lost (watcher flagged)")
        return False

    if _TEST_FORCE_FAILURE:
        log.debug("_check_alive: test force failure requested")
        return False

    if not is_fortnite_focused():
        stop_macro()
        log.warning("Fortnite lost focus ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stopping macro")
        set_overlay(status="WAITING", goal="No focus")
        return False

    return True


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Hit macro runner (with mouse centre pre-settle) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

# Background thread handle for the drill-presser loop
_drill_thread = None
_drill_stop_event = None

_DRILL_AUTO_PRESSES = 1
_DRILL_MANUAL_PRESSES = 6
_DRILL_BURST_INTERVAL = 0.05
_DRILL_EDGE_DELAY = 0.05


def _do_drill_burst(reason: str, presses: int, stop_ev=None) -> None:
    """50ms → press(es) 50ms apart → 50ms, then caller starts hitting."""
    n = max(0, int(presses))
    if n <= 0:
        return
    if stop_ev is not None and stop_ev.is_set():
        return
    time.sleep(_DRILL_EDGE_DELAY)
    try:
        from screen import is_drill_active
        if is_drill_active():
            log.debug("[DRILLS] already active (cyan timer) — skip press")
            time.sleep(_DRILL_EDGE_DELAY)
            return
    except Exception as e:
        log.debug(f"[DRILLS] active-check failed, pressing anyway: {e}")
    for idx in range(n):
        if stop_ev is not None and stop_ev.is_set():
            return
        if _KILLED or _STONE_LOST:
            return
        if idx > 0:
            time.sleep(_DRILL_BURST_INTERVAL)
        if not _trigger_drill_binding(stop_ev=stop_ev, check_active=False):
            break
    time.sleep(_DRILL_EDGE_DELAY)
    log.debug(f"[DRILLS] {reason}: burst x{n} ({_DRILL_BURST_INTERVAL:.2f}s)")

def _base_rock_drill_presses() -> int:
    try:
        import config as _cfg_runtime
        return max(0, int(getattr(_cfg_runtime, "BASE_ROCK_DRILL_PRESSES", _DRILL_MANUAL_PRESSES)))
    except Exception:
        return _DRILL_MANUAL_PRESSES


def _rebirth_drills_enabled(target: str, ds_snap: dict | None = None) -> bool:
    """Return whether rebirth drill usage is enabled for a specific target."""
    if ds_snap is None:
        from dashboard import get_state as _ds
        ds_snap = _ds()

    master = bool(ds_snap.get("rebirth_activate_drills", ds_snap.get("activate_drills", _ACTIVATE_DRILLS)))
    if not master:
        return False

    target_to_state = {
        "a5_meteor": "rebirth_drill_on_a5_meteor",
        "rock": "rebirth_drill_on_rock",
        "baserock": "rebirth_drill_on_baserock",
    }
    target_defaults = {
        "a5_meteor": _CFG_USE_DRILL_ON_A5_METEOR,
        "rock": _CFG_USE_DRILL_ON_ROCK,
        "baserock": _CFG_USE_DRILL_ON_BASEROCK,
    }
    key = target_to_state.get(target)
    if key is None:
        return master
    return bool(ds_snap.get(key, target_defaults.get(target, True)))

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Background stone reader (baserock overlay fix) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
_br_stone_reader_stop: "threading.Event | None" = None
_br_stone_reader_thread: "threading.Thread | None" = None

def _start_br_stone_reader():
    """Start a background thread that reads stone every 0.5s during baserock farming.

    The baserock_hit macro takes ~6.75s per run ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the stop-flag check (which
    calls read_stone) only fires AFTER the macro finishes, so the overlay can
    lag up to ~6.75s between updates.  This thread keeps the display live.
    """
    global _br_stone_reader_stop, _br_stone_reader_thread
    if _br_stone_reader_thread and _br_stone_reader_thread.is_alive():
        return
    _br_stone_reader_stop = threading.Event()
    _stop_ev = _br_stone_reader_stop

    def _reader(_stop_ev=_stop_ev):
        while not _stop_ev.is_set():
            if not _stone_frozen:
                try:
                    val = _read_stone_live()
                    if val is not None:
                        set_overlay(stone=val)
                        _dash_update(cur_stone=val)
                except Exception:
                    pass
            _stop_ev.wait(0.5)

    _br_stone_reader_thread = threading.Thread(target=_reader, daemon=True)
    _br_stone_reader_thread.start()
    log.debug("[BR-READER] background stone reader started")

def _stop_br_stone_reader():
    """Stop the background stone reader thread."""
    global _br_stone_reader_stop
    if _br_stone_reader_stop:
        _br_stone_reader_stop.set()
        _br_stone_reader_stop = None
    log.debug("[BR-READER] background stone reader stopped")
# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _start_drill_loop(manual_presses: int | None = None, force_presses: int | None = None):
    """Start background thread that presses configured drill binding every 10s while hitting."""
    import threading
    global _drill_thread, _drill_stop_event
    _stop_drill_loop()  # kill any existing one first
    _drill_stop_event = threading.Event()

    def _loop(stop_ev):
        while not stop_ev.wait(10):
            if stop_ev.is_set():
                break
            _do_drill_burst("Periodic drill refresh", presses, stop_ev=stop_ev)

    def _loop_boot():
        if force_presses is not None:
            return max(0, int(force_presses))
        return (manual_presses if manual_presses is not None else _DRILL_MANUAL_PRESSES) if _manual_strength_enabled() else _DRILL_AUTO_PRESSES

    presses = _loop_boot()
    _drill_thread = threading.Thread(target=_loop, args=(_drill_stop_event,), daemon=True)
    _drill_thread.start()
    log.debug("[DRILLS] Drill loop started")

def _stop_drill_loop():
    """Stop the background drill-presser thread."""
    global _drill_thread, _drill_stop_event
    _t = _drill_thread
    if _drill_stop_event is not None:
        _drill_stop_event.set()
        _drill_stop_event = None
    if _t is not None and _t.is_alive():
        _t.join(timeout=0.4)
    _drill_thread = None


def _builtin_hits_enabled(cfg_key: str) -> bool:
    """True if the bot is allowed to swing/hit itself (Rebirth → Fine-Tuning → Hit Controls).

    False means the player's own macro does the swinging: no LMB swings from
    the bot and no hit-confirmation waits — monitoring/manual strength still run.
    """
    try:
        import config as _cfg_hits
        return bool(getattr(_cfg_hits, cfg_key, True))
    except Exception:
        return True


def _select_monitor_item() -> None:
    """Press the monitor-item slot (default 2) — a left click then opens the strength window."""
    import config as _cfg_mi
    binding = str(getattr(_cfg_mi, "MONITOR_ITEM_BINDING", "2") or "2").strip() or "2"
    used = binding
    if not trigger_binding_action(binding, hold_ms=30):
        used = "2"
        trigger_binding_action(used, hold_ms=30)
    log.debug(f"[MANUAL_STR] monitor item selected: {used}")


def _run_hit_macro(macro: str, wait: bool = True, skip_center: bool = False):
    """Press configured drill binding if enabled, then run a hit macro."""
    if _KILLED or _STONE_LOST:
        return None
    from dashboard import get_state as _ds
    _ds_snap = _ds()
    import config as _cfg_hits
    _hit_gate = {
        "rock_hit":     bool(getattr(_cfg_hits, "HIT_ROCKS", True)),
        "meteor_hit":   bool(getattr(_cfg_hits, "HIT_A5_METEOR", True)),
        "baserock_hit": bool(getattr(_cfg_hits, "HIT_BASEROCK", True)),
    }.get(macro)
    if _hit_gate is False:
        log.info(f"[HIT] {macro} disabled in Rebirth → Fine-Tuning (Hit Controls) — skipping built-in hit")
        return True
    drill_target = {
        "rock_hit": "rock",
        "meteor_hit": "a5_meteor",
        "baserock_hit": "baserock",
    }.get(macro)
    drill_presses = _base_rock_drill_presses() if macro == "baserock_hit" else 1

    _equip_pickaxe(macro)

    if drill_target is not None and _rebirth_drills_enabled(drill_target, _ds_snap):
        _do_drill_burst("Immediate drill activation", drill_presses)
        if not wait:
            _start_drill_loop(force_presses=drill_presses)
    if wait:
        return _run_macro(macro)
    global _ACTIVE_HIT_MACRO
    _rec_log_macro(macro, "start")
    handle = run_macro(macro, wait=False)
    if handle is None:
        _rec_log_macro(macro, "error", error="macro_start_failed")
        _rec_set_failure(f"macro_start_failed:{macro}")
        return handle
    _ACTIVE_HIT_MACRO = macro
    return handle


def _close_hit_macro(status: str = "end", **fields) -> None:
    """Log the real stop time of whichever hit macro is currently tracked as
    active (started via _run_hit_macro(wait=False)). No-op if none is open.
    Call this right before stop_macro() wherever a hit-macro session ends —
    without it, rock_hit/meteor_hit/baserock_hit never get a macro_end and
    the timeline either shows a stretched/merged block or a blank gap where
    the bot was actually mining.
    """
    global _ACTIVE_HIT_MACRO
    if _ACTIVE_HIT_MACRO:
        _rec_log_macro(_ACTIVE_HIT_MACRO, status, **fields)
        _ACTIVE_HIT_MACRO = None

def _run_baserock_loop_until(
    stop_flag_fn,
    skip_center: bool = False,
    manual_reason: str = "",
    activity_callback=None,
):
    global _manual_strength_active
    """Run baserock_hit macro repeatedly until stop_flag_fn() returns True or _KILLED.

    Each iteration runs the macro to COMPLETION (wait=True) before checking
    whether to continue.  This guarantees the LCtrl toggle is always fully
    paired inside a single run ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the character can never be left crouched
    mid-loop.
    """
    from dashboard import get_state as _ds
    from macro_runner import _mouse_left_click as _br_click
    _ds_snap = _ds()
    _HIT_MACRO = "baserock_hit"

    # HIT_BASEROCK off = the player's own macro already swings the baserock.
    # The bot must NOT left-click the rock (no hit macro, no prime taps) and must
    # NOT wait on hit confirmation — but manual strength (menu + buying) still runs.
    import config as _cfg_hits
    _hit_off = not bool(getattr(_cfg_hits, "HIT_BASEROCK", True))

    if _rebirth_drills_enabled("baserock", _ds_snap):
        _do_drill_burst("Base rock drill activation", _base_rock_drill_presses())
        _start_drill_loop(force_presses=_base_rock_drill_presses())

    _start_br_stone_reader()
    _manual_handle = None

    try:
        if manual_reason and not _KILLED and not _STONE_LOST and not stop_flag_fn():
            # Fast open sequence (user-specified): after the nav macro ends,
            # wait 100ms -> [optional single swing if HIT_BASEROCK on] ->
            # wait MANUAL_STR_OPEN_AFTER_HIT_WAIT (default 0.5s) -> select
            # monitor item -> wait MANUAL_STR_OPEN_AFTER_MONITOR_WAIT (default
            # 0.5s) -> left click -> 250ms -> manual
            # strength starts buying. No pre-open stone checks — the buying
            # loop's own ~5s HUD stall watchdog is enough.
            log.info(f"[MANUAL_STR] {manual_reason}: fast open (no pre-open stone checks)")
            # Claim the manual-strength phase BEFORE opening the window: the
            # stone watcher must not treat the freshly-opened menu as a stray
            # menu covering the icon (it closes it and stalls the whole run).
            _manual_strength_active = True
            _rec_log_macro("baserock_open_sequence", "start")
            import config as _cfg_open
            _open_pre_wait  = max(0.0, float(getattr(_cfg_open, "MANUAL_STR_OPEN_AFTER_HIT_WAIT", 0.5)))
            _open_post_wait = max(0.0, float(getattr(_cfg_open, "MANUAL_STR_OPEN_AFTER_MONITOR_WAIT", 0.5)))
            time.sleep(0.10)
            if _builtin_hits_enabled("HIT_BASEROCK"):
                _br_click()   # single swing to start the grind — trust it hits
            import config as _cfg_msopen
            _ms_open_enabled = bool(getattr(_cfg_msopen, "MANUAL_STR_OPEN", True))
            if _ms_open_enabled:
                # Fine-tunable open pacing: hit -> wait -> monitor key -> wait -> open.
                time.sleep(_open_pre_wait)
                _select_monitor_item()
                time.sleep(_open_post_wait)
                _br_click()      # opens the strength window
                time.sleep(0.25)
            else:
                log.info("[MANUAL_STR] auto-open disabled (Manual Strength Open) — macro must open the window")
            _rec_log_macro("baserock_open_sequence", "end")
            # Give the window a moment to appear so the live loop sees it open
            # and starts buying instantly instead of re-doing its own open clicks.
            try:
                from screen import _manual_strength_window_open as _win_open
            except Exception:
                _win_open = None
            _win_deadline = time.time() + 0.75
            while _win_open and time.time() < _win_deadline and not _KILLED and not _STONE_LOST:
                if _win_open():
                    break
                time.sleep(0.10)
            _manual_handle = _start_manual_strength_live(
                manual_reason, activity_callback=activity_callback
            )
            if _manual_handle is None:
                _manual_strength_active = False
                log.warning(f"[MANUAL_STR] {manual_reason}: manual strength failed to start; retrying route")
                return
            while not _KILLED and not _STONE_LOST and not stop_flag_fn():
                if hasattr(_manual_handle, "is_alive") and not _manual_handle.is_alive():
                    _manual_strength_active = False
                    log.warning(f"[MANUAL_STR] {manual_reason}: live loop ended before target — re-navigating")
                    return
                time.sleep(0.08)
            return

        if _hit_off:
            # Auto strength + hit disabled: the player's macro does the swinging —
            # nothing to click, just watch the stone HUD.
            log.info("[HIT] built-in baserock hit disabled (Rebirth → Fine-Tuning → Hit Controls) — watching stone")
            _peak = None
            _last_gain = time.time()
            while not _KILLED and not _STONE_LOST and not stop_flag_fn():
                time.sleep(0.25)
                c = _read_stone_live(update_last=False, check_glitch=False)
                if c is not None and c > 0:
                    if _peak is None or c > _peak:
                        _peak = c
                        _last_gain = time.time()
                    elif time.time() - _last_gain >= 30.0:
                        log.warning("Base rock: no stone gain for 30.0s (built-in hit disabled) — re-navigate")
                        return
            return

        # Blocking loop: run one full macro at a time, check stop condition after.
        # Blocking loop: run one full macro at a time, check stop condition after.
        # This ensures KEY_DOWN:LCtrl and KEY_UP:LCtrl are always paired.
        while not _KILLED and not _STONE_LOST and not stop_flag_fn():
            _ok = _run_macro(_HIT_MACRO)   # blocks until macro finishes cleanly
            if not _ok:
                log.error(f"Hit macro failed or was interrupted: {_HIT_MACRO}")
                break
            # stop_flag_fn() / _KILLED is re-checked at the top of the next iteration
    finally:
        _stop_manual_strength_live(_manual_handle)
        _stop_drill_loop()
        _stop_br_stone_reader()


def _wait_stone_change(
    start_stone,
    target: float,
    timeout: float,
    goal: str,
    smart_timeout: float = 0,
    no_gain_timeout: float = 0,
    threshold_timeout: float = 0,
    manual_strength_watch=None,
) -> tuple[bool, float | None]:
    """Poll stone until >= target or timeout. Returns (success, final_stone).

    no_gain_timeout   ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â if stone has NOT moved at all within this many seconds,
                        return False for re-navigate. Stays active until stone moves.
    threshold_timeout ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â hard deadline from farming start: if threshold not reached
                        within this many seconds (regardless of stone movement),
                        return False for re-navigate. 0 = disabled.
    smart_timeout     ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â legacy: only starts counting AFTER first stone movement.
    """
    global _last_live_stone
    deadline          = None if timeout == 0 else time.time() + timeout
    threshold_deadline = (time.time() + threshold_timeout) if threshold_timeout else None
    last_stone        = start_stone
    start_time        = time.time()
    _no_gain_last_move = start_time  # tracks last time stone actually increased
    no_gain_active    = bool(no_gain_timeout)
    smart_start       = None

    while deadline is None or time.time() < deadline:
        if _KILLED:
            return False, last_stone
        if _peek_net_redo():
            return False, last_stone

        if not _check_alive():
            return False, last_stone

        if _manual_strength_watchdog_stalled(manual_strength_watch):
            return False, last_stone

        if _stone_frozen:
            time.sleep(0.5)
            continue

        cur = _read_stone_live(update_last=False, check_glitch=False)
        if cur is not None:
            # Manual-strength runs can legitimately jump far beyond 1e6x between
            # consecutive HUD reads; keep low-glitch protection, but disable the
            # high-glitch cap here (same rationale as baserock flow).
            glitch_reason = _stone_glitch_reason(
                cur,
                last_stone,
                check_high=not _manual_strength_active,
            )
            if glitch_reason:
                log.debug(f"{goal}: OCR {glitch_reason} glitch ignored: {cur} (last={last_stone})")
                time.sleep(0.1)
                continue
            set_overlay(stone=cur)
            _dash_update(cur_stone=cur)
            if cur >= target:
                if target == float("inf"):
                    return True, cur
                confirmed, confirmed_cur = _confirm_stone_at_least(
                    target,
                    goal,
                    first_value=cur,
                    attempts=5,
                    required_hits=2,
                    delay=0.12,
                )
                if confirmed:
                    cur = confirmed_cur or cur
                    _last_live_stone = cur
                    return True, cur
                if confirmed_cur is not None:
                    cur = confirmed_cur
                else:
                    time.sleep(0.1)
                    continue
            _last_live_stone = cur
            if cur > last_stone:
                # Stone moved ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â disable the initial no-gain check
                no_gain_active = bool(no_gain_timeout)  # re-arm so mid-farm stalls also fire
                _no_gain_last_move = time.time()
                smart_start    = time.time()
            # FIX 6b: Only let last_stone drop if the new value is plausible
            # relative to the current peak Ã¢â‚¬â€ prevents OCR artifacts like "153"
            # from collapsing the reference and triggering false no-gain exits.
            if last_stone is None or cur > last_stone or last_stone < 1e6 or cur >= last_stone * 0.001:
                last_stone = cur

        # no_gain_timeout: stone stalled (fires at start AND after any movement)
        if no_gain_active and no_gain_timeout and (time.time() - _no_gain_last_move) > no_gain_timeout:
            log.warning(f"{goal}: no stone gain in first {no_gain_timeout}s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â re-navigate needed")
            return False, last_stone

        # threshold_timeout: hard deadline ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â threshold not hit in time regardless of movement
        if threshold_deadline and time.time() > threshold_deadline:
            log.warning(f"{goal}: threshold not reached within {threshold_timeout}s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â re-navigate needed")
            return False, last_stone

        # smart_timeout: legacy ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â only fires after first movement
        if smart_timeout and smart_start and (time.time() - smart_start) > smart_timeout:
            log.warning(f"Smart failure timeout ({smart_timeout}s) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stone not growing")
            return False, last_stone

        time.sleep(0.1)  # v1.2: reduced from 0.5s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â faster threshold detection

    if deadline is not None:
        log.warning(f"Stone-change timeout after {timeout}s")
    return False, last_stone


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Navigation helpers ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _teleport_to_base():
    global _at_base
    _clear_current_stage_point("teleport to base")
    if _manual_strength_enabled():
        if not _stop_active_manual_strength_for_action("teleport to base"):
            _rec_set_failure("manual_strength_close_failed:teleport_to_base")
            return False
    if _auto_strength_enabled():
        disable_auto_strength()
        set_overlay(auto_str=False)
    else:
        _disable_auto_strength_for_manual("teleport to base")
    _console_status("NAVIGATING", "Base")
    ok = bool(_builtin_teleport_safe("base"))
    _at_base = bool(ok)
    if not ok:
        log.warning("Teleport to base failed")
    set_overlay(status="NAVIGATING", goal="Base")
    return bool(ok)


def _equip_pickaxe(reason: str = "teleport") -> None:
    """Press pickaxe (default F). Manual-str leaves you on the monitor item;
    LMB on that slot re-opens the strength window instead of mining."""
    if _KILLED:
        return
    try:
        from manual_strength import is_window_open, close_window_verified
        if is_window_open():
            log.info(f"[PICKAXE] strength window open before {reason} — closing")
            close_window_verified(attempts=5)
    except Exception:
        pass
    import config as _cfg_pk
    binding = str(getattr(_cfg_pk, "PICKAXE_EQUIP_BINDING", "F") or "F").strip() or "F"
    used = binding
    if not trigger_binding_action(binding, hold_ms=35):
        used = "F"
        trigger_binding_action(used, hold_ms=35)
    time.sleep(0.04)
    trigger_binding_action(used, hold_ms=35)
    log.info(f"[PICKAXE] {used} after {reason}")


def _builtin_teleport_safe(destination: str, *, attempts: int | None = None, wait_seconds: float = 0.0) -> bool:
    """Detect-based F4 teleport (no teleport_to_*.macro)."""
    destination = str(destination or "").strip().lower()
    _freeze_stone(True)
    _rec_log_macro(f"teleport_{destination}", "start")
    try:
        n = _route_redo_limit() if attempts is None else max(1, min(int(attempts), _route_redo_limit()))
        log.info(f"[TELEPORT] {destination} via F4 detect ({n} attempts)")
        ok = bool(_builtin_teleport(destination, attempts=n, wait_seconds=wait_seconds))
        if ok:
            # F during the load screen is eaten — wait for the map, then pickaxe.
            _wait_map_loaded(destination)
            _equip_pickaxe(f"teleport {destination}")
        if not ok and not _KILLED:
            # Dest locked / menu miss — caller retries the unlock path.
            # Don't stamp redo_limit here (that looks like a hard route fail).
            log.warning(f"[TELEPORT] {destination} failed")
        _rec_log_macro(f"teleport_{destination}", "end" if ok else "error",
                        error=None if ok else "teleport_failed")
        return ok
    finally:
        _freeze_stone(False)


def _hold_for_network() -> bool:
    """Pause on Lag: wait out disconnects. False if F9."""
    try:
        from net_guard import hold_if_needed
        return bool(hold_if_needed())
    except Exception:
        return True


def _peek_net_redo() -> bool:
    try:
        from net_guard import peek_redo
        return bool(peek_redo())
    except Exception:
        return False


def _take_net_redo() -> bool:
    try:
        from net_guard import take_redo
        return bool(take_redo())
    except Exception:
        return False


def _nav_or_redo(name: str) -> str:
    """Run a nav/farm walk macro. 'ok' | 'kill' | 'redo' | 'fail'."""
    ok = _run_macro(name)
    if _KILLED or _STONE_LOST:
        return "kill"
    if _take_net_redo():
        return "redo"
    return "ok" if ok else "fail"


def _force_restart_enabled(ds_snap: dict | None = None) -> bool:
    try:
        if ds_snap is None:
            from dashboard import get_state as _ds_fr
            ds_snap = _ds_fr()
        mode = str(ds_snap.get("bot_mode", "rebirth")).lower()
        # Force Restart is an engine feature: rebirth, crater, kraken, zytos, farm meteor.
        if mode not in ("rebirth", "crater", "kraken", "zytos", "farm_meteor"):
            return False
        if "force_restart" in ds_snap:
            return bool(ds_snap.get("force_restart"))
        import config as _cfg_fr
        return bool(getattr(_cfg_fr, "FORCE_RESTART_ON_FAILURE", False))
    except Exception:
        return False


def _menu_resume_enabled(ds_snap: dict | None = None) -> bool:
    """Menu Resume is bundled with Force Restart, with legacy state as fallback."""
    try:
        if ds_snap is None:
            from dashboard import get_state as _ds_mr
            ds_snap = _ds_mr()
        return bool(ds_snap.get("force_restart") or ds_snap.get("menu_resume"))
    except Exception:
        return False


def _try_force_restart_after_failure(reason: str, ds_snap: dict | None = None) -> bool:
    global _WAITING_FOR_START, _STONE_LOST, _at_base, _menu_resume_fresh_start
    reason_l = str(reason or "").lower()
    if "loadouts not set" in reason_l or "missing_loadout" in reason_l:
        log.info("[FORCE_RESTART] skipped — loadouts not set (user config, not a run failure)")
        return False
    if _LOADOUT_BLOCKED:
        return False
    if _KILLED or not _force_restart_enabled(ds_snap):
        return False

    # ── Three-state check: in game? GUI open? clearly not in game? ──
    # Runs BEFORE leaving anything. Most "failures" are a stray GUI or a
    # slow join — those recover without touching the lobby, and if we are
    # already in the lobby menu we join straight from there (no ESC round
    # trip, no chance to land on the wrong game).
    try:
        from fr_flow import three_state_recovery as _tsr, menu_join_flow as _mjf
        state = _tsr(tag=reason)
        if state == "in_game":
            log.info(f"[FORCE_RESTART] three-state: in game \u2014 recovered without leaving ({reason})")
            return True
        if state == "menu":
            log.info("[FORCE_RESTART] three-state: already in the lobby menu \u2014 joining Miner Tycoon 2")
            if _mjf(reason):
                if _KILLED:
                    return False
                _WAITING_FOR_START = False
                _at_base = False
                _menu_resume_fresh_start = True
                _dash_update(
                    killed=False,
                    run_active=False,
                    waiting_for_start=False,
                    status="RESTART",
                    goal="Restarting",
                )
                set_overlay(status="RESTART", goal="Restarting")
                log.info("[FORCE_RESTART] menu join OK; starting fresh run")
                return True
            log.warning("[FORCE_RESTART] menu join failed \u2014 falling back to leave-to-lobby")
        # "give_up" -> leave-to-lobby below
    except Exception as e:
        log.warning(f"[FORCE_RESTART] three-state check failed: {e}")

    for attempt in range(1, 4):
        if _KILLED:
            return False
        log.warning(f"[FORCE_RESTART] detect flow after failure: {reason}  attempt={attempt}/3  {_farm_env_bits()}")
        _console_status("Restarting", "Leaving To Menu")
        set_overlay(status="Restarting", goal="Leaving To Menu")
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        _clear_current_stage_point("force restart")
        _STONE_LOST = False
        try:
            from lobby import force_restart as _lobby_force
            ok = bool(_lobby_force())
        except Exception as e:
            log.warning(f"[FORCE_RESTART] failed: {e}")
            ok = False
        if ok:
            break
        log.warning(f"[FORCE_RESTART] Ready/shard failed (attempt {attempt}/3)")
        if attempt < 3 and not _KILLED:
            time.sleep(2.0)
    else:
        log.warning("[FORCE_RESTART] Ready/shard failed after 3 attempts — stopping")
        return False
    if _KILLED:
        return False
    _WAITING_FOR_START = False
    _at_base = False
    _menu_resume_fresh_start = True
    _dash_update(
        killed=False,
        run_active=False,
        waiting_for_start=False,
        status="RESTART",
        goal="Restarting",
    )
    set_overlay(status="RESTART", goal="Restarting")
    log.info("[FORCE_RESTART] lobby Ready + shard OK; starting fresh run")
    return True


def _mark_area_unlocked(area: int, reason: str = ""):
    global _A5_UNLOCKED_THIS_RUN, _AREA_UNLOCKED_THIS_RUN
    if area in _AREA_UNLOCKED_THIS_RUN:
        _AREA_UNLOCKED_THIS_RUN[area] = True
    if area == 5:
        _A5_UNLOCKED_THIS_RUN = True
    _mark_left_base()
    if reason:
        log.info(f"[AREA] Area {area} unlocked ({reason})")


def _go_to_area(area: int, attempt_label: str = "") -> bool:
    global _A5_UNLOCKED_THIS_RUN, _AREA_UNLOCKED_THIS_RUN
    _clear_current_stage_point(f"go to area{area}")
    if _manual_strength_enabled():
        if not _stop_active_manual_strength_for_action(f"go to area{area}"):
            _rec_set_failure(f"manual_strength_close_failed:go_to_area{area}")
            return False

    if _auto_strength_enabled():
        disable_auto_strength()
        set_overlay(auto_str=False)
    else:
        _disable_auto_strength_for_manual(f"go to area{area}")

    area_goal = f"Area {area}"

    if area == 5:
        if not _A5_UNLOCKED_THIS_RUN:
            _console_status("NAVIGATING", area_goal)
            if not _teleport_to_base():
                _rec_set_failure("teleport_failed:base_before_area5")
                return False
            _console_status("NAVIGATING", area_goal)
            r = _nav_or_redo("base_to_a5_teleport")
            if r == "kill":
                return False
            if r == "fail":
                _rec_set_failure("macro_failed:base_to_a5_teleport")
                return False
            if r == "redo":
                log.warning("[NET] lag during base_to_a5 — retry area5 path")
                return _go_to_area(5, attempt_label)
            _mark_area_unlocked(5, "first_manual")
            return True

        _console_status("NAVIGATING", area_goal)
        if not _builtin_teleport_safe("area5", attempts=3, wait_seconds=3.5):
            _rec_set_failure("teleport_failed:area5")
            return False
        _mark_area_unlocked(5, "teleport")
        return True

    if area not in (1, 2, 3, 4):
        log.warning(f"Unsupported area request: {area}")
        return False

    if not _AREA_UNLOCKED_THIS_RUN.get(area, False):
        _console_status("NAVIGATING", area_goal)
        if area != 1 or not _at_base:
            if not _teleport_to_base():
                _rec_set_failure(f"teleport_failed:base_before_area{area}")
                return False
            _console_status("NAVIGATING", area_goal)
        macro_name = f"base_to_a{area}_teleport"
        r = _nav_or_redo(macro_name)
        if r == "kill":
            return False
        if r == "fail":
            _rec_set_failure(f"macro_failed:{macro_name}")
            return False
        if r == "redo":
            log.warning(f"[NET] lag during {macro_name} — retry area{area} path")
            return _go_to_area(area, attempt_label)
        _mark_area_unlocked(area, "first_manual")
        return True

    _console_status("NAVIGATING", area_goal)
    if not _builtin_teleport_safe(f"area{area}", attempts=3, wait_seconds=3.5):
        _rec_set_failure(f"teleport_failed:area{area}")
        return False
    _mark_area_unlocked(area, "teleport")
    return True


def _go_to_area5(attempt_label: str = "") -> bool:
    return _go_to_area(5, attempt_label)


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Stage farming ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬


def _entry_threshold(area: int, stage: int) -> float:
    if area == 1:
        return {1: 0.0, 2: STONE_FOR_A1_STAGE2, 3: STONE_FOR_A1_STAGE3, 4: STONE_FOR_A1_STAGE4}[stage]
    if area == 2:
        return {1: STONE_FOR_A2_STAGE1, 2: STONE_FOR_A2_STAGE2, 3: STONE_FOR_A2_STAGE3, 4: STONE_FOR_A2_STAGE4}[stage]
    if area == 3:
        return {1: STONE_FOR_A3_STAGE1, 2: STONE_FOR_A3_STAGE2, 3: STONE_FOR_A3_STAGE3, 4: STONE_FOR_A3_STAGE4}[stage]
    if area == 4:
        return {1: STONE_FOR_A4_STAGE1, 2: STONE_FOR_A4_STAGE2, 3: STONE_FOR_A4_STAGE3, 4: STONE_FOR_A4_STAGE4}[stage]
    return {1: STONE_FOR_A5_STAGE1, 2: STONE_FOR_A5_STAGE2, 3: STONE_FOR_A5_STAGE3, 4: STONE_FOR_A5_STAGE4}[stage]


def _exit_threshold(area: int, stage: int) -> float:
    if stage < 4:
        return _entry_threshold(area, stage + 1)
    if area < 5:
        return _entry_threshold(area + 1, 1)
    return STONE_FOR_METEOR


def _stage_nav_macro(area: int, stage: int) -> str:
    return f"area{area}_to_stage{stage}_rock"


def _shortcuts_enabled() -> bool:
    try:
        import config as _cfg_shortcuts
        return bool(getattr(_cfg_shortcuts, "USE_SHORTCUTS", True))
    except Exception:
        return False


def _stage_shortcut_macro(area: int, stage: int) -> str | None:
    if not _shortcuts_enabled() or _CURRENT_STAGE_POINT is None:
        return None
    candidate = f"{_stage_nav_macro(area, stage)}_shortcut"
    if macro_exists(candidate):
        log.info(
            f"[SHORTCUT] Using {candidate}.macro from A{_CURRENT_STAGE_POINT[0]}S{_CURRENT_STAGE_POINT[1]} "
            f"to A{area}S{stage}"
        )
        return candidate
    log.debug(f"[SHORTCUT] Missing {candidate}.macro; normal teleport route will be used")
    return None


def _previous_stage_point(area: int, stage: int):
    if stage > 1:
        return area, stage - 1
    if area > 1:
        return area - 1, 4
    return None


def _normalize_start_mode(run_mode: str) -> str:
    mode = str(run_mode or "").strip().lower()
    legacy = {
        "full": "a1s1",
        "stage2": "a5s2",
        "stage3": "a5s3",
        "stage4": "a5s4",
        "meteor": "a5meteor",
        "a6s4": "a5meteor",
        "a6s3": "a5meteor",
        "a6s2": "a5meteor",
        "a6s1": "a5meteor",
    }
    mode = legacy.get(mode, mode)
    allowed = {f"a{a}s{s}" for a in range(1, 6) for s in range(1, 5)}
    allowed.add("a5meteor")
    if mode not in allowed:
        return "a1s1"
    return mode


# â”€â”€ Boss Fight A1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _select_bramble_fight_mode(tag: str = "BOSS_A1") -> bool:
    """After the boss card opens, OCR the mode name and cycle until it matches.

    Config > Boss Fight > Mode is solo/normal/hard/ex (shared by Bramble and
    Zytos). Kraken is Solo-only and never calls this. Each mode has OCR
    aliases for translations. Loop:
      1. OCR BRAMBLE_MODE_REGION (subtitle under the boss name).
      2. If it already matches, continue the fight.
      3. If not, click the HARD pill at BRAMBLE_MODE_SWAP_CENTER
         (bottom of the left INFO card — do not OCR the pill) and read again.
    """
    from macro_runner import _mouse_move_abs, _mouse_left_click
    from config import (
        normalize_bramble_mode, normalize_bramble_mode_ocr, DEFAULT_BRAMBLE_MODE_OCR,
    )
    import config as _cfg_mode

    want = normalize_bramble_mode(getattr(_cfg_mode, "BOSS_FIGHT_A1_MODE", "normal"))
    aliases_map = normalize_bramble_mode_ocr(getattr(_cfg_mode, "BOSS_FIGHT_A1_MODE_OCR", DEFAULT_BRAMBLE_MODE_OCR))
    aliases = list(aliases_map.get(want) or [])
    if not aliases:
        aliases = list(DEFAULT_BRAMBLE_MODE_OCR.get(want) or [want.upper()])
    max_swaps = max(1, int(getattr(_cfg_mode, "BRAMBLE_MODE_SWAP_MAX", 8)))
    wait_s = max(0.15, float(getattr(_cfg_mode, "BRAMBLE_MODE_SWAP_WAIT", 0.45)))
    swap = getattr(_cfg_mode, "BRAMBLE_MODE_SWAP_CENTER", (439, 826))
    try:
        sx, sy = int(swap[0]), int(swap[1])
    except Exception:
        sx, sy = 439, 826

    log.info(f"[{tag}] mode target={want} aliases={aliases}")
    _console_status("ZYTOS" if tag == "ZYTOS" else "BOSS FIGHT", f"Mode {want.upper()}")

    for attempt in range(max_swaps + 1):
        if _KILLED:
            return False
        text = read_bramble_mode_text()
        if bramble_mode_matches(text, aliases):
            log.info(f"[{tag}] mode match {text!r} == {want} (attempt {attempt + 1})")
            return True
        if attempt >= max_swaps:
            break
        log.info(f"[{tag}] mode {text!r} != {want} — clicking HARD pill ({attempt + 1}/{max_swaps})")
        try:
            _mouse_move_abs(sx, sy)
            time.sleep(0.05)
            _mouse_left_click()
        except Exception as e:
            log.warning(f"[{tag}] mode swap click failed: {e}")
            return False
        time.sleep(wait_s)

    log.warning(f"[{tag}] mode still not {want} after {max_swaps} swaps")
    return False


def _loadout_slot(raw) -> str:
    slot = str(raw or "none").strip().lower()
    if slot in ("", "none", "0", "null"):
        return "none"
    if slot in ("1", "2", "3", "4", "5", "6"):
        return slot
    return "none"


def missing_required_loadouts(bot_mode: str | None = None, run_mode: str | None = None, boss_fight_a1: bool | None = None) -> list[str]:
    """Loadouts that MUST be set for the current run. Empty = ok to start."""
    try:
        from dashboard import get_state as _ds
        snap = _ds()
    except Exception:
        snap = {}
    import config as _cfg_lo
    mode = str(bot_mode or snap.get("bot_mode") or "rebirth").strip().lower()
    run = _normalize_start_mode(run_mode or snap.get("run_mode") or "a1s1")
    if boss_fight_a1 is None:
        boss_on = bool(snap.get("boss_fight_a1", False))
    else:
        boss_on = bool(boss_fight_a1)
    fighting = _loadout_slot(getattr(_cfg_lo, "BOSS_FIGHT_A1_LOADOUT_FIGHTING", "none"))
    farming = _loadout_slot(getattr(_cfg_lo, "BOSS_FIGHT_A1_LOADOUT_FARMING", "none"))
    meteor_rw = _loadout_slot(getattr(_cfg_lo, "CRATER_LOADOUT_METEOR_REWARDS", "none"))
    missing: list[str] = []
    if mode in ("kraken", "zytos", "delve"):
        if fighting == "none":
            missing.append("Fighting")
        return missing
    if mode == "farm_meteor":
        meteor_farm = meteor_rw
        if meteor_farm == "none":
            meteor_farm = _loadout_slot(getattr(_cfg_lo, "FARM_METEOR_LOADOUT", "none"))
        if meteor_farm == "none":
            missing.append("Meteor Rewards")
        return missing
    if mode == "crater":
        if meteor_rw == "none":
            missing.append("Meteor Rewards")
        return missing
    # rebirth: farming always; fighting if boss
    if farming == "none":
        missing.append("Farming")
    if boss_on and fighting == "none":
        missing.append("Fighting")
    return missing


_last_loadout_focus_ts = 0.0


def _focus_bot_window() -> bool:
    """Bring the MT2 dashboard window to the front (Windows).

    Uses the classic ALT-key trick — SetForegroundWindow is normally denied
    for a background process, but a synthetic Alt press makes the OS treat
    this process as if it just received input, allowing the focus steal.
    """
    try:
        import ctypes
        u32 = ctypes.windll.user32
        hwnd = u32.FindWindowW(None, "MT2 Rebirth Bot")
        if not hwnd:
            return False
        fg = u32.GetForegroundWindow()
        if fg == hwnd:
            return True          # already focused
        u32.ShowWindow(hwnd, 9)  # SW_RESTORE (un-minimize)
        # momentary Alt tap — harmless in-game, enables foreground steal
        u32.keybd_event(0x12, 0, 0, 0)        # VK_MENU down
        u32.keybd_event(0x12, 0, 2, 0)       # VK_MENU up (KEYEVENTF_KEYUP)
        u32.SetForegroundWindow(hwnd)
        u32.BringWindowToTop(hwnd)
        return True
    except Exception as e:
        log.debug(f"[LOADOUT] focus bot window failed: {e}")
        return False


def _game_detect_active(ds_snap: dict | None = None) -> bool:
    """True when Force Restart is enabled for the current mode AND Game
    Detection (In-Game image detection) is required but not picked yet."""
    try:
        if not _force_restart_enabled(ds_snap):
            return False
        from game_detect import is_game_detect_set
        return not is_game_detect_set()
    except Exception as _e:
        log.debug(f"[GAME_DETECT] gate check failed: {_e}")
        return False


def _fresh_start_not_in_game(passes: int = 3) -> bool:
    """True when the In-Game image detection is set and CONFIRMED says we
    are not in game (a few passes, 0.4s apart — the settle window is tiny
    and a slow draw must not skip the loadout of a real in-game start).
    Returns False when the detection is not set (fallback to the classic
    loadout-first behavior)."""
    try:
        from game_detect import game_detect_result as _gdr
        for _ in range(max(1, passes)):
            res = _gdr()
            if res.get("set") is not True or res.get("ok") is not False:
                return False
            time.sleep(0.4)
        return True
    except Exception:
        return False


def missing_game_detection(ds_snap: dict | None = None) -> bool:
    """Gate: force restart ON but no In-Game image picked yet."""
    return _game_detect_active(ds_snap)


_GAME_DETECT_BLOCK_SEQ = 0


def _block_for_missing_game_detection() -> None:
    """Force Restart is ON but In-Game image detection is not picked.
    Do not start, do not force-restart — pop the dashboard widget."""
    global _WAITING_FOR_START, _GAME_DETECT_BLOCK_SEQ
    _GAME_DETECT_BLOCK_SEQ += 1
    _WAITING_FOR_START = True
    log.warning("[GAME_DETECT] Force Restart is ON but In-Game image detection is not set")
    _console_status("ERROR", "In-Game image detection not set!")
    try:
        set_overlay(status="ERROR", goal="In-Game image detection not set!")
    except Exception:
        pass
    _dash_update(
        waiting_for_start=True,
        run_active=False,
        run_start_time=None,
        status="ERROR",
        goal="In-Game image detection not set!",
        game_detect_block_seq=_GAME_DETECT_BLOCK_SEQ,
    )
    # Same as the loadout block: pull the dashboard to the front so the
    # user can pick the image right away.
    global _last_loadout_focus_ts
    _now = time.time()
    if _now - _last_loadout_focus_ts >= 5.0:
        _last_loadout_focus_ts = _now
        if _focus_bot_window():
            log.info("[GAME_DETECT] dashboard window brought to front (image detection not set)")


def _block_for_missing_loadouts(missing: list[str]) -> None:
    """User-config error: do not start, do not force-restart, keep dashboard popup up."""
    global _WAITING_FOR_START, _LOADOUT_BLOCKED, _LOADOUT_BLOCK_SEQ
    names = [str(x) for x in (missing or []) if str(x).strip()]
    if not names:
        return
    _LOADOUT_BLOCKED = True
    _LOADOUT_BLOCK_SEQ += 1
    _WAITING_FOR_START = True
    label = ", ".join(names)
    log.warning(f"[LOADOUT] cannot start — set these in Config: {label}")
    _console_status("ERROR", "Loadouts not set: " + label)
    try:
        set_overlay(status="ERROR", goal="Loadouts not set: " + label)
    except Exception:
        pass
    _dash_update(
        waiting_for_start=True,
        run_active=False,
        run_start_time=None,
        status="ERROR",
        goal="Loadouts not set: " + label,
        missing_loadouts=names,
        loadout_block_seq=_LOADOUT_BLOCK_SEQ,
    )
    # Pull the dashboard to the front so the user can fix the loadouts
    # straight away — even (especially) when the game is fullscreen-focused.
    global _last_loadout_focus_ts
    _now = time.time()
    if _now - _last_loadout_focus_ts >= 5.0:
        _last_loadout_focus_ts = _now
        if _focus_bot_window():
            log.info("[LOADOUT] dashboard window brought to front (loadouts not set)")


def _play_loadout(slot: str, label: str) -> bool:
    """F4 loadout select for a dashboard slot (1-6). Skip if none."""
    slot = _loadout_slot(slot)
    if slot == "none":
        log.info(f"[LOADOUT] {label}: None — skipping")
        return True
    log.info(f"[LOADOUT] {label}: slot {slot}")
    _console_status("LOADOUT", f"{label.capitalize()} loadout {slot}")
    _freeze_stone(True)
    try:
        ok = bool(_select_loadout_ui(int(slot)))
    finally:
        _freeze_stone(False)
    if not ok:
        log.warning(f"[LOADOUT] {label}: slot {slot} failed")
        if not _KILLED:
            _rec_set_failure(f"redo_limit:loadout_{slot}")
        return False
    return True


def _apply_fresh_start_loadout() -> bool:
    """F8/Start only: put the bot on the loadout this mode should begin with."""
    try:
        from dashboard import get_state as _ds_lo
        snap = _ds_lo()
    except Exception:
        snap = {}
    import config as _cfg_lo
    mode = str(snap.get("bot_mode") or "rebirth").strip().lower()
    if mode in ("kraken", "zytos", "delve"):
        slot = _loadout_slot(getattr(_cfg_lo, "BOSS_FIGHT_A1_LOADOUT_FIGHTING", "none"))
        log.info("[LOADOUT] fresh start → Fighting")
        return _play_loadout(slot, "fighting")
    if mode == "crater":
        slot = _loadout_slot(getattr(_cfg_lo, "CRATER_LOADOUT_METEOR_REWARDS", "none"))
        log.info("[LOADOUT] fresh start → Meteor Rewards")
        return _play_loadout(slot, "Meteor Rewards")
    if mode == "farm_meteor":
        slot = _loadout_slot(getattr(_cfg_lo, "CRATER_LOADOUT_METEOR_REWARDS", "none"))
        if slot == "none":
            slot = _loadout_slot(getattr(_cfg_lo, "FARM_METEOR_LOADOUT", "none"))
        log.info("[LOADOUT] fresh start → Meteor Rewards")
        return _play_loadout(slot, "Meteor Rewards")
    slot = _loadout_slot(getattr(_cfg_lo, "BOSS_FIGHT_A1_LOADOUT_FARMING", "none"))
    log.info("[LOADOUT] fresh start → Farming")
    return _play_loadout(slot, "farming")


def _run_boss_fight_a1() -> bool:
    """Full A1 boss fight sequence with looping (triggered by boss_fight_a1 toggle).

    Flow:
      1. Optional A1S1/A1S2, then grind baserock to threshold.
      2. Teleport to Area 1, grind meteor (base_secs * fight_amount).
      3. Teleport to Area 1, play dashboard Fighting loadout macro, walk to Bramble.
      4. For each fight: fight_bramble_open → fight_bramble_join → kill.
      5. After ALL fights: play dashboard Farming loadout macro once, teleport to base.
    """
    from macro_runner import _mouse_left_down, _mouse_left_up, _key_press
    import config as _cfg_boss

    # â”€â”€ Read live config values â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    baserock_threshold = float(getattr(_cfg_boss, "BOSS_FIGHT_A1_BASEROCK_THRESHOLD",   BOSS_FIGHT_A1_BASEROCK_THRESHOLD))
    meteor_grind_base  = float(getattr(_cfg_boss, "BOSS_FIGHT_A1_METEOR_GRIND_SECONDS",  BOSS_FIGHT_A1_METEOR_GRIND_SECONDS))
    loadout_fighting   = str(getattr(_cfg_boss, "BOSS_FIGHT_A1_LOADOUT_FIGHTING", BOSS_FIGHT_A1_LOADOUT_FIGHTING)).strip().lower()
    loadout_farming    = str(getattr(_cfg_boss, "BOSS_FIGHT_A1_LOADOUT_FARMING",  BOSS_FIGHT_A1_LOADOUT_FARMING)).strip().lower()
    fight_amount       = int(getattr(_cfg_boss, "BOSS_FIGHT_A1_AMOUNT", BOSS_FIGHT_A1_AMOUNT))
    fight_amount       = max(1, fight_amount)

    log.info(
        f"[BOSS_A1] Starting A1 boss fight sequence — {fight_amount} fight(s); "
        f"fighting loadout={loadout_fighting} farming loadout={loadout_farming}"
    )
    _console_status("BOSS FIGHT", f"Starting ({fight_amount} fight{'s' if fight_amount>1 else ''})")

    # â”€â”€ Determine run_mode â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from dashboard import get_state as _ds_boss
    _ds_b = _ds_boss()
    run_mode = _normalize_start_mode(_ds_b.get("run_mode", "a1s1"))

    _set_stage("boss_a1_baserock")

    # â”€â”€ Pre-fight: A1S1/A1S2 stages if applicable â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if run_mode in ("a1s1", "a1s2"):
        stages_to_do = [1, 2] if run_mode == "a1s1" else [2]
        for stage in stages_to_do:
            if _KILLED or _STONE_LOST:
                return False
            cur_s = _read_stone_checked(
                f"[BOSS_A1] A1S{stage} pre-check",
                attempts=6, delay=0.15, min_reads=2,
                min_expected=_entry_threshold(1, stage),
                fallback_to_last_if_plausible=True,
            )
            exit_t = _exit_threshold(1, stage)
            if cur_s is not None and cur_s >= exit_t:
                log.info(f"[BOSS_A1] A1S{stage} skip: stone {_fmt_stone(cur_s)} >= {_fmt_stone(exit_t)}")
                continue
            if not _go_to_area(1, f"(boss_a1 pre stage {stage})"):
                return False
            if not _do_stage(stage, area=1):
                return False
        if _KILLED or _STONE_LOST:
            return False

    # â”€â”€ Step 1: grind baserock (skip if already at threshold) â”€
    _cur_stone = _read_stone_checked(
        "[BOSS_A1] pre-baserock check",
        attempts=6, delay=0.15, min_reads=2,
        min_expected=None,
        fallback_to_last_if_plausible=True,
    )
    _needs_baserock = (_cur_stone is None) or (_cur_stone < baserock_threshold)
    if _needs_baserock:
        log.info(f"[BOSS_A1] Grinding baserock to {_fmt_stone(baserock_threshold)} (have {_fmt_stone(_cur_stone)})")
        _console_status("BOSS FIGHT", "Grinding Baserock")
        if not _do_base_rock(target_stone=baserock_threshold):
            return False
        if _KILLED or _STONE_LOST:
            return False
    else:
        log.info(f"[BOSS_A1] Baserock skip: stone {_fmt_stone(_cur_stone)} >= {_fmt_stone(baserock_threshold)}")
        _console_status("BOSS FIGHT", "Grinding Baserock")

    # â”€â”€ Helper: do one kill cycle on the bramble boss â”€â”€â”€â”€â”€â”€â”€â”€
    def _do_bramble_kill(fight_num: int) -> bool:
        """Press 1, wait 1s, hold LMB until healthbar gone, wait 5s, release."""
        poll_s             = 0.1
        reassert_s         = 0.5   # re-assert LMB every 0.5s to be safe
        post_kill_wait_s   = 5.0   # flat wait after bar disappears before releasing
        hb_timeout_s       = 120.0 # safety cap â€” release LMB after 2 min no matter what

        import config as _cfg_fight
        weapon = str(getattr(_cfg_fight, "WEAPON_1_BINDING", "1") or "1")
        log.info(f"[BOSS_A1] Fight {fight_num}: pressing {weapon!r} to equip gun")
        try:
            if not trigger_binding_action(weapon, hold_ms=50):
                _key_press(0x31, hold_ms=50)
        except Exception as e:
            log.warning(f"[BOSS_A1] Fight {fight_num}: SendInput KEY_PRESS {weapon!r} failed: {e}")
        time.sleep(0.1)
        _console_status("FIGHTING", "Bramble Boss")
        log.info(f"[BOSS_A1] Fight {fight_num}: waiting 1s then holding LMB via SendInput — watching healthbar")
        time.sleep(1.0)
        if _KILLED:
            return False

        try:
            _mouse_left_down()
        except Exception as e:
            log.warning(f"[BOSS_A1] Fight {fight_num}: SendInput LMB down failed: {e}")
            return False
        shooting = True
        fight_start   = time.time()
        next_reassert = fight_start + reassert_s
        hb_seen_once  = False
        hb_gone_at    = None

        try:
            while not _KILLED:
                now = time.time()

                # Safety timeout â€” should never hit this but prevents infinite hang
                if now - fight_start >= hb_timeout_s:
                    log.warning(f"[BOSS_A1] Fight {fight_num}: safety timeout after {hb_timeout_s:.0f}s â€” releasing LMB")
                    break

                # Re-assert LMB regularly
                if now >= next_reassert:
                    try:
                        _mouse_left_down()
                    except Exception as e:
                        log.debug(f"[BOSS_A1] Fight {fight_num}: SendInput LMB reassert failed: {e}")
                    next_reassert = now + reassert_s

                # Healthbar check
                hb_seen = kraken_health_bar_seen()
                if hb_gone_at is None:
                    if hb_seen:
                        hb_seen_once = True
                    elif hb_seen_once:
                        # Bar just disappeared â€” boss dead
                        hb_gone_at = now
                        log.info(f"[BOSS_A1] Fight {fight_num}: healthbar gone after {now - fight_start:.1f}s â€” waiting {post_kill_wait_s:.0f}s")
                        _console_status("FIGHTING", "Bramble Boss")
                else:
                    # Waiting post-kill
                    if now - hb_gone_at >= post_kill_wait_s:
                        log.info(f"[BOSS_A1] Fight {fight_num}: post-kill wait done â€” boss confirmed dead")
                        break

                # Stone HUD is hidden in the arena — do not abort the fight
                # if the watcher somehow still fires. User stop (_KILLED) still aborts.

                time.sleep(poll_s)
        finally:
            if shooting:
                try:
                    _mouse_left_up()
                except Exception:
                    pass
                shooting = False

        if _KILLED:
            return False
        log.info(f"[BOSS_A1] Fight {fight_num}: kill complete")
        return True

    def _select_loadout(slot: str, label: str) -> bool:
        return _play_loadout(slot, label)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  STEP 1: Single meteor grind (base_secs Ã— fight_amount)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    meteor_secs = meteor_grind_base * fight_amount
    log.info(f"[BOSS_A1] Teleporting to Area 1 for meteor grind ({meteor_secs:.0f}s total)")
    _console_status("NAVIGATING", "Area 1 â€” Meteor")
    _tp_ok = _builtin_teleport_safe("area1", attempts=3, wait_seconds=3.5)
    if not _tp_ok:
        log.warning("[BOSS_A1] Area 1 teleport failed (meteor)")
        _rec_set_failure("boss_a1_tp_area1_failed")
        return False
    _mark_area_unlocked(1, "boss_a1_f4")
    if _KILLED or _STONE_LOST:
        return False

    log.info("[BOSS_A1] Running area1_to_meteor macro")
    _console_status("NAVIGATING", "Area 1 â€” Meteor")
    if not _run_macro("area1_to_meteor"):
        log.warning("[BOSS_A1] area1_to_meteor macro failed")
        _rec_set_failure("boss_a1_macro_area1_to_meteor_failed")
        return False
    if _KILLED or _STONE_LOST:
        return False

    log.info(f"[BOSS_A1] Grinding A1 meteor for {meteor_secs:.0f}s ({meteor_grind_base:.0f}s Ã— {fight_amount} fights)")
    _console_status("FARMING", f"A1 Meteor ({meteor_secs:.0f}s)")
    _run_hit_macro("meteor_hit", wait=False)
    _meteor_end = time.time() + meteor_secs
    while time.time() < _meteor_end:
        if _KILLED or _STONE_LOST:
            stop_macro()
            return False
        time.sleep(0.1)
    stop_macro()
    time.sleep(0.3)
    if _KILLED or _STONE_LOST:
        return False


    # ══════════════════════════════════════════════════════
    #  STEP 2: Fighting loadout from Config > Boss Fight
    #  Play select_loadout_<N>.macro BEFORE walking to Bramble
    #  so the fight is entered already on the fighting slot.
    #  fight_bramble_join only presses JOIN — it does not click
    #  a hardcoded loadout (that always hit slot 1).
    # ══════════════════════════════════════════════════════
    #  STEP 3+: Bramble nav + fight loop
    #           Stone watcher suppressed for entire block
    # ══════════════════════════════════════════════════════
    # Stone HUD is hidden inside boss arena and all fight menus.
    # Suppress the watcher from here through the last kill.
    _freeze_stone(True)
    log.debug("[BOSS_A1] Stone watcher suppressed from bramble approach through all fights")
    try:
        log.info("[BOSS_A1] Teleporting to Area 1 for bramble approach")
        _console_status("NAVIGATING", "Bramble Boss")
        _tp_ok2 = _builtin_teleport_safe("area1", attempts=3, wait_seconds=3.5)
        if not _tp_ok2:
            log.warning("[BOSS_A1] Area 1 teleport failed (bramble)")
            _rec_set_failure("boss_a1_tp_area1_before_bramble_failed")
            return False
        if _KILLED:
            return False

        log.info(
            f"[BOSS_A1] Selecting fighting loadout before Bramble "
            f"(dashboard slot {loadout_fighting})"
        )
        if not _select_loadout(loadout_fighting, "fighting"):
            log.warning("[BOSS_A1] Fighting loadout select failed")
            _rec_set_failure("boss_a1_loadout_fighting_failed")
            return False
        if _KILLED:
            return False

        log.info("[BOSS_A1] Running area1_to_bramble macro")
        _console_status("NAVIGATING", "Bramble Boss")
        if not _run_macro("area1_to_bramble"):
            log.warning("[BOSS_A1] area1_to_bramble macro failed")
            _rec_set_failure("boss_a1_macro_area1_to_bramble_failed")
            return False
        if _KILLED:
            return False

        # -- Fight loop: fight_bramble_open + join + kill x fight_amount --
        for fight_num in range(1, fight_amount + 1):
            if _KILLED:
                return False

            # Step 1: Walk up and open the boss menu (F4+E)
            log.info(f"[BOSS_A1] Fight {fight_num}/{fight_amount}: Opening boss menu (fight_bramble_open)")
            _console_status("NAVIGATING", "Bramble Boss")
            if not _run_macro("fight_bramble_open"):
                log.warning(f"[BOSS_A1] fight_bramble_open macro failed on fight {fight_num}")
                _rec_set_failure(f"boss_a1_macro_fight_bramble_open_failed_fight{fight_num}")
                return False
            if _KILLED:
                return False

            # Step 2: OCR the boss-card mode (Solo/Normal/Hard/Ex) and
            # click the HARD pill until the configured mode is showing.
            # Same setting is used by Zytos. Kraken is Solo-only.
            log.info(f"[BOSS_A1] Fight {fight_num}/{fight_amount}: selecting Bramble mode")
            if not _select_bramble_fight_mode():
                log.warning(f"[BOSS_A1] Bramble mode select failed on fight {fight_num} — joining anyway")
            if _KILLED:
                return False

            # Step 3: Press JOIN x2. Loadout is already the fighting slot
            # from select_loadout_<N>.macro above — join must not click a slot.
            log.info(f"[BOSS_A1] Fight {fight_num}/{fight_amount}: Joining boss (fight_bramble_join)")
            _console_status("NAVIGATING", "Bramble Boss")
            try:
                from net_guard import set_path_redo as _set_bramble_redo
                _set_bramble_redo(False)
            except Exception:
                pass
            try:
                if not _run_macro("fight_bramble_join"):
                    log.warning(f"[BOSS_A1] fight_bramble_join macro failed on fight {fight_num}")
                    _rec_set_failure(f"boss_a1_macro_fight_bramble_join_failed_fight{fight_num}")
                    return False
                if _KILLED:
                    return False
                if not _do_bramble_kill(fight_num):
                    return False
            finally:
                try:
                    from net_guard import set_path_redo as _set_bramble_redo
                    _set_bramble_redo(True)
                except Exception:
                    pass
            if _KILLED:
                return False

        # Farming loadout once, after every fight is done — never per-kill
        # (that was playing it twice: post-last-kill + post-loop restore).
        if not _KILLED:
            log.info(
                f"[BOSS_A1] All fights done — restoring farming loadout "
                f"(dashboard slot {loadout_farming})"
            )
            _console_status("BOSS FIGHT", "Restoring farming loadout")
            if not _select_loadout(loadout_farming, "farming"):
                log.warning("[BOSS_A1] Farming loadout restore failed — continuing anyway")

    finally:
        _freeze_stone(False)
        log.debug("[BOSS_A1] Stone watcher re-enabled after boss fight sequence")

    if _KILLED:
        return False

    log.info(f"[BOSS_A1] All {fight_amount} fight(s) complete â€” teleporting to base")
    _console_status("BOSS FIGHT", "Complete")
    if not _teleport_to_base():
        return False

    log.info("[BOSS_A1] A1 Boss Fight sequence complete")
    return True

def _run_progression_cycle(start_mode: str) -> bool:
    start_mode = _normalize_start_mode(start_mode)

    # â”€â”€ Boss Fight A1 gate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # When enabled: always grind baserock to e33 first (unless run_mode is a1s1/a1s2,
    # in which case those two stages happen first inside _run_boss_fight_a1).
    # After the fight, resume normal progression from the correct start point.
    from dashboard import get_state as _ds_bfa1
    _ds_bfa1_snap = _ds_bfa1()
    _boss_fight_a1_enabled = bool(_ds_bfa1_snap.get("boss_fight_a1", False))
    _missing_lo = missing_required_loadouts(
        bot_mode="rebirth",
        run_mode=start_mode,
        boss_fight_a1=_boss_fight_a1_enabled,
    )
    if _missing_lo:
        _block_for_missing_loadouts(_missing_lo)
        return False
    if _boss_fight_a1_enabled:
        log.info("[BOSS_A1] Boss Fight A1 ENABLED â€” running fight sequence")
        if not _run_boss_fight_a1():
            return False
        if _KILLED or _STONE_LOST:
            return False
        # After boss fight we are back at base with stone intact â€”
        # fall through to normal progression so it skips stages already met.
    else:
        log.info("[BOSS_A1] Boss Fight A1 DISABLED â€” skipping")

    if start_mode == "a5meteor":
        # Explicit meteor run uses the Area6-threshold shortcut pipeline.
        return _run_meteor_shortcut_cycle()

    ordered = [f"a{a}s{s}" for a in range(1, 6) for s in range(1, 5)]
    precheck_stone_cache: float | None = None
    start_idx = ordered.index(start_mode)

    # Only Area 1 Stage 1 is allowed to start without baserock, because its
    # entry threshold is zero. Any later selected start must prove the current
    # stone already meets that entry threshold before the bot teleports there.
    if start_idx > 0:
        start_area = int(start_mode[1])
        start_stage = int(start_mode[3])
        start_entry = _entry_threshold(start_area, start_stage)
        start_cur = _read_stone_checked(
            f"[START GATE] A{start_area}S{start_stage}",
            attempts=8,
            delay=0.15,
            min_reads=3,
            min_expected=start_entry,
            fallback_to_last_if_plausible=True,
        )
        if start_cur is not None and start_cur >= start_entry:
            log.info(
                f"[START GATE] A{start_area}S{start_stage}: stone {_fmt_stone(start_cur)} "
                f">= entry {_fmt_stone(start_entry)} - skipping baserock"
            )
            precheck_stone_cache = start_cur
        else:
            log.warning(
                f"[START GATE] A{start_area}S{start_stage}: "
                f"stone {_fmt_stone(start_cur)} below entry {_fmt_stone(start_entry)} "
                f"- farming baserock first"
            )
            if not _do_base_rock(target_stone=start_entry):
                return False
            if _last_live_stone is not None and _last_live_stone >= start_entry:
                precheck_stone_cache = _last_live_stone

    points = ordered[start_idx:] + ["a5meteor"]

    for point in points:
        if _KILLED or _STONE_LOST:
            return False

        if point == "a5meteor":
            _set_stage("meteor")
            if not _go_to_area(5, "(meteor)"):
                return False

            _a5_stone_meteor = _read_stone_checked(
                "[A5 CHECK] Meteor",
                attempts=7,
                delay=0.16,
                min_reads=2,
                min_expected=STONE_FOR_METEOR,
                fallback_to_last_if_plausible=True,
            )
            _METEOR_FALLBACK_MAX = 3
            for _fb_round in range(_METEOR_FALLBACK_MAX):
                if _a5_stone_meteor is None or _a5_stone_meteor >= STONE_FOR_METEOR:
                    break
                _entry_map = {1: STONE_FOR_A5_STAGE1, 2: STONE_FOR_A5_STAGE2, 3: STONE_FOR_A5_STAGE3, 4: STONE_FOR_A5_STAGE4}
                _fallback_m = None
                for _fb_num in [4, 3, 2, 1]:
                    if _a5_stone_meteor >= _entry_map.get(_fb_num, 0):
                        _fallback_m = _fb_num
                        break
                if _fallback_m is not None:
                    _console_status("RETRY", f"Fallback: A5 Stage {_fallback_m}", stone=_a5_stone_meteor)
                    if not _do_stage(_fallback_m, area=5):
                        return False
                    if not _go_to_area(5, f"(post-fallback meteor round {_fb_round + 1})"):
                        return False
                else:
                    if not _do_base_rock(target_stone=STONE_FOR_METEOR):
                        return False
                    if not _go_to_area(5, f"(post-fallback meteor base round {_fb_round + 1})"):
                        return False
                _a5_stone_meteor = _read_stone_checked(
                    "[A5 CHECK] Meteor after fallback",
                    attempts=7,
                    delay=0.16,
                    min_reads=2,
                    min_expected=STONE_FOR_METEOR,
                    fallback_to_last_if_plausible=True,
                )

            if not _farm_meteor_with_validation("Meteor"):
                return False
            stats.mark_step("Meteor")

            if not _teleport_to_base():
                return False

            REBIRTH_MAX_RETRIES = 3
            _set_stage("rebirth")
            rebirth_ok = False
            for _rebirth_attempt in range(1, REBIRTH_MAX_RETRIES + 1):
                ok = _do_rebirth()
                if ok:
                    stats.mark_step("Rebirth")
                    rebirth_ok = True
                    break
                if _KILLED or _STONE_LOST:
                    return False
                stats.record_error()
                log.warning(f"[REBIRTH] retry {_rebirth_attempt}/{REBIRTH_MAX_RETRIES} (meteor not broken?)")
                _A5_UNLOCKED_THIS_RUN = False
                if not _go_to_area(5, "(rebirth retry)"):
                    return False
                if not _farm_meteor_with_validation("Meteor retry"):
                    return False
                if not _teleport_to_base():
                    return False

            if not rebirth_ok:
                return False
            continue

        area = int(point[1])
        stage = int(point[3])
        _set_stage(f"a{area}s{stage}")
        entry = _entry_threshold(area, stage)
        target = _exit_threshold(area, stage)

        # Pre-check stone before any travel. Reuse a cached precheck value while we
        # are fast-skipping consecutive stages to avoid long OCR-only loops.
        if precheck_stone_cache is None:
            pre_cur = _read_stone_checked(
                f"[AREA PRECHECK] A{area}S{stage}",
                attempts=5,
                delay=0.12,
                min_reads=2,
                min_expected=entry,
                fallback_to_last_if_plausible=True,
            )
            precheck_stone_cache = pre_cur
        else:
            pre_cur = precheck_stone_cache
            log.debug(f"[AREA PRECHECK] A{area}S{stage}: using cached stone {_fmt_stone(pre_cur)}")

        if _KILLED or _STONE_LOST:
            return False

        if pre_cur is not None and pre_cur >= target:
            log.info(
                f"[AREA CHECK] A{area}S{stage} pre-skip: stone {_fmt_stone(pre_cur)} >= {_fmt_stone(target)}"
            )
            continue

        # If cache says we're below target, do one fresh confirmation before travel.
        pre_cur_confirm = _read_stone_checked(
            f"[AREA PRECHECK CONFIRM] A{area}S{stage}",
            attempts=6,
            delay=0.12,
            min_reads=3,
            min_expected=entry,
            fallback_to_last_if_plausible=True,
        )
        if pre_cur_confirm is not None:
            pre_cur = pre_cur_confirm
            precheck_stone_cache = pre_cur_confirm
            if pre_cur >= target:
                log.info(
                    f"[AREA CHECK] A{area}S{stage} pre-skip: stone {_fmt_stone(pre_cur)} >= {_fmt_stone(target)}"
                )
                continue

        # From here we move/farm, so cached precheck value is no longer trustworthy.
        precheck_stone_cache = None

        if _stage_shortcut_macro(area, stage) is None:
            if not _go_to_area(area, f"(a{area}s{stage})"):
                return False
        else:
            _console_status("NAVIGATING", f"A{area}S{stage} shortcut")

        cur = _read_stone_checked(
            f"[AREA CHECK] A{area}S{stage}",
            attempts=10,
            delay=0.18,
            min_reads=4,
            min_expected=entry,
            fallback_to_last_if_plausible=True,
        )
        if cur is None and pre_cur is not None:
            cur = pre_cur

        if cur is not None and cur >= target:
            log.info(f"[AREA CHECK] A{area}S{stage} skipped: stone {_fmt_stone(cur)} >= {_fmt_stone(target)}")
            continue

        for round_idx in range(3):
            if cur is None or cur >= entry:
                break
            prev = _previous_stage_point(area, stage)
            if prev is None:
                break
            pa, ps = prev
            log.warning(
                f"[AREA CHECK] A{area}S{stage} round {round_idx+1}/3 below entry "
                f"({_fmt_stone(cur)} < {_fmt_stone(entry)}) -> fallback A{pa}S{ps}"
            )
            if not _go_to_area(pa, f"(fallback A{pa}S{ps})"):
                return False
            if not _do_stage(ps, area=pa):
                return False
            if not _go_to_area(area, f"(return A{area}S{stage})"):
                return False
            cur = _read_stone_checked(
                f"[AREA CHECK] A{area}S{stage} after fallback",
                attempts=10,
                delay=0.18,
                min_reads=4,
                min_expected=entry,
                fallback_to_last_if_plausible=True,
            )

        if not _do_stage(stage, area=area):
            return False
        if _last_live_stone is not None and _last_live_stone >= target:
            precheck_stone_cache = _last_live_stone

    return True



def _do_stage(stage: int, area: int = 5) -> bool:
    """Navigate to a stage rock and farm until threshold. Returns True on success."""
    global _last_live_stone
    nav_macro = _stage_shortcut_macro(area, stage) or _stage_nav_macro(area, stage)
    target = _exit_threshold(area, stage)
    stage_label = f"A{area}S{stage}"

    _console_status("NAVIGATING", f"{stage_label} Rock")
    r = _nav_or_redo(nav_macro)
    if r == "kill":
        return False
    if r == "fail":
        return False
    _stage_net_redo = (r == "redo")
    if _stage_net_redo:
        log.warning(f"[NET] lag during {stage_label} walk — redo path")
    if _KILLED or _STONE_LOST:
        return False

    if _auto_strength_enabled():
        enable_auto_strength()
        set_overlay(auto_str=True)

    manual_mode = _manual_strength_enabled()
    auto_stage_threshold_timeout = max(0.0, float(AUTO_ROCK_MAX_GRIND_SECONDS))
    if manual_mode:
        auto_stage_threshold_timeout = max(
            30.0,
            float(MANUAL_STR_MAX_SECONDS),
            float(MANUAL_STR_NO_STRENGTH_TIMEOUT),
        )
    elif auto_stage_threshold_timeout <= 0:
        auto_stage_threshold_timeout = 30.0

    _manual_handle = None
    if not _stage_net_redo:
        if _run_hit_macro("rock_hit", wait=False) is None:
            return False
        _manual_handle = (
            _start_manual_strength_live(f"{stage_label}")
            if manual_mode and not (_KILLED or _STONE_LOST)
            else None
        )

    topup  = STAGE_TOPUP_SECONDS.get(stage, 10)
    timeout = STONE_STALL_TIMEOUT + topup + 60

    start_stone = _read_stone_live() or 0
    _console_status("FARMING", f"{stage_label} Rock", stone=start_stone)

    # Pre-check: if stone already at or above threshold before even starting the loop,
    # skip farming entirely â€” this prevents false no_gain_timeout when OCR reads
    # an already-sufficient stone value on the very first sample (e.g. S4 double-redo bug).
    if start_stone and start_stone >= target:
        log.info(f"[STAGE {stage}] stone already at threshold on entry ({start_stone:.2e} >= {target:.2e}) â€” skipping farm")
        _stop_manual_strength_live(_manual_handle)
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        _mark_current_stage_point(area, stage)
        return True


    NO_GAIN_TIMEOUT   = _manual_hud_stall_seconds() if manual_mode else 30
    STAGE_ROCK_RETRIES = _route_redo_limit()

    ok = False
    cur = start_stone
    _first_manual_nohit = bool(manual_mode and _manual_handle is None and not (_KILLED or _STONE_LOST))
    for _sr_attempt in range(1, STAGE_ROCK_RETRIES + 1):
        if _sr_attempt == 1 and _first_manual_nohit:
            _stop_manual_strength_live(_manual_handle)
            _close_hit_macro()
            stop_macro()
            _stop_drill_loop()
            log.warning(f"[{stage_label}] no hit confirmed before manual menu open - redoing route")
            continue
        if _sr_attempt > 1 or _stage_net_redo:
            _stage_net_redo = False
            # Re-navigate: base ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ A5 (or fast-tp) ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ stage rock
            if _KILLED or _STONE_LOST:
                return False
            _console_status("RETRY", f"{stage_label} Rock")
            # A5 already unlocked this run ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ _go_to_area5 uses fast-tp, no base trip needed
            if not _go_to_area(area, f"({stage_label} retry)"):
                log.warning(f"Stage {stage} retry: failed to reach A{area}")
                return False
            _console_status("NAVIGATING", f"{stage_label} Rock")
            retry_nav_macro = _stage_nav_macro(area, stage)
            rr = _nav_or_redo(retry_nav_macro)
            if rr == "kill":
                return False
            if rr == "fail":
                return False
            if rr == "redo":
                log.warning(f"[NET] lag during {stage_label} retry walk — redo path")
                continue
            if _KILLED or _STONE_LOST:
                return False
            if _auto_strength_enabled():
                enable_auto_strength()
                set_overlay(auto_str=True)
            if _run_hit_macro("rock_hit", wait=False) is None:
                return False
            _manual_handle = (
                _start_manual_strength_live(f"{stage_label} retry")
                if manual_mode and not (_KILLED or _STONE_LOST)
                else None
            )
            if manual_mode and _manual_handle is None and not (_KILLED or _STONE_LOST):
                _stop_manual_strength_live(_manual_handle)
                _close_hit_macro()
                stop_macro()
                _stop_drill_loop()
                log.warning(f"[{stage_label}] retry no-hit before manual menu (attempt {_sr_attempt})")
                continue
            start_stone = _read_stone_live() or cur
            _console_status("FARMING", f"{stage_label} Rock", stone=start_stone)

        # Poll stone ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â no_gain_timeout fires any time stone stops gaining
        # (from the very first second, not just after initial movement)
        ok, cur = _wait_stone_change(
            start_stone, target, timeout,
            goal=f"{stage_label}",
            smart_timeout=SMART_FAILURE_TIMEOUT,
            no_gain_timeout=NO_GAIN_TIMEOUT,
            threshold_timeout=auto_stage_threshold_timeout,
            manual_strength_watch=_make_manual_strength_watchdog(stage_label) if _manual_strength_enabled() else None,
        )

        if ok:
            # Threshold confirmed by _wait_stone_change ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stop immediately, no extra confirms or blind mine.
            manual_mode = _manual_strength_enabled()
            log.debug(f"[STAGE {stage}] threshold confirmed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stopping immediately")
            _stop_manual_strength_live(_manual_handle)
            _close_hit_macro()
            stop_macro()
            _stop_drill_loop()
            if not manual_mode:
                cur = _read_stone_live() or cur
            if cur is not None:
                _last_live_stone = cur
            break  # success

        _stop_manual_strength_live(_manual_handle)
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()

        log.warning(f"Stage {stage} farming failed (attempt {_sr_attempt}/{STAGE_ROCK_RETRIES})")
        # continue retry loop

    if not ok:
        log.warning(f"Stage {stage}: all {STAGE_ROCK_RETRIES} attempts failed")
        _rec_set_failure(f"redo_limit:{stage_label}")
        return False

    stats.mark_stage_unlocked(stage, cur)

    if _manual_strength_enabled():
        cur = _manual_post_threshold_topup(stage_label, target, cur, "rock_hit")
        _console_status("FARMING", f"{stage_label} Rock", stone=cur)
        _mark_current_stage_point(area, stage)
        return True


    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Topup phase: always runs ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 3s blind hit then poll to target*1.01 ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    # Always disable auto_str, hit for 3s, then poll every 1s until target*1.01.
    # No skip guard ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â topup always runs regardless of how far stone overshot.
    topup_target = target * 1.01
    import math as _math
    if not _math.isfinite(topup_target):
        topup_target = target
    cur = _read_stone_live(update_last=False, check_glitch=False) or cur
    if topup > 0:
        if _auto_strength_enabled():
            disable_auto_strength()
            set_overlay(auto_str=False)
        _console_status("FARMING", f"Stage {stage} Rock ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â topup")
        if _run_hit_macro("rock_hit", wait=False, skip_center=True) is None:
            return False
        _manual_topup_handle = _start_manual_strength_live(f"{stage_label} topup")
        _topup_deadline = time.time() + TOPUP_TIMEOUT
        log.debug(f"[STAGE {stage}] topup - up to 3s warmup hit then polling to {_fmt_stone(topup_target)} (max {TOPUP_TIMEOUT}s)")
        _blind_deadline = time.time() + 3.0
        while time.time() < _blind_deadline and not (_KILLED or _STONE_LOST):
            _probe = _read_stone_live(update_last=False, check_glitch=False)
            if _probe is not None and _probe >= topup_target:
                break
            _wait_polling(0.25, f"Stage {stage} topup - blind hit", freeze=False)
        # Re-read after warmup, then poll until threshold met or deadline
        # FIX: close the manual strength window before the precheck so _read_stone_live
        # reads from the real HUD instead of the stale upgrade-window display.
        _stop_manual_strength_live(_manual_topup_handle)
        _manual_topup_handle = None
        _close_hit_macro()
        stop_macro()  # stop hit macro briefly; restart below if still needed
        _stop_drill_loop()
        time.sleep(0.3)  # allow menu to close and HUD to settle
        cur = _read_stone_checked(f"[STAGE {stage}] topup precheck", attempts=8, delay=0.15, min_reads=3) or cur
        if cur < topup_target:
            while time.time() < _topup_deadline:
                if _KILLED or _STONE_LOST:
                    break
                c = _read_stone_live(update_last=False, check_glitch=False)
                if c is not None:
                    glitch_reason = _stone_glitch_reason(c, cur)
                    if glitch_reason:
                        log.debug(f"[STAGE {stage}] topup OCR {glitch_reason} glitch ignored: {c} (cur={cur})")
                        time.sleep(0.1)
                        continue
                    if c >= topup_target:
                        confirmed, confirmed_cur = _confirm_stone_at_least(
                            topup_target,
                            f"[STAGE {stage}] topup",
                            first_value=c,
                            attempts=5,
                            required_hits=2,
                            delay=0.12,
                        )
                        if confirmed:
                            cur = confirmed_cur or c
                            log.debug(f"[STAGE {stage}] topup done ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stone={_fmt_stone(cur)}")
                            break
                        if confirmed_cur is not None:
                            c = confirmed_cur
                        else:
                            time.sleep(0.1)
                            continue
                    _last_live_stone = c
                    set_overlay(stone=c)
                    _dash_update(cur_stone=c)
                    cur = c
                time.sleep(0.1)  # v1.2: reduced from 1.0s ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â faster topup exit
            else:
                log.debug(f"[STAGE {stage}] topup timeout ({TOPUP_TIMEOUT}s) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â continuing with stone={_fmt_stone(cur)}")
        else:
            log.debug(f"[STAGE {stage}] topup: already at {_fmt_stone(cur)} >= {_fmt_stone(topup_target)} after blind hit")
        if _manual_topup_handle is not None:
            _stop_manual_strength_live(_manual_topup_handle)
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        _final_cur = _read_stone_checked(f"[STAGE {stage}] topup final", attempts=10, delay=0.15, min_reads=4)
        if _final_cur is not None:
            cur = max(cur or 0, _final_cur)
        set_overlay(stone=cur)

    if cur is None or cur < target:
        log.warning(f"[STAGE {stage}] final stone below target ({_fmt_stone(cur)} < {_fmt_stone(target)})")
        return False
    _last_live_stone = cur
    _console_status("FARMING", f"{stage_label} Rock", stone=cur)
    _mark_current_stage_point(area, stage)
    return True


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Meteor farming ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _wait_meteor_broken(
    max_seconds: float = 10.0,
    goal: str = "Meteor",
    *,
    start_stone=None,
    seen_votes: int = 0,
    need_gain: bool = True,
) -> bool:
    """Watch the bar from the first swing until first break.

    Bar is sampled *before* meteor_hit starts (seen_votes) and every tick
    until we stop. Stone-gain fail (not hitting) returns False so the route
    can redo. Bar-gone / grind-cap return True.
    """
    import config as _cfg_meteor

    max_seconds = min(10.0, max(1.0, float(max_seconds)))
    deadline = time.time() + max_seconds
    last_log = 0.0
    broken_votes = 0
    seen_red_votes = max(0, int(seen_votes))
    broken_vote_need = max(2, int(getattr(_cfg_meteor, "METEOR_BROKEN_VOTES", 2)))
    stall_need = float(getattr(_cfg_meteor, "METEOR_STONE_STALL_SECONDS", 1.5))
    gain_window = float(getattr(_cfg_meteor, "METEOR_INITIAL_GAIN_SECONDS", 8.0))
    last_stone = start_stone
    stall_since = None
    gained = False
    t0 = time.time()
    logged_first_seen = seen_red_votes > 0
    hb_pct = 0.0
    hb_span = 0

    while time.time() < deadline:
        if _KILLED or _STONE_LOST:
            return False
        if _peek_net_redo():
            return False
        hb_seen, hb_pct, hb_span = meteor_health_bar_metrics()

        if hb_seen:
            seen_red_votes += 1
            broken_votes = 0
            stall_since = None
            if not logged_first_seen:
                log.info(
                    f"[METEOR] health bar seen  color={hb_pct:.1%} span={hb_span}px"
                )
                logged_first_seen = True
        elif seen_red_votes > 0:
            broken_votes += 1

        cur = _read_stone_live(update_last=False, check_glitch=False)
        if cur is not None:
            if last_stone is None or cur > float(last_stone) * 1.00001:
                if last_stone is not None and cur > float(last_stone) * 1.00001:
                    gained = True
                last_stone = cur
                stall_since = None
            elif gained or seen_red_votes > 0:
                if stall_since is None:
                    stall_since = time.time()

        if time.time() - last_log > 1.0:
            log.debug(
                f"[METEOR] bar seen={hb_seen} color={hb_pct:.1%} span={hb_span}px "
                f"seen_votes={seen_red_votes} broken_votes={broken_votes}/{broken_vote_need} "
                f"gained={gained}"
            )
            last_log = time.time()

        if seen_red_votes > 0 and broken_votes >= broken_vote_need:
            log.info(
                f"[METEOR] broken confirmed by health bar disappearance "
                f"(last color={hb_pct:.1%} span={hb_span}px)"
            )
            return True
        if seen_red_votes > 0 and stall_since is not None and (time.time() - stall_since) >= stall_need:
            log.info(
                f"[METEOR] broken confirmed by stone stall after bar "
                f"(last color={hb_pct:.1%} span={hb_span}px)"
            )
            return True
        if seen_red_votes == 0 and gained and stall_since is not None and (time.time() - stall_since) >= stall_need:
            log.info(
                f"[METEOR] broken confirmed by stone stall "
                f"(health bar never seen, last color={hb_pct:.1%} span={hb_span}px)"
            )
            return True
        if need_gain and seen_red_votes == 0 and not gained and (time.time() - t0) >= gain_window:
            log.warning(
                f"{goal}: no stone gain confirmed in {gain_window:.1f}s "
                f"(bar never seen, last color={hb_pct:.1%} span={hb_span}px)"
            )
            return False

        _wait_polling(0.05, goal, freeze=False)

    if seen_red_votes == 0 and need_gain and not gained:
        log.warning(f"{goal}: grind cap with no gain / no bar — redo")
        return False
    log.info(
        f"[METEOR] grind cap {max_seconds:.1f}s — assume broken "
        f"(seen_votes={seen_red_votes} broken_votes={broken_votes})"
    )
    return True


def _meteor_health_check_enabled() -> bool:
    """Fine-Tuning: Check A5 Meteor health (default on)."""
    try:
        import config as _cfg_hc
        return bool(getattr(_cfg_hc, "METEOR_HEALTH_CHECK", True))
    except Exception:
        return True


def _fixed_a5_hold_seconds() -> float:
    """Fine-Tuning: Fixed A5 hit time (seconds) as one LMB hold duration.

    0 -> a single quick 100ms tap. N >= 1 -> 200ms windup + N seconds hold
    (e.g. 1 -> 1.2s). The meteor_hit macro is NOT used on this path.
    """
    try:
        import config as _cfg_ft
        n = float(getattr(_cfg_ft, "FIXED_A5_HIT_TIME", 60))
    except Exception:
        n = 60.0
    if n <= 0:
        return 0.1
    return 0.2 + n


def _fixed_a5_single_hit(label: str) -> bool:
    """Health check OFF: one bot-controlled LMB hold, then stop.

    No meteor_hit macro, no drills, no bar/stall watching — hold for the
    fixed time, release, and the caller teleports to base + rebirths.
    """
    from macro_runner import _mouse_left_down, _mouse_left_up
    _equip_pickaxe("meteor fixed hit")
    hold = _fixed_a5_hold_seconds()
    log.info(f"[{label}] meteor health check OFF — single fixed hit: LMB hold {hold:.2f}s")
    _console_status("FARMING", label)
    _rec_log_macro("meteor_fixed_hit", "start")
    try:
        if _KILLED or _STONE_LOST:
            _rec_log_macro("meteor_fixed_hit", "error", error="killed")
            return False
        _mouse_left_down()
        _wait_polling(hold, f"{label} fixed hit", freeze=False)
    finally:
        try:
            _mouse_left_up()
        except Exception:
            pass
    _rec_log_macro("meteor_fixed_hit", "end")
    if _KILLED or _STONE_LOST:
        return False
    if _auto_strength_enabled():
        disable_auto_strength()
        set_overlay(auto_str=False)
    log.info(f"[{label}] fixed hit done — continuing to base + rebirth")
    return True


def _finish_meteor_hit(label: str) -> bool:
    """First break is done: kill meteor_hit NOW, then a short extra hold."""
    from macro_runner import _mouse_left_down, _mouse_left_up
    _close_hit_macro()
    stop_macro()
    _stop_drill_loop()
    import config as _cfg_meteor
    post = float(getattr(_cfg_meteor, "METEOR_POST_BREAK_HIT_SECONDS", 0.10))
    if post > 0 and not _KILLED and not _STONE_LOST:
        log.info(f"[{label}] red bar gone - safety hitting {post:.1f}s more")
        try:
            _mouse_left_down()
            _wait_polling(post, f"{label} finish", freeze=False)
        finally:
            try:
                _mouse_left_up()
            except Exception:
                pass
    if _KILLED or _STONE_LOST:
        return False
    if _auto_strength_enabled():
        disable_auto_strength()
        set_overlay(auto_str=False)
    return True


def _confirm_meteor_broken(goal: str = "Meteor", last_max=None) -> bool:
    """Compatibility wrapper: meteor break detection is now boss-bar method."""
    votes = 0
    for _ in range(5):
        if _KILLED or _STONE_LOST:
            return False
        if not meteor_health_bar_seen():
            votes += 1
        else:
            log.debug("[METEOR] confirm sample rejected: health bar still visible")
        if votes >= 2:
            return True
        _wait_polling(0.1, goal, freeze=False)
    return False


def _meteor_break_retry_short_circuit(label: str) -> bool:
    """Avoid re-navigating to A5 when the meteor is already broken."""
    try:
        if _confirm_meteor_broken(label):
            log.info(f"[{label}] meteor already broken on retry check - skipping A5 re-navigation")
            return True
    except Exception as e:
        log.debug(f"[{label}] meteor retry short-circuit check failed: {e}")
    return False


def _wait_initial_stone_gain(start_stone, seconds: float, goal: str, *, warn_on_fail: bool = True) -> bool:
    """Fast validator: after a hit starts, confirm stone moves before committing."""
    global _last_live_stone
    import config as _cfg_meteor
    rel_threshold = float(getattr(_cfg_meteor, "METEOR_GAIN_REL_THRESHOLD", 1.00001))
    rel_threshold = max(1.0, rel_threshold)
    min_hits = int(getattr(_cfg_meteor, "METEOR_GAIN_MIN_HITS", 2))
    min_hits = max(1, min_hits)

    deadline = time.time() + float(seconds)
    baseline = start_stone
    unknown_baseline = baseline is None or baseline <= 0
    best = start_stone
    valid_reads = 0
    gain_hits = 0
    tiny_gain_hits = 0
    tiny_gain_need = max(min_hits + 1, 3)
    while time.time() < deadline:
        if _KILLED or _STONE_LOST:
            return False
        cur = _read_stone_live(update_last=False, check_glitch=False)
        if cur is not None:
            glitch_reason = _stone_glitch_reason(cur, best)
            if glitch_reason:
                log.debug(f"[{goal}] OCR {glitch_reason} glitch ignored during gain check: {cur} (best={best})")
                time.sleep(0.1)
                continue
            _last_live_stone = cur
            valid_reads += 1
            set_overlay(stone=cur)
            _dash_update(cur_stone=cur)
            if unknown_baseline and cur > 0:
                gain_hits += 1
                if gain_hits >= min_hits:
                    log.debug(f"[{goal}] stone read confirmed after hit: {_fmt_stone(cur)}")
                    return True
            if baseline is None or baseline <= 0:
                baseline = cur
                best = cur
            elif cur >= baseline * rel_threshold or (best is not None and cur > best * rel_threshold):
                gain_hits += 1
                tiny_gain_hits = 0
                if gain_hits >= min_hits:
                    log.debug(f"[{goal}] stone gain confirmed: {_fmt_stone(baseline)} -> {_fmt_stone(cur)}")
                    return True
            elif best is not None and cur > best:
                # Fallback for weaker accounts: accept several tiny upward highs.
                tiny_gain_hits += 1
                if tiny_gain_hits >= tiny_gain_need:
                    log.debug(f"[{goal}] tiny-gain trend confirmed: {_fmt_stone(best)} -> {_fmt_stone(cur)}")
                    return True
            else:
                tiny_gain_hits = max(0, tiny_gain_hits - 1)
            if best is None or cur > best:
                best = cur
        time.sleep(0.1)
    if warn_on_fail:
        log.warning(f"{goal}: no stone gain confirmed in {seconds:.1f}s ({valid_reads} valid reads)")
    else:
        log.debug(f"{goal}: no stone gain confirmed in {seconds:.1f}s ({valid_reads} valid reads)")
    return False


def _wait_initial_stone_gain_with_grace(start_stone, seconds: float, goal: str) -> bool:
    """Initial gain check with a short grace retry to reduce false first-collect failures."""
    if _wait_initial_stone_gain(start_stone, seconds, goal, warn_on_fail=False):
        return True
    import config as _cfg_meteor
    grace = max(0.0, float(getattr(_cfg_meteor, "METEOR_INITIAL_GAIN_GRACE_SECONDS", 1.5)))
    if grace <= 0.0:
        log.warning(f"{goal}: no stone gain confirmed in {seconds:.1f}s")
        return False
    retry_start = _read_stone_live(update_last=False, check_glitch=False)
    if retry_start is None:
        retry_start = start_stone
    log.debug(f"[{goal}] initial gain not confirmed; running grace check ({grace:.1f}s)")
    return _wait_initial_stone_gain(retry_start, grace, f"{goal} grace", warn_on_fail=True)


def _farm_meteor_with_validation(label: str = "Meteor", max_retries: int | None = None) -> bool:
    """Walk to meteor, start hitting, verify stone gain, then wait for break."""
    import config as _cfg_meteor
    gain_window = float(getattr(_cfg_meteor, "METEOR_INITIAL_GAIN_SECONDS", 8.0))
    break_timeout = float(getattr(_cfg_meteor, "METEOR_BREAK_TIMEOUT_SECONDS", 10.0))
    if max_retries is None:
        max_retries = _route_redo_limit()

    for attempt in range(1, max(1, max_retries) + 1):
        if _KILLED or _STONE_LOST:
            return False
        if attempt > 1:
            _console_status("RETRY", label)
            _close_hit_macro()
            stop_macro()
            _stop_drill_loop()
            if _meteor_break_retry_short_circuit(label):
                return True
            if not _go_to_area5(f"({label} no-gain retry)"):
                return False

        _console_status("NAVIGATING", label)
        r = _nav_or_redo("area5_to_meteor")
        if r == "kill":
            return False
        if r == "fail":
            return False
        if r == "redo":
            log.warning(f"[NET] lag during {label} walk — redo meteor path")
            continue
        if _KILLED or _STONE_LOST:
            return False

        if _auto_strength_enabled():
            enable_auto_strength()
            set_overlay(auto_str=True)

        start_stone = _read_stone_live() or 0
        hb_seen, hb_pct, hb_span = meteor_health_bar_metrics()
        pre_votes = 1 if hb_seen else 0
        if hb_seen:
            log.info(f"[METEOR] health bar pre-hit  color={hb_pct:.1%} span={hb_span}px")
        if not _meteor_health_check_enabled():
            # Health check OFF: no meteor_hit macro — one fixed LMB hold, then
            # straight on (caller teleports to base + rebirths).
            return _fixed_a5_single_hit(label)
        if _run_hit_macro("meteor_hit", wait=False) is None:
            return False
        _console_status("FARMING", label, stone=start_stone)

        broken = _wait_meteor_broken(
            break_timeout, label, start_stone=start_stone, seen_votes=pre_votes
        )
        if _KILLED or _STONE_LOST:
            return False
        if not broken and _meteor_break_retry_short_circuit(label):
            broken = True
        if not broken:
            log.warning(f"[{label}] no stone gain; redoing meteor approach ({attempt}/{max_retries})")
            _close_hit_macro()
            stop_macro()
            _stop_drill_loop()
            continue
        return _finish_meteor_hit(label)

    log.warning(f"[{label}] failed after {max_retries} no-gain retries")
    _rec_set_failure("redo_limit:meteor")
    return False


def _farm_meteor_from_current_position(label: str = "Meteor Shortcut") -> bool:
    """Mine meteor from the CURRENT position using meteor_hit (no walk macro)."""
    if _KILLED or _STONE_LOST:
        return False
    import config as _cfg_meteor
    gain_window = float(getattr(_cfg_meteor, "METEOR_INITIAL_GAIN_SECONDS", 8.0))
    break_timeout = float(getattr(_cfg_meteor, "METEOR_BREAK_TIMEOUT_SECONDS", 10.0))

    if _auto_strength_enabled():
        enable_auto_strength()
        set_overlay(auto_str=True)

    start_stone = _read_stone_live() or 0
    hb_seen, hb_pct, hb_span = meteor_health_bar_metrics()
    pre_votes = 1 if hb_seen else 0
    if hb_seen:
        log.info(f"[METEOR] health bar pre-hit  color={hb_pct:.1%} span={hb_span}px")
    if not _meteor_health_check_enabled():
        # Health check OFF: no meteor_hit macro — one fixed LMB hold, then
        # straight on (caller teleports to base + rebirths).
        return _fixed_a5_single_hit(label)
    if _run_hit_macro("meteor_hit", wait=False) is None:
        return False
    _console_status("FARMING", label, stone=start_stone)

    broken = _wait_meteor_broken(
        break_timeout, label, start_stone=start_stone, seen_votes=pre_votes
    )
    if _KILLED or _STONE_LOST:
        return False
    if not broken and _meteor_break_retry_short_circuit(label):
        broken = True
    if not broken:
        log.warning(f"[{label}] no stone gain after hit start")
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        if _auto_strength_enabled():
            disable_auto_strength()
            set_overlay(auto_str=False)
        return False

    return _finish_meteor_hit(label)


def _run_meteor_shortcut_cycle() -> bool:
    """Meteor mode: baserock -> shortcut p1/p3 macros -> meteor_hit -> base -> rebirth."""
    _set_stage("base")
    _did_baserock_trip = False
    _shortcut_stone = _last_live_stone
    if _shortcut_stone is not None and float(_shortcut_stone) <= 0:
        log.info("[Meteor Shortcut] stone=0 — skip precheck, farm baserock")
        _shortcut_stone = 0.0
    else:
        _shortcut_stone = _read_stone_checked(
            "[METEOR SHORTCUT] precheck",
            attempts=3,
            delay=0.08,
            min_reads=2,
            min_expected=STONE_FOR_AREA6_SHORTCUT,
            fallback_to_last_if_plausible=False,
        )
    if _shortcut_stone is not None and _shortcut_stone >= STONE_FOR_AREA6_SHORTCUT:
        log.info(
            f"[Meteor Shortcut] precheck ok: {_fmt_stone(_shortcut_stone)} >= "
            f"{_fmt_stone(STONE_FOR_AREA6_SHORTCUT)} - skipping baserock trip"
        )
    else:
        if _shortcut_stone is None:
            log.info("[Meteor Shortcut] precheck unreadable - using baserock fallback")
        else:
            log.info(
                f"[Meteor Shortcut] precheck below threshold: {_fmt_stone(_shortcut_stone)} < "
                f"{_fmt_stone(STONE_FOR_AREA6_SHORTCUT)} - farming baserock"
            )
        if not _do_base_rock(target_stone=STONE_FOR_AREA6_SHORTCUT):
            return False
        _did_baserock_trip = True

    try:
        import config as _cfg_shortcut
        _use_shortcuts = bool(getattr(_cfg_shortcut, "USE_SHORTCUTS", True))
    except Exception:
        _use_shortcuts = False
    _direct_shortcut = bool(_use_shortcuts and _did_baserock_trip)
    if _direct_shortcut:
        log.info("[Meteor Shortcut] Use Shortcuts=ON: direct baserock -> area6 shortcut walk")
    elif _did_baserock_trip:
        log.info("[Meteor Shortcut] Use Shortcuts=OFF: teleport to base then p1")
    else:
        log.info(f"[Meteor Shortcut] shortcuts={'ON' if _use_shortcuts else 'OFF'} (no baserock trip) — base p1 route")

    # Allow more recovery attempts when meteor is temporarily unhittable on some map states.
    SHORTCUT_TRIES = _route_redo_limit()
    mined = False
    for _try in range(1, SHORTCUT_TRIES + 1):
        if _KILLED or _STONE_LOST:
            return False
        _set_stage("meteor")
        _use_direct_this_try = _direct_shortcut and _try == 1
        if not _use_direct_this_try:
            # From baserock with shortcuts OFF (and every retry): F4 back to
            # spawn first. p1 is a from-base walk — A5 from the rock stalls F4.
            if not _teleport_to_base():
                return False
        _console_status("NAVIGATING", "Meteor Shortcut")
        _p1_macro = "base_to_meteor_shortcut_p1_shortcut" if _use_direct_this_try else "base_to_meteor_shortcut_p1"
        log.info(f"[Meteor Shortcut] try {_try}/{SHORTCUT_TRIES} macro={_p1_macro}")
        r = _nav_or_redo(_p1_macro)
        if r == "kill":
            return False
        if r == "fail":
            log.warning(
                "[Meteor Shortcut] P1 failed — retry from base "
                f"(try {_try}/{SHORTCUT_TRIES})"
            )
            _direct_shortcut = False
            continue
        if r == "redo":
            log.warning("[NET] lag during meteor shortcut p1 — redo path")
            _direct_shortcut = False
            continue
        if not _builtin_teleport_safe("area5", attempts=1, wait_seconds=4.0):
            # One F4 open. Dest button missing = A6 shortcut didn't unlock A5.
            # Do not re-open F4. Next loop teleports to base and redoes P1.
            log.warning(
                "[Meteor Shortcut] area5 dest button missing — redo P1 from base "
                f"(try {_try}/{SHORTCUT_TRIES})"
            )
            _direct_shortcut = False
            continue
        _mark_area5_unlocked_if_visible("builtin_teleport_area5", attempts=8, delay=0.25)
        r = _nav_or_redo("base_to_meteor_shortcut_p3")
        if r == "kill":
            return False
        if r == "fail":
            return False
        if r == "redo":
            log.warning("[NET] lag during meteor shortcut p3 — redo path")
            continue
        _mark_area5_unlocked_if_visible("meteor_shortcut_p3", attempts=8, delay=0.25)
        if _KILLED or _STONE_LOST:
            return False
        if _farm_meteor_from_current_position("Meteor Shortcut"):
            _mark_area5_unlocked_if_visible("meteor_shortcut_farm", attempts=1, delay=0.0)
            mined = True
            stats.mark_step("Meteor")
            break
        stats.record_error()
        log.warning(f"[Meteor Shortcut] attempt {_try}/{SHORTCUT_TRIES} failed - retrying shortcut")

    if not mined:
        _rec_set_failure("redo_limit:meteor_shortcut")
        return False

    if not _at_base:
        if not _teleport_to_base():
            return False

    REBIRTH_MAX_RETRIES = 3
    _set_stage("rebirth")
    for _rebirth_attempt in range(1, REBIRTH_MAX_RETRIES + 1):
        if _do_rebirth():
            stats.mark_step("Rebirth")
            return True
        if _KILLED or _STONE_LOST:
            return False
        stats.record_error()
        log.warning(f"[Meteor Shortcut] rebirth retry {_rebirth_attempt}/{REBIRTH_MAX_RETRIES}")
        if not _at_base:
            if not _teleport_to_base():
                return False
        _console_status("NAVIGATING", "Meteor Shortcut Retry")
        r = _nav_or_redo("base_to_meteor_shortcut_p1")
        if r == "kill":
            return False
        if r in ("fail", "redo"):
            if r == "fail":
                return False
            log.warning("[NET] lag during meteor shortcut retry — redo path")
            continue
        if not _builtin_teleport_safe("area5", attempts=10, wait_seconds=4.0):
            # Same as above: a missing A5 button means the shortcut P1 didn't
            # actually unlock Area 5. Don't kill the run — re-do the full P1
            # on the next rebirth attempt (it re-runs base_to_meteor_shortcut_p1
            # from base, which is the only thing that unlocks A5).
            log.warning(
                "[Meteor Shortcut] area5 dest button missing (retry) — A6 "
                "shortcut interact didn't register; re-doing full P1"
            )
            continue
        _mark_area5_unlocked_if_visible("builtin_teleport_area5_retry", attempts=8, delay=0.25)
        r = _nav_or_redo("base_to_meteor_shortcut_p3")
        if r == "kill":
            return False
        if r in ("fail", "redo"):
            if r == "fail":
                return False
            continue
        _mark_area5_unlocked_if_visible("meteor_shortcut_retry_p3", attempts=8, delay=0.25)
        if _KILLED or _STONE_LOST:
            return False
        if not _farm_meteor_from_current_position("Meteor Shortcut Retry"):
            return False
        _mark_area5_unlocked_if_visible("meteor_shortcut_retry_farm", attempts=1, delay=0.0)
        if not _teleport_to_base():
            return False
    return False


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Rebirth ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _quests_enabled(ds_snap: dict | None = None) -> bool:
    """Daily Quests rail toggle (dashboard state)."""
    try:
        if ds_snap is None:
            from dashboard import get_state as _ds_q
            ds_snap = _ds_q()
        return bool(ds_snap.get("daily_quests"))
    except Exception:
        return False


def _quest_mine_one(panel: int, star: int) -> bool:
    """Teleport to Area 1, walk to the star rock, hold LMB until HUD Done / timeout."""
    import config as _cfg_q
    import quest_menu as qm
    from macro_runner import _mouse_left_down, _mouse_left_up
    _console_status("QUESTS", f"Break {star} Star Rocks")
    if not _builtin_teleport_safe("area1", attempts=3, wait_seconds=3.5):
        log.warning(f"[QUEST] area1 teleport failed — skipping quest {panel}")
        return False
    _mark_area_unlocked(1, "quests")
    r = _nav_or_redo(f"break_{star}_star_rocks")
    if r != "ok":
        log.warning(f"[QUEST] break_{star}_star_rocks macro {r} — skipping quest {panel}")
        return False
    if _KILLED or _STONE_LOST:
        return False

    # Hold LMB and watch the HUD quest slot for the green Done text.
    timeout = max(5.0, float(getattr(_cfg_q, "QUEST_MINE_TIMEOUT_SECONDS", 60)))
    poll = max(0.05, float(getattr(_cfg_q, "QUEST_HUD_POLL_SECONDS", 0.15)))
    done = False
    try:
        _mouse_left_down()
        deadline = time.time() + timeout
        while time.time() < deadline:
            if _KILLED or _STONE_LOST:
                return False
            if qm.quest_hud_done(panel):
                done = True
                break
            time.sleep(poll)
    finally:
        _mouse_left_up()

    if done:
        log.info(f"[QUEST] quest {panel} complete (HUD Done) — will claim mineral reward later")
        stats.mark_step(f"Quest {panel}")
    else:
        log.warning(f"[QUEST] quest {panel} timed out after {timeout:.0f}s — auto-done, not claimable")
    return done


def _quest_mimic_one(panel: int) -> bool:
    """Open Chests quest — the quest is literally opening the chest.

    Play mimic.macro (walk + open) and consider the quest DONE. No combat,
    no LMB hold, no HUD Done watching — opening it completes the quest.
    """
    import quest_menu as qm
    _console_status("QUESTS", "Open Chests")
    if not _builtin_teleport_safe("area1", attempts=3, wait_seconds=3.5):
        log.warning(f"[QUEST] area1 teleport failed — skipping chest quest {panel}")
        return False
    _mark_area_unlocked(1, "quests")
    r = _nav_or_redo("mimic")
    if r != "ok":
        log.warning(f"[QUEST] mimic macro {r} — skipping chest quest {panel}")
        return False
    if _KILLED or _STONE_LOST:
        return False
    log.info(f"[QUEST] chest quest {panel} done (chest opened via macro) — will claim mineral reward later")
    stats.mark_step(f"Quest {panel} Chests")
    # mimic.macro may end on the weapon — back to pickaxe for the rest of the run
    try:
        _equip_pickaxe("mimic (weapon back to pickaxe)")
    except Exception as e:
        log.warning(f"[QUEST] pickaxe swap-back after mimic failed: {e}")
    return True


def _quest_wait_hud_done(panel: int, timeout: float = 6.0) -> bool:
    """Poll the HUD quest slot for the green Done text."""
    import quest_menu as qm
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _KILLED or _STONE_LOST:
            return False
        if qm.quest_hud_done(panel):
            return True
        time.sleep(0.30)
    return False


def _quest_hatch_action() -> bool:
    """Hatch Pets ACTIONS — run regardless of quest acceptance.

    Teleport to base, walk to the hatch NPC (hatch_pets.macro opens the GUI),
    page to 'Area 1 Egg', click Hatch All, close. Returns True when Hatch All
    was clicked. The 'Hatch Pets' quest itself is completed by the game when
    the quest was accepted; the actions also run before Combine Pets so
    there are hatched pets to combine.
    """
    import quest_menu as qm
    _console_status("QUESTS", "Hatch Pets")
    HATCH_TRIES = 2
    for attempt in range(1, HATCH_TRIES + 1):
        if _KILLED or _STONE_LOST:
            return False
        if not _builtin_teleport_safe("base", attempts=3, wait_seconds=3.5):
            log.warning(f"[HATCH] base teleport failed — skipping hatch pets (try {attempt}/{HATCH_TRIES})")
            return False
        r = _nav_or_redo("hatch_pets")
        if r != "ok":
            log.warning(f"[HATCH] hatch_pets macro {r} (try {attempt}/{HATCH_TRIES})")
            continue
        if _KILLED or _STONE_LOST:
            return False
        if qm.wait_hatch_menu_open(6.0):
            opened = True
            break
        # The macro's E presses may have landed before the NPC prompt was
        # ready. Standing at the NPC, one more E retries the interact — but
        # away from the NPC the same key opens the quest board; if that is
        # what opened, close it and redo the walk.
        log.warning(f"[HATCH] hatch GUI not open after macro (try {attempt}/{HATCH_TRIES})")
        if qm.quest_menu_open():
            log.warning("[HATCH] quest board opened instead of hatch GUI — closing, redo walk")
            qm.close_quest_menu()
            continue
        qm.press_menu_key()
        if qm.wait_hatch_menu_open(3.0):
            opened = True
            break
    else:
        log.warning("[HATCH] hatch GUI never opened — skipping hatch pets")
        return False
    if _KILLED or _STONE_LOST:
        return False
    ok = False
    try:
        ok = qm.hatch_all_flow()
    except Exception as e:
        log.warning(f"[HATCH] hatch GUI flow error: {e}")
    finally:
        try:
            # force_click: we KNOW the GUI was open (we clicked Hatch All on
            # it) — always send one close click even if the yellow reading
            # hovers just under the threshold; a GUI left open blocks F4.
            qm.close_hatch_menu(force_click=True)
        except Exception:
            pass
    if ok:
        log.info("[HATCH] Hatch All clicked — eggs hatched (any 'Hatch Pets' quest counts now)")
    else:
        log.warning("[HATCH] Hatch All not clicked (Area 1 Egg not reached)")
    return ok


def _quest_combine_action() -> bool:
    """Combine Pets — pure F4 monitor-menu flow, no macro needed.

    F4 -> PETS -> ZAPPY -> AUTO COMBINE -> close. The three close-button
    positions confirm every click landed. Returns True when auto combine ran.
    """
    import quest_menu as qm
    _console_status("QUESTS", "Combine Pets")
    ok = False
    try:
        ok = qm.combine_pets_flow()
    except Exception as e:
        log.warning(f"[COMBINE] combine flow error: {e}")
    # The F4 flow can leave the loadout on the monitor item — back to pickaxe
    try:
        _equip_pickaxe("combine pets (loadout back to pickaxe)")
    except Exception as e:
        log.warning(f"[QUEST] pickaxe swap-back after combine failed: {e}")
    return ok


def _open_quest_menu_and_wait(qm) -> bool:
    """Run the quest_menu macro (from the tp-base spawn) and confirm the board
    is open, with E-retries. True when the quest board is open."""
    r = _nav_or_redo("quest_menu")
    if r != "ok":
        log.warning(f"[QUESTS] quest_menu macro {r} — cannot open quest board")
        return False
    if qm.wait_quest_menu_open(5.0):
        return True
    log.warning("[QUESTS] quest menu not open after macro — pressing E a few more times")
    for _ in range(3):
        if _KILLED or _STONE_LOST:
            return False
        qm.press_menu_key()
        time.sleep(0.6)
        if qm.wait_quest_menu_open(3.0):
            return True
    log.warning("[QUESTS] quest menu did not open")
    return False


def _read_quest_plan(qm) -> dict:
    """Read all three quest panels and classify them into a quest plan."""
    quests = {}
    for panel in (1, 2, 3):
        text = qm.read_quest_panel(panel)
        star = qm.classify_quest(text)
        if star not in (1, 2, 3):
            star = None
        kind = "rocks" if star else None
        if kind is None:
            if qm.is_mimic_quest(text):
                kind = "mimic"
            elif qm.is_hatch_quest(text):
                kind = "hatch"
            elif qm.is_combine_quest(text):
                kind = "combine"
        quests[panel] = {"text": text, "star": star, "kind": kind}
    mine_list = [p for p in (1, 2, 3) if quests[p]["kind"] == "rocks"]
    # only ONE mimic per rebirth — the game only accepts one anyway
    mimic_panel = next((p for p in (1, 2, 3) if quests[p]["kind"] == "mimic"), None)
    hatch_panel = next((p for p in (1, 2, 3) if quests[p]["kind"] == "hatch"), None)
    combine_panel = next((p for p in (1, 2, 3) if quests[p]["kind"] == "combine"), None)
    # Hatch needs eggs (rock drops) and Combine needs hatched pets — both
    # are only accepted/done when a "Break X Star Rocks" quest is up too.
    has_rocks = bool(mine_list)
    hatch_do = hatch_panel is not None and has_rocks
    combine_do = combine_panel is not None and has_rocks
    # Hatch ACTIONS also run for Combine (it needs pets to combine), even
    # when the Hatch Pets quest itself is not on the board.
    hatch_actions = hatch_do or combine_do
    return {
        "quests": quests,
        "mine_list": mine_list,
        "mimic_panel": mimic_panel,
        "hatch_panel": hatch_panel,
        "combine_panel": combine_panel,
        "hatch_do": hatch_do,
        "combine_do": combine_do,
        "hatch_actions": hatch_actions,
    }


def _accept_quest_plan(qm, plan: dict, btn_settle: float) -> None:
    """Click Start ONLY on the quests the bot will actually do, then close the
    board. The rewards for the rest are confirmed/claimed at the end anyway."""
    quests = plan["quests"]
    mine_list = plan["mine_list"]
    mimic_panel = plan["mimic_panel"]
    hatch_do, combine_do = plan["hatch_do"], plan["combine_do"]
    start_list = list(mine_list)
    if mimic_panel is not None:
        start_list.append(mimic_panel)
    if hatch_do:
        start_list.append(plan["hatch_panel"])
    if combine_do:
        start_list.append(plan["combine_panel"])
    for panel in start_list:
        if not qm.click_quest_button(panel):
            log.warning(f"[QUEST] start click failed for panel {panel}")
        time.sleep(btn_settle)
    skipped = [f"q{p}={quests[p]['text']!r}" for p in (1, 2, 3) if p not in start_list]
    if skipped:
        log.info("[QUESTS] not started (bot won't do them): " + ", ".join(skipped))
    if plan["hatch_panel"] is not None and not hatch_do:
        log.info("[QUESTS] Hatch Pets quest present but no Break Star Rocks quest — skipped (no egg source)")
    if plan["combine_panel"] is not None and not combine_do:
        log.info("[QUESTS] Combine Pets quest present but no Break Star Rocks quest — skipped (no egg source)")
    if start_list:
        parts = [f"q{p}=Break {quests[p]['star']} Star Rocks" for p in mine_list]
        if mimic_panel is not None:
            parts.append(f"q{mimic_panel}=Open Chests")
        if hatch_do:
            parts.append(f"q{plan['hatch_panel']}=Hatch Pets")
        if combine_do:
            parts.append(f"q{plan['combine_panel']}=Combine Pets")
        if plan["hatch_actions"] and not hatch_do:
            parts.append("hatch actions (for Combine Pets)")
        log.info("[QUESTS] started " + ", ".join(f"q{p}" for p in start_list) + "; doing: " + ", ".join(parts))
    else:
        log.info("[QUESTS] no known quests (rocks/chests/pets) on the board")
    if not qm.close_quest_menu():
        log.warning("[QUESTS] quest menu close not confirmed")


def _start_daily_quests() -> None:
    """v1.8.32 run-START quest phase: accept (Start) the daily quests right
    after a fresh rebirth so rock quests can progress NATURALLY while the bot
    grinds the run. The DOING + claiming stays in _do_daily_quests() at the
    end (between meteor and rebirth) — this phase never does quest actions.

    On success the plan is saved to _QUEST_PLAN for the end phase. If this
    phase is skipped or fails, the end phase falls back to the legacy full
    flow (open board, read, accept, do, claim)."""
    import config as _cfg_q
    import quest_menu as qm
    global _QUESTS_STARTED_THIS_RUN, _QUEST_PLAN
    if _QUESTS_STARTED_THIS_RUN:
        return
    _QUESTS_STARTED_THIS_RUN = True
    if _KILLED or _STONE_LOST:
        return
    # Only FRESH runs (started from ~0 stone / after rebirth). After a
    # force-restart the quests are already done/accepted.
    try:
        _cur_run = getattr(stats, "_current_run", None)
        if _cur_run is not None and getattr(_cur_run, "full_rebirth", True) is False:
            log.info("[QUESTS] not a fresh run — skipping quest start phase")
            return
    except Exception:
        pass
    _console_status("QUESTS", "Starting Quests")
    btn_settle = max(0.05, float(getattr(_cfg_q, "QUEST_BTN_SETTLE", 0.35)))
    try:
        # quest_menu macro only works from the fresh tp-base spawn
        if not _at_base:
            if not _teleport_to_base():
                log.warning("[QUESTS] run-start quest phase: could not teleport to base — skipping")
                return
        if not _open_quest_menu_and_wait(qm):
            # The quest_menu macro (walk) may have already moved us off the
            # tp-base spawn — realign so the run's own nav macros line up.
            if not _KILLED and not _STONE_LOST:
                if not _teleport_to_base():
                    log.warning("[QUESTS] run-start quest phase: re-align to base failed after menu open failure")
            return
        plan = _read_quest_plan(qm)
        if not (plan["mine_list"] or plan["mimic_panel"] is not None
                or plan["hatch_actions"] or plan["combine_do"]):
            # nothing to accept — close the board and let the run go
            if not qm.close_quest_menu():
                log.warning("[QUESTS] quest menu close not confirmed (empty board)")
            _QUEST_PLAN = plan
            # back to a fresh tp-base spawn so the run's own nav macros line up
            # (the quest_menu walk already moved us off the spawn point)
            if not _KILLED and not _STONE_LOST:
                if not _teleport_to_base():
                    log.warning("[QUESTS] run-start quest phase: re-align to base failed (nothing to accept)")
            return
        _accept_quest_plan(qm, plan, btn_settle)
        _QUEST_PLAN = plan
        log.info("[QUESTS] quests accepted at run start — rock quests now progress naturally; "
                 "doing + claiming happens before rebirth")
        # back to a fresh tp-base spawn so the run's own nav macros line up
        if not _KILLED and not _STONE_LOST:
            _teleport_to_base()
    except Exception as e:
        log.warning(f"[QUESTS] run-start quest phase error (continuing run): {e}")
        _QUEST_PLAN = None


def _do_daily_quests() -> None:
    """Daily Quests END phase between meteor and rebirth. Best-effort — never
    blocks rebirth.

    v1.8.32: quests were already accepted at run start (_start_daily_quests)
    so rock quests could complete naturally during the grind. This phase uses
    the saved plan and checks the HUD FIRST for every quest: already-Done
    quests skip the whole teleport+macro trip. With no saved plan it falls
    back to the legacy full flow (open board, read, accept, do, claim)."""
    import config as _cfg_q
    import quest_menu as qm
    global _QUESTS_DONE_THIS_RUN, _QUEST_PLAN
    if _QUESTS_DONE_THIS_RUN:
        return
    _QUESTS_DONE_THIS_RUN = True
    if _KILLED or _STONE_LOST:
        return
    # Only FRESH runs (started from ~0 stone). After a force-restart the
    # quests are already done/accepted — running the phase again would just
    # sit there for 60/90s per quest waiting for a "Done" that never comes.
    try:
        _cur_run = getattr(stats, "_current_run", None)
        if _cur_run is not None and getattr(_cur_run, "full_rebirth", True) is False:
            log.info("[QUESTS] not a fresh run (resumed / force-restart) — skipping quest phase")
            return
    except Exception:
        pass
    btn_settle = max(0.05, float(getattr(_cfg_q, "QUEST_BTN_SETTLE", 0.35)))
    had_auto_str = False
    _freeze_stone(True)
    try:
        if _auto_strength_enabled():
            had_auto_str = True
            disable_auto_strength()
            set_overlay(auto_str=False)

        plan = _QUEST_PLAN
        if plan is not None:
            log.info("[QUESTS] Daily Quests ON — doing quests accepted at run start")
            _console_status("QUESTS", "Doing Quests")
        else:
            # legacy fallback — quests were never accepted at run start
            log.info("[QUESTS] Daily Quests ON — running full quest phase (no run-start plan)")
            _console_status("QUESTS", "Opening Quest Menu")
            if not _open_quest_menu_and_wait(qm):
                return
            plan = _read_quest_plan(qm)
            if not (plan["mine_list"] or plan["mimic_panel"] is not None
                    or plan["hatch_actions"] or plan["combine_do"]):
                if not qm.close_quest_menu():
                    log.warning("[QUESTS] quest menu close not confirmed")
                return
            _accept_quest_plan(qm, plan, btn_settle)
            _QUEST_PLAN = plan

        quests = plan["quests"]
        mine_list = plan["mine_list"]
        mimic_panel = plan["mimic_panel"]
        hatch_panel = plan["hatch_panel"]
        hatch_do, combine_do = plan["hatch_do"], plan["combine_do"]
        hatch_actions = plan["hatch_actions"]

        # 3) DO phase — HUD pre-check: never waste a teleport/macro walk on a
        # quest that already completed naturally during the run.
        completed = []
        for panel in mine_list:
            if _KILLED or _STONE_LOST:
                return
            if qm.quest_hud_done(panel):
                log.info(f"[QUEST] quest {panel} already Done on HUD — skipping teleport/macro")
                completed.append(panel)
                stats.mark_step(f"Quest {panel} (natural)")
                continue
            if _quest_mine_one(panel, quests[panel]["star"]):
                completed.append(panel)
        if mimic_panel is not None:
            if _KILLED or _STONE_LOST:
                return
            if qm.quest_hud_done(mimic_panel):
                log.info(f"[QUEST] chest quest {mimic_panel} already Done on HUD — skipping mimic macro")
                completed.append(mimic_panel)
                stats.mark_step(f"Quest {mimic_panel} Chests (natural)")
            elif _quest_mimic_one(mimic_panel):
                completed.append(mimic_panel)

        # 3b) hatch pets — eggs come from the rock quests above; the actions
        # run when the Hatch quest is accepted OR Combine needs pets to combine
        hatch_done = hatch_do and qm.quest_hud_done(hatch_panel)
        combine_done = combine_do and qm.quest_hud_done(plan["combine_panel"])
        if hatch_done:
            log.info(f"[QUEST] hatch quest {hatch_panel} already Done on HUD — skipping hatch actions")
            completed.append(hatch_panel)
            stats.mark_step(f"Quest {hatch_panel} Hatch (natural)")
        elif hatch_actions:
            if _KILLED or _STONE_LOST:
                return
            if _quest_hatch_action():
                if hatch_do and _quest_wait_hud_done(hatch_panel, 8.0):
                    completed.append(hatch_panel)
                    stats.mark_step(f"Quest {hatch_panel} Hatch")
                elif hatch_do:
                    log.warning(f"[QUEST] hatch quest {hatch_panel} not Done on HUD — not claimable")

        # 3c) combine pets — only when the Combine quest was accepted.
        # The in-menu flow only proves the clicks landed (yellow close
        # samples) — the HUD Done check is the real success signal, so when
        # the quest does not register we retry the whole flow instead of
        # trusting "all clicks landed" (a missed AUTO COMBINE click can open
        # some other panel that still trips the yellow sample check).
        if combine_do:
            if combine_done:
                log.info(f"[QUEST] combine quest {plan['combine_panel']} already Done on HUD — skipping combine")
                completed.append(plan["combine_panel"])
                stats.mark_step(f"Quest {plan['combine_panel']} Combine (natural)")
            elif _KILLED or _STONE_LOST:
                return
            else:
                COMBINE_PASSES = 3
                combined_ok = False
                for attempt in range(1, COMBINE_PASSES + 1):
                    if _KILLED or _STONE_LOST:
                        return
                    if attempt > 1:
                        log.info(f"[QUESTS] Combine Pets pass {attempt}/{COMBINE_PASSES} — HUD still not Done")
                    if not _quest_combine_action():
                        # flow already retried internally and verified missing
                        # panels — no point looping the same broken clicks
                        break
                    if _quest_wait_hud_done(plan["combine_panel"], 8.0):
                        completed.append(plan["combine_panel"])
                        stats.mark_step(f"Quest {plan['combine_panel']} Combine")
                        combined_ok = True
                        break
                    log.warning(f"[QUEST] combine quest {plan['combine_panel']} not Done on HUD after pass {attempt}")
                if not combined_ok:
                    log.warning(f"[QUEST] combine quest {plan['combine_panel']} not Done on HUD — not claimable "
                                "(enable SAVE_DEBUG_CROPS and check the quest_combine_* crops to recalibrate "
                                "the COMBINE_* click points)")

        # 4) claim rewards — claiming CLOSES the menu, reopen with E between claims
        if completed:
            _console_status("QUESTS", "Claiming Rewards")
            # quest_menu macro only works from the fresh tp-base spawn — the
            # quest actions moved the character, so always re-teleport.
            log.info("[QUESTS] re-teleport to base before claim-phase quest_menu macro")
            if not _teleport_to_base():
                return
            r = _nav_or_redo("quest_menu")
            if r != "ok" or not qm.wait_quest_menu_open(5.0):
                log.warning("[QUESTS] could not reopen quest menu for claiming")
                return
            for panel in completed:
                if not qm.quest_menu_open():
                    if not qm.reopen_quest_menu():
                        log.warning("[QUESTS] E reopen failed — teleport to base + quest_menu macro")
                        if not _teleport_to_base():
                            return
                        if _nav_or_redo("quest_menu") != "ok":
                            return
                        if not qm.wait_quest_menu_open(5.0):
                            return
                if not qm.click_quest_button(panel):
                    log.warning(f"[QUEST] claim click failed for panel {panel}")
                    continue
                time.sleep(0.25)
                deadline = time.time() + 3.0
                while time.time() < deadline and qm.quest_menu_open():
                    time.sleep(0.10)
                if qm.quest_menu_open():
                    log.warning(f"[QUEST] panel {panel} claim did not close the menu — not complete?")
                else:
                    log.info(f"[QUEST] reward claimed for quest {panel}")
                    stats.mark_step(f"Quest {panel} Reward")
                    stats.add_quest_completed()

        # 5) back to base for the rebirth
        if not _at_base:
            _teleport_to_base()
    except Exception as e:
        log.warning(f"[QUESTS] quest phase error (continuing to rebirth): {e}")
    finally:
        try:
            if qm.quest_menu_open():
                qm.close_quest_menu()
        except Exception:
            pass
        _freeze_stone(False)
        # The quest phase physically walks the character from the tp-base
        # spawn to the quest board. base_to_rebirth only works from the
        # fresh spawn — always re-teleport before the rebirth walk.
        if not _KILLED and not _STONE_LOST:
            try:
                log.info("[QUESTS] re-teleport to base — fresh spawn before rebirth walk")
                _teleport_to_base()
            except Exception as e:
                log.warning(f"[QUESTS] base re-teleport failed: {e}")
        if had_auto_str and not _KILLED:
            try:
                enable_auto_strength()
                set_overlay(auto_str=True)
            except Exception:
                pass
        log.info("[QUESTS] quest phase finished")


def _do_rebirth() -> bool:
    """Navigate to rebirth NPC and confirm. Returns True when rebirth confirmed.

    The stone watcher is suppressed for the whole rebirth flow because the
    rebirth macro, animation, blank HUD, and post-confirm settle can all hide
    the stone icon without meaning the run failed.
    """
    global _REBIRTH_IN_PROGRESS
    _REBIRTH_IN_PROGRESS = True
    try:
        _console_status("REBIRTH", "Rebirthing")
        if _auto_strength_enabled():
            disable_auto_strength()
            set_overlay(auto_str=False)

        # base_to_rebirth is a walk FROM BASE to the NPC. After meteor / A6 we
        # are not at base — teleport first.
        if not _at_base:
            log.info("[REBIRTH] not at base — teleport_to_base before base_to_rebirth")
            if not _teleport_to_base():
                return False
        # Daily Quests rail: run the quest phase between meteor and rebirth.
        if _quests_enabled():
            _do_daily_quests()
            if _KILLED or _STONE_LOST:
                return False
        _mark_left_base()
        if not _run_macro("base_to_rebirth"):
            return False

        _console_status("REBIRTH", "Confirming")
        _rec_log_macro("rebirth_confirm", "start")
        ui_ok, ui_reason = _confirm_rebirth_ui()
        if not ui_ok:
            log.warning(f"[REBIRTH] confirm UI failed ({ui_reason})")
            _rec_log_macro("rebirth_confirm", "error", error=str(ui_reason))
            if ui_reason == "no_confirm":
                _rec_set_failure("rebirth_no_confirm:meteor_not_broken")
            else:
                _rec_set_failure(f"rebirth_ui:{ui_reason}")
            _teleport_to_base()
            return False

        _console_status("REBIRTH", "Respawning")
        try:
            from teleport_menu import wait_black_screen_gone
            wait_black_screen_gone(timeout=8.0, settle=1.0)
        except Exception:
            _wait_polling(1.0, "Post-rebirth cooldown")

        stone = None
        non_zero_reads = 0
        deadline = time.time() + 1.0

        while time.time() < deadline:
            if _KILLED or _STONE_LOST:
                return False

            stone = _read_stone_live(update_last=False, check_glitch=False)
            log.debug(f"Rebirth fast poll: stone={stone}")

            if stone == 0.0:
                log.debug("Rebirth confirmed (stone=0)")
                _console_status("REBIRTH", "Rebirth confirmed", stone=0)
                _mark_rebirth_zero_confirmed("stone=0")
                set_overlay(stone=0.0, auto_str=None, status="REBIRTH")
                _rec_log_macro("rebirth_confirm", "end")
                return _teleport_to_base()

            if stone is not None and stone > 0:
                non_zero_reads += 1
                if non_zero_reads >= 2:
                    break
            else:
                non_zero_reads = 0

            time.sleep(0.1)

        if stone is None:
            log.debug("Rebirth confirmed (HUD blank in fast confirmation window)")
            _console_status("REBIRTH", "Rebirth confirmed", stone=0)
            _mark_rebirth_zero_confirmed("blank HUD")
            set_overlay(stone=0.0, auto_str=None, status="REBIRTH")
            _rec_log_macro("rebirth_confirm", "end")
            return _teleport_to_base()

        log.warning(f"Rebirth not confirmed (stone={stone:.2e}) - retrying")
        _rec_log_macro("rebirth_confirm", "error", error="stone_nonzero_retry")
        _console_status("REBIRTH", "Retrying...")
        _teleport_to_base()
        return False
    finally:
        _REBIRTH_IN_PROGRESS = False

def _do_base_rock(target_stone: float = None) -> bool:
    """Farm base rock until target_stone (default: STONE_FOR_A5_STAGE1). Returns True on success."""
    global _at_base, _last_live_stone

    if target_stone is None:
        target_stone = STONE_FOR_A5_STAGE1
    # Stone detection: the Manual Strength stone threshold replaces the
    # route's own target everywhere the baserock grinds (default 1.36e152).
    try:
        import config as _cfg_t
        _ms_stone = float(getattr(_cfg_t, "MANUAL_STR_STONE_TARGET", 0) or 0)
        if _manual_strength_enabled() and not _manual_surge_detection() and _ms_stone > 0:
            log.debug(f"[BASEROCK] manual stone target override: {_fmt_stone(_ms_stone)} (route: {_fmt_stone(target_stone)})")
            target_stone = _ms_stone
    except Exception:
        pass

    log.debug(f"[BASE_ROCK] _at_base={_at_base} ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â {'skipping teleport (already at base)' if _at_base else 'teleporting to base'} | target={target_stone:.2e}")
    if not _at_base:
        if not _teleport_to_base():
            return False

    if _auto_strength_enabled():
        enable_auto_strength()
        set_overlay(auto_str=True)

    NO_GAIN_TIMEOUT  = 30   # seconds — if stone doesn't move at all, re-navigate
    BASE_ROCK_RETRIES = _route_redo_limit()

    for _br_attempt in range(1, BASE_ROCK_RETRIES + 1):
        if _KILLED or _STONE_LOST:
            return False

        # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Pre-navigation drill unlock check ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
        # Check BEFORE navigating to baserock ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â if stone already >= threshold
        # (e.g. bot started above e70), unlock drills here while still at base.
        # This avoids wasting a baseÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢rockÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢base round trip.
        # _maybe_unlock_drills ends at base, so _at_base stays True and
        # base_to_baserock below navigates cleanly without an extra teleport.
        _maybe_unlock_drills()
        if _KILLED or _STONE_LOST:
            return False
        # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

        _console_status("FARMING", "Base Rock")
        log.info(f"[BASEROCK] attempt {_br_attempt}/{BASE_ROCK_RETRIES}  {_farm_env_bits()}")
        r = _nav_or_redo("base_to_baserock")
        if r == "kill":
            return False
        if r == "fail":
            return False
        if r == "redo":
            log.warning("[NET] lag during walk — redo Base Rock path")
            _at_base = False
            if not _teleport_to_base():
                return False
            continue
        _mark_left_base()

        # Re-enable auto strength each attempt ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â a failed/retried attempt goes through
        # _teleport_to_base() which disables it, so we must re-enable here.
        if _auto_strength_enabled():
            enable_auto_strength()
            set_overlay(auto_str=True)

        # Display seed only — the background stone reader and the stop-flag
        # reads keep the real value fresh. A blocking OCR here would delay the
        # fast-open sequence after the nav macro by ~0.5-1s.
        start_stone = _last_live_stone or 0
        _console_status("FARMING", "Base Rock", stone=start_stone)

        # Replay baserock_hit macro until stone target reached or no-gain timeout.
        # Each macro run is finite ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â crouch/uncrouch are always paired, so stopping
        # between runs is always safe with no stuck-crouch risk.
        # NOTE: last_stone starts None ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â the stone reading resets to baserock level
        # (much lower than carry-over stage stone), so we must seed last_stone from
        # the first valid baserock read rather than start_stone (which may be stale/high).
        last_stone          = None   # seeded on first valid read at this rock
        ok                  = False
        cur                 = start_stone

        # No-gain tolerance: count macro CYCLES with no stone increase.
        # OCR glitches (e.g. reading '7' mid-swing) must not trigger a
        # re-navigate ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â we require NO_GAIN_CYCLES consecutive gainless cycles.
        NO_GAIN_CYCLES      = 2      # faster retry if repeated macro cycles produce no stone gain
        _br_no_gain_streak  = 0      # incremented each cycle with no gain
        _manual_mode        = _manual_strength_enabled()
        _manual_no_gain_wait = _manual_hud_stall_seconds() if _manual_mode else float(NO_GAIN_TIMEOUT)
        _last_gain_time     = time.time()
        _manual_strength_watch = _make_manual_strength_watchdog("BASEROCK") if _manual_mode else None
        _manual_activity_stone = None
        _last_manual_buy_log = 0.0
        _stop_why = [""]
        _diag = {
            "buys": 0,
            "ocr_ok": 0,
            "ocr_glitch": 0,
            "ocr_miss": 0,
            "last_c": None,
            "last_glitch": None,
            "last_buy_at": 0.0,
            "last_buy": "",
            "skip_log_at": 0.0,
        }

        def _dump_stall(why: str) -> None:
            str_val = None
            try:
                if _manual_strength_watch:
                    str_val = _manual_strength_watch.get("last_val")
            except Exception:
                pass
            buy_ago = (time.time() - _diag["last_buy_at"]) if _diag["last_buy_at"] else -1
            log.warning(
                f"[STALL] {why}  peak={_fmt_stone(last_stone)} cur={_fmt_stone(_diag['last_c'])} "
                f"glitch={_diag['last_glitch'] or '-'}  ocr_ok={_diag['ocr_ok']} "
                f"ocr_glitch={_diag['ocr_glitch']} ocr_miss={_diag['ocr_miss']}  "
                f"buys={_diag['buys']} last_buy={_diag['last_buy'] or '-'} "
                f"buy_ago={buy_ago:.1f}s  str={_fmt_stone(str_val) if str_val is not None else '-'}  "
                f"{_farm_env_bits()}"
            )

        def _manual_buy_activity(row_name=None, button_name=None):
            nonlocal _last_manual_buy_log
            # Upgrade clicks are not stone gain. Resetting _last_gain_time here
            # is why 5s HUD stall never fired (6000 clicks → idle always 0.0s).
            _diag["buys"] += 1
            _diag["last_buy_at"] = time.time()
            _diag["last_buy"] = str(button_name or row_name or "upgrade")
            now = time.time()
            if now - _last_manual_buy_log >= 1.0:
                log.debug(f"[BASEROCK] manual buy activity: {_diag['last_buy']} n={_diag['buys']}")
                _last_manual_buy_log = now

        def _should_stop_baserock():
            nonlocal last_stone, ok, cur, _br_no_gain_streak, _last_gain_time, _manual_activity_stone
            global _last_live_stone
            if _KILLED:
                return True
            if _peek_net_redo():
                return True
            if not _check_alive():
                return True
            # Surge-level detection (bottom-row-only): stop buying when the
            # bottom row surge level reaches the user threshold. Stone
            # threshold checks are skipped in this mode - the surge level is
            # the "done" signal. Stall watchdogs below still protect the run.
            _surge_mode = _manual_mode and _manual_surge_detection()
            if _surge_mode:
                lvl = _read_surge_level_live()
                if lvl is not None and lvl >= _manual_surge_target():
                    _stop_why[0] = "surge_target"
                    log.info(f"[BASEROCK] surge level {lvl} >= {_manual_surge_target()} - target reached; stopping")
                    ok = True
                    return True
            c = _read_stone_live(update_last=False, check_glitch=False)
            if c is not None and c <= 0:
                c = None
            if c is None:
                _diag["ocr_miss"] += 1
            else:
                _diag["last_c"] = c

            # Determine if this OCR read looks like a glitch.
            # Manual-strength menu OCR can spike far below or far above the real
            # value. Ignore both directions for gain and threshold decisions.
            # FIX 5: check_high=False Ã¢â‚¬â€ local `last_stone` peak can grow >1e6x
            # per cycle with auto-strength ON; never treat real growth as glitch.
            glitch_reason = _stone_glitch_reason(c, last_stone, check_high=False)
            is_glitch = glitch_reason is not None

            if c is not None and not is_glitch:
                _diag["ocr_ok"] += 1
                _diag["last_glitch"] = None
                if c >= target_stone and not _surge_mode:
                    confirmed, confirmed_cur = _confirm_stone_at_least(
                        target_stone,
                        "[BASEROCK] target",
                        first_value=c,
                        attempts=6,
                        required_hits=2,
                        delay=0.15,
                    )
                    if confirmed:
                        c = confirmed_cur or c
                        _last_live_stone = c
                        last_stone = max(last_stone or c, c)
                        cur = c
                        set_overlay(stone=c)
                        _dash_update(cur_stone=c)
                        log.debug(f"[BASEROCK] threshold confirmed - stopping (stone={_fmt_stone(c)})")
                        ok = True
                        return True
                    if confirmed_cur is None:
                        return False
                    c = confirmed_cur
                    # FIX 5: same Ã¢â‚¬â€ local peak, check_high=False
                    glitch_reason = _stone_glitch_reason(c, last_stone, check_high=False)
                    is_glitch = glitch_reason is not None
                    if is_glitch:
                        log.debug(f"[BASEROCK] OCR {glitch_reason} glitch ignored after target re-check: {c} (peak={last_stone})")
                        return False

                _last_live_stone = c
                set_overlay(stone=c)
                _dash_update(cur_stone=c)
                cur = c
                if last_stone is None:
                    # FIX 6/7: Guard first-valid-read seed against OCR artifacts.
                    # If start_stone is large and c is tiny (e.g. "153" misread),
                    # seeding last_stone=153 poisons the baseline Ã¢â‚¬â€ every real
                    # stone value then looks like a 1e150x spike and gets rejected.
                    # Only accept the seed if c is plausible relative to start_stone.
                    _seed_ok = (
                        c > 0 and (
                            start_stone is None or start_stone < 1e6 or
                            c >= start_stone * 0.001
                        )
                    )
                    if not _seed_ok:
                        log.debug(f"[BASEROCK] first-read seed rejected (c={_fmt_stone(c)} << start={_fmt_stone(start_stone)}) Ã¢â‚¬â€ waiting for valid read")
                    else:
                        # First valid read Ã¢â‚¬â€ seed baseline, reset streak
                        last_stone         = c
                        _manual_activity_stone = c
                        _br_no_gain_streak = 0
                        _last_gain_time    = time.time()
                elif c > last_stone:
                    last_stone         = c
                    _manual_activity_stone = c
                    _br_no_gain_streak = 0   # real gain ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â reset streak
                    _last_gain_time    = time.time()
                else:
                    if _manual_mode:
                        # In manual mode we still drive retries by stone gain.
                        # Keep logging movement diagnostics, but do not reset
                        # the no-gain timer unless we see real gain (c > peak).
                        ref = _manual_activity_stone
                        moved = (
                            ref is None or
                            (ref <= 0 and c != ref) or
                            (ref and abs(c - ref) / ref >= 0.001)
                        )
                        _manual_activity_stone = c
                        if moved:
                            _last_gain_time = time.time()
                            log.debug(f"[BASEROCK] manual stone movement activity: peak={_fmt_stone(last_stone)} cur={_fmt_stone(c)}")
                        else:
                            no_gain_for = time.time() - _last_gain_time
                            log.debug(f"[BASEROCK] manual no-gain {no_gain_for:.1f}/{_manual_no_gain_wait:.1f}s")
                    else:
                        # Valid non-glitch read but no gain this macro cycle
                        _br_no_gain_streak += 1
                        log.debug(f"[BASEROCK] no-gain streak {_br_no_gain_streak}/{NO_GAIN_CYCLES}")
            elif is_glitch:
                _diag["ocr_glitch"] += 1
                _diag["last_glitch"] = glitch_reason
                _diag["last_c"] = c
                log.debug(f"[BASEROCK] OCR {glitch_reason} glitch ignored: {c} (peak={last_stone})")
            # else: OCR returned None ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â do NOT touch any counters

            # No-gain bail ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â only fires after baseline is set
            if last_stone is not None:
                if _manual_mode:
                    if _manual_strength_watchdog_stalled(
                        _manual_strength_watch,
                        recent_activity_at=_last_gain_time,
                    ):
                        _stop_why[0] = "strength_stall"
                        _dump_stall("strength watchdog")
                        return True
                    no_gain_for = time.time() - _last_gain_time
                    if no_gain_for >= _manual_no_gain_wait:
                        _stop_why[0] = "hud_stall"
                        _dump_stall(f"HUD no-gain {no_gain_for:.1f}s")
                        log.warning(f"Base rock: no stone gain for {no_gain_for:.1f}s — re-navigate")
                        return True
                    now = time.time()
                    if now - _diag["skip_log_at"] >= 2.0:
                        _diag["skip_log_at"] = now
                        log.info(
                            f"[STALL] HUD idle {no_gain_for:.1f}/{_manual_no_gain_wait:.1f}s  "
                            f"buys={_diag['buys']}  {_farm_env_bits()}"
                        )
                elif _br_no_gain_streak >= NO_GAIN_CYCLES:
                    _stop_why[0] = "no_gain_cycles"
                    log.warning(f"Base rock: no stone gain for {NO_GAIN_CYCLES} cycles — re-navigate")
                    return True
            elif _manual_mode:
                no_gain_for = time.time() - _last_gain_time
                if no_gain_for >= _manual_no_gain_wait:
                    _stop_why[0] = "hud_stall_no_stone"
                    _dump_stall(f"HUD no valid stone {no_gain_for:.1f}s")
                    log.warning(f"Base rock: no valid stone for {no_gain_for:.1f}s — re-navigate")
                    return True

            # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Mid-loop drill unlock check ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
            # _maybe_unlock_drills is also called once before the loop starts,
            # but if the bot starts below the e70 threshold, stone may cross it
            # during this loop ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â we must catch that here so drills unlock on time.
            if not _DRILLS_UNLOCKED:
                _maybe_unlock_drills()
                if _DRILLS_UNLOCKED:
                    # Drill macro teleported us away and back ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stop the hit loop
                    # so _do_base_rock re-navigates cleanly via base_to_baserock.
                    log.debug("[BASEROCK] drill unlock fired mid-loop ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stopping hit loop to re-navigate")
                    return True
            # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

            return False

        _run_baserock_loop_until(
            _should_stop_baserock,
            manual_reason="base rock" if _manual_strength_enabled() else "",
            activity_callback=_manual_buy_activity if _manual_strength_enabled() else None,
        )
        _stop_drill_loop()
        if _KILLED or _STONE_LOST:
            return False
        if _take_net_redo():
            ok = False
            log.warning("[NET] lag during Base Rock farm — redo path")

        if ok:
            if _manual_strength_enabled():
                valid_manual_reads = [v for v in (cur, last_stone) if v is not None]
                if valid_manual_reads:
                    cur = max(valid_manual_reads)
            else:
                cur = _read_stone_live() or cur
            if _manual_strength_enabled():
                break
            if _manual_strength_enabled() and cur is not None and cur < target_stone:
                log.warning(f"[BASEROCK] manual upgrades spent below target after stop ({_fmt_stone(cur)} < {_fmt_stone(target_stone)}); retrying base rock")
                ok = False
            else:
                break  # success ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â exit retry loop

        log.warning(
            f"Base rock farming failed (attempt {_br_attempt}/{BASE_ROCK_RETRIES})  "
            f"why={_stop_why[0] or 'unknown'}  {_farm_env_bits()}"
        )
        if _stop_why[0]:
            _dump_stall(f"attempt {_br_attempt} fail")
        # Skip re-teleport if drills just fired ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â _maybe_unlock_drills already
        # ends at base (_at_base=True), so another teleport_to_base is redundant.
        if not _at_base and not _KILLED:
            if not _teleport_to_base():
                return False
        # continue retry loop
    else:
        log.warning(f"Base rock: all {BASE_ROCK_RETRIES} attempts failed  {_farm_env_bits()}")
        _rec_set_failure("redo_limit:baserock")
        return False

    if not ok:
        return False

    stats.mark_step("Base Rock")

    if _manual_strength_enabled():
        if not _stop_active_manual_strength_for_action("base rock complete"):
            _rec_set_failure("manual_strength_close_failed:base_rock_complete")
            return False
        cur = _manual_post_threshold_topup("BASEROCK", target_stone, cur, "baserock_hit")
        _console_status("FARMING", "Base Rock", stone=cur)
        return True

    topup = STAGE_TOPUP_SECONDS.get("base", 15)
    topup_target = target_stone * 1.01
    cur = _read_stone_live(update_last=False, check_glitch=False) or cur
    if topup > 0:
        if _auto_strength_enabled():
            disable_auto_strength()
            set_overlay(auto_str=False)
        _console_status("FARMING", "Base Rock topup")
        if _run_hit_macro("baserock_hit", wait=False, skip_center=True) is None:
            return False
        _topup_deadline = time.time() + TOPUP_TIMEOUT
        log.debug(f"[BASEROCK] topup - up to 3s warmup hit then polling to {_fmt_stone(topup_target)} (max {TOPUP_TIMEOUT}s)")
        _blind_deadline = time.time() + 3.0
        while time.time() < _blind_deadline and not (_KILLED or _STONE_LOST):
            _probe = _read_stone_live(update_last=False, check_glitch=False)
            if _probe is not None and _probe >= topup_target:
                break
            _wait_polling(0.25, "Base rock topup - blind hit", freeze=False)
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        time.sleep(0.3)
        cur = _read_stone_checked("[BASEROCK] topup precheck", attempts=8, delay=0.15, min_reads=3) or cur

        if cur < topup_target:
            def _should_stop_topup():
                nonlocal cur
                global _last_live_stone
                if _KILLED:
                    return True
                if not _check_alive():
                    return True
                if time.time() > _topup_deadline:
                    return True
                c = _read_stone_live(update_last=False, check_glitch=False)
                if c is not None:
                    glitch_reason = _stone_glitch_reason(c, cur)
                    if glitch_reason:
                        log.debug(f"[BASEROCK] topup OCR {glitch_reason} glitch ignored: {c} (cur={cur})")
                        return False
                    if c >= topup_target:
                        confirmed, confirmed_cur = _confirm_stone_at_least(
                            topup_target,
                            "[BASEROCK] topup",
                            first_value=c,
                            attempts=5,
                            required_hits=2,
                            delay=0.12,
                        )
                        if confirmed:
                            cur = confirmed_cur or c
                            log.debug(f"[BASEROCK] topup done - stone={_fmt_stone(cur)}")
                            return True
                        if confirmed_cur is not None:
                            c = confirmed_cur
                        else:
                            return False
                    _last_live_stone = c
                    set_overlay(stone=c)
                    _dash_update(cur_stone=c)
                    cur = c
                return False

            _run_baserock_loop_until(
                _should_stop_topup,
                skip_center=True,
                manual_reason="base rock topup" if _manual_strength_enabled() else "",
            )
            _stop_drill_loop()
            cur = _read_stone_checked("[BASEROCK] topup final", attempts=5, delay=0.12, min_reads=2) or cur
        else:
            log.debug(f"[BASEROCK] topup: already at {_fmt_stone(cur)} >= {_fmt_stone(topup_target)} after blind hit")
            _close_hit_macro()
            stop_macro()
            _stop_drill_loop()
        set_overlay(stone=cur)

    if cur is None or cur < target_stone:
        log.warning(f"[BASEROCK] final stone below target ({_fmt_stone(cur)} < {_fmt_stone(target_stone)})")
        return False
    _last_live_stone = cur
    _console_status("FARMING", "Base Rock", stone=cur)
    return True


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Main run loop ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

def _delve_read_ui_text(region: tuple[int, int, int, int]) -> str:
    try:
        import cv2
        import pytesseract
        from screen import ensure_tesseract
        ensure_tesseract()
        img = grab_region(region)
        up = cv2.resize(img, None, fx=2.4, fy=2.4, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        raw = pytesseract.image_to_string(
            thresh,
            config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )
        return (raw or "").strip().upper()
    except Exception as e:
        log.debug(f"[DELVE] OCR failed: {e}")
        return ""


def _delve_close_visible() -> bool:
    try:
        import cv2
        import numpy as np
        import config as _cfg_delve
        img = grab_region(getattr(_cfg_delve, "DELVE_CLOSE_REGION"))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 65, 100], dtype=np.uint8),  # widened for semi-transparent close button
            np.array([45, 255, 255], dtype=np.uint8),
        )
        pct = float(np.count_nonzero(yellow)) / float(max(1, yellow.size))
        text = _delve_read_ui_text(getattr(_cfg_delve, "DELVE_CLOSE_REGION"))
        ok = pct >= 0.30 or "CLOSE" in text or "CLOS" in text
        log.debug(f"[DELVE] close check yellow={pct:.1%} text={text!r} ok={ok}")
        return ok
    except Exception as e:
        log.debug(f"[DELVE] close detection failed: {e}")
        return False


def _delve_join_visible() -> bool:
    import config as _cfg_delve
    text = _delve_read_ui_text(getattr(_cfg_delve, "DELVE_JOIN_REGION"))
    ok = "JOIN" in text or "JOI" in text
    log.debug(f"[DELVE] join OCR text={text!r} ok={ok}")
    return ok


def _delve_click_join_twice():
    import config as _cfg_delve
    from macro_runner import _mouse_left_click, _mouse_move_abs
    x, y = getattr(_cfg_delve, "DELVE_JOIN_CENTER")
    gap = max(0.0, float(getattr(_cfg_delve, "DELVE_JOIN_CLICK_GAP_SECONDS", 0.5)))
    for idx in range(2):
        _mouse_move_abs(int(x), int(y))
        time.sleep(0.06)
        _mouse_left_click()
        log.debug(f"[DELVE] JOIN click {idx + 1}/2 at ({x},{y})")
        if idx == 0:
            time.sleep(gap)


def _delve_prepare_weapon():
    import config as _cfg_delve
    wait_s = max(0.0, float(getattr(_cfg_delve, "DELVE_POST_JOIN_WAIT_SECONDS", 0.5)))
    binding = str(getattr(_cfg_delve, "DELVE_WEAPON_BINDING", None) or getattr(_cfg_delve, "WEAPON_1_BINDING", "1"))
    time.sleep(wait_s)
    for idx in range(3):
        if not trigger_binding_action(binding, hold_ms=45):
            trigger_binding_action("1", hold_ms=45)
        log.debug(f"[DELVE] weapon binding press {idx + 1}/3 ({binding})")
        time.sleep(0.12)


def _delve_try_menu_resume(reason: str) -> bool:
    global _STONE_LOST
    if not _STONE_LOST:
        # Do not run proactive menu-resume probes during normal route/fight flow.
        return False
    try:
        from dashboard import get_state as _ds
        if not _menu_resume_enabled(_ds()):
            return False
    except Exception:
        return False
    # During active Delve fight we should not attempt menu resume while the
    # in-match HUD (stone icon) is visible. This filters false positives from
    # bright yellow UI elements that can look like PLAY.
    try:
        if reason == "boss fight" and _stone_icon_visible_restart_image():
            return False
    except Exception:
        pass
    # Require a stable menu detection before resuming to avoid false positives
    # during movement/route frames (more common on higher resolutions).
    try:
        if not is_in_menu():
            return False
        time.sleep(0.12)
        if not is_in_menu():
            return False
    except Exception:
        return False
    log.warning(f"[DELVE] menu detected during {reason}; attempting menu resume")
    if _do_menu_resume():
        log.info("[DELVE] menu resume succeeded")
        return True
    log.warning("[DELVE] menu resume failed")
    return False


def _delve_open_menu_via_a5() -> bool:
    import config as _cfg_delve
    attempts = _route_redo_limit()
    wait_s = max(0.0, float(getattr(_cfg_delve, "DELVE_MENU_WAIT_SECONDS", 0.5)))
    for attempt in range(1, attempts + 1):
        if _KILLED:
            return False
        _console_status("DELVE", f"Teleport {attempt}/{attempts}")
        _dash_update(status="DELVE", goal="Teleport")
        set_overlay(status="DELVE", goal="Teleport")
        if not _builtin_teleport_safe("area5", attempts=10, wait_seconds=3.5):
            log.warning(f"[DELVE] F4 Area 5 teleport failed before delve macro ({attempt}/{attempts})")
            _delve_try_menu_resume("route teleport failure")
            continue
        _mark_area5_unlocked_if_visible(f"delve attempt {attempt}", attempts=2, delay=0.15)
        _console_status("DELVE", f"Navigation {attempt}/{attempts}")
        _dash_update(status="DELVE", goal="Navigation")
        set_overlay(status="DELVE", goal="Navigation")
        if not _run_macro("area5_to_delve"):
            log.warning(f"[DELVE] area5_to_delve macro failed ({attempt}/{attempts})")
            _delve_try_menu_resume("route macro failure")
            continue
        time.sleep(wait_s)
        close_ok = _delve_close_visible()
        join_ok = _delve_join_visible()
        if close_ok:
            if not join_ok:
                log.warning("[DELVE] CLOSE found but JOIN OCR missed; clicking configured JOIN center anyway")
            return True
        log.warning(f"[DELVE] boss menu not confirmed after route attempt {attempt}/{attempts}")
        _delve_try_menu_resume("route menu confirm miss")
    _rec_set_failure("redo_limit:delve")
    return False


def _kraken_close_visible() -> bool:
    try:
        import cv2
        import numpy as np
        import config as _cfg_kraken
        img = grab_region(getattr(_cfg_kraken, "KRAKEN_CLOSE_REGION"))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 65, 100], dtype=np.uint8),  # widened for semi-transparent close button
            np.array([45, 255, 255], dtype=np.uint8),
        )
        pct = float(np.count_nonzero(yellow)) / float(max(1, yellow.size))
        text = _delve_read_ui_text(getattr(_cfg_kraken, "KRAKEN_CLOSE_REGION"))
        ok = pct >= 0.30 or "CLOSE" in text or "CLOS" in text
        log.debug(f"[KRAKEN] close check yellow={pct:.1%} text={text!r} ok={ok}")
        return ok
    except Exception as e:
        log.debug(f"[KRAKEN] close detection failed: {e}")
        return False


def _kraken_join_visible() -> bool:
    import config as _cfg_kraken
    text = _delve_read_ui_text(getattr(_cfg_kraken, "KRAKEN_JOIN_REGION"))
    ok = "JOIN" in text or "JOI" in text
    log.debug(f"[KRAKEN] join OCR text={text!r} ok={ok}")
    return ok


def _kraken_click_join_twice():
    import config as _cfg_kraken
    from macro_runner import _mouse_left_click, _mouse_move_abs
    x, y = getattr(_cfg_kraken, "KRAKEN_JOIN_CENTER")
    gap = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_JOIN_CLICK_GAP_SECONDS", 0.5)))
    for idx in range(2):
        _mouse_move_abs(int(x), int(y))
        time.sleep(0.06)
        _mouse_left_click()
        log.debug(f"[KRAKEN] JOIN click {idx + 1}/2 at ({x},{y})")
        if idx == 0:
            time.sleep(gap)


def _kraken_prepare_weapon():
    import config as _cfg_kraken
    wait_s = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_POST_JOIN_WAIT_SECONDS", 0.5)))
    binding = str(getattr(_cfg_kraken, "KRAKEN_WEAPON_BINDING", None) or getattr(_cfg_kraken, "WEAPON_1_BINDING", "1"))
    time.sleep(wait_s)
    for idx in range(3):
        if not trigger_binding_action(binding, hold_ms=45):
            trigger_binding_action("1", hold_ms=45)
        log.debug(f"[KRAKEN] weapon binding press {idx + 1}/3 ({binding})")
        time.sleep(0.12)


def _kraken_try_menu_resume(reason: str) -> bool:
    global _STONE_LOST
    if not _STONE_LOST:
        # Do not run proactive menu-resume probes during normal route/fight flow.
        return False
    try:
        from dashboard import get_state as _ds
        if not _menu_resume_enabled(_ds()):
            return False
    except Exception:
        return False
    try:
        if not is_in_menu():
            return False
    except Exception:
        return False
    log.warning(f"[KRAKEN] menu detected during {reason}; attempting menu resume")
    if _do_menu_resume():
        log.info("[KRAKEN] menu resume succeeded")
        return True
    log.warning("[KRAKEN] menu resume failed")
    return False


def _kraken_open_menu_via_a7() -> bool:
    import config as _cfg_kraken
    attempts = _route_redo_limit()
    wait_s = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_MENU_WAIT_SECONDS", 0.5)))
    for attempt in range(1, attempts + 1):
        if _KILLED:
            return False
        if _kraken_try_menu_resume("route"):
            continue
        _console_status("KRAKEN", f"Teleport {attempt}/{attempts}")
        _dash_update(status="KRAKEN", goal="Teleport")
        set_overlay(status="KRAKEN", goal="Teleport", run_start_time=0)
        if not _builtin_teleport_safe("area7", attempts=10, wait_seconds=3.5):
            log.warning(f"[KRAKEN] F4 Area 7 teleport failed before kraken macro ({attempt}/{attempts})")
            continue
        _console_status("KRAKEN", f"Navigation {attempt}/{attempts}")
        _dash_update(status="KRAKEN", goal="Navigation")
        set_overlay(status="KRAKEN", goal="Navigation", run_start_time=0)
        if not _run_macro("area7_to_kraken"):
            log.warning(f"[KRAKEN] area7_to_kraken macro failed ({attempt}/{attempts})")
            continue
        time.sleep(wait_s)
        close_ok = _kraken_close_visible()
        join_ok = _kraken_join_visible()
        if close_ok:
            if not join_ok:
                log.warning("[KRAKEN] CLOSE found but JOIN OCR missed; clicking configured JOIN center anyway")
            return True
        log.warning(f"[KRAKEN] boss menu not confirmed after route attempt {attempt}/{attempts}")
    _rec_set_failure("redo_limit:kraken")
    return False


def _kraken_reopen_menu_after_kill():
    """Walk forward for a fixed 3s while spamming E; abort on death screen.

    Returns True (reward menu visible), False (fallback route result), or
    the string "death" if the black/respawn screen appeared during the walk.
    """
    import config as _cfg_kraken
    from macro_runner import _key_up as _mr_key_up

    walk_s = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_REWARD_WALK_SECONDS", 4.0)))
    wait_s = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_REWARD_OPEN_WAIT_SECONDS", 0.5)))
    e_interval = 0.10

    log.info("[KRAKEN] reward walk started (fixed %.1fs, spamming E)", walk_s)
    try:
        from macro_runner import live_wasd, remapped_movement_vks
        fwd_name, fwd_vk = live_wasd().get("w", ("w", 0x57))
        for _vk in remapped_movement_vks():
            try:
                _mr_key_up(_vk)
            except Exception:
                pass
    except Exception:
        fwd_name, fwd_vk = "w", 0x57
        for _vk in (0x57, 0x41, 0x53, 0x44):
            try:
                _mr_key_up(_vk)
            except Exception:
                pass
    for _k in ("w", "a", "s", "d", "shift", "ctrl", fwd_name):
        try:
            keyboard.release(_k)
        except Exception:
            pass
    time.sleep(0.08)

    walk_start = time.time()
    last_e = 0.0
    last_death_check = 0.0
    death_seen = False
    try:
        keyboard.press(fwd_name)
        from macro_runner import _key_down as _mr_key_down
        _mr_key_down(fwd_vk)
        while not _KILLED:
            now = time.time()
            elapsed = now - walk_start
            # Death guard: the kill was confirmed without a black screen, but a
            # late respawn screen can still show up - check while walking.
            if now - last_death_check >= 0.10:
                last_death_check = now
                if is_rebirth_screen():
                    death_seen = True
                    break
            if now - last_e >= e_interval:
                trigger_binding_action("e", hold_ms=50)
                last_e = now
            if elapsed >= walk_s:
                break
            time.sleep(0.02)
    finally:
        try:
            keyboard.release(fwd_name)
        except Exception:
            pass
        try:
            _mr_key_up(fwd_vk)
        except Exception:
            pass

    if death_seen:
        log.info("[KRAKEN] death screen during reward walk - treating as death")
        return "death"

    time.sleep(wait_s)
    ok = _kraken_close_visible()
    if ok:
        log.info("[KRAKEN] reward menu confirmed after fixed walk")
        return ok

    log.warning("[KRAKEN] reward menu not visible after fixed walk - fallback to full teleport route")
    _console_status("KRAKEN", "Reward fallback")
    _dash_update(status="KRAKEN", goal="Teleport")
    set_overlay(status="KRAKEN", goal="Teleport", run_start_time=0)
    return _kraken_open_menu_via_a7()


def _run_kraken_loop():
    import config as _cfg_kraken
    from macro_runner import _mouse_left_down, _mouse_left_up, _smooth_move_rel, _scale_smooth_move

    _dash_update(run_active=True, status="KRAKEN", goal="Navigation", waiting_for_start=False)
    set_overlay(status="KRAKEN", goal="Navigation", run_start_time=0)
    log.info("[KRAKEN] loop started (no ESP, no dodge â€” walk loop + mouse aim)")
    menu_ready = False

    while not _KILLED and not _TEST_FORCE_FAILURE and not _STONE_LOST:
        if not menu_ready:
            if not _kraken_open_menu_via_a7():
                _console_status("KRAKEN", "Menu retry")
                _wait_polling(1.0, "Kraken retry", freeze=False)
                continue
        menu_ready = False

        # â”€â”€ Navigation phase: NO timer shown anywhere â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _console_status("KRAKEN", "Navigation")
        _dash_update(status="KRAKEN", goal="Navigation", run_start_time=None)
        set_overlay(status="KRAKEN", goal="Navigation", run_start_time=0)
        _kraken_click_join_twice()
        _kraken_prepare_weapon()

        # â”€â”€ Wait 1 second after joining before doing anything â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        log.info("[KRAKEN] waiting 1s after join before aiming/shooting/walking")
        _wait_polling(1.0, "Kraken post-join settle", freeze=False)
        if _KILLED:
            break

        # â”€â”€ Smooth mouse aim: -75, -10 over 50ms (sensitivity-scaled) â”€â”€â”€â”€â”€â”€â”€â”€
        aim_dx, aim_dy = _scale_smooth_move(-75, -10)
        log.info("[KRAKEN] smooth mouse aim: raw(-75,-10) scaled(%d,%d) over 50ms", aim_dx, aim_dy)
        _smooth_move_rel(aim_dx, aim_dy, 50)

        # â”€â”€ Activate drill once at start of fight (if enabled) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        try:
            from dashboard import get_state as _ds_krakdrill
            _krak_drill_on = bool(_ds_krakdrill().get("kraken_activate_drills", True))
        except Exception:
            _krak_drill_on = bool(getattr(_cfg_kraken, "KRAKEN_ACTIVATE_DRILLS", True))
        if _krak_drill_on:
            log.info("[KRAKEN] activating drill at fight start")
            _trigger_drill_binding()

        # â”€â”€ Fight phase: timer starts NOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        boss_start = time.time()
        boss_end_reason = "ended"
        _console_status("KRAKEN", "Fight")
        _dash_update(status="KRAKEN", goal="Fight", run_start_time=boss_start)
        set_overlay(status="KRAKEN", goal="Fight", run_start_time=boss_start)
        try:
            from net_guard import set_path_redo as _set_kraken_redo
            _set_kraken_redo(False)
        except Exception:
            pass
        try:
            from dashboard import get_state as _ds_kraken_move
            movement_mode = str(_ds_kraken_move().get("kraken_movement_mode", "linear")).strip().lower()
        except Exception:
            movement_mode = str(getattr(_cfg_kraken, "KRAKEN_MOVEMENT_MODE", "linear")).strip().lower()
        if movement_mode not in {"linear", "square"}:
            movement_mode = "linear"
        log.info("[KRAKEN] movement mode: %s", movement_mode)

        poll_s = max(0.03, float(getattr(_cfg_kraken, "KRAKEN_SHOOT_POLL_SECONDS", 0.1)))
        reassert_s = max(poll_s, float(getattr(_cfg_kraken, "KRAKEN_SHOOT_REASSERT_SECONDS", 0.5)))
        death_wait = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_DEATH_WAIT_SECONDS", 5)))
        hb_confirm_window_s = max(0.5, float(getattr(_cfg_kraken, "KRAKEN_HB_CONFIRM_WINDOW_SECONDS", 1.5)))
        hb_post_loss_shoot_s = max(0.0, float(getattr(_cfg_kraken, "KRAKEN_POST_HB_LOSS_SHOOT_SECONDS", 1.5)))
        first_hb_timeout_s = max(3.0, float(getattr(_cfg_kraken, "KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", 8.0)))

        shooting = False
        kill_detected_at: float | None = None
        _walk_stop = threading.Event()

        def _walk_loop():
            """Background thread: selected movement pattern until _walk_stop."""
            import keyboard as _kb
            try:
                from macro_runner import live_wasd
                _wasd = live_wasd()
            except Exception:
                _wasd = {"w": ("w", 0x57), "a": ("a", 0x41), "s": ("s", 0x53), "d": ("d", 0x44)}
            names = {k: (_wasd.get(k, (k, 0))[0] or k) for k in ("w", "a", "s", "d")}
            held = list(dict.fromkeys(names.values()))
            pattern = (
                [("w", 2.0), ("d", 2.0), ("s", 2.0), ("a", 2.0)]
                if movement_mode == "square"
                else [("s", 2.0), ("w", 2.0)]
            )
            idx = 0
            phase_start = time.time()
            log.info("[KRAKEN] walk loop started")
            while not _walk_stop.is_set():
                key, phase_secs = pattern[idx]
                live = names.get(key, key)
                for k in held:
                    if k == live:
                        _kb.press(k)
                    else:
                        _kb.release(k)
                if (time.time() - phase_start) >= phase_secs:
                    idx = (idx + 1) % len(pattern)
                    phase_start = time.time()
                time.sleep(0.05)
            for k in held:
                try:
                    _kb.release(k)
                except Exception:
                    pass
            log.info("[KRAKEN] walk loop stopped")

        walk_thread = threading.Thread(target=_walk_loop, daemon=True, name="kraken_walk_loop")

        try:
            next_reassert = 0.0
            health_missing_since = None
            health_seen_once = False
            shooting = True
            walk_thread.start()

            while not _KILLED and not _TEST_FORCE_FAILURE:
                now = time.time()

                # â”€â”€ Death while fighting: immediate black screen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if is_rebirth_screen():
                    log.info("[KRAKEN] black screen detected - death; restarting")
                    if shooting:
                        _mouse_left_up()
                        shooting = False
                    boss_end_reason = "death"
                    break

                # â”€â”€ Join failure guard: if health bar never appears, reset route â”€â”€
                if (not health_seen_once) and ((now - boss_start) >= first_hb_timeout_s):
                    log.warning(
                        "[KRAKEN] no health bar seen after %.1fs - treating as join failure and retrying",
                        now - boss_start,
                    )
                    if shooting:
                        _mouse_left_up()
                        shooting = False
                    _walk_stop.set()
                    boss_end_reason = "join_failed"
                    break

                # â”€â”€ Health bar disappeared â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                # Once confirm mode starts (health_missing_since set), we never
                # reset it on temporary OCR flicker. This prevents mouse fire from
                # being re-armed right before Post Fight.
                hb_seen_now = kraken_health_bar_seen()
                if health_missing_since is None:
                    if hb_seen_now:
                        health_seen_once = True
                    elif health_seen_once:
                        health_missing_since = now
                        log.info("[KRAKEN] health bar gone â€” watching for %.1fs to confirm kill vs death", hb_confirm_window_s)
                        if shooting and hb_post_loss_shoot_s > 0:
                            log.info("[KRAKEN] keeping fire for %.1fs after health bar loss", hb_post_loss_shoot_s)
                        elif shooting:
                            _mouse_left_up()
                            shooting = False
                        # Stop walk loop immediately when health bar gone
                        _walk_stop.set()
                else:
                    elapsed = now - health_missing_since
                    if shooting and elapsed >= hb_post_loss_shoot_s:
                        _mouse_left_up()
                        shooting = False
                        log.info("[KRAKEN] post-loss fire window ended at %.2fs", elapsed)
                    if is_rebirth_screen():
                        log.info("[KRAKEN] black screen during confirm window (%.2fs) â†’ death", elapsed)
                        if shooting:
                            _mouse_left_up()
                            shooting = False
                        boss_end_reason = "death"
                        break
                    elif elapsed >= hb_confirm_window_s:
                        kill_detected_at = health_missing_since
                        log.info(
                            "[KRAKEN] %.1fs confirm window passed, no black screen -> boss killed",
                            elapsed,
                        )
                        if shooting:
                            _mouse_left_up()
                            shooting = False
                        boss_end_reason = "killed"
                        break

                # â”€â”€ Assert shooting while health bar is still visible â”€â”€â”€
                if health_missing_since is None:
                    if now >= next_reassert:
                        _mouse_left_down()
                        next_reassert = now + reassert_s
                        log.debug("[KRAKEN] left mouse down asserted")
                    # Drill activation is deliberately not re-checked or
                    # re-triggered here.  The start-of-fight path above is
                    # the single activation attempt for this fight.  The old
                    # timer path pressed the drill repeatedly whenever its
                    # unreliable active-state detection flickered.

                if _kraken_try_menu_resume("boss fight"):
                    boss_end_reason = "menu_resume"
                    break
                time.sleep(poll_s)
        finally:
            try:
                from net_guard import set_path_redo as _set_kraken_redo
                _set_kraken_redo(True)
            except Exception:
                pass
            if shooting:
                _mouse_left_up()
            _walk_stop.set()
            walk_thread.join(timeout=1.0)
            if _KILLED:
                boss_end_reason = "stopped"
            # â”€â”€ Fight ended: immediately clear timer from overlay + dashboard â”€â”€
            _dash_update(status="KRAKEN", goal="Finish", run_start_time=None)
            set_overlay(status="KRAKEN", goal="Finish", run_start_time=0)
            _console_status("KRAKEN", "Finish")
            if boss_end_reason in {"killed", "death"} and boss_start:
                fight_duration = (kill_detected_at or time.time()) - boss_start
                try:
                    _dash_record_kraken_run(fight_duration, boss_end_reason)
                    log.info(f"[KRAKEN] run recorded: {fight_duration:.1f}s ({boss_end_reason})")
                except Exception as e:
                    log.debug(f"[KRAKEN] timing record failed: {e}")

        if _KILLED or _TEST_FORCE_FAILURE:
            break
        if boss_end_reason == "join_failed":
            _dash_update(status="KRAKEN", goal="Navigation", run_start_time=None)
            set_overlay(status="KRAKEN", goal="Navigation", run_start_time=0)
            continue
        if boss_end_reason == "killed":
            _dash_update(status="KRAKEN", goal="Post Fight", run_start_time=None)
            set_overlay(status="KRAKEN", goal="Post Fight", run_start_time=0)
            _console_status("KRAKEN", "Post Fight")
            # Walk to re-enter the fight right away - no extra settle wait.
            outcome = _kraken_reopen_menu_after_kill()
            if outcome == "death":
                log.info("[KRAKEN] late death after kill - waiting for respawn")
            elif outcome:
                menu_ready = True
                # Back to navigation - timer stays cleared until next fight starts
                _dash_update(status="KRAKEN", goal="Navigation", run_start_time=None)
                set_overlay(status="KRAKEN", goal="Navigation", run_start_time=0)
                continue
        # Death / stopped / other: wait for respawn, no timer
        _dash_update(status="KRAKEN", goal="Finish", run_start_time=None)
        set_overlay(status="KRAKEN", goal="Finish", run_start_time=0)
        _wait_polling(death_wait, "Kraken respawn", freeze=True)

    _dash_update(run_active=False, run_start_time=None, waiting_for_start=True, status="WAITING", goal="Ready")
    set_overlay(status="WAITING", goal="Ready", run_start_time=0)
    stop_kraken_esp()
    stop_kraken_dodge()
    log.info("[KRAKEN] loop stopped")



def _run_zytos_loop():
    """Zytos mode entry point — own package, no kraken/delve calls."""
    try:
        from zytos.loop import run_zytos
        run_zytos()
    except Exception as e:
        cprint(f"Zytos mode error: {e}", "err")
        log.error(f"Zytos mode error: {e}")
        import traceback
        traceback.print_exc()



def _run_delve_loop():
    import config as _cfg_delve
    from macro_runner import _mouse_left_down, _mouse_left_up

    _dash_update(run_active=True, status="DELVE", goal="Navigation", waiting_for_start=False)
    set_overlay(status="DELVE", goal="Navigation")
    log.info(
        "[DELVE] runtime=%sx%s scale=%.3fx%.3f close_region=%s join_region=%s join_center=%s",
        getattr(_cfg_delve, "RUNTIME_WIDTH", "?"),
        getattr(_cfg_delve, "RUNTIME_HEIGHT", "?"),
        float(getattr(_cfg_delve, "REGION_SCALE_X", 1.0)),
        float(getattr(_cfg_delve, "REGION_SCALE_Y", 1.0)),
        getattr(_cfg_delve, "DELVE_CLOSE_REGION", None),
        getattr(_cfg_delve, "DELVE_JOIN_REGION", None),
        getattr(_cfg_delve, "DELVE_JOIN_CENTER", None),
    )
    log.info("[DELVE] loop started")
    while not _KILLED:
        if not _delve_open_menu_via_a5():
            _console_status("DELVE", "Menu retry")
            _wait_polling(1.0, "Delve retry", freeze=False)
            continue

        _console_status("DELVE", "Navigation")
        _dash_update(status="DELVE", goal="Navigation")
        set_overlay(status="DELVE", goal="Navigation")
        _delve_click_join_twice()
        _delve_prepare_weapon()

        # â”€â”€ Activate drill once at start of fight (if enabled) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        try:
            from dashboard import get_state as _ds_delvedrill
            _delve_drill_on = bool(_ds_delvedrill().get("delve_activate_drills", True))
        except Exception:
            _delve_drill_on = bool(getattr(_cfg_delve, "DELVE_ACTIVATE_DRILLS", True))
        if _delve_drill_on:
            log.info("[DELVE] activating drill at fight start")
            _trigger_drill_binding()

        boss_start = time.time()
        boss_end_reason = "ended"
        _console_status("DELVE", "Fight")
        _dash_update(status="DELVE", goal="Fight", run_start_time=boss_start)
        set_overlay(status="DELVE", goal="Fight", run_start_time=boss_start)
        try:
            from net_guard import set_path_redo as _set_delve_redo
            _set_delve_redo(False)
        except Exception:
            pass
        poll_s = max(0.03, float(getattr(_cfg_delve, "DELVE_SHOOT_POLL_SECONDS", 0.1)))
        reassert_s = max(poll_s, float(getattr(_cfg_delve, "DELVE_SHOOT_REASSERT_SECONDS", 0.5)))
        death_wait = max(0.0, float(getattr(_cfg_delve, "DELVE_DEATH_WAIT_SECONDS", 5)))
        shooting = False
        try:
            next_reassert = 0.0
            shooting = True
            death_hits = 0
            while not _KILLED:
                if time.time() >= next_reassert:
                    _mouse_left_down()
                    next_reassert = time.time() + reassert_s
                    log.debug("[DELVE] left mouse down asserted")
                if is_rebirth_screen():
                    death_hits += 1
                    if death_hits >= 2:
                        log.info("[DELVE] black/dark death screen confirmed - boss run ended/death; restarting")
                        boss_end_reason = "death"
                        break
                else:
                    death_hits = 0
                if _delve_try_menu_resume("boss fight"):
                    boss_end_reason = "menu_resume"
                    break
                time.sleep(poll_s)
        finally:
            try:
                from net_guard import set_path_redo as _set_delve_redo
                _set_delve_redo(True)
            except Exception:
                pass
            if shooting:
                _mouse_left_up()
            if _KILLED:
                boss_end_reason = "stopped"
            if boss_start:
                _console_status("DELVE", "Finish")
                _dash_update(status="DELVE", goal="Finish", run_start_time=None)
                set_overlay(status="DELVE", goal="Finish", run_start_time=0)
                try:
                    _dash_record_delve_run(time.time() - boss_start, boss_end_reason)
                except Exception as e:
                    log.debug(f"[DELVE] timing record failed: {e}")

        if _KILLED:
            break
        _console_status("DELVE", "Finish")
        _dash_update(status="DELVE", goal="Finish", run_start_time=None)
        set_overlay(status="DELVE", goal="Finish", run_start_time=0)
        _wait_polling(death_wait, "Delve respawn", freeze=True)

    _dash_update(run_active=False, run_start_time=None, waiting_for_start=True, status="WAITING", goal="Ready")
    set_overlay(status="WAITING", goal="Ready", run_start_time=0)
    log.info("[DELVE] loop stopped")


def run_bot():
    global _KILLED, _STONE_LOST, _TEST_FORCE_FAILURE, _WAITING_FOR_START, _LOADOUT_BLOCKED
    global _DRILLS_UNLOCKED, _A5_UNLOCKED_THIS_RUN, _AREA_UNLOCKED_THIS_RUN, _RUN_MODE, _ACTIVATE_DRILLS
    global _menu_resume_fresh_start, _at_base, _QUESTS_DONE_THIS_RUN, _QUESTS_STARTED_THIS_RUN, _QUEST_PLAN

    _register_hotkeys()
    _ensure_low_level_hook()
    _ensure_hotkey_poll_failsafe()
    _ensure_win_hotkey_poll_failsafe()
    start_overlay()
    # dashboard already started at module level before auth

    if _auto_strength_enabled():
        set_overlay(status="WAITING", goal="Ready", show_auto_str=True)
    else:
        set_overlay(status="WAITING", goal="Ready", auto_str=None, show_auto_str=False)
    _teleport_set_killed_fn(lambda: _KILLED or _TEST_FORCE_FAILURE)
    try:
        from quest_menu import set_killed_fn as _quest_set_killed_fn
        _quest_set_killed_fn(lambda: _KILLED or _TEST_FORCE_FAILURE)
    except Exception:
        pass
    try:
        from net_guard import start as _net_start
        _net_start()
    except Exception:
        pass
    try:
        import display_probe as _display_probe
        _display_probe.start()
    except Exception as _display_e:
        log.warning(f"[DISPLAY] probe failed to start: {_display_e}")
    log.info("Bot starting ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â waiting for dashboard Start")

    # Outer loop: soft-reset (F9) brings us back here each time
    while True:
        # suspension check removed — bot is free for all logged-in users
        _soft_reset_state()

        # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Inner run loop ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
        _just_started = True  # first iteration does startup click; subsequent runs skip it
        while not _KILLED:
            # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Wait for Start button ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
            _wait_for_start()
            if _KILLED:
                break
            _missing_lo = missing_required_loadouts()
            if _missing_lo:
                _block_for_missing_loadouts(_missing_lo)
                continue

            if missing_game_detection():
                _block_for_missing_game_detection()
                continue

            if not is_fortnite_focused():
                log.info("Waiting for Fortnite focus before starting run...")
                if not wait_for_fortnite_focus():
                    log.critical("Fortnite never focused — retrying after delay")
                    time.sleep(1)
                    continue

            # Startup click — only on first run after launch or F9.
            if _just_started:
                log.info("Startup click — activating game input")
                from macro_runner import _mouse_left_click as _startup_click
                _startup_click()
                log.info("Startup delay ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â quick settle before first macro")
                import config as _cfg_runtime
                try:
                    _startup_settle = float(_cfg_runtime.startup_settle())
                except Exception:
                    _startup_settle = min(1.0, max(0.0, float(getattr(_cfg_runtime, "STARTUP_SETTLE_SECONDS", 0.20))))
                _startup_deadline = time.time() + _startup_settle
                _startup_in_game = False
                while time.time() < _startup_deadline:
                    if _KILLED or _STONE_LOST:
                        break
                    if _stone_icon_visible_restart_image() and is_fortnite_focused():
                        _startup_in_game = True
                        break
                    time.sleep(0.05)
                if _KILLED or _STONE_LOST:
                    _just_started = False
                elif not _startup_in_game and _fresh_start_not_in_game():
                    # In-Game image detection says we are NOT in game (lobby /
                    # loading). Do NOT touch the loadout first — go straight
                    # to the three-state / lobby-menu recovery, which checks
                    # the selected game and rejoins Miner Tycoon 2.
                    log.info("[FR_FLOW] fresh start: not in game — menu recovery before loadout")
                    from dashboard import get_state as _ds_lo_ng
                    _ds_lo = {}
                    try:
                        _ds_lo = _ds_lo_ng() or {}
                    except Exception:
                        pass
                    if not _KILLED and _try_force_restart_after_failure("fresh_start_not_in_game", _ds_lo):
                        _just_started = True
                        continue
                    if not _KILLED and _menu_resume_enabled(_ds_lo):
                        if _do_menu_resume():
                            _WAITING_FOR_START = False
                            _at_base = False
                            _menu_resume_fresh_start = True
                            _just_started = True
                            continue
                    log.warning("[LOADOUT] fresh-start recovery failed — waiting for Start")
                    _WAITING_FOR_START = True
                    _just_started = True
                    continue
                elif not _apply_fresh_start_loadout():
                    log.warning("[LOADOUT] fresh-start select failed")
                    from dashboard import get_state as _ds_lo_fail
                    _ds_lo = {}
                    try:
                        _ds_lo = _ds_lo_fail() or {}
                    except Exception:
                        pass
                    if not _KILLED and _try_force_restart_after_failure("fresh_start_loadout_ui_failed", _ds_lo):
                        _just_started = True
                        continue
                    if not _KILLED and _menu_resume_enabled(_ds_lo):
                        if _do_menu_resume():
                            _WAITING_FOR_START = False
                            _at_base = False
                            _menu_resume_fresh_start = True
                            _just_started = True
                            continue
                    log.warning("[LOADOUT] recovery failed — waiting for Start")
                    _WAITING_FOR_START = True
                    _just_started = True
                    continue
                else:
                    _just_started = False
            else:
                log.debug("Continuing run — skipping startup click/delay")

            _DRILLS_UNLOCKED = False
            _A5_UNLOCKED_THIS_RUN = False
            _AREA_UNLOCKED_THIS_RUN = {1: False, 2: False, 3: False, 4: False, 5: False}
            _QUESTS_DONE_THIS_RUN = False
            _QUESTS_STARTED_THIS_RUN = False
            _QUEST_PLAN = None


            from dashboard import get_state as _ds
            _ds_snap = _ds()
            _bot_mode = str(_ds_snap.get("bot_mode", "rebirth")).lower()
            if _bot_mode == "kraken":
                _start_stone_watcher()   # stone icon watcher for kraken mode too
                try:
                    _run_kraken_loop()
                finally:
                    _stop_stone_watcher()

                # Handle test force failure (arrow down) same as rebirth mode
                _test_force_failure = bool(_TEST_FORCE_FAILURE)
                if _test_force_failure:
                    log.warning("[TEST_FAIL] simulated failure reached kraken handler")
                    _rec_set_failure("test_force_restart_hotkey")
                    _TEST_FORCE_FAILURE = False

                if _KILLED:
                    continue

                # Stone-lost recovery: try force restart or menu resume
                if _STONE_LOST and not _KILLED:
                    _dash_update(run_active=False, run_start_time=None)
                    _capture_failure_fullscreen("run_failed")
                    _ds_snap_sl = _ds()
                    _wait_secs = _ds_snap_sl.get("stone_icon_missing_wait") or 5
                    log.info(f"[KRAKEN] Stone lost — initial wait {_wait_secs}s")
                    _console_status("STONE LOST", "Recovering...")
                    set_overlay(status="STONE LOST", goal="Recovering...")
                    if not _hold_for_network():
                        continue
                    if _stone_icon_visible_restart_image():
                        log.info("[KRAKEN] HUD back after network wait — resume")
                        _STONE_LOST = False
                        continue
                    _wait_polling(float(_wait_secs), "...", freeze=True)

                    if not _KILLED:
                        if _try_force_restart_after_failure("stone_lost", _ds_snap_sl):
                            _STONE_LOST = False
                            _WAITING_FOR_START = False
                            continue
                        if _menu_resume_enabled(_ds_snap_sl):
                            import config as _cfg_kraken_sl
                            _appear_secs = float(getattr(_cfg_kraken_sl, "MENU_APPEAR_WAIT", 60))
                            _console_status("MENU RESUME", "...")
                            set_overlay(status="MENU RESUME", goal="...")
                            _appear_deadline = time.time() + _appear_secs
                            while time.time() < _appear_deadline and not _KILLED:
                                if _stone_icon_visible_restart_image() or is_in_menu():
                                    break
                                _wait_polling(0.25, "...", freeze=True)
                            if not _KILLED:
                                resume_ok = _do_menu_resume()
                                if resume_ok:
                                    log.info("[KRAKEN] Menu resume succeeded — resuming kraken loop")
                                    _STONE_LOST = False
                                    _WAITING_FOR_START = False
                                    continue
                                else:
                                    log.warning("[KRAKEN] Menu resume failed — falling back to wait-for-start")
                                    time.sleep(1)
                        _STONE_LOST = False

                # Handle test force failure: try force restart
                if _test_force_failure and not _KILLED:
                    _ds_snap_tf = _ds()
                    if _try_force_restart_after_failure("test_force_restart_hotkey", _ds_snap_tf):
                        _TEST_FORCE_FAILURE = False
                        _WAITING_FOR_START = False
                        continue
                    if not _KILLED and _menu_resume_enabled(_ds_snap_tf):
                        resume_ok = _do_menu_resume()
                        if resume_ok:
                            log.info("[KRAKEN] Menu resume after test failure — resuming")
                            _TEST_FORCE_FAILURE = False
                            _WAITING_FOR_START = False
                            continue
                        else:
                            log.warning("[KRAKEN] Menu resume failed after test failure")
                            time.sleep(1)

                if not _KILLED:
                    _WAITING_FOR_START = True
                continue
            if _bot_mode == "zytos":
                _start_stone_watcher()   # stone icon watcher for zytos mode too
                try:
                    _run_zytos_loop()
                finally:
                    _stop_stone_watcher()

                # Handle test force failure (arrow down) same as rebirth mode
                _test_force_failure = bool(_TEST_FORCE_FAILURE)
                if _test_force_failure:
                    log.warning("[TEST_FAIL] simulated failure reached zytos handler")
                    _rec_set_failure("test_force_restart_hotkey")
                    _TEST_FORCE_FAILURE = False

                if _KILLED:
                    continue

                # Stone-lost recovery: try force restart or menu resume
                if _STONE_LOST and not _KILLED:
                    _dash_update(run_active=False, run_start_time=None)
                    _capture_failure_fullscreen("run_failed")
                    _ds_snap_sl = _ds()
                    _wait_secs = _ds_snap_sl.get("stone_icon_missing_wait") or 5
                    log.info(f"[ZYTOS] Stone lost — initial wait {_wait_secs}s")
                    _console_status("STONE LOST", "Recovering...")
                    set_overlay(status="STONE LOST", goal="Recovering...")
                    if not _hold_for_network():
                        continue
                    if _stone_icon_visible_restart_image():
                        log.info("[ZYTOS] HUD back after network wait — resume")
                        _STONE_LOST = False
                        continue
                    _wait_polling(float(_wait_secs), "...", freeze=True)

                    if not _KILLED:
                        if _try_force_restart_after_failure("stone_lost", _ds_snap_sl):
                            _STONE_LOST = False
                            _WAITING_FOR_START = False
                            continue
                        if _menu_resume_enabled(_ds_snap_sl):
                            import config as _cfg_zytos_sl
                            _appear_secs = float(getattr(_cfg_zytos_sl, "MENU_APPEAR_WAIT", 60))
                            _console_status("MENU RESUME", "...")
                            set_overlay(status="MENU RESUME", goal="...")
                            _appear_deadline = time.time() + _appear_secs
                            while time.time() < _appear_deadline and not _KILLED:
                                if _stone_icon_visible_restart_image() or is_in_menu():
                                    break
                                _wait_polling(0.25, "...", freeze=True)
                            if not _KILLED:
                                resume_ok = _do_menu_resume()
                                if resume_ok:
                                    log.info("[ZYTOS] Menu resume succeeded — resuming zytos loop")
                                    _STONE_LOST = False
                                    _WAITING_FOR_START = False
                                    continue
                                else:
                                    log.warning("[ZYTOS] Menu resume failed — falling back to wait-for-start")
                                    time.sleep(1)
                        _STONE_LOST = False

                # Handle test force failure: try force restart
                if _test_force_failure and not _KILLED:
                    _ds_snap_tf = _ds()
                    if _try_force_restart_after_failure("test_force_restart_hotkey", _ds_snap_tf):
                        _TEST_FORCE_FAILURE = False
                        _WAITING_FOR_START = False
                        continue
                    if not _KILLED and _menu_resume_enabled(_ds_snap_tf):
                        resume_ok = _do_menu_resume()
                        if resume_ok:
                            log.info("[ZYTOS] Menu resume after test failure — resuming")
                            _TEST_FORCE_FAILURE = False
                            _WAITING_FOR_START = False
                            continue
                        else:
                            log.warning("[ZYTOS] Menu resume failed after test failure")
                            time.sleep(1)

                if not _KILLED:
                    _WAITING_FOR_START = True
                continue
            if _bot_mode == "delve":
                _run_delve_loop()
                if not _KILLED:
                    _WAITING_FOR_START = True
                continue
            if _bot_mode == "crater":
                _run_crater_loop()
                if not _KILLED:
                    _WAITING_FOR_START = True
                continue
            if _bot_mode == "farm_meteor":
                _start_stone_watcher()   # stone icon watcher for farm meteor mode too
                try:
                    _run_farm_meteor_loop()
                finally:
                    _stop_stone_watcher()
                if not _KILLED:
                    _WAITING_FOR_START = True
                continue
            _RUN_MODE        = _normalize_start_mode(_ds_snap.get("run_mode", "a1s1"))
            _ACTIVATE_DRILLS = _CFG_ACTIVATE_DRILLS
            log.debug(f"Run config: mode={_RUN_MODE}, activate_drills={_ACTIVATE_DRILLS}, recorder=always_on")

            start_mode = _RUN_MODE
            start_stone = None
            try:
                from screen import read_stone as _read_start_stone
                start_stone = _read_start_stone()
            except Exception:
                start_stone = None
            if start_stone is None and _last_live_stone is not None:
                start_stone = _last_live_stone
                log.debug(f"start stone OCR miss — using last live {_fmt_stone(start_stone)}")
            stats.start_run(start_stone=start_stone, start_mode=start_mode)
            _dash_update(
                run_active=True,
                status="RUNNING",
                run_start_time=stats._current_run.start_time if stats._current_run else time.time(),
                run_number=stats._current_run.run_number if stats._current_run else 0,
                run_steps=0,
                run_errors=0,
                run_quests_completed=0,
                waiting_for_start=False,
            )
            # Ã¢â€â‚¬Ã¢â€â‚¬ Start run recorder (always on) Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
            try:
                import config as _cfg_rec
                _rec_thresholds = {
                    "stage1": getattr(_cfg_rec, "STONE_FOR_A5_STAGE1", 0),
                    "stage2": getattr(_cfg_rec, "STONE_FOR_A5_STAGE2", 0),
                    "stage3": getattr(_cfg_rec, "STONE_FOR_A5_STAGE3", 0),
                    "stage4": getattr(_cfg_rec, "STONE_FOR_A5_STAGE4", 0),
                    "meteor": getattr(_cfg_rec, "STONE_FOR_METEOR", 0),
                }
                _run_num = stats._current_run.run_number if stats._current_run else 0
                _get_recorder().start_run(run_number=_run_num, thresholds=_rec_thresholds)
            except Exception as _rec_e:
                log.debug(f"[Recorder] start_run error: {_rec_e}")
            _run_start_ts = stats._current_run.start_time if stats._current_run else time.time()
            if _auto_strength_enabled():
                set_overlay(status="RUNNING", goal="Base Rock", show_auto_str=True, run_start_time=_run_start_ts)
            else:
                _disable_auto_strength_for_manual("run start")
                set_overlay(status="RUNNING", goal="Base Rock", auto_str=None, show_auto_str=False, run_start_time=_run_start_ts)
            log.info(f"Run mode={_RUN_MODE}, starting from: {start_mode}  stone={start_stone}")

            # v1.8.32: accept (Start) the daily quests right at run start so
            # rock quests can progress naturally during the grind; the doing
            # + claiming stays in the end-of-run quest phase, which skips any
            # quest already Done on the HUD before teleporting anywhere.
            if _quests_enabled():
                _start_daily_quests()
                if _KILLED or _STONE_LOST:
                    break

            run_ok = False
            _start_stone_watcher()   # always-on icon check (every 1s in background)
            try:
                run_ok = _run_progression_cycle(start_mode)
            except Exception as e:
                log.exception(f"Unexpected error in run cycle: {e}")
                stats.record_error()
            finally:
                _stop_stone_watcher()

            _test_force_failure = bool(_TEST_FORCE_FAILURE)
            if _test_force_failure:
                log.warning("[TEST_FAIL] simulated failure reached run handler")
                _rec_set_failure("test_force_restart_hotkey")
                run_ok = False
                _TEST_FORCE_FAILURE = False

            if _KILLED:
                break

            # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Stone-lost recovery (watcher fired mid-run) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
            if _STONE_LOST and not _KILLED:
                stats.record_error()
                _dash_update(run_active=False, run_start_time=None)
                _capture_failure_fullscreen("run_failed")
                from dashboard import get_state as _ds_sl
                _ds_sl_snap = _ds_sl()
                import config as _cfg_sl

                # Step 1: brief initial wait (stone icon missing debounce)
                _wait_secs = _ds_sl_snap.get("stone_icon_missing_wait") or getattr(_cfg_sl, "STONE_ICON_MISSING_WAIT", 5)
                log.info(f"[WATCHER] Stone lost ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â initial wait {_wait_secs}s")
                _console_status("STONE LOST", "Recovering...")
                if not _hold_for_network():
                    break
                if _stone_icon_visible_restart_image():
                    log.info("[WATCHER] HUD back after network wait — resume")
                    _STONE_LOST = False
                    continue
                set_overlay(status="STONE LOST", goal="Recovering...")
                _wait_polling(float(_wait_secs), "...", freeze=True)

                if not _KILLED:
                    if _try_force_restart_after_failure("stone_lost", _ds_sl_snap):
                        _just_started = True
                        continue

                    if _menu_resume_enabled(_ds_sl_snap):
                        # Step 2: wait for menu to appear after kick before checking
                        _appear_secs = float(getattr(_cfg_sl, "MENU_APPEAR_WAIT", 60))
                        log.info("...")
                        _console_status("MENU RESUME", "...")
                        set_overlay(status="MENU RESUME", goal="...")
                        _appear_deadline = time.time() + _appear_secs
                        while time.time() < _appear_deadline and not _KILLED:
                            if _stone_icon_visible_restart_image() or is_in_menu():
                                break
                            _wait_polling(0.25, "...", freeze=True)

                        if not _KILLED:
                            # Step 3: check for menu and attempt resume
                            log.info("[WATCHER] Checking for menu and attempting resume")
                            resume_ok = _do_menu_resume()
                            if resume_ok:
                                log.info("[WATCHER] Menu resume succeeded ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â starting fresh run from base")
                                _WAITING_FOR_START = False
                                _STONE_LOST = False
                                _at_base = False  # player just spawned ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not at base
                                _menu_resume_fresh_start = True
                                _just_started = True  # fresh game ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â need startup click/delay before first macro
                                continue
                            else:
                                # Step 4: check stone icon ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â maybe we're already back in game
                                log.warning("[WATCHER] Menu resume failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â checking if stone icon came back")
                                time.sleep(2)
                                if _stone_icon_visible_restart_image():
                                    log.info("[WATCHER] Stone icon visible after failed menu resume ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â resuming run")
                                    _STONE_LOST = False
                                    _WAITING_FOR_START = False
                                    continue
                                else:
                                    # Stone still gone, menu not found ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â soft kill
                                    log.warning("[WATCHER] Stone icon still gone after menu resume failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â soft killing")
                                    _console_status("STONE LOST", "Recovery failed")
                                    set_overlay(status="WAITING", goal="Stone lost")
                                    _capture_failure_fullscreen("stone_lost_recovery_failed")
                                    _KILLED = True
                    else:
                        log.info("[WATCHER] menu_resume OFF ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â soft-kill, waiting for Start")
                        _console_status("STONE LOST", "Stone lost ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â soft kill (menu resume OFF)")
                        set_overlay(status="WAITING", goal="Stone lost")
                        _capture_failure_fullscreen("stone_lost_menu_resume_off")
                        _KILLED = True

                _STONE_LOST = False
                continue   # loop back (either to _wait_for_start via _KILLED path, or clean restart)

            if run_ok:
                stats.finish_run()
                gs = stats.global_stats
                _dash_update(
                    run_active=False,
                    run_start_time=None,
                    total_rebirths=gs.total_rebirths,
                    total_errors=gs.total_errors,
                    avg_time_secs=gs.average_time_secs,
                    min_time_secs=gs.min_time_secs,
                    max_time_secs=gs.max_time_secs,
                    run_history=gs.run_history,
                )
                # Ã¢â€â‚¬Ã¢â€â‚¬ Stop recorder on successful rebirth Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
                try:
                    _rec = _get_recorder()
                    if _rec.is_active():
                        _last_stone = _state_stone_snapshot()
                        _rec.stop_run(final_stone=_last_stone, status="rebirth_complete")
                except Exception as _rec_e:
                    log.debug(f"[Recorder] stop_run error: {_rec_e}")
            else:
                if _LOADOUT_BLOCKED:
                    _LOADOUT_BLOCKED = False
                    _WAITING_FOR_START = True
                    continue
                stats.record_error()
                _dash_update(run_active=False, run_start_time=None)
                _failure_reason = "test_force_restart_hotkey" if _test_force_failure else "run_failed"
                _capture_failure_fullscreen(_failure_reason)
                # Ã¢â€â‚¬Ã¢â€â‚¬ Stop recorder on failed run Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
                try:
                    _rec = _get_recorder()
                    if _rec.is_active():
                        if not getattr(_rec, "_failure_reason", None):
                            _rec.set_failure_reason(_failure_reason if _test_force_failure else "run_failed_unspecified")
                        _rec.stop_run(final_stone=None, status=_failure_reason)
                except Exception as _rec_e:
                    log.debug(f"[Recorder] stop_run error: {_rec_e}")

                # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Auto menu resume on run failure ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
                from dashboard import get_state as _ds_mr
                _ds_mr_snap = _ds_mr()
                if _try_force_restart_after_failure(_failure_reason, _ds_mr_snap):
                    _just_started = True
                    continue
                if not _KILLED and _menu_resume_enabled(_ds_mr_snap):
                    # Read join-wait from live dashboard state (updated when user saves config)
                    # Falls back to config module, then hardcoded default
                    import config as _cfg_mr2
                    _configured_wait = float(_ds_mr_snap.get("menu_resume_join_wait") or getattr(_cfg_mr2, "MENU_RESUME_JOIN_WAIT", 120))
                    pre_wait = min(10.0, _configured_wait)
                    log.info(f"[MENU_RESUME] Run failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â waiting {pre_wait} s then attempting menu resume")
                    _console_status("MENU RESUME", "...")
                    set_overlay(status="WAITING", goal="...")
                    _pre_deadline = time.time() + float(pre_wait)
                    while time.time() < _pre_deadline and not _KILLED:
                        if _stone_icon_visible_restart_image() or is_in_menu():
                            break
                        _wait_polling(0.25, "...", freeze=False)
                    if not _KILLED:
                        resume_ok = _do_menu_resume()
                        if resume_ok:
                            log.info("[MENU_RESUME] Resume succeeded ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â starting fresh run from base")
                            # Skip _wait_for_start: mark bot as active and continue
                            _WAITING_FOR_START = False
                            _at_base = False  # player just spawned ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not at base
                            _menu_resume_fresh_start = True
                            _just_started = True  # fresh game ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â need startup click/delay before first macro
                            continue
                        else:
                            log.warning("[MENU_RESUME] Resume failed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â falling back to normal wait-for-start")
                            time.sleep(1)
                else:
                    time.sleep(1)

        # _KILLED=True means F9 was pressed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â soft reset and loop back to waiting
        log.info("F9 soft reset: stopping macros, resetting state, waiting for Start")
        _register_hotkeys()   # re-register every loop so F9 survives game focus changes
        # Ã¢â€â‚¬Ã¢â€â‚¬ Stop recorder WITHOUT uploading (F9 = mid-run abort, not a complete run) Ã¢â€â‚¬Ã¢â€â‚¬
        try:
            _rec = _get_recorder()
            if _rec.is_active():
                _rec.stop_run(final_stone=_state_stone_snapshot(), status="stopped")
                
        except Exception as _rec_f9_e:
            log.debug(f"[Recorder] stop_run (F9) error: {_rec_f9_e}")
        _stop_stone_watcher()
        _close_hit_macro()
        stop_macro()
        _stop_drill_loop()
        if _auto_strength_enabled():
            disable_auto_strength()
            set_overlay(status="WAITING", goal="Ready", show_auto_str=True)
        else:
            _disable_auto_strength_for_manual("soft reset")
            set_overlay(status="WAITING", goal="Ready", auto_str=None, show_auto_str=False)
        _dash_update(killed=False, bot_alive=True, run_active=False,
                     status="WAITING", goal="Ready",
                     waiting_for_start=True)
        log.info("Soft reset complete")




if __name__ == "__main__":
    import sys as _sys_main

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ --webview mode: just open the embedded browser window ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    # When the main EXE is re-launched with --webview (by start_dashboard),
    # this process's sole job is to show the pywebview window.  It exits when
    # the window is closed.  This gives pywebview its own main thread (required
    # by the WinForms/edgechromium COM STA model).
    if "--webview" in _sys_main.argv:
        import time as _t
        _t.sleep(0.5)          # brief wait for Flask to be ready
        try:
            import webview
            webview.create_window(
                "MT2 Rebirth Bot",
                "http://127.0.0.1:7373",
                width=1100, height=760,
                resizable=True, min_size=(900, 600),
            )
            webview.start()
        except Exception as _wve:
            import webbrowser
            webbrowser.open("http://127.0.0.1:7373")
        import sys; sys.exit(0)

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Normal mode ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    # main thread  ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ tkinter overlay mainloop (Windows requires this)
    # thread       ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Flask server             (started inside start_dashboard)
    # process      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ pywebview window         (separate process, own main thread)
    # thread       ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ bot logic + auth wait

    def _bot_main():
        run_bot()

    bot_thread = threading.Thread(target=_bot_main, daemon=True, name="bot")
    bot_thread.start()

    # Start Flask (+ pywebview in dev) ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â returns immediately
    start_dashboard()

    # Give main thread to tkinter overlay (blocks here until process exits)
    from overlay import run_overlay_mainloop
    run_overlay_mainloop()

    # run_overlay_mainloop only returns if tkinter crashes/exits.
    # Keep process alive as long as bot thread is running.
    bot_thread.join()
