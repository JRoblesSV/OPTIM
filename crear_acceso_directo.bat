@echo off
title OPTIM Labs - Crear Acceso Directo

echo Creando acceso directo en el escritorio...

REM Crear acceso directo usando PowerShell
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\OPTIM Labs.lnk'); $Shortcut.TargetPath = '%~dp0ejecutar_optim.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'OPTIM Labs - Sistema de Programacion de Laboratorios'; $Shortcut.Save()"

if exist "%USERPROFILE%\Desktop\OPTIM Labs.lnk" (
    echo [OK] Acceso directo creado en el escritorio
) else (
    echo [ERROR] No se pudo crear el acceso directo
)

echo.
pause