from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QLabel, QPushButton,
    QLineEdit, QRadioButton, QCheckBox, QComboBox, QGroupBox, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QMessageBox,
    QFileDialog, QFrame, QSizePolicy, QToolTip, QMenu, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize, QTimer, QMimeData, QUrl
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QAction, QKeySequence, QDrag, QIcon
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

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FOLDER = os.path.join(BASE_DIR, "icons")
FOCUS_HIGHLIGHT_COLOR = "#000000"
FOCUS_HIGHLIGHT_WIDTH = 2

# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor"
PROGRAM_VERSION = "4.1.1"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 (w punktach PDF i mm) ===
A4_WIDTH_POINTS = 595.276
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4  # ~2.8346

def mm2pt(mm):
    return float(mm) * MM_TO_POINTS

# === STAŁE KOLORY NARZĘDZIOWE ===
BG_IMPORT = "#F0AD4E"
GRAY_FG = "#555555"

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

# === STAŁE KOLORYSTYKA DLA SPOJNOSCI ===
BG_PRIMARY = '#F0F0F0'
BG_SECONDARY = '#E0E0E0'
BG_BUTTON_DEFAULT = "#D0D0D0"
FG_TEXT = "#444444"

def resource_path(relative_path):
    """
    Tworzy poprawną ścieżkę do zasobów (logo, ikony itp.).
    Działa w trybie deweloperskim i po spakowaniu PyInstallerem.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

