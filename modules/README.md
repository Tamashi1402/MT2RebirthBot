# modules/

Mode addons will live here later (see `concept-modulable.md`):

    modules/zytos.zip
    modules/kraken.zip
    modules/rebirth.zip
    ...

A mode zip is identified by `manifest.json` inside it.

ESP / YOLO / torch runtimes (ultra_instinct_*.exe, *.pt models) are gone.
The Download Center UI is kept as WIP for future mode-zip downloads.

Right now no mode zips are loaded from here. Built-in modes still come from
`code/` (zytos is `code/zytos/`, crater is `code/crater/`, others still inlined).
