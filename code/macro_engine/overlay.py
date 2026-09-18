"""Recorder overlay proxy — drives the bot's single top-left overlay.

A second Tk() root on a background thread wedges the main HUD on Windows.
Recorder play/record state is pushed into overlay.set_recorder_overlay().
"""
import threading


class MacroOverlay:
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
            from overlay import set_recorder_overlay
            set_recorder_overlay(active=active, header=header, goal=goal, hint=hint)
        except Exception:
            pass
