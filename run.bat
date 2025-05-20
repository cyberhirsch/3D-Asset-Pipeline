@echo off
echo ============================================================
echo  STARTING KITBASH AUTOMATION
echo ============================================================
echo.

REM Set the directory where the scripts are located
set SCRIPT_DIR=%~dp0
REM For older systems or if %~dp0 doesn't work as expected, you can hardcode:
REM set SCRIPT_DIR=E:\Projects\2025\Spaceship Kitbash\

echo Changing directory to: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================================
echo  STAGE 1: RUNNING BLENDER PROCESSING (process_assets.py)
echo ============================================================
echo.
python process_assets.py
echo.
echo STAGE 1 (Blender Processing) COMPLETE.
echo Press any key to continue to Substance Painter processing...
pause >nul
echo.

echo ============================================================
echo  STAGE 2: RUNNING SUBSTANCE PAINTER PROCESSING (substance_painter_batch.py)
echo ============================================================
echo.
python substance_painter_batch.py
echo.
echo STAGE 2 (Substance Painter Processing) COMPLETE.
echo.

echo ============================================================
echo  AUTOMATION SCRIPT FINISHED
echo ============================================================
echo The command window will remain open. Close it manually.
pause