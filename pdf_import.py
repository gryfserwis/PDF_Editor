"""
Moduł pdf_import.py - Import plików do PDF.

Zawiera funkcje do importowania obrazów jako strony PDF oraz
scalania dokumentów PDF.
"""

import fitz
from PIL import Image


def create_pdf_page_from_image(pdf_document, image_path):
    """Tworzy nową stronę PDF z obrazu.
    
    Strona PDF będzie miała rozmiar dopasowany do wymiarów obrazu.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        image_path: Ścieżka do pliku obrazu
        
    Returns:
        fitz.Page: Nowo utworzona strona lub None w przypadku błędu
        
    Raises:
        Exception: Jeśli nie można wczytać obrazu
    """
    img = Image.open(image_path)
    image_width_px, image_height_px = img.size
    image_dpi = img.info.get('dpi', (96, 96))[0] if isinstance(img.info.get('dpi'), tuple) else 96
    img.close()
    
    # Przelicz piksele na punkty PDF (1 cal = 72 punkty)
    image_width_pt = (image_width_px / image_dpi) * 72
    image_height_pt = (image_height_px / image_dpi) * 72
    
    # Nowa strona o rozmiarze obrazu
    page = pdf_document.new_page(width=image_width_pt, height=image_height_pt)
    rect = fitz.Rect(0, 0, image_width_pt, image_height_pt)
    page.insert_image(rect, filename=image_path)
    
    return page


def insert_image_as_page(pdf_document, image_path, settings, mm_to_points):
    """Wstawia obraz jako nową stronę PDF z określonymi ustawieniami.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        image_path: Ścieżka do pliku obrazu
        settings: Słownik z ustawieniami importu zawierający:
            - page_width_pt: Szerokość strony w punktach
            - page_height_pt: Wysokość strony w punktach
            - margin_pt: Margines w punktach
            - scaling_mode: Tryb skalowania
            - alignment_mode: Tryb wyrównania
            - scale_factor: Współczynnik skali
            - custom_width_pt: Niestandardowa szerokość
            - custom_height_pt: Niestandardowa wysokość
        mm_to_points: Współczynnik konwersji mm na punkty
        
    Returns:
        fitz.Page: Nowo utworzona strona
    """
    img = Image.open(image_path)
    img_width_px, img_height_px = img.size
    img_dpi = img.info.get('dpi', (96, 96))[0] if isinstance(img.info.get('dpi'), tuple) else 96
    img.close()
    
    img_width_pt = (img_width_px / img_dpi) * 72
    img_height_pt = (img_height_px / img_dpi) * 72
    
    page_width = settings['page_width_pt']
    page_height = settings['page_height_pt']
    margin = settings.get('margin_pt', 0)
    
    page = pdf_document.new_page(width=page_width, height=page_height)
    
    # Oblicz obszar dostępny dla obrazu
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin
    
    scaling_mode = settings.get('scaling_mode', 'DOPASUJ')
    
    if scaling_mode == 'DOPASUJ':
        scale = min(available_width / img_width_pt, available_height / img_height_pt)
        final_width = img_width_pt * scale
        final_height = img_height_pt * scale
    elif scaling_mode == 'ORYGINALNY':
        final_width = img_width_pt
        final_height = img_height_pt
    elif scaling_mode == 'SKALA':
        scale_factor = settings.get('scale_factor', 100.0) / 100.0
        final_width = img_width_pt * scale_factor
        final_height = img_height_pt * scale_factor
    elif scaling_mode == 'CUSTOM_SIZE':
        final_width = settings.get('custom_width_pt', img_width_pt)
        final_height = settings.get('custom_height_pt', img_height_pt)
    else:
        final_width = img_width_pt
        final_height = img_height_pt
    
    # Wyrównanie
    alignment_mode = settings.get('alignment_mode', 'SRODEK')
    
    if alignment_mode == 'SRODEK':
        x0 = margin + (available_width - final_width) / 2
        y0 = margin + (available_height - final_height) / 2
    elif alignment_mode == 'GORA_LEWO':
        x0 = margin
        y0 = margin
    elif alignment_mode == 'GORA_PRAWO':
        x0 = page_width - margin - final_width
        y0 = margin
    elif alignment_mode == 'DOL_LEWO':
        x0 = margin
        y0 = page_height - margin - final_height
    elif alignment_mode == 'DOL_PRAWO':
        x0 = page_width - margin - final_width
        y0 = page_height - margin - final_height
    else:
        x0 = margin
        y0 = margin
    
    rect = fitz.Rect(x0, y0, x0 + final_width, y0 + final_height)
    page.insert_image(rect, filename=image_path)
    
    return page


def import_pdf_pages(target_doc, source_doc, page_indices=None, insert_after_index=None):
    """Importuje strony z jednego PDF do drugiego.
    
    Args:
        target_doc: Docelowy dokument PDF (fitz.Document)
        source_doc: Źródłowy dokument PDF (fitz.Document)
        page_indices: Lista indeksów stron do importu (None = wszystkie)
        insert_after_index: Indeks, po którym wstawić strony (None = na końcu)
        
    Returns:
        int: Liczba zaimportowanych stron
    """
    if page_indices is None:
        page_indices = list(range(len(source_doc)))
    
    if insert_after_index is None:
        insert_after_index = len(target_doc) - 1
    
    for idx in page_indices:
        target_doc.insert_pdf(source_doc, from_page=idx, to_page=idx, 
                            start_at=insert_after_index + 1)
        insert_after_index += 1
    
    return len(page_indices)
