@echo off
chcp 65001 >nul
echo ========================================
echo   禅道Bug监控程序
echo ========================================
echo.
cd /d "%~dp0"
C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe main.py
echo.
echo 程序已退出
pause
