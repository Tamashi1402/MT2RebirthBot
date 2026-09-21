# Force Restart flow v2 — three-state recovery + OCR lobby navigation +
# wrong-game map search.
#
# Replaces the old "pixel-color Ready/shard" rejoin with an OCR-driven flow:
#
#   three_state_recovery()
#     1. In game?                    -> in-game HUD image check: path is clear
#     2. In-game not detected        -> check every known GUI (close-button
#                                     detect on all) -> close -> re-check
#     3. Clearly not in game        -> wait up to FORCE_NOTINGAME_WAIT for the
#                                     HUD image (joins take 30s-2min) or the
#                                     lobby menu, then either join straight
#                                     from the menu or give up -> full leave.
#
#   menu_join_flow()
#     - wait for the lobby: OCR "PLAY" (aliases) at FORCE_PLAY_OCR_REGION,
#       scroll up every 0.5s while waiting (we may have drifted onto some
#       other game screen), then 3 clearing clicks on the left edge
#       (x0, y/2) 20ms apart so nothing steals the first real click.
#     - verify the selected game: OCR "MINER TYCOON 2" (aliases) at
#       FORCE_GAME_TITLE_REGION. If it reads something else the bot joined
#       the wrong game after a restart — run the map search:
#         scroll down, open "Search Discover", type the island code,
#         wait for the picked "game logo" billboard image (up to
#         FORCE_MAP_SEARCH_TIMEOUT, 0.1s passes), click it, wait for the
#         SELECT button (OCR), click it, re-verify the title.
#     - every "found -> click" step sleeps 1s first: a freshly drawn
#       button is not clickable yet.
#     - press PLAY (the same play button press as before), then wait for
#       the new in-game HUD image (MENU_RESUME_JOIN_WAIT).
#
# No default game-logo image is shipped: if the bot drifts to a wrong game
# and no logo was picked, the map search aborts and the bot STOPS with a
# clear error instead of clicking random things.
from __future__ import annotations

import os
import re
import time

from logger import get_logger

log = get_logger()


def _cfg():
    import config as _config
    return _config


def _killed() -> bool:
    try:
        import bot as _bot
        return bool(getattr(_bot, "_KILLED", False))
    except Exception:
        return False


def _sleep(seconds: float) -> bool:
    """Interruptible sleep. Returns False when the bot was killed."""
    deadline = time.time() + max(0.0, float(seconds))
    while True:
        now = time.time()
        if now >= deadline:
            break
        if _killed():
            return False
        time.sleep(min(0.05, max(0.0, deadline - now)))
    return not _killed()


def _overlay(status: str, goal: str) -> None:
    try:
        from overlay import set_overlay
        set_overlay(status=status, goal=goal)
    except Exception:
        pass


def _console(status: str, goal: str = "") -> None:
    try:
        from bot import _console_status
        _console_status(status, goal)
    except Exception:
        pass


# ───────────────────────── In-game HUD check ─────────────────────────

def in_game_hud() -> bool:
    """User-picked in-game image first; legacy inGame template fallback."""
    try:
        from game_detect import game_detect_result
        res = game_detect_result()
        if res.get("ok") is not None:
            return bool(res.get("ok"))
    except Exception as e:
        log.debug(f"[FR_FLOW] game detection failed: {e}")
    try:
        from macro_logic import image_match_result
        bot_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        macro_dir = os.path.join(bot_root, "macros", "rebirth_mode")
        data = {
            "var": "inGame",
            "path": "images/1920x1080_inGame.png",
            "threshold": 90,
            "fixed": False,
        }
        res = image_match_result(data, bot_root, macro_dir)
        return bool(res.get("matched"))
    except Exception as e:
        log.debug(f"[FR_FLOW] legacy in-game template failed: {e}")
    return False


# ───────────────────────── OCR helpers ─────────────────────────

def _norm(text: str) -> str:
    """lowercase + strip everything that is not a letter or digit."""
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def _aliases(cfg_key: str, default: str) -> set:
    """Comma-separated alias list from config -> normalized set."""
    try:
        raw = str(getattr(_cfg(), cfg_key, default) or default)
    except Exception:
        raw = default
    out = set()
    for part in raw.split(","):
        n = _norm(part)
        if n:
            out.add(n)
    return out or {_norm(default)}


def _alias_hit(text_norm: str, aliases: set) -> bool:
    if len(text_norm) < 3:   # "" / 1-2 char OCR junk can substring-match anything
        return False
    return any(a in text_norm or text_norm in a for a in aliases)


def _preprocess_variants(img):
    """Grayscale Otsu (normal + inverted) and a 2x upscale — small menu text
    reads much better after upscaling. Yields (label, processed) pairs."""
    import cv2
    import numpy as np

    if img is None or getattr(img, "size", 0) == 0:
        return
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    yield "otsu", otsu
    yield "otsu_inv", cv2.bitwise_not(otsu)
    up = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    _, otsu2 = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    yield "otsu_x2", otsu2
    yield "gray", gray


def ocr_region_text(region: tuple) -> str:
    """OCR a screen region. Returns the best (most matched) raw text."""
    import pytesseract

    try:
        from screen import grab_region, ensure_tesseract
        ensure_tesseract()
        img = grab_region(region)
    except Exception as e:
        log.warning(f"[FR_FLOW] grab {tuple(region)} failed: {e}")
        return ""
    if img is None or getattr(img, "size", 0) == 0:
        return ""
    texts = []
    for label, proc in _preprocess_variants(img):
        try:
            raw = pytesseract.image_to_string(
                proc,
                config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
            )
        except Exception as e:
            log.debug(f"[FR_FLOW] ocr {label} failed: {e}")
            continue
        texts.append(raw.strip())
    best = max(texts, key=len) if texts else ""
    return best


def ocr_play_visible() -> bool:
    """OCR the lobby PLAY button (region + aliases configurable)."""
    region = tuple(int(v) for v in getattr(
        _cfg(), "FORCE_PLAY_OCR_REGION", (100, 887, 417, 942)))
    text = ocr_region_text(region)
    norm = _norm(text)
    if not norm:
        return False
    if _alias_hit(norm, _aliases("FORCE_OCR_PLAY_ALIASES", "play")):
        return True
    # classic dropped-char reads of PLAY: PAY / PLY / PLA / LAY / PUAY ...
    return bool(
        re.search(r"P[A-Z]AY", text.upper())
        or re.search(r"PL[A-Z]Y", text.upper())
        or re.search(r"PLA[A-Z]", text.upper())
        or _norm("play") in norm
    )


def ocr_title_mt2() -> bool:
    """OCR the selected-game title — 'MINER TYCOON 2' aliases."""
    region = tuple(int(v) for v in getattr(
        _cfg(), "FORCE_GAME_TITLE_REGION", (83, 665, 438, 704)))
    text = ocr_region_text(region)
    norm = _norm(text)
    if not norm:
        return False
    return _alias_hit(norm, _aliases("FORCE_OCR_TITLE_ALIASES", "miner tycoon 2,minertycoon2,miner tycoon,miner"))


def _search_region() -> tuple:
    return tuple(int(v) for v in getattr(
        _cfg(), "FORCE_SEARCH_DISCOVER_REGION", (147, 145, 883, 201)))


def ocr_search_discover_text() -> str:
    """Raw OCR text of the Search Discover bar region."""
    return ocr_region_text(_search_region())


def ocr_search_discover_visible() -> bool:
    text = ocr_search_discover_text()
    norm = _norm(text)
    if not norm:
        return False
    return _alias_hit(norm, _aliases("FORCE_OCR_SEARCH_ALIASES", "search discover,search,discover"))


def _debug_crop(label: str, region: tuple = None) -> None:
    """Save an fr_* debug crop (region + fullscreen) when SAVE_DEBUG_CROPS
    is on — the fr_* labels carry a fail/missing token so they pass the
    screen.py label filter and always save while the flag is on."""
    try:
        from screen import save_debug_region, save_debug_fullscreen
        if region:
            save_debug_region(label, region)
        save_debug_fullscreen(label)
    except Exception as e:
        log.debug(f"[FR_FLOW] debug crop failed: {e}")


def ocr_select_visible() -> bool:
    region = tuple(int(v) for v in getattr(
        _cfg(), "FORCE_SELECT_OCR_REGION", (89, 898, 392, 935)))
    text = ocr_region_text(region)
    norm = _norm(text)
    if not norm:
        return False
    return _alias_hit(norm, _aliases("FORCE_OCR_SELECT_ALIASES", "select"))


# ───────────────────────── Input helpers ─────────────────────────

def _click(x: int, y: int) -> None:
    from teleport_menu import _click_xy
    _click_xy(int(x), int(y))


def _mouse_to_list_center() -> None:
    """Park the cursor over the lobby's scrollable list. Wheel events only
    scroll the list while the cursor hovers it — over the left margin the
    wheel does nothing (the clearing clicks leave the cursor at x0)."""
    try:
        from teleport_menu import _pt
        x, y = _pt("FORCE_LIST_CENTER_POINT", (960, 540))
        from macro_runner import _mouse_move_abs
        _mouse_move_abs(int(x), int(y))
    except Exception as e:
        log.debug(f"[FR_FLOW] move-to-list-center failed: {e}")


def _scroll(notches: int) -> None:
    """Mouse wheel. Positive = scroll DOWN (content moves up = view toward
    the bottom), negative = scroll UP toward the top.

    Windows wheel delta is inverted relative to intuition: a POSITIVE
    delta means the wheel rotated away from the user, which scrolls the
    content UP (view toward the top of the list). So scrolling down needs
    a NEGATIVE delta — the sign is flipped here on purpose."""
    try:
        from macro_runner import _make_mouse, _send_input, MOUSEEVENTF_WHEEL
        _send_input(_make_mouse(MOUSEEVENTF_WHEEL, data=-int(notches) * 120))
    except Exception as e:
        log.warning(f"[FR_FLOW] scroll failed: {e}")


def _press_esc() -> None:
    from macro_runner import _key_press
    _key_press(0x1B, hold_ms=40)


def _left_edge_clear_clicks() -> None:
    """3 clicks at (x0, y/2), 20ms apart.

    Left screen edge, vertical middle: guaranteed empty of UI in the lobby.
    It unfocuses any popup that swallowed input and makes the window
    foreground, so the PLAY press and the map-search clicks all register."""
    try:
        cfg = _cfg()
        w = int(getattr(cfg, "RUNTIME_WIDTH", 1920) or 1920)
        h = int(getattr(cfg, "RUNTIME_HEIGHT", 1080) or 1080)
    except Exception:
        w, h = 1920, 1080
    for _ in range(3):
        _click(2, h // 2)
        time.sleep(0.020)


def _type_text(text: str) -> None:
    """Type a string into the focused field (digits + hyphens for codes)."""
    try:
        import keyboard
        keyboard.write(str(text))
        return
    except Exception as e:
        log.debug(f"[FR_FLOW] keyboard.write failed ({e}) — falling back to per-key")
    from macro_runner import _key_press
    for ch in str(text):
        vk = 0x30 + int(ch) if ch.isdigit() else (0xBD if ch == "-" else 0)
        if vk:
            _key_press(vk, hold_ms=30)
            time.sleep(0.03)


def _press_enter() -> None:
    """Press Enter with a real ~120ms hold — instant taps can get swallowed
    by the game's input handling (the map search submit needs it)."""
    try:
        import keyboard
        keyboard.press("enter")
        time.sleep(0.12)
        keyboard.release("enter")
    except Exception:
        from macro_runner import _key_press
        _key_press(0x0D, hold_ms=120)


# ───────────────────────── GUI close (close-button on all) ─────────────────────────

_GUI_CLOSE_POINTS = (
    # (name, sample point cfg key, default sample, click point cfg key, default click)
    ("teleport-f4", "TELEPORT_CLOSE_SAMPLE", (1001, 957), "TELEPORT_CLOSE_CLICK", (1001, 939)),
    ("loadout", "LOADOUT_CLOSE_SAMPLE", (959, 1054), "LOADOUT_CLOSE_CLICK", (958, 1028)),
    ("rebirth", "REBIRTH_CLOSE_SAMPLE", (381, 960), "REBIRTH_CLOSE_CLICK", (381, 940)),
)


def _close_yellow_at(xy) -> bool:
    try:
        from teleport_menu import _close_yellow_at as _cy
        return bool(_cy(xy))
    except Exception:
        return False


def _manual_strength_open() -> bool:
    """Strength window open = its yellow close button visible (region check)."""
    try:
        from manual_strength import is_window_open
        return bool(is_window_open())
    except Exception:
        return False


def close_all_open_guis() -> list:
    """Close-button detect on every known GUI. Returns names closed."""
    from teleport_menu import _pt
    closed = []
    for name, skey, sdef, ckey, cdef in _GUI_CLOSE_POINTS:
        try:
            sample = _pt(skey, sdef)
            if _close_yellow_at(sample):
                log.info(f"[FR_FLOW] {name} GUI open — closing")
                _click(*_pt(ckey, cdef))
                closed.append(name)
                if not _sleep(0.30):
                    return closed
        except Exception as e:
            log.debug(f"[FR_FLOW] close {name}: {e}")
    # Manual strength window: yellow close button anywhere in its region.
    try:
        if _manual_strength_open():
            log.info("[FR_FLOW] manual strength window open — closing")
            from teleport_menu import _pt
            _click(*_pt("MANUAL_STR_CLOSE_CENTER", (1742, 101)))
            closed.append("manual-strength")
            if not _sleep(0.30):
                return closed
    except Exception as e:
        log.debug(f"[FR_FLOW] close manual-strength: {e}")
    return closed


def _pause_menu_open() -> bool:
    try:
        from lobby import _pause_menu_open as _pm
        return bool(_pm())
    except Exception:
        return False


# ───────────────────────── Three-state recovery ─────────────────────────

def three_state_recovery(wait_secs: float | None = None, tag: str = "") -> str:
    """Where are we? Returns 'in_game' | 'menu' | 'give_up'.

    1. In game? -> 'in_game' (path is clear)
    2. In-game image missing -> close every open GUI -> re-check
    3. Still missing -> ESC (a popup may be eating the check) -> re-check,
       then wait up to wait_secs for the HUD image (joins take 30s-2min)
       or the lobby menu. Menu wins early: join straight from there.
       While waiting: if a pass detects nothing, it acts instead of idling —
       3 clearing clicks (x0, y/2), scroll UP to the top, re-check PLAY."""
    pre = f"[FR_FLOW]{(' [' + tag + ']') if tag else ''}"

    if in_game_hud():
        log.info(f"{pre} state 1: in game — path is clear")
        return "in_game"

    closed = close_all_open_guis()
    if closed:
        log.info(f"{pre} state 2: closed open GUIs {closed} — re-checking")
        if not _sleep(0.5):
            return "give_up"
        if in_game_hud():
            log.info(f"{pre} state 2: in game after closing GUIs")
            return "in_game"

    log.info(f"{pre} state 3: clearly not in game — ESC + pause-menu probe")
    _press_esc()
    if not _sleep(0.4):
        return "give_up"
    if _pause_menu_open():
        log.info(f"{pre} pause menu answered the ESC — still in the game client")
        _press_esc()   # close the pause menu again
        if not _sleep(0.4):
            return "give_up"
        if in_game_hud():
            log.info(f"{pre} in game after pause-menu round-trip")
            return "in_game"

    try:
        cfg_wait = int(getattr(_cfg(), "FORCE_NOTINGAME_WAIT", 120))
    except Exception:
        cfg_wait = 120
    total = max(0, int(wait_secs if wait_secs is not None else cfg_wait))
    deadline = time.time() + float(total)
    _overlay("RECOVER", f"Waiting for game / menu ({total}s)")
    _console("RECOVER", "Waiting for game / menu")
    log.info(f"{pre} state 3: waiting up to {total}s for HUD image or lobby menu")
    _mouse_to_list_center()   # wheel only scrolls the list while hovering it
    menu_hits = 0
    while time.time() < deadline:
        if _killed():
            return "give_up"
        if in_game_hud():
            log.info(f"{pre} state 3: HUD image back — in game")
            return "in_game"
        if ocr_play_visible():
            menu_hits += 1
        else:
            # Nothing detected in this pass — do NOT just sit and scroll:
            # 3 clearing clicks on the left edge REGARDLESS (x0, y/2 —
            # escapes any popup/panel the ESC probe left open and makes
            # sure the window is foreground), then scroll the list UP to
            # the top, then look for the menu again.
            log.info(f"{pre} state 3: nothing detected — "
                     f"3 clear clicks + scroll up, then re-check")
            _left_edge_clear_clicks()
            # The clicks park the cursor at x0 — the wheel only scrolls
            # while hovering the list, so move it back first.
            _mouse_to_list_center()
            _scroll(-1)   # UP — toward the top of the list
            menu_hits = 1 if ocr_play_visible() else 0
        if menu_hits >= 2:   # two consecutive reads, not one fluke
            log.info(f"{pre} state 3: lobby menu detected (PLAY x{menu_hits})")
            # No second ESC here: the PLAY button reads fine with the
            # probe-opened panel, and toggling ESC again can re-open UI
            # instead of closing it. The 3 clearing clicks in
            # wait_for_menu dismiss whatever is on screen.
            return "menu"
        time.sleep(0.5)
    log.warning(f"{pre} state 3: neither HUD image nor lobby menu after {total}s — give up")
    return "give_up"


# ───────────────────────── Lobby / menu navigation ─────────────────────────

def wait_for_menu(timeout: float = 60.0) -> bool:
    """Loop until the lobby PLAY button OCR hits.

    While looping: scroll up every 0.5s (we may have drifted onto another
    game's screen — scrolling tops the list back out) and keep the window
    clickable. On detection: 3 clearing clicks on the left edge (x0, y/2),
    20ms apart, then the caller can click real UI safely."""
    deadline = time.time() + max(0.0, float(timeout))
    last_scroll = 0.0
    log.info(f"[FR_FLOW] waiting for lobby menu (PLAY OCR, max {timeout:.0f}s)")
    _overlay("MENU", "Looking for lobby")
    _mouse_to_list_center()   # wheel scroll-up only works over the list
    while time.time() < deadline:
        if _killed():
            return False
        now = time.time()
        if now - last_scroll >= 0.5:
            _scroll(-1)   # scroll up — drift protection
            last_scroll = now
        if ocr_play_visible():
            _left_edge_clear_clicks()
            log.info("[FR_FLOW] lobby menu detected — cleared input (3x left-edge clicks)")
            return True
        time.sleep(0.15)
    log.warning("[FR_FLOW] lobby menu not found in time")
    return False


def ensure_mt2_selected(passes: int = 3) -> str:
    """'mt2' | 'wrong' | 'unknown'.

    Reads the selected-game title. An open island/SELECT page counts as
    MID-SELECTION, not a wrong game: the title region reads garbage on
    that page, so click SELECT and re-read before ever declaring 'wrong' —
    a map search run on the SELECT page scrolls the wrong surface and
    wrecks the recovery."""
    region = tuple(int(v) for v in getattr(
        _cfg(), "FORCE_GAME_TITLE_REGION", (83, 665, 438, 704)))
    last_text = ""
    for attempt in range(1, max(1, passes) + 1):
        if _killed():
            return "unknown"
        if ocr_title_mt2():
            log.info("[FR_FLOW] selected game is Miner Tycoon 2")
            return "mt2"
        # Island page still open? Confirm the selection and re-read —
        # do NOT run a map search on this page.
        if ocr_select_visible():
            log.info("[FR_FLOW] SELECT window open — clicking SELECT, then re-reading the title")
            from teleport_menu import _pt
            if not _sleep(1.0):   # settle -> click
                return "unknown"
            _click(*_pt("FORCE_SELECT_CLICK", (238, 915)))
            if not _sleep(1.5):
                return "unknown"
            continue
        last_text = ocr_region_text(region)
        time.sleep(0.3)
    if not last_text.strip():
        log.warning("[FR_FLOW] game title OCR unreadable — wrong-game recovery (debug crop: fr_title_missing)")
        _debug_crop("fr_title_missing", tuple(int(v) for v in getattr(
            _cfg(), "FORCE_GAME_TITLE_REGION", (83, 665, 438, 704))))
    else:
        log.warning(f"[FR_FLOW] selected game title OCR read \u201c{last_text.strip()}\u201d — NOT Miner Tycoon 2, wrong-game recovery (debug crop: fr_title_fail)")
        _debug_crop("fr_title_fail", region)
    return "wrong"


def _reach_search_bar() -> bool:
    """Cursor over the list, scroll UP to the top, then two notches DOWN
    to the Search Discover bar. Unhurried — every wheel step is spaced so
    the view keeps up."""
    _mouse_to_list_center()
    if not _sleep(0.5):
        return False
    for _ in range(5):
        _scroll(-1)   # up — guarantee the very top of the list
        if not _sleep(0.25):
            return False
    if not _sleep(0.5):
        return False
    _scroll(1)   # down one
    if not _sleep(0.7):
        return False
    _scroll(1)   # down two — the bar sits two notches below the top
    if not _sleep(0.7):
        return False
    last = ""
    for attempt in range(4):
        if _killed():
            return False
        last = ocr_search_discover_text()
        if _alias_hit(_norm(last), _aliases("FORCE_OCR_SEARCH_ALIASES", "search discover,search,discover")):
            log.info(f"[FR_FLOW] Search Discover bar found (OCR read “{last.strip()}”, attempt {attempt + 1})")
            return True
        _scroll(1)   # down one more notch, then look again
        if not _sleep(0.6):
            return False
    log.warning(
        f"[FR_FLOW] 'Search Discover' not found — map search will retry "
        f"(last OCR read “{last.strip() or '<nothing>'}” in region {_search_region()}; "
        "debug crops: fr_search_missing)")
    _debug_crop("fr_search_missing", _search_region())
    return False


def _submit_island_search(code: str) -> bool:
    """Click the search bar, type the island code, settle, press Enter."""
    from teleport_menu import _pt
    if not _sleep(1.0):   # found -> pause before the click (freshly drawn UI is not clickable yet)
        return False
    _click(*_pt("FORCE_SEARCH_CLICK", (243, 172)))
    if not _sleep(0.8):   # field needs a beat to take focus
        return False
    log.info(f"[FR_FLOW] typing island code {code}")
    _type_text(code)
    if not _sleep(1.0):   # typed -> settle -> Enter (too fast gets swallowed)
        return False
    _press_enter()
    if not _sleep(1.5):
        return False
    return True


def _wait_for_billboard(timeout: float) -> bool:
    """Loop for the MT2 billboard image. If it has not shown up 8s in,
    press Enter once more — the first submit sometimes gets swallowed."""
    log.info(f"[FR_FLOW] searching for the MT2 billboard image (max {timeout:.0f}s, 0.1s passes)")
    deadline = time.time() + float(timeout)
    enter_retry_at = time.time() + 8.0
    enter_retried = False
    while time.time() < deadline:
        if _killed():
            return False
        from game_detect import game_logo_result
        if game_logo_result().get("ok"):
            return True
        if not enter_retried and time.time() >= enter_retry_at:
            enter_retried = True
            log.info("[FR_FLOW] billboard not up after 8s — pressing Enter again (first submit swallowed?)")
            _press_enter()
        time.sleep(0.1)
    log.warning("[FR_FLOW] MT2 billboard image not found in search results (debug crop: fr_logo_missing)")
    _debug_crop("fr_logo_missing")
    return False


def _click_billboard_select_confirm() -> bool:
    """Click the billboard TWICE — the first click only SELECTS the card
    (it highlights and stops matching the logo image), the second click
    CONFIRMS and opens the island page. Spaced 1s; the SELECT-button loop
    afterwards verifies it landed, and the outer attempt loop retries the
    whole search if it did not."""
    from teleport_menu import _pt
    if not _sleep(1.0):   # found -> settle -> click
        return False
    log.info("[FR_FLOW] billboard click 1/2 (select)")
    _click(*_pt("FORCE_GAME_BILLBOARD_CLICK", (225, 493)))
    if not _sleep(1.0):   # let the selection register
        return False
    log.info("[FR_FLOW] billboard click 2/2 (confirm)")
    _click(*_pt("FORCE_GAME_BILLBOARD_CLICK", (225, 493)))
    if not _sleep(1.5):   # give the island page time to draw
        return False
    return True


def _find_and_click_select() -> bool:
    """Loop until SELECT is readable, settle, click it."""
    from teleport_menu import _pt
    try:
        sel_timeout = max(5, int(getattr(_cfg(), "FORCE_SELECT_TIMEOUT", 30)))
    except Exception:
        sel_timeout = 30
    deadline = time.time() + float(sel_timeout)
    while time.time() < deadline:
        if _killed():
            return False
        if ocr_select_visible():
            break
        time.sleep(0.2)
    else:
        log.warning("[FR_FLOW] SELECT button not found after clicking the billboard (debug crops: fr_select_missing)")
        _debug_crop("fr_select_missing", tuple(int(v) for v in getattr(
            _cfg(), "FORCE_SELECT_OCR_REGION", (89, 898, 392, 935))))
        return False
    if not _sleep(1.0):   # found -> settle -> click
        return False
    _click(*_pt("FORCE_SELECT_CLICK", (238, 915)))
    if not _sleep(1.5):
        return False
    return True


def _verify_title_mt2() -> bool:
    """Back in the lobby — the title must read Miner Tycoon 2 again."""
    try:
        title_timeout = max(5, int(getattr(_cfg(), "FORCE_TITLE_TIMEOUT", 30)))
    except Exception:
        title_timeout = 30
    deadline = time.time() + float(title_timeout)
    while time.time() < deadline:
        if _killed():
            return False
        if ocr_title_mt2():
            log.info("[FR_FLOW] map search done — Miner Tycoon 2 selected again")
            return True
        time.sleep(0.3)
    log.warning("[FR_FLOW] title did not read Miner Tycoon 2 after SELECT")
    return False


def map_search_flow() -> bool:
    """Drifted onto another game: search the MT2 island and select it.

    Careful by design — nothing here hard-fails on the first miss:
      * each step has 0.5-1s settle pauses (freshly drawn UI eats fast clicks)
      * the billboard takes TWO clicks: first selects, second confirms
      * if the search comes up empty, the flow scrolls UP to reset it and
        runs the whole search again (up to FORCE_MAP_SEARCH_ATTEMPTS)"""
    from game_detect import game_logo_result

    _overlay("MENU", "Searching Miner Tycoon 2")
    log.warning("[FR_FLOW] wrong game selected — starting map search")

    logo = game_logo_result()
    if not logo.get("set"):
        log.error("[FR_FLOW] game logo image not picked — cannot finish the map search (Force Restart → Wrong Game / Map Search)")
        return False
    try:
        timeout = max(5, int(getattr(_cfg(), "FORCE_MAP_SEARCH_TIMEOUT", 30)))
    except Exception:
        timeout = 30
    try:
        attempts = max(1, int(getattr(_cfg(), "FORCE_MAP_SEARCH_ATTEMPTS", 3)))
    except Exception:
        attempts = 3
    code = str(getattr(_cfg(), "FORCE_MAP_CODE", "2311-7649-8274") or "2311-7649-8274")

    for attempt in range(1, attempts + 1):
        if _killed():
            return False
        if attempt > 1:
            # A failed attempt may have left the island/SELECT page open —
            # confirm the selection instead of scrolling that page.
            if ocr_select_visible():
                log.info(f"[FR_FLOW] map search attempt {attempt}/{attempts}: SELECT window open — clicking SELECT, verifying the title")
                from teleport_menu import _pt
                if not _sleep(1.0):
                    return False
                _click(*_pt("FORCE_SELECT_CLICK", (238, 915)))
                if not _sleep(1.5):
                    return False
                if _verify_title_mt2():
                    return True
            # Previous attempt found nothing. Scroll UP — that resets the
            # search back to the lobby — then run the search again from
            # the top.
            log.info(f"[FR_FLOW] map search attempt {attempt}/{attempts}: scrolling up to reset the search, then redoing it")
            _mouse_to_list_center()
            if not _sleep(0.5):
                return False
            for _ in range(3):   # a bit more than needed — make sure it resets
                _scroll(-1)
                if not _sleep(0.5):
                    return False
            if not _sleep(1.0):
                return False

        ok = (_reach_search_bar()
              and _submit_island_search(code)
              and _wait_for_billboard(timeout)
              and _click_billboard_select_confirm()
              and _find_and_click_select()
              and _verify_title_mt2())
        if ok:
            return True
        if _killed():
            return False
        log.warning(f"[FR_FLOW] map search attempt {attempt}/{attempts} failed — "
                    + ("retrying from the top" if attempt < attempts else "no attempts left"))

    log.error("[FR_FLOW] map search failed after all attempts — giving up")
    return False



def play_and_wait_in_game() -> bool:
    """Same play button press as always, then wait for the new in-game image."""
    from teleport_menu import _pt
    try:
        settle = max(0.0, float(getattr(_cfg(), "FORCE_PLAY_SETTLE", 5.0)))
    except Exception:
        settle = 5.0
    log.info(f"[FR_FLOW] waiting {settle:.0f}s before PLAY press")
    _overlay("MENU", "Joining Miner Tycoon 2")
    if not _sleep(settle):
        return False
    play_xy = _pt("FORCE_READY_CLICK", (255, 910))
    _click(*play_xy)
    log.info(f"[FR_FLOW] clicked PLAY {play_xy}")

    try:
        join_wait = max(10, int(getattr(_cfg(), "MENU_RESUME_JOIN_WAIT", 120)))
    except Exception:
        join_wait = 120
    deadline = time.time() + float(join_wait)
    while time.time() < deadline:
        if _killed():
            return False
        if in_game_hud():
            log.info(f"[FR_FLOW] in-game HUD image found — back in the game")
            return True
        time.sleep(0.5)
    log.warning(f"[FR_FLOW] in-game HUD image not found {join_wait:.0f}s after PLAY")
    return False


def menu_join_flow(reason: str = "") -> bool:
    """From whatever menu-ish state: find lobby -> ensure MT2 -> PLAY -> in game.

    Returns True only when the picked in-game HUD image is visible again."""
    pre = f"[FR_FLOW]{(' [' + reason + ']') if reason else ''}"
    try:
        menu_timeout = max(10, int(getattr(_cfg(), "FORCE_MENU_TIMEOUT", 60)))
    except Exception:
        menu_timeout = 60
    if not wait_for_menu(menu_timeout):
        return False

    which = ensure_mt2_selected()
    if which == "wrong":
        if not map_search_flow():
            log.error(f"{pre} map search failed")
            return False
    elif which == "unknown":
        return False

    return play_and_wait_in_game()
