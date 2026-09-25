@echo off
cd /d "%~dp0"
echo =======================================================================
echo Ejecutando pipeline incremental de derivados FFMM (Circular 1333)...
echo =======================================================================
python ffmm/circular_1333_cartera/scripts/update_pipeline.py
if %ERRORLEVEL% equ 0 (
    echo.
    echo [EXITO] Pipeline finalizado correctamente.
) else (
    echo.
    echo [ERROR] Ocurrio un problema en la ejecucion.
)
pause
