# -*- coding: utf-8 -*-
"""
GRYF PDF Editor - PySide6 Version
Kompletna migracja z Tkinter do PySide6 (Qt for Python)
Data migracji: 2025-10-17
Wersja: 5.6.0

Zachowane wszystkie funkcje z oryginalnej wersji Tkinter:
- Przeglądanie, edycja i manipulacja PDF
- Numeracja stron, kadrowanie, zmiana rozmiaru, obracanie
- Nagrywanie i odtwarzanie makr
- Zarządzanie preferencjami
- Import/eksport obrazów
- Przeciąganie i upuszczanie
- I wszystkie pozostałe funkcje
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QDialog, QLineEdit, QCheckBox,
    QComboBox, QRadioButton, QButtonGroup, QGroupBox, QScrollArea, QFrame,
    QListWidget, QTextEdit, QProgressBar, QSpinBox, QDoubleSpinBox,
    QTabWidget, QDialogButtonBox, QMenu, QToolBar, QStatusBar, QSplitter,
    QGridLayout, QFormLayout, QSizePolicy, QAbstractItemView, QListWidgetItem,
    QStyle, QStyledItemDelegate, QInputDialog
)
from PySide6.QtCore import (
    Qt, QSize, QPoint, QRect, QTimer, Signal, QMimeData, QByteArray, 
    QBuffer, QIODevice, QEvent, Slot, QObject
)
from PySide6.QtGui import (
    QPixmap, QImage, QIcon, QPainter, QColor, QAction, QKeySequence, 
    QDrag, QPalette, QCursor, QMouseEvent, QKeyEvent
)

import fitz  # PyMuPDF
from PIL import Image
import io
import math 
import os
import sys 
import re 
from typing import Optional, List, Set, Dict, Union
from datetime import date, datetime 
import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, FloatObject, ArrayObject, NameObject
import json

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_icon_folder():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "icons")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

ICON_FOLDER = get_icon_folder()

#FOCUS_HIGHLIGHT_COLOR = "#B3E5FC" # Czarny (Black)
FOCUS_HIGHLIGHT_COLOR = "#d3d3d3" # Czarny (Black)
FOCUS_HIGHLIGHT_WIDTH = 6       # Szerokość ramki fokusu (stała)
 
# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor" 
PROGRAM_VERSION = "5.6.0"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 [w punktach PDF i mm] ===
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

def validate_float_range(value, minval, maxval):
    if not value:
        return True
    try:
        v = float(value.replace(",", "."))
        return minval <= v <= maxval
    except Exception:
        return False

def generate_unique_export_filename(directory, base_name, page_range, extension):
    """
    Generuje unikalną nazwę pliku w formacie:
    "Eksport z pliku [base_name]_[page_range]_[date]_[time].[extension]"
    Jeśli plik istnieje, dodaje (1), (2), (3) itd.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Eksport_{page_range}_{timestamp}.{extension}"
    filepath = os.path.join(directory, filename)
    
    # Jeśli plik istnieje, dodaj numer
    if os.path.exists(filepath):
        counter = 1
        base_without_ext = f"Eksport_{page_range}_{timestamp}"
        while True:
            filename = f"{base_without_ext} ({counter}).{extension}"
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                break
            counter += 1
    
    return filepath
        
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
  
import tkinter as tk
from tkinter import ttk, messagebox


import tkinter as tk
from tkinter import ttk

def custom_messagebox(parent, title, message, typ="info"):
    """
    Wyświetla niestandardowe okno dialogowe wyśrodkowane na oknie aplikacji (nie na środku ekranu).
    Brak obsługi ikon PNG, okno jest nieco mniejsze.
    """
    import tkinter as tk
    from tkinter import ttk

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    # Kolory dla różnych typów (opcjonalnie)
    colors = {
        "info": "#d1ecf1",
        "error": "#f8d7da",
        "warning": "#fff3cd",
        "question": "#d1ecf1",
        "yesnocancel": "#d1ecf1"
    }
    bg_color = colors.get(typ, "#f0f0f0")

    main_frame = ttk.Frame(dialog, padding="12")
    main_frame.pack(fill="both", expand=True)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True, pady=(0, 12))

    # Tylko tekst komunikatu, bez ikony
    msg_label = tk.Label(content_frame, text=message, justify="left", wraplength=310, font=("Arial", 10))
    msg_label.pack(fill="both", expand=True, pady=6)

    result = [None]

    def on_yes():
        result[0] = True
        dialog.destroy()
    def on_no():
        result[0] = False
        dialog.destroy()
    def on_cancel():
        result[0] = None
        dialog.destroy()
    def on_ok():
        dialog.destroy()

    button_frame = ttk.Frame(main_frame)
    button_frame.pack()
    if typ == "question":
        yes_btn = ttk.Button(button_frame, text="Tak", command=on_yes, width=10)
        yes_btn.pack(side="left", padx=4)
        no_btn = ttk.Button(button_frame, text="Nie", command=on_no, width=10)
        no_btn.pack(side="left", padx=4)
        dialog.bind("<Return>", lambda e: on_yes())
        dialog.bind("<Escape>", lambda e: on_no())
        yes_btn.focus_set()
    elif typ == "yesnocancel":
        yes_btn = ttk.Button(button_frame, text="Tak", command=on_yes, width=10)
        yes_btn.pack(side="left", padx=4)
        no_btn = ttk.Button(button_frame, text="Nie", command=on_no, width=10)
        no_btn.pack(side="left", padx=4)
        cancel_btn = ttk.Button(button_frame, text="Anuluj", command=on_cancel, width=10)
        cancel_btn.pack(side="left", padx=4)
        dialog.bind("<Return>", lambda e: on_yes())
        dialog.bind("<Escape>", lambda e: on_cancel())
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        yes_btn.focus_set()
    else:
        ok_btn = ttk.Button(button_frame, text="OK", command=on_ok, width=10)
        ok_btn.pack(padx=4)
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_ok())
        ok_btn.focus_set()

    # Wyśrodkuj na rodzicu
    dialog.update_idletasks()
    dialog_w = dialog.winfo_width()
    dialog_h = dialog.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    x = parent_x + (parent_w - dialog_w) // 2
    y = parent_y + (parent_h - dialog_h) // 2
    dialog.geometry(f"+{x}+{y}")
    dialog.wait_window()
    return result[0]

# === SYSTEM ZARZĄDZANIA PREFERENCJAMI ===

class PreferencesManager:
    """Zarządza preferencjami programu i dialogów, zapisuje/odczytuje z pliku preferences.txt"""
    
    def __init__(self, filepath="preferences.txt"):
        self.filepath = os.path.join(BASE_DIR, filepath)
        self.preferences = {}
        self.defaults = {
            # Preferencje globalne
            'default_save_path': '',
            'default_read_path': '',
            'last_open_path': '',
            'last_save_path': '',
            'thumbnail_quality': 'Średnia',
            'confirm_delete': 'False',
            'export_image_dpi': '300',  # DPI dla eksportu obrazów (150, 300, 600)
            
            # PageCropResizeDialog
            'PageCropResizeDialog.crop_mode': 'nocrop',
            'PageCropResizeDialog.margin_top': '10',
            'PageCropResizeDialog.margin_bottom': '10',
            'PageCropResizeDialog.margin_left': '10',
            'PageCropResizeDialog.margin_right': '10',
            'PageCropResizeDialog.resize_mode': 'noresize',
            'PageCropResizeDialog.target_format': 'A4',
            'PageCropResizeDialog.custom_width': '',
            'PageCropResizeDialog.custom_height': '',
            'PageCropResizeDialog.position_mode': 'center',
            'PageCropResizeDialog.offset_x': '0',
            'PageCropResizeDialog.offset_y': '0',
            
            # PageNumberingDialog
            'PageNumberingDialog.margin_left': '35',
            'PageNumberingDialog.margin_right': '25',
            'PageNumberingDialog.margin_vertical_mm': '15',
            'PageNumberingDialog.vertical_pos': 'dol',
            'PageNumberingDialog.alignment': 'prawa',
            'PageNumberingDialog.mode': 'normalna',
            'PageNumberingDialog.start_page': '1',
            'PageNumberingDialog.start_number': '1',
            'PageNumberingDialog.font_name': 'Times-Roman',
            'PageNumberingDialog.font_size': '12',
            'PageNumberingDialog.mirror_margins': 'False',
            'PageNumberingDialog.format_type': 'simple',
            
            # ShiftContentDialog
            'ShiftContentDialog.x_direction': 'P',
            'ShiftContentDialog.y_direction': 'G',
            'ShiftContentDialog.x_value': '0',
            'ShiftContentDialog.y_value': '0',
            
            # PageNumberMarginDialog
            'PageNumberMarginDialog.top_margin': '20',
            'PageNumberMarginDialog.bottom_margin': '20',
            
            # MergePageGridDialog
            'MergePageGridDialog.sheet_format': 'A4',
            'MergePageGridDialog.orientation': 'Pionowa',
            'MergePageGridDialog.margin_top_mm': '5',
            'MergePageGridDialog.margin_bottom_mm': '5',
            'MergePageGridDialog.margin_left_mm': '5',
            'MergePageGridDialog.margin_right_mm': '5',
            'MergePageGridDialog.spacing_x_mm': '10',
            'MergePageGridDialog.spacing_y_mm': '10',
            'MergePageGridDialog.dpi_var': '300',
            
            # EnhancedPageRangeDialog
            'EnhancedPageRangeDialog.last_range': '',
            
            # ImageImportSettingsDialog
            'ImageImportSettingsDialog.target_format': 'A4',
            'ImageImportSettingsDialog.orientation': 'auto',
            'ImageImportSettingsDialog.margin_mm': '10',
            'ImageImportSettingsDialog.scaling_mode': 'DOPASUJ',
            'ImageImportSettingsDialog.alignment_mode': 'SRODEK',
            'ImageImportSettingsDialog.scale_factor': '100.0',
            'ImageImportSettingsDialog.page_orientation': 'PIONOWO',
            'ImageImportSettingsDialog.custom_width': '',
            'ImageImportSettingsDialog.custom_height': '',
            'ImageImportSettingsDialog.keep_ratio': 'True',
            
            # Color detection settings
            'color_detect_threshold': '5',
            'color_detect_samples': '300',
            'color_detect_scale': '0.2',
        }
        self.load_preferences()
    
    def load_preferences(self):
        """Wczytuje preferencje z pliku"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line:
                            key, value = line.split('=', 1)
                            self.preferences[key.strip()] = value.strip()
            except Exception as e:
                print(f"Błąd wczytywania preferencji: {e}")
        # Wypełnij brakujące wartości domyślnymi
        for key, value in self.defaults.items():
            if key not in self.preferences:
                self.preferences[key] = value
    
    def save_preferences(self):
        """Zapisuje preferencje do pliku"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for key, value in sorted(self.preferences.items()):
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Błąd zapisywania preferencji: {e}")
    
    def get(self, key, default=None):
        """Pobiera wartość preferencji"""
        return self.preferences.get(key, default if default is not None else self.defaults.get(key, ''))
    
    def set(self, key, value):
        """Ustawia wartość preferencji"""
        self.preferences[key] = str(value)
        self.save_preferences()
    
    def reset_to_defaults(self):
        """Przywraca wszystkie preferencje do wartości domyślnych"""
        self.preferences = self.defaults.copy()
        self.save_preferences()
    
    def reset_dialog_defaults(self, dialog_name):
        """Przywraca wartości domyślne dla konkretnego dialogu"""
        for key in list(self.preferences.keys()):
            if key.startswith(f"{dialog_name}."):
                if key in self.defaults:
                    self.preferences[key] = self.defaults[key]
        self.save_preferences()
    
    def get_profiles(self, profile_key):
        """Pobiera profile z preferencji jako słownik"""
        profiles_json = self.get(profile_key, '{}')
        try:
            return json.loads(profiles_json)
        except:
            return {}
    
    def save_profiles(self, profile_key, profiles_dict):
        """Zapisuje profile do preferencji jako JSON"""
        profiles_json = json.dumps(profiles_dict, ensure_ascii=False)
        self.set(profile_key, profiles_json)


