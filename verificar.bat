@echo off
rem Doble clic: corre TODOS los tests y la regresion, y dice OK o FALLA al final.
rem   verificar.bat            tests + regresion rapida
rem   verificar.bat completo   ademas la regresion desde el video (si se toco ROI, bordes o RANSAC)
rem   verificar.bat rapido     sin test_textura (el mas lento)
cd /d "%~dp0"
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
set OPC=
if /i "%1"=="completo" set OPC=--completo
if /i "%1"=="rapido" set OPC=--rapido
"%PY%" tests\correr_todo.py %OPC%
echo.
pause
