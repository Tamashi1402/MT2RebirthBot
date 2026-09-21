# ============================================================
# MT2 BOT - HTML DASHBOARD SERVER  (v18.1)
# Flask server on localhost:7373 ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â auto-opens in browser.
# Persistent state saved to data/dashboard_state.json.
# Changes v18:
#   - Macro editor: block/bauble-based visual editor (no raw text)
#     each instruction is a pill with [x] delete + click to edit
#   - Screenshot overlay: DPI-aware canvas (fixes X/Y stretching)
#   - Full logging for OCR region saves, macro loads/saves
# ============================================================
import json
import math
import os
import re
import sys
import hmac
import secrets
import subprocess
import threading
import time
import urllib.request
import zipfile
from datetime import datetime, timezone

import logging
from flask import Flask, jsonify, request, send_file
from logger import get_logger
from config import BOT_DIR, DATA_DIR, MODULES_DIR, STATS_FILE

log = get_logger()

# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Persistent dashboard state file ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

DASHBOARD_STATE_FILE = os.path.join(DATA_DIR, "dashboard_state.json")
DELVE_STATS_FILE = os.path.join(DATA_DIR, "delve_stats.json")
KRAKEN_STATS_FILE = os.path.join(DATA_DIR, "kraken_stats.json")
ZYTOS_STATS_FILE = os.path.join(DATA_DIR, "zytos_stats.json")
MAX_RUN_HISTORY = 25000


def _screen_size_for_image_prefix() -> tuple[int, int]:
    try:
        import mss
        with mss.mss() as sct:
            mon = sct.monitors[0]
            return int(mon["width"]), int(mon["height"])
    except Exception:
        return 1920, 1080


def _unique_image_path(images_dir: str, filename: str) -> str:
    root, ext = os.path.splitext(filename)
    path = os.path.join(images_dir, filename)
    suffix = 1
    while os.path.exists(path):
        path = os.path.join(images_dir, f"{root}_{suffix}{ext}")
        suffix += 1
    return path


def _prefix_unversioned_macro_images() -> int:
    images_dir = os.path.join(BOT_DIR, "macros", "images")
    try:
        os.makedirs(images_dir, exist_ok=True)
    except Exception:
        return 0
    base_w, base_h = _screen_size_for_image_prefix()
    prefix = f"{base_w}x{base_h}_"
    renamed = 0
    try:
        entries = sorted(os.scandir(images_dir), key=lambda e: e.name.lower())
    except Exception:
        return 0
    for entry in entries:
        if not entry.is_file():
            continue
        name = entry.name
        if not name.lower().endswith(".png"):
            continue
        if re.match(r"^\d{3,5}x\d{3,5}_", name, flags=re.I):
            continue
        target = _unique_image_path(images_dir, prefix + name)
        try:
            os.replace(entry.path, target)
            renamed += 1
        except Exception:
            pass
    return renamed


def _resolve_path_from_bot(path_value: str, fallback_rel: str) -> str:
    raw = str(path_value or "").strip() or fallback_rel
    return raw if os.path.isabs(raw) else os.path.join(BOT_DIR, raw)


def _load_persistent_state() -> dict:
    try:
        if os.path.exists(DASHBOARD_STATE_FILE):
            with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    except Exception as e:
        log.debug(f"dashboard_state load failed: {e}")
    return {}

def _trim_history(history: list, max_runs: int = MAX_RUN_HISTORY) -> list:
    if not isinstance(history, list):
        return []
    cleaned = [r for r in history if isinstance(r, dict)]
    if len(cleaned) > max_runs:
        cleaned = cleaned[-max_runs:]
    return cleaned

def _atomic_json_dump(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)
    os.replace(tmp_path, path)

def _save_persistent_state(s: dict):
    keys = ("total_rebirths", "total_errors", "avg_time_secs",
            "min_time_secs", "max_time_secs",
            "bot_mode", "farm_meteor_area", "unlock_drills", "activate_drills", "run_mode", "menu_resume", "crater_overlay", "crater_elapsed_secs", "crater_pet_drops",
            "auto_strength", "boss_fight_a1", "force_restart", "pause_on_lag", "daily_quests",
            "kraken_drill",
            "rebirth_activate_drills", "delve_activate_drills", "kraken_activate_drills", "zytos_activate_drills",
            "rebirth_drill_on_a5_meteor", "rebirth_drill_on_rock", "rebirth_drill_on_baserock",
            "kraken_movement_mode", "zytos_movement_mode")
    try:
        data = {k: s[k] for k in keys if k in s}
        _atomic_json_dump(DASHBOARD_STATE_FILE, data)
    except Exception as e:
        log.debug(f"dashboard_state save failed: {e}")


def _load_delve_history() -> list:
    try:
        if os.path.exists(DELVE_STATS_FILE):
            with open(DELVE_STATS_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            history = data.get("run_history", []) if isinstance(data, dict) else []
            return _trim_history(history)
    except Exception as e:
        log.debug(f"delve_stats load failed: {e}")
    return []


def _load_kraken_history() -> list:
    try:
        if os.path.exists(KRAKEN_STATS_FILE):
            with open(KRAKEN_STATS_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            history = data.get("run_history", []) if isinstance(data, dict) else []
            return _trim_history(history)
    except Exception as e:
        log.debug(f"kraken_stats load failed: {e}")
    return []


def _save_delve_history(history: list):
    try:
        data = {
            "run_history": _json_safe(history),
            "updated_at": time.time(),
        }
        data["run_history"] = _trim_history(data["run_history"])
        _atomic_json_dump(DELVE_STATS_FILE, data)
    except Exception as e:
        log.debug(f"delve_stats save failed: {e}")


def _save_kraken_history(history: list):
    try:
        data = {
            "run_history": _json_safe(history),
            "updated_at": time.time(),
        }
        data["run_history"] = _trim_history(data["run_history"])
        _atomic_json_dump(KRAKEN_STATS_FILE, data)
    except Exception as e:
        log.debug(f"kraken_stats save failed: {e}")


def _save_zytos_history(history: list):
    try:
        data = {
            "run_history": _json_safe(history),
            "updated_at": time.time(),
        }
        data["run_history"] = _trim_history(data["run_history"])
        _atomic_json_dump(ZYTOS_STATS_FILE, data)
    except Exception as e:
        log.debug(f"zytos_stats save failed: {e}")


def _load_zytos_history() -> list:
    try:
        if os.path.exists(ZYTOS_STATS_FILE):
            with open(ZYTOS_STATS_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            history = data.get("run_history", []) if isinstance(data, dict) else []
            return _trim_history(history)
    except Exception as e:
        log.debug(f"zytos_stats load failed: {e}")
    return []


# Macro presets removed ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â macros live flat in macros/ root.

def _recalc_stats_from_history(history: list) -> dict:
    if not history:
        return dict(total_rebirths=0, total_errors=0, avg_time_secs=0.0,
                    min_time_secs=0.0, max_time_secs=0.0)
    total_rebirths = len(history)
    total_errors   = sum(r.get("error_count", 0) for r in history)
    durations      = [r["duration_secs"] for r in history if r.get("duration_secs", 0) > 0]
    avg_time_secs  = sum(durations) / len(durations) if durations else 0.0
    min_time_secs  = min(durations) if durations else 0.0
    max_time_secs  = max(durations) if durations else 0.0
    return dict(total_rebirths=total_rebirths, total_errors=total_errors,
                avg_time_secs=avg_time_secs, min_time_secs=min_time_secs,
                max_time_secs=max_time_secs)


def _safe_float(value, default: float = 0.0) -> float:
    try:
        v = float(value)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else 0.0
    return value


def _load_history_from_recordings(max_runs: int = MAX_RUN_HISTORY) -> list:
    """
    Recovery fallback: rebuild dashboard run history from recorder metadata files.
    Uses only successful runs to mirror dashboard stats semantics.
    """
    records_dir = os.path.join(BOT_DIR, "run_recordings")
    if not os.path.isdir(records_dir):
        return []

    history = []
    try:
        entries = sorted(
            (e for e in os.scandir(records_dir) if e.is_dir() and e.name.startswith("run_")),
            key=lambda e: e.name.lower(),
        )
    except Exception:
        return []

    for entry in entries:
        meta_path = os.path.join(entry.path, "metadata.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path, "r", encoding="utf-8-sig") as f:
                meta = json.load(f)
            if str(meta.get("result", "")).lower() != "success":
                continue

            run_number = int(meta.get("run_number", 0) or 0)
            duration = float(meta.get("duration_secs", 0.0) or 0.0)
            error_count = int(meta.get("error_count", 0) or 0)
            step_count = int(meta.get("step_count", 0) or 0)

            start_epoch = 0.0
            created_at = str(meta.get("created_at", "") or "")
            if created_at:
                try:
                    start_epoch = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=timezone.utc
                    ).timestamp()
                except Exception:
                    start_epoch = 0.0
            end_epoch = start_epoch + duration if start_epoch and duration >= 0 else 0.0

            history.append({
                "run_number": run_number,
                "start_time": start_epoch,
                "end_time": end_epoch,
                "error_count": error_count,
                "step_count": step_count,
                "duration_secs": duration,
            })
        except Exception:
            continue

    history.sort(key=lambda r: (r.get("start_time", 0.0), r.get("run_number", 0)))
    for idx, row in enumerate(history, start=1):
        if int(row.get("run_number", 0) or 0) <= 0:
            row["run_number"] = idx
    return _trim_history(history, max_runs=max_runs)


def _load_stats_snapshot() -> dict | None:
    """Load summary + run history from stats.json (if available)."""
    try:
        data = {}
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

        history = data.get("run_history", []) if isinstance(data, dict) else []
        if not isinstance(history, list) or not history:
            persisted = _load_persistent_state()
            persisted_history = persisted.get("run_history", []) if isinstance(persisted, dict) else []
            history = persisted_history if isinstance(persisted_history, list) and persisted_history else []
        if not isinstance(history, list) or not history:
            history = _load_history_from_recordings(max_runs=MAX_RUN_HISTORY)
        history = _trim_history(history)
        recalced = _recalc_stats_from_history(history)
        saved_total = int(data.get("total_rebirths", 0) or 0) if isinstance(data, dict) else 0
        saved_errors = int(data.get("total_errors", 0) or 0) if isinstance(data, dict) else 0
        saved_avg = _safe_float(data.get("average_time_secs", 0.0), 0.0) if isinstance(data, dict) else 0.0
        saved_min = _safe_float(data.get("min_time_secs", 0.0), 0.0) if isinstance(data, dict) else 0.0
        saved_max = _safe_float(data.get("max_time_secs", 0.0), 0.0) if isinstance(data, dict) else 0.0
        return {
            "run_history": history,
            "total_rebirths": max(saved_total, recalced["total_rebirths"]),
            "total_errors": max(saved_errors, recalced["total_errors"]),
            "avg_time_secs": saved_avg if saved_avg > 0 else recalced["avg_time_secs"],
            "min_time_secs": saved_min if saved_min > 0 else recalced["min_time_secs"],
            "max_time_secs": saved_max if saved_max > 0 else recalced["max_time_secs"],
        }
    except Exception as e:
        log.debug(f"stats snapshot load failed: {e}")
        return None


_last_stats_sync_ts = 0.0
_stats_sync_interval_secs = 10.0


def _sync_state_from_stats(force: bool = False):
    """Keep dashboard history in sync with stats.json if it is newer."""
    global _last_stats_sync_ts
    now = time.time()
    if not force and (now - _last_stats_sync_ts) < _stats_sync_interval_secs:
        return
    _last_stats_sync_ts = now

    snap = _load_stats_snapshot()
    if not snap:
        return

    with _lock:
        cur_hist = _state.get("run_history", []) or []
        cur_total = int(_state.get("total_rebirths", 0) or 0)
        new_hist = snap["run_history"]
        new_total = int(snap["total_rebirths"])

        should_sync = (
            force
            or (new_total > cur_total)
            or (len(new_hist) > len(cur_hist))
            or (not cur_hist and bool(new_hist))
        )
        if not should_sync:
            return

        _state.update({
            "run_history": new_hist,
            "total_rebirths": new_total,
            "total_errors": int(snap["total_errors"]),
            "avg_time_secs": float(snap["avg_time_secs"]),
            "min_time_secs": float(snap["min_time_secs"]),
            "max_time_secs": float(snap["max_time_secs"]),
        })
        persisted = dict(_state)

    _save_persistent_state(persisted)
    log.debug(f"[Dashboard] Synced run stats from stats.json ({len(snap['run_history'])} runs)")

# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Config read/write helpers ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
# config.json is managed via config.save_values() / config.save_region()

CONFIG_EDITABLE = [
    ("USER_SENS_H",              "float", "Horizontal Sensitivity (1-100) - your Fortnite H mouse sensitivity"),
    ("USER_SENS_V",              "float", "Vertical Sensitivity (1-100) - your Fortnite V mouse sensitivity"),
    ("STONE_FOR_A1_STAGE2",      "float", "Area 1 Stage 1 -> Stage 2 threshold"),
    ("STONE_FOR_A1_STAGE3",      "float", "Area 1 Stage 2 -> Stage 3 threshold"),
    ("STONE_FOR_A1_STAGE4",      "float", "Area 1 Stage 3 -> Stage 4 threshold"),
    ("STONE_FOR_A2_STAGE1",      "float", "Area 1 Stage 4 -> Area 2 Stage 1 threshold"),
    ("STONE_FOR_A2_STAGE2",      "float", "Area 2 Stage 1 -> Stage 2 threshold"),
    ("STONE_FOR_A2_STAGE3",      "float", "Area 2 Stage 2 -> Stage 3 threshold"),
    ("STONE_FOR_A2_STAGE4",      "float", "Area 2 Stage 3 -> Stage 4 threshold"),
    ("STONE_FOR_A3_STAGE1",      "float", "Area 2 Stage 4 -> Area 3 Stage 1 threshold"),
    ("STONE_FOR_A3_STAGE2",      "float", "Area 3 Stage 1 -> Stage 2 threshold"),
    ("STONE_FOR_A3_STAGE3",      "float", "Area 3 Stage 2 -> Stage 3 threshold"),
    ("STONE_FOR_A3_STAGE4",      "float", "Area 3 Stage 3 -> Stage 4 threshold"),
    ("STONE_FOR_A4_STAGE1",      "float", "Area 3 Stage 4 -> Area 4 Stage 1 threshold"),
    ("STONE_FOR_A4_STAGE2",      "float", "Area 4 Stage 1 -> Stage 2 threshold"),
    ("STONE_FOR_A4_STAGE3",      "float", "Area 4 Stage 2 -> Stage 3 threshold"),
    ("STONE_FOR_A4_STAGE4",      "float", "Area 4 Stage 3 -> Stage 4 threshold"),
    ("STONE_FOR_A5_STAGE1",      "float", "Area 4 Stage 4 -> Area 5 Stage 1 threshold"),
    ("STONE_FOR_A5_STAGE2",      "float", "Area 5 Stage 1 -> Stage 2 threshold"),
    ("STONE_FOR_A5_STAGE3",      "float", "Area 5 Stage 2 -> Stage 3 threshold"),
    ("STONE_FOR_A5_STAGE4",      "float", "Area 5 Stage 3 -> Stage 4 threshold"),
    ("STONE_FOR_METEOR",         "float", "Area 5 Stage 4 -> Meteor threshold"),
    ("STONE_FOR_AREA6_SHORTCUT", "float", "Meteor shortcut base-rock threshold"),
    ("BOSS_FIGHT_A1_BASEROCK_THRESHOLD",           "float", "Boss Fight A1: baserock grind threshold before boss sequence (default 1e33)"),
    ("BOSS_FIGHT_A1_AMOUNT",                       "int",   "Boss Fight A1: how many times to loop the boss fight (default 3)"),
    ("BOSS_FIGHT_A1_METEOR_GRIND_SECONDS",         "float", "Boss Fight A1: base seconds to grind A1 meteor per fight (default 10; scales: actual = grind_secs * fight_number)"),
    ("BOSS_FIGHT_A1_LOADOUT_FIGHTING",              "str",   "Fighting loadout (Boss Fight A1, none / 1-6)"),
    ("BOSS_FIGHT_A1_LOADOUT_FARMING",               "str",   "Farming loadout (A1-A5 / baserock, none / 1-6)"),
    ("CRATER_LOADOUT_METEOR_REWARDS",               "str",   "Meteor Rewards loadout (Crater, none / 1-6)"),
    ("FARM_METEOR_LOADOUT",                          "str",   "Legacy Meteor Farm loadout (falls back to Meteor Rewards)"),
    ("DISABLE_OVERLAYS",                             "bool",  "Disable overlays (HUD will not be drawn at all)"),
    ("METEOR_HEALTH_CHECK",                          "bool",  "Check A5 Meteor health (auto stop when the red bar disappears)"),
    ("FIXED_A5_HIT_TIME",                            "int",   "Fixed A5 hit time (seconds) — used only when the A5 Meteor health check is disabled"),
    ("HIT_ROCKS",                                    "bool",  "Hit stage rocks"),
    ("HIT_BASEROCK",                                 "bool",  "Hit baserock"),
    ("HIT_A5_METEOR",                                "bool",  "Hit A5 Meteor"),
    ("BOSS_FIGHT_A1_MODE",                          "str",   "Boss fight mode (Bramble / Zytos)"),
    ("QUEST_MINE_TIMEOUT_SECONDS",                   "int",   "Daily Quests: max seconds to mine one quest rock before auto-done"),
    ("DAILY_QUEST_ALIASES",                          "str",   "Daily Quests: OCR aliases for Break X Star Rocks (| separated, {$NUMBER} = digit)"),
    ("QUEST_MIMIC_ALIASES",                          "str",   "Daily Quests: OCR aliases for Open Chests"),
    ("QUEST_HATCH_ALIASES",                          "str",   "Daily Quests: OCR aliases for Hatch Pets"),
    ("HATCH_CLOSE_MIN_PCT",                          "float", "Daily Quests: hatch GUI close-button yellow threshold (0-1)"),
    ("QUEST_COMBINE_ALIASES",                         "str",   "Daily Quests: OCR aliases for Combine Pets"),
    ("HATCH_AREA1_ALIASES",                           "str",   "Daily Quests: hatch GUI aliases for the Area 1 Egg page"),
    ("BOSS_FIGHT_A1_MODE_OCR",                      "json",  "Bramble mode OCR aliases"),
    ("STONE_STALL_TIMEOUT",      "int",   "Stall timeout (seconds)"),
    ("SMART_FAILURE_TIMEOUT",    "int",   "Smart failure timeout (seconds)"),
    ("STARTUP_SETTLE_SECONDS",   "float", "Startup wait (seconds)"),
    ("A5_POST_MACRO_VERIFY_DELAY", "float", "Area 5: delay after A5 macro before post-navigation settle check (seconds)"),
    ("A5_CHECK_ATTEMPTS",        "int",   "Area 5 check attempts"),
    ("REBIRTH_CHECK_DELAY",      "int",   "Rebirth check delay (seconds)"),
    ("REBIRTH_POST_CONFIRM_WAIT", "int",   "Post-rebirth cooldown (seconds to wait after rebirth confirmed before teleporting to base)"),
    ("STONE_FOR_UNLOCK_DRILLS",  "float", "Drill unlock threshold"),
    ("BASE_ROCK_DRILL_PRESSES",  "int",   "Base rock manual-strength drill presses per burst"),
    ("AUTO_ROCK_MAX_GRIND_SECONDS", "int", "Auto Strength: max grind time per stage rock before re-route (seconds, not baserock)"),
    ("USE_SHORTCUTS",            "bool",  "Use Shortcuts"),
    ("UNLOCK_DRILLS",            "bool",  "Unlock drills automatically when the stone threshold is reached"),
    ("FORCE_RESTART_ON_FAILURE", "bool",  "Force Restart"),
    ("PAUSE_ON_LAG",             "bool",  "Pause on Lag"),
    ("USE_DRILL_ON_A5_METEOR",   "bool",  "Use Drill on A5 Meteor"),
    ("USE_DRILL_ON_ROCK",        "bool",  "Use Drill on Rock"),
    ("USE_DRILL_ON_BASEROCK",    "bool",  "Use Drill on Baserock"),
    ("GAME_DETECT_IMAGE",        "str",   "In-Game image detection: picked template (filename in data/game_detect/)"),
    ("GAME_DETECT_BOX",          "json",  "In-Game image detection: pick box [x1,y1,x2,y2] (pick-time screen px)"),
    ("GAME_DETECT_SCREEN",       "json",  "In-Game image detection: screen size the box was picked at [w,h]"),
    ("GAME_DETECT_DIFF",         "float", "In-Game image detection: max image difference % counted as in-game (default 5)"),
    ("FORCE_GAME_LOGO_IMAGE",    "str",   "Map search: game logo image (picked template in data/game_detect/)"),
    ("FORCE_GAME_LOGO_BOX",      "json",  "Map search: game logo pick box [x1,y1,x2,y2] (pick-time screen px)"),
    ("FORCE_GAME_LOGO_SCREEN",   "json",  "Map search: screen size the logo box was picked at [w,h]"),
    ("FORCE_NOTINGAME_WAIT",     "int",   "Not in game: wait up to X seconds for HUD/menu before leaving (default 120)"),
    ("FORCE_MENU_TIMEOUT",       "int",   "Lobby menu search: max seconds to find the PLAY button (default 60)"),
    ("FORCE_PLAY_SETTLE",        "float", "Wait after MT2 confirmed before pressing PLAY (seconds, default 5)"),
    ("FORCE_MAP_CODE",           "str",   "Island code typed into Search Discover when the wrong game is selected"),
    ("FORCE_MAP_SEARCH_TIMEOUT", "int",   "Map search: max seconds to wait for the game logo image (default 30)"),
    ("FORCE_MAP_SEARCH_ATTEMPTS", "int",  "Map search: full attempts (reset + retype + search) before giving up (default 3)"),
    ("FORCE_SELECT_TIMEOUT",     "int",   "Map search: max seconds to wait for SELECT after the billboard (default 30)"),
    ("FORCE_TITLE_TIMEOUT",      "int",   "Map search: max seconds to wait for the MT2 title again (default 30)"),
    ("FORCE_OCR_PLAY_ALIASES",   "str",   "PLAY button OCR aliases (comma separated, normalized)"),
    ("FORCE_OCR_TITLE_ALIASES",  "str",   "Selected-game title OCR aliases (comma separated, normalized)"),
    ("FORCE_OCR_SEARCH_ALIASES", "str",   "Search Discover OCR aliases (comma separated, normalized)"),
    ("FORCE_OCR_SELECT_ALIASES", "str",   "SELECT button OCR aliases (comma separated, normalized)"),
    ("FORCE_PLAY_OCR_REGION",    "json",  "PLAY button OCR region [x1,y1,x2,y2] (1920x1080 base, scaled at runtime)"),
    ("FORCE_GAME_TITLE_REGION",  "json",  "Selected-game title OCR region [x1,y1,x2,y2] (1920x1080 base)"),
    ("FORCE_SEARCH_DISCOVER_REGION", "json", "Search Discover OCR region [x1,y1,x2,y2] (1920x1080 base)"),
    ("FORCE_SELECT_OCR_REGION",   "json",  "SELECT button OCR region [x1,y1,x2,y2] (1920x1080 base)"),
    ("FORCE_SEARCH_CLICK",       "json",  "Search Discover click [x,y] (1920x1080 base, scaled at runtime)"),
    ("FORCE_GAME_BILLBOARD_CLICK", "json", "Map search billboard click [x,y] (1920x1080 base, scaled at runtime)"),
    ("FORCE_SELECT_CLICK",       "json",  "SELECT button click [x,y] (1920x1080 base, scaled at runtime)"),
    ("MENU_RESUME_JOIN_WAIT",     "int",   "Menu resume: join wait after PLAY (seconds, default 120 — a join can take up to 2min)"),
    ("STONE_ICON_MISSING_WAIT",  "int",   "In-game HUD missing: wait before recovery (seconds)"),
    ("MENU_PLAY_COLOR_THRESH",   "float", "PLAY button color detection threshold (0.0-1.0, default 0.08 = 8% of region must match yellow)"),
    ("MENU_PLAY_HUE_TOL",        "int",   "PLAY button HSV hue tolerance (default 15)"),
    ("MENU_PLAY_SAT_TOL",        "int",   "PLAY button HSV saturation tolerance (default 60)"),
    ("MENU_PLAY_VAL_TOL",        "int",   "PLAY button HSV value tolerance (default 60)"),
    ("METEOR_RED_MISSING_THRESH", "float", "Meteor broken: red fill threshold in health bar region (default 0.003)"),
    ("METEOR_RED_SEEN_THRESH",   "float", "Meteor alive: red fill threshold in health bar region (default 0.010)"),
    ("METEOR_BROKEN_VOTES",      "int",   "Meteor broken: consecutive missing-red samples required (default 1)"),
    ("METEOR_BREAK_TIMEOUT_SECONDS", "float", "Meteor max grind (seconds, default 10). Then assume broken."),
    ("METEOR_INITIAL_GAIN_SECONDS", "float", "Meteor initial gain-check window (seconds, default 8). Increase if first gain is slow."),
    ("METEOR_GAIN_REL_THRESHOLD", "float", "Meteor gain relative threshold (default 1.00001 = +0.001%). Lower = more sensitive."),
    ("METEOR_GAIN_MIN_HITS", "int", "Meteor gain checks needed before confirm (default 2)."),
    ("METEOR_POST_BREAK_HIT_SECONDS", "float", "Meteor: keep hitting this many seconds after red bar disappears (default 0.10)"),
    ("MANUAL_STR_MAX_SECONDS",   "int",   "Max time per rock (seconds)"),
    ("MANUAL_STR_IDLE_WAIT",     "float", "Idle timeout, nothing buyable (seconds)"),
    ("MANUAL_STR_NO_STRENGTH_TIMEOUT", "float", "No-progress reroute (seconds)"),
    ("MANUAL_STR_CLICK_METHOD", "str", "Clicking method (default / classic / compat)"),
    ("MANUAL_STR_OPEN",                             "bool",  "Manual Strength Open (off = macros must open the window)"),
    ("MANUAL_STR_CLICK_DELAY_MS",                     "int",   "Manual Strength: click delay between clicks (ms, min 1)"),
    ("MANUAL_STR_CLICK_HOLD_MS",                     "int",   "Manual Strength: click hold time down->up (ms, min 1)"),
    ("MANUAL_STR_BOTTOM_RIGHT_CLICKS", "int", "Bottom row: right clicks per left click"),
    ("MANUAL_STR_BOTTOM_LEFT_CLICKS", "int", "Bottom row: left (unlock) clicks"),
    ("MANUAL_STR_HUD_STALL_SECONDS", "float", "HUD stall timeout (seconds)"),
    ("MANUAL_STR_DETECTION", "str", "Detection type (stone / surge level)"),
    ("MANUAL_STR_STONE_TARGET", "float", "Stone threshold - stone detection (default 1.36e152)"),
    ("MANUAL_STR_SURGE_TARGET", "int", "Surge level threshold - surge detection (0-999)"),
    ("MANUAL_STR_OPEN_AFTER_HIT_WAIT", "float", "Open: wait after hit before monitor key (seconds)"),
    ("MANUAL_STR_OPEN_AFTER_MONITOR_WAIT", "float", "Open: wait after monitor key before open click (seconds)"),
    ("ROUTE_REDO_LIMIT", "int", "Route retry limit"),
    ("MANUAL_STR_POST_CLOSE_SETTLE_SECONDS", "float", "Settle after menu close (seconds)"),
    ("MANUAL_STR_POST_CLOSE_TOPUP_SECONDS", "float", "Topup after menu close (seconds)"),
    ("MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS", "float", "Topup confirm timeout (seconds)"),
    ("MANUAL_STR_CLOSE_YELLOW_THRESH", "float", "Close button sensitivity (0.0-1.0)"),
    ("UI_CLICK_SETTLE", "float", "Wait after UI clicks (seconds)"),
    ("UI_BTN_SETTLE", "float", "Wait after menu clicks (seconds)"),
    ("MAP_LOAD_FIXED_SECONDS", "float", "Map load settle (seconds) — fixed wait after every teleport"),
    ("LOBBY_SETTLE", "float", "Lobby: wait after shard (seconds)"),
    ("LOBBY_READY_SETTLE", "float", "Lobby: wait before clicking Ready (seconds)"),
    ("LOBBY_STEP_DELAY", "float", "Lobby: delay between clicks (seconds)"),
        ("REBIRTH_BTN2_TIMEOUT", "float", "Rebirth: confirm button wait (seconds)"),
    ("TELEPORT_MENU_SHIFT_DX", "int", "F4 menu left-shift bug offset in pixels (0 = disable shift detection)"),
    ("MANUAL_STR_ONLY_LAST_ROW", "bool", "Bottom row only"),
    ("SAVE_DEBUG_CROPS",         "bool", "Save debug crops"),
    ("MENU_TOGGLE_BINDING", "str", "Monitor Menu - F4"),
    ("PICKAXE_EQUIP_BINDING", "str", "Pickaxe - F"),
    ("DRILL_ACTIVATE_BINDING", "str", "Activate Drill - I"),
    ("WEAPON_1_BINDING", "str", "Weapon"),
    ("WEAPON_2_BINDING", "str", "Monitor Item"),
    ("MONITOR_ITEM_BINDING", "str", "Monitor Item"),
    ("SPRINT_BINDING", "str", "Sprint"),
    ("FORWARD_BINDING", "str", "Forwards"),
    ("BACKWARD_BINDING", "str", "Backwards"),
    ("LEFT_BINDING", "str", "Left"),
    ("RIGHT_BINDING", "str", "Right"),
    ("JUMP_BINDING", "str", "Jump"),
    ("CROUCH_BINDING", "str", "Crouch"),
    ("AUTO_STRENGTH_TOGGLE_BINDING", "str", "Auto Strength Toggle - Mouse Scroll Click"),
    ("BOT_START_BINDING", "str", "Start Bot - F8"),
    ("BOT_STOP_BINDING", "str", "Stop Bot - F9"),
    ("RECORDER_RECORD_BINDING", "str", "Recorder Record"),
    ("RECORDER_PLAY_BINDING", "str", "Recorder Play / Stop"),
    ("RECORDER_SMOOTH_MOVE_KEY", "str", "Recorder Smooth Move (hold)"),
    ("KRAKEN_HB_CONFIRM_WINDOW_SECONDS", "float", "Kraken: kill-confirm watch after health bar gone (seconds)"),
    ("KRAKEN_POST_HB_LOSS_SHOOT_SECONDS", "float", "Kraken: keep firing after health bar gone (seconds)"),
    ("KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", "float", "Kraken: max wait for boss health bar to appear (seconds)"),
    ("KRAKEN_DEATH_WAIT_SECONDS", "float", "Kraken: wait for respawn after death (seconds)"),
    ("KRAKEN_MENU_WAIT_SECONDS", "float", "Kraken: settle after opening the boss menu (seconds)"),
    ("KRAKEN_JOIN_CLICK_GAP_SECONDS", "float", "Kraken: gap between the two Join clicks (seconds)"),
    ("KRAKEN_POST_JOIN_WAIT_SECONDS", "float", "Kraken: settle after joining (seconds)"),
    ("KRAKEN_REWARD_OPEN_WAIT_SECONDS", "float", "Kraken: wait for reward window to open (seconds)"),
    ("KRAKEN_REWARD_WALK_SECONDS", "float", "Kraken: reward walk forward time (seconds)"),
    ("KRAKEN_ROUTE_ATTEMPTS", "int", "Kraken: route retries before failing"),
    ("KRAKEN_SHOOT_POLL_SECONDS", "float", "Kraken: shoot-loop poll interval (seconds)"),
    ("KRAKEN_SHOOT_REASSERT_SECONDS", "float", "Kraken: re-assert left mouse down every N seconds"),
    ("ZYTOS_POST_KILL_WAIT_SECONDS", "float", "Zytos: wait after boss killed before post-fight walk (seconds)"),
    ("ZYTOS_HB_CONFIRM_WINDOW_SECONDS", "float", "Zytos: kill-confirm watch after health bar gone (seconds)"),
    ("ZYTOS_HB_EXTENDED_WINDOW_SECONDS", "float", "Zytos: extended kill-confirm watch (seconds)"),
    ("ZYTOS_POST_HB_LOSS_SHOOT_SECONDS", "float", "Zytos: keep firing after health bar gone (seconds)"),
    ("ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", "float", "Zytos: max wait for boss health bar to appear (seconds)"),
    ("ZYTOS_DEATH_WAIT_SECONDS", "float", "Zytos: wait for respawn after death (seconds)"),
    ("ZYTOS_MENU_WAIT_SECONDS", "float", "Zytos: settle after opening the boss menu (seconds)"),
    ("ZYTOS_JOIN_CLICK_GAP_SECONDS", "float", "Zytos: gap between the two Join clicks (seconds)"),
    ("ZYTOS_POST_JOIN_WAIT_SECONDS", "float", "Zytos: settle after joining (seconds)"),
    ("ZYTOS_REWARD_OPEN_WAIT_SECONDS", "float", "Zytos: wait for reward window to open (seconds)"),
    ("ZYTOS_ROUTE_ATTEMPTS", "int", "Zytos: route retries before failing"),
    ("ZYTOS_SHOOT_POLL_SECONDS", "float", "Zytos: shoot-loop poll interval (seconds)"),
    ("ZYTOS_SHOOT_REASSERT_SECONDS", "float", "Zytos: re-assert left mouse down every N seconds"),
    ("DELVE_MENU_WAIT_SECONDS", "float", "Delve: settle after opening the boss menu (seconds)"),
    ("DELVE_JOIN_CLICK_GAP_SECONDS", "float", "Delve: gap between the two Join clicks (seconds)"),
    ("DELVE_POST_JOIN_WAIT_SECONDS", "float", "Delve: settle after joining (seconds)"),
    ("DELVE_DEATH_WAIT_SECONDS", "float", "Delve: wait for respawn after death (seconds)"),
    ("DELVE_SHOOT_POLL_SECONDS", "float", "Delve: shoot-loop poll interval (seconds)"),
    ("DELVE_SHOOT_REASSERT_SECONDS", "float", "Delve: re-assert left mouse down every N seconds"),
]

def _read_config_values() -> dict:
    import config as _cfg
    result = {}
    for key, typ, _ in CONFIG_EDITABLE:
        val = getattr(_cfg, key, None)
        result[key] = val
    return result

def _apply_config_to_module(updates: dict):
    """Write updates to config module (shared singleton) and to dashboard _state.
    bot.py runs as __main__ so `import bot` gives a DIFFERENT module object ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â
    setattr(_bot, ...) has no effect on __main__. Instead bot reads live toggles
    from dashboard.get_state() at call time. All we need here is:
      1. update the config module (shared via sys.modules['config'])
      2. update dashboard _state so bot.get_state() picks it up instantly
    """
    import config as _cfg
    for key, value in updates.items():
        setattr(_cfg, key, value)
    # Push all updates directly into dashboard state ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â bot reads live from get_state()
    state_map = {
        "UNLOCK_DRILLS":          "unlock_drills",
        "ACTIVATE_DRILLS":        "activate_drills",
        "USER_SENS_H":            "user_sens_h",
        "USER_SENS_V":            "user_sens_v",
        "STONE_FOR_A5_STAGE1":    "stone_for_a5_stage1",
        "STONE_FOR_A5_STAGE2":    "stone_for_a5_stage2",
        "STONE_FOR_A5_STAGE3":    "stone_for_a5_stage3",
        "STONE_FOR_A5_STAGE4":    "stone_for_a5_stage4",
        "STONE_FOR_METEOR":       "stone_for_meteor",
        "STONE_STALL_TIMEOUT":    "stone_stall_timeout",
        "SMART_FAILURE_TIMEOUT":  "smart_failure_timeout",
        "A5_CHECK_ATTEMPTS":      "a5_check_attempts",
        "REBIRTH_CHECK_DELAY":    "rebirth_check_delay",
        "REBIRTH_POST_CONFIRM_WAIT":"rebirth_post_confirm_wait",
        "STONE_FOR_UNLOCK_DRILLS":"stone_for_unlock_drills",
        "BASE_ROCK_DRILL_PRESSES":"base_rock_drill_presses",
        "USE_DRILL_ON_A5_METEOR":"rebirth_drill_on_a5_meteor",
        "USE_DRILL_ON_ROCK":"rebirth_drill_on_rock",
        "USE_DRILL_ON_BASEROCK":"rebirth_drill_on_baserock",
        "FORCE_RESTART_ON_FAILURE":"force_restart",
        "PAUSE_ON_LAG":           "pause_on_lag",
        "MENU_RESUME_JOIN_WAIT":  "menu_resume_join_wait",
        "STONE_ICON_MISSING_WAIT": "stone_icon_missing_wait",
        "STONE_ICON_THRESH":       "stone_icon_thresh",
        "MENU_PLAY_COLOR_THRESH":  "menu_play_color_thresh",
        "MENU_PLAY_HUE_TOL":       "menu_play_hue_tol",
        "MENU_PLAY_SAT_TOL":       "menu_play_sat_tol",
        "MENU_PLAY_VAL_TOL":       "menu_play_val_tol",
    }
    state_updates = {}
    for cfg_key, state_key in state_map.items():
        if cfg_key in updates:
            state_updates[state_key] = updates[cfg_key]
    if state_updates:
        update_state(**state_updates)
    # Game Detection: keep state.game_detect_set in sync (bot gate + widget)
    if any(k in updates for k in ("GAME_DETECT_IMAGE", "GAME_DETECT_BOX", "GAME_DETECT_SCREEN")):
        try:
            import game_detect as _gd_mod
            with _lock:
                _state["game_detect_set"] = bool(_gd_mod.is_game_detect_set())
        except Exception as _gd_e:
            log.debug(f"game_detect_set sync failed: {_gd_e}")
    if any(k in updates for k in ("FORCE_GAME_LOGO_IMAGE", "FORCE_GAME_LOGO_BOX", "FORCE_GAME_LOGO_SCREEN")):
        try:
            import game_detect as _gd_mod
            with _lock:
                _state["game_logo_set"] = bool(_gd_mod.is_game_logo_set())
        except Exception as _gd_e:
            log.debug(f"game_logo_set sync failed: {_gd_e}")

def _save_config_to_file(updates: dict):
    """Persist config changes to config.json via the config module helper."""
    try:
        import config as _cfg_mod
        _cfg_mod.save_values(updates)
        log.info(f"[Config] Saved {len(updates)} key(s)")
        log.debug(f"[Config] Saved keys: {list(updates.keys())}")
    except Exception as e:
        log.warning(f"Config file save failed: {e}")

# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Shared live state ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
_lock = threading.Lock()
_state = {
    "bot_alive": True, "status": "WAITING",
    "goal": "Press Start to begin", "next_steps": "", "auto_str": None,
    "stone": None,
    "run_number": 0, "run_start_time": None, "run_steps": 0,
    "run_errors": 0, "run_active": False,
    "cur_stone": None, "cur_auto_str": None,
    "total_rebirths": 0, "total_errors": 0,
    "avg_time_secs": 0.0, "min_time_secs": 0.0, "max_time_secs": 0.0,
    "run_history": [],
    "delve_run_history": _load_delve_history(),
    "kraken_run_history": _load_kraken_history(),
    "zytos_run_history": _load_zytos_history(),
    "waiting_for_start": True, "killed": False,
    "bot_mode": "rebirth",
    "farm_meteor_area": "a6",
    "run_mode": "a1s1", "unlock_drills": True, "activate_drills": True,
    "rebirth_drill_on_a5_meteor": True,
    "rebirth_drill_on_rock": True,
    "rebirth_drill_on_baserock": True,
    "rebirth_activate_drills": True, "delve_activate_drills": True, "kraken_activate_drills": True, "zytos_activate_drills": True,
    "menu_resume": False,
        "crater_overlay": True,
        "crater_elapsed_secs": 0.0,
        "crater_pet_drops": 0,
        "crater_session_history": [],
    "auto_strength": False,
    "boss_fight_a1": False,
    "daily_quests": False,
    "force_restart": False,
    "pause_on_lag": False,
    "missing_loadouts": [],
    "loadout_block_seq": 0,
    "game_detect_set": False,
    "game_detect_block_seq": 0,
    "kraken_drill": False,
    "kraken_movement_mode": "linear",
    "zytos_movement_mode": "linear",
    "stage": "unknown",
    "active_app_tab": "run",
}
_persisted = _load_persistent_state()
_state.update(_persisted)
if str(_state.get("run_mode") or "") in {"a6s1", "a6s2", "a6s3", "a6s4"}:
    _state["run_mode"] = "a5meteor"
if _state.get("run_mode") not in {"a5meteor", *{f"a{a}s{s}" for a in range(1, 6) for s in range(1, 5)}}:
    _state["run_mode"] = "a1s1"
if _state.get("bot_mode") not in {"rebirth", "delve", "kraken", "zytos", "crater", "farm_meteor"}:
    _state["bot_mode"] = "rebirth"
if _state.get("farm_meteor_area") not in {"a6", "a7", "a8"}:
    _state["farm_meteor_area"] = str(getattr(_cfg_init, "FARM_METEOR_AREA", "a6")).strip().lower()
    if _state["farm_meteor_area"] not in {"a6", "a7", "a8"}:
        _state["farm_meteor_area"] = "a6"
if _state.get("kraken_movement_mode") not in {"linear", "square"}:
    _state["kraken_movement_mode"] = "linear"
if _state.get("zytos_movement_mode") not in {"linear", "square"}:
    _state["zytos_movement_mode"] = "linear"

try:
    import config as _cfg_init
    if "bot_mode" not in _persisted:
        _state["bot_mode"] = str(getattr(_cfg_init, "BOT_MODE", "rebirth")).lower()
    _state["unlock_drills"] = bool(getattr(_cfg_init, "UNLOCK_DRILLS", True))
    _state["activate_drills"] = bool(getattr(_cfg_init, "ACTIVATE_DRILLS", True))
    _state["auto_strength"] = False
    if "boss_fight_a1" not in _persisted:
        _state["boss_fight_a1"] = False
    if "daily_quests" not in _persisted:
        _state["daily_quests"] = False
    if "farm_meteor_area" not in _persisted:
        _state["farm_meteor_area"] = str(getattr(_cfg_init, "FARM_METEOR_AREA", "a6")).strip().lower()
        if _state["farm_meteor_area"] not in {"a6", "a7", "a8"}:
            _state["farm_meteor_area"] = "a6"
    if "force_restart" not in _persisted:
        _state["force_restart"] = bool(getattr(_cfg_init, "FORCE_RESTART_ON_FAILURE", False))
    if "pause_on_lag" not in _persisted:
        _state["pause_on_lag"] = bool(getattr(_cfg_init, "PAUSE_ON_LAG", False))
    _state["menu_resume"] = bool(_state.get("force_restart", False))
    if "kraken_drill" not in _persisted:
        _state["kraken_drill"] = bool(getattr(_cfg_init, "KRAKEN_DRILL_ENABLED", False))
    if "rebirth_activate_drills" not in _persisted:
        _state["rebirth_activate_drills"] = bool(getattr(_cfg_init, "ACTIVATE_DRILLS", True))
    if "rebirth_drill_on_a5_meteor" not in _persisted:
        _state["rebirth_drill_on_a5_meteor"] = bool(getattr(_cfg_init, "USE_DRILL_ON_A5_METEOR", True))
    if "rebirth_drill_on_rock" not in _persisted:
        _state["rebirth_drill_on_rock"] = bool(getattr(_cfg_init, "USE_DRILL_ON_ROCK", True))
    if "rebirth_drill_on_baserock" not in _persisted:
        _state["rebirth_drill_on_baserock"] = bool(getattr(_cfg_init, "USE_DRILL_ON_BASEROCK", True))
    if "delve_activate_drills" not in _persisted:
        _state["delve_activate_drills"] = bool(getattr(_cfg_init, "DELVE_ACTIVATE_DRILLS", True))
    if "kraken_activate_drills" not in _persisted:
        _state["kraken_activate_drills"] = bool(getattr(_cfg_init, "KRAKEN_ACTIVATE_DRILLS", True))
    if "zytos_activate_drills" not in _persisted:
        _state["zytos_activate_drills"] = bool(getattr(_cfg_init, "ZYTOS_ACTIVATE_DRILLS", True))
    if "kraken_movement_mode" not in _persisted:
        _state["kraken_movement_mode"] = str(getattr(_cfg_init, "KRAKEN_MOVEMENT_MODE", "linear")).strip().lower()
    if _state.get("kraken_movement_mode") not in {"linear", "square"}:
        _state["kraken_movement_mode"] = "linear"
    if "zytos_movement_mode" not in _persisted:
        _state["zytos_movement_mode"] = str(getattr(_cfg_init, "ZYTOS_MOVEMENT_MODE", "linear")).strip().lower()
    if _state.get("zytos_movement_mode") not in {"linear", "square"}:
        _state["zytos_movement_mode"] = "linear"
except Exception:
    pass
_sync_state_from_stats(force=True)

# Game Detection boot sync: was an In-Game image already picked?
try:
    import game_detect as _gd_init
    _state["game_detect_set"] = bool(_gd_init.is_game_detect_set())
except Exception as _gd_boot_e:
    log.debug(f"game_detect boot sync failed: {_gd_boot_e}")

# Session start timestamp ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â set once when dashboard module is loaded (= bot launch)
_SESSION_START_TIME: float = __import__('time').time()

def update_state(**kwargs):
    with _lock:
        _state.update(kwargs)
        snap = _json_safe(dict(_state))
    _save_persistent_state(snap)

def get_state() -> dict:
    """Return a snapshot of the current dashboard state (used by bot.py)."""
    with _lock:
        return dict(_state)


def record_delve_run(duration_secs: float, reason: str = "ended") -> dict:
    duration = max(0.0, _safe_float(duration_secs, 0.0))
    start_time = time.time() - duration if duration > 0 else time.time()
    with _lock:
        history = list(_state.get("delve_run_history", []) or [])
        next_num = 1 + max([int(r.get("run_number", 0) or 0) for r in history] or [0])
        entry = {
            "run_number": next_num,
            "start_time": start_time,
            "end_time": time.time(),
            "duration_secs": duration,
            "reason": str(reason or "ended"),
        }
        history.append(entry)
        history = _trim_history(history)
        _state["delve_run_history"] = history
        snap = dict(_state)
    _save_delve_history(history)
    _save_persistent_state(snap)
    return entry


def record_kraken_run(duration_secs: float, reason: str = "ended") -> dict:
    duration = max(0.0, _safe_float(duration_secs, 0.0))
    start_time = time.time() - duration if duration > 0 else time.time()
    with _lock:
        history = list(_state.get("kraken_run_history", []) or [])
        next_num = 1 + max([int(r.get("run_number", 0) or 0) for r in history] or [0])
        entry = {
            "run_number": next_num,
            "start_time": start_time,
            "end_time": time.time(),
            "duration_secs": duration,
            "reason": str(reason or "ended"),
        }
        history.append(entry)
        history = _trim_history(history)
        _state["kraken_run_history"] = history
        snap = dict(_state)
    _save_kraken_history(history)
    _save_persistent_state(snap)
    return entry

def record_zytos_run(duration_secs: float, reason: str = "ended") -> dict:
    duration = max(0.0, _safe_float(duration_secs, 0.0))
    start_time = time.time() - duration if duration > 0 else time.time()
    with _lock:
        history = list(_state.get("zytos_run_history", []) or [])
        next_num = 1 + max([int(r.get("run_number", 0) or 0) for r in history] or [0])
        entry = {
            "run_number": next_num,
            "start_time": start_time,
            "end_time": time.time(),
            "duration_secs": duration,
            "reason": str(reason or "ended"),
        }
        history.append(entry)
        history = _trim_history(history)
        _state["zytos_run_history"] = history
        snap = dict(_state)
    _save_zytos_history(history)
    _save_persistent_state(snap)
    return entry




# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Flask app ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
_CSRF_TOKEN = secrets.token_urlsafe(32)
_ALLOWED_ORIGINS = {"http://127.0.0.1:7373", "http://localhost:7373"}

@app.before_request
def _guard_local_post():
    if request.method != "POST":
        return None
    # Recorder engine lives at /me and uses its own POSTs (no dashboard CSRF header).
    if (request.path or "").startswith("/me"):
        return None
    # The blockly macro editor iframe (served at /editor/) posts to the
    # picker endpoints directly and has no access to the dashboard CSRF
    # token — same-origin, local-only server.
    if (request.path or "").startswith("/blockly/"):
        return None
    origin = request.headers.get("Origin")
    if origin and origin not in _ALLOWED_ORIGINS:
        return jsonify({"ok": False, "error": "Bad request origin."}), 403
    token = request.headers.get("X-MT2-CSRF", "")
    if not hmac.compare_digest(token, _CSRF_TOKEN):
        return jsonify({"ok": False, "error": "Bad request token."}), 403
    return None

# ── Blockly macro editor assets ─────────────────────────────────────────────
# The visual macro editor (code/editor/) runs inside the recorder tab's
# iframe; it loads the blockly core from code/blockly/ and its block
# definitions through /blockly/blocks_data. The .macro files it edits stay
# plain v1 text — see macro_engine/app.py.

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_BLOCKLY_DIR = os.path.join(_CODE_DIR, "blockly")
_EDITOR_DIR = os.path.join(_CODE_DIR, "editor")


def _blockly_safe_path(*parts):
    base = os.path.normpath(_BLOCKLY_DIR)
    path = os.path.normpath(os.path.join(base, *parts))
    if path != base and not path.startswith(base + os.sep):
        return None
    return path


@app.route("/editor/<path:filename>")
def editor_assets(filename):
    root = os.path.normpath(_EDITOR_DIR)
    path = os.path.normpath(os.path.join(root, filename))
    if path != root and not path.startswith(root + os.sep):
        return jsonify({"ok": False, "error": "Not found"}), 404
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "Not found"}), 404
    return send_file(path)


@app.route("/blockly/lib/<path:filename>")
def blockly_lib(filename):
    path = _blockly_safe_path("lib", filename)
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "Not found"}), 404
    return send_file(path)


@app.route("/blockly/media/<path:filename>")
def blockly_media(filename):
    path = _blockly_safe_path("lib", "media", filename)
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "Not found"}), 404
    return send_file(path)


@app.route("/blockly/<path:filename>")
def blockly_file(filename):
    path = _blockly_safe_path(filename)
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "Not found"}), 404
    return send_file(path)


_BLOCKS_DATA_CACHE = None


def _blockly_scan_blocks():
    # Scan block .js definitions (code/blockly/blocks/**.block.js) for the
    # editor to eval — {name, code, category} per file.
    blocks_dir = os.path.join(_BLOCKLY_DIR, "blocks")
    result = []
    seen_paths = set()
    if not os.path.isdir(blocks_dir):
        return result
    for category in sorted(os.listdir(blocks_dir)):
        cat_path = os.path.join(blocks_dir, category)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.endswith(".block.js"):
                continue
            fpath = os.path.join(cat_path, fname)
            if fpath in seen_paths:
                continue
            seen_paths.add(fpath)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    code = f.read()
                result.append({"name": fname, "code": code, "category": category})
            except Exception:
                pass
    return result


@app.route("/blockly/blocks_data")
def blockly_blocks_data():
    global _BLOCKS_DATA_CACHE
    if _BLOCKS_DATA_CACHE is None:
        _BLOCKS_DATA_CACHE = {"blocks": _blockly_scan_blocks()}
    return jsonify(_BLOCKS_DATA_CACHE)


@app.route("/blockly/screen_info")
def blockly_screen_info():
    w, h = 1920, 1080
    try:
        import ctypes
        w = int(ctypes.windll.user32.GetSystemMetrics(0))
        h = int(ctypes.windll.user32.GetSystemMetrics(1))
    except Exception:
        pass
    try:
        g = math.gcd(int(w), int(h))
        rw, rh = (int(w) // g, int(h) // g) if g else (16, 9)
    except Exception:
        rw, rh = 16, 9
    return jsonify({"ok": True, "width": int(w), "height": int(h), "ratio_w": rw, "ratio_h": rh})


# ── F2 screen picker (shared by the blockly macro editor) ───────────────────
# Arm F2 → capture the full screen → the editor crops a region from the
# frozen shot into the macro's images folder.

_PICKER_LOCK = threading.Lock()
_PICKER = {"state": "idle", "mode": None, "error": None, "f2_armed": False,
           "shot_path": None, "screen": None, "armed_at": 0.0}


def _picker_reset(state="idle"):
    _PICKER.update({"state": state, "mode": None, "error": None,
                    "shot_path": None, "screen": None, "armed_at": 0.0})


def _picker_disarm_f2():
    if not _PICKER.get("f2_armed"):
        return
    try:
        import keyboard
        keyboard.unhook_key("f2")
    except Exception:
        pass


def _picker_launch(mode):
    # runs on the keyboard module's hook thread — one shot, then disarm.
    with _PICKER_LOCK:
        if _PICKER["state"] != "armed":
            return
        _PICKER["state"] = "capturing"
        _picker_disarm_f2()
    try:
        import time as _time
        _time.sleep(0.15)  # let the F2 keypress / window settle
        import cv2
        import tempfile
        from screen import grab_full_screen
        arr = grab_full_screen()
        if arr is None or arr.size == 0:
            raise RuntimeError("empty screenshot")
        shot_path = os.path.join(tempfile.gettempdir(), "mf_picker_shot.png")
        if not cv2.imwrite(shot_path, arr):
            raise RuntimeError("could not save screenshot")
        with _PICKER_LOCK:
            _PICKER.update({
                "state": "captured",
                "shot_path": shot_path,
                "screen": [int(arr.shape[1]), int(arr.shape[0])],
            })
    except Exception as exc:
        with _PICKER_LOCK:
            _picker_reset("error")
            _PICKER["error"] = str(exc)


@app.route("/blockly/picker/prepare", methods=["POST"])
def blockly_picker_prepare():
    body = request.get_json(silent=True) or {}
    mode = "box" if str(body.get("mode") or "").lower() == "box" else "point"
    with _PICKER_LOCK:
        _picker_disarm_f2()
        _picker_reset("armed")
        _PICKER["mode"] = mode
        try:
            import time as _time
            _PICKER["armed_at"] = _time.time()
            import keyboard
            keyboard.on_press_key("f2", lambda e: _picker_launch(mode))
            _PICKER["f2_armed"] = True
        except Exception as exc:
            _picker_reset("error")
            _PICKER["error"] = "F2 hotkey unavailable (keyboard module): %s" % exc
        ok = _PICKER["state"] == "armed"
        state = _PICKER["state"]
        error = _PICKER["error"]
    return jsonify({"ok": ok, "state": state, "error": error})


@app.route("/blockly/picker/status")
def blockly_picker_status():
    with _PICKER_LOCK:
        # housekeeping: an armed popup that was never closed/captured
        # (tab crash etc.) expires after 10 minutes and disarms F2.
        if _PICKER["state"] == "armed" and _PICKER.get("armed_at"):
            if time.time() - _PICKER["armed_at"] > 600:
                _picker_disarm_f2()
                _picker_reset("idle")
        return jsonify({
            "state": _PICKER["state"],
            "mode": _PICKER["mode"],
            "error": _PICKER["error"],
            "screen": _PICKER["screen"],
            "has_shot": bool(_PICKER["shot_path"]),
        })


@app.route("/blockly/picker/shot")
def blockly_picker_shot():
    with _PICKER_LOCK:
        shot = _PICKER.get("shot_path")
    if not shot or not os.path.exists(shot):
        return jsonify({"ok": False, "error": "no screenshot"}), 404
    return send_file(shot, mimetype="image/png", max_age=0)


@app.route("/blockly/picker/crop_to_file", methods=["POST"])
def blockly_picker_crop_to_file():
    """Crop the armed F2 screenshot into the macro's images folder."""
    body = request.get_json(silent=True) or {}
    box = body.get("box") or []
    dest_dir = str(body.get("dir") or "").strip()
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return jsonify({"ok": False, "error": "box[x1,y1,x2,y2] required"}), 400
    if not dest_dir or not os.path.isabs(dest_dir):
        return jsonify({"ok": False, "error": "absolute dir required"}), 400
    with _PICKER_LOCK:
        shot = _PICKER.get("shot_path") or ""
        screen = _PICKER.get("screen") or []
    if not shot or not os.path.isfile(shot):
        return jsonify({"ok": False, "error": "no screenshot to crop — press F2 first"}), 400
    try:
        from PIL import Image
        x1, y1, x2, y2 = (int(round(float(v))) for v in box)
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        if x2 - x1 < 1 or y2 - y1 < 1:
            return jsonify({"ok": False, "error": "empty region"}), 400
        os.makedirs(dest_dir, exist_ok=True)
        with Image.open(shot) as im:
            im = im.convert("RGB")
            W, H = im.size
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W, x2 or W), min(H, y2 or H)
            crop = im.crop((x1, y1, max(x1 + 1, x2), max(y1 + 1, y2)))
        # 1:1 recorder naming: {screenW}x{screenH}_f2_<ts>.png — the size
        # prefix is what the image loader reads back for scaling.
        sw = int(screen[0]) if len(screen) > 0 and screen[0] else W
        sh = int(screen[1]) if len(screen) > 1 and screen[1] else H
        fname = "%dx%d_f2_%s.png" % (sw, sh, time.strftime("%H%M%S"))
        dest = os.path.join(dest_dir, fname)
        crop.save(dest)
        # remember where on the screen this crop came from
        try:
            from macro_engine.image_meta import write_meta
            meta = write_meta(dest, (x1, y1, x2, y2), (sw, sh))
        except Exception:
            meta = None
        return jsonify({"ok": True, "path": "images/" + fname, "meta": meta})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/blockly/picker/cancel", methods=["POST"])
def blockly_picker_cancel():
    with _PICKER_LOCK:
        _picker_disarm_f2()
        _picker_reset("idle")
    return jsonify({"ok": True})


# ── Game Detection (In-Game image detection, Force Restart tab) ─────────────
# Same F2 pipette flow as the MacroForge pickers: the screenshot stays in
# _PICKER["shot_path"], the user drags a box in the dashboard overlay, the
# crop lands in data/game_detect/game_detect.png with the pick box/point
# embedded in the PNG (mfmeta tEXt chunk) + mirrored into config.json.
@app.route("/game_detect/info")
def game_detect_info():
    import config as _cfg_gd
    import game_detect as _gd
    name = str(getattr(_cfg_gd, "GAME_DETECT_IMAGE", "") or "")
    try:
        meta = _gd.meta_json_for_dashboard()
        is_set = _gd.is_game_detect_set()
    except Exception:
        meta, is_set = None, False
    try:
        diff = float(getattr(_cfg_gd, "GAME_DETECT_DIFF", 5.0))
    except Exception:
        diff = 5.0
    try:
        logo_set = _gd.is_game_logo_set()
    except Exception:
        logo_set = False
    try:
        logo_name = str(getattr(_cfg_gd, "FORCE_GAME_LOGO_IMAGE", "") or "")
    except Exception:
        logo_name = ""
    return jsonify({
        "ok": True,
        "set": bool(is_set),
        "image": name,
        "meta": meta,
        "diff": diff,
        "game_logo_set": bool(logo_set),
        "game_logo_image": logo_name,
        "dir": _gd.game_detect_dir(),
    })


@app.route("/game_detect/preview")
def game_detect_preview():
    import game_detect as _gd
    tmpl = str(request.args.get("tmpl", "in_game") or "in_game").strip().lower()
    path = _gd.game_detect_image_path(tmpl) if tmpl != "game_logo" else _gd.game_logo_image_path()
    if not path:
        return jsonify({"ok": False, "error": "no image picked"}), 404
    return send_file(path, mimetype="image/png", max_age=0)


@app.route("/game_detect/crop", methods=["POST"])
def game_detect_crop():
    """Crop the armed F2 screenshot into data/game_detect/game_detect.png
    and persist GAME_DETECT_IMAGE/BOX/SCREEN. Overwrites the previous pick
    (the Pick button doubles as Change)."""
    body = request.get_json(silent=True) or {}
    tmpl = str(body.get("tmpl", "in_game") or "in_game").strip().lower()
    if tmpl not in ("in_game", "game_logo"):
        return jsonify({"ok": False, "error": "tmpl must be in_game or game_logo"}), 400
    box = body.get("box") or []
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return jsonify({"ok": False, "error": "box[x1,y1,x2,y2] required"}), 400
    with _PICKER_LOCK:
        shot = _PICKER.get("shot_path") or ""
        screen = _PICKER.get("screen") or []
    if not shot or not os.path.isfile(shot):
        return jsonify({"ok": False, "error": "no screenshot to crop \u2014 press F2 first"}), 400
    try:
        from PIL import Image
        x1, y1, x2, y2 = (int(round(float(v))) for v in box)
        if x2 < x1: x1, x2 = x2, x1
        if y2 < y1: y1, y2 = y2, y1
        if x2 - x1 < 1 or y2 - y1 < 1:
            return jsonify({"ok": False, "error": "empty region"}), 400
        import game_detect as _gd
        dest_dir = _gd.game_detect_dir()
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "game_logo.png" if tmpl == "game_logo" else "game_detect.png")
        with Image.open(shot) as im:
            im = im.convert("RGB")
            W, H = im.size
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W, x2 or W), min(H, y2 or H)
            im.crop((x1, y1, max(x1 + 1, x2), max(y1 + 1, y2))).save(dest)
        sw = int(screen[0]) if len(screen) > 0 and screen[0] else W
        sh = int(screen[1]) if len(screen) > 1 and screen[1] else H
        # box + point travel INSIDE the PNG (mfmeta tEXt chunk), same as
        # MacroForge image-block crops — plus the config mirror below.
        meta = None
        try:
            from macro_engine.image_meta import write_meta
            meta = write_meta(dest, (x1, y1, x2, y2), (sw, sh))
        except Exception:
            meta = None
        _gd.save_pick(dest, [x1, y1, x2, y2], [sw, sh], tmpl=tmpl)
        with _lock:
            if tmpl == "game_logo":
                _state["game_logo_set"] = True
            else:
                _state["game_detect_set"] = True
        log.info(f"[GAME_DETECT] picked ({tmpl}) {os.path.basename(dest)} box={(x1, y1, x2, y2)} screen={(sw, sh)}")
        return jsonify({"ok": True, "path": os.path.basename(dest), "meta": meta})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/game_detect/clear", methods=["POST"])
def game_detect_clear():
    body = request.get_json(silent=True) or {}
    tmpl = str(body.get("tmpl", "in_game") or "in_game").strip().lower()
    import game_detect as _gd
    try:
        if tmpl == "game_logo":
            _gd.clear_game_logo()
        else:
            _gd.clear_game_detect()
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    with _lock:
        if tmpl == "game_logo":
            _state["game_logo_set"] = False
        else:
            _state["game_detect_set"] = False
    return jsonify({"ok": True})

@app.route("/")
def index():
    return _DASHBOARD_HTML.replace("__MT2_CSRF_TOKEN__", _CSRF_TOKEN)

@app.route("/state")
def state():
    _sync_state_from_stats(force=False)
    with _lock:
        snap = dict(_state)

    now = time.time()
    if snap.get("run_active") and snap.get("run_start_time"):
        snap["run_elapsed_secs"] = now - snap["run_start_time"]
    else:
        snap["run_elapsed_secs"] = 0
    try:
        from version import __version__ as _app_version
        snap["app_version"] = str(_app_version)
    except Exception:
        pass
    snap["session_start_time"] = _SESSION_START_TIME
    try:
        from macro_engine.app import engine as _me_engine
        snap["recorder_busy"] = bool(_me_engine.is_running() or _me_engine.is_recording())
    except Exception:
        snap["recorder_busy"] = False
    return jsonify(_json_safe(snap))


@app.route("/config", methods=["GET"])
def config_get():
    try:
        vals = _read_config_values()
        schema = [{"key": k, "type": t, "label": l} for k, t, l in CONFIG_EDITABLE]
        return jsonify({"ok": True, "values": vals, "schema": schema})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/config", methods=["POST"])
def config_post():
    data = request.get_json(force=True, silent=True) or {}
    updates = data.get("updates", {})
    typed = {}
    schema_map = {k: t for k, t, _ in CONFIG_EDITABLE}
    schema_map.update({"UNLOCK_DRILLS": "bool", "ACTIVATE_DRILLS": "bool"})
    for key, val in updates.items():
        if key not in schema_map:
            log.warning(f"[Config] Ignoring unknown config key: {key}")
            continue
        t = schema_map[key]
        try:
            if t == "bool":
                if isinstance(val, str):
                    typed[key] = val.strip().lower() in ("true", "1", "yes", "on")
                else:
                    typed[key] = bool(val)
            elif t == "int":  typed[key] = int(val)
            elif t == "float":typed[key] = float(val)
            elif t == "json":
                if isinstance(val, (dict, list)):
                    typed[key] = val
                else:
                    typed[key] = json.loads(val) if isinstance(val, str) else val
            else:             typed[key] = val
        except Exception:
            typed[key] = val
    try:
        if "BOSS_FIGHT_A1_MODE" in typed:
            from config import normalize_bramble_mode
            typed["BOSS_FIGHT_A1_MODE"] = normalize_bramble_mode(typed["BOSS_FIGHT_A1_MODE"])
        if "MANUAL_STR_CLICK_METHOD" in typed:
            _m = str(typed["MANUAL_STR_CLICK_METHOD"]).strip().lower()
            typed["MANUAL_STR_CLICK_METHOD"] = _m if _m in ("default", "classic", "compat") else "default"
        if "MANUAL_STR_DETECTION" in typed:
            _msd = str(typed["MANUAL_STR_DETECTION"]).strip().lower()
            typed["MANUAL_STR_DETECTION"] = _msd if _msd in ("stone", "surge") else "stone"
        if "BOSS_FIGHT_A1_MODE_OCR" in typed:
            from config import normalize_bramble_mode_ocr
            typed["BOSS_FIGHT_A1_MODE_OCR"] = normalize_bramble_mode_ocr(typed["BOSS_FIGHT_A1_MODE_OCR"])
        # quest aliases must be stored as a LIST — a raw string makes
        # classify_quest iterate it character-by-character ('B', 'R', ...)
        if "DAILY_QUEST_ALIASES" in typed:
            from config import normalize_quest_aliases
            typed["DAILY_QUEST_ALIASES"] = normalize_quest_aliases(typed["DAILY_QUEST_ALIASES"])
        if "QUEST_MIMIC_ALIASES" in typed:
            from config import normalize_quest_aliases
            typed["QUEST_MIMIC_ALIASES"] = normalize_quest_aliases(typed["QUEST_MIMIC_ALIASES"])
        if "QUEST_HATCH_ALIASES" in typed:
            from config import normalize_quest_aliases
            typed["QUEST_HATCH_ALIASES"] = normalize_quest_aliases(typed["QUEST_HATCH_ALIASES"])
        if "QUEST_COMBINE_ALIASES" in typed:
            from config import normalize_quest_aliases
            typed["QUEST_COMBINE_ALIASES"] = normalize_quest_aliases(typed["QUEST_COMBINE_ALIASES"])
        if "HATCH_AREA1_ALIASES" in typed:
            from config import normalize_quest_aliases
            typed["HATCH_AREA1_ALIASES"] = normalize_quest_aliases(typed["HATCH_AREA1_ALIASES"])
        if "MONITOR_ITEM_BINDING" in typed and "WEAPON_2_BINDING" not in typed:
            typed["WEAPON_2_BINDING"] = typed["MONITOR_ITEM_BINDING"]
        if "WEAPON_2_BINDING" in typed and "MONITOR_ITEM_BINDING" not in typed:
            typed["MONITOR_ITEM_BINDING"] = typed["WEAPON_2_BINDING"]
        _apply_config_to_module(typed)
        _save_config_to_file(typed)
        if "USER_SENS_H" in typed or "USER_SENS_V" in typed:
            try:
                from macro_engine.app import _apply_bot_user_sensitivity
                _apply_bot_user_sensitivity()
            except Exception:
                pass
        if "UNLOCK_DRILLS" in typed:
            with _lock:
                _state["unlock_drills"] = typed["UNLOCK_DRILLS"]
        if "ACTIVATE_DRILLS" in typed:
            with _lock:
                _state["activate_drills"] = typed["ACTIVATE_DRILLS"]
        if "BOT_START_BINDING" in typed or "BOT_STOP_BINDING" in typed:
            try:
                import bot as _bot_mod
                _bot_mod._register_hotkeys()
            except Exception as _hk_e:
                log.warning(f"[Config] hotkey re-register failed: {_hk_e}")
        if "RECORDER_RECORD_BINDING" in typed or "RECORDER_PLAY_BINDING" in typed or "RECORDER_SMOOTH_MOVE_KEY" in typed:
            try:
                from macro_engine.app import apply_recorder_bindings_from_config
                apply_recorder_bindings_from_config()
            except Exception as _rec_hk:
                log.warning(f"[Config] recorder binding apply failed: {_rec_hk}")
        log.info(f"[Config] Applied {len(typed)} key(s)")
        log.debug(f"[Config] Applied keys: {list(typed.keys())}")
        return jsonify({"ok": True})
    except Exception as e:
        log.warning(f"[Config] Apply failed: {e}")
        return jsonify({"ok": False, "error": str(e)})


@app.route("/run_detail", methods=["GET"])
def run_detail():
    """Per-run action timeline for the per-run graph (macro / strength spans)."""
    try:
        return _run_detail_impl()
    except Exception as e:
        log.exception("[RUN_DETAIL] failed")
        try:
            return jsonify({"ok": False, "message": f"server error: {e}"})
        except Exception:
            return jsonify({"ok": False, "message": "server error"})


def _run_detail_impl():
    try:
        run_number = int(float(request.args.get("run", 0) or 0))
    except Exception:
        run_number = 0
    try:
        start = float(request.args.get("start", 0) or 0)
    except Exception:
        start = 0.0
    import datetime as _dt
    from run_recorder import RECORDS_DIR

    def _read_meta(d):
        try:
            with open(os.path.join(d, "metadata.json"), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _meta_epoch(md, dirname):
        """Recording start epoch: start_epoch field, else created_at ISO, else
        the run_YYYYMMDD_HHMMSS folder name."""
        try:
            se = float(md.get("start_epoch") or 0)
            if se:
                return se
        except Exception:
            pass
        try:
            ca = str(md.get("created_at") or "")
            if ca:
                return _dt.datetime.fromisoformat(ca.replace("Z", "+00:00")).timestamp()
        except Exception:
            pass
        try:
            return _dt.datetime.strptime(dirname[4:], "%Y%m%d_%H%M%S").timestamp()
        except Exception:
            return 0.0

    try:
        dirs = sorted([e.path for e in os.scandir(RECORDS_DIR)
                       if e.is_dir() and e.name.startswith("run_") and not e.name.startswith("run_._")])
    except Exception:
        dirs = []

    def _classify(name):
        n = str(name or "").lower()
        if n.endswith("_hit"):
            return "rock"
        if n.startswith("teleport_") or "_to_" in n or "shortcut" in n or n.startswith("select_loadout"):
            return "nav"
        return "main"

    # Score every recording by |recording_start - run_start|; run_number acts
    # only as a tiebreak hint (numbers repeat across installs of the bot
    # because the recordings folder is shared while stats.json is not).
    best = None   # (score, run_number_match_bonus, dir, meta)
    for d in dirs:
        bn = os.path.basename(d)
        md = _read_meta(d)
        se = _meta_epoch(md, bn)
        if not se:
            continue
        score = abs(se - start) if start else 0.0
        rn = int(md.get("run_number") or 0)
        rn_bonus = 0 if (run_number and rn == run_number) else 1
        key = (score, rn_bonus)
        if best is None or key < best[0]:
            best = (key, d, md)
    log.debug(f"[RUN_DETAIL] run={run_number} start={start} dirs={len(dirs)} "
              f"matched={os.path.basename(best[1]) if best else None} score={best[0][0] if best else None}")
    # Tolerance: the recording must start within 10 min of the run; without a
    # run start time we can only trust an exact run_number match.
    if best is None or (start and best[0][0] > 600) or (not start and best[0][1] != 0):
        return jsonify({"ok": False, "run_number": run_number,
                        "message": "no recorded data for this run"})
    _, run_dir, md = best

    segments = []
    open_macros = {}
    open_manual = None
    starts_order = []   # times of every macro_start, for closing dangling spans
    try:
        with open(os.path.join(run_dir, "actions.jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    a = json.loads(line)
                except Exception:
                    continue
                t = float(a.get("t") or 0)
                typ = str(a.get("type") or "")
                if typ == "macro_start":
                    starts_order.append(t)
                    open_macros.setdefault(str(a.get("macro_name") or "?"), []).append(t)
                elif typ in ("macro_end", "macro_error"):
                    name = str(a.get("macro_name") or "?")
                    lst = open_macros.get(name)
                    st = lst.pop() if lst else None
                    if st is None:
                        st = t
                    seg = {
                        "s": round(st, 2), "e": round(t, 2),
                        "kind": ("fail" if typ == "macro_error" else _classify(name)),
                        "label": name, "ok": typ == "macro_end",
                    }
                    if a.get("error"):
                        seg["err"] = str(a.get("error"))
                    segments.append(seg)
                elif typ == "manual_strength_flow":
                    if str(a.get("phase") or "") == "start":
                        if open_manual is None:
                            open_manual = t
                    else:
                        if open_manual is not None:
                            segments.append({"s": round(open_manual, 2), "e": round(t, 2),
                                             "kind": "manual", "label": "Manual Strength", "ok": True})
                            open_manual = None
                elif typ == "manual_strength":
                    act = a.get("action") if isinstance(a.get("action"), dict) else {}
                    if str(act.get("type") or "") == "manual_strength_flow":
                        if str(act.get("phase") or "") == "start":
                            if open_manual is None:
                                open_manual = t
                        elif open_manual is not None:
                            segments.append({"s": round(open_manual, 2), "e": round(t, 2),
                                             "kind": "manual", "label": "Manual Strength", "ok": True})
                            open_manual = None
    except Exception:
        pass

    # Dangling macros (hit macros run in the background get no explicit end):
    # close them at the next macro start after them, else at the last event.
    last_t = max([s["e"] for s in segments] + starts_order, default=0.0)
    for name, lst in open_macros.items():
        for st in lst:
            nxt = next((t for t in starts_order if t > st), last_t)
            segments.append({"s": round(st, 2), "e": round(max(st + 0.3, nxt), 2),
                             "kind": _classify(name), "label": name, "ok": True})
    if open_manual is not None:
        nxt = next((t for t in starts_order if t > open_manual), last_t)
        segments.append({"s": round(open_manual, 2), "e": round(max(open_manual + 0.3, nxt), 2),
                         "kind": "manual", "label": "Manual Strength", "ok": True})

    segments.sort(key=lambda s: (s["s"], s["e"]))
    duration = float(md.get("duration_secs") or 0)
    return jsonify({"ok": bool(segments), "run_number": run_number,
                    "dir": os.path.basename(run_dir), "duration": duration,
                    "segments": segments})


@app.route("/first_steps", methods=["GET"])
def first_steps_get():
    import config as _cfg
    return jsonify({"ok": True, "completed": bool(getattr(_cfg, "FIRST_STEPS_COMPLETED", False))})


@app.route("/first_steps", methods=["POST"])
def first_steps_post():
    data = request.get_json(force=True, silent=True) or {}
    completed = bool(data.get("completed", True))
    try:
        import config as _cfg
        _cfg.FIRST_STEPS_COMPLETED = completed
        _cfg.save_values({"FIRST_STEPS_COMPLETED": completed})
        return jsonify({"ok": True, "completed": completed})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/first_steps/img/<name>")
def first_steps_img(name):
    import re as _re
    safe = _re.sub(r"[^A-Za-z0-9._-]", "", str(name or ""))
    if not safe:
        return jsonify({"ok": False, "error": "bad name"}), 400
    folder = os.path.join(DATA_DIR, "first_steps")
    for ext in ("", ".png", ".jpg", ".jpeg", ".webp"):
        path = os.path.join(folder, safe if "." in safe else safe + ext)
        if os.path.isfile(path):
            return send_file(path)
        if "." in safe:
            break
    from flask import Response
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='640' height='200'>"
        "<rect width='100%' height='100%' fill='#111118'/>"
        "<rect x='8' y='8' width='624' height='184' fill='none' stroke='#3a3a50' "
        "stroke-dasharray='6 4' rx='8'/>"
        "<text x='50%' y='50%' fill='#7070a0' font-size='14' text-anchor='middle' "
        "font-family='Segoe UI,sans-serif'>Screenshot placeholder — add "
        f"{safe} to data/first_steps/</text></svg>"
    )
    return Response(svg, mimetype="image/svg+xml")


# Region calibrator routesÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
CALIB_REGIONS = {
    "stone":          ("STONE_REGION",           "Stone amount region"),
    "strength":       ("STRENGTH_REGION",         "Strength region"),
    "stone_icon":     ("STONE_ICON_REGION",        "Stone icon region"),
    "auto_str":       ("AUTO_STR_REGION",          "Auto strength icon region"),
    "rock_hp_bar":    ("ROCK_HEALTH_BAR_REGION",   "Rock health bar"),
    "bramble_mode":   ("BRAMBLE_MODE_REGION",      "Bramble fight mode name (OCR)"),
    "tp_button":      ("TELEPORT_BUTTON_REGION",    "Teleport button (UI)"),
    "tp_base":        ("TELEPORT_BASE_REGION",      "Teleport base button (UI)"),
    "tp_area1":       ("TELEPORT_AREA1_REGION",     "Teleport Area 1 button (UI)"),
    "tp_area2":       ("TELEPORT_AREA2_REGION",     "Teleport Area 2 button (UI)"),
    "tp_area3":       ("TELEPORT_AREA3_REGION",     "Teleport Area 3 button (UI)"),
    "tp_area4":       ("TELEPORT_AREA4_REGION",     "Teleport Area 4 button (UI)"),
    "tp_area5":       ("TELEPORT_AREA5_REGION",     "Teleport Area 5 button (UI)"),
    "tp_area6":       ("TELEPORT_AREA6_REGION",     "Teleport Area 6 button (UI)"),
    "tp_area7":       ("TELEPORT_AREA7_REGION",     "Teleport Cosmic/Area 7 button (UI)"),
    "menu_play":      ("MENU_PLAY_REGION",         "Menu Resume - PLAY button"),
    "ms_row1_left":   ("MANUAL_STR_ROW1_LEFT",    "Row 1 - Upgrade (top)"),
    "ms_row1_right":  ("MANUAL_STR_ROW1_RIGHT",   "Row 1 - Upgrade Efficiency (top)"),
    "ms_row2_left":   ("MANUAL_STR_ROW2_LEFT",    "Row 2 - Upgrade"),
    "ms_row2_right":  ("MANUAL_STR_ROW2_RIGHT",   "Row 2 - Upgrade Efficiency"),
    "ms_row3_left":   ("MANUAL_STR_ROW3_LEFT",    "Row 3 - Upgrade"),
    "ms_row3_right":  ("MANUAL_STR_ROW3_RIGHT",   "Row 3 - Upgrade Efficiency"),
    "ms_row4_left":   ("MANUAL_STR_ROW4_LEFT",    "Row 4 - Upgrade"),
    "ms_row4_right":  ("MANUAL_STR_ROW4_RIGHT",   "Row 4 - Upgrade Efficiency"),
    "ms_row5_left":   ("MANUAL_STR_ROW5_LEFT",    "Row 5 - Upgrade (bottom)"),
    "ms_row5_right":  ("MANUAL_STR_ROW5_RIGHT",   "Row 5 - Upgrade Efficiency (bottom)"),
    "ms_close":       ("MANUAL_STR_CLOSE_REGION", "CLOSE button (yellow)"),
    "ms_stone":       ("MANUAL_STR_STONE_REGION", "Stone amount (Strength Menu)"),
    "ms_strength":    ("MANUAL_STR_STRENGTH_REGION", "Strength (Strength Menu)"),
}

# Default values for every region key ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â used by /regions/reset endpoint.
# Values must match the defaults in config.py exactly.
REGION_DEFAULTS = {
    "stone":          [1700, 659,  1919, 721],
    "strength":       [1698, 602,  1919, 655],
    "stone_icon":     [1629, 657,  1704, 727],
    "auto_str":       [76,   1023, 126,  1073],
    "rock_hp_bar":    [610,  55,   1328, 122],
    "bramble_mode":   [182,  270,  701,  331],
    "tp_button":      [827,  807,  1171, 868],
    "tp_base":        [790,  843,  1130, 902],
    "tp_area1":       [790,  138,  1130, 198],
    "tp_area2":       [790,  226,  1130, 286],
    "tp_area3":       [790,  314,  1130, 374],
    "tp_area4":       [790,  403,  1130, 463],
    "tp_area5":       [790,  491,  1130, 551],
    "tp_area6":       [790,  579,  1130, 639],
    "tp_area7":       [790,  755,  1130, 815],
    "menu_play":      [660,  840,  820,  900],
    "ms_row1_left":   [1137, 269,  1466, 339],
    "ms_row1_right":  [1495, 266,  1828, 341],
    "ms_row2_left":   [1137, 426,  1466, 496],
    "ms_row2_right":  [1495, 426,  1828, 496],
    "ms_row3_left":   [1137, 583,  1466, 653],
    "ms_row3_right":  [1495, 583,  1828, 653],
    "ms_row4_left":   [1137, 740,  1466, 810],
    "ms_row4_right":  [1495, 740,  1828, 810],
    "ms_row5_left":   [1137, 897,  1466, 967],
    "ms_row5_right":  [1495, 897,  1828, 967],
    "ms_close":       [1605, 66,   1881, 137],
    "ms_stone":       [145,  72,   370,  139],
    "ms_strength":    [475,  72,   682,  139],
}

@app.route("/screenshot", methods=["GET"])
def screenshot():
    """Return full-screen screenshot as JPEG + actual pixel dimensions."""
    try:
        try:
            from overlay import hide_for_capture
            hide_for_capture(1.0)
            time.sleep(0.15)
        except Exception:
            pass
        import mss, cv2, numpy as np, base64
        with mss.mss() as sct:
            mon = sct.monitors[1]
            raw = sct.grab(mon)
            img = np.array(raw)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf.tobytes()).decode()
        sw, sh = mon["width"], mon["height"]
        log.debug(f"[Calib] Screenshot taken: {sw}x{sh}")
        return jsonify({"ok": True, "img": b64, "w": sw, "h": sh})
    except Exception as e:
        log.warning(f"[Calib] Screenshot failed: {e}")
        return jsonify({"ok": False, "error": str(e)})


@app.route("/regions", methods=["GET"])
def regions_get():
    try:
        import config as _cfg
        result = {}
        for key, (attr, label) in CALIB_REGIONS.items():
            val = getattr(_cfg, attr, None)
            result[key] = {"label": label, "value": list(val) if val else None}
        log.debug(f"[Calib] Regions read: {list(result.keys())}")
        return jsonify({"ok": True, "regions": result, "defaults": REGION_DEFAULTS})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/regions", methods=["POST"])
def regions_post():
    data   = request.get_json(force=True, silent=True) or {}
    key    = data.get("key")
    region = data.get("region")
    if key not in CALIB_REGIONS:
        return jsonify({"ok": False, "error": f"Unknown region key: {key}"})
    if not region or len(region) != 4:
        return jsonify({"ok": False, "error": "region must be [x1,y1,x2,y2]"})
    attr, label = CALIB_REGIONS[key]
    tup = tuple(int(v) for v in region)
    import config as _cfg
    setattr(_cfg, attr, tup)
    try:
        _cfg.save_region(attr, tup)
        log.info(f"[Calib] Region '{key}' ({attr}) saved to config.json ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ {tup}")
    except Exception as e:
        log.warning(f"[Calib] Region save to file failed: {e}")
    # For ms_close: also auto-compute and persist the click center point
    if key == "ms_close":
        region_now = getattr(_cfg, "MANUAL_STR_CLOSE_REGION", tup)
        x1_, y1_, x2_, y2_ = [int(v) for v in region_now]
        center = (int((x1_+x2_)//2), int((y1_+y2_)//2))
        setattr(_cfg, "MANUAL_STR_CLOSE_CENTER", center)
        try:
            _cfg.save_values({"MANUAL_STR_CLOSE_CENTER": list(center)})
            log.info(f"[Calib] ms_close center auto-saved ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ {center}")
        except Exception as e:
            log.warning(f"[Calib] ms_close center save failed: {e}")
    return jsonify({"ok": True})

@app.route("/region_preview", methods=["POST"])
def region_preview():
    data = request.get_json(force=True, silent=True) or {}
    region = data.get("region")
    if not region or len(region) != 4:
        return jsonify({"ok": False, "error": "region must be [x1,y1,x2,y2]"})
    try:
        try:
            from overlay import hide_for_capture
            hide_for_capture(1.0)
            time.sleep(0.15)
        except Exception:
            pass
        import mss, cv2, numpy as np, base64
        x1, y1, x2, y2 = [int(v) for v in region]
        with mss.mss() as sct:
            mon = {"left": x1, "top": y1, "width": max(1, x2-x1), "height": max(1, y2-y1)}
            raw = sct.grab(mon)
            img = np.array(raw)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        b64 = base64.b64encode(buf.tobytes()).decode()
        log.debug(f"[Calib] Region preview: {region}")
        return jsonify({"ok": True, "img": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/ocr_test", methods=["POST"])
def ocr_test():
    data = request.get_json(force=True, silent=True) or {}
    region = data.get("region")
    if not region or len(region) != 4:
        return jsonify({"ok": False, "error": "region must be [x1,y1,x2,y2]"})
    try:
        try:
            from overlay import hide_for_capture
            hide_for_capture(1.0)
            time.sleep(0.15)
        except Exception:
            pass
        from screen import grab_region, _preprocess, parse_scientific, ensure_tesseract
        import pytesseract, cv2, base64, numpy as np
        ensure_tesseract()
        img  = grab_region(tuple(int(v) for v in region))
        proc = _preprocess(img)
        raw  = pytesseract.image_to_string(
            proc, config="--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.,eExXkKmMbBtTqQaAsSpPoOcCnNdDuUvVgGiIrR")
        parsed = parse_scientific(raw)
        _, buf = cv2.imencode(".jpg", proc)
        b64 = base64.b64encode(buf.tobytes()).decode()
        log.info(f"[OCR Test] region={region} raw={raw.strip()!r} parsed={parsed}")
        return jsonify({"ok": True, "raw": raw.strip(), "parsed": parsed, "proc_img": b64})
    except Exception as e:
        log.warning(f"[OCR Test] failed: {e}")
        return jsonify({"ok": False, "error": str(e)})


@app.route("/regions/reset", methods=["POST"])
def regions_reset():
    """Reset one region key (or all keys in a tab group) to hardcoded defaults."""
    data = request.get_json(force=True, silent=True) or {}
    keys = data.get("keys")   # list of region keys to reset
    if not keys or not isinstance(keys, list):
        return jsonify({"ok": False, "error": "keys must be a non-empty list"})
    import config as _cfg
    reset = {}
    for key in keys:
        if key not in REGION_DEFAULTS:
            continue
        default = REGION_DEFAULTS[key]
        attr, _ = CALIB_REGIONS[key]
        tup = tuple(int(v) for v in default)
        setattr(_cfg, attr, tup)
        try:
            _cfg.save_region(attr, tup, already_base=True)
        except Exception as e:
            log.warning(f"[Calib] reset save failed for {key}: {e}")
        reset[key] = default
        # auto-compute close center when resetting ms_close
        if key == "ms_close":
            region_now = getattr(_cfg, "MANUAL_STR_CLOSE_REGION", tup)
            x1_, y1_, x2_, y2_ = [int(v) for v in region_now]
            center = (int((x1_+x2_)//2), int((y1_+y2_)//2))
            setattr(_cfg, "MANUAL_STR_CLOSE_CENTER", center)
            try:
                _cfg.save_values({"MANUAL_STR_CLOSE_CENTER": list(center)})
            except Exception:
                pass
    log.info(f"[Calib] Reset {list(reset.keys())} to defaults")
    return jsonify({"ok": True, "reset": reset})


@app.route("/action", methods=["POST"])
def action():
    data = request.get_json(force=True, silent=True) or {}
    act  = data.get("action", "")
    if act == "start":
        try:
            import bot as _bot_lo
            _missing = _bot_lo.missing_required_loadouts()
            if _missing:
                with _lock:
                    _state["missing_loadouts"] = list(_missing)
                    _state["loadout_block_seq"] = int(_state.get("loadout_block_seq") or 0) + 1
                    _state["waiting_for_start"] = True
                    _state["run_active"] = False
                    _state["status"] = "ERROR"
                    _state["goal"] = "Loadouts not set: " + ", ".join(_missing)
                return jsonify({
                    "ok": False,
                    "error": "Set loadouts first: " + ", ".join(_missing),
                    "missing_loadouts": _missing,
                    "loadout_block_seq": _state.get("loadout_block_seq"),
                }), 400
        except Exception as _lo_e:
            log.debug(f"loadout start gate failed: {_lo_e}")
        try:
            import bot as _bot_gd
            if _bot_gd.missing_game_detection():
                with _lock:
                    _state["game_detect_block_seq"] = int(_state.get("game_detect_block_seq") or 0) + 1
                    _state["waiting_for_start"] = True
                    _state["run_active"] = False
                    _state["status"] = "ERROR"
                    _state["goal"] = "In-Game image detection not set!"
                return jsonify({
                    "ok": False,
                    "error": "In-Game image detection not set! Pick an image in Config (top gear) \u2192 Force Restart.",
                    "game_detect_block_seq": _state.get("game_detect_block_seq"),
                }), 400
        except Exception as _gd_e:
            log.debug(f"game-detect start gate failed: {_gd_e}")
        with _lock:
            _state["waiting_for_start"] = False
            _state["status"] = "STARTING"
            _state["goal"]   = "Initialising..."
            _state["run_active"] = True
            _state["run_start_time"] = time.time()
            _state["run_steps"] = 0
            _state["run_errors"] = 0
            _state["missing_loadouts"] = []
        log.debug("Dashboard: START clicked")
    elif act == "quit":
        import threading, bot as _bot
        threading.Thread(target=_bot.hard_quit, daemon=True).start()
    elif act == "stop":
        with _lock:
            _state["waiting_for_start"] = True
            _state["status"] = "STOPPED"
            _state["goal"]   = "Press Start to begin"
            _state["run_active"] = False
            _state["run_start_time"] = None
        import threading, bot as _bot
        threading.Thread(target=_bot._on_f9, daemon=True, name="dashboard-stop-f9").start()
    elif act == "delete_run":
        run_number = data.get("run_number")
        if run_number is not None:
            mode = str(data.get("mode") or _state.get("bot_mode") or "rebirth").lower()
            try:
                run_number_i = int(run_number)
            except Exception:
                run_number_i = run_number
            if mode == "delve":
                with _lock:
                    _state["delve_run_history"] = [
                        r for r in (_state.get("delve_run_history", []) or [])
                        if r.get("run_number") != run_number_i
                    ]
                    history = list(_state["delve_run_history"])
                    snap = dict(_state)
                _save_delve_history(history)
                _save_persistent_state(snap)
            elif mode == "kraken":
                with _lock:
                    _state["kraken_run_history"] = [
                        r for r in (_state.get("kraken_run_history", []) or [])
                        if r.get("run_number") != run_number_i
                    ]
                    history = list(_state["kraken_run_history"])
                    snap = dict(_state)
                _save_kraken_history(history)
                _save_persistent_state(snap)
            elif mode == "zytos":
                with _lock:
                    _state["zytos_run_history"] = [
                        r for r in (_state.get("zytos_run_history", []) or [])
                        if r.get("run_number") != run_number_i
                    ]
                    history = list(_state["zytos_run_history"])
                    snap = dict(_state)
                _save_zytos_history(history)
                _save_persistent_state(snap)
            else:
                with _lock:
                    _state["run_history"] = [
                        r for r in _state["run_history"]
                        if r.get("run_number") != run_number_i
                    ]
                    recalc = _recalc_stats_from_history(_state["run_history"])
                    _state.update(recalc)
                    snap = dict(_state)
                _save_persistent_state(snap)
                try:
                    import bot as _bot_mod
                    gs = _bot_mod.stats.global_stats
                    gs.total_rebirths = recalc["total_rebirths"]
                    gs.total_errors   = recalc["total_errors"]
                    gs.min_time_secs  = recalc["min_time_secs"] if recalc["min_time_secs"] > 0 else float("inf")
                    gs.max_time_secs  = recalc["max_time_secs"]
                    durations = [r["duration_secs"] for r in snap["run_history"] if r.get("duration_secs",0)>0]
                    gs.total_time_secs = sum(durations)
                    gs.run_history = list(snap["run_history"])
                    _bot_mod.stats.save()
                except Exception as e:
                    log.debug(f"Stats sync after delete failed: {e}")
    elif act == "delete_all_runs":
        mode = str(data.get("mode") or _state.get("bot_mode") or "rebirth").lower()
        if mode == "delve":
            with _lock:
                _state["delve_run_history"] = []
                snap = dict(_state)
            _save_delve_history([])
            _save_persistent_state(snap)
        elif mode == "kraken":
            with _lock:
                _state["kraken_run_history"] = []
                snap = dict(_state)
            _save_kraken_history([])
            _save_persistent_state(snap)
        elif mode == "zytos":
            with _lock:
                _state["zytos_run_history"] = []
                snap = dict(_state)
            _save_zytos_history([])
            _save_persistent_state(snap)
        else:
            with _lock:
                _state["run_history"] = []
                recalc = _recalc_stats_from_history([])
                _state.update(recalc)
                snap = dict(_state)
            _save_persistent_state(snap)
            try:
                import bot as _bot_mod
                gs = _bot_mod.stats.global_stats
                gs.total_rebirths = 0; gs.total_errors = 0
                gs.min_time_secs = float("inf"); gs.max_time_secs = 0.0
                gs.total_time_secs = 0.0; gs.run_history = []
                _bot_mod.stats.save()
            except Exception as e:
                log.debug(f"Stats sync after delete_all failed: {e}")
    elif act == "set_run_mode":
        mode = str(data.get("mode", "a1s1"))
        if mode in {"a6s1", "a6s2", "a6s3", "a6s4"}:
            mode = "a5meteor"
        allowed_modes = {"a5meteor", *{f"a{a}s{s}" for a in range(1, 6) for s in range(1, 5)}}
        if mode not in allowed_modes:
            mode = "a1s1"
        with _lock:
            _state["run_mode"] = mode
            snap = dict(_state)
        try:
            import bot as _bot; _bot._RUN_MODE = mode
        except Exception as e:
            log.debug(f"set_run_mode bot patch failed: {e}")
        _save_persistent_state(snap)

    elif act == "set_app_tab":
        tab = str(data.get("tab") or "run").strip().lower()
        if tab not in {"run", "recorder", "builder"}:
            tab = "run"
        with _lock:
            _state["active_app_tab"] = tab

    elif act == "set_farm_meteor_area":
        area = str(data.get("area", "a6")).strip().lower()
        if area not in {"a6", "a7", "a8"}:
            area = "a6"
        with _lock:
            _state["farm_meteor_area"] = area
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "FARM_METEOR_AREA", area)
            _cfg_mod.save_values({"FARM_METEOR_AREA": area})
        except Exception as e:
            log.debug(f"set_farm_meteor_area config save failed: {e}")
        _save_persistent_state(snap)

    elif act == "set_crater_overlay":
        val = bool(data.get("value", True))
        with _lock:
            _state["crater_overlay"] = val
            snap = dict(_state)
        _save_persistent_state(snap)

    elif act == "set_bot_mode":
        mode = str(data.get("mode", "rebirth")).strip().lower()
        if mode not in {"rebirth", "delve", "kraken", "zytos", "crater", "farm_meteor"}:
            mode = "rebirth"
        with _lock:
            _state["bot_mode"] = mode
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "BOT_MODE", mode)
            _cfg_mod.save_values({"BOT_MODE": mode})
        except Exception as e:
            log.debug(f"set_bot_mode config save failed: {e}")
        _save_persistent_state(snap)

    elif act == "set_menu_resume":
        val = bool(data.get("value", False))
        with _lock:
            _state["menu_resume"] = val
            _state["force_restart"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "FORCE_RESTART_ON_FAILURE", val)
            _cfg_mod.save_values({"FORCE_RESTART_ON_FAILURE": val})
        except Exception as e:
            log.debug(f"set_menu_resume bundled config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: menu_resume bundled with force_restart set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Force Restart: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_auto_strength":
        val = bool(data.get("value", False))
        with _lock:
            _state["auto_strength"] = val
            snap = dict(_state)
        _save_persistent_state(snap)
        log.debug(f"Dashboard: auto_strength set to {val}")
        try:
            from overlay import set_overlay as _set_overlay
            if val:
                _set_overlay(show_auto_str=True)
            else:
                _set_overlay(auto_str=None, show_auto_str=False)
        except Exception as e:
            log.debug(f"Dashboard: overlay auto_strength sync failed: {e}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Auto Strength: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_boss_fight_a1":
        val = bool(data.get("value", False))
        with _lock:
            _state["boss_fight_a1"] = val
            snap = dict(_state)
        _save_persistent_state(snap)
        log.debug(f"Dashboard: boss_fight_a1 set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Boss Fight (A1): {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_daily_quests":
        val = bool(data.get("value", False))
        with _lock:
            _state["daily_quests"] = val
            snap = dict(_state)
        _save_persistent_state(snap)
        log.debug(f"Dashboard: daily_quests set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Daily Quests: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_force_restart":
        val = bool(data.get("value", False))
        with _lock:
            _state["force_restart"] = val
            _state["menu_resume"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "FORCE_RESTART_ON_FAILURE", val)
            _cfg_mod.save_values({"FORCE_RESTART_ON_FAILURE": val})
        except Exception as e:
            log.debug(f"set_force_restart config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: force_restart set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Force Restart: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_pause_on_lag":
        val = bool(data.get("value", False))
        with _lock:
            _state["pause_on_lag"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "PAUSE_ON_LAG", val)
            _cfg_mod.save_values({"PAUSE_ON_LAG": val})
        except Exception as e:
            log.debug(f"set_pause_on_lag config save failed: {e}")
        _save_persistent_state(snap)
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Pause on Lag: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_rebirth_activate_drills":
        val = bool(data.get("value", True))
        with _lock:
            _state["rebirth_activate_drills"] = val
            _state["activate_drills"] = val  # keep legacy key in sync for rebirth
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "ACTIVATE_DRILLS", val)
            _cfg_mod.save_values({"ACTIVATE_DRILLS": val})
        except Exception as e:
            log.debug(f"set_rebirth_activate_drills config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: rebirth_activate_drills set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Rebirth Activate Drills: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_rebirth_drill_on_rock":
        val = bool(data.get("value", True))
        with _lock:
            _state["rebirth_drill_on_rock"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "USE_DRILL_ON_ROCK", val)
            _cfg_mod.save_values({"USE_DRILL_ON_ROCK": val})
        except Exception as e:
            log.debug(f"set_rebirth_drill_on_rock config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: rebirth_drill_on_rock set to {val}")
    elif act == "set_rebirth_drill_on_baserock":
        val = bool(data.get("value", True))
        with _lock:
            _state["rebirth_drill_on_baserock"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "USE_DRILL_ON_BASEROCK", val)
            _cfg_mod.save_values({"USE_DRILL_ON_BASEROCK": val})
        except Exception as e:
            log.debug(f"set_rebirth_drill_on_baserock config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: rebirth_drill_on_baserock set to {val}")
    elif act == "set_rebirth_drill_on_a5_meteor":
        val = bool(data.get("value", False))
        with _lock:
            _state["rebirth_drill_on_a5_meteor"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "USE_DRILL_ON_A5_METEOR", val)
            _cfg_mod.save_values({"USE_DRILL_ON_A5_METEOR": val})
        except Exception as e:
            log.debug(f"set_rebirth_drill_on_a5_meteor config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: rebirth_drill_on_a5_meteor set to {val}")
    elif act == "set_delve_activate_drills":
        val = bool(data.get("value", True))
        with _lock:
            _state["delve_activate_drills"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "DELVE_ACTIVATE_DRILLS", val)
            _cfg_mod.save_values({"DELVE_ACTIVATE_DRILLS": val})
        except Exception as e:
            log.debug(f"set_delve_activate_drills config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: delve_activate_drills set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Delve Activate Drills: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_kraken_activate_drills":
        val = bool(data.get("value", True))
        with _lock:
            _state["kraken_activate_drills"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "KRAKEN_ACTIVATE_DRILLS", val)
            _cfg_mod.save_values({"KRAKEN_ACTIVATE_DRILLS": val})
        except Exception as e:
            log.debug(f"set_kraken_activate_drills config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: kraken_activate_drills set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Kraken Activate Drills: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_kraken_movement_mode":
        mode = str(data.get("mode", "linear")).strip().lower()
        if mode not in {"linear", "square"}:
            mode = "linear"
        with _lock:
            _state["kraken_movement_mode"] = mode
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "KRAKEN_MOVEMENT_MODE", mode)
            _cfg_mod.save_values({"KRAKEN_MOVEMENT_MODE": mode})
        except Exception as e:
            log.debug(f"set_kraken_movement_mode config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: kraken_movement_mode set to {mode}")
    elif act == "set_zytos_activate_drills":
        val = bool(data.get("value", True))
        with _lock:
            _state["zytos_activate_drills"] = val
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "ZYTOS_ACTIVATE_DRILLS", val)
            _cfg_mod.save_values({"ZYTOS_ACTIVATE_DRILLS": val})
        except Exception as e:
            log.debug(f"set_zytos_activate_drills config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: zytos_activate_drills set to {val}")
        try:
            from logger import cprint as _cp
            _cp(f"[Config] Zytos Activate Drills: {'ON' if val else 'OFF'}", "ok" if val else "warn")
        except Exception:
            pass
    elif act == "set_zytos_movement_mode":
        mode = str(data.get("mode", "linear")).strip().lower()
        if mode not in {"linear", "square"}:
            mode = "linear"
        with _lock:
            _state["zytos_movement_mode"] = mode
            snap = dict(_state)
        try:
            import config as _cfg_mod
            setattr(_cfg_mod, "ZYTOS_MOVEMENT_MODE", mode)
            _cfg_mod.save_values({"ZYTOS_MOVEMENT_MODE": mode})
        except Exception as e:
            log.debug(f"set_zytos_movement_mode config save failed: {e}")
        _save_persistent_state(snap)
        log.debug(f"Dashboard: zytos_movement_mode set to {mode}")
    elif act == "crater_reset_stats":
        try:
            from crater.loop import reset_crater_stats
            reset_crater_stats()
            log.info("Dashboard: crater stats reset")
            return jsonify({"ok": True})
        except Exception as e:
            log.warning(f"Dashboard: crater reset failed: {e}")
            return jsonify({"ok": False, "error": str(e)})
    return jsonify({"ok": True})


@app.route("/icon")
def icon_route():
    import sys as _sys
    # When running as a frozen EXE, icon.png is bundled inside via --add-data
    if getattr(_sys, "frozen", False):
        icon_path = os.path.join(_sys._MEIPASS, "icon.png")
    else:
        icon_path = os.path.join(BOT_DIR, "icon.png")
    if os.path.exists(icon_path):
        return send_file(icon_path, mimetype="image/png")
    import base64
    from flask import Response
    pixel = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    return Response(pixel, mimetype="image/png")


# ============================================================
# CUSTOM MODES API (kept for v1.8 Mode Builder)
# Builder tab is hidden in this build. Routes stay so 1.8 can enable it.
# NOTE: the Blockly editor bundle and its serving routes were removed
# from this build (unused third-party code); re-add code/blockly/ and
# the /blockly/* routes to bring the visual editor back.
# ============================================================
_MODES_DIR = os.path.join(BOT_DIR, "modes")
_BUILDER_TAB_ENABLED = False


def _ensure_modes_dir():
    os.makedirs(_MODES_DIR, exist_ok=True)




@app.route("/modes/list")
def modes_list():
    _ensure_modes_dir()
    modes = []
    try:
        for entry in sorted(os.scandir(_MODES_DIR), key=lambda e: e.name.lower()):
            if not entry.is_dir():
                continue
            mode_file = os.path.join(entry.path, "mode.json")
            if not os.path.isfile(mode_file):
                continue
            with open(mode_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            modes.append({
                "name": data.get("name", entry.name),
                "description": data.get("description", ""),
            })
    except Exception as e:
        log.error(f"modes_list error: {e}")
    return jsonify({"modes": modes})


@app.route("/modes/create", methods=["POST"])
def modes_create():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name required"})
    _ensure_modes_dir()
    mode_dir = os.path.join(_MODES_DIR, name)
    if os.path.exists(mode_dir):
        return jsonify({"ok": False, "error": "Mode already exists"})
    os.makedirs(mode_dir, exist_ok=True)
    mode_data = {
        "name": name,
        "description": body.get("description", ""),
        "version": "2.0",
        "flow_graph": {
            "nodes": [{"id": "start", "type": "start", "label": "Start", "x": 100, "y": 100}],
            "edges": [],
            "startNodeId": "start"
        },
        "procedures": {},
        "toggles": [],
        "dashboard": {}
    }
    with open(os.path.join(mode_dir, "mode.json"), "w", encoding="utf-8") as f:
        json.dump(mode_data, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True})


@app.route("/modes/load")
def modes_load():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name required"})
    mode_dir = os.path.join(_MODES_DIR, name)
    mode_file = os.path.join(mode_dir, "mode.json")
    if not os.path.isfile(mode_file):
        return jsonify({"ok": False, "error": "Mode not found"})
    try:
        with open(mode_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, "mode": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/modes/save", methods=["POST"])
def modes_save():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name required"})
    mode_dir = os.path.join(_MODES_DIR, name)
    mode_file = os.path.join(mode_dir, "mode.json")
    if not os.path.isfile(mode_file):
        return jsonify({"ok": False, "error": "Mode not found"})
    try:
        with open(mode_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if "flow_graph" in body:
            existing["flow_graph"] = body["flow_graph"]
        if "variables" in body:
            existing["variables"] = body["variables"]
        if "config" in body:
            existing["config"] = body["config"]
        if "procedure_xml" in body:
            if "procedures" not in existing:
                existing["procedures"] = {}
            existing["procedures"][body.get("proc_id", "default")] = {
                "name": body.get("proc_name", ""),
                "xml": body.get("procedure_xml", ""),
                "code": body.get("procedure_code", ""),
            }
        with open(mode_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/modes/save_procedure", methods=["POST"])
def modes_save_procedure():
    try:
        body = request.get_json(silent=True) or {}
        mode_name = body.get("mode_name", "")
        proc_id = body.get("proc_id", "")
        proc_name = body.get("proc_name", "")
        xml = body.get("xml", "")
        code = body.get("code", "")
        if not mode_name or not proc_id:
            return jsonify({"ok": False, "error": "Missing mode_name or proc_id"})
        mode_file = os.path.join(_MODES_DIR, mode_name, "mode.json")
        if not os.path.isfile(mode_file):
            return jsonify({"ok": False, "error": "Mode not found"})
        with open(mode_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "procedures" not in data:
            data["procedures"] = {}
        data["procedures"][proc_id] = {
            "name": proc_name,
            "xml": xml,
            "code": code,
        }
        with open(mode_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"ok": True})
    except Exception as e:
        log.error(f"modes_save_procedure error: {e}")
        return jsonify({"ok": False, "error": str(e)})


@app.route("/modes/run", methods=["POST"])
def modes_run():
    """Start running a custom mode (Mode Builder / v1.8)."""
    import mode_runner
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "")
    mode_dir = os.path.join(_MODES_DIR, name)
    mode_file = os.path.join(mode_dir, "mode.json")

    if not os.path.isfile(mode_file):
        return jsonify({"ok": False, "error": f"Mode '{name}' not found"})

    with open(mode_file, "r", encoding="utf-8") as f:
        mode_data = json.load(f)

    flow_graph = mode_data.get("flow_graph", {})
    procedures = mode_data.get("procedures", {})

    for node in flow_graph.get("nodes", []):
        if node.get("type") == "procedure":
            nid = node.get("id", "")
            if nid in procedures:
                if "generated_code" in node:
                    procedures[nid]["generated_code"] = node["generated_code"]
            else:
                procedures[nid] = {
                    "name": node.get("label", nid),
                    "generated_code": node.get("generated_code", ""),
                    "event": "on_start",
                    "interval": 100,
                }

    ok = mode_runner.start_mode(mode_data)
    return jsonify({"ok": ok, "mode": name})


@app.route("/modes/stop", methods=["POST"])
def modes_stop():
    """Stop the currently running custom mode."""
    import mode_runner
    mode_runner.stop_mode()
    return jsonify({"ok": True})


@app.route("/modes/status", methods=["GET"])
def modes_status():
    """Check if a custom mode is running."""
    import mode_runner
    return jsonify({
        "running": mode_runner.is_running(),
        "mode": mode_runner.get_active_mode(),
    })


@app.route("/modes/delete", methods=["POST"])
def modes_delete():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name required"})
    mode_dir = os.path.join(_MODES_DIR, name)
    if not os.path.isdir(mode_dir):
        return jsonify({"ok": False, "error": "Mode not found"})
    import shutil as _shutil
    _shutil.rmtree(mode_dir, ignore_errors=True)
    return jsonify({"ok": True})


def _minimize_console():
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 6)
    except Exception as e:
        log.debug(f"Console minimize failed: {e}")

def start_dashboard():
    """Start Flask + open dashboard UI.  NON-BLOCKING ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â returns immediately.

    Thread layout (both frozen EXE and dev):
      main thread  ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ tkinter overlay mainloop  (Windows: tkinter needs main thread)
      thread       ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ Flask server
      thread       ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ pywebview embedded browser window  (background thread ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â safe)
      thread       ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ bot logic

    pywebview runs on a background thread in ALL cases so the main thread stays
    free for tkinter.  Closing the pywebview window does NOT kill the process.
    """
    _minimize_console()
    renamed_images = _prefix_unversioned_macro_images()
    if renamed_images:
        log.info(f"[DASHBOARD] renamed {renamed_images} macro image(s) with current resolution prefix")

    try:
        from macro_engine.app import attach_macro_engine
        attach_macro_engine(app)
        log.info("[DASHBOARD] Macro Engine attached at /me")
    except Exception as e:
        log.warning(f"[DASHBOARD] Macro Engine attach failed: {e}")

    # ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Flask on background thread (always) ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
    def _run_flask():
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        app.run(host="127.0.0.1", port=7373, debug=False, use_reloader=False, threaded=True)
    flask_thread = threading.Thread(target=_run_flask, daemon=True, name="flask")
    flask_thread.start()

    # Brief pause so Flask is ready before anything tries to load the page
    time.sleep(0.8)

    import sys as _sys
    # ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ pywebview on background thread (both dev AND frozen EXE) ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
    # IMPORTANT: pywebview must NOT run on the main thread when tkinter overlay
    # is also in use.  In frozen EXE, the WinForms pump inside webview.start()
    # previously blocked the main thread ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ tkinter overlay never ran.
    # Fix: always spin pywebview onto its own daemon thread.  Main thread stays
    # free for tkinter overlay mainloop (run_overlay_mainloop in bot.py).
    # When the pywebview window is closed we do NOT os._exit() ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â instead we let
    # the bot and tkinter keep running.  User can still use the system browser
    # at http://127.0.0.1:7373 after closing the embedded window.
    # ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Launch dashboard window ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
    # pywebview's WinForms/edgechromium backend MUST run on the main thread of
    # its process (Windows COM/STA requirement).  Our main thread belongs to
    # tkinter overlay, so we spawn a SEPARATE PROCESS for the webview window.
    #
    # In frozen EXE:  re-launch self with --webview flag ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ that process runs
    #                 webview on its main thread and exits when window closes.
    # In dev mode:    spawn python -c "import webview; ..." subprocess.
    # Fallback:       system browser if anything fails.
    def _launch_webview_process():
        """Spawn webview as a separate process. When it exits (window closed),
        kill the entire bot ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â overlay, Flask, everything."""
        import subprocess, sys as _sys2
        is_frozen = getattr(_sys, "frozen", False)
        proc = None
        try:
            if is_frozen:
                exe = _sys2.executable
                log.debug(f"[DASHBOARD] Spawning webview process: {exe} --webview")
                proc = subprocess.Popen(
                    [exe, "--webview"],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
                )
            else:
                script = (
                    "import webview;"
                    "webview.create_window('MT2 Rebirth Bot','http://127.0.0.1:7373',"
                    "width=1100,height=760,resizable=True,min_size=(900,600));"
                    "webview.start()"
                )
                log.debug("[DASHBOARD] Spawning webview subprocess (dev mode)")
                proc = subprocess.Popen(
                    [_sys2.executable, "-c", script],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
                )
        except Exception as _pe:
            log.error(f"[DASHBOARD] webview process launch failed: {_pe}")
            import webbrowser
            webbrowser.open("http://127.0.0.1:7373")
            return  # no process to monitor ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â don't kill on browser close

        # Monitor: when the webview window is closed, shut down everything.
        if proc is not None:
            proc.wait()   # blocks until webview process exits
            if proc.returncode != 0:
                # webview subprocess crashed/failed to import - pywebview not installed.
                # Fall back to browser and keep the bot running.
                log.warning("[DASHBOARD] Webview subprocess exited with error (pywebview not installed?) - opening browser fallback")
                import webbrowser
                webbrowser.open("http://127.0.0.1:7373")
                return
            log.info("[DASHBOARD] Webview window closed - shutting down bot")
            try:
                import bot as _bot
                _bot.hard_quit()   # stops macros, saves stats, os._exit(0)
            except Exception:
                import os
                os._exit(0)

    threading.Thread(target=_launch_webview_process, daemon=True, name="webview-monitor").start()
    log.debug("[DASHBOARD] webview launcher+monitor thread started")


# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
# EMBEDDED DASHBOARD HTML
# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â

_DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MT2 Bot</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<style>
  :root {
    --bg:      #0e0e12;
    --panel:   #16161c;
    --border:  #2a2a35;
    --accent:  #7c6af7;
    --accent2: #f7a06a;
    --green:   #44cc77;
    --red:     #cc4455;
    --yellow:  #f0c040;
    --text:    #e0e0e8;
    --muted:   #7070a0;
    --topbar:  #111118;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; overflow: hidden; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }
  /* ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Dark scrollbars everywhere ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ */
  * { scrollbar-width: thin; scrollbar-color: #3a3a50 var(--bg); }
  *::-webkit-scrollbar { width: 6px; height: 6px; }
  *::-webkit-scrollbar-track { background: var(--bg); }
  *::-webkit-scrollbar-thumb { background: #3a3a50; border-radius: 3px; }
  *::-webkit-scrollbar-thumb:hover { background: #5a5a78; }


  /* â”€â”€ Download Center popup (same style as launcher) â”€â”€ */
  .dl-popup-wrap { position: relative; }

  /* TOP BAR */
  #topbar { position: fixed; top: 0; left: 0; right: 0; z-index: 400; background: var(--topbar); border-bottom: 1px solid var(--border); display: flex; align-items: center; padding: 0 16px; height: 52px; gap: 0; }
  .brand-wrap { display: flex; align-items: center; flex-shrink: 0; padding-right: 16px; }
  .brand-text { font-size: 17px; font-weight: 800; letter-spacing: .4px; line-height: 1; white-space: nowrap; }
  .brand-mt2 { color: #ff8c00; text-shadow: 0 0 8px rgba(255,140,0,.7), 0 0 20px rgba(255,140,0,.35); }
  .brand-rebirth { color: #fff; text-shadow: 0 0 8px rgba(255,255,255,.55), 0 0 20px rgba(255,255,255,.2); }
  .topbar-sep { width: 1px; height: 28px; background: var(--border); flex-shrink: 0; margin: 0 12px; }
  /* Left cluster */
  .topbar-left { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  /* Run mode cluster */
  .topbar-runmode { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
  /* Spacer */
  .topbar-spacer { flex: 1 1 0; min-width: 0; }
  /* Right cluster */
  .topbar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  .topbar-field { display: flex; align-items: center; gap: 7px; }
  .topbar-field-label { font-size: 11px; letter-spacing: .4px; color: var(--muted); text-transform: uppercase; white-space: nowrap; }
  .icon-btn { width: 38px; height: 38px; border-radius: 8px; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; transition: opacity .15s, transform .08s, background .15s; }
  .icon-btn:hover { opacity: .82; }
  .icon-btn:active { transform: scale(.92); }
  .icon-btn svg { width: 18px; height: 18px; }
  #btn-config { background: #252530; border: 1px solid var(--border); color: var(--muted); }
  #btn-config:hover { background: #2e2e3e; border-color: var(--accent); color: var(--text); }
  #btn-config.active { background: rgba(124,106,247,.18); border-color: var(--accent); color: var(--accent); }
  #btn-calib { background: #252530; border: 1px solid var(--border); color: var(--muted); }
  #btn-calib:hover { background: #2e2e3e; border-color: var(--yellow); color: var(--text); }
  #btn-calib.active { background: rgba(240,192,64,.12); border-color: var(--yellow); color: var(--yellow); }
  #btn-start-stop { height: 38px; padding: 0 18px; border-radius: 8px; border: none; font-size: 13px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: opacity .15s, transform .08s, background .15s; color: #fff; }
  #btn-start-stop:hover { opacity: .85; }
  #btn-start-stop:active { transform: scale(.95); }
  #run-mode-select, #bot-mode-select, #farm-meteor-area-select { height: 34px; padding: 0 10px; border-radius: 8px; border: 1px solid var(--border); background: #1c1c26; color: var(--text); font-size: 13px; font-weight: 500; cursor: pointer; outline: none; transition: border-color .15s; }
  #run-mode-select:hover, #run-mode-select:focus, #bot-mode-select:hover, #bot-mode-select:focus, #farm-meteor-area-select:hover, #farm-meteor-area-select:focus { border-color: var(--accent); }
  #run-mode-select option:disabled, #bot-mode-select option:disabled, #farm-meteor-area-select option:disabled { color: #4a4a58; background: #14141c; }
  #run-mode-select option.run-mode-dummy { color: #3e3e4a; background: #121218; font-style: italic; }
  #bot-mode-select { min-width: 112px; }

  /* LAYOUT */
  #layout { position: fixed; top: 98px; left: 0; right: 0; bottom: 0; display: flex; overflow: hidden; min-width: 0; }
  #main { flex: 1; min-width: 0; padding: 22px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }

  /* LEFT SIDEBAR */
  #left-sidebar {
    width: 200px; min-width: 200px; max-width: 200px;
    background: var(--panel); border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    transition: width .25s cubic-bezier(.4,0,.2,1), min-width .25s cubic-bezier(.4,0,.2,1), padding .25s cubic-bezier(.4,0,.2,1);
    overflow: hidden; flex-shrink: 0;
  }
  #left-sidebar.collapsed {
    width: 44px; min-width: 44px;
  }
  #left-sidebar.collapsed .sb-label,
  #left-sidebar.collapsed .sb-section-sep,
  #left-sidebar.collapsed .sb-section-label { display: none; }
  #left-sidebar.collapsed .sb-item { justify-content: center; padding: 9px 0; }
  #left-sidebar.collapsed .sb-item svg { margin: 0; }
  #left-sidebar.collapsed #sb-toggle-btn { justify-content: center; }
  #left-sidebar.collapsed #sb-toggle-icon { transform: rotate(180deg); }
  .sb-body { flex: 1; overflow-y: auto; padding: 10px 0; display: flex; flex-direction: column; gap: 2px; }
  .sb-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 16px; font-size: 13px; font-weight: 500;
    color: var(--text); cursor: pointer; border: none;
    background: transparent; width: 100%; text-align: left;
    border-radius: 0; transition: background .12s, color .12s;
    white-space: nowrap; overflow: hidden;
  }
  .sb-item:hover { background: rgba(124,106,247,.10); color: var(--accent); }
  .sb-item:active { background: rgba(124,106,247,.18); }
  .sb-item.disabled { opacity: .45; cursor: not-allowed; }
  .sb-item.disabled:hover { background: transparent; color: var(--text); }
  .sb-item svg { width: 16px; height: 16px; flex-shrink: 0; }
  .sb-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sb-section-sep { display: none !important; border: none; }
  .sb-section-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); padding: 4px 16px 2px; white-space: nowrap; overflow: hidden; }
  #sb-footer { border-top: 1px solid var(--border); padding: 6px 0; }
  #sb-toggle-btn {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 16px; font-size: 12px; color: var(--muted);
    cursor: pointer; border: none; background: transparent;
    width: 100%; white-space: nowrap; overflow: hidden;
    transition: color .12s;
  }
  #sb-toggle-btn:hover { color: var(--text); }
  #sb-toggle-icon { width: 14px; height: 14px; flex-shrink: 0; transition: transform .25s cubic-bezier(.4,0,.2,1); }

  /* BAUBLES */
  .sec-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: -8px; }
  .baubles { display: flex; gap: 10px; flex-wrap: wrap; }
  .bauble { flex: 1; min-width: 120px; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px; }
  .bauble .b-label { font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: var(--muted); }
  .bauble .b-val { font-size: 24px; font-weight: 700; color: var(--text); }
  .bauble .b-val.accent { color: var(--accent); }
  .bauble .b-val.green  { color: var(--green); }
  .bauble .b-val.yellow { color: var(--yellow); }
  .bauble .b-val.red    { color: var(--red); }
  .bauble .b-val.muted  { color: var(--muted);
  }
  .bauble.rebirth-bauble { position: relative; }
  .rebirth-val-row { display: inline-flex; align-items: center; gap: 6px; }
  .rebirth-mode-icon { display: none; }
  body.mode-rebirth .rebirth-mode-icon { display: inline; }
  .bauble.status-bauble .b-val { font-size: 15px; }

  .mode-settings {
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 10px;
  }
  .mode-settings-head {
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px; flex-wrap: wrap;
  }
  .mode-settings-head .sec-label { margin: 0; }
  .mode-settings-cats { display: flex; flex-wrap: wrap; gap: 6px; }
  .mode-settings-cats .cfg-tab-btn { padding: 5px 12px; }
  .mode-settings-body { display: flex; flex-direction: column; gap: 10px; }
  .mode-settings-body .cfg-tab-panel { display: none; }
  .mode-settings-body .cfg-tab-panel.active { display: flex; flex-direction: column; gap: 10px; }
  .mode-settings-foot {
    display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
  }
  .mode-settings-foot .btn-primary {
    height: 32px; padding: 0 14px; border-radius: 8px; border: 1px solid rgba(124,106,247,.55);
    background: rgba(124,106,247,.18); color: #fff; font-size: 12px; font-weight: 700; cursor: pointer;
  }
  .mode-settings-status { font-size: 12px; color: var(--muted); min-height: 16px; }
  .mode-settings-sep { border: none; border-top: 1px solid var(--border); margin: 4px 0 6px; }

  /* CHART */
  #chart-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }
  .filter-btn { padding:5px 11px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s; }
  .filter-btn.active,.filter-btn:hover { background:var(--accent);color:#fff;border-color:var(--accent); }
  .card-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--muted); margin-bottom: 14px; display:flex; align-items:center; justify-content:space-between; gap:10px; }
  #chart-wrap { height: 220px; }
  .chart-sort { position: relative; flex-shrink:0; }
  .rdl { margin-top:10px; max-height:168px; overflow-y:auto; display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:2px 18px; }
  .rdl-row { display:flex; align-items:center; gap:8px; font-size:11px; color:#cfcce8; padding:3px 2px; }
  .rdl-dot { width:8px; height:8px; border-radius:50%; flex:0 0 auto; }
  .rdl-name { flex:1 1 auto; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .rdl-t { color:#7a7aa0; font-weight:500; white-space:nowrap; }
  .rdl-d { color:#a0a0c0; font-weight:600; white-space:nowrap; min-width:44px; text-align:right; }
  .rdl-chip { display:inline-flex; align-items:center; gap:6px; font-size:10px; font-weight:700; color:#a0a0c0; text-transform:uppercase; letter-spacing:.6px; margin-right:14px; }
  .rdl-chip span { width:9px; height:9px; border-radius:3px; }
  .chart-sort-btn {
    width:32px; height:32px; padding:0; border-radius:8px;
    border:1px solid var(--border); background:transparent; color:var(--muted);
    display:inline-flex; align-items:center; justify-content:center; cursor:pointer;
  }
  .chart-sort-btn svg { width:16px; height:16px; display:block; }
  .chart-sort-btn:hover, .chart-sort.open .chart-sort-btn { background:var(--accent); color:#fff; border-color:var(--accent); }
  .chart-sort-menu { display:none; position:absolute; left:0; top:calc(100% + 8px); width:248px; max-width:calc(100vw - 32px); background:#16161e; border:1px solid var(--border); border-radius:10px; padding:8px; z-index:50; box-shadow:0 14px 36px rgba(0,0,0,.55); }
  .chart-sort.open .chart-sort-menu { display:block; }
  .chart-sort-menu .sort-head { font-size:10px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; color:var(--muted); padding:8px 10px 4px; }
  .chart-sort-menu .sort-head:first-child { padding-top:2px; }
  .chart-sort-menu button { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; width:100%; text-align:left; padding:8px 10px; border:0; background:transparent; color:var(--text); font-size:12px; font-weight:600; cursor:pointer; border-radius:7px; line-height:1.25; }
  .chart-sort-menu button .lbl { display:flex; flex-direction:column; gap:2px; }
  .chart-sort-menu button .hint { font-size:10px; color:var(--muted); font-weight:500; }
  .chart-sort-menu button:hover { background:rgba(124,106,247,.14); }
  .chart-sort-menu button.active { background:rgba(124,106,247,.22); color:#fff; }
  .chart-sort-menu button.active .hint { color:#c8c4ea; }
  .chart-sort-menu .dot { width:8px; height:8px; border-radius:50%; margin-top:4px; flex-shrink:0; background:transparent; }
  .chart-sort-menu button.active .dot { background:var(--accent); }
  .btn-danger-cfg { border-color:rgba(204,68,85,.45) !important; color:#e07080 !important; }
  .btn-danger-cfg:hover { border-color:#e07080 !important; color:#fff !important; background:rgba(204,68,85,.2) !important; }
  #rebirth-main { display: flex; flex-direction: column; gap: 20px; }
  #delve-main { display: none; }
  .boss-only { display: none !important; }
  .delve-only { display: none !important; }
  .kraken-only { display: none !important; }
  .zytos-only { display: none !important; }
  body.mode-delve .rebirth-only { display: none !important; }
  body.mode-delve .boss-only { display: flex !important; }
  body.mode-delve .delve-only { display: flex !important; }
  /* separator removed */
  /* separator removed */
  body.mode-delve #rebirth-main { display: flex !important; }
  body.mode-delve #delve-main { display: none !important; }
  body.mode-kraken .rebirth-only { display: none !important; }
  /* kraken mode: kraken-only items visible (Activate Drills), boss-only separator shown */
  body.mode-kraken .boss-only { display: flex !important; }
  body.mode-kraken .kraken-only { display: flex !important; }
  /* separator removed */
  /* separator removed */
  body.mode-kraken #rebirth-main { display: flex !important; }
  body.mode-kraken #delve-main { display: none !important; }
  body.mode-zytos .rebirth-only { display: none !important; }
  /* zytos mode: zytos-only items visible (Activate Drills), boss-only separator shown */
  body.mode-zytos .boss-only { display: flex !important; }
  body.mode-zytos .zytos-only { display: flex !important; }
  /* separator removed */
  /* separator removed */
  body.mode-zytos #rebirth-main { display: flex !important; }
  body.mode-zytos #delve-main { display: none !important; }

  /* Meteor mode — no shared rebirth graph */
  body.mode-farm-meteor .rebirth-only { display: none !important; }
  body.mode-farm-meteor #rebirth-main { display: none !important; }
  body.mode-farm-meteor #delve-main { display: none !important; }
  body.mode-farm-meteor #crater-main { display: none !important; }
  body.mode-farm-meteor #meteor-main { display: flex !important; flex-direction: column; align-items: center; justify-content: center; min-height: 280px; padding: 40px 20px; }
  #meteor-main { display: none; }
  #meteor-main .mode-empty-msg { color: var(--muted); font-size: 15px; text-align: center; line-height: 1.6; }

  /* Crater mode */
  .crater-only { display: none !important; }
  body.mode-crater .rebirth-only { display: none !important; }
  body.mode-crater .crater-only { display: flex !important; }
  /* separator removed */
  body.mode-crater #rebirth-main { display: none !important; }
  body.mode-crater #delve-main { display: none !important; }
  body.mode-crater #crater-main { display: flex !important; flex-direction: column; gap: 20px; padding: 20px 0; }
  #crater-main { display: none; }
  #crater-main .crater-empty-msg { color: var(--muted); font-size: 14px; text-align: center; line-height: 1.6; }

  /* SLIDE-IN PANEL */
  .side-panel {
    position: fixed; top: 52px; right: 0; bottom: 0;
    background: #13131a; border-left: 1px solid var(--border);
    z-index: 300; display: flex; flex-direction: column;
    transform: translateX(110%);
    transition: transform .25s cubic-bezier(.4,0,.2,1);
    box-shadow: -4px 0 32px rgba(0,0,0,.5);
  }
  .side-panel.open { transform: translateX(0); }
  .panel-header { display: flex; align-items: center; gap: 8px; padding: 16px 20px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
  .panel-header .title { font-size: 14px; font-weight: 700; color: var(--text); }
  .panel-header .title + button { margin-left: auto; }
  .panel-header button { background: none; border: none; color: var(--muted); font-size: 20px; cursor: pointer; line-height: 1; padding: 2px 6px; border-radius: 4px; }
  .panel-header button:hover { color: var(--text); background: #2a2a35; }
  .panel-body { flex: 1; overflow-y: auto; overflow-x: visible; padding: 16px 20px; display: flex; flex-direction: column; gap: 10px; overscroll-behavior: contain; }
  .panel-footer { padding: 14px 20px; border-top: 1px solid var(--border); display: flex; gap: 10px; flex-shrink: 0; }
  .panel-footer button { flex: 1; padding: 10px; border-radius: 8px; border: none; font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .15s; }
  .panel-footer button:hover { opacity: .85; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-secondary { background: #252530; color: var(--muted); border: 1px solid var(--border); }
  .panel-status { font-size: 12px; color: var(--green); text-align: center; padding: 0 20px 10px; display: none; flex-shrink: 0; }


      /* CONFIG PANEL */
  #config-panel { width: 460px; }
  .cfg-tabs { display: flex; flex-wrap: wrap; gap: 6px 8px; padding: 10px 12px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
  .cfg-tabs:empty, .cfg-tabs[hidden] { display: none; padding: 0; border: 0; }
  .cfg-tab-btn { flex: 0 0 auto; white-space: nowrap; border: 1px solid var(--border); background: #1a1a24; color: var(--muted); border-radius: 999px; padding: 6px 12px; font-size: 12px; font-weight: 700; cursor: pointer; transition: color .15s, border-color .15s, background .15s; }
  .cfg-tab-btn:hover { color: var(--text); border-color: var(--accent); }
  .cfg-tab-btn.active { background: rgba(124,106,247,.14); color: var(--accent); border-color: rgba(124,106,247,.45); }
  .cfg-tab-panel { display: none; flex-direction: column; gap: 10px; }
  .cfg-tab-panel.active { display: flex; }
  .cfg-section-title { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--accent); font-weight: 700; margin-top: 6px; }
  .cfg-section-sep { border: none; border-top: 1px solid var(--border); margin: 2px 0; }
  .cfg-group { display: flex; flex-direction: column; gap: 4px; overflow: visible; }
  .cfg-label { font-size: 11px; color: var(--muted); letter-spacing: .4px; }
  .cfg-input { background: #1c1c26; border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 13px; padding: 7px 10px; width: 100%; outline: none; transition: border-color .15s; }
  .cfg-input:focus { border-color: var(--accent); }
  .cfg-check-row { display: flex; align-items: center; gap: 8px; }
  .cfg-input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; padding: 0; }
  .cfg-label-row { display: flex; align-items: center; gap: 5px; }
  .cfg-info-icon { position: relative; display: inline-flex; align-items: center; cursor: help; color: var(--muted); flex-shrink: 0; }
  .cfg-info-icon svg { width: 13px; height: 13px; }
  .cfg-tooltip { display: none !important; }
  #floating-tooltip {
    position: fixed;
    top: -9999px;
    left: -9999px;
    max-width: 280px;
    min-width: 180px;
    background: #1e1e2e;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 11px;
    color: var(--text);
    line-height: 1.45;
    z-index: 10050;
    box-shadow: 0 4px 16px rgba(0,0,0,.5);
    pointer-events: none;
    opacity: 0;
    transition: opacity .08s ease;
    white-space: normal;
  }
  #floating-tooltip.show { opacity: 1; }
  .cfg-slider-row { display: flex; align-items: center; gap: 8px; }
  .cfg-slider { flex: 1; -webkit-appearance: none; appearance: none; height: 4px; border-radius: 2px; background: var(--border); outline: none; cursor: pointer; touch-action: none; }
  .cfg-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: var(--accent); cursor: pointer; transition: background .15s; margin-top: -6px; }
  .cfg-slider::-webkit-slider-thumb:hover { background: #9d8fff; }
  .cfg-slider::-webkit-slider-runnable-track { height: 4px; border-radius: 2px; background: var(--border); width: 100%; }
  .cfg-slider::-moz-range-track { height: 4px; border-radius: 2px; background: var(--border); border: none; }
  .cfg-slider::-moz-range-thumb { width: 16px; height: 16px; border-radius: 50%; background: var(--accent); border: none; cursor: pointer; }
  .cfg-slider::-moz-range-thumb:hover { background: #9d8fff; }
  .cfg-slider-input { width: 64px; background: #1c1c26; border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 13px; padding: 5px 8px; outline: none; text-align: center; transition: border-color .15s; }
  .cfg-slider-input:focus { border-color: var(--accent); }

  /* CALIBRATION PANEL */
  #calib-panel { width: 600px; }
  .calib-region-row { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
  .calib-region-label { font-size: 11px; font-weight: 600; color: var(--text); display: flex; justify-content: space-between; align-items: center; }
  .calib-region-coords { font-size: 11px; color: var(--muted); font-family: monospace; }
  .calib-btn-row { display: flex; gap: 6px; flex-wrap: wrap; }
  .calib-sm-btn { padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border); background: #1c1c26; color: var(--text); font-size: 12px; cursor: pointer; transition: border-color .15s, background .15s; }
  .calib-sm-btn:hover { border-color: var(--yellow); background: #222; }
  .calib-preview { width: 100%; border-radius: 6px; border: 1px solid var(--border); max-height: 80px; object-fit: contain; background: #0a0a0f; display: none; }
  .calib-ocr-result { font-size: 11px; color: var(--green); font-family: monospace; display: none; }
  /* Calib tabs */
  .calib-tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border); margin-bottom: 12px; flex-wrap: wrap; }
  .calib-tab { padding: 7px 14px; font-size: 12px; font-weight: 600; color: var(--muted); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color .15s, border-color .15s; background: none; border-top: none; border-left: none; border-right: none; white-space: nowrap; }
  .calib-tab:hover { color: var(--text); }
  .calib-tab.active { color: var(--accent); border-bottom-color: var(--accent); }
  .calib-tab-sep { width: 1px; background: var(--border); margin: 4px 6px; align-self: stretch; }
  .calib-section-label { font-size: 10px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
  .calib-empty-tab { font-size: 12px; color: var(--muted); padding: 20px 0; text-align: center; font-style: italic; }
  .calib-reset-btn { padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border); background: #1c1c26; color: var(--red); font-size: 11px; cursor: pointer; transition: border-color .15s, background .15s; }
  .calib-reset-btn:hover { border-color: var(--red); background: rgba(255,80,80,.08); }
  .panel-header .calib-reset-btn { font-size: 11px; line-height: 1.2; padding: 5px 10px; color: var(--red); background: #1c1c26; border: 1px solid var(--border); }
  .calib-tab-reset { margin-left: auto; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--border); background: transparent; color: var(--red); font-size: 11px; cursor: pointer; white-space: nowrap; }
  .calib-tab-reset:hover { border-color: var(--red); background: rgba(255,80,80,.08); }

  /* DOWNLOAD CENTER PANEL */
  #download-panel { width: 460px; }
  .dl-wrap { display: flex; flex-direction: column; gap: 12px; }
  .dl-card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; overflow: visible; }
  .dl-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .dl-title { font-size: 13px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 6px; }
  .dl-hint { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; border: 1px solid var(--border); color: var(--muted); font-size: 11px; cursor: help; }
  .dl-desc { font-size: 12px; color: var(--muted); line-height: 1.4; }
  .dl-actions { display: flex; gap: 8px; }
  .dl-progress { width: 100%; height: 8px; border-radius: 6px; overflow: hidden; background: #1a1a24; border: 1px solid var(--border); }
  .dl-progress > div { height: 100%; width: 0%; background: linear-gradient(90deg, #7c6af7 0%, #59d6ff 100%); transition: width .18s linear; }
  .dl-meta { font-size: 11px; color: var(--muted); display: flex; justify-content: space-between; gap: 8px; }




  /* Screenshot overlay (DPI-aware) */
  #ss-overlay { display: none; position: fixed; inset: 0; z-index: 9999; cursor: crosshair; background: transparent; }
  #ss-overlay canvas { position: absolute; top: 0; left: 0; /* width/height set by JS */ }
  #ss-hint { position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,.78); color: #fff; padding: 8px 18px; border-radius: 20px; font-size: 13px; font-weight: 600; pointer-events: none; white-space: nowrap; }

  /* Run popup */
  #run-popup { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%); background: #1e1e28; border: 1px solid #2a2a35; border-radius: 12px; padding: 22px 26px; z-index: 200; min-width: 260px; box-shadow: 0 8px 32px rgba(0,0,0,.6); }
  #run-popup-bg { display: none; position: fixed; inset: 0; z-index: 199; }


  #startup-screen {
    position: fixed; inset: 0; z-index: 9100;
    background: var(--bg); display: flex; align-items: center; justify-content: center;
  }
  .startup-content { text-align: center; }
  .startup-logo { font-size: 25px; font-weight: 900; margin-bottom: 18px; }
  .startup-logo .l-mt2 { color: #ff8c00; text-shadow: 0 0 18px rgba(255,140,0,.6); }
  .startup-logo .l-rb { color: #fff; }
  .startup-balls { display: flex; justify-content: center; gap: 12px; margin-bottom: 16px; }
  .startup-balls i {
    width: 14px; height: 14px; border-radius: 50%; background: var(--accent);
    animation: startupSpin .8s infinite alternate;
  }
  .startup-balls i:nth-child(2) { animation-delay: .16s; }
  .startup-balls i:nth-child(3) { animation-delay: .32s; }
  @keyframes startupSpin { to { opacity: .3; transform: translateY(-11px) rotate(180deg); } }
  .startup-label { color: var(--muted); font-size: 13px; }

  #login-screen {
    display: none; position: fixed; inset: 0; z-index: 9000;
    background: var(--bg);
    align-items: center; justify-content: center;
    flex-direction: column; gap: 0;
  }
  .login-footer { text-align: center; font-size: 12px; color: var(--muted); }
  .login-footer a { color: var(--accent); text-decoration: none; }
  .login-footer a:hover { text-decoration: underline; }

  /* ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ ACCOUNT POPUP ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ */
  .acct-btn {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--accent); border: 2px solid transparent;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    position: relative;
    transition: border-color .15s; flex-shrink: 0;
  }

  .live-att-preview { display: none; }
  @keyframes mfpulse { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
  @keyframes fadeDown {
    from { opacity:0; transform:translateY(-6px); }
    to   { opacity:1; transform:translateY(0); }
  }

  /* Sub-modal (change pw / delete account) */
  .acct-modal-bg {
    display: none; position: fixed; inset: 0; z-index: 600;
    background: rgba(0,0,0,.55);
  }

  /* First Steps wizard */
  .fs-modal-bg {
    display: none; position: fixed; inset: 0; z-index: 720;
    background: rgba(0,0,0,.62);
  }
  .fs-modal-bg.open { display: flex; align-items: center; justify-content: center; padding: 18px; }
  .lo-block-bg {
    display: none; position: fixed; inset: 0; z-index: 800;
    background: rgba(0,0,0,.72);
  }
  .lo-block-bg.open { display: flex; align-items: center; justify-content: center; padding: 18px; }
  .lo-block {
    background: #1a1a24; border: 1px solid var(--border);
    border-radius: 14px; width: min(420px, 92vw);
    box-shadow: 0 12px 48px rgba(0,0,0,.55);
    padding: 22px 24px 18px;
  }
  .lo-block h3 { font-size: 15px; font-weight: 800; color: var(--text); margin: 0 0 10px; }
  .lo-block p { font-size: 13px; line-height: 1.5; color: var(--text); margin: 0 0 8px; }
  .lo-block ul { margin: 8px 0 16px; padding-left: 18px; color: var(--accent2); font-size: 13px; font-weight: 700; }
  .lo-block button { width: 100%; padding: 10px; border: none; border-radius: 8px; background: var(--accent); color: #fff; font-weight: 700; cursor: pointer; }

  .lo-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 4px 0 8px;
  }
  .lo-slot {
    background: #14141c;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 8px 8px;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    min-width: 0;
  }
  .lo-slot[data-role="farming"],
  .lo-slot[data-role="fighting"],
  .lo-slot[data-role="stardust"],
  .lo-slot[data-role="meteor_rewards"] { border-color: #7c6af7; }
  .lo-slot-win {
    height: 72px;
    border-radius: 8px;
    background: linear-gradient(180deg, #1e1e2a 0%, #121218 100%);
    border: 1px solid #2a2a38;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: .5px;
  }
  .lo-slot select {
    width: 100%;
    height: 30px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: #1c1c26;
    color: var(--text);
    font-size: 12px;
    font-weight: 600;
    outline: none;
  }
  .lo-hint { font-size: 11px; color: var(--muted); line-height: 1.45; margin-top: 2px; }
  .fs-modal {
    background: #1a1a24; border: 1px solid var(--border);
    border-radius: 14px; width: min(760px, 94vw); max-height: 90vh;
    box-shadow: 0 12px 48px rgba(0,0,0,.75);
    display: flex; flex-direction: column; overflow: hidden;
  }
  .fs-head {
    display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap;
    padding: 16px 20px 12px; border-bottom: 1px solid var(--border);
  }
  .fs-head .fs-title { font-size: 15px; font-weight: 800; letter-spacing: .3px; }
  .fs-head .fs-sep { color: var(--muted); }
  .fs-head .fs-page-label { font-size: 13px; color: var(--accent); font-weight: 700; }
  .fs-body { padding: 16px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
  .fs-body p { font-size: 13px; line-height: 1.55; color: var(--text); }
  .fs-shot-wrap { display: flex; flex-direction: column; gap: 6px; }
  .fs-shot-cap { font-size: 11px; color: var(--muted); letter-spacing: .3px; }
  .fs-shot {
    border: 1px dashed #3a3a50; border-radius: 10px; background: #111118;
    min-height: 132px; overflow: hidden; display: flex; align-items: center; justify-content: center;
  }
  .fs-shot img { display: block; max-width: 100%; max-height: 280px; object-fit: contain; }
  .fs-shot .fs-ph { font-size: 12px; color: var(--muted); padding: 22px 16px; text-align: center; }
  .fs-foot {
    padding: 12px 20px; border-top: 1px solid var(--border);
    display: flex; gap: 8px; justify-content: flex-end;
  }
  .fs-foot button {
    min-width: 96px; padding: 9px 14px; border-radius: 8px; border: none;
    font-size: 13px; font-weight: 700; cursor: pointer;
  }
  .fs-dots { display: flex; gap: 6px; margin-left: auto; align-items: center; }
  .fs-dot { width: 7px; height: 7px; border-radius: 50%; background: #3a3a50; }
  .fs-dot.on { background: var(--accent); }
  .ocr-alias-row { display: flex; gap: 6px; align-items: center; margin-top: 4px; }
  .ocr-alias-row input { flex: 1; }
  .ocr-alias-btn {
    width: 28px; height: 28px; border-radius: 6px; border: 1px solid var(--border);
    background: #1c1c26; color: var(--text); font-weight: 800; cursor: pointer; flex-shrink: 0;
  }
  .ocr-alias-btn:hover { border-color: var(--accent); color: var(--accent); }
  .ocr-alias-btn.minus { color: var(--red); }
  .ocr-add-row { display: flex; gap: 6px; margin-top: 6px; }
  .fs-reopen-btn {
    width: 100%; padding: 9px 12px; border-radius: 8px; border: 1px solid var(--border);
    background: #1c1c26; color: var(--text); font-size: 13px; font-weight: 700; cursor: pointer;
  }
  .fs-reopen-btn:hover { border-color: var(--accent); color: var(--accent); }
  /* Offline banner */
  #offline-banner { display: none; position: fixed; top: 98px; left: 0; right: 0; background: #2a1018; border-bottom: 1px solid var(--red); color: #ff6677; padding: 10px 20px; text-align: center; font-weight: 600; z-index: 100; }
  #offline-banner.show { display: block; }


  /* === TWO-LEVEL TOPBAR === */
  #topbar { display: none !important; } /* hide old single topbar */
  
  #topbar-app {
    position: fixed; top: 0; left: 0; right: 0; z-index: 400;
    background: var(--topbar); border-bottom: 1px solid var(--border);
    display: flex; align-items: center; padding: 0 16px; height: 52px; gap: 0;
  }
  #topbar-run {
    position: fixed; top: 52px; left: 0; right: 0; z-index: 399;
    background: var(--panel); border-bottom: 1px solid var(--border);
    display: flex; align-items: center; padding: 0 16px; height: 46px; gap: 0;
  }
  body.tab-builder #topbar-run, body.tab-recorder #topbar-run { display: none !important; }
  body.tab-builder #page-run, body.tab-recorder #page-run { top: 52px !important; }

  /* === RECORDER CONTROL ISLAND (topbar, recorder tab) === */
  #topbar-recorder {
    display: none; align-items: center; gap: 6px; min-width: 0; flex: 1 1 auto;
  }
  body.tab-recorder #topbar-recorder { display: flex; }
  .rec-control {
    width: 38px; height: 38px; border-radius: 8px; border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    background: #252530; color: var(--text); cursor: pointer;
    font-size: 15px; font-weight: 900; line-height: 1; flex-shrink: 0;
    transition: opacity .15s, transform .08s, background .15s, border-color .15s;
  }
  .rec-control:hover { border-color: var(--accent); background: #2e2e3e; }
  .rec-control:active { transform: scale(.95); }
  .rec-control:disabled { opacity: .42; cursor: not-allowed; }
  .rec-control.on { background: rgba(124,106,247,.18); border-color: var(--accent); color: var(--accent); }
  .rec-control.rec-on { background: rgba(204,68,85,.18); border-color: var(--red); color: #ff91a2; }
  #rec-play-mode { width: 120px; min-width: 0; font-size: 12px; font-weight: 600; height: 34px; padding: 0 10px; border-radius: 8px; border: 1px solid var(--border); background: #1c1c26; color: var(--text); cursor: pointer; outline: none; }
  #rec-play-mode:hover, #rec-play-mode:focus { border-color: var(--accent); }
  #rec-play-times {
    width: 52px; height: 34px; padding: 0 8px; border-radius: 8px;
    border: 1px solid var(--border); background: #1c1c26; color: var(--text);
    font-size: 12px; font-weight: 700; outline: none;
  }
  #rec-play-times:hover, #rec-play-times:focus { border-color: var(--accent); }
  #rec-play-times[hidden] { display: none !important; }
  .rec-menu-wrap { position: relative; }
  .rec-menu-btn {
    height: 34px; border-radius: 8px; border: 1px solid transparent;
    background: transparent; color: var(--text); padding: 0 10px;
    font-size: 13px; font-weight: 800; cursor: pointer;
  }
  .rec-menu-btn:hover, .rec-menu-wrap.open .rec-menu-btn {
    background: #1c1c26; border-color: var(--border); color: #fff;
  }
  .rec-menu-pop {
    position: absolute; top: calc(100% + 6px); left: 0; min-width: 152px;
    display: none; flex-direction: column; padding: 6px;
    background: #15151d; border: 1px solid var(--border); border-radius: 8px;
    box-shadow: 0 12px 30px rgba(0,0,0,.45); z-index: 700;
  }
  .rec-menu-wrap.open .rec-menu-pop { display: flex; }
  .rec-menu-item {
    height: 32px; border: none; border-radius: 6px; background: transparent;
    color: var(--text); padding: 0 10px; text-align: left;
    font-size: 13px; font-weight: 650; cursor: pointer;
  }
  .rec-menu-item:hover { background: rgba(124,106,247,.14); color: #fff; }
  .rec-menu-sep { height: 1px; background: var(--border); margin: 4px 6px; }
  #rec-macro-label {
    min-width: 0; max-width: 160px; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
    color: var(--muted); font-size: 12px; font-weight: 700; padding: 0 6px;
  }
  @media (max-width: 1100px) {
    #rec-macro-label, .rec-macro-sep { display: none !important; }
  }
  
  /* App tabs */
  .app-tabs { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
  .app-tab {
    height: 34px; padding: 0 18px; border-radius: 8px; border: none;
    background: transparent; color: var(--muted); font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: 7px;
  }
  .app-tab:hover { background: rgba(124,106,247,.10); color: var(--text); }
  .app-tab.active { background: rgba(124,106,247,.18); color: var(--accent); }
  .app-tab:disabled, .app-tab.wip {
    opacity: .42; cursor: not-allowed; pointer-events: none;
  }
  .app-tab svg { width: 15px; height: 15px; }
  
  /* Adjust layout offset for two topbars */
  body.tab-run #layout { top: 98px; }
  body.tab-builder .builder-page, body.tab-recorder .recorder-page { top: 52px; }
  
  /* === APP PAGES === */
  .app-page { display: none; position: fixed; left: 0; right: 0; bottom: 0; overflow: hidden; }
  body.tab-run #page-run { display: flex; }
  body.tab-builder #page-builder { display: flex; }
  body.tab-recorder #page-recorder { visibility: visible; pointer-events: auto; z-index: 5; }

  #page-run { top: 98px; }
  #page-builder { top: 52px; flex-direction: column; }
  #page-recorder {
    display: flex !important;
    top: 52px; flex-direction: column; padding: 0; overflow: hidden;
    visibility: hidden; pointer-events: none; z-index: 0;
  }

  #recorder-frame {
    flex: 1; width: 100%; height: 100%; border: 0; background: var(--bg); display: block;
  }
  
  /* === BUILDER PAGE === */
  .builder-page { width: 100%; height: 100%; display: flex; flex-direction: column; background: var(--bg); }
  
  /* Builder welcome screen */
  #builder-welcome {
    flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 24px; padding: 40px;
  }
  .builder-welcome-title {
    font-size: 28px; font-weight: 800; color: #ff8c00;
    text-shadow: 0 0 8px rgba(255,140,0,.7), 0 0 20px rgba(255,140,0,.35);
  }
  .builder-welcome-sub { font-size: 14px; color: var(--muted); }
  .builder-mode-list { display: flex; flex-wrap: wrap; gap: 16px; max-width: 800px; justify-content: center; }
  .builder-mode-card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 20px 24px; width: 220px; cursor: pointer; transition: all .15s;
    display: flex; flex-direction: column; gap: 8px;
  }
  .builder-mode-card:hover { border-color: var(--accent); background: rgba(124,106,247,.08); transform: translateY(-2px); }
  .builder-mode-card .bmc-name { font-size: 16px; font-weight: 700; color: var(--text); }
  .builder-mode-card .bmc-desc { font-size: 12px; color: var(--muted); }
  .builder-mode-card .bmc-actions { display: flex; gap: 8px; margin-top: 6px; }
  .builder-mode-card .bmc-btn {
    padding: 4px 12px; border-radius: 6px; border: 1px solid var(--border);
    background: rgba(124,106,247,.10); color: var(--accent); font-size: 11px; font-weight: 600;
    cursor: pointer;
  }
  .builder-mode-card .bmc-btn:hover { background: rgba(124,106,247,.20); }
  .builder-mode-card .bmc-btn.danger { border-color: var(--red); color: var(--red); background: rgba(204,68,85,.10); }
  .builder-mode-card .bmc-btn.danger:hover { background: rgba(204,68,85,.20); }
  .builder-new-btn {
    padding: 12px 28px; border-radius: 10px; border: 2px dashed var(--border);
    background: transparent; color: var(--muted); font-size: 14px; font-weight: 600;
    cursor: pointer; transition: all .15s;
  }
  .builder-new-btn:hover { border-color: var(--accent); color: var(--accent); }
  
  /* Builder editor layout */
  #builder-editor { display: none; flex: 1; flex-direction: row; overflow: hidden; }
  .builder-sidebar {
    width: 48px; min-width: 48px; background: var(--panel);
    border-right: 1px solid var(--border); display: flex; flex-direction: column;
    align-items: center; padding: 8px 0; gap: 4px;
  }
  .builder-nav-btn {
    display: flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; border-radius: 8px; cursor: pointer;
    border: none; background: transparent; color: var(--muted);
    transition: background .12s, color .12s; position: relative;
  }
  .builder-nav-btn:hover { background: rgba(124,106,247,.10); color: var(--accent); }
  .builder-nav-btn.active { background: rgba(124,106,247,.18); color: var(--accent); }
  .builder-nav-btn svg { width: 18px; height: 18px; flex-shrink: 0; }
  .builder-nav-btn[data-tooltip]::after {
    content: attr(data-tooltip); position: absolute; left: 44px; top: 50%;
    transform: translateY(-50%); background: #16161c; border: 1px solid var(--border);
    padding: 4px 10px; border-radius: 6px; font-size: 12px; white-space: nowrap;
    color: var(--text); opacity: 0; pointer-events: none; z-index: 1000;
    transition: opacity .15s;
  }
  .builder-nav-btn[data-tooltip]:hover::after { opacity: 1; }
  .builder-sidebar-sep { border: none; border-top: 1px solid var(--border); width: 28px; margin: 4px 0; }
  
  .builder-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .builder-view { display: none; flex: 1; flex-direction: column; overflow: hidden; }
  .builder-view.active { display: flex; }
  
  /* Builder toolbar */
  .builder-toolbar {
    height: 44px; background: var(--panel); border-bottom: 1px solid var(--border);
    display: flex; align-items: center; padding: 0 16px; gap: 8px; flex-shrink: 0;
  }
  .builder-toolbar-title { font-size: 14px; font-weight: 600; color: var(--text); margin-right: auto; }
  .builder-toolbar-btn {
    padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); font-size: 12px; font-weight: 500; cursor: pointer;
  }
  .builder-toolbar-btn:hover { border-color: var(--accent); }
  .builder-toolbar-btn.primary { background: rgba(124,106,247,.18); border-color: var(--accent); color: var(--accent); }
  
  /* Flow graph */
  .flow-area { flex: 1; display: flex; overflow: hidden; }
  .flow-palette {
    width: 220px; min-width: 220px; background: var(--panel);
    border-left: 1px solid var(--border); padding: 12px; overflow-y: auto;
    order: 2;
  }
  #flow-canvas-container { order: 1; }
  .flow-palette-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 8px; }
  .flow-palette-item {
    padding: 10px 12px; margin-bottom: 6px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg); cursor: grab;
    display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500;
    transition: border-color .15s, background .15s;
  }
  .flow-palette-item:hover { border-color: var(--accent); background: rgba(124,106,247,.08); }
  .flow-palette-item:active { cursor: grabbing; }
  .flow-palette-item .fpi-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .flow-palette-item .fpi-letter { display: none; }
  
  #flow-canvas-container { flex: 1; position: relative; overflow: hidden; background: #0a0a0e; }
  #flow-canvas { width: 100%; height: 100%; display: block; cursor: default; }
  
  /* Procedure editor overlay (in-page, multi-tab) */
  #proc-editor-overlay {
    display: none; position: fixed; inset: 0; z-index: 8000;
    flex-direction: column; background: #0e0e12;
  }
  #proc-editor-overlay.open { display: flex; }
  .proc-editor-topbar {
    height: 40px; display: flex; align-items: center; gap: 2px;
    background: #16161c; border-bottom: 1px solid #2a2a35; padding: 0 8px;
    flex-shrink: 0;
  }
  .proc-editor-tab {
    display: flex; align-items: center; gap: 6px; padding: 6px 12px;
    border-radius: 6px 6px 0 0; cursor: pointer; font-size: 12px; font-weight: 500;
    color: #7070a0; background: transparent; border: 1px solid transparent;
    border-bottom: none; transition: all .12s; max-width: 200px; position: relative;
  }
  .proc-editor-tab:hover { color: #e0e0e8; background: rgba(255,255,255,.03); }
  .proc-editor-tab.active {
    color: #f7a06a; background: #0e0e12; border-color: #2a2a35; border-bottom: 1px solid #0e0e12;
  }
  .proc-editor-tab .tab-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .proc-editor-tab .tab-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .proc-editor-tab .tab-close {
    width: 16px; height: 16px; border-radius: 4px; display: flex; align-items: center;
    justify-content: center; font-size: 14px; color: #555; flex-shrink: 0; margin-left: 2px;
  }
  .proc-editor-tab .tab-close:hover { color: #f76a6a; background: rgba(255,0,0,.1); }
  .proc-editor-close-btn {
    margin-left: auto; padding: 4px 12px; border-radius: 6px; cursor: pointer;
    font-size: 12px; color: #7070a0; background: transparent; border: 1px solid #2a2a35;
  }
  .proc-editor-close-btn:hover { color: #f76a6a; border-color: #f76a6a; }
  .proc-editor-body { flex: 1; position: relative; overflow: hidden; }
  .proc-editor-iframe {
    position: absolute; inset: 0; width: 100%; height: 100%; border: none; display: none;
  }
  .proc-editor-iframe.active { display: block; }
  .proc-modal {
    width: 90%; max-width: 900px; height: 80%; background: var(--panel);
    border: 1px solid var(--border); border-radius: 12px; display: flex; flex-direction: column;
    box-shadow: 0 8px 32px rgba(0,0,0,.6);
  }
  .proc-modal-header {
    display: flex; align-items: center; padding: 12px 18px;
    border-bottom: 1px solid var(--border); gap: 12px;
  }
  .proc-modal-title { font-size: 15px; font-weight: 700; color: var(--accent2); }
  .proc-modal-close {
    margin-left: auto; background: none; border: none; color: var(--muted);
    font-size: 18px; cursor: pointer; padding: 4px 8px;
  }
  .proc-modal-close:hover { color: var(--text); }
  .proc-modal-body { flex: 1; overflow: hidden; padding: 16px; }
  .proc-modal-body textarea {
    width: 100%; height: 100%; background: #0a0a0e; color: var(--text);
    border: 1px solid var(--border); border-radius: 8px; padding: 12px;
    font-family: 'Consolas', 'Cascadia Code', monospace; font-size: 13px;
    resize: none; outline: none;
  }
  .proc-modal-body textarea:focus { border-color: var(--accent); }

  /* === VARIABLES VIEW === */
  .var-list { flex: 1; overflow-y: auto; padding: 16px; }
  .var-row {
    display: flex; align-items: center; gap: 8px; padding: 10px 14px;
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    margin-bottom: 8px;
  }
  .var-row input, .var-row select {
    background: var(--panel); border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 10px; color: var(--text); font-size: 12px; outline: none;
  }
  .var-row input:focus, .var-row select:focus { border-color: var(--accent); }
  .var-row .var-name { width: 160px; font-weight: 600; }
  .var-row .var-type { width: 100px; }
  .var-row .var-value { flex: 1; }
  .var-row .var-delete {
    background: rgba(204,68,85,.10); border: 1px solid var(--red); color: var(--red);
    border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; font-weight: 600;
  }
  .var-row .var-delete:hover { background: rgba(204,68,85,.25); }
  .var-add-btn {
    padding: 10px 20px; border-radius: 8px; border: 2px dashed var(--border);
    background: transparent; color: var(--muted); font-size: 13px; font-weight: 600;
    cursor: pointer; margin: 8px 0;
  }
  .var-add-btn:hover { border-color: var(--accent); color: var(--accent); }
  .var-section-title {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: var(--muted); margin-bottom: 8px; padding: 0 4px;
  }
  .var-hint { font-size: 11px; color: var(--muted); padding: 0 4px 12px; line-height: 1.5; }

  /* === PROCEDURE EDITOR (enhanced) === */
  .proc-editor {
    flex: 1; display: flex; flex-direction: row; overflow: hidden;
  }
  .proc-blocks-palette {
    width: 200px; min-width: 200px; background: var(--panel);
    border-right: 1px solid var(--border); padding: 12px; overflow-y: auto;
  }
  .proc-blocks-palette .flow-palette-title { margin-bottom: 8px; }
  .proc-block-item {
    padding: 8px 12px; margin-bottom: 6px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg); cursor: pointer;
    display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 500;
    transition: border-color .15s, background .15s;
  }
  .proc-block-item:hover { border-color: var(--accent); background: rgba(124,106,247,.08); }
  .proc-block-item .pbi-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  .proc-steps-area {
    flex: 1; overflow-y: auto; padding: 16px; background: #0a0a0e;
  }
  .proc-step {
    display: flex; align-items: flex-start; gap: 8px; padding: 10px 14px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    margin-bottom: 6px; position: relative;
  }
  .proc-step-nested { margin-left: 24px; border-left: 2px solid var(--accent); }
  .proc-step-handle { cursor: grab; color: var(--muted); padding-top: 2px; }
  .proc-step-type {
    font-size: 10px; text-transform: uppercase; letter-spacing: .5px;
    color: var(--accent); font-weight: 700; min-width: 60px; padding-top: 4px;
  }
  .proc-step input, .proc-step select {
    background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
    padding: 5px 8px; color: var(--text); font-size: 12px; outline: none; flex: 1;
  }
  .proc-step input:focus, .proc-step select:focus { border-color: var(--accent); }
  .proc-step .step-del {
    background: rgba(204,68,85,.10); border: 1px solid var(--red); color: var(--red);
    border-radius: 6px; padding: 3px 8px; font-size: 11px; cursor: pointer; flex-shrink: 0;
  }
  .proc-step .step-del:hover { background: rgba(204,68,85,.25); }

  .proc-code-preview {
    width: 360px; min-width: 360px; background: #0d0d14;
    border-left: 1px solid var(--border); display: flex; flex-direction: column;
  }
  .proc-code-header {
    padding: 10px 14px; border-bottom: 1px solid var(--border);
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted);
  }
  .proc-code-body { flex: 1; overflow: auto; padding: 14px; }
  .proc-code-body pre {
    margin: 0; font-family: 'Consolas', 'Cascadia Code', monospace;
    font-size: 12px; color: #a0d0a0; white-space: pre-wrap; line-height: 1.6;
  }
  .proc-code-body .kw { color: #f7a06a; }
  .proc-code-body .str { color: #a0d0a0; }
  .proc-code-body .var { color: #6aa6f7; }
  .proc-code-body .cmt { color: #555; }

  .proc-empty-hint { color: var(--muted); font-size: 13px; text-align: center; padding: 40px 20px; }
  
  /* === RECORDER PAGE === */
  .recorder-page {
    width: 100%; height: 100%; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 20px; padding: 40px;
  }
  .recorder-title {
    font-size: 28px; font-weight: 800; color: var(--muted);
  }
  .recorder-sub { font-size: 14px; color: var(--muted); }
  .recorder-icon {
    width: 80px; height: 80px; border-radius: 50%;
    border: 3px solid var(--border); display: flex; align-items: center; justify-content: center;
    color: var(--muted);
  }
  .recorder-icon svg { width: 36px; height: 36px; }
  body.tab-recorder #offline-banner, body.tab-builder #offline-banner { top: 52px; }


</style>
</head>
<body class="tab-run">


<!-- ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ LOGIN SCREEN ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ -->
<div id="startup-screen">
  <div class="startup-content">
    <div class="startup-logo"><span class="l-mt2">MT2</span> <span class="l-rb">Rebirth Bot</span></div>
    <div class="startup-balls"><i></i><i></i><i></i></div>
    <div class="startup-label">Starting up...</div>
  </div>
</div>

<div class="lo-block-bg" id="modal-loadout-block">
  <div class="lo-block">
    <h3>Loadouts required</h3>
    <p>Set these in Config before Start. Bot will not run with None on a used loadout.</p>
    <ul id="lo-block-list"></ul>
    <p style="color:var(--muted);font-size:12px;">Boss Fight uses Fighting + Farming. Crater and Meteor use Meteor Rewards.</p>
    <button type="button" onclick="closeLoadoutBlock()">OK</button>
  </div>
</div>

<div class="lo-block-bg" id="modal-gamedetect-block">
  <div class="lo-block">
    <h3>In-Game image detection not set!</h3>
    <p>Force Restart is ON, so the bot needs to know what the in-game HUD looks like. Pick an always-visible element (Miner Tycoon 2 logo, stone icon or shard icon) once in the global Config (top gear) &rarr; Force Restart. The bot will not start without it.</p>
    <p style="color:var(--muted);font-size:12px;">Pick it while in-game: press Pick, then F2, then drag a box around the element. Box and point save automatically.</p>
    <div style="display:flex;gap:8px;justify-content:center;margin-top:14px;">
      <button type="button" style="background:var(--accent);border:none;border-radius:8px;color:#fff;padding:8px 16px;font:600 13px 'Segoe UI',sans-serif;cursor:pointer" onclick="takeMeToGameDetect()">Take me there</button>
      <button type="button" style="background:var(--panel);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:8px 16px;font:13px 'Segoe UI',sans-serif;cursor:pointer" onclick="closeGameDetectBlock()">Close</button>
    </div>
  </div>
</div>

<div class="fs-modal-bg" id="modal-first-steps">
  <div class="fs-modal" role="dialog" aria-labelledby="fs-title">
    <div class="fs-head">
      <span class="fs-title" id="fs-title">First Steps</span>
      <span class="fs-sep">|</span>
      <span class="fs-page-label" id="fs-page-label">Sensitivity</span>
      <div class="fs-dots" id="fs-dots"></div>
    </div>
    <div class="fs-body" id="fs-body"></div>
    <div class="fs-foot">
      <button class="btn-secondary" id="fs-prev" onclick="firstStepsPrev()">Previous</button>
      <button class="btn-primary" id="fs-next" onclick="firstStepsNext()">Next</button>
      <button class="btn-primary" id="fs-close" onclick="firstStepsClose()" style="display:none;">Close</button>
    </div>
  </div>
</div>

<!-- CHANGE PASSWORD MODAL -->

<!-- ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ CHANGE PASSWORD MODAL ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ -->


<!-- ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ DELETE ACCOUNT MODAL ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ -->



<!-- TOP BAR 1 (app-level) -->
<div id="topbar-app" style="display:none;">
  <div class="brand-wrap">
    <span class="brand-text"><span class="brand-mt2">MT2</span> <span class="brand-rebirth">Rebirth Bot</span></span>
  </div>
  <div class="topbar-sep"></div>
  <div class="app-tabs">
    <button class="app-tab active" data-tab="run" onclick="switchAppTab('run')">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>
      Run
    </button>
    <button class="app-tab" data-tab="recorder" onclick="switchAppTab('recorder')">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>
      Recorder
    </button>
  </div>
  <div id="topbar-recorder">
    <div class="topbar-sep"></div>
    <button type="button" class="rec-control" id="rec-play-btn" onclick="recCmd('play')" title="Play / Stop (F6)">&#9654;</button>
    <button type="button" class="rec-control" id="rec-record-btn" onclick="recCmd('record')" title="Record (F5)">&#9679;</button>
    <select id="rec-play-mode" title="Playback" onchange="recCmd('playMode', {value:this.value})">
      <option value="once">Play Once</option>
      <option value="loop">Loop</option>
      <option value="times">Loop xTimes</option>
    </select>
    <input id="rec-play-times" type="number" min="1" step="1" value="5" hidden title="Loop count" onchange="recCmd('playTimes', {value:this.value})">
    <div class="topbar-sep"></div>
    <div class="rec-menu-wrap" id="rec-file-wrap">
      <button type="button" class="rec-menu-btn" onclick="toggleRecMenu('file')">File</button>
      <div class="rec-menu-pop">
        <button type="button" class="rec-menu-item" onclick="recCmd('new')">New Macro</button>
        <button type="button" class="rec-menu-item" onclick="recCmd('open')">Open</button>
        <button type="button" class="rec-menu-item" onclick="recCmd('import')">Import</button>
        <div class="rec-menu-sep"></div>
        <button type="button" class="rec-menu-item" onclick="recCmd('save')">Save</button>
        <button type="button" class="rec-menu-item" onclick="recCmd('saveAs')">Save As</button>
      </div>
    </div>
    <div class="topbar-sep rec-macro-sep"></div>
    <span id="rec-macro-label">No macro</span>
  </div>
  <div class="topbar-spacer"></div>
  <div class="topbar-right">
    <button class="icon-btn" id="btn-config" onclick="togglePanel('config')" title="Config">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
    </button>
  </div>
  </div>
</div>

 — no Calibration button -->
<div id="topbar-run" style="display:none;">
  <div class="topbar-left">
    <select id="bot-mode-select" onchange="setBotMode(this.value)" title="Bot mode">
      <option value="" disabled>- MODE -</option>
      <option value="rebirth" selected>Rebirth</option>
      <option value="" disabled>- BOSS -</option>
      <option value="delve">Delve</option>
      <option value="kraken">Kraken</option>
      <option value="zytos">Zytos</option>
      <option value="" disabled>- FARM -</option>
      <option value="crater">Crater</option>
      <option value="farm_meteor">Meteor</option>
    </select>
    <div class="topbar-runmode" id="farm-meteor-area-wrap" style="display:none;">
      <select id="farm-meteor-area-select" onchange="setFarmMeteorArea(this.value)" title="Meteor area">
        <option value="" disabled>- METEOR -</option>
        <option value="a6">Area 6</option>
        <option value="a7">Area 7</option>
        <option value="a8">Area 8</option>
      </select>
    </div>
    <button id="btn-start-stop" style="background:var(--green)" onclick="toggleStartStop()">
      <svg id="ss-icon-play" fill="white" viewBox="0 0 24 24" width="16" height="16"><polygon points="5,3 19,12 5,21"/></svg>
      <svg id="ss-icon-stop" fill="white" viewBox="0 0 24 24" width="16" height="16" style="display:none"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
      <span id="ss-label">Start</span>
    </button>
  </div>
  <div class="topbar-sep rebirth-only"></div>
  <div class="topbar-runmode rebirth-only" id="run-mode-wrap">
    <select id="run-mode-select" onchange="setRunMode(this.value)" title="Run mode">
      <option value="" disabled>- RUN MODES -</option>
      <option value="" disabled>- AREA 5 -</option>
      <option value="a5meteor">Area 5 - Meteor</option>
      <option value="a5s4">Area 5 - Stage 4</option>
      <option value="a5s3">Area 5 - Stage 3</option>
      <option value="a5s2">Area 5 - Stage 2</option>
      <option value="a5s1">Area 5 - Stage 1</option>
      <option value="" disabled>- AREA 4 -</option>
      <option value="a4s4">Area 4 - Stage 4</option>
      <option value="a4s3">Area 4 - Stage 3</option>
      <option value="a4s2">Area 4 - Stage 2</option>
      <option value="a4s1">Area 4 - Stage 1</option>
      <option value="" disabled>- AREA 3 -</option>
      <option value="a3s4">Area 3 - Stage 4</option>
      <option value="a3s3">Area 3 - Stage 3</option>
      <option value="a3s2">Area 3 - Stage 2</option>
      <option value="a3s1">Area 3 - Stage 1</option>
      <option value="" disabled>- AREA 2 -</option>
      <option value="a2s4">Area 2 - Stage 4</option>
      <option value="a2s3">Area 2 - Stage 3</option>
      <option value="a2s2">Area 2 - Stage 2</option>
      <option value="a2s1">Area 2 - Stage 1</option>
      <option value="" disabled>- AREA 1 -</option>
      <option value="a1s4">Area 1 - Stage 4</option>
      <option value="a1s3">Area 1 - Stage 3</option>
      <option value="a1s2">Area 1 - Stage 2</option>
      <option value="a1s1" selected>Area 1 - Stage 1</option>
    </select>
  </div>
</div>

<div id="offline-banner">Bot offline - reconnecting...</div>

<div id="page-run" class="app-page">
<div id="layout">
  <!-- LEFT SIDEBAR -->
  <div id="left-sidebar">
    <div class="sb-body">
      <button class="sb-item" id="sb-force-restart-btn" onclick="sbToggleForceRestart()" title="On failure, recover automatically: three-state check (in game? GUI open? clearly not in game?), then leave to the lobby, verify Miner Tycoon 2 is selected (wrong game -> island-code map search) and rejoin. Works for Rebirth, Kraken, Zytos, Crater and Farm Meteor. Settings: global Config (top gear) &rarr; Force Restart. Needs the In-Game image detection picked once.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
        <span class="sb-label">Force Restart</span>
      </button>
      <input type="checkbox" id="force-restart-check" onchange="setForceRestart(this.checked)" style="display:none;">
      <button class="sb-item" id="sb-pause-on-lag-btn" onclick="sbTogglePauseOnLag()" title="When the internet drops or packet probes fail, freeze the current action and wait until the connection is back. No force restart.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/></svg>
        <span class="sb-label">Pause on Lag</span>
      </button>
      <input type="checkbox" id="pause-on-lag-check" onchange="setPauseOnLag(this.checked)" style="display:none;">
      <div style="height:1px;background:var(--border);margin:8px 10px;"></div>
      <!-- Kraken ESP and Dodge removed Ã¢â‚¬â€ not used in new kraken mode -->
      <!-- Activate Drills (delve mode) -->
      <button class="sb-item delve-only" id="sb-activate-drills-delve-btn" onclick="sbToggleActivateDrillsDelve()" title="Activate one drill at the start of each Delve boss fight.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span class="sb-label">Activate Drills</span>
      </button>
      <input type="checkbox" id="activate-drills-delve-check" onchange="setActivateDrillsDelve(this.checked)" style="display:none;">
      <!-- Activate Drills (kraken mode) -->
      <button class="sb-item kraken-only" id="sb-activate-drills-kraken-btn" onclick="sbToggleActivateDrillsKraken()" title="Activate one drill at the start of each Kraken boss fight.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span class="sb-label">Activate Drills</span>
      </button>
      <input type="checkbox" id="activate-drills-kraken-check" onchange="setActivateDrillsKraken(this.checked)" style="display:none;">
      <!-- Activate Drills (zytos mode) -->
      <button class="sb-item zytos-only" id="sb-activate-drills-zytos-btn" onclick="sbToggleActivateDrillsZytos()" title="Activate one drill at the start of each Zytos boss fight.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span class="sb-label">Activate Drills</span>
      </button>
      <input type="checkbox" id="activate-drills-zytos-check" onchange="setActivateDrillsZytos(this.checked)" style="display:none;">
      <button class="sb-item crater-only" id="sb-crater-overlay-btn" onclick="sbToggleCraterOverlay()" title="Toggle rock detection overlay.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>
        <span class="sb-label">Overlay</span>
      </button>
      <input type="checkbox" id="crater-overlay-check" onchange="setCraterOverlay(this.checked)" style="display:none;">
      <!-- Unlock Drills -->
      <button class="sb-item rebirth-only" id="sb-unlock-drills-btn" onclick="sbToggleUnlockDrills()" title="Automatically unlock drills once the stone threshold is reached">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>
        <span class="sb-label">Unlock Drills</span>
      </button>
      <!-- Activate Drills -->
      <button class="sb-item rebirth-only" id="sb-activate-drills-btn" onclick="sbToggleActivateDrills()" title="Activate drills every 10 seconds.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span class="sb-label">Activate Drills</span>
      </button>
      <button class="sb-item rebirth-only" id="sb-boss-fight-a1-btn" onclick="sbToggleBossFightA1()" title="Boss Fight A1: grind baserock to e33, then fight the A1 Meteor + Bramble boss each run.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M9 12h6M12 9v6"/></svg>
        <span class="sb-label">Boss Fight</span>
      </button>
      <button class="sb-item rebirth-only" id="sb-daily-quests-btn" onclick="sbToggleDailyQuests()" title="Daily Quests: right after each rebirth, open the quest panel and Start the quests the bot will do — rock quests then progress naturally during the run. Before the rebirth walk, do any quest not already Done on the HUD (no wasted teleports), claim rewards, then rebirth.">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6M9 16h4"/></svg>
        <span class="sb-label">Daily Quests</span>
      </button>
      <!-- Hidden checkboxes for state sync -->
      <input type="checkbox" id="unlock-drills-check" onchange="setUnlockDrills(this.checked)" style="display:none;">
      <input type="checkbox" id="activate-drills-check" onchange="setActivateDrills(this.checked)" style="display:none;">
      <input type="checkbox" id="auto-strength-check" onchange="setAutoStrength(this.checked)" style="display:none;">
      <input type="checkbox" id="boss-fight-a1-check" onchange="setBossFightA1(this.checked)" style="display:none;">
      <input type="checkbox" id="daily-quests-check" onchange="setDailyQuests(this.checked)" style="display:none;">
    </div>
    <div id="sb-footer">
      <button id="sb-toggle-btn" onclick="toggleSidebar()" title="Collapse / expand sidebar">
        <svg id="sb-toggle-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
        <span class="sb-label">Hide panel</span>
      </button>
    </div>
  </div>
  <!-- MAIN CONTENT -->
  <div id="main">
    <div id="rebirth-main">
    <div class="sec-label" style="display:none;">Current Run</div>
    <div class="baubles" style="display:none;">
      <div class="bauble status-bauble"><div class="b-label">Status</div><div class="b-val accent" id="b-status">-</div></div>
      <div class="bauble"><div class="b-label">Time</div><div class="b-val accent" id="b-time">-</div></div>
      <div class="bauble"><div class="b-label">Steps</div><div class="b-val accent" id="b-steps">0</div></div>
      <div class="bauble"><div class="b-label">Errors</div><div class="b-val red" id="b-errors">-</div></div>
    </div>
    <hr style="display:none;border:none;border-top:1px solid var(--border);margin:18px 0 14px 0;">
    <div class="sec-label" id="alltime-label" style="display:none;">All-Time Stats</div>
    <div class="baubles">
        <div class="bauble rebirth-bauble"><div class="b-label" id="g-count-label">Rebirths</div>
      <div class="b-val green rebirth-val-row"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAYAAAAehFoBAAAT0UlEQVR4nJWZebRlVXXuf3OttZvT3v5W3Vv3FtUBVTQBaSwoQIw8kpARY7SUSAWTqHHgMAG7JG+YPzAvMZr3HHlvxOAYeSogoBKRFzTS2QAPUekKqBKoDqqvoprb1L2n3d1a6/1xzgV9icl7c4w9xj5nn73PN+f65pzfXFtq5Tq/zLzA+PQkJggIHNgsJ5WCAwcOKpUVnLl+vbvq7b/O3d+6Z6XS6q1Zlp1fqZSm2+12COT1UuUYab4jUuapiakVL65Zvbrw3nPHXXdrpXHXX7/F/+DhH5DnBUFgyPOCMIywhSWzBc45ut0uAE56mOQ/Arxi7SpCbeg2W5RKJV58cbtG4c47+1y/MHfq8kLsTcDVcRwPFrbAe0uRFwCYwFAyIdbaNCvyHUVR3ItSd1208eLDDz38sNjCquGBYVtkGUEQUhQ5cVTGe4/F472n0Wj8vwH2/R9MTE0ShiG7XnxZOUHWrj/dLiycmgxFfz7y6jrf7YrxQpIkzhjta7UKxgQAJDaXucYCBFqZMPQSGiHQLR0E/7OdJZ+78oor5r7zzfu0drh6ve4BnPWIElAKEfn/B9xqN0W0Vmefsd7u2rVLhsaHPxhF0WdjMWP5XMNVktz/ypoz1SWXXCJjY2MMDtWplMu9ezsdDhw9zNaXtvPCrpfdTLvho8GaspGWVp6+prT+aLLQvjfvJFpr5dI0Ay+itEIZ45VS3lr77wMOwwBrLd0kIc1TRRzI6nWn2+6x2Q3Kc4upRm+zeeGYb/nzJlerm975Xjl3ag1BGAIQBPoNp60lUgaJQ3a+doDvP/ckDz3zY3+4c8oVlVA5LeJTd8vE+LJPHDp8OJ+Zm1cjQ0MuMAEz83PKe4+IuDAMQQlpmv5rwFor8jwnTVNlSpEbn14R2Sz/M93J/6LqdclYa107kSvPv1jduOX9TJsyZafIswwRQWnBOYt3HuU8uvB4AT9YphXCkbzJ7d/5Fvc9+j2nByrOGmOs4sFWq33t8PBQ0emkv6JEstrgwM4TJ05ks7OzEoahV6YXCKlWeoDF9wBneYYtCl2uVGy9XDkjEH2XOP9mJeIq7cKfawb1lRvexLWbN1MOI0gzXFEQhgbrHFopvPc479EOiErQblEYhSsHLLgUWw554rln+Mp9/+RfzZs2LwUGeBrQRgcXFdaSZOlW4MOtVus555yy3rsgMG8AXuJIp9VQpVLFDQwMnCfd/MFRKpNBJy+G47qeLtflkuVTvO+33kFpdATX6aBqVfJ2g6BSwXW6iPjXnccDQQR5DuLIDPggoJ0lVGo1ds4d5eNf/Dx7GzMurlVVXuTkncyXalWfKK8yVxwLtNk4Ozt7OM1ShYhTQyOjDI0vY3jZGJ12Q02sWuVqw0NrvLj7K2F5stJSxblMmi1jG+WtwSp+deMmSqvGcK6LKmts0YZYk9uEwngkNjgszqegHXRbYByEiqxI8d5SCQJMJ+P02hifu+GTnFVfrtx808Zd66697G1y2doNymdpFpbCCa/8H5eqMXhkcKiO0kYRxQGJzRlbdZo7dvCgRMZ8qariKZlpFRvUmLlq9BxWd6us0cOsWzFF3l7Ei8P64vWVWbIiyVFKoySC1IMpgVWQFUQqRBUO40BbKOWwfmg5f/uRP+W80Wn9J5uvVze9+318/Pf/iLH6oCmKAiVyiVKaIA5cmqYY53LS1DJ7+JAen1ppxydX3FAluorFZnFuacK8c/wcprsVGo0Way8+AxkYIbBzIEKWZ4QmAK/6FDAQxNBoQzMF6yFvw/gY1AcIkjbgelTxoBzUCs/ZQ8u55RM3E8YRYQIqCJgaHJXjxxpIqNdoparlcqm1uNAQo8Vx8PBBWT69wjpra8bpT0orZ7QTqE3TZzKRBJS7ljSKqI8MQ7MJJcA5Am16oHDgDDhFa89BXt2+k4Ujc9TiEoVzRNWYNeeeSf2s08FlPar0V0ZbwTU6jJdKuNzjraMWh0wOj+H270bCcJnzfqUxwQ48opTK6fUVh7L+HaHS6/xiYi8YXKXWhaMo6+koh63FVKaXgQKsA+cR63vlJclAxSQvHeTZ+x4j2b/IkKtTSsu4WUvrUJNtDz/Ns3fcB8caoEpgLRR53/EQcguFI89zRITVp60Sm2bO5T6Mg3iNyx14RInP8BavxRJo2exTx2hQZU0wwmBHCCSgcA6UQK0GYQha4awlzTOszSGOyU/N8sOtT2MrFXIJ6bQs7ZmMOK8w4OuM6GF02/H4tx/E7TsIoQHlX6eH9r2PSmlwnomBYao69MYBsEEpBSDq6OF5Wbt61HlbDIl1G4tuynBcV6uiEUoNT95sI85RU2GPq3kvKmI0KgxwpZh2RfHVF37ENw9t52ellAMVKMpVotIAkakSFDE6gagwZIsJe/fsg3KJLOu+Uf76ZoyGvOCM0eWMqdBr7wA2vH7deVRWWKu8rAu0TITaM16tSVk0NR2SOUGFhsXZWeaf2sbwBadBOULKMUHZ0LYN5qTg3ud/zJFsgUP7XmB9PImtruOcynL8XJvQWvI8I5WcTVdcQeXSDdBoEVbKUBT0eAYIaFFo65ioDTCgA2k4C3C6iABYk1p400WX88xTT66NvIWka4N6pttZi0zVqZgSzUaT1LZ56SfbqGw7QFCOGTtthJENk5Q3DLO7cZzFUFioGQjgmYUDHGnOML9sAxeFQwxYTyoZiSmoXHgOuARcPxeUB8lBQOHxXmO8UA01p01OqT37diBRfa2I1KemphpGeSUBEeKZstYSBwFRtYy3ZY6lBW3bZWBqmPE1Z3Bw32GacwUDuXDilUN0Z/dx4PkG2/PjzCRdugHkts3U+ADHX5vl+eM/49xll2OVwuoAr6G581VqZ54GlSq0TuJjjzMOjUIQxIPBE4pm+fgo7ANgTESmgZdNBUfZeUJMM4gC8tyyoDQzKOYGAtQFZ3PlDVsYPGeUs3bP8NSd32Pn088z2z7FocWTPHdkL7NRga+GmLSgVq6QnGqwSpU4u7YSvCEnBO/Q1rD1kecY23WEc87bAOesQvQpnGQ4W2AQcB7nAAvTE9PSO8MAq4GXzbt+a3Px9JNPlYyS9zTbHYLSoDywYzt63Sjv/8iNRJdu4OBkiYEJkOoYl7zpei559d3c8aUv8i/33MGOzgyV+jB4izEBhc+JBS4+/3xWtCtwqkdP5QFnqJUqzO+d5Yn9PyL66VZO27Se6kSdyugQ+AJcgVGeAsPE2DjK9xCLyHrgftXVBZ0i+5hYuSoq1eys8+qa//xxfufr/8DC1Rewq6w4iSMFMpVCHTg35g/+9hM88spW/svf/zcGJsc51WzQ6bQJggAdGmabTaQcEMUQmRzlMoI8p2h0qZsqdVNHTlp23PcUL9/7JIcfeRHmHOg6kgu+W7B8ZBnVcs3jBI0+y2YW06LA1Ctva8ydolKp8T9u+UemLtjEkXnoeDCmRCwZOWDCAisRLgS04DLFR2+6gff87rU88OAD3P6VW3l+63OsKA/y0sn9tI/N8ObqNJNhmXq5ik6FIPNEBZhMUTYhpWic9kLCwecPcGD3flasn2Z4wwpKa8cYX7ECpZQAiKjV3ltMqiHV6FQpAq2YWLWG+VMdTDhIRUEBpNaSeM9Q4NFkaASnNUFkIIHJ8SE+9IfXs3nzO/nhAw9z951f4+nHn2AhTth18ihnDCzjrPoq1g6PM9gAaVrCTkFRwLw4rDHodkFsYd8zO9h1aC/hRSs5WitwSuOxeOUy5x1GBxGtTvdQuVYhsbk/9tprVKYG8B7SFMIyZBY6XhiQiKXWpFC98hn000KgXq1w7XWbefe7N/OBD32AB777L4xPVtmRLXDg5HaWSZ2z6quYqI+wbHAYWwiX/841LD9tJft/8lMO79/N7KkWe2cO8uQ3H+Ww7pAPVxAleMeDAGZyeJzIBHtRioVmQxqLc4yugXaeYuIILdDt5Jxc9NSHAqSPcamlLhV8dF9mZBYdaoYHh9BK0cy6dI1iIVIczhd59ORzjAytYsvvfpjf+E9vY/n5U1CF1e8/g9WLGUd2vkjzse+jfpDRPLDHKuN1kWWPnDx58h/K5TJGAeLV/t6U7Jg9eZzTxeJIcT7EOcGYiMwKto/R9fv+62D7yksBGM1f3/xX3PHV29DGUAi0bU6qQ9oRXPiet/P2d/0eG87ayKF2g3VjMBz27k1Cz4qVF/Khay7krS+9g2uuucZ3s5QwDE/UajXXaDS0wWtYKs+gDh48xKVLYrywKGOIAkOWWRRvTMSv25KA7zvw1dtv4+a//jRnrF3H4uIiojViytSnVvHRj/05Z194GUUutBsNzls9Rhy+8agoihAFeW4ZXTZOuVqV1qk58K4WxgF+0S8pb3UcrzqAzMzMeBHBe9effkEpRWHtvwW3Tw3/+vG+338fN37kjzl69OhSDEjygquv+W2uvPo36eaWPElZNhAzPgA/hxcx4F1vq6DdapOmqQ+CgDRNTy49TAFkWXas2WzOGWPYv3+fz7OMMAgRUaRphveeIs8p6EsAC1nWS0pnf05qAVobvvDFW/jyl7/M8MgIc3NztE/MMrl8grzbgqTF8qGI1ctqDJh/7bz0Q7jnlT3Mzs1KFEUA+53v/Y+57R+/KB++6WPdb9//zwcz9HS706LVaqOGB9E9uuC9xTpH0ZevSoGO+nRwvdVYMucsLnNct2ULm664nAceephnX9rBb1x5KVlyivWTA4zWqkzHUKZXYP4t271rN0k3odvtEobhy0WeQm8IM0pEbJqmh3S5zOLColtYnFMj46ehlxjjLLYoSFOQuLdsed4Db5R/PSoAOgjwLgMlrFy5ko98+AYAUiweh+AQCkICQND9VVsyW3gUwhM/fsJHpVhbaxcF/XyWZ5jIeIM2kqc5A+XyK3OtFl2X0pxfYNg6rBUUkFvLQl4wm8JADE0HjVZB0mmzenoAjaCdQ+EQ5zFRj5mFc1ivEOUwKkcoUAg9LeOgnxWqT4ceSYXtL2zjsUcfc6VySStjnmp3u4fa7Y6q1+tOYfE/e+55fKe7fyiMiGwhs4ePEHpNpBTeeYrAsKhDXu3CIWBHE7bOp7yw0GHbiQaLQKEEr/qjMHmfzxptBFEaR4wnxvUj2y+Qv0hh5/A4br31yzRbTYw2KKW+kacpRVrI4kITA705Ujv2inOQZqp58gSBK0ibCWGkqFSq5KUac60uT7xsKZWqqFIFF8bsXZilYy3nTQ5RJiDEoXEoekvbb4J962WZwy3NGDjn8M73XPCO7//wh3zt7m+4weFhrY1+sdXpfMtaC0qcKEEpnO83gWNAC5AD+171JQpGY5iMYdsj36Wz7xVWlEKQgkwcuYWkEFrBAPs78PjheWaADorcG/I+TA3ovhPSj6hH4fqHiGCdRRnNoYOH+NSnPkUURb5cKpFl+V81m82utVZrbbyIoAQ84gB1zKFmatUSr+56mdf27WL+4B7+7tN/zuc/fqP/ws1/QevIAaqhkKdtkk6KUgonEYWuciqPeHLvKQ53oCX05Gi/Cvh+vD0K2yfCUtcUEbTS7N6xk+u2bOH48eN5HMd6YXHxtl/7tavvTZJEWWut0golglx+4WU8+9zTeuPGC+3h145+ITfBjW1LagZGTavVwjUWGShX1fxCx685/wL1Z3/336ksX0E39eRegYmggABLJdR0OwsMlgNWj1eYLvVIENFTfUukKDwE0ju3ec7tt97K5z73N77b7do4Khvr3A9KcfzbmzZtSr529zfEGOPpqUzkVy++jCef/alccukmv/3ll4bCSul7RNHFVpQTr1TJiu00u53BZRO1Y42Gi6em1Cc//ZesO+tcGklBtzBoHRGoEGM0hXIol1PKU6oGaqFhYqyMclCKINJQUTC30OC79/4vvn77V/wru/c4pTzVak2naX5/KY6vu+Itb2ndeecdooOg13mXduB/87K3YvE8+pPH5fwLLvQn5meHkjz/E0fxlkCCQifq7sCUnkwM3/JxfN5Mo1FQivR7/+j98uvv2Mzg+DTzrZxWJihdxoigPQRFiisyCgfiHSVtGa+XIFnksYe+w7fv+Rp7Xtxuq6GRgVpFAd0kST4zc3Luv1q801rLBz/4QXfnnXf2eL8E+PIL3gxK0KWIx5/4kQBs3LTR53mC5LBz2265+S8/47/09TsGUmdv01q9a7HTdos29SNT0/o9Wz7AZVddQ2VkksxrfOrw1iK2tyOPV1RKMVlrkf/90Hd48J//ib27ttlYeTU6UBNVpGmRJXfHcemzV175llfuuuvr2jnntlx/vVdKcc899/wiYKNUP3d7O+fe27667X2t+uRxShzA2NjYjXEcf6YQau00880UNzKxQi6+/Ap14cVvZvnkFOVaBRFP1mmzePwEO1/4GVufecrv2fWS075Q9VpF4sDkRZZ9M+12Ptvtdnd2u12x1irTg+Od9PRUrz6/URtF9FJF7AEW7/D+DUETBMFSxRRAVctlG8fx2iiKPu0leG/qVeAQZhcXvIlCb+LIR6WYQoGkOSZNpGi3JYoiKZcrpN12YYy5V2v9N977l44ePSrOOeW991prJ/6Nt0a/BPAbkqkHmD7gXtzjOObnLUsSLYiLosiHpfKGam3gA17J251lXeGdTmyOaIWIQjyUtUIj5EU2KyL3uyL7+1qtti1JEo4dO6astSilnDEGay3/IWDUL6rc/xtwuf/O7fXrzpMkiQJFHMfuzLM2cGr+VKmTpG/Sxmx0+DMLZ8edoKMg7OZJeiA0wfNp2n2iVqsdK7KEI0eOaIDp6Wl74sQJrLW9juc9WkDklwP+P1KN9wIudCIGAAAAAElFTkSuQmCC" style="height:19px;width:19px;flex:none;" alt="rebirth" class="rebirth-mode-icon"><span id="g-rebirths">-</span></div>
    </div>
        <div class="bauble"><div class="b-label" id="g-avg-label">Avg Time</div><div class="b-val" id="g-avg">-</div></div>
        <div class="bauble"><div class="b-label" id="g-fails-label">Avg Fails / Run</div><div class="b-val red" id="g-fails">-</div></div>
        <div class="bauble"><div class="b-label" id="g-best-label">Best Run</div><div class="b-val green" id="g-best">-</div></div>
        <div class="bauble"><div class="b-label" id="g-worst-label">Worst Run</div><div class="b-val red" id="g-worst">-</div></div>
    </div>
    <div id="quest-stats-sep" style="display:none;"><div style="border-top:1px dashed #4a4a5e;margin:14px 0 10px 0;"></div></div>
    <div class="baubles" id="quest-stats-row" style="display:none;">
        <div class="bauble"><div class="b-label">Quests All Time</div><div class="b-val" id="q-total">-</div></div>
        <div class="bauble"><div class="b-label">Quests Avg / Run</div><div class="b-val" id="q-avg">-</div></div>
    </div>
    <div id="chart-card">
      <div class="card-title">
        <div style="display:flex;align-items:center;gap:8px;">
        <button type="button" class="chart-sort-btn" id="chart-back-btn" style="display:none;" onclick="showRegularChart()" title="Back to run history">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        </button>
        <div class="chart-sort" id="chart-sort">
          <button type="button" class="chart-sort-btn" id="chart-sort-btn" onclick="toggleChartSort(event)" title="Sort graph">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M7 12h10"/><path d="M10 17h4"/></svg>
          </button>
          <div class="chart-sort-menu" id="chart-sort-menu" onclick="event.stopPropagation()">
            <div class="sort-head">Range</div>
            <button type="button" data-filter="all" onclick="setFilter('all')"><span class="lbl">All time<span class="hint">Every recorded run</span></span><span class="dot"></span></button>
            <button type="button" data-filter="session" onclick="setFilter('session')"><span class="lbl">This session<span class="hint">Since this bot launch</span></span><span class="dot"></span></button>
            <button type="button" data-filter="hour" onclick="setFilter('hour')"><span class="lbl">This hour<span class="hint">Last 60 minutes</span></span><span class="dot"></span></button>
            <button type="button" data-filter="today" onclick="setFilter('today')"><span class="lbl">Today<span class="hint">Since midnight</span></span><span class="dot"></span></button>
            <button type="button" data-filter="week" onclick="setFilter('week')"><span class="lbl">This week<span class="hint">Since Sunday</span></span><span class="dot"></span></button>
            <button type="button" data-filter="month" onclick="setFilter('month')"><span class="lbl">This month<span class="hint">Since the 1st</span></span><span class="dot"></span></button>
            <div class="sort-head">Type</div>
            <button type="button" data-kind="all" onclick="setRunKind('all')"><span class="lbl">All runs<span class="hint">Full + resumed</span></span><span class="dot"></span></button>
            <button type="button" data-kind="full" onclick="setRunKind('full')"><span class="lbl">Full rebirths<span class="hint">Rebirths started with zero stone</span></span><span class="dot"></span></button>
            <button type="button" data-kind="resumed" onclick="setRunKind('resumed')"><span class="lbl">Resumed<span class="hint">Started with stone already on you</span></span><span class="dot"></span></button>
          </div>
        </div>
        <span><span id="chart-title-main">Rebirth History</span> <span id="chart-title-hint" style="font-size:11px;color:#5a5a80;font-weight:400;margin-left:6px;">click a dot for run data</span></span>
        </div>
      </div>
      <div id="chart-wrap"><canvas id="run-chart"></canvas></div>
      <div id="run-detail-wrap" style="display:none;position:relative;">
        <canvas id="run-detail-chart"></canvas>
        <div id="run-detail-empty" style="display:none;padding:34px 8px;text-align:center;"></div>
      </div>
    </div>
    <hr class="mode-settings-sep">
    <div id="mode-settings" class="mode-settings">
      <div class="mode-settings-head">
        <div class="sec-label">Mode Settings</div>
        <div class="mode-settings-cats" id="mode-settings-cats"></div>
      </div>
      <div class="mode-settings-body" id="mode-settings-body"></div>
      <div class="mode-settings-foot">
        <span class="mode-settings-status" id="mode-settings-status"></span>
        <button class="btn-primary" type="button" onclick="saveModeSettings()">Save & Apply</button>
      </div>
    </div>
    </div>
    <div id="delve-main">ToDo</div>
    <div id="meteor-main">
      <div class="mode-empty-msg">This mode doesn't have anything yet.</div>
      <div id="meteor-mode-settings" class="mode-settings" style="margin-top:18px;">
        <div class="mode-settings-head">
          <div class="sec-label">Mode Settings</div>
          <div class="mode-settings-cats" id="meteor-mode-settings-cats"></div>
        </div>
        <div class="mode-settings-body" id="meteor-mode-settings-body"></div>
        <div class="mode-settings-foot">
          <span class="mode-settings-status" id="meteor-mode-settings-status"></span>
          <button class="btn-primary" type="button" onclick="saveModeSettings()">Save & Apply</button>
        </div>
      </div>
    </div>
    <div id="crater-main">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:6px;">
      <div class="sec-label">All-Time Crater Stats</div>
      <div style="display:flex;gap:6px;align-items:center;">
        <button onclick="craterResetStats()" style="padding:5px 12px;border-radius:6px;border:1px solid var(--red);background:rgba(204,68,85,.1);color:var(--red);font-weight:700;cursor:pointer;font-size:12px;">RESET STATS</button>
      </div>
    </div>
    <div class="baubles">
        <div class="bauble"><div class="b-label">Runned For</div><div class="b-val accent" id="crater-runtime">-</div></div>
        <div class="bauble"><div class="b-label">Pets Dropped</div><div class="b-val green" id="crater-pets">0</div></div>
        <div class="bauble"><div class="b-label">Pets / Hour</div><div class="b-val" id="crater-pets-per-hour">-</div></div>
    </div>
    <hr class="mode-settings-sep">
    <div id="crater-mode-settings" class="mode-settings" style="margin-top:4px;">
      <div class="mode-settings-head">
        <div class="sec-label">Mode Settings</div>
        <div class="mode-settings-cats" id="crater-mode-settings-cats"></div>
      </div>
      <div class="mode-settings-body" id="crater-mode-settings-body"></div>
      <div class="mode-settings-foot">
        <span class="mode-settings-status" id="crater-mode-settings-status"></span>
        <button class="btn-primary" type="button" onclick="saveModeSettings()">Save & Apply</button>
      </div>
    </div>
    </div>
  </div>
</div>
</div><!-- /page-run -->

<!-- BUILDER PAGE -->
<div id="page-builder" class="app-page">
  <div class="builder-page">
    <!-- Welcome screen -->
    <div id="builder-welcome">
      <div class="builder-welcome-title">Mode Builder</div>
      <div class="builder-welcome-sub">Select a mode to edit or create a new one</div>
      <div class="builder-mode-list" id="builder-mode-list">
        <div style="color:var(--muted);font-size:13px;">Loading modes...</div>
      </div>
      <button class="builder-new-btn" onclick="builderNewMode()">+ New Mode</button>
    </div>
    <!-- Editor -->
    <div id="builder-editor">
      <div class="builder-sidebar">
        <button class="builder-nav-btn active" data-view="flow" data-tooltip="Flow Graph" onclick="builderSwitchView('flow')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><line x1="6" y1="9" x2="6" y2="15"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="9" y1="18" x2="15" y2="18"/><line x1="18" y1="9" x2="18" y2="15"/></svg>
        </button>
        <button class="builder-nav-btn" data-view="dashboard" data-tooltip="Dashboard" onclick="builderSwitchView('dashboard')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
        </button>
        <button class="builder-nav-btn" data-view="toggles" data-tooltip="Toggles" onclick="builderSwitchView('toggles')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        </button>
        <hr class="builder-sidebar-sep">
        <button class="builder-nav-btn" data-view="variables" data-tooltip="Variables" onclick="builderSwitchView('variables')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </button>
        <button class="builder-nav-btn" data-view="config" data-tooltip="Config" onclick="builderSwitchView('config')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </button>
      </div>
      <div class="builder-content">
        <!-- Flow view -->
        <div class="builder-view active" id="builder-view-flow">
          <div class="builder-toolbar">
            <button class="builder-toolbar-btn" onclick="builderBackToWelcome()" style="font-size:12px;">← Modes</button>
            <span class="builder-toolbar-title" id="builder-mode-name" style="margin-left:0">Untitled Mode</span>
            <span style="font-size:11px;color:var(--muted);margin-left:12px;" id="builder-autosave-indicator">All changes saved</span>
          </div>
          <div class="flow-area">
            <div id="flow-canvas-container">
              <canvas id="flow-canvas"></canvas>
            </div>
            <div class="flow-palette">
              <div class="flow-palette-title">Flow Blocks</div>
              <div class="flow-palette-item" draggable="true" data-type="procedure">
                <span class="fpi-dot" style="background:#6a5aff"></span> Procedure
              </div>
              <div class="flow-palette-item" draggable="true" data-type="code_snippet">
                <span class="fpi-dot" style="background:#f7c46a"></span> Code Snippet
              </div>
            </div>
          </div>
        </div>
        <!-- Dashboard view -->
        <div class="builder-view" id="builder-view-dashboard">
          <div class="builder-toolbar">
            <span class="builder-toolbar-title">Dashboard Editor</span>
          </div>
          <div style="flex:1;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:14px;">
            Dashboard editor coming soon
          </div>
        </div>
        <!-- Toggles view -->
        <div class="builder-view" id="builder-view-toggles">
          <div class="builder-toolbar">
            <span class="builder-toolbar-title">Toggle Editor</span>
          </div>
          <div style="flex:1;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:14px;">
            Toggle editor coming soon
          </div>
        </div>
        <!-- Variables view -->
        <div class="builder-view" id="builder-view-variables">
          <div class="builder-toolbar">
            <span class="builder-toolbar-title">Global Variables</span>
            <span style="font-size:11px;color:var(--muted);margin-left:12px;">Runtime data accessible from procedures</span>
          </div>
          <div class="var-list" id="var-list-variables">
            <div class="var-section-title">Variables</div>
            <div class="var-hint">These are read/write from procedures. Use them for counters, state tracking, and runtime data.</div>
            <div id="var-rows-variables"></div>
            <button class="var-add-btn" onclick="varAddRow('variables')">+ Add Variable</button>
          </div>
        </div>
        <!-- Config view -->
        <div class="builder-view" id="builder-view-config">
          <div class="builder-toolbar">
            <span class="builder-toolbar-title">Config Variables</span>
            <span style="font-size:11px;color:var(--muted);margin-left:12px;">Read-only from procedures (mode settings)</span>
          </div>
          <div class="var-list" id="var-list-config">
            <div class="var-section-title">Config</div>
            <div class="var-hint">These can be read from procedures but not changed. Use them for mode settings like target area, timing thresholds, etc.</div>
            <div id="var-rows-config"></div>
            <button class="var-add-btn" onclick="varAddRow('config')">+ Add Config</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- RECORDER PAGE -->
<div id="page-recorder" class="app-page">
  <iframe id="recorder-frame" title="Recorder" src="/me/" loading="eager"></iframe>
</div>

<!-- Procedure Editor Overlay (in-page, multi-tab) -->
<div id="proc-editor-overlay">
  <div class="proc-editor-topbar" id="proc-editor-tabs"></div>
  <div class="proc-editor-body" id="proc-editor-body"></div>
</div>


<!-- CONFIG PANEL -->
<div class="side-panel" id="config-panel">
  <div class="panel-header">
      <span class="title">Config</span>
      <button onclick="togglePanel('config')">x</button>
  </div>
  <div class="cfg-tabs" id="config-tabs" hidden></div>
  <div class="panel-body" id="config-form"></div>
  <div class="panel-status" id="cfg-status"></div>
  <div class="panel-footer">
      <button class="btn-secondary" onclick="loadConfig()">Reload</button>
    <button class="btn-primary" onclick="saveConfig()">Save & Apply</button>
  </div>
</div>

<!-- CALIBRATION PANEL -->
<div class="side-panel" id="calib-panel">
  <div class="panel-header">
      <span class="title">Region Calibrator</span>
      <button id="calib-header-reset" class="calib-reset-btn" onclick="resetActiveCalibTab()" title="Reset all regions in this tab to defaults">Reset All</button>
      <button onclick="togglePanel('calib')">x</button>
  </div>
  <div class="panel-body" id="calib-body">
    <div style="font-size:12px;color:var(--muted);">Click <b>Select</b> on any region to draw it on a live screenshot. Coords are saved to config.json instantly.</div>
  </div>
  <div class="panel-status" id="calib-status"></div>
</div>

<!-- Screenshot overlay (DPI-aware) -->
<div id="ss-overlay">
  <canvas id="ss-canvas"></canvas>
    <div id="ss-hint">Drag to select region - Esc to cancel</div>
</div>

<!-- Run popup -->
<div id="run-popup-bg" onclick="closeRunPopup()"></div>
<div id="run-popup">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
    <span style="font-weight:700;font-size:15px;" id="popup-title">Run</span>
    <button onclick="closeRunPopup()" style="background:none;border:none;color:var(--muted);font-size:18px;cursor:pointer;line-height:1;">x</button>
  </div>
  <div id="popup-body" style="display:flex;flex-direction:column;gap:8px;"></div>
    <button onclick="deleteRun()" style="margin-top:16px;width:100%;padding:9px;border-radius:7px;border:1px solid var(--red);background:rgba(204,68,85,.1);color:var(--red);font-weight:700;cursor:pointer;font-size:13px;">Remove this run</button>
</div>

<script>
const MT2_CSRF_TOKEN = "__MT2_CSRF_TOKEN__";
function mt2Fetch(url, options = {}) {
  const opts = {...options};
  const method = (opts.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    opts.headers = {...(opts.headers || {}), 'X-MT2-CSRF': MT2_CSRF_TOKEN};
  }
  return fetch(url, opts);
}
function postJson(url, body) {
  return mt2Fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
}
function _escapeHtml(v){
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
function _repairMojibake(v){
  const s = String(v ?? '');
  if (!s) return s;
  if (!/[ÃƒÃ‚Ã¢â‚¬]/.test(s)) return s;
  try {
    const repaired = decodeURIComponent(escape(s));
    if (repaired && repaired !== s && !repaired.includes('\ufffd')) return repaired;
  } catch (_) {}
  return s
    .replaceAll('Ã¢â‚¬â€', '-')
    .replaceAll('Ã¢â‚¬â€œ', '-')
    .replaceAll('Ã¢â‚¬Â¦', '...')
    .replaceAll('Ã¢â‚¬"', '"')
    .replaceAll('Ã¢â‚¬"', '"')
    .replaceAll('Ã¢â‚¬Ëœ', "'")
    .replaceAll('Ã¢â‚¬â„¢', "'")
    .replaceAll('Ã‚', '')
    .replaceAll('Ãƒ', '');
}
let _floatingTooltipEl = null;
function _ensureFloatingTooltip(){
  if (_floatingTooltipEl) return _floatingTooltipEl;
  let el = document.getElementById('floating-tooltip');
  if (!el){
    el = document.createElement('div');
    el.id = 'floating-tooltip';
    document.body.appendChild(el);
  }
  _floatingTooltipEl = el;
  return el;
}
function _hideFloatingTooltip(){
  const el = _ensureFloatingTooltip();
  el.classList.remove('show');
  el.style.left = '-9999px';
  el.style.top = '-9999px';
}
function _showFloatingTooltip(anchor){
  const tipRaw = anchor?.getAttribute?.('data-tip') || '';
  const tip = _repairMojibake(tipRaw).trim();
  if (!tip) return;
  const el = _ensureFloatingTooltip();
  el.textContent = tip;
  el.style.left = '-9999px';
  el.style.top = '-9999px';
  el.classList.add('show');
  const rect = anchor.getBoundingClientRect();
  const pad = 10;
  const gap = 8;
  let x = rect.right + gap;
  let y = rect.top - 6;
  const w = el.offsetWidth || 220;
  const h = el.offsetHeight || 40;
  if (x + w > window.innerWidth - pad) x = Math.max(pad, rect.left - w - gap);
  if (y + h > window.innerHeight - pad) y = Math.max(pad, window.innerHeight - h - pad);
  if (y < pad) y = pad;
  el.style.left = `${Math.round(x)}px`;
  el.style.top = `${Math.round(y)}px`;
}
function _bindFloatingTooltips(root=document){
  const nodes = root.querySelectorAll('.tip-anchor[data-tip]');
  nodes.forEach((el) => {
    if (el.dataset.tipBound === '1') return;
    el.dataset.tipBound = '1';
    el.addEventListener('mouseenter', () => _showFloatingTooltip(el));
    el.addEventListener('focus', () => _showFloatingTooltip(el), true);
    el.addEventListener('mousemove', () => _showFloatingTooltip(el));
    el.addEventListener('mouseleave', _hideFloatingTooltip);
    el.addEventListener('blur', _hideFloatingTooltip, true);
  });
}
window.addEventListener('scroll', _hideFloatingTooltip, true);
window.addEventListener('resize', _hideFloatingTooltip);
const runChart = new Chart(document.getElementById('run-chart').getContext('2d'), {
  type: 'line',
  data: { labels: [], datasets: [{ label: 'Duration (min)', data: [], borderColor: '#7c6af7', backgroundColor: 'rgba(124,106,247,0.12)', tension: 0.35, pointRadius: 6, pointHoverRadius: 10, pointBackgroundColor: '#7c6af7', pointHoverBackgroundColor: '#f7a06a', fill: true }]},
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'nearest', intersect: true },
    onClick: (evt, elements) => { if (!elements.length) return; const idx = elements[0].index; const meta = runChart._runMeta || []; if (meta[idx]) openRunDetail(meta[idx]); },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { title: i=>{ const m=runChart._runMeta||[]; const r=m[i[0].dataIndex]; if(r&&r.start_time){const d=new Date(r.start_time*1000);return d.toLocaleDateString()+' '+d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}return i[0].label; }, label: i=>{ const d=i.raw,m=Math.floor(d),s=Math.round((d-m)*60); return ` ${m}m ${String(s).padStart(2,'0')}s`; }, afterLabel: i=>{ const meta=runChart._runMeta||[]; const m=meta[i.dataIndex]; if(!m)return''; if(_chartMode==='delve'||_chartMode==='kraken'||_chartMode==='zytos') return ` Reason: ${m.reason||'-'}`; return ` ${m.step_count??0} steps · ${m.error_count??0} errors`; } }, backgroundColor:'#1e1e28',borderColor:'#2a2a35',borderWidth:1,titleColor:'#e0e0e8',bodyColor:'#a0a0c0',padding:12 }
    },
    scales: { x:{ticks:{color:'#9a9ab0', font:{size:11}},grid:{color:'#1e1e28'}}, y:{ticks:{color:'#9a9ab0', font:{size:11}},grid:{color:'#1e1e28'},title:{display:true,text:'Minutes',color:'#b0b0c4',font:{size:12, weight:'700'}}} }
  }
});
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â

// Crater session history chart removed (keeping info baubles only)

let _popupRunNumber = null;
let _chartMode = 'rebirth';
// ─────────── Per-run data view (per-action timeline) ───────────
let _runDetailOpen=false, _detailChart=null;
const RUN_DETAIL_KINDS={
  nav:    {color:'#7c6af7', label:'Main (travel)'},
  main:   {color:'#9a6bf0', label:'Actions'},
  rock:   {color:'#b36bf0', label:'Stage Rocks'},
  manual: {color:'#c96fc6', label:'Manual Strength'},
  fail:   {color:'#e8a04a', label:'Failures / Redo'},
};
function fmtDetailAxis(v){
  if(!isFinite(v)||v<0) v=0;
  if(v<60) return Math.round(v)+'s';
  const m=Math.floor(v/60), s=Math.round(v%60);
  return m+'m '+String(s).padStart(2,'0')+'s';
}
async function openRunDetail(run){
  _runDetailOpen=true;
  document.getElementById('chart-wrap').style.display='none';
  document.getElementById('run-detail-wrap').style.display='';
  document.getElementById('chart-back-btn').style.display='';
  const hint=document.getElementById('chart-title-hint');
  if(hint) hint.style.display='none';
  document.getElementById('chart-title-main').textContent='#'+(run.run_number??'?')+' RUN DATA';
  const sb=document.getElementById('chart-sort');
  if(sb) sb.classList.remove('open');   // close via class, NEVER inline display
  renderRunDetail(run, null);   // loading state
  let d=null;
  try{
    const ctrl=new AbortController();
    const to=setTimeout(()=>ctrl.abort(), 8000);
    const r=await fetch('/run_detail?run='+encodeURIComponent(run.run_number??0)+'&start='+encodeURIComponent(run.start_time||0), {signal:ctrl.signal});
    clearTimeout(to);
    if(r.ok){
      d=await r.json();
    } else {
      d={ok:false, message:'server error ('+r.status+')'};
    }
  }catch(e){
    d={ok:false, message:'request failed'};
  }
  if(!_runDetailOpen) return;
  renderRunDetail(run, d);
}
function showRegularChart(){
  _runDetailOpen=false;
  document.getElementById('run-detail-wrap').style.display='none';
  document.getElementById('chart-wrap').style.display='';
  document.getElementById('chart-back-btn').style.display='none';
  const hint=document.getElementById('chart-title-hint');
  if(hint) hint.style.display='';
  const t=document.getElementById('chart-title-main');
  if(t){
    const m=(_lastPollState&&_lastPollState.bot_mode)||'rebirth';
    t.textContent=(m==='delve')?'Delve Boss Time History':(m==='kraken')?'Kraken Fight History':(m==='zytos')?'Zytos Fight History':'Rebirth History';
  }
  poll();
}
let _detailVizRun=null, _detailVizD=null;
let _rdResizeT=null;
window.addEventListener('resize', ()=>{
  if(!_runDetailOpen || !_detailVizRun) return;
  clearTimeout(_rdResizeT);
  _rdResizeT=setTimeout(()=>{ if(_runDetailOpen && _detailVizRun) renderRunDetail(_detailVizRun, _detailVizD); }, 180);
});
function _detailClean(n){ return String(n||'').replace(/_/g,' '); }
function _detailEsc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
function renderRunDetail(run, d){
  const wrap=document.getElementById('run-detail-wrap');
  const canvas=document.getElementById('run-detail-chart');
  const empty=document.getElementById('run-detail-empty');
  if(_detailChart){ _detailChart.destroy(); _detailChart=null; }
  const segs=(d && d.ok && Array.isArray(d.segments)) ? d.segments.slice() : null;
  if(!segs || !segs.length){
    canvas.style.display='none'; empty.style.display='';
    wrap.style.height='220px';
    const dur=run.duration_secs||0;
    empty.innerHTML = (d===null)
      ? '<span style="color:#5a5a80;font-size:13px;font-weight:600;">Loading run data…</span>'
      : '<div style="color:#5a5a80;font-size:13px;font-weight:600;">No recorded per-action data for this run</div>'+
        '<div style="margin-top:6px;font-size:12px;color:#7a7aa0;">Duration '+fmtTime(dur)+' · Errors '+(run.error_count??'-')+' · Steps '+(run.step_count??'-')+(Number(run.quests_completed||0)>0?' · Quests '+(run.quests_completed||0):'')+'</div>'+
        (d.message?'<div style="margin-top:4px;font-size:11px;color:#5a5a80;">'+String(d.message)+'</div>':'');
    return;
  }
  _detailVizRun=run; _detailVizD=d;
  canvas.style.display='none'; empty.style.display='none';
  segs.sort((a,b)=>(a.s-b.s)||(a.e-b.e));
  const dur=Math.max(1, run.duration_secs||0, d.duration||0, segs[segs.length-1].e||0);
  let viz=document.getElementById('run-detail-viz');
  if(!viz){ viz=document.createElement('div'); viz.id='run-detail-viz'; wrap.appendChild(viz); }

  // ---- connected single-track timeline (SVG) ----
  const W=Math.max(560, (wrap.clientWidth||1072)-2);
  const H=216, pad=14;
  const x=t=>pad+(Math.max(0,Math.min(dur,t))/dur)*(W-2*pad);
  const bandY=78, bandH=40, bandB=bandY+bandH;
  const lanes=[{y:18,d:-1},{y:38,d:-1},{y:58,d:-1},{y:148,d:1},{y:168,d:1},{y:188,d:1}];
  const laneRight=lanes.map(()=>0);

  let svg='<svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" style="display:block;">';
  // base track: the idle/underline that makes every block read as one connected line
  svg+='<rect x="'+(pad-4)+'" y="'+bandY+'" width="'+(W-2*pad+8)+'" height="'+bandH+'" rx="5" fill="#1d1d26" stroke="#2a2a35" stroke-width="1"><title>Idle / waiting — gaps between actions. Hover any colored block for details.</title></rect>';

  let blocks='', labels='';
  segs.forEach(s=>{
    const k=RUN_DETAIL_KINDS[s.kind]||RUN_DETAIL_KINDS.main;
    const x1=x(s.s), x2=x(Math.max(s.e, s.s+0.05));
    const bw=Math.max(3, x2-x1), cx=x1+bw/2;
    const tip=_detailEsc(_detailClean(s.label))+' — '+(s.e-s.s).toFixed(1)+'s ('+fmtDetailAxis(s.s)+' → '+fmtDetailAxis(s.e)+')'+(s.err?' · '+_detailEsc(s.err):'');
    blocks+='<rect x="'+x1.toFixed(1)+'" y="'+(bandY+2)+'" width="'+bw.toFixed(1)+'" height="'+(bandH-4)+'" rx="3" fill="'+k.color+'"><title>'+tip+'</title></rect>';
    const txt=_detailClean(s.label);
    const lw=txt.length*6.4+12;
    const lx=Math.min(Math.max(cx, pad+lw/2), W-pad-lw/2);
    for(let li=0; li<lanes.length; li++){
      if(lx-lw/2 >= laneRight[li]-4){
        laneRight[li]=lx+lw/2+4;
        const ln=lanes[li], ly=ln.y;
        const conny = ln.d<0 ? bandY-2 : bandB+2;
        const connl = ln.d<0 ? ly+5 : ly-13;
        labels+='<line x1="'+cx.toFixed(1)+'" y1="'+connl+'" x2="'+cx.toFixed(1)+'" y2="'+conny+'" stroke="#4a4a5e" stroke-width="1"/>';
        labels+='<text x="'+lx.toFixed(1)+'" y="'+ly+'" fill="#cfcce8" font-size="11" font-weight="600" text-anchor="middle">'+_detailEsc(txt)+'</text>';
        break;
      }
    }
  });

  // time axis
  const steps=[1,2,5,10,15,30,60,120,300,600,1200,1800];
  const step=steps.find(st=>dur/st<=10)||1800;
  for(let t=0;t<=dur+0.0001;t+=step){
    const tx=x(t).toFixed(1);
    svg+='<line x1="'+tx+'" y1="'+(bandB+2)+'" x2="'+tx+'" y2="'+(H-20)+'" stroke="rgba(124,106,247,.10)" stroke-width="1"/>';
    svg+='<text x="'+tx+'" y="'+(H-5)+'" fill="#7a7aa0" font-size="10" font-weight="600" text-anchor="middle">'+fmtDetailAxis(t)+'</text>';
  }
  svg+=blocks+labels+'</svg>';

  // ---- kind chips ----
  const kindsPresent=[...new Set(segs.map(s=>s.kind))].filter(k=>RUN_DETAIL_KINDS[k]);
  const chips=kindsPresent.map(k=>'<span class="rdl-chip"><span style="background:'+RUN_DETAIL_KINDS[k].color+'"></span>'+RUN_DETAIL_KINDS[k].label+'</span>').join('');

  // ---- readable action list (chronological) ----
  const rows=segs.map(s=>{
    const k=RUN_DETAIL_KINDS[s.kind]||RUN_DETAIL_KINDS.main;
    return '<div class="rdl-row"><span class="rdl-dot" style="background:'+k.color+'"></span>'+
      '<span class="rdl-name" title="'+_detailEsc(_detailClean(s.label))+'">'+_detailEsc(_detailClean(s.label))+'</span>'+
      '<span class="rdl-t">'+fmtDetailAxis(s.s)+' → '+fmtDetailAxis(s.e)+'</span>'+
      '<span class="rdl-d">'+(s.e-s.s).toFixed(1)+'s</span></div>';
  }).join('');
  const listH=Math.min(168, Math.ceil(segs.length/2)*26+10);
  wrap.style.height=(H+listH+78)+'px';
  const cap='<div style="display:flex;align-items:center;gap:14px;margin:2px 2px 6px;">'+
    '<span style="font-size:10px;font-weight:700;color:#5a5a80;text-transform:uppercase;letter-spacing:.7px;">Action timeline — full run on one connected line · hover blocks for details</span></div>';
  viz.innerHTML=cap+svg+'<div style="margin-top:8px;">'+chips+'</div><div class="rdl" style="max-height:'+listH+'px;">'+rows+'</div>';
}

function showRunPopup(run) {
  _popupRunNumber = run.run_number;
  const runLabel = run.start_time ? new Date(run.start_time*1000).toLocaleString([],{dateStyle:'short',timeStyle:'short'}) : `Run #${run.run_number}`;
  document.getElementById('popup-title').textContent = runLabel;
  const dur=run.duration_secs||0,m=Math.floor(dur/60),s=Math.floor(dur%60);
  const rows=[['Duration',`${m}m ${String(s).padStart(2,'0')}s`]];
  if (_chartMode === 'delve' || _chartMode === 'kraken' || _chartMode === 'zytos') {
    rows.push(['Reason', run.reason || '-']);
  } else {
    rows.push(['Errors',run.error_count??'-'],['Steps',run.step_count??'-']);
    rows.push(['Type', isFullRun(run)?'Full':'Resumed']);
    const qc=Number(run&&run.quests_completed||0);
    if(qc>0) rows.push(['Quests Done', String(qc)]);
  }
  document.getElementById('popup-body').innerHTML=rows.map(([k,v])=>`<div style="display:flex;justify-content:space-between;gap:24px;"><span style="color:#5a5a80;">${k}</span><span style="color:#e0e0e8;font-weight:600;">${v}</span></div>`).join('');
  document.getElementById('run-popup').style.display='block';
  document.getElementById('run-popup-bg').style.display='block';
}
function closeRunPopup() { document.getElementById('run-popup').style.display='none'; document.getElementById('run-popup-bg').style.display='none'; _popupRunNumber=null; }
function refreshRunHistorySoon() {
  _lastHistKey = null;
  setTimeout(() => { poll(); }, 350);
}
function deleteRun() {
  if(_popupRunNumber==null)return;
  post('delete_run',{run_number:_popupRunNumber, mode:_chartMode});
  closeRunPopup();
  refreshRunHistorySoon();
}
function fmtTime(s) { if(!s||s<=0)return'-'; const m=Math.floor(s/60),sec=Math.floor(s%60); if(m>=60){const h=Math.floor(m/60);return`${h}h${String(m%60).padStart(2,'0')}m${String(sec).padStart(2,'0')}s`;} return`${m}m${String(sec).padStart(2,'0')}s`; }

const BOT_MODE_VALUES = ['rebirth', 'delve', 'kraken', 'zytos', 'crater', 'farm_meteor'];
const RUN_MODE_VALUES = [
  'a5meteor',
  'a5s4', 'a5s3', 'a5s2', 'a5s1',
  'a4s4', 'a4s3', 'a4s2', 'a4s1',
  'a3s4', 'a3s3', 'a3s2', 'a3s1',
  'a2s4', 'a2s3', 'a2s2', 'a2s1',
  'a1s4', 'a1s3', 'a1s2', 'a1s1',
];
const LEGACY_RUN_MODE_MAP = {
  meteor: 'a5meteor',
  a6s4: 'a5meteor',
  a6s3: 'a5meteor',
  a6s2: 'a5meteor',
  a6s1: 'a5meteor',
  stage4: 'a5s4',
  stage3: 'a5s3',
  stage2: 'a5s2',
  full: 'a1s1',
};
function normalizeRunModeClient(mode) {
  const raw = String(mode || '').trim().toLowerCase();
  const mapped = LEGACY_RUN_MODE_MAP[raw] || raw;
  return RUN_MODE_VALUES.includes(mapped) ? mapped : 'a1s1';
}
function ensureModeSelectors() {
  const botSel = document.getElementById('bot-mode-select');
  if (botSel && botSel.dataset.ready !== '1') {
    const keep = String(botSel.value || '').trim().toLowerCase();
    botSel.innerHTML = [
      '<option value="" disabled>- MODE -</option>',
      '<option value="rebirth">Rebirth</option>',
      '<option value="" disabled>- BOSS -</option>',
      '<option value="delve">Delve</option>',
      '<option value="kraken">Kraken</option>',
      '<option value="zytos">Zytos</option>',
      '<option value="" disabled>- FARM -</option>',
      '<option value="crater">Crater</option>',
      '<option value="farm_meteor">Meteor</option>',
    ].join('');
    botSel.value = BOT_MODE_VALUES.includes(keep) ? keep : 'rebirth';
    botSel.dataset.ready = '1';
  }
  const runSel = document.getElementById('run-mode-select');
  if (runSel && runSel.dataset.ready !== '1') {
    const keep = normalizeRunModeClient(runSel.value);
    runSel.innerHTML = [
      '<option value="" disabled>- RUN MODES -</option>',
      '<option value="" disabled>- AREA 5 -</option>',
      '<option value="a5meteor">Area 5 - Meteor</option>',
      '<option value="a5s4">Area 5 - Stage 4</option>',
      '<option value="a5s3">Area 5 - Stage 3</option>',
      '<option value="a5s2">Area 5 - Stage 2</option>',
      '<option value="a5s1">Area 5 - Stage 1</option>',
      '<option value="" disabled>- AREA 4 -</option>',
      '<option value="a4s4">Area 4 - Stage 4</option>',
      '<option value="a4s3">Area 4 - Stage 3</option>',
      '<option value="a4s2">Area 4 - Stage 2</option>',
      '<option value="a4s1">Area 4 - Stage 1</option>',
      '<option value="" disabled>- AREA 3 -</option>',
      '<option value="a3s4">Area 3 - Stage 4</option>',
      '<option value="a3s3">Area 3 - Stage 3</option>',
      '<option value="a3s2">Area 3 - Stage 2</option>',
      '<option value="a3s1">Area 3 - Stage 1</option>',
      '<option value="" disabled>- AREA 2 -</option>',
      '<option value="a2s4">Area 2 - Stage 4</option>',
      '<option value="a2s3">Area 2 - Stage 3</option>',
      '<option value="a2s2">Area 2 - Stage 2</option>',
      '<option value="a2s1">Area 2 - Stage 1</option>',
      '<option value="" disabled>- AREA 1 -</option>',
      '<option value="a1s4">Area 1 - Stage 4</option>',
      '<option value="a1s3">Area 1 - Stage 3</option>',
      '<option value="a1s2">Area 1 - Stage 2</option>',
      '<option value="a1s1">Area 1 - Stage 1</option>',
    ].join('');
    runSel.disabled = false;
    runSel.value = keep;
    runSel.dataset.ready = '1';
  }
}

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// PANEL MANAGEMENT
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
const PANELS = { config:'config-panel' };
const BTNS   = { config:'btn-config' };
let _openPanel = null;
function togglePanel(name) {
  if (!PANELS[name] || !BTNS[name]) return;
  const btn = document.getElementById(BTNS[name]);
  if (btn && (btn.disabled || btn.classList.contains('wip'))) return;
  if (_openPanel === name) {
    document.getElementById(PANELS[name]).classList.remove('open');
    document.getElementById(BTNS[name]).classList.remove('active');
    _openPanel = null;
    document.body.classList.remove('config-open');
    if (typeof syncLiveFab === 'function') syncLiveFab();
    return;
  }
  Object.keys(PANELS).forEach(k => {
    document.getElementById(PANELS[k]).classList.remove('open');
    document.getElementById(BTNS[k]).classList.remove('active');
  });
  _openPanel = name;
  document.getElementById(PANELS[name]).classList.add('open');
  document.getElementById(BTNS[name]).classList.add('active');
  if (name === 'config') {
    loadConfig();
    toggleLiveChat(false);
    document.body.classList.add('config-open');
  } else {
    document.body.classList.remove('config-open');
  }
  if (typeof syncLiveFab === 'function') syncLiveFab();
}

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// LEFT SIDEBAR
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
let _sidebarCollapsed = false;
function toggleSidebar() {
  _sidebarCollapsed = !_sidebarCollapsed;
  const sb = document.getElementById('left-sidebar');
  const lbl = sb.querySelector('#sb-toggle-btn .sb-label');
  if (_sidebarCollapsed) {
    sb.classList.add('collapsed');
    if (lbl) lbl.textContent = 'Show panel';
  } else {
    sb.classList.remove('collapsed');
    if (lbl) lbl.textContent = 'Hide panel';
  }
}
// Sidebar button visual active state (toggles accent highlight when ON)
function _sbSetActive(btnId, active) {
  if (!btnId) return;
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (active) {
    btn.style.color = 'var(--accent)';
    btn.style.background = 'rgba(124,106,247,.14)';
  } else {
    btn.style.color = '';
    btn.style.background = '';
  }
}
function _syncSidebarToggle(checkId, btnId, value) {
  const chk = document.getElementById(checkId);
  if (!chk) return;
  const active = !!value;
  chk.checked = active;
  _sbSetActive(btnId, active);
}
function _setSidebarDisabled(checkId, btnId, disabled, reason='') {
  const chk = document.getElementById(checkId);
  const btn = document.getElementById(btnId);
  if (chk) chk.disabled = !!disabled;
  if (!btn) return;
  if (!btn.dataset.defaultTitle) btn.dataset.defaultTitle = btn.getAttribute('title') || '';
  btn.classList.toggle('disabled', !!disabled);
  if (disabled) {
    btn.setAttribute('title', reason || btn.dataset.defaultTitle || 'Unavailable');
  } else {
    btn.setAttribute('title', btn.dataset.defaultTitle || '');
  }
}
function sbToggleUnlockDrills(val) {
  const chk = document.getElementById('unlock-drills-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setUnlockDrills(chk.checked);
  _sbSetActive('sb-unlock-drills-btn', chk.checked);
}
function sbToggleActivateDrills(val) {
  const chk = document.getElementById('activate-drills-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setActivateDrills(chk.checked);
  _sbSetActive('sb-activate-drills-btn', chk.checked);
}
function sbToggleAutoStrength(val) {
  const chk = document.getElementById('auto-strength-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setAutoStrength(chk.checked);
}
function sbToggleBossFightA1(val) {
  const chk = document.getElementById('boss-fight-a1-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setBossFightA1(chk.checked);
  _sbSetActive('sb-boss-fight-a1-btn', chk.checked);
}
function sbToggleDailyQuests(val) {
  const chk = document.getElementById('daily-quests-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setDailyQuests(chk.checked);
  _sbSetActive('sb-daily-quests-btn', chk.checked);
}
function setDailyQuests(val) {
  _markPending('daily_quests', val);
  postJson('/action', {action:'set_daily_quests', value:val});
}
function sbToggleForceRestart(val) {
  const chk = document.getElementById('force-restart-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setForceRestart(chk.checked);
  _sbSetActive('sb-force-restart-btn', chk.checked);
}
function setAutoStrength(val) {
  _markPending('auto_strength', val);
  postJson('/action', {action:'set_auto_strength', value:val});
}
function setBossFightA1(val) {
  _markPending('boss_fight_a1', val);
  postJson('/action', {action:'set_boss_fight_a1', value:val});
}
function setForceRestart(val) {
  _markPending('force_restart', val);
  postJson('/action', {action:'set_force_restart', value:val});
}
function sbTogglePauseOnLag(val) {
  const chk = document.getElementById('pause-on-lag-check');
  if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked;
  setPauseOnLag(chk.checked);
  _sbSetActive('sb-pause-on-lag-btn', chk.checked);
}
function setPauseOnLag(val) {
  _markPending('pause_on_lag', val);
  postJson('/action', {action:'set_pause_on_lag', value:val});
}
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Prevent panel-body scroll-jitter while dragging a range slider ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
(function() {
  let _sliderActive = false;
  document.addEventListener('mousedown', function(e) {
    if (e.target && e.target.classList && e.target.classList.contains('cfg-slider')) {
      _sliderActive = true;
      document.body.style.userSelect = 'none';
      // freeze scroll on the panel-body ancestor
      let el = e.target.parentElement;
      while (el) {
        if (el.classList && el.classList.contains('panel-body')) {
          el.style.overflowY = 'hidden';
          el._sliderLocked = true;
          break;
        }
        el = el.parentElement;
      }
    }
  }, true);
  function _sliderRelease() {
    if (!_sliderActive) return;
    _sliderActive = false;
    document.body.style.userSelect = '';
    document.querySelectorAll('.panel-body').forEach(function(el) {
      if (el._sliderLocked) { el.style.overflowY = ''; el._sliderLocked = false; }
    });
  }
  document.addEventListener('mouseup',    _sliderRelease, true);
  document.addEventListener('touchend',   _sliderRelease, true);
  document.addEventListener('touchcancel',_sliderRelease, true);
})();

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// BOT CONTROLS
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
let _lastHistLen=-1, _pollFails=0, _botRunning=false;
const _pendingUi = {};
function _markPending(key, value, ms=1800) {
  _pendingUi[key] = { value, until: Date.now() + ms };
}
function _pendingValue(key) {
  const p = _pendingUi[key];
  if (!p) return null;
  if (Date.now() > p.until) { delete _pendingUi[key]; return null; }
  return p.value;
}
function post(action, extra) { return postJson('/action', {action,...extra}); }
function _cfgLoadoutVal(key) {
  const el = document.getElementById('cfg_'+key);
  if (el && el.value != null && String(el.value).trim() !== '') return String(el.value).trim().toLowerCase();
  return String((_cfgValues||{})[key] || 'none').trim().toLowerCase() || 'none';
}
function requiredLoadoutsMissing() {
  const mode = String((_lastPollState && _lastPollState.bot_mode) || 'rebirth').toLowerCase();
  const fighting = _cfgLoadoutVal('BOSS_FIGHT_A1_LOADOUT_FIGHTING');
  const farming  = _cfgLoadoutVal('BOSS_FIGHT_A1_LOADOUT_FARMING');
  const meteorRw = _cfgLoadoutVal('CRATER_LOADOUT_METEOR_REWARDS');
  const meteorFarm = _cfgLoadoutVal('FARM_METEOR_LOADOUT');
  const missing = [];
  if (mode === 'kraken' || mode === 'zytos' || mode === 'delve') {
    if (fighting === 'none') missing.push('Fighting');
    return missing;
  }
  if (mode === 'farm_meteor') {
    if (meteorRw === 'none' && meteorFarm === 'none') missing.push('Meteor Rewards');
    return missing;
  }
  if (mode === 'crater') {
    if (meteorRw === 'none') missing.push('Meteor Rewards');
    return missing;
  }
  const bf = !!( _lastPollState && _lastPollState.boss_fight_a1 );
  if (farming === 'none') missing.push('Farming');
  if (bf && fighting === 'none') missing.push('Fighting');
  return missing;
}
function showLoadoutBlock(missing) {
  const ul = document.getElementById('lo-block-list');
  if (ul) ul.innerHTML = (missing||[]).map(n => '<li>'+_escapeHtml(n)+'</li>').join('');
  const bg = document.getElementById('modal-loadout-block');
  if (bg) bg.classList.add('open');
}
let _loadoutBlockAckSeq = 0;
function closeLoadoutBlock() {
  const bg = document.getElementById('modal-loadout-block');
  if (bg) bg.classList.remove('open');
  _loadoutBlockAckSeq = Number((_lastPollState && _lastPollState.loadout_block_seq) || 0);
}
// ── Game Detection: block widget + F2 pipette picker (MacroForge flow) ─────
let _gameDetectBlockAckSeq = 0;
function showGameDetectBlock() {
  const bg = document.getElementById('modal-gamedetect-block');
  if (bg) bg.classList.add('open');
}
function closeGameDetectBlock() {
  const bg = document.getElementById('modal-gamedetect-block');
  if (bg) bg.classList.remove('open');
  _gameDetectBlockAckSeq = Number((_lastPollState && _lastPollState.game_detect_block_seq) || 0);
}
async function takeMeToGameDetect() {
  closeGameDetectBlock();
  try { await switchAppTab('run'); } catch (e) {}
  const panel = document.getElementById('config-panel');
  const wasOpen = !!(panel && panel.classList.contains('open'));
  if (!wasOpen) togglePanel('config');   // opens the global config + loads it
  _cfgActiveTab = 'forcerestart';       // renderConfigForm keeps this tab
  setTimeout(function () { setConfigTab('forcerestart'); }, wasOpen ? 0 : 350);
  showToast('Config → Force Restart → Game Detection');
}
function gameDetectPickImage() {
  dashPickBox(function (box) {
    if (!box) return;
    postJson('/game_detect/crop', {box: box}).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { showToast(d.error || 'Crop failed'); return; }
      const name = d.path || 'game_detect.png';
      const img = document.getElementById('gd_preview');
      if (img) { img.src = '/game_detect/preview?v=' + Date.now(); img.style.visibility = 'visible'; }
      const nm = document.getElementById('gd_name');
      if (nm) nm.textContent = name;
      const hid = document.getElementById('cfg_GAME_DETECT_IMAGE');
      if (hid) hid.value = name;
      _cfgValues.GAME_DETECT_IMAGE = name;
      _cfgValues.GAME_DETECT_BOX = (d.meta && d.meta.box) || box.slice();
      _cfgValues.GAME_DETECT_SCREEN = (d.meta && d.meta.screen) || [];
      const pickBtn = document.getElementById('gd_pick_btn');
      if (pickBtn && pickBtn.textContent.trim() === 'Pick') pickBtn.textContent = 'Change';
      if (!document.getElementById('gd_clear_btn') && pickBtn) {
        const clr = document.createElement('button');
        clr.type = 'button'; clr.id = 'gd_clear_btn';
        clr.setAttribute('style', pickBtn.getAttribute('style'));
        clr.textContent = 'Clear';
        clr.onclick = gameDetectClearImage;
        pickBtn.insertAdjacentElement('afterend', clr);
      }
      _lastPollState = Object.assign({}, _lastPollState || {}, {game_detect_set: true});
      showToast('Picked ' + name + ' \u2014 box + point saved');
    }).catch(function () { showToast('Server unreachable'); });
  });
}
function gameLogoPickImage() {
  dashPickBox(function (box) {
    if (!box) return;
    postJson('/game_detect/crop', {box: box, tmpl: 'game_logo'}).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { showToast(d.error || 'Crop failed'); return; }
      const name = d.path || 'game_logo.png';
      const img = document.getElementById('glogo_preview');
      if (img) { img.src = '/game_detect/preview?tmpl=game_logo&v=' + Date.now(); img.style.visibility = 'visible'; }
      const nm = document.getElementById('glogo_name');
      if (nm) nm.textContent = name;
      const hid = document.getElementById('cfg_FORCE_GAME_LOGO_IMAGE');
      if (hid) hid.value = name;
      _cfgValues.FORCE_GAME_LOGO_IMAGE = name;
      _cfgValues.FORCE_GAME_LOGO_BOX = (d.meta && d.meta.box) || box.slice();
      _cfgValues.FORCE_GAME_LOGO_SCREEN = (d.meta && d.meta.screen) || [];
      _lastPollState = Object.assign({}, _lastPollState || {}, {game_logo_set: true});
      showToast('Picked ' + name + ' — box + point saved');
      renderModeSettings();
    }).catch(function () { showToast('Server unreachable'); });
  });
}
function gameLogoClearImage() {
  postJson('/game_detect/clear', {tmpl: 'game_logo'}).then(function (r) { return r.json(); }).then(function (d) {
    if (!d.ok) { showToast(d.error || 'Clear failed'); return; }
    _cfgValues.FORCE_GAME_LOGO_IMAGE = '';
    _cfgValues.FORCE_GAME_LOGO_BOX = [];
    _cfgValues.FORCE_GAME_LOGO_SCREEN = [];
    _lastPollState = Object.assign({}, _lastPollState || {}, {game_logo_set: false});
    renderModeSettings();
    showToast('Game logo image cleared');
  }).catch(function () { showToast('Server unreachable'); });
}
function gameDetectClearImage() {
  postJson('/game_detect/clear', {}).then(function (r) { return r.json(); }).then(function (d) {
    if (!d.ok) { showToast(d.error || 'Clear failed'); return; }
    _cfgValues.GAME_DETECT_IMAGE = '';
    _cfgValues.GAME_DETECT_BOX = [];
    _cfgValues.GAME_DETECT_SCREEN = [];
    _lastPollState = Object.assign({}, _lastPollState || {}, {game_detect_set: false});
    renderModeSettings();
    showToast('In-Game image detection cleared');
  }).catch(function () { showToast('Server unreachable'); });
}

// ── Dashboard-side screen box picker: F2 screenshot → drag a rectangle ────
// 1:1 with MacroForge's dashPickBox — same endpoints, same flow, same look.
// Returns [x1, y1, x2, y2] (real screenshot pixels) via the callback, or
// null when cancelled.
let _dashPicker = null;
function _dashPickerClose(cancelServer) {
  if (!_dashPicker) return;
  var st = _dashPicker;
  _dashPicker = null;
  try { clearInterval(st.timer); } catch (e) {}
  try { window.removeEventListener('resize', st.fit); } catch (e) {}
  try { document.removeEventListener('keydown', st.keys); } catch (e) {}
  try { st.root.remove(); if (st.overlay) st.overlay.remove(); } catch (e) {}
  if (cancelServer !== false) { try { postJson('/blockly/picker/cancel', {}); } catch (e) {} }
}
function _dashPickerStatus(el, text) {
  if (!el) return;
  el.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);margin-right:8px;animation:mfpulse 1s infinite"></span>' + text;
}
function dashPickBox(onDone) {
  if (_dashPicker) { _dashPickerClose(true); }
  var root = document.createElement('div');
  root.style.cssText = 'position:fixed;inset:0;background:rgba(12,12,16,.62);z-index:12000;display:flex;align-items:center;justify-content:center';
  root.innerHTML =
    '<div style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:22px 26px;max-width:560px;color:var(--text);box-shadow:0 18px 44px rgba(0,0,0,.55)">'
    + '<div style="font:700 15px \'Segoe UI\',sans-serif;margin-bottom:10px">Pick a box from the screen</div>'
    + '<ol style="margin:0 0 12px 20px;font:13px \'Segoe UI\',sans-serif;line-height:1.55;color:var(--text)">'
    + '<li>Open the game <b>the way the bot will see it</b> — fullscreen, or the exact window size you play at.</li>'
    + '<li>Press <b>F2</b> there. It works only while this popup is open — a screenshot is taken instantly.</li>'
    + '<li>The screenshot opens fullscreen here. Drag a rectangle around what you want, then <b>Accept</b>.</li>'
    + '</ol>'
    + '<div id="dash-pick-status" style="font:12.5px \'Segoe UI\',sans-serif;color:var(--muted);margin-bottom:14px"></div>'
    + '<button type="button" id="dash-pick-cancel" style="background:var(--panel);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:8px 16px;font:13px \'Segoe UI\',sans-serif;cursor:pointer">Cancel</button>'
    + '</div>';
  document.body.appendChild(root);
  var st = { root: root, overlay: null, timer: null, map: null, box: null, fit: null, keys: null };
  _dashPicker = st;
  var statusEl = root.querySelector('#dash-pick-status');
  _dashPickerStatus(statusEl, 'Arming F2 …');
  root.querySelector('#dash-pick-cancel').addEventListener('click', function () { _dashPickerClose(true); onDone(null); });
  root.addEventListener('mousedown', function (e) { if (e.target === root) { _dashPickerClose(true); onDone(null); } });
  st.keys = function (e) {
    if (e.key === 'Escape') { _dashPickerClose(true); onDone(null); }
  };
  document.addEventListener('keydown', st.keys);
  postJson('/blockly/picker/prepare', { mode: 'box' }).then(function (r) { return r.json(); }).then(function (d) {
    if (!_dashPicker) return;
    if (!d.ok) { _dashPickerStatus(statusEl, 'Error: ' + (d.error || 'could not arm F2')); return; }
    _dashPickerStatus(statusEl, 'Waiting for F2 — press it in your game');
  }).catch(function () { if (_dashPicker) _dashPickerStatus(statusEl, 'Server unreachable'); });

  st.timer = setInterval(function () {
    if (!_dashPicker) return;
    fetch('/blockly/picker/status').then(function (r) { return r.json(); }).then(function (d) {
      if (!_dashPicker) return;
      if (d.state === 'armed') _dashPickerStatus(statusEl, 'Waiting for F2 — press it in your game');
      else if (d.state === 'capturing') _dashPickerStatus(statusEl, 'Taking screenshot …');
      else if (d.state === 'captured' && d.has_shot) {
        clearInterval(st.timer);
        _dashPickerOpenShot('/blockly/picker/shot?v=' + Date.now(), d.screen || null, onDone);
      } else if (d.state === 'error') {
        showToast('Picker error: ' + (d.error || 'unknown'));
        _dashPickerClose(true); onDone(null);
      }
    }).catch(function () {});
  }, 350);
}
function _dashPickerOpenShot(shotUrl, screenInfo, onDone) {
  var st = _dashPicker;
  if (!st) return;
  st.root.remove();
  var ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;inset:0;background:#0a0a0e;z-index:12001';
  ov.innerHTML =
    '<img id="dash-shot-img" alt="screenshot" style="position:absolute;user-select:none;cursor:crosshair">'
    + '<div id="dash-shot-sel" style="position:absolute;display:none;border:2px solid #7c6af7;background:rgba(124,106,247,.18);pointer-events:none"></div>'
    + '<div id="dash-shot-bar" style="position:fixed;left:0;right:0;bottom:0;height:44px;display:flex;align-items:center;gap:18px;padding:0 16px;background:#12121a;border-top:1px solid #262633;color:#e0e0e8;font:12.5px \'Segoe UI\',sans-serif;justify-content:center;z-index:12002">'
    + '<span>Drag a rectangle' + (screenInfo ? ' · ' + screenInfo[0] + '×' + screenInfo[1] : '') + '</span>'
    + '<span id="dash-shot-coords" style="min-width:150px;color:#9a9ab0"></span>'
    + '<button type="button" id="dash-shot-ok" style="background:#7c6af7;border:none;border-radius:7px;color:#fff;padding:7px 18px;font:12.5px \'Segoe UI\',sans-serif;cursor:pointer">Accept</button>'
    + '<button type="button" id="dash-shot-cancel" style="background:#262633;border:1px solid #262633;color:#e0e0e8;border-radius:7px;padding:7px 14px;font:12.5px \'Segoe UI\',sans-serif;cursor:pointer">Cancel</button>'
    + '</div>';
  document.body.appendChild(ov);
  st.overlay = ov;
  var img = ov.querySelector('#dash-shot-img');
  var sel = ov.querySelector('#dash-shot-sel');
  var coords = ov.querySelector('#dash-shot-coords');
  var box = null;
  function fit() {
    var w = img.naturalWidth, h = img.naturalHeight;
    if (!w || !h) return;
    var availW = window.innerWidth, availH = window.innerHeight - 44;
    var scale = Math.min(availW / w, availH / h, 1);
    img.style.width = (w * scale) + 'px';
    img.style.height = (h * scale) + 'px';
    var x = (availW - w * scale) / 2, y = (availH - h * scale) / 2;
    img.style.left = x + 'px';
    img.style.top = y + 'px';
    st.map = { x: x, y: y, scale: scale };
  }
  st.fit = fit;
  img.addEventListener('load', fit);
  window.addEventListener('resize', fit);
  img.src = shotUrl;
  function toReal(cx, cy) { return [Math.round((cx - st.map.x) / st.map.scale), Math.round((cy - st.map.y) / st.map.scale)]; }
  function mark(b) {
    if (!b || !st.map) { sel.style.display = 'none'; coords.textContent = ''; return; }
    var x1 = st.map.x + b[0] * st.map.scale, y1 = st.map.y + b[1] * st.map.scale;
    sel.style.display = 'block';
    sel.style.left = x1 + 'px'; sel.style.top = y1 + 'px';
    sel.style.width = Math.max(2, (b[2] - b[0]) * st.map.scale) + 'px';
    sel.style.height = Math.max(2, (b[3] - b[1]) * st.map.scale) + 'px';
    coords.textContent = '(' + b.join(', ') + ')';
  }
  var start = null, dragging = false;
  ov.addEventListener('mousedown', function (e) {
    if (e.target.closest('#dash-shot-bar')) return;
    e.preventDefault();
    start = toReal(e.clientX, e.clientY); dragging = true; box = null; mark(null);
  });
  window.addEventListener('mousemove', function (e) {
    if (!dragging || !st.map) return;
    var p = toReal(e.clientX, e.clientY);
    box = [Math.min(start[0], p[0]), Math.min(start[1], p[1]), Math.max(start[0], p[0]), Math.max(start[1], p[1])];
    mark(box);
  });
  window.addEventListener('mouseup', function () { dragging = false; });
  ov.querySelector('#dash-shot-ok').addEventListener('click', function () {
    if (!box || box[2] - box[0] < 1 || box[3] - box[1] < 1) { showToast('Drag a rectangle first'); return; }
    var b = box.slice();
    _dashPickerClose(false); // keep the shot server-side: cropping needs it
    onDone(b);
  });
  ov.querySelector('#dash-shot-cancel').addEventListener('click', function () { _dashPickerClose(true); onDone(null); });
}

function toggleStartStop() {
  if(_botRunning){ if(!confirm('Stop the current run?'))return; _markPending('running', false, 2500); post('stop'); _botRunning=false; _updateStartStopBtn(false); }
  else {
    // Optimistically update UI, then verify server accepted the start
    _markPending('running', true, 3500);
    _botRunning=true; _updateStartStopBtn(true);
    const _missingLo = requiredLoadoutsMissing();
    if(_missingLo.length){
      _botRunning=false; _updateStartStopBtn(false);
      showLoadoutBlock(_missingLo);
      return;
    }
    if(_lastPollState && _lastPollState.force_restart && !_lastPollState.game_detect_set){
      _botRunning=false; _updateStartStopBtn(false);
      showGameDetectBlock();
      return;
    }
    post('start').then(r=>r.json()).then(d=>{
      if(d && d.ok===false){
        _botRunning=false; _updateStartStopBtn(false);
        if (d.missing_loadouts && d.missing_loadouts.length) showLoadoutBlock(d.missing_loadouts);
        else if (d.game_detect_block_seq) showGameDetectBlock();
        else alert(_repairMojibake(d.error || 'Cannot start.'));
      }
    }).catch(()=>{ /* server error — leave running, poll will catch it */ });
  }
}
function _updateStartStopBtn(running) {
  document.getElementById('ss-icon-play').style.display=running?'none':'';
  document.getElementById('ss-icon-stop').style.display=running?'':'none';
  document.getElementById('ss-label').textContent=running?'Stop':'Start';
  document.getElementById('btn-start-stop').style.background=running?'var(--red)':'var(--green)';
}
// togglePause removed ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â F8/pause not used
function confirmQuit() { if(confirm('Stop the bot and close?'))post('quit'); }
function applyBotMode(mode) {
  mode = (mode === 'delve' || mode === 'kraken' || mode === 'zytos' || mode === 'crater' || mode === 'farm_meteor') ? mode : 'rebirth';
  document.body.classList.toggle('mode-delve', mode === 'delve');
  document.body.classList.toggle('mode-kraken', mode === 'kraken');
  document.body.classList.toggle('mode-zytos', mode === 'zytos');
  document.body.classList.toggle('mode-crater', mode === 'crater');
  document.body.classList.toggle('mode-farm-meteor', mode === 'farm_meteor');
  document.body.classList.toggle('mode-rebirth', mode === 'rebirth');
  const runSel = document.getElementById('run-mode-select');
  if (runSel) runSel.disabled = (mode !== 'rebirth');
  const fmAreaWrap = document.getElementById('farm-meteor-area-wrap');
  if (fmAreaWrap) fmAreaWrap.style.display = (mode === 'farm_meteor') ? '' : 'none';
  const cats = document.getElementById(mode === 'crater' ? 'crater-mode-settings-cats' : 'mode-settings-cats');
  const needRender = (_modeSettingsMode !== mode) || !(cats && cats.innerHTML.trim());
  if (needRender) {
    _modeSettingsMode = mode;
    if (_cfgSchema && _cfgSchema.length) renderModeSettings();
  }
}
function setBotMode(mode) {
  applyBotMode(mode);
  post('set_bot_mode',{mode});
}
function setFarmMeteorArea(area) {
  if (!['a6','a7','a8'].includes(String(area))) return;
  post('set_farm_meteor_area',{area});
}
function setRunMode(mode) {
  if (!mode || !RUN_MODE_VALUES.includes(String(mode))) return;
  post('set_run_mode',{mode});
}
function setCraterOverlay(val) { post('set_crater_overlay',{value: val}); }
function sbToggleCraterOverlay(val) {
  const chk = document.getElementById('crater-overlay-check');
  if (chk) { if (val !== undefined) chk.checked = val; else chk.checked = !chk.checked; setCraterOverlay(chk.checked); _sbSetActive('sb-crater-overlay-btn', chk.checked); }
}
function setUnlockDrills(val) { _markPending('unlock_drills', val); postJson('/config', {updates:{UNLOCK_DRILLS:val}}); }
function setActivateDrills(val) { _markPending('activate_drills', val); postJson('/action', {action:'set_rebirth_activate_drills', value:val}); }
function setDrillOnRock(val) { _markPending('rebirth_drill_on_rock', val); postJson('/action', {action:'set_rebirth_drill_on_rock', value:val}); }
function setDrillOnBaserock(val) { _markPending('rebirth_drill_on_baserock', val); postJson('/action', {action:'set_rebirth_drill_on_baserock', value:val}); }
function setDrillOnA5Meteor(val) { _markPending('rebirth_drill_on_a5_meteor', val); postJson('/action', {action:'set_rebirth_drill_on_a5_meteor', value:val}); }
function sbToggleActivateDrillsDelve() {
  const chk = document.getElementById('activate-drills-delve-check');
  chk.checked = !chk.checked;
  setActivateDrillsDelve(chk.checked);
  _sbSetActive('sb-activate-drills-delve-btn', chk.checked);
}
function setActivateDrillsDelve(val) { _markPending('delve_activate_drills', val); postJson('/action', {action:'set_delve_activate_drills', value:val}); }
function sbToggleActivateDrillsKraken() {
  const chk = document.getElementById('activate-drills-kraken-check');
  chk.checked = !chk.checked;
  setActivateDrillsKraken(chk.checked);
  _sbSetActive('sb-activate-drills-kraken-btn', chk.checked);
}
function setActivateDrillsKraken(val) { _markPending('kraken_activate_drills', val); postJson('/action', {action:'set_kraken_activate_drills', value:val}); }
function sbToggleActivateDrillsZytos() {
  const chk = document.getElementById('activate-drills-zytos-check');
  chk.checked = !chk.checked;
  setActivateDrillsZytos(chk.checked);
  _sbSetActive('sb-activate-drills-zytos-btn', chk.checked);
}
function setActivateDrillsZytos(val) { _markPending('zytos_activate_drills', val); postJson('/action', {action:'set_zytos_activate_drills', value:val}); }



// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// STATE POLL
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
async function poll() {
  try {
    ensureModeSelectors();
    const r=await fetch('/state'); if(!r.ok)throw new Error();
    const s=await r.json(); _pollFails=0; _lastPollState=s;
    document.getElementById('offline-banner').classList.remove('show');
    const missLo = Array.isArray(s.missing_loadouts) ? s.missing_loadouts : [];
    const missSeq = Number(s.loadout_block_seq || 0);
    if (missLo.length && missSeq > _loadoutBlockAckSeq) {
      showLoadoutBlock(missLo);
    }
    const gdSeq = Number(s.game_detect_block_seq || 0);
    if (gdSeq > _gameDetectBlockAckSeq && !s.game_detect_set) {
      showGameDetectBlock();
    }
    // Sync Start/Stop button with actual server state
    let serverRunning = !!s.run_active || (!s.waiting_for_start && s.status !== 'STOPPED' && s.status !== 'WAITING' && s.status !== 'INIT');
    const pendingRun = _pendingValue('running');
    if (pendingRun !== null) serverRunning = pendingRun;
    if (_botRunning !== serverRunning) { _botRunning = serverRunning; _updateStartStopBtn(serverRunning); }
    applyTabLocks(s);
    document.getElementById('b-status').textContent=_repairMojibake(s.status||'-');
    document.getElementById('b-time').textContent=s.run_active?fmtTime(s.run_elapsed_secs):'-';
    document.getElementById('b-steps').textContent=s.run_active?(s.run_steps??0):'-';
    document.getElementById('b-errors').textContent=s.run_active?s.run_errors:'-';
    // all-time stats are updated by applyRunFilter() driven by filter selection
    const botSel=document.getElementById('bot-mode-select');
    const botMode=(s.bot_mode==='delve'||s.bot_mode==='kraken'||s.bot_mode==='zytos'||s.bot_mode==='crater'||s.bot_mode==='farm_meteor')?s.bot_mode:'rebirth';
    if(botSel&&botSel.value!==botMode)botSel.value=botMode;
    applyBotMode(botMode);
    if (botMode === 'crater') {
      const elapsed = s.crater_elapsed_secs || 0;
      const petDrops = s.crater_pet_drops || 0;
      const runtimeEl = document.getElementById('crater-runtime');
      const petsEl = document.getElementById('crater-pets');
      const pphEl = document.getElementById('crater-pets-per-hour');
      if (elapsed > 0) {
        const hrs = Math.floor(elapsed / 3600);
        const mins = Math.floor((elapsed % 3600) / 60);
        if (runtimeEl) runtimeEl.textContent = hrs > 0 ? hrs + 'h ' + mins + 'm' : mins + 'm';
        const pph = elapsed > 0 ? (petDrops / (elapsed / 3600)).toFixed(2) : '0';
        if (pphEl) pphEl.textContent = pph;
      } else {
        if (runtimeEl) runtimeEl.textContent = '-';
        if (pphEl) pphEl.textContent = '-';
      }
      if (petsEl) petsEl.textContent = String(petDrops);
      // Crater chart removed
    }
    const sel=document.getElementById('run-mode-select');
    if (sel && s.run_mode) {
      const v = normalizeRunModeClient(s.run_mode);
      if (sel.value !== v) sel.value = v;
    }
    const fmAreaSel=document.getElementById('farm-meteor-area-select');
    if (fmAreaSel && s.farm_meteor_area) {
      const vArea = ['a6','a7','a8'].includes(String(s.farm_meteor_area)) ? String(s.farm_meteor_area) : 'a6';
      if (fmAreaSel.value !== vArea) fmAreaSel.value = vArea;
    }
    const pUnlock=_pendingValue('unlock_drills'); const vUnlock=pUnlock!==null?pUnlock:!!s.unlock_drills;
    const pAct=_pendingValue('activate_drills'); const vAct=pAct!==null?pAct:!!s.activate_drills;
    const pDelveAct=_pendingValue('delve_activate_drills'); const vDelveAct=pDelveAct!==null?pDelveAct:!!(s.delve_activate_drills!==undefined?s.delve_activate_drills:true);
    const pKrakenAct=_pendingValue('kraken_activate_drills'); const vKrakenAct=pKrakenAct!==null?pKrakenAct:!!(s.kraken_activate_drills!==undefined?s.kraken_activate_drills:true);
    const pZytosAct=_pendingValue('zytos_activate_drills'); const vZytosAct=pZytosAct!==null?pZytosAct:!!(s.zytos_activate_drills!==undefined?s.zytos_activate_drills:true);
    const pAuto=_pendingValue('auto_strength'); const vAuto=pAuto!==null?pAuto:!!s.auto_strength;
    const pBossA1=_pendingValue('boss_fight_a1'); const vBossA1=pBossA1!==null?pBossA1:!!s.boss_fight_a1;
    const pDailyQ=_pendingValue('daily_quests'); const vDailyQ=pDailyQ!==null?pDailyQ:!!s.daily_quests;
    const pForceRestart=_pendingValue('force_restart'); const vForceRestart=pForceRestart!==null?pForceRestart:!!s.force_restart;
    const pPauseLag=_pendingValue('pause_on_lag'); const vPauseLag=pPauseLag!==null?pPauseLag:!!s.pause_on_lag;
        
    _syncSidebarToggle('unlock-drills-check', 'sb-unlock-drills-btn', vUnlock);
    _syncSidebarToggle('activate-drills-check', 'sb-activate-drills-btn', vAct);
    _syncSidebarToggle('activate-drills-delve-check', 'sb-activate-drills-delve-btn', vDelveAct);
    _syncSidebarToggle('activate-drills-kraken-check', 'sb-activate-drills-kraken-btn', vKrakenAct);
    _syncSidebarToggle('activate-drills-zytos-check', 'sb-activate-drills-zytos-btn', vZytosAct);
    _syncSidebarToggle('auto-strength-check', null, vAuto);
    _syncSidebarToggle('boss-fight-a1-check', 'sb-boss-fight-a1-btn', vBossA1);
    _syncSidebarToggle('daily-quests-check', 'sb-daily-quests-btn', vDailyQ);
    _syncSidebarToggle('force-restart-check', 'sb-force-restart-btn', vForceRestart);
    _syncSidebarToggle('pause-on-lag-check', 'sb-pause-on-lag-btn', vPauseLag);
    const pCraterOv=_pendingValue('crater_overlay'); const vCraterOv=pCraterOv!==null?pCraterOv:!!(s.crater_overlay!==undefined?s.crater_overlay:true);
    _syncSidebarToggle('crater-overlay-check', 'sb-crater-overlay-btn', vCraterOv);
    const versionLabel = document.getElementById('acct-version-label');
    if (versionLabel) versionLabel.textContent = s.app_version ? `Current version ${s.app_version}` : 'Current version -';
    const hist=(botMode==='delve')?(s.delve_run_history||[]):(botMode==='kraken')?(s.kraken_run_history||[]):(botMode==='zytos')?(s.zytos_run_history||[]):(s.run_history||[]);
    _chartMode=botMode;
    const chartTitle=document.getElementById('chart-title-main');
    if(chartTitle && !_runDetailOpen) chartTitle.textContent=(botMode==='delve')?'Delve Boss Time History':(botMode==='kraken')?'Kraken Fight History':(botMode==='zytos')?'Zytos Fight History':'Rebirth History';
    if(s.session_start_time) _sessionStartTime=s.session_start_time;
    _allRuns=hist;
    updateQuestStats(s, botMode, hist);
    const filt=getFilteredRuns();
    const histKey=runHistoryKey(botMode, filt)+'|'+_runKind;
    if(!_dashReady || histKey!==_lastHistKey){_dashReady=true;_lastHistKey=histKey;applyRunFilter(filt);}
  } catch(e){_pollFails++;if(_pollFails>3)document.getElementById('offline-banner').classList.add('show');}
}
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Run filter ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
let _allRuns=[], _activeFilter='all', _runKind='all', _lastHistKey=null, _dashReady=false;
const MAX_CHART_POINTS = 1200;
function isFullRun(r){
  if(!r) return true;
  if(r.full_rebirth===false || r.full_rebirth===0 || r.full_rebirth==='false') return false;
  return true;
}
function toggleChartSort(ev){
  if(ev) ev.stopPropagation();
  const box=document.getElementById('chart-sort');
  if(!box) return;
  box.classList.toggle('open');
}
document.addEventListener('click', ()=>{
  const box=document.getElementById('chart-sort');
  if(box) box.classList.remove('open');
});
function syncChartSortUI(){
  const btn=document.getElementById('chart-sort-btn');
  const range={all:'All time',session:'This session',hour:'This hour',today:'Today',week:'This week',month:'This month'}[_activeFilter]||'All time';
  const kind={all:'All runs',full:'Full rebirths',resumed:'Resumed'}[_runKind]||'All runs';
  if(btn) btn.title='Sort · '+range+' · '+kind;
  document.querySelectorAll('#chart-sort-menu button[data-filter]').forEach(b=>b.classList.toggle('active', b.getAttribute('data-filter')===_activeFilter));
  document.querySelectorAll('#chart-sort-menu button[data-kind]').forEach(b=>b.classList.toggle('active', b.getAttribute('data-kind')===_runKind));
}
function setRunKind(kind){
  _runKind=kind||'all';
  const box=document.getElementById('chart-sort');
  if(box) box.classList.remove('open');
  syncChartSortUI();
  applyRunFilter(getFilteredRuns());
}
function setFilter(f){
  _activeFilter=f||'all';
  const box=document.getElementById('chart-sort');
  if(box) box.classList.remove('open');
  syncChartSortUI();
  applyRunFilter(getFilteredRuns());
}
let _sessionStartTime=0; // set from server state
function getFilteredRuns(){
  let rows=_allRuns;
  if(_runKind==='full') rows=rows.filter(isFullRun);
  else if(_runKind==='resumed') rows=rows.filter(r=>!isFullRun(r));
  if(_activeFilter==='all') return rows;
  const now=Date.now()/1000, d=new Date();
  const todayStart=new Date(d.getFullYear(),d.getMonth(),d.getDate()).getTime()/1000;
  const weekDay=d.getDay(); // 0=Sun
  const weekStart=todayStart - weekDay*86400;
  const monthStart=new Date(d.getFullYear(),d.getMonth(),1).getTime()/1000;
  const hourStart=now - 3600;
  return rows.filter(r=>{
    const t=r.start_time||r.end_time||0;
    if(_activeFilter==='today')   return t>=todayStart;
    if(_activeFilter==='week')    return t>=weekStart;
    if(_activeFilter==='month')   return t>=monthStart;
    if(_activeFilter==='hour')    return t>=hourStart;
    if(_activeFilter==='session') return _sessionStartTime>0 ? t>=_sessionStartTime : true;
    return true;
  });
}
function runHistoryKey(mode, rows){
  const n=rows.length;
  const first=rows[0]||{};
  const last=rows[n-1]||{};
  return [
    mode, n,
    first.run_number||'', first.start_time||'', first.end_time||'',
    last.run_number||'', last.start_time||'', last.end_time||'', last.duration_secs||''
  ].join('|');
}
function downsampleRuns(rows, maxPoints=MAX_CHART_POINTS){
  if(!Array.isArray(rows) || rows.length<=maxPoints) return rows || [];
  const out=[];
  const last=rows.length-1;
  const step=last/(maxPoints-1);
  let prev=-1;
  for(let i=0;i<maxPoints;i++){
    const idx=Math.min(last, Math.round(i*step));
    if(idx!==prev){ out.push(rows[idx]); prev=idx; }
  }
  return out;
}
function fmtMineral(v){
  v=Number(v)||0; if(v<=0)return '0';
  const SU=[[1e33,'Dc'],[1e30,'No'],[1e27,'Oc'],[1e24,'Sp'],[1e21,'Sx'],[1e18,'Qi'],[1e15,'Qa'],[1e12,'T'],[1e9,'B'],[1e6,'M'],[1e3,'k']];
  for(const [f,sx] of SU){ if(v>=f) return (v/f).toFixed(2)+sx; }
  return v<10?v.toFixed(2):String(Math.round(v));
}
function updateQuestStats(s, botMode, hist){
  const show=!!s.daily_quests && botMode!=='delve' && botMode!=='kraken' && botMode!=='zytos';
  const sep=document.getElementById('quest-stats-sep');
  const row=document.getElementById('quest-stats-row');
  if(sep) sep.style.display=show?'':'none';
  if(row) row.style.display=show?'flex':'none';
  if(!show) return;
  let total=0, runs=0;
  (hist||[]).forEach(r=>{ const q=Number(r.quests_completed||0); if(q>0){ total+=q; runs++; } });
  const live=Number(s.run_quests_completed||0);
  if(live>0){ total+=live; runs+=1; }
  document.getElementById('q-total').textContent=total>0?String(total):'-';
  document.getElementById('q-avg').textContent=runs>0?(total/Math.max(1,runs)).toFixed(1):'-';
}
function applyRunFilter(filt){
  const chartRuns=downsampleRuns(filt);
  const labels=chartRuns.map((r,i)=>{
    if(r.start_time){ const d=new Date(r.start_time*1000); return d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0'); }
    return String(i+1);
  });
  const data=chartRuns.map(r=>(r.duration_secs||0)/60);
  const ds=runChart.data.datasets[0];
  ds.data=data;
  runChart.data.labels=labels;
  const colorFor=r=>isFullRun(r)?'#7c6af7':'#e8a04a';
  if(_runKind==='all'){
    ds.pointBackgroundColor=chartRuns.map(colorFor);
    ds.borderColor='#7c6af7';
  } else if(_runKind==='resumed'){
    ds.pointBackgroundColor='#e8a04a';
    ds.borderColor='#e8a04a';
  } else {
    ds.pointBackgroundColor='#7c6af7';
    ds.borderColor='#7c6af7';
  }
  runChart._runMeta=chartRuns; runChart.update('none');
  // Update all-time stats from filtered runs
  const durations=((_runKind==='resumed')?filt:filt.filter(isFullRun)).map(r=>r.duration_secs||0).filter(d=>d>0);
  const minDuration=durations.length?durations.reduce((a,b)=>Math.min(a,b),durations[0]):0;
  const maxDuration=durations.length?durations.reduce((a,b)=>Math.max(a,b),durations[0]):0;
  const totalErrors=filt.reduce((a,r)=>a+(r.error_count||0),0);
  const count=filt.length;
  const isBoss=(_chartMode==='delve'); const isKraken=(_chartMode==='kraken'||_chartMode==='zytos');
  const bossName='Delve';
  document.getElementById('g-count-label').textContent=isBoss?'Delve Runs':(_chartMode==='zytos')?'Zytos Runs':isKraken?'Kraken Runs':'Rebirths';
  document.getElementById('g-avg-label').textContent='Avg Time';
  document.getElementById('g-fails-label').textContent=isBoss?'Lowest Time':isKraken?'Lowest Time':'Avg Fails / Run';
  document.getElementById('g-best-label').textContent=(isBoss||isKraken)?'Best Time':'Best Run';
  document.getElementById('g-worst-label').textContent=isBoss?'Latest Time':isKraken?'Latest Time':'Worst Run';
  document.getElementById('g-rebirths').textContent=count;
  document.getElementById('g-avg').textContent=durations.length?fmtTime(durations.reduce((a,b)=>a+b,0)/durations.length):'-';
  document.getElementById('g-best').textContent=durations.length?fmtTime(maxDuration):'-';
  document.getElementById('g-worst').textContent=durations.length?fmtTime(durations[durations.length-1]):'-';
  document.getElementById('g-fails').textContent=(isBoss||isKraken)?(durations.length?fmtTime(minDuration):'-'):(count>0?(totalErrors/count).toFixed(2):'-');
  if(!isBoss && !isKraken) {
    document.getElementById('g-best').textContent=durations.length?fmtTime(minDuration):'-';
    document.getElementById('g-worst').textContent=durations.length?fmtTime(maxDuration):'-';
  }
  // Update label to reflect active filter
  const labelMap={all:'All-Time Stats',session:"This Session",hour:"Last Hour",today:"Today's Stats",week:"This Week's Stats",month:"This Month's Stats"};
  document.getElementById('alltime-label').textContent=labelMap[_activeFilter]||'All-Time Stats';
  syncChartSortUI();
}

function craterResetStats() {
  if (!confirm('Reset all crater stats? This cannot be undone.')) return;
  postJson('/action', {action: 'crater_reset_stats'})
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        document.getElementById('crater-runtime').textContent = '-';
        document.getElementById('crater-pets').textContent = '0';
        document.getElementById('crater-pets-per-hour').textContent = '-';
        // Crater chart removed
      }
    })
    .catch(e => console.error('crater reset failed:', e));
}

function confirmDeleteAll(){
  if(!confirm('Delete ALL run history? This cannot be undone.')) return;
  post('delete_all_runs',{mode:_chartMode});
  _lastHistKey=''; _allRuns=[];
  applyRunFilter([]);
  refreshRunHistorySoon();
}


// Polling

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// CONFIG PANEL
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
let _cfgSchema=[];
async function loadConfig() {
  const form=document.getElementById('config-form');
  form.innerHTML='<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px 0;">Loading...</div>';
  try {
    const r=await fetch('/config'); const d=await r.json();
    if(!d.ok)throw new Error(d.error);
    _cfgSchema=d.schema; _cfgValues=d.values || {}; renderConfigForm(d.values); renderModeSettings();
  } catch(e){form.innerHTML=`<div style="color:var(--red);font-size:13px;padding:10px;">Error: ${_escapeHtml(_repairMojibake(e.message || 'Unknown error'))}</div>`;}
}
const CFG_TOOLTIPS = {
  BOSS_FIGHT_A1_BASEROCK_THRESHOLD: 'Baserock grind target before the first A1 boss fight. Any e33 value (default: 1e33). Bot grinds baserock until this stone amount, then starts the fight loop.',
  BOSS_FIGHT_A1_AMOUNT: 'How many boss fights to loop. Default: 3. Fight 1 goes via meteor â†’ bramble; fights 2+ re-enter via fight_bramble macro. Each fight also scales the meteor grind and fire time.',
  BOSS_FIGHT_A1_METEOR_GRIND_SECONDS: 'Base meteor grind time per fight (default: 10s). Scales with fight number â€” fight 1 = 10s, fight 2 = 20s, fight 3 = 30s, etc. Formula: meteor_grind_secs Ã— fight_number.',
  BOSS_FIGHT_A1_LOADOUT_FIGHTING: 'Fighting loadout. Required for Kraken / Zytos / Delve, and for Rebirth when Boss Fight is on. Played on Start for those fight modes, and before walking to Bramble.',
  BOSS_FIGHT_A1_LOADOUT_FARMING:  'Farming loadout. Required for Rebirth. Played once on Start (F8).',
  CRATER_LOADOUT_METEOR_REWARDS: 'Meteor Rewards loadout. Required for Crater and Meteor. Played on Start (F8).',
  BOSS_FIGHT_A1_MODE: 'Boss card difficulty for Bramble and Zytos (same setting). After the menu opens the bot OCRs the mode name and clicks the HARD pill until this mode is showing. Kraken is Solo-only and skips this. Add translated names under OCR aliases.',
  BOSS_FIGHT_A1_MODE_OCR: 'OCR aliases per mode. Fortnite translates Solo/Normal/Hard/Ex — add those words here. Use + to add, - to remove. Matching is case-insensitive and ignores spaces.',
  DISABLE_OVERLAYS: 'Fully disable ALL overlay windows (top-left HUD, recorder HUD, crater ESP boxes). ON: no overlay window is ever shown or created on screen - zero interaction with Fortnite, no focus fighting, no performance cost. The dashboard still shows everything you need. OFF (default): overlays work normally. Applies live within a quarter second - no restart needed.',
  USER_SENS_H: 'Your Fortnite Horizontal Sensitivity (%). Go to Fortnite Settings ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ Mouse ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ Horizontal Sensitivity. Bot was recorded at 17%.',
  USER_SENS_V: 'Your Fortnite Vertical Sensitivity (%). Go to Fortnite Settings Mouse → Vertical Sensitivity. Bot was recorded at 17%.',
  STONE_FOR_A5_STAGE1: 'Stone amount required to move from Base rock to Area 5 Stage 1.',
  STONE_FOR_A5_STAGE2: 'Stone amount required to move from Stage 1 to Stage 2.',
  STONE_FOR_A5_STAGE3: 'Stone amount required to move from Stage 2 to Stage 3.',
  STONE_FOR_A5_STAGE4: 'Stone amount required to move from Stage 3 to Stage 4.',
  STONE_FOR_METEOR: 'Stone amount required to switch from Stage 4 to Meteor farming.',
  STONE_FOR_AREA6_SHORTCUT: 'Baserock stone needed before Meteor shortcut (default 136e150).',
  STONE_STALL_TIMEOUT: 'If stone count does not change for this many seconds, the bot detects a stall and recovers.',
  SMART_FAILURE_TIMEOUT: 'Maximum seconds any single macro may run before the bot force-kills it.',
  A5_CHECK_ATTEMPTS: 'How many times the bot checks whether it is in Area 5 before giving up.',
  REBIRTH_CHECK_DELAY: 'Seconds to wait before checking if a rebirth screen appeared.',
  QUEST_MINE_TIMEOUT_SECONDS: 'Daily Quests: max seconds to hold LMB on one star rock before the bot gives up and auto-finishes that quest (default 90).',
  MANUAL_STR_OPEN: 'Manual Strength Open: when checked (default) the bot opens the strength window itself (monitor key -> left click). Unchecked = the bot never opens it — your macros must open the window; the buying loop just waits for it to appear.',
  MANUAL_STR_CLICK_DELAY_MS: 'Manual Strength: delay between one click and the next (release -> next press), in milliseconds. Default 1ms, minimum 1ms (0ms makes the game merge and eat clicks entirely — they register nothing; the bot forces 1ms even if you enter 0). Compat clicking mode overrides this to 12ms.',
  MANUAL_STR_CLICK_HOLD_MS: 'Manual Strength: hold time between mouse down and mouse up for each click, in milliseconds. Default 1ms, minimum 1ms (0ms makes the game merge and eat clicks entirely; the bot forces 1ms even if you enter 0). Compat clicking mode overrides this to 12ms.',
  HATCH_CLOSE_MIN_PCT: 'Daily Quests: yellow-pixel percentage needed to consider the hatch GUI (and its close button) detected. The hatch button is thinner than the quest board close, reading ~0.27 when open, so the default is 0.20.',
  DAILY_QUEST_ALIASES: 'Daily Quests: OCR aliases per quest type. Pick the quest type in the dropdown (Break N Star Rocks / Open Chests / Hatch Pets / Combine Pets / Hatch GUI: Area 1 Egg), then add translated names with +. For rocks, {$NUMBER} marks where the rock-count digit sits (BREAK {$NUMBER} STAR ROCKS). Matching is case-insensitive and ignores spaces.',
  GAME_DETECT_IMAGE: 'Pick an always-visible in-game HUD element as proof we are in the MT2 map: the Miner Tycoon 2 logo, the stone icon or the shard icon. Press Pick, then F2 in-game, drag a box around it. The box and point are recorded with the image and save immediately. Nothing is shipped by default — Force Restart refuses to start until this is picked (global Config, top gear). The image is NOT searched for on screens where the HUD is hidden (menus, Manual Strength overlays) — those paths already skip the stone/shard checks.',
  GAME_DETECT_DIFF: 'Image difference tolerance in percent (default 5). The bot grabs the live screen at the picked box and compares it with your picked image: a mean difference above this percent means we are NOT looking at the MT2 in-game HUD (wrong map, menu, loading screen) and Force Restart / recovery treats it as out-of-game. Raise it if the check fails while you are in game; lower it to be stricter.',
  FORCE_GAME_LOGO_IMAGE: 'Pick the Miner Tycoon 2 billboard from the map-search results (the game card shown after searching the island code). Press Pick, then F2 in-game while the search results are open, drag a box around the billboard/logo. Nothing is shipped by default: if the bot drifts onto a wrong game and this image is not picked, the map search cannot finish and the bot STOPS with an error instead of clicking random things. Box and point are recorded with the image and save immediately.',
  FORCE_NOTINGAME_WAIT: 'Three-state recovery, state 3: after every known GUI is closed and the in-game image is still missing, wait up to this many seconds for the HUD image or the lobby menu before giving up and leaving to the lobby. A join can legitimately take 30s-2min, so the default is 120s.',
  FORCE_MENU_TIMEOUT: 'Max seconds to search for the lobby menu (PLAY button OCR, scroll-up drift protection) before the join is considered failed.',
  FORCE_PLAY_SETTLE: 'Pause between confirming Miner Tycoon 2 is selected and pressing PLAY, in seconds (default 5). Fresh UI is not clickable instantly.',
  FORCE_MAP_CODE: 'The Fortnite island code typed into Search Discover when the lobby selected the wrong game (default 2311-7649-8274 = Miner Tycoon 2).',
  FORCE_MAP_SEARCH_TIMEOUT: 'Wrong-game recovery: max seconds to wait for the picked game-logo billboard image in the search results, checked every 0.1s (default 30).',
  FORCE_MAP_SEARCH_ATTEMPTS: 'Wrong-game recovery: if a search comes up empty, the flow scrolls up to reset it and runs the whole search again — this is how many full attempts before it gives up (default 3).',
  FORCE_SELECT_TIMEOUT: 'Wrong-game recovery: max seconds to wait for the SELECT button after clicking the billboard (default 30).',
  FORCE_TITLE_TIMEOUT: 'Wrong-game recovery: max seconds to wait for the selected-game title to read Miner Tycoon 2 again after SELECT (default 30).',
  FORCE_OCR_PLAY_ALIASES: 'Lobby detection reads the PLAY button with OCR. Aliases are matched case/punctuation-insensitive as substrings (comma separated). Dropped-char reads like PAY/PLY/LAY always count too.',
  FORCE_OCR_TITLE_ALIASES: 'The selected-game title (bottom-left of the lobby) is OCR-read and matched against these aliases. If it reads anything else, the wrong-game map search starts. Default: miner tycoon 2, minertycoon2, miner tycoon, miner.',
  FORCE_OCR_SEARCH_ALIASES: 'The Search Discover bar is found by OCR before clicking it (default: search discover, search, discover).',
  FORCE_OCR_SELECT_ALIASES: 'The SELECT button on the map card is found by OCR (default: select).',
  FORCE_PLAY_OCR_REGION: 'Screen region [x1,y1,x2,y2] the PLAY button is OCR-read from. 1920x1080 base coordinates, scaled automatically to your resolution.',
  FORCE_GAME_TITLE_REGION: 'Screen region [x1,y1,x2,y2] the selected-game title (Miner Tycoon 2) is OCR-read from. 1920x1080 base coordinates.',
  FORCE_SEARCH_DISCOVER_REGION: 'Screen region [x1,y1,x2,y2] the Search Discover bar is OCR-read from. 1920x1080 base coordinates.',
  FORCE_SELECT_OCR_REGION: 'Screen region [x1,y1,x2,y2] the SELECT button is OCR-read from. 1920x1080 base coordinates.',
  FORCE_SEARCH_CLICK: 'Click point [x,y] of the Search Discover bar. 1920x1080 base coordinates, scaled automatically.',
  FORCE_GAME_BILLBOARD_CLICK: 'Click point [x,y] of the Miner Tycoon 2 billboard in the search results. 1920x1080 base coordinates, scaled automatically.',
  FORCE_SELECT_CLICK: 'Click point [x,y] of the SELECT button on the map card. 1920x1080 base coordinates, scaled automatically.',
  MENU_RESUME_JOIN_WAIT: 'Seconds to wait after pressing PLAY for the new game to load (in-game image check). A join can take 30s-2min — too short and the bot thinks it failed while you are still on the loading screen and starts recovery mid-join. Default 120.',
  REBIRTH_POST_CONFIRM_WAIT: 'Seconds to wait after a rebirth is confirmed before teleporting back to base. Gives the game time to fully load.',
  STONE_ICON_MISSING_WAIT: 'Seconds the in-game HUD (your picked In-Game image detection) must stay missing (crash/disconnect/wrong map) before Force Restart recovery starts.',
  MENU_PLAY_COLOR_THRESH: 'Fraction of MENU_PLAY_REGION pixels that must match the yellow PLAY button color (0.0ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“1.0). Default 0.08. Raise if menu is falsely detected.',
  MENU_PLAY_HUE_TOL: 'Hue tolerance for PLAY button yellow color detection (default 15).',
  MENU_PLAY_SAT_TOL: 'Saturation tolerance for PLAY button color detection (default 60).',
  MENU_PLAY_VAL_TOL: 'Value/brightness tolerance for PLAY button color detection (default 60).',
  STONE_FOR_UNLOCK_DRILLS: 'Stone amount at which the bot will automatically unlock drills (once per run).',
  BASE_ROCK_DRILL_PRESSES: 'How many times to press the drill activation key per base-rock burst in manual-strength mode. Default 6.',
  AUTO_ROCK_MAX_GRIND_SECONDS: 'Auto Strength only: max seconds to stay on one stage rock before forcing a route retry. Does not apply to baserock.',
  HIT_ROCKS: 'ON: the bot performs its built-in stage-rock swings. OFF: the bot never swings itself — use this when your own macro already includes the swings; the bot still monitors stone progress and handles routing.',
  HIT_BASEROCK: 'ON: the bot performs its built-in baserock hits (hit macro, prime clicks, drill bursts). OFF: never swings itself — use this when your own macro already swings the baserock; the bot still monitors stone and reroutes if nothing moves for 30s.',
  HIT_A5_METEOR: 'ON: the bot performs its built-in A5 Meteor hits. OFF: the bot never swings itself — use this when your own macro already hits the meteor; the bot still monitors progress.',
  USE_SHORTCUTS: 'ON: after baserock in Area 5 Meteor, walk the baserock→A6 shortcut (p1_shortcut) then teleport A5. OFF: after baserock, teleport to A5 and run base_to_meteor_shortcut_p1 instead of walking to A6. Stage-rock *_shortcut.macro files are also used when present.',
  FORCE_RESTART_ON_FAILURE: 'When enabled, non-user failures play force_restart.macro (engine), then the bot starts a fresh lobby/run. Works in Rebirth, Kraken, Zytos and Crater.',
  PAUSE_ON_LAG: 'When Windows goes offline or 1.1.1.1 / 8.8.8.8 fail, freeze the current action and wait until the connection is back. Does not force restart.',
  UI_CLICK_SETTLE: 'Pause after UI clicks (teleport, map, loadout, rebirth menus) before the next action. Raise if menus eat clicks. Default 0.1s (100ms).',
  UI_BTN_SETTLE: 'Pause after a menu button click before the next screen check. Default 0.1s.',
  MAP_LOAD_FIXED_SECONDS: 'The single map-load wait: after every teleport the bot just settles this many seconds, then continues. Default 0.5s. Raise it if actions ever run on a map that is still loading.',
  METEOR_HEALTH_CHECK: 'ON: watch the A5 Meteor health bar and stop the grind as soon as the red bar disappears. OFF: skip the health bar and use the Fixed A5 hit hold below instead. Default ON.',
  FIXED_A5_HIT_TIME: 'Used only when Check A5 Meteor health is OFF. One left-mouse hold instead of the meteor_hit macro: 0 = a single 100ms tap; 1 = hold 200ms + 1s (1.2s total); 5 = 5.2s total — then it stops and continues to base + rebirth.',
  LOBBY_SETTLE: 'After the shard is seen in lobby, wait this long before continuing the run. Default 5s.',
  LOBBY_READY_SETTLE: 'After the Ready button is seen, wait this long before clicking it. Default 10s.',
  LOBBY_STEP_DELAY: 'Pause after ESC / each lobby click before the next check. Default 0.5s.',
  REBIRTH_BTN2_TIMEOUT: 'Seconds to wait for the rebirth confirm button after clicking Rebirth. Default 4s.',
  TELEPORT_MENU_SHIFT_DX: 'The F4 teleport menu can occasionally render the whole panel shifted this many pixels to the left (a client-side UI glitch, measured at 1920x1080). When the close button is not found at its normal spot, the bot checks this shifted spot before assuming the menu is stuck - if found, it works the whole attempt with every F4-menu coordinate shifted by this amount instead of force-closing and reopening. Default 663. Set to 0 to disable shift detection.',
  USE_DRILL_ON_ROCK: 'When enabled, drill activation is used while farming stage rocks (A1-A5 stages).',
  USE_DRILL_ON_BASEROCK: 'When enabled, drill activation is used while farming baserock. Uses BASE_ROCK_DRILL_PRESSES bursts.',
  USE_DRILL_ON_A5_METEOR: 'When enabled, drill activation is used while hitting Area 5 Meteor.',
  STARTUP_SETTLE_SECONDS: 'Pause after the Start click before the first macro runs. Default 0.35s.',
  A5_POST_MACRO_VERIFY_DELAY: 'Extra delay after an Area 5 navigation macro before post-navigation settle. Lower saves time; raise only if transitions are flaky.',
  MANUAL_STR_ONLY_LAST_ROW: 'When enabled, manual strength buys only the bottom row left/right buttons and ignores upper rows.',
  MANUAL_STR_DETECTION: 'What baserock manual strength watches to decide it is done. Stone: stop when the stone amount reaches the Stone threshold below (default 1.36e152 - the standard base-rock threshold). Surge level: stop when the bottom-row Surge level reaches the Surge threshold. Surge needs Bottom Row Only ON (Features tab); with it off, stone detection is always used.',
  MANUAL_STR_CLICK_METHOD: 'How manual strength paces its clicks. Default: current profile (1ms clicks, 5s stall watchdog, 0.5s open waits, 30s give-up). Classic: the original timing profile tuned by the author - same 1ms clicks but patient watchdogs (60s stall, 0.25s post-monitor open wait, 60s give-up). Compat: classic pacing with clicks slowed to a guaranteed 12ms hold/gap - for machines where 1ms clicks get dropped by the game (usually a 1ms system timer; not an FPS thing).',
  MANUAL_STR_BOTTOM_RIGHT_CLICKS: 'Bottom-row spam: how many RIGHT-side buys per cycle (default 5). With Left clicks = 1 this is the classic 5-right/1-left pattern.',
  MANUAL_STR_BOTTOM_LEFT_CLICKS: 'Bottom-row spam: how many LEFT (unlock) clicks per cycle (default 1). Set Right=1 and Left=1 for plain alternation.',
  MANUAL_STR_STONE_TARGET: 'Stone detection: stop buying when stone reaches this amount. Default 1.36e152 (the standard base-rock threshold). Applies everywhere the baserock grinds with manual strength on (start gate, meteor shortcut, boss A1) - it replaces the per-route thresholds.',
  KRAKEN_HB_CONFIRM_WINDOW_SECONDS: 'After the boss health bar disappears, watch this many seconds: black screen = death (you died), no black screen = boss killed. The reward walk also keeps checking for the death screen while it runs. Default 1.5s.',
  KRAKEN_POST_HB_LOSS_SHOOT_SECONDS: 'Keep the left mouse held this long after the health bar disappears, so a flicker does not stop DPS. Default 1.5s.',
  KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS: 'Max seconds to wait for the boss health bar to appear after clicking Join. Default 8s.',
  KRAKEN_DEATH_WAIT_SECONDS: 'Wait this long for respawn after a death before continuing the loop. Default 5s.',
  KRAKEN_MENU_WAIT_SECONDS: 'Settle wait after opening the boss menu (F4 → Area 7 → kraken macro). Default 0.5s.',
  KRAKEN_JOIN_CLICK_GAP_SECONDS: 'Gap between the two Join button clicks. Default 0.5s.',
  KRAKEN_POST_JOIN_WAIT_SECONDS: 'Settle wait after joining the fight, before weapon prep. Default 0.5s.',
  KRAKEN_REWARD_OPEN_WAIT_SECONDS: 'Short settle after the reward walk before checking for the CLOSE button. Default 0.5s.',
  KRAKEN_REWARD_WALK_SECONDS: 'How long to walk forward after the boss dies (spamming E) until the reward menu opens. Default 4.0s.',
  KRAKEN_ROUTE_ATTEMPTS: 'How many times to retry the route to the kraken (F4 teleport + area7_to_kraken macro + menu check) before failing. Default 10.',
  KRAKEN_SHOOT_POLL_SECONDS: 'Shoot-loop tick interval — how often the loop checks health bar / black screen. Default 0.1s. Keep >= 0.03.',
  KRAKEN_SHOOT_REASSERT_SECONDS: 'Re-assert left mouse down every N seconds during the fight (guard against lost input). Default 0.5s.',
  ZYTOS_POST_KILL_WAIT_SECONDS: 'Wait after the boss-killed detection before continuing, same idea as Kraken. 0 = immediate. Default 0s.',
  ZYTOS_HB_CONFIRM_WINDOW_SECONDS: 'After the Zytos health bar disappears, watch this many seconds: black screen = death, no black screen = probably killed. Default 2.5s.',
  ZYTOS_HB_EXTENDED_WINDOW_SECONDS: 'Extra confirm window after the first one passes with no black screen. Default 5s.',
  ZYTOS_POST_HB_LOSS_SHOOT_SECONDS: 'Keep the left mouse held this long after the Zytos health bar disappears. Default 1.5s.',
  ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS: 'Max seconds to wait for the Zytos health bar to appear after joining. Default 8s.',
  ZYTOS_DEATH_WAIT_SECONDS: 'Wait this long for respawn after a death in the Zytos fight. Default 5s.',
  ZYTOS_MENU_WAIT_SECONDS: 'Settle wait after opening the Zytos boss menu. Default 0.5s.',
  ZYTOS_JOIN_CLICK_GAP_SECONDS: 'Gap between the two Join button clicks. Default 0.5s.',
  ZYTOS_POST_JOIN_WAIT_SECONDS: 'Settle wait after joining the Zytos fight, before weapon prep. Default 0.5s.',
  ZYTOS_REWARD_OPEN_WAIT_SECONDS: 'Wait for the reward window to open before continuing. Default 1s.',
  ZYTOS_ROUTE_ATTEMPTS: 'How many times to retry the route to Zytos before failing. Default 10.',
  ZYTOS_SHOOT_POLL_SECONDS: 'Shoot-loop tick interval during the Zytos fight. Default 0.1s. Keep >= 0.03.',
  ZYTOS_SHOOT_REASSERT_SECONDS: 'Re-assert left mouse down every N seconds during the Zytos fight. Default 0.5s.',
  DELVE_MENU_WAIT_SECONDS: 'Settle wait after opening the Delve boss menu. Default 0.5s.',
  DELVE_JOIN_CLICK_GAP_SECONDS: 'Gap between the two Join button clicks. Default 0.5s.',
  DELVE_POST_JOIN_WAIT_SECONDS: 'Settle wait after joining the Delve fight, before weapon prep. Default 0.5s.',
  DELVE_DEATH_WAIT_SECONDS: 'Wait this long for respawn after a death in the Delve fight. Default 5s.',
  DELVE_SHOOT_POLL_SECONDS: 'Shoot-loop tick interval during the Delve fight. Default 0.1s. Keep >= 0.03.',
  DELVE_SHOOT_REASSERT_SECONDS: 'Re-assert left mouse down every N seconds during the Delve fight. Default 0.5s.',
  MANUAL_STR_SURGE_TARGET: 'Surge detection: stop buying when the Surge level (bottom row, 0-999) reaches this value. Default 160.',
  MANUAL_STR_OPEN_AFTER_HIT_WAIT: 'Open sequence: seconds to wait after the baserock hit before pressing the monitor item key (default 0.5s).',
  MANUAL_STR_OPEN_AFTER_MONITOR_WAIT: 'Open sequence: seconds to wait after pressing the monitor item key before the click that opens the strength menu (default 0.5s).',
  MANUAL_STR_NO_STRENGTH_TIMEOUT: 'Seconds without manual strength progress before the bot treats the rock as stalled and reroutes.',
  MANUAL_STR_HUD_STALL_SECONDS: 'While the manual strength menu is open, if HUD stone does not change for this many seconds the bot closes the menu and redoes the rock/baserock route (default 5).',
  ROUTE_REDO_LIMIT: 'Global. How many times a failed route can be redone (baserock, rock, meteor, crater, kraken, zytos, delve) before the run stops. With Force Restart on, that triggers a force restart. Default 5.',
  MANUAL_STR_POST_CLOSE_SETTLE_SECONDS: 'Seconds to wait after manual strength closes before mining/reading HUD outside the menu.',
  MANUAL_STR_POST_CLOSE_TOPUP_SECONDS: 'Minimum seconds to mine outside the menu after a manual threshold before moving on.',
  MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS: 'Maximum seconds to keep mining/reading HUD outside the menu after a manual threshold.',
  SAVE_DEBUG_CROPS: 'When enabled, saves OCR debug crops and full-screen failure screenshots (non-F9 failures) to code/debug_crops.',
  BOT_START_BINDING: 'Global hotkey that starts the bot (default F8).',
  BOT_STOP_BINDING: 'Global hotkey that stops the bot immediately (default F9).',
  PICKAXE_EQUIP_BINDING: 'Pickaxe equip key (default F). Must not share a key with Fortnite Quick Swap Pickaxe.',
  WEAPON_1_BINDING: 'Weapon slot 1 (default 1). Used for boss fight gun equip and as the default for Kraken/Zytos/Delve. Macros that press 1 are remapped to this bind.',
  WEAPON_2_BINDING: 'Monitor item / slot 2 (default 2). Macros that press 2 are remapped to this bind.',
  MONITOR_ITEM_BINDING: 'Monitor item key (default 2). Same slot as Weapon 2. Macros that press 2 are remapped to this bind.',
  SPRINT_BINDING: 'Sprint key (default Left Shift). Held with walk in Crater. Macros that press Shift are remapped to this bind.',
  FORWARD_BINDING: 'Move forward (default W). Every macro KEY_DOWN/UP/PRESS of W is replaced with this bind.',
  BACKWARD_BINDING: 'Move backward (default S). Macros that press S are remapped to this bind.',
  LEFT_BINDING: 'Strafe left (default A). Macros that press A are remapped to this bind.',
  RIGHT_BINDING: 'Strafe right (default D). Macros that press D are remapped to this bind.',
  JUMP_BINDING: 'Jump (default Space). Macros that press Space are remapped to this bind.',
  CROUCH_BINDING: 'Crouch (default Left Ctrl). Macros that press Ctrl are remapped to this bind.',
  RECORDER_RECORD_BINDING: 'Recorder tab only: start/stop recording (default F5). Does not fire on Run or Editor.',
  RECORDER_PLAY_BINDING: 'Recorder tab only: play/stop the open macro (default F6). Does not fire on Run or Editor.',
  RECORDER_SMOOTH_MOVE_KEY: 'Recorder tab only: hold this key in Fortnite to capture a smooth move on both axes (default L). Mouse input is not blocked; on release a popup gives the (x, y) value to copy into a Smooth Move block.',




  UNLOCK_DRILLS: 'Automatically unlock drills once the stone threshold is reached.',
};
const CFG_SLIDERS = {
  USER_SENS_H: {min:1, max:100, step:0.1},
  USER_SENS_V: {min:1, max:100, step:0.1},
};
const CFG_KEYBIND_FIELDS = new Set([
  'MENU_TOGGLE_BINDING',
  'PICKAXE_EQUIP_BINDING',
  'DRILL_ACTIVATE_BINDING',
  'WEAPON_1_BINDING',
  'WEAPON_2_BINDING',
  'MONITOR_ITEM_BINDING',
  'SPRINT_BINDING',
  'FORWARD_BINDING',
  'BACKWARD_BINDING',
  'LEFT_BINDING',
  'RIGHT_BINDING',
  'JUMP_BINDING',
  'CROUCH_BINDING',
  'BOT_START_BINDING',
  'BOT_STOP_BINDING',
  'RECORDER_RECORD_BINDING',
  'RECORDER_PLAY_BINDING',
  'RECORDER_SMOOTH_MOVE_KEY',
]);
const CFG_KEYBIND_OPTIONS = [
  ['F1','F1'], ['F2','F2'], ['F3','F3'], ['F4','F4'], ['F5','F5'], ['F6','F6'],
  ['F7','F7'], ['F8','F8'], ['F9','F9'], ['F10','F10'], ['F11','F11'], ['F12','F12'],
  ['0','0'], ['1','1'], ['2','2'], ['3','3'], ['4','4'], ['5','5'], ['6','6'], ['7','7'], ['8','8'], ['9','9'],
  ['A','A'], ['B','B'], ['C','C'], ['D','D'], ['E','E'], ['F','F'], ['G','G'], ['H','H'], ['I','I'], ['J','J'],
  ['K','K'], ['L','L'], ['M','M'], ['N','N'], ['O','O'], ['P','P'], ['Q','Q'], ['R','R'], ['S','S'], ['T','T'],
  ['U','U'], ['V','V'], ['W','W'], ['X','X'], ['Y','Y'], ['Z','Z'],
  ['Space','SPACE'], ['Tab','TAB'], ['Enter','ENTER'], ['Escape','ESC'], ['Left Shift','SHIFT'], ['Left Ctrl','CTRL'], ['Left Alt','ALT'],
  ['Mouse Left','MOUSE_LEFT'], ['Mouse Right','MOUSE_RIGHT'], ['Mouse Middle / Scroll Click','MOUSE_MIDDLE'],
  ['Mouse Button 4','MOUSE4'], ['Mouse Button 5','MOUSE5'],
];
function renderKeybindSelect(key, value) {
  const cur = String(value ?? '').trim() || '';
  const normalized = cur.toUpperCase().replace(/[-\s]+/g, '_');
  const known = CFG_KEYBIND_OPTIONS.some(([,v]) => v === normalized);
  let opts = CFG_KEYBIND_OPTIONS.map(([label,val]) => `<option value="${val}" ${val===normalized?'selected':''}>${label}</option>`).join('');
  if(cur && !known) opts = `<option value="${cur}" selected>${cur} (custom)</option>` + opts;
  return `<select class="cfg-input" id="cfg_${key}">${opts}</select>`;
}
const INFO_ICON = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6.5"/><line x1="8" y1="7" x2="8" y2="11"/><circle cx="8" cy="5" r=".5" fill="currentColor" stroke="none"/></svg>`;
const CFG_TABS = [
  {id:'general', label:'General', sections:[
    {title:'Overlays',keys:['DISABLE_OVERLAYS']},
    {title:'Fortnite Sensitivity',keys:['USER_SENS_H','USER_SENS_V']},
    {title:'Run Keybinds',keys:['BOT_START_BINDING','BOT_STOP_BINDING','MENU_TOGGLE_BINDING','PICKAXE_EQUIP_BINDING','WEAPON_1_BINDING','MONITOR_ITEM_BINDING','FORWARD_BINDING','BACKWARD_BINDING','LEFT_BINDING','RIGHT_BINDING','JUMP_BINDING','SPRINT_BINDING','CROUCH_BINDING','DRILL_ACTIVATE_BINDING']},
    {title:'Recorder Keybinds',keys:['RECORDER_RECORD_BINDING','RECORDER_PLAY_BINDING','RECORDER_SMOOTH_MOVE_KEY']},
  ]},
  {id:'finetuning', label:'Fine-Tuning', sections:[
    {title:'Run',keys:['ROUTE_REDO_LIMIT','REBIRTH_BTN2_TIMEOUT','TELEPORT_MENU_SHIFT_DX']},
    {title:'Performance',keys:['UI_CLICK_SETTLE','UI_BTN_SETTLE','MAP_LOAD_FIXED_SECONDS','LOBBY_SETTLE','LOBBY_READY_SETTLE','LOBBY_STEP_DELAY','STARTUP_SETTLE_SECONDS']},
  ]},
  {id:'loadout', label:'Loadout', sections:[
    {title:'Loadouts',keys:['BOSS_FIGHT_A1_LOADOUT_FIGHTING','BOSS_FIGHT_A1_LOADOUT_FARMING','CRATER_LOADOUT_METEOR_REWARDS','FARM_METEOR_LOADOUT']},
  ]},
  {id:'tracker', label:'Data', sections:[
    {title:'Debug',keys:['SAVE_DEBUG_CROPS']},
  ]},
  {id:'forcerestart', label:'Force Restart', sections:[
    {title:'Game Detection',keys:['GAME_DETECT_IMAGE','GAME_DETECT_DIFF']},
    {title:'Three-State Recovery',keys:['FORCE_NOTINGAME_WAIT','FORCE_MENU_TIMEOUT','STONE_ICON_MISSING_WAIT','MENU_RESUME_JOIN_WAIT','FORCE_PLAY_SETTLE']},
    {title:'Wrong Game / Map Search',keys:['FORCE_GAME_LOGO_IMAGE','FORCE_MAP_CODE','FORCE_MAP_SEARCH_TIMEOUT','FORCE_MAP_SEARCH_ATTEMPTS','FORCE_SELECT_TIMEOUT','FORCE_TITLE_TIMEOUT']},
    {title:'Lobby OCR Aliases',keys:['FORCE_OCR_PLAY_ALIASES']},
  ]},
];
const MODE_SETTINGS_TABS = {
  rebirth: [
    {id:'features', label:'Features', sections:[
      {title:'Features',keys:['BASE_ROCK_DRILL_PRESSES','AUTO_ROCK_MAX_GRIND_SECONDS','USE_SHORTCUTS','USE_DRILL_ON_ROCK','USE_DRILL_ON_BASEROCK','USE_DRILL_ON_A5_METEOR']},
      {title:'Manual Strength',keys:['MANUAL_STR_ONLY_LAST_ROW']},
    ]},
    {id:'bossfight', label:'Boss Fight', sections:[
      {title:'Boss Fight A1',keys:['BOSS_FIGHT_A1_AMOUNT','BOSS_FIGHT_A1_BASEROCK_THRESHOLD','BOSS_FIGHT_A1_METEOR_GRIND_SECONDS','BOSS_FIGHT_A1_MODE']},
    ]},
    {id:'quests', label:'Daily Quests', sections:[
      {title:'Daily Quests',keys:['QUEST_MINE_TIMEOUT_SECONDS','DAILY_QUEST_ALIASES','HATCH_CLOSE_MIN_PCT']},
    ]},
    {id:'finetuning', label:'Fine-Tuning', sections:[
      {title:'Manual Strength',keys:['MANUAL_STR_OPEN','MANUAL_STR_DETECTION','MANUAL_STR_STONE_TARGET','MANUAL_STR_SURGE_TARGET','MANUAL_STR_CLICK_METHOD','MANUAL_STR_CLICK_DELAY_MS','MANUAL_STR_CLICK_HOLD_MS','MANUAL_STR_BOTTOM_RIGHT_CLICKS','MANUAL_STR_BOTTOM_LEFT_CLICKS','MANUAL_STR_OPEN_AFTER_HIT_WAIT','MANUAL_STR_OPEN_AFTER_MONITOR_WAIT','MANUAL_STR_MAX_SECONDS','MANUAL_STR_IDLE_WAIT','MANUAL_STR_NO_STRENGTH_TIMEOUT','MANUAL_STR_HUD_STALL_SECONDS','MANUAL_STR_CLOSE_YELLOW_THRESH','MANUAL_STR_POST_CLOSE_SETTLE_SECONDS','MANUAL_STR_POST_CLOSE_TOPUP_SECONDS','MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS']},
      {title:'A5 Meteor',keys:['METEOR_HEALTH_CHECK','FIXED_A5_HIT_TIME']},
      {title:'Hit Controls',keys:['HIT_ROCKS','HIT_BASEROCK','HIT_A5_METEOR']},
    ]},
  ],
  delve: [
    {id:'finetuning', label:'Fine-Tuning', sections:[
      {title:'Join & Navigation',keys:['DELVE_MENU_WAIT_SECONDS','DELVE_JOIN_CLICK_GAP_SECONDS','DELVE_POST_JOIN_WAIT_SECONDS']},
      {title:'Death',keys:['DELVE_DEATH_WAIT_SECONDS']},
      {title:'Shooting',keys:['DELVE_SHOOT_POLL_SECONDS','DELVE_SHOOT_REASSERT_SECONDS']},
    ]},
  ],
  kraken: [
    {id:'finetuning', label:'Fine-Tuning', sections:[
      {title:'Kill Detection',keys:['KRAKEN_HB_CONFIRM_WINDOW_SECONDS','KRAKEN_POST_HB_LOSS_SHOOT_SECONDS','KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS']},
      {title:'Death',keys:['KRAKEN_DEATH_WAIT_SECONDS']},
      {title:'Navigation & Join',keys:['KRAKEN_MENU_WAIT_SECONDS','KRAKEN_JOIN_CLICK_GAP_SECONDS','KRAKEN_POST_JOIN_WAIT_SECONDS','KRAKEN_REWARD_OPEN_WAIT_SECONDS','KRAKEN_REWARD_WALK_SECONDS','KRAKEN_ROUTE_ATTEMPTS']},
      {title:'Shooting',keys:['KRAKEN_SHOOT_POLL_SECONDS','KRAKEN_SHOOT_REASSERT_SECONDS']},
    ]},
  ],
  zytos: [
    {id:'bossfight', label:'Boss Fight', sections:[
      {title:'Boss Mode',keys:['BOSS_FIGHT_A1_MODE']},
    ]},
    {id:'finetuning', label:'Fine-Tuning', sections:[
      {title:'Post Fight',keys:['ZYTOS_POST_KILL_WAIT_SECONDS']},
      {title:'Kill Detection',keys:['ZYTOS_HB_CONFIRM_WINDOW_SECONDS','ZYTOS_HB_EXTENDED_WINDOW_SECONDS','ZYTOS_POST_HB_LOSS_SHOOT_SECONDS','ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS']},
      {title:'Death',keys:['ZYTOS_DEATH_WAIT_SECONDS']},
      {title:'Navigation & Join',keys:['ZYTOS_MENU_WAIT_SECONDS','ZYTOS_JOIN_CLICK_GAP_SECONDS','ZYTOS_POST_JOIN_WAIT_SECONDS','ZYTOS_REWARD_OPEN_WAIT_SECONDS','ZYTOS_ROUTE_ATTEMPTS']},
      {title:'Shooting',keys:['ZYTOS_SHOOT_POLL_SECONDS','ZYTOS_SHOOT_REASSERT_SECONDS']},
    ]},
  ],
  crater: [
  ],
  farm_meteor: [
  ],
};
let _modeSettingsTab = {};
let _modeSettingsMode = '';
let _cfgValues = {};
let _cfgActiveTab='general';
let _lastPollState={};
function setConfigTab(tabId){
  _cfgActiveTab=tabId;
  // Scope to the config panel only — mode settings has its own tab system.
  const host = document.getElementById('config-panel');
  if(!host) return;
  host.querySelectorAll('.cfg-tab-btn').forEach(btn=>btn.classList.toggle('active', btn.dataset.tab===tabId));
  host.querySelectorAll('.cfg-tab-panel').forEach(panel=>panel.classList.toggle('active', panel.dataset.tab===tabId));
}
const BRAMBLE_MODE_OPTS = [
  ['solo','Solo'], ['normal','Normal'], ['hard','Hard'], ['ex','Ex']
];
const BRAMBLE_MODE_DEFAULT_OCR = {
  solo: ['SOLO'], normal: ['NORMAL'], hard: ['HARD'], ex: ['EX','EXTREME']
};
function _brambleOcrMap(values) {
  const raw = (values && values.BOSS_FIGHT_A1_MODE_OCR) || {};
  const out = {};
  for (const [k, defs] of Object.entries(BRAMBLE_MODE_DEFAULT_OCR)) {
    const src = Array.isArray(raw[k]) ? raw[k] : defs;
    out[k] = src.map(s => String(s||'').trim()).filter(Boolean);
  }
  return out;
}
const LO_ROLE_KEYS = {
  farming: 'BOSS_FIGHT_A1_LOADOUT_FARMING',
  fighting: 'BOSS_FIGHT_A1_LOADOUT_FIGHTING',
  meteor_rewards: 'CRATER_LOADOUT_METEOR_REWARDS',
  meteor_farm: 'FARM_METEOR_LOADOUT',
};
function _loSlotOf(values, role) {
  const v = String((values && values[LO_ROLE_KEYS[role]]) || 'none').trim().toLowerCase();
  return ['1','2','3','4','5','6'].includes(v) ? v : 'none';
}
function _loRoleOfSlot(values, slot) {
  const s = String(slot);
  if (_loSlotOf(values, 'farming') === s) return 'farming';
  if (_loSlotOf(values, 'fighting') === s) return 'fighting';
  if (_loSlotOf(values, 'meteor_rewards') === s) return 'meteor_rewards';
  if (_loSlotOf(values, 'meteor_farm') === s) return 'meteor_farm';
  return 'none';
}
function renderLoadoutGrid(values) {
  const v = values || _cfgValues || {};
  const hiddens = Object.values(LO_ROLE_KEYS).map(k => {
    const cur = ['none','1','2','3','4','5','6'].includes(String(v[k]||'none').trim().toLowerCase())
      ? String(v[k]).trim().toLowerCase() : 'none';
    return `<input type="hidden" class="cfg-input" id="cfg_${k}" value="${cur}">`;
  }).join('');
  const slots = [1,2,3,4,5,6].map(n => {
    const role = _loRoleOfSlot(v, n);
    const opts = [
      ['none','None'],
      ['farming','Farming'],
      ['fighting','Fighting'],
      ['meteor_rewards','Meteor Rewards'],
    ].map(([val,lbl]) => `<option value="${val}" ${val===role?'selected':''}>${lbl}</option>`).join('');
    return `<div class="lo-slot" data-slot="${n}" data-role="${role}">
      <div class="lo-slot-win">${n}</div>
      <select onchange="loadoutSlotChanged(${n}, this.value)">${opts}</select>
    </div>`;
  }).join('');
  return `<div class="cfg-group">
    ${hiddens}
    <div class="cfg-label-row"><span class="cfg-label">In-game loadouts</span><span class="cfg-info-icon tip-anchor" data-tip="Each slot is one of your six Fortnite loadouts. A type can only sit on one slot — picking Farming on 5 clears it from 2." tabindex="0">${INFO_ICON}</span></div>
    <div class="lo-grid">${slots}</div>
  </div>`;
}
function loadoutSlotChanged(slot, role) {
  slot = String(slot);
  role = String(role || 'none').toLowerCase();
  if (!_cfgValues) _cfgValues = {};
  if (role !== 'none' && LO_ROLE_KEYS[role]) {
    const prev = _loSlotOf(_cfgValues, role);
    if (prev !== 'none' && prev !== slot) {
      /* previous slot of this type becomes None automatically */
    }
    Object.keys(LO_ROLE_KEYS).forEach(r => {
      if (_loSlotOf(_cfgValues, r) === slot) _cfgValues[LO_ROLE_KEYS[r]] = 'none';
    });
    _cfgValues[LO_ROLE_KEYS[role]] = slot;
  } else {
    Object.keys(LO_ROLE_KEYS).forEach(r => {
      if (_loSlotOf(_cfgValues, r) === slot) _cfgValues[LO_ROLE_KEYS[r]] = 'none';
    });
  }
  const host = document.querySelector('.lo-grid');
  if (!host) return;
  const wrap = host.closest('.cfg-group');
  if (!wrap) return;
  const next = document.createElement('div');
  next.innerHTML = renderLoadoutGrid(_cfgValues);
  wrap.replaceWith(next.firstElementChild);
}

// ── Daily Quests alias editor (dropdown of quest kinds + per-alias rows) ────
const QUEST_ALIAS_KINDS = [
  ['rocks','Break N Star Rocks'],
  ['chests','Open Chests'],
  ['hatch','Hatch Pets'],
  ['combine','Combine Pets'],
  ['area1egg','Hatch GUI: Area 1 Egg'],
];
const QUEST_ALIAS_KIND_META = {
  rocks:   { key:'DAILY_QUEST_ALIASES',
             tip:"OCR aliases for the Break X Star Rocks daily quest. Use {$NUMBER} where the rock-count digit sits (e.g. BREAK {$NUMBER} STAR ROCKS) — the digit picks which break_N_star_rocks macro runs. Add translated names with +. Matching is case-insensitive and ignores spaces." },
  chests:  { key:'QUEST_MIMIC_ALIASES',
             tip:'OCR aliases for the Open Chests daily quest. The bot plays mimic.macro for it once a fresh run. Add translated names with +. Matching is case-insensitive and ignores spaces.' },
  hatch:   { key:'QUEST_HATCH_ALIASES',
             tip:'OCR aliases for the Hatch Pets daily quest. Accepted only when a Break Star Rocks quest is also on the board (eggs drop from rocks). The bot teleports to base, opens the hatch GUI at the NPC and hatches all Area 1 eggs. Matching is case-insensitive, ignores spaces, and tolerates small OCR junk between words (e.g. "Hatch 5 Pets").' },
  combine: { key:'QUEST_COMBINE_ALIASES',
             tip:'OCR aliases for the Combine Pets daily quest. Accepted only when a Break Star Rocks quest is also on the board. The bot hatches pets first (if needed), then runs the F4 monitor-menu auto combine. Matching is case-insensitive, ignores spaces, and tolerates small OCR junk between words (e.g. "Combine 5 Pets").' },
  area1egg:{ key:'HATCH_AREA1_ALIASES',
             tip:'OCR aliases for the "Area 1 Egg" page title in the hatch GUI. The bot pages through the GUI with Next until a page matches, then clicks Hatch All. Add translated names with +.' },
};
let _questAliasKind = 'rocks';
function _questAliasKey(){ return (QUEST_ALIAS_KIND_META[_questAliasKind]||QUEST_ALIAS_KIND_META.rocks).key; }
function _questAliasArr(values){
  const v = values[_questAliasKey()];
  return Array.isArray(v) ? v.map(String).map(x=>x.trim()).filter(Boolean)
       : String(v||'').split('|').map(x=>x.trim()).filter(Boolean);
}
// ── Force Restart lobby OCR aliases — same dropdown + rows + add UI as
// the quest aliases. Stored as comma-separated strings in config
// (FORCE_OCR_*_ALIASES), rendered as editable rows per kind.
const FORCE_ALIAS_KINDS = [
  ['play',  'PLAY button'],
  ['title', 'Game title'],
  ['search','Search Discover'],
  ['select','SELECT button'],
];
const FORCE_ALIAS_KIND_META = {
  play:  { key:'FORCE_OCR_PLAY_ALIASES' },
  title: { key:'FORCE_OCR_TITLE_ALIASES' },
  search:{ key:'FORCE_OCR_SEARCH_ALIASES' },
  select:{ key:'FORCE_OCR_SELECT_ALIASES' },
};
let _forceAliasKind = 'play';
function _forceAliasKey(){ return (FORCE_ALIAS_KIND_META[_forceAliasKind]||FORCE_ALIAS_KIND_META.play).key; }
function _forceAliasArr(values){
  const v = values[_forceAliasKey()];
  return Array.isArray(v) ? v.map(String).map(x=>x.trim()).filter(Boolean)
       : String(v||'').split(',').map(x=>x.trim()).filter(Boolean);
}
function renderForceAliasField(values) {
  const kind = FORCE_ALIAS_KINDS.some(([v])=>v===_forceAliasKind) ? _forceAliasKind : 'play';
  const opts = FORCE_ALIAS_KINDS.map(([v,l])=>`<option value="${v}" ${v===kind?'selected':''}>${l}</option>`).join('');
  const aliases = _forceAliasArr(values);
  const rows = aliases.map((a,i)=>`
    <div class="ocr-alias-row">
      <input class="cfg-input ocr-alias-input" data-idx="${i}" value="${_escapeHtml(a)}" onchange="forceAliasEdit(${i}, this.value)">
      <button type="button" class="ocr-alias-btn minus" title="Remove" onclick="forceAliasRemove(${i})">-</button>
    </div>`).join('');
  const tip = CFG_TOOLTIPS[_forceAliasKey()] || 'Lobby OCR aliases.';
  return `<div class="cfg-group" id="force-alias-field">
    <div class="cfg-label-row"><span class="cfg-label">Lobby OCR aliases</span><span class="cfg-info-icon tip-anchor" data-tip="${_escapeHtml(tip)}" tabindex="0">${INFO_ICON}</span></div>
    <select class="cfg-input" id="force_alias_kind" onchange="forceAliasKindChanged(this.value)">${opts}</select>
    <div id="force-alias-list">${rows}</div>
    <div class="ocr-add-row">
      <input class="cfg-input" id="force-alias-add" placeholder="Add alias">
      <button type="button" class="ocr-alias-btn" title="Add" onclick="forceAliasAdd()">+</button>
    </div>
  </div>`;
}
function forceAliasKindChanged(kind) {
  _forceAliasKind = kind;
  const host = document.getElementById('force-alias-field');
  if (!host) return;
  const wrap = document.createElement('div');
  wrap.innerHTML = renderForceAliasField(_cfgValues);
  host.replaceWith(wrap.firstElementChild);
  _bindFloatingTooltips(document.getElementById('force-alias-field'));
}
function forceAliasEdit(idx, value) {
  const k = _forceAliasKey();
  const arr = _forceAliasArr(_cfgValues);
  if (arr[idx] === undefined) return;
  arr[idx] = String(value||'').trim();
  _cfgValues[k] = arr.join(',');
}
function forceAliasRemove(idx) {
  const k = _forceAliasKey();
  _cfgValues[k] = _forceAliasArr(_cfgValues).filter((_,i)=>i!==idx).join(',');
  forceAliasKindChanged(_forceAliasKind);
}
function forceAliasAdd() {
  const inp = document.getElementById('force-alias-add');
  const val = inp ? String(inp.value||'').trim() : '';
  if (!val) return;
  const k = _forceAliasKey();
  const arr = _forceAliasArr(_cfgValues);
  arr.push(val);
  _cfgValues[k] = arr.join(',');
  forceAliasKindChanged(_forceAliasKind);
}
function renderQuestAliasField(values) {
  if(!QUEST_ALIAS_KINDS.some(([v])=>v===_questAliasKind)) _questAliasKind='rocks';
  const kind = _questAliasKind;
  const opts = QUEST_ALIAS_KINDS.map(([v,l])=>`<option value="${v}" ${v===kind?'selected':''}>${l}</option>`).join('');
  const aliases = _questAliasArr(values);
  const rows = aliases.map((a,i)=>`
    <div class="ocr-alias-row">
      <input class="cfg-input ocr-alias-input" data-idx="${i}" value="${_escapeHtml(a)}" onchange="questAliasEdit(${i}, this.value)">
      <button type="button" class="ocr-alias-btn minus" title="Remove" onclick="questAliasRemove(${i})">-</button>
    </div>`).join('');
  const tip = (QUEST_ALIAS_KIND_META[kind]||QUEST_ALIAS_KIND_META.rocks).tip;
  return `<div class="cfg-group" id="quest-alias-field">
    <div class="cfg-label-row"><span class="cfg-label">Quest aliases</span><span class="cfg-info-icon tip-anchor" data-tip="${_escapeHtml(tip)}" tabindex="0">${INFO_ICON}</span></div>
    <select class="cfg-input" id="quest_alias_kind" onchange="questAliasKindChanged(this.value)">${opts}</select>
    <div id="quest-alias-list">${rows}</div>
    <div class="ocr-add-row">
      <input class="cfg-input" id="quest-alias-add" placeholder="Add alias">
      <button type="button" class="ocr-alias-btn" title="Add" onclick="questAliasAdd()">+</button>
    </div>
  </div>`;
}
function questAliasKindChanged(kind) {
  _questAliasKind = kind;
  const host = document.getElementById('quest-alias-field');
  if (!host) return;
  const wrap = document.createElement('div');
  wrap.innerHTML = renderQuestAliasField(_cfgValues);
  host.replaceWith(wrap.firstElementChild);
  _bindFloatingTooltips(document.getElementById('quest-alias-field'));
}
function questAliasEdit(idx, value) {
  const k = _questAliasKey();
  const arr = _questAliasArr(_cfgValues);
  if (arr[idx] === undefined) return;
  arr[idx] = String(value||'').trim();
  _cfgValues[k] = arr;
}
function questAliasRemove(idx) {
  const k = _questAliasKey();
  _cfgValues[k] = _questAliasArr(_cfgValues).filter((_,i)=>i!==idx);
  questAliasKindChanged(_questAliasKind);
}
function questAliasAdd() {
  const inp = document.getElementById('quest-alias-add');
  const val = inp ? String(inp.value||'').trim() : '';
  if (!val) return;
  const k = _questAliasKey();
  const arr = _questAliasArr(_cfgValues);
  arr.push(val);
  _cfgValues[k] = arr;
  questAliasKindChanged(_questAliasKind);
}

function renderBrambleModeField(values) {
  const cur = String(values.BOSS_FIGHT_A1_MODE||'normal').toLowerCase();
  const mode = BRAMBLE_MODE_OPTS.some(([v])=>v===cur) ? cur : 'normal';
  const ocr = _brambleOcrMap(values);
  const opts = BRAMBLE_MODE_OPTS.map(([v,l]) => `<option value="${v}" ${v===mode?'selected':''}>${l}</option>`).join('');
  const aliases = ocr[mode] || [];
  const rows = aliases.map((a,i)=>`
    <div class="ocr-alias-row">
      <input class="cfg-input ocr-alias-input" data-idx="${i}" value="${_escapeHtml(a)}" onchange="brambleAliasEdit(${i}, this.value)">
      <button type="button" class="ocr-alias-btn minus" title="Remove" onclick="brambleAliasRemove(${i})">-</button>
    </div>`).join('');
  return `<div class="cfg-group" id="bramble-mode-field">
    <div class="cfg-label-row"><span class="cfg-label">Mode</span><span class="cfg-info-icon tip-anchor" data-tip="${_escapeHtml(CFG_TOOLTIPS.BOSS_FIGHT_A1_MODE)}" tabindex="0">${INFO_ICON}</span></div>
    <select class="cfg-input" id="cfg_BOSS_FIGHT_A1_MODE" onchange="brambleModeChanged(this.value)">${opts}</select>
    <div class="cfg-label-row" style="margin-top:8px;"><span class="cfg-label">OCR aliases for ${mode}</span><span class="cfg-info-icon tip-anchor" data-tip="${_escapeHtml(CFG_TOOLTIPS.BOSS_FIGHT_A1_MODE_OCR)}" tabindex="0">${INFO_ICON}</span></div>
    <div id="bramble-ocr-list">${rows}</div>
    <div class="ocr-add-row">
      <input class="cfg-input" id="bramble-ocr-add" placeholder="Add translated name">
      <button type="button" class="ocr-alias-btn" title="Add" onclick="brambleAliasAdd()">+</button>
    </div>
  </div>`;
}
function brambleModeChanged(mode) {
  _cfgValues.BOSS_FIGHT_A1_MODE = mode;
  const host = document.getElementById('bramble-mode-field');
  if (!host) return;
  const wrap = document.createElement('div');
  wrap.innerHTML = renderBrambleModeField(_cfgValues);
  host.replaceWith(wrap.firstElementChild);
  _bindFloatingTooltips(document.getElementById('bramble-mode-field'));
}
function brambleAliasEdit(idx, value) {
  const mode = String(_cfgValues.BOSS_FIGHT_A1_MODE||'normal').toLowerCase();
  const ocr = _brambleOcrMap(_cfgValues);
  if (!ocr[mode]) ocr[mode] = [];
  ocr[mode][idx] = String(value||'').trim();
  _cfgValues.BOSS_FIGHT_A1_MODE_OCR = ocr;
}
function brambleAliasRemove(idx) {
  const mode = String(_cfgValues.BOSS_FIGHT_A1_MODE||'normal').toLowerCase();
  const ocr = _brambleOcrMap(_cfgValues);
  ocr[mode] = (ocr[mode]||[]).filter((_,i)=>i!==idx);
  _cfgValues.BOSS_FIGHT_A1_MODE_OCR = ocr;
  brambleModeChanged(mode);
}
function brambleAliasAdd() {
  const inp = document.getElementById('bramble-ocr-add');
  const val = inp ? String(inp.value||'').trim() : '';
  if (!val) return;
  const mode = String(_cfgValues.BOSS_FIGHT_A1_MODE||'normal').toLowerCase();
  const ocr = _brambleOcrMap(_cfgValues);
  const have = (ocr[mode]||[]).map(s=>s.toUpperCase());
  if (!have.includes(val.toUpperCase())) ocr[mode].push(val);
  _cfgValues.BOSS_FIGHT_A1_MODE_OCR = ocr;
  if (inp) inp.value = '';
  brambleModeChanged(mode);
}
function renderConfigField(key, values) {
  const s=_cfgSchema.find(x=>x.key===key); if(!s)return '';
  const tip=CFG_TOOLTIPS[key]||s.label;
  const shortLabel=_repairMojibake(s.label).replace(/ \(.*$/,'');
  const tipEsc = _escapeHtml(_repairMojibake(tip));
  const labelHtml=`<div class="cfg-label-row"><span class="cfg-label">${shortLabel}</span><span class="cfg-info-icon tip-anchor" data-tip="${tipEsc}" tabindex="0">${INFO_ICON}</span></div>`;
  if(s.type==='bool'){
    const cur = values[key]===true || String(values[key]).toLowerCase()==='true';
    let onchange = '';
    if(key==='METEOR_HEALTH_CHECK') onchange = ' onchange="onMeteorHealthCheckChange(this.checked)"';
    return `<div class="cfg-group"><div class="cfg-check-row"><input class="cfg-input" type="checkbox" id="cfg_${key}" ${cur?'checked':''}${onchange}><label for="cfg_${key}" style="font-size:12px;">${shortLabel}</label><span class="cfg-info-icon tip-anchor" style="margin-left:2px;" data-tip="${tipEsc}" tabindex="0">${INFO_ICON}</span></div></div>`;
  }
  if(CFG_SLIDERS[key]){
    const sl=CFG_SLIDERS[key];
    const val=parseFloat(values[key]??sl.min).toFixed(1);
    return `<div class="cfg-group">${labelHtml}<div class="cfg-slider-row"><input class="cfg-slider" type="range" id="cfg_sl_${key}" min="${sl.min}" max="${sl.max}" step="${sl.step}" value="${val}" oninput="document.getElementById('cfg_${key}').value=parseFloat(this.value).toFixed(1)"><input class="cfg-slider-input" id="cfg_${key}" value="${val}" oninput="document.getElementById('cfg_sl_${key}').value=this.value"></div></div>`;
  }
  if(CFG_KEYBIND_FIELDS.has(key)){
    return `<div class="cfg-group">${labelHtml}${renderKeybindSelect(key, values[key])}</div>`;
  }
  if(key==='BOSS_FIGHT_A1_LOADOUT_FIGHTING'){
    return renderLoadoutGrid(values);
  }
  if(key==='BOSS_FIGHT_A1_LOADOUT_FARMING'||key==='CRATER_LOADOUT_METEOR_REWARDS'||key==='FARM_METEOR_LOADOUT') return '';
  if(key==='BOSS_FIGHT_A1_MODE'){
    return renderBrambleModeField(values);
  }
  if(key==='MANUAL_STR_DETECTION'){
    const cur = String(values[key]||'stone').toLowerCase()==='surge' ? 'surge' : 'stone';
    return `<div class="cfg-group">${labelHtml}<select class="cfg-input" id="cfg_${key}" onchange="onManualStrDetectionChange(this.value)">
      <option value="stone"${cur==='stone'?' selected':''}>Stone</option>
      <option value="surge"${cur==='surge'?' selected':''}>Surge level</option>
    </select></div>`;
  }
  if(key==='MANUAL_STR_CLICK_METHOD'){
    const cur = String(values[key]||'default').toLowerCase()==='classic' ? 'classic' : (String(values[key]||'').toLowerCase()==='compat' ? 'compat' : 'default');
    return `<div class="cfg-group">${labelHtml}<select class="cfg-input" id="cfg_${key}">
      <option value="default"${cur==='default'?' selected':''}>Default</option>
      <option value="classic"${cur==='classic'?' selected':''}>Classic (original pacing)</option>
      <option value="compat"${cur==='compat'?' selected':''}>Compat (slow clicks - drop-proof)</option>
    </select></div>`;
  }
  if(key==='MANUAL_STR_STONE_TARGET'){
    const show = String(values['MANUAL_STR_DETECTION']||'stone').toLowerCase() !== 'surge';
    const v = Number(values[key]);
    const shown = (!values[key] || v===0) ? '1.36e152' : String(values[key]).replace('e+','e');
    return `<div id="cfg_dep_MANUAL_STR_STONE_TARGET" style="display:${show?'':'none'};"><div class="cfg-group">${labelHtml}<input class="cfg-input" id="cfg_${key}" value="${shown}"></div></div>`;
  }
  if(key==='MANUAL_STR_SURGE_TARGET'){
    const show = String(values['MANUAL_STR_DETECTION']||'stone').toLowerCase() === 'surge';
    return `<div id="cfg_dep_MANUAL_STR_SURGE_TARGET" style="display:${show?'':'none'};"><div class="cfg-group">${labelHtml}<input class="cfg-input" id="cfg_${key}" value="${values[key]??160}"></div></div>`;
  }
  if(key==='FIXED_A5_HIT_TIME'){
    const showHC = values['METEOR_HEALTH_CHECK']===false;
    return `<div id="cfg_dep_FIXED_A5_HIT_TIME" style="display:${showHC?'':'none'};"><div class="cfg-group">${labelHtml}<input class="cfg-input" id="cfg_${key}" value="${values[key]??''}"></div></div>`;
  }
  if(key==='BOSS_FIGHT_A1_MODE_OCR') return '';
  if(key==='GAME_DETECT_IMAGE'){
    const v = String(values[key]||'').trim();
    const set = !!v;
    const prev = set ? '/game_detect/preview' : '';
    const btnStyle = "padding:5px 12px;border-radius:7px;border:1px solid var(--border);background:transparent;color:var(--text);cursor:pointer;font:12px 'Segoe UI',sans-serif";
    return `<div class="cfg-group">${labelHtml}<div style="display:flex;align-items:center;gap:8px">`
      + `<img id="gd_preview" src="${prev}" style="width:44px;height:32px;object-fit:contain;border:1px solid var(--border);border-radius:5px;background:#14141c" onerror="this.style.visibility='hidden'">`
      + `<span id="gd_name" style="flex:1;font:11.5px 'Segoe UI',sans-serif;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${set?_escapeHtml(v):'not set'}</span>`
      + `<button type="button" id="gd_pick_btn" style="${btnStyle}" onclick="gameDetectPickImage()" title="Pick this image from the screen (F2). The box and point are recorded with it and save immediately.">${set?'Change':'Pick'}</button>`
      + (set?`<button type="button" id="gd_clear_btn" style="${btnStyle}" onclick="gameDetectClearImage()">Clear</button>`:'')
      + `</div><input type="hidden" id="cfg_GAME_DETECT_IMAGE" value="${_escapeHtml(v)}"></div>`;
  }
  if(key==='GAME_DETECT_BOX'||key==='GAME_DETECT_SCREEN') return '';
  if(key==='FORCE_GAME_LOGO_IMAGE'){
    const v = String(values[key]||'').trim();
    const set = !!v;
    const prev = set ? '/game_detect/preview?tmpl=game_logo' : '';
    const btnStyle = "padding:5px 12px;border-radius:7px;border:1px solid var(--border);background:transparent;color:var(--text);cursor:pointer;font:12px 'Segoe UI',sans-serif";
    return `<div class="cfg-group">${labelHtml}<div style="display:flex;align-items:center;gap:8px">`
      + `<img id="glogo_preview" src="${prev}" style="width:44px;height:32px;object-fit:contain;border:1px solid var(--border);border-radius:5px;background:#14141c" onerror="this.style.visibility='hidden'">`
      + `<span id="glogo_name" style="flex:1;font:11.5px 'Segoe UI',sans-serif;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${set?_escapeHtml(v):'not set'}</span>`
      + `<button type="button" id="glogo_pick_btn" style="${btnStyle}" onclick="gameLogoPickImage()" title="Pick the Miner Tycoon 2 billboard from the map-search results (F2). The box and point are recorded with the image and save immediately.">${set?'Change':'Pick'}</button>`
      + (set?`<button type="button" id="glogo_clear_btn" style="${btnStyle}" onclick="gameLogoClearImage()">Clear</button>`:'')
      + `</div><input type="hidden" id="cfg_FORCE_GAME_LOGO_IMAGE" value="${_escapeHtml(v)}"></div>`;
  }
  if(key==='FORCE_GAME_LOGO_BOX'||key==='FORCE_GAME_LOGO_SCREEN') return '';
  if(key==='DAILY_QUEST_ALIASES'){
    return renderQuestAliasField(values);
  }
  if(key==='QUEST_MIMIC_ALIASES') return '';
  if(key==='QUEST_HATCH_ALIASES'||key==='QUEST_COMBINE_ALIASES'||key==='HATCH_AREA1_ALIASES') return '';
  if(key==='FORCE_OCR_PLAY_ALIASES') return renderForceAliasField(values);
  if(key==='FORCE_OCR_TITLE_ALIASES'||key==='FORCE_OCR_SEARCH_ALIASES'||key==='FORCE_OCR_SELECT_ALIASES') return '';
  if(s.type==='json'){
    let jv = values[key] ?? [];
    if (typeof jv !== 'string') { try { jv = JSON.stringify(jv); } catch (e) { jv = '[]'; } }
    return `<div class="cfg-group">${labelHtml}<input class="cfg-input" id="cfg_${key}" value="${_escapeHtml(jv)}"></div>`;
  }
  return `<div class="cfg-group">${labelHtml}<input class="cfg-input" id="cfg_${key}" value="${values[key]??''}"></div>`;
}
function onManualStrDetectionChange(val){
  const isSurge = String(val||'stone').toLowerCase()==='surge';
  const stone = document.getElementById('cfg_dep_MANUAL_STR_STONE_TARGET');
  const surge = document.getElementById('cfg_dep_MANUAL_STR_SURGE_TARGET');
  if (stone) stone.style.display = isSurge ? 'none' : '';
  if (surge) surge.style.display = isSurge ? '' : 'none';
}
function onMeteorHealthCheckChange(checked){
  const wrap = document.getElementById('cfg_dep_FIXED_A5_HIT_TIME');
  if (wrap) wrap.style.display = checked ? 'none' : '';
}
function renderConfigForm(values) {
  const showTabs = CFG_TABS.length > 1;
  if(!showTabs) _cfgActiveTab = CFG_TABS[0] ? CFG_TABS[0].id : 'general';
  else if(!CFG_TABS.some(t=>t.id===_cfgActiveTab)) _cfgActiveTab=CFG_TABS[0].id;
  const tabs=document.getElementById('config-tabs');
  if(tabs){
    if(!showTabs){
      tabs.innerHTML='';
      tabs.hidden = true;
    } else {
      tabs.hidden = false;
      tabs.innerHTML=CFG_TABS.map(tab=>`<button class="cfg-tab-btn ${tab.id===_cfgActiveTab?'active':''}" data-tab="${tab.id}" onclick="setConfigTab('${tab.id}')">${tab.label}</button>`).join('');
    }
  }
  let html='';
  for(const tab of CFG_TABS){
    html+=`<div class="cfg-tab-panel ${tab.id===_cfgActiveTab?'active':''}" data-tab="${tab.id}">`;
    const visibleSections = tab.sections
      .map(sec => ({ sec, fields: sec.keys.map(key=>renderConfigField(key, values)).filter(Boolean) }))
      .filter(x => x.fields.length > 0);
    const hideSectionTitles = tab.id!=='tracker' && visibleSections.length <= 1;
    for(const item of visibleSections){
      if(!hideSectionTitles){
        html+=`<div class="cfg-section-title">${item.sec.title}</div>`;
      }
      html+=item.fields.join('');
      if(!hideSectionTitles){
        html+='<hr class="cfg-section-sep">';
      }
    }
    if(tab.id==='general'){
      html+=`<div class="cfg-section-title">Setup</div>
        <button type="button" class="fs-reopen-btn" onclick="openFirstSteps(true)">Open First Steps</button>
        <div style="font-size:11px;color:var(--muted);line-height:1.45;">Replay the first-launch setup guide (sensitivity, windowed fullscreen, HUD, pickaxe). Screenshots can be dropped into data/first_steps/ later.</div>`;
    }
    if(tab.id==='tracker'){
      html+=`
        <div class="cfg-section-title">Local Data</div>        <div class="cfg-section-title">Local Data</div>
        <button type="button" class="fs-reopen-btn btn-danger-cfg" onclick="confirmDeleteAll()">Delete Stats</button>
        <div style="font-size:11px;color:var(--muted);line-height:1.45;margin-top:6px;">Clears dashboard run history for the current mode. Cannot be undone.</div>`;
    }
    html+='</div>';
  }
  document.getElementById('config-form').innerHTML=html;
  _bindFloatingTooltips(document.getElementById('config-form'));
}
function fmtEtaSpan(secs){
  if(!Number.isFinite(secs) || secs<0) return '—';
  if(secs<60) return '<1m';
  const MIN=60, H=3600, D=86400, MO=30*D, Y=365*D;
  let left=Math.round(secs);
  const y=Math.floor(left/Y); left%=Y;
  const mo=Math.floor(left/MO); left%=MO;
  const d=Math.floor(left/D); left%=D;
  const h=Math.floor(left/H); left%=H;
  const m=Math.floor(left/MIN);
  const parts=[];
  if(y) parts.push(y+'y');
  if(mo) parts.push(mo+'mo');
  if(d) parts.push(d+'d');
  if(h) parts.push(h+'h');
  if(m || !parts.length) parts.push(m+'m');
  return parts.join(' ');
}
async function saveConfig() {
  const updates={};
  for(const s of _cfgSchema){
    if(s.key==='BOSS_FIGHT_A1_MODE_OCR'){
      updates[s.key]=_brambleOcrMap(_cfgValues);
      continue;
    }
    if(s.key==='DAILY_QUEST_ALIASES'||s.key==='QUEST_MIMIC_ALIASES'||s.key==='QUEST_HATCH_ALIASES'||s.key==='QUEST_COMBINE_ALIASES'||s.key==='HATCH_AREA1_ALIASES'){
      const v = _cfgValues[s.key];
      updates[s.key] = Array.isArray(v) ? v.map(String).map(x=>x.trim()).filter(Boolean) : String(v||'');
      continue;
    }
    if(s.key==='FORCE_OCR_PLAY_ALIASES'||s.key==='FORCE_OCR_TITLE_ALIASES'||s.key==='FORCE_OCR_SEARCH_ALIASES'||s.key==='FORCE_OCR_SELECT_ALIASES'){
      updates[s.key] = String(_cfgValues[s.key]||'');
      continue;
    }
    if(s.key==='WEAPON_2_BINDING'){
      const mon=document.getElementById('cfg_MONITOR_ITEM_BINDING');
      if(mon){ updates[s.key]=mon.value; continue; }
    }
    const el=document.getElementById('cfg_'+s.key);
    if(!el)continue;
    if(s.type==='bool'){ updates[s.key] = el.type==='checkbox' ? !!el.checked : String(el.value).toLowerCase()==='true'; }
    else if(s.type==='int'){ updates[s.key]=parseInt(el.value, 10); }
    else if(s.type==='float'){ updates[s.key]=parseFloat(el.value); }
    else { updates[s.key]=el.value; }
  }
  if(updates.MONITOR_ITEM_BINDING && !updates.WEAPON_2_BINDING) updates.WEAPON_2_BINDING = updates.MONITOR_ITEM_BINDING;
  try {
    const r=await postJson('/config', {updates});
    const d=await r.json();
    const st=document.getElementById('cfg-status');
    if(d.ok){st.style.display='block';st.style.color='var(--green)';st.textContent='Saved & applied';setTimeout(()=>st.style.display='none',2500); _flashModeSettingsStatus('Saved & applied', true);
      try {
        const frame = document.getElementById('recorder-frame');
        if (frame && frame.contentWindow) {
          frame.contentWindow.postMessage({
            type: 'bot-config',
            sensitivity: {
              SENS_USER_H: updates.USER_SENS_H,
              SENS_USER_V: updates.USER_SENS_V,
              USER_SENS_H: updates.USER_SENS_H,
              USER_SENS_V: updates.USER_SENS_V,
            },
            record_binding: updates.RECORDER_RECORD_BINDING,
            play_binding: updates.RECORDER_PLAY_BINDING,
          }, '*');
        }
      } catch (e) {}
    }
    else{st.style.display='block';st.style.color='var(--red)';st.textContent='Save failed: '+_repairMojibake(d.error || 'Unknown error');setTimeout(()=>st.style.display='none',3000); _flashModeSettingsStatus('Save failed', false);}
  } catch(e){alert('Save failed: '+_repairMojibake(e.message || 'Unknown error'));}
}
function _currentBotMode() {
  const sel = document.getElementById('bot-mode-select');
  const v = (sel && sel.value) || (_lastPollState && _lastPollState.bot_mode) || 'rebirth';
  return (v==='delve'||v==='kraken'||v==='zytos'||v==='crater'||v==='farm_meteor') ? v : 'rebirth';
}
function setModeSettingsTab(tabId) {
  const mode = _currentBotMode();
  _modeSettingsTab[mode] = tabId;
  const host = mode === 'crater' ? document.getElementById('crater-mode-settings') : (mode === 'farm_meteor' ? document.getElementById('meteor-mode-settings') : document.getElementById('mode-settings'));
  if (!host) return;
  host.querySelectorAll('.cfg-tab-btn').forEach(btn=>btn.classList.toggle('active', btn.dataset.tab===tabId));
  host.querySelectorAll('.cfg-tab-panel').forEach(panel=>panel.classList.toggle('active', panel.dataset.tab===tabId));
}
function _modeSettingsTargets() {
  const mode = _currentBotMode();
  if (mode === 'farm_meteor') {
    return {
      cats: document.getElementById('meteor-mode-settings-cats'),
      body: document.getElementById('meteor-mode-settings-body'),
      status: document.getElementById('meteor-mode-settings-status'),
    };
  }
  if (mode === 'crater') {
    return {
      cats: document.getElementById('crater-mode-settings-cats'),
      body: document.getElementById('crater-mode-settings-body'),
      status: document.getElementById('crater-mode-settings-status'),
    };
  }
  return {
    cats: document.getElementById('mode-settings-cats'),
    body: document.getElementById('mode-settings-body'),
    status: document.getElementById('mode-settings-status'),
  };
}
function renderModeSettings() {
  const mode = _currentBotMode();
  _modeSettingsMode = mode;
  const tabs = MODE_SETTINGS_TABS[mode] || MODE_SETTINGS_TABS.rebirth;
  const active = _modeSettingsTab[mode] || (tabs[0] && tabs[0].id) || 'features';
  _modeSettingsTab[mode] = tabs.some(t=>t.id===active) ? active : (tabs[0] && tabs[0].id);
  const t = _modeSettingsTargets();
  if (!t.cats || !t.body) return;
  const values = _cfgValues || {};
  t.cats.innerHTML = tabs.map(tab=>`<button class="cfg-tab-btn ${tab.id===_modeSettingsTab[mode]?'active':''}" data-tab="${tab.id}" onclick="setModeSettingsTab('${tab.id}')">${tab.label}</button>`).join('');
  let html = '';
  for (const tab of tabs) {
    html += `<div class="cfg-tab-panel ${tab.id===_modeSettingsTab[mode]?'active':''}" data-tab="${tab.id}">`;
    const visibleSections = tab.sections
      .map(sec => ({ sec, fields: sec.keys.map(key=>renderConfigField(key, values)).filter(Boolean) }))
      .filter(x => x.fields.length > 0);
    if (!visibleSections.length) {
      html += `<div style="color:var(--muted);font-size:12px;">No extra settings for this category yet.</div>`;
    }
    const hideSectionTitles = visibleSections.length <= 1;
    for (const item of visibleSections) {
      if (!hideSectionTitles) html += `<div class="cfg-section-title">${item.sec.title}</div>`;
      html += item.fields.join('');
    }
    html += `</div>`;
  }
  t.body.innerHTML = html;
  _bindFloatingTooltips(t.body);
}
function _flashModeSettingsStatus(msg, ok) {
  const el = _modeSettingsTargets().status;
  if (!el) return;
  el.style.color = ok ? 'var(--green)' : 'var(--red)';
  el.textContent = msg;
  setTimeout(()=>{ if (el.textContent === msg) el.textContent = ''; }, 2500);
}
async function saveModeSettings() {
  await saveConfig();
}

const FIRST_STEPS_PAGES = [
  {
    label: 'Sensitivity',
    html: `<p>Copy your in-game Fortnite mouse sensitivity into the bot Config. Open Fortnite Settings → Mouse and match Horizontal / Vertical % with Config → General → Fortnite Sensitivity. Macros were recorded at 17%.</p>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Fortnite Settings — mouse sensitivity</div>${fsShot('01_fortnite_sensitivity.png','Fortnite Settings where Horizontal / Vertical sensitivity is')}</div>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Bot Config — top right, sensitivity fields</div>${fsShot('01_config_sensitivity.png','Config button (top right) with sensitivity setting open')}</div>`
  },
  {
    label: 'Windowed Fullscreen Mode',
    html: `<p>Set Fortnite display mode to <b>Windowed Fullscreen</b>. Exclusive fullscreen can block HUD OCR readings and mouse movements from macros.</p>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Fortnite Settings — Windowed Fullscreen</div>${fsShot('02_windowed_fullscreen.png','Fortnite display mode set to Windowed Fullscreen')}</div>`
  },
  {
    label: 'Colorblind and HUD Scale',
    html: `<p>Color Blind Mode must stay <b>Off</b> (default). HUD Scale must be <b>100%</b>. Other values shift OCR regions and health-bar detection.</p>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Color Blind Mode = Off</div>${fsShot('03_colorblind.png','Fortnite Color Blind Mode set to Off')}</div>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">HUD Scale = 100%</div>${fsShot('03_hud_scale.png','Fortnite HUD Scale at 100%')}</div>`
  },
  {
    label: 'Quick Swap Pickaxe',
    html: `<p>Keep your regular Pickaxe keybind (default <b>F</b>). In the Misc tab, <b>Toggle Pickaxe (Press) / Gizmos (Hold)</b> must be unbound — or bound to a different key than Pickaxe (the screenshot uses <b>L</b>). If both use the same key, the bot's pickaxe press swaps back and forth.</p>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Combat — Pickaxe (Press) = F</div>${fsShot('04_pickaxe_keybind.png','Fortnite Combat: Pickaxe (Press) / Gizmos (Hold) on F')}</div>
      <div class="fs-shot-wrap"><div class="fs-shot-cap">Misc — Toggle Pickaxe on a different key (or unbound)</div>${fsShot('04_quick_swap.png','Fortnite Misc: Toggle Pickaxe bound to L, not F')}</div>`
  }
];
function fsShot(file, caption) {
  const src = '/first_steps/img/' + file;
  return `<div class="fs-shot"><img src="${src}" alt="${_escapeHtml(caption)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"><div class="fs-ph" style="display:none;">Screenshot placeholder — add <code>data/first_steps/${_escapeHtml(file)}</code></div></div>`;
}
let _fsPage = 0;
let _fsForce = false;
function renderFirstStepsPage() {
  const pages = FIRST_STEPS_PAGES;
  const last = pages.length - 1;
  if (_fsPage < 0) _fsPage = 0;
  if (_fsPage > last) _fsPage = last;
  const page = pages[_fsPage];
  document.getElementById('fs-page-label').textContent = page.label;
  document.getElementById('fs-body').innerHTML = page.html;
  document.getElementById('fs-prev').style.display = _fsPage === 0 ? 'none' : '';
  document.getElementById('fs-next').style.display = _fsPage === last ? 'none' : '';
  document.getElementById('fs-close').style.display = _fsPage === last ? '' : 'none';
  const dots = document.getElementById('fs-dots');
  dots.innerHTML = pages.map((_,i)=>`<span class="fs-dot ${i===_fsPage?'on':''}"></span>`).join('');
}
function openFirstSteps(force) {
  _fsForce = !!force;
  _fsPage = 0;
  renderFirstStepsPage();
  document.getElementById('modal-first-steps').classList.add('open');
}
function firstStepsPrev() { if (_fsPage > 0) { _fsPage--; renderFirstStepsPage(); } }
function firstStepsNext() { if (_fsPage < FIRST_STEPS_PAGES.length - 1) { _fsPage++; renderFirstStepsPage(); } }
async function firstStepsClose() {
  document.getElementById('modal-first-steps').classList.remove('open');
  try { await postJson('/first_steps', {completed: true}); } catch(e) {}
}
async function maybeShowFirstSteps() {
  try {
    const r = await fetch('/first_steps');
    const d = await r.json();
    if (d && d.ok && !d.completed) openFirstSteps(false);
  } catch(e) {}
}

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// CALIBRATION PANEL
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
let _calibRegions={};
let _calibDefaults={};
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ Calib tab config ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬
// Tabs: ALL shows everything with section separators; individual tabs show subsets
const CALIB_TABS_DEF = [
  { id:'all',   label:'ALL',   groups:[
    { title:'UI',     keys:['menu_play','tp_button','tp_base','tp_area1','tp_area2','tp_area3','tp_area4','tp_area5','tp_area7'] },
    { title:'HUD',    keys:['stone','strength','stone_icon','auto_str'] },
    { title:'MISC',   keys:['rock_hp_bar','bramble_mode'] },
    { title:'MANUAL STRENGTH', keys:['ms_stone', 'ms_strength', 'ms_row1_left', 'ms_row1_right', 'ms_row2_left', 'ms_row2_right', 'ms_row3_left', 'ms_row3_right', 'ms_row4_left', 'ms_row4_right', 'ms_row5_left', 'ms_row5_right', 'ms_close'] },
  ]},
  { id:'ui',     label:'UI',       groups:[{ title:null, keys:['menu_play','tp_button','tp_base','tp_area1','tp_area2','tp_area3','tp_area4','tp_area5','tp_area7'] }] },
  { id:'hud',    label:'HUD',      groups:[{ title:null, keys:['stone','strength','stone_icon','auto_str'] }] },
  { id:'misc',   label:'MISC',     groups:[{ title:null, keys:['rock_hp_bar','bramble_mode'] }] },
  { id:'manstr', label:'MANUAL STR', groups:[
    { title:'VALUES', keys:['ms_stone','ms_strength'] },
    { title:'UPGRADE BUTTONS (top -> bottom)', keys:['ms_row1_left','ms_row1_right','ms_row2_left','ms_row2_right','ms_row3_left','ms_row3_right','ms_row4_left','ms_row4_right','ms_row5_left','ms_row5_right'] },
    { title:'CLOSE BUTTON', keys:['ms_close'] },
  ]},
];
let _calibActiveTab = 'all';

async function loadCalibRegions() {
  try {
    const r=await fetch('/regions'); const d=await r.json();
    if(!d.ok)throw new Error(d.error||'failed');
    _calibRegions=d.regions; _calibDefaults=d.defaults||{}; renderCalibPanel();
  } catch(e){document.getElementById('calib-body').innerHTML=`<div style="color:var(--red);font-size:12px;">${e.message}</div>`;}
}

function setCalibTab(tabId) { _calibActiveTab=tabId; renderCalibPanel(); }

function _buildRegionRow(key) {
  const reg=_calibRegions[key]; if(!reg)return '';
  const coordStr=reg.value?`[${reg.value.join(', ')}]`:'not set';
  const def=_calibDefaults[key];
  const defStr=def?`[${def.join(', ')}]`:'-';
  const isDefault=def&&reg.value&&def.length===reg.value.length&&def.every((v,i)=>v===reg.value[i]);
  const ocrBtn=['stone','strength','ms_stone','ms_strength'].includes(key)
    ?`<button class="calib-sm-btn" onclick="testRegionText('${key}')" ${reg.value?'':'disabled'}>Test</button>`:'';
  return `<div class="calib-region-row" id="calib-row-${key}">
    <div class="calib-region-label"><span>${reg.label}</span><code style="font-size:10px;color:var(--muted);">${key}</code></div>
    <div class="calib-region-coords" id="calib-coords-${key}">${coordStr}</div>
    <div style="font-size:10px;color:var(--muted);font-family:monospace;" id="calib-def-${key}">default: ${defStr}</div>
    <div class="calib-btn-row">
      <button class="calib-sm-btn" onclick="selectCalibRegion('${key}')">Select</button>
      <button class="calib-sm-btn" onclick="previewRegion('${key}')" ${reg.value?'':'disabled'}>Preview</button>
      ${ocrBtn}
      <button class="calib-reset-btn" onclick="resetCalibRegion('${key}')" ${isDefault?'disabled title="Already default"':''}>Reset</button>
    </div>
    <img class="calib-preview" id="calib-prev-${key}" src="">
    <div class="calib-ocr-result" id="calib-ocr-${key}"></div>
  </div>`;
}

function _getTabKeys(tab) {
  const keys=[];
  (tab.groups||[]).forEach(g=>(g.keys||[]).forEach(k=>keys.push(k)));
  return keys;
}
function renderCalibPanel() {
  const body=document.getElementById('calib-body');
  const tabBar=CALIB_TABS_DEF.map((t,i)=>{
    const active=t.id===_calibActiveTab?' active':'';
    const sep=(i>0&&i<CALIB_TABS_DEF.length)?'<div class="calib-tab-sep"></div>':'';
    return sep+`<button class="calib-tab${active}" onclick="setCalibTab('${t.id}')">${t.label}</button>`;
  }).join('');
  const tab=CALIB_TABS_DEF.find(t=>t.id===_calibActiveTab)||CALIB_TABS_DEF[0];
  const tabKeys=_getTabKeys(tab);
  const resetHeader=document.getElementById('calib-header-reset');
  if(resetHeader) resetHeader.disabled = tabKeys.length <= 0;
  let content='';
  if(!tab.groups||tab.groups.length===0){
    content='<div class="calib-empty-tab">Nothing here yet.</div>';
  } else {
    const isAll=(tab.id==='all');
    for(let gi=0;gi<tab.groups.length;gi++){
      const grp=tab.groups[gi];
      if(isAll&&gi>0) content+='<div style="height:1px;background:var(--border);margin:10px 0;"></div>';
      if(grp.title) content+=`<div class="calib-section-label">${grp.title}</div>`;
      content+=`<div style="display:flex;flex-direction:column;gap:8px;">${(grp.keys||[]).map(k=>_buildRegionRow(k)).join('')}</div>`;
    }
  }
  body.innerHTML=`<div class="calib-tabs" style="display:flex;align-items:center;">${tabBar}</div><div style="font-size:12px;color:var(--muted);margin:8px 0 10px;">Click <b>Select</b> to draw on a live screenshot. Coordinates save instantly to config.json.</div>${content}`;
}

function selectCalibRegion(key) {
  _pendingCalibKey=key;
  fetch('/screenshot').then(r=>r.json()).then(d=>{
    if(!d.ok)throw new Error(d.error);
    _ssData=d; showSsOverlay('calib');
  }).catch(e=>alert('Screenshot failed: '+e.message));
}

async function previewRegion(key) {
  const reg=_calibRegions[key]; if(!reg||!reg.value)return;
  try {
    const r=await postJson('/region_preview', {region:reg.value});
    const d=await r.json();
    if(!d.ok)throw new Error(d.error);
    const img=document.getElementById('calib-prev-'+key);
    img.src='data:image/jpeg;base64,'+d.img;
    img.style.display='block';
  } catch(e){alert('Preview failed: '+e.message);}
}

async function testRegionText(key) {
  const reg=_calibRegions[key]; if(!reg||!reg.value)return;
  try {
    const r=await postJson('/ocr_test', {region:reg.value});
    const d=await r.json();
    const el=document.getElementById('calib-ocr-'+key);
    if(d.ok){el.textContent=`raw: "${d.raw}" -> parsed: ${d.parsed??'null'}`;el.style.display='block';el.style.color='var(--green)';}
    else{el.textContent='Error: '+d.error;el.style.display='block';el.style.color='var(--red)';}
  } catch(e){alert('Test failed: '+e.message);}
}

function resetActiveCalibTab() {
  resetCalibTab(_calibActiveTab);
}

async function saveCalibRegion(key, region) {
  try {
    const r=await postJson('/regions', {key,region});
    const d=await r.json();
    if(d.ok){
      _calibRegions[key].value=region;
      const el=document.getElementById('calib-coords-'+key);
      if(el)el.textContent='['+region.join(', ')+']';
      const st=document.getElementById('calib-status');
      st.style.display='block';st.style.color='var(--green)';st.textContent=`Saved ${key}: [${region.join(', ')}]`;
      setTimeout(()=>st.style.display='none',3000);
    } else {alert('Save failed: '+d.error);}
  } catch(e){alert('Save failed: '+e.message);}
}

async function resetCalibRegion(key) {
  try {
    const r=await postJson('/regions/reset', {keys:[key]});
    const d=await r.json();
    if(!d.ok)throw new Error(d.error||'reset failed');
    const def=d.reset[key];
    if(def){
      if(_calibRegions[key]) _calibRegions[key].value=def;
      const el=document.getElementById('calib-coords-'+key);
      if(el) el.textContent='['+def.join(', ')+']';
    }
    // Re-render so Reset button state updates
    renderCalibPanel();
    const st=document.getElementById('calib-status');
    st.style.display='block'; st.style.color='var(--yellow)';
    st.textContent=`Reset ${key} to default`;
    setTimeout(()=>st.style.display='none',2500);
  } catch(e){alert('Reset failed: '+e.message);}
}

async function resetCalibTab(tabId) {
  const tab=CALIB_TABS_DEF.find(t=>t.id===tabId);
  if(!tab) return;
  const keys=_getTabKeys(tab);
  if(!keys.length) return;
  if(!confirm(`Reset ALL ${keys.length} region(s) in "${tab.label}" tab to defaults?`)) return;
  try {
    const r=await postJson('/regions/reset', {keys});
    const d=await r.json();
    if(!d.ok)throw new Error(d.error||'reset failed');
    Object.entries(d.reset).forEach(([k,v])=>{ if(_calibRegions[k]) _calibRegions[k].value=v; });
    renderCalibPanel();
    const st=document.getElementById('calib-status');
    st.style.display='block'; st.style.color='var(--yellow)';
    st.textContent=`Reset ${Object.keys(d.reset).length} region(s) in "${tab.label}" to defaults`;
    setTimeout(()=>st.style.display='none',3000);
  } catch(e){alert('Reset tab failed: '+e.message);}
}

// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
// DPI-AWARE SCREENSHOT OVERLAY
// Fixes the stretching bug: canvas internal px ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  CSS px on
// HiDPI screens (retina/4K). We must set canvas.width/height
// to CSS dimensions * devicePixelRatio, then scale the ctx.
// ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â
let _ssData=null, _pendingCalibKey=null;
let _ssMode='calib';
let _ssOnSelect=null; // callback(x1,y1,x2,y2) in game pixels

function showSsOverlay(mode, onSelect) {
  _ssMode=mode; _ssOnSelect=onSelect||null;
  const overlay=document.getElementById('ss-overlay');
  const canvas=document.getElementById('ss-canvas');
  const dpr=window.devicePixelRatio||1;
  const cssW=window.innerWidth, cssH=window.innerHeight;

  // Set CSS size
  canvas.style.width=cssW+'px'; canvas.style.height=cssH+'px';
  // Set actual pixel buffer (DPI-aware)
  canvas.width=cssW*dpr; canvas.height=cssH*dpr;

  const ctx=canvas.getContext('2d');
  ctx.scale(dpr,dpr); // scale so 1 unit = 1 CSS px

  overlay.style.display='block';

  const imgW=_ssData.w, imgH=_ssData.h;
  const scale=Math.min(cssW/imgW, cssH/imgH);
  const dw=imgW*scale, dh=imgH*scale;
  const ox=(cssW-dw)/2, oy=(cssH-dh)/2;

  const img=new Image();
  img.onload=()=>{
    ctx.drawImage(img,ox,oy,dw,dh);
    ctx.fillStyle='rgba(0,0,0,0.45)';
    ctx.fillRect(0,0,cssW,cssH);
    canvas._ox=ox; canvas._oy=oy; canvas._dw=dw; canvas._dh=dh;
    canvas._scale=scale; canvas._bgImg=img; canvas._ctx=ctx;
  };
  img.src='data:image/jpeg;base64,'+_ssData.img;

  let sx,sy,dragging=false;
  canvas.onmousedown=e=>{
    const r=canvas.getBoundingClientRect();
    sx=e.clientX-r.left; sy=e.clientY-r.top; dragging=true;
  };
  canvas.onmousemove=e=>{
    if(!dragging||!canvas._bgImg)return;
    const r=canvas.getBoundingClientRect();
    const mx=e.clientX-r.left, my=e.clientY-r.top;
    ctx.clearRect(0,0,cssW,cssH);
    ctx.drawImage(canvas._bgImg,ox,oy,dw,dh);
    ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.fillRect(0,0,cssW,cssH);
    const rx=Math.min(sx,mx),ry=Math.min(sy,my),rw=Math.abs(mx-sx),rh=Math.abs(my-sy);
    ctx.clearRect(rx,ry,rw,rh);
    ctx.drawImage(canvas._bgImg,
      (rx-ox)/scale, (ry-oy)/scale, rw/scale, rh/scale,
      rx, ry, rw, rh);
    ctx.strokeStyle='#f0c040'; ctx.lineWidth=2; ctx.strokeRect(rx,ry,rw,rh);
    ctx.fillStyle='#f0c040'; ctx.font='bold 12px Segoe UI';
    const label=`${Math.round(rw/scale)} ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ${Math.round(rh/scale)}`;
    ctx.fillText(label, rx+5, ry>20?ry-6:ry+rh+16);
  };
  canvas.onmouseup=e=>{
    if(!dragging)return; dragging=false;
    const r=canvas.getBoundingClientRect();
    const mx=e.clientX-r.left, my=e.clientY-r.top;
    const x1=Math.round((Math.min(sx,mx)-ox)/scale);
    const y1=Math.round((Math.min(sy,my)-oy)/scale);
    const x2=Math.round((Math.max(sx,mx)-ox)/scale);
    const y2=Math.round((Math.max(sy,my)-oy)/scale);
    if((x2-x1)<4||(y2-y1)<4){hideSsOverlay();return;}
    hideSsOverlay();
    if(_ssMode==='calib' && _pendingCalibKey){
      saveCalibRegion(_pendingCalibKey,[x1,y1,x2,y2]);
    } else if(_ssOnSelect){
      _ssOnSelect(x1,y1,x2,y2);
    }
  };
}

function hideSsOverlay() {
  document.getElementById('ss-overlay').style.display='none';
  const c=document.getElementById('ss-canvas');
  c.onmousedown=c.onmousemove=c.onmouseup=null;
}

document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){ hideSsOverlay(); cancelBlockEdit(); }
});


// ============================================================
// AUTH REMOVED - open-source build. Dashboard shows directly.
// ============================================================
function showDashboard(username) {
  const startup = document.getElementById('startup-screen');
  if (startup) startup.style.display = 'none';
  var ta = document.getElementById('topbar-app'); if (ta) ta.style.display = 'flex';
  var trb = document.getElementById('topbar-run'); if (trb) trb.style.display = 'flex';
  document.getElementById('layout').style.display = 'flex';
  document.body.classList.add('tab-run');
  document.body.classList.remove('tab-builder', 'tab-recorder');
  maybeShowFirstSteps();
}

async function tryAutoLogin() {
  showDashboard('local');
  startPolling();
  return true;
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

  // Polling helpers
  let _pollInterval = null;
  function startPolling() {
    if (_pollInterval) return;
    poll();
    _pollInterval = setInterval(poll, 400);  // fast UI sync without excessive request load
  }
  function stopPolling() {
    if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
  }

  // Boot — straight to dashboard (auth removed).
  _bindFloatingTooltips(document);
  (async function boot() {
    const ok = await tryAutoLogin();
    if (ok) {
      try { loadConfig(); } catch(e) {}
      try { await postJson('/me/api/tab', {active:false}); } catch(e) {}
    }
  })();



// ÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚Â


// ============================================================
// TAB SYSTEM + BUILDER + FLOW GRAPH  (from MT2 Rebirth Bot 2.0)
// Editor tab is visible but disabled until 1.8. Recorder is live.
// F5/F6 are armed only while the Recorder tab is open.
// ============================================================
const BUILDER_TAB_ENABLED = false;
if (typeof showToast !== 'function') {
  function showToast(msg) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(124,106,247,.9);color:#fff;padding:10px 24px;border-radius:8px;font-size:13px;font-weight:600;z-index:99999;transition:opacity .3s;pointer-events:none;';
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 300); }, 2000);
  }
}

async function armRecorderHotkeys(active) {
  try {
    await postJson('/me/api/tab', {active: !!active});
  } catch (e) {}
  const frame = document.getElementById('recorder-frame');
  if (frame && frame.contentWindow) {
    try { frame.contentWindow.postMessage({type:'recorder-arm', active: !!active}, '*'); } catch (e) {}
  }
  if (!active && frame) {
    try { frame.blur(); } catch (e) {}
    try { if (frame.contentWindow) frame.contentWindow.blur(); } catch (e) {}
  }
}

function preloadRecorder() {
  const frame = document.getElementById('recorder-frame');
  if (!frame) return;
  const src = frame.getAttribute('src') || '';
  if (!src || src === 'about:blank') frame.src = '/me/';
}

function recCmd(cmd, extra) {
  extra = extra || {};
  closeRecMenus();
  const frame = document.getElementById('recorder-frame');
  if (frame && frame.contentWindow) {
    try { frame.contentWindow.postMessage(Object.assign({type:'recorder-cmd', cmd: cmd}, extra), '*'); } catch (e) {}
  }
}
function toggleRecMenu(which) {
  const fileWrap = document.getElementById('rec-file-wrap');
  const recIsland = document.getElementById('topbar-recorder');
  if (fileWrap) fileWrap.classList.toggle('open');
  if (recIsland) recIsland.classList.toggle('menu-open', !!(fileWrap && fileWrap.classList.contains('open')));
}
function closeRecMenus() {
  document.querySelectorAll('#topbar-recorder .rec-menu-wrap.open').forEach(function(w){ w.classList.remove('open'); });
  const recIsland = document.getElementById('topbar-recorder');
  if (recIsland) recIsland.classList.remove('menu-open');
}
function applyRecorderUi(data) {
  if (!data) return;
  const playBtn = document.getElementById('rec-play-btn');
  const recBtn = document.getElementById('rec-record-btn');
  const modeSel = document.getElementById('rec-play-mode');
  const times = document.getElementById('rec-play-times');
  const label = document.getElementById('rec-macro-label');
  if (playBtn) {
    playBtn.textContent = data.running ? '\u25A0' : '\u25B6';
    playBtn.title = data.running ? 'Stop (F6)' : 'Play (F6)';
    playBtn.classList.toggle('on', !!data.running);
    playBtn.disabled = !!data.playDisabled;
  }
  if (recBtn) {
    recBtn.textContent = data.recording ? '\u25A0' : '\u25CF';
    recBtn.title = data.recording ? 'Stop recording (F5)' : 'Record (F5)';
    recBtn.classList.toggle('rec-on', !!data.recording);
    recBtn.disabled = !!data.recordDisabled;
  }
  if (modeSel && data.playMode) modeSel.value = data.playMode;
  if (times) {
    times.hidden = data.playMode !== 'times';
    if (data.playTimes != null) times.value = String(data.playTimes);
  }
  if (label && data.macroName) {
    label.textContent = data.macroName;
    label.title = data.macroName;
  }
}
window.addEventListener('message', function(e) {
  if (!e.data) return;
  if (e.data.type === 'recorder-ui') { applyRecorderUi(e.data); return; }
  // pointerdown inside the recorder iframe (blockly editor, macro list):
  // its clicks never reach this document, so the iframe reports them
  if (e.data.type === 'rec-close-menus') closeRecMenus();
});
document.addEventListener('click', function(e) {
  const rec = document.getElementById('topbar-recorder');
  if (rec && !rec.contains(e.target)) closeRecMenus();
});
// clicking into ANY iframe (recorder, builder) moves focus off this
// window — close the File / Play-mode menus then too
window.addEventListener('blur', closeRecMenus);

function _setAppTabsBusy(busy) {
  if (busy) {
    document.querySelectorAll('.app-tab').forEach(btn => {
      if (btn.dataset.tab === 'builder') return;
      btn.disabled = true;
    });
    return;
  }
  applyTabLocks(_lastPollState || {});
}

let _runBusy = false;
let _recorderBusy = false;
function applyTabLocks(s) {
  s = s || {};
  _runBusy = !!s.run_active || (!s.waiting_for_start && s.status && s.status !== 'STOPPED' && s.status !== 'WAITING' && s.status !== 'INIT');
  _recorderBusy = !!s.recorder_busy;
  const recBtn = document.querySelector('.app-tab[data-tab="recorder"]');
  const runBtn = document.querySelector('.app-tab[data-tab="run"]');
  if (recBtn) {
    recBtn.disabled = _runBusy;
    recBtn.title = _runBusy ? 'Stop the bot first' : 'Recorder';
  }
  if (runBtn) {
    runBtn.disabled = _recorderBusy;
    runBtn.title = _recorderBusy ? 'Stop recording / playback first' : 'Run';
  }
}

// --- Tab Switching ---
let _currentAppTab = 'run';
let _tabSwitchLock = Promise.resolve();

async function switchAppTab(tab) {
  if (tab === 'builder' && !BUILDER_TAB_ENABLED) {
    showToast('Editor is coming in 1.8');
    return;
  }
  if (tab !== 'run' && _runBusy) {
    showToast('Stop the bot before switching tabs');
    return;
  }
  if (tab !== 'recorder' && _recorderBusy) {
    showToast('Stop recording / playback first');
    return;
  }
  const run = async () => {
    // Await arm/disarm BEFORE flipping the page so F5/F6 cannot leak into Run.
    _setAppTabsBusy(true);
    try {
      await armRecorderHotkeys(tab === 'recorder');
      _currentAppTab = tab;
      try { post('set_app_tab', {tab: tab}); } catch (e) {}
      document.body.classList.remove('tab-run', 'tab-builder', 'tab-recorder');
      document.body.classList.add('tab-' + tab);
      document.querySelectorAll('.app-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
      });
      var tr = document.getElementById('topbar-run');
      if (tr) tr.style.display = (tab === 'run') ? 'flex' : 'none';
      var pr = document.getElementById('page-run');
      if (pr) pr.style.top = (tab === 'run') ? '98px' : '0px';
      if (tab === 'recorder') {
        preloadRecorder();
        const frame = document.getElementById('recorder-frame');
        if (frame) {
          try { frame.contentWindow.postMessage({type:'recorder-arm', active:true}, '*'); } catch (e) {}
          try { frame.contentWindow.postMessage({type:'recorder-cmd', cmd:'sync'}, '*'); } catch (e) {}
        }
      }
      if (tab === 'builder') {
        builderLoadModes();
        builderCheckModeStatus();
      }
      if (tab === 'builder' && !_flowCanvas) {
        setTimeout(() => flowInit(), 100);
      }
      if (tab === 'builder' && _flowCanvas) {
        setTimeout(() => flowResize(), 100);
      }
    } finally {
      _setAppTabsBusy(false);
    }
  };
  const next = _tabSwitchLock.then(run, run);
  _tabSwitchLock = next.catch(() => {});
  return next;
}

// --- Builder: Mode Management ---
let _builderCurrentMode = null;
let _builderFlowData = { nodes: [], edges: [], startNodeId: null };

async function builderLoadModes() {
  try {
    const r = await mt2Fetch('/modes/list');
    const d = await r.json();
    const list = document.getElementById('builder-mode-list');
    if (!d.modes || d.modes.length === 0) {
      list.innerHTML = '<div style="color:var(--muted);font-size:13px;">No custom modes yet. Create one to get started!</div>';
      return;
    }
    list.innerHTML = d.modes.map(m => {
      const safeName = _escapeHtml(m.name).replace(/'/g, '&#39;');
      return '<div class="builder-mode-card">' +
        '<div class="bmc-name">' + _escapeHtml(m.name) + '</div>' +
        '<div class="bmc-desc">' + _escapeHtml(m.description || 'No description') + '</div>' +
        '<div class="bmc-actions">' +
          '<button class="bmc-btn" onclick="builderRunMode(\'' + safeName + '\')">Run</button>' +
          '<button class="bmc-btn" onclick="builderEditMode(\'' + safeName + '\')">Edit</button>' +
          '<button class="bmc-btn danger" onclick="builderDeleteMode(\'' + safeName + '\')">Delete</button>' +
        '</div>' +
      '</div>';
    }).join('');
  } catch(e) {
    document.getElementById('builder-mode-list').innerHTML = '<div style="color:var(--red);font-size:13px;">Failed to load modes.</div>';
  }
}

async function builderRunMode(name) {
  try {
    const r = await postJson('/modes/run', { name: name });
    const d = await r.json();
    if (d.ok) {
      _builderRunningMode = name;
      builderUpdateModeButtons();
    } else {
      alert(d.error || 'Failed to start mode');
    }
  } catch(e) {
    alert('Network error: ' + e.message);
  }
}

async function builderStopMode() {
  try {
    await postJson('/modes/stop', {});
    _builderRunningMode = null;
    builderUpdateModeButtons();
  } catch(e) {
    console.error('Stop mode error:', e);
  }
}

async function builderCheckModeStatus() {
  try {
    const r = await mt2Fetch('/modes/status');
    const d = await r.json();
    _builderRunningMode = d.running ? d.mode : null;
    builderUpdateModeButtons();
  } catch(e) {}
}

function builderUpdateModeButtons() {
  document.querySelectorAll('.builder-mode-card').forEach(card => {
    const nameEl = card.querySelector('.bmc-name');
    if (!nameEl) return;
    const name = nameEl.textContent;
    const isRunning = _builderRunningMode === name;
    const existing = card.querySelector('.bmc-btn.run-stop');
    if (isRunning && !existing) {
      const btn = document.createElement('button');
      btn.className = 'bmc-btn danger run-stop';
      btn.textContent = 'Stop';
      btn.onclick = builderStopMode;
      card.querySelector('.bmc-actions').prepend(btn);
    } else if (!isRunning && existing) {
      existing.remove();
    }
  });
}

let _builderRunningMode = null;

async function builderNewMode() {
  const name = prompt('Mode name:');
  if (!name || !name.trim()) return;
  try {
    const r = await postJson('/modes/create', { name: name.trim(), description: '' });
    const d = await r.json();
    if (d.ok) {
      builderEditMode(name.trim());
    } else {
      alert(d.error || 'Failed to create mode');
    }
  } catch(e) {
    alert('Network error');
  }
}

async function builderEditMode(name) {
  try {
    const r = await mt2Fetch('/modes/load?name=' + encodeURIComponent(name));
    const d = await r.json();
    if (!d.ok) { alert(d.error || 'Failed to load mode'); return; }
    _builderCurrentMode = d.mode;
    const fg = d.mode.flow_graph || { nodes: [], edges: [], startNodeId: null };
    if (!fg.nodes.length) {
      fg.nodes.push({ id: 'start', type: 'start', label: 'Start', x: 100, y: 100 });
      fg.startNodeId = 'start';
    }
    flowLoadData(fg);
    _builderModeData = {
      variables: d.mode.variables || [],
      config: d.mode.config || []
    };
    document.getElementById('builder-welcome').style.display = 'none';
    document.getElementById('builder-editor').style.display = 'flex';
    document.getElementById('builder-mode-name').textContent = _builderCurrentMode.name;
    if (!_flowCanvas) flowInit();
    setTimeout(() => flowResize(), 50);
  } catch(e) {
    alert('Network error');
  }
}

function builderBackToWelcome() {
  document.getElementById('builder-welcome').style.display = 'flex';
  document.getElementById('builder-editor').style.display = 'none';
  _builderCurrentMode = null;
  builderLoadModes();
}

let _autoSaveTimer = null;
function _autoSave() {
  if (!_builderCurrentMode) return;
  if (_autoSaveTimer) clearTimeout(_autoSaveTimer);
  const ind = document.getElementById('builder-autosave-indicator');
  if (ind) ind.textContent = 'Saving...';
  _autoSaveTimer = setTimeout(async () => {
    flowSyncData();
    try {
      // Save flow + variables + config + procedures
      const saveData = {
        name: _builderCurrentMode.name,
        flow_graph: _builderFlowData,
        variables: _builderModeData.variables || [],
        config: _builderModeData.config || [],
      };
      const r = await postJson('/modes/save', saveData);
      const d = await r.json();
      if (ind) ind.textContent = d.ok ? 'All changes saved' : 'Save failed!';
    } catch(e) {
      if (ind) ind.textContent = 'Save failed!';
    }
  }, 600);
}

async function builderSaveMode() {
  if (!_builderCurrentMode) return;
  flowSyncData();
  try {
    const r = await postJson('/modes/save', {
      name: _builderCurrentMode.name,
      flow_graph: _builderFlowData,
      variables: _builderModeData.variables || [],
      config: _builderModeData.config || [],
    });
    const d = await r.json();
    if (d.ok) { showToast('Mode saved'); }
    else { alert(d.error || 'Failed to save'); }
  } catch(e) { alert('Network error'); }
}

async function builderDeleteMode(name) {
  if (!confirm('Delete mode "' + name + '"? This cannot be undone.')) return;
  try {
    const r = await postJson('/modes/delete', { name });
    const d = await r.json();
    if (d.ok) { builderLoadModes(); }
    else { alert(d.error || 'Failed to delete'); }
  } catch(e) { alert('Network error'); }
}

function builderSwitchView(view) {
  document.querySelectorAll('.builder-nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
  document.querySelectorAll('.builder-view').forEach(v => {
    v.classList.toggle('active', v.id === 'builder-view-' + view);
  });
  if (view === 'flow') { setTimeout(() => flowResize(), 50); }
  if (view === 'variables') { varRenderRows('variables'); }
  if (view === 'config') { varRenderRows('config'); }
}

// --- Flow Graph Engine (HTML5 Canvas) ---
const FLOW_NODE_W = 180;
const FLOW_NODE_H = 56;
const FLOW_COLORS = {
  start:          { fill: '#2d8a52', border: '#44cc77', dot: '#44cc77' },
  procedure:      { fill: '#4a3aa0', border: '#6a5aff', dot: '#6a5aff' },
  code_snippet:   { fill: '#7a6a30', border: '#f7c46a', dot: '#f7c46a' },
  play_macro:     { fill: '#7a3a5a', border: '#f76aa6', dot: '#f76aa6' },
  stop_macro:     { fill: '#7a3a3a', border: '#f76a6a', dot: '#f76a6a' },
  connector:      { fill: '#3a5a7a', border: '#6aa6f7', dot: '#6aa6f7' },
};

let _flowCanvas = null;
let _flowCtx = null;
let _flowNodes = [];
let _flowEdges = [];
let _flowStartId = null;
let _flowDragNode = null;
let _flowDragOffset = { x: 0, y: 0 };
let _flowConnecting = null;
let _flowSelectedNode = null;
let _flowMouse = { x: 0, y: 0 };
let _flowPan = { x: 0, y: 0 };
let _flowIsPanning = false;
let _flowPanStart = { x: 0, y: 0 };
let _nodeIdCounter = 0;

function flowInit() {
  _flowCanvas = document.getElementById('flow-canvas');
  if (!_flowCanvas) return;
  _flowCtx = _flowCanvas.getContext('2d');
  flowResize();
  _flowCanvas.addEventListener('mousedown', flowMouseDown);
  _flowCanvas.addEventListener('mousemove', flowMouseMove);
  _flowCanvas.addEventListener('mouseup', flowMouseUp);
  _flowCanvas.addEventListener('dblclick', flowDoubleClick);
  _flowCanvas.addEventListener('contextmenu', flowRightClick);
  window.addEventListener('resize', flowResize);
  document.querySelectorAll('.flow-palette-item').forEach(item => {
    item.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', item.dataset.type);
    });
  });
  const container = document.getElementById('flow-canvas-container');
  if (container) {
    container.addEventListener('dragover', (e) => { e.preventDefault(); });
    container.addEventListener('drop', flowDrop);
  }
}

function flowResize() {
  if (!_flowCanvas) return;
  const container = _flowCanvas.parentElement;
  _flowCanvas.width = container.clientWidth;
  _flowCanvas.height = container.clientHeight;
  flowRender();
}

function flowRender() {
  if (!_flowCtx) return;
  const w = _flowCanvas.width;
  const h = _flowCanvas.height;
  _flowCtx.clearRect(0, 0, w, h);
  _flowCtx.strokeStyle = '#161620';
  _flowCtx.lineWidth = 1;
  const gridSize = 20;
  for (let x = (_flowPan.x % gridSize); x < w; x += gridSize) {
    _flowCtx.beginPath(); _flowCtx.moveTo(x, 0); _flowCtx.lineTo(x, h); _flowCtx.stroke();
  }
  for (let y = (_flowPan.y % gridSize); y < h; y += gridSize) {
    _flowCtx.beginPath(); _flowCtx.moveTo(0, y); _flowCtx.lineTo(w, y); _flowCtx.stroke();
  }
  _flowEdges.forEach(e => {
    const from = _flowNodes.find(n => n.id === e.source);
    const to = _flowNodes.find(n => n.id === e.target);
    if (!from || !to) return;
    const x1 = from.x + FLOW_NODE_W / 2 + _flowPan.x;
    const y1 = from.y + FLOW_NODE_H + _flowPan.y;
    const x2 = to.x + FLOW_NODE_W / 2 + _flowPan.x;
    const y2 = to.y + _flowPan.y;
    const dy = Math.abs(y2 - y1) * 0.5 + 30;
    const col = FLOW_COLORS[from.type] || FLOW_COLORS.connector;
    _flowCtx.strokeStyle = e === _flowSelectedNode ? '#fff' : col.border;
    _flowCtx.lineWidth = e === _flowSelectedNode ? 3 : 2;
    _flowCtx.beginPath();
    _flowCtx.moveTo(x1, y1);
    _flowCtx.bezierCurveTo(x1, y1 + dy, x2, y2 - dy, x2, y2);
    _flowCtx.stroke();
  });
  if (_flowConnecting) {
    const from = _flowNodes.find(n => n.id === _flowConnecting.fromId);
    if (from) {
      const x1 = from.x + FLOW_NODE_W / 2 + _flowPan.x;
      const y1 = from.y + FLOW_NODE_H + _flowPan.y;
      _flowCtx.strokeStyle = '#f7a06a';
      _flowCtx.lineWidth = 2;
      _flowCtx.setLineDash([6, 4]);
      _flowCtx.beginPath();
      _flowCtx.moveTo(x1, y1);
      _flowCtx.lineTo(_flowMouse.x, _flowMouse.y);
      _flowCtx.stroke();
      _flowCtx.setLineDash([]);
    }
  }
  _flowNodes.forEach(n => {
    const col = FLOW_COLORS[n.type] || FLOW_COLORS.connector;
    const x = n.x + _flowPan.x;
    const y = n.y + _flowPan.y;
    const isSelected = n === _flowSelectedNode;
    _flowCtx.fillStyle = col.fill;
    _flowCtx.strokeStyle = isSelected ? '#fff' : col.border;
    _flowCtx.lineWidth = isSelected ? 3 : 2;
    roundRect(_flowCtx, x, y, FLOW_NODE_W, FLOW_NODE_H, 8);
    _flowCtx.fill();
    _flowCtx.stroke();
    _flowCtx.fillStyle = col.border;
    roundRect(_flowCtx, x, y, FLOW_NODE_W, 26, 8, true);
    _flowCtx.fill();
    _flowCtx.fillStyle = '#fff';
    _flowCtx.font = 'bold 10px Segoe UI';
    _flowCtx.textAlign = 'left';
    _flowCtx.textBaseline = 'middle';
    const title = n.type === 'start' ? 'Start' :
                  n.type === 'procedure' ? 'Procedure' :
                  n.type === 'code_snippet' ? 'Code Snippet' :
                  n.type === 'play_macro' ? 'Play Macro' :
                  n.type === 'stop_macro' ? 'Stop Macro' :
                  n.type === 'connector' ? 'Connector' : n.type;
    _flowCtx.fillText(title, x + 10, y + 13);
    _flowCtx.fillStyle = '#c0c0d0';
    _flowCtx.font = '10px Segoe UI';
    let body = '';
    if (n.type === 'procedure') body = n.steps && n.steps.length ? n.steps.length + ' steps' : 'Double-click to edit';
    else if (n.type === 'code_snippet') body = n.code ? n.code.substring(0, 30) + '...' : 'Empty';
    else if (n.type === 'play_macro') body = n.macro_path || '(select macro)';
    else if (n.type === 'start') body = 'Entry point';
    else if (n.type === 'connector') body = 'Hub';
    else body = '—';
    _flowCtx.fillText(body, x + 10, y + 42);
    _flowCtx.fillStyle = col.border;
    _flowCtx.beginPath();
    _flowCtx.arc(x + FLOW_NODE_W / 2, y + FLOW_NODE_H, 6, 0, Math.PI * 2);
    _flowCtx.fill();
    if (n.type !== 'start') {
      _flowCtx.fillStyle = '#f7a06a';
      _flowCtx.beginPath();
      _flowCtx.arc(x + FLOW_NODE_W / 2, y, 6, 0, Math.PI * 2);
      _flowCtx.fill();
    }
  });
}

function roundRect(ctx, x, y, w, h, r, topOnly) {
  ctx.beginPath();
  if (topOnly) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
  } else {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
  }
  ctx.closePath();
}

function flowGetNodeAt(mx, my) {
  for (let i = _flowNodes.length - 1; i >= 0; i--) {
    const n = _flowNodes[i];
    const x = n.x + _flowPan.x;
    const y = n.y + _flowPan.y;
    if (mx >= x && mx <= x + FLOW_NODE_W && my >= y && my <= y + FLOW_NODE_H) return n;
  }
  return null;
}

function flowGetPortAt(mx, my) {
  for (let n of _flowNodes) {
    const x = n.x + _flowPan.x;
    const y = n.y + _flowPan.y;
    const dx = mx - (x + FLOW_NODE_W / 2);
    const dy = my - (y + FLOW_NODE_H);
    if (Math.sqrt(dx*dx + dy*dy) < 10) return { node: n, port: 'output' };
    if (n.type !== 'start') {
      const dx2 = mx - (x + FLOW_NODE_W / 2);
      const dy2 = my - y;
      if (Math.sqrt(dx2*dx2 + dy2*dy2) < 10) return { node: n, port: 'input' };
    }
  }
  return null;
}

function flowMouseDown(e) {
  const rect = _flowCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  _flowMouse = { x: mx, y: my };
  const port = flowGetPortAt(mx, my);
  if (port && port.port === 'output') { _flowConnecting = { fromId: port.node.id }; return; }
  if (port && port.port === 'input' && _flowConnecting) {
    const fromId = _flowConnecting.fromId;
    const toId = port.node.id;
    if (fromId !== toId && !_flowEdges.some(e => e.source === fromId && e.target === toId)) {
      _flowEdges.push({ id: 'e' + (++_nodeIdCounter), source: fromId, target: toId });
    }
    _flowConnecting = null;
    flowRender();
    return;
  }
  const node = flowGetNodeAt(mx, my);
  if (node) {
    _flowSelectedNode = node;
    _flowDragNode = node;
    _flowDragOffset = { x: mx - (node.x + _flowPan.x), y: my - (node.y + _flowPan.y) };
    flowRender();
  } else {
    _flowSelectedNode = null;
    _flowIsPanning = true;
    _flowPanStart = { x: mx - _flowPan.x, y: my - _flowPan.y };
    flowRender();
  }
}

function flowMouseMove(e) {
  const rect = _flowCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  _flowMouse = { x: mx, y: my };
  if (_flowDragNode) {
    _flowDragNode.x = mx - _flowDragOffset.x - _flowPan.x;
    _flowDragNode.y = my - _flowDragOffset.y - _flowPan.y;
    flowRender();
  } else if (_flowConnecting) {
    flowRender();
  } else if (_flowIsPanning) {
    _flowPan.x = mx - _flowPanStart.x;
    _flowPan.y = my - _flowPanStart.y;
    flowRender();
  }
  if (!_flowDragNode && !_flowIsPanning) {
    const port = flowGetPortAt(mx, my);
    const node = flowGetNodeAt(mx, my);
    _flowCanvas.style.cursor = port ? 'crosshair' : (node ? 'move' : 'default');
  }
}

function flowMouseUp(e) {
  var wasDragging = !!_flowDragNode;
  _flowDragNode = null;
  _flowIsPanning = false;
  if (_flowConnecting) {
    const rect = _flowCanvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const port = flowGetPortAt(mx, my);
    if (port && port.port === 'input') {
      const fromId = _flowConnecting.fromId;
      const toId = port.node.id;
      if (fromId !== toId && !_flowEdges.some(e => e.source === fromId && e.target === toId)) {
        _flowEdges.push({ id: 'e' + (++_nodeIdCounter), source: fromId, target: toId });
        _autoSave();
      }
    }
    _flowConnecting = null;
    flowRender();
  }
  if (wasDragging) _autoSave();
}

function flowDoubleClick(e) {
  const rect = _flowCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const node = flowGetNodeAt(mx, my);
  if (node) {
    if (node.type === 'procedure') openProcEditor(node);
    else if (node.type === 'code_snippet') openCodeEditor(node);
    else if (node.type === 'play_macro') openMacroPicker(node);
  }
}

function flowRightClick(e) {
  e.preventDefault();
  const rect = _flowCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const node = flowGetNodeAt(mx, my);
  if (node && node.type !== 'start') {
    if (confirm('Delete this node?')) {
      _flowNodes = _flowNodes.filter(n => n.id !== node.id);
      _flowEdges = _flowEdges.filter(e => e.source !== node.id && e.target !== node.id);
      _flowSelectedNode = null;
      flowRender();
      _autoSave();
    }
  }
}

function flowDrop(e) {
  e.preventDefault();
  const type = e.dataTransfer.getData('text/plain');
  if (!type) return;
  const rect = _flowCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  builderAddNodeAt(type, mx - _flowPan.x - FLOW_NODE_W/2, my - _flowPan.y - FLOW_NODE_H/2);
}

function builderAddNode(type) {
  const cx = _flowCanvas ? _flowCanvas.width / 2 : 400;
  const cy = _flowCanvas ? _flowCanvas.height / 2 : 200;
  builderAddNodeAt(type, cx - _flowPan.x - FLOW_NODE_W/2, cy - _flowPan.y - FLOW_NODE_H/2);
}

function builderAddNodeAt(type, x, y) {
  const id = type + '_' + (++_nodeIdCounter);
  const node = { id, type, label: '', x: x || 100, y: y || 100, steps: type === 'procedure' ? [] : undefined };
  if (type === 'start') { node.label = 'Start'; _flowStartId = id; }
  if (type === 'procedure') node.label = 'Procedure ' + _nodeIdCounter;
  _flowNodes.push(node);
  flowRender();
  _autoSave();
}

function openProcEditor(node) {
  const bg = document.createElement('div');
  bg.className = 'proc-modal-bg open';
  bg.innerHTML = '<div class="proc-modal"><div class="proc-modal-header"><span class="proc-modal-title">Edit Procedure: ' + _escapeHtml(node.label || node.id) + '</span><button class="proc-modal-close" onclick="this.closest(\'.proc-modal-bg\').remove()">x</button></div><div class="proc-modal-body"><textarea placeholder="Procedure blocks will go here (Blockly integration coming)"></textarea></div></div>';
  document.body.appendChild(bg);
}

function openCodeEditor(node) {
  const bg = document.createElement('div');
  bg.className = 'proc-modal-bg open';
  bg.innerHTML = '<div class="proc-modal"><div class="proc-modal-header"><span class="proc-modal-title">Code Snippet</span><button class="proc-modal-close">x</button></div><div class="proc-modal-body"><textarea placeholder="print(\'Hello MT2!\')">' + _escapeHtml(node.code || '') + '</textarea></div></div>';
  document.body.appendChild(bg);
  const ta = bg.querySelector('textarea');
  bg.querySelector('.proc-modal-close').addEventListener('click', () => {
    node.code = ta.value;
    bg.remove();
    flowRender();
  });
}

function openMacroPicker(node) {
  const path = prompt('Macro file path (relative to macros/):', node.macro_path || '');
  if (path !== null) { node.macro_path = path; flowRender(); }
}

function builderAddToggle() { alert('Toggle editor coming soon!'); }

// === MODE DATA (variables, config) ===
let _builderModeData = { variables: [], config: [] };

function _varOC(section, idx, field) {
  return "varUpdate('" + section + "'," + idx + ",'" + field + "',this.value)";
}
function _varDel(section, idx) {
  return "varDelRow('" + section + "'," + idx + ")";
}
function varRenderRows(section) {
  var rows = document.getElementById('var-rows-' + section);
  if (!rows) return;
  var data = _builderModeData[section] || [];
  if (!data.length) {
    rows.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px;">Nothing here yet. Click the button below to add.</div>';
    return;
  }
  rows.innerHTML = data.map(function(v, i) {
    var ocName = _varOC(section, i, 'name');
    var ocType = _varOC(section, i, 'type');
    var ocValue = _varOC(section, i, 'value');
    var ocDel = _varDel(section, i);
    var html = '<div class="var-row">';
    html += '<input class="var-name" placeholder="name" value="' + _escapeHtml(v.name || '') + '" onchange="' + ocName + '">';
    html += '<select class="var-type" onchange="' + ocType + '">';
    html += '<option value="string"' + (v.type === 'string' ? ' selected' : '') + '>string</option>';
    html += '<option value="int"' + (v.type === 'int' ? ' selected' : '') + '>int</option>';
    html += '<option value="float"' + (v.type === 'float' ? ' selected' : '') + '>float</option>';
    html += '<option value="bool"' + (v.type === 'bool' ? ' selected' : '') + '>bool</option>';
    html += '</select>';
    html += '<input class="var-value" placeholder="default value" value="' + _escapeHtml(String(v.value == null ? '' : v.value)) + '" onchange="' + ocValue + '">';
    html += '<button class="var-delete" onclick="' + ocDel + '">Del</button>';
    html += '</div>';
    return html;
  }).join('');
}

function varAddRow(section) {
  if (!_builderModeData[section]) _builderModeData[section] = [];
  _builderModeData[section].push({ name: 'new_' + section, type: 'string', value: '' });
  varRenderRows(section);
  _autoSave();
}

function varUpdate(section, idx, field, val) {
  if (!_builderModeData[section] || !_builderModeData[section][idx]) return;
  _builderModeData[section][idx][field] = val;
  _autoSave();
}

function varDelRow(section, idx) {
  if (!_builderModeData[section]) return;
  _builderModeData[section].splice(idx, 1);
  varRenderRows(section);
  _autoSave();
}

// === PROCEDURE EDITOR (in-page overlay with tabs, real Blockly) ===
let _blocklyBlocksData = null;
let _procEditorTabs = {}; // procId -> { node, iframe, tabEl, ready, unsaved, messageHandler }
let _procEditorActive = null;

async function loadBlocklyBlocksData() {
  if (_blocklyBlocksData) return _blocklyBlocksData;
  try {
    const r = await mt2Fetch('/blockly/blocks_data');
    _blocklyBlocksData = await r.json();
  } catch(e) {
    console.error('Failed to load blockly blocks:', e);
    _blocklyBlocksData = { blocks: [], toolbox: '<xml></xml>' };
  }
  return _blocklyBlocksData;
}

function openProcEditor(node) {
  var procId = node.id;

  // If tab already open, just switch to it
  if (_procEditorTabs[procId]) {
    procSwitchToTab(procId);
    return;
  }

  // Show overlay
  var overlay = document.getElementById('proc-editor-overlay');
  overlay.classList.add('open');

  // Create iframe
  var iframe = document.createElement('iframe');
  iframe.className = 'proc-editor-iframe';
  iframe.src = '/blockly/editor';
  document.getElementById('proc-editor-body').appendChild(iframe);

  // Create tab element
  var tabEl = document.createElement('div');
  tabEl.className = 'proc-editor-tab';
  tabEl.innerHTML = '<span class="tab-dot" style="background:#6a5aff"></span>' +
    '<span class="tab-name">' + (node.label || procId) + '</span>' +
    '<span class="tab-close" title="Close">\u00d7</span>';
  tabEl.onclick = function(e) {
    if (e.target.classList.contains('tab-close')) {
      procCloseTab(procId);
    } else {
      procSwitchToTab(procId);
    }
  };
  document.getElementById('proc-editor-tabs').appendChild(tabEl);

  _procEditorTabs[procId] = {
    node: node,
    iframe: iframe,
    tabEl: tabEl,
    ready: false,
    unsaved: false
  };

  // Add close-all button if not present
  if (!document.getElementById('proc-close-all-btn')) {
    var closeBtn = document.createElement('button');
    closeBtn.id = 'proc-close-all-btn';
    closeBtn.className = 'proc-editor-close-btn';
    closeBtn.textContent = 'Close Editor';
    closeBtn.onclick = function() { procCloseAll(); };
    document.getElementById('proc-editor-tabs').appendChild(closeBtn);
  }

  // Listen for messages from this iframe
  var messageHandler = function(event) {
    if (!event.data || !event.data.type) return;
    var data = event.data;

    if (data.type === 'proc_editor_ready') {
      // Check if this message came from our iframe
      if (event.source !== iframe.contentWindow) return;
      loadBlocklyBlocksData().then(function(blocksData) {
        var existingXml = node.blockly_xml || '';
        var callableProcs = _flowNodes
          .filter(function(n) { return n.type === 'procedure' && n.id !== procId; })
          .map(function(n) { return n.label || n.id; });

        iframe.contentWindow.postMessage({
          type: 'proc_init',
          procId: procId,
          procName: node.label || procId,
          blockFiles: blocksData.blocks,
          toolboxXml: blocksData.toolbox,
          variables: _builderModeData.variables || [],
          config: _builderModeData.config || [],
          callableProcs: callableProcs,
          xml: existingXml
        }, '*');

        _procEditorTabs[procId].ready = true;
      });
    }

    if (data.type === 'proc_save') {
      var saveProcId = data.procId;
      if (!_procEditorTabs[saveProcId]) return;
      var tab = _procEditorTabs[saveProcId];
      var savedNode = tab.node;

      savedNode.label = data.procName;
      savedNode.blockly_xml = data.xml;
      savedNode.generated_code = data.code;

      // Update tab name
      var tabName = tab.tabEl.querySelector('.tab-name');
      if (tabName) tabName.textContent = data.procName;
      tab.unsaved = false;

      flowRender();
      _autoSave();

      if (_builderCurrentMode) {
        postJson('/modes/save_procedure', {
          mode_name: _builderCurrentMode.name,
          proc_id: saveProcId,
          proc_name: data.procName,
          xml: data.xml,
          code: data.code
        });
      }
    }
  };

  window.addEventListener('message', messageHandler);
  _procEditorTabs[procId].messageHandler = messageHandler;

  procSwitchToTab(procId);
}

function procSwitchToTab(procId) {
  _procEditorActive = procId;
  for (var id in _procEditorTabs) {
    var tab = _procEditorTabs[id];
    if (id === procId) {
      tab.iframe.classList.add('active');
      tab.tabEl.classList.add('active');
    } else {
      tab.iframe.classList.remove('active');
      tab.tabEl.classList.remove('active');
    }
  }
}

function procCloseTab(procId) {
  var tab = _procEditorTabs[procId];
  if (!tab) return;

  if (tab.messageHandler) {
    window.removeEventListener('message', tab.messageHandler);
  }
  tab.iframe.remove();
  tab.tabEl.remove();
  delete _procEditorTabs[procId];

  if (_procEditorActive === procId) {
    var remaining = Object.keys(_procEditorTabs);
    if (remaining.length > 0) {
      procSwitchToTab(remaining[0]);
    } else {
      document.getElementById('proc-editor-overlay').classList.remove('open');
      _procEditorActive = null;
      var btn = document.getElementById('proc-close-all-btn');
      if (btn) btn.remove();
    }
  }
}

function procCloseAll() {
  var ids = Object.keys(_procEditorTabs);
  for (var i = 0; i < ids.length; i++) {
    var tab = _procEditorTabs[ids[i]];
    if (tab.messageHandler) window.removeEventListener('message', tab.messageHandler);
    tab.iframe.remove();
    tab.tabEl.remove();
    delete _procEditorTabs[ids[i]];
  }
  document.getElementById('proc-editor-overlay').classList.remove('open');
  _procEditorActive = null;
  var btn = document.getElementById('proc-close-all-btn');
  if (btn) btn.remove();
}

function flowSyncData() {
  _builderFlowData = {
    nodes: _flowNodes.map(n => ({ ...n })),
    edges: _flowEdges.map(e => ({ ...e })),
    startNodeId: _flowStartId
  };
}

function flowLoadData(data) {
  _flowNodes = (data.nodes || []).map(n => ({ ...n }));
  _flowEdges = (data.edges || []).map(e => ({ ...e }));
  _flowStartId = data.startNodeId || null;
  _flowSelectedNode = null;
  flowRender();
}

preloadRecorder();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', preloadRecorder, {once:true});
}

</script>
</body>
</html>"""
