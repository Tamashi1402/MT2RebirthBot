# Macro Engine (visual macro editor)

Self-contained editor + player/record engine for `.macro` files, served by
the dashboard at `/me` (the recorder tab). It replaces the legacy macro
recorder while keeping the same `.macro` v1 format and the custom-modes API.

Layout:

- `app.py` — Flask blueprint: `/me` host page, macro open/save/play/record
  API, recorder HUD. `.macro` files are always stored as **plain v1 text**
  (`TYPE:VALUE` lines); the editor never rewrites lines it cannot represent
  (image checks, IF conditions, …) — they load as Raw blocks and save back
  byte-for-byte.
- `playback.py` — macro player/record engine (input injection, smooth-move
  tracker, failsafe).
- `macro_runner.py` — one-shot runner used by the API (`/me/api/play`).
- `macro_logic.py` — parsing + runtime for macro instructions, resolution
  scaling (mirrors the top-level `macro_logic.py`).
- `macro_text.py` — v1/v2 text format helpers (canonicalize/pretty).
- `container.py` — reads legacy zip macro containers (write path removed).
- `smooth_move.py` — smooth mouse movement tracker.
- `image_meta.py` — screen-position metadata for F2 image crops.
- `overlay.py` — recorder HUD push (uses the bot's `overlay.py` when
  present, falls back gracefully otherwise).
- `static/`, `templates/` — the `/me` host app. The Blockly canvas itself
  lives in `code/editor/` (served at `/editor/`), the Blockly core in
  `code/blockly/` (served at `/blockly/`).

The engine module keeps its own copy of the runtime logic so the bot's
top-level runner (`macro_runner.py` + `macro_logic.py`) stays untouched;
both sides read and write the exact same `.macro` v1 format.
