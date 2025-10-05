# Changelog - System Preferencji i Zapamiętywania Wartości

## Nowe Funkcje

### 1. System Zarządzania Preferencjami
- Dodano klasę `PreferencesManager` do zarządzania preferencjami programu
- Preferencje zapisywane są automatycznie do pliku `preferences.txt` w folderze programu
- Preferencje wczytywane są automatycznie przy starcie programu

### 2. Okno Dialogowe Preferencji
- Dodano pozycję "Preferencje..." w menu **Plik**
- Okno preferencji zawiera:
  - Domyślną ścieżkę zapisu plików
  - Wybór języka (pl/en)
  - Skalowanie GUI (75%, 100%, 125%, 150%)
- Przycisk "Przywróć domyślne (wszystkie)" resetuje wszystkie preferencje

### 3. Automatyczne Zapamiętywanie Wartości w Dialogach
Program teraz automatycznie zapamiętuje ostatnio użyte wartości w następujących oknach dialogowych:

#### PageCropResizeDialog (Kadrowanie i zmiana rozmiaru)
- Tryb kadrowania (crop_mode)
- Marginesy (góra, dół, lewo, prawo)
- Tryb zmiany rozmiaru (resize_mode)
- Format docelowy (A4, A3, itp.)
- Niestandardowe wymiary
- Pozycjonowanie i przesunięcia

#### PageNumberingDialog (Dodawanie numeracji)
- Marginesy poziome (lewy, prawy)
- Margines pionowy
- Pozycja pionowa (góra/dół)
- Wyrównanie (lewa/środek/prawa)
- Tryb numeracji (normalna/naprzemiennie)
- Strona początkowa i numer początkowy
- Czcionka i rozmiar czcionki
- Lustrzane marginesy
- Format numeracji (standardowy/pełny)

#### ShiftContentDialog (Przesuwanie zawartości)
- Kierunek przesunięcia poziomego (lewo/prawo)
- Kierunek przesunięcia pionowego (góra/dół)
- Wartości przesunięcia (X i Y w mm)

#### PageNumberMarginDialog (Usuwanie numeracji)
- Margines górny (nagłówek)
- Margines dolny (stopka)

#### MergePageGridDialog (Scalanie stron)
- Format arkusza (A0-A6)
- Orientacja (pionowa/pozioma)
- Marginesy (góra, dół, lewo, prawo)
- Odstępy między stronami (poziomo/pionowo)
- Rozdzielczość eksportu (DPI)

### 4. Przycisk "Przywróć domyślne" w Każdym Dialogu
- Każde okno dialogowe zawiera teraz przycisk "Przywróć domyślne"
- Przycisk umieszczony między przyciskami "Zastosuj"/"OK" a "Anuluj"
- Przywraca fabryczne wartości domyślne dla danego dialogu
- Nie zapisuje zmian do preferencji - tylko wypełnia pola wartościami domyślnymi

## Struktura Pliku Preferencji

Plik `preferences.txt` jest plikiem tekstowym w formacie `klucz=wartość`, np.:

```
default_save_path=
language=pl
gui_scale=100
PageCropResizeDialog.crop_mode=nocrop
PageCropResizeDialog.margin_top=10
PageNumberingDialog.font_name=Times-Roman
ShiftContentDialog.x_direction=P
...
```

## Użycie

### Otwieranie Preferencji
1. Menu **Plik** → **Preferencje...**
2. Edytuj wymagane ustawienia
3. Kliknij **Zapisz** aby zapamiętać zmiany lub **Anuluj** aby je odrzucić

### Przywracanie Domyślnych Wartości
#### W pojedynczym dialogu:
1. Otwórz dowolne okno dialogowe (np. Kadrowanie i zmiana rozmiaru)
2. Kliknij przycisk **Przywróć domyślne**
3. Wartości w polach zostaną zastąpione wartościami fabrycznymi
4. Kliknij **Zastosuj** aby użyć tych wartości lub **Anuluj** aby odrzucić

#### We wszystkich dialogach:
1. Menu **Plik** → **Preferencje...**
2. Kliknij **Przywróć domyślne (wszystkie)**
3. Potwierdź reset
4. Wszystkie zapamiętane wartości zostaną zresetowane do wartości fabrycznych

## Uwagi Techniczne
- Preferencje są zapisywane automatycznie po każdym użyciu dialogu z przyciskiem "Zastosuj"
- Plik preferencji jest tworzony automatycznie przy pierwszym uruchomieniu
- W razie problemów z preferencjami, można bezpiecznie usunąć plik `preferences.txt` - zostanie on odtworzony z wartościami domyślnymi
- Dialogi `EnhancedPageRangeDialog` i `ImageImportSettingsDialog` nie zapamiętują wartości, ponieważ są one zależne od kontekstu (zakresu stron lub właściwości obrazu)
