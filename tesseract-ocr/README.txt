MT2 Rebirth Bot — bundled Tesseract OCR 5.4.0 (UB Mannheim)
===========================================================

This folder is a portable Windows Tesseract. The bot finds it automatically:

  Frozen exe: packed INSIDE MT2RebirthBot.exe (extracted to a temp folder at run).
              Users who only receive the .exe still get OCR — rebuild with BUILD.ps1.
  Source:     <bot folder>/tesseract-ocr/tesseract.exe  (next to START.bat)


No PATH, no installer, no extra setup. Keep this folder next to
MT2RebirthBot.exe (or next to START.bat when running from source).

English (eng) language data is included. Training tools and extra
languages were stripped to keep the package smaller.

Runtime DLLs required by tesseract.exe (including libcrypto-3-x64.dll
and libwebpmux-3.dll) live in this same folder. Do not move tesseract.exe
out of here.

License: Apache 2.0 — see doc/LICENSE
