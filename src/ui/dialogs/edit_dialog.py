
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from src.core.models import Character
from src.utils.translations import translator
from src.ui.styles import ThemeColors

class EditCharacterDialog(QDialog):
    def __init__(self, character: Character, parent=None):
        super().__init__(parent)
        self.character = character
        self.setWindowTitle(translator.get("edit_character_title", default="Edit Character"))
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Determine theme
        is_dark = True # Default
        if self.parent() and hasattr(self.parent(), 'theme_manager'):
             is_dark = (self.parent().theme_manager.get_effective_theme() == 'dark') # heuristic
        c = ThemeColors(is_dark)
        
        # Name
        layout.addWidget(QLabel(translator.get("name")))
        self.input_name = QLineEdit(self.character.name)
        layout.addWidget(self.input_name)

        # Author
        layout.addWidget(QLabel("Author"))
        self.input_author = QLineEdit(self.character.author if self.character.author else "Unknown")
        layout.addWidget(self.input_author)
        
        # Description (We need to fetch it first? Character model doesn't store description in list view always)
        # We assume the caller might have full details or we just edit what we have.
        # Ideally we read the json here to be sure.
        # For now, let's pass current value or empty.
        layout.addWidget(QLabel(translator.get("description", default="Description")))
        self.input_desc = QTextEdit()
        # Initial value populated by caller usually
        layout.addWidget(self.input_desc)
        
        # Tags
        layout.addWidget(QLabel(translator.get("tags_comma", default="Tags (comma separated)")))
        tags_str = ", ".join(self.character.tags) if self.character.tags else ""
        self.input_tags = QLineEdit(tags_str)
        layout.addWidget(self.input_tags)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(translator.get("save"))
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(translator.get("cancel"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
    def get_data(self):
        tags = [t.strip() for t in self.input_tags.text().split(',') if t.strip()]
        return {
            "name": self.input_name.text(),
            "author": self.input_author.text(),
            "description": self.input_desc.toPlainText(),
            "tags": tags
        }
