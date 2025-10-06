"""
Moduł eksportu zaznaczonych stron PDF do formatu DOCX.
"""

import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches
from PIL import Image
import io
import os


def export_selected_pages_to_docx(pdf_document, selected_pages, output_path, dpi=300):
    """
    Eksportuje zaznaczone strony PDF do pliku DOCX.
    
    Każda strona PDF jest konwertowana na obraz w wysokiej rozdzielczości
    i wstawiana na osobną stronę dokumentu Word.
    
    Args:
        pdf_document: Obiekt PyMuPDF (fitz.Document) z otwartym PDF
        selected_pages: Lista indeksów stron do eksportu (0-based)
        output_path: Ścieżka do pliku DOCX, który zostanie utworzony
        dpi: Rozdzielczość DPI dla konwersji stron (domyślnie 300)
    
    Returns:
        int: Liczba wyeksportowanych stron
        
    Raises:
        Exception: W przypadku błędu podczas eksportu
    """
    if not pdf_document:
        raise ValueError("Nie podano dokumentu PDF")
    
    if not selected_pages:
        raise ValueError("Nie wybrano stron do eksportu")
    
    # Sortuj strony według indeksów
    sorted_pages = sorted(selected_pages)
    
    # Utwórz nowy dokument Word
    doc = Document()
    
    # Ustaw rozdzielczość konwersji
    zoom = dpi / 72.0  # 72 DPI to bazowa rozdzielczość PDF
    matrix = fitz.Matrix(zoom, zoom)
    
    exported_count = 0
    
    for page_index in sorted_pages:
        if page_index >= len(pdf_document):
            continue
            
        # Załaduj stronę PDF
        page = pdf_document.load_page(page_index)
        
        # Konwertuj stronę na pixmap (obraz)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Konwertuj pixmap do PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Zapisz obraz do bufora
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Pobierz wymiary strony PDF w punktach
        page_rect = page.rect
        page_width_pt = page_rect.width
        page_height_pt = page_rect.height
        
        # Konwertuj wymiary z punktów na cale (1 cal = 72 punkty)
        page_width_inches = page_width_pt / 72.0
        page_height_inches = page_height_pt / 72.0
        
        # Dodaj nową stronę do dokumentu Word (jeśli to nie pierwsza strona)
        if exported_count > 0:
            doc.add_page_break()
        
        # Dodaj obraz do dokumentu
        # Skaluj obraz, aby zmieścił się na stronie (z marginesem)
        # Domyślne marginesy Word to około 1 cal z każdej strony
        max_width = page_width_inches - 2.0  # Zostaw 1 cal marginesu z każdej strony
        max_height = page_height_inches - 2.0
        
        # Oblicz współczynnik skali, aby obraz zmieścił się na stronie
        scale_w = max_width / page_width_inches if page_width_inches > max_width else 1.0
        scale_h = max_height / page_height_inches if page_height_inches > max_height else 1.0
        scale = min(scale_w, scale_h, 1.0)  # Nie powiększaj, tylko zmniejszaj jeśli potrzeba
        
        final_width = page_width_inches * scale
        final_height = page_height_inches * scale
        
        # Wstaw obraz z odpowiednią szerokością (zachowanie proporcji)
        doc.add_picture(img_buffer, width=Inches(final_width))
        
        exported_count += 1
    
    # Zapisz dokument DOCX
    doc.save(output_path)
    
    return exported_count
