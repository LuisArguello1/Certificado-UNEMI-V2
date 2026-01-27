@echo off
echo ===============================================
echo   Iniciando Redis Server
echo ===============================================
echo.

REM --- PASO 0: VERIFICAR PUERTO ---
netstat -an | find "6379" | find "LISTENING" >nul
if %ERRORLEVEL% EQU 0 goto :REDIS_RUNNING

REM --- PASO 1: BUSCAR EN RUTAS COMUNES ---
if exist "C:\Program Files\Redis\redis-server.exe" goto :FOUND_PF
if exist "C:\Redis\redis-server.exe" goto :FOUND_C
if exist "C:\Program Files (x86)\Redis\redis-server.exe" goto :FOUND_X86

REM --- PASO 2: INTENTAR PATH ---
where redis-server >nul 2>nul
if %ERRORLEVEL% EQU 0 goto :FOUND_PATH

goto :NOT_FOUND

:REDIS_RUNNING
echo [INFO] Redis YA ESTA CORRIENDO (Puerto 6379 en uso).
echo Puedes cerrar esta ventana.
pause
goto :EOF

:FOUND_PF
echo Encontrado en C:\Program Files\Redis
"C:\Program Files\Redis\redis-server.exe"
goto :EOF

:FOUND_C
echo Encontrado en C:\Redis
"C:\Redis\redis-server.exe"
goto :EOF

:FOUND_X86
echo Encontrado en C:\Program Files (x86)\Redis
"C:\Program Files (x86)\Redis\redis-server.exe"
goto :EOF

:FOUND_PATH
echo Redis encontrado en el PATH.
redis-server
goto :EOF

:NOT_FOUND
echo ERROR: No se encontro Redis Server.
echo Instalar desde: https://github.com/microsoftarchive/redis/releases
pause
exit /b 1
