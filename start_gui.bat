@echo off
title SaldoBoek
echo Activeer virtuele environment...
call .venv\Scripts\activate.bat
echo Start SaldoBoek GUI...
python -m saldoboek.gui.app
pause
