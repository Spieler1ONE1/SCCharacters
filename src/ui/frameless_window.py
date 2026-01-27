from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint

class FramelessWindow(QMainWindow):
    """
    A base class for a frameless window with custom resize and drag logic.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._resize_edge = 0
        
        # Setup Fade In Animation
        self.setWindowOpacity(0)
        self.startup_fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.startup_fade_anim.setDuration(800)
        self.startup_fade_anim.setStartValue(0)
        self.startup_fade_anim.setEndValue(1)
        self.startup_fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.startup_fade_anim.start()

    @property
    def _grip_size(self):
        return 5

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        
        # Optional: Update title bar icon if it exists
        if hasattr(self, 'title_bar') and hasattr(self.title_bar, 'set_maximized_icon'):
            self.title_bar.set_maximized_icon(self.isMaximized())

    def _get_resize_edge(self, pos):
        # Calculate which edge the mouse is on
        edge = 0 # 0=None
        rect = self.rect()
        x, y, w, h = pos.x(), pos.y(), rect.width(), rect.height()
        
        # Edges
        left = x < self._grip_size
        right = x > w - self._grip_size
        top = y < self._grip_size
        bottom = y > h - self._grip_size
        
        # Define constants for edges
        if top: edge |= 1
        if bottom: edge |= 2
        if left: edge |= 4
        if right: edge |= 8
        
        return edge

    def _get_qt_edge(self, edge_mask):
        """Maps internal bitmask to Qt.Edge for startSystemResize."""
        if edge_mask == 1: return Qt.TopEdge
        if edge_mask == 2: return Qt.BottomEdge
        if edge_mask == 4: return Qt.LeftEdge
        if edge_mask == 8: return Qt.RightEdge
        if edge_mask == 5: return Qt.TopLeftEdge
        if edge_mask == 9: return Qt.TopRightEdge
        if edge_mask == 6: return Qt.BottomLeftEdge
        if edge_mask == 10: return Qt.BottomRightEdge
        return None

    def _update_cursor(self, edge):
        cursor_map = {
            0: Qt.ArrowCursor,
            1: Qt.SizeVerCursor, # Top
            2: Qt.SizeVerCursor, # Bottom
            4: Qt.SizeHorCursor, # Left
            8: Qt.SizeHorCursor, # Right
            5: Qt.SizeFDiagCursor, # Top-Left
            9: Qt.SizeBDiagCursor, # Top-Right
            6: Qt.SizeBDiagCursor, # Bottom-Left
            10: Qt.SizeFDiagCursor # Bottom-Right
        }
        self.setCursor(cursor_map.get(edge, Qt.ArrowCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge_mask = self._get_resize_edge(event.position().toPoint())
            
            # 1. Check Resize (Native)
            if edge_mask != 0:
                qt_edge = self._get_qt_edge(edge_mask)
                if qt_edge and self.windowHandle().startSystemResize(qt_edge):
                    return

            # 2. Check Move (Native)
            # If not resizing, check if moving (Title bar area assumed < 60px from top)
            # Child classes can override or parameterize this limit
            if event.position().y() < 60:
                if self.windowHandle().startSystemMove():
                    return
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Only needed for Hover Cursor Update now
        if not event.buttons() & Qt.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            self._update_cursor(edge)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self._resize_edge = 0 
        super().mouseReleaseEvent(event)
