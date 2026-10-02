@echo off
cd /d "%~dp0"
echo =======================================================================
echo Actualizacion incremental de la cartera de fondos mutuos (Circular 1333)...
echo Mismo pipeline que ejecuta .github/workflows/ffmm_carteras.yml
echo (antes apuntaba a ffmm\circular_1333_cartera, carpeta que ya no existe).
echo =======================================================================
python -m ffmm.scripts.actualizar_carteras --diagnostico
echo.
echo Para descargar y publicar los meses pendientes, use el workflow
echo ffmm_carteras.yml (Actions). Aqui solo se deja el diagnostico local.
if %ERRORLEVEL% equ 0 (
  echo.
  echo [EXITO] Diagnostico finalizado correctamente.
) else (
  echo.
  echo [ERROR] Ocurrio un problema al revisar los meses pendientes.
)
pause
