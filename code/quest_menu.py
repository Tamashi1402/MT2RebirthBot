# Daily Quests rail — quest menu mechanics.
# Pure menu/OCR helpers; run orchestration lives in bot.py (_do_daily_quests).
# All regions/points come from config (1920x1080 authoring, runtime-scaled).
import json
import os
import re
import time

import cv2
import numpy as np
import pytesseract

import config as _cfg
from logger import get_logger
from macro_runner import _mouse_left_click, _mouse_move_abs, trigger_binding_action
from screen import grab_region, color_match_percent, parse_stone, save_debug_region

log = get_logger()

_killed_fn = None

# ── killed hook (same pattern as teleport_menu) ──────────────────────────────
def set_killed_fn(fn):
    global _killed_fn
    _killed_fn = fn


def _is_killed() -> bool:
    try:
        return bool(_killed_fn and _killed_fn())
    except Exception:
        return False


# ── config accessors ─────────────────────────────────────────────────────────
_PANEL_TEXT_ATTRS = {
    1: "QUEST_PANEL1_TEXT_REGION",
    2: "QUEST_PANEL2_TEXT_REGION",
    3: "QUEST_PANEL3_TEXT_REGION",
}
_PANEL_BTN_ATTRS = {
    1: "QUEST_PANEL1_BTN",
    2: "QUEST_PANEL2_BTN",
    3: "QUEST_PANEL3_BTN",
}
_HUD_DONE_ATTRS = {
    1: "QUEST_HUD1_DONE_REGION",
    2: "QUEST_HUD2_DONE_REGION",
    3: "QUEST_HUD3_DONE_REGION",
}


def _region(attr: str, fallback: tuple) -> tuple:
    val = getattr(_cfg, attr, None)
    try:
        if val is not None and len(val) == 4:
            return tuple(int(v) for v in val)
    except Exception:
        pass
    return tuple(int(v) for v in fallback)


def _point(attr: str, fallback: tuple) -> tuple:
    val = getattr(_cfg, attr, None)
    try:
        if val is not None and len(val) == 2:
            return int(val[0]), int(val[1])
    except Exception:
        pass
    return int(fallback[0]), int(fallback[1])


def _debug_enabled() -> bool:
    try:
        return bool(getattr(_cfg, "QUEST_DEBUG", True))
    except Exception:
        return True


# ── clicks ───────────────────────────────────────────────────────────────────
def _click_xy(x: int, y: int) -> bool:
    """Move + hover dwell + click (same anti-drop pattern as teleport_menu)."""
    if _is_killed():
        return False
    _mouse_move_abs(int(x), int(y))
    time.sleep(0.12)
    _mouse_left_click()
    return True


def click_quest_button(panel: int) -> bool:
    attr = _PANEL_BTN_ATTRS.get(int(panel))
    if not attr:
        return False
    x, y = _point(attr, (0, 0))
    return _click_xy(x, y)


def click_close() -> bool:
    x, y = _point("QUEST_CLOSE_CLICK", (969, 846))
    return _click_xy(x, y)


# ── close button detection (yellow sample, like F4 close) ────────────────────
_CLOSE_YELLOW_MIN_PCT = 0.30
_SAMPLE_W = 14
_SAMPLE_H = 10


def _sample_wh() -> tuple:
    try:
        sx = float(getattr(_cfg, "REGION_SCALE_X", 1.0) or 1.0)
        sy = float(getattr(_cfg, "REGION_SCALE_Y", 1.0) or 1.0)
        return max(3, int(round(_SAMPLE_W * sx))), max(3, int(round(_SAMPLE_H * sy)))
    except Exception:
        return _SAMPLE_W, _SAMPLE_H


def _yellow_pct_at(x: int, y: int) -> float:
    """Yellow pixel % in the standard sample window at (x, y). HSV, transparency-safe."""
    try:
        w, h = _sample_wh()
        img = grab_region((int(x), int(y), int(x) + w, int(y) + h))
        if img is None or img.size == 0:
            return 0.0
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # generous yellow range (semi-transparent button support)
        mask = cv2.inRange(hsv,
                           np.array([18, 120, 170], dtype=np.uint8),
                           np.array([48, 255, 255], dtype=np.uint8))
        total = int(img.shape[0]) * int(img.shape[1])
        return float(np.sum(mask > 0)) / max(1, total)
    except Exception as e:
        log.warning(f"[QUEST] yellow-sample check failed at ({x},{y}): {e}")
        return 0.0


def _yellow_at(attr: str, fallback: tuple, tag: str, min_pct: float | None = None) -> bool:
    x, y = _point(attr, fallback)
    pct = _yellow_pct_at(x, y)
    if min_pct is None:
        min_pct = float(getattr(_cfg, "QUEST_CLOSE_MIN_PCT", _CLOSE_YELLOW_MIN_PCT))
    log.debug(f"[QUEST] {tag} yellow pct={pct:.3f} at ({x},{y}) (need>={min_pct})")
    return pct >= min_pct


def quest_menu_open() -> bool:
    """True if the yellow close-button sample matches (menu is open)."""
    try:
        return _yellow_at("QUEST_CLOSE_SAMPLE", (1073, 861), "quest close-sample")
    except Exception as e:
        log.warning(f"[QUEST] close-sample check failed: {e}")
        return False


def wait_quest_menu_open(timeout: float = 4.0) -> bool:
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _is_killed():
            return False
        if quest_menu_open():
            return True
        time.sleep(0.10)
    return False


def close_quest_menu(timeout: float = 3.0) -> bool:
    """Click close and wait until the yellow sample is gone."""
    if not quest_menu_open():
        return True
    if not click_close():
        return False
    settle = float(getattr(_cfg, "QUEST_BTN_SETTLE", 0.35))
    time.sleep(settle)
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _is_killed():
            return False
        if not quest_menu_open():
            return True
        time.sleep(0.10)
        # retry click once mid-way
        if time.time() > deadline - (timeout / 2.0):
            click_close()
    return not quest_menu_open()


# ── panel OCR ───────────────────────────────────────────────────────────────
def _preprocess_quest_text(img: np.ndarray) -> np.ndarray:
    """Quest panel text: white on dark panel. Threshold + invert for tesseract."""
    scale = 3
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    thresh = cv2.bitwise_not(thresh)
    return thresh


def read_quest_panel(panel: int) -> str:
    """OCR one quest panel's title text. Returns stripped string ('' on fail)."""
    attr = _PANEL_TEXT_ATTRS.get(int(panel))
    if not attr:
        return ""
    region = _region(attr, (0, 0, 1, 1))
    try:
        img = grab_region(region)
        if img is None or img.size == 0:
            return ""
        proc = _preprocess_quest_text(img)
        raw = pytesseract.image_to_string(
            proc,
            config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
        )
        text = raw.strip()
        if _debug_enabled():
            save_debug_region(f"quest_panel{panel}", region, extra=proc)
            log.info(f"[QUEST] panel {panel} OCR raw={text!r}")
        return text
    except Exception as e:
        log.warning(f"[QUEST] panel {panel} OCR failed: {e}")
        return ""


def is_mimic_quest(text: str, aliases=None) -> bool:
    """True when the panel OCR text matches the Mimic quest aliases."""
    aliases = aliases if aliases is not None else getattr(_cfg, "QUEST_MIMIC_ALIASES", [])
    if isinstance(aliases, str):
        # a raw string (e.g. after a config setattr bypass) would otherwise
        # be iterated character-by-character
        aliases = [a.strip() for a in aliases.split("|") if a.strip()]
    t = re.sub(r"[^A-Z0-9]", "", str(text or "").upper())
    if not t:
        return False
    merged = list(aliases or [])
    # the real quest is "Open Chests" — always match it even if the saved
    # config still holds an older alias value
    if "OPENCHESTS" not in [re.sub(r"[^A-Z0-9]", "", str(a or "").upper()) for a in merged]:
        merged.append("Open Chests")
    for alias in merged:
        n = re.sub(r"[^A-Z0-9]", "", str(alias or "").upper())
        if n and n in t:
            log.info(f"[QUEST] mimic alias {alias!r} matched text")
            return True
    return False


def classify_quest(text: str, aliases=None) -> int | None:
    """Match OCR text against DAILY_QUEST_ALIASES.

    Each alias may contain {$NUMBER} where the quest digit sits.
    Returns the star number (1-3) when matched, else None.
    """
    aliases = aliases if aliases is not None else getattr(_cfg, "DAILY_QUEST_ALIASES", [])
    if isinstance(aliases, str):
        # a raw string (e.g. after a config setattr bypass) would otherwise
        # be iterated character-by-character
        aliases = [a.strip() for a in aliases.split("|") if a.strip()]
    t = re.sub(r"[^A-Z0-9]", "", str(text or "").upper())
    if not t:
        return None
    for alias in (aliases or []):
        a = str(alias or "").upper()
        parts = re.split(r"\{\s*\$?\s*NUMBER\s*\}", a)
        if len(parts) < 2:
            # no placeholder — plain alias match, no number to extract
            n = re.sub(r"[^A-Z0-9]", "", a)
            if n and (n in t or t in n):
                log.info(f"[QUEST] alias {alias!r} matched text (no number) — cannot pick star level")
                return None
            continue
        # build: text-before-number, (\d+), text-after-number —
        # up to 4 junk chars tolerated between tokens (OCR noise)
        regex = r""
        for i, part in enumerate(parts):
            regex += re.escape(re.sub(r"\s+", "", part))
            if i < len(parts) - 1:
                regex += r".{0,4}(\d+).{0,4}"
        m = re.search(regex, t)
        if m:
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            log.info(f"[QUEST] alias {alias!r} matched {t!r} -> star={n}")
            return n
    return None


# ── HUD "Done" watch (green #00f500) ─────────────────────────────────────────
_DONE_HSV = (60, 255, 245)   # #00f500 -> opencv hue 60, full sat, ~245 val


def quest_hud_done(panel: int) -> bool:
    """True if HUD quest slot `panel` shows the green Done text."""
    attr = _HUD_DONE_ATTRS.get(int(panel))
    if not attr:
        return False
    try:
        region = _region(attr, (0, 0, 1, 1))
        img = grab_region(region)
        if img is None or img.size == 0:
            return False
        pct = color_match_percent(img, _DONE_HSV, hue_tol=12, sat_tol=60, val_tol=60)
        min_pct = float(getattr(_cfg, "QUEST_DONE_MIN_PCT", 0.02))
        if pct >= min_pct:
            log.info(f"[QUEST] HUD slot {panel} Done: green pct={pct:.3f}")
            return True
        return False
    except Exception as e:
        log.warning(f"[QUEST] HUD slot {panel} check failed: {e}")
        return False


# NOTE: mineral gain OCR was removed in v1.9 — quests are now counted
# (QUESTS COMPLETED), not measured in mineral. The claim flow simply
# clicks and counts; no counter/popup reads.


def _menu_binding() -> str:
    try:
        raw = str(getattr(_cfg, "QUEST_MENU_KEY", "E") or "E").strip().upper() or "E"
        from config import normalize_binding_name
        return normalize_binding_name(raw) or "E"
    except Exception:
        return "E"


def press_menu_key() -> None:
    from macro_runner import trigger_binding_action
    key = _menu_binding()
    try:
        if not trigger_binding_action(key, hold_ms=35):
            log.warning(f"[QUEST] invalid QUEST_MENU_KEY={key!r}; using E")
            trigger_binding_action("E", hold_ms=35)
    except Exception as e:
        log.warning(f"[QUEST] menu key press failed: {e}")


def reopen_quest_menu(timeout: float | None = None) -> bool:
    """Press E, settle, wait for the close button. False if it never opens."""
    settle = float(getattr(_cfg, "QUEST_REOPEN_SETTLE", 0.25))
    if timeout is None:
        timeout = float(getattr(_cfg, "QUEST_REOPEN_TIMEOUT_SECONDS", 60.0))
    press_menu_key()
    time.sleep(settle)
    return wait_quest_menu_open(timeout)


# ── Hatch / Combine Pets quests (v1.8.30) ────────────────────────────────────

def _norm_alias(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _alias_match(text: str, aliases, hard_fallback: str) -> bool:
    """Same alias add/remove style as is_mimic_quest: config list wins, the
    real quest name is ALWAYS matched even if the saved config holds an
    older alias value. Pipe-separated string input is supported."""
    if isinstance(aliases, str):
        aliases = [a.strip() for a in aliases.split("|") if a.strip()]
    t = _norm_alias(text)
    if not t:
        return False
    merged = [str(a or "") for a in (aliases or [])]
    if _norm_alias(hard_fallback) not in [_norm_alias(a) for a in merged]:
        merged.append(hard_fallback)
    for alias in merged:
        n = _norm_alias(alias)
        if n and n in t:
            log.info(f"[QUEST] alias {alias!r} matched text {text!r}")
            return True
        # tolerant pass: allow a few junk chars between the alias words —
        # covers OCR noise and inserted counts ("Hatch 5 Pets" etc.),
        # same tolerance idea as classify_quest's {$NUMBER} matcher.
        words = [w for w in re.split(r"\s+", str(alias or "").strip()) if w]
        if len(words) >= 2:
            regex = r".{0,3}".join(re.escape(_norm_alias(w)) for w in words)
            if re.search(regex, t):
                log.info(f"[QUEST] alias {alias!r} matched text {text!r} (word-tolerant)")
                return True
    return False


def is_hatch_quest(text: str, aliases=None) -> bool:
    """True when the panel OCR text matches the Hatch Pets quest aliases."""
    aliases = aliases if aliases is not None else getattr(_cfg, "QUEST_HATCH_ALIASES", [])
    return _alias_match(text, aliases, "Hatch Pets")


def is_combine_quest(text: str, aliases=None) -> bool:
    """True when the panel OCR text matches the Combine Pets quest aliases."""
    aliases = aliases if aliases is not None else getattr(_cfg, "QUEST_COMBINE_ALIASES", [])
    return _alias_match(text, aliases, "Combine Pets")


# ── Hatch Pets GUI (base NPC) ─────────────────────────────────────────────────

def _hatch_min_pct() -> float:
    """Hatch GUI's own close-button threshold (button reads ~0.27 when open)."""
    return float(getattr(_cfg, "HATCH_CLOSE_MIN_PCT", 0.20))


def hatch_menu_open() -> bool:
    """True if the hatch GUI's yellow close button is visible."""
    return _yellow_at("HATCH_CLOSE_SAMPLE", (1569, 918), "hatch close-sample", min_pct=_hatch_min_pct())


def wait_hatch_menu_open(timeout: float | None = None) -> bool:
    if timeout is None:
        timeout = float(getattr(_cfg, "HATCH_OPEN_TIMEOUT", 6.0))
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _is_killed():
            return False
        if hatch_menu_open():
            return True
        time.sleep(0.10)
    return False


def close_hatch_menu(timeout: float = 3.0, force_click: bool = False) -> bool:
    """Click the hatch GUI close button and wait until the yellow sample is gone.

    force_click: click at least once even when the open-detection says the GUI
    is already closed — the detection threshold can sit BELOW an open reading
    (the hatch button is thinner than the quest board's), and a GUI left open
    blocks every later F4/teleport flow.
    """
    x, y = _point("HATCH_CLOSE_CLICK", (1567, 897))
    if force_click or hatch_menu_open():
        if not _click_xy(x, y):
            return False
        settle = float(getattr(_cfg, "QUEST_BTN_SETTLE", 0.35))
        time.sleep(settle)
    else:
        return True
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _is_killed():
            return False
        if not hatch_menu_open():
            return True
        time.sleep(0.10)
        if time.time() > deadline - (timeout / 2.0):
            _click_xy(x, y)
    return not hatch_menu_open()


def read_hatch_page_text() -> str:
    """OCR the hatch GUI page-title strip ('Area 1 Egg' etc.)."""
    region = _region("HATCH_AREA1_TEXT_REGION", (525, 375, 1201, 434))
    try:
        img = grab_region(region)
        if img is None or img.size == 0:
            return ""
        proc = _preprocess_quest_text(img)
        raw = pytesseract.image_to_string(
            proc,
            config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
        )
        text = raw.strip()
        if _debug_enabled():
            save_debug_region("hatch_page", region, extra=proc)
            log.info(f"[HATCH] page OCR raw={text!r}")
        return text
    except Exception as e:
        log.warning(f"[HATCH] page OCR failed: {e}")
        return ""


def is_area1_egg(text: str, aliases=None) -> bool:
    """Alias match for the hatch GUI 'Area 1 Egg' page title (same add/remove style)."""
    aliases = aliases if aliases is not None else getattr(_cfg, "HATCH_AREA1_ALIASES", [])
    return _alias_match(text, aliases, "Area 1 Egg")


def hatch_all_flow() -> bool:
    """Page through the hatch GUI until 'Area 1 Egg', click Hatch All.

    The GUI must already be open. Returns True when Hatch All was clicked.
    Caller closes the menu afterwards either way.
    """
    settle = max(0.10, float(getattr(_cfg, "HATCH_OCR_SETTLE", 0.45)))
    max_pages = max(2, int(getattr(_cfg, "HATCH_MAX_PAGES", 12)))
    next_xy = _point("HATCH_NEXT_CLICK", (1070, 918))
    all_xy = _point("HATCH_ALL_CLICK", (1042, 839))
    for page in range(1, max_pages + 1):
        if _is_killed():
            return False
        time.sleep(settle)
        text = read_hatch_page_text()
        if not text:
            # transition frame / OCR blank — one re-read before deciding
            time.sleep(settle)
            text = read_hatch_page_text()
        if is_area1_egg(text):
            log.info(f"[HATCH] 'Area 1 Egg' found on page {page} ({text!r}) — clicking Hatch All")
            if not _click_xy(*all_xy):
                return False
            time.sleep(settle)
            return True
        log.info(f"[HATCH] page {page}: {text!r} — clicking Next")
        if not _click_xy(*next_xy):
            return False
    log.warning(f"[HATCH] 'Area 1 Egg' not found after {max_pages} pages — giving up")
    return False


# ── Combine Pets (F4 monitor menu) ─────────────────────────────────────────────

def _press_menu_toggle() -> None:
    binding = str(getattr(_cfg, "MENU_TOGGLE_BINDING", "F4") or "F4").strip().upper() or "F4"
    try:
        if not trigger_binding_action(binding, hold_ms=35):
            log.warning(f"[COMBINE] invalid MENU_TOGGLE_BINDING={binding!r}; using F4")
            trigger_binding_action("F4", hold_ms=35)
    except Exception as e:
        log.warning(f"[COMBINE] menu toggle press failed: {e}")


def _f4_menu_open() -> bool:
    """F4 menu visible (known close button — same sample the teleports use)."""
    return _yellow_at("TELEPORT_CLOSE_SAMPLE", (1001, 957), "f4 close-sample")


def _wait_yellow(attr: str, fallback: tuple, tag: str, timeout: float) -> bool:
    deadline = time.time() + max(0.0, float(timeout))
    while True:
        if _is_killed():
            return False
        if _yellow_at(attr, fallback, tag):
            return True
        if time.time() >= deadline:
            log.warning(f"[COMBINE] {tag} not seen within {timeout:.1f}s")
            return False
        time.sleep(0.10)


def _wait_yellow_gone(attr: str, fallback: tuple, tag: str, timeout: float) -> bool:
    deadline = time.time() + max(0.0, float(timeout))
    while time.time() < deadline:
        if _is_killed():
            return False
        if not _yellow_at(attr, fallback, tag):
            return True
        time.sleep(0.10)
    return False


def _click_point(attr: str, fallback: tuple, what: str) -> bool:
    x, y = _point(attr, fallback)
    log.info(f"[COMBINE] clicking {what} at ({x},{y})")
    return _click_xy(x, y)


def _combine_debug_crop(label: str, cx: int, cy: int, w: int = 700, h: int = 300) -> None:
    """Save a quest_-labeled debug crop centered on (cx, cy) when
    SAVE_DEBUG_CROPS is on. quest_* labels always save — these crops show
    what was actually on screen at the combine click points so the
    COMBINE_* points can be re-calibrated when a click misses."""
    try:
        x = max(0, int(cx) - w // 2)
        y = max(0, int(cy) - h // 2)
        save_debug_region(label, (x, y, w, h))
    except Exception as e:
        log.debug(f"[COMBINE] debug crop failed: {e}")


def combine_pets_flow(max_tries: int = 3) -> bool:
    """F4 -> PETS -> ZAPPY -> AUTO COMBINE (x3 confirm spam) -> close -> close.

    Three different close-button positions confirm the clicks landed:
    the F4 menu close (known), the ZAPPY panel close, and the AUTO COMBINE
    panel close. The auto-combine panel asks for the button AGAIN after it
    opens (3 confirmations, spam-safe), then its close button only backs
    out to the ZAPPY/inventory screen — which is closed too when detected.
    Returns True when the flow walked all the way back out. Best-effort
    cleanup of any leftover panels either way.
    """
    settle = max(0.05, float(getattr(_cfg, "QUEST_BTN_SETTLE", 0.35)))
    panel_timeout = float(getattr(_cfg, "COMBINE_PANEL_TIMEOUT", 3.5))
    f4_close_xy = _point("TELEPORT_CLOSE_CLICK", (1001, 939))
    zappy_close_xy = _point("COMBINE_ZAPPY_CLOSE_CLICK", (965, 1031))
    ac_close_xy = _point("COMBINE_AUTOCOMBINE_CLOSE_CLICK", (359, 941))
    ac_confirm_xy = _point("COMBINE_AUTOCOMBINE_CONFIRM_CLICK", (344, 1020))
    ac_confirm_clicks = max(1, int(getattr(_cfg, "COMBINE_AC_CONFIRM_CLICKS", 3)))
    ac_confirm_settle = max(0.0, float(getattr(_cfg, "COMBINE_AC_CONFIRM_SETTLE", 0.15)))

    def _cleanup() -> None:
        # best-effort: close auto-combine, then zappy, then F4 — only when detected
        try:
            if _yellow_at("COMBINE_AUTOCOMBINE_CLOSE_SAMPLE", (362, 923), "ac close"):
                _click_xy(*ac_close_xy)
                time.sleep(settle)
            if _yellow_at("COMBINE_ZAPPY_CLOSE_SAMPLE", (965, 1010), "zappy close"):
                _click_xy(*zappy_close_xy)
                time.sleep(settle)
            if _f4_menu_open():
                _click_xy(*f4_close_xy)
                time.sleep(settle)
        except Exception as e:
            log.warning(f"[COMBINE] cleanup failed: {e}")

    for attempt in range(1, max(1, int(max_tries)) + 1):
        if _is_killed():
            return False
        log.info(f"[COMBINE] attempt {attempt}/{max_tries}")
        # 1) F4 open (skip the press if a menu is already on screen)
        if not _f4_menu_open():
            _press_menu_toggle()
            time.sleep(settle)
            if not _wait_yellow("TELEPORT_CLOSE_SAMPLE", (1001, 957), "f4 close", 3.0):
                log.warning("[COMBINE] F4 menu did not open")
                continue
        # 2) PETS -> pets panel (shares the F4 menu's close button position)
        if not _click_point("COMBINE_PETS_CLICK", (991, 486), "PETS"):
            _cleanup()
            return False
        time.sleep(settle)
        # 3) ZAPPY -> zappy panel (first NEW close button position)
        if not _click_point("COMBINE_ZAPPY_CLICK", (253, 346), "ZAPPY"):
            _cleanup()
            return False
        if not _wait_yellow("COMBINE_ZAPPY_CLOSE_SAMPLE", (965, 1010), "zappy close", panel_timeout):
            log.warning("[COMBINE] zappy panel did not open — PETS/ZAPPY click may have missed")
            _cleanup()
            continue
        # 4) AUTO COMBINE (second NEW close button position)
        # Crop the panel right before the click — if the ZAPPY panel the
        # user sees on screen is not what this point expects, the crop shows it.
        _ac_click = _point("COMBINE_AUTOCOMBINE_CLICK", (357, 1029))
        _combine_debug_crop("quest_combine_ac_before", _ac_click[0], _ac_click[1])
        if not _click_point("COMBINE_AUTOCOMBINE_CLICK", (357, 1029), "AUTO COMBINE"):
            _cleanup()
            return False
        if not _wait_yellow("COMBINE_AUTOCOMBINE_CLOSE_SAMPLE", (362, 923), "ac close", panel_timeout):
            log.warning("[COMBINE] auto-combine panel not seen — retrying AUTO COMBINE click")
            time.sleep(settle)
            if not _click_point("COMBINE_AUTOCOMBINE_CLICK", (357, 1029), "AUTO COMBINE (retry)"):
                _cleanup()
                return False
            if not _wait_yellow("COMBINE_AUTOCOMBINE_CLOSE_SAMPLE", (362, 923), "ac close", panel_timeout):
                log.warning("[COMBINE] auto-combine panel still not visible")
                _cleanup()
                continue
        # 5) AUTO COMBINE confirm — the panel that opened wants the button
        # pressed AGAIN (3 confirmations; the button is spam-safe). Without
        # these clicks the auto-combine never actually runs.
        _combine_debug_crop("quest_combine_ac_panel", 362, 923)
        for i in range(1, ac_confirm_clicks + 1):
            if _is_killed():
                _cleanup()
                return False
            log.info(f"[COMBINE] clicking AUTO COMBINE confirm {i}/{ac_confirm_clicks} at "
                     f"({ac_confirm_xy[0]},{ac_confirm_xy[1]})")
            if not _click_xy(*ac_confirm_xy):
                _cleanup()
                return False
            time.sleep(ac_confirm_settle)
        # 6) close the auto-combine panel — NOTE: this does NOT fully close
        # the menus; it only backs out to the ZAPPY/inventory screen.
        if not _click_point("COMBINE_AUTOCOMBINE_CLOSE_CLICK", (359, 941), "AUTO COMBINE close"):
            _cleanup()
            return False
        if not _wait_yellow_gone("COMBINE_AUTOCOMBINE_CLOSE_SAMPLE", (362, 923), "ac close", 3.0):
            log.warning("[COMBINE] auto-combine panel still open after close")
            _cleanup()
            continue
        # 7) the panel close backs out to the ZAPPY/inventory screen — let
        # that screen actually settle in first (it needs a moment), then close
        # it when detected. If the close click does not take, retry the same
        # button with ±5px offsets on x/y (the yellow sample can still read
        # open when the click itself lands a hair off).
        if _wait_yellow("COMBINE_ZAPPY_CLOSE_SAMPLE", (965, 1010), "zappy close", 2.0):
            log.info("[COMBINE] backed out to ZAPPY screen — closing it too")
            time.sleep(settle)  # let the screen finish its transition
            zc_x, zc_y = zappy_close_xy
            for dx, dy in ((0, 0), (5, 5), (-5, -5), (5, -5), (-5, 5)):
                if _is_killed():
                    _cleanup()
                    return False
                if not _click_xy(zc_x + dx, zc_y + dy):
                    _cleanup()
                    return False
                if _wait_yellow_gone("COMBINE_ZAPPY_CLOSE_SAMPLE", (965, 1010), "zappy close", 3.0):
                    break
                log.warning(f"[COMBINE] zappy close did not take — retrying with offset ({dx:+d},{dy:+d})")
            else:
                log.warning("[COMBINE] zappy screen did not close after offsets")
                _cleanup()
                continue
        # 8) cleanup whatever is still on screen (F4 leftovers)
        _cleanup()
        log.info("[COMBINE] all clicks landed — auto combine done")
        return True

    _cleanup()
    log.warning(f"[COMBINE] failed after {max_tries} attempts")
    return False
