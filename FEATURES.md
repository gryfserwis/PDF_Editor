# Nowe funkcje w GRYF PDF Editor

## 1. System Makr
Menu "Makra" umożliwia:
- **Nagrywanie makr**: Zapisuje sekwencję operacji wykonywanych przez użytkownika
- **Lista makr użytkownika**: Zarządzanie zapisanymi makrami
- **Przypisywanie skrótów klawiszowych**: Możliwość przypisania własnych skrótów do makr

### Jak używać makr:
1. Wybierz "Makra" → "Nagraj makro..."
2. Wprowadź nazwę makra i rozpocznij nagrywanie
3. Wykonaj żądane operacje (np. obracanie, zaznaczanie, usuwanie stron)
4. Wybierz ponownie "Nagraj makro" aby zakończyć nagrywanie
5. Makro zostanie zapisane i będzie dostępne w "Lista makr użytkownika"

### Obsługiwane akcje w makrach:
- Obracanie stron (w lewo/prawo)
- Usuwanie stron
- Duplikowanie stron
- Zaznaczanie stron (wszystkie/nieparzyste/parzyste)

## 2. Hasła PDF
Menu "Modyfikacje" zawiera nowe opcje:
- **Ustaw hasło PDF**: Zabezpiecza PDF hasłem
- **Usuń hasło PDF**: Usuwa hasło z pliku PDF (jeśli jest otwarty)

### Jak używać:
1. Otwórz plik PDF
2. Wybierz "Modyfikacje" → "Ustaw hasło PDF..."
3. Wprowadź hasło i potwierdź
4. Zapisz chroniony plik w nowej lokalizacji

## 3. Usuwanie pustych stron
Menu "Modyfikacje" → "Usuń puste strony"

### Definicja pustej strony:
- Brak tekstu
- Brak rysunków
- Brak obrazów (białe tło)

### Jak używać:
1. Otwórz plik PDF
2. Wybierz "Modyfikacje" → "Usuń puste strony"
3. Potwierdź operację
4. Puste strony zostaną automatycznie usunięte

## 4. Scalanie plików PDF
Menu "Plik" → "Scalanie plików PDF..."

### Funkcje:
- Dodawanie wielu plików PDF
- Zmiana kolejności plików
- Eksport do jednego pliku PDF

### Jak używać:
1. Wybierz "Plik" → "Scalanie plików PDF..."
2. Kliknij "Dodaj pliki..." i wybierz pliki PDF
3. Użyj "Przesuń w górę/dół" aby zmienić kolejność
4. Kliknij "Scal i zapisz..." aby wyeksportować

## 5. Rozszerzone opcje eksportu

### Eksport stron do PDF (Menu "Plik" → "Eksportuj strony do PDF...")
Dla wielu stron:
- **Wszystkie strony do jednego pliku**: Standardowy tryb
- **Każda strona do osobnego pliku**: Każda strona zapisywana osobno

### Eksport stron jako obrazy PNG (Menu "Plik" → "Eksportuj strony jako obrazy PNG...")
- **Każda strona do osobnego pliku PNG**: Wysoka rozdzielczość 300 DPI

## 6. Komunikaty użytkownika
Wszystkie komunikaty używają jednolitego systemu `custom_messagebox`:
- Lepsze wyśrodkowanie
- Spójny wygląd
- Obsługa różnych typów (info, error, warning, question)

## Skróty klawiszowe
Wszystkie istniejące skróty pozostają niezmienione. Nowe makra mogą mieć przypisane własne skróty klawiszowe.
