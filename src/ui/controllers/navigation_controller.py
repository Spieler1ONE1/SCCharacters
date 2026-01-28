from PySide6.QtCore import QObject, Signal

class NavigationController(QObject):
    """
    Controlador encargado de la navegación y gestión de vistas en la ventana principal.
    Desacopla la lógica de cambio de pestañas y botones de la UI directa.
    """
    # Señales para comunicar cambios a la vista
    tab_changed = Signal(int)
    view_requested = Signal(str) # ej: 'settings', 'home', etc.

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        self._current_tab_index = 0
    
    def switch_tab(self, index: int):
        """Cambia la pestaña activa de forma segura."""
        if 0 <= index < self._main_window.tabs_widget.count():
            self._main_window.tabs_widget.setCurrentIndex(index)
            self._current_tab_index = index
            self.tab_changed.emit(index)
            
    def go_to_installed(self):
        # Asumiendo que installed es indice 0, o buscar por nombre
        self.switch_tab(0)
        
    def go_to_online(self):
        self.switch_tab(1)
