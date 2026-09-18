# ============================================================
# CALIBRATION TOOL — find_regions.py
# Run with Fortnite open to verify all HUD regions are correct.
#
# Output:
#   - Live readings printed to console every 2 seconds
#   - Debug PNG crops saved to tools/debug_*.png
#
# Usage:  python tools/find_regions.py
# ============================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import cv2
from screen import (
    grab_region, _preprocess,
    read_stone, read_strength,
    is_stone_icon_visible, is_in_area5,
    is_auto_strength_active, is_rebirth_screen,
)
from config import (
    STONE_REGION, STRENGTH_REGION, STONE_ICON_REGION,
    AUTO_STR_REGION,
)

OUT = os.path.dirname(__file__)

print("=" * 60)
print("MT2 Bot — Region Calibrator  (Ctrl+C to stop)")
print("Resolution expected: 1024x576")
print("Debug crops saved to: tools/debug_*.png")
print("=" * 60)

i = 0
while True:
    stone    = read_stone()
    strength = read_strength()
    icon_ok  = is_stone_icon_visible()
    auto_str = is_auto_strength_active()
    rebirth  = is_rebirth_screen()

    print(
        f"\r  Stone: {str(stone):<18}"
        f"  Strength: {str(strength):<18}"
        f"  Icon: {'✓' if icon_ok else '✗'}"
        f"  AutoStr: {'ON ' if auto_str else 'OFF'}"
        f"  RebirthScreen: {'YES' if rebirth else 'no '}   ",
        end="", flush=True
    )

    # Save debug crops every 5 ticks
    if i % 5 == 0:
        for label, region in [
            ("stone",      STONE_REGION),
            ("strength",   STRENGTH_REGION),
            ("stone_icon", STONE_ICON_REGION),
            ("auto_str",   AUTO_STR_REGION),
        ]:
            img = grab_region(region)
            cv2.imwrite(os.path.join(OUT, f"debug_{label}.png"), img)
            if label in ("stone", "strength"):
                proc = _preprocess(img)
                cv2.imwrite(os.path.join(OUT, f"debug_{label}_proc.png"), proc)

    i += 1
    time.sleep(2)
