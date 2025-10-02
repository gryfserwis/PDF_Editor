#!/usr/bin/env python3
"""
GRYF PDF Editor - Qt Version
Complete implementation with drag & drop support for files and pages
Based on PDFEditor.py but using PySide6 for modern UI
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QFileDialog, QMessageBox,
    QMenu, QToolBar, QStatusBar, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QRadioButton, QCheckBox, QGroupBox,
    QGridLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QSize, QMimeData, QByteArray, QBuffer, QIODevice,
    Signal, QPoint, QRect, QTimer, QEvent
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QBrush, QPen,
    QAction, QKeySequence, QDragEnterEvent, QDropEvent,
    QDrag, QMouseEvent, QPalette, QIcon
)

import fitz  # PyMuPDF
from PIL import Image
import io
import os
import sys
import math
import re
from typing import Optional, List, Set, Dict, Union
from datetime import date
import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject, NameObject

# ====================================================================
# CONSTANTS AND CONFIGURATION
# ====================================================================

# Base directory setup
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FOLDER = os.path.join(BASE_DIR, "icons")

# Program information
PROGRAM_TITLE = "GRYF PDF Editor (Qt)"
PROGRAM_VERSION = "5.0.0"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# PDF Constants
A4_WIDTH_POINTS = 595.276
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4  # ~2.8346

def mm2pt(mm):
    return float(mm) * MM_TO_POINTS

# UI Colors
BG_PRIMARY = '#F0F0F0'
BG_SECONDARY = '#E0E0E0'
BG_BUTTON_DEFAULT = "#D0D0D0"
FG_TEXT = "#444444"
FOCUS_HIGHLIGHT_COLOR = "#000000"
FOCUS_HIGHLIGHT_WIDTH = 2

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\\n\\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# ====================================================================
# DIALOG CLASSES
# ====================================================================

class PageNumberingDialog(QDialog):
    """Dialog for adding page numbers to PDF"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodawanie numeracji stron")
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Marginesy poziome
        margin_group = QGroupBox("Marginesy poziome (mm)")
        margin_layout = QHBoxLayout()
        self.margin_left = QLineEdit("35")
        self.margin_right = QLineEdit("25")
        margin_layout.addWidget(QLabel("Lewy:"))
        margin_layout.addWidget(self.margin_left)
        margin_layout.addWidget(QLabel("Prawy:"))
        margin_layout.addWidget(self.margin_right)
        self.mirror_margins = QCheckBox("Plik ma marginesy lustrzane")
        margin_group_vbox = QVBoxLayout()
        margin_group_vbox.addLayout(margin_layout)
        margin_group_vbox.addWidget(self.mirror_margins)
        margin_group.setLayout(margin_group_vbox)
        layout.addWidget(margin_group)
        
        # Położenie
        pos_group = QGroupBox("Położenie numeru strony")
        pos_layout = QGridLayout()
        
        pos_layout.addWidget(QLabel("Od krawędzi (mm):"), 0, 0)
        self.margin_vertical = QLineEdit("15")
        pos_layout.addWidget(self.margin_vertical, 0, 1)
        
        pos_layout.addWidget(QLabel("Pion:"), 1, 0)
        self.pos_top = QRadioButton("Nagłówek")
        self.pos_bottom = QRadioButton("Stopka")
        self.pos_bottom.setChecked(True)
        pos_h1 = QHBoxLayout()
        pos_h1.addWidget(self.pos_top)
        pos_h1.addWidget(self.pos_bottom)
        pos_layout.addLayout(pos_h1, 1, 1)
        
        pos_layout.addWidget(QLabel("Poziom:"), 2, 0)
        self.align_left = QRadioButton("Lewo")
        self.align_center = QRadioButton("Środek")
        self.align_right = QRadioButton("Prawo")
        self.align_right.setChecked(True)
        pos_h2 = QHBoxLayout()
        pos_h2.addWidget(self.align_left)
        pos_h2.addWidget(self.align_center)
        pos_h2.addWidget(self.align_right)
        pos_layout.addLayout(pos_h2, 2, 1)
        
        pos_layout.addWidget(QLabel("Tryb:"), 3, 0)
        self.mode_normal = QRadioButton("Normalna")
        self.mode_mirror = QRadioButton("Lustrzana")
        self.mode_normal.setChecked(True)
        pos_h3 = QHBoxLayout()
        pos_h3.addWidget(self.mode_normal)
        pos_h3.addWidget(self.mode_mirror)
        pos_layout.addLayout(pos_h3, 3, 1)
        
        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)
        
        # Wartość numeracji
        counter_group = QGroupBox("Wartość numeracji")
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("Licznik zacznij od:"))
        self.start_number = QSpinBox()
        self.start_number.setMinimum(1)
        self.start_number.setValue(1)
        counter_layout.addWidget(self.start_number)
        counter_group.setLayout(counter_layout)
        layout.addWidget(counter_group)
        
        # Czcionka
        font_group = QGroupBox("Czcionka i format numeracji")
        font_layout = QGridLayout()
        font_layout.addWidget(QLabel("Czcionka:"), 0, 0)
        self.font_name = QComboBox()
        self.font_name.addItems(["Helvetica", "Times-Roman", "Courier", "Arial"])
        self.font_name.setCurrentText("Times-Roman")
        font_layout.addWidget(self.font_name, 0, 1)
        
        font_layout.addWidget(QLabel("Rozmiar [pt]:"), 0, 2)
        self.font_size = QComboBox()
        self.font_size.addItems(["6", "8", "10", "11", "12", "13", "14"])
        self.font_size.setCurrentText("12")
        font_layout.addWidget(self.font_size, 0, 3)
        
        font_layout.addWidget(QLabel("Format:"), 1, 0)
        self.format_simple = QRadioButton("Standardowy (1, 2...)")
        self.format_full = QRadioButton("Strona 1 z 99")
        self.format_simple.setChecked(True)
        format_h = QHBoxLayout()
        format_h.addWidget(self.format_simple)
        format_h.addWidget(self.format_full)
        font_layout.addLayout(format_h, 1, 1, 1, 3)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def accept_dialog(self):
        try:
            self.result = {
                'margin_left_mm': float(self.margin_left.text().replace(',', '.')),
                'margin_right_mm': float(self.margin_right.text().replace(',', '.')),
                'margin_vertical_mm': float(self.margin_vertical.text().replace(',', '.')),
                'vertical_pos': 'gora' if self.pos_top.isChecked() else 'dol',
                'alignment': 'lewa' if self.align_left.isChecked() else ('srodek' if self.align_center.isChecked() else 'prawa'),
                'mode': 'lustrzana' if self.mode_mirror.isChecked() else 'normalna',
                'start_num': self.start_number.value(),
                'start_page_idx': 0,
                'font_name': self.font_name.currentText(),
                'font_size': float(self.font_size.currentText()),
                'mirror_margins': self.mirror_margins.isChecked(),
                'format_type': 'full' if self.format_full.isChecked() else 'simple'
            }
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Błąd", f"Nieprawidłowe wartości: {e}")


class ShiftContentDialog(QDialog):
    """Dialog for shifting page content"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przesuwanie zawartości stron")
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Kierunek i wartość przesunięcia (mm)")
        grid = QGridLayout()
        
        # Horizontal shift
        grid.addWidget(QLabel("Poziome:"), 0, 0)
        self.x_value = QLineEdit("0")
        grid.addWidget(self.x_value, 0, 1)
        self.x_left = QRadioButton("Lewo")
        self.x_right = QRadioButton("Prawo")
        self.x_right.setChecked(True)
        x_h = QHBoxLayout()
        x_h.addWidget(self.x_left)
        x_h.addWidget(self.x_right)
        grid.addLayout(x_h, 0, 2)
        
        # Vertical shift
        grid.addWidget(QLabel("Pionowe:"), 1, 0)
        self.y_value = QLineEdit("0")
        grid.addWidget(self.y_value, 1, 1)
        self.y_down = QRadioButton("Dół")
        self.y_up = QRadioButton("Góra")
        self.y_up.setChecked(True)
        y_h = QHBoxLayout()
        y_h.addWidget(self.y_down)
        y_h.addWidget(self.y_up)
        grid.addLayout(y_h, 1, 2)
        
        group.setLayout(grid)
        layout.addWidget(group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def accept_dialog(self):
        try:
            x_mm = float(self.x_value.text().replace(',', '.'))
            y_mm = float(self.y_value.text().replace(',', '.'))
            if x_mm < 0 or y_mm < 0:
                raise ValueError("Wartości muszą być nieujemne")
            self.result = {
                'x_dir': 'L' if self.x_left.isChecked() else 'P',
                'y_dir': 'D' if self.y_down.isChecked() else 'G',
                'x_mm': x_mm,
                'y_mm': y_mm
            }
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Błąd", f"Nieprawidłowe wartości: {e}")


class PageNumberMarginDialog(QDialog):
    """Dialog for removing page numbers"""
    
    def __init__(self, parent=None, initial_margin_mm=20):
        super().__init__(parent)
        self.setWindowTitle("Usuwanie numeracji stron")
        self.result = None
        self.setup_ui(initial_margin_mm)
        
    def setup_ui(self, initial_margin):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Wysokość pola z numerem (mm)")
        grid = QGridLayout()
        
        grid.addWidget(QLabel("Od góry (nagłówek):"), 0, 0)
        self.top_margin = QLineEdit(str(initial_margin))
        grid.addWidget(self.top_margin, 0, 1)
        
        grid.addWidget(QLabel("Od dołu (stopka):"), 1, 0)
        self.bottom_margin = QLineEdit(str(initial_margin))
        grid.addWidget(self.bottom_margin, 1, 1)
        
        group.setLayout(grid)
        layout.addWidget(group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def accept_dialog(self):
        try:
            top = float(self.top_margin.text().replace(',', '.'))
            bottom = float(self.bottom_margin.text().replace(',', '.'))
            if top < 0 or bottom < 0:
                raise ValueError("Wartości muszą być nieujemne")
            self.result = {'top_mm': top, 'bottom_mm': bottom}
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Błąd", f"Nieprawidłowe wartości: {e}")



#  ====================================================================
# THUMBNAIL WIDGET WITH DRAG & DROP SUPPORT
# ====================================================================

class ThumbnailWidget(QWidget):
    """Widget representing a single PDF page thumbnail with drag & drop support"""
    
    clicked = Signal(int, Qt.MouseButton, Qt.KeyboardModifiers)
    drag_started = Signal(int)
    
    def __init__(self, page_index, pixmap, page_label, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.is_selected = False
        self.is_focused = False
        self.setAcceptDrops(True)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        layout.addWidget(self.image_label)
        
        # Page number label
        self.page_label = QLabel(f"Strona {page_index + 1}")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.page_label)
        
        # Format label
        self.format_label = QLabel(page_label)
        self.format_label.setAlignment(Qt.AlignCenter)
        self.format_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.format_label)
        
        self.update_appearance()
        
    def update_appearance(self):
        """Update widget appearance based on selection/focus state"""
        if self.is_selected:
            self.setStyleSheet("background-color: #B3E5FC;")
        else:
            self.setStyleSheet("background-color: #F5F5F5;")
            
        if self.is_focused:
            self.setStyleSheet(self.styleSheet() + f" border: {FOCUS_HIGHLIGHT_WIDTH}px solid {FOCUS_HIGHLIGHT_COLOR};")
        
    def set_selected(self, selected):
        self.is_selected = selected
        self.update_appearance()
        
    def set_focused(self, focused):
        self.is_focused = focused
        self.update_appearance()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        self.clicked.emit(self.page_index, event.button(), event.modifiers())
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle drag initiation"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        self.drag_started.emit(self.page_index)
        super().mouseMoveEvent(event)


class ThumbnailListWidget(QListWidget):
    """Custom list widget for thumbnails with internal drag & drop for reordering"""
    
    pages_dropped = Signal(list, int, bool)  # source_indices, target_index, copy_mode
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(8)
        self.setMovement(QListWidget.Static)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Custom drag & drop settings
        self.drag_copy_mode = False
        
    def startDrag(self, supportedActions):
        """Override to handle multi-selection drag"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        # Create drag with selected indices
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Store selected indices
        indices = [self.row(item) for item in selected_items]
        mime_data.setText(','.join(map(str, indices)))
        drag.setMimeData(mime_data)
        
        # Set pixmap preview
        first_item = selected_items[0]
        if first_item.icon():
            pixmap = first_item.icon().pixmap(100, 100)
            if len(selected_items) > 1:
                # Add badge for multiple items
                painter = QPainter(pixmap)
                painter.drawText(pixmap.rect(), Qt.AlignBottom | Qt.AlignRight, 
                               f"+{len(selected_items)-1}")
                painter.end()
            drag.setPixmap(pixmap)
        
        # Determine if copy or move
        self.drag_copy_mode = QApplication.keyboardModifiers() & Qt.ControlModifier
        
        # Execute drag
        if self.drag_copy_mode:
            drag.exec_(Qt.CopyAction)
        else:
            drag.exec_(Qt.MoveAction)
            
    def dropEvent(self, event):
        """Handle drop event for reordering pages"""
        source_indices_str = event.mimeData().text()
        if not source_indices_str:
            return
            
        try:
            source_indices = [int(x) for x in source_indices_str.split(',')]
        except ValueError:
            return
            
        # Determine target position
        target_item = self.itemAt(event.pos())
        if target_item:
            target_index = self.row(target_item)
        else:
            target_index = self.count()
            
        # Check if it's a copy or move operation
        is_copy = event.dropAction() == Qt.CopyAction or (event.modifiers() & Qt.ControlModifier)
        
        # Emit signal with operation details
        self.pages_dropped.emit(source_indices, target_index, is_copy)
        
        event.accept()
        
    def contextMenuEvent(self, event):
        """Show context menu on right-click during drag"""
        # This allows right-click menu for copy/move choice during drag
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            copy_action = menu.addAction("Kopiuj tutaj")
            move_action = menu.addAction("Przenieś tutaj")
            menu.addSeparator()
            cancel_action = menu.addAction("Anuluj")
            
            action = menu.exec_(self.mapToGlobal(event.pos()))
            # Handle menu selection
            # This would need to be connected to actual drag operation
        super().contextMenuEvent(event)



# ====================================================================
# MAIN PDF EDITOR APPLICATION
# ====================================================================

class PDFEditorQt(QMainWindow):
    """Main PDF Editor application with Qt UI and full drag & drop support"""
    
    MM_TO_POINTS = 72 / 25.4
    
    def __init__(self):
        super().__init__()
        self.pdf_document = None
        self.selected_pages = set()
        self.active_page_index = 0
        self.clipboard = None
        self.pages_in_clipboard_count = 0
        
        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []
        self.max_stack_size = 50
        
        # Thumbnail settings
        self.thumb_width = 250
        self.zoom_level = 4  # number of columns
        self.min_zoom = 2
        self.max_zoom = 10
        
        # Thumbnail widgets storage
        self.thumb_widgets = {}
        
        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.update_buttons_state()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle(PROGRAM_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        
        # Enable drag & drop for files
        self.setAcceptDrops(True)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        self.setup_toolbar()
        
        # Thumbnail area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Use list widget for better drag & drop support
        self.thumbnail_list = ThumbnailListWidget()
        self.thumbnail_list.pages_dropped.connect(self.handle_page_drop)
        self.scroll_area.setWidget(self.thumbnail_list)
        
        main_layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Gotowy. Otwórz plik PDF.")
        
    def setup_toolbar(self):
        """Setup toolbar with all buttons"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # File operations
        self.action_open = QAction("📂 Otwórz", self)
        self.action_open.triggered.connect(self.open_pdf)
        toolbar.addAction(self.action_open)
        
        self.action_save = QAction("💾 Zapisz", self)
        self.action_save.triggered.connect(self.save_document)
        self.action_save.setEnabled(False)
        toolbar.addAction(self.action_save)
        
        toolbar.addSeparator()
        
        # Import/Export
        self.action_import_pdf = QAction("📥 Import PDF", self)
        self.action_import_pdf.triggered.connect(self.import_pdf)
        self.action_import_pdf.setEnabled(False)
        toolbar.addAction(self.action_import_pdf)
        
        self.action_export_pdf = QAction("📤 Export PDF", self)
        self.action_export_pdf.triggered.connect(self.extract_selected_pages)
        self.action_export_pdf.setEnabled(False)
        toolbar.addAction(self.action_export_pdf)
        
        self.action_import_image = QAction("🖼️ Import Obraz", self)
        self.action_import_image.triggered.connect(self.import_image)
        self.action_import_image.setEnabled(False)
        toolbar.addAction(self.action_import_image)
        
        self.action_export_image = QAction("🖼️ Export Obraz", self)
        self.action_export_image.triggered.connect(self.export_images)
        self.action_export_image.setEnabled(False)
        toolbar.addAction(self.action_export_image)
        
        toolbar.addSeparator()
        
        # Undo/Redo
        self.action_undo = QAction("↩️ Cofnij", self)
        self.action_undo.triggered.connect(self.undo)
        self.action_undo.setEnabled(False)
        toolbar.addAction(self.action_undo)
        
        self.action_redo = QAction("↪️ Ponów", self)
        self.action_redo.triggered.connect(self.redo)
        self.action_redo.setEnabled(False)
        toolbar.addAction(self.action_redo)
        
        toolbar.addSeparator()
        
        # Edit operations
        self.action_delete = QAction("🗑️ Usuń", self)
        self.action_delete.triggered.connect(self.delete_selected_pages)
        self.action_delete.setEnabled(False)
        toolbar.addAction(self.action_delete)
        
        self.action_cut = QAction("✂️ Wytnij", self)
        self.action_cut.triggered.connect(self.cut_pages)
        self.action_cut.setEnabled(False)
        toolbar.addAction(self.action_cut)
        
        self.action_copy = QAction("📋 Kopiuj", self)
        self.action_copy.triggered.connect(self.copy_pages)
        self.action_copy.setEnabled(False)
        toolbar.addAction(self.action_copy)
        
        self.action_paste_before = QAction("⬆️📄 Wklej przed", self)
        self.action_paste_before.triggered.connect(self.paste_before)
        self.action_paste_before.setEnabled(False)
        toolbar.addAction(self.action_paste_before)
        
        self.action_paste_after = QAction("⬇️📄 Wklej po", self)
        self.action_paste_after.triggered.connect(self.paste_after)
        self.action_paste_after.setEnabled(False)
        toolbar.addAction(self.action_paste_after)
        
        toolbar.addSeparator()
        
        # Rotate
        self.action_rotate_left = QAction("↺ Obróć w lewo", self)
        self.action_rotate_left.triggered.connect(lambda: self.rotate_pages(-90))
        self.action_rotate_left.setEnabled(False)
        toolbar.addAction(self.action_rotate_left)
        
        self.action_rotate_right = QAction("↻ Obróć w prawo", self)
        self.action_rotate_right.triggered.connect(lambda: self.rotate_pages(90))
        self.action_rotate_right.setEnabled(False)
        toolbar.addAction(self.action_rotate_right)
        
        toolbar.addSeparator()
        
        # Page modifications
        self.action_shift_content = QAction("↔️ Przesuń", self)
        self.action_shift_content.triggered.connect(self.shift_page_content)
        self.action_shift_content.setEnabled(False)
        toolbar.addAction(self.action_shift_content)
        
        self.action_remove_numbers = QAction("#️⃣❌ Usuń numery", self)
        self.action_remove_numbers.triggered.connect(self.remove_page_numbers)
        self.action_remove_numbers.setEnabled(False)
        toolbar.addAction(self.action_remove_numbers)
        
        self.action_add_numbers = QAction("#️⃣➕ Dodaj numery", self)
        self.action_add_numbers.triggered.connect(self.insert_page_numbers)
        self.action_add_numbers.setEnabled(False)
        toolbar.addAction(self.action_add_numbers)
        
        toolbar.addSeparator()
        
        # Zoom
        self.action_zoom_in = QAction("➕ Zoom In", self)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_in.setEnabled(False)
        toolbar.addAction(self.action_zoom_in)
        
        self.action_zoom_out = QAction("➖ Zoom Out", self)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_zoom_out.setEnabled(False)
        toolbar.addAction(self.action_zoom_out)
        
    def setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Plik")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addSeparator()
        file_menu.addAction(self.action_import_pdf)
        file_menu.addAction(self.action_export_pdf)
        file_menu.addSeparator()
        file_menu.addAction(self.action_import_image)
        file_menu.addAction(self.action_export_image)
        file_menu.addSeparator()
        quit_action = QAction("Zamknij program", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edycja")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_delete)
        edit_menu.addAction(self.action_cut)
        edit_menu.addAction(self.action_copy)
        edit_menu.addAction(self.action_paste_before)
        edit_menu.addAction(self.action_paste_after)
        edit_menu.addSeparator()
        
        duplicate_action = QAction("Duplikuj stronę", self)
        duplicate_action.triggered.connect(self.duplicate_page)
        duplicate_action.setEnabled(False)
        self.action_duplicate = duplicate_action
        edit_menu.addAction(duplicate_action)
        
        # Select menu
        select_menu = menubar.addMenu("Zaznacz")
        select_all_action = QAction("Wszystkie strony", self)
        select_all_action.triggered.connect(self.select_all)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_menu.addAction(select_all_action)
        select_menu.addSeparator()
        
        select_odd_action = QAction("Strony nieparzyste", self)
        select_odd_action.triggered.connect(self.select_odd_pages)
        select_odd_action.setShortcut(QKeySequence("F1"))
        select_menu.addAction(select_odd_action)
        self.action_select_odd = select_odd_action
        
        select_even_action = QAction("Strony parzyste", self)
        select_even_action.triggered.connect(self.select_even_pages)
        select_even_action.setShortcut(QKeySequence("F2"))
        select_menu.addAction(select_even_action)
        self.action_select_even = select_even_action
        
        # Modifications menu
        mod_menu = menubar.addMenu("Modyfikacje")
        mod_menu.addAction(self.action_rotate_left)
        mod_menu.addAction(self.action_rotate_right)
        mod_menu.addSeparator()
        mod_menu.addAction(self.action_shift_content)
        mod_menu.addAction(self.action_remove_numbers)
        mod_menu.addAction(self.action_add_numbers)
        
        # Help menu
        help_menu = menubar.addMenu("Pomoc")
        shortcuts_action = QAction("Skróty klawiszowe", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # File operations
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_save.setShortcut(QKeySequence.Save)
        
        # Edit operations
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_redo.setShortcut(QKeySequence.Redo)
        self.action_cut.setShortcut(QKeySequence.Cut)
        self.action_copy.setShortcut(QKeySequence.Copy)
        self.action_paste_after.setShortcut(QKeySequence.Paste)
        
        # Delete
        delete_shortcut = QKeySequence(Qt.Key_Delete)
        self.action_delete.setShortcut(delete_shortcut)
        
        # Import/Export
        self.action_import_pdf.setShortcut(QKeySequence("Ctrl+I"))
        self.action_export_pdf.setShortcut(QKeySequence("Ctrl+E"))
        self.action_import_image.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.action_export_image.setShortcut(QKeySequence("Ctrl+Shift+E"))
        
        # Modifications
        self.action_shift_content.setShortcut(QKeySequence("F5"))
        self.action_remove_numbers.setShortcut(QKeySequence("F6"))
        self.action_add_numbers.setShortcut(QKeySequence("F7"))
        
        # Zoom
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        
        # Duplicate
        if hasattr(self, 'action_duplicate'):
            self.action_duplicate.setShortcut(QKeySequence("Ctrl+D"))


    # ================================================================
    # DRAG & DROP HANDLERS FOR FILES
    # ================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag enter if files are dragged"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Accept drag move if files are being dragged"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """Handle file drop - open PDF or import image"""
        if not event.mimeData().hasUrls():
            return
            
        urls = event.mimeData().urls()
        if not urls:
            return
            
        filepath = urls[0].toLocalFile()
        if not filepath:
            return
            
        # Determine file type
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.pdf':
            # If no document open, open the PDF, otherwise import it
            if self.pdf_document is None:
                self.open_pdf(filepath=filepath)
            else:
                self.import_pdf(filepath=filepath)
        elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
            # Import image
            if self.pdf_document:
                self.import_image(filepath=filepath)
            else:
                QMessageBox.information(self, "Info", "Najpierw otwórz dokument PDF, aby zaimportować obraz.")
        else:
            QMessageBox.warning(self, "Nieprawidłowy plik", f"Nieobsługiwany typ pliku: {ext}")
            
        event.acceptProposedAction()
        
    def handle_page_drop(self, source_indices, target_index, is_copy):
        """Handle internal page drag & drop for reordering or copying"""
        if not self.pdf_document:
            return
            
        try:
            self._save_state_to_undo()
            
            # Get pages to move/copy
            pages_data = []
            for idx in sorted(source_indices):
                if 0 <= idx < len(self.pdf_document):
                    pages_data.append(idx)
                    
            if not pages_data:
                return
                
            if is_copy:
                # Copy pages
                temp_doc = fitz.open()
                for idx in pages_data:
                    temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
                
                # Insert at target
                self.pdf_document.insert_pdf(temp_doc, start_at=target_index)
                temp_doc.close()
                
                self.update_status(f"Skopiowano {len(pages_data)} stron do pozycji {target_index}")
            else:
                # Move pages - need to be more careful about indices
                # First, extract pages
                temp_doc = fitz.open()
                for idx in pages_data:
                    temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
                
                # Delete original pages (in reverse order to maintain indices)
                for idx in reversed(sorted(pages_data)):
                    self.pdf_document.delete_page(idx)
                    
                # Adjust target index if necessary
                adjusted_target = target_index
                for idx in pages_data:
                    if idx < target_index:
                        adjusted_target -= 1
                        
                # Insert at adjusted position
                self.pdf_document.insert_pdf(temp_doc, start_at=adjusted_target)
                temp_doc.close()
                
                self.update_status(f"Przeniesiono {len(pages_data)} stron do pozycji {adjusted_target}")
                
            # Refresh view
            self.refresh_thumbnails()
            self.update_buttons_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się przenieść/skopiować stron: {e}")
            
    # ================================================================
    # FILE OPERATIONS
    # ================================================================
    
    def open_pdf(self, filepath=None):
        """Open a PDF file"""
        # Check for unsaved changes
        if self.pdf_document and len(self.undo_stack) > 0:
            reply = QMessageBox.question(
                self, "Niezapisane zmiany",
                "Dokument został zmodyfikowany. Czy chcesz zapisać zmiany?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.save_document()
                if len(self.undo_stack) > 0:  # Save failed
                    return
                    
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Otwórz plik PDF", "", "Pliki PDF (*.pdf)"
            )
            
        if not filepath:
            self.update_status("Anulowano otwieranie pliku.")
            return
            
        try:
            if self.pdf_document:
                self.pdf_document.close()
                
            self.pdf_document = fitz.open(filepath)
            self.selected_pages.clear()
            self.active_page_index = 0
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Wczytano {len(self.pdf_document)} stron. Gotowy do edycji.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać pliku PDF: {e}")
            self.pdf_document = None
            self.update_buttons_state()
            
    def save_document(self):
        """Save the current PDF"""
        if not self.pdf_document:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Zapisz PDF jako", "", "Pliki PDF (*.pdf)"
        )
        
        if not filepath:
            self.update_status("Anulowano zapisywanie.")
            return
            
        try:
            self.pdf_document.save(filepath, garbage=4, clean=True, pretty=True)
            self.update_status(f"Dokument zapisany jako: {filepath}")
            
            # Clear undo/redo after save
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_buttons_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać pliku: {e}")
            
    def import_pdf(self, filepath=None):
        """Import pages from another PDF"""
        if not self.pdf_document:
            self.update_status("Najpierw otwórz dokument PDF.")
            return
            
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Wybierz plik PDF do zaimportowania", "", "Pliki PDF (*.pdf)"
            )
            
        if not filepath:
            self.update_status("Anulowano importowanie.")
            return
            
        try:
            imported_doc = fitz.open(filepath)
            
            # Determine insert position
            if len(self.selected_pages) == 1:
                insert_index = list(self.selected_pages)[0] + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
                
            self._save_state_to_undo()
            
            # Import all pages
            self.pdf_document.insert_pdf(imported_doc, start_at=insert_index)
            num_imported = len(imported_doc)
            imported_doc.close()
            
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Zaimportowano {num_imported} stron w pozycji {insert_index}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować PDF: {e}")
            
    def import_image(self, filepath=None):
        """Import an image as a new PDF page"""
        if not self.pdf_document:
            QMessageBox.information(self, "Info", "Najpierw otwórz dokument PDF.")
            return
            
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Wybierz obraz do zaimportowania", "",
                "Obrazy (*.png *.jpg *.jpeg *.tif *.tiff)"
            )
            
        if not filepath:
            return
            
        try:
            # Get image dimensions
            img = Image.open(filepath)
            img_width, img_height = img.size
            img_dpi = img.info.get('dpi', (96, 96))[0] if isinstance(img.info.get('dpi'), tuple) else 96
            
            # Convert to points
            img_width_pt = (img_width / img_dpi) * 72
            img_height_pt = (img_height / img_dpi) * 72
            
            # Create new page (A4)
            page_w, page_h = A4_WIDTH_POINTS, A4_HEIGHT_POINTS
            
            # Determine insert position
            if len(self.selected_pages) == 1:
                insert_index = list(self.selected_pages)[0] + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
                
            self._save_state_to_undo()
            
            # Create temporary document with image
            temp_doc = fitz.open()
            temp_page = temp_doc.new_page(-1, width=page_w, height=page_h)
            
            # Fit image to page with margin
            margin = 50 * MM_TO_POINTS
            scale_w = (page_w - margin) / img_width_pt
            scale_h = (page_h - margin) / img_height_pt
            scale = min(scale_w, scale_h)
            
            final_w = img_width_pt * scale
            final_h = img_height_pt * scale
            
            x = (page_w - final_w) / 2
            y = (page_h - final_h) / 2
            
            rect = fitz.Rect(x, y, x + final_w, y + final_h)
            temp_page.insert_image(rect, filename=filepath)
            
            # Insert into main document
            self.pdf_document.insert_pdf(temp_doc, from_page=0, to_page=0, start_at=insert_index)
            temp_doc.close()
            
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Zaimportowano obraz jako stronę {insert_index + 1}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować obrazu: {e}")


    def extract_selected_pages(self):
        """Export selected pages to a new PDF"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do eksportu.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wyodrębnione strony jako", "", "Pliki PDF (*.pdf)"
        )
        
        if not filepath:
            self.update_status("Anulowano ekstrakcję.")
            return
            
        try:
            temp_doc = fitz.open()
            for idx in sorted(self.selected_pages):
                temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
                
            temp_doc.save(filepath)
            temp_doc.close()
            
            self.update_status(f"Wyeksportowano {len(self.selected_pages)} stron do: {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować stron: {e}")
            
    def export_images(self):
        """Export selected pages as PNG images"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do eksportu.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder do zapisu obrazów")
        
        if not folder:
            return
            
        try:
            zoom = 300 / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            
            for idx in sorted(self.selected_pages):
                page = self.pdf_document[idx]
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                output_path = os.path.join(folder, f"strona_{idx + 1}.png")
                pix.save(output_path)
                
            self.update_status(f"Wyeksportowano {len(self.selected_pages)} obrazów do: {folder}")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować obrazów: {e}")
            
    # ================================================================
    # PAGE EDITING OPERATIONS
    # ================================================================
    
    def delete_selected_pages(self):
        """Delete selected pages"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do usunięcia.")
            return
            
        try:
            self._save_state_to_undo()
            
            # Delete in reverse order to maintain indices
            for idx in reversed(sorted(self.selected_pages)):
                self.pdf_document.delete_page(idx)
                
            count = len(self.selected_pages)
            self.selected_pages.clear()
            
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Usunięto {count} stron.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się usunąć stron: {e}")
            
    def cut_pages(self):
        """Cut selected pages to clipboard"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do wycięcia.")
            return
            
        try:
            # Save to clipboard
            temp_doc = fitz.open()
            for idx in sorted(self.selected_pages):
                temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
            self.clipboard = temp_doc.write()
            self.pages_in_clipboard_count = len(temp_doc)
            temp_doc.close()
            
            # Delete from document
            self._save_state_to_undo()
            for idx in reversed(sorted(self.selected_pages)):
                self.pdf_document.delete_page(idx)
                
            count = len(self.selected_pages)
            self.selected_pages.clear()
            
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Wycięto {count} stron do schowka.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wyciąć stron: {e}")
            
    def copy_pages(self):
        """Copy selected pages to clipboard"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do skopiowania.")
            return
            
        try:
            temp_doc = fitz.open()
            for idx in sorted(self.selected_pages):
                temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
            self.clipboard = temp_doc.write()
            self.pages_in_clipboard_count = len(temp_doc)
            temp_doc.close()
            
            self.selected_pages.clear()
            self.update_selection_display()
            self.update_buttons_state()
            self.update_status(f"Skopiowano {self.pages_in_clipboard_count} stron do schowka.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się skopiować stron: {e}")
            
    def paste_before(self):
        """Paste clipboard pages before selected page"""
        self._handle_paste(before=True)
        
    def paste_after(self):
        """Paste clipboard pages after selected page"""
        self._handle_paste(before=False)
        
    def _handle_paste(self, before):
        """Handle paste operation"""
        if not self.pdf_document or not self.clipboard:
            self.update_status("Schowek jest pusty.")
            return
            
        if len(self.selected_pages) > 1:
            self.update_status("Zaznacz jedną stronę do wklejenia przed/po.")
            return
            
        # Determine insert position
        if len(self.selected_pages) == 1:
            page_idx = list(self.selected_pages)[0]
            insert_index = page_idx if before else page_idx + 1
        else:
            insert_index = len(self.pdf_document)
            
        try:
            self._save_state_to_undo()
            
            temp_doc = fitz.open("pdf", self.clipboard)
            self.pdf_document.insert_pdf(temp_doc, start_at=insert_index)
            num_inserted = len(temp_doc)
            temp_doc.close()
            
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.selected_pages.clear()
            
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Wklejono {num_inserted} stron w pozycji {insert_index}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wkleić stron: {e}")
            
    def duplicate_page(self):
        """Duplicate selected page"""
        if not self.pdf_document or len(self.selected_pages) != 1:
            self.update_status("Zaznacz dokładnie jedną stronę do duplikacji.")
            return
            
        try:
            page_idx = list(self.selected_pages)[0]
            
            self._save_state_to_undo()
            
            temp_doc = fitz.open()
            temp_doc.insert_pdf(self.pdf_document, from_page=page_idx, to_page=page_idx)
            self.pdf_document.insert_pdf(temp_doc, from_page=0, to_page=0, start_at=page_idx + 1)
            temp_doc.close()
            
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Zduplikowano stronę {page_idx + 1}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zduplikować strony: {e}")
            
    def rotate_pages(self, angle):
        """Rotate selected pages"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do obrotu.")
            return
            
        try:
            self._save_state_to_undo()
            
            for idx in self.selected_pages:
                page = self.pdf_document[idx]
                current_rotation = page.rotation
                new_rotation = (current_rotation + angle) % 360
                page.set_rotation(new_rotation)
                
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Obrócono {len(self.selected_pages)} stron o {angle}°.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się obrócić stron: {e}")
            
    # ================================================================
    # UNDO/REDO
    # ================================================================
    
    def _save_state_to_undo(self):
        """Save current document state to undo stack"""
        if self.pdf_document:
            buffer = self.pdf_document.write()
            self.undo_stack.append(buffer)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.update_buttons_state()
            
    def undo(self):
        """Undo last operation"""
        if not self.undo_stack:
            self.update_status("Brak operacji do cofnięcia.")
            return
            
        try:
            # Save current state to redo
            if self.pdf_document:
                current_state = self.pdf_document.write()
                self.redo_stack.append(current_state)
                if len(self.redo_stack) > self.max_stack_size:
                    self.redo_stack.pop(0)
                    
            # Restore previous state
            previous_state = self.undo_stack.pop()
            
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", previous_state)
            
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status("Cofnięto ostatnią operację.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się cofnąć operacji: {e}")
            
    def redo(self):
        """Redo last undone operation"""
        if not self.redo_stack:
            self.update_status("Brak operacji do ponowienia.")
            return
            
        try:
            # Save current state to undo
            if self.pdf_document:
                current_state = self.pdf_document.write()
                self.undo_stack.append(current_state)
                if len(self.undo_stack) > self.max_stack_size:
                    self.undo_stack.pop(0)
                    
            # Restore next state
            next_state = self.redo_stack.pop()
            
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", next_state)
            
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status("Ponowiono operację.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się ponowić operacji: {e}")


    # ================================================================
    # PAGE MODIFICATIONS
    # ================================================================
    
    def shift_page_content(self):
        """Shift content on selected pages"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do przesunięcia zawartości.")
            return
            
        dialog = ShiftContentDialog(self)
        if dialog.exec_() != QDialog.Accepted or not dialog.result:
            self.update_status("Anulowano przesuwanie zawartości.")
            return
            
        result = dialog.result
        
        if result['x_mm'] == 0 and result['y_mm'] == 0:
            self.update_status("Zerowe przesunięcie - operacja anulowana.")
            return
            
        try:
            # Convert to points
            dx_pt = result['x_mm'] * self.MM_TO_POINTS
            dy_pt = result['y_mm'] * self.MM_TO_POINTS
            
            # Apply direction
            x_sign = -1 if result['x_dir'] == 'L' else 1
            y_sign = -1 if result['y_dir'] == 'D' else 1
            
            final_dx = dx_pt * x_sign
            final_dy = dy_pt * y_sign
            
            # Save state
            self._save_state_to_undo()
            
            # Use pypdf for transformation
            pdf_bytes = self.pdf_document.write()
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            
            transform = Transformation().translate(tx=final_dx, ty=final_dy)
            
            for i, page in enumerate(pdf_reader.pages):
                if i in self.selected_pages:
                    page.add_transformation(transform)
                pdf_writer.add_page(page)
                
            # Write back
            output = io.BytesIO()
            pdf_writer.write(output)
            new_pdf_bytes = output.getvalue()
            
            if self.pdf_document:
                self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Przesunięto zawartość na {len(self.selected_pages)} stronach.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się przesunąć zawartości: {e}")
            
    def insert_page_numbers(self):
        """Add page numbers to selected pages"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do numeracji.")
            return
            
        dialog = PageNumberingDialog(self)
        if dialog.exec_() != QDialog.Accepted or not dialog.result:
            self.update_status("Anulowano wstawianie numeracji.")
            return
            
        settings = dialog.result
        
        try:
            self._save_state_to_undo()
            
            MM_PT = self.MM_TO_POINTS
            start_number = settings['start_num']
            mode = settings['mode']
            direction = settings['alignment']
            position = settings['vertical_pos']
            mirror_margins = settings['mirror_margins']
            format_mode = settings['format_type']
            
            left_mm = settings['margin_left_mm']
            right_mm = settings['margin_right_mm']
            left_pt_base = left_mm * MM_PT
            right_pt_base = right_mm * MM_PT
            margin_v = settings['margin_vertical_mm'] * MM_PT
            font_size = settings['font_size']
            font = settings['font_name']
            
            selected_indices = sorted(self.selected_pages)
            current_number = start_number
            total_counted_pages = len(selected_indices) + start_number - 1
            
            for i in selected_indices:
                page = self.pdf_document[i]
                rect = page.rect
                rotation = page.rotation
                
                # Create text
                if format_mode == 'full':
                    text = f"Strona {current_number} z {total_counted_pages}"
                else:
                    text = str(current_number)
                    
                text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)
                
                # Determine alignment
                is_even_counted = (current_number - start_number) % 2 == 0
                
                if mode == "lustrzana":
                    if direction == "srodek":
                        align = "srodek"
                    elif direction == "lewa":
                        align = "lewa" if is_even_counted else "prawa"
                    else:
                        align = "prawa" if is_even_counted else "lewa"
                else:
                    align = direction
                    
                # Margin correction
                is_physical_odd = (i + 1) % 2 == 1
                if mirror_margins:
                    if is_physical_odd:
                        left_pt, right_pt = left_pt_base, right_pt_base
                    else:
                        left_pt, right_pt = right_pt_base, left_pt_base
                else:
                    left_pt, right_pt = left_pt_base, right_pt_base
                    
                # Calculate position
                if rotation == 0:
                    if align == "lewa":
                        x = rect.x0 + left_pt
                    elif align == "prawa":
                        x = rect.x1 - right_pt - text_width
                    else:  # center
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                        
                    y = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v
                    angle = 0
                else:
                    # Simplified for other rotations
                    x = rect.x0 + left_pt
                    y = rect.y1 - margin_v if position == "gora" else rect.y0 + margin_v
                    angle = rotation
                    
                # Insert text
                page.insert_text(
                    fitz.Point(x, y),
                    text,
                    fontsize=font_size,
                    fontname=font,
                    color=(0, 0, 0),
                    rotate=angle
                )
                
                current_number += 1
                
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Dodano numerację na {len(selected_indices)} stronach.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się dodać numeracji: {e}")
            
    def remove_page_numbers(self):
        """Remove page numbers from selected pages"""
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do usunięcia numeracji.")
            return
            
        dialog = PageNumberMarginDialog(self, initial_margin_mm=20)
        if dialog.exec_() != QDialog.Accepted or not dialog.result:
            self.update_status("Anulowano usuwanie numeracji.")
            return
            
        margins = dialog.result
        top_mm = margins['top_mm']
        bottom_mm = margins['bottom_mm']
        
        mm_to_pt = self.MM_TO_POINTS
        top_pt = top_mm * mm_to_pt
        bottom_pt = bottom_mm * mm_to_pt
        
        # Patterns for detecting page numbers
        page_number_patterns = [
            r'^\s*[-–]?\s*\d+\s*[-–]?\s*$',
            r'^\s*(?:Strona|Page)\s+\d+\s+(?:z|of)\s+\d+\s*$',
            r'^\s*\d+\s*(?:/|-|\s+)\s*\d+\s*$',
            r'^\s*\(\s*\d+\s*\)\s*$'
        ]
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in page_number_patterns]
        
        try:
            self._save_state_to_undo()
            
            modified_count = 0
            
            for page_index in sorted(self.selected_pages):
                page = self.pdf_document[page_index]
                rect = page.rect
                
                # Define scan areas
                top_margin_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + top_pt)
                bottom_margin_rect = fitz.Rect(rect.x0, rect.y1 - bottom_pt, rect.x1, rect.y1)
                
                scan_rects = [top_margin_rect, bottom_margin_rect]
                
                found_and_removed = False
                
                for scan_rect in scan_rects:
                    text_blocks = page.get_text("blocks", clip=scan_rect)
                    
                    for block in text_blocks:
                        block_text = block[4]
                        lines = block_text.strip().split('\n')
                        
                        for line in lines:
                            cleaned_line = line.strip()
                            for pattern in compiled_patterns:
                                if pattern.fullmatch(cleaned_line):
                                    text_instances = page.search_for(cleaned_line, clip=scan_rect)
                                    
                                    for inst in text_instances:
                                        page.add_redact_annot(inst)
                                        found_and_removed = True
                                        
                if found_and_removed:
                    page.apply_redactions()
                    modified_count += 1
                    
            if modified_count > 0:
                self.refresh_thumbnails()
                self.update_buttons_state()
                self.update_status(f"Usunięto numery na {modified_count} stronach.")
            else:
                self.update_status("Nie znaleziono numerów do usunięcia.")
                
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się usunąć numerów: {e}")


    # ================================================================
    # SELECTION OPERATIONS
    # ================================================================
    
    def select_all(self):
        """Select all pages"""
        if not self.pdf_document:
            return
            
        all_pages = set(range(len(self.pdf_document)))
        
        if self.selected_pages == all_pages:
            # Deselect all
            self.selected_pages.clear()
            self.update_status("Anulowano zaznaczenie wszystkich stron.")
        else:
            # Select all
            self.selected_pages = all_pages
            self.update_status(f"Zaznaczono wszystkie strony ({len(self.pdf_document)}).")
            
        self.update_selection_display()
        self.update_buttons_state()
        
    def select_odd_pages(self):
        """Select odd pages (1, 3, 5, ...)"""
        if not self.pdf_document:
            return
            
        indices = [i for i in range(len(self.pdf_document)) if i % 2 == 0]
        self.selected_pages = set(indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(indices)} stron nieparzystych.")
        
    def select_even_pages(self):
        """Select even pages (2, 4, 6, ...)"""
        if not self.pdf_document:
            return
            
        indices = [i for i in range(len(self.pdf_document)) if i % 2 != 0]
        self.selected_pages = set(indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(indices)} stron parzystych.")
        
    # ================================================================
    # VIEW OPERATIONS
    # ================================================================
    
    def zoom_in(self):
        """Zoom in (fewer columns, larger thumbnails)"""
        if self.pdf_document and self.zoom_level > self.min_zoom:
            self.zoom_level -= 1
            self.refresh_thumbnails()
            self.update_buttons_state()
            
    def zoom_out(self):
        """Zoom out (more columns, smaller thumbnails)"""
        if self.pdf_document and self.zoom_level < self.max_zoom:
            self.zoom_level += 1
            self.refresh_thumbnails()
            self.update_buttons_state()
            
    def refresh_thumbnails(self):
        """Refresh all thumbnail widgets"""
        if not self.pdf_document:
            self.thumbnail_list.clear()
            self.thumb_widgets.clear()
            return
            
        self.thumbnail_list.clear()
        self.thumb_widgets.clear()
        
        # Calculate thumbnail size based on zoom level
        base_width = 200
        thumb_width = int(base_width * (self.max_zoom - self.zoom_level + self.min_zoom) / self.max_zoom)
        
        for i in range(len(self.pdf_document)):
            page = self.pdf_document[i]
            
            # Render page as pixmap
            mat = fitz.Matrix(0.5, 0.5)  # Smaller resolution for thumbnails
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimage = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale to thumbnail size
            aspect_ratio = pix.height / pix.width if pix.width > 0 else 1
            thumb_height = int(thumb_width * aspect_ratio)
            scaled_pixmap = pixmap.scaled(thumb_width, thumb_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Get page label
            page_label = self._get_page_size_label(i)
            
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(QSize(thumb_width + 20, thumb_height + 60))
            self.thumbnail_list.addItem(item)
            
            # Create thumbnail widget
            thumb_widget = ThumbnailWidget(i, scaled_pixmap, page_label)
            thumb_widget.clicked.connect(self.on_thumbnail_clicked)
            self.thumbnail_list.setItemWidget(item, thumb_widget)
            
            self.thumb_widgets[i] = thumb_widget
            
        self.update_selection_display()
        
    def _get_page_size_label(self, page_index):
        """Get formatted page size label"""
        if not self.pdf_document:
            return ""
            
        page = self.pdf_document[page_index]
        width_mm = round(page.rect.width / 72 * 25.4)
        height_mm = round(page.rect.height / 72 * 25.4)
        
        if 205 <= width_mm <= 215 and 292 <= height_mm <= 302:
            return "A4"
        elif 292 <= width_mm <= 302 and 205 <= height_mm <= 215:
            return "A4 (Poziom)"
        elif 292 <= width_mm <= 302 and 415 <= height_mm <= 425:
            return "A3"
        else:
            return f"{width_mm} x {height_mm} mm"
            
    def on_thumbnail_clicked(self, page_index, button, modifiers):
        """Handle thumbnail click"""
        if button == Qt.LeftButton:
            if modifiers & Qt.ControlModifier:
                # Toggle selection
                if page_index in self.selected_pages:
                    self.selected_pages.remove(page_index)
                else:
                    self.selected_pages.add(page_index)
            elif modifiers & Qt.ShiftModifier:
                # Range selection
                if self.selected_pages:
                    last_selected = max(self.selected_pages)
                    start = min(page_index, last_selected)
                    end = max(page_index, last_selected)
                    for i in range(start, end + 1):
                        self.selected_pages.add(i)
                else:
                    self.selected_pages.add(page_index)
            else:
                # Single selection
                self.selected_pages = {page_index}
                
            self.active_page_index = page_index
            self.update_selection_display()
            self.update_buttons_state()
            
        elif button == Qt.RightButton:
            # Right-click context menu
            if page_index not in self.selected_pages:
                self.selected_pages = {page_index}
                self.update_selection_display()
                
            self.show_context_menu()
            
    def show_context_menu(self):
        """Show context menu for page operations"""
        menu = QMenu(self)
        
        menu.addAction(self.action_cut)
        menu.addAction(self.action_copy)
        menu.addAction(self.action_paste_before)
        menu.addAction(self.action_paste_after)
        menu.addSeparator()
        menu.addAction(self.action_delete)
        menu.addAction(self.action_duplicate)
        menu.addSeparator()
        menu.addAction(self.action_rotate_left)
        menu.addAction(self.action_rotate_right)
        
        menu.exec_(QCursor.pos())
        
    def update_selection_display(self):
        """Update visual selection state of thumbnails"""
        for idx, widget in self.thumb_widgets.items():
            widget.set_selected(idx in self.selected_pages)
            widget.set_focused(idx == self.active_page_index)
            
    def update_buttons_state(self):
        """Update enabled/disabled state of all buttons"""
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        has_clipboard = self.clipboard is not None
        
        # File operations
        self.action_save.setEnabled(doc_loaded)
        self.action_import_pdf.setEnabled(doc_loaded)
        self.action_import_image.setEnabled(doc_loaded)
        
        # Edit operations
        self.action_undo.setEnabled(has_undo)
        self.action_redo.setEnabled(has_redo)
        self.action_delete.setEnabled(doc_loaded and has_selection)
        self.action_cut.setEnabled(doc_loaded and has_selection)
        self.action_copy.setEnabled(doc_loaded and has_selection)
        self.action_paste_before.setEnabled(doc_loaded and has_clipboard and len(self.selected_pages) <= 1)
        self.action_paste_after.setEnabled(doc_loaded and has_clipboard and len(self.selected_pages) <= 1)
        
        # Export
        self.action_export_pdf.setEnabled(doc_loaded and has_selection)
        self.action_export_image.setEnabled(doc_loaded and has_selection)
        
        # Page operations
        self.action_rotate_left.setEnabled(doc_loaded and has_selection)
        self.action_rotate_right.setEnabled(doc_loaded and has_selection)
        self.action_shift_content.setEnabled(doc_loaded and has_selection)
        self.action_remove_numbers.setEnabled(doc_loaded and has_selection)
        self.action_add_numbers.setEnabled(doc_loaded and has_selection)
        
        if hasattr(self, 'action_duplicate'):
            self.action_duplicate.setEnabled(doc_loaded and has_single_selection)
            
        if hasattr(self, 'action_select_odd'):
            self.action_select_odd.setEnabled(doc_loaded)
        if hasattr(self, 'action_select_even'):
            self.action_select_even.setEnabled(doc_loaded)
            
        # Zoom
        self.action_zoom_in.setEnabled(doc_loaded and self.zoom_level > self.min_zoom)
        self.action_zoom_out.setEnabled(doc_loaded and self.zoom_level < self.max_zoom)
        
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)
        
    # ================================================================
    # DIALOG FUNCTIONS
    # ================================================================
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Skróty klawiszowe")
        msg.setText("""
<b>Plik:</b><br>
Ctrl+O - Otwórz PDF<br>
Ctrl+S - Zapisz jako<br>
Ctrl+I - Importuj PDF<br>
Ctrl+E - Eksportuj PDF<br>
Ctrl+Shift+I - Importuj obraz<br>
Ctrl+Shift+E - Eksportuj obrazy<br>
<br>
<b>Edycja:</b><br>
Ctrl+Z - Cofnij<br>
Ctrl+Y - Ponów<br>
Ctrl+X - Wytnij<br>
Ctrl+C - Kopiuj<br>
Ctrl+V - Wklej<br>
Delete - Usuń<br>
Ctrl+D - Duplikuj<br>
<br>
<b>Zaznacz:</b><br>
Ctrl+A - Wszystkie strony<br>
F1 - Strony nieparzyste<br>
F2 - Strony parzyste<br>
<br>
<b>Modyfikacje:</b><br>
F5 - Przesuń zawartość<br>
F6 - Usuń numerację<br>
F7 - Dodaj numerację<br>
<br>
<b>Widok:</b><br>
Ctrl++ - Zoom in<br>
Ctrl+- - Zoom out<br>
        """)
        msg.exec_()
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "O programie",
            f"""<h2>{PROGRAM_TITLE}</h2>
            <p>Wersja: {PROGRAM_VERSION}</p>
            <p>Data: {PROGRAM_DATE}</p>
            <hr>
            <p>{COPYRIGHT_INFO}</p>
            """
        )
        
    # ================================================================
    # CLOSE EVENT
    # ================================================================
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.pdf_document and len(self.undo_stack) > 0:
            reply = QMessageBox.question(
                self, "Niezapisane zmiany",
                "Czy chcesz zapisać zmiany przed zamknięciem?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.save_document()
                if len(self.undo_stack) > 0:  # Save failed or cancelled
                    event.ignore()
                    return
                    
        event.accept()


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_TITLE)
    app.setApplicationVersion(PROGRAM_VERSION)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = PDFEditorQt()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

