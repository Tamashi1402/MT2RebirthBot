# MT2 Rebirth Bot

A Windows desktop bot for the **Miner Tycoon 2 Rebirth (MT2)** Fortnite Creative map. It plays
the full rebirth progression loop for you — stone farming, area navigation,
meteor hits, rebirths — and supports boss/farm modes (Delve, Kraken, Zytos,
Crater, Meteor). Everything is driven from a local web dashboard with live
graphs, OCR/color calibration tools and a visual macro recorder.

> ⚠️ **Disclaimer** — this project is for learning and personal use. Automating
> a game can violate the platform's terms of service; use it at your own risk.

## Features

- **Rebirth progression** — base-rock grinding, area teleports, stage rocks,
  meteor hits, automatic rebirth, with OCR-verified stone counting.
- **Boss & farm modes** — Delve, Kraken, Zytos boss loops and Crater/Meteor
  farming with detection overlays (ESP-style boxes for Crater rocks).
- **Local web dashboard** (`http://localhost:7373`) — live state, run history
  graphs with per-run step timelines, settings, stats.
- **Vision & calibration tools** — OCR region calibration, color sampling,
  screenshot preview, live OCR test, plus a guided First Steps wizard.
- **Macro Engine** — visual macro recorder/editor (mouse/keyboard blocks,
  IF/ELSE logic, variables, labels/gotos, screenshot-based image checks).
- **Robustness** — stone watcher, network lag guard, failure screenshots,
  force-restart recovery, hotkey failsafe polling.

## Requirements

- Windows 10/11 (input hooks and WinAPI calls are Windows-only)
- Python 3.10+
- Fortnite running in **windowed fullscreen** — any resolution and aspect
  ratio (regions/points are auto-scaled from a 1920×1080 authoring frame to
  your live resolution; the Vision tab lets you recalibrate if needed)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed
  (the bot also looks for a bundled copy next to the app)

## Installation

```bat
scripts\INSTALL.bat
```

or manually:

```bat
pip install -r requirements.txt
```

## Usage

1. Run **`START.bat`** (or `python code/bot.py`).
   The dashboard opens automatically in your browser.
2. Complete the **First Steps** wizard (sensitivity, windowed fullscreen,
   HUD scale, colorblind mode).
3. Pick a mode (Rebirth / Delve / Kraken / Zytos / Crater / Meteor) and press
   **F8** to start, **F9** to stop.
4. The Macro Engine editor is available at `http://localhost:7373/me/`.

### Hotkeys (configurable in `data/config.json`)

| Key | Action |
| --- | --- |
| F8 | Start run |
| F9 | Stop / soft reset |
| F4 | In-game map toggle (used by navigation) |
| F5 / F6 | Macro Engine record / play toggle (Recorder tab) |

## Repo layout

```
code/              bot, dashboard, macro engine and all modules
  bot.py           main state machine / run loop
  dashboard.py     Flask dashboard server (localhost:7373)
  macro_engine/    standalone macro recorder/editor app
data/              config.json, calibration defaults, wizard state
macros/           recorded macros + image checks
modules/           future mode addons
scripts/           install / build / utility scripts
```

## Configuration

All tunables live in `data/config.json` and are editable from the dashboard's
Config tab. Screen regions/points auto-scale between the recorded base
resolution (1920×1080) and your live resolution; `data/default_regions.json`
holds the factory calibration, and the Vision tab lets you recalibrate any
region by sampling your screen.

## License

MIT — see [LICENSE](LICENSE). Third-party components are credited in
[THIRD_PARTY.md](THIRD_PARTY.md).
