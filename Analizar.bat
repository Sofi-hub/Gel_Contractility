@echo off
rem Doble clic: abre la ventana de analisis con el entorno del proyecto.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" interfaz.py
) else (
    python interfaz.py
)
if errorlevel 1 pause
