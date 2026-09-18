# Macro Engine (Rebirth-Compatible)

Run:
1. Run root `START.bat`, or run `python code/macro_engine/app.py`.
2. Macro Engine opens in its own app window.

Features:
- Preset-based workflow only (`/macros/<preset>/<macro>.macro`)
- Create preset by copying existing preset, or create a fresh preset
- Fixed macro filenames only (no free custom names)
- Save directly into selected preset files (no import/export flow)
- Global `F6` toggles Start/Stop for selected macro
- Sensitivity metadata is written into macro comments

Compatibility:
- Uses Macro Engine instruction names and runner behavior.
- Macro files stay plain `.macro` text and are read directly by Rebirth Bot presets.
