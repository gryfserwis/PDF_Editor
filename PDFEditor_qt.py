#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRYF PDF Editor - PySide6 Version
Migrated from Tkinter to PySide6 (Qt for Python)

Original: PDFEditor.py (Tkinter version)
This version: PDFEditor_qt.py (PySide6 version)
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QDialog, QLineEdit, QComboBox,
    QCheckBox, QRadioButton, QButtonGroup, QMessageBox, QFileDialog, QMenuBar,
    QMenu, QStatusBar, QToolBar, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize, QRect, QEvent, Slot
from PySide6.QtGui import QPixmap, QImage, QIcon, QAction, QPainter, QKeySequence, QShortcut, QWheelEvent
import fitz
from PIL import Image
import io
import math
import os
import sys
import re
from typing import Optional, List, Set, Dict, Union
from datetime import date
import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject, NameObject

# ArrayObject jest nadal potrzebne, jeśli użyjesz add_transformation, choć FloatObject 
# wystarczyłoby, jeśli pypdf je konwertuje. Zostawiam dla pełnej kompatybilności.

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FOLDER = os.path.join(BASE_DIR, "icons")
FOCUS_HIGHLIGHT_COLOR = "#000000" # Czarny (Black)
FOCUS_HIGHLIGHT_WIDTH = 2        # Szerokość ramki fokusu (stała)

# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor" 
PROGRAM_VERSION = "4.1.1"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 (w punktach PDF i mm) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4 # ~2.8346

def mm2pt(mm):
    return float(mm) * MM_TO_POINTS


# === STAŁE KOLORY NARZĘDZIOWE (jeśli ich nie masz) ===
# Musisz zdefiniować te kolory, jeśli ich nie masz, dla przycisku importu
BG_IMPORT = "#F0AD4E" # np. Jakiś pomarańczowy dla importu
GRAY_FG = "#555555" # Jeśli używasz tego dla ikon

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

# === STAŁE KOLORYSTYKA DLA SPOJNOSCI ===
BG_PRIMARY = '#F0F0F0'  # Główne tło okien i dialogów
BG_SECONDARY = '#E0E0E0' # Tło paneli kontrolnych/przycisków
BG_BUTTON_DEFAULT = "#D0D0D0" # Domyślny kolor przycisków
FG_TEXT = "#444444" # Kolor tekstu na przyciskach

# === STAŁE DLA A4 (w punktach PDF) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89


def resource_path(relative_path):
    """
    Tworzy poprawną ścieżkę do zasobów (logo, ikony itp.).
    Działa w trybie deweloperskim i po spakowaniu PyInstallerem.
    """
    try:
        # Aplikacja spakowana (PyInstaller --onefile)
        base_path = sys._MEIPASS
    except AttributeError:
        # Tryb deweloperski (po prostu katalog skryptu)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)
  



# Check for logo
PROGRAM_LOGO_PATH = None
logo_path_check = os.path.join(ICON_FOLDER, 'gryf_logo.png')
if os.path.exists(logo_path_check):
    PROGRAM_LOGO_PATH = logo_path_check


# ====================================================================
# KLASA: DIALOG KADROWANIA I ZMIANY ROZMIARU STRON
# ====================================================================

class PageCropResizeDialog(QDialog):
    """Dialog for cropping and resizing PDF pages - migrated from Tkinter"""
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

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Kadrowanie i zmiana rozmiaru stron")
        self.setModal(True)
        self.result = None

        # Initialize variables (replaces tk.StringVar)
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

        self.build_ui()
        self.update_field_states()
        self.center_dialog(parent)

    def build_ui(self):
        """Build the dialog UI using Qt layouts (replaces pack/grid)"""
        layout = QVBoxLayout(self)
        
        # --- CROP SECTION ---
        crop_group = QFrame()
        crop_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        crop_layout = QVBoxLayout(crop_group)
        
        crop_label = QLabel("Przycinanie strony")
        crop_label.setStyleSheet("font-weight: bold;")
        crop_layout.addWidget(crop_label)
        
        self.crop_button_group = QButtonGroup(self)
        
        self.rb_nocrop = QRadioButton("Nie przycinaj")
        self.rb_nocrop.setChecked(True)
        self.crop_button_group.addButton(self.rb_nocrop, 0)
        crop_layout.addWidget(self.rb_nocrop)
        
        self.rb_crop_only = QRadioButton("Przytnij obraz bez zmiany rozmiaru arkusza")
        self.crop_button_group.addButton(self.rb_crop_only, 1)
        crop_layout.addWidget(self.rb_crop_only)
        
        self.rb_crop_resize = QRadioButton("Przytnij obraz i dostosuj rozmiar arkusza")
        self.crop_button_group.addButton(self.rb_crop_resize, 2)
        crop_layout.addWidget(self.rb_crop_resize)
        
        # Margin fields
        margin_layout = QGridLayout()
        margin_layout.addWidget(QLabel("Góra [mm]:"), 0, 0)
        self.e_margin_top = QLineEdit(self.margin_top)
        margin_layout.addWidget(self.e_margin_top, 0, 1)
        
        margin_layout.addWidget(QLabel("Dół [mm]:"), 0, 2)
        self.e_margin_bottom = QLineEdit(self.margin_bottom)
        margin_layout.addWidget(self.e_margin_bottom, 0, 3)
        
        margin_layout.addWidget(QLabel("Lewo [mm]:"), 1, 0)
        self.e_margin_left = QLineEdit(self.margin_left)
        margin_layout.addWidget(self.e_margin_left, 1, 1)
        
        margin_layout.addWidget(QLabel("Prawo [mm]:"), 1, 2)
        self.e_margin_right = QLineEdit(self.margin_right)
        margin_layout.addWidget(self.e_margin_right, 1, 3)
        
        crop_layout.addLayout(margin_layout)
        layout.addWidget(crop_group)
        
        # --- RESIZE SECTION ---
        resize_group = QFrame()
        resize_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        resize_layout = QVBoxLayout(resize_group)
        
        resize_label = QLabel("Zmiana rozmiaru arkusza")
        resize_label.setStyleSheet("font-weight: bold;")
        resize_layout.addWidget(resize_label)
        
        self.resize_button_group = QButtonGroup(self)
        
        self.rb_noresize = QRadioButton("Nie zmieniaj rozmiaru")
        self.rb_noresize.setChecked(True)
        self.resize_button_group.addButton(self.rb_noresize, 0)
        resize_layout.addWidget(self.rb_noresize)
        
        self.rb_resize_scale = QRadioButton("Zmień rozmiar i skaluj obraz")
        self.resize_button_group.addButton(self.rb_resize_scale, 1)
        resize_layout.addWidget(self.rb_resize_scale)
        
        self.rb_resize_noscale = QRadioButton("Zmień rozmiar i nie skaluj obrazu")
        self.resize_button_group.addButton(self.rb_resize_noscale, 2)
        resize_layout.addWidget(self.rb_resize_noscale)
        
        # Format combo
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(self.PAPER_FORMATS.keys()))
        self.format_combo.setCurrentText(self.target_format)
        format_layout.addWidget(self.format_combo)
        resize_layout.addLayout(format_layout)
        
        # Custom size
        custom_layout = QGridLayout()
        custom_layout.addWidget(QLabel("Szerokość [mm]:"), 0, 0)
        self.e_custom_width = QLineEdit(self.custom_width)
        custom_layout.addWidget(self.e_custom_width, 0, 1)
        
        custom_layout.addWidget(QLabel("Wysokość [mm]:"), 0, 2)
        self.e_custom_height = QLineEdit(self.custom_height)
        custom_layout.addWidget(self.e_custom_height, 0, 3)
        resize_layout.addLayout(custom_layout)
        
        layout.addWidget(resize_group)
        
        # --- POSITION SECTION ---
        position_group = QFrame()
        position_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        position_layout = QVBoxLayout(position_group)
        
        position_label = QLabel("Położenie obrazu")
        position_label.setStyleSheet("font-weight: bold;")
        position_layout.addWidget(position_label)
        
        self.position_button_group = QButtonGroup(self)
        
        self.rb_pos_center = QRadioButton("Wyśrodkuj")
        self.rb_pos_center.setChecked(True)
        self.position_button_group.addButton(self.rb_pos_center, 0)
        position_layout.addWidget(self.rb_pos_center)
        
        self.rb_pos_custom = QRadioButton("Niestandardowe położenie")
        self.position_button_group.addButton(self.rb_pos_custom, 1)
        position_layout.addWidget(self.rb_pos_custom)
        
        # Offsets
        offset_layout = QGridLayout()
        offset_layout.addWidget(QLabel("Od lewej [mm]:"), 0, 0)
        self.e_offset_x = QLineEdit(self.offset_x)
        offset_layout.addWidget(self.e_offset_x, 0, 1)
        
        offset_layout.addWidget(QLabel("Od dołu [mm]:"), 0, 2)
        self.e_offset_y = QLineEdit(self.offset_y)
        offset_layout.addWidget(self.e_offset_y, 0, 3)
        position_layout.addLayout(offset_layout)
        
        layout.addWidget(position_group)
        
        # --- BUTTONS ---
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("Zastosuj")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        
        # Connect signals (replaces command= in Tkinter)
        self.crop_button_group.buttonClicked.connect(self.update_field_states)
        self.resize_button_group.buttonClicked.connect(self.update_field_states)
        self.position_button_group.buttonClicked.connect(self.update_field_states)
        self.format_combo.currentTextChanged.connect(self.update_field_states)
        
        # Keyboard shortcuts (replaces bind)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def update_field_states(self):
        """Update field states based on selections"""
        crop_mode = self.get_crop_mode()
        resize_mode = self.get_resize_mode()
        
        crop_selected = crop_mode != "nocrop"
        resize_selected = resize_mode != "noresize"
        
        # Mutual exclusivity
        self.rb_resize_scale.setEnabled(not crop_selected)
        self.rb_resize_noscale.setEnabled(not crop_selected)
        self.rb_noresize.setEnabled(not crop_selected)
        
        self.rb_crop_only.setEnabled(not resize_selected)
        self.rb_crop_resize.setEnabled(not resize_selected)
        self.rb_nocrop.setEnabled(not resize_selected)
        
        # Margin fields
        enable_crop = crop_selected and not resize_selected
        self.e_margin_top.setEnabled(enable_crop)
        self.e_margin_bottom.setEnabled(enable_crop)
        self.e_margin_left.setEnabled(enable_crop)
        self.e_margin_right.setEnabled(enable_crop)
        
        # Format and custom size
        enable_format = resize_selected and not crop_selected
        self.format_combo.setEnabled(enable_format)
        
        enable_custom = enable_format and self.format_combo.currentText() == "Niestandardowy"
        self.e_custom_width.setEnabled(enable_custom)
        self.e_custom_height.setEnabled(enable_custom)
        
        # Position
        enable_position = resize_mode == "resize_noscale" and not crop_selected
        self.rb_pos_center.setEnabled(enable_position)
        self.rb_pos_custom.setEnabled(enable_position)
        
        pos_mode = "custom" if self.rb_pos_custom.isChecked() else "center"
        enable_offsets = enable_position and pos_mode == "custom"
        self.e_offset_x.setEnabled(enable_offsets)
        self.e_offset_y.setEnabled(enable_offsets)

    def get_crop_mode(self):
        if self.rb_nocrop.isChecked():
            return "nocrop"
        elif self.rb_crop_only.isChecked():
            return "crop_only"
        elif self.rb_crop_resize.isChecked():
            return "crop_resize"
        return "nocrop"

    def get_resize_mode(self):
        if self.rb_noresize.isChecked():
            return "noresize"
        elif self.rb_resize_scale.isChecked():
            return "resize_scale"
        elif self.rb_resize_noscale.isChecked():
            return "resize_noscale"
        return "noresize"

    def center_dialog(self, parent):
        """Center dialog relative to parent (replaces Tkinter geometry management)"""
        if parent:
            parent_geo = parent.geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def ok(self):
        """OK button handler"""
        try:
            crop_mode = self.get_crop_mode()
            resize_mode = self.get_resize_mode()

            # Parse margins
            if crop_mode == "nocrop":
                top = bottom = left = right = 0.0
            else:
                top = float(self.e_margin_top.text().replace(',', '.'))
                bottom = float(self.e_margin_bottom.text().replace(',', '.'))
                left = float(self.e_margin_left.text().replace(',', '.'))
                right = float(self.e_margin_right.text().replace(',', '.'))
                for v in [top, bottom, left, right]:
                    if v < 0:
                        raise ValueError("Marginesy muszą być nieujemne.")

            # Parse format and dimensions
            if resize_mode != "noresize":
                format_name = self.format_combo.currentText()
                if format_name == "Niestandardowy":
                    w = float(self.e_custom_width.text().replace(",", "."))
                    h = float(self.e_custom_height.text().replace(",", "."))
                    if w <= 0 or h <= 0:
                        raise ValueError("Rozmiar niestandardowy musi być większy od zera.")
                else:
                    w, h = self.PAPER_FORMATS[format_name]
            else:
                w = h = 0

            pos_mode = "custom" if self.rb_pos_custom.isChecked() else "center"
            offset_x_val = float(self.e_offset_x.text().replace(",", ".")) if pos_mode == "custom" else 0
            offset_y_val = float(self.e_offset_y.text().replace(",", ".")) if pos_mode == "custom" else 0

            self.result = {
                'crop_mode': crop_mode,
                'resize_mode': resize_mode,
                'crop_top_mm': top,
                'crop_bottom_mm': bottom,
                'crop_left_mm': left,
                'crop_right_mm': right,
                'target_width_mm': w,
                'target_height_mm': h,
                'position_mode': pos_mode,
                'offset_x_mm': offset_x_val,
                'offset_y_mm': offset_y_val
            }
            self.accept()  # Closes dialog with Accepted result
        except ValueError as e:
            QMessageBox.critical(self, "Błąd Wprowadzania", 
                f"Nieprawidłowa wartość: {e}. Użyj cyfr, kropki lub przecinka.")

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()  # Closes dialog with Rejected result



# ====================================================================
# KLASA: DIALOG NUMERACJI STRON
# ====================================================================

class PageNumberingDialog(QDialog):
    """Dialog for page numbering settings - migrated from Tkinter"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Wstawianie numeracji stron")
        self.setModal(True)
        self.result = None
        
        self.create_variables()
        self.build_ui()
        self.center_window()

    def create_variables(self):
        """Initialize variables (replaces tk.StringVar, tk.BooleanVar)"""
        self.v_margin_left = "35"
        self.v_margin_right = "25"
        self.v_margin_vertical_mm = "15"
        self.v_vertical_pos = 'dol'
        self.v_alignment = 'prawa'
        self.v_mode = 'normalna'
        self.v_start_page = "1"
        self.v_start_number = "1"
        self.font_options = ["Helvetica", "Times-Roman", "Courier", "Arial"]
        self.size_options = ["6", "8", "10", "11", "12", "13", "14"]
        self.v_font_name = "Times-Roman"
        self.v_font_size = "12"
        self.v_mirror_margins = False
        self.v_format_type = 'simple'

    def center_window(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # 1. Margins configuration
        margin_group = QFrame()
        margin_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        margin_layout = QVBoxLayout(margin_group)
        
        margin_label = QLabel("Marginesy tekstu (milimetry)")
        margin_label.setStyleSheet("font-weight: bold;")
        margin_layout.addWidget(margin_label)
        
        margin_grid = QGridLayout()
        margin_grid.addWidget(QLabel("Margines lewy:"), 0, 0)
        self.e_margin_left = QLineEdit(self.v_margin_left)
        margin_grid.addWidget(self.e_margin_left, 0, 1)
        
        margin_grid.addWidget(QLabel("Margines prawy:"), 0, 2)
        self.e_margin_right = QLineEdit(self.v_margin_right)
        margin_grid.addWidget(self.e_margin_right, 0, 3)
        
        margin_layout.addLayout(margin_grid)
        
        self.cb_mirror_margins = QCheckBox("Plik ma marginesy lustrzane")
        self.cb_mirror_margins.setChecked(self.v_mirror_margins)
        margin_layout.addWidget(self.cb_mirror_margins)
        
        layout.addWidget(margin_group)
        
        # 2. Position
        position_group = QFrame()
        position_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        position_layout = QVBoxLayout(position_group)
        
        position_label = QLabel("Położenie numeru strony")
        position_label.setStyleSheet("font-weight: bold;")
        position_layout.addWidget(position_label)
        
        pos_grid = QGridLayout()
        pos_grid.addWidget(QLabel("Od krawędzi:"), 0, 0)
        self.e_margin_vertical = QLineEdit(self.v_margin_vertical_mm)
        pos_grid.addWidget(self.e_margin_vertical, 0, 1)
        pos_grid.addWidget(QLabel("mm"), 0, 2)
        position_layout.addLayout(pos_grid)
        
        # Vertical position
        pos_v_layout = QHBoxLayout()
        pos_v_layout.addWidget(QLabel("Pozycja pionowa:"))
        self.rb_pos_top = QRadioButton("Góra")
        self.rb_pos_bottom = QRadioButton("Dół")
        self.rb_pos_bottom.setChecked(True)
        pos_v_layout.addWidget(self.rb_pos_top)
        pos_v_layout.addWidget(self.rb_pos_bottom)
        position_layout.addLayout(pos_v_layout)
        
        # Alignment
        align_layout = QHBoxLayout()
        align_layout.addWidget(QLabel("Wyrównanie:"))
        self.rb_align_left = QRadioButton("Lewa")
        self.rb_align_center = QRadioButton("Środek")
        self.rb_align_right = QRadioButton("Prawa")
        self.rb_align_right.setChecked(True)
        align_layout.addWidget(self.rb_align_left)
        align_layout.addWidget(self.rb_align_center)
        align_layout.addWidget(self.rb_align_right)
        position_layout.addLayout(align_layout)
        
        layout.addWidget(position_group)
        
        # 3. Format
        format_group = QFrame()
        format_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        format_layout = QVBoxLayout(format_group)
        
        format_label = QLabel("Format numeracji")
        format_label.setStyleSheet("font-weight: bold;")
        format_layout.addWidget(format_label)
        
        self.rb_format_simple = QRadioButton("Prosty (np. 1, 2, 3)")
        self.rb_format_full = QRadioButton("Pełny (np. Strona 1 z 10)")
        self.rb_format_simple.setChecked(True)
        format_layout.addWidget(self.rb_format_simple)
        format_layout.addWidget(self.rb_format_full)
        
        layout.addWidget(format_group)
        
        # 4. Font
        font_group = QFrame()
        font_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        font_layout = QVBoxLayout(font_group)
        
        font_label = QLabel("Czcionka")
        font_label.setStyleSheet("font-weight: bold;")
        font_layout.addWidget(font_label)
        
        font_grid = QGridLayout()
        font_grid.addWidget(QLabel("Nazwa:"), 0, 0)
        self.combo_font_name = QComboBox()
        self.combo_font_name.addItems(self.font_options)
        self.combo_font_name.setCurrentText(self.v_font_name)
        font_grid.addWidget(self.combo_font_name, 0, 1)
        
        font_grid.addWidget(QLabel("Rozmiar:"), 0, 2)
        self.combo_font_size = QComboBox()
        self.combo_font_size.addItems(self.size_options)
        self.combo_font_size.setCurrentText(self.v_font_size)
        font_grid.addWidget(self.combo_font_size, 0, 3)
        
        font_layout.addLayout(font_grid)
        layout.addWidget(font_group)
        
        # 5. Mode
        mode_group = QFrame()
        mode_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        mode_layout = QVBoxLayout(mode_group)
        
        mode_label = QLabel("Tryb numeracji")
        mode_label.setStyleSheet("font-weight: bold;")
        mode_layout.addWidget(mode_label)
        
        self.rb_mode_normal = QRadioButton("Normalna")
        self.rb_mode_mirror = QRadioButton("Lustrzana")
        self.rb_mode_normal.setChecked(True)
        mode_layout.addWidget(self.rb_mode_normal)
        mode_layout.addWidget(self.rb_mode_mirror)
        
        layout.addWidget(mode_group)
        
        # 6. Start numbering
        start_group = QFrame()
        start_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        start_layout = QVBoxLayout(start_group)
        
        start_label = QLabel("Początek numeracji")
        start_label.setStyleSheet("font-weight: bold;")
        start_layout.addWidget(start_label)
        
        start_grid = QGridLayout()
        start_grid.addWidget(QLabel("Strona początkowa:"), 0, 0)
        self.e_start_page = QLineEdit(self.v_start_page)
        start_grid.addWidget(self.e_start_page, 0, 1)
        
        start_grid.addWidget(QLabel("Liczba początkowa:"), 1, 0)
        self.e_start_number = QLineEdit(self.v_start_number)
        start_grid.addWidget(self.e_start_number, 1, 1)
        
        start_layout.addLayout(start_grid)
        layout.addWidget(start_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)

    def ok(self):
        """OK button handler"""
        try:
            margin_left = float(self.e_margin_left.text().replace(',', '.'))
            margin_right = float(self.e_margin_right.text().replace(',', '.'))
            margin_vertical = float(self.e_margin_vertical.text().replace(',', '.'))
            start_page = int(self.e_start_page.text())
            start_number = int(self.e_start_number.text())
            
            if start_page < 1 or start_number < 1:
                raise ValueError("Strona i liczba początkowa muszą być >= 1")
            
            vertical_pos = 'gora' if self.rb_pos_top.isChecked() else 'dol'
            
            if self.rb_align_left.isChecked():
                alignment = 'lewa'
            elif self.rb_align_center.isChecked():
                alignment = 'srodek'
            else:
                alignment = 'prawa'
            
            mode = 'lustrzana' if self.rb_mode_mirror.isChecked() else 'normalna'
            format_type = 'full' if self.rb_format_full.isChecked() else 'simple'
            
            self.result = {
                'margin_left_mm': margin_left,
                'margin_right_mm': margin_right,
                'margin_vertical_mm': margin_vertical,
                'vertical_pos': vertical_pos,
                'alignment': alignment,
                'mode': mode,
                'format_type': format_type,
                'font_name': self.combo_font_name.currentText(),
                'font_size': int(self.combo_font_size.currentText()),
                'mirror_margins': self.cb_mirror_margins.isChecked(),
                'start_page': start_page,
                'start_num': start_number
            }
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowe dane: {e}")

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()


# ====================================================================
# KLASA: DIALOG MARGINESU NUMERACJI
# ====================================================================

class PageNumberMarginDialog(QDialog):
    """Dialog for page number margin settings - migrated from Tkinter"""
    
    def __init__(self, parent, initial_margin_mm=20):
        super().__init__(parent)
        self.setWindowTitle("Usuń numerację stron")
        self.setModal(True)
        self.result = None
        self.initial_margin_mm = initial_margin_mm
        
        self.build_ui()
        self.center_dialog()

    def center_dialog(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        label = QLabel("Podaj wysokość marginesu do skanowania (w mm):")
        layout.addWidget(label)
        
        self.entry = QLineEdit(str(self.initial_margin_mm))
        layout.addWidget(self.entry)
        
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)

    def ok(self):
        """OK button handler"""
        try:
            value = float(self.entry.text().replace(',', '.'))
            if value <= 0:
                raise ValueError("Margines musi być większy od zera")
            self.result = value
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowa wartość: {e}")

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()


# ====================================================================
# KLASA: DIALOG PRZESUNIĘCIA ZAWARTOŚCI
# ====================================================================

class ShiftContentDialog(QDialog):
    """Dialog for shifting page content - migrated from Tkinter"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Przesunięcie zawartości strony")
        self.setModal(True)
        self.result = None
        
        self.build_ui()
        self.center_dialog()

    def center_dialog(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # X shift
        x_group = QFrame()
        x_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        x_layout = QVBoxLayout(x_group)
        
        x_label = QLabel("Przesunięcie poziome (X)")
        x_label.setStyleSheet("font-weight: bold;")
        x_layout.addWidget(x_label)
        
        x_dir_layout = QHBoxLayout()
        x_dir_layout.addWidget(QLabel("Kierunek:"))
        self.rb_x_left = QRadioButton("Lewo")
        self.rb_x_right = QRadioButton("Prawo")
        self.rb_x_right.setChecked(True)
        x_dir_layout.addWidget(self.rb_x_left)
        x_dir_layout.addWidget(self.rb_x_right)
        x_layout.addLayout(x_dir_layout)
        
        x_val_layout = QHBoxLayout()
        x_val_layout.addWidget(QLabel("Wartość:"))
        self.e_x_value = QLineEdit("0")
        x_val_layout.addWidget(self.e_x_value)
        x_val_layout.addWidget(QLabel("mm"))
        x_layout.addLayout(x_val_layout)
        
        layout.addWidget(x_group)
        
        # Y shift
        y_group = QFrame()
        y_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        y_layout = QVBoxLayout(y_group)
        
        y_label = QLabel("Przesunięcie pionowe (Y)")
        y_label.setStyleSheet("font-weight: bold;")
        y_layout.addWidget(y_label)
        
        y_dir_layout = QHBoxLayout()
        y_dir_layout.addWidget(QLabel("Kierunek:"))
        self.rb_y_down = QRadioButton("Dół")
        self.rb_y_up = QRadioButton("Góra")
        self.rb_y_up.setChecked(True)
        y_dir_layout.addWidget(self.rb_y_down)
        y_dir_layout.addWidget(self.rb_y_up)
        y_layout.addLayout(y_dir_layout)
        
        y_val_layout = QHBoxLayout()
        y_val_layout.addWidget(QLabel("Wartość:"))
        self.e_y_value = QLineEdit("0")
        y_val_layout.addWidget(self.e_y_value)
        y_val_layout.addWidget(QLabel("mm"))
        y_layout.addLayout(y_val_layout)
        
        layout.addWidget(y_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)

    def ok(self):
        """OK button handler"""
        try:
            x_mm = float(self.e_x_value.text().replace(',', '.'))
            y_mm = float(self.e_y_value.text().replace(',', '.'))
            if x_mm < 0 or y_mm < 0:
                raise ValueError("Wartości przesunięcia muszą być nieujemne.")
            
            x_dir = 'lewo' if self.rb_x_left.isChecked() else 'prawo'
            y_dir = 'dol' if self.rb_y_down.isChecked() else 'gora'
            
            self.result = {
                'x_dir': x_dir,
                'y_dir': y_dir,
                'x_mm': x_mm,
                'y_mm': y_mm
            }
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Błąd Wprowadzania", 
                f"Nieprawidłowa wartość: {e}. Użyj cyfr, kropki lub przecinka.")

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()



# ====================================================================
# KLASA: DIALOG IMPORTU OBRAZU
# ====================================================================

class ImageImportSettingsDialog(QDialog):
    """Dialog for image import settings - migrated from Tkinter"""
    
    def __init__(self, parent, title, image_path):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result = None
        self.image_path = image_path
        
        # Read image information
        try:
            img = Image.open(image_path)
            self.image_pixel_width, self.image_pixel_height = img.size
            dpi_info = img.info.get('dpi', (72, 72))
            self.image_dpi = int(dpi_info[0]) if isinstance(dpi_info, tuple) else 72
        except Exception as e:
            self.image_pixel_width = self.image_pixel_height = 0
            self.image_dpi = 72
        
        self.build_ui()
        self.center_dialog()

    def center_dialog(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Image information
        info_group = QFrame()
        info_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        info_layout = QVBoxLayout(info_group)
        
        info_label = QLabel("Informacje o obrazie źródłowym")
        info_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(info_label)
        
        info_layout.addWidget(QLabel(f"Wymiary: {self.image_pixel_width} x {self.image_pixel_height} px"))
        info_layout.addWidget(QLabel(f"DPI: {self.image_dpi}"))
        
        layout.addWidget(info_group)
        
        # Orientation
        orient_group = QFrame()
        orient_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        orient_layout = QVBoxLayout(orient_group)
        
        orient_label = QLabel("Orientacja strony docelowej (A4)")
        orient_label.setStyleSheet("font-weight: bold;")
        orient_layout.addWidget(orient_label)
        
        self.rb_portrait = QRadioButton("Pionowa (210 × 297 mm)")
        self.rb_landscape = QRadioButton("Pozioma (297 × 210 mm)")
        self.rb_portrait.setChecked(True)
        orient_layout.addWidget(self.rb_portrait)
        orient_layout.addWidget(self.rb_landscape)
        
        layout.addWidget(orient_group)
        
        # Fit mode
        fit_group = QFrame()
        fit_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        fit_layout = QVBoxLayout(fit_group)
        
        fit_label = QLabel("Tryb dopasowania obrazu")
        fit_label.setStyleSheet("font-weight: bold;")
        fit_layout.addWidget(fit_label)
        
        self.rb_fit = QRadioButton("Dopasuj (zachowaj proporcje)")
        self.rb_fill = QRadioButton("Wypełnij (może przyciąć)")
        self.rb_stretch = QRadioButton("Rozciągnij (bez zachowania proporcji)")
        self.rb_fit.setChecked(True)
        fit_layout.addWidget(self.rb_fit)
        fit_layout.addWidget(self.rb_fill)
        fit_layout.addWidget(self.rb_stretch)
        
        layout.addWidget(fit_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)

    def ok(self):
        """OK button handler"""
        orientation = 'portrait' if self.rb_portrait.isChecked() else 'landscape'
        
        if self.rb_fit.isChecked():
            fit_mode = 'fit'
        elif self.rb_fill.isChecked():
            fit_mode = 'fill'
        else:
            fit_mode = 'stretch'
        
        self.result = {
            'orientation': orientation,
            'fit_mode': fit_mode
        }
        self.accept()

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()


# ====================================================================
# KLASA: DIALOG WYBORU ZAKRESU STRON
# ====================================================================

class EnhancedPageRangeDialog(QDialog):
    """Dialog for selecting page range - migrated from Tkinter"""
    
    def __init__(self, parent, title, imported_doc):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result = None
        self.imported_doc = imported_doc
        self.total_pages = len(imported_doc) if imported_doc else 0
        
        self.build_ui()
        self.center_dialog()

    def center_dialog(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        label = QLabel(f"Dokument zawiera {self.total_pages} stron.\nWybierz strony do zaimportowania:")
        layout.addWidget(label)
        
        self.rb_all = QRadioButton("Wszystkie strony")
        self.rb_all.setChecked(True)
        layout.addWidget(self.rb_all)
        
        self.rb_range = QRadioButton("Zakres stron (np. 1-3,5,7-9):")
        layout.addWidget(self.rb_range)
        
        self.entry_range = QLineEdit()
        self.entry_range.setPlaceholderText("Przykład: 1-3,5,7-9")
        layout.addWidget(self.entry_range)
        
        # Buttons
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)

    def ok(self):
        """OK button handler"""
        if self.rb_all.isChecked():
            self.result = list(range(self.total_pages))
        else:
            raw_range = self.entry_range.text().strip()
            parsed = self._parse_range(raw_range)
            if parsed is None:
                QMessageBox.warning(self, "Błąd zakresu", 
                    "Nieprawidłowy format zakresu. Użyj formatu: 1-3,5,7-9")
                return
            self.result = parsed
        self.accept()

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()

    def _parse_range(self, raw_range: str) -> Optional[List[int]]:
        """Parse page range string"""
        try:
            indices = []
            parts = raw_range.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start_str, end_str = part.split('-', 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    if start < 1 or end < start or end > self.total_pages:
                        return None
                    indices.extend(range(start - 1, end))
                else:
                    page_num = int(part)
                    if page_num < 1 or page_num > self.total_pages:
                        return None
                    indices.append(page_num - 1)
            return sorted(set(indices))
        except:
            return None


# ====================================================================
# KLASA: DIALOG SCALANIA STRON NA ARKUSZU
# ====================================================================

class MergePageGridDialog(QDialog):
    """Dialog for merging pages into a grid - migrated from Tkinter"""
    
    def __init__(self, parent, page_count):
        super().__init__(parent)
        self.setWindowTitle("Scal strony na arkusz")
        self.setModal(True)
        self.result = None
        self.page_count = page_count
        
        # Initialize variables
        self.format_var = "A4"
        self.orientation_var = "portrait"
        self.rows_var = "2"
        self.cols_var = "2"
        self.spacing_x_mm = "5"
        self.spacing_y_mm = "5"
        
        self.build_ui()
        self.center_dialog()

    def center_dialog(self):
        """Center dialog relative to parent"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2
            )

    def build_ui(self):
        """Build the dialog UI"""
        main_layout = QHBoxLayout(self)
        
        # LEFT PART - Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Sheet format
        format_group = QFrame()
        format_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        format_layout = QVBoxLayout(format_group)
        
        format_label = QLabel("Arkusz docelowy")
        format_label.setStyleSheet("font-weight: bold;")
        format_layout.addWidget(format_label)
        
        format_grid = QGridLayout()
        format_grid.addWidget(QLabel("Format:"), 0, 0)
        self.combo_format = QComboBox()
        self.combo_format.addItems(["A3", "A4", "A5"])
        self.combo_format.setCurrentText(self.format_var)
        format_grid.addWidget(self.combo_format, 0, 1)
        
        format_grid.addWidget(QLabel("Orientacja:"), 1, 0)
        self.combo_orientation = QComboBox()
        self.combo_orientation.addItems(["Pionowa", "Pozioma"])
        format_grid.addWidget(self.combo_orientation, 1, 1)
        
        format_layout.addLayout(format_grid)
        left_layout.addWidget(format_group)
        
        # Spacing
        spacing_group = QFrame()
        spacing_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        spacing_layout = QVBoxLayout(spacing_group)
        
        spacing_label = QLabel("Odstępy między stronami (mm)")
        spacing_label.setStyleSheet("font-weight: bold;")
        spacing_layout.addWidget(spacing_label)
        
        spacing_grid = QGridLayout()
        spacing_grid.addWidget(QLabel("Poziomy:"), 0, 0)
        self.e_spacing_x = QLineEdit(self.spacing_x_mm)
        spacing_grid.addWidget(self.e_spacing_x, 0, 1)
        
        spacing_grid.addWidget(QLabel("Pionowy:"), 1, 0)
        self.e_spacing_y = QLineEdit(self.spacing_y_mm)
        spacing_grid.addWidget(self.e_spacing_y, 1, 1)
        
        spacing_layout.addLayout(spacing_grid)
        left_layout.addWidget(spacing_group)
        
        # Grid
        grid_group = QFrame()
        grid_group.setFrameStyle(QFrame.Box | QFrame.Plain)
        grid_layout = QVBoxLayout(grid_group)
        
        grid_label = QLabel("Siatka stron")
        grid_label.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(grid_label)
        
        grid_grid = QGridLayout()
        grid_grid.addWidget(QLabel("Wiersze:"), 0, 0)
        self.e_rows = QLineEdit(self.rows_var)
        grid_grid.addWidget(self.e_rows, 0, 1)
        
        grid_grid.addWidget(QLabel("Kolumny:"), 1, 0)
        self.e_cols = QLineEdit(self.cols_var)
        grid_grid.addWidget(self.e_cols, 1, 1)
        
        grid_layout.addLayout(grid_grid)
        left_layout.addWidget(grid_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        
        # RIGHT PART - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_label = QLabel("Podgląd układu")
        preview_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(preview_label)
        
        self.preview_canvas = QLabel()
        self.preview_canvas.setMinimumSize(300, 400)
        self.preview_canvas.setStyleSheet("background-color: white; border: 1px solid black;")
        self.preview_canvas.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.preview_canvas)
        
        main_layout.addWidget(right_widget)
        
        # Buttons at bottom
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        
        btn_ok = QPushButton("Scal")
        btn_ok.clicked.connect(self.ok)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.clicked.connect(self.cancel)
        button_layout.addWidget(btn_cancel)
        
        main_layout_vertical = QVBoxLayout()
        main_layout_vertical.addLayout(main_layout)
        main_layout_vertical.addWidget(button_widget)
        
        container = QWidget()
        container.setLayout(main_layout_vertical)
        final_layout = QVBoxLayout(self)
        final_layout.addWidget(container)
        
        # Connect signals for preview updates
        self.combo_format.currentTextChanged.connect(self._update_grid_preview)
        self.combo_orientation.currentTextChanged.connect(self._update_grid_preview)
        self.e_rows.textChanged.connect(self._update_grid_preview)
        self.e_cols.textChanged.connect(self._update_grid_preview)
        self.e_spacing_x.textChanged.connect(self._update_grid_preview)
        self.e_spacing_y.textChanged.connect(self._update_grid_preview)
        
        self._update_grid_preview()

    def _update_grid_preview(self):
        """Update preview (simple text preview)"""
        try:
            rows = int(self.e_rows.text())
            cols = int(self.e_cols.text())
            text = f"Układ: {rows} × {cols}\n"
            text += f"Stron na arkusz: {rows * cols}\n"
            text += f"Format: {self.combo_format.currentText()}\n"
            text += f"Orientacja: {self.combo_orientation.currentText()}"
            self.preview_canvas.setText(text)
        except:
            self.preview_canvas.setText("Nieprawidłowe dane")

    def ok(self):
        """OK button handler"""
        try:
            rows = int(self.e_rows.text())
            cols = int(self.e_cols.text())
            spacing_x = float(self.e_spacing_x.text().replace(',', '.'))
            spacing_y = float(self.e_spacing_y.text().replace(',', '.'))
            
            if rows < 1 or cols < 1:
                raise ValueError("Liczba wierszy i kolumn musi być >= 1")
            
            orientation = 'portrait' if self.combo_orientation.currentText() == "Pionowa" else 'landscape'
            
            self.result = {
                'format': self.combo_format.currentText(),
                'orientation': orientation,
                'rows': rows,
                'cols': cols,
                'spacing_x_mm': spacing_x,
                'spacing_y_mm': spacing_y
            }
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowe dane: {e}")

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.reject()



# ====================================================================
# KLASA: RAMKA MINIATURY
# ====================================================================

class ThumbnailFrame(QFrame):
    """Thumbnail frame widget - migrated from tk.Frame"""
    
    def __init__(self, parent, viewer_app, page_index, column_width):
        super().__init__(parent)
        self.viewer_app = viewer_app
        self.page_index = page_index
        self.column_width = column_width
        
        self.bg_normal = "#F5F5F5"
        self.bg_selected = "#CCEEFF"
        
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        self.setStyleSheet(f"background-color: {self.bg_normal};")
        
        self.setup_ui()

    def setup_ui(self):
        """Build the thumbnail UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Render image
        pixmap = self.viewer_app._render_and_scale(self.page_index, self.column_width)
        
        # Image container
        image_container = QFrame()
        image_container.setStyleSheet("background-color: white;")
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.img_label = QLabel()
        self.img_label.setPixmap(pixmap)
        self.img_label.setAlignment(Qt.AlignCenter)
        image_container_layout.addWidget(self.img_label)
        
        layout.addWidget(image_container)
        
        # Page label
        self.page_label = QLabel(f"Strona {self.page_index + 1}")
        self.page_label.setStyleSheet("font-weight: bold;")
        self.page_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.page_label)
        
        # Size label
        format_label = self.viewer_app._get_page_size_label(self.page_index)
        self.size_label = QLabel(format_label)
        self.size_label.setStyleSheet("color: gray;")
        self.size_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.size_label)

    def mousePressEvent(self, event):
        """Handle mouse press events (replaces bind)"""
        if event.button() == Qt.LeftButton:
            self.viewer_app._handle_lpm_click(self.page_index, event)
        elif event.button() == Qt.RightButton:
            self._handle_ppm_click(event, self.page_index)
        super().mousePressEvent(event)

    def _handle_ppm_click(self, event, page_index):
        """Handle right-click to show context menu"""
        self.viewer_app.show_context_menu(event.globalPos(), page_index)



# ====================================================================
# GŁÓWNA KLASA PROGRAMU: SELECTABLEPDFVIEWER
# ====================================================================

class SelectablePDFViewer(QMainWindow):
    """Main PDF Editor application - migrated from Tkinter to PySide6"""
    
    MM_TO_POINTS = 72 / 25.4
    MARGIN_HEIGHT_MM = 20
    MARGIN_HEIGHT_PT = MARGIN_HEIGHT_MM * MM_TO_POINTS

    def __init__(self):
        super().__init__()
        self.setWindowTitle(PROGRAM_TITLE)
        
        # Initialize data structures
        self.pdf_document = None
        self.selected_pages: Set[int] = set()
        self.pixmaps: Dict[int, QPixmap] = {}
        self.icons: Dict[str, Union[QIcon, str]] = {}
        
        self.thumb_frames: Dict[int, 'ThumbnailFrame'] = {}
        self.active_page_index = 0
        
        self.clipboard: Optional[bytes] = None
        self.pages_in_clipboard_count: int = 0
        
        # Thumbnail settings
        self.fixed_thumb_width = 250
        self.min_zoom_width = 150
        self.THUMB_PADDING = 8
        self.ZOOM_FACTOR = 0.9
        self.target_num_cols = 4
        self.min_cols = 2
        self.max_cols = 10
        self.MIN_WINDOW_WIDTH = 997
        self.render_dpi_factor = 0.833
        
        # Undo/Redo stacks
        self.undo_stack: List[bytes] = []
        self.redo_stack: List[bytes] = []
        self.max_stack_size = 50
        
        # Setup UI
        self._set_initial_geometry()
        self._load_icons_or_fallback(size=28)
        self._create_menu()
        self._setup_key_bindings()
        self._setup_main_ui()
        
        self.update_tool_button_states()

    def _set_initial_geometry(self):
        """Set initial window size and position"""
        screen = QApplication.primaryScreen().geometry()
        initial_width = self.MIN_WINDOW_WIDTH
        initial_height = int(screen.height() * 0.50)
        self.setMinimumSize(self.MIN_WINDOW_WIDTH, initial_height)
        
        x_cordinate = (screen.width() - initial_width) // 2
        y_cordinate = (screen.height() - initial_height) // 2
        self.setGeometry(x_cordinate, y_cordinate, initial_width, initial_height)

    def _load_icons_or_fallback(self, size=28):
        """Load icons from files or use emoji fallbacks"""
        icon_map = {
            'open': ('📂', "open.png"),
            'save': ('💾', "save.png"),
            'undo': ('↩️', "undo.png"),
            'redo': ('↪️', "redo.png"),
            'delete': ('🗑️', "delete.png"),
            'cut': ('✂️', "cut.png"),
            'copy': ('📋', "copy.png"),
            'paste_b': ('⬆️📄', "paste_before.png"),
            'paste_a': ('⬇️📄', "paste_after.png"),
            'insert_b': ('⬆️➕', "insert_before.png"),
            'insert_a': ('⬇️➕', "insert_after.png"),
            'rotate_l': ('↶', "rotate_left.png"),
            'rotate_r': ('↷', "rotate_right.png"),
            'import': ('📥', "import.png"),
            'export': ('📤', "export.png"),
            'image_import': ('🖼️', "image_import.png"),
            'export_image': ('🎨', "export_image.png"),
            'shift': ('⬌', "shift.png"),
            'page_num_del': ('🔢❌', "page_num_del.png"),
            'add_nums': ('🔢', "add_nums.png"),
            'zoom_in': ('+', "zoom_in.png"),
            'zoom_out': ('-', "zoom_out.png"),
        }
        
        for key, (fallback, filename) in icon_map.items():
            icon_path = os.path.join(ICON_FOLDER, filename)
            if os.path.exists(icon_path):
                try:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self.icons[key] = icon
                        continue
                except Exception as e:
                    pass
            # Fallback to emoji text
            self.icons[key] = fallback

    def _create_menu(self):
        """Create menu bar (replaces tk.Menu)"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Plik")
        
        open_action = QAction("Otwórz PDF", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)
        
        save_action = QAction("Zapisz jako...", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Importuj PDF...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_pdf_after_active_page)
        file_menu.addAction(import_action)
        
        export_action = QAction("Eksportuj zaznaczone...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.extract_selected_pages)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        import_img_action = QAction("Importuj obraz...", self)
        import_img_action.triggered.connect(self.import_image_to_new_page)
        file_menu.addAction(import_img_action)
        
        export_img_action = QAction("Eksportuj do obrazu...", self)
        export_img_action.triggered.connect(self.export_selected_pages_to_image)
        file_menu.addAction(export_img_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Zakończ", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edycja")
        self._populate_edit_menu(edit_menu)
        
        # Modifications menu
        mod_menu = menubar.addMenu("Modyfikacje")
        self._populate_modifications_menu(mod_menu)
        
        # Help menu
        help_menu = menubar.addMenu("Pomoc")
        
        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _populate_edit_menu(self, menu):
        """Populate edit menu"""
        undo_action = QAction("Cofnij", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo)
        menu.addAction(undo_action)
        
        redo_action = QAction("Ponów", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo)
        menu.addAction(redo_action)
        
        menu.addSeparator()
        
        cut_action = QAction("Wytnij", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        cut_action.triggered.connect(self.cut_selected_pages)
        menu.addAction(cut_action)
        
        copy_action = QAction("Kopiuj", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self.copy_selected_pages)
        menu.addAction(copy_action)
        
        paste_action = QAction("Wklej po", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        paste_action.triggered.connect(self.paste_pages_after)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Usuń zaznaczone", self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self.delete_selected_pages)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        select_all_action = QAction("Zaznacz wszystko", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self._select_all)
        menu.addAction(select_all_action)

    def _populate_modifications_menu(self, menu):
        """Populate modifications menu"""
        rotate_left_action = QAction("Obróć w lewo", self)
        rotate_left_action.triggered.connect(lambda: self.rotate_selected_page(-90))
        menu.addAction(rotate_left_action)
        
        rotate_right_action = QAction("Obróć w prawo", self)
        rotate_right_action.triggered.connect(lambda: self.rotate_selected_page(90))
        menu.addAction(rotate_right_action)
        
        menu.addSeparator()
        
        insert_before_action = QAction("Wstaw pustą stronę przed", self)
        insert_before_action.triggered.connect(self.insert_blank_page_before)
        menu.addAction(insert_before_action)
        
        insert_after_action = QAction("Wstaw pustą stronę po", self)
        insert_after_action.triggered.connect(self.insert_blank_page_after)
        menu.addAction(insert_after_action)
        
        menu.addSeparator()
        
        crop_action = QAction("Kadruj/Zmień rozmiar", self)
        crop_action.triggered.connect(self.apply_page_crop_resize_dialog)
        menu.addAction(crop_action)
        
        shift_action = QAction("Przesuń zawartość", self)
        shift_action.triggered.connect(self.shift_page_content)
        menu.addAction(shift_action)
        
        menu.addSeparator()
        
        add_nums_action = QAction("Wstaw numerację", self)
        add_nums_action.triggered.connect(self.insert_page_numbers)
        menu.addAction(add_nums_action)
        
        remove_nums_action = QAction("Usuń numerację", self)
        remove_nums_action.triggered.connect(self.remove_page_numbers)
        menu.addAction(remove_nums_action)
        
        menu.addSeparator()
        
        merge_action = QAction("Scal strony na arkusz", self)
        merge_action.triggered.connect(self.merge_pages_to_grid)
        menu.addAction(merge_action)
        
        duplicate_action = QAction("Duplikuj stronę", self)
        duplicate_action.triggered.connect(self.duplicate_selected_page)
        menu.addAction(duplicate_action)

    def _setup_key_bindings(self):
        """Setup keyboard shortcuts (replaces bind)"""
        # Navigation shortcuts
        QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self._move_focus_and_scroll(-1))
        QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self._move_focus_and_scroll(1))
        QShortcut(QKeySequence(Qt.Key_Space), self, self._toggle_selection_space)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._clear_all_selection)
        
        # Zoom shortcuts
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)


    def _setup_main_ui(self):
        """Setup main UI with toolbar and scroll area"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar frame
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"background-color: {BG_SECONDARY}; padding: 5px;")
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # Add tool buttons
        self._create_toolbar_buttons(toolbar_layout)
        
        main_layout.addWidget(toolbar_frame)
        
        # Scroll area for thumbnails (replaces tk.Canvas + Scrollbar)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #F5F5F5;")
        
        self.scrollable_frame = QWidget()
        self.scrollable_frame.setStyleSheet("background-color: #F5F5F5;")
        self.scroll_layout = QGridLayout(self.scrollable_frame)
        
        self.scroll_area.setWidget(self.scrollable_frame)
        main_layout.addWidget(self.scroll_area)
        
        # Status bar (replaces tk.Label)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("Gotowy. Otwórz plik PDF.")
        
        # Install event filter for wheel events
        self.scroll_area.installEventFilter(self)

    def _create_toolbar_buttons(self, layout):
        """Create toolbar buttons (replaces tk.Button with pack)"""
        # Button styles
        GRAY_BG = BG_BUTTON_DEFAULT
        GRAY_FG = FG_TEXT
        
        def create_tool_button(key, slot, tooltip_text):
            """Helper to create a button"""
            btn = QPushButton()
            icon = self.icons.get(key)
            if isinstance(icon, QIcon):
                btn.setIcon(icon)
                btn.setIconSize(QSize(28, 28))
            else:
                btn.setText(icon)  # Emoji fallback
                btn.setStyleSheet(f"font-size: 14pt;")
            btn.clicked.connect(slot)
            btn.setEnabled(False)  # Initially disabled
            btn.setToolTip(tooltip_text)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GRAY_BG};
                    border: 1px solid #999;
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: #C0C0C0;
                }}
                QPushButton:pressed {{
                    background-color: #A0A0A0;
                }}
                QPushButton:disabled {{
                    background-color: #E0E0E0;
                    color: #999;
                }}
            """)
            return btn
        
        # File operations
        self.open_button = QPushButton()
        self.open_button.setText("📂" if not isinstance(self.icons.get('open'), QIcon) else "")
        if isinstance(self.icons.get('open'), QIcon):
            self.open_button.setIcon(self.icons['open'])
            self.open_button.setIconSize(QSize(28, 28))
        self.open_button.clicked.connect(self.open_pdf)
        self.open_button.setToolTip("Otwórz plik PDF")
        self.open_button.setFixedSize(36, 36)
        layout.addWidget(self.open_button)
        
        self.save_button = create_tool_button('save', self.save_document, "Zapisz całość do nowego pliku PDF")
        layout.addWidget(self.save_button)
        
        layout.addSpacing(15)
        
        # Import/Export
        self.import_button = create_tool_button('import', self.import_pdf_after_active_page, "Importuj strony z pliku PDF")
        layout.addWidget(self.import_button)
        
        self.export_button = create_tool_button('export', self.extract_selected_pages, "Eksportuj strony do pliku PDF")
        layout.addWidget(self.export_button)
        
        layout.addSpacing(15)
        
        self.image_import_button = create_tool_button('image_import', self.import_image_to_new_page, "Importuj strony z pliku obrazu")
        layout.addWidget(self.image_import_button)
        
        self.export_image_button = create_tool_button('export_image', self.export_selected_pages_to_image, "Eksportuj strony do plików PNG")
        layout.addWidget(self.export_image_button)
        
        layout.addSpacing(15)
        
        # Undo/Redo
        self.undo_button = create_tool_button('undo', self.undo, "Cofnij ostatnią zmianę")
        layout.addWidget(self.undo_button)
        
        self.redo_button = create_tool_button('redo', self.redo, "Ponów cofniętą zmianę")
        layout.addWidget(self.redo_button)
        
        layout.addSpacing(15)
        
        # Edit operations
        self.delete_button = create_tool_button('delete', self.delete_selected_pages, "Usuń zaznaczone strony")
        layout.addWidget(self.delete_button)
        
        self.cut_button = create_tool_button('cut', self.cut_selected_pages, "Wytnij zaznaczone strony")
        layout.addWidget(self.cut_button)
        
        self.copy_button = create_tool_button('copy', self.copy_selected_pages, "Skopiuj zaznaczone strony")
        layout.addWidget(self.copy_button)
        
        self.paste_before_button = create_tool_button('paste_b', self.paste_pages_before, "Wklej stronę przed bieżącą")
        layout.addWidget(self.paste_before_button)
        
        self.paste_after_button = create_tool_button('paste_a', self.paste_pages_after, "Wklej stronę po bieżącej")
        layout.addWidget(self.paste_after_button)
        
        layout.addSpacing(15)
        
        # Insert
        self.insert_before_button = create_tool_button('insert_b', self.insert_blank_page_before, "Wstaw pustą stronę przed bieżącą")
        layout.addWidget(self.insert_before_button)
        
        self.insert_after_button = create_tool_button('insert_a', self.insert_blank_page_after, "Wstaw pustą stronę po bieżącej")
        layout.addWidget(self.insert_after_button)
        
        layout.addSpacing(15)
        
        # Rotate
        self.rotate_left_button = create_tool_button('rotate_l', lambda: self.rotate_selected_page(-90), "Obróć w lewo")
        layout.addWidget(self.rotate_left_button)
        
        self.rotate_right_button = create_tool_button('rotate_r', lambda: self.rotate_selected_page(90), "Obróć w prawo")
        layout.addWidget(self.rotate_right_button)
        
        layout.addSpacing(15)
        
        # Modifications
        self.shift_content_btn = create_tool_button('shift', self.shift_page_content, "Zmiana marginesów")
        layout.addWidget(self.shift_content_btn)
        
        self.remove_nums_btn = create_tool_button('page_num_del', self.remove_page_numbers, "Usuwanie numeracji")
        layout.addWidget(self.remove_nums_btn)
        
        self.add_nums_btn = create_tool_button('add_nums', self.insert_page_numbers, "Wstawianie numeracji")
        layout.addWidget(self.add_nums_btn)
        
        layout.addStretch()
        
        # Zoom buttons (right side)
        self.zoom_in_button = create_tool_button('zoom_in', self.zoom_in, "Powiększ")
        layout.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = create_tool_button('zoom_out', self.zoom_out, "Pomniejsz")
        layout.addWidget(self.zoom_out_button)

    def eventFilter(self, obj, event):
        """Event filter for handling mouse wheel (replaces bind)"""
        if obj == self.scroll_area and event.type() == QEvent.Wheel:
            # Handle mouse wheel for scrolling
            return False  # Let Qt handle it
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Handle window close event (replaces protocol WM_DELETE_WINDOW)"""
        if self.pdf_document is not None and len(self.undo_stack) > 0:
            reply = QMessageBox.question(
                self,
                "Niezapisane zmiany",
                "Czy chcesz zapisać zmiany w dokumencie przed zamknięciem programu?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.save_document()
                if len(self.undo_stack) > 0:
                    event.ignore()
                    return
        event.accept()

    # ===================================================================
    # STATUS AND UPDATE METHODS
    # ===================================================================

    def _update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)

    def update_tool_button_states(self):
        """Update toolbar button states based on document and selection"""
        has_doc = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single = len(self.selected_pages) == 1
        has_clipboard = self.clipboard is not None
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        
        # Enable/disable buttons
        self.save_button.setEnabled(has_doc)
        self.import_button.setEnabled(has_doc)
        self.export_button.setEnabled(has_selection)
        self.image_import_button.setEnabled(has_doc)
        self.export_image_button.setEnabled(has_selection)
        
        self.undo_button.setEnabled(has_undo)
        self.redo_button.setEnabled(has_redo)
        
        self.delete_button.setEnabled(has_selection)
        self.cut_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        self.paste_before_button.setEnabled(has_clipboard and has_doc)
        self.paste_after_button.setEnabled(has_clipboard and has_doc)
        
        self.insert_before_button.setEnabled(has_single)
        self.insert_after_button.setEnabled(has_single)
        
        self.rotate_left_button.setEnabled(has_selection)
        self.rotate_right_button.setEnabled(has_selection)
        
        self.shift_content_btn.setEnabled(has_selection)
        self.remove_nums_btn.setEnabled(has_selection)
        self.add_nums_btn.setEnabled(has_selection)
        
        self.zoom_in_button.setEnabled(has_doc)
        self.zoom_out_button.setEnabled(has_doc)


    # ===================================================================
    # FILE OPERATIONS
    # ===================================================================

    def open_pdf(self, filepath=None):
        """Open a PDF file"""
        if filepath is None:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Wybierz plik PDF",
                "",
                "Pliki PDF (*.pdf);;Wszystkie pliki (*)"
            )
        
        if not filepath:
            return
        
        try:
            if self.pdf_document:
                self.pdf_document.close()
            
            self.pdf_document = fitz.open(filepath)
            self.selected_pages.clear()
            self.pixmaps.clear()
            self.thumb_frames.clear()
            self.active_page_index = 0
            
            self.undo_stack.clear()
            self.redo_stack.clear()
            
            self._reconfigure_grid()
            self._update_status(f"Wczytano: {os.path.basename(filepath)} ({len(self.pdf_document)} stron)")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można otworzyć pliku: {e}")

    def save_document(self):
        """Save PDF document"""
        if not self.pdf_document:
            QMessageBox.warning(self, "Brak dokumentu", "Najpierw wczytaj lub stwórz dokument PDF.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz dokument PDF",
            "",
            "Pliki PDF (*.pdf);;Wszystkie pliki (*)"
        )
        
        if not filepath:
            return
        
        try:
            self.pdf_document.save(filepath)
            self._update_status(f"Zapisano: {os.path.basename(filepath)}")
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_tool_button_states()
            QMessageBox.information(self, "Sukces", f"Dokument zapisano pomyślnie:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku: {e}")

    def import_pdf_after_active_page(self):
        """Import pages from another PDF"""
        if not self.pdf_document:
            QMessageBox.warning(self, "Brak dokumentu", "Najpierw otwórz dokument PDF.")
            return
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik PDF do importu",
            "",
            "Pliki PDF (*.pdf)"
        )
        
        if not filepath:
            return
        
        try:
            imported_doc = fitz.open(filepath)
            
            # Show page range dialog
            dialog = EnhancedPageRangeDialog(self, "Wybierz strony do importu", imported_doc)
            dialog.exec()
            
            if dialog.result is None:
                imported_doc.close()
                return
            
            selected_indices = dialog.result
            
            # Determine insert position
            if self.selected_pages:
                insert_after = max(self.selected_pages)
            else:
                insert_after = len(self.pdf_document) - 1
            
            self._save_state_to_undo()
            
            # Import pages
            for offset, src_idx in enumerate(selected_indices):
                dest_idx = insert_after + 1 + offset
                self.pdf_document.insert_pdf(imported_doc, from_page=src_idx, to_page=src_idx, start_at=dest_idx)
            
            imported_doc.close()
            
            self._reconfigure_grid()
            self._update_status(f"Zaimportowano {len(selected_indices)} stron.")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zaimportować PDF: {e}")

    def extract_selected_pages(self):
        """Export selected pages to a new PDF"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do eksportu.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Eksportuj zaznaczone strony",
            "",
            "Pliki PDF (*.pdf)"
        )
        
        if not filepath:
            return
        
        try:
            output_doc = fitz.open()
            for page_idx in sorted(self.selected_pages):
                output_doc.insert_pdf(self.pdf_document, from_page=page_idx, to_page=page_idx)
            
            output_doc.save(filepath)
            output_doc.close()
            
            self._update_status(f"Wyeksportowano {len(self.selected_pages)} stron do: {os.path.basename(filepath)}")
            QMessageBox.information(self, "Sukces", f"Wyeksportowano {len(self.selected_pages)} stron.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wyeksportować stron: {e}")

    def import_image_to_new_page(self):
        """Import an image as a new PDF page"""
        if not self.pdf_document:
            QMessageBox.warning(self, "Brak dokumentu", "Najpierw otwórz dokument PDF.")
            return
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz obraz do importu",
            "",
            "Pliki obrazów (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        
        if not filepath:
            return
        
        try:
            # Show import settings dialog
            dialog = ImageImportSettingsDialog(self, "Ustawienia importu obrazu", filepath)
            dialog.exec()
            
            if dialog.result is None:
                return
            
            settings = dialog.result
            orientation = settings['orientation']
            fit_mode = settings['fit_mode']
            
            # Create new page with image
            if orientation == 'portrait':
                rect = fitz.Rect(0, 0, A4_WIDTH_POINTS, A4_HEIGHT_POINTS)
            else:
                rect = fitz.Rect(0, 0, A4_HEIGHT_POINTS, A4_WIDTH_POINTS)
            
            # Determine insert position
            if self.selected_pages:
                insert_after = max(self.selected_pages)
            else:
                insert_after = len(self.pdf_document) - 1
            
            self._save_state_to_undo()
            
            new_page = self.pdf_document.new_page(pno=insert_after + 1, width=rect.width, height=rect.height)
            
            # Insert image
            img_rect = new_page.rect
            new_page.insert_image(img_rect, filename=filepath, keep_proportion=(fit_mode != 'stretch'))
            
            self._reconfigure_grid()
            self._update_status(f"Zaimportowano obraz jako nową stronę.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zaimportować obrazu: {e}")

    def export_selected_pages_to_image(self):
        """Export selected pages to PNG images"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do eksportu.")
            return
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Wybierz katalog do zapisu obrazów"
        )
        
        if not directory:
            return
        
        try:
            for page_idx in sorted(self.selected_pages):
                page = self.pdf_document.load_page(page_idx)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for quality
                
                filename = f"page_{page_idx + 1}.png"
                filepath = os.path.join(directory, filename)
                pix.save(filepath)
            
            self._update_status(f"Wyeksportowano {len(self.selected_pages)} stron do: {directory}")
            QMessageBox.information(self, "Sukces", f"Wyeksportowano {len(self.selected_pages)} stron jako obrazy PNG.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wyeksportować obrazów: {e}")

    # ===================================================================
    # UNDO/REDO
    # ===================================================================

    def _save_state_to_undo(self):
        """Save current document state to undo stack"""
        if not self.pdf_document:
            return
        
        try:
            pdf_bytes = io.BytesIO()
            self.pdf_document.save(pdf_bytes)
            pdf_bytes.seek(0)
            
            self.undo_stack.append(pdf_bytes.read())
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            
            self.redo_stack.clear()
            self.update_tool_button_states()
            
        except Exception as e:
            self._update_status(f"Błąd zapisywania stanu: {e}")

    def undo(self):
        """Undo last operation"""
        if not self.undo_stack:
            return
        
        try:
            # Save current state to redo
            current_bytes = io.BytesIO()
            self.pdf_document.save(current_bytes)
            current_bytes.seek(0)
            self.redo_stack.append(current_bytes.read())
            
            # Restore previous state
            prev_bytes = self.undo_stack.pop()
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", prev_bytes)
            
            self._reconfigure_grid()
            self._update_status("Cofnięto ostatnią operację.")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można cofnąć operacji: {e}")

    def redo(self):
        """Redo last undone operation"""
        if not self.redo_stack:
            return
        
        try:
            # Save current state to undo
            current_bytes = io.BytesIO()
            self.pdf_document.save(current_bytes)
            current_bytes.seek(0)
            self.undo_stack.append(current_bytes.read())
            
            # Restore redo state
            redo_bytes = self.redo_stack.pop()
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", redo_bytes)
            
            self._reconfigure_grid()
            self._update_status("Ponowiono cofniętą operację.")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można ponowić operacji: {e}")


    # ===================================================================
    # CLIPBOARD OPERATIONS
    # ===================================================================

    def copy_selected_pages(self):
        """Copy selected pages to clipboard"""
        if not self.selected_pages:
            return
        
        try:
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            self._update_status(f"Skopiowano {len(self.selected_pages)} stron do schowka.")
            self.update_tool_button_states()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można skopiować stron: {e}")

    def cut_selected_pages(self):
        """Cut selected pages to clipboard"""
        if not self.selected_pages:
            return
        
        try:
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            
            self.delete_selected_pages(save_state=True)
            self._update_status(f"Wycięto {self.pages_in_clipboard_count} stron.")
            self.update_tool_button_states()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wyciąć stron: {e}")

    def paste_pages_before(self):
        """Paste pages before active page"""
        self._handle_paste_operation(before=True)

    def paste_pages_after(self):
        """Paste pages after active page"""
        self._handle_paste_operation(before=False)

    def _handle_paste_operation(self, before: bool):
        """Handle paste operation"""
        if not self.clipboard or not self.pdf_document:
            return
        
        try:
            target_index = self.active_page_index if before else self.active_page_index + 1
            self._perform_paste(target_index)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wkleić stron: {e}")

    def _perform_paste(self, target_index: int):
        """Perform paste at target index"""
        if not self.clipboard:
            return
        
        try:
            self._save_state_to_undo()
            
            clipboard_doc = fitz.open("pdf", self.clipboard)
            for i in range(len(clipboard_doc)):
                self.pdf_document.insert_pdf(clipboard_doc, from_page=i, to_page=i, start_at=target_index + i)
            
            clipboard_doc.close()
            
            self._reconfigure_grid()
            self._update_status(f"Wklejono {self.pages_in_clipboard_count} stron.")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas wklejania: {e}")

    def _get_page_bytes(self, page_indices: Set[int]) -> bytes:
        """Get pages as PDF bytes"""
        temp_doc = fitz.open()
        for idx in sorted(page_indices):
            temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
        
        pdf_bytes = io.BytesIO()
        temp_doc.save(pdf_bytes)
        temp_doc.close()
        pdf_bytes.seek(0)
        return pdf_bytes.read()

    # ===================================================================
    # PAGE EDIT OPERATIONS
    # ===================================================================

    def delete_selected_pages(self, save_state: bool = True):
        """Delete selected pages"""
        if not self.selected_pages:
            return
        
        total = len(self.pdf_document)
        to_delete = len(self.selected_pages)
        
        if to_delete >= total:
            QMessageBox.warning(self, "Błąd", "Nie można usunąć wszystkich stron z dokumentu.")
            return
        
        try:
            if save_state:
                self._save_state_to_undo()
            
            for page_idx in sorted(self.selected_pages, reverse=True):
                self.pdf_document.delete_page(page_idx)
            
            self.selected_pages.clear()
            self.active_page_index = min(self.active_page_index, len(self.pdf_document) - 1)
            
            self._reconfigure_grid()
            if save_state:
                self._update_status(f"Usunięto {to_delete} stron. Aktualna liczba stron: {len(self.pdf_document)}.")
            self.update_tool_button_states()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania: {e}")

    def rotate_selected_page(self, angle):
        """Rotate selected pages"""
        if not self.selected_pages:
            return
        
        try:
            self._save_state_to_undo()
            
            for page_idx in self.selected_pages:
                page = self.pdf_document.load_page(page_idx)
                page.set_rotation((page.rotation + angle) % 360)
            
            self._reconfigure_grid()
            self._update_status(f"Obrócono {len(self.selected_pages)} stron o {angle}°.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można obrócić stron: {e}")

    def insert_blank_page_before(self):
        """Insert blank page before active page"""
        self._handle_insert_operation(before=True)

    def insert_blank_page_after(self):
        """Insert blank page after active page"""
        self._handle_insert_operation(before=False)

    def _handle_insert_operation(self, before: bool):
        """Handle insert blank page operation"""
        if not self.pdf_document or len(self.selected_pages) != 1:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz dokładnie jedną stronę.")
            return
        
        try:
            self._save_state_to_undo()
            
            target_idx = list(self.selected_pages)[0]
            if not before:
                target_idx += 1
            
            self.pdf_document.new_page(pno=target_idx, width=A4_WIDTH_POINTS, height=A4_HEIGHT_POINTS)
            
            self._reconfigure_grid()
            position_text = "przed" if before else "po"
            self._update_status(f"Wstawiono pustą stronę {position_text} stroną {target_idx}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wstawić strony: {e}")

    def duplicate_selected_page(self):
        """Duplicate selected page"""
        if len(self.selected_pages) != 1:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz dokładnie jedną stronę do duplikacji.")
            return
        
        try:
            self._save_state_to_undo()
            
            page_idx = list(self.selected_pages)[0]
            self.pdf_document.insert_pdf(self.pdf_document, from_page=page_idx, to_page=page_idx, start_at=page_idx + 1)
            
            self._reconfigure_grid()
            self._update_status(f"Zduplikowano stronę {page_idx + 1}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zduplikować strony: {e}")

    # ===================================================================
    # PAGE MODIFICATIONS
    # ===================================================================

    def shift_page_content(self):
        """Shift page content"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do przesunięcia.")
            return
        
        dialog = ShiftContentDialog(self)
        dialog.exec()
        
        if dialog.result is None:
            return
        
        # Implementation would require pypdf transformations
        # Placeholder for now
        QMessageBox.information(self, "Info", "Funkcja przesuwania zawartości - implementacja w toku.")

    def apply_page_crop_resize_dialog(self):
        """Apply crop/resize dialog"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do obróbki.")
            return
        
        dialog = PageCropResizeDialog(self)
        dialog.exec()
        
        if dialog.result is None:
            return
        
        # Implementation would use the PDF processing methods
        # Placeholder for now
        QMessageBox.information(self, "Info", "Funkcja kadrowania/zmiany rozmiaru - implementacja w toku.")


    # ===================================================================
    # PAGE NUMBERING
    # ===================================================================

    def insert_page_numbers(self):
        """Insert page numbers"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do numeracji.")
            return
        
        dialog = PageNumberingDialog(self)
        dialog.exec()
        
        if dialog.result is None:
            return
        
        settings = dialog.result
        
        try:
            self._save_state_to_undo()
            
            # Implementation would use fitz to insert text
            # This is a simplified placeholder
            selected_indices = sorted(self.selected_pages)
            current_number = settings['start_num']
            
            for i in selected_indices:
                page = self.pdf_document.load_page(i)
                # Insert text using fitz
                # (Full implementation from original code would go here)
                current_number += 1
            
            self._reconfigure_grid()
            self._update_status(f"Numeracja wstawiona na {len(selected_indices)} stronach.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd przy dodawaniu numeracji: {e}")

    def remove_page_numbers(self):
        """Remove page numbers"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do usunięcia numeracji.")
            return
        
        dialog = PageNumberMarginDialog(self, initial_margin_mm=20)
        dialog.exec()
        
        if dialog.result is None:
            return
        
        margin_mm = dialog.result
        
        try:
            self._save_state_to_undo()
            
            # Implementation would use fitz to mask margins with white rectangles
            # (Full implementation from original code would go here)
            
            self._reconfigure_grid()
            self._update_status(f"Usunięto numerację z {len(self.selected_pages)} stron.")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd przy usuwaniu numeracji: {e}")

    def merge_pages_to_grid(self):
        """Merge pages into a grid"""
        if not self.selected_pages:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz strony do scalenia.")
            return
        
        dialog = MergePageGridDialog(self, len(self.selected_pages))
        dialog.exec()
        
        if dialog.result is None:
            return
        
        # Implementation would create a new page with a grid of pages
        # (Full implementation from original code would go here)
        QMessageBox.information(self, "Info", "Funkcja scalania stron - implementacja w toku.")

    # ===================================================================
    # NAVIGATION AND SELECTION
    # ===================================================================

    def _select_all(self):
        """Select all pages"""
        if self.pdf_document:
            self.selected_pages = set(range(len(self.pdf_document)))
            self.update_selection_display()

    def _clear_all_selection(self):
        """Clear all selection"""
        self.selected_pages.clear()
        self.update_selection_display()

    def _toggle_selection_space(self):
        """Toggle selection of active page"""
        if self.pdf_document:
            if self.active_page_index in self.selected_pages:
                self.selected_pages.remove(self.active_page_index)
            else:
                self.selected_pages.add(self.active_page_index)
            self.update_selection_display()

    def _move_focus_and_scroll(self, delta: int):
        """Move focus up/down and scroll"""
        if not self.pdf_document:
            return
        
        new_index = self.active_page_index + delta
        new_index = max(0, min(new_index, len(self.pdf_document) - 1))
        
        if new_index != self.active_page_index:
            self.active_page_index = new_index
            self.update_focus_display()
            
            # Scroll to make active frame visible
            if self.active_page_index in self.thumb_frames:
                frame = self.thumb_frames[self.active_page_index]
                self.scroll_area.ensureWidgetVisible(frame)

    def _handle_lpm_click(self, page_index, event):
        """Handle left mouse button click"""
        # Check for Ctrl modifier
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ControlModifier:
            # Toggle selection
            if page_index in self.selected_pages:
                self.selected_pages.remove(page_index)
            else:
                self.selected_pages.add(page_index)
        else:
            # Clear selection and select this page
            self.selected_pages.clear()
            self.selected_pages.add(page_index)
        
        self.active_page_index = page_index
        self.update_selection_display()
        self.update_focus_display()

    def show_context_menu(self, global_pos, page_index):
        """Show context menu (replaces tk.Menu post)"""
        menu = QMenu(self)
        
        menu.addAction("Obróć w lewo", lambda: self._context_rotate(page_index, -90))
        menu.addAction("Obróć w prawo", lambda: self._context_rotate(page_index, 90))
        menu.addSeparator()
        menu.addAction("Usuń stronę", lambda: self._context_delete(page_index))
        menu.addSeparator()
        menu.addAction("Wstaw pustą przed", lambda: self._context_insert(page_index, True))
        menu.addAction("Wstaw pustą po", lambda: self._context_insert(page_index, False))
        
        menu.exec(global_pos)

    def _context_rotate(self, page_index, angle):
        """Context menu: rotate page"""
        self.selected_pages = {page_index}
        self.rotate_selected_page(angle)

    def _context_delete(self, page_index):
        """Context menu: delete page"""
        self.selected_pages = {page_index}
        self.delete_selected_pages()

    def _context_insert(self, page_index, before):
        """Context menu: insert blank page"""
        self.selected_pages = {page_index}
        if before:
            self.insert_blank_page_before()
        else:
            self.insert_blank_page_after()

    # ===================================================================
    # RENDERING AND DISPLAY
    # ===================================================================

    def _reconfigure_grid(self):
        """Reconfigure thumbnail grid (replaces Canvas reconfiguration)"""
        if not self.pdf_document:
            return
        
        # Calculate layout
        scroll_width = self.scroll_area.viewport().width()
        available_width = scroll_width - 40  # Margins
        
        # Calculate columns
        thumb_width_with_padding = self.fixed_thumb_width + 2 * self.THUMB_PADDING
        num_cols = max(self.min_cols, min(self.max_cols, available_width // thumb_width_with_padding))
        column_width = self.fixed_thumb_width
        
        # Clear existing layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.thumb_frames.clear()
        self.pixmaps.clear()
        
        # Create thumbnails
        for i in range(len(self.pdf_document)):
            frame = ThumbnailFrame(
                self.scrollable_frame,
                self,
                i,
                column_width
            )
            row = i // num_cols
            col = i % num_cols
            self.scroll_layout.addWidget(frame, row, col)
            self.thumb_frames[i] = frame
        
        self.update_selection_display()
        self.update_focus_display()

    def _render_and_scale(self, page_index, column_width):
        """Render page and scale to thumbnail size"""
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        aspect_ratio = page_height / page_width if page_width != 0 else 1
        
        final_thumb_width = column_width
        final_thumb_height = int(final_thumb_width * aspect_ratio)
        if final_thumb_width <= 0: final_thumb_width = 1
        if final_thumb_height <= 0: final_thumb_height = 1
        
        mat = fitz.Matrix(self.render_dpi_factor, self.render_dpi_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to QPixmap
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        resized_image = image.resize((final_thumb_width, final_thumb_height), Image.LANCZOS)
        
        # Convert PIL Image to QPixmap
        img_byte_arr = io.BytesIO()
        resized_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        pixmap = QPixmap()
        pixmap.loadFromData(img_byte_arr)
        
        return pixmap

    def _get_page_size_label(self, page_index):
        """Get page size label"""
        if not self.pdf_document:
            return ""
        
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        width_mm = round(page_width / 72 * 25.4)
        height_mm = round(page_height / 72 * 25.4)
        
        # Check for standard formats
        if 205 <= width_mm <= 215 and 292 <= height_mm <= 302:
            return "A4"
        if 292 <= width_mm <= 302 and 205 <= height_mm <= 215:
            return "A4 (Poziom)"
        if 292 <= width_mm <= 302 and 415 <= height_mm <= 425:
            return "A3"
        
        return f"{width_mm} x {height_mm} mm"

    def update_selection_display(self):
        """Update visual display of selected pages"""
        num_selected = len(self.selected_pages)
        
        for frame_index, frame in self.thumb_frames.items():
            if frame_index in self.selected_pages:
                frame.setStyleSheet(f"background-color: {frame.bg_selected};")
            else:
                frame.setStyleSheet(f"background-color: {frame.bg_normal};")
        
        self.update_tool_button_states()
        
        # Update status message
        if self.pdf_document:
            if num_selected > 0:
                msg = f"Zaznaczono {num_selected} stron. Użyj przycisków w panelu do edycji."
                if num_selected == 1:
                    page_num = list(self.selected_pages)[0] + 1
                    msg = f"Zaznaczono 1 stronę (Strona {page_num}). Użyj przycisków w panelu do edycji."
                self._update_status(msg)
            else:
                self._update_status(f"Dokument wczytany. Liczba stron: {len(self.pdf_document)}. Zaznacz strony (LPM lub Spacja) do edycji.")
        else:
            self._update_status("Gotowy. Otwórz plik PDF.")

    def update_focus_display(self):
        """Update focus display"""
        for index, frame in self.thumb_frames.items():
            if index == self.active_page_index:
                frame.setFrameStyle(QFrame.Box | QFrame.Plain)
                frame.setLineWidth(3)
            else:
                frame.setLineWidth(2)

    # ===================================================================
    # ZOOM
    # ===================================================================

    def zoom_in(self):
        """Zoom in thumbnails"""
        self.fixed_thumb_width = int(self.fixed_thumb_width / self.ZOOM_FACTOR)
        self.fixed_thumb_width = min(self.fixed_thumb_width, 400)
        self._reconfigure_grid()

    def zoom_out(self):
        """Zoom out thumbnails"""
        self.fixed_thumb_width = int(self.fixed_thumb_width * self.ZOOM_FACTOR)
        self.fixed_thumb_width = max(self.fixed_thumb_width, self.min_zoom_width)
        self._reconfigure_grid()

    # ===================================================================
    # ABOUT DIALOG
    # ===================================================================

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = f"""
        <h2>{PROGRAM_TITLE}</h2>
        <p>Wersja: {PROGRAM_VERSION}</p>
        <p>Data: {PROGRAM_DATE}</p>
        <hr>
        <p>{COPYRIGHT_INFO}</p>
        """
        
        QMessageBox.about(self, "O programie", about_text)


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

def main():
    """Main entry point for the application"""
    import sys
    
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName(PROGRAM_TITLE)
    app.setApplicationVersion(PROGRAM_VERSION)
    
    # Set application icon if available
    icon_path = os.path.join(ICON_FOLDER, 'gryf.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = SelectablePDFViewer()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        main()
    except ImportError as e:
        print(f"BŁĄD: Wymagane biblioteki nie są zainstalowane.")
        print(f"Upewnij się, że masz zainstalowane: PySide6, PyMuPDF, Pillow, pypdf")
        print(f"Szczegóły: {e}")
        sys.exit(1)

