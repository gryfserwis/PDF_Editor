"""
Moduł page_numbering.py - Numeracja stron PDF.

Zawiera funkcje do dodawania i usuwania numeracji na stronach PDF
z różnymi opcjami położenia, wyrównania i formatowania.
"""

import fitz
from utils import mm_to_pt


def insert_page_numbers_on_pages(pdf_document, selected_indices, settings, mm_to_points):
    """Wstawia numerację na wybranych stronach PDF.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        selected_indices: Lista indeksów stron do numeracji
        settings: Słownik z ustawieniami numeracji zawierający:
            - start_num: Numer początkowy
            - mode: Tryb ('normalna' lub 'lustrzana')
            - alignment: Wyrównanie ('lewa', 'prawa', 'srodek')
            - vertical_pos: Położenie pionowe ('gora' lub 'dol')
            - mirror_margins: Czy odbijać marginesy dla stron parzystych
            - format_type: Typ formatowania ('simple' lub 'full')
            - margin_left_mm: Lewy margines w mm
            - margin_right_mm: Prawy margines w mm
            - margin_vertical_mm: Margines pionowy w mm
            - font_size: Rozmiar czcionki
            - font_name: Nazwa czcionki
        mm_to_points: Współczynnik konwersji mm na punkty
        
    Returns:
        int: Liczba stron, na których wstawiono numerację
    """
    start_number = settings['start_num']
    mode = settings['mode']
    direction = settings['alignment']
    position = settings['vertical_pos']
    mirror_margins = settings['mirror_margins']
    format_mode = settings['format_type']
    
    left_mm = settings['margin_left_mm']
    right_mm = settings['margin_right_mm']
    
    left_pt_base = left_mm * mm_to_points
    right_pt_base = right_mm * mm_to_points
    margin_v_mm = settings['margin_vertical_mm']
    margin_v = margin_v_mm * mm_to_points
    font_size = settings['font_size']
    font = settings['font_name']
    
    current_number = start_number
    total_counted_pages = len(selected_indices) + start_number - 1
    
    for i in selected_indices:
        page = pdf_document.load_page(i)
        rect = page.rect
        rotation = page.rotation
        
        # Tworzenie tekstu numeracji
        if format_mode == 'full':
            text = f"Strona {current_number} z {total_counted_pages}"
        else:
            text = str(current_number)
        
        text_width = fitz.get_text_length(text, fontname=font, fontsize=font_size)
        
        # Ustal wyrównanie
        is_even_counted_page = (current_number - start_number) % 2 == 0
        
        if mode == "lustrzana":
            if direction == "srodek":
                align = "srodek"
            elif direction == "lewa":
                align = "lewa" if is_even_counted_page else "prawa"
            else:
                align = "prawa" if is_even_counted_page else "lewa"
        else:
            align = direction
        
        # Korekta marginesów
        is_physical_odd = (i + 1) % 2 == 1
        
        if mirror_margins:
            if is_physical_odd:
                left_pt, right_pt = left_pt_base, right_pt_base
            else:
                left_pt, right_pt = right_pt_base, left_pt_base
        else:
            left_pt, right_pt = left_pt_base, right_pt_base
        
        # Obliczanie pozycji z uwzględnieniem rotacji
        x, y, angle = _calculate_position(
            rect, rotation, align, position,
            left_pt, right_pt, margin_v,
            text_width, font_size
        )
        
        # Wstawienie numeru
        page.insert_text(
            fitz.Point(x, y),
            text,
            fontsize=font_size,
            fontname=font,
            color=(0, 0, 0),
            rotate=angle
        )
        
        current_number += 1
    
    return len(selected_indices)


def _calculate_position(rect, rotation, align, position, left_pt, right_pt, margin_v, text_width, font_size):
    """Oblicza pozycję numeru strony z uwzględnieniem rotacji i wyrównania.
    
    Args:
        rect: Prostokąt strony (fitz.Rect)
        rotation: Kąt obrotu strony (0, 90, 180, 270)
        align: Wyrównanie ('lewa', 'prawa', 'srodek')
        position: Pozycja pionowa ('gora', 'dol')
        left_pt: Lewy margines w punktach
        right_pt: Prawy margines w punktach
        margin_v: Margines pionowy w punktach
        text_width: Szerokość tekstu w punktach
        font_size: Rozmiar czcionki
        
    Returns:
        tuple: (x, y, angle) - współrzędne i kąt obrotu tekstu
    """
    if rotation == 0:
        if align == "lewa":
            x = rect.x0 + left_pt
        elif align == "prawa":
            x = rect.x1 - right_pt - text_width
        else:  # srodek
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
        else:  # srodek
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
        else:  # srodek
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
        else:  # srodek
            total_height = rect.height
            margin_diff = left_pt - right_pt
            y = rect.y0 + (total_height / 2) - (text_width / 2) + (margin_diff / 2)
        
        x = rect.x1 - margin_v - font_size if position == "gora" else rect.x0 + margin_v
        angle = 270
    
    else:
        x = rect.x0 + left_pt
        y = rect.y1 - margin_v
        angle = 0
    
    return x, y, angle


def remove_page_numbers_from_pages(pdf_document, pages_to_process, top_mm, bottom_mm, mm_to_points):
    """Usuwa numery stron z określonych marginesów.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        pages_to_process: Lista indeksów stron do przetworzenia
        top_mm: Wysokość górnego marginesu w mm
        bottom_mm: Wysokość dolnego marginesu w mm
        mm_to_points: Współczynnik konwersji mm na punkty
        
    Returns:
        int: Liczba przetworzonych stron
    """
    top_pt = top_mm * mm_to_points
    bottom_pt = bottom_mm * mm_to_points
    
    modified_count = 0
    
    for page_index in pages_to_process:
        page = pdf_document.load_page(page_index)
        rect = page.rect
        
        # Definicja obszarów skanowania
        top_margin_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + top_pt)
        bottom_margin_rect = fitz.Rect(rect.x0, rect.y1 - bottom_pt, rect.x1, rect.y1)
        
        # Redakcja tekstów w marginesach
        redacted = False
        for area in [top_margin_rect, bottom_margin_rect]:
            redactions = page.search_for("", clip=area)
            if redactions or True:
                page.add_redact_annot(area, fill=(1, 1, 1))
                redacted = True
        
        if redacted:
            page.apply_redactions()
            modified_count += 1
    
    return modified_count
