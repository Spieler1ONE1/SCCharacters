from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QKeySequence, QGuiApplication
from PySide6.QtCore import Qt
from src.utils.translations import translator

# Valid only for QLineEdit usage mostly
def setup_localized_context_menu(widget):
    """
    Attaches a localized custom context menu to a QLineEdit.
    """
    widget.setContextMenuPolicy(Qt.CustomContextMenu)
    # Disconnect if existing to avoid dupes (safeguard)
    if widget.property("_ctx_menu_connected"):
        try:
            widget.customContextMenuRequested.disconnect() 
        except: 
            pass
        
    widget.customContextMenuRequested.connect(lambda pos: _show_edit_menu(widget, pos))
    widget.setProperty("_ctx_menu_connected", True)

def _show_edit_menu(widget, pos):
    menu = QMenu(widget)
    
    # Undo
    act_undo = menu.addAction(translator.get('ctx_undo'))
    # Use standard key sequences for display hints
    act_undo.setShortcut(QKeySequence(QKeySequence.Undo))
    act_undo.setEnabled(widget.isUndoAvailable())
    act_undo.triggered.connect(widget.undo)
    
    # Redo
    act_redo = menu.addAction(translator.get('ctx_redo'))
    act_redo.setShortcut(QKeySequence(QKeySequence.Redo))
    act_redo.setEnabled(widget.isRedoAvailable())
    act_redo.triggered.connect(widget.redo)
    
    menu.addSeparator()
    
    # Cut
    act_cut = menu.addAction(translator.get('ctx_cut'))
    act_cut.setShortcut(QKeySequence(QKeySequence.Cut))
    has_sel = widget.hasSelectedText()
    act_cut.setEnabled(has_sel)
    act_cut.triggered.connect(widget.cut)
    
    # Copy
    act_copy = menu.addAction(translator.get('ctx_copy'))
    act_copy.setShortcut(QKeySequence(QKeySequence.Copy))
    act_copy.setEnabled(has_sel)
    act_copy.triggered.connect(widget.copy)
    
    # Paste
    act_paste = menu.addAction(translator.get('ctx_paste'))
    act_paste.setShortcut(QKeySequence(QKeySequence.Paste))
    
    # Check clipboard
    clipboard = QGuiApplication.clipboard()
    # Simple text check. 
    can_paste = bool(clipboard.mimeData().hasText())
    act_paste.setEnabled(can_paste)
    act_paste.triggered.connect(widget.paste)
    
    # Delete
    act_delete = menu.addAction(translator.get('ctx_delete'))
    act_delete.setShortcut(QKeySequence.Delete)
    act_delete.setEnabled(has_sel)
    
    if hasattr(widget, 'del_'):
        act_delete.triggered.connect(widget.del_)
    else:
        # Fallback: Replace selection with empty string
        act_delete.triggered.connect(lambda: widget.insert(""))
    
    menu.addSeparator()
    
    # Select All
    act_sel = menu.addAction(translator.get('ctx_select_all'))
    act_sel.setShortcut(QKeySequence(QKeySequence.SelectAll))
    act_sel.triggered.connect(widget.selectAll)
    
    menu.exec(widget.mapToGlobal(pos))
