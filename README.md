# GRYF PDF Editor

Profesjonalny edytor plików PDF z rozbudowanymi funkcjami edycji, modyfikacji i zarządzania stronami.

## Wymagania

- Python 3.8+
- PyMuPDF (fitz)
- Pillow (PIL)
- pypdf
- tkinter

## Instalacja zależności

```bash
pip install PyMuPDF Pillow pypdf
```

## Uruchomienie

```bash
python PDFEditor.py
```

## Funkcje programu

### Podstawowe operacje na plikach

- **Otwórz PDF** (Ctrl+O): Wczytaj plik PDF do edycji
- **Zapisz jako** (Ctrl+S): Zapisz zmodyfikowany dokument PDF
- **Importuj strony z PDF** (Ctrl+I): Dodaj strony z innego pliku PDF
- **Eksportuj strony do PDF** (Ctrl+E): Wyodrębnij zaznaczone strony do nowego pliku
- **Importuj obraz na nową stronę** (Ctrl+Shift+I): Dodaj obrazy jako nowe strony
- **Eksportuj strony jako obrazy PNG** (Ctrl+Shift+E): Zapisz strony jako pliki PNG

### Zaznaczanie stron

- **Wszystkie strony** (Ctrl+A, F4): Zaznacz lub odznacz wszystkie strony
- **Strony nieparzyste** (F1): Zaznacz strony 1, 3, 5, ...
- **Strony parzyste** (F2): Zaznacz strony 2, 4, 6, ...
- **Strony pionowe** (Ctrl+F1): Zaznacz wszystkie strony w orientacji pionowej
- **Strony poziome** (Ctrl+F2): Zaznacz wszystkie strony w orientacji poziomej

### Edycja stron

- **Cofnij** (Ctrl+Z): Cofnij ostatnią operację (do 50 poziomów)
- **Ponów** (Ctrl+Y): Ponów cofniętą operację
- **Usuń zaznaczone** (Delete/Backspace): Usuń zaznaczone strony
- **Wytnij zaznaczone** (Ctrl+X): Wytnij strony do schowka
- **Kopiuj zaznaczone** (Ctrl+C): Skopiuj strony do schowka
- **Wklej przed** (Ctrl+Shift+V): Wklej strony ze schowka przed zaznaczoną
- **Wklej po** (Ctrl+V): Wklej strony ze schowka po zaznaczonej
- **Duplikuj stronę** (Ctrl+D): Duplikuj zaznaczoną stronę (nowa funkcja)
- **Wstaw nową stronę przed** (Ctrl+Shift+N): Wstaw pustą stronę przed zaznaczoną
- **Wstaw nową stronę po** (Ctrl+N): Wstaw pustą stronę po zaznaczonej

### Modyfikacje stron

- **Obróć w lewo** (Ctrl+Shift+-): Obróć zaznaczone strony o -90°
- **Obróć w prawo** (Ctrl+Shift++): Obróć zaznaczone strony o +90°
- **Przesuń zawartość zaznaczonych stron** (F5): Przesuń zawartość stron
- **Usuń numery stron** (F6): Usuń numerację z marginesów
- **Wstaw numery stron** (F7): Dodaj numerację do stron
- **Przytnij zaznaczone strony** (F8): Kadruj i zmień rozmiar stron
- **Scal strony na arkuszu**: Scal wiele stron w siatkę na jednym arkuszu (nowa funkcja)
- **Odwróć kolejność wszystkich stron**: Odwróć kolejność stron w dokumencie

### Widok

- **Powiększ** (+): Zmniejsz liczbę kolumn (większe miniatury)
- **Pomniejsz** (-): Zwiększ liczbę kolumn (mniejsze miniatury)
- Nawigacja strzałkami: Przesuwaj fokus między stronami
- Spacja: Zaznacz/odznacz stronę pod fokusem
- Escape: Wyczyść wszystkie zaznaczenia

## Nowe funkcje (wersja 3.6.0+)

### 1. Duplikuj stronę (Ctrl+D)

Funkcja umożliwia szybkie duplikowanie pojedynczej strony.

**Użycie:**
1. Zaznacz jedną stronę do zduplikowania
2. Naciśnij Ctrl+D lub wybierz "Edycja → Duplikuj stronę"
3. Kopia strony zostanie wstawiona zaraz po oryginale

**Szczegóły:**
- Dostępna tylko gdy zaznaczona jest dokładnie jedna strona
- Zduplikowana strona jest identyczna z oryginałem
- Operacja jest rejestrowana w historii cofnij/ponów
- Idealnie do szybkiego tworzenia kopii pojedynczych stron

### 2. Scal strony na arkuszu

Funkcja scala wiele stron w układ siatki na jednym nowym arkuszu.

**Użycie:**
1. Zaznacz strony do scalenia (lub jedną stronę do wypełnienia siatki)
2. Wybierz "Modyfikacje → Scal strony na arkuszu..."
3. W oknie dialogowym ustaw:
   - **Format arkusza**: A0, A1, A2, A3, A4, A5 lub A6
   - **Margines do krawędzi arkusza**: odstęp od krawędzi (domyślnie 10 mm)
   - **Odstęp między stronami**: przestrzeń między komórkami siatki (domyślnie 5 mm)
4. Kliknij "Zastosuj"

**Szczegóły:**
- Program automatycznie oblicza optymalną siatkę (wiersze × kolumny)
- Maksymalizuje rozmiar stron w dostępnej przestrzeni
- Jeśli zaznaczona jest jedna strona: wypełnia siatkę jej kopiami (do 12 kopii)
- Jeśli zaznaczone są strony wielokrotne: układa je w kolejności
- Scalona strona jest dodawana na końcu dokumentu
- Operacja jest rejestrowana w historii cofnij/ponów

**Przykłady użycia:**
- Tworzenie arkuszy kontaktowych z miniaturami stron
- Drukowanie wielu stron na jednym arkuszu (np. 4 na 1, 9 na 1)
- Tworzenie podglądów dokumentów
- Drukowanie etykiet lub wizytówek z tej samej strony

**Algorytm optymalizacji:**
Program testuje wszystkie możliwe układy siatki (1×N, 2×N, 3×N, ...) i wybiera ten, który daje największy rozmiar pojedynczej komórki, uwzględniając:
- Wymiary wybranego formatu arkusza
- Marginesy brzegowe
- Odstępy między stronami
- Liczbę stron do umieszczenia

## Wskazówki użytkowania

### Praca z zaznaczeniami

- **LPM (lewy przycisk myszy)**: Zaznacz/odznacz pojedynczą stronę
- **Shift + LPM**: Zaznacz zakres stron
- **PPM (prawy przycisk myszy)**: Pokaż menu kontekstowe
- **Spacja**: Zaznacz/odznacz stronę pod fokusem
- **Strzałki**: Przesuń fokus między stronami

### Schowek

- Schowek przechowuje skopiowane/wycięte strony
- Można wkleić strony wielokrotnie
- Schowek jest czyszczony po wklejeniu
- Licznik pokazuje liczbę stron w schowku

### Historia operacji

- Do 50 poziomów cofania (Ctrl+Z)
- Po zapisaniu dokumentu historia jest czyszczona
- Każda modyfikacja czyści stos ponów
- Operacje są zapisywane automatycznie

## Klawisze skrótów

### Plik
- Ctrl+O: Otwórz PDF
- Ctrl+S: Zapisz jako
- Ctrl+I: Importuj strony z PDF
- Ctrl+E: Eksportuj strony do PDF
- Ctrl+Shift+I: Importuj obraz
- Ctrl+Shift+E: Eksportuj strony jako PNG

### Edycja
- Ctrl+Z: Cofnij
- Ctrl+Y: Ponów
- Ctrl+X: Wytnij
- Ctrl+C: Kopiuj
- Ctrl+V: Wklej po
- Ctrl+Shift+V: Wklej przed
- Ctrl+D: Duplikuj stronę
- Ctrl+N: Wstaw nową stronę po
- Ctrl+Shift+N: Wstaw nową stronę przed
- Delete/Backspace: Usuń zaznaczone

### Zaznaczanie
- Ctrl+A / F4: Wszystkie strony
- F1: Strony nieparzyste
- F2: Strony parzyste
- Ctrl+F1: Strony pionowe
- Ctrl+F2: Strony poziome
- Escape: Wyczyść zaznaczenia

### Modyfikacje
- Ctrl+Shift+-: Obróć w lewo
- Ctrl+Shift++: Obróć w prawo
- F5: Przesuń zawartość
- F6: Usuń numery stron
- F7: Wstaw numery stron
- F8: Przytnij strony

### Nawigacja
- Strzałki: Przesuń fokus
- Spacja: Zaznacz/odznacz pod fokusem

## Uwagi techniczne

### Formaty stron
Program rozpoznaje następujące formaty:
- A4 (210 × 297 mm)
- A3 (297 × 420 mm)
- A4 poziom (297 × 210 mm)
- Inne (wyświetlane jako "XXX × YYY mm")

### Limity
- Maksymalna liczba stron: nieograniczona (zależna od pamięci RAM)
- Historia cofnij/ponów: 50 poziomów
- Minimalna liczba kolumn widoku: 2
- Maksymalna liczba kolumn widoku: 10

### Wydajność
- Miniatury są renderowane w wysokiej jakości (DPI: 0.833)
- Przy dużych dokumentach (>100 stron) zaleca się cierpliwość przy pierwszym wczytaniu
- Operacje na dużych dokumentach mogą chwilę potrwać

## O programie

**GRYF PDF Editor**  
Wersja: 3.6.0  

Program stanowi wyłączną własność intelektualną Centrum Graficznego Gryf sp. z o.o.

Wszelkie prawa zastrzeżone. Kopiowanie, modyfikowanie oraz rozpowszechnianie programu bez pisemnej zgody autora jest zabronione.

## Zgłaszanie błędów

W razie problemów lub pytań, prosimy o kontakt z działem wsparcia technicznego.

---

*Dokument aktualizowany: 2024*
