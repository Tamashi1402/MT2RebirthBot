# Game Detection — user-picked "proof we're in the MT2 map" image check.
#
# The user picks a small always-visible HUD element (Miner Tycoon 2 logo,
# stone icon, shard icon...) once via the dashboard's Force Restart tab
# (same F2 pipette picker as MacroForge: drag a box on a screenshot, the
# crop + its pick box/point are saved — box/point embedded in the PNG as
# an mfmeta tEXt chunk by macro_engine.image_meta).
#
# At runtime we grab the live screen at the picked box (scaled from the
# pick resolution to the live resolution) and compare it against the
# template with a mean absolute-difference score:
#
#     diff% = mean(|live - template|) / 255 * 100
#
# diff% <= GAME_DETECT_DIFF (default 5%)  ->  we are looking at the same
# game HUD -> "in game". Anything bigger (menu, loading screen, wrong
# creative map) counts as NOT in game, which the recovery flow treats as
# a run failure / force-restart trigger.
#
# No default image is shipped: the check is only active once the user
# picks one. Force Restart refuses to start while it is missing.
from __future__ import annotations

import os

from logger import get_logger

log = get_logger()


def _bot_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def game_detect_dir() -> str:
    """Folder the picked templates live in (data/game_detect)."""
    return os.path.join(_bot_root(), "data", "game_detect")


# Two user-picked templates share this module's pick/persist machinery:
#   "in_game"   — always-visible HUD element: proof we are in the MT2 map
#                (Force Restart -> Game Detection)
#   "game_logo" — the Miner Tycoon 2 billboard in the map-search results
#                (Force Restart -> Wrong Game / Map Search). No default:
#                when the bot drifts to another game and the logo is not
#                picked, the map search cannot finish and the bot stops.
_SPECS = {
    "in_game": {
        "cfg_image": "GAME_DETECT_IMAGE",
        "cfg_box": "GAME_DETECT_BOX",
        "cfg_screen": "GAME_DETECT_SCREEN",
        "file": "game_detect.png",
    },
    "game_logo": {
        "cfg_image": "FORCE_GAME_LOGO_IMAGE",
        "cfg_box": "FORCE_GAME_LOGO_BOX",
        "cfg_screen": "FORCE_GAME_LOGO_SCREEN",
        "file": "game_logo.png",
    },
}


def _spec(tmpl: str) -> dict:
    return _SPECS.get(str(tmpl or "in_game").strip().lower() or "in_game", _SPECS["in_game"])


def _cfg():
    import config as _config
    return _config


def _image_path(tmpl: str) -> str | None:
    """Absolute path of the picked template, or None when not set/missing."""
    spec = _spec(tmpl)
    try:
        name = str(getattr(_cfg(), spec["cfg_image"], "") or "").strip()
    except Exception:
        return None
    if not name:
        return None
    # Only a bare filename is ever expected — refuse anything that escapes
    # the game_detect dir (no ../, no absolute paths).
    base = os.path.basename(name.replace("\\", "/"))
    if not base:
        return None
    path = os.path.join(game_detect_dir(), base)
    return path if os.path.isfile(path) else None


def game_detect_image_path(tmpl: str = "in_game") -> str | None:
    return _image_path(tmpl)


def game_logo_image_path() -> str | None:
    return _image_path("game_logo")


def _meta_from_config(tmpl: str) -> dict | None:
    spec = _spec(tmpl)
    try:
        cfg = _cfg()
        box = getattr(cfg, spec["cfg_box"], None)
        screen = getattr(cfg, spec["cfg_screen"], None)
    except Exception:
        return None
    if isinstance(box, (list, tuple)) and len(box) == 4:
        try:
            box = [int(round(float(v))) for v in box]
            if box[2] > box[0] and box[3] > box[1]:
                meta = {"box": box, "point": [box[0], box[1]]}
                if isinstance(screen, (list, tuple)) and len(screen) >= 2:
                    try:
                        meta["screen"] = [int(screen[0]), int(screen[1])]
                    except Exception:
                        pass
                return meta
        except (TypeError, ValueError):
            pass
    return None


def _meta(tmpl: str) -> dict | None:
    """Pick metadata {box, point, screen} — PNG mfmeta first, config fallback."""
    path = _image_path(tmpl)
    if path:
        try:
            from macro_engine.image_meta import read_meta
            meta = read_meta(path)
            if meta and isinstance(meta.get("box"), (list, tuple)) and len(meta["box"]) == 4:
                return meta
        except Exception as e:
            log.debug(f"[GAME_DETECT] png meta read failed: {e}")
    return _meta_from_config(tmpl)


def game_detect_meta(tmpl: str = "in_game") -> dict | None:
    return _meta(tmpl)


def game_logo_meta() -> dict | None:
    return _meta("game_logo")


def _is_set(tmpl: str) -> bool:
    return bool(_image_path(tmpl) and _meta(tmpl))


def is_game_detect_set() -> bool:
    """True when the in-game template AND its pick box are available."""
    return _is_set("in_game")


def is_game_logo_set() -> bool:
    """True when the map-search game-logo template AND its box are available."""
    return _is_set("game_logo")


def diff_threshold_pct() -> float:
    """Configured difference tolerance in % (default 5)."""
    try:
        val = float(getattr(_cfg(), "GAME_DETECT_DIFF", 5.0))
    except Exception:
        val = 5.0
    return min(100.0, max(0.0, val))


def _live_screen_size() -> tuple[int, int]:
    try:
        cfg = _cfg()
        return int(cfg.RUNTIME_WIDTH), int(cfg.RUNTIME_HEIGHT)
    except Exception:
        try:
            from screen import _screen_size
            return _screen_size()
        except Exception:
            return 1920, 1080


def game_detect_diff_pct() -> float | None:
    """Mean abs-difference between live region and template, in % (0-100).

    None when the check cannot run (not set, capture failed, template
    unreadable). Callers treat None as "unknown" — never as "in game".
    """
    import cv2
    import numpy as np

    path = _image_path("in_game")
    meta = _meta("in_game")
    if not path or not meta:
        return None
    try:
        x1, y1, x2, y2 = (int(v) for v in meta["box"])
    except Exception:
        return None
    if x2 - x1 < 1 or y2 - y1 < 1:
        return None

    # Scale the pick box from the pick-time screen to the live screen.
    pick_screen = meta.get("screen") or []
    sx = sy = 1.0
    if isinstance(pick_screen, (list, tuple)) and len(pick_screen) >= 2:
        try:
            pw, ph = int(pick_screen[0]), int(pick_screen[1])
            lw, lh = _live_screen_size()
            if pw > 0 and ph > 0 and (pw != lw or ph != lh):
                sx, sy = lw / pw, lh / ph
                x1, y1 = int(round(x1 * sx)), int(round(y1 * sy))
                x2, y2 = int(round(x2 * sx)), int(round(y2 * sy))
        except Exception:
            sx = sy = 1.0
    if x2 - x1 < 1 or y2 - y1 < 1:
        return None

    template = cv2.imread(path)
    if template is None:
        log.warning(f"[GAME_DETECT] template unreadable: {path}")
        return None
    tw, th = template.shape[1], template.shape[0]
    if tw != (x2 - x1) or th != (y2 - y1):
        # Pick-time size differs from the live-scaled box (resolution
        # changed since the pick) — rescale the template to compare 1:1.
        template = cv2.resize(template, (x2 - x1, y2 - y1), interpolation=cv2.INTER_AREA)

    try:
        from screen import grab_region
        live = grab_region((x1, y1, x2, y2))
    except Exception as e:
        log.warning(f"[GAME_DETECT] live grab failed: {e}")
        return None
    if live is None or live.size == 0:
        return None
    lh_, lw_ = live.shape[:2]
    if (lw_, lh_) != (x2 - x1, y2 - y1):
        # mss clamps at screen edges — compare the overlapping area only
        w = min(lw_, x2 - x1, tw)
        h = min(lh_, y2 - y1, th)
        live = live[0:h, 0:w]
        template = template[0:h, 0:w]

    diff = cv2.absdiff(live.astype(np.float32), template.astype(np.float32))
    return float(diff.mean()) / 255.0 * 100.0


def game_detect_result() -> dict:
    """Full result for logging / dashboard: {set, diff, threshold, ok}.

    ok is True when the check is active AND the live HUD matches.
    ok is None when the check is not active (nothing picked) so callers
    can fall back to their legacy behavior.
    """
    if not is_game_detect_set():
        return {"set": False, "diff": None, "threshold": diff_threshold_pct(), "ok": None}
    diff = game_detect_diff_pct()
    thresh = diff_threshold_pct()
    ok = None if diff is None else bool(diff <= thresh)
    return {"set": True, "diff": diff, "threshold": thresh, "ok": ok}


def is_in_game_by_detection() -> bool:
    """Simple gate: True only when active and matching.

    Not set -> False here (callers decide their own fallback); use
    game_detect_result()['ok'] when the tri-state matters.
    """
    res = game_detect_result()
    return bool(res["ok"])


def _clear(tmpl: str) -> bool:
    """Remove the picked image + reset config keys (dashboard Clear button)."""
    spec = _spec(tmpl)
    # capture the path BEFORE the config reset — _image_path() reads the
    # image key, which is about to become empty.
    path = _image_path(tmpl)
    try:
        cfg = _cfg()
        setattr(cfg, spec["cfg_image"], "")
        setattr(cfg, spec["cfg_box"], [])
        setattr(cfg, spec["cfg_screen"], [])
        cfg.save_values({
            spec["cfg_image"]: "",
            spec["cfg_box"]: [],
            spec["cfg_screen"]: [],
        })
    except Exception as e:
        log.warning(f"[GAME_DETECT] config clear failed: {e}")
    if path:
        try:
            os.remove(path)
        except OSError as e:
            log.warning(f"[GAME_DETECT] could not delete {path}: {e}")
    log.info(f"[GAME_DETECT] cleared ({tmpl})")
    return True


def clear_game_detect() -> bool:
    return _clear("in_game")


def clear_game_logo() -> bool:
    return _clear("game_logo")


def save_pick(path: str, box: list, screen: list, tmpl: str = "in_game") -> None:
    """Persist a fresh pick (called by the dashboard crop flow)."""
    spec = _spec(tmpl)
    try:
        cfg = _cfg()
        setattr(cfg, spec["cfg_image"], os.path.basename(str(path)))
        setattr(cfg, spec["cfg_box"], [int(round(float(v))) for v in box])
        setattr(cfg, spec["cfg_screen"], [int(v) for v in (screen or [])][:2])
        cfg.save_values({
            spec["cfg_image"]: getattr(cfg, spec["cfg_image"]),
            spec["cfg_box"]: getattr(cfg, spec["cfg_box"]),
            spec["cfg_screen"]: getattr(cfg, spec["cfg_screen"]),
        })
    except Exception as e:
        log.warning(f"[GAME_DETECT] save_pick failed ({tmpl}): {e}")


_GAME_LOGO_MATCH_MIN = 0.80   # template-match score floor for the billboard


def game_logo_result() -> dict:
    """Map-search billboard check: {set, score, ok}.

    Template match (TM_CCOEFF_NORMED) of the picked logo against the live
    picked box. ok is True when set and score >= 0.80. Not picked -> ok None
    (the map-search flow then stops the bot with a clear error)."""
    import cv2
    import numpy as np

    if not _is_set("game_logo"):
        return {"set": False, "score": None, "ok": None}
    path = _image_path("game_logo")
    meta = _meta("game_logo")
    try:
        x1, y1, x2, y2 = (int(v) for v in meta["box"])
    except Exception:
        return {"set": True, "score": None, "ok": None}
    pick_screen = meta.get("screen") or []
    sx = sy = 1.0
    if isinstance(pick_screen, (list, tuple)) and len(pick_screen) >= 2:
        try:
            pw, ph = int(pick_screen[0]), int(pick_screen[1])
            lw, lh = _live_screen_size()
            if pw > 0 and ph > 0 and (pw != lw or ph != lh):
                sx, sy = lw / pw, lh / ph
                x1, y1 = int(round(x1 * sx)), int(round(y1 * sy))
                x2, y2 = int(round(x2 * sx)), int(round(y2 * sy))
        except Exception:
            sx = sy = 1.0
    if x2 - x1 < 2 or y2 - y1 < 2:
        return {"set": True, "score": None, "ok": None}
    template = cv2.imread(path)
    if template is None:
        log.warning(f"[GAME_DETECT] game logo unreadable: {path}")
        return {"set": True, "score": None, "ok": None}
    template = cv2.resize(template, (x2 - x1, y2 - y1), interpolation=cv2.INTER_AREA)
    try:
        from screen import grab_region
        live = grab_region((x1, y1, x2, y2))
    except Exception as e:
        log.warning(f"[GAME_DETECT] game logo grab failed: {e}")
        return {"set": True, "score": None, "ok": None}
    if live is None or live.size == 0:
        return {"set": True, "score": None, "ok": None}
    lh_, lw_ = live.shape[:2]
    if (lw_, lh_) != (x2 - x1, y2 - y1):
        w = min(lw_, x2 - x1)
        h = min(lh_, y2 - y1)
        if w < 2 or h < 2:
            return {"set": True, "score": None, "ok": None}
        live = live[0:h, 0:w]
        template = template[0:h, 0:w]
    try:
        score = float(cv2.matchTemplate(
            live.astype(np.float32), template.astype(np.float32), cv2.TM_CCOEFF_NORMED
        ).max())
    except Exception as e:
        log.debug(f"[GAME_DETECT] logo match failed: {e}")
        return {"set": True, "score": None, "ok": None}
    ok = bool(score >= _GAME_LOGO_MATCH_MIN)
    log.debug(f"[GAME_DETECT] logo score={score:.3f} min={_GAME_LOGO_MATCH_MIN} ok={ok}")
    return {"set": True, "score": score, "ok": ok}


def meta_json_for_dashboard() -> dict | None:
    """Best-effort meta for the info endpoint (never raises)."""
    try:
        return game_detect_meta()
    except Exception:
        return None
