import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.conf import settings

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """
    Servicio para interactuar con la API de Google Drive.
    Maneja autenticación y subida de archivos.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    _service_instance = None  # Singleton para mantener la sesión
    
    def __init__(self):
        # Si ya existe una instancia autenticada, no re-autenticar
        if GoogleDriveService._service_instance:
            self.service = GoogleDriveService._service_instance
            return

        self.creds = None
        self.service = None # Initialize service to None before authentication attempt
        self._authenticate()
        # Guardar la instancia autenticada para usos futuros si la autenticación fue exitosa
        if self.service:
            GoogleDriveService._service_instance = self.service
        
    def _authenticate(self):
        """Autentica usando las credenciales configuradas en settings."""
        try:
            creds_path = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS', None)
            
            if not creds_path:
                logger.warning("GOOGLE_DRIVE_CREDENTIALS no configurado en settings.")
                return

            if not os.path.isabs(creds_path):
                # Si es relativa, asumir desde la raíz del proyecto
                creds_path = os.path.join(settings.BASE_DIR, creds_path)

            if not os.path.exists(creds_path):
                logger.error(f"Archivo de credenciales no encontrado en: {creds_path}")
                return

            self.creds = Credentials.from_service_account_file(
                creds_path, scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Autenticación con Google Drive exitosa (Inicial).")
            
        except Exception as e:
            logger.error(f"Error autenticando con Google Drive: {e}")
            raise

    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Busca una carpeta por nombre. Si no existe, la crea.
        """
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            # NOTA: includeItemsFromAllDrives=True y supportsAllDrives=True son obligatorios para Unidades Compartidas
            results = self.service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name)',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            items = results.get('files', [])
            
            if not items:
                # Crear carpeta si no existe
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                folder = self.service.files().create(
                    body=file_metadata, 
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                logger.info(f"Carpeta creada: {folder_name} (ID: {folder.get('id')})")
                return folder.get('id')
            else:
                return items[0]['id']
                
        except Exception as e:
            logger.error(f"Error obteniendo/creando carpeta {folder_name}: {e}")
            raise

    def upload_file(self, file_path: str, file_name: str, mime_type: str, folder_id: str = None) -> dict:
        """
        Sube un archivo a Google Drive.
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo a subir no encontrado: {file_path}")

            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink',
                supportsAllDrives=True
            ).execute()
            
            
            logger.info(f"Archivo subido exitosamente: {file_name} (ID: {file.get('id')})")
            return file
            
        except Exception as e:
            logger.error(f"Error subiendo archivo {file_name}: {e}")
            raise

    def find_items(self, name: str, parent_id: str = None, mime_type: str = None) -> list:
        """
        Busca archivos o carpetas por nombre y padre.
        """
        try:
            query = f"name='{name}' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error buscando item {name}: {e}")
            return []

    def delete_file(self, file_id: str):
        """
        Elimina un archivo o carpeta por su ID (lo mueve a la papelera lo hace 'trashed' o delete permanente).
        Para seguridad usamos 'delete' definitivo o lo dejamos en trash?
        La API de Drive v3 tiene delete() que es permanente.
        """
        try:
            self.service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
            logger.info(f"Item eliminado de Drive: {file_id}")
        except Exception as e:
            logger.error(f"Error eliminando item {file_id}: {e}")
            # No lanzamos excepción para no romper el flujo de borrado local
