@echo off
echo ===============================================
echo   Iniciando Celery Worker
echo ===============================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate

echo Entorno virtual activado.
echo.
echo Verificando que Redis este corriendo...
echo (Asegurate de haber ejecutado start_redis.bat primero)
echo.

REM Iniciar Celery worker con configuración para Windows
echo Iniciando Celery worker...
echo.

celery -A config worker --loglevel=info --pool=solo

echo.
echo Celery worker finalizado.
pause
