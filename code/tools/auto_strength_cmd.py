"""
auto_strength_cmd.py — command-line auto-strength toggle for Macro Recorder
===========================================================================
Call from a macro "Run Program" action:

    python auto_strength_cmd.py enable     → turn ON  (only if currently OFF)
    python auto_strength_cmd.py disable    → turn OFF (only if currently ON)
    python auto_strength_cmd.py status     → print ACTIVE or INACTIVE, exit 0/1

Exit codes:
    0 = success (or already in desired state)
    1 = INACTIVE (status command only)
    2 = error

Where to put this file:
    Keep it in MT2RebirthBot\tools\
    Full path example:
        python "C:/Users/You/MT2RebirthBot/tools/auto_strength_cmd.py" enable
"""
import sys
import os

# Add parent dir so we can import screen + macro_runner
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from screen import is_auto_strength_active
from macro_runner import enable_auto_strength, disable_auto_strength

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"

    if cmd == "status":
        active = is_auto_strength_active()
        print("ACTIVE" if active else "INACTIVE")
        sys.exit(0 if active else 1)

    elif cmd == "enable":
        active = is_auto_strength_active()
        if active:
            print("[AutoStr] Already ON — no action needed")
        else:
            print("[AutoStr] OFF → enabling")
            enable_auto_strength()
            print("[AutoStr] Enabled ✓")
        sys.exit(0)

    elif cmd == "disable":
        active = is_auto_strength_active()
        if not active:
            print("[AutoStr] Already OFF — no action needed")
        else:
            print("[AutoStr] ON → disabling")
            disable_auto_strength()
            print("[AutoStr] Disabled ✓")
        sys.exit(0)

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: auto_strength_cmd.py [enable|disable|status]")
        sys.exit(2)

if __name__ == "__main__":
    main()
