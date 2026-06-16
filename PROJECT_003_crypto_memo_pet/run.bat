@echo off
chcp 65001 >nul 2>nul
title CryptoMemoPet
start "" /B C:\Users\94858\.workbuddy\binaries\python\envs\crypto_memo\Scripts\pythonw.exe "%~dp0src\main.py"
