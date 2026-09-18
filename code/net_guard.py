# Pause the bot when Windows is offline or 1.1.1.1 / 8.8.8.8 TCP fail.
# No packet-loss %, no Fortnite ping. No force restart.
from __future__ import annotations

import socket
import threading
import time
from ctypes import byref, c_ulong, windll

from logger import get_logger

log = get_logger()

_lock = threading.Lock()
_lagging = False
_fail_streak = 0
_ok_streak = 0
_started = False
_thread: threading.Thread | None = None
_last_probe = 0.0
_holding = False
_redo_pending = False
_path_redo = True
_pause_since = 0.0
_last_status_log = 0.0
_last_snap = {
    "connected": True,
    "tcp": "n/a",
    "reason": "ok",
}

_enabled_cache = (0.0, False)


def _enabled() -> bool:
    global _enabled_cache
    now = time.time()
    ts, val = _enabled_cache
    if now - ts < 0.4:
        return val
    on = False
    try:
        from dashboard import get_state
        snap = get_state() or {}
        if "pause_on_lag" in snap:
            on = bool(snap.get("pause_on_lag"))
        else:
            raise KeyError
    except Exception:
        try:
            import config as _cfg
            on = bool(getattr(_cfg, "PAUSE_ON_LAG", False))
        except Exception:
            on = False
    _enabled_cache = (now, on)
    return on


def _internet_connected() -> bool:
    try:
        flags = c_ulong(0)
        ok = windll.wininet.InternetGetConnectedState(byref(flags), 0)
        if not ok:
            return False
        if int(flags.value) & 0x20:  # INTERNET_CONNECTION_OFFLINE
            return False
        return True
    except Exception:
        return True


def _tcp_probe() -> str:
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            with socket.create_connection((host, port), timeout=0.80):
                return f"{host}:{port}"
        except Exception:
            continue
    return "fail"


def _fmt_snap(s: dict) -> str:
    return (
        f"connected={'yes' if s.get('connected') else 'NO'}  "
        f"tcp={s.get('tcp')}  reason={s.get('reason')}"
    )


def _probe_snapshot() -> dict:
    connected = _internet_connected()
    tcp = _tcp_probe() if connected else "fail"
    reason = "ok"
    if not connected or tcp == "fail":
        reason = "disconnect"
    return {"connected": connected, "tcp": tcp, "reason": reason}


def _should_pause(snap: dict) -> bool:
    return snap.get("reason") != "ok"


def _refresh(force: bool = False) -> bool:
    global _lagging, _fail_streak, _ok_streak, _last_probe, _last_snap, _last_status_log, _pause_since
    now = time.time()
    with _lock:
        if not force and (now - _last_probe) < 0.7:
            return _lagging
        _last_probe = now
    snap = _probe_snapshot()
    _last_snap = snap
    bad = _should_pause(snap)
    with _lock:
        if bad:
            _fail_streak += 1
            _ok_streak = 0
            if not _lagging and _fail_streak >= 2:
                _lagging = True
                _pause_since = now
                log.warning(f"[NET] PAUSE  {_fmt_snap(snap)}")
            elif _lagging and (now - _last_status_log) >= 8.0:
                held = now - _pause_since
                log.info(f"[NET] still paused  t={held:.1f}s  {_fmt_snap(snap)}")
                _last_status_log = now
        else:
            _ok_streak += 1
            _fail_streak = 0
            if _lagging and _ok_streak >= 2:
                held = now - _pause_since if _pause_since else 0.0
                _lagging = False
                log.info(f"[NET] RESUME  paused_for={held:.1f}s  {_fmt_snap(snap)}")
            elif not _lagging:
                if _last_status_log == 0.0:
                    log.info(f"[NET] watching  {_fmt_snap(snap)}")
                    _last_status_log = now
                elif (now - _last_status_log) >= 120.0:
                    log.debug(f"[NET] ok  {_fmt_snap(snap)}")
                    _last_status_log = now
        return _lagging


def is_lagging() -> bool:
    if not _enabled():
        return False
    return _refresh()


def _killed() -> bool:
    try:
        import bot as _bot
        return bool(getattr(_bot, "_KILLED", False))
    except Exception:
        return False


def set_path_redo(enabled: bool) -> None:
    """False during crater farm / active boss fights (no teleport)."""
    global _path_redo
    _path_redo = bool(enabled)


def path_redo_allowed() -> bool:
    return bool(_path_redo)


def peek_redo() -> bool:
    return bool(_redo_pending)


def take_redo() -> bool:
    global _redo_pending
    if not _redo_pending:
        return False
    _redo_pending = False
    return True


def hold_if_needed() -> bool:
    """Block while offline. False if F9.

    After a real pause, keys are released and redo is marked so the bot
    re-does the current path (teleport + walk) instead of resuming mid-macro.
    """
    global _holding, _redo_pending
    if not _enabled():
        return True
    if not is_lagging():
        return True
    if _killed():
        return False
    if _holding:
        while is_lagging() and not _killed():
            time.sleep(0.35)
        return not _killed()
    _holding = True
    paused = False
    allow_redo = bool(_path_redo)
    try:
        paused = True
        if allow_redo:
            _redo_pending = True
            try:
                from macro_runner import stop_macro
                stop_macro()
            except Exception:
                pass
            log.warning(f"[NET] Pause on Lag — wait, then redo path  {_fmt_snap(_last_snap)}")
        else:
            log.warning(f"[NET] Pause on Lag — wait only (boss/crater, no teleport)  {_fmt_snap(_last_snap)}")
        try:
            from overlay import set_overlay
            set_overlay(status="PAUSED", goal="Waiting for connection")
        except Exception:
            pass
        try:
            from dashboard import update_state
            update_state(status="PAUSED", goal="Waiting for connection")
        except Exception:
            pass
        while is_lagging() and not _killed():
            time.sleep(0.45)
        if _killed():
            return False
        if allow_redo:
            log.info(f"[NET] connection back — redo current path  {_fmt_snap(_last_snap)}")
            try:
                from overlay import set_overlay
                set_overlay(status="RUNNING", goal="Redo path")
            except Exception:
                pass
        else:
            log.info(f"[NET] connection back — resume fight  {_fmt_snap(_last_snap)}")
            try:
                from overlay import set_overlay
                set_overlay(status="RUNNING", goal="Connection restored")
            except Exception:
                pass
        return True
    finally:
        _holding = False
        if paused and allow_redo:
            _redo_pending = True


def _loop():
    while True:
        try:
            if _enabled():
                _refresh(force=True)
        except Exception as e:
            log.debug(f"[NET] probe error: {e}")
        time.sleep(1.0)


def start():
    global _started, _thread
    if _started:
        return
    _started = True
    _thread = threading.Thread(target=_loop, name="net-guard", daemon=True)
    _thread.start()
    log.info("[NET] Pause on Lag watcher started")
