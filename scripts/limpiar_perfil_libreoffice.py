"""
Script para limpiar el perfil compartido de LibreOffice.
Ejecutar si hay problemas con conversiones o para limpiar cache.
"""

import os
import shutil
import tempfile

def limpiar_perfil_libreoffice():
    """Limpia el perfil compartido de LibreOffice"""
    shared_profile_dir = os.path.join(tempfile.gettempdir(), "LO_shared_profile")
    
    if os.path.exists(shared_profile_dir):
        try:
            shutil.rmtree(shared_profile_dir)
            print(f"✓ Perfil LibreOffice limpiado: {shared_profile_dir}")
        except Exception as e:
            print(f"✗ Error al limpiar perfil: {e}")
    else:
        print(f"ℹ No existe perfil compartido en: {shared_profile_dir}")

if __name__ == "__main__":
    limpiar_perfil_libreoffice()
