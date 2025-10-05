# Zmiany w PDF Editor - Eksport PDF i Obrazów

## Podsumowanie zmian

Dodano nowe ustawienia eksportu PDF i obrazów jako sekcje w oknie Preferencji programu. Ustawienia te są teraz konfigurowane w preferencjach, a nie jako osobne okna podczas eksportu.

## Szczegółowe zmiany

### 1. PreferencesManager (PDFEditor.py)

Dodano nowe domyślne preferencje:

**Eksport PDF:**
- `pdf_export.version` - domyślna wersja PDF (1.4, 1.5, 1.7, PDF/A) - domyślnie: '1.7'
- `pdf_export.print_prep` - opcje przygotowania do druku - domyślnie: 'brak'
  - Opcje: brak, tryb drukarski, spłaszcz warstwy, usuń metadane, wstaw trimbox/cropbox
- `pdf_export.filename_pattern` - wzorzec nazwy pliku - domyślnie: 'Eksport_{range}_{data}_{czas}'
  - Zmienne: {data}, {czas}, {base_name}, {range}

**Eksport obrazów:**
- `image_export.format` - domyślny format obrazu - domyślnie: 'PNG'
  - Opcje: PNG, TIFF, JPEG
- `image_export.dpi` - domyślne DPI - domyślnie: '300'
  - Opcje: 150, 300, 600
- `image_export.filename_pattern` - wzorzec nazwy pliku - domyślnie: '{base_name}_strona_{page}_{data}_{czas}'
  - Zmienne: {data}, {czas}, {base_name}, {range}, {page}

### 2. PreferencesDialog (PDFEditor.py)

Rozszerzono okno Preferencji o dwie nowe sekcje:

**Sekcja "Eksport PDF":**
- Combobox wyboru wersji PDF
- Combobox przygotowania do druku
- Pole tekstowe wzorca nazwy pliku
- Etykieta z listą dostępnych zmiennych

**Sekcja "Eksport obrazów":**
- Combobox wyboru formatu obrazu
- Combobox wyboru DPI
- Pole tekstowe wzorca nazwy pliku
- Etykieta z listą dostępnych zmiennych

Zaktualizowano metody:
- `load_current_values()` - wczytuje nowe preferencje
- `ok()` - zapisuje nowe preferencje

### 3. Funkcje pomocnicze (PDFEditor.py)

**format_export_filename()**
- Nowa funkcja formatująca nazwy plików według wzorca
- Obsługuje zmienne: {data}, {czas}, {base_name}, {range}, {page}
- Zastępuje wartości zmiennych aktualnymi danymi

**generate_unique_export_filename()**
- Zaktualizowana funkcja generująca unikalne nazwy plików
- Dodano parametr `pattern` dla wzorca nazwy
- Dodano parametr `page_number` dla numeru strony
- Dodaje liczby (1), (2), (3) jeśli plik istnieje

### 4. Funkcja export_selected_pages_to_image() (PDFEditor.py)

Zmiany:
- Usunięto dialog wyboru trybu eksportu
- Dodano odczyt ustawień z preferencji (format, DPI, wzorzec nazwy)
- Użycie wzorca nazwy z preferencji przy generowaniu nazw plików
- Użycie DPI z preferencji zamiast stałej wartości 300
- Obsługa formatów PNG, JPEG, TIFF
- Wszystkie komunikaty używają `custom_messagebox`

### 5. Funkcja extract_selected_pages() (PDFEditor.py)

Zmiany:
- Usunięto dialog wyboru trybu eksportu (single/separate)
- Domyślnie eksportuje wszystkie zaznaczone strony do jednego pliku
- Dodano odczyt wzorca nazwy z preferencji
- Użycie wzorca nazwy z preferencji przy generowaniu nazw plików
- Zastąpiono `_update_status` błędów przez `custom_messagebox` z typem 'error'
- Wszystkie komunikaty używają `custom_messagebox`

### 6. Inne zmiany

- Dodano plik `.gitignore` z wykluczeniem `__pycache__/` i innych plików tymczasowych
- Wszystkie komunikaty błędów w funkcjach eksportu używają `custom_messagebox` zamiast `messagebox`

## Zmienne dostępne we wzorcach nazw

### Dla eksportu PDF:
- `{data}` - data w formacie YYYY-MM-DD (np. 2025-10-05)
- `{czas}` - czas w formacie HH-MM-SS (np. 21-00-45)
- `{base_name}` - nazwa bazowa otwartego pliku PDF (bez rozszerzenia)
- `{range}` - zakres eksportowanych stron (np. "1-5" lub "3")

### Dla eksportu obrazów:
- `{data}` - data w formacie YYYY-MM-DD
- `{czas}` - czas w formacie HH-MM-SS
- `{base_name}` - nazwa bazowa otwartego pliku PDF
- `{range}` - zakres eksportowanych stron
- `{page}` - numer aktualnie eksportowanej strony

## Przykłady użycia wzorców

**Przykład 1 - Eksport PDF:**
- Wzorzec: `Eksport_{range}_{data}_{czas}`
- Plik: `dokument.pdf`, strony 3-5
- Wynik: `Eksport_3-5_2025-10-05_21-00-45.pdf`

**Przykład 2 - Eksport obrazów:**
- Wzorzec: `{base_name}_strona_{page}_{data}_{czas}`
- Plik: `raport.pdf`, strona 10
- Wynik: `raport_strona_10_2025-10-05_21-00-45.png`

**Przykład 3 - Własny wzorzec:**
- Wzorzec: `Backup_{base_name}_{data}`
- Plik: `dokument.pdf`, strony 1-3
- Wynik: `Backup_dokument_2025-10-05.pdf`

## Testy

Utworzono skrypt testowy `/tmp/test_export_preferences.py` weryfikujący:
- Poprawność formatowania nazw plików według wzorca
- Poprawność domyślnych wartości preferencji
- Obsługę wszystkich zmiennych we wzorcach

Wszystkie testy przeszły pomyślnie.

## Zgodność wsteczna

Zmiany są w pełni kompatybilne wstecz:
- Istniejące pliki preferencji zostaną uzupełnione domyślnymi wartościami
- Użytkownicy bez zapisanych preferencji eksportu otrzymają rozsądne domyślne wartości
- Nie zmieniono interfejsu żadnych istniejących funkcji (poza wewnętrzną implementacją)
