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
    QListWidget, QListWidgetItem, QAbstractItemView, QSizePolicy,
    QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem
)
from PySide6.QtCore import (
    Qt, QSize, QMimeData, QByteArray, QBuffer, QIODevice,
    Signal, QPoint, QRect, QTimer, QEvent
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QBrush, QPen,
    QAction, QKeySequence, QDragEnterEvent, QDropEvent,
    QDrag, QMouseEvent, QPalette, QIcon, QWheelEvent, QCursor, QFont
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
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
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

class PageCropResizeDialog(QDialog):
    """Dialog for cropping and resizing PDF pages with full feature parity"""
    
    PAPER_FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'Niestandardowy': (0, 0)
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kadrowanie i zmiana rozmiaru stron")
        self.result = None
        
        # Initialize variables
        self.crop_mode = "nocrop"
        self.margin_top = "10"
        self.margin_bottom = "10"
        self.margin_left = "10"
        self.margin_right = "10"
        
        self.resize_mode = "noresize"
        self.target_format = "A4"
        self.custom_width = ""
        self.custom_height = ""
        self.position_mode = "center"
        self.offset_x = "0"
        self.offset_y = "0"
        
        self.setup_ui()
        self.update_field_states()
        
def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # === CROP SECTION ===
        crop_group = QGroupBox("Przycinanie strony")
        crop_layout = QVBoxLayout()
        
        self.crop_none = QRadioButton("Nie przycinaj")
        self.crop_only = QRadioButton("Przytnij obraz bez zmiany rozmiaru arkusza")
        self.crop_resize = QRadioButton("Przytnij obraz i dostosuj rozmiar arkusza")
        self.crop_none.setChecked(True)
        
        crop_layout.addWidget(self.crop_none)
        crop_layout.addWidget(self.crop_only)
        crop_layout.addWidget(self.crop_resize)
        
        # Margin inputs
        margin_frame = QWidget()
        margin_grid = QGridLayout(margin_frame)
        margin_grid.addWidget(QLabel("Góra [mm]:"), 0, 0)
        self.e_margin_top = QLineEdit(self.margin_top)
        margin_grid.addWidget(self.e_margin_top, 0, 1)
        margin_grid.addWidget(QLabel("Dół [mm]:"), 0, 2)
        self.e_margin_bottom = QLineEdit(self.margin_bottom)
        margin_grid.addWidget(self.e_margin_bottom, 0, 3)
        margin_grid.addWidget(QLabel("Lewo [mm]:"), 1, 0)
        self.e_margin_left = QLineEdit(self.margin_left)
        margin_grid.addWidget(self.e_margin_left, 1, 1)
        margin_grid.addWidget(QLabel("Prawo [mm]:"), 1, 2)
        self.e_margin_right = QLineEdit(self.margin_right)
        margin_grid.addWidget(self.e_margin_right, 1, 3)
        
        crop_layout.addWidget(margin_frame)
        crop_group.setLayout(crop_layout)
        layout.addWidget(crop_group)
        
        # === RESIZE SECTION ===
        resize_group = QGroupBox("Zmiana rozmiaru arkusza")
        resize_layout = QVBoxLayout()
        
        self.resize_none = QRadioButton("Nie zmieniaj rozmiaru")
        self.resize_scale = QRadioButton("Zmień rozmiar i skaluj obraz")
        self.resize_noscale = QRadioButton("Zmień rozmiar i nie skaluj obrazu")
        self.resize_none.setChecked(True)
        
        resize_layout.addWidget(self.resize_none)
        resize_layout.addWidget(self.resize_scale)
        resize_layout.addWidget(self.resize_noscale)
        
        # Format selection
        format_frame = QWidget()
        format_layout = QHBoxLayout(format_frame)
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(self.PAPER_FORMATS.keys()))
        self.format_combo.setCurrentText(self.target_format)
        format_layout.addWidget(self.format_combo)
        resize_layout.addWidget(format_frame)
        
        # Custom size inputs
        self.custom_size_frame = QWidget()
        custom_grid = QGridLayout(self.custom_size_frame)
        custom_grid.addWidget(QLabel("Szerokość [mm]:"), 0, 0)
        self.e_custom_width = QLineEdit(self.custom_width)
        custom_grid.addWidget(self.e_custom_width, 0, 1)
        custom_grid.addWidget(QLabel("Wysokość [mm]:"), 0, 2)
        self.e_custom_height = QLineEdit(self.custom_height)
        custom_grid.addWidget(self.e_custom_height, 0, 3)
        resize_layout.addWidget(self.custom_size_frame)
        
        resize_group.setLayout(resize_layout)
        layout.addWidget(resize_group)
        
        # === POSITION SECTION ===
        self.position_group = QGroupBox("Położenie obrazu")
        position_layout = QVBoxLayout()
        
        self.pos_center = QRadioButton("Wyśrodkuj")
        self.pos_custom = QRadioButton("Niestandardowe położenie")
        self.pos_center.setChecked(True)
        
        position_layout.addWidget(self.pos_center)
        position_layout.addWidget(self.pos_custom)
        
        # Offset inputs
        self.offset_frame = QWidget()
        offset_grid = QGridLayout(self.offset_frame)
        offset_grid.addWidget(QLabel("Od lewej [mm]:"), 0, 0)
        self.e_offset_x = QLineEdit(self.offset_x)
        offset_grid.addWidget(self.e_offset_x, 0, 1)
        offset_grid.addWidget(QLabel("Od dołu [mm]:"), 0, 2)
        self.e_offset_y = QLineEdit(self.offset_y)
        offset_grid.addWidget(self.e_offset_y, 0, 3)
        position_layout.addWidget(self.offset_frame)
        
        self.position_group.setLayout(position_layout)
        layout.addWidget(self.position_group)
        
        # === BUTTONS ===
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.crop_none.toggled.connect(self.update_field_states)
        self.crop_only.toggled.connect(self.update_field_states)
        self.crop_resize.toggled.connect(self.update_field_states)
        self.resize_none.toggled.connect(self.update_field_states)
        self.resize_scale.toggled.connect(self.update_field_states)
        self.resize_noscale.toggled.connect(self.update_field_states)
        self.format_combo.currentTextChanged.connect(self.update_field_states)
        self.pos_center.toggled.connect(self.update_field_states)
        self.pos_custom.toggled.connect(self.update_field_states)
        
def update_field_states(self):
        crop_selected = not self.crop_none.isChecked()
        resize_selected = not self.resize_none.isChecked()
        # Mutual exclusivity (design choice)
        self.resize_none.setEnabled(!crop_selected)