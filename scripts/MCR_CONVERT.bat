@echo off
set "ROOT=%~dp0.."
cd /d "%ROOT%"
:: ============================================================
:: MCR ??? .macro CONVERTER  (drag & drop)
:: Drop one or more .mcr files onto this .bat
:: Output .macro files go into the /macros/ folder
:: ============================================================
python code\tools\mcr_convert.py %*

