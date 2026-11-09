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
# The live "are we in game" check does not use this template —
# fr_flow.in_game_hud() averages one HUD box. This module stores the
# map-search billboard (game_logo). A 1920x1080 logo is shipped as the
# default. Any other live resolution drops that default so the user
# picks their own. A logo the user picked themselves is left alone.
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
#   "game_logo" — the Miner Tycoon 2 tile in the map-search results
#                (Force Restart -> Wrong Game / Map Search). Shipped
#                default is 1920x1080 only.
_SPECS = {
    "in_game": {
        "cfg_image": "GAME_DETECT_IMAGE",
        "cfg_box": "GAME_DETECT_BOX",
        "file": "game_detect.png",
    },
    "game_logo": {
        "cfg_image": "FORCE_GAME_LOGO_IMAGE",
        "cfg_box": "FORCE_GAME_LOGO_BOX",
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


def _pick_screen_from_name(tmpl: str) -> list[int]:
    """Pick-time screen, read from the crop filename (MacroForge method).

    The picker saves crops as ``{w}x{h}_f2_<HHMMSS>.png`` — the size prefix
    IS the screen the box was dragged on. Nothing is stored in config, so a
    resolution/ratio change can never leave a stale [w,h] behind: the scale
    is recomputed at runtime from the file itself.
    """
    try:
        name = os.path.basename(str(getattr(_cfg(), _spec(tmpl)["cfg_image"], "") or ""))
    except Exception:
        return []
    head = name.split("_", 1)[0]
    if "x" not in head:
        return []
    try:
        w_s, h_s = head.split("x", 1)
        w, h = int(w_s), int(h_s)
    except (TypeError, ValueError):
        return []
    return [w, h] if w > 0 and h > 0 else []


def _meta_from_config(tmpl: str) -> dict | None:
    """Legacy fallback: box from config + pick screen from the image name."""
    spec = _spec(tmpl)
    try:
        box = getattr(_cfg(), spec["cfg_box"], None)
    except Exception:
        return None
    if isinstance(box, (list, tuple)) and len(box) == 4:
        try:
            box = [int(round(float(v))) for v in box]
            if box[2] > box[0] and box[3] > box[1]:
                meta = {"box": box, "point": [box[0], box[1]]}
                screen = _pick_screen_from_name(tmpl)
                if screen:
                    meta["screen"] = screen
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
    if tmpl == "game_logo":
        enforce_default_logo_for_resolution()
    elif tmpl == "in_game":
        enforce_default_ingame_for_resolution()
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


# Shipped map-search logo. The crop is the first-tile artwork at 1920x1080,
# box [83, 474, 225, 589]. game_logo_1080.png is the copy we never delete.
_DEFAULT_LOGO_BOX = [83, 474, 225, 589]
_DEFAULT_LOGO_SCREEN = (1920, 1080)
_DEFAULT_LOGO_NAME = "game_logo.png"
_DEFAULT_LOGO_KEEP = "game_logo_1080.png"
_default_logo_gate_logged = False


def _logo_png_meta(path: str) -> dict | None:
    try:
        from macro_engine.image_meta import read_meta
        meta = read_meta(path)
        return meta if isinstance(meta, dict) else None
    except Exception:
        return None


def _is_shipped_logo(path: str) -> bool:
    """True only for the file we shipped, never for a user pick."""
    if not path or not os.path.isfile(path):
        return False
    meta = _logo_png_meta(path)
    if meta and meta.get("default_1080"):
        return True
    keep = os.path.join(game_detect_dir(), _DEFAULT_LOGO_KEEP)
    try:
        if os.path.isfile(keep) and os.path.getsize(keep) == os.path.getsize(path):
            with open(keep, "rb") as a, open(path, "rb") as b:
                return a.read() == b.read()
    except OSError:
        return False
    return False


def _config_logo_is_default() -> bool:
    try:
        cfg = _cfg()
        name = os.path.basename(str(getattr(cfg, "FORCE_GAME_LOGO_IMAGE", "") or "").replace("\\", "/"))
        box = getattr(cfg, "FORCE_GAME_LOGO_BOX", None) or []
        box_i = [int(v) for v in box]
    except Exception:
        return False
    return name == _DEFAULT_LOGO_NAME and box_i == _DEFAULT_LOGO_BOX


def _skip_default_logo() -> bool:
    try:
        return bool(getattr(_cfg(), "FORCE_GAME_LOGO_SKIP_DEFAULT", False))
    except Exception:
        return False


def _write_logo_config(image: str, box: list, skip: bool | None = None) -> None:
    try:
        cfg = _cfg()
        cfg.FORCE_GAME_LOGO_IMAGE = image
        cfg.FORCE_GAME_LOGO_BOX = list(box)
        updates = {
            "FORCE_GAME_LOGO_IMAGE": image,
            "FORCE_GAME_LOGO_BOX": list(box),
        }
        if skip is not None:
            cfg.FORCE_GAME_LOGO_SKIP_DEFAULT = bool(skip)
            updates["FORCE_GAME_LOGO_SKIP_DEFAULT"] = bool(skip)
        cfg.save_values(updates)
    except Exception as e:
        log.warning(f"[GAME_DETECT] default logo config write failed: {e}")


def enforce_default_logo_for_resolution() -> None:
    """Keep the shipped logo only at 1920x1080. Any other size drops it.

    A logo the user picked (different file bytes, no default_1080 flag)
    is never removed. Clearing the logo from the dashboard opts out of
    the default coming back on the next full-HD launch.
    """
    global _default_logo_gate_logged
    folder = game_detect_dir()
    active = os.path.join(folder, _DEFAULT_LOGO_NAME)
    keep = os.path.join(folder, _DEFAULT_LOGO_KEEP)
    lw, lh = _live_screen_size()
    fhd = (int(lw), int(lh)) == _DEFAULT_LOGO_SCREEN
    shipped = _is_shipped_logo(active)
    config_default = _config_logo_is_default()

    if fhd:
        if _skip_default_logo():
            return
        # Already using it, or the user picked something else.
        if shipped and config_default:
            return
        if not config_default and str(getattr(_cfg(), "FORCE_GAME_LOGO_IMAGE", "") or "").strip():
            return
        if os.path.isfile(active) and not shipped:
            return
        src = keep if os.path.isfile(keep) else ""
        if not src:
            return
        try:
            os.makedirs(folder, exist_ok=True)
            if os.path.abspath(src) != os.path.abspath(active):
                import shutil
                shutil.copyfile(src, active)
        except OSError as e:
            log.warning(f"[GAME_DETECT] could not install default logo: {e}")
            return
        if not config_default:
            _write_logo_config(_DEFAULT_LOGO_NAME, list(_DEFAULT_LOGO_BOX))
            log.info("[GAME_DETECT] using the shipped 1920x1080 game logo")
        return

    if not (shipped or config_default):
        return
    if not _default_logo_gate_logged:
        _default_logo_gate_logged = True
        log.warning(
            f"[GAME_DETECT] shipped game logo is 1920x1080 only "
            f"(this screen is {lw}x{lh}) — removed, pick your own"
        )
    _write_logo_config("", [])
    if shipped:
        try:
            os.remove(active)
        except OSError as e:
            log.warning(f"[GAME_DETECT] could not remove default logo: {e}")


# Shipped in-game HUD mark (the MINER TYCOON wordmark) at 1920x1080.
# Box [925, 18, 997, 43]. game_detect_1080.png is the copy we never delete.
_DEFAULT_INGAME_BOX = [925, 18, 997, 43]
_DEFAULT_INGAME_SCREEN = (1920, 1080)
_DEFAULT_INGAME_NAME = "game_detect.png"
_DEFAULT_INGAME_KEEP = "game_detect_1080.png"
_default_ingame_gate_logged = False
_IN_GAME_MATCH_MIN = 0.80


def _is_shipped_ingame(path: str) -> bool:
    """True only for the file we shipped, never for a user pick."""
    if not path or not os.path.isfile(path):
        return False
    meta = _logo_png_meta(path)
    if meta and meta.get("default_1080") and list(meta.get("box") or []) == _DEFAULT_INGAME_BOX:
        return True
    keep = os.path.join(game_detect_dir(), _DEFAULT_INGAME_KEEP)
    try:
        if os.path.isfile(keep) and os.path.getsize(keep) == os.path.getsize(path):
            with open(keep, "rb") as a, open(path, "rb") as b:
                return a.read() == b.read()
    except OSError:
        return False
    return False


def _config_ingame_is_default() -> bool:
    try:
        cfg = _cfg()
        name = os.path.basename(str(getattr(cfg, "GAME_DETECT_IMAGE", "") or "").replace("\\", "/"))
        box = getattr(cfg, "GAME_DETECT_BOX", None) or []
        box_i = [int(v) for v in box]
    except Exception:
        return False
    return name == _DEFAULT_INGAME_NAME and box_i == _DEFAULT_INGAME_BOX


def _write_ingame_config(image: str, box: list) -> None:
    try:
        cfg = _cfg()
        cfg.GAME_DETECT_IMAGE = image
        cfg.GAME_DETECT_BOX = list(box)
        cfg.save_values({
            "GAME_DETECT_IMAGE": image,
            "GAME_DETECT_BOX": list(box),
        })
    except Exception as e:
        log.warning(f"[GAME_DETECT] default in-game image config write failed: {e}")


def enforce_default_ingame_for_resolution() -> None:
    """Keep the shipped HUD image only at 1920x1080. Any other size drops it.

    A picture the user picked (different bytes, not the default flag) is
    never removed. Clearing on a 1080p screen puts this default back.
    """
    global _default_ingame_gate_logged
    folder = game_detect_dir()
    active = os.path.join(folder, _DEFAULT_INGAME_NAME)
    keep = os.path.join(folder, _DEFAULT_INGAME_KEEP)
    lw, lh = _live_screen_size()
    fhd = (int(lw), int(lh)) == _DEFAULT_INGAME_SCREEN
    shipped = _is_shipped_ingame(active)
    config_default = _config_ingame_is_default()

    if fhd:
        if shipped and config_default:
            return
        if not config_default and str(getattr(_cfg(), "GAME_DETECT_IMAGE", "") or "").strip():
            return
        if os.path.isfile(active) and not shipped:
            return
        if not os.path.isfile(keep):
            return
        try:
            os.makedirs(folder, exist_ok=True)
            if os.path.abspath(keep) != os.path.abspath(active):
                import shutil
                shutil.copyfile(keep, active)
        except OSError as e:
            log.warning(f"[GAME_DETECT] could not install default in-game image: {e}")
            return
        if not config_default:
            _write_ingame_config(_DEFAULT_INGAME_NAME, list(_DEFAULT_INGAME_BOX))
            log.info("[GAME_DETECT] using the shipped 1920x1080 in-game image")
        return

    if not (shipped or config_default):
        return
    if not _default_ingame_gate_logged:
        _default_ingame_gate_logged = True
        log.warning(
            f"[GAME_DETECT] shipped in-game image is 1920x1080 only "
            f"(this screen is {lw}x{lh}) — removed, pick your own"
        )
    _write_ingame_config("", [])
    if shipped:
        try:
            os.remove(active)
        except OSError as e:
            log.warning(f"[GAME_DETECT] could not remove default in-game image: {e}")


def _match_score(tmpl: str, pad: int = 0) -> float | None:
    """TM_CCOEFF_NORMED of the template against its live box.

    Same compare the map-search logo uses. pad > 0 slides a few pixels
    and keeps the best hit, so a 1px HUD nudge is not a miss.
    """
    import cv2
    import numpy as np

    path = _image_path(tmpl)
    meta = _meta(tmpl)
    if not path or not meta:
        return None
    try:
        x1, y1, x2, y2 = (int(v) for v in meta["box"])
    except Exception:
        return None
    pick_screen = meta.get("screen") or []
    if isinstance(pick_screen, (list, tuple)) and len(pick_screen) >= 2:
        try:
            pw, ph = int(pick_screen[0]), int(pick_screen[1])
            lw, lh = _live_screen_size()
            if pw > 0 and ph > 0 and (pw != lw or ph != lh):
                sx, sy = lw / float(pw), lh / float(ph)
                x1, y1 = int(round(x1 * sx)), int(round(y1 * sy))
                x2, y2 = int(round(x2 * sx)), int(round(y2 * sy))
        except Exception:
            pass
    bw, bh = x2 - x1, y2 - y1
    if bw < 2 or bh < 2:
        return None
    template = cv2.imread(path)
    if template is None:
        log.warning(f"[GAME_DETECT] template unreadable: {path}")
        return None
    template = cv2.resize(template, (bw, bh), interpolation=cv2.INTER_AREA)
    lw, lh = _live_screen_size()
    gx1, gy1 = max(0, x1 - pad), max(0, y1 - pad)
    gx2, gy2 = min(int(lw), x2 + pad), min(int(lh), y2 + pad)
    if gx2 - gx1 < bw or gy2 - gy1 < bh:
        gx1, gy1, gx2, gy2 = x1, y1, x2, y2
    try:
        from screen import grab_region
        live = grab_region((gx1, gy1, gx2, gy2))
    except Exception as e:
        log.warning(f"[GAME_DETECT] live grab failed: {e}")
        return None
    if live is None or getattr(live, "size", 0) == 0:
        return None
    if live.shape[0] < bh or live.shape[1] < bw:
        return None
    try:
        score = float(cv2.matchTemplate(
            live.astype(np.float32), template.astype(np.float32), cv2.TM_CCOEFF_NORMED
        ).max())
    except Exception as e:
        log.debug(f"[GAME_DETECT] match failed: {e}")
        return None
    if score != score:
        return None
    return max(0.0, min(1.0, score))


def game_detect_diff_pct() -> float | None:
    """(1 - match score) * 100, using the logo's template match. None if it cannot run."""
    score = _match_score("in_game", pad=4)
    if score is None:
        return None
    return (1.0 - score) * 100.0


def game_detect_result() -> dict:
    """{set, score, min, ok}. Same template match as the map logo.

    4px of slack because this crop is only 72x25. Not set -> ok None.
    """
    if not is_game_detect_set():
        return {"set": False, "score": None, "min": _IN_GAME_MATCH_MIN, "ok": None}
    score = _match_score("in_game", pad=4)
    ok = None if score is None else bool(score >= _IN_GAME_MATCH_MIN)
    return {
        "set": True,
        "score": score,
        "min": _IN_GAME_MATCH_MIN,
        "diff": None if score is None else (1.0 - score) * 100.0,
        "threshold": (1.0 - _IN_GAME_MATCH_MIN) * 100.0,
        "ok": ok,
    }


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
        updates = {
            spec["cfg_image"]: "",
            spec["cfg_box"]: [],
        }
        # A manual clear opts out of the shipped 1080p logo coming back.
        if tmpl == "game_logo":
            cfg.FORCE_GAME_LOGO_SKIP_DEFAULT = True
            updates["FORCE_GAME_LOGO_SKIP_DEFAULT"] = True
        cfg.save_values(updates)
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
    ok = _clear("in_game")
    # Clear means "back to the built-in picture", which on 1080p is the
    # shipped wordmark. Other resolutions stay empty.
    enforce_default_ingame_for_resolution()
    return ok


def clear_game_logo() -> bool:
    return _clear("game_logo")


def save_pick(path: str, box: list, screen: list, tmpl: str = "in_game") -> None:
    """Persist a fresh pick (called by the dashboard crop flow)."""
    spec = _spec(tmpl)
    try:
        cfg = _cfg()
        setattr(cfg, spec["cfg_image"], os.path.basename(str(path)))
        setattr(cfg, spec["cfg_box"], [int(round(float(v))) for v in box])
        # NOTE: the pick-time screen is NOT stored. The crop filename carries
        # it ({w}x{h}_f2_*.png) and scaling happens at runtime, so a
        # resolution/ratio change never leaves a stale value behind.
        cfg.save_values({
            spec["cfg_image"]: getattr(cfg, spec["cfg_image"]),
            spec["cfg_box"]: getattr(cfg, spec["cfg_box"]),
        })
    except Exception as e:
        log.warning(f"[GAME_DETECT] save_pick failed ({tmpl}): {e}")


_GAME_LOGO_MATCH_MIN = 0.40   # template-match score floor for the billboard (0.80 before: display-off captures score ~0.5, so blind runs can never pass 0.80)


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
