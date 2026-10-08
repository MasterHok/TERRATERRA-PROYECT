@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Instalador TERRARIA LAUNCHER
color 0C

echo.
echo ===============================================================
echo    INSTALADOR TERRARIA LAUNCHER
echo ===============================================================
echo.
echo Este instalador hara lo siguiente:
echo   1. Verificar que Python esta instalado
echo   2. Instalar PySide6, pywinpty y PyInstaller
echo   3. Crear carpetas y los archivos LANZADOR_PYTHON.bat y CREA_UN_EXE.bat
echo   4. Descargar tModLoader
echo   5. Descargar el mod IPv6Remapper
echo   6. Instalar Terraria GOG (seleccionando el instalador)
echo.
pause

REM ===============================================================
REM  1. Verificar Python
REM ===============================================================
echo.
echo [1/6] Verificando Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo.
    echo Descargalo desde: https://www.python.org/downloads/
    echo Durante la instalacion, marca la casilla "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
echo OK - Python detectado.

REM ===============================================================
REM  2. Instalar dependencias
REM ===============================================================
echo.
echo [2/6] Instalando dependencias (PySide6, pywinpty, PyInstaller)...
python -m pip install --upgrade pip
python -m pip install PySide6 pywinpty pyinstaller
if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron instalar las dependencias.
    echo Intenta ejecutar este instalador como Administrador.
    echo.
    pause
    exit /b 1
)
echo OK - Dependencias instaladas.

REM ===============================================================
REM  3. Crear carpetas y archivos .bat
REM ===============================================================
echo.
echo [3/6] Creando carpetas...
if not exist "tModLoader" mkdir tModLoader
if not exist "tModLoader\Mods" mkdir "tModLoader\Mods"
if not exist "Terraria" mkdir Terraria
if not exist "Worlds" mkdir Worlds
if not exist "Worlds\tModLoader" mkdir "Worlds\tModLoader"
if not exist "Worlds\Vanilla" mkdir "Worlds\Vanilla"
if not exist "assets" mkdir assets
if not exist "config" mkdir config
echo OK - Carpetas creadas.

REM ---------------------------------------------------------------
REM  Crear LANZADOR_PYTHON.bat
REM ---------------------------------------------------------------
echo Creando LANZADOR_PYTHON.bat...
> "LANZADOR_PYTHON.bat" echo @echo off
>> "LANZADOR_PYTHON.bat" echo title TERRARIANOS_LAUNCHER
>> "LANZADOR_PYTHON.bat" echo cd /d "%%~dp0"
>> "LANZADOR_PYTHON.bat" echo python TERRATERRA.py
>> "LANZADOR_PYTHON.bat" echo pause
echo OK - LANZADOR_PYTHON.bat creado.

REM ---------------------------------------------------------------
REM  Crear CREA_UN_EXE.bat
REM ---------------------------------------------------------------
echo Creando CREA_UN_EXE.bat...
> "CREA_UN_EXE.bat" echo @echo off
>> "CREA_UN_EXE.bat" echo setlocal enabledelayedexpansion
>> "CREA_UN_EXE.bat" echo title COMPILAR TERRATERRA
>> "CREA_UN_EXE.bat" echo cd /d "%%~dp0"
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo echo ========================================
>> "CREA_UN_EXE.bat" echo echo   COMPILANDO TERRATERRA
>> "CREA_UN_EXE.bat" echo echo ========================================
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo echo Instalando PyInstaller...
>> "CREA_UN_EXE.bat" echo python -m pip install pyinstaller
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo if errorlevel 1 ^(
>> "CREA_UN_EXE.bat" echo     echo ERROR: No se pudo instalar PyInstaller.
>> "CREA_UN_EXE.bat" echo     pause
>> "CREA_UN_EXE.bat" echo     exit /b 1
>> "CREA_UN_EXE.bat" echo ^)
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo echo Detectando icono...
>> "CREA_UN_EXE.bat" echo set "ICON_OPT="
>> "CREA_UN_EXE.bat" echo if exist assets\icon.ico set "ICON_OPT=--icon assets\icon.ico"
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo echo Compilando con PyInstaller...
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo python -m PyInstaller --onefile --windowed --clean %%ICON_OPT%% --add-data "assets;assets" --distpath "TERRALAUNCHER" --name TERRATERRA TERRATERRA.py
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo if errorlevel 1 ^(
>> "CREA_UN_EXE.bat" echo     echo ERROR: La compilacion fallo.
>> "CREA_UN_EXE.bat" echo     pause
>> "CREA_UN_EXE.bat" echo     exit /b 1
>> "CREA_UN_EXE.bat" echo ^)
>> "CREA_UN_EXE.bat" echo.
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo echo ========================================
>> "CREA_UN_EXE.bat" echo echo   COMPILACION COMPLETADA
>> "CREA_UN_EXE.bat" echo echo ========================================
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo echo Ejecutable generado en:
>> "CREA_UN_EXE.bat" echo echo   TERRALAUNCHER\TERRATERRA.exe
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo echo NOTA: El .exe lleva los assets dentro.
>> "CREA_UN_EXE.bat" echo echo Necesita una carpeta con permisos de escritura para usar:
>> "CREA_UN_EXE.bat" echo echo   - config\
>> "CREA_UN_EXE.bat" echo echo   - tModLoader\
>> "CREA_UN_EXE.bat" echo echo   - Terraria\
>> "CREA_UN_EXE.bat" echo echo   - Worlds\
>> "CREA_UN_EXE.bat" echo echo.
>> "CREA_UN_EXE.bat" echo pause
>> "CREA_UN_EXE.bat" echo endlocal
echo OK - CREA_UN_EXE.bat creado.

REM ===============================================================
REM  4. Descargar tModLoader
REM ===============================================================
echo.
echo [4/6] Descargando tModLoader v2026.08.3.0...
if exist "tModLoader\tModLoader.dll" (
    echo tModLoader ya parece estar instalado. Saltando descarga.
) else (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tModLoader/tModLoader/releases/download/v2026.08.3.0/tModLoader.zip' -OutFile 'tModLoader.zip'"
    if errorlevel 1 (
        echo ERROR: No se pudo descargar tModLoader.
        echo Comprueba tu conexion a Internet.
        pause
        exit /b 1
    )
    echo Extrayendo tModLoader...
    powershell -Command "Expand-Archive -Path 'tModLoader.zip' -DestinationPath 'tModLoader' -Force"
    del tModLoader.zip
    echo OK - tModLoader instalado.
)

REM ===============================================================
REM  5. Descargar IPv6Remapper
REM ===============================================================
echo.
echo [5/6] Descargando mod IPv6Remapper-1.4.5.tmod...
if exist "tModLoader\Mods\IPv6Remapper-1.4.5.tmod" (
    echo El mod ya esta descargado. Saltando.
) else (
    powershell -Command "Invoke-WebRequest -Uri 'https://codeberg.org/EatDatPie_445/IPv6Remapper/releases/download/2.0/IPv6Remapper-1.4.5.tmod' -OutFile 'tModLoader\Mods\IPv6Remapper-1.4.5.tmod'"
    if errorlevel 1 (
        echo.
        echo AVISO: No se pudo descargar IPv6Remapper automaticamente.
        echo     Es posible que Codeberg este bloqueando la descarga.
        echo.
        echo     Descargalo manualmente desde:
        echo     https://codeberg.org/EatDatPie_445/IPv6Remapper/releases
        echo.
        echo     Y coloca el archivo .tmod en:
        echo     tModLoader\Mods\
        echo.
    ) else (
        echo OK - Mod IPv6Remapper descargado.
    )
)

REM ===============================================================
REM  6. Terraria GOG (instalador manual desde Google Drive)
REM ===============================================================
echo.
echo [6/6] Terraria GOG
echo.

if exist "Terraria\Terraria.exe" (
    echo Terraria ya instalado. Saltando.
    goto :skip_terraria
)

echo Terraria no esta instalado.
echo.
echo El instalador de Terraria debe descargarse MANUALMENTE desde Google Drive:
echo.
echo    https://drive.google.com/file/d/1rp9Z_--9oLadQBjxjO0BFPyy38-aJ0U3/view?usp=sharing
echo.
echo Es un archivo de ~500 MB. Google Drive no permite descarga automatica.
echo.

set /p ABRIR="Quieres que abra el navegador ahora para descargarlo? (S/N): "
if /i "!ABRIR!"=="S" (
    echo.
    echo Abriendo el navegador...
    start "" "https://drive.google.com/file/d/1rp9Z_--9oLadQBjxjO0BFPyy38-aJ0U3/view?usp=sharing"
) else (
    echo.
    echo Copia este enlace en tu navegador para descargarlo:
    echo.
    echo   https://drive.google.com/file/d/1rp9Z_--9oLadQBjxjO0BFPyy38-aJ0U3/view?usp=sharing
    echo.
)

echo.
echo Cuando termines de descargar el archivo, pulsa cualquier tecla
echo para abrir el cuadro de seleccion de archivos.
echo.
pause

echo.
echo Abriendo ventana para seleccionar el archivo descargado...
echo Busca el setup_terraria*.exe en tu carpeta de Descargas.
echo.

set "RUTA_TERRARIA="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.Form; $f.TopMost=$true; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Selecciona el instalador de Terraria'; $d.Filter='Instalador Terraria (*.exe)'+[char]124+'*.exe'+[char]124+'Todos los archivos (*.*)'+[char]124+'*.*'; $d.InitialDirectory=[Environment]::GetFolderPath('UserProfile')+'\Downloads'; if($d.ShowDialog($f) -eq 'OK'){$d.FileName}"`) do set "RUTA_TERRARIA=%%I"

if "!RUTA_TERRARIA!"=="" (
    echo.
    echo Cancelado. No se selecciono ningun archivo.
    echo Puedes ejecutar el instalador de Terraria manualmente
    echo y volver a lanzar este instalador despues.
    goto :skip_terraria
)

echo.
echo Archivo seleccionado:
echo   !RUTA_TERRARIA!
echo.

echo Copiando el instalador a la carpeta del launcher...
copy "!RUTA_TERRARIA!" "setup_terraria.exe" >nul

if not exist "setup_terraria.exe" (
    echo.
    echo ERROR: No se pudo copiar el archivo.
    goto :skip_terraria
)

cls
echo.
echo ===============================================================
echo    INSTALADOR DE TERRARIA - INSTRUCCIONES
echo ===============================================================
echo.
echo Se va a abrir el instalador de Terraria GOG.
echo.
echo Sigue estos pasos EXACTAMENTE:
echo.
echo -------------------------------------------------------------------
echo  PASO 1: Acepta la licencia
echo -------------------------------------------------------------------
echo.
echo   Marca la casilla:
echo      [X] Yes, I have read and accept the EULA
echo.
echo -------------------------------------------------------------------
echo  PASO 2: Abre las opciones de instalacion
echo -------------------------------------------------------------------
echo.
echo   Pulsa el boton:  Options
echo.
echo -------------------------------------------------------------------
echo  PASO 3: Elige la carpeta de instalacion
echo -------------------------------------------------------------------
echo.
echo   En la opcion "Install game to:" pulsa  Browse
echo   y selecciona esta carpeta (la raiz del launcher):
echo.
echo      %CD%
echo.
echo   El instalador creara la carpeta "Terraria" dentro por si solo.
echo.
echo -------------------------------------------------------------------
echo  PASO 4: Instala
echo -------------------------------------------------------------------
echo.
echo   Pulsa Install y espera a que termine.
echo.
echo ===============================================================
echo.
echo Pulsa cualquier tecla para abrir el instalador de Terraria...
pause >nul

start /wait setup_terraria.exe

echo.
echo Comprobando instalacion...

if exist "Terraria\Terraria.exe" (
    echo.
    echo ===============================================================
    echo   TERRARIA INSTALADO CORRECTAMENTE
    echo ===============================================================
    echo.
    echo El launcher ya puede usar Terraria en modo Vanilla.
    echo.
) else (
    echo.
    echo ===============================================================
    echo   AVISO: No se detecto Terraria.exe en la carpeta esperada
    echo ===============================================================
    echo.
    echo Es posible que hayas instalado Terraria en otra carpeta.
    echo Si es asi, puedes moverlo manualmente a:
    echo.
    echo   %CD%\Terraria
    echo.
)

if exist "setup_terraria.exe" (
    del setup_terraria.exe
)

:skip_terraria

echo.
echo ===============================================================
echo   INSTALACION COMPLETADA
echo ===============================================================
echo.
echo PASOS SIGUIENTES:
echo.
echo  1. Si no instalaste Terraria GOG, hazlo manualmente.
echo     Debe quedar en: %CD%\Terraria
echo.
echo  2. Arranca el launcher con:
echo        LANZADOR_PYTHON.bat
echo.
echo  3. Para crear un .exe del launcher, ejecuta:
echo        CREA_UN_EXE.bat
echo.
echo  4. En la pestana Servidor, crea o carga un mundo.
echo.
echo ===============================================================
echo.
pause