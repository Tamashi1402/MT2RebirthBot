#!/usr/bin/env python3
# ============================================================
# MCR → .macro CONVERTER
# Drag a .mcr file onto mcr_convert.bat to convert it.
# Output goes into the /macros/ folder next to the bot.
#
# Supported .mcr commands:
#   LABEL, GOTO, DELAY, COMMENT
#   Keyboard : KEY : KeyDown / KeyUp / KeyPress
#   Mouse : X : Y : LeftButtonDown / LeftButtonUp
#   RUN CSHARP  (SmoothMouseMove, SetCursorPos+Click, raw mouse_event)
#   REPEAT : N  / ENDREPEAT
#   IF IMAGE ... / ENDIF   (converted to a skip/pass — image check not supported natively)
# ============================================================
import sys
import os
import re

# ---------- key name map (JJibit → win32 VK) ----------
KEY_MAP = {
    "A": "0x41", "B": "0x42", "C": "0x43", "D": "0x44",
    "E": "0x45", "F": "0x46", "G": "0x47", "H": "0x48",
    "I": "0x49", "J": "0x4A", "K": "0x4B", "L": "0x4C",
    "M": "0x4D", "N": "0x4E", "O": "0x4F", "P": "0x50",
    "Q": "0x51", "R": "0x52", "S": "0x53", "T": "0x54",
    "U": "0x55", "V": "0x56", "W": "0x57", "X": "0x58",
    "Y": "0x59", "Z": "0x5A",
    "F1":  "0x70", "F2":  "0x71", "F3":  "0x72", "F4":  "0x73",
    "F5":  "0x74", "F6":  "0x75", "F7":  "0x76", "F8":  "0x77",
    "F9":  "0x78", "F10": "0x79", "F11": "0x7A", "F12": "0x7B",
    "Space":      "0x20",
    "Enter":      "0x0D",
    "Tab":        "0x09",
    "Escape":     "0x1B",
    "BackSpace":  "0x08",
    "Delete":     "0x2E",
    "Up":         "0x26",
    "Down":       "0x28",
    "Left":       "0x25",
    "Right":      "0x27",
    "Home":       "0x24",
    "End":        "0x23",
    "PageUp":     "0x21",
    "PageDown":   "0x22",
    "ControlLeft":  "0x11",
    "ControlRight": "0x11",
    "ShiftLeft":    "0x10",
    "ShiftRight":   "0x10",
    "AltLeft":      "0x12",
    "AltRight":     "0x12",
}

# ---------- parse helpers ----------

def decode_csharp(line: str) -> str:
    """Strip 'RUN CSHARP :' prefix and decode {#crlf#} escapes."""
    code = line[len("RUN CSHARP :"):].strip()
    return code.replace("{#crlf#}", "\n")


def parse_smooth_move(code: str):
    """Return (dx, dy, duration_ms) if the C# does a SmoothMouseMove call."""
    m = re.search(r"SmoothMouseMove\((-?\d+),\s*(-?\d+),\s*(\d+)\)", code)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def parse_raw_mouse_event(code: str):
    """Return (dx, dy) if the C# does a single mouse_event(0x0001, dx, dy, ...) call."""
    m = re.search(r"mouse_event\(0x0001,\s*(-?\d+),\s*(-?\d+),", code)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def parse_move_and_click(code: str):
    """Return (x, y, pre_sleep_ms) if the C# does SetCursorPos + click."""
    # pre-sleep before MoveTo
    sleep_m = re.search(r"Thread\.Sleep\((\d+)\).*?MoveTo\(", code, re.DOTALL)
    pre_ms = int(sleep_m.group(1)) if sleep_m else 0
    # coordinates
    coord_m = re.search(r"MoveTo\((\d+),\s*(\d+)\)", code)
    if coord_m:
        return int(coord_m.group(1)), int(coord_m.group(2)), pre_ms
    return None


def is_kill_macro_recorder(code: str) -> bool:
    return "GetProcessesByName" in code and "MacroRecorder" in code


# ---------- main converter ----------

def convert_mcr(mcr_path: str, out_dir: str) -> str:
    name = os.path.splitext(os.path.basename(mcr_path))[0]
    out_path = os.path.join(out_dir, name + ".macro")

    with open(mcr_path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()

    instructions = []

    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        i += 1

        if not line or line.startswith("COMMENT"):
            continue

        # ── LABEL ──────────────────────────────────────────────
        if line.startswith("LABEL :"):
            label = line.split(":", 1)[1].strip()
            instructions.append(f"LABEL:{label}")
            continue

        # ── GOTO ───────────────────────────────────────────────
        if line.startswith("GOTO :"):
            label = line.split(":", 1)[1].strip()
            instructions.append(f"GOTO:{label}")
            continue

        # ── DELAY ──────────────────────────────────────────────
        if line.startswith("DELAY :"):
            ms = line.split(":", 1)[1].strip()
            instructions.append(f"DELAY:{ms}")
            continue

        # ── REPEAT ─────────────────────────────────────────────
        if line.startswith("REPEAT :"):
            parts = line.split(":")
            count = parts[1].strip()
            instructions.append(f"REPEAT:{count}")
            continue

        if line == "ENDREPEAT":
            instructions.append("ENDREPEAT")
            continue

        # ── IF IMAGE → skip block, just emit NOOP ──────────────
        if line.startswith("IF IMAGE"):
            while i < len(raw_lines):
                inner = raw_lines[i].strip()
                i += 1
                if inner == "ENDIF":
                    break
            continue

        # ── Keyboard ───────────────────────────────────────────
        if line.startswith("Keyboard :"):
            parts = [p.strip() for p in line.split(":")]
            # parts[0]='Keyboard', parts[1]=key, parts[2]=action
            key_name = parts[1]
            action   = parts[2]
            vk = KEY_MAP.get(key_name, "0x00")
            if action == "KeyDown":
                instructions.append(f"KEY_DOWN:{vk}")
            elif action == "KeyUp":
                instructions.append(f"KEY_UP:{vk}")
            elif action == "KeyPress":
                instructions.append(f"KEY_PRESS:{vk}")
            else:
                instructions.append(f"# unknown keyboard action: {line}")
            continue

        # ── Mouse ──────────────────────────────────────────────
        if line.startswith("Mouse :"):
            parts = [p.strip() for p in line.split(":")]
            # Mouse : X : Y : Action : ...
            x      = int(parts[1])
            y      = int(parts[2])
            action = parts[3]
            if "LeftButtonDown" in action:
                # Look ahead: if the next Mouse line is ALSO LeftButtonDown (not LeftButtonUp)
                # then this is a standalone click, not the start of a held drag.
                # Only emit LEFT_DOWN (held drag) if the next Mouse line is LeftButtonUp.
                next_mouse_action = None
                for future_line in raw_lines[i:]:  # i already points past current line
                    fp = [p.strip() for p in future_line.split(':')]
                    if len(fp) >= 4 and fp[0] == 'Mouse':
                        next_mouse_action = fp[3]
                        break
                if next_mouse_action and 'LeftButtonUp' in next_mouse_action:
                    # Intentional drag — hold button down
                    instructions.append(f"MOUSE_MOVE_ABS:{x},{y}")
                    instructions.append("MOUSE_LEFT_DOWN")
                else:
                    # Standalone click (no matching LeftButtonUp coming)
                    instructions.append(f"MOUSE_MOVE_ABS:{x},{y}")
                    instructions.append("MOUSE_LEFT_CLICK")
            elif "LeftButtonUp" in action:
                instructions.append(f"MOUSE_MOVE_ABS:{x},{y}")
                instructions.append("MOUSE_LEFT_UP")
            else:
                instructions.append(f"# unknown mouse action: {line}")
            continue

        # ── RUN CSHARP ─────────────────────────────────────────
        if line.startswith("RUN CSHARP"):
            code = decode_csharp(line)
            _append_csharp(instructions, code)
            continue

        # anything else — comment it out
        instructions.append(f"# skipped: {line[:80]}")

    # write output
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Auto-converted from {os.path.basename(mcr_path)}\n")
        for inst in instructions:
            f.write(inst + "\n")

    return out_path


def _append_csharp(instructions: list, code: str, indent: str = ""):
    """Translate a decoded C# block into macro instructions."""
    if is_kill_macro_recorder(code):
        # No-op — our runner doesn't need this
        instructions.append(f"{indent}# (kill MacroRecorder — ignored in native runner)")
        return

    sm = parse_smooth_move(code)
    if sm:
        dx, dy, duration_ms = sm
        instructions.append(f"{indent}SMOOTH_MOVE:{dx},{dy},{duration_ms}")
        return

    mc = parse_move_and_click(code)
    if mc:
        x, y, pre_ms = mc
        if pre_ms:
            instructions.append(f"{indent}DELAY:{pre_ms}")
        instructions.append(f"{indent}MOUSE_MOVE_ABS:{x},{y}")
        instructions.append(f"{indent}DELAY:100")
        instructions.append(f"{indent}MOUSE_LEFT_CLICK")
        return

    raw = parse_raw_mouse_event(code)
    if raw:
        dx, dy = raw
        # single instant mouse_event move — treat as instant relative move
        instructions.append(f"{indent}SMOOTH_MOVE:{dx},{dy},0")
        return

    instructions.append(f"{indent}# unrecognised C# block (manual review needed)")


# ---------- entry point ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mcr_convert.py <file.mcr> [<file2.mcr> ...]")
        print("       (or drag .mcr files onto mcr_convert.bat)")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Determine output dir: macros/ folder next to this script's parent
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    bot_dir     = os.path.dirname(script_dir)   # tools/ → bot root
    macros_dir  = os.path.join(bot_dir, "macros")

    ok  = []
    err = []
    for mcr_path in sys.argv[1:]:
        if not mcr_path.lower().endswith(".mcr"):
            print(f"[SKIP] Not a .mcr file: {mcr_path}")
            continue
        if not os.path.isfile(mcr_path):
            print(f"[MISS] File not found: {mcr_path}")
            err.append(mcr_path)
            continue
        try:
            out = convert_mcr(mcr_path, macros_dir)
            print(f"[OK]  {os.path.basename(mcr_path)}  →  {out}")
            ok.append(out)
        except Exception as e:
            print(f"[ERR] {mcr_path}: {e}")
            err.append(mcr_path)

    print(f"\nDone — {len(ok)} converted, {len(err)} failed.")
    print(f"Output folder: {macros_dir}")
    input("\nPress Enter to exit...")
