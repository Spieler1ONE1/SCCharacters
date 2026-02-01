from PySide6.QtCore import QObject, Signal
from src.core.workers import InstallWorker

class InstallationController(QObject):
    """
    Controlador encargado de la lógica de instalación y desinstalación de personajes.
    Separa la lógica de negocio de la UI.
    """
    install_started = Signal(str) # message
    install_finished = Signal(bool, object) # success, character/error_msg
    uninstall_finished = Signal(bool, str) # success, message

    def __init__(self, character_service, downloader, threadpool, parent=None):
        super().__init__(parent)
        self._character_service = character_service
        self._downloader = downloader
        self._threadpool = threadpool

    def install_character(self, character):
        """
        Orquesta la instalación de un personaje.
        """
        if not character:
            self.install_finished.emit(False, "Datos inválidos para instalación.")
            return

        self.install_started.emit("Iniciando descarga e instalación...")
        
        # Crear y ejecutar Worker
        worker = InstallWorker(self._downloader, character)
        worker.signals.result.connect(self._on_install_success)
        worker.signals.error.connect(self._on_install_error)
        self._threadpool.start(worker)

    def _on_install_success(self, result):
        # Result es una lista [character] según el worker original
        # Emitimos éxito con el objeto personaje
        if result and len(result) > 0:
            self.install_finished.emit(True, result[0])
        else:
            self.install_finished.emit(True, None) # Should not happen usually

    def _on_install_error(self, error_msg):
        self.install_finished.emit(False, str(error_msg))

    def uninstall_character(self, character):
        """
        Maneja la desinstalación usando el servicio.
        """
        try:
            success = self._character_service.uninstall_character(character)
            if success:
                self.uninstall_finished.emit(True, f"Personaje '{character.name}' eliminado correctamente.")
            else:
                self.uninstall_finished.emit(False, "No se pudo eliminar el archivo o no existe.")
        except Exception as e:
            self.uninstall_finished.emit(False, f"Error al eliminar: {str(e)}")
