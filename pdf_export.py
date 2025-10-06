"""
Moduł pdf_export.py - Eksport stron PDF.

Zawiera funkcje do eksportowania wybranych stron jako nowe dokumenty PDF.
"""

import os
import fitz
from utils import generate_unique_export_filename


def export_pages_to_pdf(pdf_document, selected_indices, output_dir, base_filename, mode='single'):
    """Eksportuje wybrane strony do pliku/plików PDF.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        selected_indices: Lista indeksów stron do eksportu
        output_dir: Katalog docelowy dla plików
        base_filename: Nazwa bazowa pliku źródłowego
        mode: Tryb eksportu ('single' - jeden plik, 'separate' - osobne pliki)
        
    Returns:
        tuple: (liczba_plików, lista_ścieżek) - liczba utworzonych plików i ich ścieżki
        
    Raises:
        Exception: Jeśli wystąpi błąd podczas eksportu
    """
    exported_files = []
    
    if mode == 'single':
        # Wszystkie strony do jednego pliku
        if len(selected_indices) == 1:
            page_range = str(selected_indices[0] + 1)
        else:
            page_range = f"{selected_indices[0] + 1}-{selected_indices[-1] + 1}"
        
        output_path = generate_unique_export_filename(
            output_dir, base_filename, page_range, "pdf"
        )
        
        new_doc = fitz.open()
        for idx in selected_indices:
            new_doc.insert_pdf(pdf_document, from_page=idx, to_page=idx)
        
        new_doc.save(output_path)
        new_doc.close()
        exported_files.append(output_path)
    
    else:  # mode == 'separate'
        # Każda strona do osobnego pliku
        for idx in selected_indices:
            page_range = str(idx + 1)
            output_path = generate_unique_export_filename(
                output_dir, base_filename, page_range, "pdf"
            )
            
            new_doc = fitz.open()
            new_doc.insert_pdf(pdf_document, from_page=idx, to_page=idx)
            new_doc.save(output_path)
            new_doc.close()
            exported_files.append(output_path)
    
    return len(exported_files), exported_files


def save_pdf_document(pdf_document, filepath):
    """Zapisuje dokument PDF do pliku.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        filepath: Ścieżka docelowa
        
    Returns:
        bool: True jeśli zapisano pomyślnie
    """
    try:
        pdf_document.save(filepath)
        return True
    except Exception as e:
        raise Exception(f"Błąd zapisu pliku: {e}")
