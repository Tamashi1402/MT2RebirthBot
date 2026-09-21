# ============================================================
# MT2 BOT - CONFIG LOADER  (v16 â€” JSON-backed, no Python in output)
# All user settings live in data/config.json next to the EXE.
# This module loads that file and exposes the same names as
# before so every other module keeps working unchanged.
# ============================================================
import os
import sys
import json
import re
from datetime import datetime

def _enable_dpi_awareness():
    """Best-effort enable per-monitor DPI awareness (Windows)."""
    if os.name != "nt":
        return
    try:
        import ctypes
        try:
            user32 = ctypes.windll.user32
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return
        except Exception:
            pass
        try:
            shcore = ctypes.windll.shcore
            # PROCESS_PER_MONITOR_DPI_AWARE = 2
            shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    except Exception:
        pass

_enable_dpi_awareness()

# â”€â”€ Locate config/data paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _has_config(folder: str) -> bool:
    return os.path.isfile(os.path.join(folder, "data", "config.json")) or os.path.isfile(
        os.path.join(folder, "config.json")
    )


def _resolve_bot_dir(start: str) -> str:
    """Find the folder that actually contains data/config.json.

    Walks up from code/ or a mistaken logs/code copy so launching from
    logs\\code\\bot.py still uses the real bot folder.
    """
    cur = os.path.abspath(start)
    for _ in range(8):
        name = os.path.basename(cur).lower()
        candidates = []
        if name in ("code", "logs"):
            candidates.append(os.path.dirname(cur))
        candidates.append(cur)
        for c in candidates:
            if c and _has_config(c):
                return c
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    if os.path.basename(os.path.abspath(start)).lower() == "code":
        return os.path.dirname(os.path.abspath(start))
    return os.path.abspath(start)


if getattr(sys, "frozen", False):
    CODE_DIR = os.path.dirname(sys.executable)
    BOT_DIR = _resolve_bot_dir(CODE_DIR)
else:
    CODE_DIR = os.path.dirname(os.path.abspath(__file__))
    BOT_DIR = _resolve_bot_dir(CODE_DIR)

DATA_DIR = os.path.join(BOT_DIR, "data")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

_LEGACY_CONFIG_FILE = os.path.join(BOT_DIR, "config.json")
_CODE_CONFIG_FILE = os.path.join(CODE_DIR, "config.json")
_CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
_BUNDLED_DATA_DIR = os.path.join(getattr(sys, "_MEIPASS", BOT_DIR), "data")
_BUNDLED_CONFIG_FILE = os.path.join(_BUNDLED_DATA_DIR, "config.json")

def _migrate_legacy_json_file(name: str):
    """Move legacy root-level JSON file into /data if needed."""
    src = os.path.join(BOT_DIR, name)
    dst = os.path.join(DATA_DIR, name)
    if os.path.abspath(src) == os.path.abspath(dst):
        return
    if not os.path.exists(src) or os.path.exists(dst):
        return
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass
    try:
        os.replace(src, dst)
    except Exception:
        try:
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                fdst.write(fsrc.read())
        except Exception:
            return
        try:
            os.remove(src)
        except Exception:
            pass

# One-time migration for main config file.
if not os.path.exists(_CONFIG_FILE) and os.path.exists(_LEGACY_CONFIG_FILE):
    _migrate_legacy_json_file("config.json")
if not os.path.exists(_CONFIG_FILE) and os.path.exists(_CODE_CONFIG_FILE):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass
    try:
        os.replace(_CODE_CONFIG_FILE, _CONFIG_FILE)
    except Exception:
        try:
            with open(_CODE_CONFIG_FILE, "rb") as _src, open(_CONFIG_FILE, "wb") as _dst:
                _dst.write(_src.read())
        except Exception:
            pass
if not os.path.exists(_CONFIG_FILE) and os.path.exists(_BUNDLED_CONFIG_FILE):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(_BUNDLED_CONFIG_FILE, "rb") as _src, open(_CONFIG_FILE, "wb") as _dst:
            _dst.write(_src.read())
    except Exception:
        pass

def _load() -> dict:
    try:
        # Use utf-8-sig so config still loads if a BOM is present.
        with open(_CONFIG_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"config.json not found at {_CONFIG_FILE}\n"
            "Make sure data/config.json exists next to MT2RebirthBot.exe"
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"config.json is invalid JSON: {e}")

_cfg = _load()

def _cfg_bool(key: str, default: bool) -> bool:
    """Bool config value that also parses 'true'/'false'/'0'/'1' strings
    (older UI versions saved booleans as typed text)."""
    v = _cfg.get(key, default)
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")



BOT_MODE = str(_cfg.get("BOT_MODE", "rebirth")).strip().lower()
if BOT_MODE not in {"rebirth", "delve", "kraken", "zytos", "crater"}:
    BOT_MODE = "rebirth"

def _t(key, cast, default):
    v = _cfg.get(key, default)
    try:
        return cast(v)
    except Exception:
        return default


def _detect_runtime_resolution() -> tuple[int, int]:
    """Best-effort current screen resolution used for runtime region scaling."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        w = int(user32.GetSystemMetrics(0))
        h = int(user32.GetSystemMetrics(1))
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return 1920, 1080


_SCALED_REGION_KEYS = [
    "STONE_ICON_REGION", "STONE_REGION", "STRENGTH_REGION", "AUTO_STR_REGION",
    "MAIN_MENU_REGION", "ROCK_HEALTH_BAR_REGION",
    "TELEPORT_BUTTON_REGION", "TELEPORT_BASE_REGION", "TELEPORT_AREA1_REGION", "TELEPORT_AREA2_REGION",
    "TELEPORT_AREA3_REGION", "TELEPORT_AREA4_REGION", "TELEPORT_AREA5_REGION", "TELEPORT_AREA7_REGION",
    "MENU_PLAY_REGION", "MENU_PRIVACY_REGION",
    "MANUAL_STR_ROW1_LEFT", "MANUAL_STR_ROW1_RIGHT",
    "MANUAL_STR_ROW2_LEFT", "MANUAL_STR_ROW2_RIGHT",
    "MANUAL_STR_ROW3_LEFT", "MANUAL_STR_ROW3_RIGHT",
    "MANUAL_STR_ROW4_LEFT", "MANUAL_STR_ROW4_RIGHT",
    "MANUAL_STR_ROW5_LEFT", "MANUAL_STR_ROW5_RIGHT",
    "MANUAL_STR_CLOSE_REGION", "MANUAL_STR_STONE_REGION", "MANUAL_STR_STRENGTH_REGION",
    "MANUAL_STR_SURGE_REGION",
    "DELVE_CLOSE_REGION", "DELVE_JOIN_REGION",
    "KRAKEN_CLOSE_REGION", "KRAKEN_JOIN_REGION", "KRAKEN_HEALTH_BAR_REGION",
    "ZYTOS_CLOSE_REGION", "ZYTOS_JOIN_REGION", "ZYTOS_HEALTH_BAR_REGION",
    "TELEPORT_AREA8_REGION",
    "CRATER_TIMER_REGION",
    "CRATER_PET_DROP_REGION",
    "BRAMBLE_MODE_REGION",
    "TELEPORT_AREA6_REGION",
    "DRILL_ACTIVE_REGION",
    "A6_STARDUST_REGION",
    "A6_STAR_LEVEL_REGION",
    "MAP_BLACK_REGION",
    "QUEST_PANEL1_TEXT_REGION", "QUEST_PANEL2_TEXT_REGION", "QUEST_PANEL3_TEXT_REGION",
    "QUEST_HUD1_DONE_REGION", "QUEST_HUD2_DONE_REGION", "QUEST_HUD3_DONE_REGION",
    "HATCH_AREA1_TEXT_REGION",
    # Force Restart flow v2 (OCR regions, 1920x1080 base)
    "FORCE_PLAY_OCR_REGION", "FORCE_GAME_TITLE_REGION",
    "FORCE_SEARCH_DISCOVER_REGION", "FORCE_SELECT_OCR_REGION",
]
_SCALED_POINT_KEYS = [
    "MANUAL_STR_CLOSE_CENTER", "DELVE_JOIN_CENTER", "KRAKEN_JOIN_CENTER",
    "ZYTOS_JOIN_CENTER", "BRAMBLE_MODE_SWAP_CENTER",
    "A6_SKILLHUT_MAX_CLICK", "A6_SKILLHUT_CLOSE_CLICK",
    "A6_AUTOSTR_CLOSE_CHECK", "A6_AUTOSTR_STATE_CHECK",
    "A6_AUTOSTR_TOGGLE_CLICK", "A6_AUTOSTR_CLOSE_CLICK", "A6_AUTOSTR_AUTO_CLICK",
    "TELEPORT_PANEL_CLICK", "TELEPORT_CLOSE_SAMPLE", "TELEPORT_CLOSE_CLICK",
    "TELEPORT_DEST_AREA1", "TELEPORT_DEST_AREA2", "TELEPORT_DEST_AREA3",
    "TELEPORT_DEST_AREA4", "TELEPORT_DEST_AREA5", "TELEPORT_DEST_AREA6",
    "TELEPORT_DEST_AREA7", "TELEPORT_DEST_AREA8", "TELEPORT_DEST_COSMIC",
    "TELEPORT_DEST_BASE",
    "TELEPORT_SAMPLE_AREA1", "TELEPORT_SAMPLE_AREA2", "TELEPORT_SAMPLE_AREA3",
    "TELEPORT_SAMPLE_AREA4", "TELEPORT_SAMPLE_AREA5", "TELEPORT_SAMPLE_AREA6",
    "TELEPORT_SAMPLE_COSMIC", "TELEPORT_SAMPLE_BASE",
    "REBIRTH_CLOSE_SAMPLE", "REBIRTH_CLOSE_CLICK",
    "REBIRTH_BTN1_CLICK", "REBIRTH_BTN2_SAMPLE", "REBIRTH_BTN2_CLICK",
    "LOADOUT_PANEL_CLICK", "LOADOUT_PANEL_SAMPLE",
    "LOADOUT_CLOSE_CLICK", "LOADOUT_CLOSE_SAMPLE",
    "LOADOUT_SLOT_1", "LOADOUT_SLOT_2", "LOADOUT_SLOT_3",
    "LOADOUT_SLOT_4", "LOADOUT_SLOT_5", "LOADOUT_SLOT_6",
    "LOADOUT_SAMPLE_1", "LOADOUT_SAMPLE_2", "LOADOUT_SAMPLE_3",
    "LOADOUT_SAMPLE_4", "LOADOUT_SAMPLE_5", "LOADOUT_SAMPLE_6",
    "FORCE_ESC_SAMPLE", "FORCE_MENU_CLICK",
    "FORCE_EXIT_SAMPLE", "FORCE_LOBBY_CLICK",
    "FORCE_READY_SAMPLE", "FORCE_READY_CLICK",
    "FORCE_SEARCH_CLICK", "FORCE_GAME_BILLBOARD_CLICK", "FORCE_SELECT_CLICK",
    "FORCE_SHARD_SAMPLE",
    "QUEST_PANEL1_BTN", "QUEST_PANEL2_BTN", "QUEST_PANEL3_BTN",
    "QUEST_CLOSE_CLICK", "QUEST_CLOSE_SAMPLE",
    "HATCH_CLOSE_SAMPLE", "HATCH_CLOSE_CLICK", "HATCH_NEXT_CLICK", "HATCH_ALL_CLICK",
    "COMBINE_PETS_CLICK",
    "COMBINE_ZAPPY_CLICK", "COMBINE_ZAPPY_CLOSE_CLICK", "COMBINE_ZAPPY_CLOSE_SAMPLE",
    "COMBINE_AUTOCOMBINE_CLICK", "COMBINE_AUTOCOMBINE_CLOSE_CLICK", "COMBINE_AUTOCOMBINE_CLOSE_SAMPLE",
    "COMBINE_AUTOCOMBINE_CONFIRM_CLICK",
]

# Frozen 1920x1080 authoring-frame defaults. Runtime scaling ALWAYS starts
# from these (or from a user calibration that still sits inside this frame).
# Never scale from previously-scaled config values — that is what broke
# OCR after a wrong-ratio scale in 1.7.
DEFAULT_REGIONS = {
    "FORCE_PLAY_OCR_REGION": (100, 887, 417, 942),
    "FORCE_GAME_TITLE_REGION": (83, 665, 438, 704),
    "FORCE_SEARCH_DISCOVER_REGION": (147, 145, 883, 201),
    "FORCE_SELECT_OCR_REGION": (89, 898, 392, 935),
    "STONE_ICON_REGION": (1629, 657, 1704, 727),
    "STONE_REGION": (1700, 659, 1919, 721),
    "STRENGTH_REGION": (1698, 602, 1919, 655),
    "AUTO_STR_REGION": (76, 1023, 126, 1073),
    "MAIN_MENU_REGION": (660, 760, 1260, 900),
    "ROCK_HEALTH_BAR_REGION": (610, 55, 1328, 122),
    "TELEPORT_BUTTON_REGION": (827, 807, 1171, 868),
    "TELEPORT_BASE_REGION": (790, 843, 1130, 902),
    "TELEPORT_AREA1_REGION": (790, 138, 1130, 198),
    "TELEPORT_AREA2_REGION": (790, 226, 1130, 286),
    "TELEPORT_AREA3_REGION": (790, 314, 1130, 374),
    "TELEPORT_AREA4_REGION": (790, 403, 1130, 463),
    "TELEPORT_AREA5_REGION": (790, 491, 1130, 551),
    "TELEPORT_AREA6_REGION": (790, 579, 1130, 639),
    "TELEPORT_AREA7_REGION": (790, 755, 1130, 815),
    "TELEPORT_AREA8_REGION": (790, 843, 1130, 902),
    "MENU_PLAY_REGION": (660, 840, 820, 900),
    "MENU_PRIVACY_REGION": (660, 770, 820, 840),
    "MANUAL_STR_ROW1_LEFT": (1137, 269, 1466, 339),
    "MANUAL_STR_ROW1_RIGHT": (1495, 266, 1828, 341),
    "MANUAL_STR_ROW2_LEFT": (1137, 426, 1466, 496),
    "MANUAL_STR_ROW2_RIGHT": (1495, 426, 1828, 496),
    "MANUAL_STR_ROW3_LEFT": (1137, 583, 1466, 653),
    "MANUAL_STR_ROW3_RIGHT": (1495, 583, 1828, 653),
    "MANUAL_STR_ROW4_LEFT": (1137, 740, 1466, 810),
    "MANUAL_STR_ROW4_RIGHT": (1495, 740, 1828, 810),
    "MANUAL_STR_ROW5_LEFT": (1137, 897, 1466, 967),
    "MANUAL_STR_ROW5_RIGHT": (1495, 897, 1828, 967),
    "MANUAL_STR_CLOSE_REGION": (1605, 66, 1881, 137),
    "MANUAL_STR_STONE_REGION": (145, 72, 370, 139),
    "MANUAL_STR_STRENGTH_REGION": (475, 72, 682, 139),
    "MANUAL_STR_SURGE_REGION": (207, 912, 308, 971),
    "DELVE_CLOSE_REGION": (900, 895, 1220, 955),
    "DELVE_JOIN_REGION": (1070, 795, 1415, 865),
    "KRAKEN_CLOSE_REGION": (900, 895, 1220, 955),
    "KRAKEN_JOIN_REGION": (1070, 795, 1415, 865),
    "KRAKEN_HEALTH_BAR_REGION": (610, 55, 1328, 122),
    "ZYTOS_CLOSE_REGION": (900, 895, 1220, 955),
    "ZYTOS_JOIN_REGION": (1070, 795, 1415, 865),
    "ZYTOS_HEALTH_BAR_REGION": (605, 48, 657, 121),
    "CRATER_TIMER_REGION": (890, 170, 1025, 215),
    "CRATER_PET_DROP_REGION": (760, 200, 1160, 400),
    # Subtitle under the Bramble name on the left INFO card (Easy/Normal/Hard/Ex).
    # User-measured 1920x1080 via MT2 Picker: (182, 270, 701, 331).
    "BRAMBLE_MODE_REGION": (182, 270, 701, 331),
    # Bottom-left cyan drill timer ("00:24"). Tight Y, extra X slack.
    # User-measured 1920x1080: (28, 697, 124, 728).
    "DRILL_ACTIVE_REGION": (28, 697, 124, 728),
    "A6_STARDUST_REGION": (1716, 532, 1919, 583),
    "A6_STAR_LEVEL_REGION": (54, 212, 222, 283),
    # World view after rebirth (skip HUD). Black-screen fade detect.
    "MAP_BLACK_REGION": (360, 90, 1560, 960),
    # Daily Quests panel text crops (user-measured 1920x1080, wide X for localization).
    "QUEST_PANEL1_TEXT_REGION": (105, 485, 619, 544),
    "QUEST_PANEL2_TEXT_REGION": (705, 484, 1219, 545),
    "QUEST_PANEL3_TEXT_REGION": (1307, 482, 1817, 548),
    # HUD quest tracker slots — green "Done" text (#00f500).
    "QUEST_HUD1_DONE_REGION": (0, 409, 90, 464),
    "QUEST_HUD2_DONE_REGION": (0, 488, 90, 544),
    "QUEST_HUD3_DONE_REGION": (0, 567, 90, 625),
    # Top-right mineral "+gain" popup.
    # Hatch GUI (base NPC) page-title strip — OCR searches "Area 1 Egg" here.
    "HATCH_AREA1_TEXT_REGION": (525, 375, 1201, 434),
}
DEFAULT_POINTS = {
    "FORCE_SEARCH_CLICK": (243, 172),
    "FORCE_GAME_BILLBOARD_CLICK": (225, 493),
    "FORCE_SELECT_CLICK": (238, 915),
    "MANUAL_STR_CLOSE_CENTER": (1742, 101),
    "DELVE_JOIN_CENTER": (1242, 830),
    "KRAKEN_JOIN_CENTER": (1242, 830),
    "ZYTOS_JOIN_CENTER": (1337, 826),
    # Middle of the HARD pill at the bottom of the left INFO card.
    # User-measured 1920x1080 via MT2 Picker: (439, 826).
    # Click the pill, do not OCR it. Cycles Easy/Normal/Hard/Ex.
    "BRAMBLE_MODE_SWAP_CENTER": (439, 826),
    "A6_SKILLHUT_MAX_CLICK": (1039, 861),
    "A6_SKILLHUT_CLOSE_CLICK": (662, 950),
    "A6_AUTOSTR_CLOSE_CHECK": (1729, 123),
    "A6_AUTOSTR_STATE_CHECK": (1154, 120),
    "A6_AUTOSTR_TOGGLE_CLICK": (1235, 100),
    "A6_AUTOSTR_CLOSE_CLICK": (1741, 95),
    "A6_AUTOSTR_AUTO_CLICK": (1480, 100),
    "TELEPORT_PANEL_CLICK": (997, 836),
    "TELEPORT_CLOSE_SAMPLE": (1001, 957),
    "TELEPORT_CLOSE_CLICK": (1001, 939),
    "TELEPORT_DEST_AREA1": (954, 113),
    "TELEPORT_DEST_AREA2": (954, 200),
    "TELEPORT_DEST_AREA3": (953, 292),
    "TELEPORT_DEST_AREA4": (951, 378),
    "TELEPORT_DEST_AREA5": (954, 468),
    "TELEPORT_DEST_AREA6": (960, 559),
    "TELEPORT_DEST_AREA7": (953, 646),
    "TELEPORT_DEST_AREA8": (953, 734),
    "TELEPORT_DEST_COSMIC": (957, 822),
    "TELEPORT_DEST_BASE": (952, 915),
    "TELEPORT_SAMPLE_AREA1": (823, 136),
    "TELEPORT_SAMPLE_AREA2": (820, 184),
    "TELEPORT_SAMPLE_AREA3": (810, 278),
    "TELEPORT_SAMPLE_AREA4": (813, 363),
    "TELEPORT_SAMPLE_AREA5": (815, 452),
    "TELEPORT_SAMPLE_AREA6": (806, 542),
    "TELEPORT_SAMPLE_COSMIC": (810, 804),
    "TELEPORT_SAMPLE_BASE": (811, 889),
    "REBIRTH_CLOSE_SAMPLE": (381, 960),
    "REBIRTH_CLOSE_CLICK": (381, 940),
    "REBIRTH_BTN1_CLICK": (955, 938),
    "REBIRTH_BTN2_SAMPLE": (1366, 966),
    "REBIRTH_BTN2_CLICK": (1548, 940),
    "LOADOUT_PANEL_CLICK": (1001, 659),
    "LOADOUT_PANEL_SAMPLE": (853, 679),
    "LOADOUT_CLOSE_CLICK": (958, 1028),
    "LOADOUT_CLOSE_SAMPLE": (959, 1054),
    "LOADOUT_SLOT_1": (359, 465),
    "LOADOUT_SLOT_2": (952, 460),
    "LOADOUT_SLOT_3": (1561, 465),
    "LOADOUT_SLOT_4": (360, 967),
    "LOADOUT_SLOT_5": (958, 963),
    "LOADOUT_SLOT_6": (1554, 966),
    "LOADOUT_SAMPLE_1": (278, 446),
    "LOADOUT_SAMPLE_2": (891, 446),
    "LOADOUT_SAMPLE_3": (1499, 446),
    "LOADOUT_SAMPLE_4": (290, 946),
    "LOADOUT_SAMPLE_5": (901, 946),
    "LOADOUT_SAMPLE_6": (1501, 945),
    "FORCE_ESC_SAMPLE": (1622, 149),
    "FORCE_MENU_CLICK": (1677, 66),
    "FORCE_EXIT_SAMPLE": (1800, 779),
    "FORCE_LOBBY_CLICK": (1567, 170),
    "FORCE_READY_SAMPLE": (252, 940),
    "FORCE_READY_CLICK": (255, 910),
    "FORCE_SHARD_SAMPLE": (1668, 773),
    # Daily Quests start/complete buttons + close click/sample (user-measured 1920x1080).
    "QUEST_PANEL1_BTN": (355, 762),
    "QUEST_PANEL2_BTN": (949, 763),
    "QUEST_PANEL3_BTN": (1570, 760),
    "QUEST_CLOSE_CLICK": (969, 846),
    "QUEST_CLOSE_SAMPLE": (1073, 861),
    # Hatch Pets GUI (base NPC) — user-measured 1920x1080.
    "HATCH_CLOSE_SAMPLE": (1569, 918),   # yellow close detection
    "HATCH_CLOSE_CLICK": (1567, 897),    # close click
    "HATCH_NEXT_CLICK": (1070, 918),     # page "Next"
    "HATCH_ALL_CLICK": (1042, 839),      # "Hatch All"
    # Combine Pets (F4 monitor menu) — user-measured 1920x1080.
    "COMBINE_PETS_CLICK": (991, 486),
    "COMBINE_ZAPPY_CLICK": (253, 346),
    "COMBINE_ZAPPY_CLOSE_CLICK": (965, 1031),
    "COMBINE_ZAPPY_CLOSE_SAMPLE": (965, 1010),
    "COMBINE_AUTOCOMBINE_CLICK": (357, 1029),
    "COMBINE_AUTOCOMBINE_CLOSE_CLICK": (359, 941),
    "COMBINE_AUTOCOMBINE_CLOSE_SAMPLE": (362, 923),
    "COMBINE_AUTOCOMBINE_CONFIRM_CLICK": (344, 1020),  # confirm AUTO COMBINE on the opened panel
}
_OLD_ROCK_HEALTH_BAR_REGION = (610, 57, 830, 113)
# Stale Bramble OCR boxes. Frozen default is the picker-measured INFO-card crop.
_OLD_BRAMBLE_MODE_REGIONS = (
    (500, 480, 850, 620),  # guessed Queued Players panel
    (150, 180, 640, 226),  # first measured guess (too high)
)
# Stale HARD-pill click points.
_OLD_BRAMBLE_MODE_SWAP_CENTERS = (
    (890, 550),  # guessed center-card chevron
    (460, 705),  # first HARD-text guess (too high)
)

_BASE_REGIONS: dict = {}
_BASE_POINTS: dict = {}


def _is_base_frame_region(vals, bw: int = 1920, bh: int = 1080) -> bool:
    if not isinstance(vals, (list, tuple)) or len(vals) != 4:
        return False
    try:
        x1, y1, x2, y2 = (int(v) for v in vals)
    except Exception:
        return False
    return 0 <= x1 < x2 <= bw and 0 <= y1 < y2 <= bh


def _is_base_frame_point(vals, bw: int = 1920, bh: int = 1080) -> bool:
    if not isinstance(vals, (list, tuple)) or len(vals) != 2:
        return False
    try:
        x, y = int(vals[0]), int(vals[1])
    except Exception:
        return False
    return 0 <= x < bw and 0 <= y < bh


def _persist_cfg_patch(patch: dict) -> None:
    if not patch:
        return
    try:
        _cfg.update(patch)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_cfg, f, indent=2)
    except Exception:
        pass


def _repair_scaled_config_coords() -> None:
    """Drop leftover runtime-scaled coords from config.json.

    1.7 wrote already-scaled OCR boxes back into config and then treated
    them as 1920x1080 base. After a resolution change those boxes never
    recovered. Any region that does not sit inside the authoring frame is
    replaced with the frozen default. This runs every launch.
    """
    patch = {}
    for key, default in DEFAULT_REGIONS.items():
        vals = _cfg.get(key)
        if vals is None:
            continue
        tup = None
        try:
            if isinstance(vals, (list, tuple)) and len(vals) == 4:
                tup = tuple(int(v) for v in vals)
        except Exception:
            tup = None
        if key == "ROCK_HEALTH_BAR_REGION" and tup == _OLD_ROCK_HEALTH_BAR_REGION:
            patch[key] = list(default)
            continue
        if key == "BRAMBLE_MODE_REGION" and tup in _OLD_BRAMBLE_MODE_REGIONS:
            patch[key] = list(default)
            continue
        if tup is None or not _is_base_frame_region(tup):
            patch[key] = list(default)
    for key, default in DEFAULT_POINTS.items():
        vals = _cfg.get(key)
        if vals is None:
            continue
        tup = None
        try:
            if isinstance(vals, (list, tuple)) and len(vals) == 2:
                tup = tuple(int(v) for v in vals)
        except Exception:
            tup = None
        if tup is None or not _is_base_frame_point(tup):
            patch[key] = list(default)
            continue
        if key == "BRAMBLE_MODE_SWAP_CENTER" and tup in _OLD_BRAMBLE_MODE_SWAP_CENTERS:
            patch[key] = list(default)
    patch["REGION_COORDS_ARE_BASE"] = True
    _persist_cfg_patch(patch)


_repair_scaled_config_coords()


# Paths
def _resolve_macros_dir() -> str:
    return os.path.join(BOT_DIR, "macros")


MACROS_DIR = _resolve_macros_dir()
MODULES_DIR = os.path.join(BOT_DIR, "modules")
try:
    os.makedirs(MODULES_DIR, exist_ok=True)
except Exception:
    pass
LOGS_DIR = os.path.join(BOT_DIR, "logs")
_LOGS_DATE = datetime.now().strftime("%Y-%m-%d")
LOGS_FILE = os.path.join(LOGS_DIR, f"logs-{_LOGS_DATE}.txt")
# Backwards-compatible alias; logger now writes a single daily file only.
LOGS_DEV_FILE = LOGS_FILE
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
MIGRATED_FILES = {
    "config": _CONFIG_FILE,
    "stats": STATS_FILE,
}

_migrate_legacy_json_file("stats.json")
_migrate_legacy_json_file("dashboard_state.json")
_migrate_legacy_json_file("delve_stats.json")
_migrate_legacy_json_file("kraken_stats.json")
_migrate_legacy_json_file("zytos_stats.json")
_migrate_legacy_json_file("macro_engine_state.json")

# â”€â”€ Debug â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SAVE_DEBUG_CROPS = _cfg_bool("SAVE_DEBUG_CROPS", False)
DISABLE_OVERLAYS = _cfg_bool("DISABLE_OVERLAYS", False)  # True: overlay windows never shown

# â”€â”€ HUD regions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STONE_ICON_REGION  = tuple(int(x) for x in _cfg.get("STONE_ICON_REGION",  [1629, 657,  1704, 727]))
STONE_REGION       = tuple(int(x) for x in _cfg.get("STONE_REGION",       [1700, 659,  1919, 721]))
STRENGTH_REGION    = tuple(int(x) for x in _cfg.get("STRENGTH_REGION",    [1698, 602,  1919, 655]))
AUTO_STR_REGION    = tuple(int(x) for x in _cfg.get("AUTO_STR_REGION",    [76,   1023, 126,  1073]))
MAIN_MENU_REGION   = tuple(int(x) for x in _cfg.get("MAIN_MENU_REGION",   [660,  760,  1260, 900]))
ROCK_HEALTH_BAR_REGION  = tuple(int(x) for x in _cfg.get("ROCK_HEALTH_BAR_REGION",  [610, 55, 1328, 122]))
# Same scale as Kraken (1.5%). 15% was leftover from the old fill-% detector and
# missed the thin meteor bar ~75% of the time (stall fallback "won").
ROCK_HEALTH_BAR_SEEN_THRESH = float(_cfg.get("ROCK_HEALTH_BAR_SEEN_THRESH", 0.015))
METEOR_RED_MISSING_THRESH = float(_cfg.get("METEOR_RED_MISSING_THRESH", 0.003))
METEOR_RED_SEEN_THRESH = float(_cfg.get("METEOR_RED_SEEN_THRESH", 0.010))
METEOR_BROKEN_VOTES = int(_cfg.get("METEOR_BROKEN_VOTES", 2))
METEOR_POST_BREAK_HIT_SECONDS = float(_cfg.get("METEOR_POST_BREAK_HIT_SECONDS", 0.10))
METEOR_BREAK_TIMEOUT_SECONDS = float(_cfg.get("METEOR_BREAK_TIMEOUT_SECONDS", 10.0))
METEOR_HEALTH_BAR_SEEN_THRESH = float(_cfg.get("METEOR_HEALTH_BAR_SEEN_THRESH", 0.06))
METEOR_INITIAL_GAIN_SECONDS = float(_cfg.get("METEOR_INITIAL_GAIN_SECONDS", 8.0))
METEOR_GAIN_REL_THRESHOLD = float(_cfg.get("METEOR_GAIN_REL_THRESHOLD", 1.00001))
METEOR_GAIN_MIN_HITS = int(_cfg.get("METEOR_GAIN_MIN_HITS", 2))
METEOR_STONE_STALL_SECONDS = float(_cfg.get("METEOR_STONE_STALL_SECONDS", 1.5))
METEOR_NO_BAR_MAX_SECONDS = float(_cfg.get("METEOR_NO_BAR_MAX_SECONDS", 8.0))
TELEPORT_BUTTON_REGION    = tuple(int(x) for x in _cfg.get("TELEPORT_BUTTON_REGION",    [827, 807, 1171, 868]))
TELEPORT_BASE_REGION      = tuple(int(x) for x in _cfg.get("TELEPORT_BASE_REGION",      [790, 843, 1130, 902]))
TELEPORT_AREA1_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA1_REGION",     [790, 138, 1130, 198]))
TELEPORT_AREA2_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA2_REGION",     [790, 226, 1130, 286]))
TELEPORT_AREA3_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA3_REGION",     [790, 314, 1130, 374]))
TELEPORT_AREA4_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA4_REGION",     [790, 403, 1130, 463]))
TELEPORT_AREA5_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA5_REGION",     [790, 491, 1130, 551]))
TELEPORT_AREA6_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA6_REGION",     [790, 579, 1130, 639]))
TELEPORT_AREA7_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA7_REGION",     [790, 755, 1130, 815]))
TELEPORT_AREA8_REGION     = tuple(int(x) for x in _cfg.get("TELEPORT_AREA8_REGION",     [790, 843, 1130, 902]))
TELEPORT_PANEL_CLICK      = tuple(int(x) for x in _cfg.get("TELEPORT_PANEL_CLICK",      [997, 836]))
TELEPORT_CLOSE_SAMPLE     = tuple(int(x) for x in _cfg.get("TELEPORT_CLOSE_SAMPLE",     [1001, 957]))
TELEPORT_CLOSE_CLICK      = tuple(int(x) for x in _cfg.get("TELEPORT_CLOSE_CLICK",      [1001, 939]))
TELEPORT_DEST_AREA1       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA1",       [954, 113]))
TELEPORT_DEST_AREA2       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA2",       [954, 200]))
TELEPORT_DEST_AREA3       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA3",       [953, 292]))
TELEPORT_DEST_AREA4       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA4",       [951, 378]))
TELEPORT_DEST_AREA5       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA5",       [954, 468]))
TELEPORT_DEST_AREA6       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA6",       [960, 559]))
TELEPORT_DEST_AREA7       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA7",       [953, 646]))
TELEPORT_DEST_AREA8       = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_AREA8",       [953, 734]))
TELEPORT_DEST_COSMIC      = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_COSMIC",      [957, 822]))
TELEPORT_DEST_BASE        = tuple(int(x) for x in _cfg.get("TELEPORT_DEST_BASE",        [952, 915]))
TELEPORT_SAMPLE_AREA1     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA1",     [823, 136]))
TELEPORT_SAMPLE_AREA2     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA2",     [820, 184]))
TELEPORT_SAMPLE_AREA3     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA3",     [810, 278]))
TELEPORT_SAMPLE_AREA4     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA4",     [813, 363]))
TELEPORT_SAMPLE_AREA5     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA5",     [815, 452]))
TELEPORT_SAMPLE_AREA6     = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_AREA6",     [806, 542]))
TELEPORT_SAMPLE_COSMIC    = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_COSMIC",    [810, 804]))
TELEPORT_SAMPLE_BASE      = tuple(int(x) for x in _cfg.get("TELEPORT_SAMPLE_BASE",      [811, 889]))
# TODO: picker color samples for TELEPORT_SAMPLE_AREA7 / AREA8 (currently 500ms wait)
REBIRTH_CLOSE_SAMPLE      = tuple(int(x) for x in _cfg.get("REBIRTH_CLOSE_SAMPLE",      [381, 960]))
REBIRTH_CLOSE_CLICK       = tuple(int(x) for x in _cfg.get("REBIRTH_CLOSE_CLICK",       [381, 940]))
REBIRTH_BTN1_CLICK        = tuple(int(x) for x in _cfg.get("REBIRTH_BTN1_CLICK",        [955, 938]))
REBIRTH_BTN2_SAMPLE       = tuple(int(x) for x in _cfg.get("REBIRTH_BTN2_SAMPLE",       [1366, 966]))
REBIRTH_BTN2_CLICK        = tuple(int(x) for x in _cfg.get("REBIRTH_BTN2_CLICK",        [1548, 940]))
LOADOUT_PANEL_CLICK       = tuple(int(x) for x in _cfg.get("LOADOUT_PANEL_CLICK",       [1001, 659]))
LOADOUT_PANEL_SAMPLE      = tuple(int(x) for x in _cfg.get("LOADOUT_PANEL_SAMPLE",      [853, 679]))
LOADOUT_CLOSE_CLICK       = tuple(int(x) for x in _cfg.get("LOADOUT_CLOSE_CLICK",       [958, 1028]))
LOADOUT_CLOSE_SAMPLE      = tuple(int(x) for x in _cfg.get("LOADOUT_CLOSE_SAMPLE",      [959, 1054]))
LOADOUT_SLOT_1            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_1",            [359, 465]))
LOADOUT_SLOT_2            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_2",            [952, 460]))
LOADOUT_SLOT_3            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_3",            [1561, 465]))
LOADOUT_SLOT_4            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_4",            [360, 967]))
LOADOUT_SLOT_5            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_5",            [958, 963]))
LOADOUT_SLOT_6            = tuple(int(x) for x in _cfg.get("LOADOUT_SLOT_6",            [1554, 966]))
LOADOUT_SAMPLE_1          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_1",          [278, 446]))
LOADOUT_SAMPLE_2          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_2",          [891, 446]))
LOADOUT_SAMPLE_3          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_3",          [1499, 446]))
LOADOUT_SAMPLE_4          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_4",          [290, 946]))
LOADOUT_SAMPLE_5          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_5",          [901, 946]))
LOADOUT_SAMPLE_6          = tuple(int(x) for x in _cfg.get("LOADOUT_SAMPLE_6",          [1501, 945]))
FORCE_ESC_SAMPLE          = tuple(int(x) for x in _cfg.get("FORCE_ESC_SAMPLE",          [1622, 149]))
FORCE_MENU_CLICK          = tuple(int(x) for x in _cfg.get("FORCE_MENU_CLICK",          [1677, 66]))
FORCE_EXIT_SAMPLE         = tuple(int(x) for x in _cfg.get("FORCE_EXIT_SAMPLE",         [1800, 779]))
FORCE_LOBBY_CLICK         = tuple(int(x) for x in _cfg.get("FORCE_LOBBY_CLICK",         [1567, 170]))
FORCE_READY_SAMPLE        = tuple(int(x) for x in _cfg.get("FORCE_READY_SAMPLE",        [252, 940]))
FORCE_READY_CLICK         = tuple(int(x) for x in _cfg.get("FORCE_READY_CLICK",         [255, 910]))
FORCE_SHARD_SAMPLE        = tuple(int(x) for x in _cfg.get("FORCE_SHARD_SAMPLE",        [1668, 773]))
FORCE_ESC_COLOR           = (5, 14, 38)        # #050e26
FORCE_EXIT_COLOR          = (247, 255, 26)     # #f7ff1a
FORCE_READY_COLOR         = (247, 255, 26)     # #f7ff1a
FORCE_SHARD_COLORS        = ((111, 21, 192), (108, 15, 193))  # #6f15c0 #6c0fc1
TELEPORT_CLOSE_COLOR      = (247, 255, 26)   # #f7ff1a
# ── F4 teleport menu shift bug ──────────────────────────────────────────────
# The F4 teleport menu (and its destination list) can occasionally render
# the whole panel anchored further LEFT than normal - a client-side UI
# scale/anchor glitch, not something the bot does. Measured at 1920x1080:
# normal close button ~x=1001, bugged close button ~x=339 -> ~663px left.
# teleport_menu.py checks this shifted spot before assuming a stuck leftover
# menu; if found there, it keeps working with every F4-menu coordinate
# offset by this same amount instead of force-closing + reopening.
# 0 disables shift detection entirely.
TELEPORT_MENU_SHIFT_DX = float(_cfg.get("TELEPORT_MENU_SHIFT_DX", 663) or 0)
REBIRTH_BTN2_COLOR        = (191, 196, 200)  # #bfc4c8
MAP_BLACK_REGION          = tuple(int(x) for x in _cfg.get("MAP_BLACK_REGION",          [360, 90, 1560, 960]))

# ── Daily Quests (rebirth rail) ────────────────────────────────────────────────
# 1920x1080 authoring coords — auto-scaled at runtime (see _SCALED_*_KEYS).
# Quest panel OCR crops (user-measured, wide X for localization text).
QUEST_PANEL1_TEXT_REGION = tuple(int(x) for x in _cfg.get("QUEST_PANEL1_TEXT_REGION", [105, 485, 619, 544]))
QUEST_PANEL2_TEXT_REGION = tuple(int(x) for x in _cfg.get("QUEST_PANEL2_TEXT_REGION", [705, 484, 1219, 545]))
QUEST_PANEL3_TEXT_REGION = tuple(int(x) for x in _cfg.get("QUEST_PANEL3_TEXT_REGION", [1307, 482, 1817, 548]))
# Start / Complete button per panel.
QUEST_PANEL1_BTN  = tuple(int(x) for x in _cfg.get("QUEST_PANEL1_BTN",  [355, 762]))
QUEST_PANEL2_BTN  = tuple(int(x) for x in _cfg.get("QUEST_PANEL2_BTN",  [949, 763]))
QUEST_PANEL3_BTN  = tuple(int(x) for x in _cfg.get("QUEST_PANEL3_BTN",  [1570, 760]))
# Close button: click point + yellow sample point (detect like F4 close).
QUEST_CLOSE_CLICK  = tuple(int(x) for x in _cfg.get("QUEST_CLOSE_CLICK",  [969, 846]))
QUEST_CLOSE_SAMPLE = tuple(int(x) for x in _cfg.get("QUEST_CLOSE_SAMPLE", [1073, 861]))
# HUD quest tracker slots — green "Done" (#00f500) detection regions.
QUEST_HUD1_DONE_REGION = tuple(int(x) for x in _cfg.get("QUEST_HUD1_DONE_REGION", [0, 409, 90, 464]))
QUEST_HUD2_DONE_REGION = tuple(int(x) for x in _cfg.get("QUEST_HUD2_DONE_REGION", [0, 488, 90, 544]))
QUEST_HUD3_DONE_REGION = tuple(int(x) for x in _cfg.get("QUEST_HUD3_DONE_REGION", [0, 567, 90, 625]))
# ── Hatch Pets GUI (base NPC) — user-measured 1920x1080 ──────────────────────
HATCH_AREA1_TEXT_REGION = tuple(int(x) for x in _cfg.get("HATCH_AREA1_TEXT_REGION", [525, 375, 1201, 434]))
HATCH_CLOSE_SAMPLE  = tuple(int(x) for x in _cfg.get("HATCH_CLOSE_SAMPLE",  [1569, 918]))
HATCH_CLOSE_CLICK   = tuple(int(x) for x in _cfg.get("HATCH_CLOSE_CLICK",   [1567, 897]))
HATCH_NEXT_CLICK    = tuple(int(x) for x in _cfg.get("HATCH_NEXT_CLICK",    [1070, 918]))
HATCH_ALL_CLICK     = tuple(int(x) for x in _cfg.get("HATCH_ALL_CLICK",     [1042, 839]))
HATCH_MAX_PAGES       = int(_cfg.get("HATCH_MAX_PAGES", 12))
# Hatch GUI's yellow close button reads ~0.27 when open (thinner button than
# the quest board's) — its own threshold, lower than QUEST_CLOSE_MIN_PCT.
HATCH_CLOSE_MIN_PCT   = float(_cfg.get("HATCH_CLOSE_MIN_PCT", 0.20))
HATCH_OCR_SETTLE      = float(_cfg.get("HATCH_OCR_SETTLE", 0.45))
HATCH_OPEN_TIMEOUT    = float(_cfg.get("HATCH_OPEN_TIMEOUT", 6.0))
# ── Combine Pets (F4 monitor menu) — user-measured 1920x1080 ─────────────────
COMBINE_PETS_CLICK  = tuple(int(x) for x in _cfg.get("COMBINE_PETS_CLICK",  [991, 486]))
COMBINE_ZAPPY_CLICK = tuple(int(x) for x in _cfg.get("COMBINE_ZAPPY_CLICK", [253, 346]))
COMBINE_ZAPPY_CLOSE_CLICK  = tuple(int(x) for x in _cfg.get("COMBINE_ZAPPY_CLOSE_CLICK",  [965, 1031]))
COMBINE_ZAPPY_CLOSE_SAMPLE = tuple(int(x) for x in _cfg.get("COMBINE_ZAPPY_CLOSE_SAMPLE", [965, 1010]))
COMBINE_AUTOCOMBINE_CLICK  = tuple(int(x) for x in _cfg.get("COMBINE_AUTOCOMBINE_CLICK",  [357, 1029]))
COMBINE_AUTOCOMBINE_CLOSE_CLICK  = tuple(int(x) for x in _cfg.get("COMBINE_AUTOCOMBINE_CLOSE_CLICK",  [359, 941]))
COMBINE_AUTOCOMBINE_CLOSE_SAMPLE = tuple(int(x) for x in _cfg.get("COMBINE_AUTOCOMBINE_CLOSE_SAMPLE", [362, 923]))
COMBINE_AUTOCOMBINE_CONFIRM_CLICK = tuple(int(x) for x in _cfg.get("COMBINE_AUTOCOMBINE_CONFIRM_CLICK", [344, 1020]))
COMBINE_AC_CONFIRM_CLICKS = int(_cfg.get("COMBINE_AC_CONFIRM_CLICKS", 3))
COMBINE_AC_CONFIRM_SETTLE = float(_cfg.get("COMBINE_AC_CONFIRM_SETTLE", 0.15))
COMBINE_PANEL_TIMEOUT = float(_cfg.get("COMBINE_PANEL_TIMEOUT", 3.5))
# Top-right mineral "+gain" popup crop (only the +number part is parsed).

QUEST_MINE_TIMEOUT_SECONDS  = int(_cfg.get("QUEST_MINE_TIMEOUT_SECONDS", 90))
QUEST_HUD_POLL_SECONDS      = float(_cfg.get("QUEST_HUD_POLL_SECONDS", 0.15))
QUEST_BTN_SETTLE            = float(_cfg.get("QUEST_BTN_SETTLE", 0.35))
QUEST_CLOSE_MIN_PCT          = float(_cfg.get("QUEST_CLOSE_MIN_PCT", 0.30))
QUEST_DONE_MIN_PCT           = float(_cfg.get("QUEST_DONE_MIN_PCT", 0.02))
QUEST_REOPEN_SETTLE          = float(_cfg.get("QUEST_REOPEN_SETTLE", 0.25))
QUEST_REOPEN_TIMEOUT_SECONDS = float(_cfg.get("QUEST_REOPEN_TIMEOUT_SECONDS", 60.0))
# normalized lazily in quest_menu (normalize_binding_name is defined further down)
QUEST_MENU_KEY               = str(_cfg.get("QUEST_MENU_KEY", "E") or "E").strip().upper() or "E"
QUEST_DEBUG                  = _cfg_bool("QUEST_DEBUG", True)

def normalize_quest_aliases(raw) -> list:
    """Parse DAILY_QUEST_ALIASES ('|'-separated) into a clean list.

    Each alias may contain {$NUMBER} where the quest digit sits, e.g.
    'BREAK {$NUMBER} STAR ROCKS'. Matching is case/space-insensitive.
    """
    if isinstance(raw, (list, tuple)):
        items = [str(x) for x in raw]
    else:
        items = str(raw or "").split("|")
    out, seen = [], set()
    for it in items:
        a = it.strip()
        if a and a.upper() not in seen:
            seen.add(a.upper())
            out.append(a)
    return out or ["BREAK {$NUMBER} STAR ROCKS"]

DAILY_QUEST_ALIASES = normalize_quest_aliases(_cfg.get("DAILY_QUEST_ALIASES", "BREAK {$NUMBER} STAR ROCKS"))
QUEST_MIMIC_ALIASES  = normalize_quest_aliases(_cfg.get("QUEST_MIMIC_ALIASES", "Open Chests"))
# Hatch / Combine pet quests (Daily Quests rail, v1.8.30) + the hatch GUI
# page-title alias ("Area 1 Egg"). Same alias add/remove style as the others:
# pipe-separated lists in data/config.json.
QUEST_HATCH_ALIASES   = normalize_quest_aliases(_cfg.get("QUEST_HATCH_ALIASES", "Hatch Pets"))
QUEST_COMBINE_ALIASES = normalize_quest_aliases(_cfg.get("QUEST_COMBINE_ALIASES", "Combine Pets"))
HATCH_AREA1_ALIASES   = normalize_quest_aliases(_cfg.get("HATCH_AREA1_ALIASES", "Area 1 Egg"))
# â”€â”€ Menu Resume OCR regions (user-selected via dashboard calib) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MENU_PLAY_REGION    = tuple(int(x) for x in _cfg.get("MENU_PLAY_REGION",    [660,  840,  820,  900]))
MENU_PRIVACY_REGION = tuple(int(x) for x in _cfg.get("MENU_PRIVACY_REGION", [660,  770,  820,  840]))
# â”€â”€ PLAY button color detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Fortnite PLAY button is bright yellow (HSV ~25, 220, 240).
# Tolerances are wide so slight UI theme changes don't break it.
MENU_PLAY_HSV_TARGET = tuple(int(x) for x in _cfg.get("MENU_PLAY_HSV_TARGET", [25, 220, 240]))
MENU_PLAY_HUE_TOL    = int(_cfg.get("MENU_PLAY_HUE_TOL",   15))
MENU_PLAY_SAT_TOL    = int(_cfg.get("MENU_PLAY_SAT_TOL",   60))
MENU_PLAY_VAL_TOL    = int(_cfg.get("MENU_PLAY_VAL_TOL",   60))
MENU_PLAY_COLOR_THRESH = float(_cfg.get("MENU_PLAY_COLOR_THRESH", 0.08))  # 8% of region must match

# â”€â”€ Stone icon color â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STONE_ICON_HSV_TARGET = tuple(int(x) for x in _cfg.get("STONE_ICON_HSV_TARGET", [13, 140, 180]))
STONE_ICON_HUE_TOL    = int(_cfg.get("STONE_ICON_HUE_TOL",   10))
STONE_ICON_SAT_TOL    = int(_cfg.get("STONE_ICON_SAT_TOL",   70))
STONE_ICON_VAL_TOL    = int(_cfg.get("STONE_ICON_VAL_TOL",   80))
STONE_ICON_THRESH     = float(_cfg.get("STONE_ICON_THRESH", 0.15))

# â”€â”€ Auto-strength icon â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
AUTO_STR_WHITE_THRESH = float(_cfg.get("AUTO_STR_WHITE_THRESH", 0.15))
AUTO_STR_SAT_MAX      = int(_cfg.get("AUTO_STR_SAT_MAX",   60))
AUTO_STR_VAL_MIN      = int(_cfg.get("AUTO_STR_VAL_MIN",  180))

# Bottom-left cyan drill timer. #00ffff → OpenCV HSV (90, 255, 255).
# Threshold is well below 50% — digits on dark HUD are ~10-25% of the box.
# Too high = false "not active" = wasting drills. Too low = skip when idle.
DRILL_ACTIVE_REGION = tuple(int(x) for x in _cfg.get("DRILL_ACTIVE_REGION", [28, 697, 124, 728]))
CRATER_LOADOUT_METEOR_REWARDS = str(_cfg.get("CRATER_LOADOUT_METEOR_REWARDS", "none")).strip().lower() or "none"
FARM_METEOR_LOADOUT = str(_cfg.get("FARM_METEOR_LOADOUT", "none")).strip().lower() or "none"
FARM_METEOR_AREA = str(_cfg.get("FARM_METEOR_AREA", "a6")).strip().lower()
if FARM_METEOR_AREA not in ("a6", "a7", "a8"):
    FARM_METEOR_AREA = "a6"
METEOR_HEALTH_CHECK = _cfg_bool("METEOR_HEALTH_CHECK", True)
FIXED_A5_HIT_TIME = _t("FIXED_A5_HIT_TIME", int, 60)
HIT_ROCKS = _cfg_bool("HIT_ROCKS", True)
# Single fixed settle after every teleport / map load (the old per-area
# base/A5/A6 color detection is gone).
MAP_LOAD_FIXED_SECONDS = float(_cfg.get("MAP_LOAD_FIXED_SECONDS", 0.5) or 0.5)
HIT_BASEROCK = _cfg_bool("HIT_BASEROCK", True)
HIT_A5_METEOR = _cfg_bool("HIT_A5_METEOR", True)
FARM_METEOR_NODE_FARM_SECONDS = float(_cfg.get("FARM_METEOR_NODE_FARM_SECONDS", 10.0) or 10.0)
ROUTE_REDO_LIMIT = int(_cfg.get("ROUTE_REDO_LIMIT", 5) or 5)
# ---- Manual strength clicking method (Fine-Tuning -> Manual Strength) ----
# "default": current pacing profile (5s stall watchdog, 0.5s open waits,
#             30s no-strength timeout) and 1ms hold/gap clicks.
# "classic": the original v1.9.10 timing profile the fast method was tuned
#             on (60s stall watchdog, 0.25s post-monitor open wait, 60s
#             no-strength timeout) - same 1ms clicks, patient watchdogs.
# "compat":  like classic but clicks at a guaranteed 12ms hold + 12ms gap
#             (perf_counter spin-wait). For machines whose 1ms sleeps are
#             REAL 1ms (high-res timer) - the game drops near-1ms clicks
#             there; 12ms registers everywhere.
# Manual Strength open/click pacing (v1.8.31). When MANUAL_STR_OPEN is False
# the bot never presses the monitor key + clicks to open the strength window
# itself — a macro must open it (the live loop waits for the window instead).
MANUAL_STR_OPEN = bool(_cfg.get("MANUAL_STR_OPEN", True))
# Click pacing: gap between LEFTUP and the next LEFTDOWN (click -> click), and
# hold time between LEFTDOWN and LEFTUP (down -> up). Both in ms, default 1ms.
# MINIMUM 1ms is enforced: 0ms makes the game merge/eat clicks ENTIRELY (they
# register nothing — verified on the Fortnite lobby click tests and the Sep 17
# 09:27 baserock stall: ~690 clicks at 0ms bought zero upgrades, every attempt
# tripped the 5s HUD no-gain watchdog). Compat mode overrides both to 12ms.
MANUAL_STR_CLICK_DELAY_MS = max(1, int(float(_cfg.get("MANUAL_STR_CLICK_DELAY_MS", 1) or 1)))
MANUAL_STR_CLICK_HOLD_MS  = max(1, int(float(_cfg.get("MANUAL_STR_CLICK_HOLD_MS", 1) or 1)))
_ms_method = str(_cfg.get("MANUAL_STR_CLICK_METHOD", "default") or "default").strip().lower()
MANUAL_STR_CLICK_METHOD = _ms_method if _ms_method in ("default", "classic", "compat") else "default"
# Bottom-row spam pattern: N right-side buys, then M left-side unlock
# clicks (5/1 = the classic pattern; 1/1 = plain alternation).
MANUAL_STR_BOTTOM_RIGHT_CLICKS = max(1, int(_cfg.get("MANUAL_STR_BOTTOM_RIGHT_CLICKS", 5) or 5))
MANUAL_STR_BOTTOM_LEFT_CLICKS  = max(1, int(_cfg.get("MANUAL_STR_BOTTOM_LEFT_CLICKS", 1) or 1))
MANUAL_STR_HUD_STALL_SECONDS = float(_cfg.get("MANUAL_STR_HUD_STALL_SECONDS", 5.0 if MANUAL_STR_CLICK_METHOD == "default" else 60.0) or 5.0)
DRILL_ACTIVE_HSV_TARGET = tuple(int(x) for x in _cfg.get("DRILL_ACTIVE_HSV_TARGET", [90, 255, 255]))
DRILL_ACTIVE_HUE_TOL    = int(_cfg.get("DRILL_ACTIVE_HUE_TOL", 12))
DRILL_ACTIVE_SAT_TOL    = int(_cfg.get("DRILL_ACTIVE_SAT_TOL", 90))
DRILL_ACTIVE_VAL_TOL    = int(_cfg.get("DRILL_ACTIVE_VAL_TOL", 90))
DRILL_ACTIVE_THRESH     = float(_cfg.get("DRILL_ACTIVE_THRESH", 0.10))

# â”€â”€ Area 5 detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# â”€â”€ Mouse sensitivity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
RECORDED_SENS_H = float(_cfg.get("RECORDED_SENS_H", 17.0))
RECORDED_SENS_V = float(_cfg.get("RECORDED_SENS_V", 17.0))
USER_SENS_H     = float(_cfg.get("USER_SENS_H",     17.0))
USER_SENS_V     = float(_cfg.get("USER_SENS_V",     17.0))

# Never call SPI_SETMOUSESPEED — that opens the Windows mouse-settings popup.
# Playback is 1:1 with recorded deltas (no software pointer-speed scaling).
MACRO_NORMALIZE_WINDOWS_MOUSE = False
MACRO_EXPECTED_WINDOWS_MOUSE_SPEED = 10
MACRO_EXPECTED_WINDOWS_MOUSE_ACCELERATION = 1

# â”€â”€ Stone thresholds â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
STONE_FOR_A1_STAGE2 = float(_cfg.get("STONE_FOR_A1_STAGE2", 34.20e9))
STONE_FOR_A1_STAGE3 = float(_cfg.get("STONE_FOR_A1_STAGE3", 934.00e15))
STONE_FOR_A1_STAGE4 = float(_cfg.get("STONE_FOR_A1_STAGE4", 25.50e24))

STONE_FOR_A2_STAGE1 = float(_cfg.get("STONE_FOR_A2_STAGE1", 837.99e30))
STONE_FOR_A2_STAGE2 = float(_cfg.get("STONE_FOR_A2_STAGE2", 22.89e39))
STONE_FOR_A2_STAGE3 = float(_cfg.get("STONE_FOR_A2_STAGE3", 626.00e45))
STONE_FOR_A2_STAGE4 = float(_cfg.get("STONE_FOR_A2_STAGE4", 17.09e54))

STONE_FOR_A3_STAGE1 = float(_cfg.get("STONE_FOR_A3_STAGE1", 572.00e60))
STONE_FOR_A3_STAGE2 = float(_cfg.get("STONE_FOR_A3_STAGE2", 15.59e69))
STONE_FOR_A3_STAGE3 = float(_cfg.get("STONE_FOR_A3_STAGE3", 427.00e75))
STONE_FOR_A3_STAGE4 = float(_cfg.get("STONE_FOR_A3_STAGE4", 11.69e84))

STONE_FOR_A4_STAGE1 = float(_cfg.get("STONE_FOR_A4_STAGE1", 363.00e90))
STONE_FOR_A4_STAGE2 = float(_cfg.get("STONE_FOR_A4_STAGE2", 9.29e99))
STONE_FOR_A4_STAGE3 = float(_cfg.get("STONE_FOR_A4_STAGE3", 271.00e105))
STONE_FOR_A4_STAGE4 = float(_cfg.get("STONE_FOR_A4_STAGE4", 7.41e114))

STONE_FOR_A5_STAGE1 = float(_cfg.get("STONE_FOR_A5_STAGE1", 2.43e+122))
STONE_FOR_A5_STAGE2 = float(_cfg.get("STONE_FOR_A5_STAGE2", 6.65e+129))
STONE_FOR_A5_STAGE3 = float(_cfg.get("STONE_FOR_A5_STAGE3", 1.82e+137))
STONE_FOR_A5_STAGE4 = float(_cfg.get("STONE_FOR_A5_STAGE4", 4.96e+144))
STONE_FOR_METEOR    = float(_cfg.get("STONE_FOR_METEOR",     1.5e+151))
# Shortcut meteor mode base-rock target (user-provided: 136.00e150 = 1.36e152)
STONE_FOR_AREA6_SHORTCUT = float(_cfg.get("STONE_FOR_AREA6_SHORTCUT", 1.36e152))

# â”€â”€ Boss Fight A1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Baserock grind target before running A1 boss fight sequence.
# Any e33 value qualifies (default: 1e33).
BOSS_FIGHT_A1_BASEROCK_THRESHOLD = float(_cfg.get("BOSS_FIGHT_A1_BASEROCK_THRESHOLD", 1e33))
# How many boss fight loops to run (each loop = meteor grind + bramble kill).
# Default: 3. On loop 2+ the bot re-enters bramble via fight_bramble macro.
BOSS_FIGHT_A1_AMOUNT = int(_cfg.get("BOSS_FIGHT_A1_AMOUNT", 3))
# How many seconds to grind the A1 meteor PER fight on the FIRST fight (default 10).
# Actual grind time = METEOR_GRIND_SECONDS * fight_number (scales: fight1=10s, fight2=20s, fight3=30s).
BOSS_FIGHT_A1_METEOR_GRIND_SECONDS = float(_cfg.get("BOSS_FIGHT_A1_METEOR_GRIND_SECONDS", 10.0))
# Loadout slot to select BEFORE walking to Bramble (1-6, or "none" to skip).
# Plays macros/select_loadout_<N>.macro from Config > Boss Fight.
BOSS_FIGHT_A1_LOADOUT_FIGHTING = str(_cfg.get("BOSS_FIGHT_A1_LOADOUT_FIGHTING", "none"))
# Loadout slot to restore ONCE after all Bramble fights (1-6, or "none" to skip).
BOSS_FIGHT_A1_LOADOUT_FARMING  = str(_cfg.get("BOSS_FIGHT_A1_LOADOUT_FARMING",  "none"))
# Bramble / Zytos card difficulty. OCR aliases live in BOSS_FIGHT_A1_MODE_OCR so
# translated clients can match Solo/Normal/Hard/Ex without a code change.
# Card cycle is Normal → Hard → Ex → Solo. Kraken is Solo-only and skips this.
_BRAMBLE_MODE_KEYS = ("solo", "normal", "hard", "ex")
DEFAULT_BRAMBLE_MODE_OCR = {
    "solo": ["SOLO"],
    "normal": ["NORMAL"],
    "hard": ["HARD"],
    "ex": ["EX", "EXTREME"],
}


def normalize_bramble_mode(value: str) -> str:
    v = str(value or "normal").strip().lower().replace(" ", "")
    aliases = {"extreme": "ex", "expert": "ex", "normalmode": "normal", "easy": "normal"}
    v = aliases.get(v, v)
    return v if v in _BRAMBLE_MODE_KEYS else "normal"


def normalize_bramble_mode_ocr(raw) -> dict:
    out = {k: list(v) for k, v in DEFAULT_BRAMBLE_MODE_OCR.items()}
    if not isinstance(raw, dict):
        return out
    for k in _BRAMBLE_MODE_KEYS:
        src = raw.get(k, raw.get(k.upper()))
        if not isinstance(src, list):
            continue
        cleaned = []
        seen = set()
        for item in src:
            s = str(item or "").strip()
            key = s.upper()
            if s and key not in seen:
                seen.add(key)
                cleaned.append(s)
        out[k] = cleaned
    return out


BOSS_FIGHT_A1_MODE = normalize_bramble_mode(_cfg.get("BOSS_FIGHT_A1_MODE", "normal"))
BOSS_FIGHT_A1_MODE_OCR = normalize_bramble_mode_ocr(_cfg.get("BOSS_FIGHT_A1_MODE_OCR"))
BRAMBLE_MODE_REGION = tuple(int(x) for x in _cfg.get("BRAMBLE_MODE_REGION", [182, 270, 701, 331]))
BRAMBLE_MODE_SWAP_CENTER = tuple(int(x) for x in _cfg.get("BRAMBLE_MODE_SWAP_CENTER", [439, 826]))
BRAMBLE_MODE_SWAP_MAX = int(_cfg.get("BRAMBLE_MODE_SWAP_MAX", 8))
BRAMBLE_MODE_SWAP_WAIT = float(_cfg.get("BRAMBLE_MODE_SWAP_WAIT", 0.45))
# â”€â”€ Timing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MACRO_POLL_INTERVAL   = float(_cfg.get("MACRO_POLL_INTERVAL",   1.0))
STONE_STALL_TIMEOUT   = int(_cfg.get("STONE_STALL_TIMEOUT",   120))
SMART_FAILURE_TIMEOUT = int(_cfg.get("SMART_FAILURE_TIMEOUT",   60))
METEOR_HIT_SECONDS    = int(_cfg.get("METEOR_HIT_SECONDS",      5))
STARTUP_SETTLE_SECONDS = float(_cfg.get("STARTUP_SETTLE_SECONDS", 0.35))
PERFORMANCE_PROFILE = str(_cfg.get("PERFORMANCE_PROFILE", "normal")).strip().lower()
if PERFORMANCE_PROFILE == "default":
    PERFORMANCE_PROFILE = "normal"
if PERFORMANCE_PROFILE not in ("fast", "normal", "slow"):
    PERFORMANCE_PROFILE = "normal"
PAUSE_ON_LAG = _cfg_bool("PAUSE_ON_LAG", False)


def _perf() -> str:
    """Legacy profile - only used to pick DEFAULTS for the per-key timings below."""
    try:
        p = str(PERFORMANCE_PROFILE or "normal").strip().lower()
    except Exception:
        p = "normal"
    if p == "default":
        p = "normal"
    return p if p in ("fast", "normal", "slow") else "normal"


def _perf_value(key: str, fast: float, normal: float, slow: float) -> float:
    """Editable per-key timing (fine-tune config). The old PERFORMANCE_PROFILE
    (fast/normal/slow) only decides the DEFAULT when the key is unset."""
    p = _perf()
    base = slow if p == "slow" else (fast if p == "fast" else normal)
    try:
        return max(0.0, float(_cfg.get(key, base) or base))
    except Exception:
        return base


# Per-key timings are real module attributes now: the dashboard reads them via
# getattr() (which it could not do when they lived only inside the getters),
# and save_values() setattr()s them live, so an edit saved in the dashboard
# takes effect immediately — the getters below just return the attribute.
UI_CLICK_SETTLE = _perf_value("UI_CLICK_SETTLE", 0.10, 0.10, 0.55)
UI_BTN_SETTLE = _perf_value("UI_BTN_SETTLE", 0.10, 0.10, 0.17)
LOBBY_SETTLE = _perf_value("LOBBY_SETTLE", 1.0, 5.0, 10.0)
LOBBY_READY_SETTLE = _perf_value("LOBBY_READY_SETTLE", 5.0, 10.0, 15.0)
LOBBY_STEP_DELAY = _perf_value("LOBBY_STEP_DELAY", 0.25, 0.50, 1.00)


def ui_click_settle() -> float:
    """After F4 / teleport / loadout / rebirth clicks (not the manual-str spam)."""
    return UI_CLICK_SETTLE


def ui_btn_settle() -> float:
    return UI_BTN_SETTLE


def startup_settle() -> float:
    return max(0.0, float(STARTUP_SETTLE_SECONDS or 0.35))


def lobby_settle() -> float:
    """After shard is seen, before continuing the run."""
    return LOBBY_SETTLE


def lobby_ready_settle() -> float:
    """After Ready is seen, before clicking it."""
    return LOBBY_READY_SETTLE


def lobby_step_delay() -> float:
    """After ESC / each lobby click, before the next color poll."""
    return LOBBY_STEP_DELAY


# Rebirth confirm (rebirth2) button detection
REBIRTH_BTN2_TOL = int(_cfg.get("REBIRTH_BTN2_TOL", 120) or 120)
REBIRTH_BTN2_TIMEOUT = float(_cfg.get("REBIRTH_BTN2_TIMEOUT", 4.0) or 4.0)


# â”€â”€ Stage top-up timeouts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_raw_topup = _cfg.get("STAGE_TOPUP_SECONDS", {})
STAGE_TOPUP_SECONDS = {
    "base":   int(_raw_topup.get("base",   15)),
    1:        int(_raw_topup.get("1",      15)),
    2:        int(_raw_topup.get("2",      15)),
    3:        int(_raw_topup.get("3",      15)),
    4:        int(_raw_topup.get("4",      15)),
    "meteor": int(_raw_topup.get("meteor", 15)),
}

# â”€â”€ Topup poll timeout â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TOPUP_TIMEOUT = int(_cfg.get("TOPUP_TIMEOUT", 60))   # hard cap on topup poll phase (seconds)
MANUAL_STR_POST_CLOSE_SETTLE_SECONDS = float(_cfg.get("MANUAL_STR_POST_CLOSE_SETTLE_SECONDS", 1.0))
MANUAL_STR_POST_CLOSE_TOPUP_SECONDS = float(_cfg.get("MANUAL_STR_POST_CLOSE_TOPUP_SECONDS", 2.0))
MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS = float(_cfg.get("MANUAL_STR_POST_CLOSE_CONFIRM_TIMEOUT_SECONDS", 20.0))

TELEPORT_WAIT         = float(_cfg.get("TELEPORT_WAIT",         0.5))
TELEPORT_TO_BASE_WAIT = float(_cfg.get("TELEPORT_TO_BASE_WAIT", 0.5))
TELEPORT_WAIT_A5      = float(_cfg.get("TELEPORT_WAIT_A5",      0.5))
A5_CHECK_ATTEMPTS     = int(_cfg.get("A5_CHECK_ATTEMPTS",     10))
REBIRTH_CHECK_DELAY   = int(_cfg.get("REBIRTH_CHECK_DELAY",   5))
REBIRTH_SETTLE_WAIT   = int(_cfg.get("REBIRTH_SETTLE_WAIT",   3))
REBIRTH_POST_CONFIRM_WAIT = float(_cfg.get("REBIRTH_POST_CONFIRM_WAIT", 1.0))  # wait AFTER rebirth confirmed before teleporting to base
FOCUS_RECHECK_DELAY   = float(_cfg.get("FOCUS_RECHECK_DELAY",   1.0))
MENU_RESUME_JOIN_WAIT = int(_cfg.get("MENU_RESUME_JOIN_WAIT",  120))   # seconds to wait after pressing PLAY for the game to load (a join can take 30s-2min)

# ─────────────────────────────────────────────────────────────────────────────
# Force Restart flow v2 — three-state recovery + OCR lobby navigation +
# wrong-game map search. All values editable in Global Force Restart settings.
# ─────────────────────────────────────────────────────────────────────────────
# State 3 of the three-state recovery: after all GUIs are closed and the
# in-game image is still missing, wait up to this long for the HUD image or
# the lobby menu (a join can legitimately take 30s-2min) before giving up
# and leaving to the lobby. Default 120s.
FORCE_NOTINGAME_WAIT     = int(_cfg.get("FORCE_NOTINGAME_WAIT",     120))
# ── Display probe (display-off diagnostic logging) ──────────────────────────
# Background thread grabs the full screen every DISPLAY_PROBE_SECONDS and logs
# black/dark/vivid ratios, grab latency, monitor count, foreground window and
# the GAME_DETECT result, bracketing any display-off window in the log.
# Grep "[DISPLAY]" after a display-off test. Set DISPLAY_PROBE_ENABLED=False
# to silence it completely.
DISPLAY_PROBE_ENABLED     = _cfg_bool("DISPLAY_PROBE_ENABLED",     True)
DISPLAY_PROBE_SECONDS     = float(_cfg.get("DISPLAY_PROBE_SECONDS", 30))
# Lobby menu search window (PLAY OCR + scroll-up drift protection).
FORCE_MENU_TIMEOUT       = int(_cfg.get("FORCE_MENU_TIMEOUT",       60))
# Pause between "MT2 already selected" and the PLAY press. Default 5s.
FORCE_PLAY_SETTLE        = float(_cfg.get("FORCE_PLAY_SETTLE",      5.0))
# Island code typed into Search Discover when the wrong game is selected.
FORCE_MAP_CODE           = str(_cfg.get("FORCE_MAP_CODE",          "2311-7649-8274")).strip()
# Map search: max seconds to wait for the picked game-logo billboard image.
FORCE_MAP_SEARCH_TIMEOUT = int(_cfg.get("FORCE_MAP_SEARCH_TIMEOUT", 30))
# Map search: how many full attempts (scroll-up reset -> type -> search)
# before giving up. Each miss resets the search and runs it again.
FORCE_MAP_SEARCH_ATTEMPTS = int(_cfg.get("FORCE_MAP_SEARCH_ATTEMPTS", 3))
# Map search: max seconds to wait for the SELECT button after the billboard.
FORCE_SELECT_TIMEOUT     = int(_cfg.get("FORCE_SELECT_TIMEOUT",     30))
# Map search: max seconds to wait for the title to read Miner Tycoon 2 again.
FORCE_TITLE_TIMEOUT      = int(_cfg.get("FORCE_TITLE_TIMEOUT",      30))
# OCR alias lists (comma-separated, normalized: case/punctuation ignored).
FORCE_OCR_PLAY_ALIASES   = str(_cfg.get("FORCE_OCR_PLAY_ALIASES",   "play"))
FORCE_OCR_TITLE_ALIASES  = str(_cfg.get("FORCE_OCR_TITLE_ALIASES",  "miner tycoon 2,minertycoon2,miner tycoon,miner"))
FORCE_OCR_SEARCH_ALIASES = str(_cfg.get("FORCE_OCR_SEARCH_ALIASES", "search discover,search,discover"))
FORCE_OCR_SELECT_ALIASES = str(_cfg.get("FORCE_OCR_SELECT_ALIASES", "select"))
# OCR regions (1920x1080 base coords, scaled at runtime).
FORCE_PLAY_OCR_REGION    = tuple(int(x) for x in _cfg.get("FORCE_PLAY_OCR_REGION",    [100, 887, 417, 942]))
FORCE_GAME_TITLE_REGION  = tuple(int(x) for x in _cfg.get("FORCE_GAME_TITLE_REGION",  [83, 665, 438, 704]))
FORCE_SEARCH_DISCOVER_REGION = tuple(int(x) for x in _cfg.get("FORCE_SEARCH_DISCOVER_REGION", [147, 145, 883, 201]))
FORCE_SELECT_OCR_REGION  = tuple(int(x) for x in _cfg.get("FORCE_SELECT_OCR_REGION",  [89, 898, 392, 935]))
# Map search click points (1920x1080 base coords, scaled at runtime).
FORCE_SEARCH_CLICK         = tuple(int(x) for x in _cfg.get("FORCE_SEARCH_CLICK",         [243, 172]))
FORCE_GAME_BILLBOARD_CLICK = tuple(int(x) for x in _cfg.get("FORCE_GAME_BILLBOARD_CLICK", [225, 493]))
FORCE_SELECT_CLICK         = tuple(int(x) for x in _cfg.get("FORCE_SELECT_CLICK",         [238, 915]))
# Map-search game-logo billboard image (picked via the Force Restart tab,
# no default: wrong-game recovery without it stops the bot with an error).
FORCE_GAME_LOGO_IMAGE     = str(_cfg.get("FORCE_GAME_LOGO_IMAGE", "")).strip()
FORCE_GAME_LOGO_BOX       = list(_cfg.get("FORCE_GAME_LOGO_BOX", []))
FORCE_GAME_LOGO_SCREEN    = list(_cfg.get("FORCE_GAME_LOGO_SCREEN", []))
STONE_ICON_MISSING_WAIT = int(_cfg.get("STONE_ICON_MISSING_WAIT", 3))   # seconds to wait after stone icon disappears before attempting menu resume / soft-kill
MENU_APPEAR_WAIT      = int(_cfg.get("MENU_APPEAR_WAIT",      60))  # seconds to wait for the menu to appear after kick, before checking for PLAY button

# Teleport/menu interaction timings (F4 flow reliability)
TELEPORT_MENU_OPEN_DELAY_SECONDS = float(_cfg.get("TELEPORT_MENU_OPEN_DELAY_SECONDS", 0.10))
TELEPORT_MENU_OPEN_TIMEOUT_SECONDS = float(_cfg.get("TELEPORT_MENU_OPEN_TIMEOUT_SECONDS", 1.25))
TELEPORT_PANEL_OPEN_DELAY_SECONDS = float(_cfg.get("TELEPORT_PANEL_OPEN_DELAY_SECONDS", 0.10))
TELEPORT_POST_CLICK_DELAY_SECONDS = float(_cfg.get("TELEPORT_POST_CLICK_DELAY_SECONDS", 0.10))
TELEPORT_MENU_CHECK_DELAY_SECONDS = float(_cfg.get("TELEPORT_MENU_CHECK_DELAY_SECONDS", 0.10))
TELEPORT_VERIFY_POLL_SECONDS = float(_cfg.get("TELEPORT_VERIFY_POLL_SECONDS", 0.05))
TELEPORT_VERIFY_EXTRA_SECONDS = float(_cfg.get("TELEPORT_VERIFY_EXTRA_SECONDS", 0.30))
TELEPORT_POST_F4_CHECK_DELAY_SECONDS = float(_cfg.get("TELEPORT_POST_F4_CHECK_DELAY_SECONDS", 2.00))
TELEPORT_MENU_SETTLE_BEFORE_FIRST_CLICK_SECONDS = float(_cfg.get("TELEPORT_MENU_SETTLE_BEFORE_FIRST_CLICK_SECONDS", 0.35))
TELEPORT_MENU_CLOSE_GRACE_SECONDS = float(_cfg.get("TELEPORT_MENU_CLOSE_GRACE_SECONDS", 0.35))
TELEPORT_POST_SUCCESS_SETTLE_SECONDS = float(_cfg.get("TELEPORT_POST_SUCCESS_SETTLE_SECONDS", 1.50))
A5_POST_MACRO_VERIFY_DELAY = float(_cfg.get("A5_POST_MACRO_VERIFY_DELAY", 0.05))

# Delve mode menu/button regions (1920x1080 game coords, scaled at runtime).
DELVE_CLOSE_REGION = tuple(int(x) for x in _cfg.get("DELVE_CLOSE_REGION", [900, 895, 1220, 955]))
DELVE_JOIN_REGION = tuple(int(x) for x in _cfg.get("DELVE_JOIN_REGION", [1070, 795, 1415, 865]))
DELVE_JOIN_CENTER = tuple(int(x) for x in _cfg.get("DELVE_JOIN_CENTER", [1242, 830]))
DELVE_MENU_WAIT_SECONDS = float(_cfg.get("DELVE_MENU_WAIT_SECONDS", 0.5))
DELVE_JOIN_CLICK_GAP_SECONDS = float(_cfg.get("DELVE_JOIN_CLICK_GAP_SECONDS", 0.5))
DELVE_POST_JOIN_WAIT_SECONDS = float(_cfg.get("DELVE_POST_JOIN_WAIT_SECONDS", 0.5))
DELVE_WEAPON_BINDING = str(_cfg.get("DELVE_WEAPON_BINDING", "1"))
DELVE_DEATH_WAIT_SECONDS = float(_cfg.get("DELVE_DEATH_WAIT_SECONDS", 5))
DELVE_SHOOT_POLL_SECONDS = float(_cfg.get("DELVE_SHOOT_POLL_SECONDS", 0.1))
DELVE_SHOOT_REASSERT_SECONDS = float(_cfg.get("DELVE_SHOOT_REASSERT_SECONDS", 0.5))
DELVE_ROUTE_ATTEMPTS = int(_cfg.get("DELVE_ROUTE_ATTEMPTS", 10))
# AI / ESP / YOLO / torch removed. Download Center is WIP for future mode zips.
# Kraken mode. Model is intentionally not bundled; train/copy it to this path.
KRAKEN_CLOSE_REGION = tuple(int(x) for x in _cfg.get("KRAKEN_CLOSE_REGION", list(DELVE_CLOSE_REGION)))
KRAKEN_JOIN_REGION = tuple(int(x) for x in _cfg.get("KRAKEN_JOIN_REGION", list(DELVE_JOIN_REGION)))
KRAKEN_JOIN_CENTER = tuple(int(x) for x in _cfg.get("KRAKEN_JOIN_CENTER", list(DELVE_JOIN_CENTER)))
KRAKEN_MENU_WAIT_SECONDS = float(_cfg.get("KRAKEN_MENU_WAIT_SECONDS", DELVE_MENU_WAIT_SECONDS))
KRAKEN_JOIN_CLICK_GAP_SECONDS = float(_cfg.get("KRAKEN_JOIN_CLICK_GAP_SECONDS", DELVE_JOIN_CLICK_GAP_SECONDS))
KRAKEN_POST_JOIN_WAIT_SECONDS = float(_cfg.get("KRAKEN_POST_JOIN_WAIT_SECONDS", 1.0))  # settle after joining (default 1s)
KRAKEN_WEAPON_BINDING = str(_cfg.get("KRAKEN_WEAPON_BINDING", DELVE_WEAPON_BINDING))
KRAKEN_DEATH_WAIT_SECONDS = float(_cfg.get("KRAKEN_DEATH_WAIT_SECONDS", DELVE_DEATH_WAIT_SECONDS))
KRAKEN_SHOOT_POLL_SECONDS = float(_cfg.get("KRAKEN_SHOOT_POLL_SECONDS", DELVE_SHOOT_POLL_SECONDS))
KRAKEN_SHOOT_REASSERT_SECONDS = float(_cfg.get("KRAKEN_SHOOT_REASSERT_SECONDS", DELVE_SHOOT_REASSERT_SECONDS))
KRAKEN_ROUTE_ATTEMPTS = int(_cfg.get("KRAKEN_ROUTE_ATTEMPTS", 10))
KRAKEN_DRILL_ENABLED = _cfg_bool("KRAKEN_DRILL_ENABLED", False)
KRAKEN_DRILL_INTERVAL_SECONDS = float(_cfg.get("KRAKEN_DRILL_INTERVAL_SECONDS", 10.0))
KRAKEN_HEALTH_BAR_REGION = tuple(int(x) for x in _cfg.get("KRAKEN_HEALTH_BAR_REGION", [610, 55, 1328, 122]))
KRAKEN_HEALTH_BAR_SEEN_THRESH = float(_cfg.get("KRAKEN_HEALTH_BAR_SEEN_THRESH", 0.015))
KRAKEN_HB_CONFIRM_WINDOW_SECONDS = float(_cfg.get("KRAKEN_HB_CONFIRM_WINDOW_SECONDS", 3.5))  # single watch window after bar gone: no black screen = kill (default 3.5s)
KRAKEN_POST_HB_LOSS_SHOOT_SECONDS = float(_cfg.get("KRAKEN_POST_HB_LOSS_SHOOT_SECONDS", 1.5))  # keep firing this long after the health bar disappears
KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS = float(_cfg.get("KRAKEN_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", 8.0))  # max seconds to wait for the boss health bar to appear after joining
KRAKEN_REWARD_OPEN_WAIT_SECONDS = float(_cfg.get("KRAKEN_REWARD_OPEN_WAIT_SECONDS", 0.5))  # settle after reward walk before checking menu (default 0.5s)
KRAKEN_REWARD_WALK_SECONDS = float(_cfg.get("KRAKEN_REWARD_WALK_SECONDS", 4.0))  # fixed forward walk after the kill, spamming E, until the reward NPC menu opens (default 4.0s)

# -- Zytos mode (mirrors Kraken, separate config) --
ZYTOS_CLOSE_REGION = tuple(int(x) for x in _cfg.get("ZYTOS_CLOSE_REGION", list(KRAKEN_CLOSE_REGION)))
ZYTOS_JOIN_REGION = tuple(int(x) for x in _cfg.get("ZYTOS_JOIN_REGION", [1070, 795, 1415, 865]))
ZYTOS_JOIN_CENTER = tuple(int(x) for x in _cfg.get("ZYTOS_JOIN_CENTER", [1337, 826]))
ZYTOS_MENU_WAIT_SECONDS = float(_cfg.get("ZYTOS_MENU_WAIT_SECONDS", KRAKEN_MENU_WAIT_SECONDS))
ZYTOS_JOIN_CLICK_GAP_SECONDS = float(_cfg.get("ZYTOS_JOIN_CLICK_GAP_SECONDS", KRAKEN_JOIN_CLICK_GAP_SECONDS))
ZYTOS_POST_JOIN_WAIT_SECONDS = float(_cfg.get("ZYTOS_POST_JOIN_WAIT_SECONDS", KRAKEN_POST_JOIN_WAIT_SECONDS))
ZYTOS_WEAPON_BINDING = str(_cfg.get("ZYTOS_WEAPON_BINDING", KRAKEN_WEAPON_BINDING))
ZYTOS_DEATH_WAIT_SECONDS = float(_cfg.get("ZYTOS_DEATH_WAIT_SECONDS", KRAKEN_DEATH_WAIT_SECONDS))
ZYTOS_SHOOT_POLL_SECONDS = float(_cfg.get("ZYTOS_SHOOT_POLL_SECONDS", KRAKEN_SHOOT_POLL_SECONDS))
ZYTOS_SHOOT_REASSERT_SECONDS = float(_cfg.get("ZYTOS_SHOOT_REASSERT_SECONDS", KRAKEN_SHOOT_REASSERT_SECONDS))
ZYTOS_ROUTE_ATTEMPTS = int(_cfg.get("ZYTOS_ROUTE_ATTEMPTS", 10))
ZYTOS_HEALTH_BAR_REGION = tuple(int(x) for x in _cfg.get("ZYTOS_HEALTH_BAR_REGION", [605, 48, 657, 121]))
ZYTOS_HEALTH_BAR_SEEN_THRESH = float(_cfg.get("ZYTOS_HEALTH_BAR_SEEN_THRESH", 0.015))
ZYTOS_HB_CONFIRM_WINDOW_SECONDS = float(_cfg.get("ZYTOS_HB_CONFIRM_WINDOW_SECONDS", 3.5))  # single watch window after bar gone: no black screen = kill (default 3.5s)
ZYTOS_REWARD_OPEN_WAIT_SECONDS = float(_cfg.get("ZYTOS_REWARD_OPEN_WAIT_SECONDS", 1.0))
ZYTOS_POST_HB_LOSS_SHOOT_SECONDS = float(_cfg.get("ZYTOS_POST_HB_LOSS_SHOOT_SECONDS", 1.5))
ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS = float(_cfg.get("ZYTOS_HEALTH_BAR_FIRST_SEEN_TIMEOUT_SECONDS", 8.0))


# User-configurable keybinds/buttons
MENU_TOGGLE_BINDING = str(_cfg.get("MENU_TOGGLE_BINDING", "F4"))
PICKAXE_EQUIP_BINDING = str(_cfg.get("PICKAXE_EQUIP_BINDING", "F"))
DRILL_ACTIVATE_BINDING = str(_cfg.get("DRILL_ACTIVATE_BINDING", "I"))
AUTO_STRENGTH_TOGGLE_BINDING = str(_cfg.get("AUTO_STRENGTH_TOGGLE_BINDING", "MOUSE_MIDDLE"))
BOT_START_BINDING = str(_cfg.get("BOT_START_BINDING", "F8"))
BOT_STOP_BINDING = str(_cfg.get("BOT_STOP_BINDING", "F9"))
RECORDER_RECORD_BINDING = str(_cfg.get("RECORDER_RECORD_BINDING", "F5")).strip().upper() or "F5"
RECORDER_PLAY_BINDING = str(_cfg.get("RECORDER_PLAY_BINDING", "F6")).strip().upper() or "F6"
RECORDER_SMOOTH_MOVE_KEY = str(_cfg.get("RECORDER_SMOOTH_MOVE_KEY", "L")).strip().upper() or "L"
WEAPON_1_BINDING = str(_cfg.get("WEAPON_1_BINDING", "1")).strip().upper() or "1"
WEAPON_2_BINDING = str(_cfg.get("WEAPON_2_BINDING", "2")).strip().upper() or "2"
MONITOR_ITEM_BINDING = str(_cfg.get("MONITOR_ITEM_BINDING", WEAPON_2_BINDING)).strip().upper() or "2"
SPRINT_BINDING = str(_cfg.get("SPRINT_BINDING", "SHIFT")).strip().upper() or "SHIFT"
FORWARD_BINDING = str(_cfg.get("FORWARD_BINDING", "W")).strip().upper() or "W"
BACKWARD_BINDING = str(_cfg.get("BACKWARD_BINDING", "S")).strip().upper() or "S"
LEFT_BINDING = str(_cfg.get("LEFT_BINDING", "A")).strip().upper() or "A"
RIGHT_BINDING = str(_cfg.get("RIGHT_BINDING", "D")).strip().upper() or "D"
JUMP_BINDING = str(_cfg.get("JUMP_BINDING", "SPACE")).strip().upper() or "SPACE"
CROUCH_BINDING = str(_cfg.get("CROUCH_BINDING", "CTRL")).strip().upper() or "CTRL"
FIRST_STEPS_COMPLETED = _cfg_bool("FIRST_STEPS_COMPLETED", False)

# â”€â”€ Bot features â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BOT_HANDLES_AUTO_STRENGTH = _cfg_bool("BOT_HANDLES_AUTO_STRENGTH", False)

# â”€â”€ Manual strength button regions (1920Ã—1080 game coords) â”€â”€
# Used by dashboard Region Calibration â†’ MANUAL STR tab.
# MANUAL_STR_MAX_SECONDS / IDLE_WAIT are still editable in config panel.
MANUAL_STR_MAX_SECONDS    = int(_cfg.get("MANUAL_STR_MAX_SECONDS",     60))
MANUAL_STR_IDLE_WAIT      = float(_cfg.get("MANUAL_STR_IDLE_WAIT",     3.0))
MANUAL_STR_CLOSE_YELLOW_THRESH = float(_cfg.get("MANUAL_STR_CLOSE_YELLOW_THRESH", 0.45))
MANUAL_STR_MOVE_SETTLE_DELAY = float(_cfg.get("MANUAL_STR_MOVE_SETTLE_DELAY", 0.012))
# Click pacing lives in MANUAL_STR_CLICK_DELAY_MS / MANUAL_STR_CLICK_HOLD_MS
# (defaults 1ms, floors 1ms). The old MANUAL_STR_CLICK_DELAY (0.010s) /
# MANUAL_STR_POST_CLICK_DELAY keys were dead and are removed.
_mslr = _cfg.get("MANUAL_STR_ONLY_LAST_ROW", True)
MANUAL_STR_ONLY_LAST_ROW = _mslr if isinstance(_mslr, bool) else str(_mslr).strip().lower() in ("true", "1", "yes", "on")
MANUAL_STR_NO_STRENGTH_TIMEOUT = float(_cfg.get("MANUAL_STR_NO_STRENGTH_TIMEOUT", 30.0 if MANUAL_STR_CLICK_METHOD == "default" else 60.0))
MANUAL_STR_STRENGTH_POLL_SECONDS = float(_cfg.get("MANUAL_STR_STRENGTH_POLL_SECONDS", 0.35))
MANUAL_STR_STRENGTH_MIN_REL_CHANGE = float(_cfg.get("MANUAL_STR_STRENGTH_MIN_REL_CHANGE", 0.0001))
MANUAL_STR_PREOPEN_HIT_WAIT_SECONDS = float(_cfg.get("MANUAL_STR_PREOPEN_HIT_WAIT_SECONDS", 4.0))

# ---- Manual strength stop detection ----
# "stone": stop buying when the stone amount reaches the target
#          (MANUAL_STR_STONE_TARGET - the stone amount the baserock
#           grinds to with manual strength on; default = the standard
#           base-rock threshold, STONE_FOR_AREA6_SHORTCUT = 1.36e152).
# "surge": stop buying when the bottom-row Surge level (0-999) reaches
#          MANUAL_STR_SURGE_TARGET. Only works with
#          MANUAL_STR_ONLY_LAST_ROW=True (the level is read from the
#          bottom row display); otherwise the bot falls back to stone.
_ms_det = str(_cfg.get("MANUAL_STR_DETECTION", "stone") or "stone").strip().lower()
MANUAL_STR_DETECTION = _ms_det if _ms_det in ("stone", "surge") else "stone"
MANUAL_STR_STONE_TARGET = float(_cfg.get("MANUAL_STR_STONE_TARGET", STONE_FOR_AREA6_SHORTCUT) or STONE_FOR_AREA6_SHORTCUT)
MANUAL_STR_SURGE_TARGET = int(_cfg.get("MANUAL_STR_SURGE_TARGET", 160) or 160)
# Fast-open pacing: hit -> MANUAL_STR_OPEN_AFTER_HIT_WAIT -> monitor key
# ("2") -> MANUAL_STR_OPEN_AFTER_MONITOR_WAIT -> open click.
MANUAL_STR_OPEN_AFTER_HIT_WAIT = float(_cfg.get("MANUAL_STR_OPEN_AFTER_HIT_WAIT", 0.5) or 0.0)
MANUAL_STR_OPEN_AFTER_MONITOR_WAIT = float(_cfg.get("MANUAL_STR_OPEN_AFTER_MONITOR_WAIT", 0.5 if MANUAL_STR_CLICK_METHOD == "default" else 0.25) or 0.0)

# â”€â”€ Manual strength button regions (1920Ã—1080 game coords) â”€â”€â”€â”€
# Stored as flat lists [x1, y1, x2, y2] â€” dashboard calibration writes these.
MANUAL_STR_ROW1_LEFT   = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW1_LEFT",  [1137, 269, 1466, 339]))
MANUAL_STR_ROW1_RIGHT  = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW1_RIGHT", [1495, 266, 1828, 341]))
MANUAL_STR_ROW2_LEFT   = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW2_LEFT",  [1137, 426, 1466, 496]))
MANUAL_STR_ROW2_RIGHT  = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW2_RIGHT", [1495, 426, 1828, 496]))
MANUAL_STR_ROW3_LEFT   = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW3_LEFT",  [1137, 583, 1466, 653]))
MANUAL_STR_ROW3_RIGHT  = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW3_RIGHT", [1495, 583, 1828, 653]))
MANUAL_STR_ROW4_LEFT   = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW4_LEFT",  [1137, 740, 1466, 810]))
MANUAL_STR_ROW4_RIGHT  = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW4_RIGHT", [1495, 740, 1828, 810]))
MANUAL_STR_ROW5_LEFT   = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW5_LEFT",  [1137, 897, 1466, 967]))
MANUAL_STR_ROW5_RIGHT  = tuple(int(x) for x in _cfg.get("MANUAL_STR_ROW5_RIGHT", [1495, 897, 1828, 967]))
MANUAL_STR_CLOSE_REGION = tuple(int(x) for x in _cfg.get("MANUAL_STR_CLOSE_REGION", [1605, 66, 1881, 137]))
MANUAL_STR_CLOSE_CENTER = tuple(int(x) for x in _cfg.get("MANUAL_STR_CLOSE_CENTER", [1742, 101]))
MANUAL_STR_STONE_REGION = tuple(int(x) for x in _cfg.get("MANUAL_STR_STONE_REGION", [145, 72, 370, 139]))
# FIX 4 (revised): icon gap is auto-detected from the thresholded image â€” no fixed crop needed.
# MANUAL_STR_STONE_ICON_CROP_PX is no longer used and can be removed from config.json.
MANUAL_STR_STRENGTH_REGION = tuple(int(x) for x in _cfg.get("MANUAL_STR_STRENGTH_REGION", [475, 72, 682, 139]))
# Bottom-row Surge level display (0-999), left of the bottom row buttons.
MANUAL_STR_SURGE_REGION = tuple(int(x) for x in _cfg.get("MANUAL_STR_SURGE_REGION", [207, 912, 308, 971]))

# Crater countdown HUD timer (top-center "M:SS", counts down while in the
# crater mining area, resets to its start value on completion). Used to
# confirm we're actually in the crater — NOT for the rock detector capture.
CRATER_TIMER_REGION = tuple(int(x) for x in _cfg.get("CRATER_TIMER_REGION", [890, 170, 1025, 215]))
CRATER_TIMER_DEBUG  = _cfg_bool("CRATER_TIMER_DEBUG", True)

# â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
REGION_BASE_WIDTH  = int(_cfg.get("REGION_BASE_WIDTH", 1920))
REGION_BASE_HEIGHT = int(_cfg.get("REGION_BASE_HEIGHT", 1080))
RUNTIME_WIDTH, RUNTIME_HEIGHT = _detect_runtime_resolution()
REGION_SCALE_X = float(RUNTIME_WIDTH) / float(max(1, REGION_BASE_WIDTH))
REGION_SCALE_Y = float(RUNTIME_HEIGHT) / float(max(1, REGION_BASE_HEIGHT))

def _scale_point_2d(pt: tuple, w: int, h: int, sx: float, sy: float) -> tuple:
    x, y = int(pt[0]), int(pt[1])
    nx = int(round(x * sx))
    ny = int(round(y * sy))
    nx = max(0, min(max(0, w - 1), nx))
    ny = max(0, min(max(0, h - 1), ny))
    return (nx, ny)

def _scale_region_2d(region: tuple, w: int, h: int, sx: float, sy: float) -> tuple:
    x1, y1, x2, y2 = [int(v) for v in region]
    nx1 = int(round(x1 * sx)); ny1 = int(round(y1 * sy))
    nx2 = int(round(x2 * sx)); ny2 = int(round(y2 * sy))
    nx1 = max(0, min(max(0, w - 1), nx1))
    ny1 = max(0, min(max(0, h - 1), ny1))
    nx2 = max(0, min(max(1, w), nx2))
    ny2 = max(0, min(max(1, h), ny2))
    if nx2 <= nx1:
        nx2 = min(max(1, w), nx1 + 1)
    if ny2 <= ny1:
        ny2 = min(max(1, h), ny1 + 1)
    return (nx1, ny1, nx2, ny2)


def _unscale_point_2d(pt: tuple, base_w: int, base_h: int, sx: float, sy: float) -> tuple:
    x, y = int(pt[0]), int(pt[1])
    ux = int(round(x / sx)) if sx else x
    uy = int(round(y / sy)) if sy else y
    ux = max(0, min(max(0, base_w - 1), ux))
    uy = max(0, min(max(0, base_h - 1), uy))
    return (ux, uy)


def _unscale_region_2d(region: tuple, base_w: int, base_h: int, sx: float, sy: float) -> tuple:
    x1, y1, x2, y2 = [int(v) for v in region]
    ux1 = int(round(x1 / sx)) if sx else x1
    uy1 = int(round(y1 / sy)) if sy else y1
    ux2 = int(round(x2 / sx)) if sx else x2
    uy2 = int(round(y2 / sy)) if sy else y2
    ux1 = max(0, min(max(0, base_w - 1), ux1))
    uy1 = max(0, min(max(0, base_h - 1), uy1))
    ux2 = max(0, min(max(1, base_w), ux2))
    uy2 = max(0, min(max(1, base_h), uy2))
    if ux2 <= ux1:
        ux2 = min(max(1, base_w), ux1 + 1)
    if uy2 <= uy1:
        uy2 = min(max(1, base_h), uy1 + 1)
    return (ux1, uy1, ux2, uy2)


def _capture_base_regions() -> None:
    """Snapshot 1920x1080 source coords before runtime scaling.

    Scaling always starts from this snapshot so a resolution change
    never multiplies already-scaled values. Config is treated as base
    only when coords sit inside the 1920x1080 authoring frame;
    otherwise we fall back to hardcoded defaults. Works on every
    launch and every aspect ratio (16:9, 16:10, 21:9, 4:3, 9:16, ...).
    """
    _mod = sys.modules[__name__]
    repair = {}
    for key in _SCALED_REGION_KEYS:
        default = DEFAULT_REGIONS.get(key)
        val = getattr(_mod, key, default)
        if key == "ROCK_HEALTH_BAR_REGION":
            try:
                if tuple(int(x) for x in val) == _OLD_ROCK_HEALTH_BAR_REGION:
                    val = default
                    repair[key] = list(default)
            except Exception:
                val = default
        if key == "BRAMBLE_MODE_REGION":
            try:
                if tuple(int(x) for x in val) in _OLD_BRAMBLE_MODE_REGIONS:
                    val = default
                    repair[key] = list(default)
            except Exception:
                val = default
        if default is not None and not _is_base_frame_region(val):
            val = default
            repair[key] = list(default)
        if val is None:
            continue
        _BASE_REGIONS[key] = tuple(int(x) for x in val)
    for key in _SCALED_POINT_KEYS:
        default = DEFAULT_POINTS.get(key)
        val = getattr(_mod, key, default)
        if key == "BRAMBLE_MODE_SWAP_CENTER":
            try:
                if tuple(int(x) for x in val) in _OLD_BRAMBLE_MODE_SWAP_CENTERS:
                    val = default
                    repair[key] = list(default)
            except Exception:
                val = default
        if default is not None and not _is_base_frame_point(val):
            val = default
            repair[key] = list(default)
        if val is None:
            continue
        _BASE_POINTS[key] = tuple(int(x) for x in val)
    if repair:
        repair["REGION_COORDS_ARE_BASE"] = True
        _persist_cfg_patch(repair)


def _apply_runtime_region_scaling():
    """Always rescale FROM frozen/base 1920x1080 coords, never from last runtime.

    Independent X/Y scale supports every aspect ratio. Calling this twice
    is safe because the source is `_BASE_*`, not the already-scaled attrs.
    """
    global REGION_SCALE_X, REGION_SCALE_Y, RUNTIME_WIDTH, RUNTIME_HEIGHT
    if REGION_BASE_WIDTH <= 0 or REGION_BASE_HEIGHT <= 0:
        return
    if not _BASE_REGIONS and not _BASE_POINTS:
        _capture_base_regions()
    RUNTIME_WIDTH, RUNTIME_HEIGHT = _detect_runtime_resolution()
    REGION_SCALE_X = float(RUNTIME_WIDTH) / float(max(1, REGION_BASE_WIDTH))
    REGION_SCALE_Y = float(RUNTIME_HEIGHT) / float(max(1, REGION_BASE_HEIGHT))
    _mod = sys.modules[__name__]
    for key, base in _BASE_REGIONS.items():
        setattr(_mod, key, _scale_region_2d(base, RUNTIME_WIDTH, RUNTIME_HEIGHT, REGION_SCALE_X, REGION_SCALE_Y))
    for key, base in _BASE_POINTS.items():
        setattr(_mod, key, _scale_point_2d(base, RUNTIME_WIDTH, RUNTIME_HEIGHT, REGION_SCALE_X, REGION_SCALE_Y))
    try:
        from logger import get_logger as _get_scale_log
        _get_scale_log().info(
            f"[SCALE] runtime {RUNTIME_WIDTH}x{RUNTIME_HEIGHT}  "
            f"base {REGION_BASE_WIDTH}x{REGION_BASE_HEIGHT}  "
            f"sx={REGION_SCALE_X:.3f} sy={REGION_SCALE_Y:.3f}  "
            f"ratio={RUNTIME_WIDTH / max(1, RUNTIME_HEIGHT):.3f}  "
            f"regions={len(_BASE_REGIONS)} points={len(_BASE_POINTS)}"
        )
    except Exception:
        pass

LOG_LEVEL_CONSOLE = str(_cfg.get("LOG_LEVEL_CONSOLE", "INFO"))
LOG_LEVEL_FILE    = str(_cfg.get("LOG_LEVEL_FILE",    "DEBUG"))

# â”€â”€ Drill unlock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
UNLOCK_DRILLS           = _cfg_bool("UNLOCK_DRILLS", True)
STONE_FOR_UNLOCK_DRILLS = float(_cfg.get("STONE_FOR_UNLOCK_DRILLS", 1e+70))
ACTIVATE_DRILLS         = _cfg_bool("ACTIVATE_DRILLS", True)
USE_DRILL_ON_A5_METEOR  = _cfg_bool("USE_DRILL_ON_A5_METEOR", True)
USE_DRILL_ON_ROCK       = _cfg_bool("USE_DRILL_ON_ROCK", True)
USE_DRILL_ON_BASEROCK   = _cfg_bool("USE_DRILL_ON_BASEROCK", True)
AUTO_ROCK_MAX_GRIND_SECONDS = int(_cfg.get("AUTO_ROCK_MAX_GRIND_SECONDS", 30))
DELVE_ACTIVATE_DRILLS   = _cfg_bool("DELVE_ACTIVATE_DRILLS", True)
KRAKEN_ACTIVATE_DRILLS  = _cfg_bool("KRAKEN_ACTIVATE_DRILLS", True)
KRAKEN_MOVEMENT_MODE    = str(_cfg.get("KRAKEN_MOVEMENT_MODE", "linear")).strip().lower()
if KRAKEN_MOVEMENT_MODE not in {"linear", "square"}:
    KRAKEN_MOVEMENT_MODE = "linear"

ZYTOS_ACTIVATE_DRILLS  = _cfg_bool("ZYTOS_ACTIVATE_DRILLS", True)
ZYTOS_MOVEMENT_MODE    = str(_cfg.get("ZYTOS_MOVEMENT_MODE", "linear")).strip().lower()
if ZYTOS_MOVEMENT_MODE not in {"linear", "square"}:
    ZYTOS_MOVEMENT_MODE = "linear"
ZYTOS_STRAFE_HOLD_MS = int(_cfg.get("ZYTOS_STRAFE_HOLD_MS", 1750))
ZYTOS_STRAFE_INITIAL_KEY = str(_cfg.get("ZYTOS_STRAFE_INITIAL_KEY", "d")).strip().lower()
if ZYTOS_STRAFE_INITIAL_KEY not in {"w", "a", "s", "d"}:
    ZYTOS_STRAFE_INITIAL_KEY = "d"
ZYTOS_SQUARE_HOLD_SECONDS = float(_cfg.get("ZYTOS_SQUARE_HOLD_SECONDS", 2.0))
BASE_ROCK_DRILL_PRESSES = int(_cfg.get("BASE_ROCK_DRILL_PRESSES",   6))
USE_SHORTCUTS = _cfg_bool("USE_SHORTCUTS", True)
FORCE_RESTART_ON_FAILURE = _cfg_bool("FORCE_RESTART_ON_FAILURE", False)

# ── Game Detection (In-Game image detection, Force Restart tab) ─────────────
# User-picked always-visible HUD element (MT2 logo / stone icon / shard icon).
# No default is shipped — nothing is active until the user picks an image
# from the dashboard (F2 pipette, same as MacroForge). The picked PNG lives
# in data/game_detect/ with its pick box/point embedded (mfmeta tEXt chunk).
GAME_DETECT_IMAGE = str(_cfg.get("GAME_DETECT_IMAGE", "") or "").strip()   # filename in data/game_detect/
def _game_detect_box_default():
    v = _cfg.get("GAME_DETECT_BOX", [])
    if isinstance(v, (list, tuple)) and len(v) == 4:
        try:
            return [int(round(float(x))) for x in v]
        except (TypeError, ValueError):
            return []
    return []
GAME_DETECT_BOX = _game_detect_box_default()           # [x1, y1, x2, y2] at pick-time screen res
def _game_detect_screen_default():
    v = _cfg.get("GAME_DETECT_SCREEN", [])
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        try:
            return [int(v[0]), int(v[1])]
        except (TypeError, ValueError):
            return []
    return []
GAME_DETECT_SCREEN = _game_detect_screen_default()     # [w, h] the box was picked at
GAME_DETECT_DIFF = float(_cfg.get("GAME_DETECT_DIFF", 5.0))  # max image difference % counted as "in game"
GAME_DETECT_DIFF = min(100.0, max(0.0, GAME_DETECT_DIFF))


# Nova sync removed
NOVA_SYNC_ENABLED = False
NOVA_SYNC_URL = ""
NOVA_SYNC_TIMEOUT_SECONDS = 5.0
NOVA_SYNC_URL_FALLBACKS = []

def normalize_binding_name(value: str) -> str:
    """Normalize user-configured key/mouse binding names."""
    s = str(value or "").strip().upper()
    if not s:
        return ""
    s = s.replace("-", "_").replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    return s


# â”€â”€ Live-patch helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# dashboard.py calls this to update values in-memory AND persist to JSON.


# ── Crater plugin config ────────────────────────────────────
CRATER_CAPTURE_W = _t("CRATER_CAPTURE_W", int, 500)
CRATER_CAPTURE_H = _t("CRATER_CAPTURE_H", int, 350)
CRATER_HSV_LOW = _cfg.get("CRATER_HSV_LOW", [140, 50, 50])
CRATER_HSV_HIGH = _cfg.get("CRATER_HSV_HIGH", [180, 255, 255])
CRATER_USE_HUE_WRAP = _t("CRATER_USE_HUE_WRAP", bool, True)
CRATER_HSV_LOW2 = _cfg.get("CRATER_HSV_LOW2", [0, 50, 50])
CRATER_HSV_HIGH2 = _cfg.get("CRATER_HSV_HIGH2", [10, 255, 255])
CRATER_MIN_CONTOUR_AREA = _t("CRATER_MIN_CONTOUR_AREA", int, 800)
CRATER_LOCK_MIN_AREA = _t("CRATER_LOCK_MIN_AREA", int, 2000)
CRATER_AIM_SMOOTH_X = _t("CRATER_AIM_SMOOTH_X", float, 0.55)
CRATER_AIM_DEADZONE_X = _t("CRATER_AIM_DEADZONE_X", int, 12)
CRATER_SEARCH_SPEED_PX_PER_MS = _t("CRATER_SEARCH_SPEED_PX_PER_MS", int, 10)
CRATER_TARGET_LOSS_COOLDOWN_MS = _t("CRATER_TARGET_LOSS_COOLDOWN_MS", int, 50)
CRATER_TARGET_SWITCH_RATIO = _t("CRATER_TARGET_SWITCH_RATIO", float, 1.5)
CRATER_TARGET_SWITCH_COOLDOWN_MS = _t("CRATER_TARGET_SWITCH_COOLDOWN_MS", int, 200)
CRATER_LOOP_SLEEP_MS = _t("CRATER_LOOP_SLEEP_MS", int, 10)
CRATER_STARTUP_DELAY_MS = _t("CRATER_STARTUP_DELAY_MS", int, 1000)
CRATER_HIT_BINDING = str(_cfg.get("CRATER_HIT_BINDING", "MOUSE_LEFT"))
CRATER_WALK_KEY = str(_cfg.get("CRATER_WALK_KEY", "W"))
CRATER_CONTINUOUS_HIT = _t("CRATER_CONTINUOUS_HIT", bool, True)
CRATER_HIT_INTERVAL_MS = _t("CRATER_HIT_INTERVAL_MS", int, 100)
CRATER_MAX_FAILURES = _t("CRATER_MAX_FAILURES", int, 5)

# Crater timer validity tracker — confirms we're actually in the crater
# area via the countdown HUD (it only ever counts down, resetting to its
# start value on completion). Hysteresis-based: a single bad/missing read
# is common (dust, dropped frame, blend with background) and must NOT
# immediately flag "not in crater" — that would trigger a teleport retry
# while still legitimately in the crater, which fully breaks positioning.
# Only CRATER_TIMER_MISS_THRESHOLD consecutive bad reads in a row (checked
# every CRATER_TIMER_CHECK_INTERVAL_MS) confirms we've actually left.
CRATER_TIMER_CHECK_INTERVAL_MS = _t("CRATER_TIMER_CHECK_INTERVAL_MS", int, 1000)
CRATER_TIMER_MISS_THRESHOLD = _t("CRATER_TIMER_MISS_THRESHOLD", int, 8)
CRATER_TIMER_RESET_GRACE_SECONDS = _t("CRATER_TIMER_RESET_GRACE_SECONDS", int, 5)

# ── Crater pet-drop detection ──────────────────────────────
# OCR region to scan for "Received" text when a pet drops.
# Default covers center-screen notification area (1920x1080).
CRATER_PET_DROP_REGION = tuple(int(x) for x in _cfg.get("CRATER_PET_DROP_REGION", [760, 200, 1160, 400]))
# Cooldown after a detected pet drop to avoid double-counting (ms).
CRATER_PET_DROP_COOLDOWN_MS = _t("CRATER_PET_DROP_COOLDOWN_MS", int, 10000)
# Save debug crops when pet drop is detected.
CRATER_PET_DROP_DEBUG = _cfg_bool("CRATER_PET_DROP_DEBUG", True)

CRATER_DEBUG = _cfg_bool("CRATER_DEBUG", True)  # Master debug flag for crater logging

# Apply this only after every scalable region has been declared.  Previously
# the call was above the Crater pet/rocks declarations, leaving those OCR
# crops at 1920x1080 coordinates on every custom resolution.
_capture_base_regions()
_apply_runtime_region_scaling()


def save_values(updates: dict):
    """
    Persist `updates` (dict of CONFIG_KEY â†’ value) to config.json
    and apply them to this module so running code sees them immediately.
    """
    import sys as _sys
    # Reload the current JSON from disk so we don't clobber anything
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    # JSON stores STAGE_TOPUP_SECONDS with string keys â€” keep that format.
    # For all scalable regions/points, persist BASE (1920x1080) coordinates.
    sx = float(REGION_SCALE_X or 1.0)
    sy = float(REGION_SCALE_Y or 1.0)
    bw = int(REGION_BASE_WIDTH or 1920)
    bh = int(REGION_BASE_HEIGHT or 1080)

    for k, v in updates.items():
        if k in _SCALED_REGION_KEYS and isinstance(v, (list, tuple)) and len(v) == 4:
            base_region = _unscale_region_2d(tuple(int(x) for x in v), bw, bh, sx, sy)
            data[k] = list(base_region)
            _BASE_REGIONS[k] = tuple(base_region)
        elif k in _SCALED_POINT_KEYS and isinstance(v, (list, tuple)) and len(v) == 2:
            base_point = _unscale_point_2d(tuple(int(x) for x in v), bw, bh, sx, sy)
            data[k] = list(base_point)
            _BASE_POINTS[k] = tuple(base_point)
        else:
            data[k] = v
    data["REGION_COORDS_ARE_BASE"] = True

    try:
        os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
    except Exception:
        pass
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Also patch this module in sys.modules so the running bot picks it up
    _mod = _sys.modules[__name__]
    for k, v in updates.items():
        if not hasattr(_mod, k):
            continue
        if k in _SCALED_REGION_KEYS and isinstance(v, (list, tuple)) and len(v) == 4:
            base_region = _unscale_region_2d(tuple(int(x) for x in v), bw, bh, sx, sy)
            runtime_region = _scale_region_2d(base_region, RUNTIME_WIDTH, RUNTIME_HEIGHT, sx, sy)
            setattr(_mod, k, runtime_region)
        elif k in _SCALED_POINT_KEYS and isinstance(v, (list, tuple)) and len(v) == 2:
            base_point = _unscale_point_2d(tuple(int(x) for x in v), bw, bh, sx, sy)
            runtime_point = _scale_point_2d(base_point, RUNTIME_WIDTH, RUNTIME_HEIGHT, sx, sy)
            setattr(_mod, k, runtime_point)
        else:
            setattr(_mod, k, v)


def save_region(attr: str, tup: tuple, *, already_base: bool = False):
    """Persist a single HUD region tuple (by attr name) to config.json."""
    # Map Python attr names â†’ JSON keys (they match 1:1 in this project)
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    sx = float(REGION_SCALE_X or 1.0)
    sy = float(REGION_SCALE_Y or 1.0)
    bw = int(REGION_BASE_WIDTH or 1920)
    bh = int(REGION_BASE_HEIGHT or 1080)

    if attr in _SCALED_REGION_KEYS:
        if already_base:
            base_tup = tuple(int(v) for v in tup)
        else:
            base_tup = _unscale_region_2d(tuple(int(v) for v in tup), bw, bh, sx, sy)
        data[attr] = list(base_tup)
        _BASE_REGIONS[attr] = tuple(base_tup)
    else:
        data[attr] = list(tup)
    data["REGION_COORDS_ARE_BASE"] = True
    try:
        os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
    except Exception:
        pass
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    import sys as _sys
    _mod = _sys.modules[__name__]
    if attr in _SCALED_REGION_KEYS:
        runtime_tup = _scale_region_2d(base_tup, RUNTIME_WIDTH, RUNTIME_HEIGHT, sx, sy)
        setattr(_mod, attr, runtime_tup)
    else:
        setattr(_mod, attr, tup)
