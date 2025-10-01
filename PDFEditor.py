import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz
from PIL import Image, ImageTk
import io
import math 
import os
import sys 
import re 
from typing import Optional, List, Set, Dict, Union
from datetime import date 
import pypdf

# Definicja BASE_DIR i inne stałe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FOLDER = os.path.join(BASE_DIR, "icons")
FOCUS_HIGHLIGHT_COLOR = "#000000" # Czarny (Black)
FOCUS_HIGHLIGHT_WIDTH = 2        # Szerokość ramki fokusu (stała)

# DANE PROGRAMU
PROGRAM_TITLE = "GRYF PDF Editor" 
PROGRAM_VERSION = "2.5.1"
PROGRAM_DATE = date.today().strftime("%Y-%m-%d")

# === STAŁE DLA A4 (w punktach PDF i mm) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89
MM_TO_POINTS = 72 / 25.4 # ~2.8346

# === STAŁE KOLORY NARZĘDZIOWE (jeśli ich nie masz) ===
# Musisz zdefiniować te kolory, jeśli ich nie masz, dla przycisku importu
BG_IMPORT = "#F0AD4E" # np. Jakiś pomarańczowy dla importu
GRAY_FG = "#555555" # Jeśli używasz tego dla ikon

COPYRIGHT_INFO = (
    "Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.\n\n"
    "Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie "
    "programu bez pisemnej zgody autora jest zabronione."
)

# === STAŁE KOLORYSTYKA DLA SPOJNOSCI ===
BG_PRIMARY = '#F0F0F0'  # Główne tło okien i dialogów
BG_SECONDARY = '#E0E0E0' # Tło paneli kontrolnych/przycisków
BG_BUTTON_DEFAULT = "#D0D0D0" # Domyślny kolor przycisków
FG_TEXT = "#444444" # Kolor tekstu na przyciskach

# === STAŁE DLA A4 (w punktach PDF) ===
A4_WIDTH_POINTS = 595.276 
A4_HEIGHT_POINTS = 841.89

def resource_path(relative_path):
    """
    Tworzy poprawną ścieżkę do zasobów (logo, ikony itp.).
    Działa w trybie deweloperskim i po spakowaniu PyInstallerem.
    """
    try:
        # Aplikacja spakowana (PyInstaller --onefile)
        base_path = sys._MEIPASS
    except AttributeError:
        # Tryb deweloperski (po prostu katalog skryptu)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)

class ImageImportSettingsDialog(tk.Toplevel):
    def __init__(self, parent, title, image_path):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.image_path = image_path
        self.result = None
        
        self.image_pixel_width, self.image_pixel_height = 0, 0
        self.image_dpi = 96
        
        try:
            img = Image.open(image_path)
            self.image_pixel_width, self.image_pixel_height = img.size
            dpi_info = img.info.get('dpi', (96, 96))
            self.image_dpi = dpi_info[0] if isinstance(dpi_info, tuple) else 96
            img.close()
        except Exception:
            pass 

        # --- ZMIENNE KLASY ---
        self.scaling_mode = tk.StringVar(value="DOPASUJ")
        self.alignment_mode = tk.StringVar(value="SRODEK")
        self.scale_factor = tk.DoubleVar(value=100.0)
        self.page_orientation = tk.StringVar(value="PIONOWO")
        
        # --- TWORZENIE WIDŻETÓW (POZWALA NA WYLICZENIE WYSOKOŚCI) ---
        self.initial_focus = self.body()
        self.buttonbox() 
        self.update_scale_controls()
        
        # --- USTAWIENIE GEOMETRII I CENTROWANIE (POPRAWIONE) ---
        
        # 1. Wymuszenie rysowania i wylizenie rozmiaru
        self.update_idletasks() 
        
        # 2. Używamy stałej szerokości, ale bierzemy wylaną wysokość
        dialog_width = 450
        dialog_height = self.winfo_height() # Używamy wysokości dopasowanej do zawartości
        
        # 3. Obliczanie centrowania
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        
        x = parent_x + parent_width // 2 - dialog_width // 2
        y = parent_y + parent_height // 2 - dialog_height // 2
        
        # 4. Zastosowanie geometrii
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.resizable(False, False)
        self.grab_set()
        
        # --- FINALIZACJA ---
        if self.initial_focus: self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self):
        # ... (metoda body() bez zmian) ...
        main_frame = tk.Frame(self, bg=BG_PRIMARY, padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # Sekcja 1: Informacje o obrazie
        info_frame = tk.LabelFrame(main_frame, text="Informacje o obrazie źródłowym", bg=BG_PRIMARY, fg=FG_TEXT, padx=10, pady=5)
        info_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(info_frame, text=f"Wymiary: {self.image_pixel_width} x {self.image_pixel_height} px", anchor="w", bg=BG_PRIMARY, fg=FG_TEXT).pack(fill='x')
        tk.Label(info_frame, text=f"DPI: {self.image_dpi}", anchor="w", bg=BG_PRIMARY, fg=FG_TEXT).pack(fill='x')

        # Sekcja 2: Orientacja strony A4
        orient_frame = tk.LabelFrame(main_frame, text="Orientacja strony docelowej (A4)", bg=BG_PRIMARY, fg=FG_TEXT, padx=10, pady=5)
        orient_frame.pack(fill='x', pady=(0, 10))
        
        tk.Radiobutton(orient_frame, text="Pionowo", variable=self.page_orientation, value="PIONOWO", bg=BG_PRIMARY, fg=FG_TEXT, selectcolor=BG_PRIMARY).pack(anchor="w")
        tk.Radiobutton(orient_frame, text="Poziomo", variable=self.page_orientation, value="POZIOMO", bg=BG_PRIMARY, fg=FG_TEXT, selectcolor=BG_PRIMARY).pack(anchor="w")

        # Sekcja 3: Skalowanie
        scale_frame = tk.LabelFrame(main_frame, text="Ustawienia Skalowania", bg=BG_PRIMARY, fg=FG_TEXT, padx=10, pady=5)
        scale_frame.pack(fill='x', pady=(0, 10))
        
        options = [
            ("Dopasuj do strony A4", "DOPASUJ"),
            ("Oryginalny rozmiar (100%)", "ORYGINALNY"), 
            ("Skala niestandardowa", "SKALA")
        ]
        
        for text, value in options:
            rb = tk.Radiobutton(scale_frame, text=text, variable=self.scaling_mode, value=value, 
                                 command=self.update_scale_controls, bg=BG_PRIMARY, fg=FG_TEXT, selectcolor=BG_PRIMARY)
            rb.pack(anchor="w")

        self.scale_entry_frame = tk.Frame(scale_frame, bg=BG_PRIMARY)
        self.scale_entry_frame.pack(fill='x', pady=5, padx=20)
        tk.Label(self.scale_entry_frame, text="Skala (%):", bg=BG_PRIMARY, fg=FG_TEXT).pack(side=tk.LEFT)
        self.scale_entry = tk.Entry(self.scale_entry_frame, textvariable=self.scale_factor, width=8, relief=tk.FLAT, bd=1)
        self.scale_entry.pack(side=tk.LEFT, padx=5)

        # Sekcja 4: Wyrównanie
        align_frame = tk.LabelFrame(main_frame, text="Wyrównanie na stronie", bg=BG_PRIMARY, fg=FG_TEXT, padx=10, pady=5)
        align_frame.pack(fill='x')

        align_options = [
            ("Środek strony", "SRODEK"),
            ("Góra", "GORA"),
            ("Dół", "DOL")
        ]
        
        for text, value in align_options:
            mapped_value = value if value in ("SRODEK", "GORA") else "DOL" 
            rb = tk.Radiobutton(align_frame, text=text, variable=self.alignment_mode, value=mapped_value, bg=BG_PRIMARY, fg=FG_TEXT, selectcolor=BG_PRIMARY)
            rb.pack(anchor="w")
            
        return self.scale_entry
    
    def update_scale_controls(self):
        # ... (metoda update_scale_controls() bez zmian) ...
        if self.scaling_mode.get() == "SKALA":
            self.scale_entry.config(state=tk.NORMAL)
        else:
            self.scale_entry.config(state=tk.DISABLED)

    def buttonbox(self):
        # NOWA RAMKA dla przycisków, używamy pakowania na środek
        box = tk.Frame(self, bg=BG_PRIMARY)
        
        # Ramka wewnątrz, aby wyśrodkować przyciski w poziomie
        center_frame = tk.Frame(box, bg=BG_PRIMARY)
        center_frame.pack(expand=True, padx=5, pady=5) # Pakowanie ramki centującej na środku ramki "box"
        
        # Przycisk "Importuj" (pakowany pierwszy po lewej, by był pierwszy)
        tk.Button(center_frame, text="Importuj", width=12, command=self.ok, default=tk.ACTIVE, 
                  bg=BG_BUTTON_DEFAULT, fg=FG_TEXT, relief=tk.FLAT, bd=0).pack(
                      side=tk.LEFT, padx=5)
        
        # Przycisk "Anuluj" (pakowany drugi po lewej)
        tk.Button(center_frame, text="Anuluj", width=12, command=self.cancel, 
                  bg=BG_BUTTON_DEFAULT, fg=FG_TEXT, relief=tk.FLAT, bd=0).pack(
                      side=tk.LEFT, padx=5)
        
        # Pakowanie ramki przycisków na dole okna dialogowego
        box.pack(fill=tk.X, pady=(0, 5)) 
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())

    def ok(self, event=None):
        # ... (metoda ok() bez zmian) ...
        if self.scaling_mode.get() == "SKALA":
             try:
                 scale_val = self.scale_factor.get()
                 if not (0.1 <= scale_val <= 1000):
                     messagebox.showerror("Błąd", "Skala musi być wartością liczbową od 0.1 do 1000%.", parent=self)
                     self.scale_entry.focus_set()
                     return
             except tk.TclError:
                 messagebox.showerror("Błąd", "Wprowadź poprawną wartość liczbową skali.", parent=self)
                 self.scale_entry.focus_set()
                 return
                 
        self.result = {
            'scaling_mode': self.scaling_mode.get(),
            'scale_factor': self.scale_factor.get() / 100,
            'alignment': self.alignment_mode.get(),
            'page_orientation': self.page_orientation.get(),
            'image_dpi': self.image_dpi
        }
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()



# ====================================================================
# KLASA: OKNO DIALOGOWE WYBORU ZAKRESU STRON (Bez zmian)
# ====================================================================

class EnhancedPageRangeDialog(tk.Toplevel):
    def __init__(self, parent, title, imported_doc: fitz.Document):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.imported_doc = imported_doc
        
        try:
             self.max_pages = len(imported_doc)
        except ValueError:
             self.max_pages = 0
             messagebox.showerror("Błąd", "Dokument PDF został zamknięty przed otwarciem dialogu.")
             self.destroy()
             self.result = None
             return
             
        self.result = None
        
        # Stylizacja i geometria (skrócono dla czytelności)
        self.configure(bg=BG_PRIMARY) 
        dialog_width, dialog_height = 300, 150
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        x = parent_x + parent_width // 2 - dialog_width // 2
        y = parent_y + parent_height // 2 - dialog_height // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.grab_set()
        self.initial_focus = self.body()
        self.buttonbox()
        
        if self.initial_focus:
             self.initial_focus.focus_set()
             
        self.wait_window(self)


    def body(self):
        main_frame = tk.Frame(self, bg=BG_PRIMARY)
        main_frame.pack(padx=5, pady=5, fill="both", expand=True)
        range_frame = tk.Frame(main_frame, bg=BG_PRIMARY)
        range_frame.pack(fill='x', expand=True, pady=(2, 0)) 
        
        tk.Label(range_frame, text=f"Zakres stron do importu (1 - {self.max_pages}):", anchor="w", font=("Helvetica", 10, "bold"), bg=BG_PRIMARY).pack(fill='x', pady=(0, 2))
        self.entry = tk.Entry(range_frame, relief=tk.FLAT, bd=2)
        self.entry.pack(pady=2, fill='x')
        tk.Label(range_frame, text="Format: 1, 3-5, 7", fg="gray", anchor="w", bg=BG_PRIMARY).pack(fill='x', pady=(2, 0))
        button_frame = tk.Frame(range_frame, bg=BG_PRIMARY)
        button_frame.pack(pady=(2, 0), fill='x') 
        
        tk.Button(button_frame, text="Wszystkie strony", 
                  command=lambda: self.entry.delete(0, tk.END) or self.entry.insert(0, f"1-{self.max_pages}"), 
                  bg=BG_BUTTON_DEFAULT, relief=tk.FLAT, bd=1).pack(padx=1, pady=1) 
                  
        return self.entry 
    
    def buttonbox(self):
        box = tk.Frame(self, bg=BG_PRIMARY)
        tk.Button(box, text="Importuj", width=12, command=self.ok, default=tk.ACTIVE, 
                  bg=BG_BUTTON_DEFAULT, fg=FG_TEXT, relief=tk.FLAT, bd=0).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(box, text="Anuluj", width=12, command=self.cancel, 
                  bg=BG_BUTTON_DEFAULT, fg=FG_TEXT, relief=tk.FLAT, bd=1).pack(side=tk.LEFT, padx=5, pady=5)
        box.pack(pady=(0, 5)) 
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", lambda e: self.cancel())

    def ok(self, event=None):
        raw_range = self.entry.get().strip()
        if not raw_range:
            messagebox.showerror("Błąd", "Wprowadź zakres stron.", parent=self)
            self.entry.focus_set()
            return
            
        page_indices = self._parse_range(raw_range)
        if page_indices is None:
            messagebox.showerror("Błąd formatu", "Niepoprawny format zakresu. Użyj np. 1, 3-5, 7.", parent=self)
            self.entry.focus_set()
            return
            
        self.result = page_indices
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()
        
    def _parse_range(self, raw_range: str) -> Optional[List[int]]:
        selected_pages = set()
        if not re.fullmatch(r'[\d,\-\s]+', raw_range):
             return None
        parts = raw_range.split(',')
        for part in parts:
            part = part.strip()
            if not part: continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    start = max(1, start)
                    end = min(self.max_pages, end)
                    if start > end: continue
                    for page_num in range(start, end + 1):
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None 
            else:
                try:
                    page_num = int(part)
                    if 1 <= page_num <= self.max_pages:
                        selected_pages.add(page_num - 1)
                except ValueError:
                    return None 
        return sorted(list(selected_pages))

# ====================================================================
# KLASA: RAMKA MINIATURY (Bez zmian)
# ====================================================================

class ThumbnailFrame(tk.Frame):
    def __init__(self, parent, viewer_app, page_index, column_width):
        super().__init__(parent, bg="#F5F5F5") 
        self.page_index = page_index
        self.viewer_app = viewer_app
        self.column_width = column_width
        self.bg_normal = "#F5F5F5"
        self.bg_selected = "#B3E5FC"
        self.outer_frame = tk.Frame(
            self, 
            bg=self.bg_normal, 
            borderwidth=0, 
            relief=tk.FLAT,
            highlightthickness=FOCUS_HIGHLIGHT_WIDTH, 
            highlightbackground=self.bg_normal 
        )
        self.outer_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.img_label = None 
        self.setup_ui(self.outer_frame)

    def _bind_all_children(self, sequence, func):
        self.bind(sequence, func)
        self.outer_frame.bind(sequence, func)
        for child in self.outer_frame.winfo_children():
            child.bind(sequence, func)
            if child.winfo_class() == 'Frame':
                 for grandchild in child.winfo_children():
                     grandchild.bind(sequence, func)

    def setup_ui(self, parent_frame):
        img_tk = self.viewer_app._render_and_scale(self.page_index, self.column_width)
        self.viewer_app.tk_images[self.page_index] = img_tk
        
        image_container = tk.Frame(parent_frame, bg="white") 
        image_container.pack(padx=5, pady=(5, 0))
        
        self.img_label = tk.Label(image_container, image=img_tk, bg="white")
        self.img_label.pack() 
        
        tk.Label(parent_frame, text=f"Strona {self.page_index + 1}", bg=self.bg_normal, font=("Helvetica", 10, "bold")).pack(pady=(5, 0))
        
        format_label = self.viewer_app._get_page_size_label(self.page_index)
        tk.Label(parent_frame, text=format_label, fg="gray", bg=self.bg_normal, font=("Helvetica", 9)).pack(pady=(0, 5))

        self._bind_all_children("<Button-1>", lambda event, idx=self.page_index: self.viewer_app._handle_lpm_click(idx, event))

        self._bind_all_children("<Button-3>", lambda event, idx=self.page_index: self._handle_ppm_click(event, idx))

    def _handle_ppm_click(self, event, page_index):
        self.viewer_app.active_page_index = page_index
        
        if page_index not in self.viewer_app.selected_pages:
             self.viewer_app.selected_pages.clear()
             self.viewer_app.selected_pages.add(page_index)
             self.viewer_app.update_selection_display()
        
        self.viewer_app.update_focus_display(hide_mouse_focus=True) 
        self.viewer_app.context_menu.tk_popup(event.x_root, event.y_root)

# ====================================================================
# GŁÓWNA KLASA PROGRAMU: SELECTABLEPDFVIEWER
# ====================================================================

class SelectablePDFViewer:
    
    def _apply_selection_by_indices(self, indices_to_select):
        """Ogólna metoda do zaznaczania stron na podstawie listy indeksów."""
        if not self.pdf_document:
            return

        current_selection = self.selected_pages.copy()
        
        # Tworzenie nowej, czystej selekcji
        new_selection = set(indices_to_select)
        
        # Zastąpienie dotychczasowej selekcji
        self.selected_pages = new_selection
        
        # Przerenderowanie, jeśli selekcja się zmieniła
        if current_selection != self.selected_pages:
            
            # === POPRAWKA ===
            # Właściwa metoda do odświeżania widoku po zmianie zaznaczenia:
            self.update_selection_display()
            # ================
            self.update_tool_button_states()
            
    def _select_odd_pages(self):
        """Zaznacza strony nieparzyste (indeksy 0, 2, 4...)."""
        if not self.pdf_document: return
        
        # W Pythonie indeksy są od 0, więc strony nieparzyste mają indeksy parzyste (0, 2, 4...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 == 0]
        self._apply_selection_by_indices(indices)

    def _select_even_pages(self):
        """Zaznacza strony parzyste (indeksy 1, 3, 5...)."""
        if not self.pdf_document: return

        # Strony parzyste mają indeksy nieparzyste (1, 3, 5...)
        indices = [i for i in range(len(self.pdf_document)) if i % 2 != 0]
        self._apply_selection_by_indices(indices)

    def _select_portrait_pages(self):
        """Zaznacza strony pionowe (wysokość > szerokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy wysokość bounding boxu jest większa niż szerokość
            if page.rect.height > page.rect.width:
                indices.append(i)
        self._apply_selection_by_indices(indices)
        
    def _select_landscape_pages(self):
        """Zaznacza strony poziome (szerokość >= wysokość)."""
        if not self.pdf_document: return
        
        indices = []
        for i in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(i)
            # Sprawdzenie, czy szerokość bounding boxu jest większa lub równa wysokości
            if page.rect.width >= page.rect.height:
                indices.append(i)
        self._apply_selection_by_indices(indices)
    
    def export_selected_pages_to_image(self):
        """Eksportuje wybrane strony do plików PNG o wysokiej rozdzielczości."""
        
        selected_indices = sorted(list(self.selected_pages))
        
        if not selected_indices:
            messagebox.showinfo("Informacja", "Wybierz strony do eksportu.")
            return

        output_dir = filedialog.askdirectory(
            title="Wybierz folder do zapisu wyeksportowanych obrazów"
        )
        
        if not output_dir:
            return

        try:
            # Ustawienia eksportu
            zoom = 300 / 72.0 
            matrix = fitz.Matrix(zoom, zoom)
            
            # POPRAWKA BŁĘDU: Bezpieczne pobieranie nazwy bazowej
            # Jeśli self.file_path istnieje, użyj jego nazwy. W przeciwnym razie, użyj "export".
            if hasattr(self, 'file_path') and self.file_path:
                base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
            else:
                base_filename = "export"
            
            exported_count = 0
            
            self.master.config(cursor="wait")
            self.master.update()
            
            for index in selected_indices:
                if index < len(self.pdf_document):
                    page = self.pdf_document.load_page(index)
                    
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    
                    # Budowanie nazwy pliku: "nazwa_dokumentu_strona_X.png"
                    output_filename = f"{base_filename}_strona_{index + 1}.png"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    pix.save(output_path)
                    exported_count += 1
            
            self.master.config(cursor="")
            
        #    messagebox.showinfo(
        #        "Sukces Eksportu", 
        #        f"Pomyślnie wyeksportowano {exported_count} stron do folderu:\n{output_dir}"
        #    )
            self._update_status(f"Pomyślnie wyeksportowano {exported_count} stron do folderu: {output_dir}")   
        except Exception as e:
            self.master.config(cursor="")
            messagebox.showerror("Błąd Eksportu", f"Wystąpił błąd podczas eksportowania stron:\n{e}")
            
            
    
    
    def __init__(self, master):
        self.master = master
        master.title(PROGRAM_TITLE) 
        
        master.protocol("WM_DELETE_WINDOW", self.on_close_window) 

        self.pdf_document = None
        self.selected_pages: Set[int] = set()
        self.tk_images: Dict[int, ImageTk.PhotoImage] = {}
        self.icons: Dict[str, Union[ImageTk.PhotoImage, str]] = {} 
        
        self.thumb_frames: Dict[int, 'ThumbnailFrame'] = {}
        self.active_page_index = 0 

        self.clipboard: Optional[bytes] = None 
        self.pages_in_clipboard_count: int = 0 
        
        self.fixed_thumb_width = 250  
        self.min_zoom_width = 150    
        self.THUMB_PADDING = 8       
        self.ZOOM_FACTOR = 0.9       
        self.target_num_cols = 4     
        self.min_cols = 2            
        self.max_cols = 10           
        self.MIN_WINDOW_WIDTH = 950    
        self.render_dpi_factor = 0.833 
        
        self.history: List[bytes] = []
        self.max_history_size = 10 
        
        self._set_initial_geometry() 
        self._load_icons_or_fallback(size=28) 
        self._create_menu() 
        self._setup_context_menu() 
        self._setup_key_bindings() 
        
        GRAY_BG = BG_BUTTON_DEFAULT    
        GRAY_FG = FG_TEXT
        
        self.BG_OPEN = GRAY_BG     
        self.BG_SAVE = GRAY_BG     
        self.BG_UNDO = GRAY_BG     
        self.BG_DELETE = GRAY_BG   
        self.BG_INSERT = GRAY_BG   
        self.BG_ROTATE = GRAY_BG
        self.BG_CLIPBOARD = GRAY_BG 
        
        self.BG_IMPORT = GRAY_BG
        self.BG_EXPORT = GRAY_BG

        main_control_panel = tk.Frame(master, bg=BG_SECONDARY, padx=10, pady=5) 
        main_control_panel.pack(side=tk.TOP, fill=tk.X)
        
        tools_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        tools_frame.pack(side=tk.LEFT, fill=tk.Y)

        ICON_WIDTH = 3
        ICON_FONT = ("Arial", 14)
        PADX_SMALL = 5
        PADX_LARGE = 15
        
        def create_tool_button(parent, key, command, bg_color, fg_color="#333", state=tk.NORMAL, padx=(0, PADX_SMALL)):
            icon = self.icons[key]
            
            # NOWA LOGIKA: Zwiększenie czytelności przycisku
            btn_text = ""
                        
            common_config = {
                'command': command,
                'state': state,
                'bg': bg_color,
                'relief': tk.RAISED,
                'bd': 1,
            }

            if isinstance(icon, ImageTk.PhotoImage):
                 # Jeśli używamy ikon graficznych, używamy ich
                 btn = tk.Button(parent, image=icon, **common_config)
                 btn.image = icon 
            else:
                 # Jeśli używamy emoji/tekstu zastępczego, używamy dłuższej formy dla czytelności
                 if btn_text:
                     btn = tk.Button(parent, text=btn_text, font=("Arial", 9, "bold"), fg=fg_color, **common_config)
                 else:
                     btn = tk.Button(parent, text=icon, width=ICON_WIDTH, font=ICON_FONT, fg=fg_color, **common_config)
            
            btn.pack(side=tk.LEFT, padx=padx)
            return btn

        # 1. PRZYCISKI PLIK/ZAPISZ/IMPORT/EKSPORT/COFNIJ
        self.open_button = create_tool_button(tools_frame, 'open', self.open_pdf, self.BG_OPEN, GRAY_FG, padx=(5, PADX_SMALL)) 
        
        self.save_button_icon = create_tool_button(tools_frame, 'save', self.save_document, self.BG_SAVE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU PDF 
        self.import_button = create_tool_button(tools_frame, 'import', self.import_pdf_after_active_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.extract_button = create_tool_button(tools_frame, 'export', self.extract_selected_pages, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # PRZYCISK IMPORTU OBRAZU 
        self.image_import_button = create_tool_button(tools_frame, 'image_import', self.import_image_to_new_page, self.BG_IMPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.export_image_button = create_tool_button(tools_frame, 'export_image', self.export_selected_pages_to_image, self.BG_EXPORT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE))
        
        self.undo_button = create_tool_button(tools_frame, 'undo', self.undo_last_action, self.BG_UNDO, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        # 2. PRZYCISKI EDYCJI STRON
        self.delete_button = create_tool_button(tools_frame, 'delete', self.delete_selected_pages, self.BG_DELETE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        # 3. PRZYCISKI WYCINAJ/KOPIUJ/WKLEJ
        self.cut_button = create_tool_button(tools_frame, 'cut', self.cut_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.copy_button = create_tool_button(tools_frame, 'copy', self.copy_selected_pages, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        
        self.paste_before_button = create_tool_button(tools_frame, 'paste_b', self.paste_pages_before, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.paste_after_button = create_tool_button(tools_frame, 'paste_a', self.paste_pages_after, self.BG_CLIPBOARD, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.insert_before_button = create_tool_button(tools_frame, 'insert_b', self.insert_blank_page_before, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.insert_after_button = create_tool_button(tools_frame, 'insert_a', self.insert_blank_page_after, self.BG_INSERT, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_LARGE)) 
        
        self.rotate_left_button = create_tool_button(tools_frame, 'rotate_l', lambda: self.rotate_selected_page(-90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, PADX_SMALL)) 
        self.rotate_right_button = create_tool_button(tools_frame, 'rotate_r', lambda: self.rotate_selected_page(90), self.BG_ROTATE, GRAY_FG, state=tk.DISABLED, padx=(0, 20)) 


        # ZOOM 
        zoom_frame = tk.Frame(main_control_panel, bg=BG_SECONDARY)
        zoom_frame.pack(side=tk.RIGHT, padx=10)
        
        ZOOM_BG = GRAY_BG 
        ZOOM_FONT = ("Arial", 14, "bold") 
        ZOOM_WIDTH = 2
        
        self.zoom_in_button = create_tool_button(zoom_frame, 'zoom_in', self.zoom_in, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 2), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_in'], ImageTk.PhotoImage):
             self.zoom_in_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)

        self.zoom_out_button = create_tool_button(zoom_frame, 'zoom_out', self.zoom_out, ZOOM_BG, fg_color=GRAY_FG, padx=(2, 5), state=tk.DISABLED) 
        if not isinstance(self.icons['zoom_out'], ImageTk.PhotoImage):
             self.zoom_out_button.config(width=ZOOM_WIDTH, height=1, font=ZOOM_FONT)
        
        
        # Pasek statusu 
        self.status_bar = tk.Label(master, text="Gotowy. Otwórz plik PDF.", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0", fg="black")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


        self.canvas = tk.Canvas(master, bg="#F5F5F5") 
        self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F5F5F5") 
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.bind("<Configure>", self._reconfigure_grid) 
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True) 

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel) 
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        self.update_tool_button_states() 
        self._setup_drag_and_drop_file()

    # --- Metody obsługi GUI i zdarzeń (Bez zmian) ---
    def on_close_window(self):
        if self.pdf_document is not None and len(self.history) > 1:
            response = messagebox.askyesnocancel(
                "Niezapisane zmiany",
                "Czy chcesz zapisać zmiany w dokumencie przed zamknięciem programu?"
            )
            if response is None: 
                return
            elif response is True: 
                self.save_document() 
                if len(self.history) > 1:
                    return 
                self.master.quit() 
            else: 
                self.master.quit()
        else:
            self.master.quit()

    def _set_initial_geometry(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        initial_width = self.MIN_WINDOW_WIDTH
        initial_height = int(screen_height * 0.50)  
        self.master.minsize(self.MIN_WINDOW_WIDTH, initial_height)
        x_cordinate = int((screen_width / 2) - (initial_width / 2))
        y_cordinate = int((screen_height / 2) - (initial_height / 2))
        self.master.geometry(f"{initial_width}x{initial_height}+{x_cordinate}+{y_cordinate}")

    def _load_icons_or_fallback(self, size=28):
        icon_map = {
            'open': ('📂', "open.png"),
            'save': ('💾', "save.png"),
            'undo': ('↩️', "undo.png"),
            'delete': ('🗑️', "delete.png"),
            'cut': ('✂️', "cut.png"),  
            'copy': ('📋', "copy.png"),  
            'paste_b': ('⬆️📄', "paste_before.png"),  
            'paste_a': ('⬇️📄', "paste_after.png"),  
            'insert_b': ('⬆️➕', "insert_before.png"),  
            'insert_a': ('⬇️➕', "insert_after.png"),  
            'rotate_l': ('↺', "rotate_left.png"),
            'rotate_r': ('↻', "rotate_right.png"),
            'zoom_in': ('➖', "zoom_in.png"),  
            'zoom_out': ('➕', "zoom_out.png"),
            'export': ('📤', "export.png"), 
            'export_image': ('🖼️', "export_image.png"),
            'import': ('📥', "import.png"), # Import PDF
            'image_import': ('🖼️', "import_image.png"), # Import Obrazu
        }
        for key, (emoji, filename) in icon_map.items():
            try:
                path = os.path.join(ICON_FOLDER, filename)
                img = Image.open(path).convert("RGBA")
                self.icons[key] = ImageTk.PhotoImage(img.resize((size, size), Image.LANCZOS))
            except Exception:
                self.icons[key] = emoji

    def _create_menu(self):
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        self.file_menu = tk.Menu(menu_bar, tearoff=0)  
        menu_bar.add_cascade(label="Plik", menu=self.file_menu)
        self.file_menu.add_command(label="Otwórz PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Zapisz jako...", command=self.save_document, state=tk.DISABLED, accelerator="Ctrl+S")
        self.file_menu.add_separator() 
        self.file_menu.add_command(label="Importuj strony z PDF...", command=self.import_pdf_after_active_page, state=tk.DISABLED, accelerator="Ctrl+I") 
        self.file_menu.add_command(label="Eksportuj strony do PDF...", command=self.extract_selected_pages, state=tk.DISABLED,accelerator="Ctrl+E") 
        self.file_menu.add_separator() 
        self.file_menu.add_command(label="Importuj obraz na nową stronę...", command=self.import_image_to_new_page, state=tk.DISABLED, accelerator="Ctrl+Shift+I") 
        self.file_menu.add_command(label="Eksportuj strony jako obrazy PNG...", command=self.export_selected_pages_to_image, state=tk.DISABLED, accelerator="Ctrl+Shift+E")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Zamknij program", command=self.on_close_window)  

        select_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Zaznacz", menu=select_menu)
        select_menu.add_command(label="Wszystkie strony", command=self._select_all, accelerator="Ctrl+A")
        select_menu.add_separator()
        select_menu.add_command(label="Strony nieparzyste", command=self._select_odd_pages, state=tk.DISABLED)
        select_menu.add_command(label="Strony parzyste", command=self._select_even_pages, state=tk.DISABLED)
        select_menu.add_separator()
        select_menu.add_command(label="Strony pionowe", command=self._select_portrait_pages, state=tk.DISABLED)
        select_menu.add_command(label="Strony poziome", command=self._select_landscape_pages, state=tk.DISABLED)
        self.select_menu = select_menu
        
        self.edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edycja", menu=self.edit_menu)
        self._populate_edit_menu(self.edit_menu)
        
        self.help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Pomoc", menu=self.help_menu)
        self.help_menu.add_command(label="O programie", command=self.show_about_dialog)

    def show_about_dialog(self):
        PROGRAM_LOGO_PATH = resource_path(os.path.join('icons', 'logo.png'))
        # STAŁE WYMIARY OKNA
        DIALOG_WIDTH = 280
        DIALOG_HEIGHT = 260

        # 1. Inicjalizacja i Ustawienia Okna
        dialog = tk.Toplevel(self.master)
        dialog.title("O programie")
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}") # Ustawienie stałego rozmiaru
        dialog.resizable(False, False) # Zablokowanie zmiany rozmiaru
        
        # Ustawienia modalne
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.focus_set()
        
        # 2. Centralizacja Okna (Matematyczna, używając stałych)
        dialog.update_idletasks() # Wymuś odświeżenie dla bezpieczeństwa
        
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # Obliczenia bazujące na stałych
        position_top = int(screen_height / 2 - DIALOG_HEIGHT / 2)
        position_right = int(screen_width / 2 - DIALOG_WIDTH / 2)
        
        # Zastosowanie pozycji (nie zmieniamy rozmiaru w tym wywołaniu)
        dialog.geometry(f'+{position_right}+{position_top}')
        
        # --- Ramka Centrująca Treść ---
        main_frame = ttk.Frame(dialog)
        # Pack bez expand/fill sprawia, że treść jest mała i wyśrodkowana w stałym oknie
        main_frame.pack(padx=10, pady=10) 

        # 3. Dodanie Grafiki
        logo_path = PROGRAM_LOGO_PATH 
        self.tk_image = None 

        if logo_path:
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((60, 60), Image.Resampling.LANCZOS)
                
                self.tk_image = ImageTk.PhotoImage(pil_image)
                
                logo_label = ttk.Label(main_frame, image=self.tk_image)
                logo_label.pack(pady=(0, 5))
            except Exception as e:
                print(f"Błąd ładowania logo: {e}") 

        # 4. Dodanie Treści
        
        # Tytuł
        title_label = ttk.Label(main_frame, text=PROGRAM_TITLE, font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(2, 1))
        
        # Wersja
        version_label = ttk.Label(main_frame, text=f"Wersja: {PROGRAM_VERSION} (Data: {PROGRAM_DATE})", font=("Helvetica", 8))
        version_label.pack(pady=1)

        separator_frame = tk.Frame(main_frame, height=1, bg='lightgray')
        separator_frame.pack(fill='x', padx=15, pady=15)
        # Prawa Autorskie (Zmodyfikowano: czcionka 10, bez pogrubienia, dodano zawijanie)
        copy_label = ttk.Label(
        main_frame, 
        text=COPYRIGHT_INFO, 
        font=("Helvetica", 8),              # Czcionka 10, bez pogrubienia
        foreground="black",
        wraplength=250                       # Zawijanie tekstu po osiągnięciu 300 pikseli szerokości
        )
        copy_label.pack(pady=(5, 0))
        
        # 5. Blokowanie
        dialog.wait_window()
    
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self._populate_edit_menu(self.context_menu)
    
    def _populate_edit_menu(self, menu_obj):
        menu_obj.add_command(label="Cofnij", command=self.undo_last_action, accelerator="Ctrl+Z")
        menu_obj.add_separator()
        menu_obj.add_command(label="Usuń zaznaczone", command=self.delete_selected_pages, accelerator="Delete/Backspace")
        menu_obj.add_command(label="Wytnij zaznaczone", command=self.cut_selected_pages, accelerator="Ctrl+X")
        menu_obj.add_command(label="Kopiuj zaznaczone", command=self.copy_selected_pages, accelerator="Ctrl+C")
        menu_obj.add_command(label="Wklej przed", command=self.paste_pages_before, accelerator="Ctrl+Shift+V")
        menu_obj.add_command(label="Wklej po", command=self.paste_pages_after, accelerator="Ctrl+V")
        menu_obj.add_separator()
        menu_obj.add_command(label="Wstaw nową stronę przed", command=self.insert_blank_page_before, accelerator="Ctrl+Shift+N")
        menu_obj.add_command(label="Wstaw nową stronę po", command=self.insert_blank_page_after, accelerator="Ctrl+N")
        menu_obj.add_separator()
        menu_obj.add_command(label="Obróć w lewo (-90°)", command=lambda: self.rotate_selected_page(-90))
        menu_obj.add_command(label="Obróć w prawo (+90°)", command=lambda: self.rotate_selected_page(90))

    def _setup_key_bindings(self):
        self.master.bind('<Control-x>', lambda e: self.cut_selected_pages())
        self.master.bind('<Control-c>', lambda e: self.copy_selected_pages())
        self.master.bind('<Control-z>', lambda e: self.undo_last_action())
        self.master.bind('<Delete>', lambda e: self.delete_selected_pages())  
        self.master.bind('<BackSpace>', lambda e: self.delete_selected_pages())
        self.master.bind('<Control-a>', lambda e: self._select_all())
        self.master.bind('<Control-v>', lambda e: self.paste_pages_after())
        self.master.bind('<Control-Shift-V>', lambda e: self.paste_pages_before())
        self.master.bind('<Control-n>', lambda e: self.insert_blank_page_after())
        self.master.bind('<Control-Shift-N>', lambda e: self.insert_blank_page_before())
        # === SKRÓTY DLA EKSPORTU ===
        # Ctrl+E dla Eksportu stron do nowego PDF
        self.master.bind('<Control-e>', lambda e: self.extract_selected_pages())
        # Ctrl+Shift+E dla Eksportu stron jako obrazów PNG
        self.master.bind('<Control-Shift-E>', lambda e: self.export_selected_pages_to_image())
        # ===========================
        self._setup_focus_logic()
        self.master.bind('<Control-o>', lambda e: self.open_pdf())
        self.master.bind('<Control-s>', lambda e: self.save_document())
        # Zmienione skróty
        self.master.bind('<Control-Shift-I>', lambda e: self.import_image_to_new_page()) # Ctrl+K dla obrazu
        self.master.bind('<Control-i>', lambda e: self.import_pdf_after_active_page()) # Ctrl+I dla PDF
        
    def _setup_focus_logic(self):
        self.master.bind('<Escape>', lambda e: self._clear_all_selection())
        self.master.bind('<space>', lambda e: self._toggle_selection_space())
        self.master.bind('<Left>', lambda e: self._move_focus_and_scroll(-1))
        self.master.bind('<Right>', lambda e: self._move_focus_and_scroll(1))
        self.master.bind('<Up>', lambda e: self._move_focus_and_scroll(-self.target_num_cols))
        self.master.bind('<Down>', lambda e: self._move_focus_and_scroll(self.target_num_cols))

    def _select_all(self):
        if self.pdf_document:
            all_pages = set(range(len(self.pdf_document)))
            if self.selected_pages == all_pages:
                self.selected_pages.clear()
                self._update_status("Anulowano zaznaczenie wszystkich stron (Ctrl+A).")
            else:
                self.selected_pages = all_pages
                self._update_status(f"Zaznaczono wszystkie strony ({len(self.pdf_document)}).")
            if self.pdf_document.page_count > 0:
                self.active_page_index = 0
            self.update_selection_display()
            self.update_focus_display()
            
    def _select_range(self, start_index, end_index):
        if not self.pdf_document: return
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        self.selected_pages.clear() 
        for i in range(start_index, end_index + 1):
            if i < len(self.pdf_document):
                self.selected_pages.add(i)
        self.update_selection_display()
        self.active_page_index = end_index 
        
    def _clear_all_selection(self):
        if self.pdf_document:
            self.active_page_index = 0
        if self.selected_pages:
            self.selected_pages.clear()
            self.update_selection_display()
            self.update_focus_display()
            self._update_status("Anulowano zaznaczenie wszystkich stron (ESC).")
            
    def _toggle_selection_space(self):
        if self.pdf_document and self.pdf_document.page_count > 0:
            if self.active_page_index in self.selected_pages:
                self.selected_pages.remove(self.active_page_index)
            else:
                self.selected_pages.add(self.active_page_index)
            self.update_selection_display()

    def _get_page_frame(self, index) -> Optional['ThumbnailFrame']:
        return self.thumb_frames.get(index)

    def _move_focus_and_scroll(self, delta: int):
        if not self.pdf_document: return
        new_index = self.active_page_index + delta
        max_index = len(self.pdf_document) - 1
        if 0 <= new_index <= max_index:
            self.active_page_index = new_index
            self.update_focus_display(hide_mouse_focus=False)  
            frame = self._get_page_frame(self.active_page_index)
            if frame:
                self.canvas.update_idletasks()
                y1 = frame.winfo_y()
                y2 = frame.winfo_y() + frame.winfo_height()
                bbox = self.canvas.bbox("all")
                total_height = bbox[3] if bbox is not None else 1
                norm_top = y1 / total_height
                norm_bottom = y2 / total_height
                current_top, current_bottom = self.canvas.yview()
                if norm_top < current_top:
                    self.canvas.yview_moveto(norm_top)
                elif norm_bottom > current_bottom:
                    scroll_pos = norm_bottom - (current_bottom - current_top)
                    self.canvas.yview_moveto(scroll_pos)
                        
    def _handle_lpm_click(self, page_index, event):
        is_shift_pressed = (event.state & 0x1) != 0 
        if is_shift_pressed and self.selected_pages:
            last_active = self.active_page_index
            self._select_range(last_active, page_index)
        else:
            self._toggle_selection_lpm(page_index)
        self.active_page_index = page_index
        self.update_focus_display(hide_mouse_focus=True)

    def _toggle_selection_lpm(self, page_index):
        if page_index in self.selected_pages:
            self.selected_pages.remove(page_index)
        else:
            self.selected_pages.add(page_index)
        self.update_selection_display()

    def update_tool_button_states(self):
        doc_loaded = self.pdf_document is not None
        has_selection = len(self.selected_pages) > 0
        has_single_selection = len(self.selected_pages) == 1
        has_history_to_undo = len(self.history) > 1
        has_clipboard_content = self.clipboard is not None
        
        delete_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        insert_state = tk.NORMAL if doc_loaded and has_single_selection else tk.DISABLED
        paste_enable_state = tk.NORMAL if has_clipboard_content and doc_loaded and (len(self.selected_pages) <= 1) else tk.DISABLED 
        rotate_state = tk.NORMAL if doc_loaded and has_selection else tk.DISABLED
        undo_state = tk.NORMAL if has_history_to_undo else tk.DISABLED
        import_state = tk.NORMAL if doc_loaded else tk.DISABLED 
        select_state = tk.NORMAL if doc_loaded else tk.DISABLED
         
        # 1. Aktualizacja przycisków w panelu głównym
        self.undo_button.config(state=undo_state)
        self.delete_button.config(state=delete_state)
        self.cut_button.config(state=delete_state)
        self.copy_button.config(state=delete_state)
        self.import_button.config(state=import_state) 
        self.image_import_button.config(state=import_state) 
        self.extract_button.config(state=delete_state) 
        self.export_image_button.config(state=delete_state) 
        self.insert_before_button.config(state=insert_state)
        self.insert_after_button.config(state=insert_state)
        self.paste_before_button.config(state=paste_enable_state)
        self.paste_after_button.config(state=paste_enable_state)
        self.rotate_left_button.config(state=rotate_state)
        self.rotate_right_button.config(state=rotate_state)
        
        if doc_loaded:
             zoom_in_state = tk.NORMAL if self.target_num_cols > self.min_cols else tk.DISABLED
             zoom_out_state = tk.NORMAL if self.target_num_cols < self.max_cols else tk.DISABLED
        else:
             zoom_in_state = tk.DISABLED
             zoom_out_state = tk.DISABLED
             
        self.zoom_in_button.config(state=zoom_in_state)
        self.zoom_out_button.config(state=zoom_out_state)

        # 2. Aktualizacja pozycji w menu
        menus_to_update = [self.file_menu, self.edit_menu, self.select_menu]
        if hasattr(self, 'context_menu'):
            menus_to_update.append(self.context_menu)
        
        menu_state_map = {
            "Importuj strony z PDF...": import_state, 
            "Importuj obraz na nową stronę...": import_state,
            "Eksportuj strony do PDF...": delete_state,
            "Eksportuj strony jako obrazy PNG...": delete_state,            
            "Cofnij": undo_state,
            "Wszystkie strony": select_state, 
            "Strony nieparzyste": select_state,
            "Strony parzyste": select_state,
            "Strony pionowe": select_state,
            "Strony poziome": select_state,
            "Wytnij zaznaczone": delete_state,
            "Kopiuj zaznaczone": delete_state,
            "Usuń zaznaczone": delete_state,
            "Wklej przed": paste_enable_state,
            "Wklej po": paste_enable_state,
            "Wstaw nową stronę przed": insert_state,
            "Wstaw nową stronę po": insert_state,
            "Obróć w lewo (-90°)": rotate_state,
            "Obróć w prawo (+90°)": rotate_state,
        }
        
        for menu in menus_to_update:
            for label, state in menu_state_map.items():
                try:
                    menu.entryconfig(label, state=state)
                except tk.TclError:
                    continue
    
    def _setup_drag_and_drop_file(self):
        pass

    # --- Metody obsługi plików i edycji (Ze zmianami w import_image_to_new_page) ---
    def open_pdf(self, event=None, filepath=None):
        if not filepath:
            filepath = filedialog.askopenfilename(filetypes=[("Pliki PDF", "*.pdf")])
            if not filepath:  
                self._update_status("Anulowano otwieranie pliku.")
                return

        try:
            if self.pdf_document: self.pdf_document.close()
            self.pdf_document = fitz.open(filepath)
            self.selected_pages = set()
            self.tk_images = {}
            self.history.clear()  
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.active_page_index = 0
            self.thumb_frames.clear()
            self._save_state()
            for widget in list(self.scrollable_frame.winfo_children()):
                widget.destroy()
            self.target_num_cols = 4  
            self._reconfigure_grid()  
            self._update_status(f"Wczytano {len(self.pdf_document)} stron. Gotowy do edycji.")
            self.save_button_icon.config(state=tk.NORMAL)
            self.file_menu.entryconfig("Zapisz jako...", state=tk.NORMAL)
            self.update_tool_button_states()
            self.update_focus_display()
            
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się wczytać pliku PDF: {e}")
            self.pdf_document = None
            self.save_button_icon.config(state=tk.DISABLED)
            self.file_menu.entryconfig("Zapisz jako...", state=tk.DISABLED)
            self.update_tool_button_states()

    def import_pdf_after_active_page(self, event=None): # Dodano event=None dla skrótu
        if not self.pdf_document:
            self._update_status("BŁĄD: Otwórz najpierw dokument PDF.")
            return
        import_path = filedialog.askopenfilename(
            title="Wybierz plik PDF do zaimportowania",
            filetypes=[("Pliki PDF", "*.pdf")]
        )
        if not import_path:
            self._update_status("Anulowano importowanie pliku.")
            return
            
        imported_doc = None
        selected_indices = None 
        try:
            imported_doc = fitz.open(import_path)
            max_pages = len(imported_doc)
            self.master.update_idletasks() 
            dialog = EnhancedPageRangeDialog(self.master, "Wybór stron do importu", imported_doc)
            selected_indices = dialog.result 
            if selected_indices is None or not selected_indices:
                self._update_status("Anulowano importowanie lub nie wybrano stron.")
                return
            insert_index = len(self.pdf_document)
            if len(self.selected_pages) == 1:
                page_index = list(self.selected_pages)[0]
                insert_index = page_index + 1 
            elif len(self.selected_pages) > 1:
                 insert_index = max(self.selected_pages) + 1
            else:
                 insert_index = len(self.pdf_document)
                 
            self._save_state()
            num_inserted = len(selected_indices)
            temp_doc_for_insert = fitz.open()
            for page_index_to_import in selected_indices:
                 temp_doc_for_insert.insert_pdf(imported_doc, from_page=page_index_to_import, to_page=page_index_to_import)
            self.pdf_document.insert_pdf(temp_doc_for_insert, start_at=insert_index)
            temp_doc_for_insert.close()

            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()

            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Zaimportowano {num_inserted} wybranych stron i wstawiono w pozycji {insert_index}.")

        except Exception as e:
            self._update_status(f"BŁĄD Importowania: Nie udało się wczytać lub wstawić pliku: {e}")
            
        finally:
             if imported_doc and not imported_doc.is_closed:
                  imported_doc.close()

    def import_image_to_new_page(self):
        if not self.pdf_document:
            messagebox.showerror("Błąd", "Najpierw otwórz dokument PDF.")
            return

        image_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")],
            title="Wybierz plik obrazu do importu"
        )
        
        if not image_path:
            return

        # 1. Otwarcie dialogu i pobranie ustawień
        dialog = ImageImportSettingsDialog(self.master, "Ustawienia importu obrazu", image_path)
        settings = dialog.result
        
        if not settings:
            return
            
        scaling_mode = settings['scaling_mode']
        alignment = settings['alignment']
        scale_factor = settings['scale_factor']
        page_orientation = settings['page_orientation']
        
        try:
            # Wczytanie obrazu za pomocą PIL dla wymiarów
            img = Image.open(image_path)
            image_width_px, image_height_px = img.size
            image_dpi = settings.get('image_dpi', 96)
            
            # Konwersja wymiarów obrazu z pikseli na punkty PDF
            image_width_points = (image_width_px / image_dpi) * 72
            image_height_points = (image_height_px / image_dpi) * 72
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można wczytać obrazu: {e}")
            return
        
        # 2. Ustalanie wymiarów nowej strony docelowej (A4) i Tworzenie tymczasowego dokumentu fitz
        if page_orientation == "PIONOWO":
            page_w, page_h = A4_WIDTH_POINTS, A4_HEIGHT_POINTS
        else:
            page_w, page_h = A4_HEIGHT_POINTS, A4_WIDTH_POINTS
            
        # Tworzymy NOWY, TYMCZASOWY dokument fitz, w którym umieścimy obraz (wzorzec z Twojego działającego kodu)
        imported_doc = fitz.open()
        try:
            imported_page = imported_doc.new_page(
                -1, 
                width=page_w, 
                height=page_h
            )
        except Exception as e:
            messagebox.showerror("Błąd inicjalizacji fitz", f"Nie udało się utworzyć tymczasowej strony PDF: {e}")
            return

        # 3. Obliczanie Skalowania
        if scaling_mode == "ORYGINALNY":
            # Używa scale_factor jako końcowego współczynnika (np. 1.0 dla 100%, 0.5 dla 50%)
            scale = scale_factor
            
        elif scaling_mode == "SKALA":
            # W tym trybie również używamy scale_factor jako końcowego współczynnika
            scale = scale_factor
            
        elif scaling_mode == "DOPASUJ":
            scale_margin_points = MM_TO_POINTS * 50 # 50mm marginesu (25mm z każdej strony)
            scale_w = (page_w - scale_margin_points) / image_width_points
            scale_h = (page_h - scale_margin_points) / image_height_points
            scale = min(scale_w, scale_h)
        else:
            # Domyślnie 100% oryginalnego rozmiaru (jeśli DPI jest poprawne)
            scale = 1.0

        # ZAWSZE używaj obliczonego współczynnika 'scale' do określenia ostatecznych wymiarów
        final_w = image_width_points * scale
        final_h = image_height_points * scale
        # 4. Obliczanie Pozycji (Wyrównanie)
        offset_mm = 25.0
        offset_points = offset_mm * MM_TO_POINTS # ~70.87 punktów (25 mm)
        
        if alignment == "SRODEK":
            x_start = (page_w - final_w) / 2
            y_start = (page_h - final_h) / 2
            
        elif alignment == "GORA":
            # !!! ZAMIANA: Wstawiamy przy dolnej krawędzi (bo Twoja aplikacja interpretuje to odwrotnie)
            x_start = (page_w - final_w) / 2
            y_start = offset_points  # Wstawia obraz 25 mm od dolnej krawędzi
            
        elif alignment == "DOL":
            # !!! ZAMIANA: Wstawiamy przy górnej krawędzi (bo Twoja aplikacja interpretuje to odwrotnie)
            x_start = (page_w - final_w) / 2
            y_start = page_h - final_h - offset_points  # Wstawia obraz 25 mm od górnej krawędzi
            
        else: # Domyślnie Lewy Górny (lub jakakolwiek inna domyślna logika)
            x_start = offset_points 
            y_start = page_h - final_h - offset_points 
        
        # Określenie prostokąta docelowego dla fitz: Rect(x0, y0, x1, y1)
        rect = fitz.Rect(x_start, y_start, x_start + final_w, y_start + final_h)

        # 5. Wklejenie obrazu do tymczasowej strony fitz
        try:
            imported_page.insert_image(rect, filename=image_path)
            
            # 6. Określenie pozycji wstawienia w głównym dokumencie
            
            # Wzorzec przejęty z Twojego import_pdf_after_active_page:
            insert_index = len(self.pdf_document)
            if len(self.selected_pages) == 1:
                page_index = list(self.selected_pages)[0]
                insert_index = page_index + 1
            elif len(self.selected_pages) > 1:
                insert_index = max(self.selected_pages) + 1
            else:
                insert_index = len(self.pdf_document)
            
            # Zapis stanu przed modyfikacją głównego dokumentu
            self._save_state()
            
            # *** KLUCZOWA ZMIANA: Wstawienie tymczasowego dokumentu do głównego ***
            # Wykorzystujemy fitz.Document.insert_pdf() w taki sam sposób jak w Twojej działającej funkcji:
            self.pdf_document.insert_pdf(
                imported_doc, 
                from_page=0, 
                to_page=0,  # Wstawiamy tylko pierwszą stronę (z indeksem 0) z naszego tymczasowego dokumentu
                start_at=insert_index # Wstawiamy na docelową pozycję w głównym dokumencie
            )
            # --------------------------------------------------------------------
            
            # Aktualizacja aktywnej strony po wstawieniu
            self.active_page_index = insert_index
            
            # 7. Odświeżenie widoku i statusu
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            
            self._reconfigure_grid()
            self.update_tool_button_states()
            self.update_focus_display()
            
            self.status_bar.config(text=f"Zaimportowano obraz jako stronę na pozycji {insert_index + 1}. Aktualna liczba stron: {len(self.pdf_document)}.")
            
        except Exception as e:
            messagebox.showerror("Błąd Wklejania", f"Nie udało się wkleić obrazu: {e}")
            
        finally:
            # Zamknięcie tymczasowego dokumentu (ważne dla uniknięcia wycieków pamięci)
            if imported_doc and not imported_doc.is_closed:
                imported_doc.close()
            
    def _update_status(self, message):
        self.status_bar.config(text=message, fg="black")
            
    def _save_state(self):
        if self.pdf_document:
            buffer = self.pdf_document.write()
            self.history.append(buffer)
            if len(self.history) > self.max_history_size:
                self.history.pop(0)
            self.update_tool_button_states()
        else:
            self.history.clear()
            self.update_tool_button_states()
            
    def _get_page_bytes(self, page_indices: Set[int]) -> bytes:
        temp_doc = fitz.open()
        sorted_indices = sorted(list(page_indices))
        for index in sorted_indices:
            temp_doc.insert_pdf(self.pdf_document, from_page=index, to_page=index)
        page_bytes = temp_doc.write()
        temp_doc.close()
        return page_bytes
    
    def copy_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do skopiowania.")
            return
        try:
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            self.selected_pages.clear()
            self.update_selection_display()
            self._update_status(f"Skopiowano {self.pages_in_clipboard_count} stron do schowka.")
        except Exception as e:
            self._update_status(f"BŁĄD Kopiowania: {e}")
            
    def cut_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony do wycięcia.")
            return
        try:
            self._save_state()
            self.clipboard = self._get_page_bytes(self.selected_pages)
            self.pages_in_clipboard_count = len(self.selected_pages)
            pages_to_delete = sorted(list(self.selected_pages), reverse=True)
            for page_index in pages_to_delete:
                self.pdf_document.delete_page(page_index)
            deleted_count = len(self.selected_pages)
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self._reconfigure_grid()
            self.update_tool_button_states()
            self._update_status(f"Wycięto {deleted_count} stron i skopiowano do schowka.")
        except Exception as e:
            self._update_status(f"BŁĄD Wycinania: {e}")
            
    def paste_pages_before(self):
        self._handle_paste_operation(before=True)

    def paste_pages_after(self):
        self._handle_paste_operation(before=False)
        
    def _handle_paste_operation(self, before: bool):
        if not self.pdf_document or not self.clipboard:
            self._update_status("BŁĄD: Schowek jest pusty.")
            return
            
        if len(self.selected_pages) > 1:
             self._update_status("BŁĄD: Do wklejenia po/przed, zaznacz dokładnie jedną stronę, lub w ogóle by wkleić na końcu.")
             return
            
        target_index = len(self.pdf_document)
        if len(self.selected_pages) == 1:
            page_index = list(self.selected_pages)[0]
            if before:
                target_index = page_index  
            else:
                target_index = page_index + 1  
            
        self._perform_paste(target_index)

    def _perform_paste(self, target_index: int):
        try:
            self._save_state()
            temp_doc = fitz.open("pdf", self.clipboard)
            self.pdf_document.insert_pdf(temp_doc, start_at=target_index)
            num_inserted = len(temp_doc)
            temp_doc.close()
            self.clipboard = None
            self.pages_in_clipboard_count = 0
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self._reconfigure_grid()
            self.update_tool_button_states()
            self._update_status(f"Wklejono {num_inserted} stron w pozycji {target_index}.")
        except Exception as e:
            self._update_status(f"BŁĄD Wklejania: {e}")
            
    def delete_selected_pages(self, event=None, save_state: bool = True): 
        if not self.pdf_document or not self.selected_pages:  
            self._update_status("BŁĄD: Brak zaznaczonych stron do usunięcia.")
            return
        pages_to_delete = sorted(list(self.selected_pages), reverse=True)
        deleted_count = 0
        try:
            if save_state:
                self._save_state()
            for page_index in pages_to_delete:
                self.pdf_document.delete_page(page_index)
                deleted_count += 1
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()  
            self.total_pages = len(self.pdf_document)
            self.active_page_index = min(self.active_page_index, self.total_pages - 1)
            self.active_page_index = max(0, self.active_page_index)
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()  
            if save_state:
                 self._update_status(f"Usunięto {deleted_count} stron. Aktualna liczba stron: {self.total_pages}.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas usuwania: {e}")

    def extract_selected_pages(self):
        if not self.pdf_document or not self.selected_pages:
            self._update_status("BŁĄD: Zaznacz strony, które chcesz wyodrębnić do nowego pliku.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz wyodrębnione strony jako nowy PDF..."
        )
        if not filepath:
            self._update_status("Anulowano ekstrakcję stron.")
            return
        try:
            page_bytes = self._get_page_bytes(self.selected_pages)
            num_extracted = len(self.selected_pages)
            with open(filepath, "wb") as f:
                f.write(page_bytes)
            self._update_status(f"Pomyślnie wyodrębniono {num_extracted} stron do: {filepath}")
        except Exception as e:
            self._update_status(f"BŁĄD Eksportu: Nie udało się zapisać nowego pliku: {e}")

    def undo_last_action(self):
        if len(self.history) < 2:
            self._update_status("Brak operacji do cofnięcia!")
            self.update_tool_button_states()
            return

        self.history.pop()  
        previous_state_bytes = self.history[-1]  
        
        try:
            if self.pdf_document: self.pdf_document.close()
            self.pdf_document = fitz.open("pdf", previous_state_bytes)
            self.selected_pages.clear()
            self.tk_images.clear()
            self.thumb_frames.clear()
            for widget in list(self.scrollable_frame.winfo_children()):  
                widget.destroy()

            self.active_page_index = min(self.active_page_index, len(self.pdf_document) - 1)
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status("Cofnięto ostatnią operację.")
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się cofnąć operacji: {e}")
            self.pdf_document = None
            
    def save_document(self):
        if not self.pdf_document: return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Pliki PDF", "*.pdf")],
            title="Zapisz zmodyfikowany PDF jako..."
        )
        if not filepath:  
            self._update_status("Anulowano zapisywanie.")
            return
        try:
            self.pdf_document.save(filepath, garbage=4, clean=True, pretty=True)  
            self._update_status(f"Dokument pomyślnie zapisany jako: {filepath}")
            if self.history:
                 current_state = self.history[-1]
                 self.history = [current_state]
                 self.update_tool_button_states() 
        except Exception as e:
            self._update_status(f"BŁĄD: Nie udało się zapisać pliku: {e}")
            
    def rotate_selected_page(self, angle):
        if not self.pdf_document or not self.selected_pages: 
            self._update_status("BŁĄD: Zaznacz strony do obrotu.")
            return
        pages_to_rotate = sorted(list(self.selected_pages))
        try:
            self._save_state()
            rotated_count = 0
            for page_index in pages_to_rotate:
                page = self.pdf_document.load_page(page_index)
                current_rotation = page.rotation
                new_rotation = (current_rotation + angle) % 360
                page.set_rotation(new_rotation)
                rotated_count += 1
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Obrócono {rotated_count} stron o {angle} stopni.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas obracania: {e}")

    def insert_blank_page_before(self):
           self._handle_insert_operation(before=True)

    def insert_blank_page_after(self):
        self._handle_insert_operation(before=False)
        
    def _handle_insert_operation(self, before: bool):
        if not self.pdf_document or len(self.selected_pages) != 1:  
             self._update_status("BŁĄD: Zaznacz dokładnie jedną stronę, aby wstawić obok niej nową.")
             return
        width, height = (595.276, 841.89)
        page_index = list(self.selected_pages)[0]
        try:
            # Użycie wymiarów istniejącej strony
            rect = self.pdf_document[page_index].rect
            width = rect.width
            height = rect.height  
        except Exception:
            pass # Pozostawienie domyślnych A4
        
        if before:
              target_page = page_index
        else:
              target_page = page_index + 1
              
        try:
            self._save_state()
            self.pdf_document.insert_page(
                pno=target_page,  
                width=width,  
                height=height
            )
            self.selected_pages.clear()
            self.tk_images.clear()
            for widget in list(self.scrollable_frame.winfo_children()): widget.destroy()
            self.thumb_frames.clear()
            self._reconfigure_grid()  
            self.update_tool_button_states()
            self.update_focus_display()
            self._update_status(f"Wstawiono nową, pustą stronę. Aktualna liczba stron: {len(self.pdf_document)}.")
        except Exception as e:
            self._update_status(f"BŁĄD: Wystąpił błąd podczas wstawiania: {e}")
            
    # --- Metody obsługi widoku/GUI (Bez zmian) ---
    def _on_mousewheel(self, event):
        current_y = self.canvas.yview()[0]
        if event.num == 4 or event.delta > 0:  
            if current_y <= 0.001:  
                return  
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  
            self.canvas.yview_scroll(1, "units")
            
    def zoom_in(self):
        if self.pdf_document:
            self.target_num_cols = max(self.min_cols, self.target_num_cols - 1)
            self._reconfigure_grid()
            self.update_tool_button_states()  

    def zoom_out(self):
        if self.pdf_document:
            self.target_num_cols = min(self.max_cols, self.target_num_cols + 1)
            self._reconfigure_grid()
            self.update_tool_button_states()  

    def _reconfigure_grid(self, event=None):
        if not self.pdf_document:  
             self.canvas.config(scrollregion=self.canvas.bbox("all"))
             return

        self.master.update_idletasks()
        actual_canvas_width = self.canvas.winfo_width()
        scrollbar_safety = 25  
        available_width = max(100, actual_canvas_width - scrollbar_safety)  
        internal_padding = self.THUMB_PADDING  
        min_thumb_size = self.min_zoom_width
        min_required_col_size = min_thumb_size + internal_padding  
        calculated_num_cols = int((available_width - internal_padding) / min_required_col_size)
        num_cols = self.target_num_cols  
        if num_cols > calculated_num_cols:
            num_cols = calculated_num_cols
            self.target_num_cols = max(self.min_cols, num_cols)
        num_cols = max(self.min_cols, min(self.max_cols, num_cols))
        total_padding_width = (num_cols + 1) * internal_padding
        space_for_thumbs = available_width - total_padding_width
        theoretical_width = space_for_thumbs / num_cols
        final_column_width = theoretical_width * self.ZOOM_FACTOR
        column_width = max(1, math.floor(final_column_width))  
        self.fixed_thumb_width = column_width  
        
        for widget in list(self.scrollable_frame.grid_slaves()):
             if not isinstance(widget, ThumbnailFrame):
                 widget.destroy()

        for col in range(self.max_cols):  
             if col < num_cols:
                 self.scrollable_frame.grid_columnconfigure(col, weight=1)  
             else:
                 self.scrollable_frame.grid_columnconfigure(col, weight=0)  

        if not self.thumb_frames:
             self._create_widgets(num_cols, column_width)
        else:
             self._update_widgets(num_cols, column_width)
            
        self.scrollable_frame.update_idletasks()  
        bbox = self.canvas.bbox("all")
        if bbox is not None:
              self.canvas.config(scrollregion=(bbox[0], 0, bbox[2], bbox[3]))
              self.canvas.yview_moveto(0.0)  
              self.canvas.coords(self.canvas_window_id, 0, 0)
              self.canvas.yview_moveto(0.0)
        else:
              self.canvas.config(scrollregion=(0, 0, actual_canvas_width, 10))

    def _get_page_size_label(self, page_index):
        if not self.pdf_document: return ""
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        width_mm = round(page_width / 72 * 25.4)
        page_height_mm = round(page_height / 72 * 25.4)
        
        if 205 <= width_mm <= 215 and 292 <= page_height_mm <= 302: return "A4"
        if 292 <= width_mm <= 302 and 205 <= page_height_mm <= 215: return "A4 (Poziom)"
        if 292 <= width_mm <= 302 and 415 <= page_height_mm <= 425: return "A3"
        return f"{width_mm} x {page_height_mm} mm"


    def _create_widgets(self, num_cols, column_width):
        for i in range(len(self.pdf_document)):
            page_frame = ThumbnailFrame(
                parent=self.scrollable_frame,  
                viewer_app=self,  
                page_index=i,  
                column_width=column_width
            )
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")  
            self.thumb_frames[i] = page_frame  
            
        self.update_selection_display()
        self.update_focus_display()

    def _update_widgets(self, num_cols, column_width):
        page_frames = [c for c in self.scrollable_frame.grid_slaves() if isinstance(c, ThumbnailFrame)]
        page_frames.sort(key=lambda x: x.page_index)
        frame_bg = "#F5F5F5"  
        for i, page_frame in enumerate(page_frames):
            page_frame.grid(row=i // num_cols, column=i % num_cols, padx=self.THUMB_PADDING, pady=self.THUMB_PADDING, sticky="n")  
            idx = page_frame.page_index
            img_tk = self._render_and_scale(idx, column_width)
            self.tk_images[idx] = img_tk
            page_frame.img_label.config(image=img_tk)
            page_frame.img_label.image = img_tk
            outer_frame_children = page_frame.outer_frame.winfo_children()
            if len(outer_frame_children) > 2:
                  outer_frame_children[1].config(text=f"Strona {idx + 1}", bg=frame_bg)
                  outer_frame_children[2].config(text=self._get_page_size_label(idx), bg=frame_bg)
            
        self.update_selection_display()
        self.update_focus_display()

    
    def _render_and_scale(self, page_index, column_width):
        page = self.pdf_document.load_page(page_index)
        page_width = page.rect.width
        page_height = page.rect.height
        aspect_ratio = page_height / page_width if page_width != 0 else 1
        final_thumb_width = column_width  
        final_thumb_height = int(final_thumb_width * aspect_ratio)
        if final_thumb_width <= 0: final_thumb_width = 1
        if final_thumb_height <= 0: final_thumb_height = 1

        mat = fitz.Matrix(self.render_dpi_factor, self.render_dpi_factor)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        resized_image = image.resize((final_thumb_width, final_thumb_height), Image.LANCZOS)  
        
        return ImageTk.PhotoImage(resized_image)

    def update_selection_display(self):
        num_selected = len(self.selected_pages)
        
        for frame_index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if frame_index in self.selected_pages:
                frame.config(bg=frame.bg_selected)  
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_selected)
                inner_frame.config(bg=frame.bg_selected)
            else:
                frame.config(bg=frame.bg_normal)
                for widget in inner_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget('bg') != 'white':
                         widget.config(bg=frame.bg_normal)
                inner_frame.config(bg=frame.bg_normal)

        self.update_tool_button_states()
        
        if self.pdf_document:
             if num_selected > 0:
                 msg = f"Zaznaczono {num_selected} stron. Użyj przycisków w panelu do edycji."
                 if num_selected == 1:
                      page_num = list(self.selected_pages)[0] + 1
                      msg = f"Zaznaczono 1 stronę (Strona {page_num}). Użyj przycisków w panelu do edycji."
                 self._update_status(msg)
             else:
                 self._update_status(f"Dokument wczytany. Liczba stron: {len(self.pdf_document)}. Zaznacz strony (LPM lub Spacja) do edycji.")
        else:
             self._update_status("Gotowy. Otwórz plik PDF.")

    def update_focus_display(self, hide_mouse_focus: bool = False):
        if not self.pdf_document: return
        for index, frame in self.thumb_frames.items():
            inner_frame = frame.outer_frame
            if index == self.active_page_index and not hide_mouse_focus:
                inner_frame.config(highlightbackground=FOCUS_HIGHLIGHT_COLOR, highlightcolor=FOCUS_HIGHLIGHT_COLOR)
            else:
                inner_frame.config(highlightbackground=frame.bg_normal, highlightcolor=frame.bg_normal)

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = SelectablePDFViewer(root)
        root.mainloop()
    except ImportError as e:
        print(f"BŁĄD: Wymagane biblioteki nie są zainstalowane. Upewnij się, że masz PyMuPDF (pip install PyMuPDF) i Pillow (pip install Pillow). Szczegóły: {e}")
        sys.exit(1)