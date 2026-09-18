# ============================================================
# CRATER - ROCK DETECTOR
# Captures a small area around screen center, masks for pink/magenta
# rocks via HSV, finds contours. Returns rocks in SCREEN coordinates.
# ============================================================
import numpy as np
import cv2
import mss

from logger import get_logger

log = get_logger()
_sct = mss.mss()


def get_capture_rect(capture_w=500, capture_h=350):
    sw, sh = _sct.monitors[1]["width"], _sct.monitors[1]["height"]
    cx = sw // 2
    cy = sh // 2
    x1 = max(0, cx - capture_w // 2)
    y1 = max(0, cy - capture_h // 2)
    x2 = min(sw, x1 + capture_w)
    y2 = min(sh, y1 + capture_h)
    return (x1, y1, x2, y2)


def grab_capture(capture_w=500, capture_h=350):
    rect = get_capture_rect(capture_w, capture_h)
    x1, y1, x2, y2 = rect
    mon = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
    raw = _sct.grab(mon)
    img = np.array(raw)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), rect


def detect_rocks(img, hsv_low, hsv_high, use_hue_wrap=True,
                 hsv_low2=None, hsv_high2=None, min_area=150):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low = np.array(hsv_low, dtype=np.uint8)
    high = np.array(hsv_high, dtype=np.uint8)
    mask = cv2.inRange(hsv, low, high)

    if use_hue_wrap and hsv_low2 is not None and hsv_high2 is not None:
        low2 = np.array(hsv_low2, dtype=np.uint8)
        high2 = np.array(hsv_high2, dtype=np.uint8)
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, low2, high2))

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rocks = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        x, y, w, h = cv2.boundingRect(c)

        # -- Reject thin slivers (edge fragments, HUD lines) ----------
        # Real crater rocks are roughly compact blobs.  Fragments torn
        # off the edge of a red rock by the morphological open tend to
        # be thin strips with a very high aspect ratio.  Reject anything
        # where one dimension is more than 4x the other.
        if w > 0 and h > 0:
            aspect = max(w, h) / min(w, h)
            if aspect > 4.0:
                continue

        # -- Reject low solidity (irregular, non-rock shapes) ----------
        # Solidity = contour area / convex hull area.  Real rocks are
        # solid, compact blobs (solidity > 0.5).  Noise from terrain and
        # HUD elements tends to be wispy/irregular (solidity < 0.35).
        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < 0.35:
                continue

        rocks.append({"cx": cx, "cy": cy, "area": area,
                      "bx1": x, "by1": y, "bx2": x + w, "by2": y + h})
    rocks.sort(key=lambda r: r["area"], reverse=True)
    return rocks, mask


def rocks_to_screen(rocks, capture_rect):
    x_off, y_off = capture_rect[0], capture_rect[1]
    for r in rocks:
        r["screen_cx"] = r["cx"] + x_off
        r["screen_cy"] = r["cy"] + y_off
        r["screen_bx1"] = r["bx1"] + x_off
        r["screen_by1"] = r["by1"] + y_off
        r["screen_bx2"] = r["bx2"] + x_off
        r["screen_by2"] = r["by2"] + y_off
    return rocks


def pick_target(rocks, mode="largest"):
    if not rocks:
        return None
    if mode == "lowest":
        return max(rocks, key=lambda r: r["cy"])
    return rocks[0]
