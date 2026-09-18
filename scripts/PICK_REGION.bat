@echo off
set "ROOT=%~dp0.."
cd /d "%ROOT%"
echo ==========================================
echo  MT2 Bot -- Region Picker
echo  Drag to select any area on screen.
echo  Coordinates printed here + saved to
echo  code\tools\region_result.txt
echo ==========================================
echo.
set "PYTHONPATH=%ROOT%\code"
python code\tools\pick_region.py
echo.
echo Done! Check above for coordinates.
pause
