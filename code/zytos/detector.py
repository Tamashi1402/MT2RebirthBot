# ============================================================
# ZYTOS - detection (own OCR / health-bar / CLOSE / JOIN)
# Does not call delve or kraken helpers.
# ============================================================
from logger import get_logger

log = get_logger()


def _cfg():
    import config as _c
    return _c


def read_ui_text(region: tuple[int, int, int, int]) -> str:
    """OCR a UI region. Zytos-owned copy (not _delve_read_ui_text)."""
    try:
        import cv2
        import pytesseract
        from screen import grab_region, ensure_tesseract
        ensure_tesseract()
        img = grab_region(region)
        up = cv2.resize(img, None, fx=2.4, fy=2.4, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        raw = pytesseract.image_to_string(
            thresh,
            config="--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )
        return (raw or "").strip().upper()
    except Exception as e:
        log.debug(f"[ZYTOS] OCR failed: {e}")
        return ""


def close_visible() -> bool:
    try:
        import cv2
        import numpy as np
        from screen import grab_region
        cfg = _cfg()
        img = grab_region(getattr(cfg, "ZYTOS_CLOSE_REGION"))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(
            hsv,
            np.array([18, 65, 100], dtype=np.uint8),  # widened for semi-transparent close button
            np.array([45, 255, 255], dtype=np.uint8),
        )
        pct = float(np.count_nonzero(yellow)) / float(max(1, yellow.size))
        text = read_ui_text(getattr(cfg, "ZYTOS_CLOSE_REGION"))
        ok = pct >= 0.30 or "CLOSE" in text or "CLOS" in text
        log.debug(f"[ZYTOS] close check yellow={pct:.1%} text={text!r} ok={ok}")
        return ok
    except Exception as e:
        log.debug(f"[ZYTOS] close detection failed: {e}")
        return False


def join_visible() -> bool:
    cfg = _cfg()
    text = read_ui_text(getattr(cfg, "ZYTOS_JOIN_REGION"))
    ok = "JOIN" in text or "JOI" in text
    log.debug(f"[ZYTOS] join OCR text={text!r} ok={ok}")
    return ok


def health_bar_seen() -> bool:
    """True only for a horizontal Zytos health-bar fill, not UI color noise."""
    try:
        import cv2
        import numpy as np
        from screen import grab_region, _save_debug
        cfg = _cfg()
        img = grab_region(cfg.ZYTOS_HEALTH_BAR_REGION)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red1 = cv2.inRange(hsv, np.array([0, 70, 80], dtype=np.uint8), np.array([14, 255, 255], dtype=np.uint8))
        red2 = cv2.inRange(hsv, np.array([170, 70, 80], dtype=np.uint8), np.array([179, 255, 255], dtype=np.uint8))
        orange = cv2.inRange(hsv, np.array([15, 80, 90], dtype=np.uint8), np.array([28, 255, 255], dtype=np.uint8))
        mask = cv2.bitwise_or(cv2.bitwise_or(red1, red2), orange)
        pct = float(np.count_nonzero(mask)) / float(max(1, mask.size))
        components, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        min_span = max(24, int(mask.shape[1] * 0.035))
        longest_span = 0
        for index in range(1, components):
            x, y, width, height, area = (int(v) for v in stats[index])
            if height >= 2 and area >= max(20, min_span):
                longest_span = max(longest_span, width)
        seen = (
            pct >= float(getattr(cfg, "ZYTOS_HEALTH_BAR_SEEN_THRESH", 0.015))
            and longest_span >= min_span
        )
        log.debug(
            f"Zytos health bar: color={pct:.1%} longest_span={longest_span}px "
            f"min_span={min_span}px seen={seen}"
        )
        _save_debug("zytos_health_seen" if seen else "zytos_health_missing", img)
        return seen
    except Exception as e:
        log.warning(f"zytos health_bar_seen() failed: {e}")
        return True
