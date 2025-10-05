# Ustawienia Eksportu PDF i Obrazów - Instrukcja Użytkownika

## Spis treści
1. [Przegląd](#przegląd)
2. [Nowe ustawienia](#nowe-ustawienia)
3. [Jak używać](#jak-używać)
4. [Wzorce nazw plików](#wzorce-nazw-plików)
5. [Przykłady](#przykłady)

---

## Przegląd

Od tej wersji, ustawienia eksportu PDF i obrazów są konfigurowane centralnie w oknie **Preferencji** zamiast w osobnych oknach dialogowych podczas eksportu. Dzięki temu:

- ⚡ Szybszy eksport - bez dodatkowych okien dialogowych
- 🎯 Spójne ustawienia - zapisane dla przyszłych eksportów
- 🔧 Elastyczne nazwy plików - pełna kontrola nad wzorcem nazw

---

## Nowe ustawienia

### W menu: Ustawienia → Preferencje

#### Sekcja "Eksport PDF"

| Ustawienie | Opcje | Domyślnie |
|------------|-------|-----------|
| **Domyślna wersja PDF** | 1.4, 1.5, 1.7, PDF/A | 1.7 |
| **Przygotuj do druku** | brak, tryb drukarski, spłaszcz warstwy, usuń metadane, wstaw trimbox/cropbox | brak |
| **Wzorzec nazwy pliku** | Dowolny tekst ze zmiennymi | `Eksport_{range}_{data}_{czas}` |

#### Sekcja "Eksport obrazów"

| Ustawienie | Opcje | Domyślnie |
|------------|-------|-----------|
| **Domyślny format** | PNG, TIFF, JPEG | PNG |
| **Domyślne DPI** | 150, 300, 600 | 300 |
| **Wzorzec nazwy pliku** | Dowolny tekst ze zmiennymi | `{base_name}_strona_{page}_{data}_{czas}` |

---

## Jak używać

### Konfiguracja ustawień

1. Otwórz program PDF Editor
2. Przejdź do: **Ustawienia** → **Preferencje**
3. Przewiń w dół do sekcji **"Eksport PDF"** i **"Eksport obrazów"**
4. Dostosuj ustawienia według potrzeb
5. Kliknij **"Zapisz"**

### Eksport PDF

1. Zaznacz strony do eksportu
2. Kliknij **"Eksportuj PDF"** (Ctrl+E) lub wybierz z menu
3. Wybierz folder docelowy
4. Plik zostanie zapisany automatycznie z nazwą wg wzorca

**Uwaga:** Eksport PDF zawsze zapisuje wszystkie zaznaczone strony do jednego pliku.

### Eksport obrazów

1. Zaznacz strony do eksportu
2. Kliknij **"Eksportuj obrazy"** (Ctrl+Shift+E) lub wybierz z menu
3. Wybierz folder docelowy
4. Każda strona zostanie zapisana jako osobny plik obrazu

---

## Wzorce nazw plików

### Dostępne zmienne

#### Dla eksportu PDF:

| Zmienna | Opis | Przykład |
|---------|------|----------|
| `{data}` | Data eksportu (YYYY-MM-DD) | 2025-10-05 |
| `{czas}` | Czas eksportu (HH-MM-SS) | 14-30-45 |
| `{base_name}` | Nazwa pliku źródłowego | dokument |
| `{range}` | Zakres eksportowanych stron | 1-5 lub 3 |

#### Dla eksportu obrazów:

Wszystkie powyższe, plus:

| Zmienna | Opis | Przykład |
|---------|------|----------|
| `{page}` | Numer aktualnej strony | 10 |

### Zasady tworzenia wzorców

- ✅ Używaj zmiennych w `{nawiasach klamrowych}`
- ✅ Możesz łączyć zmienne z własnym tekstem
- ✅ Możesz używać podkreśleń `_` i myślników `-`
- ❌ Unikaj znaków specjalnych jak: `/ \ : * ? " < > |`
- ❌ Nie dodawaj rozszerzenia (program doda automatycznie)

---

## Przykłady

### Przykład 1: Prosty eksport PDF

**Ustawienia:**
- Wzorzec: `Eksport_{range}_{data}_{czas}`
- Plik źródłowy: `faktura.pdf`
- Zaznaczone strony: 1-3
- Data: 2025-10-05
- Czas: 14:30:45

**Wynik:**
```
Eksport_1-3_2025-10-05_14-30-45.pdf
```

---

### Przykład 2: Eksport obrazów z nazwą źródłową

**Ustawienia:**
- Wzorzec: `{base_name}_strona_{page}_{data}_{czas}`
- Format: PNG
- DPI: 300
- Plik źródłowy: `raport.pdf`
- Zaznaczone strony: 5, 10, 15

**Wynik:**
```
raport_strona_5_2025-10-05_14-30-45.png
raport_strona_10_2025-10-05_14-30-45.png
raport_strona_15_2025-10-05_14-30-45.png
```

---

### Przykład 3: Backup z prostą nazwą

**Ustawienia:**
- Wzorzec: `Backup_{base_name}_{data}`
- Plik źródłowy: `dokument.pdf`
- Zaznaczone strony: wszystkie

**Wynik:**
```
Backup_dokument_2025-10-05.pdf
```

---

### Przykład 4: Archiwum z datą na początku

**Ustawienia:**
- Wzorzec: `{data}_archiwum_{range}`
- Plik źródłowy: `umowa.pdf`
- Zaznaczone strony: 1-10

**Wynik:**
```
2025-10-05_archiwum_1-10.pdf
```

---

### Przykład 5: Eksport wysokiej jakości do druku

**Ustawienia:**
- Wzorzec: `{base_name}_print_{page}_DPI600`
- Format: TIFF
- DPI: 600
- Plik źródłowy: `plakat.pdf`

**Wynik:**
```
plakat_print_1_DPI600.tiff
```

---

## Automatyczna numeracja

Jeśli plik o takiej nazwie już istnieje, program automatycznie doda numer:

```
dokument.pdf      (oryginalny)
dokument (1).pdf  (pierwszy duplikat)
dokument (2).pdf  (drugi duplikat)
dokument (3).pdf  (trzeci duplikat)
```

---

## Wskazówki

### 💡 Porady dotyczące wzorców

1. **Data na początku** - ułatwia sortowanie chronologiczne
   ```
   {data}_{base_name}_{range}
   ```

2. **Opis w nazwie** - dodaj stały tekst dla kontekstu
   ```
   Faktura_{base_name}_{data}
   ```

3. **Numeracja stron** - użyj `{page}` dla obrazów
   ```
   {base_name}_str{page}_z_{range}
   ```

### 🎯 Najlepsze praktyki

- Używaj spójnego wzorca dla podobnych dokumentów
- Dodawaj datę dla dokumentów archiwizowanych
- Używaj `{base_name}` aby zachować kontekst źródła
- Testuj wzorce na niewielkiej liczbie stron

### ⚠️ Uwagi

- Zmienne są **wrażliwe na wielkość liter** - użyj dokładnie jak podano
- Niewykorzystane zmienne pozostaną w nazwie jako tekst
- Puste zmienne (np. brak numeru strony dla PDF) będą pominięte

---

## Resetowanie ustawień

Aby przywrócić domyślne ustawienia eksportu:

1. Otwórz **Preferencje**
2. Kliknij przycisk **"Resetuj"** w sekcji "Reset do ustawień domyślnych"
3. Potwierdź resetowanie

**Uwaga:** To zresetuje **wszystkie** ustawienia programu, nie tylko eksportu.

---

## Wsparcie techniczne

W razie problemów:
1. Sprawdź czy wzorzec nie zawiera niedozwolonych znaków
2. Upewnij się że masz uprawnienia zapisu do folderu docelowego
3. Sprawdź czy masz wystarczająco miejsca na dysku

---

**Ostatnia aktualizacja:** 2025-10-05  
**Wersja:** 5.0.0
