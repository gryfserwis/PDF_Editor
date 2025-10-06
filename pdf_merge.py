"""
Moduł pdf_merge.py - Scalanie stron i dokumentów PDF.

Zawiera funkcje do scalania wielu stron PDF w siatkę oraz łączenia
wielu plików PDF w jeden dokument.
"""

import fitz


def merge_pages_to_grid(pdf_document, selected_indices, params, mm_to_points):
    """Scala wybrane strony w siatkę na nowym arkuszu.
    
    Renderuje strony jako bitmapy w wysokiej rozdzielczości i umieszcza
    je w siatce na nowym arkuszu PDF.
    
    Args:
        pdf_document: Obiekt dokumentu PyMuPDF (fitz.Document)
        selected_indices: Lista indeksów stron do scalenia
        params: Słownik z parametrami scalania zawierający:
            - sheet_width_mm: Szerokość arkusza w mm
            - sheet_height_mm: Wysokość arkusza w mm
            - margin_top_mm: Górny margines w mm
            - margin_bottom_mm: Dolny margines w mm
            - margin_left_mm: Lewy margines w mm
            - margin_right_mm: Prawy margines w mm
            - spacing_x_mm: Odstęp poziomy w mm
            - spacing_y_mm: Odstęp pionowy w mm
            - rows: Liczba wierszy
            - cols: Liczba kolumn
            - dpi: DPI renderowania (domyślnie 600)
        mm_to_points: Współczynnik konwersji mm na punkty
        
    Returns:
        fitz.Page: Nowa strona z scalonymi obrazami
    """
    sheet_width_pt = params["sheet_width_mm"] * mm_to_points
    sheet_height_pt = params["sheet_height_mm"] * mm_to_points
    margin_top_pt = params["margin_top_mm"] * mm_to_points
    margin_bottom_pt = params["margin_bottom_mm"] * mm_to_points
    margin_left_pt = params["margin_left_mm"] * mm_to_points
    margin_right_pt = params["margin_right_mm"] * mm_to_points
    spacing_x_pt = params["spacing_x_mm"] * mm_to_points
    spacing_y_pt = params["spacing_y_mm"] * mm_to_points
    rows = params["rows"]
    cols = params["cols"]
    
    target_dpi = params.get("dpi", 600)
    pt_to_inch = 1 / 72
    
    total_cells = rows * cols
    num_pages = len(selected_indices)
    
    if num_pages == 1:
        source_pages = [selected_indices[0]] * total_cells
    else:
        source_pages = [selected_indices[i] if i < num_pages else None for i in range(total_cells)]
    
    # Oblicz rozmiar komórki
    if cols == 1:
        cell_width = sheet_width_pt - margin_left_pt - margin_right_pt
    else:
        cell_width = (sheet_width_pt - margin_left_pt - margin_right_pt - (cols - 1) * spacing_x_pt) / cols
    
    if rows == 1:
        cell_height = sheet_height_pt - margin_top_pt - margin_bottom_pt
    else:
        cell_height = (sheet_height_pt - margin_top_pt - margin_bottom_pt - (rows - 1) * spacing_y_pt) / rows
    
    new_page = pdf_document.new_page(width=sheet_width_pt, height=sheet_height_pt)
    
    for idx, src_idx in enumerate(source_pages):
        row = idx // cols
        col = idx % cols
        if row >= rows:
            break
        if src_idx is None:
            continue
        
        x = margin_left_pt + col * (cell_width + spacing_x_pt)
        y = margin_top_pt + row * (cell_height + spacing_y_pt)
        
        src_page = pdf_document[src_idx]
        page_rect = src_page.rect
        page_w = page_rect.width
        page_h = page_rect.height
        
        # Automatyczny obrót jeśli orientacja nie pasuje
        page_landscape = page_w > page_h
        cell_landscape = cell_width > cell_height
        rotate = 90 if page_landscape != cell_landscape else 0
        
        # Skala renderowania
        bitmap_w = int(round(cell_width * target_dpi * pt_to_inch))
        bitmap_h = int(round(cell_height * target_dpi * pt_to_inch))
        
        if rotate == 90:
            scale_x = bitmap_w / page_h
            scale_y = bitmap_h / page_w
        else:
            scale_x = bitmap_w / page_w
            scale_y = bitmap_h / page_h
        
        # Renderuj bitmapę
        pix = src_page.get_pixmap(matrix=fitz.Matrix(scale_x, scale_y).prerotate(rotate), alpha=False)
        img_bytes = pix.tobytes("png")
        rect = fitz.Rect(x, y, x + cell_width, y + cell_height)
        new_page.insert_image(rect, stream=img_bytes)
    
    return new_page
