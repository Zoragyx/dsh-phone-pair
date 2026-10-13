@echo off
chcp 65001 >nul
echo ================================================
echo   DSH Phone Pair - tester self check (read only)
echo ================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tester-check.ps1"
echo.
echo Report saved to Desktop: dsh-tester-check.txt
echo Send the whole report back.
echo.
pause
