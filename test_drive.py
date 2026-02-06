# test_drive.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.certificado.services.google_drive_service import GoogleDriveService
from django.conf import settings

# Crear servicio
drive = GoogleDriveService()

# Crear carpeta de prueba dentro de la carpeta configurada
root_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
print(f"Usando carpeta raíz configurada: {root_id}")

folder_id = drive.get_or_create_folder('Prueba_Integracion', parent_id=root_id)
print(f"Carpeta creada/encontrada: {folder_id}")

# Subir archivo de prueba
with open('test.txt', 'w') as f:
    f.write('Hola desde Django')

result = drive.upload_file('test.txt', 'prueba.txt', 'text/plain', folder_id)
print(f"Resultado: {result}")

# Limpiar
os.remove('test.txt')