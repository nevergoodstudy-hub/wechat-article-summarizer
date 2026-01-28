@echo off
chcp 65001 >nul 2>&1
title 微信文章助手
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" "run_gui.pyw"
