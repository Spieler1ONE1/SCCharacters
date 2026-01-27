import requests
import packaging.version
import hashlib
import os
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from src.version import APP_VERSION

logger = logging.getLogger(__name__)

class UpdateManager:
    # URL del archivo JSON con la información de la última versión
    MANIFEST_URL = "https://raw.githubusercontent.com/Spieler1ONE1/SCCharacters/main/version.json"
    
    def __init__(self):
        self.current_version = APP_VERSION
        self.downloaded_file_path: Optional[str] = None

    def check_for_updates(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Consulta el servidor para ver si hay una versión nueva.
        Retorna (HayActualizacion, DatosDelManifest).
        """
        if "TuUsuario/TuRepo" in self.MANIFEST_URL:
            logger.info("Update check skipped: Repository URL not configured.")
            return False, None
            
        try:
            response = requests.get(self.MANIFEST_URL, timeout=5)
            response.raise_for_status()
            manifest = response.json()
            
            latest_version_str = manifest.get("latest_version")
            if not latest_version_str:
                logger.error("Manifest inválido: falta 'latest_version'")
                return False, None

            latest_ver = packaging.version.parse(latest_version_str)
            current_ver = packaging.version.parse(self.current_version)

            if latest_ver > current_ver:
                logger.info(f"Nueva versión encontrada: {latest_version_str}")
                return True, manifest
            
            return False, manifest

        except requests.RequestException as e:
            logger.warning(f"No se pudo comprobar actualizaciones: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error inesperado al comprobar actualizaciones: {e}")
            return False, None

    def download_update(self, download_url: str, progress_callback=None) -> Optional[str]:
        """
        Descarga el instalador a un archivo temporal.
        Retorna la ruta del archivo descargado si es exitoso.
        """
        try:
            with requests.get(download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                
                # Crear archivo temporal
                fd, path = tempfile.mkstemp(suffix=".exe")
                
                with os.fdopen(fd, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length and progress_callback:
                                percent = int((downloaded / int(total_length)) * 100)
                                progress_callback(percent)
                
                return path
        except Exception as e:
            logger.error(f"Error descargando actualización: {e}")
            return None

    def verify_integrity(self, file_path: str, expected_hash: str) -> bool:
        """
        Verifica el SHA256 del archivo descargado.
        """
        if not expected_hash:
            logger.warning("No se proporcionó hash para verificación. Omitiendo (INSEGURO).")
            return True # O cambiar a False si quieres seguridad estricta

        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Leer y actualizar hash por bloques
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated_hash = sha256_hash.hexdigest()
            if calculated_hash.lower() == expected_hash.lower():
                return True
            else:
                logger.error(f"Hash mismatch! Esperado: {expected_hash}, Calculado: {calculated_hash}")
                return False
        except Exception as e:
            logger.error(f"Error verificando hash: {e}")
            return False
