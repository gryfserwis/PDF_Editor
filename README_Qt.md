# GRYF PDF Editor - Qt Version

## Przegląd

PDFEditor_qt.py to kompletna implementacja edytora PDF z wykorzystaniem PySide6 (Qt6) zapewniająca nowoczesny interfejs użytkownika i pełną obsługę drag & drop.

## Wymagania

```bash
pip install PySide6 PyMuPDF Pillow pypdf
```

## Uruchomienie

```bash
python PDFEditor_qt.py
```

## Główne funkcje

### 1. Operacje na plikach

#### Otwieranie PDF
- **Menu/Przycisk**: Plik → Otwórz PDF (Ctrl+O)
- **Drag & Drop**: Przeciągnij plik PDF na okno programu
  - Jeśli dokument nie jest otwarty: otwiera PDF
  - Jeśli dokument jest otwarty: importuje strony z PDF

#### Import/Eksport
- **Import PDF**: Ctrl+I lub przeciągnij PDF na okno
- **Import obrazu**: Ctrl+Shift+I lub przeciągnij obraz na okno
- **Eksport stron**: Ctrl+E (wybrane strony do nowego PDF)
- **Eksport obrazów**: Ctrl+Shift+E (wybrane strony jako PNG)

### 2. Drag & Drop stron (Miniatury)

#### Przenoszenie stron
- **Lewy przycisk myszy**: Zaznacz strony i przeciągnij aby **przenieść**
- **Ctrl + przeciągnij**: **Kopiuj** strony zamiast przenosić
- **Wielokrotne strony**: Zaznacz wiele stron i przeciągnij wszystkie na raz

#### Zaznaczanie
- **LPM**: Zaznacz pojedynczą stronę
- **Ctrl+LPM**: Przełącz zaznaczenie (dodaj/usuń z zaznaczenia)
- **Shift+LPM**: Zaznacz zakres stron
- **Ctrl+A**: Zaznacz wszystkie strony
- **F1**: Zaznacz strony nieparzyste (1, 3, 5...)
- **F2**: Zaznacz strony parzyste (2, 4, 6...)
- **Esc**: Odznacz wszystkie

#### Menu kontekstowe (PPM)
- Kliknij prawym przyciskiem na stronie aby wyświetlić menu z operacjami:
  - Wytnij, Kopiuj, Wklej przed/po
  - Usuń, Duplikuj
  - Obróć w lewo/prawo

### 3. Edycja stron

#### Operacje schowka
- **Ctrl+X**: Wytnij zaznaczone strony
- **Ctrl+C**: Kopiuj zaznaczone strony
- **Ctrl+V**: Wklej po zaznaczonej stronie
- **Ctrl+Shift+V**: Wklej przed zaznaczoną stroną

#### Inne operacje
- **Delete**: Usuń zaznaczone strony
- **Ctrl+D**: Duplikuj zaznaczoną stronę
- **Ctrl+Shift+(-/+)**: Obróć w lewo/prawo

### 4. Modyfikacje stron

#### Przesuwanie zawartości (F5)
- Przesuń zawartość zaznaczonych stron w poziomie/pionie
- Użyj transformacji PyPDF dla precyzyjnego przesunięcia

#### Numeracja stron
- **Dodaj numery (F7)**: Pełna konfiguracja
  - Położenie (góra/dół, lewo/środek/prawo)
  - Tryb normalny/lustrzany
  - Marginesy poziome (z opcją lustrzanych)
  - Czcionka i rozmiar
  - Format (prosty: "1, 2..." lub pełny: "Strona 1 z 10")
  
- **Usuń numery (F6)**: 
  - Określ wysokość pola skanowania (góra/dół)
  - Automatyczne wykrywanie wzorców numeracji

### 5. Widok

#### Zoom
- **Ctrl+Plus**: Powiększ miniatury (mniej kolumn)
- **Ctrl+Minus**: Pomniejsz miniatury (więcej kolumn)
- Zakres: 2-10 kolumn

#### Nawigacja
- Użyj paska przewijania lub kółka myszy
- Strzałki klawiatury do poruszania się między stronami

### 6. Cofnij/Ponów

- **Ctrl+Z**: Cofnij ostatnią operację
- **Ctrl+Y**: Ponów cofniętą operację
- Historia: do 50 kroków wstecz/wprzód

## Skróty klawiszowe

### Plik
- `Ctrl+O` - Otwórz PDF
- `Ctrl+S` - Zapisz jako
- `Ctrl+I` - Importuj PDF
- `Ctrl+E` - Eksportuj PDF
- `Ctrl+Shift+I` - Importuj obraz
- `Ctrl+Shift+E` - Eksportuj obrazy

### Edycja
- `Ctrl+Z` - Cofnij
- `Ctrl+Y` - Ponów
- `Ctrl+X` - Wytnij
- `Ctrl+C` - Kopiuj
- `Ctrl+V` - Wklej po
- `Ctrl+Shift+V` - Wklej przed
- `Delete` - Usuń
- `Ctrl+D` - Duplikuj
- `Ctrl+A` - Zaznacz wszystko
- `Esc` - Odznacz wszystko

### Zaznacz
- `F1` - Strony nieparzyste
- `F2` - Strony parzyste

### Modyfikacje
- `F5` - Przesuń zawartość
- `F6` - Usuń numerację
- `F7` - Dodaj numerację
- `F8` - Przytnij/zmień rozmiar (do dodania)

### Widok
- `Ctrl++` - Zoom in
- `Ctrl+-` - Zoom out

## Różnice w stosunku do wersji Tkinter

### Ulepszone funkcje:
1. **Natywny drag & drop** - przeciąganie plików i stron
2. **Lepsza obsługa zaznaczania** - Ctrl i Shift dla wielu stron
3. **Wizualna informacja zwrotna** - wyraźne podświetlenie zaznaczenia
4. **Nowoczesny interfejs** - Qt Fusion style
5. **Lepsze dialogi** - wykorzystanie layoutów Qt

### Zachowana zgodność:
- Wszystkie funkcje z PDFEditor.py
- Ta sama logika operacji PDF
- Kompatybilne formaty plików
- Identyczne wyniki operacji

## Obsługiwane formaty

### Wejście:
- PDF - wszystkie wersje obsługiwane przez PyMuPDF
- Obrazy - PNG, JPG, JPEG, TIF, TIFF

### Wyjście:
- PDF - z optymalizacją i czyszczeniem
- PNG - 300 DPI dla eksportu obrazów

## Struktura kodu

```
PDFEditor_qt.py
├── Stałe i konfiguracja
├── Klasy dialogów
│   ├── PageNumberingDialog
│   ├── ShiftContentDialog
│   └── PageNumberMarginDialog
├── Widgety miniaturek
│   ├── ThumbnailWidget
│   └── ThumbnailListWidget (z obsługą D&D)
└── PDFEditorQt (główna klasa)
    ├── Inicjalizacja UI
    ├── Obsługa drag & drop plików
    ├── Operacje na plikach
    ├── Operacje edycji stron
    ├── Undo/Redo
    ├── Modyfikacje stron
    ├── Operacje zaznaczania
    └── Funkcje pomocnicze
```

## Znane ograniczenia

1. Wymaga środowiska graficznego (nie działa w trybie headless)
2. Duże PDF (>500 stron) mogą spowalniać renderowanie miniaturek
3. Niektóre zaawansowane transformacje PDF mogą wymagać dodatkowej optymalizacji

## Wsparcie

Program jest własnością Centrum Graficznego Gryf sp. z o.o.
Wszelkie prawa zastrzeżone.

## Wersja

**5.0.0** - Kompletna implementacja Qt z pełnym drag & drop
