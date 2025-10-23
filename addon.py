import sys
import os
import io
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF for watermark removal

OWNER_PASSWORD = "bK@92!fJ#Lp*Xz7$wQv%Tg^Rm&nH_Us+oIq=Zl[Wj]Eo{Aq};:Vx,Pb.<D>y|cS/0t1u2v3w4x5y6z7a8b9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X1Y2Z3AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"

def remove_watermark_from_page(page):
    """
    Usuwa watermark "GRYF" ze strony PDF używając PyMuPDF.
    
    Funkcja przeszukuje stronę w poszukiwaniu tekstu "GRYF" i usuwa go
    poprzez redakcję (redact annotations).
    
    Args:
        page: Obiekt strony PyMuPDF (fitz.Page)
        
    Returns:
        bool: True jeśli znaleziono i usunięto watermark, False w przeciwnym razie
    """
    try:
        # Szukaj wszystkich wystąpień tekstu "GRYF" na stronie
        text_instances = page.search_for("GRYF")
        
        if text_instances:
            # Dla każdego znalezionego wystąpienia dodaj adnotację redakcji
            for inst in text_instances:
                # Dodaj adnotację redakcji (usuwa tekst)
                page.add_redact_annot(inst, fill=(1, 1, 1))  # Biały kolor wypełnienia
            
            # Zastosuj wszystkie adnotacje redakcji
            page.apply_redactions()
            return True
        
        return False
    except Exception as e:
        print(f"Błąd podczas usuwania watermarku: {e}")
        return False

def remove_pdf_restrictions(pdf_path):
    """
    Usuwa restrykcje z pliku PDF oraz watermark "GRYF".
    
    Funkcja:
    1. Odszyfrowuje plik jeśli jest zaszyfrowany
    2. Usuwa watermark "GRYF" ze wszystkich stron
    3. Zapisuje plik bez restrykcji i watermarku
    
    Args:
        pdf_path: Ścieżka do pliku PDF
        
    Returns:
        str: Komunikat o wyniku operacji
    """
    try:
        filename = os.path.basename(pdf_path)
        
        # Krok 1: Odczytaj plik i usuń restrykcje używając pypdf
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Próbuj otworzyć z hasłem właściciela
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes), password=OWNER_PASSWORD)
            restrictions_removed = reader.is_encrypted
        except Exception:
            # Jeśli nie ma hasła, otwórz normalnie
            reader = PdfReader(io.BytesIO(pdf_bytes))
            restrictions_removed = False
        
        # Zapisz odszyfrowany PDF do bufora
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        decrypted_buffer = io.BytesIO()
        writer.write(decrypted_buffer)
        decrypted_pdf_bytes = decrypted_buffer.getvalue()
        
        # Krok 2: Usuń watermark z odszyfrowanego PDF używając PyMuPDF
        watermark_removed = False
        try:
            doc = fitz.open("pdf", decrypted_pdf_bytes)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                if remove_watermark_from_page(page):
                    watermark_removed = True
            
            # Zapisz finalny PDF
            final_pdf_bytes = doc.tobytes()
            doc.close()
            
            # Zapisz do pliku
            with open(pdf_path, "wb") as f:
                f.write(final_pdf_bytes)
            
        except Exception as e:
            # Jeśli nie udało się usunąć watermarku, zapisz odszyfrowany PDF
            print(f"Warning: Could not remove watermark: {e}")
            with open(pdf_path, "wb") as f:
                f.write(decrypted_pdf_bytes)
        
        # Przygotuj komunikat o wyniku
        if watermark_removed and restrictions_removed:
            return f"Usunięto watermark i ograniczenia: {filename}"
        elif watermark_removed:
            return f"Usunięto watermark: {filename}"
        elif restrictions_removed:
            return f"Ograniczenia usunięte: {filename}"
        else:
            return f"Plik nie był zabezpieczony ani nie zawierał watermarku: {filename}"
            
    except Exception as e:
        filename = os.path.basename(pdf_path)
        return f"Błąd: {e} ({filename})"

def on_drop(event):
    file_path = event.data.strip("{}")
    if file_path.lower().endswith(".pdf"):
        msg = remove_pdf_restrictions(file_path)
        label.config(text=msg)

def process_arg_file(pdf_path):
    if os.path.isfile(pdf_path) and pdf_path.lower().endswith(".pdf"):
        msg = remove_pdf_restrictions(pdf_path)
        print(msg)

if len(sys.argv) > 1:
    process_arg_file(sys.argv[1])
else:
    root = TkinterDnD.Tk()
    root.title("Usuń restrykcje PDF (drag & drop)")
    window_width = 400
    window_height = 200
    # Wyśrodkuj okno na ekranie
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(50, 50)
    # Okno zawsze na wierzchu
    root.attributes('-topmost', True)

    label = tk.Label(root, text="Przeciągnij plik PDF tutaj", font=("Arial", 12), wraplength=window_width-20, justify="center")
    label.pack(expand=True, fill="both")

    label.drop_target_register(DND_FILES)
    label.dnd_bind('<<Drop>>', on_drop)

    root.mainloop()