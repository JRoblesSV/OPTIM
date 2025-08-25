@echo off
title OPTIM Labs - Instalador de Dependencias
color 0B

echo ========================================================
echo         OPTIM Labs - Instalador de Dependencias
echo ========================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalacion
    echo.
    pause
    exit /b 1
)

echo [OK] Python detectado:
python --version

REM Actualizar pip
echo.
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias principales
echo.
echo Instalando PyQt6...
pip install PyQt6

echo.
echo Instalando pandas...
pip install pandas

echo.
echo Instalando dependencias adicionales...
pip install numpy
pip install openpyxl

REM Verificar instalación
echo.
echo ========================================================
echo            VERIFICANDO INSTALACION
echo ========================================================

python -c "import PyQt6; print('[OK] PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)"
python -c "import pandas; print('[OK] pandas version:', pandas.__version__)"
python -c "import numpy; print('[OK] numpy version:', numpy.__version__)"
python -c "import openpyxl; print('[OK] openpyxl version:', openpyxl.__version__)"

echo.
echo ========================================================
echo          INSTALACION COMPLETADA EXITOSAMENTE
echo ========================================================
echo.
echo Ya puedes ejecutar OPTIM Labs usando 'ejecutar_optim.bat'
echo.
pause