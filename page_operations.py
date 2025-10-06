"""
Moduł page_operations.py - Operacje na stronach PDF.

Zawiera funkcje do kadrowania, przycinania, skalowania i zmiany rozmiaru
stron PDF oraz przesuwania zawartości.
"""

import io
import fitz
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
from utils import mm_to_pt


def crop_pages(pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm, 
               reposition=False, pos_mode="center", offset_x_mm=0, offset_y_mm=0):
    """Kadruje wybrane strony PDF z użyciem pypdf.
    
    Args:
        pdf_bytes: Bajty dokumentu PDF
        selected_indices: Zestaw indeksów stron do kadrowania
        top_mm: Górny margines w mm
        bottom_mm: Dolny margines w mm
        left_mm: Lewy margines w mm
        right_mm: Prawy margines w mm
        reposition: Czy przesuwać zawartość
        pos_mode: Tryb pozycjonowania ('center' lub 'custom')
        offset_x_mm: Przesunięcie X w mm
        offset_y_mm: Przesunięcie Y w mm
        
    Returns:
        bytes: Zmodyfikowany dokument PDF
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        if i not in selected_indices:
            writer.add_page(page)
            continue
        
        orig_mediabox = RectangleObject([float(v) for v in page.mediabox])
        x0, y0, x1, y1 = [float(v) for v in orig_mediabox]
        new_x0 = x0 + mm_to_pt(left_mm)
        new_y0 = y0 + mm_to_pt(bottom_mm)
        new_x1 = x1 - mm_to_pt(right_mm)
        new_y1 = y1 - mm_to_pt(top_mm)
        
        if new_x0 >= new_x1 or new_y0 >= new_y1:
            writer.add_page(page)
            continue
        
        new_rect = RectangleObject([new_x0, new_y0, new_x1, new_y1])
        
        page.cropbox = new_rect
        page.trimbox = new_rect
        page.artbox = new_rect
        page.mediabox = orig_mediabox
        
        if reposition:
            dx = mm_to_pt(offset_x_mm) if pos_mode == "custom" else 0
            dy = mm_to_pt(offset_y_mm) if pos_mode == "custom" else 0
            if dx != 0 or dy != 0:
                transform = Transformation().translate(tx=dx, ty=dy)
                page.add_transformation(transform)
        
        writer.add_page(page)
    
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def mask_crop_pages(pdf_bytes, selected_indices, top_mm, bottom_mm, left_mm, right_mm):
    """Maskuje (białe wypełnienie) marginesy na wybranych stronach.
    
    Args:
        pdf_bytes: Bajty dokumentu PDF
        selected_indices: Zestaw indeksów stron do maskowania
        top_mm: Górny margines w mm
        bottom_mm: Dolny margines w mm
        left_mm: Lewy margines w mm
        right_mm: Prawy margines w mm
        
    Returns:
        bytes: Zmodyfikowany dokument PDF
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    mm_to_points = 72 / 25.4
    
    for i in selected_indices:
        page = doc[i]
        rect = page.rect
        
        left_pt = left_mm * mm_to_points
        right_pt = right_mm * mm_to_points
        top_pt = top_mm * mm_to_points
        bottom_pt = bottom_mm * mm_to_points
        
        if left_pt > 0:
            mask_rect = fitz.Rect(rect.x0, rect.y0, rect.x0 + left_pt, rect.y1)
            page.draw_rect(mask_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        
        if right_pt > 0:
            mask_rect = fitz.Rect(rect.x1 - right_pt, rect.y0, rect.x1, rect.y1)
            page.draw_rect(mask_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        
        if top_pt > 0:
            mask_rect = fitz.Rect(rect.x0, rect.y1 - top_pt, rect.x1, rect.y1)
            page.draw_rect(mask_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        
        if bottom_pt > 0:
            mask_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + bottom_pt)
            page.draw_rect(mask_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
    
    output_bytes = doc.write()
    doc.close()
    return output_bytes


def resize_pages_with_scale(pdf_bytes, selected_indices, width_mm, height_mm):
    """Zmienia rozmiar stron ze skalowaniem zawartości.
    
    Args:
        pdf_bytes: Bajty dokumentu PDF
        selected_indices: Zestaw indeksów stron do skalowania
        width_mm: Docelowa szerokość w mm
        height_mm: Docelowa wysokość w mm
        
    Returns:
        bytes: Zmodyfikowany dokument PDF
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    target_width = mm_to_pt(width_mm)
    target_height = mm_to_pt(height_mm)
    
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


def resize_pages_no_scale(pdf_bytes, selected_indices, width_mm, height_mm, 
                          pos_mode="center", offset_x_mm=0, offset_y_mm=0):
    """Zmienia rozmiar stron bez skalowania zawartości.
    
    Args:
        pdf_bytes: Bajty dokumentu PDF
        selected_indices: Zestaw indeksów stron do zmiany rozmiaru
        width_mm: Docelowa szerokość w mm
        height_mm: Docelowa wysokość w mm
        pos_mode: Tryb pozycjonowania ('center' lub 'custom')
        offset_x_mm: Przesunięcie X w mm
        offset_y_mm: Przesunięcie Y w mm
        
    Returns:
        bytes: Zmodyfikowany dokument PDF
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    target_width = mm_to_pt(width_mm)
    target_height = mm_to_pt(height_mm)
    
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
            dx = mm_to_pt(offset_x_mm)
            dy = mm_to_pt(offset_y_mm)
        
        transform = Transformation().translate(tx=dx, ty=dy)
        page.add_transformation(transform)
        page.mediabox = RectangleObject([0, 0, target_width, target_height])
        page.cropbox = RectangleObject([0, 0, target_width, target_height])
        writer.add_page(page)
    
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def shift_page_content(pdf_bytes, pages_to_shift, dx_mm, dy_mm):
    """Przesuwa zawartość wybranych stron.
    
    Args:
        pdf_bytes: Bajty dokumentu PDF
        pages_to_shift: Zestaw indeksów stron do przesunięcia
        dx_mm: Przesunięcie w poziomie w mm
        dy_mm: Przesunięcie w pionie w mm
        
    Returns:
        bytes: Zmodyfikowany dokument PDF
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    final_dx = mm_to_pt(dx_mm)
    final_dy = mm_to_pt(dy_mm)
    transform = Transformation().translate(tx=final_dx, ty=final_dy)
    
    for i, page in enumerate(reader.pages):
        if i in pages_to_shift:
            page.add_transformation(transform)
        writer.add_page(page)
    
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
