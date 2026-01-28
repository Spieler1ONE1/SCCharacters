import pytest
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget
from src.ui.controllers.navigation_controller import NavigationController

class MockMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabs_widget = QTabWidget()
        self.setCentralWidget(self.tabs_widget)
        # Add some dummy tabs
        self.tabs_widget.addTab(QWidget(), "Tab 1")
        self.tabs_widget.addTab(QWidget(), "Tab 2")

def test_navigation_switching(qtbot):
    """Test switching tabs via controller."""
    window = MockMainWindow()
    qtbot.addWidget(window)
    
    controller = NavigationController(window)
    
    with qtbot.waitSignal(controller.tab_changed) as blocker:
        controller.switch_tab(1)
        
    assert blocker.args == [1]
    assert window.tabs_widget.currentIndex() == 1
    
def test_navigation_bounds(qtbot):
    """Test invalid index safety."""
    window = MockMainWindow()
    qtbot.addWidget(window)
    controller = NavigationController(window)
    
    current = window.tabs_widget.currentIndex()
    controller.switch_tab(99) # Invalid
    
    assert window.tabs_widget.currentIndex() == current
