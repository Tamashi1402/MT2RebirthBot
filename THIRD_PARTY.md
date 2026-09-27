# Third-party software used by this repository

## Python dependencies

See `requirements.txt` (mss, opencv-python, pytesseract, psutil, numpy,
keyboard, mouse, flask, pywebview, Pillow). Each is used under its own
license; none are bundled in this repository.

## Tesseract OCR (bundled)

The bot uses [Tesseract](https://github.com/tesseract-ocr/tesseract)
(Apache-2.0) via `pytesseract`. A portable Windows build — Tesseract
5.4.0 from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
— is bundled in `tesseract-ocr/` (tesseract.exe, English `eng` traineddata
and its runtime DLLs, including Leptonica). The upstream Apache-2.0
license is included at `tesseract-ocr/doc/LICENSE`. BUILD packs the whole
folder into the exe, so OCR works with no separate install.

## Blockly (bundled)

The visual macro editor (`code/editor/`, `code/blockly/`) embeds a build of
[Blockly](https://developers.google.com/blockly) by Google LLC, licensed
under the Apache License 2.0. The minified core
(`code/blockly/lib/blockly.min.js`), its English messages (`en.js`) and the
media sprites are unmodified upstream build outputs.
