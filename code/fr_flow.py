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
#     - wait for the lobby: OCR "PLAY" at FORCE_PLAY_OCR_REGION. The new
#       lobby always shows PLAY, so this does not scroll.
#     - verify the selected game: OCR "MINER TYCOON 2" at
#       FORCE_GAME_TITLE_REGION. Wrong game -> map search:
#         click the top-left search icon (up to 3 times, no scrolling),
#         click the search field, type the island code, wait for the
#         picked game-logo image, click the FIRST result tile, then PLAY.
#     - every "found -> click" step sleeps 1s first: a freshly drawn
#       button is not clickable yet.
#     - press PLAY (the same play button press as before), then wait for
#       the new in-game HUD image (MENU_RESUME_JOIN_WAIT).
#
# A 1920x1080 game-logo image is shipped. Any other resolution drops that
# default and the map search stops until the user picks their own tile.
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

# In-game check: ONE box of HUD pixels, averaged and compared to the colour
# MacroForge reports for that spot while in game. Box + colour are stored at
# the 1920x1080 reference and scaled to the live screen at runtime, exactly
# like every other region here (no resolution is saved to config).
IN_GAME_BOX_REF = (925, 34, 978, 43)     # MacroForge pick box @1920x1080
IN_GAME_RGB_REF = (214, 165, 29)         # avg colour of that box in game
IN_GAME_TOL_REF = 10.0                   # <= 10% off = in game
# Last sample, so a failed recovery can log the actual pixels it compared.
_hud_detail: dict = {}
_ocr_detail: dict = {}


def _ing_cfg(name: str, default):
    try:
        return getattr(_cfg(), name, default)
    except Exception:
        return default


def _detection_frame() -> tuple:
    """(left, top, width, height) the HUD is drawn in.

    Prefer the Fortnite client rectangle. A windowed or off-primary game
    is not the primary monitor, and scaling the 1920x1080 box by the
    monitor puts the sample on the desktop instead of the HUD. Fullscreen
    on the primary monitor is (0, 0, screen) — the same frame as before.
    Wider than 16:9 keeps the HUD in the centered 16:9 band (ultrawide).
    """
    left = top = 0
    try:
        cfgm = _cfg()
        fw = int(getattr(cfgm, "RUNTIME_WIDTH", 1920) or 1920)
        fh = int(getattr(cfgm, "RUNTIME_HEIGHT", 1080) or 1080)
    except Exception:
        fw, fh = 1920, 1080
    mode = "monitor"
    if os.name == "nt":
        try:
            from macro_runner import _find_fortnite_hwnd
            hwnd = _find_fortnite_hwnd()
            if hwnd:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                rc = wintypes.RECT()
                if user32.GetClientRect(int(hwnd), ctypes.byref(rc)):
                    cw = int(rc.right - rc.left)
                    ch = int(rc.bottom - rc.top)
                    pt = wintypes.POINT(0, 0)
                    if cw >= 800 and ch >= 600 and user32.ClientToScreen(int(hwnd), ctypes.byref(pt)):
                        left, top, fw, fh = int(pt.x), int(pt.y), cw, ch
                        mode = "window"
        except Exception as e:
            log.debug(f"[IN_GAME] window frame failed: {e}")
    aspect = fw / float(max(1, fh))
    base_aspect = 1920.0 / 1080.0
    if aspect > base_aspect * 1.04:
        # Ultrawide: the HUD stays in a centered 16:9 band, it does not
        # stretch to the side gutters. Scale by height and center X.
        sy = fh / 1080.0
        sx = sy
        content_w = 1920.0 * sx
        ox = left + (fw - content_w) / 2.0
        oy = float(top)
        fit = "center-16:9"
    elif aspect < base_aspect * 0.96:
        sx = fw / 1920.0
        sy = sx
        content_h = 1080.0 * sy
        ox = float(left)
        oy = top + (fh - content_h) / 2.0
        fit = "center-16:9"
    else:
        sx = fw / 1920.0
        sy = fh / 1080.0
        ox, oy = float(left), float(top)
        fit = "linear"
    return {
        "left": left, "top": top, "w": fw, "h": fh,
        "ox": ox, "oy": oy, "sx": sx, "sy": sy,
        "mode": mode, "fit": fit,
    }


def _map_box(ref) -> tuple:
    fr = _detection_frame()
    x1, y1, x2, y2 = (float(v) for v in ref)
    ax1 = int(round(fr["ox"] + x1 * fr["sx"]))
    ay1 = int(round(fr["oy"] + y1 * fr["sy"]))
    ax2 = int(round(fr["ox"] + x2 * fr["sx"]))
    ay2 = int(round(fr["oy"] + y2 * fr["sy"]))
    if ax2 <= ax1:
        ax2 = ax1 + 1
    if ay2 <= ay1:
        ay2 = ay1 + 1
    return (ax1, ay1, ax2, ay2)


def _map_point(ref) -> tuple:
    fr = _detection_frame()
    x = int(round(fr["ox"] + float(ref[0]) * fr["sx"]))
    y = int(round(fr["oy"] + float(ref[1]) * fr["sy"]))
    return (x, y)


def _base_region(key: str, default) -> tuple:
    try:
        cfgm = _cfg()
        base = getattr(cfgm, "_BASE_REGIONS", {}).get(key)
        if base and len(base) == 4:
            return tuple(int(v) for v in base)
    except Exception:
        pass
    return tuple(int(v) for v in default)


def _base_point(key: str, default) -> tuple:
    try:
        cfgm = _cfg()
        base = getattr(cfgm, "_BASE_POINTS", {}).get(key)
        if base and len(base) == 2:
            return tuple(int(v) for v in base)
    except Exception:
        pass
    return tuple(int(v) for v in default)


def _screen_region(key: str, default) -> tuple:
    return _map_box(_base_region(key, default))


def _screen_point(key: str, default) -> tuple:
    return _map_point(_base_point(key, default))


def _frame_text() -> str:
    fr = _detection_frame()
    return (
        f"frame={fr['w']}x{fr['h']}+{fr['left']},{fr['top']} "
        f"{fr['mode']} {fr['fit']} sx={fr['sx']:.3f} sy={fr['sy']:.3f}"
    )


def log_monitors(reason: str = "") -> None:
    """One INFO line: every monitor, and which one the Fortnite window is on."""
    parts = []
    monitors = []
    try:
        import mss
        with mss.mss() as sct:
            virt = sct.monitors[0]
            parts.append(
                f"virtual {virt['width']}x{virt['height']} at {int(virt['left'])},{int(virt['top'])}"
            )
            for i, m in enumerate(sct.monitors[1:], start=1):
                monitors.append(m)
                parts.append(
                    f"mon{i} {m['width']}x{m['height']} at {int(m['left'])},{int(m['top'])}"
                )
    except Exception as e:
        parts.append(f"mss failed ({e})")
    try:
        cfgm = _cfg()
        parts.append(
            f"runtime {int(getattr(cfgm, 'RUNTIME_WIDTH', 0))}x"
            f"{int(getattr(cfgm, 'RUNTIME_HEIGHT', 0))}"
        )
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes
            dpi = int(ctypes.windll.user32.GetDpiForSystem())
            parts.append(f"dpi={dpi} ({round(dpi * 100 / 96)}%)")
        except Exception:
            pass
    fr = _detection_frame()
    parts.append(
        f"fortnite {fr['w']}x{fr['h']} at {fr['left']},{fr['top']} "
        f"({fr['mode']}, {fr['fit']})"
    )
    cx = int(fr["left"]) + int(fr["w"]) // 2
    cy = int(fr["top"]) + int(fr["h"]) // 2
    hit = "none"
    for i, m in enumerate(monitors, start=1):
        if (int(m["left"]) <= cx < int(m["left"]) + int(m["width"])
                and int(m["top"]) <= cy < int(m["top"]) + int(m["height"])):
            hit = f"mon{i}"
            break
    parts.append(f"fortnite is on {hit}")
    tag = f" {reason}" if reason else ""
    log.info(f"[MONITOR]{tag} " + " | ".join(parts))


def in_game_check_type() -> str:
    """'image' (default, the old template) or 'pixel'."""
    raw = str(_ing_cfg("IN_GAME_CHECK_TYPE", "image") or "image").strip().lower()
    if raw in ("pixel", "pixel_check", "color", "colour"):
        return "pixel"
    return "image"


# The check that used to live in the force-restart / menu-resume macros:
# images/1920x1080_inGame.png, fixed box, 90%.
_IN_GAME_IMAGE = {
    "var": "inGame",
    "path": "images/1920x1080_inGame.png",
    "threshold": 90,
    "fixed": True,
    "base_w": 1920,
    "base_h": 1080,
    "x1": 1667,
    "y1": 663,
    "x2": 1703,
    "y2": 721,
    "search_x1": 0,
    "search_y1": 0,
    "search_x2": 1920,
    "search_y2": 1080,
    "result_mode": "bool",
}


def in_game_box() -> tuple:
    """Pixel-check box in live screen pixels.

    config.IN_GAME_CHECK_BOX is the 1920x1080 reference, scaled by the same
    runtime factors as every other region (RUNTIME_WIDTH/HEIGHT).
    """
    try:
        cfgm = _cfg()
        ref = tuple(int(round(float(v))) for v in _ing_cfg("IN_GAME_CHECK_BOX", IN_GAME_BOX_REF))[:4]
        if len(ref) != 4:
            ref = IN_GAME_BOX_REF
        w = int(getattr(cfgm, "RUNTIME_WIDTH", 1920) or 1920)
        h = int(getattr(cfgm, "RUNTIME_HEIGHT", 1080) or 1080)
        sx = float(getattr(cfgm, "REGION_SCALE_X", 1.0) or 1.0)
        sy = float(getattr(cfgm, "REGION_SCALE_Y", 1.0) or 1.0)
        return tuple(int(v) for v in cfgm._scale_region_2d(ref, w, h, sx, sy))
    except Exception as e:
        log.debug(f"[IN_GAME] box scale failed: {e}")
    return IN_GAME_BOX_REF


def in_game_average_rgba() -> tuple | None:
    """Mean RGB of the pixel-check box, or None when the grab failed."""
    try:
        from screen import grab_region
        img = grab_region(in_game_box())
        if img is None or getattr(img, "size", 0) == 0:
            return None
        px = img.reshape(-1, img.shape[2])
        mean = px.mean(axis=0)          # BGR
        return (float(mean[2]), float(mean[1]), float(mean[0]))
    except Exception as e:
        log.debug(f"[IN_GAME] colour read failed: {e}")
        return None


def _ing_target_rgb() -> list:
    try:
        return [float(v) for v in _ing_cfg("IN_GAME_CHECK_RGB", IN_GAME_RGB_REF)][:3]
    except Exception:
        return list(IN_GAME_RGB_REF)


def in_game_color_diff() -> float | None:
    """Worst per-channel deviation from the reference colour, in %."""
    got = in_game_average_rgba()
    if got is None:
        return None
    tgt = _ing_target_rgb()
    return max(abs(got[i] - tgt[i]) for i in range(3)) / 255.0 * 100.0


def _fmt_rgb(got) -> str:
    if not got:
        return "none"
    return f"({got[0]:.0f},{got[1]:.0f},{got[2]:.0f})"


def _in_game_by_image() -> bool:
    """Image check. A picture you picked wins. Otherwise the built-in
    1920x1080_inGame.png on its old fixed box."""
    try:
        import game_detect
        if game_detect.is_game_detect_set():
            res = game_detect.game_detect_result()
            score = res.get("score")
            mn = res.get("min")
            ok = bool(res.get("ok"))
            _hud_detail.clear()
            _hud_detail.update(kind="image", ok=ok, score=score, thr=mn, box=None, path="picked")
            score_s = "none" if score is None else f"{float(score):.2f}"
            line = f"[IN_GAME] image picked score={score_s} min={mn} -> {ok}"
            if ok:
                log.debug(line)
            else:
                log.info(line)
            return ok
    except Exception as e:
        log.info(f"[IN_GAME] picked image check failed: {e}")
    try:
        from macro_logic import image_match_result
        bot_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        result = image_match_result(_IN_GAME_IMAGE, bot_root)
    except Exception as e:
        log.info(f"[IN_GAME] image check failed: {e}")
        _hud_detail.clear()
        _hud_detail.update(kind="image", ok=False, error=str(e))
        return False
    score = float(result.get("score") or 0.0)
    ok = bool(result.get("matched"))
    thr = float(_IN_GAME_IMAGE["threshold"]) / 100.0
    _hud_detail.clear()
    _hud_detail.update(
        kind="image", ok=ok, score=score, thr=thr,
        box=result.get("box"), path=result.get("path") or "",
    )
    line = (
        f"[IN_GAME] image built-in score={score:.2f} thr={thr:.2f} "
        f"box={result.get('box')} -> {ok}"
    )
    if ok:
        log.debug(line)
    else:
        log.info(line)
    return ok


def _in_game_by_pixel() -> bool:
    """One HUD box, averaged against the in-game colour."""
    tol = float(_ing_cfg("IN_GAME_CHECK_TOL", IN_GAME_TOL_REF) or IN_GAME_TOL_REF)
    got = in_game_average_rgba()
    tgt = _ing_target_rgb()
    box = in_game_box()
    if got is None:
        _hud_detail.clear()
        _hud_detail.update(kind="pixel", ok=False, box=box, got=None, tgt=tuple(tgt), diff=None, tol=tol)
        log.info(f"[IN_GAME] pixel no colour read box={box} -> NOT in game")
        return False
    diff = max(abs(got[i] - tgt[i]) for i in range(3)) / 255.0 * 100.0
    ok = diff <= tol
    _hud_detail.clear()
    _hud_detail.update(kind="pixel", ok=ok, box=box, got=got, tgt=tuple(tgt), diff=diff, tol=tol)
    line = (
        f"[IN_GAME] pixel box={box} avg={_fmt_rgb(got)} want={_fmt_rgb(tgt)} "
        f"diff={diff:.1f}% tol={tol:.0f}% -> {ok}"
    )
    if ok:
        log.debug(line)
    else:
        log.info(line)
    return bool(ok)


def in_game_hud() -> bool:
    """True when the selected in-game check says we are in the match.

    Image (default) is the old 1920x1080_inGame.png match. Pixel Check is
    the colour average. Config → General → In-Game check type.
    """
    if in_game_check_type() == "pixel":
        return _in_game_by_pixel()
    return _in_game_by_image()


def _fail_detail() -> str:
    """One line: which in-game check missed, and what PLAY OCR read."""
    hud = _hud_detail or {}
    kind = hud.get("kind") or in_game_check_type()
    play = _ocr_detail.get("play_text", "")
    play_box = _ocr_detail.get("play_box")
    if kind == "pixel":
        diff = hud.get("diff")
        diff_s = "none" if diff is None else f"{diff:.1f}%"
        check = (
            f"pixel box={hud.get('box')} got={_fmt_rgb(hud.get('got'))} "
            f"want={_fmt_rgb(hud.get('tgt'))} diff={diff_s} tol={hud.get('tol')}"
        )
    else:
        score = hud.get("score")
        score_s = "none" if score is None else f"{float(score):.2f}"
        check = f"image score={score_s} thr={hud.get('thr')} box={hud.get('box')}"
    return (
        f"check={kind} {check} "
        f"play_box={play_box} play_ocr={play!r} "
        f"title_ocr={_ocr_detail.get('title_text', '')!r}"
    )


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
    region = _screen_region("FORCE_PLAY_OCR_REGION", (100, 887, 417, 942))
    text = ocr_region_text(region)
    _ocr_detail["play_text"] = text
    _ocr_detail["play_box"] = region
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
    region = _screen_region("FORCE_GAME_TITLE_REGION", (83, 665, 438, 704))
    text = ocr_region_text(region)
    _ocr_detail["title_text"] = text
    _ocr_detail["title_box"] = region
    norm = _norm(text)
    if not norm:
        return False
    return _alias_hit(norm, _aliases("FORCE_OCR_TITLE_ALIASES", "miner tycoon 2,minertycoon2,miner tycoon,miner"))


def _search_region() -> tuple:
    return _screen_region("FORCE_SEARCH_DISCOVER_REGION", (110, 168, 640, 222))


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


def _select_regions() -> list[tuple]:
    """Every place the SELECT label can be read from.

    The configured strip first (user-calibrated), then two widened bands
    around it: the island page draws SELECT larger and a few pixels away
    from the lobby button, and a fresh UI blurs the thin strip.
    """
    base = _base_region("FORCE_SELECT_OCR_REGION", (89, 898, 392, 935))
    x1, y1, x2, y2 = base
    variants = [
        (x1, y1, x2, y2),
        (x1 - 40, y1 - 70, x2 + 140, y2 + 80),
        (x1 - 40, y1 - 130, x2 + 300, y2 + 120),
    ]
    out = [_map_box(v) for v in variants]
    seen, uniq = set(), []
    for r in out:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq


def _select_text_hit(text: str) -> bool:
    """'select' plus the dropped/confused-character reads OCR returns."""
    norm = _norm(text)
    if not norm:
        return False
    if _alias_hit(norm, _aliases("FORCE_OCR_SELECT_ALIASES", "select")):
        return True
    up = re.sub(r"[^A-Z0-9]", "", str(text or "").upper())
    if not up:
        return False
    # 5ELECT / SEL3CT / SELECTT / SELCT / SLECT - the label is short and
    # lives alone in its band, so a loose shape match is safe here.
    return bool(re.search(r"[S5][E3][L1]?[E3]?[C6][T7]?[T7]?", up)) or bool(
        re.search(r"S[E3]L[A-Z0-9]{0,3}C[A-Z0-9]?T", up))


def ocr_select_visible() -> bool:
    """True when a SELECT label is readable anywhere it can appear."""
    for region in _select_regions():
        try:
            if _select_text_hit(ocr_region_text(region)):
                return True
        except Exception:
            continue
    return False


def page_state() -> str:
    """'in_game' | 'island' | 'lobby' | 'unknown' - who owns the screen.

    Order matters: the island page shows the island NAME, which reads like
    "MINER TYCOON 2" in the title region, so the in-game check and SELECT
    both have to be answered before the title is trusted.
    """
    try:
        if in_game_hud():
            return "in_game"
    except Exception:
        pass
    if ocr_select_visible():
        return "island"
    try:
        if ocr_title_mt2():
            return "lobby"
    except Exception:
        pass
    return "unknown"


def _poll_page_state(seconds: float, want: tuple = ("in_game", "island", "lobby")) -> str:
    """Poll the page state until it is one of `want` or the timeout hits."""
    deadline = time.time() + max(0.0, float(seconds))
    state = "unknown"
    while time.time() < deadline:
        if _killed():
            return "unknown"
        state = page_state()
        if state in want:
            return state
        time.sleep(0.25)
    return state


def _select_click_point() -> tuple:
    return _screen_point("FORCE_SELECT_CLICK", (238, 915))


# ───────────────────────── Input helpers ─────────────────────────

def _click(x: int, y: int) -> None:
    from teleport_menu import _click_xy
    _click_xy(int(x), int(y))


def _mouse_to_list_center() -> None:
    """Park the cursor over the lobby's scrollable list. Wheel events only
    scroll the list while the cursor hovers it — over the left margin the
    wheel does nothing (the clearing clicks leave the cursor at x0)."""
    try:
        x, y = _screen_point("FORCE_LIST_CENTER_POINT", (960, 540))
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
    fr = _detection_frame()
    x = int(fr["left"]) + 2
    y = int(fr["top"]) + int(fr["h"]) // 2
    for _ in range(3):
        _click(x, y)
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
    closed = []
    for name, skey, sdef, ckey, cdef in _GUI_CLOSE_POINTS:
        try:
            sample = _screen_point(skey, sdef)
            if _close_yellow_at(sample):
                log.info(f"[FR_FLOW] {name} GUI open — closing")
                _click(*_screen_point(ckey, cdef))
                closed.append(name)
                if not _sleep(0.30):
                    return closed
        except Exception as e:
            log.debug(f"[FR_FLOW] close {name}: {e}")
    # Manual strength window: yellow close button anywhere in its region.
    try:
        if _manual_strength_open():
            log.info("[FR_FLOW] manual strength window open — closing")
            _click(*_screen_point("MANUAL_STR_CLOSE_CENTER", (1742, 101)))
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
    log_monitors(tag or "recovery")

    if in_game_hud():
        log.info(f"{pre} state 1: in game — {_fail_detail()}")
        return "in_game"

    closed = close_all_open_guis()
    if closed:
        log.info(f"{pre} state 2: closed open GUIs {closed} — re-checking")
        if not _sleep(0.5):
            return "give_up"
        if in_game_hud():
            log.info(f"{pre} state 2: in game after closing GUIs")
            return "in_game"

    ocr_play_visible()
    ocr_title_mt2()
    log.info(f"{pre} state 3: clearly not in game — {_fail_detail()} — ESC + pause-menu probe")
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
            log.info(
                f"{pre} state 3: nothing detected — {_fail_detail()} "
                f"— 3 clear clicks + scroll up, then re-check"
            )
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
    log.warning(f"{pre} state 3: neither HUD image nor lobby menu after {total}s — {_fail_detail()} — give up")
    return "give_up"


# ───────────────────────── Lobby / menu navigation ─────────────────────────

def wait_for_menu(timeout: float = 60.0) -> bool:
    """Loop until the lobby PLAY button OCR hits.

    The Nov 2026 lobby shows PLAY without scrolling. Scrolling here used
    to walk off the menu. On detection: 3 clearing clicks on the left
    edge so nothing steals the first real click."""
    deadline = time.time() + max(0.0, float(timeout))
    log.info(f"[FR_FLOW] waiting for lobby menu (PLAY OCR, max {timeout:.0f}s, no scroll)")
    _overlay("MENU", "Looking for lobby")
    while time.time() < deadline:
        if _killed():
            return False
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
    region = _screen_region("FORCE_GAME_TITLE_REGION", (83, 665, 438, 704))
    last_text = ""
    for attempt in range(1, max(1, passes) + 1):
        if _killed():
            return "unknown"
        # The island page's own name reads "MINER TYCOON 2" in the title
        # region, so SELECT and the in-game HUD are answered BEFORE the
        # title — otherwise this returned "mt2" on the island page and the
        # PLAY click landed on nothing ("assumes it already went through").
        state = page_state()
        if state == "in_game":
            log.info("[FR_FLOW] already in game — nothing to select")
            return "mt2"
        if state == "island":
            log.info("[FR_FLOW] island page open (SELECT) — clicking SELECT, then re-checking")
            if not _sleep(1.0):
                return "unknown"
            _click(*_select_click_point())
            after = _poll_page_state(8.0)
            log.info(f"[FR_FLOW] after SELECT: page state = {after}")
            continue
        if state == "lobby":
            log.info("[FR_FLOW] selected game is Miner Tycoon 2")
            return "mt2"
        # Nothing conclusive yet — remember the raw read for the log and
        # give the freshly drawn menu a moment.
        last_text = ocr_region_text(region)
        time.sleep(0.3)
        last_text = ocr_region_text(region)
        time.sleep(0.3)
    if not last_text.strip():
        log.warning("[FR_FLOW] game title OCR unreadable — wrong-game recovery (debug crop: fr_title_missing)")
        _debug_crop("fr_title_missing", _screen_region("FORCE_GAME_TITLE_REGION", (83, 665, 438, 704)))
    else:
        log.warning(f"[FR_FLOW] selected game title OCR read \u201c{last_text.strip()}\u201d — NOT Miner Tycoon 2, wrong-game recovery (debug crop: fr_title_fail)")
        _debug_crop("fr_title_fail", region)
    return "wrong"


def _reach_search_bar() -> bool:
    """Open Discover from the lobby search icon. No scrolling.

    The icon sits at the top-left of the main menu. Click it up to 3
    times (a repeat click on an already-open search page is harmless),
    then look for the Search Discover placeholder."""
    icon = _screen_point("FORCE_SEARCH_ICON_CLICK", (112, 68))
    aliases = _aliases("FORCE_OCR_SEARCH_ALIASES", "search discover,search,discover")
    last = ""
    for n in range(1, 4):
        if _killed():
            return False
        log.info(f"[FR_FLOW] search icon click {n}/3 {tuple(int(v) for v in icon)}")
        _click(*icon)
        if not _sleep(0.7):
            return False
        last = ocr_search_discover_text()
        if _alias_hit(_norm(last), aliases):
            log.info(f"[FR_FLOW] search field open (OCR “{last.strip()}”, click {n})")
            return True
    log.warning(
        f"[FR_FLOW] search field placeholder not read after 3 icon clicks "
        f"(last OCR “{last.strip() or '<nothing>'}” in {_search_region()}) "
        "— typing into the field anyway"
    )
    _debug_crop("fr_search_missing", _search_region())
    return True


def _submit_island_search(code: str) -> bool:
    """Click the search bar, type the island code, settle, press Enter."""
    from teleport_menu import _pt
    if not _sleep(1.0):   # found -> pause before the click (freshly drawn UI is not clickable yet)
        return False
    _click(*_screen_point("FORCE_SEARCH_CLICK", (360, 194)))
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
    """Click the first result tile once.

    A correct island code puts Miner Tycoon 2 in that tile. One click
    opens it. A second click used to be required by the old billboard
    and now lands on the lobby behind the results."""
    from teleport_menu import _pt
    if not _sleep(1.0):
        return False
    xy = _screen_point("FORCE_GAME_BILLBOARD_CLICK", (220, 540))
    log.info(f"[FR_FLOW] clicking first search-result tile {tuple(int(v) for v in xy)}")
    _click(*xy)
    if not _sleep(1.5):
        return False
    return True


def _find_and_click_select() -> bool:
    """Click the island page's SELECT button, verifying what the page is.

    Three outcomes, all decided from the real page state instead of a
    guess:
      * already in game / lobby -> nothing to click, success
      * SELECT readable        -> click it, success
      * island page, SELECT not readable -> click the SELECT point anyway
        (blind), then verify - the label is famously unreadable right
        after the page draws, and scrolling up would wreck a page that is
        one click from joining
    Returns False only when the page is unreadable AND the blind click did
    not move it either.
    """
    try:
        sel_timeout = max(5, int(getattr(_cfg(), "FORCE_SELECT_TIMEOUT", 30)))
    except Exception:
        sel_timeout = 30

    state = _poll_page_state(float(sel_timeout), want=("in_game", "island", "lobby"))
    log.info(f"[FR_FLOW] after billboard: page state = {state}")

    if state in ("in_game", "lobby"):
        # The second billboard click already confirmed the join.
        log.info(f"[FR_FLOW] billboard click already joined ({state}) - skipping SELECT")
        return True

    if state == "island":
        if not _sleep(1.0):   # settle -> click
            return False
        xy = _select_click_point()
        _ocr_state = "read" if ocr_select_visible() else "unreadable"
        log.info(f"[FR_FLOW] clicking SELECT {xy} (OCR {_ocr_state} — clicking anyway)")
        _click(*xy)
        after = _poll_page_state(10.0, want=("in_game", "lobby"))
        log.info(f"[FR_FLOW] after SELECT click: page state = {after}")
        if after in ("in_game", "lobby"):
            return True
        # Still on the island page -> one more click, then let the caller
        # decide from the verified state.
        if page_state() == "island":
            log.warning("[FR_FLOW] still on the island page after SELECT - clicking again")
            _click(*xy)
            after = _poll_page_state(10.0, want=("in_game", "lobby"))
            log.info(f"[FR_FLOW] second SELECT click: page state = {after}")
            return after in ("in_game", "lobby")
        return False

    log.warning("[FR_FLOW] page state unknown after clicking the billboard (debug crops: fr_select_missing)")
    _debug_crop("fr_select_missing", tuple(int(v) for v in getattr(
        _cfg(), "FORCE_SELECT_OCR_REGION", (89, 898, 392, 935))))
    # Last resort: the blind click is cheap compared with a full retry that
    # scrolls away a possibly open island page.
    if not _sleep(0.5):
        return False
    _click(*_select_click_point())
    after = _poll_page_state(8.0, want=("in_game", "lobby"))
    log.info(f"[FR_FLOW] blind SELECT click: page state = {after}")
    return after in ("in_game", "lobby")


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
        # A join that already started is a success - the title is gone by
        # then and waiting for it only manufactured false failures.
        if in_game_hud():
            log.info("[FR_FLOW] map search done - already joining the game")
            return True
        if ocr_title_mt2():
            log.info("[FR_FLOW] map search done — Miner Tycoon 2 selected again")
            return True
        time.sleep(0.3)
    log.warning("[FR_FLOW] title did not read Miner Tycoon 2 after SELECT (page state: %s)" % page_state())
    return False


def map_search_flow() -> bool:
    """Drifted onto another game: search the MT2 island and select it.

    Careful by design — nothing here hard-fails on the first miss:
      * each step has 0.5-1s settle pauses (freshly drawn UI eats fast clicks)
      * the billboard takes TWO clicks: first selects, second confirms
      * if the search comes up empty, the flow clicks the search icon
        again and retypes (up to FORCE_MAP_SEARCH_ATTEMPTS). No scrolling."""
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
            if page_state() in ("island", "in_game"):
                log.info(f"[FR_FLOW] map search attempt {attempt}/{attempts}: page state {page_state()} - confirming the selection instead of scrolling")
                if not _find_and_click_select():
                    return False
                if _verify_title_mt2():
                    return True
            # Previous attempt found nothing. The next pass clicks the
            # search icon again and retypes. Do not scroll — the new
            # lobby search is not a list you scroll to.
            log.info(f"[FR_FLOW] map search attempt {attempt}/{attempts}: reopening search (no scroll)")
            if not _sleep(0.4):
                return False

        ok = (_reach_search_bar()
              and _submit_island_search(code)
              and _wait_for_billboard(timeout)
              and _click_billboard_select_confirm()
              and _find_and_click_select()
              and _verify_title_mt2())   # accepts a join that already started
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
    play_xy = _screen_point("FORCE_READY_CLICK", (255, 910))
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
