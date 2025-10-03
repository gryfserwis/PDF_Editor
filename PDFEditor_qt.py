#!/usr/bin/env python3
"""
GRYF PDF Editor - Qt Version
Complete implementation with drag & drop support for files and pages
Based on PDFEditor.py but using PySide6 for modern UI

Uzupełniono brakujące funkcjonalności względem wersji Tkinter:
1. Import PDF z wyborem zakresu stron (EnhancedPageRangeDialog)
2. Import obrazu z dialogiem ustawień (ImageImportSettingsDialog: skala, orientacja, wyrównanie)
3. Pełna obsługa rotacji (0/90/180/270) przy dodawaniu numeracji stron (logika jak w wersji Tk)
4. Scalanie stron w siatkę – teraz dodaje nową stronę do istniejącego dokumentu (nie zastępuje całego PDF)
5. Poprawiono błąd: insert_blank_page_before/after używało self.active_page (nieistniejącego) – użyto self.active_page_index

Nie zmieniano istniejących funkcji poza dodaniem brakującej funkcjonalności i poprawą zgodności.
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
# DIALOG CLASSES (UNCHANGED EXCEPT USED NOW IN IMPORTS)
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
        # Czy wybrano tryb crop (cokolwiek poza "nie przycinaj")
        crop_selected = not self.crop_none.isChecked()
        # Czy wybrano tryb resize (cokolwiek poza "nie zmieniaj rozmiaru")
        resize_selected = not self.resize_none.isChecked()

        # Wzajemne wykluczanie sekcji
        self.resize_none.setEnabled(not crop_selected)
        self.resize_scale.setEnabled(not crop_selected)
        self.resize_noscale.setEnabled(not crop_selected)

        self.crop_none.setEnabled(not resize_selected)
        self.crop_only.setEnabled(not resize_selected)
        self.crop_resize.setEnabled(not resize_selected)

        # Pola marginesów aktywne tylko gdy crop aktywny i nie wybrano resize
        enable_margins = crop_selected and not resize_selected
        for w in (self.e_margin_top, self.e_margin_bottom, self.e_margin_left, self.e_margin_right):
            w.setEnabled(enable_margins)

        # Format i ewentualny niestandardowy rozmiar tylko przy aktywnym resize (i bez crop)
        enable_format = resize_selected and not crop_selected
        self.format_combo.setEnabled(enable_format)
        enable_custom = enable_format and self.format_combo.currentText() == "Niestandardowy"
        self.e_custom_width.setEnabled(enable_custom)
        self.e_custom_height.setEnabled(enable_custom)

        # Pozycjonowanie tylko dla trybu "resize_noscale" (bez crop)
        enable_position = self.resize_noscale.isChecked() and not crop_selected
        self.position_group.setEnabled(enable_position)

        # Offsety tylko gdy ręczne pozycjonowanie
        enable_offsets = enable_position and self.pos_custom.isChecked()
        self.e_offset_x.setEnabled(enable_offsets)
        self.e_offset_y.setEnabled(enable_offsets)
            
    def accept_dialog(self):
        try:
            if self.crop_none.isChecked():
                crop_mode = "nocrop"
                top = bottom = left = right = 0.0
            else:
                crop_mode = "crop_only" if self.crop_only.isChecked() else "crop_resize"
                top = float(self.e_margin_top.text().replace(",", "."))
                bottom = float(self.e_margin_bottom.text().replace(",", "."))
                left = float(self.e_margin_left.text().replace(",", "."))
                right = float(self.e_margin_right.text().replace(",", "."))
                if any(v < 0 for v in [top, bottom, left, right]):
                    raise ValueError("Marginesy muszą być nieujemne.")
            if self.resize_none.isChecked():
                resize_mode = "noresize"
                format_name = None
                target_dims = (None, None)
            else:
                resize_mode = "resize_scale" if self.resize_scale.isChecked() else "resize_noscale"
                format_name = self.format_combo.currentText()
                if format_name == "Niestandardowy":
                    w = float(self.e_custom_width.text().replace(",", "."))
                    h = float(self.e_custom_height.text().replace(",", "."))
                    if w <= 0 or h <= 0:
                        raise ValueError("Rozmiar niestandardowy musi być większy od zera.")
                    target_dims = (w, h)
                else:
                    target_dims = self.PAPER_FORMATS[format_name]
            enable_position = self.resize_noscale.isChecked() and self.crop_none.isChecked()
            if enable_position:
                position_mode = "custom" if self.pos_custom.isChecked() else "center"
                if position_mode == "custom":
                    offset_x = float(self.e_offset_x.text().replace(",", "."))
                    offset_y = float(self.e_offset_y.text().replace(",", "."))
                    if offset_x < 0 or offset_y < 0:
                        raise ValueError("Offset musi być nieujemny.")
                else:
                    offset_x = offset_y = 0.0
            else:
                position_mode = None
                offset_x = offset_y = None
            self.result = {
                "crop_mode": crop_mode,
                "crop_top_mm": top,
                "crop_bottom_mm": bottom,
                "crop_left_mm": left,
                "crop_right_mm": right,
                "resize_mode": resize_mode,
                "target_format": format_name,
                "target_width_mm": target_dims[0],
                "target_height_mm": target_dims[1],
                "position_mode": position_mode,
                "offset_x_mm": offset_x,
                "offset_y_mm": offset_y,
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowe dane: {e}")


class ImageImportSettingsDialog(QDialog):
    """Dialog for image import settings with scaling and alignment options (used now)"""
    
    def __init__(self, parent=None, title="Ustawienia importu obrazu", image_path=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.image_path = image_path
        self.result = None
        
        self.image_pixel_width, self.image_pixel_height = 0, 0
        self.image_dpi = 96
        
        try:
            img = Image.open(image_path)
            self.image_pixel_width, self.image_pixel_height = img.size
            dpi_info = img.info.get('dpi', (96, 96))
            self.image_dpi = dpi_info[0] if isinstance(dpi_info, tuple) else 96
            img.close()
        except Exception:
            pass
        
        self.setup_ui()
        self.update_scale_controls()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox("Informacje o obrazie źródłowym")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"Wymiary: {self.image_pixel_width} x {self.image_pixel_height} px"))
        info_layout.addWidget(QLabel(f"DPI: {self.image_dpi}"))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        orient_group = QGroupBox("Orientacja strony docelowej (A4)")
        orient_layout = QVBoxLayout()
        self.orient_portrait = QRadioButton("Pionowo")
        self.orient_landscape = QRadioButton("Poziomo")
        self.orient_portrait.setChecked(True)
        orient_layout.addWidget(self.orient_portrait)
        orient_layout.addWidget(self.orient_landscape)
        orient_group.setLayout(orient_layout)
        layout.addWidget(orient_group)
        
        scale_group = QGroupBox("Ustawienia skalowania")
        scale_layout = QVBoxLayout()
        self.scale_fit = QRadioButton("Dopasuj do strony A4")
        self.scale_original = QRadioButton("Oryginalny rozmiar (100%)")
        self.scale_custom = QRadioButton("Skala niestandardowa")
        self.scale_fit.setChecked(True)
        scale_layout.addWidget(self.scale_fit)
        scale_layout.addWidget(self.scale_original)
        scale_layout.addWidget(self.scale_custom)
        scale_input_layout = QHBoxLayout()
        scale_input_layout.addWidget(QLabel("Skala [%]:"))
        self.scale_value = QLineEdit("100.0")
        scale_input_layout.addWidget(self.scale_value)
        scale_layout.addLayout(scale_input_layout)
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        align_group = QGroupBox("Wyrównanie na stronie")
        align_layout = QVBoxLayout()
        self.align_center = QRadioButton("Środek strony")
        self.align_top = QRadioButton("Góra")
        self.align_bottom = QRadioButton("Dół")
        self.align_center.setChecked(True)
        align_layout.addWidget(self.align_center)
        align_layout.addWidget(self.align_top)
        align_layout.addWidget(self.align_bottom)
        align_group.setLayout(align_layout)
        layout.addWidget(align_group)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.scale_fit.toggled.connect(self.update_scale_controls)
        self.scale_original.toggled.connect(self.update_scale_controls)
        self.scale_custom.toggled.connect(self.update_scale_controls)
        
    def update_scale_controls(self):
        self.scale_value.setEnabled(self.scale_custom.isChecked())
        
    def accept_dialog(self):
        try:
            if self.scale_fit.isChecked():
                scaling_mode = "DOPASUJ"
                scale_factor = 1.0
            elif self.scale_original.isChecked():
                scaling_mode = "ORYGINALNY"
                scale_factor = 1.0
            else:
                scaling_mode = "SKALA"
                scale_val = float(self.scale_value.text().replace(',', '.'))
                if not (0.1 <= scale_val <= 1000):
                    raise ValueError("Skala musi być wartością liczbową od 0.1 do 1000%.")
                scale_factor = scale_val / 100.0
            
            if self.align_center.isChecked():
                alignment = "SRODEK"
            elif self.align_top.isChecked():
                alignment = "GORA"
            else:
                alignment = "DOL"
            
            orientation = "PIONOWO" if self.orient_portrait.isChecked() else "POZIOMO"
            
            self.result = {
                'scaling_mode': scaling_mode,
                'scale_factor': scale_factor,
                'alignment': alignment,
                'page_orientation': orientation,
                'image_dpi': self.image_dpi
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowe wartości: {e}")


class EnhancedPageRangeDialog(QDialog):
    """Dialog for selecting page range with parsing support (now used)"""
    
    def __init__(self, parent=None, title="Wybór zakresu stron", imported_doc=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.imported_doc = imported_doc
        self.result = None
        
        try:
            self.max_pages = len(imported_doc) if imported_doc else 0
        except:
            self.max_pages = 0
            QMessageBox.critical(self, "Błąd", "Dokument PDF został zamknięty przed otwarciem dialogu.")
            self.reject()
            return
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        range_group = QGroupBox("Zakres stron do importu")
        range_layout = QVBoxLayout()
        range_layout.addWidget(QLabel(f"Podaj strony z zakresu [1 - {self.max_pages}]:"))
        self.entry = QLineEdit(f"1-{self.max_pages}")
        range_layout.addWidget(self.entry)
        helper = QLabel("Format: 1, 3-5, 7")
        helper.setStyleSheet("color: gray;")
        range_layout.addWidget(helper)
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        button_layout = QHBoxLayout()
        import_btn = QPushButton("Importuj")
        import_btn.clicked.connect(self.accept_dialog)
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
    def accept_dialog(self):
        raw_range = self.entry.text().strip()
        if not raw_range:
            QMessageBox.critical(self, "Błąd", "Wprowadź zakres stron.")
            return
        page_indices = self._parse_range(raw_range)
        if page_indices is None:
            QMessageBox.critical(self, "Błąd formatu", "Niepoprawny format zakresu. Użyj np. 1, 3-5, 7.")
            return
        self.result = page_indices
        self.accept()
        
    def _parse_range(self, raw_range: str) -> Optional[List[int]]:
        selected_pages = set()
        if not re.fullmatch(r'[\d,\-\s]+', raw_range):
            return None
        parts = raw_range.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    start = max(1, start)
                    end = min(self.max_pages, end)
                    if start > end:
                        continue
                    for page_num in range(start, end + 1):
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
            else:
                try:
                    page_num = int(part)
                    if 1 <= page_num <= self.max_pages:
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None
        return sorted(list(selected_pages))

class MergePageGridDialog(QDialog):
    """Dialog for merging multiple pages into a grid on a single sheet with live preview"""

    PAPER_FORMATS = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
    }

    def __init__(self, parent=None, page_count=1):
        super().__init__(parent)
        self.setWindowTitle("Scalanie strony na arkuszu")
        self.setMinimumSize(700, 520)
        self.result = None
        self.page_count = page_count

        self.sheet_format_val = "A4"
        self.orientation_val = "Pionowa"
        self.margin_top_val = "4"
        self.margin_bottom_val = "4"
        self.margin_left_val = "5"
        self.margin_right_val = "5"
        self.spacing_x_val = "10"
        self.spacing_y_val = "10"

        if page_count == 1:
            self.rows_val = 1
            self.cols_val = 1
        else:
            sq = math.ceil(page_count ** 0.5)
            if (sq - 1) * sq >= page_count:
                self.rows_val = sq - 1
                self.cols_val = sq
            else:
                self.rows_val = sq
                self.cols_val = sq

        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Arkusz docelowy
        format_group = QGroupBox("Arkusz docelowy")
        format_layout = QGridLayout()
        format_layout.addWidget(QLabel("Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(list(self.PAPER_FORMATS.keys()))
        self.format_combo.setCurrentText(self.sheet_format_val)
        self.format_combo.currentTextChanged.connect(self.update_preview)
        format_layout.addWidget(self.format_combo, 0, 1)
        format_layout.addWidget(QLabel("Orientacja:"), 1, 0)
        orient_widget = QWidget()
        orient_layout = QHBoxLayout(orient_widget)
        orient_layout.setContentsMargins(0, 0, 0, 0)
        self.orient_portrait = QRadioButton("Pionowa")
        self.orient_landscape = QRadioButton("Pozioma")
        self.orient_portrait.setChecked(True)
        self.orient_portrait.toggled.connect(self.update_preview)
        orient_layout.addWidget(self.orient_portrait)
        orient_layout.addWidget(self.orient_landscape)
        format_layout.addWidget(orient_widget, 1, 1)
        format_group.setLayout(format_layout)
        left_layout.addWidget(format_group)

        # Marginesy
        margin_group = QGroupBox("Marginesy [mm]")
        margin_layout = QGridLayout()
        margin_layout.addWidget(QLabel("Górny:"), 0, 0)
        self.margin_top = QLineEdit(self.margin_top_val)
        self.margin_top.textChanged.connect(self.update_preview)
        margin_layout.addWidget(self.margin_top, 0, 1)
        margin_layout.addWidget(QLabel("Dolny:"), 0, 2)
        self.margin_bottom = QLineEdit(self.margin_bottom_val)
        self.margin_bottom.textChanged.connect(self.update_preview)
        margin_layout.addWidget(self.margin_bottom, 0, 3)
        margin_layout.addWidget(QLabel("Lewy:"), 1, 0)
        self.margin_left = QLineEdit(self.margin_left_val)
        self.margin_left.textChanged.connect(self.update_preview)
        margin_layout.addWidget(self.margin_left, 1, 1)
        margin_layout.addWidget(QLabel("Prawy:"), 1, 2)
        self.margin_right = QLineEdit(self.margin_right_val)
        self.margin_right.textChanged.connect(self.update_preview)
        margin_layout.addWidget(self.margin_right, 1, 3)
        margin_group.setLayout(margin_layout)
        left_layout.addWidget(margin_group)

        # Odstępy
        spacing_group = QGroupBox("Odstępy [mm]")
        spacing_layout = QGridLayout()
        spacing_layout.addWidget(QLabel("Między kolumnami:"), 0, 0)
        self.spacing_x = QLineEdit(self.spacing_x_val)
        self.spacing_x.textChanged.connect(self.update_preview)
        spacing_layout.addWidget(self.spacing_x, 0, 1)
        spacing_layout.addWidget(QLabel("Między wierszami:"), 1, 0)
        self.spacing_y = QLineEdit(self.spacing_y_val)
        self.spacing_y.textChanged.connect(self.update_preview)
        spacing_layout.addWidget(self.spacing_y, 1, 1)
        spacing_group.setLayout(spacing_layout)
        left_layout.addWidget(spacing_group)

        # Siatka stron
        grid_group = QGroupBox("Siatka stron")
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Wiersze:"), 0, 0)
        self.rows_spin = QSpinBox()
        self.rows_spin.setMinimum(1)
        self.rows_spin.setMaximum(10)
        self.rows_spin.setValue(self.rows_val)
        self.rows_spin.valueChanged.connect(self.update_preview)
        grid_layout.addWidget(self.rows_spin, 0, 1)
        grid_layout.addWidget(QLabel("Kolumny:"), 0, 2)
        self.cols_spin = QSpinBox()
        self.cols_spin.setMinimum(1)
        self.cols_spin.setMaximum(10)
        self.cols_spin.setValue(self.cols_val)
        self.cols_spin.valueChanged.connect(self.update_preview)
        grid_layout.addWidget(self.cols_spin, 0, 3)
        grid_group.setLayout(grid_layout)
        left_layout.addWidget(grid_group)

        left_layout.addStretch()
        main_layout.addWidget(left_widget)

        # Podgląd
        preview_group = QGroupBox("Podgląd rozkładu stron")
        preview_layout = QVBoxLayout()
        self.preview_scene = QGraphicsScene()
        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setMinimumSize(320, 450)
        self.preview_view.setMaximumSize(320, 450)
        preview_layout.addWidget(self.preview_view)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # Główny layout dialogu
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addLayout(main_layout)

        # Przyciski OK/Anuluj
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_dialog)
        button_box.rejected.connect(self.reject)
        dialog_layout.addWidget(button_box)

    def get_sheet_dimensions(self):
        sf = self.format_combo.currentText()
        sheet_w, sheet_h = self.PAPER_FORMATS.get(sf, (210, 297))
        if self.orient_landscape.isChecked():
            return sheet_h, sheet_w
        return sheet_w, sheet_h

    def update_preview(self):
        try:
            self.preview_scene.clear()
            margin_top = float(self.margin_top.text().replace(",", "."))
            margin_bottom = float(self.margin_bottom.text().replace(",", "."))
            margin_left = float(self.margin_left.text().replace(",", "."))
            margin_right = float(self.margin_right.text().replace(",", "."))
            spacing_x = float(self.spacing_x.text().replace(",", "."))
            spacing_y = float(self.spacing_y.text().replace(",", "."))
            rows = self.rows_spin.value()
            cols = self.cols_spin.value()
            sheet_w, sheet_h = self.get_sheet_dimensions()
            PREVIEW_W = 320
            PREVIEW_H = 450
            PREVIEW_PAD = 20
            preview_area_w = PREVIEW_W - 2 * PREVIEW_PAD
            preview_area_h = PREVIEW_H - 2 * PREVIEW_PAD
            scale = min(preview_area_w / sheet_w, preview_area_h / sheet_h)
            width_px = sheet_w * scale
            height_px = sheet_h * scale
            offset_x = (PREVIEW_W - width_px) / 2
            offset_y = (PREVIEW_H - height_px) / 2
            sheet_rect = QGraphicsRectItem(offset_x, offset_y, width_px, height_px)
            sheet_rect.setBrush(QBrush(QColor("white")))
            sheet_rect.setPen(QPen(QColor("#bbb"), 1))
            self.preview_scene.addItem(sheet_rect)
            if cols == 1:
                cell_w = sheet_w - margin_left - margin_right
            else:
                cell_w = (sheet_w - margin_left - margin_right - (cols - 1) * spacing_x) / cols
            if rows == 1:
                cell_h = sheet_h - margin_top - margin_bottom
            else:
                cell_h = (sheet_h - margin_top - margin_bottom - (rows - 1) * spacing_y) / rows
            cell_w_px = cell_w * scale
            cell_h_px = cell_h * scale
            margin_left_px = margin_left * scale
            margin_top_px = margin_top * scale
            spacing_x_px = spacing_x * scale
            spacing_y_px = spacing_y * scale
            num_pages = self.page_count
            for r in range(rows):
                for c in range(cols):
                    x0 = offset_x + margin_left_px + c * (cell_w_px + spacing_x_px)
                    y0 = offset_y + margin_top_px + r * (cell_h_px + spacing_y_px)
                    idx = r * cols + c
                    color = QColor("#d0e6f8") if idx < num_pages else QColor("#f5f5f5")
                    cell_rect = QGraphicsRectItem(x0, y0, cell_w_px, cell_h_px)
                    cell_rect.setBrush(QBrush(color))
                    cell_rect.setPen(QPen(QColor("#666"), 1))
                    self.preview_scene.addItem(cell_rect)
                    if idx < num_pages:
                        text_item = QGraphicsTextItem(str(idx + 1))
                        text_item.setDefaultTextColor(QColor("#345"))
                        font = QFont("Arial", 11, QFont.Bold)
                        text_item.setFont(font)
                        text_rect = text_item.boundingRect()
                        text_x = x0 + (cell_w_px - text_rect.width()) / 2
                        text_y = y0 + (cell_h_px - text_rect.height()) / 2
                        text_item.setPos(text_x, text_y)
                        self.preview_scene.addItem(text_item)
            self.preview_scene.setSceneRect(0, 0, PREVIEW_W, PREVIEW_H)
        except:
            pass

    def accept_dialog(self):
        try:
            margin_top = float(self.margin_top.text().replace(",", "."))
            margin_bottom = float(self.margin_bottom.text().replace(",", "."))
            margin_left = float(self.margin_left.text().replace(",", "."))
            margin_right = float(self.margin_right.text().replace(",", "."))
            spacing_x = float(self.spacing_x.text().replace(",", "."))
            spacing_y = float(self.spacing_y.text().replace(",", "."))
            if any(m < 0 for m in [margin_top, margin_bottom, margin_left, margin_right]):
                raise ValueError("Marginesy muszą być nieujemne.")
            if spacing_x < 0 or spacing_y < 0:
                raise ValueError("Odstępy muszą być nieujemne.")
            rows = self.rows_spin.value()
            cols = self.cols_spin.value()
            if rows < 1 or cols < 1:
                raise ValueError("Liczba wierszy i kolumn musi być dodatnia.")
            format_name = self.format_combo.currentText()
            sheet_dims = self.PAPER_FORMATS[format_name]
            orientation = "Pozioma" if self.orient_landscape.isChecked() else "Pionowa"
            if orientation == "Pozioma":
                sheet_dims = (sheet_dims[1], sheet_dims[0])
            self.result = {
                "format_name": format_name,
                "sheet_width_mm": sheet_dims[0],
                "sheet_height_mm": sheet_dims[1],
                "margin_top_mm": margin_top,
                "margin_bottom_mm": margin_bottom,
                "margin_left_mm": margin_left,
                "margin_right_mm": margin_right,
                "spacing_x_mm": spacing_x,
                "spacing_y_mm": spacing_y,
                "rows": rows,
                "cols": cols,
                "orientation": orientation
            }
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nieprawidłowe dane: {e}")


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


# ====================================================================
# TOOLTIP HELPER
# ====================================================================

def set_tooltip(widget, text):
    widget.setToolTip(text)


# ====================================================================
# THUMBNAIL WIDGET WITH DRAG & DROP SUPPORT
# ====================================================================

class ThumbnailWidget(QFrame):
    """Widget representing a single PDF page thumbnail with drag & drop support"""
    clicked = Signal(int, Qt.MouseButton, Qt.KeyboardModifiers)
    drag_started = Signal(int)

    def __init__(self, page_index, pixmap, page_label, thumb_width=320, thumb_height=410, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.is_selected = False
        self.is_focused = False
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)
        self.setFixedSize(self.thumb_width, self.thumb_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = QLabel()
        self.set_thumb(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.image_label, stretch=1)

        self.page_label = QLabel(f"Strona {page_index + 1}")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("font-size: 11px; color: #434343; background: transparent; border: none;")
        layout.addWidget(self.page_label)

        self.format_label = QLabel(page_label)
        self.format_label.setAlignment(Qt.AlignCenter)
        self.format_label.setStyleSheet("font-size: 10px; color: #888888; background: transparent; border: none;")
        layout.addWidget(self.format_label)

        self.set_selected(False)

    def set_thumb(self, pixmap):
        pixmap = pixmap.scaled(self.thumb_width - 20, self.thumb_height - 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pixmap)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if self.is_selected:
            # Ramka i tło w tym samym kolorze
            self.setStyleSheet(
                "background: #b3c6e0;"
                "border: 3px solid #b3c6e0;"
                "border-radius: 7px;"
            )
        else:
            self.setStyleSheet(
                "background: transparent;"
                "border: none;"
            )

    def set_focused(self, focused: bool):
        # Możesz dodać własny styl pod aktywną miniaturę
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        self.clicked.emit(self.page_index, event.button(), event.modifiers())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
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
        self.drag_copy_mode = False
        
    def startDrag(self, supportedActions):
        selected_items = self.selectedItems()
        if not selected_items:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        indices = [self.row(item) for item in selected_items]
        mime_data.setText(','.join(map(str, indices)))
        drag.setMimeData(mime_data)
        first_item = selected_items[0]
        if first_item.icon():
            pixmap = first_item.icon().pixmap(100, 100)
            if len(selected_items) > 1:
                painter = QPainter(pixmap)
                painter.drawText(pixmap.rect(), Qt.AlignBottom | Qt.AlignRight,
                                 f"+{len(selected_items)-1}")
                painter.end()
            drag.setPixmap(pixmap)
        self.drag_copy_mode = QApplication.keyboardModifiers() & Qt.ControlModifier
        if self.drag_copy_mode:
            drag.exec_(Qt.CopyAction)
        else:
            drag.exec_(Qt.MoveAction)
            
    def dropEvent(self, event):
        source_indices_str = event.mimeData().text()
        if not source_indices_str:
            return
        try:
            source_indices = [int(x) for x in source_indices_str.split(',')]
        except ValueError:
            return
        target_item = self.itemAt(event.pos())
        if target_item:
            target_index = self.row(target_item)
        else:
            target_index = self.count()
        is_copy = event.dropAction() == Qt.CopyAction or (event.modifiers() & Qt.ControlModifier)
        self.pages_dropped.emit(source_indices, target_index, is_copy)
        event.accept()
        
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            menu.addAction("Kopiuj tutaj")
            menu.addAction("Przenieś tutaj")
            menu.addSeparator()
            menu.addAction("Anuluj")
            menu.exec_(self.mapToGlobal(event.pos()))
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
        self.undo_stack = []
        self.redo_stack = []
        self.max_stack_size = 50
        self.thumb_width = 250
        self.zoom_level = 4  # number of columns
        self.min_zoom = 2
        self.max_zoom = 10
        self.thumb_widgets = {}
        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.update_buttons_state()
        
    def setup_ui(self):
        self.setWindowTitle(PROGRAM_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        self.setAcceptDrops(True)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setup_toolbar()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.thumbnail_list = ThumbnailListWidget()
      
        self.thumbnail_list.pages_dropped.connect(self.handle_page_drop)
        self.scroll_area.setWidget(self.thumbnail_list)
        main_layout.addWidget(self.scroll_area)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Gotowy. Otwórz plik PDF.")
        
    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        self.action_open = QAction("📂 Otwórz", self)
        self.action_open.setToolTip("Otwórz plik PDF")
        self.action_open.triggered.connect(self.open_pdf)
        toolbar.addAction(self.action_open)
        self.action_save = QAction("💾 Zapisz", self)
        self.action_save.setToolTip("Zapisz całość do nowego pliku PDF")
        self.action_save.triggered.connect(self.save_document)
        self.action_save.setEnabled(False)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        self.action_import_pdf = QAction("📥 Import PDF", self)
        self.action_import_pdf.setToolTip("Importuj strony z pliku PDF.\nStrony zostaną wstawione po bieżącej, a przy braku zaznaczenia - na końcu pliku.\n(Obsługa zakresu stron)")
        self.action_import_pdf.triggered.connect(self.import_pdf)
        self.action_import_pdf.setEnabled(False)
        toolbar.addAction(self.action_import_pdf)
        self.action_export_pdf = QAction("📤 Export PDF", self)
        self.action_export_pdf.setToolTip("Eksportuj strony do pliku PDF.\nWymaga zaznaczenia przynajmniej jednej strony.")
        self.action_export_pdf.triggered.connect(self.extract_selected_pages)
        self.action_export_pdf.setEnabled(False)
        toolbar.addAction(self.action_export_pdf)
        self.action_import_image = QAction("🖼️ Import Obraz", self)
        self.action_import_image.setToolTip("Importuj obraz jako stronę (z ustawieniami).")
        self.action_import_image.triggered.connect(self.import_image)
        self.action_import_image.setEnabled(False)
        toolbar.addAction(self.action_import_image)
        self.action_export_image = QAction("🖼️ Export Obraz", self)
        self.action_export_image.setToolTip("Eksportuj strony do plików PNG.\nWymaga zaznaczenia przynajmniej jednej strony.")
        self.action_export_image.triggered.connect(self.export_images)
        self.action_export_image.setEnabled(False)
        toolbar.addAction(self.action_export_image)
        toolbar.addSeparator()
        self.action_undo = QAction("↩️ Cofnij", self)
        self.action_undo.setToolTip("Cofnij ostatnią operację")
        self.action_undo.triggered.connect(self.undo)
        self.action_undo.setEnabled(False)
        toolbar.addAction(self.action_undo)
        self.action_redo = QAction("↪️ Ponów", self)
        self.action_redo.setToolTip("Ponów cofniętą operację")
        self.action_redo.triggered.connect(self.redo)
        self.action_redo.setEnabled(False)
        toolbar.addAction(self.action_redo)
        toolbar.addSeparator()
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
        self.action_rotate_left = QAction("↺ Obróć w lewo", self)
        self.action_rotate_left.triggered.connect(lambda: self.rotate_pages(-90))
        self.action_rotate_left.setEnabled(False)
        toolbar.addAction(self.action_rotate_left)
        self.action_rotate_right = QAction("↻ Obróć w prawo", self)
        self.action_rotate_right.triggered.connect(lambda: self.rotate_pages(90))
        self.action_rotate_right.setEnabled(False)
        toolbar.addAction(self.action_rotate_right)
        toolbar.addSeparator()
        self.action_shift_content = QAction("↔️ Przesuń", self)
        self.action_shift_content.setToolTip("Przesuń zawartość zaznaczonych stron")
        self.action_shift_content.triggered.connect(self.shift_page_content)
        self.action_shift_content.setEnabled(False)
        toolbar.addAction(self.action_shift_content)
        self.action_remove_numbers = QAction("#️⃣❌ Usuń numery", self)
        self.action_remove_numbers.setToolTip("Usuń numerację ze zaznaczonych stron")
        self.action_remove_numbers.triggered.connect(self.remove_page_numbers)
        self.action_remove_numbers.setEnabled(False)
        toolbar.addAction(self.action_remove_numbers)
        self.action_add_numbers = QAction("#️⃣➕ Dodaj numery", self)
        self.action_add_numbers.setToolTip("Wstaw numerację na zaznaczonych stronach")
        self.action_add_numbers.triggered.connect(self.insert_page_numbers)
        self.action_add_numbers.setEnabled(False)
        toolbar.addAction(self.action_add_numbers)
        toolbar.addSeparator()
        self.action_zoom_in = QAction("➕ Zoom In", self)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_in.setEnabled(False)
        toolbar.addAction(self.action_zoom_in)
        self.action_zoom_out = QAction("➖ Zoom Out", self)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_zoom_out.setEnabled(False)
        toolbar.addAction(self.action_zoom_out)
        
    def setup_menus(self):
        menubar = self.menuBar()
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
        select_menu.addSeparator()
        select_portrait_action = QAction("Strony pionowe", self)
        select_portrait_action.triggered.connect(self.select_portrait_pages)
        select_portrait_action.setShortcut(QKeySequence("Ctrl+F1"))
        select_menu.addAction(select_portrait_action)
        self.action_select_portrait = select_portrait_action
        select_landscape_action = QAction("Strony poziome", self)
        select_landscape_action.triggered.connect(self.select_landscape_pages)
        select_landscape_action.setShortcut(QKeySequence("Ctrl+F2"))
        select_menu.addAction(select_landscape_action)
        self.action_select_landscape = select_landscape_action
        mod_menu = menubar.addMenu("Modyfikacje")
        mod_menu.addAction(self.action_rotate_left)
        mod_menu.addAction(self.action_rotate_right)
        mod_menu.addSeparator()
        mod_menu.addAction(self.action_shift_content)
        mod_menu.addAction(self.action_remove_numbers)
        mod_menu.addAction(self.action_add_numbers)
        mod_menu.addSeparator()
        crop_resize_action = QAction("Przytnij/Zmień rozmiar", self)
        crop_resize_action.triggered.connect(self.apply_page_crop_resize_dialog)
        crop_resize_action.setShortcut(QKeySequence("F8"))
        crop_resize_action.setEnabled(False)
        self.action_crop_resize = crop_resize_action
        mod_menu.addAction(crop_resize_action)
        merge_grid_action = QAction("Scalaj strony w siatkę", self)
        merge_grid_action.triggered.connect(self.merge_pages_to_grid)
        merge_grid_action.setEnabled(False)
        self.action_merge_grid = merge_grid_action
        mod_menu.addAction(merge_grid_action)
        mod_menu.addSeparator()
        insert_before_action = QAction("Wstaw pustą stronę przed", self)
        insert_before_action.triggered.connect(self.insert_blank_page_before)
        insert_before_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        insert_before_action.setEnabled(False)
        self.action_insert_before = insert_before_action
        mod_menu.addAction(insert_before_action)
        insert_after_action = QAction("Wstaw pustą stronę po", self)
        insert_after_action.triggered.connect(self.insert_blank_page_after)
        insert_after_action.setShortcut(QKeySequence("Ctrl+N"))
        insert_after_action.setEnabled(False)
        self.action_insert_after = insert_after_action
        mod_menu.addAction(insert_after_action)
        mod_menu.addSeparator()
        reverse_action = QAction("Odwróć kolejność stron", self)
        reverse_action.triggered.connect(self.reverse_pages)
        reverse_action.setEnabled(False)
        self.action_reverse = reverse_action
        mod_menu.addAction(reverse_action)
        help_menu = menubar.addMenu("Pomoc")
        shortcuts_action = QAction("Skróty klawiszowe", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_shortcuts(self):
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_redo.setShortcut(QKeySequence.Redo)
        self.action_cut.setShortcut(QKeySequence.Cut)
        self.action_copy.setShortcut(QKeySequence.Copy)
        self.action_paste_after.setShortcut(QKeySequence.Paste)
        self.action_delete.setShortcut(QKeySequence(Qt.Key_Delete))
        self.action_import_pdf.setShortcut(QKeySequence("Ctrl+I"))
        self.action_export_pdf.setShortcut(QKeySequence("Ctrl+E"))
        self.action_import_image.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.action_export_image.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.action_paste_before.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.action_rotate_left.setShortcut(QKeySequence("Ctrl+Shift+-"))
        self.action_rotate_right.setShortcut(QKeySequence("Ctrl+Shift++"))
        self.action_shift_content.setShortcut(QKeySequence("F5"))
        self.action_remove_numbers.setShortcut(QKeySequence("F6"))
        self.action_add_numbers.setShortcut(QKeySequence("F7"))
        select_all_f4 = QAction(self)
        select_all_f4.setShortcut(QKeySequence("F4"))
        select_all_f4.triggered.connect(self.select_all)
        self.addAction(select_all_f4)
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        if hasattr(self, 'action_duplicate'):
            self.action_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        
    # ================================================================
    # DRAG & DROP HANDLERS FOR FILES
    # ================================================================
    
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            elif event.angleDelta().y() < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            return
        urls = event.mimeData().urls()
        if not urls:
            return
        filepath = urls[0].toLocalFile()
        if not filepath:
            return
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            if self.pdf_document is None:
                self.open_pdf(filepath=filepath)
            else:
                self.import_pdf(filepath=filepath, from_drop=True)
        elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
            if self.pdf_document:
                self.import_image(filepath=filepath, from_drop=True)
            else:
                QMessageBox.information(self, "Info", "Najpierw otwórz dokument PDF, aby zaimportować obraz.")
        else:
            QMessageBox.warning(self, "Nieprawidłowy plik", f"Nieobsługiwany typ pliku: {ext}")
        event.acceptProposedAction()
        
    def handle_page_drop(self, source_indices, target_index, is_copy):
        if not self.pdf_document:
            return
        try:
            self._save_state_to_undo()
            pages_data = []
            for idx in sorted(source_indices):
                if 0 <= idx < len(self.pdf_document):
                    pages_data.append(idx)
            if not pages_data:
                return
            if is_copy:
                temp_doc = fitz.open()
                for idx in pages_data:
                    temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
                self.pdf_document.insert_pdf(temp_doc, start_at=target_index)
                temp_doc.close()
                self.update_status(f"Skopiowano {len(pages_data)} stron do pozycji {target_index}")
            else:
                temp_doc = fitz.open()
                for idx in pages_data:
                    temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
                for idx in reversed(sorted(pages_data)):
                    self.pdf_document.delete_page(idx)
                adjusted_target = target_index
                for idx in pages_data:
                    if idx < target_index:
                        adjusted_target -= 1
                self.pdf_document.insert_pdf(temp_doc, start_at=adjusted_target)
                temp_doc.close()
                self.update_status(f"Przeniesiono {len(pages_data)} stron do pozycji {adjusted_target}")
            self.refresh_thumbnails()
            self.update_buttons_state()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się przenieść/skopiować stron: {e}")
            
    # ================================================================
    # FILE OPERATIONS
    # ================================================================
    
    def open_pdf(self, filepath=None):
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
                if len(self.undo_stack) > 0:
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
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_buttons_state()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać pliku: {e}")
            
    def import_pdf(self, filepath=None, from_drop=False):
        """Import PDF pages with range selection (added parity)."""
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
            # Determine insert position (same logic)
            if len(self.selected_pages) == 1:
                insert_index = list(self.selected_pages)[0] + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
            # Range dialog (skip if drag&drop import wants full doc? keep full on drop)
            if from_drop:
                selected_indices = list(range(len(imported_doc)))
            else:
                dlg = EnhancedPageRangeDialog(self, "Zakres stron do importu", imported_doc)
                if dlg.result is None or len(dlg.result) == 0:
                    imported_doc.close()
                    self.update_status("Anulowano import (brak wybranego zakresu).")
                    return
                selected_indices = dlg.result
            self._save_state_to_undo()
            temp_doc = fitz.open()
            for idx in selected_indices:
                temp_doc.insert_pdf(imported_doc, from_page=idx, to_page=idx)
            self.pdf_document.insert_pdf(temp_doc, start_at=insert_index)
            num_imported = len(selected_indices)
            imported_doc.close()
            temp_doc.close()
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Zaimportowano {num_imported} stron w pozycji {insert_index}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować PDF: {e}")
            
    def import_image(self, filepath=None, from_drop=False):
        """Import image as new PDF page using settings dialog (added parity)."""
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
        # Show settings dialog (skip only if from_drop -> use defaults)
        if from_drop:
            # Basic default settings: FIT, CENTER, PORTRAIT
            settings = {
                'scaling_mode': "DOPASUJ",
                'scale_factor': 1.0,
                'alignment': "SRODEK",
                'page_orientation': "PIONOWO",
                'image_dpi': 96
            }
            try:
                img = Image.open(filepath)
                dpi_info = img.info.get('dpi', (96, 96))
                settings['image_dpi'] = dpi_info[0] if isinstance(dpi_info, tuple) else 96
                img.close()
            except:
                pass
        else:
            dlg = ImageImportSettingsDialog(self, "Ustawienia importu obrazu", filepath)
            if dlg.result is None:
                self.update_status("Anulowano import obrazu.")
                return
            settings = dlg.result
        try:
            img = Image.open(filepath)
            img_width, img_height = img.size
            img_dpi = settings.get('image_dpi', 96)
            img_width_pt = (img_width / img_dpi) * 72
            img_height_pt = (img_height / img_dpi) * 72
            img.close()
            if settings['page_orientation'] == "PIONOWO":
                page_w, page_h = A4_WIDTH_POINTS, A4_HEIGHT_POINTS
            else:
                page_w, page_h = A4_HEIGHT_POINTS, A4_WIDTH_POINTS
            scaling_mode = settings['scaling_mode']
            if scaling_mode == "DOPASUJ":
                margin = 50 * MM_TO_POINTS
                scale_w = (page_w - margin) / img_width_pt
                scale_h = (page_h - margin) / img_height_pt
                scale = min(scale_w, scale_h)
            elif scaling_mode == "ORYGINALNY":
                scale = 1.0
            else:  # SKALA
                scale = settings['scale_factor']
            final_w = img_width_pt * scale
            final_h = img_height_pt * scale
            offset_points = 25 * MM_TO_POINTS
            alignment = settings['alignment']
            if alignment == "SRODEK":
                x = (page_w - final_w) / 2
                y = (page_h - final_h) / 2
            elif alignment == "GORA":
                x = (page_w - final_w) / 2
                y = offset_points
            else:  # DOL
                x = (page_w - final_w) / 2
                y = page_h - final_h - offset_points
            rect = fitz.Rect(x, y, x + final_w, y + final_h)
            if len(self.selected_pages) == 1:
                insert_index = list(self.selected_pages)[0] + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
            self._save_state_to_undo()
            temp_doc = fitz.open()
            temp_page = temp_doc.new_page(-1, width=page_w, height=page_h)
            temp_page.insert_image(rect, filename=filepath)
            self.pdf_document.insert_pdf(temp_doc, from_page=0, to_page=0, start_at=insert_index)
            temp_doc.close()
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Zaimportowano obraz jako stronę {insert_index + 1}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować obrazu: {e}")
            
    def extract_selected_pages(self):
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
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do usunięcia.")
            return
        try:
            self._save_state_to_undo()
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
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Zaznacz strony do wycięcia.")
            return
        try:
            temp_doc = fitz.open()
            for idx in sorted(self.selected_pages):
                temp_doc.insert_pdf(self.pdf_document, from_page=idx, to_page=idx)
            self.clipboard = temp_doc.write()
            self.pages_in_clipboard_count = len(temp_doc)
            temp_doc.close()
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
        self._handle_paste(before=True)
        
    def paste_after(self):
        self._handle_paste(before=False)
        
    def _handle_paste(self, before):
        if not self.pdf_document or not self.clipboard:
            self.update_status("Schowek jest pusty.")
            return
        
        # If multiple pages selected, ask for confirmation
        if len(self.selected_pages) > 1:
            num_copies = len(self.selected_pages)
            reply = QMessageBox.question(
                self, "Potwierdzenie wklejania",
                f"Czy na pewno chcesz wkleić {num_copies} kopii stron?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.update_status("Wklejanie anulowane.")
                return
            
            # Sort selected pages to insert in correct order
            sorted_pages = sorted(list(self.selected_pages))
            
            try:
                self._save_state_to_undo()
                temp_doc = fitz.open("pdf", self.clipboard)
                # Insert after each selected page (in reverse order to maintain indices)
                for page_idx in reversed(sorted_pages):
                    if before:
                        insert_pos = page_idx
                    else:
                        insert_pos = page_idx + 1
                    self.pdf_document.insert_pdf(temp_doc, start_at=insert_pos)
                temp_doc.close()
                
                # Don't clear clipboard
                self.selected_pages.clear()
                self.refresh_thumbnails()
                self.update_buttons_state()
                self.update_status(f"Wklejono {num_copies} kopii stron.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się wkleić stron: {e}")
            return
        
        # Single page or no selection
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
            # Don't clear clipboard - keep it for future pastes
            # self.clipboard = None
            # self.pages_in_clipboard_count = 0
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_buttons_state()
            self.update_status(f"Wklejono {num_inserted} stron w pozycji {insert_index}.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wkleić stron: {e}")
            
    def duplicate_page(self):
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
        if self.pdf_document:
            buffer = self.pdf_document.write()
            self.undo_stack.append(buffer)
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.update_buttons_state()
            
    def undo(self):
        if not self.undo_stack:
            self.update_status("Brak operacji do cofnięcia.")
            return
        try:
            if self.pdf_document:
                current_state = self.pdf_document.write()
                self.redo_stack.append(current_state)
                if len(self.redo_stack) > self.max_stack_size:
                    self.redo_stack.pop(0)
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
        if not self.redo_stack:
            self.update_status("Brak operacji do ponowienia.")
            return
        try:
            if self.pdf_document:
                current_state = self.pdf_document.write()
                self.undo_stack.append(current_state)
                if len(self.undo_stack) > self.max_stack_size:
                    self.undo_stack.pop(0)
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
            dx_pt = result['x_mm'] * self.MM_TO_POINTS
            dy_pt = result['y_mm'] * self.MM_TO_POINTS
            x_sign = -1 if result['x_dir'] == 'L' else 1
            y_sign = -1 if result['y_dir'] == 'D' else 1
            final_dx = dx_pt * x_sign
            final_dy = dy_pt * y_sign
            self._save_state_to_undo()
            pdf_bytes = self.pdf_document.write()
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            transform = Transformation().translate(tx=final_dx, ty=final_dy)
            for i, page in enumerate(pdf_reader.pages):
                if i in self.selected_pages:
                    page.add_transformation(transform)
                pdf_writer.add_page(page)
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
                if format_mode == 'full':
                    text = f"Strona {current_number} z {total_counted_pages}"
                else:
                    text = str(current_number)
                text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)
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
                is_physical_odd = (i + 1) % 2 == 1
                if mirror_margins:
                    if is_physical_odd:
                        left_pt, right_pt = left_pt_base, right_pt_base
                    else:
                        left_pt, right_pt = right_pt_base, left_pt_base
                else:
                    left_pt, right_pt = left_pt_base, right_pt_base
                # FULL ROTATION HANDLING (taken from Tk logic)
                if rotation == 0:
                    if align == "lewa":
                        x = rect.x0 + left_pt
                    elif align == "prawa":
                        x = rect.x1 - right_pt - text_width
                    else:
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                    y = rect.y0 + margin_v + font_size if position == "gora" else rect.y1 - margin_v
                    angle = 0
                elif rotation == 90:
                    if align == "lewa":
                        y = rect.y0 + left_pt
                    elif align == "prawa":
                        y = rect.y1 - right_pt - text_width
                    else:
                        total_height = rect.height
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                    x = rect.x0 + margin_v + font_size if position == "gora" else rect.x1 - margin_v
                    angle = 90
                elif rotation == 180:
                    if align == "lewa":
                        x = rect.x1 - right_pt - text_width
                    elif align == "prawa":
                        x = rect.x0 + left_pt
                    else:
                        total_width = rect.width
                        margin_diff = left_pt - right_pt
                        x = rect.x0 + (total_width / 2) - (text_width / 2) + (margin_diff / 2)
                    y = rect.y1 - margin_v - font_size if position == "gora" else rect.y0 + margin_v
                    angle = 180
                elif rotation == 270:
                    if align == "lewa":
                        y = rect.y1 - right_pt - text_width
                    elif align == "prawa":
                        y = rect.y0 + left_pt
                    else:
                        total_height = rect.height
                        margin_diff = left_pt - right_pt
                        y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
                    x = rect.x1 - margin_v - font_size if position == "gora" else rect.x0 + margin_v
                    angle = 270
                else:
                    x = rect.x0 + left_pt
                    y = rect.y1 - margin_v
                    angle = 0
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
        if not self.pdf_document:
            return
        all_pages = set(range(len(self.pdf_document)))
        if self.selected_pages == all_pages:
            self.selected_pages.clear()
            self.update_status("Anulowano zaznaczenie wszystkich stron.")
        else:
            self.selected_pages = all_pages
            self.update_status(f"Zaznaczono wszystkie strony ({len(self.pdf_document)}).")
        self.update_selection_display()
        self.update_buttons_state()
        
    def select_odd_pages(self):
        if not self.pdf_document:
            return
        indices = [i for i in range(len(self.pdf_document)) if i % 2 == 0]
        self.selected_pages = set(indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(indices)} stron nieparzystych.")
        
    def select_even_pages(self):
        if not self.pdf_document:
            return
        indices = [i for i in range(len(self.pdf_document)) if i % 2 != 0]
        self.selected_pages = set(indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(indices)} stron parzystych.")
        
    def select_portrait_pages(self):
        if not self.pdf_document:
            return
        portrait_indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document[i]
            rect = page.rect
            if rect.height >= rect.width:
                portrait_indices.append(i)
        self.selected_pages = set(portrait_indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(portrait_indices)} stron pionowych.")
    
    def select_landscape_pages(self):
        if not self.pdf_document:
            return
        landscape_indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document[i]
            rect = page.rect
            if rect.width > rect.height:
                landscape_indices.append(i)
        self.selected_pages = set(landscape_indices)
        self.update_selection_display()
        self.update_buttons_state()
        self.update_status(f"Zaznaczono {len(landscape_indices)} stron poziomych.")
        
    # ================================================================
    # VIEW OPERATIONS
    # ================================================================
    
    def zoom_in(self):
        if self.pdf_document and self.zoom_level > self.min_zoom:
            self.zoom_level -= 1
            self.refresh_thumbnails()
            self.update_buttons_state()
            
    def zoom_out(self):
        if self.pdf_document and self.zoom_level < self.max_zoom:
            self.zoom_level += 1
            self.refresh_thumbnails()
            self.update_buttons_state()
            
    def refresh_thumbnails(self):
        if not self.pdf_document:
            self.thumbnail_list.clear()
            self.thumb_widgets.clear()
            return
        self.thumbnail_list.clear()
        self.thumb_widgets.clear()
        base_width = 200
        thumb_width = int(base_width * (self.max_zoom - self.zoom_level + self.min_zoom) / self.max_zoom)
        for i in range(len(self.pdf_document)):
            page = self.pdf_document[i]
            mat = fitz.Matrix(0.5, 0.5)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            try:
                img_data = pix.tobytes("ppm")
                qimage = QImage.fromData(img_data)
                pixmap = QPixmap.fromImage(qimage)
            except:
                # fallback: create empty pixmap
                pixmap = QPixmap(thumb_width, int(thumb_width*1.414))
                pixmap.fill(Qt.white)
            aspect_ratio = pix.height / pix.width if pix.width > 0 else 1
            thumb_height = int(thumb_width * aspect_ratio)
            scaled_pixmap = pixmap.scaled(thumb_width, thumb_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            page_label = self._get_page_size_label(i)
            item = QListWidgetItem()
            item.setSizeHint(QSize(thumb_width + 20, thumb_height + 60))
            self.thumbnail_list.addItem(item)
            thumb_widget = ThumbnailWidget(i, scaled_pixmap, page_label)
            thumb_widget.clicked.connect(self.on_thumbnail_clicked)
            self.thumbnail_list.setItemWidget(item, thumb_widget)
            self.thumb_widgets[i] = thumb_widget
        self.update_selection_display()
        
    def _get_page_size_label(self, page_index):
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
        if button == Qt.LeftButton:
            if modifiers & Qt.ControlModifier:
                if page_index in self.selected_pages:
                    self.selected_pages.remove(page_index)
                else:
                    self.selected_pages.add(page_index)
            elif modifiers & Qt.ShiftModifier:
                if self.selected_pages:
                    anchor = self.active_page_index
                    start = min(page_index, anchor)
                    end = max(page_index, anchor)
                    for i in range(start, end + 1):
                        self.selected_pages.add(i)
                else:
                    self.selected_pages.add(page_index)
            else:
                self.selected_pages = {page_index}
            self.active_page_index = page_index
            self.update_selection_display()
            self.update_buttons_state()
        elif button == Qt.RightButton:
            if page_index not in self.selected_pages:
                self.selected_pages = {page_index}
                self.update_selection_display()
            self.show_context_menu()
            
    def show_context_menu(self):
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
        for idx, widget in self.thumb_widgets.items():
            widget.set_selected(idx in self.selected_pages)
            widget.set_focused(idx == self.active_page_index)
            
    def update_buttons_state(self):
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_undo = len(self.undo_stack) > 0
        has_redo = len(self.redo_stack) > 0
        has_clipboard = self.clipboard is not None
        self.action_save.setEnabled(doc_loaded)
        self.action_import_pdf.setEnabled(doc_loaded)
        self.action_import_image.setEnabled(doc_loaded)
        self.action_undo.setEnabled(has_undo)
        self.action_redo.setEnabled(has_redo)
        self.action_delete.setEnabled(doc_loaded and has_selection)
        self.action_cut.setEnabled(doc_loaded and has_selection)
        self.action_copy.setEnabled(doc_loaded and has_selection)
        self.action_paste_before.setEnabled(doc_loaded and has_clipboard and len(self.selected_pages) <= 1)
        self.action_paste_after.setEnabled(doc_loaded and has_clipboard and len(self.selected_pages) <= 1)
        self.action_export_pdf.setEnabled(doc_loaded and has_selection)
        self.action_export_image.setEnabled(doc_loaded and has_selection)
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
        if hasattr(self, 'action_select_portrait'):
            self.action_select_portrait.setEnabled(doc_loaded)
        if hasattr(self, 'action_select_landscape'):
            self.action_select_landscape.setEnabled(doc_loaded)
        if hasattr(self, 'action_crop_resize'):
            self.action_crop_resize.setEnabled(doc_loaded and has_selection)
        if hasattr(self, 'action_merge_grid'):
            self.action_merge_grid.setEnabled(doc_loaded and has_selection)
        if hasattr(self, 'action_insert_before'):
            self.action_insert_before.setEnabled(doc_loaded)
        if hasattr(self, 'action_insert_after'):
            self.action_insert_after.setEnabled(doc_loaded)
        if hasattr(self, 'action_reverse'):
            self.action_reverse.setEnabled(doc_loaded)
        self.action_zoom_in.setEnabled(doc_loaded and self.zoom_level > self.min_zoom)
        self.action_zoom_out.setEnabled(doc_loaded and self.zoom_level < self.max_zoom)
        
    def update_status(self, message):
        self.status_bar.showMessage(message)
        
    # ================================================================
    # DIALOG FUNCTIONS
    # ================================================================
    
    def show_shortcuts(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Skróty klawiszowe")
        msg.setText("""
<b>Plik:</b><br>
Ctrl+O - Otwórz PDF<br>
Ctrl+S - Zapisz jako<br>
Ctrl+I - Importuj PDF (z zakresem)<br>
Ctrl+E - Eksportuj PDF<br>
Ctrl+Shift+I - Importuj obraz (z ustawieniami)<br>
Ctrl+Shift+E - Eksportuj obrazy<br>
<br>
<b>Edycja:</b><br>
Ctrl+Z - Cofnij<br>
Ctrl+Y - Ponów<br>
Ctrl+X - Wytnij<br>
Ctrl+C - Kopiuj<br>
Ctrl+V - Wklej po<br>
Ctrl+Shift+V - Wklej przed<br>
Delete - Usuń<br>
Ctrl+D - Duplikuj<br>
<br>
<b>Zaznacz:</b><br>
Ctrl+A / F4 - Wszystkie strony<br>
F1 - Strony nieparzyste<br>
F2 - Strony parzyste<br>
Ctrl+F1 - Strony pionowe<br>
Ctrl+F2 - Strony poziome<br>
<br>
<b>Modyfikacje:</b><br>
Ctrl+Shift+- - Obróć w lewo<br>
Ctrl+Shift++ - Obróć w prawo<br>
F5 - Przesuń zawartość<br>
F6 - Usuń numerację<br>
F7 - Dodaj numerację<br>
F8 - Przytnij/Zmień rozmiar<br>
Ctrl+N - Wstaw pustą stronę po<br>
Ctrl+Shift+N - Wstaw pustą stronę przed<br>
<br>
<b>Widok:</b><br>
Ctrl++ - Zoom in<br>
Ctrl+- - Zoom out<br>
        """)
        msg.exec_()
        
    def show_about(self):
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
    # PAGE CROP AND RESIZE OPERATIONS
    # ================================================================
    
    def apply_page_crop_resize_dialog(self):
        if not self.pdf_document or not self.selected_pages:
            self.update_status("Musisz zaznaczyć przynajmniej jedną stronę PDF.")
            return
        dialog = PageCropResizeDialog(self)
        dialog.exec_()
        result = dialog.result
        if not result:
            self.update_status("Anulowano operację.")
            return
        pdf_bytes_export = io.BytesIO()
        self.pdf_document.save(pdf_bytes_export)
        pdf_bytes_export.seek(0)
        pdf_bytes_val = pdf_bytes_export.read()
        indices = sorted(list(self.selected_pages))
        crop_mode = result["crop_mode"]
        resize_mode = result["resize_mode"]
        try:
            if crop_mode == "crop_only" and resize_mode == "noresize":
                new_pdf_bytes = self._mask_crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"]
                )
                msg = "Dodano białe maski zamiast przycinania stron."
            elif crop_mode == "crop_resize" and resize_mode == "noresize":
                new_pdf_bytes = self._crop_pages(
                    pdf_bytes_val, indices,
                    result["crop_top_mm"], result["crop_bottom_mm"],
                    result["crop_left_mm"], result["crop_right_mm"],
                    reposition=False
                )
                msg = "Zastosowano przycięcie i zmianę rozmiaru arkusza."
            elif resize_mode == "resize_scale":
                new_pdf_bytes = self._resize_scale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"]
                )
                msg = "Zmieniono rozmiar i skalowano zawartość."
            elif resize_mode == "resize_noscale":
                new_pdf_bytes = self._resize_noscale(
                    pdf_bytes_val, indices,
                    result["target_width_mm"], result["target_height_mm"],
                    pos_mode=result.get("position_mode") or "center",
                    offset_x_mm=result.get("offset_x_mm") or 0,
                    offset_y_mm=result.get("offset_y_mm") or 0
                )
                msg = "Zmieniono rozmiar strony (bez skalowania zawartości)."
            else:
                self.update_status("Nie wybrano żadnej operacji do wykonania.")
                return
            self._save_state_to_undo()
            self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", new_pdf_bytes)
            self.update_status(msg)
            self.refresh_thumbnails()
        except Exception as e:
            self.update_status(f"Błąd podczas przetwarzania PDF: {e}")
            
    def _crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm, reposition=False, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_mediabox = RectangleObject([float(v) for v in page.mediabox])
            x0, y0, x1, y1 = [float(v) for v in orig_mediabox]
            new_x0 = x0 + mm2pt(left_mm)
            new_y0 = y0 + mm2pt(bottom_mm)
            new_x1 = x1 - mm2pt(right_mm)
            new_y1 = y1 - mm2pt(top_mm)
            if new_x0 >= new_x1 or new_y0 >= new_y1:
                writer.add_page(page)
                continue
            new_rect = RectangleObject([new_x0, new_y0, new_x1, new_y1])
            page.cropbox = new_rect
            page.trimbox = new_rect
            page.artbox = new_rect
            page.mediabox = orig_mediabox
            if reposition:
                dx = mm2pt(offset_x_mm) if pos_mode == "custom" else 0
                dy = mm2pt(offset_y_mm) if pos_mode == "custom" else 0
                if dx != 0 or dy != 0:
                    transform = Transformation().translate(tx=dx, ty=dy)
                    page.add_transformation(transform)
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
        
    def _mask_crop_pages(self, pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        MM_TO_PT = 72 / 25.4
        for i in selected_indices:
            page = doc[i]
            rect = page.rect
            left_pt = left_mm * MM_TO_PT
            right_pt = right_mm * MM_TO_PT
            top_pt = top_mm * MM_TO_PT
            bottom_pt = bottom_mm * MM_TO_PT
            if left_pt > 0:
                page.draw_rect(fitz.Rect(rect.x0, rect.y0, rect.x0 + left_pt, rect.y1), color=(1,1,1), fill=(1,1,1), overlay=True)
            if right_pt > 0:
                page.draw_rect(fitz.Rect(rect.x1 - right_pt, rect.y0, rect.x1, rect.y1), color=(1,1,1), fill=(1,1,1), overlay=True)
            if top_pt > 0:
                page.draw_rect(fitz.Rect(rect.x0, rect.y1 - top_pt, rect.x1, rect.y1), color=(1,1,1), fill=(1,1,1), overlay=True)
            if bottom_pt > 0:
                page.draw_rect(fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + bottom_pt), color=(1,1,1), fill=(1,1,1), overlay=True)
        output_bytes = doc.write()
        doc.close()
        return output_bytes
        
    def _resize_scale(self, pdf_bytes, selected_indices, width_mm, height_mm):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            scale = min(target_width / orig_w, target_height / orig_h)
            dx = (target_width - orig_w * scale) / 2
            dy = (target_height - orig_h * scale) / 2
            transform = Transformation().scale(sx=scale, sy=scale).translate(tx=dx, ty=dy)
            page.add_transformation(transform)
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
        
    def _resize_noscale(self, pdf_bytes, selected_indices, width_mm, height_mm, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        target_width = mm2pt(width_mm)
        target_height = mm2pt(height_mm)
        for i, page in enumerate(reader.pages):
            if i not in selected_indices:
                writer.add_page(page)
                continue
            orig_w = float(page.mediabox.width)
            orig_h = float(page.mediabox.height)
            if pos_mode == "center":
                dx = (target_width - orig_w) / 2
                dy = (target_height - orig_h) / 2
            else:
                dx = mm2pt(offset_x_mm)
                dy = mm2pt(offset_y_mm)
            transform = Transformation().translate(tx=dx, ty=dy)
            page.add_transformation(transform)
            page.mediabox = RectangleObject([0, 0, target_width, target_height])
            page.cropbox = RectangleObject([0, 0, target_width, target_height])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()
    
    # ================================================================
    # MERGE PAGES TO GRID (APPENDS NEW PAGE – PARITY WITH TK)
    # ================================================================
    
    def merge_pages_to_grid(self):
        """
        Scala zaznaczone strony w siatkę na nowym arkuszu.
        Każda strona jest renderowana do bitmapy i wstawiana jako obraz w PDF.
        Marginesy i odstępy są liczone od górnej/lewej krawędzi arkusza.
        """
        import io

        if not self.pdf_document:
            self.update_status("BŁĄD: Otwórz najpierw dokument PDF.")
            return
        if len(self.selected_pages) == 0:
            self.update_status("BŁĄD: Zaznacz przynajmniej jedną stronę do scalenia.")
            return

        selected_indices = sorted(list(self.selected_pages))
        num_pages = len(selected_indices)

        dialog = MergePageGridDialog(self, page_count=num_pages)
        dialog.exec_()
        params = dialog.result
        if params is None:
            self.update_status("Anulowano scalanie stron.")
            return

        try:
            sheet_width_pt = params["sheet_width_mm"] * self.MM_TO_POINTS
            sheet_height_pt = params["sheet_height_mm"] * self.MM_TO_POINTS
            margin_top_pt = params["margin_top_mm"] * self.MM_TO_POINTS
            margin_bottom_pt = params["margin_bottom_mm"] * self.MM_TO_POINTS
            margin_left_pt = params["margin_left_mm"] * self.MM_TO_POINTS
            margin_right_pt = params["margin_right_mm"] * self.MM_TO_POINTS
            spacing_x_pt = params["spacing_x_mm"] * self.MM_TO_POINTS
            spacing_y_pt = params["spacing_y_mm"] * self.MM_TO_POINTS
            rows = params["rows"]
            cols = params["cols"]

            TARGET_DPI = 600  # Wysoka jakość bitmapy
            PT_TO_INCH = 1 / 72

            total_cells = rows * cols
            source_pages = []
            for i in range(total_cells):
                if i < num_pages:
                    source_pages.append(selected_indices[i])
                else:
                    source_pages.append(selected_indices[-1])

            # Oblicz rozmiar komórki
            if cols == 1:
                cell_width = sheet_width_pt - margin_left_pt - margin_right_pt
            else:
                cell_width = (sheet_width_pt - margin_left_pt - margin_right_pt - (cols - 1) * spacing_x_pt) / cols
            if rows == 1:
                cell_height = sheet_height_pt - margin_top_pt - margin_bottom_pt
            else:
                cell_height = (sheet_height_pt - margin_top_pt - margin_bottom_pt - (rows - 1) * spacing_y_pt) / rows

            self._save_state_to_undo()
            new_page = self.pdf_document.new_page(width=sheet_width_pt, height=sheet_height_pt)

            for idx, src_idx in enumerate(source_pages):
                row = idx // cols
                col = idx % cols
                if row >= rows:
                    break

                x = margin_left_pt + col * (cell_width + spacing_x_pt)
                y = margin_top_pt + row * (cell_height + spacing_y_pt)

                src_page = self.pdf_document[src_idx]
                page_rect = src_page.rect
                page_w = page_rect.width
                page_h = page_rect.height

                # Automatyczny obrót jeśli orientacja strony nie pasuje do komórki
                page_landscape = page_w > page_h
                cell_landscape = cell_width > cell_height
                rotate = 0
                if page_landscape != cell_landscape:
                    rotate = 90

                # Oblicz skalę renderowania
                bitmap_w = int(round(cell_width * TARGET_DPI * PT_TO_INCH))
                bitmap_h = int(round(cell_height * TARGET_DPI * PT_TO_INCH))

                if rotate == 90:
                    scale_x = bitmap_w / page_h
                    scale_y = bitmap_h / page_w
                else:
                    scale_x = bitmap_w / page_w
                    scale_y = bitmap_h / page_h

                pix = src_page.get_pixmap(matrix=fitz.Matrix(scale_x, scale_y).prerotate(rotate), alpha=False)
                img_bytes = pix.tobytes("png")
                rect = fitz.Rect(x, y, x + cell_width, y + cell_height)
                new_page.insert_image(rect, stream=img_bytes)

            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_status(
                f"Scalono {num_pages} stron w siatkę {rows}x{cols} na nowym arkuszu {params['format_name']} (bitmapy 600dpi)."
            )
        except Exception as e:
            self.update_status(f"BŁĄD: Nie udało się scalić stron: {e}")
            import traceback
            traceback.print_exc()

    # ================================================================
    # INSERT BLANK PAGES (FIXED active_page_index)
    # ================================================================
    
    def insert_blank_page_before(self):
        if not self.pdf_document:
            self.update_status("Najpierw otwórz dokument PDF.")
            return
        
        # If multiple pages selected, ask for confirmation
        if len(self.selected_pages) > 1:
            num_inserts = len(self.selected_pages)
            reply = QMessageBox.question(
                self, "Potwierdzenie wstawiania",
                f"Czy na pewno chcesz wstawić {num_inserts} stron?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.update_status("Wstawianie anulowane.")
                return
            
            # Sort selected pages to insert in correct order
            sorted_pages = sorted(list(self.selected_pages))
            
            try:
                self._save_state_to_undo()
                # Insert before each selected page (in reverse order to maintain indices)
                for page_idx in reversed(sorted_pages):
                    insert_pos = page_idx
                    try:
                        rect = self.pdf_document[page_idx].rect
                        width = rect.width
                        height = rect.height
                    except Exception:
                        width, height = (595.276, 841.89)
                    self.pdf_document.insert_page(insert_pos, width=width, height=height)
                
                self.refresh_thumbnails()
                self.update_status(f"Dodano {num_inserts} pustych stron.")
            except Exception as e:
                self.update_status(f"Błąd: {e}")
            return
        
        # Single page or no selection
        try:
            self._save_state_to_undo()
            # use active_page_index (bugfix)
            insert_pos = self.active_page_index if self.active_page_index >= 0 else 0
            self.pdf_document.insert_page(insert_pos)
            self.refresh_thumbnails()
            self.update_status(f"Dodano pustą stronę przed stroną {insert_pos + 1}.")
        except Exception as e:
            self.update_status(f"Błąd: {e}")
    
    def insert_blank_page_after(self):
        if not self.pdf_document:
            self.update_status("Najpierw otwórz dokument PDF.")
            return
        
        # If multiple pages selected, ask for confirmation
        if len(self.selected_pages) > 1:
            num_inserts = len(self.selected_pages)
            reply = QMessageBox.question(
                self, "Potwierdzenie wstawiania",
                f"Czy na pewno chcesz wstawić {num_inserts} stron?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.update_status("Wstawianie anulowane.")
                return
            
            # Sort selected pages to insert in correct order
            sorted_pages = sorted(list(self.selected_pages))
            
            try:
                self._save_state_to_undo()
                # Insert after each selected page (in reverse order to maintain indices)
                for page_idx in reversed(sorted_pages):
                    insert_pos = page_idx + 1
                    try:
                        rect = self.pdf_document[page_idx].rect
                        width = rect.width
                        height = rect.height
                    except Exception:
                        width, height = (595.276, 841.89)
                    self.pdf_document.insert_page(insert_pos, width=width, height=height)
                
                self.refresh_thumbnails()
                self.update_status(f"Dodano {num_inserts} pustych stron.")
            except Exception as e:
                self.update_status(f"Błąd: {e}")
            return
        
        # Single page or no selection
        try:
            self._save_state_to_undo()
            insert_pos = self.active_page_index + 1 if self.active_page_index >= 0 else len(self.pdf_document)
            self.pdf_document.insert_page(insert_pos)
            self.refresh_thumbnails()
            self.update_status(f"Dodano pustą stronę po stronie {self.active_page_index + 1}.")
        except Exception as e:
            self.update_status(f"Błąd: {e}")
    
    # ================================================================
    # REVERSE PAGES
    # ================================================================
    
    def reverse_pages(self):
        if not self.pdf_document:
            QMessageBox.information(self, "Informacja", "Najpierw otwórz plik PDF.")
            return
        try:
            self._save_state_to_undo()
            page_count = len(self.pdf_document)
            new_doc = fitz.open()
            for i in range(page_count - 1, -1, -1):
                new_doc.insert_pdf(self.pdf_document, from_page=i, to_page=i)
            self.pdf_document.close()
            self.pdf_document = new_doc
            self.active_page_index = 0
            self.selected_pages.clear()
            self.refresh_thumbnails()
            self.update_status(f"Pomyślnie odwrócono kolejność {page_count} stron.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas odwracania stron: {e}")
    
    # ================================================================
    # CLOSE EVENT
    # ================================================================
    
    def closeEvent(self, event):
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
                if len(self.undo_stack) > 0:
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
    app.setStyle("Fusion")
    window = PDFEditorQt()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()