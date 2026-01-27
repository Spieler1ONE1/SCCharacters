from PySide6.QtWidgets import QScrollArea, QApplication, QMenu, QAbstractSlider, QStyle, QStyleOptionSlider
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QCursor, QPainter, QColor, QPen
from src.utils.translations import translator

class AutoScrollArea(QScrollArea):
    """
    A QScrollArea that implements browser-style middle-click autoscroll.
    Click mid button -> Move mouse up/down to scroll.
    Click mid button again -> Stop.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Custom Context Menu for Scrollbars (Translated)
        self.verticalScrollBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.verticalScrollBar().customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.verticalScrollBar())
        )
        self.horizontalScrollBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalScrollBar().customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.horizontalScrollBar())
        )
        
        self._scrolling = False
        self._origin_pos = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_scroll)
        self._timer.setInterval(16) # ~60fps
        
        # Visual anchor indicator (optional, but good UX)
        self._anchor_widget = None

    def _show_context_menu(self, pos, scrollbar):
        menu = QMenu(scrollbar)
        
        # Actions
        act_scroll_here = menu.addAction(translator.get("ctx_scroll_here"))
        menu.addSeparator()
        act_top = menu.addAction(translator.get("ctx_top"))
        act_bottom = menu.addAction(translator.get("ctx_bottom"))
        menu.addSeparator()
        act_page_up = menu.addAction(translator.get("ctx_page_up"))
        act_page_down = menu.addAction(translator.get("ctx_page_down"))
        menu.addSeparator()
        act_scroll_up = menu.addAction(translator.get("ctx_scroll_up"))
        act_scroll_down = menu.addAction(translator.get("ctx_scroll_down"))
        
        action = menu.exec(scrollbar.mapToGlobal(pos))
        
        if not action: return
        
        if action == act_scroll_here:
            opt = QStyleOptionSlider()
            scrollbar.initStyleOption(opt)
            
            # Position depending on orientation
            p = pos.y() if scrollbar.orientation() == Qt.Vertical else pos.x()
            span = scrollbar.height() if scrollbar.orientation() == Qt.Vertical else scrollbar.width()
            
            val = scrollbar.style().sliderValueFromPosition(
                scrollbar.minimum(), scrollbar.maximum(), 
                p, span, opt.upsideDown
            )
            scrollbar.setValue(val)
            
        elif action == act_top:
            scrollbar.triggerAction(QAbstractSlider.SliderToMinimum)
        elif action == act_bottom:
            scrollbar.triggerAction(QAbstractSlider.SliderToMaximum)
        elif action == act_page_up:
             scrollbar.triggerAction(QAbstractSlider.SliderPageStepSub)
        elif action == act_page_down:
             scrollbar.triggerAction(QAbstractSlider.SliderPageStepAdd)
        elif action == act_scroll_up:
             scrollbar.triggerAction(QAbstractSlider.SliderSingleStepSub)
        elif action == act_scroll_down:
             scrollbar.triggerAction(QAbstractSlider.SliderSingleStepAdd)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            if self._scrolling:
                self.stop_autoscroll()
            else:
                self.start_autoscroll(event) # Pass local pos for visual anchor if implemented
                # But we need global pos for movement tracking
            event.accept()
            return
            
        # Any other click stops scrolling
        if self._scrolling:
            self.stop_autoscroll()
            # Do NOT propagate event if you want to consume the 'stop' click
            # But usually user might want to click a button immediately.
            # Browser behavior: Click just stops scroll, doesn't trigger underlying element necessarily?
            # Let's stop and consume event to be safe.
            event.accept()
            return
            
        super().mousePressEvent(event)

    def start_autoscroll(self, event):
        self._scrolling = True
        self._origin_pos = event.globalPosition().toPoint()
        
        # Change cursor
        self.setCursor(Qt.SizeVerCursor)
        self._timer.start()

    def stop_autoscroll(self):
        self._scrolling = False
        self._timer.stop()
        self.unsetCursor()

    def _process_scroll(self):
        if not self._scrolling: 
            return
            
        current_pos = QCursor.pos()
        diff = current_pos.y() - self._origin_pos.y()
        
        # Deadzone
        if abs(diff) < 20:
            return
            
        # Speed calculation
        # Subtract deadzone
        val = diff - 20 if diff > 0 else diff + 20
        
        # Sensitivity factor
        speed = int(val * 0.2) 
        
        if speed == 0: 
            return
            
        sb = self.verticalScrollBar()
        sb.setValue(sb.value() + speed)
        
    def wheelEvent(self, event):
        # Using wheel usually cancels autoscroll in browsers
        if self._scrolling:
            self.stop_autoscroll()
        super().wheelEvent(event)
