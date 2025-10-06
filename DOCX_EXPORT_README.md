# Funkcja Eksportu PDF do DOCX

## Opis
Nowa funkcjonalność umożliwia eksport zaznaczonych stron PDF do formatu Microsoft Word (DOCX).

## Jak używać

### Przez menu
1. Otwórz plik PDF w programie
2. Zaznacz strony do eksportu (kliknij na miniatury)
3. Wybierz: **Plik → Eksportuj zaznaczone strony do DOCX...**
4. Wybierz lokalizację i nazwę pliku w oknie dialogowym
5. Kliknij "Zapisz"

### Skrót klawiszowy
- **Ctrl+Shift+W** - eksport zaznaczonych stron do DOCX

## Szczegóły techniczne

### Pliki
- `export_to_docx.py` - główny moduł eksportu
- `PDFEditor.py` - integracja z interfejsem użytkownika

### Funkcja eksportu
```python
export_selected_pages_to_docx(pdf_document, selected_pages, output_path, dpi=300)
```

**Parametry:**
- `pdf_document` - obiekt PyMuPDF (fitz.Document)
- `selected_pages` - lista indeksów stron do eksportu (0-based)
- `output_path` - ścieżka do pliku DOCX
- `dpi` - rozdzielczość eksportu (domyślnie 300)

**Zwraca:**
- Liczba wyeksportowanych stron

### Proces eksportu
1. Każda strona PDF jest renderowana do obrazu PNG w wysokiej rozdzielczości (300 DPI)
2. Obraz jest konwertowany do formatu PIL/Pillow
3. Obraz jest wstawiany na osobną stronę dokumentu Word
4. Automatyczne skalowanie zachowuje proporcje i dopasowuje do strony

### Rozdzielczość
- Domyślnie: **300 DPI** - dobry kompromis między jakością a rozmiarem pliku
- Możliwe wartości: 150-600 DPI
- Wyższe DPI = lepsza jakość, ale większy plik

### Obsługiwane formaty stron
- Pionowe (portrait)
- Poziome (landscape)
- Różne rozmiary (A4, Letter, itp.)

## Wymagania

### Biblioteki Python
```bash
pip install PyMuPDF Pillow pypdf python-docx
```

Lub:
```bash
pip install -r requirements.txt
```

### Wersje
- PyMuPDF (fitz) >= 1.18.0
- python-docx >= 0.8.11
- Pillow >= 8.0.0

## Obsługa błędów

### Brak zaznaczonych stron
**Komunikat:** "Wybierz strony do eksportu."
**Rozwiązanie:** Zaznacz przynajmniej jedną stronę przed eksportem

### Anulowanie dialogu
**Komunikat:** "Anulowano eksport do DOCX."
**Efekt:** Operacja zostaje przerwana, żadne pliki nie są tworzone

### Błędy podczas eksportu
**Komunikat:** "Wystąpił błąd podczas eksportowania stron do DOCX: [szczegóły]"
**Przyczyny:**
- Brak uprawnień do zapisu w wybranej lokalizacji
- Niewystarczająca ilość miejsca na dysku
- Uszkodzony plik PDF
- Problem z bibliotekami

## Przykłady użycia

### Eksport wszystkich stron
1. Zaznacz wszystkie strony (Ctrl+A lub F4)
2. Ctrl+Shift+W
3. Wybierz lokalizację i zapisz

### Eksport wybranych stron
1. Przytrzymaj Ctrl i kliknij wybrane miniatury stron
2. Menu: Plik → Eksportuj zaznaczone strony do DOCX...
3. Wybierz lokalizację i zapisz

### Eksport pojedynczej strony
1. Kliknij na miniaturę strony
2. Ctrl+Shift+W
3. Wybierz lokalizację i zapisz

## Porównanie z innymi formatami eksportu

| Format | Rozmiar pliku | Jakość | Edytowalność | Użycie |
|--------|---------------|--------|--------------|--------|
| PDF | Mały | Oryginalna | Nie | Zachowanie oryginalnego dokumentu |
| PNG | Średni-Duży | Wysoka | Nie | Obrazy do prezentacji |
| DOCX | Średni | Wysoka | Tak* | Wstawianie do dokumentów Word |

\* Strony są obrazami, więc edycja wymaga narzędzi graficznych

## Zalecenia

### Optymalna rozdzielczość dla różnych zastosowań
- **Druk (print):** 300 DPI
- **Wyświetlanie na ekranie:** 150-200 DPI
- **Wysoka jakość:** 400-600 DPI

### Rozmiar pliku
Szacunkowy rozmiar wynikowego pliku DOCX:
- 1 strona A4 przy 300 DPI: ~150-200 KB
- 10 stron: ~1.5-2 MB
- 50 stron: ~7.5-10 MB

### Ograniczenia
- Nie ekstrahuje tekstu (strony jako obrazy)
- Nie zachowuje interaktywnych elementów (linki, formularze)
- Nie zachowuje warstw PDF
- Duże dokumenty mogą generować duże pliki DOCX

## Rozwiązywanie problemów

### Problem: Plik DOCX nie otwiera się w Word
**Rozwiązanie:** Sprawdź czy plik został zapisany całkowicie (nie przerwano operacji)

### Problem: Niska jakość obrazów
**Rozwiązanie:** Zwiększ rozdzielczość DPI w kodzie (edytuj export_dpi w PDFEditor.py, linia 4138)

### Problem: Zbyt duży rozmiar pliku
**Rozwiązanie:** Zmniejsz rozdzielczość DPI lub eksportuj mniej stron na raz

### Problem: Długi czas eksportu
**Przyczyna:** Wysokie DPI i/lub wiele stron
**Rozwiązanie:** Poczekaj na zakończenie (wskaźnik czekania pokazuje postęp)

## Historia zmian

### Wersja 1.0 (2025-01-XX)
- Pierwsza implementacja funkcji eksportu do DOCX
- Obsługa stron pionowych i poziomych
- Rozdzielczość 300 DPI
- Integracja z menu i skróty klawiszowe
- Obsługa błędów i komunikaty użytkownika

## Autor
GRYF PDF Editor Team

## Licencja
Zgodnie z licencją głównego programu PDF Editor
