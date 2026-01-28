# Optimización de Rendimiento - Resumen

## Problema con Workers Paralelos en Windows

Windows + Celery tiene **problemas conocidos** con `--concurrency > 1` usando el pool de procesos predeterminado.

**Error**:
```
PermissionError: [WinError 5] Acceso denegado
OSError: [WinError 6] Controlador no válido
```

## Solución: Usar Eventlet o Gevent

En Windows, en lugar de usar workers basados en procesos, usa **concurrencia basada en greenlets**:

### Opción 1: Eventlet (Recomendado para Windows)

```bash
# Instalar eventlet
pip install eventlet

# Ejecutar Celery con pool eventlet y 100 trabajos concurrentes
celery -A config worker -l INFO --pool=eventlet --concurrency=100
```

### Opción 2: Gevent

```bash
# Instalar gevent
pip install gevent

# Ejecutar Celery con pool gevent
celery -A config worker -l INFO --pool=gevent --concurrency=100
```

## Optimizaciones Implementadas

1. ✅ **Logs eliminados** - Todos los logs INFO innecesarios removidos
2. ✅ **Perfil compartido LibreOffice** - Reduce overhead de creación/limpieza
3. ✅ **Flags optimizados** - `--norestore`, `--nofirststartwizard`, `--nologo`, `--nolockcheck`
4. ✅ **Timeout reducido** - De 180s a 30s

## Resultado Esperado

- **Sin workers paralelos**: ~9-10s por certificado (mejor que los 11-12s originales)
- **Con eventlet (100 concurrencia)**: Procesamiento paralelo real en Windows
- **70 certificados**: ~10-12 minutos → **~2-3 minutos**

## Comando Final

```bash
pip install eventlet
celery -A config worker -l INFO --pool=eventlet --concurrency=100
```
