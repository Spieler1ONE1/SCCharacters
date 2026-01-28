from PySide6.QtCore import QObject, Signal, QThread
import os
import shutil

class InstallationController(QObject):
    """
    Controlador encargado de la lógica de instalación y desinstalación de personajes.
    Separa la lógica de negocio de la UI.
    """
    install_finished = Signal(bool, str) # success, message
    uninstall_finished = Signal(bool, str)

    def __init__(self, character_service, parent=None):
        super().__init__(parent)
        self._character_service = character_service

    def install_character(self, character_data, game_path):
        """
        Orquesta la instalación de un personaje.
        """
        if not character_data or not game_path:
            self.install_finished.emit(False, "Datos inválidos para instalación.")
            return

        # Aquí iría la lógica que antes estaba en MainWindow o workers
        # Por simplicidad en este paso inicial, delegamos al servicio directamente
        # o preparamos el worker.
        
        # Nota: En una refactorización completa, moveríamos la creación del worker aquí
        # o llamaríamos al servicio si es bloqueante (aunque debería ser async).
        
        try:
            # Lógica simulada de servicio (en realidad debería usar Workers como antes)
            # self._character_service.install(...) 
            # Por ahora emitimos éxito para probar el flujo si se llamara
            pass 
        except Exception as e:
            self.install_finished.emit(False, str(e))

    def uninstall_character(self, character_path):
        """
        Maneja la desinstalación.
        """
        try:
            if os.path.exists(character_path):
                shutil.rmtree(character_path)
                self.uninstall_finished.emit(True, "Personaje eliminado correctamente.")
            else:
                self.uninstall_finished.emit(False, "El directorio no existe.")
        except Exception as e:
            self.uninstall_finished.emit(False, f"Error al eliminar: {e}")
