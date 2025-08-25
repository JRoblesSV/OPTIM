@echo off
title OPTIM Labs - Modo Debug
color 0E

echo ========================================================
echo           OPTIM Labs - MODO DEBUG
echo ========================================================

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Mostrar información del sistema
echo.
echo === INFORMACION DEL SISTEMA ===
echo Directorio actual: %CD%
echo Usuario: %USERNAME%
echo Fecha/Hora: %DATE% %TIME%

REM Información de Python
echo.
echo === INFORMACION DE PYTHON ===
python --version
python -c "import sys; print(f'Ejecutable: {sys.executable}')"
python -c "import sys; print(f'Ruta: {sys.path[0]}')"

REM Verificar todas las dependencias
echo.
echo === VERIFICACION DE DEPENDENCIAS ===
python -c "import PyQt6; print('[OK] PyQt6:', PyQt6.QtCore.PYQT_VERSION_STR)" 2>nul || echo "[ERROR] PyQt6 no disponible"
python -c "import pandas; print('[OK] pandas:', pandas.__version__)" 2>nul || echo "[ERROR] pandas no disponible"
python -c "import json; print('[OK] json: modulo estandar')" 2>nul || echo "[ERROR] json no disponible"
python -c "import os; print('[OK] os: modulo estandar')" 2>nul || echo "[ERROR] os no disponible"
python -c "import datetime; print('[OK] datetime: modulo estandar')" 2>nul || echo "[ERROR] datetime no disponible"

REM Verificar estructura de archivos
echo.
echo === VERIFICACION DE ARCHIVOS ===
if exist "src\gui_labs.py" (echo [OK] gui_labs.py) else (echo [ERROR] gui_labs.py no encontrado)
if exist "src\modules\interfaces\configurar_asignaturas.py" (echo [OK] configurar_asignaturas.py) else (echo [ERROR] configurar_asignaturas.py no encontrado)
if exist "src\modules\interfaces\configurar_profesores.py" (echo [OK] configurar_profesores.py) else (echo [ERROR] configurar_profesores.py no encontrado)
if exist "src\modules\interfaces\configurar_alumnos.py" (echo [OK] configurar_alumnos.py) else (echo [ERROR] configurar_alumnos.py no encontrado)
if exist "src\configuracion_labs.json" (echo [OK] configuracion_labs.json) else (echo [INFO] configuracion_labs.json - se creará)

echo.
echo ========================================================
echo                EJECUTANDO EN MODO DEBUG
echo ========================================================
echo.

REM Ejecutar con información detallada de errores
cd src
python -u gui_labs.py

echo.
echo === FINALIZACION ===
echo Codigo de salida: %ERRORLEVEL%
echo Presiona cualquier tecla para cerrar...
pause >nul