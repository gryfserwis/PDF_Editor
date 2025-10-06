"""
Moduł utils.py - Funkcje pomocnicze dla PDF Editor.

Zawiera wspólne funkcje używane w całej aplikacji, takie jak konwersja jednostek,
walidacja danych i generowanie nazw plików.
"""

import os
import sys
from datetime import datetime


# Stałe do konwersji jednostek
MM_TO_POINTS = 72 / 25.4  # ~2.8346


def mm_to_pt(mm):
    """Konwertuje milimetry na punkty PDF.
    
    Args:
        mm: Wartość w milimetrach
        
    Returns:
        float: Wartość w punktach PDF
    """
    return float(mm) * MM_TO_POINTS


def validate_float_range(value, min_val, max_val):
    """Waliduje czy wartość mieści się w podanym zakresie.
    
    Args:
        value: Wartość do sprawdzenia (string lub liczba)
        min_val: Minimalna dopuszczalna wartość
        max_val: Maksymalna dopuszczalna wartość
        
    Returns:
        bool: True jeśli wartość jest poprawna, False w przeciwnym razie
    """
    if not value:
        return True
    try:
        v = float(str(value).replace(",", "."))
        return min_val <= v <= max_val
    except Exception:
        return False


def generate_unique_export_filename(directory, base_name, page_range, extension):
    """Generuje unikalną nazwę pliku dla eksportu.
    
    Generuje nazwę w formacie: "Eksport_[page_range]_[timestamp].[extension]"
    Jeśli plik już istnieje, dodaje (1), (2), (3) itd.
    
    Args:
        directory: Ścieżka do katalogu docelowego
        base_name: Nazwa bazowa pliku (nieużywana obecnie)
        page_range: Zakres stron (np. "1-5" lub "3")
        extension: Rozszerzenie pliku (bez kropki)
        
    Returns:
        str: Pełna ścieżka do unikalnego pliku
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"Eksport_{page_range}_{timestamp}.{extension}"
    filepath = os.path.join(directory, filename)
    
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
    """Tworzy poprawną ścieżkę do zasobów (ikony, logo itp.).
    
    Działa zarówno w trybie deweloperskim jak i po spakowaniu PyInstallerem.
    
    Args:
        relative_path: Relatywna ścieżka do zasobu
        
    Returns:
        str: Pełna ścieżka do zasobu
    """
    try:
        # Aplikacja spakowana (PyInstaller --onefile)
        base_path = sys._MEIPASS
    except AttributeError:
        # Tryb deweloperski
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)
