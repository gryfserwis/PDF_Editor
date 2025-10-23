import sys
import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

OWNER_PASSWORD = "bK@92!fJ#Lp*Xz7$wQv%Tg^Rm&nH_Us+oIq=Zl[Wj]Eo{Aq};:Vx,Pb.<D>y|cS/0t1u2v3w4x5y6z7a8b9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X1Y2Z3AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"

def remove_gryf_watermark(reader):
    """
    Usuwa watermark GRYF z PDF przez usunięcie XObject o nazwie '/GRYF_WATERMARK' z każdej strony.
    
    Ta funkcja:
    - Bezpośrednio usuwa XObject watermarku po nazwie (nie szuka tekstu 'GRYF')
    - Nie maskuje tekstu ani nie używa redakcji
    - Jest odporna na brak watermarku (nie powoduje błędu)
    
    Args:
        reader: PdfReader object z załadowanym PDF
        
    Returns:
        True jeśli znaleziono i usunięto watermark, False jeśli watermark nie istniał
    """
    watermark_found = False
    
    # Iteruj przez wszystkie strony
    for page in reader.pages:
        try:
            # Sprawdź czy strona ma zasoby
            if '/Resources' not in page:
                continue
            
            resources = page['/Resources']
            
            # Sprawdź czy są XObjecty
            if '/XObject' not in resources:
                continue
            
            xobjects = resources['/XObject']
            
            # Sprawdź czy istnieje watermark GRYF
            watermark_name = NameObject('/GRYF_WATERMARK')
            if watermark_name in xobjects:
                # Usuń watermark XObject
                del xobjects[watermark_name]
                watermark_found = True
                
        except Exception as e:
            # Ignoruj błędy dla pojedynczych stron - kontynuuj przetwarzanie
            print(f"Ostrzeżenie: Nie można przetworzyć strony: {e}")
            continue
    
    return watermark_found

def remove_pdf_restrictions(pdf_path):
    """
    Usuwa restrykcje z PDF oraz watermark GRYF.
    
    Funkcja:
    1. Usuwa restrykcje drukowania/edycji (używając hasła właściciela)
    2. Usuwa watermark GRYF przez bezpośrednie usunięcie XObject '/GRYF_WATERMARK'
    3. Zapisuje oczyszczony PDF do tego samego pliku
    """
    try:
        # Wczytaj PDF z hasłem właściciela (jeśli jest zaszyfrowany)
        reader = PdfReader(pdf_path, password=OWNER_PASSWORD)
        filename = os.path.basename(pdf_path)
        
        # Jeśli PDF jest zaszyfrowany, odszyfruj go
        was_encrypted = False
        if reader.is_encrypted:
            if not reader.decrypt(OWNER_PASSWORD):
                raise ValueError("Nieprawidłowe hasło lub plik nie może zostać odszyfrowany.")
            was_encrypted = True
        
        # Usuń watermark GRYF z wszystkich stron
        watermark_removed = remove_gryf_watermark(reader)
        
        # Utwórz writer i skopiuj strony (bez restrykcji i watermarku)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        # Zapisz oczyszczony PDF (bez hasła i restrykcji)
        with open(pdf_path, "wb") as f:
            writer.write(f)
        
        # Przygotuj komunikat zwrotny
        messages = []
        if was_encrypted:
            messages.append("Ograniczenia usunięte")
        if watermark_removed:
            messages.append("Watermark GRYF usunięty")
        
        if messages:
            return f"{', '.join(messages)}: {filename}"
        else:
            return f"Plik nie był zabezpieczony ani nie miał watermarku: {filename}"
            
    except Exception as e:
        filename = os.path.basename(pdf_path)
        # Obsługa komunikatów o plikach niezaszyfrowanych
        if isinstance(e, ValueError) and "Not an encrypted file" in str(e):
            # Nawet jeśli nie był zaszyfrowany, spróbuj usunąć watermark
            try:
                reader = PdfReader(pdf_path)
                watermark_removed = remove_gryf_watermark(reader)
                if watermark_removed:
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    with open(pdf_path, "wb") as f:
                        writer.write(f)
                    return f"Watermark GRYF usunięty: {filename}"
                else:
                    return f"Plik nie był zabezpieczony ani nie miał watermarku: {filename}"
            except:
                return f"Plik nie był zabezpieczony: {filename}"
        if "Not an encrypted file" in str(e):
            # Nawet jeśli nie był zaszyfrowany, spróbuj usunąć watermark
            try:
                reader = PdfReader(pdf_path)
                watermark_removed = remove_gryf_watermark(reader)
                if watermark_removed:
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    with open(pdf_path, "wb") as f:
                        writer.write(f)
                    return f"Watermark GRYF usunięty: {filename}"
                else:
                    return f"Plik nie był zabezpieczony ani nie miał watermarku: {filename}"
            except:
                return f"Plik nie był zabezpieczony: {filename}"
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