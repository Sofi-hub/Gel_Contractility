@echo off
rem ---------------------------------------------------------------------------
rem Control de una noche (2026-10-17): videos de Andres medidos por textura a
rem RESOLUCION COMPLETA (4K), comparados contra la corrida normal (achicada x0.5)
rem que ya esta en data\processed_data\<carpeta>.
rem
rem Doble clic, o desde la consola:  data\_mediciones_fases\textura\noche_4k.bat
rem Cada video: ~1 h o mas. Van en orden de prioridad: si se corta a la manana,
rem lo que termino ya sirve. Lo que se imprime queda tambien en noche_4k_log.txt.
rem Resultados: data\processed_data\_4k_completo\<carpeta>\ y
rem             data\_mediciones_fases\textura\comparacion_<carpeta>.txt
rem No toca los resultados normales.
rem ---------------------------------------------------------------------------
cd /d "%~dp0..\..\.."
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
set LOG=data\_mediciones_fases\textura\noche_4k_log.txt
echo Inicio %date% %time% > "%LOG%"

for %%V in (40V_1 20V_3 10V_1 40V_3 10V_3) do call :uno %%V

echo Fin %date% %time% >> "%LOG%"
echo.
echo LISTO. Comparaciones en data\_mediciones_fases\textura\comparacion_*.txt
pause
goto :eof

:uno
rem %1 = carpeta (ej. 40V_1) -> video Videos_Andres\40V\1.mp4
set C=%1
set VOLT=%C:~0,3%
set N=%C:~4,1%
set OUT=data\processed_data\_4k_completo\%C%
echo. >> "%LOG%"
echo ===== %C%  (inicio %time%) ===== >> "%LOG%"
echo ===== %C%  (inicio %time%) =====
%PY% main.py --video "data\raw_videos\Videos_Andres\%VOLT%\%N%.mp4" --metodo textura --resolucion-completa --output-dir "%OUT%" >> "%LOG%" 2>&1
if errorlevel 1 (echo   ERROR en main.py, sigo con el proximo >> "%LOG%" & goto :eof)
%PY% scripts\contraction_report.py --input "%OUT%\serie_temporal_%N%.xlsx" --frecuencia-estimulo 0.1 >> "%LOG%" 2>&1
if errorlevel 1 (echo   ERROR en el reporte, sigo con el proximo >> "%LOG%" & goto :eof)
%PY% data\_mediciones_fases\textura\comparar_resolucion.py "data\processed_data\%C%" "%OUT%" >> "%LOG%" 2>&1
echo   %C% terminado a las %time% >> "%LOG%"
goto :eof
