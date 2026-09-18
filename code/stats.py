# ============================================================
# MT2 REBIRTH BOT - STATS TRACKER
# Persists to stats.json
# ============================================================
import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from logger import get_logger, cprint
from config import STATS_FILE, STONE_FOR_A5_STAGE1, STONE_FOR_A5_STAGE2, STONE_FOR_A5_STAGE3, STONE_FOR_A5_STAGE4

log = get_logger()
MAX_RUN_HISTORY = 25000

def _fmt_time(secs: float) -> str:
    if secs == float("inf") or secs <= 0:
        return "—"
    m, s = divmod(int(secs), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"

@dataclass
class RunStats:
    run_number:    int   = 0
    start_time:    float = 0.0   # epoch
    end_time:      float = 0.0
    error_count:   int   = 0     # retries / failures this run
    step_count:    int   = 0     # steps taken this run
    duration_secs: float = 0.0   # filled on completion
    start_stone:   float = -1.0  # HUD stone at run start; -1 = unknown
    start_mode:    str   = ""
    full_rebirth:  bool  = True  # True = started from ~0 stone (spawn) and finished
    quests_completed: int = 0            # Daily Quests: quests claimed this run

@dataclass
class GlobalStats:
    total_rebirths:     int   = 0
    total_errors:       int   = 0
    min_time_secs:      float = float("inf")
    max_time_secs:      float = 0.0
    total_time_secs:    float = 0.0
    run_history:        list  = field(default_factory=list)

    @property
    def average_time_secs(self) -> float:
        if self.total_rebirths == 0:
            return 0.0
        return self.total_time_secs / self.total_rebirths

    def to_dict(self) -> dict:
        d = asdict(self)
        d["average_time_secs"] = self.average_time_secs
        for key in ("min_time_secs", "max_time_secs", "total_time_secs", "average_time_secs"):
            try:
                if not math.isfinite(float(d.get(key, 0.0))):
                    d[key] = 0.0
            except Exception:
                d[key] = 0.0
        return d


class StatsTracker:
    def __init__(self):
        self.global_stats = GlobalStats()
        self._current_run: Optional[RunStats] = None

        # Live run tracking — updated by bot as stages complete
        self._stage_unlocked = {1: False, 2: False, 3: False, 4: False}
        self._stage_stone    = {1: None,  2: None,  3: None,  4: None}   # stone when unlocked
        self._run_start_time = 0.0

        self._load()

    def _trim_history(self):
        gs = self.global_stats
        if not isinstance(gs.run_history, list):
            gs.run_history = []
        if len(gs.run_history) > MAX_RUN_HISTORY:
            gs.run_history = gs.run_history[-MAX_RUN_HISTORY:]

    def _repair_summary_from_history(self):
        gs = self.global_stats
        hist = [r for r in (gs.run_history or []) if isinstance(r, dict)]
        durations = []
        total_errors = 0
        for r in hist:
            try:
                d = float(r.get("duration_secs", 0.0) or 0.0)
                if math.isfinite(d) and d > 0:
                    durations.append(d)
            except Exception:
                pass
            try:
                total_errors += int(r.get("error_count", 0) or 0)
            except Exception:
                pass

        if hist and int(gs.total_rebirths or 0) <= 0:
            gs.total_rebirths = len(hist)
        if hist and int(gs.total_errors or 0) <= 0:
            gs.total_errors = total_errors
        if durations:
            if not gs.total_time_secs or gs.total_time_secs <= 0:
                gs.total_time_secs = sum(durations)
            if not gs.min_time_secs or gs.min_time_secs <= 0 or not math.isfinite(float(gs.min_time_secs)):
                gs.min_time_secs = min(durations)
            if not gs.max_time_secs or gs.max_time_secs <= 0:
                gs.max_time_secs = max(durations)

    def _load(self):
        if os.path.exists(STATS_FILE):
            try:
                # Accept UTF-8 BOM to avoid startup failures after external edits.
                with open(STATS_FILE, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                gs = self.global_stats
                gs.total_rebirths  = data.get("total_rebirths", 0)
                gs.total_errors    = data.get("total_errors", 0)
                _raw_min = data.get("min_time_secs", float("inf"))
                gs.min_time_secs   = float("inf") if (_raw_min == 0.0 and int(data.get("total_rebirths", 0)) > 0) else _raw_min
                gs.max_time_secs   = data.get("max_time_secs", 0.0)
                gs.total_time_secs = data.get("total_time_secs", 0.0)
                gs.run_history     = data.get("run_history", [])
                self._trim_history()
                self._repair_summary_from_history()
                log.debug(f"Stats loaded: {gs.total_rebirths} rebirths so far")
            except Exception as e:
                log.warning(f"Could not load stats: {e}")
            finally:
                gs = self.global_stats
                for attr in ("min_time_secs", "max_time_secs", "total_time_secs"):
                    try:
                        if not math.isfinite(float(getattr(gs, attr))):
                            setattr(gs, attr, 0.0)
                    except Exception:
                        setattr(gs, attr, 0.0)

    def save(self):
        try:
            self._trim_history()
            os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
            tmp_path = f"{STATS_FILE}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.global_stats.to_dict(), f, indent=2, allow_nan=False)
            os.replace(tmp_path, STATS_FILE)
        except Exception as e:
            log.warning(f"Could not save stats: {e}")

    # ── Run lifecycle ────────────────────────────────────────

    def start_run(self, start_stone=None, start_mode: str = ""):
        stone_val = -1.0
        try:
            if start_stone is not None:
                stone_val = float(start_stone)
        except Exception:
            stone_val = -1.0
        mode = str(start_mode or "").strip().lower()
        # Full = HUD stone is ~0 (just rebirthed). Unreadable HUD is NOT resumed
        # (4K/OCR miss used to mark every a5meteor run as resumed).
        if stone_val < 0:
            full = True
        else:
            full = stone_val <= 1.0
        self._current_run = RunStats(
            run_number = self.global_stats.total_rebirths + 1,
            start_time = time.time(),
            start_stone = stone_val,
            start_mode = mode,
            full_rebirth = bool(full),
        )
        self._run_start_time = self._current_run.start_time
        self._stage_unlocked = {1: False, 2: False, 3: False, 4: False}
        self._stage_stone    = {1: None,  2: None,  3: None,  4: None}
        log.info(
            f"Run #{self._current_run.run_number} started  stone={stone_val}  "
            f"mode={mode or '-'}  full={self._current_run.full_rebirth}"
        )

    def mark_stage_unlocked(self, stage: int, stone: float = None):
        """Call this right after a stage rock_hit succeeds."""
        self._stage_unlocked[stage] = True
        self._stage_stone[stage]    = stone
        self._increment_step()
        log.debug(f"Stage {stage} unlocked — stone: {stone}")
        self.print_run_status()
        
    def _increment_step(self):
        if self._current_run:
            self._current_run.step_count += 1
        try:
            from dashboard import update_state as _du
            _du(run_steps=self._current_run.step_count if self._current_run else 0)
        except Exception:
            pass

    def mark_step(self, label: str = ""):
        """Increment the live dashboard step counter for non-stage milestones."""
        self._increment_step()
        log.debug(f"Run step complete{f': {label}' if label else ''}")

    def record_error(self):
        if self._current_run:
            self._current_run.error_count += 1
        self.global_stats.total_errors += 1
        try:
            from dashboard import update_state as _du
            _du(run_errors=self._current_run.error_count if self._current_run else 0,
                total_errors=self.global_stats.total_errors)
        except Exception:
            pass

    def add_quest_completed(self):
        """Daily Quests: count one successfully claimed quest into the current run."""
        if not self._current_run:
            return
        self._current_run.quests_completed = int(getattr(self._current_run, "quests_completed", 0)) + 1
        try:
            from dashboard import update_state as _du
            _du(run_quests_completed=self._current_run.quests_completed)
        except Exception:
            pass
        log.info(f"[QUEST] quests completed this run: {self._current_run.quests_completed}")

    def finish_run(self):
        if not self._current_run:
            return
        r = self._current_run
        r.end_time      = time.time()
        r.duration_secs = r.end_time - r.start_time

        gs = self.global_stats
        gs.total_rebirths  += 1
        gs.total_time_secs += r.duration_secs
        if r.duration_secs < gs.min_time_secs:
            gs.min_time_secs = r.duration_secs
        if r.duration_secs > gs.max_time_secs:
            gs.max_time_secs = r.duration_secs
        gs.run_history.append(asdict(r))
        self._trim_history()

        self.save()
        try:
            # Run record is now in history — clear the live per-run counter so
            # the dashboard's All Time / Avg can't double-count this run while
            # the bot idles before the next one starts.
            from dashboard import update_state as _du0
            _du0(run_quests_completed=0)
        except Exception:
            pass
        log.info(
            f"Run #{r.run_number} complete — "
            f"{_fmt_time(r.duration_secs)} | full={r.full_rebirth} | errors: {r.error_count} | "
            f"avg: {_fmt_time(gs.average_time_secs)} | best: {_fmt_time(gs.min_time_secs)} | "
            f"worst: {_fmt_time(gs.max_time_secs)} | total rebirths: {gs.total_rebirths}"
        )
        self._current_run = None

    # ── Display ─────────────────────────────────────────────

    def _stage_line(self, stage: int, threshold: float) -> str:
        """Build the stage unlock line for the current run display."""
        if self._stage_unlocked.get(stage):
            stone_str = f"  ({self._stage_stone[stage]:.2e})" if self._stage_stone[stage] else ""
            return f"  Stage {stage}  done{stone_str}", "info"
        else:
            need = f"need {threshold:.2e}" if threshold > 0 else "need: TODO"
            return f"  Stage {stage}  pending  [{need}]", "info"

    def print_run_status(self):
        """Print live current-run status with stage unlock progress."""
        r  = self._current_run
        gs = self.global_stats

        elapsed = time.time() - self._run_start_time if self._run_start_time else 0
        run_num = r.run_number if r else gs.total_rebirths + 1
        errors  = r.error_count if r else 0

        thresholds = {
            1: STONE_FOR_A5_STAGE1,
            2: STONE_FOR_A5_STAGE2,
            3: STONE_FOR_A5_STAGE3,
            4: STONE_FOR_A5_STAGE4,
        }

        avg = _fmt_time(gs.average_time_secs)
        mn  = _fmt_time(gs.min_time_secs)
        mx  = _fmt_time(gs.max_time_secs)

        cprint(f"")
        cprint(f"Run #{run_num}  |  elapsed: {_fmt_time(elapsed)}  |  errors: {errors}")
        for stage in range(1, 5):
            line, lvl = self._stage_line(stage, thresholds[stage])
            cprint(line, lvl)
        cprint(f"Total rebirths: {gs.total_rebirths}  |  avg: {avg}  |  best: {mn}  |  worst: {mx}")

    def print_summary(self):
        """Short summary shown at startup and after each rebirth."""
        gs  = self.global_stats
        avg = _fmt_time(gs.average_time_secs)
        mn  = _fmt_time(gs.min_time_secs)
        mx  = _fmt_time(gs.max_time_secs)
        cprint(f"")
        cprint(f"Stats  |  rebirths: {gs.total_rebirths}  |  errors: {gs.total_errors}  |  avg: {avg}  |  best: {mn}  |  worst: {mx}")
        cprint(f"")
