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


