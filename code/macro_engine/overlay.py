"""Recorder overlay proxy — drives the bot's single top-left overlay.

A second Tk() root on a background thread wedges the main HUD on Windows.
Recorder play/record state is pushed into overlay.set_recorder_overlay().
"""
import threading


class MacroOverlay:
    _push_warned = False

    def __init__(self):
        self._state = {
            "running": False,
            "recording": False,
            "macro": "-",
            "elapsed": 0.0,
            "estimated": 0.0,
            "progress": 0.0,
            "countdown": 0,
            "mode": "",
            "play_binding": "F6",
            "record_binding": "F5",
        }
        self._lock = threading.Lock()

    def update(self, state: dict):
        with self._lock:
            self._state.update(state or {})
            st = dict(self._state)
        running = bool(st.get("running"))
        recording = bool(st.get("recording"))
        countdown = int(st.get("countdown") or 0)
        active = running or recording or countdown > 0
        rec = str(st.get("record_binding") or "F5")
        play = str(st.get("play_binding") or "F6")
        macro = str(st.get("macro") or "-")
        if countdown > 0:
            mode = "Recording" if st.get("mode") == "record" else "Playing"
            header = "READY"
            goal = f"{mode} in {countdown}..."
            hint = "Get ready"
        elif recording:
            header = "RECORDING"
            goal = macro
            hint = f"{rec}: Stop"
        elif running:
            header = "PLAYING"
            goal = macro
            elapsed = max(0, int(float(st.get("elapsed") or 0)))
            hint = f"{elapsed // 60:02d}:{elapsed % 60:02d}  |  {play}: Stop"
        else:
            header, goal, hint = "", "", ""
        try:
            try:
                from run.overlay import set_recorder_overlay   # forge build layout
            except ImportError:
                from overlay import set_recorder_overlay     # bot layout (code/overlay.py)
            set_recorder_overlay(active=active, header=header, goal=goal, hint=hint)
        except Exception as e:
            # HUD not importable in this build mode - surface it once so
            # "overlay not showing during F5/F6" is diagnosable, not silent.
            if not MacroOverlay._push_warned:
                MacroOverlay._push_warned = True
                try:
                    import sys
                    print(f"[macro overlay] recorder HUD unavailable: {e}",
                          file=sys.stderr, flush=True)
                except Exception:
                    pass
