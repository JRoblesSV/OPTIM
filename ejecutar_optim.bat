@echo off
title OPTIM Labs - Sistema de Programacion de Laboratorios
color 0A

echo.
echo ========================================================
echo           OPTIM Labs - ETSIDI (UPM)
echo     Sistema de Programacion Automatica de Laboratorios
echo ========================================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Verificar si existe Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion
    pause
    exit /b 1
)

echo [OK] Python detectado correctamente
python --version

REM Verificar si existe el archivo principal
if not exist "src\gui_labs.py" (
    echo.
    echo ERROR: No se encontro el archivo principal 'src\gui_labs.py'
    echo Verifica que estes en el directorio correcto del proyecto OPTIM
    pause
    exit /b 1
)

echo [OK] Archivo principal encontrado

REM Verificar dependencias principales
echo.
echo Verificando dependencias de Python...

python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [WARNING] PyQt6 no detectado. Intentando instalar...
    pip install PyQt6
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyQt6
        echo Ejecuta manualmente: pip install PyQt6
        pause
        exit /b 1
    )
) else (
    echo [OK] PyQt6 disponible
)

python -c "import pandas" 2>nul
if errorlevel 1 (
    echo [WARNING] pandas no detectado. Intentando instalar...
    pip install pandas
    if errorlevel 1 (
        echo ERROR: No se pudo instalar pandas
        echo Ejecuta manualmente: pip install pandas
        pause
        exit /b 1
    )
) else (
    echo [OK] pandas disponible
)

REM Verificar configuración
if exist "src\configuracion_labs.json" (
    echo [OK] Archivo de configuracion encontrado
) else (
    echo [INFO] No hay configuracion previa - se creara una nueva
)

echo.
echo ========================================================
echo                  INICIANDO OPTIM LABS
echo ========================================================
echo.

REM Ejecutar el programa principal
cd src
python gui_labs.py

REM Verificar si hubo errores
if errorlevel 1 (
    echo.
    echo ERROR: El programa termino con errores
    echo Revisa los mensajes anteriores para mas detalles
) else (
    echo.
    echo [OK] OPTIM Labs finalizado correctamente
)

echo.