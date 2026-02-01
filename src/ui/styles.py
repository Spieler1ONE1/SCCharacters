from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class ThemeColors:
    """
    Defines the color palette for the application themes.
    Supports: 'default' (BioMetrics Dark), 'drake', 'origin', 'aegis', 'light'
    """
    def __init__(self, theme_mode: str = "default"):
        self.theme_mode = theme_mode
        self.is_dark = theme_mode != "light"
        
        # --- Defaults (BioMetrics Dark / Premium) ---
        self.bg_primary = "#0f172a"    # Deep Navy/Slate
        self.bg_secondary = "#1e293b"  # Lighter Slate
        self.bg_tertiary = "#334155"   # Interactive Elements
        self.text_primary = "#f8fafc"
        self.text_secondary = "#94a3b8"
        self.text_disabled = "#475569"
        self.accent = "#6366f1"        # Electric Blue/Indigo
        self.accent_hover = "#818cf8"
        self.accent_pressed = "#4f46e5"
        self.border = "#334155"
        self.input_bg = "#1e293b"
        self.success = "#10b981"
        self.error = "#ef4444"
        self.warning = "#f59e0b"
        self.overlay_bg = "rgba(15, 23, 42, 0.90)"
        self.card_gradient_start = "rgba(0, 0, 0, 0.60)"
        self.card_gradient_end = "rgba(15, 23, 42, 0.85)"
        self.card_hover_bg = "rgba(255, 255, 255, 0.05)"

        # --- Theme Overrides ---
        if theme_mode == "light":
            # Clean Light Theme
            self.bg_primary = "#f8fafc"
            self.bg_secondary = "#ffffff"
            self.bg_tertiary = "#f1f5f9"
            self.text_primary = "#0f172a"
            self.text_secondary = "#475569"
            self.text_disabled = "#94a3b8"
            self.accent = "#4f46e5"
            self.accent_hover = "#4338ca"
            self.accent_pressed = "#3730a3"
            self.border = "#cbd5e1"
            self.input_bg = "#ffffff"
            self.success = "#059669"
            self.error = "#dc2626"
            self.warning = "#d97706"
            self.overlay_bg = "rgba(255, 255, 255, 0.95)"
            self.card_gradient_start = "rgba(255, 255, 255, 0.80)"
            self.card_gradient_end = "rgba(248, 250, 252, 0.90)"
            self.card_hover_bg = "rgba(255, 255, 255, 0.60)"
            
        elif theme_mode == "drake":
            # Drake Interplanetary: Industrial, Green, Amber, Gritty
            self.bg_primary = "#1a1c10"    # Dark Olive/Black
            self.bg_secondary = "#26291b"  # Olive Drab
            self.bg_tertiary = "#3a3d2c"   # Worn Green
            self.text_primary = "#d4d8c0"  # Pale Green/White
            self.text_secondary = "#8c9175" # Mossy Grey
            self.input_bg = "#12140b"
            self.border = "#444a33"
            self.accent = "#a3b808"        # Industrial Neon Yellow/Green
            self.accent_hover = "#bccc29"
            self.accent_pressed = "#7a8a06"
            self.warning = "#e67e22"       # Amber
            self.card_gradient_start = "rgba(10, 12, 5, 0.70)"
            self.card_gradient_end = "rgba(38, 41, 27, 0.85)"
            
        elif theme_mode == "origin":
             # Origin Jumpworks: Luxury, Ultra-Clean White/Grey, Cyan/Blue glow
             # Dark Luxury variant (Star Citizen menus are often dark even for Origin, but let's go sleek dark grey)
             self.bg_primary = "#18181b"    # Zinc 900
             self.bg_secondary = "#27272a"  # Zinc 800
             self.bg_tertiary = "#3f3f46"   # Zinc 700
             self.text_primary = "#ffffff"
             self.text_secondary = "#a1a1aa"
             self.border = "#52525b"
             self.input_bg = "#09090b"
             self.accent = "#06b6d4"        # Cyan 500 (High tech)
             self.accent_hover = "#22d3ee"
             self.accent_pressed = "#0891b2"
             self.card_gradient_start = "rgba(24, 24, 27, 0.60)"
             self.card_gradient_end = "rgba(39, 39, 42, 0.85)"
             
        elif theme_mode == "aegis":
            # Aegis Dynamics: Military, Gunmetal Blue, Tactical Red/Orange Highlights? 
            # Or Classic Aegis UI is often Blue/Cyan. Let's go with a Navy/Tactical look.
            self.bg_primary = "#0a0a0f"    # Almost Black Blue
            self.bg_secondary = "#111827"  # Cool Gray 900
            self.bg_tertiary = "#1f2937"   # Cool Gray 800
            self.text_primary = "#e5e7eb"
            self.text_secondary = "#9ca3af"
            self.border = "#374151"
            self.input_bg = "#030712"
            self.accent = "#3b82f6"        # Royal Blue
            self.accent_hover = "#60a5fa"
            self.accent_pressed = "#2563eb"
            self.card_gradient_start = "rgba(17, 24, 39, 0.70)"
            self.card_gradient_end = "rgba(31, 41, 55, 0.85)"

def get_stylesheet(theme_mode: str) -> str:
    c = ThemeColors(theme_mode)
    
    return f"""
    QMainWindow {{
        background-color: {c.bg_primary};
        color: {c.text_primary};
    }}
    
    QWidget {{
        font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        font-size: 14px;
        color: {c.text_primary};
    }}

    /* --- Title Bar --- */
    QWidget#TitleBar {{
        background-color: {c.bg_secondary};
        border-bottom: 1px solid {c.border};
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }}
    
    QLabel#TitleLabel {{
        font-weight: 700;
        font-size: 14px;
        color: {c.text_primary};
        letter-spacing: 0.5px;
    }}
    
    QPushButton#TitleBarButton {{
        background-color: transparent;
        border: none;
        color: {c.text_secondary};
        font-size: 12px;
        padding: 10px 16px;
        border-radius: 0px;
    }}
    QPushButton#TitleBarButton:hover {{
        background-color: {c.bg_tertiary};
        color: {c.text_primary};
    }}
    
    QPushButton#TitleBarCloseButton {{
        background-color: transparent;
        border: none;
        color: {c.text_secondary};
        font-size: 14px;
        padding: 10px 16px;
        border-top-right-radius: 12px;
    }}
    QPushButton#TitleBarCloseButton:hover {{
        background-color: {c.error};
        color: white;
    }}

    /* --- Menu Bar --- */
    QMenuBar#CustomMenuBar {{
        background-color: {c.bg_secondary};
        border-bottom: 1px solid {c.border};
        padding: 4px 10px;
    }}
    QMenuBar#CustomMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        margin-right: 4px;
        border-radius: 6px;
        color: {c.text_primary};
    }}
    QMenuBar#CustomMenuBar::item:selected {{
        background-color: {c.bg_tertiary};
    }}
    
    /* --- Main Content Area --- */
    /* --- Main Content Area --- */
    QWidget#CentralWidget {{
        /* Premium Background Gradient */
        background-color: qradialgradient(cx:0.5, cy:0, radius: 1.2, fx:0.5, fy:0, stop:0 #1e293b, stop:1 #0f172a);
        border: 1px solid {c.border};
        border-radius: 12px;
    }}

    QWidget#OnlineTab, QWidget#ContentWidget, QWidget#GridWidget,
    QWidget#InstalledTab, QWidget#InstalledContentWidget {{
         background-color: transparent;
    }}
    
    /* Dialogs */
    QDialog {{
        background-color: {c.bg_primary};
    }}

    /* --- Cards --- */
    QFrame#CharacterCard {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c.card_gradient_start}, stop:1 {c.card_gradient_end});
        border: 1px solid {c.border};
        border-radius: 16px;
    }}
    QFrame#CharacterCard:hover {{
        border: 1px solid {c.accent};
        background-color: {c.card_hover_bg};
    }}
    
    /* --- Buttons --- */
    QPushButton {{
        background-color: {c.bg_secondary};
        border: 1px solid {c.border};
        color: {c.text_primary};
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {c.bg_tertiary};
        border-color: {c.text_secondary};
    }}
    QPushButton:pressed {{
        background-color: {c.bg_tertiary};
        border-color: {c.accent};
        color: {c.accent};
    }}
    QPushButton:disabled {{
        background-color: {c.bg_primary};
        color: {c.text_disabled};
        border-color: {c.border};
    }}
    
    /* Primary Action */
    QPushButton#actionButton {{
        background-color: {c.accent};
        border: 1px solid {c.accent};
        color: white;
    }}
    QPushButton#actionButton:hover {{
        background-color: {c.accent_hover};
        border-color: {c.accent_hover};
    }}
    QPushButton#actionButton:pressed {{
        background-color: {c.accent_pressed};
    }}
    QPushButton#actionButton:disabled {{
        background-color: {c.bg_tertiary};
        color: {c.text_disabled};
        border-color: {c.border};
    }}
    
    /* Destructive/Delete Button */
    QPushButton#deleteButton {{
        background-color: transparent;
        border: 1px solid {c.error};
        color: {c.error};
        border-radius: 6px;
        font-size: 16px;
        padding: 4px;
    }}
    QPushButton#deleteButton:hover {{
        background-color: {c.error};
        color: #ffffff;
    }}
    
    /* --- Inputs --- */
    QLineEdit, QComboBox {{
        background-color: {c.input_bg};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 8px 12px;
        color: {c.text_primary};
        selection-background-color: {c.accent};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {c.accent};
    }}
    QLineEdit::placeholder {{
        color: {c.text_disabled};
    }}

    /* --- ComboBox Dropdown --- */
    /* --- ComboBox Dropdown --- */
    QComboBox QAbstractItemView {{
        background-color: {c.bg_secondary};
        color: {c.text_primary};
        border: 1px solid {c.border};
        selection-background-color: {c.accent};
        selection-color: white;
        outline: none;
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 0px;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}
    
    /* --- Tabs --- */
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c.text_secondary};
        padding: 12px 20px;
        border-bottom: 2px solid transparent;
        font-weight: 600;
        font-size: 15px;
    }}
    QTabBar::tab:selected {{
        color: {c.accent};
        border-bottom: 2px solid {c.accent};
    }}
    QTabBar::tab:hover:!selected {{
        color: {c.text_primary};
    }}
    
    QTabBar::tab:last {{
        margin-left: 100px;
    }}
    
    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        background: {c.bg_primary};
        width: 10px;
        margin: 0;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {c.border};
        min-height: 30px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.text_secondary};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    /* --- Menus --- */
    QMenu {{
        background-color: {c.bg_secondary};
        border: 1px solid {c.border};
        border-radius: 8px;
        padding: 5px;
        color: {c.text_primary};
    }}
    QMenu::item {{
        padding: 6px 20px 6px 10px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c.accent};
        color: white;
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.border};
        margin: 4px 0px;
    }}
    
    /* --- Status Bar --- */
    QStatusBar {{
        background-color: {c.bg_secondary}; 
        color: {c.text_secondary};
        border-top: 1px solid {c.border};
    }}
    
    /* --- Toast --- */
    QLabel#Toast {{
        background-color: {c.bg_secondary};
        color: {c.text_primary};
        border: 1px solid {c.accent};
        border-radius: 8px;
        padding: 12px;
    }}

    /* --- Stat Badges --- */
    QLabel#StatBadge {{
        background-color: transparent; 
        color: {c.text_secondary};
        border: 1px solid {c.border};
        border-radius: 10px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: 500;
    }}
    
    /* --- Modern Character Card --- */
    QFrame#CharacterCard {{
        background-color: {c.bg_secondary};
        border: 1px solid {c.border};
        border-radius: 16px;
    }}
    
    QFrame#CharacterCard:hover {{
        background-color: {c.bg_tertiary};
        border: 1px solid {c.text_disabled}; /* Softer grey instead of intense accent */
    }}
    
    /* Typography Overrides for Cards */
    QLabel#CardTitle {{
        font-size: 14px; /* Reduced from 15 to 14 */
        font-weight: 600;
        color: {c.text_primary};
    }}
    
    QLabel#CardAuthor {{
        font-size: 11px;
        font-weight: 400;
        color: {c.text_secondary}; 
    }}
    """
