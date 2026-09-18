# ============================================================
# MT2 BOT - RUN RECORDER  (v4.1)
# Records full rebirth runs as training data â€” NO screenshots.
#
# What is recorded:
#   actions.jsonl  â€” every key/mouse action + bot actions (teleport, macro, etc.)
#                    each entry has: t, tick, type, key/action, stone, stage
#   events.jsonl   â€” state ticks every second + stage transitions + start/stop
#                    each tick has: t, tick, stone, stage, status, goal,
#                    auto_strength, activate_drills, run_mode, run_number
#   metadata.json  â€” full run metadata + ALL config values + ALL sidebar settings
#   notes.md       â€” human-readable run summary
#
# No frames/ folder, no annotations/ folder, no screenshots whatsoever.
# Recording is always enabled by the bot runtime.
# Write strategy:
#   - Data is first written to a temp folder: run_recordings/_temp_<run_id>/
#   - On clean completion (rebirth or failure), temp is atomically moved to:
#       run_recordings/run_<timestamp>/
#   - Incomplete runs (F9 / crash) stay in _temp_ and are ignored at startup.
#     They are not finalized and are ignored on startup.
#
# Output per completed run:
#   <BOT_ROOT>/run_recordings/run_YYYYMMDD_HHMMSS/
#   â”œâ”€â”€ actions.jsonl
#   â”œâ”€â”€ events.jsonl
#   â”œâ”€â”€ metadata.json
#   â””â”€â”€ notes.md
#
# Changes in v4.2 (vs v4.1):
#   - Recorder root moved to system temp directory by default.
#   - Completed runs stay in run_recordings/ locally.
#   - All recorder activity is silent in logs (debug-level only).
#     Only genuine errors (file I/O failures) emit warnings.
# ============================================================

from __future__ import annotations

import json
import math
import os
import platform
import shutil
import tempfile
import threading
import time
from datetime import datetime, timezone

from logger import get_logger
from config import BOT_DIR
from version import __version__ as BOT_VERSION

log = get_logger()

# â”€â”€ Recorder version â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# recorder_version and recording_schema_version not included in metadata — only bot_version

# â”€â”€ Output root â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_BOT_ROOT = BOT_DIR
RECORDS_DIR = os.environ.get(
    "MT2_RECORDER_DIR",
    os.path.join(tempfile.gettempdir(), "MT2RebirthBot", "run_recordings"),
)


# â”€â”€ Keyboard hook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import keyboard as _keyboard
    _HAS_KEYBOARD = True
except ImportError:
    _HAS_KEYBOARD = False


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helpers
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _fmt_stone(v) -> str:
    if v is None:
        return "?"
    try:
        v = float(v)
        if v <= 0:
            return "0"
        exp = int(math.floor(math.log10(abs(v))))
        _SUFFIXES = [
            (3,  "k"),  (6,  "M"),  (9,  "B"),  (12, "T"),
            (15, "Qa"), (18, "Qi"), (21, "Sx"),  (24, "Sp"),
            (27, "Oc"), (30, "No"), (33, "Dc"),
        ]
        chosen_suffix, chosen_exp = None, 0
        for _exp, _suf in _SUFFIXES:
            if exp >= _exp:
                chosen_suffix, chosen_exp = _suf, _exp
        if chosen_suffix and exp <= 57:
            return f"{v / (10 ** chosen_exp):.2f}{chosen_suffix}"
        return f"{v:.2e}"
    except Exception:
        return str(v)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_user_for_path(username: str) -> str:
    allowed = []
    for ch in (username or "").strip():
        if ch.isalnum() or ch in ("_", "-", "."):
            allowed.append(ch)
    return "".join(allowed) or "unknown"


def _get_logged_in_username() -> str:
    return "local"






def _get_screen_resolution() -> dict:
    """Get primary monitor resolution. Returns {"width": W, "height": H}."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        w = user32.GetSystemMetrics(0)   # SM_CXSCREEN
        h = user32.GetSystemMetrics(1)   # SM_CYSCREEN
        if w > 0 and h > 0:
            return {"width": w, "height": h}
    except Exception:
        pass
    try:
        import mss as _mss
        with _mss.mss() as sct:
            m = sct.monitors[1]
            return {"width": m["width"], "height": m["height"]}
    except Exception:
        pass
    return {"width": None, "height": None}


def _get_environment_details() -> dict:
    """Collect OS + hardware info for environment context."""
    env = {}
    try:
        env["os_name"]    = platform.system()
        env["os_version"] = platform.version()
        env["os_release"] = platform.release()
    except Exception:
        pass
    try:
        env["cpu_model"] = platform.processor()
    except Exception:
        pass
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get",
             "Name,AdapterRAM", "/format:csv"],
            capture_output=True, text=True, timeout=5
        )
        gpus = []
        for line in result.stdout.strip().splitlines():
            parts = line.split(",")
            if len(parts) >= 3 and parts[1].strip() and parts[1].strip() != "Name":
                name = parts[1].strip()
                try:
                    vram_mb = round(int(parts[2].strip()) / (1024 ** 2))
                except Exception:
                    vram_mb = None
                gpus.append({"name": name, "vram_mb": vram_mb})
        if gpus:
            env["gpus"] = gpus
    except Exception:
        pass
    return env


def _get_perf_snapshot() -> dict:
    """Capture CPU load, memory usage."""
    snap = {}
    try:
        import psutil
        snap["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        vm = psutil.virtual_memory()
        snap["ram_used_mb"]  = round(vm.used / 1024 ** 2)
        snap["ram_total_mb"] = round(vm.total / 1024 ** 2)
        snap["ram_percent"]  = vm.percent
    except Exception:
        pass
    return snap


def _collect_config_snapshot() -> dict:
    """
    Read ALL config values + ALL dashboard sidebar settings into one flat dict.
    auth_username is intentionally NOT included anywhere here.
    """
    snap = {}

    def _preset_tag(preset_name: str | None) -> str:
        v = (preset_name or "").strip().lower()
        if v in {"fast", "fast mode", "fast_mode"}:
            return "fast"
        if v in {"slow", "slow mode", "slow_mode"}:
            return "slow"
        return "custom"

    try:
        import config as _cfg

        # Stone thresholds (area5 labels)
        snap["cfg_stone_for_area5_stage1"]    = getattr(_cfg, "STONE_FOR_A5_STAGE1", None)
        snap["cfg_stone_for_area5_stage2"]    = getattr(_cfg, "STONE_FOR_A5_STAGE2", None)
        snap["cfg_stone_for_area5_stage3"]    = getattr(_cfg, "STONE_FOR_A5_STAGE3", None)
        snap["cfg_stone_for_area5_stage4"]    = getattr(_cfg, "STONE_FOR_A5_STAGE4", None)
        snap["cfg_stone_for_area5_meteor"]    = getattr(_cfg, "STONE_FOR_METEOR", None)
        snap["cfg_stone_for_area6_shortcut"]  = getattr(_cfg, "STONE_FOR_AREA6_SHORTCUT", None)
        snap["cfg_stone_for_unlock_drills"]   = getattr(_cfg, "STONE_FOR_UNLOCK_DRILLS", None)

        snap["cfg_stone_for_area5_stage1_h"]  = _fmt_stone(snap["cfg_stone_for_area5_stage1"])
        snap["cfg_stone_for_area5_stage2_h"]  = _fmt_stone(snap["cfg_stone_for_area5_stage2"])
        snap["cfg_stone_for_area5_stage3_h"]  = _fmt_stone(snap["cfg_stone_for_area5_stage3"])
        snap["cfg_stone_for_area5_stage4_h"]  = _fmt_stone(snap["cfg_stone_for_area5_stage4"])
        snap["cfg_stone_for_area5_meteor_h"]  = _fmt_stone(snap["cfg_stone_for_area5_meteor"])
        snap["cfg_stone_for_area6_shortcut_h"] = _fmt_stone(snap["cfg_stone_for_area6_shortcut"])
        snap["cfg_stone_for_unlock_drills_h"] = _fmt_stone(snap["cfg_stone_for_unlock_drills"])

        # Timing
        snap["cfg_stone_stall_timeout"]           = getattr(_cfg, "STONE_STALL_TIMEOUT", None)
        snap["cfg_smart_failure_timeout"]         = getattr(_cfg, "SMART_FAILURE_TIMEOUT", None)
        snap["cfg_teleport_wait"]                 = getattr(_cfg, "TELEPORT_WAIT", None)
        snap["cfg_teleport_to_base_wait"]         = getattr(_cfg, "TELEPORT_TO_BASE_WAIT", None)
        snap["cfg_teleport_wait_a5"]              = getattr(_cfg, "TELEPORT_WAIT_A5", None)
        snap["cfg_a5_check_attempts"]             = getattr(_cfg, "A5_CHECK_ATTEMPTS", None)
        snap["cfg_rebirth_check_delay"]           = getattr(_cfg, "REBIRTH_CHECK_DELAY", None)
        snap["cfg_rebirth_settle_wait"]           = getattr(_cfg, "REBIRTH_SETTLE_WAIT", None)
        snap["cfg_rebirth_post_confirm_wait"]     = getattr(_cfg, "REBIRTH_POST_CONFIRM_WAIT", None)
        snap["cfg_menu_resume_join_wait"]         = getattr(_cfg, "MENU_RESUME_JOIN_WAIT", None)
        snap["cfg_stone_icon_missing_wait"]       = getattr(_cfg, "STONE_ICON_MISSING_WAIT", None)
        snap["cfg_menu_appear_wait"]              = getattr(_cfg, "MENU_APPEAR_WAIT", None)
        snap["cfg_focus_recheck_delay"]           = getattr(_cfg, "FOCUS_RECHECK_DELAY", None)
        snap["cfg_macro_poll_interval"]           = getattr(_cfg, "MACRO_POLL_INTERVAL", None)
        snap["cfg_meteor_hit_seconds"]            = getattr(_cfg, "METEOR_HIT_SECONDS", None)
        snap["cfg_topup_timeout"]                 = getattr(_cfg, "TOPUP_TIMEOUT", None)
        snap["cfg_meteor_post_break_hit_seconds"] = getattr(_cfg, "METEOR_POST_BREAK_HIT_SECONDS", None)
        snap["cfg_meteor_broken_votes"]           = getattr(_cfg, "METEOR_BROKEN_VOTES", None)

        # Stage topup seconds (area5 labels)
        topup = getattr(_cfg, "STAGE_TOPUP_SECONDS", {})
        snap["cfg_stage_topup_base"]         = topup.get("base",   None)
        snap["cfg_stage_topup_area5_stage1"] = topup.get(1,        None)
        snap["cfg_stage_topup_area5_stage2"] = topup.get(2,        None)
        snap["cfg_stage_topup_area5_stage3"] = topup.get(3,        None)
        snap["cfg_stage_topup_area5_stage4"] = topup.get(4,        None)
        snap["cfg_stage_topup_area5_meteor"] = topup.get("meteor", None)

        # Mouse sensitivity
        snap["cfg_user_sens_h"]     = getattr(_cfg, "USER_SENS_H", None)
        snap["cfg_user_sens_v"]     = getattr(_cfg, "USER_SENS_V", None)
        snap["cfg_recorded_sens_h"] = getattr(_cfg, "RECORDED_SENS_H", None)
        snap["cfg_recorded_sens_v"] = getattr(_cfg, "RECORDED_SENS_V", None)

        # Manual strength
        snap["cfg_manual_str_max_seconds"]         = getattr(_cfg, "MANUAL_STR_MAX_SECONDS", None)
        snap["cfg_manual_str_idle_wait"]           = getattr(_cfg, "MANUAL_STR_IDLE_WAIT", None)
        snap["cfg_manual_str_close_yellow_thresh"] = getattr(_cfg, "MANUAL_STR_CLOSE_YELLOW_THRESH", None)
        snap["cfg_manual_str_only_last_row"]       = getattr(_cfg, "MANUAL_STR_ONLY_LAST_ROW", None)

        # Detection thresholds
        snap["cfg_stone_icon_thresh"]         = getattr(_cfg, "STONE_ICON_THRESH", None)
        snap["cfg_meteor_red_missing_thresh"] = getattr(_cfg, "METEOR_RED_MISSING_THRESH", None)
        snap["cfg_meteor_red_seen_thresh"]    = getattr(_cfg, "METEOR_RED_SEEN_THRESH", None)
        snap["cfg_menu_play_color_thresh"]    = getattr(_cfg, "MENU_PLAY_COLOR_THRESH", None)
        snap["cfg_menu_play_hue_tol"]         = getattr(_cfg, "MENU_PLAY_HUE_TOL", None)
        snap["cfg_menu_play_sat_tol"]         = getattr(_cfg, "MENU_PLAY_SAT_TOL", None)
        snap["cfg_menu_play_val_tol"]         = getattr(_cfg, "MENU_PLAY_VAL_TOL", None)
        snap["cfg_auto_str_white_thresh"]     = getattr(_cfg, "AUTO_STR_WHITE_THRESH", None)

        # Feature flags
        snap["cfg_unlock_drills"]             = getattr(_cfg, "UNLOCK_DRILLS", None)
        snap["cfg_activate_drills"]           = getattr(_cfg, "ACTIVATE_DRILLS", None)
        snap["cfg_bot_handles_auto_strength"] = getattr(_cfg, "BOT_HANDLES_AUTO_STRENGTH", None)
        snap["cfg_save_debug_crops"]          = getattr(_cfg, "SAVE_DEBUG_CROPS", None)

        # HUD regions
        for attr in (
            "STONE_REGION", "STRENGTH_REGION", "STONE_ICON_REGION",
            "AUTO_STR_REGION", "ROCK_HEALTH_BAR_REGION",
            "TELEPORT_BUTTON_REGION", "TELEPORT_BASE_REGION", "TELEPORT_AREA5_REGION",
            "MENU_PLAY_REGION",
        ):
            val = getattr(_cfg, attr, None)
            if val is not None:
                snap[f"cfg_region_{attr.lower()}"] = list(val)

    except Exception as e:
        snap["cfg_load_error"] = str(e)

    # â”€â”€ Dashboard live state â€” auth_username intentionally excluded â”€â”€
    try:
        import dashboard as _dash
        ds = _dash.get_state()
        snap["dash_run_mode"]        = ds.get("run_mode", None)
        snap["dash_meteor_shortcut_mode"] = (ds.get("run_mode", None) == "meteor")
        snap["dash_unlock_drills"]   = ds.get("unlock_drills", None)
        snap["dash_activate_drills"] = ds.get("activate_drills", None)
        snap["dash_auto_strength"]   = ds.get("auto_strength", None)
        snap["dash_menu_resume"]     = ds.get("menu_resume", None)
        snap["dash_total_rebirths"]  = ds.get("total_rebirths", None)

    except Exception as e:
        snap["dash_load_error"] = str(e)

    return snap


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Stage â†’ event name mapping  (Area 5 labelled)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_STAGE_LABEL: dict[str, str] = {
    "base":    "base",
    "stage1":  "area5_stage1",
    "stage2":  "area5_stage2",
    "stage3":  "area5_stage3",
    "stage4":  "area5_stage4",
    "meteor":  "area5_meteor",
    "rebirth": "rebirth",
}

_STAGE_EVENT: dict[str, str] = {
    "base":    "entered_base_rock",
    "stage1":  "entered_area5_stage1_rock",
    "stage2":  "entered_area5_stage2_rock",
    "stage3":  "entered_area5_stage3_rock",
    "stage4":  "entered_area5_stage4_rock",
    "meteor":  "entered_area5_meteor",
    "rebirth": "rebirth_menu_opened",
}


def _stage_label(stage: str) -> str:
    return _STAGE_LABEL.get(stage, stage)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Main recorder class
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class RunRecorder:
    """
    Thread-safe run recorder.

    Write strategy:
        - All files written to: run_recordings/_temp_<run_id>/
        - On stop_run(): temp dir moved to run_recordings/run_<id>/
        - Files stay local only (no upload queue).
        - Incomplete runs (F9 / crash) stay in _temp_ and are never finalized.

    All data remains local on this machine.

    Public API:
        start_run(run_number, thresholds)
        record_tick(stone, status, goal, stage, run_number, auto_str, activate_drills)
        record_frame(...)                  â† alias for record_tick
        log_stage(stage, stone)
        log_action(action_dict)
        log_macro_event(name, event, macro_file, return_code, error)
        log_manual_strength_action(action, stone, context)
        log_settings_change(setting, old_value, new_value)
        log_error_or_retry(reason, context)
        set_failure_reason(reason)
        stop_run(final_stone, status)
    """

    def __init__(self):
        self._lock               = threading.Lock()
        self._active             = False
        self._temp_dir: str | None  = None
        self._run_dir:  str | None  = None
        self._run_id:   str | None  = None
        self._run_meta: dict        = {}
        self._run_start_time        = 0.0
        self._last_stage: str       = ""
        self._tick_count            = 0
        self._failure_reason: str | None = None

        self._keypress_counts: dict[str, int] = {}
        self._teleport_count   = 0
        self._macro_call_count = 0
        self._error_count      = 0
        self._retry_count      = 0
        self._perf_start: dict = {}

        self._actions_file = None
        self._events_file  = None
        self._actions_lock = threading.Lock()
        self._events_lock  = threading.Lock()
        self._ks_hook      = None
        self._mouse_hook   = None
        try:
            os.makedirs(RECORDS_DIR, exist_ok=True)
        except Exception:
            pass

    # â”€â”€ Public API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def is_active(self) -> bool:
        return self._active

    def start_run(self, run_number: int, thresholds: dict):
        """Begin recording. Data goes to _temp_ folder until stop_run()."""
        with self._lock:
            if self._active:
                return

            ts_str   = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id   = f"run_{ts_str}"
            temp_dir = os.path.join(RECORDS_DIR, f"_temp_{run_id}")
            run_dir  = os.path.join(RECORDS_DIR, run_id)
            os.makedirs(RECORDS_DIR, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            self._run_id          = run_id
            self._temp_dir        = temp_dir
            self._run_dir         = run_dir
            self._tick_count      = 0
            self._last_stage      = ""
            self._run_start_time  = time.time()
            self._failure_reason  = None
            self._keypress_counts = {}
            self._teleport_count  = 0
            self._macro_call_count = 0
            self._error_count      = 0
            self._retry_count      = 0

            self._run_meta = {
                "run_id":      run_id,
                "run_number":  run_number,
                "start_epoch": self._run_start_time,
                "thresholds":  thresholds,
                "bot_version": str(BOT_VERSION),
            }

            self._actions_file = open(
                os.path.join(temp_dir, "actions.jsonl"), "w", encoding="utf-8")
            self._events_file  = open(
                os.path.join(temp_dir, "events.jsonl"),  "w", encoding="utf-8")

            self._active = True

        try:
            self._perf_start = _get_perf_snapshot()
        except Exception:
            self._perf_start = {}

        self._write_action({
            "t": 0.0,
            "tick": 0,
            "type": "bot_version",
            "bot_version": str(BOT_VERSION),
        })
        self._write_event({
            "t": 0.0,
            "tick": 0,
            "event": "bot_version",
            "bot_version": str(BOT_VERSION),
        })
        self._write_event({"event": "run_started", "run_number": run_number})
        self._install_keyboard_hook()

    def stop_run(self, final_stone, status: str = "rebirth_complete"):
        """
        Finish recording, write metadata + notes, then move tempâ†’final.
        For F9 aborts (status="stopped"): files stay in _temp_ and are not finalized.
        """
        with self._lock:
            if not self._active:
                return
            self._active       = False
            temp_dir           = self._temp_dir
            run_dir            = self._run_dir
            run_meta           = dict(self._run_meta)
            tick_count         = self._tick_count
            failure_reason     = self._failure_reason
            keypress_counts    = dict(self._keypress_counts)
            teleport_count     = self._teleport_count
            macro_call_count   = self._macro_call_count
            error_count        = self._error_count
            retry_count        = self._retry_count
            act_file           = self._actions_file
            evt_file           = self._events_file
            self._actions_file = None
            self._events_file  = None

        result_map = {
            "rebirth_complete": "success",
            "run_failed":       "fail",
            "stopped":          "stopped",
        }
        spec_result = result_map.get(status, "unknown")

        self._write_event(
            {"event": "run_success" if spec_result == "success" else
                      "run_failed"  if spec_result == "fail"     else "run_stopped",
             "stone": _fmt_stone(final_stone)},
            _file=evt_file,
        )

        self._remove_keyboard_hook()

        for f in (act_file, evt_file):
            if f:
                try:
                    f.close()
                except Exception:
                    pass

        # F9/manual stop: keep temp folder and do NOT finalize.
        if status == "stopped":
            return

        # â”€â”€ Collect metadata â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        config_snap = _collect_config_snapshot()
        screen_res  = _get_screen_resolution()
        env_details = _get_environment_details()
        perf_end    = _get_perf_snapshot()
        total_keypresses = sum(keypress_counts.values())

        end_epoch = time.time()
        duration  = end_epoch - run_meta.get("start_epoch", end_epoch)

        metadata = {
            # â”€â”€ Identity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "run_id":                   run_meta["run_id"],
            "created_at":               datetime.fromtimestamp(
                                            run_meta["start_epoch"], tz=timezone.utc
                                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "start_epoch":              float(run_meta.get("start_epoch") or 0.0),
            "game":                     "Miner Tycoon 2",
            "bot_version":              run_meta.get("bot_version", str(BOT_VERSION)),
            # username intentionally NOT recorded

            # â”€â”€ Screen resolution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "screen_resolution": screen_res,

            # â”€â”€ Environment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "environment": env_details,

            # â”€â”€ Run result â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "result":         spec_result,
            "failure_reason": (
                failure_reason
                if failure_reason
                else (None if spec_result == "success" else "unknown_failure")
            ),
            "run_number":        run_meta.get("run_number", 0),
            "final_stone":       final_stone if final_stone is not None else 0,
            "final_stone_human": _fmt_stone(final_stone),
            "duration_secs":     round(duration, 1),
            "total_ticks":       tick_count,
            "notes":             "",

            # â”€â”€ Thresholds (area5 labels) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "stage_thresholds": {
                _stage_label(k): v
                for k, v in run_meta.get("thresholds", {}).items()
            },

            # â”€â”€ Aggregate stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "keypress_stats": {
                "total_keypresses": total_keypresses,
                "per_key_counts":   keypress_counts,
                "teleport_count":   teleport_count,
                "macro_call_count": macro_call_count,
            },
            "error_count":  error_count,
            "retry_count":  retry_count,

            # â”€â”€ System performance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            "perf_start": self._perf_start,
            "perf_end":   perf_end,

            # â”€â”€ Full config + sidebar snapshot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            **config_snap,
        }

        try:
            with open(os.path.join(temp_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            log.warning(f"[Recorder] metadata write failed: {e}")

        # â”€â”€ Write notes.md â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        try:
            with open(os.path.join(temp_dir, "notes.md"), "w", encoding="utf-8") as f:
                f.write(f"# {run_meta['run_id']}\n\n")
                f.write(f"Result: {spec_result}\n\n")
                f.write(f"## Summary\n")
                f.write(f"- Bot version: {run_meta.get('bot_version', str(BOT_VERSION))}\n")
                f.write(f"- Run #{run_meta.get('run_number', '?')}\n")
                f.write(f"- Duration: {round(duration, 0):.0f}s  ({tick_count} ticks)\n")
                f.write(f"- Final stone: {_fmt_stone(final_stone)}\n")
                if screen_res.get("width") and screen_res.get("height"):
                    f.write(f"- Screen: {screen_res['width']}x{screen_res['height']}\n")
                f.write(f"\n## Settings snapshot\n")
                f.write(f"- run_mode: {config_snap.get('dash_run_mode', '?')}\n")
                f.write(f"- unlock_drills: {config_snap.get('dash_unlock_drills', '?')}\n")
                f.write(f"- activate_drills: {config_snap.get('dash_activate_drills', '?')}\n")
                f.write(f"- auto_strength: {config_snap.get('dash_auto_strength', '?')}\n")
                f.write(f"- menu_resume: {config_snap.get('dash_menu_resume', '?')}\n")
                f.write(f"- area5_stage1 threshold: {config_snap.get('cfg_stone_for_area5_stage1_h', '?')}\n")
                f.write(f"- area5_stage2 threshold: {config_snap.get('cfg_stone_for_area5_stage2_h', '?')}\n")
                f.write(f"- area5_stage3 threshold: {config_snap.get('cfg_stone_for_area5_stage3_h', '?')}\n")
                f.write(f"- area5_stage4 threshold: {config_snap.get('cfg_stone_for_area5_stage4_h', '?')}\n")
                f.write(f"- area5_meteor threshold: {config_snap.get('cfg_stone_for_area5_meteor_h', '?')}\n")
                f.write(f"- area6_shortcut threshold: {config_snap.get('cfg_stone_for_area6_shortcut_h', '?')}\n")
                f.write(f"\n## Stats\n")
                f.write(f"- Total keypresses: {total_keypresses}\n")
                f.write(f"- Teleports: {teleport_count}\n")
                f.write(f"- Macro calls: {macro_call_count}\n")
                f.write(f"- Errors: {error_count}\n")
                f.write(f"- Retries: {retry_count}\n")
                if failure_reason and spec_result != "success":
                    f.write(f"\n## Failure reason\n- {failure_reason}\n")
        except Exception as e:
            log.warning(f"[Recorder] notes.md write failed: {e}")

        # â”€â”€ Move temp dir â†’ final dir â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        moved_ok = False
        try:
            if os.path.exists(temp_dir):
                shutil.move(temp_dir, run_dir)
                moved_ok = True
        except Exception as e:
            log.warning(f"[Recorder] move to final dir failed: {e}")


    def set_failure_reason(self, reason: str):
        """Set a specific failure reason. Can be called mid-run."""
        with self._lock:
            self._failure_reason = reason

    def record_tick(self, stone, status: str, goal: str, stage: str,
                    run_number: int, auto_str: bool, activate_drills: bool):
        """Call every second. Logs full state to events.jsonl."""
        with self._lock:
            if not self._active:
                return
            self._tick_count += 1
            tick_count  = self._tick_count
            run_start   = self._run_start_time

        t_rel = round(time.time() - run_start, 3)
        self._write_event({
            "t":               t_rel,
            "tick":            tick_count,
            "event":           "state_tick",
            "stone":           _fmt_stone(stone),
            "stone_raw":       stone if stone is not None else 0,
            "stage":           _stage_label(stage),
            "status":          status,
            "goal":            goal,
            "auto_strength":   auto_str,
            "activate_drills": activate_drills,
            "run_number":      run_number,
        })

    def record_frame(self, stone, status: str, goal: str, stage: str,
                     run_number: int, auto_str: bool, activate_drills: bool):
        """Backwards-compatible alias for record_tick."""
        self.record_tick(stone, status, goal, stage, run_number, auto_str, activate_drills)

    def log_stage(self, stage: str, stone=None):
        """Call at every stage transition."""
        with self._lock:
            if not self._active:
                return
            if stage == self._last_stage:
                return
            self._last_stage = stage
            run_start   = self._run_start_time
            tick_count  = self._tick_count

        t_rel      = round(time.time() - run_start, 3)
        event_name = _STAGE_EVENT.get(stage, f"entered_{_stage_label(stage)}")
        label      = _stage_label(stage)

        self._write_event({
            "t": t_rel, "tick": tick_count,
            "event": event_name, "stone": _fmt_stone(stone), "stage": label,
        })
        self._write_action({
            "t": t_rel, "tick": tick_count,
            "type": "stage_transition", "stage": label, "stone": _fmt_stone(stone),
        })

    def log_action(self, action: dict):
        """Log any bot action. Timestamp and tick added automatically."""
        with self._lock:
            if not self._active:
                return
            t_rel      = round(time.time() - self._run_start_time, 3)
            tick_count = self._tick_count
            atype = str(action.get("type", "") or "").lower()
            if atype.startswith("teleport_"):
                # Count one teleport per attempt action.
                if atype == "teleport_attempt":
                    self._teleport_count += 1
            elif atype.startswith("retry"):
                self._retry_count += 1
            elif atype.startswith("error"):
                self._error_count += 1

        action.setdefault("t",    t_rel)
        action.setdefault("tick", tick_count)
        if "stage" in action:
            action["stage"] = _stage_label(action["stage"])
        self._write_action(action)

    def log_macro_event(self, name: str, event: str,
                        macro_file: str | None = None,
                        return_code: int | None = None,
                        error: str | None = None):
        """Record macro lifecycle events. event: 'start' | 'end' | 'error'"""
        with self._lock:
            if not self._active:
                return
            t_rel      = round(time.time() - self._run_start_time, 3)
            tick_count = self._tick_count
            if event == "start":
                self._macro_call_count += 1

        entry: dict = {"t": t_rel, "tick": tick_count,
                       "type": f"macro_{event}", "macro_name": name}
        if macro_file  is not None: entry["macro_file"]  = macro_file
        if return_code is not None: entry["return_code"] = return_code
        if error       is not None: entry["error"]       = error
        self._write_action(entry)

    def log_manual_strength_action(self, action: str, stone=None, context: str = ""):
        """Log a manual-strength click or delay event."""
        with self._lock:
            if not self._active:
                return
            t_rel      = round(time.time() - self._run_start_time, 3)
            tick_count = self._tick_count

        entry: dict = {"t": t_rel, "tick": tick_count,
                       "type": "manual_strength", "action": action}
        if stone   is not None: entry["stone"]   = _fmt_stone(stone)
        if context:             entry["context"] = context
        self._write_action(entry)

    def log_settings_change(self, setting: str, old_value, new_value):
        """Record a mid-run settings toggle."""
        with self._lock:
            if not self._active:
                return
            t_rel      = round(time.time() - self._run_start_time, 3)
            tick_count = self._tick_count

        self._write_event({
            "t": t_rel, "tick": tick_count, "event": "settings_change",
            "setting": setting, "old_value": old_value, "new_value": new_value,
        })

    def log_error_or_retry(self, reason: str, context: str = ""):
        """Increment error/retry counters and log a structured event."""
        with self._lock:
            if not self._active:
                return
            t_rel      = round(time.time() - self._run_start_time, 3)
            tick_count = self._tick_count
            is_retry   = "retry" in reason.lower()
            if is_retry:
                self._retry_count += 1
            else:
                self._error_count += 1

        entry: dict = {"t": t_rel, "tick": tick_count,
                       "event": "retry" if is_retry else "error", "reason": reason}
        if context: entry["context"] = context
        self._write_event(entry)

    # â”€â”€ Internal helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _write_action(self, obj: dict, _file=None):
        f = _file or self._actions_file
        if not f:
            return
        with self._actions_lock:
            try:
                f.write(json.dumps(obj) + "\n")
                f.flush()
            except Exception:
                pass   # silent â€” don't spam logs during recording

    def _write_event(self, obj: dict, _file=None):
        f = _file or self._events_file
        if not f:
            return
        with self._events_lock:
            try:
                f.write(json.dumps(obj) + "\n")
                f.flush()
            except Exception:
                pass   # silent

    def _install_keyboard_hook(self):
        if not _HAS_KEYBOARD:
            return
        try:
            run_start_ref = self._run_start_time

            def _on_key(event):
                if not self._active:
                    return
                t_rel   = round(time.time() - run_start_ref, 3)
                is_down = (event.event_type == "down")
                with self._lock:
                    tick = self._tick_count
                    if is_down:
                        key_name = str(event.name)
                        self._keypress_counts[key_name] = (
                            self._keypress_counts.get(key_name, 0) + 1
                        )
                self._write_action({
                    "t":    t_rel,
                    "tick": tick,
                    "type": "key_down" if is_down else "key_up",
                    "key":  event.name,
                })

            self._ks_hook = _keyboard.hook(_on_key)
        except Exception:
            pass   # silent

    def _remove_keyboard_hook(self):
        if _HAS_KEYBOARD and self._ks_hook is not None:
            try:
                _keyboard.unhook(self._ks_hook)
                self._ks_hook = None
            except Exception:
                pass
        if getattr(self, "_mouse_hook", None) is not None:
            try:
                import mouse as _mouse_lib
                _mouse_lib.unhook(self._mouse_hook)
                self._mouse_hook = None
            except Exception:
                pass


# â”€â”€ Module-level singleton â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_recorder_instance: RunRecorder | None = None
_recorder_lock = threading.Lock()


def get_recorder() -> RunRecorder:
    """Return (or create) the module-level RunRecorder singleton."""
    global _recorder_instance
    with _recorder_lock:
        if _recorder_instance is None:
            _recorder_instance = RunRecorder()
        return _recorder_instance



