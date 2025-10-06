"""
Moduł export_images.py - Eksport stron PDF do obrazów.

Zawiera funkcje do eksportowania stron PDF jako pliki obrazów
w różnych formatach i rozdzielczościach.
"""

import os
import fitz
from utils import generate_unique_export_filename


def export_pages_to_images(pdf_document, selected_indices, output_dir, base_filename, export_dpi=600):
    """Eksportuje wybrane strony PDF do plików PNG.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        selected_indices: Lista indeksów stron do eksportu
        output_dir: Katalog docelowy dla plików
        base_filename: Nazwa bazowa pliku źródłowego
        export_dpi: Rozdzielczość DPI dla eksportu (domyślnie 600)
        
    Returns:
        int: Liczba pomyślnie wyeksportowanych stron
        
    Raises:
        Exception: Jeśli wystąpi błąd podczas eksportu
    """
    zoom = export_dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    exported_count = 0
    
    for index in selected_indices:
        if index < len(pdf_document):
            page = pdf_document.load_page(index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            single_page_range = str(index + 1)
            output_path = generate_unique_export_filename(
                output_dir, base_filename, single_page_range, "png"
            )
            
            pix.save(output_path)
            exported_count += 1
    
    return exported_count
