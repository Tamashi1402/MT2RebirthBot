# ============================================================
# MT2 BOT - OVERLAY  (v9 â€” Win32 HWND_TOPMOST + layered window)
# Renders OVER fullscreen DirectX games (Fortnite, etc.)
# Uses ctypes SetWindowPos + SetWindowLong to punch through
# the DX exclusive fullscreen surface.
# Always-on-top at 0,0. Grows DOWNWARD.
# ============================================================
import threading
import tkinter as tk
import ctypes
import ctypes.wintypes
import time
import re
from typing import Optional

# â”€â”€ Win32 constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW  = 0x00000080
WS_EX_TOPMOST     = 0x00000008   # informational â€” set via SetWindowPos
LWA_ALPHA         = 0x00000002
LWA_COLORKEY      = 0x00000001

HWND_TOPMOST      = ctypes.wintypes.HWND(-1)
SWP_NOMOVE        = 0x0002
SWP_NOSIZE        = 0x0001
SWP_NOACTIVATE    = 0x0010
SWP_SHOWWINDOW    = 0x0040

user32 = ctypes.windll.user32

def _get_hwnd(tk_root) -> int:
    """Return the Win32 HWND for a tkinter Tk/Toplevel window."""
    return int(tk_root.frame(), 16)

def _hex_to_colorref(color: str) -> int:
    """Convert '#RRGGBB' to Win32 COLORREF (0x00bbggrr)."""
    color = str(color or "").strip()
    if color.startswith("#"):
        color = color[1:]
    if len(color) != 6:
        return 0
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return r | (g << 8) | (b << 16)

def _apply_win32_overlay_styles(tk_root, alpha_byte: int = 224, click_through: bool = False, transparent_color: str = None):
    """
    Set Win32 extended window styles so the overlay sits on top of
    fullscreen DX games:
      â€¢ WS_EX_LAYERED   â€” enables per-window alpha
      â€¢ WS_EX_TOOLWINDOW â€” hides it from Alt-Tab
      â€¢ SetWindowPos(HWND_TOPMOST) â€” true Win32 Z-order topmost
      â€¢ SetLayeredWindowAttributes â€” applies opacity
    """
    try:
        hwnd = _get_hwnd(tk_root)
        # Add layered + toolwindow to existing exstyle
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        exstyle |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
        if click_through:
            exstyle |= WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle)
        # Win32 TOPMOST z-order (stronger than tkinter's -topmost)
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
        # Alpha (0â€“255)
        if transparent_color:
            user32.SetLayeredWindowAttributes(hwnd, _hex_to_colorref(transparent_color), alpha_byte, LWA_ALPHA | LWA_COLORKEY)
        else:
            user32.SetLayeredWindowAttributes(hwnd, 0, alpha_byte, LWA_ALPHA)
        get_logger().debug(f"[OVERLAY] Win32 styles applied â€” hwnd={hwnd:#010x} alpha={alpha_byte}")
    except Exception as e:
        get_logger().warning(f"[OVERLAY] _apply_win32_overlay_styles failed: {e}")

def _reapply_topmost(tk_root, show_window: bool = True):
    """Re-assert HWND_TOPMOST every tick â€” game reclaims Z-order on each frame."""
    try:
        hwnd = _get_hwnd(tk_root)
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | (SWP_SHOWWINDOW if show_window else 0),
        )
    except Exception:
        pass

# â”€â”€ Shared state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_state = {
    "goal":       "Ready",
    "auto_str":   None,
    "stone":      None,
    "status":     "INIT",
    "next_steps": "",
    "stone_frozen": False,
    "show_auto_str": False,
    "manual_position": False,
    "run_start_time": None,
    # Crater rock-detection overlay -- driven by crater/overlay.py (proxy, no separate Tk()).
    "crater_esp_active": False,
    "crater_capture_rect": None,
    "crater_rock_boxes": [],
    "crater_rock_ids": [],     # persistent IDs for each rock box
    "crater_target_box": None,
    "crater_timer_box": None,
    "crater_timer_state": "ok",
    "recorder_active": False,
    "recorder_header": "",
    "recorder_goal": "",
    "recorder_hint": "",
}
_lock = threading.Lock()

_macro_active: bool = False
_macro_active_lock  = threading.Lock()
_overlay_instance = None
_capture_hide_until = 0.0

def notify_macro_end(name: str = ""):
    global _macro_active
    with _macro_active_lock:
        _macro_active = False

def hide_for_capture(seconds: float = 0.8):
    """Temporarily hide overlay so dashboard screenshots do not capture it."""
    global _capture_hide_until
    _capture_hide_until = max(_capture_hide_until, time.time() + seconds)
    inst = _overlay_instance
    if inst is not None:
        try:
            hwnd = _get_hwnd(inst.root)
            user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
        try:
            inst.root.after(0, inst.root.withdraw)
        except Exception:
            pass


def set_overlay(goal=None, auto_str=None, stone=None, status=None, next_steps=None, stone_frozen=None, show_auto_str=None, manual_position=None, run_start_time=None):
    with _lock:
        if goal         is not None: _state["goal"]         = goal
        if auto_str     is not None: _state["auto_str"]     = auto_str
        if stone        is not None: _state["stone"]        = stone
        if status       is not None: _state["status"]       = status
        if next_steps   is not None: _state["next_steps"]   = next_steps
        if stone_frozen is not None: _state["stone_frozen"] = stone_frozen
        if show_auto_str is not None: _state["show_auto_str"] = bool(show_auto_str)
        if manual_position is not None: _state["manual_position"] = bool(manual_position)
        if run_start_time is not None: _state["run_start_time"] = (None if run_start_time == 0 else run_start_time)


def set_recorder_overlay(active=None, header=None, goal=None, hint=None):
    """Push Recorder play/record HUD into the shared top-left overlay."""
    with _lock:
        if active is not None:
            _state["recorder_active"] = bool(active)
        if header is not None:
            _state["recorder_header"] = str(header or "")
        if goal is not None:
            _state["recorder_goal"] = str(goal or "")
        if hint is not None:
            _state["recorder_hint"] = str(hint or "")

def set_esp_boxes(boxes=None, enabled=None, source_size=None):
    """No-op. AI/YOLO ESP was removed. Crater overlay uses set_crater_esp()."""
    return None

def set_crater_esp(capture_rect=None, rock_boxes=None, target_box=None,
                   timer_box=None, timer_state=None, rock_ids=None):
    """Push crater rock/timer ESP boxes into the shared overlay state.
    Called by crater/overlay.py (proxy) -- rendered by _Overlay._update_crater_esp
    on the main overlay's own Tk()/thread, no second Tk() instance involved."""
    with _lock:
        if capture_rect is not None:
            _state["crater_capture_rect"] = capture_rect
        if rock_boxes is not None:
            _state["crater_rock_boxes"] = list(rock_boxes)
        if rock_ids is not None:
            _state["crater_rock_ids"] = list(rock_ids)
        if target_box is not None:
            _state["crater_target_box"] = target_box
        if timer_box is not None:
            _state["crater_timer_box"] = timer_box
        if timer_state is not None:
            _state["crater_timer_state"] = timer_state


def clear_crater_esp():
    with _lock:
        _state["crater_capture_rect"] = None
        _state["crater_rock_boxes"] = []
        _state["crater_rock_ids"] = []
        _state["crater_target_box"] = None
        _state["crater_timer_box"] = None
        _state["crater_timer_state"] = "ok"


def set_crater_esp_active(active: bool):
    with _lock:
        _state["crater_esp_active"] = bool(active)

def _plain_text(value) -> str:
    text = "" if value is None else str(value)
    text = (text.replace("â€”", "-")
                .replace("—", "-")
                .replace("â†’", "->")
                .replace("→", "->")
                .replace("âœ“", "")
                .replace("✓", "")
                .replace("â›”", "")
                .replace("⚠️", "")
                .replace("⚠", ""))
    text = re.sub(r"[^\x20-\x7E]", "", text)
    return " ".join(text.split())

def _stage_goal(stage: str, area: int = 5) -> str:
    try:
        area_n = int(area)
    except Exception:
        area_n = 5
    return f"Area {area_n} - Stage {int(stage)}"

def _resolve_goal(status: str, goal: str) -> str:
    """Turn internal bot goals into short overlay labels."""
    up = _plain_text(status).upper()
    g = _plain_text(goal)
    low = g.lower()

    if not g or g in ("...", "-"):
        if "MENU RESUME" in up:
            return "Joining"
        return ""

    if "press start" in low or low == "ready":
        return "Ready"
    if "no focus" in low:
        return "No focus"
    if "manual strength" in low or "strength" in low:
        return "Strength"
    if "unlocking drill" in low or "unlock drills" in low:
        return "Unlock Drills"
    if "pressing play" in low:
        return "Play"
    if "not in menu" in low:
        return "Not in menu"
    if "recover" in low:
        return "Recovering"
    if "fallback" in low and "base" in low and "rock" in low:
        return "Base Rock"

    g = re.sub(r"(?i)^mining\s+", "", g).strip()
    g = re.sub(r"(?i)\s*-\s*topup$", "", g).strip()
    g = re.sub(r"(?i)\s+topup$", "", g).strip()
    g = re.sub(r"(?i)\s*-\s*blind hit$", "", g).strip()
    g = re.sub(r"(?i)^fallback:\s*", "", g).strip()
    low = g.lower()

    compact = re.search(r"\ba(\d+)\s*s(\d+)\b", g, flags=re.IGNORECASE)
    if compact:
        return _stage_goal(compact.group(2), int(compact.group(1)))
    area_then_stage = re.search(r"area\s*(\d+).*?stage\s*(\d+)", g, flags=re.IGNORECASE)
    if area_then_stage:
        return _stage_goal(area_then_stage.group(2), int(area_then_stage.group(1)))
    a_stage = re.search(r"\ba(\d+)\s+stage\s*(\d+)", g, flags=re.IGNORECASE)
    if a_stage:
        return _stage_goal(a_stage.group(2), int(a_stage.group(1)))
    stage_match = re.search(r"stage\s*(\d+)", g, flags=re.IGNORECASE)
    if stage_match:
        area_n = 5
        am = re.search(r"area\s*(\d+)|\ba(\d+)\b", g, flags=re.IGNORECASE)
        if am:
            area_n = int(am.group(1) or am.group(2))
        return _stage_goal(stage_match.group(1), area_n)

    if "base" in low and "rock" in low:
        return "Base Rock"
    if low in ("base", "teleport base"):
        return "Base"
    if "area 5" in low or low in ("a5", "area5"):
        return "Area 5"
    if "meteor" in low:
        return "Meteor"
    if "rebirth" in low:
        return "Rebirth"
    if "cooldown" in low:
        return "Cooldown"
    if "settle" in low:
        return "Settling"
    if low.startswith("hitting "):
        return g[8:].strip().title()
    return g

# Suffix display table â€” sorted largest-first for _fmt_stone()
_STONE_SUFFIXES = [
    (306, "DDd"), (303, "Dd"),  (300, "NNn"), (297, "ONn"), (294, "SpNn"),
    (291, "SxNn"),(288, "QtNn"),(285, "QaNn"),(282, "TNn"), (279, "DNn"),
    (276, "UNn"), (273, "Nn"),  (270, "NOg"), (267, "OOg"), (264, "SpOg"),
    (261, "SxOg"),(258, "QtOg"),(255, "QaOg"),(252, "TOg"), (249, "DOg"),
    (246, "UOg"), (243, "Og"),  (240, "NSt"), (237, "OSt"), (234, "SpSt"),
    (231, "SxSt"),(228, "QtSt"),(225, "QaSt"),(222, "TSt"), (219, "DSt"),
    (216, "USt"), (213, "St"),  (210, "NSe"), (207, "OSe"), (204, "SpSe"),
    (201, "SxSe"),(198, "QtSe"),(195, "QaSe"),(192, "TSe"), (189, "DSe"),
    (186, "USe"), (183, "Se"),  (180, "NQi"), (177, "OQi"), (174, "SpQi"),
    (171, "SxQi"),(168, "QtQi"),(165, "QaQi"),(162, "TQi"), (159, "DQi"),
    (156, "UQi"), (153, "Qi"),  (150, "NQd"), (147, "OQd"), (144, "SpQd"),
    (141, "SxQd"),(138, "QtQd"),(135, "QaQd"),(132, "TQd"), (129, "DQd"),
    (126, "UQd"), (123, "Qd"),  (120, "NTg"), (117, "OTg"), (114, "SpTg"),
    (111, "SxTg"),(108, "QtTg"),(105, "QaTg"),(102, "TTg"), (99,  "DTg"),
    (96,  "UTg"), (93,  "Tg"),  (90,  "NVg"), (87,  "OVg"), (84,  "SpVg"),
    (81,  "SxVg"),(78,  "QtVg"),(75,  "QaVg"),(72,  "TVg"), (69,  "DVg"),
    (66,  "UVg"), (63,  "Vg"),  (60,  "NDc"), (57,  "ODc"), (54,  "SpDc"),
    (51,  "SxDc"),(48,  "QtDc"),(45,  "QaDc"),(42,  "TDc"), (39,  "DDc"),
    (36,  "UDc"), (33,  "Dc"),  (30,  "No"),  (27,  "Oc"),  (24,  "Sp"),
    (21,  "Sx"),  (18,  "Qt"),  (15,  "Qa"),  (12,  "T"),   (9,   "B"),
    (6,   "M"),   (3,   "K"),
]

# Which display mode the user is running â€” auto-detected from the first valid read.
# "eng"    â†’ engineering notation:  4.53e123
# "suffix" â†’ suffix notation:       4.53OcDc
_stone_display_mode = "eng"   # default; updated by set_stone_display_mode()

def set_stone_display_mode(mode: str):
    """Call with "eng" or "suffix" to switch overlay display format."""
    global _stone_display_mode
    if mode in ("eng", "suffix"):
        _stone_display_mode = mode

def _fmt_stone(s) -> str:
    """Format stone value to match the game HUD display mode (eN or suffix).
    The internal value is always a plain float â€” only the display changes.
    Both modes stay in sync with the same float, so thresholds need no changes.
    """
    if s is None:
        return "-"
    try:
        import math
        v = float(s)
        if v <= 0:
            return "0"
        exp = int(math.floor(math.log10(abs(v))))

        if _stone_display_mode == "suffix":
            # Find the largest matching suffix
            for thresh_exp, suffix in _STONE_SUFFIXES:
                if exp >= thresh_exp:
                    mantissa = v / (10 ** thresh_exp)
                    return f"{mantissa:.2f}{suffix}"
            # Below 1K â€” show plain
            return f"{v:.2f}"
        else:
            # Engineering notation: mantissa Ã— 10^(multiple of 3)
            eng_exp  = (exp // 3) * 3
            mantissa = v / (10 ** eng_exp)
            return f"{mantissa:.2f}e{eng_exp}"
    except Exception:
        return str(s)

# â”€â”€ Status â†’ friendly header label â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
C_HEADER = "#7c6af7"

def _resolve_header(status: str) -> tuple:
    up = _plain_text(status).upper()
    if "FARMING"     == up: return "Farming",     C_HEADER
    if "NAVIGATING"  == up: return "Navigating",  C_HEADER
    if "UPGRADING"   == up: return "Upgrading",   C_HEADER
    if "REBIRTH"     == up: return "Rebirth",     C_HEADER
    if "ACTION"      == up: return "Working",     C_HEADER
    if "CHECKING"    == up: return "Checking",    C_HEADER
    if "RETRY"       == up: return "Retrying",    C_HEADER
    if "STONE LOST"  == up: return "Stone Lost",  C_HEADER
    if "MENU RESUME" == up: return "Resume",      C_HEADER
    if "RUNNING"     == up: return "Running",     C_HEADER
    if "DELVE"       == up: return "Delve",       C_HEADER
    if "KRAKEN"      == up: return "Kraken",      C_HEADER
    if "ZYTOS"       == up: return "Zytos",       C_HEADER
    if "CRATER"      == up: return "Crater",      C_HEADER
    if "RECORD"     == up: return "Recording",  C_HEADER
    if "PLAYING"    == up: return "Playing",    C_HEADER
    if "WAITING"     == up: return "Waiting",     C_HEADER
    if "STOPPED"     == up: return "Stopped",     C_HEADER
    # fallbacks
    if "FARM"    in up: return "Farming",     C_HEADER
    if "NAVIG"   in up: return "Navigating",  C_HEADER
    if "UPGRAD"  in up: return "Upgrading",   C_HEADER
    if "REBIRTH" in up: return "Rebirth",     C_HEADER
    if "ACTION"  in up: return "Working",     C_HEADER
    if "CHECK"   in up: return "Checking",    C_HEADER
    if "RETRY"   in up: return "Retrying",    C_HEADER
    if "MENU"    in up: return "Resume",      C_HEADER
    if "RESET"   in up: return "Resetting",   C_HEADER
    if "ERROR"   in up: return "Error",       C_HEADER
    if "WAIT"    in up: return "Waiting",     C_HEADER
    if "KILL"    in up: return "Stopped",     C_HEADER
    if "RUN"     in up: return "Running",     C_HEADER
    return _plain_text(status),               C_HEADER

# â”€â”€ Dashboard color palette â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
C_BG     = "#0e0e12"
C_BORDER = "#2a2a35"
C_GREEN  = "#44cc77"
C_RED    = "#cc4455"
C_YELLOW = "#f0c040"
C_TEXT   = "#e0e0e8"
C_MUTED  = "#7070a0"
C_TOPBAR = "#111118"
C_SUBBAR = "#181820"
C_SEPARATOR = "#2a2a35"
C_ESP_TRANSPARENT = "#010203"
C_ESP_BOX = "#37ff7a"
C_ESP_TEXT = "#eafff1"

# Crater ESP colors (ported from crater/overlay.py -- crater's rock/timer
# HUD is now rendered through this SAME overlay window/thread instead of
# a second independent Tk() instance, see set_crater_esp() below).
C_CRATER_CAPTURE   = "#37aaff"
C_CRATER_ROCK      = "#37ff7a"  # green (was gray)
C_CRATER_TARGET    = "#37ff7a"
C_CRATER_TIMER_OK  = "#37ff7a"
C_CRATER_TIMER_WARN = "#ffb020"
C_CRATER_TIMER_LOST = "#ff3737"

FONT_HDR   = ("Segoe UI", 9, "bold")
FONT_LABEL = ("Segoe UI",  8, "bold")
FONT_GOAL  = ("Segoe UI", 9)
FONT_STONE = ("Segoe UI", 9)

OVERLAY_BASE_W = 339
OVERLAY_BASE_H = 52
OVERLAY_BASE_SCREEN_W = 1920
OVERLAY_BASE_SCREEN_H = 1080
OVERLAY_MIN_SCALE = 0.85
OVERLAY_MAX_SCALE = 2.20

OVERLAY_W = OVERLAY_BASE_W
OVERLAY_H = OVERLAY_BASE_H
OVERLAY_X = 0
OVERLAY_DEFAULT_Y = 0
OVERLAY_MANUAL_Y = 0

# â”€â”€ Overlay window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class _Overlay:
    # Re-apply Win32 TOPMOST every N ticks.
    _TOPMOST_REAPPLY_INTERVAL = 300

    def __init__(self):
        global _overlay_instance
        get_logger().debug("[OVERLAY] _Overlay.__init__() â€” creating tkinter root window")
        self.root = tk.Tk()
        r = self.root
        self._ui_scale = self._detect_overlay_scale()
        self._overlay_w = self._s(OVERLAY_BASE_W)
        self._overlay_h = self._s(OVERLAY_BASE_H)
        self._font_hdr = ("Segoe UI", self._sf(9), "bold")
        self._font_label = ("Segoe UI", self._sf(8), "bold")
        self._font_goal = ("Segoe UI", self._sf(9))
        self._font_stone = ("Segoe UI", self._sf(9))
        self._font_esp = ("Segoe UI", self._sf(10), "bold")
        get_logger().debug(
            f"[OVERLAY] ui_scale={self._ui_scale:.3f} size={self._overlay_w}x{self._overlay_h}"
        )

        # Basic tkinter flags first
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 1.0)
        r.configure(bg=C_BORDER)
        r.geometry(f"{self._overlay_w}x{self._overlay_h}+{OVERLAY_X}+{OVERLAY_DEFAULT_Y}")
        r.withdraw()   # start hidden â€” shown only after auth (see _wait_for_auth_then_show)

        panel = tk.Frame(r, bg=C_BG, width=self._overlay_w - 2, height=self._overlay_h - 2, bd=0, highlightthickness=0)
        panel.pack(fill="both", expand=True, padx=1, pady=1)
        panel.pack_propagate(False)

        bar = tk.Frame(panel, bg=C_TOPBAR, width=self._overlay_w - 2, height=self._s(28))
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        self._hdr_var = tk.StringVar(value="Initialising")
        self._hdr_lbl = tk.Label(
            bar, textvariable=self._hdr_var,
            font=self._font_hdr, fg=C_HEADER, bg=C_TOPBAR,
            anchor="w", padx=self._s(8), pady=self._s(4), width=10,
        )
        self._hdr_lbl.pack(side="left", fill="y")

        tk.Frame(bar, bg=C_SEPARATOR, width=1, height=self._s(18)).pack(side="left", pady=self._s(5))

        self._goal_var = tk.StringVar(value="-")
        tk.Label(bar, textvariable=self._goal_var,
                 font=self._font_goal, fg=C_TEXT, bg=C_TOPBAR,
                 anchor="w", padx=self._s(8), width=20).pack(side="left")

        help_bar = tk.Frame(panel, bg=C_SUBBAR, width=self._overlay_w - 2, height=self._s(22))
        help_bar.pack(fill="x", side="top")
        help_bar.pack_propagate(False)
        self._timer_var = tk.StringVar(value="")
        tk.Label(help_bar, textvariable=self._timer_var,
                 font=self._font_label, fg=C_MUTED, bg=C_SUBBAR,
                 anchor="w", padx=self._s(8)).pack(side="left", fill="y")
        self._help_var = tk.StringVar(value="F9: Stop Bot")
        tk.Label(help_bar, textvariable=self._help_var,
                 font=self._font_label, fg=C_MUTED, bg=C_SUBBAR,
                 anchor="e", padx=self._s(8)).pack(side="right", fill="y")

        r.geometry(f"{self._overlay_w}x{self._overlay_h}+{OVERLAY_X}+{OVERLAY_DEFAULT_Y}")

        # Apply Win32 overlay magic AFTER window is drawn
        r.update_idletasks()
        r.update()
        _apply_win32_overlay_styles(r, alpha_byte=255)
        self._init_esp_window()

        self._tick_count = 0
        self._auth_shown = False
        _overlay_instance = self
        self._tick()

    def _screen_size(self) -> tuple[int, int]:
        try:
            sw = int(user32.GetSystemMetrics(0)) or OVERLAY_BASE_SCREEN_W
            sh = int(user32.GetSystemMetrics(1)) or OVERLAY_BASE_SCREEN_H
            return sw, sh
        except Exception:
            return OVERLAY_BASE_SCREEN_W, OVERLAY_BASE_SCREEN_H

    def _init_esp_window(self):
        sw, sh = self._screen_size()
        self._esp_root = tk.Toplevel(self.root)
        e = self._esp_root
        e.overrideredirect(True)
        e.attributes("-topmost", True)
        e.configure(bg=C_ESP_TRANSPARENT)
        try:
            e.attributes("-transparentcolor", C_ESP_TRANSPARENT)
        except Exception:
            pass
        e.geometry(f"{sw}x{sh}+0+0")
        e.withdraw()
        self._esp_canvas = tk.Canvas(
            e,
            width=sw,
            height=sh,
            bg=C_ESP_TRANSPARENT,
            highlightthickness=0,
            bd=0,
        )
        self._esp_canvas.pack(fill="both", expand=True)
        e.update_idletasks()
        _apply_win32_overlay_styles(e, alpha_byte=255, click_through=True, transparent_color=C_ESP_TRANSPARENT)

    def _hide_esp(self):
        try:
            self._esp_canvas.delete("all")
            self._esp_root.withdraw()
        except Exception:
            pass

    def _update_esp(self, s: dict):
        self._hide_esp()

    def _update_crater_esp(self, s: dict):
        """Render crater's rock-detection/timer ESP on the SAME esp canvas
        used by delve/kraken -- crater used to run its own separate Tk()
        instance on a background thread for this (crater/overlay.py's old
        _CraterESP), which is not safe: Tcl's event loop is not meant to
        host two Tk() roots on two different threads in one process, and
        the create/destroy cycle on every force-restart would eventually
        wedge the MAIN overlay's `self.root.after()` scheduling -- the
        header/goal text (and this ESP) would then freeze forever, even
        though the bot kept running fine underneath."""
        try:
            cap = s.get("crater_capture_rect")
            rock_boxes = list(s.get("crater_rock_boxes") or [])
            target = s.get("crater_target_box")
            timer_box = s.get("crater_timer_box")
            if not cap and not rock_boxes and not target and not timer_box:
                self._hide_esp()
                return

            sw, sh = self._screen_size()
            self._esp_root.geometry(f"{sw}x{sh}+0+0")
            self._esp_canvas.config(width=sw, height=sh)
            self._esp_canvas.delete("all")
            if cap:
                x1, y1, x2, y2 = cap
                self._esp_canvas.create_rectangle(x1, y1, x2, y2, outline=C_CRATER_CAPTURE, width=2)
            rock_ids = list(s.get("crater_rock_ids") or [])
            for idx, box in enumerate(rock_boxes):
                bx1, by1, bx2, by2 = box
                self._esp_canvas.create_rectangle(bx1, by1, bx2, by2, outline=C_CRATER_ROCK, width=1)
                # Draw ID label above the box if available
                rid = rock_ids[idx] if idx < len(rock_ids) else idx
                self._esp_canvas.create_text((bx1 + bx2) // 2, by1 - 8,
                                             text=f"#{rid}", fill=C_CRATER_ROCK,
                                             font=("Segoe UI", 7, "bold"))
            if target:
                tx1, ty1, tx2, ty2 = target
                self._esp_canvas.create_rectangle(tx1, ty1, tx2, ty2, outline=C_CRATER_TARGET, width=3)
            if timer_box:
                ttx1, tty1, ttx2, tty2 = timer_box
                tstate = s.get("crater_timer_state", "ok")
                tcolor = {"ok": C_CRATER_TIMER_OK, "warn": C_CRATER_TIMER_WARN,
                         "lost": C_CRATER_TIMER_LOST}.get(tstate, C_CRATER_TIMER_OK)
                self._esp_canvas.create_rectangle(ttx1, tty1, ttx2, tty2, outline=tcolor, width=2)
                self._esp_canvas.create_text((ttx1 + ttx2) // 2, tty1 - 10, text="CRATER TIMER",
                                             fill=tcolor, font=("Segoe UI", 8, "bold"))


            self._esp_root.deiconify()
        except Exception:
            self._hide_esp()

    def _detect_overlay_scale(self) -> float:
        try:
            sw = int(user32.GetSystemMetrics(0)) or OVERLAY_BASE_SCREEN_W
            sh = int(user32.GetSystemMetrics(1)) or OVERLAY_BASE_SCREEN_H
            sx = float(sw) / float(OVERLAY_BASE_SCREEN_W)
            sy = float(sh) / float(OVERLAY_BASE_SCREEN_H)
            s = min(sx, sy)
            if s < OVERLAY_MIN_SCALE:
                return OVERLAY_MIN_SCALE
            if s > OVERLAY_MAX_SCALE:
                return OVERLAY_MAX_SCALE
            return s
        except Exception:
            return 1.0

    def _s(self, px: int) -> int:
        return max(1, int(round(float(px) * self._ui_scale)))

    def _sf(self, pt: int) -> int:
        return max(7, int(round(float(pt) * self._ui_scale)))

    def _tick(self):
        # Global kill switch: overlays fully disabled -> hide everything and
        # idle. No window is shown, no focus games. Read LIVE from config.
        if _overlays_disabled():
            self._hide_esp()
            self.root.withdraw()
            self.root.after(250, self._tick)
            return

        with _lock:
            s = dict(_state)

        # Only show while the bot is actually running, or Recorder is
        # recording / playing. Idle WAITING stays hidden.
        _hide = ("WAITING", "UNFOCUSED", "INIT", "KILLED", "STOPPED", "RESETTING")
        if time.time() < _capture_hide_until:
            self._hide_esp()
            self.root.withdraw()
            self.root.after(100, self._tick)
            return

        recorder_active = bool(s.get("recorder_active"))
        if (not recorder_active) and s["status"] in _hide:
            self._hide_esp()
            self.root.withdraw()
            self.root.after(500, self._tick)
            return

        if recorder_active:
            self._timer_var.set("")
            self._help_var.set(s.get("recorder_hint") or "")
            self._hdr_var.set(s.get("recorder_header") or "Recorder")
            rec_color = "#ff7a90" if "RECORD" in str(s.get("recorder_header") or "").upper() else C_GREEN
            if str(s.get("recorder_header") or "").upper() == "READY":
                rec_color = C_YELLOW
            self._hdr_lbl.config(fg=rec_color)
            self._goal_var.set(s.get("recorder_goal") or "")
            self._hide_esp()
        else:
            rst = s.get("run_start_time")
            if rst:
                elapsed = int(time.time() - rst)
                m, sec = divmod(elapsed, 60)
                self._timer_var.set(f"{m}m{sec:02d}s")
            else:
                self._timer_var.set("")
            try:
                import config as _cfg
                stop_bind = str(getattr(_cfg, "BOT_STOP_BINDING", "F9") or "F9")
            except Exception:
                stop_bind = "F9"
            self._help_var.set(f"{stop_bind}: Stop Bot")
            hdr_text, hdr_color = _resolve_header(s["status"])
            self._hdr_var.set(hdr_text)
            self._hdr_lbl.config(fg=hdr_color)
            self._goal_var.set(_resolve_goal(s["status"], s["goal"]))
            if s.get("crater_esp_active"):
                self._update_crater_esp(s)
            else:
                self._hide_esp()

        self.root.deiconify()
        self.root.geometry(f"{self._overlay_w}x{self._overlay_h}+{OVERLAY_X}+{OVERLAY_DEFAULT_Y}")

        self._tick_count += 1
        if self._tick_count % self._TOPMOST_REAPPLY_INTERVAL == 0:
            _reapply_topmost(self.root)
            _reapply_topmost(self._esp_root, show_window=False)

        self.root.after(16, self._tick)

    def run(self):
        get_logger().debug("[OVERLAY] root.mainloop() starting")
        self.root.mainloop()
        get_logger().debug("[OVERLAY] root.mainloop() returned")


# â”€â”€ Public â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_overlay_thread: Optional[threading.Thread] = None
_overlay_ready = threading.Event()


def _overlays_disabled() -> bool:
    """Global kill switch - read LIVE from config so the dashboard toggle
    takes effect immediately (and applies to an already-running overlay)."""
    try:
        import config as _cfg
        return bool(getattr(_cfg, "DISABLE_OVERLAYS", False))
    except Exception:
        return False


def run_overlay_mainloop():
    """Run the tkinter overlay on the CALLING thread (must be main thread on Windows).
    Blocks until the overlay window is destroyed."""
    import threading as _th
    _log = get_logger()
    _log.debug(f"[OVERLAY] run_overlay_mainloop() entered on thread={_th.current_thread().name} "
               f"id={_th.current_thread().ident}")
    if _overlays_disabled():
        _log.info("[OVERLAY] DISABLE_OVERLAYS is enabled - overlay windows stay fully hidden.")
    try:
        _log.debug("[OVERLAY] Creating _Overlay instance...")
        ov = _Overlay()
        _log.debug("[OVERLAY] _Overlay created â€” signalling ready")
        _overlay_ready.set()
        _log.debug("[OVERLAY] Entering tkinter mainloop")
        ov.run()
        _log.debug("[OVERLAY] tkinter mainloop exited cleanly")
    except Exception as _e:
        _log.error(f"[OVERLAY] run_overlay_mainloop() error: {_e}")
        _overlay_ready.set()

def start_overlay():
    """Legacy shim â€” main thread calls run_overlay_mainloop() directly."""
    pass


# â”€â”€ Logger import (deferred to avoid circular imports) â”€â”€â”€â”€â”€â”€â”€â”€
def get_logger():
    from logger import get_logger as _gl
    return _gl()
