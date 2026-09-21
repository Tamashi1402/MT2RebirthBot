# ============================================================
# MT2 BOT - DISPLAY PROBE  (v1.0)
#
# Purpose: find out, from the log alone, exactly what happens to
# screen capture / window focus when the physical display is
# turned off (or Windows blanks it). Yesterday's report was
# "bot runs longer than it should or fails shortly after I turn
# the monitor back on" — the suspects are:
#
#   1. Capture goes BLACK while the display is off (GPU/driver
#      dependent) → is_rebirth_screen() sees an eternal respawn,
#      GAME_DETECT fails, FR_FLOW thinks we left the game.
#   2. The PC went to SLEEP (nothing in the bot prevents it) →
#      the whole process freezes, Fortnite disconnects.
#   3. Display topology change on DP/HDMI disconnect (window
#      minimized / moved to a phantom monitor, resolution change).
#
# This probe runs a small background thread (same pattern as
# net_guard) that grabs the full screen every DISPLAY_PROBE_SECONDS
# and logs one compact line per probe:
#
#   [DISPLAY] probe black=0.0% dark=1.4% vivid=37.2% v=91.3 grab=9ms
#             res=1920x1080 nmon=1 fg='Fortnite  ' fn_min=False
#             hud=True diff=0.01%
#
# State transitions are the important part:
#   [DISPLAY] capture went BLACK — display content unreadable (display off?)  <- WARN on entry
#   [DISPLAY] still black ... 8m 0s (16 probes)                               <- heartbeat
#   [DISPLAY] capture RESTORED — black window lasted 59.5m (119 probes)      <- INFO on exit
#   [DISPLAY] capture went DARK (not pure black) — unusual ...                <- WARN entry
#   [DISPLAY] TIME GAP: loop stalled for 1874.3s — system slept or froze     <- WARN sleep detector
#
# So after a display-off test you can grep "\[DISPLAY\]" and see
# exactly which of the three suspects bit, when, and for how long.
# If capture never goes black and there is no time gap, display-off
# is innocent and the overnight failure is something else.
#
# The probe never blocks or interacts with the game — it only
# reads the screen, same mss GDI path the rest of the bot uses.
from __future__ import annotations

import time
import threading

from logger import get_logger

log = get_logger()

_started = False
_thread: "threading.Thread | None" = None
_stop_ev = threading.Event()

# ── Shared probe state (readable by other modules) ─────────────────────────
_last_stats: dict = {}
_lock = threading.Lock()

# Black / dark classification thresholds — same idea as
# screen.is_rebirth_screen() so the probe agrees with what the
# rebirth detector would conclude from the same frame.
_BLACK_RATIO = 0.75   # gray < 30 over 75% of the frame → "black capture"
_DARK_RATIO = 0.75    # gray < 55 over 75% → "dark capture"
_VIVID_SAT = 60       # live game content has saturated bright pixels;
_VIVID_V = 120        # a dead capture has vivid ≈ 0%


def _cfg():
    import config as _config
    return _config


def _probe_seconds() -> float:
    try:
        v = float(getattr(_cfg(), "DISPLAY_PROBE_SECONDS", 30))
        return max(5.0, min(v, 300.0))
    except Exception:
        return 30.0


def _probe_enabled() -> bool:
    try:
        return bool(getattr(_cfg(), "DISPLAY_PROBE_ENABLED", True))
    except Exception:
        return True


def last_stats() -> dict:
    """Latest probe result (may be empty before the first probe)."""
    with _lock:
        return dict(_last_stats)


def is_capture_black() -> bool:
    """True if the last probe classified the capture as BLACK.
    Callers can use this to distrust black-frame conclusions
    (rebirth screen, HUD miss) while the display is known-off."""
    with _lock:
        return bool(_last_stats.get("state") == "BLACK")


# ── Frame stats ────────────────────────────────────────────────────────────
def _grab_stats() -> dict | None:
    """Full-screen grab + luma/saturation stats. None if the grab failed."""
    t0 = time.perf_counter()
    try:
        import mss
        import numpy as np
        import cv2
        with mss.mss() as sct:
            mon = sct.monitors[1]
            n_mon = max(0, len(sct.monitors) - 1)
            raw = sct.grab(mon)
            img = np.array(raw)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        grab_ms = (time.perf_counter() - t0) * 1000.0

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        total = float(gray.shape[0] * gray.shape[1])
        if total <= 0:
            return None

        black_ratio = float(np.sum(gray < 30)) / total
        dark_ratio = float(np.sum(gray < 55)) / total
        vivid = float(
            np.sum((hsv[:, :, 1] > _VIVID_SAT) & (hsv[:, :, 2] > _VIVID_V))
        ) / total
        mean_v = float(np.mean(hsv[:, :, 2]))
        return {
            "black_ratio": black_ratio,
            "dark_ratio": dark_ratio,
            "vivid_ratio": vivid,
            "mean_v": mean_v,
            "grab_ms": grab_ms,
            "res": f"{gray.shape[1]}x{gray.shape[0]}",
            "n_mon": n_mon,
        }
    except Exception as e:
        log.warning(f"[DISPLAY] probe grab failed: {e}")
        return None


# ── Window / focus facts ────────────────────────────────────────────────────
def _window_facts() -> dict:
    """Foreground title + Fortnite window minimized/visible state."""
    out = {"fg": "", "fg_fn": False, "fn_min": None, "fn_visible": None}
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            out["fg"] = buf.value
            out["fg_fn"] = "Fortnite" in buf.value

        fn = 0

        def _cb(hwnd, _):
            nonlocal fn
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buf2 = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf2, length + 1)
                if "Fortnite" in buf2.value:
                    fn = hwnd
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )
        user32.EnumWindows(EnumWindowsProc(_cb), 0)
        if fn:
            out["fn_min"] = bool(user32.IsIconic(fn))
            out["fn_visible"] = bool(user32.IsWindowVisible(fn))
    except Exception:
        pass
    return out


def _hud_facts() -> dict:
    """GAME_DETECT result for this frame (only if the user picked one).
    This is the exact signal FR_FLOW trusts — logged so we can see
    whether display-off makes the bot 'believe' it left the game."""
    out: dict = {}
    try:
        from game_detect import game_detect_result
        r = game_detect_result()
        if r.get("set"):
            out["hud"] = bool(r.get("ok"))
            d = r.get("diff")
            out["diff"] = "?" if d is None else f"{d:.2f}%"
    except Exception:
        pass
    return out


def _fmt_probe(st: dict, wf: dict, hud: dict) -> str:
    bits = [
        f"black={st['black_ratio']*100:.1f}%",
        f"dark={st['dark_ratio']*100:.1f}%",
        f"vivid={st['vivid_ratio']*100:.1f}%",
        f"v={st['mean_v']:.1f}",
        f"grab={st['grab_ms']:.0f}ms",
        f"res={st['res']}",
        f"nmon={st['n_mon']}",
        f"fg={wf['fg']!r}",
        f"fn_min={wf['fn_min']}",
    ]
    if "hud" in hud:
        bits.append(f"hud={hud['hud']}")
        bits.append(f"diff={hud.get('diff', '?')}")
    return " ".join(bits)


def _loop():
    global _last_stats
    probe_secs = _probe_seconds()
    state = "NORMAL"          # NORMAL | BLACK | DARK
    state_since = time.time()
    state_probes = 0
    last_loop = time.time()
    log.info(
        f"[DISPLAY] probe started (every {probe_secs:.0f}s) — logs what capture "
        f"sees while the display is off; grep '[DISPLAY]' after the test"
    )
    while not _stop_ev.wait(probe_secs):
        now = time.time()

        # ── Sleep / freeze detector ─────────────────────────────────────
        gap = now - last_loop
        last_loop = time.time()
        if gap > probe_secs * 3.0:
            log.warning(
                f"[DISPLAY] TIME GAP: loop stalled for {gap:.1f}s "
                f"(expected {probe_secs:.0f}s) — system slept / display driver froze"
            )
            # State conclusions from before the gap are stale — re-baseline.
            state = "NORMAL"
            state_since = now
            state_probes = 0

        st = _grab_stats()
        if st is None:
            continue
        wf = _window_facts()
        hud = _hud_facts()

        # ── Classify this frame ────────────────────────────────────────
        if st["black_ratio"] > _BLACK_RATIO:
            new_state = "BLACK"
        elif st["dark_ratio"] > _DARK_RATIO:
            new_state = "DARK"
        else:
            new_state = "NORMAL"

        dur = now - state_since
        if new_state != state:
            if new_state == "BLACK":
                log.warning(
                    f"[DISPLAY] capture went BLACK — display content unreadable "
                    f"(display off / black capture). {_fmt_probe(st, wf, hud)}"
                )
            elif new_state == "DARK":
                log.warning(
                    f"[DISPLAY] capture went DARK (not pure black) — unusual, "
                    f"verify the game screen is actually visible. "
                    f"{_fmt_probe(st, wf, hud)}"
                )
            else:
                was = state
                log.info(
                    f"[DISPLAY] capture {'RESTORED' if was == 'BLACK' else 'normalized'} "
                    f"— {was.lower()} window lasted {dur/60:.1f}m ({state_probes} probes). "
                    f"{_fmt_probe(st, wf, hud)}"
                )
            state = new_state
            state_since = now
            state_probes = 0
        else:
            state_probes += 1
            if state == "NORMAL":
                log.info(f"[DISPLAY] probe {_fmt_probe(st, wf, hud)}")
            elif state == "BLACK":
                # Heartbeat every 8 probes (~4 min at 30s) instead of spamming.
                if state_probes % 8 == 0:
                    log.warning(
                        f"[DISPLAY] still black ... {dur/60:.0f}m ({state_probes} probes)"
                    )
            elif state == "DARK":
                if state_probes % 8 == 0:
                    log.warning(
                        f"[DISPLAY] still dark ... {dur/60:.0f}m ({state_probes} probes)"
                    )

        with _lock:
            _last_stats = {
                "t": now,
                "state": state,
                **st,
                **hud,
            }
        probe_secs = _probe_seconds()   # pick up config changes live


def start():
    """Start the display probe thread (idempotent, daemon)."""
    global _started, _thread
    if _started or not _probe_enabled():
        return
    _started = True
    _thread = threading.Thread(target=_loop, name="display-probe", daemon=True)
    _thread.start()
    log.info("[DISPLAY] display probe watcher started")


def stop():
    """Stop the probe thread (used by tests / soft shutdown)."""
    global _started
    _stop_ev.set()
    _started = False
