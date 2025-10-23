import sys
import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from pypdf import PdfReader, PdfWriter

OWNER_PASSWORD = "bK@92!fJ#Lp*Xz7$wQv%Tg^Rm&nH_Us+oIq=Zl[Wj]Eo{Aq};:Vx,Pb.<D>y|cS/0t1u2v3w4x5y6z7a8b9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X1Y2Z3AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"

def remove_pdf_restrictions(pdf_path):
    try:
        reader = PdfReader(pdf_path, password=OWNER_PASSWORD)
        filename = os.path.basename(pdf_path)
        if reader.is_encrypted:
            if not reader.decrypt(OWNER_PASSWORD):
                raise ValueError("Nieprawidłowe hasło lub plik nie może zostać odszyfrowany.")
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(pdf_path, "wb") as f:
                writer.write(f)
            return f"Ograniczenia usunięte: {filename}"
        else:
            return f"Plik nie był zabezpieczony: {filename}"
    except Exception as e:
        filename = os.path.basename(pdf_path)
        if isinstance(e, ValueError) and "Not an encrypted file" in str(e):
            return f"Plik nie był zabezpieczony: {filename}"
        if "Not an encrypted file" in str(e):
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