# Zmiany w interfejsie użytkownika

## Nowe menu i opcje

### 1. Menu "Makra" (nowe)
```
Makra
├── Nagraj makro...
└── Lista makr użytkownika...
```

**Lokalizacja:** Między menu "Modyfikacje" a "Pomoc"

### 2. Menu "Plik" - nowe opcje
```
Plik
├── ...
├── Scalanie plików PDF...  ← NOWA OPCJA
├── ────────────────────
└── Zamknij plik
```

**Pozycja:** Po opcjach eksportu obrazów, przed "Zamknij plik"

### 3. Menu "Modyfikacje" - nowe opcje
```
Modyfikacje
├── ...
├── Odwróć kolejność wszystkich stron
├── ────────────────────
├── Ustaw hasło PDF...      ← NOWA OPCJA
├── Usuń hasło PDF...       ← NOWA OPCJA
├── ────────────────────
└── Usuń puste strony       ← NOWA OPCJA
```

**Pozycja:** Na końcu menu modyfikacji

## Nowe okna dialogowe

### Dialog "Nagrywanie makra"
- Pole tekstowe: Nazwa makra
- Przyciski: [Rozpocznij] [Anuluj]

### Dialog "Lista makr użytkownika"
- Lista makr z przypisanymi skrótami
- Przyciski: [Uruchom] [Usuń] [Ustaw skrót...] [Zamknij]

### Dialog "Scalanie plików PDF"
- Lista plików do scalenia
- Przyciski zarządzania:
  - [Dodaj pliki...]
  - [Usuń zaznaczony]
  - [Przesuń w górę]
  - [Przesuń w dół]
- Akcje: [Scal i zapisz...] [Anuluj]

### Dialog "Ustaw hasło PDF"
- Pole: Wprowadź hasło (ukryte)
- Pole: Potwierdź hasło (ukryte)
- Przyciski: [OK] [Anuluj]

### Dialog "Tryb eksportu" (dla wielu stron)
**Dla PDF:**
- Radio button: ○ Wszystkie strony do jednego pliku PDF
- Radio button: ○ Każda strona do osobnego pliku PDF
- Przyciski: [OK] [Anuluj]

**Dla PNG:**
- Radio button: ○ Każda strona do osobnego pliku PNG
- Przyciski: [OK] [Anuluj]

## Komunikaty użytkownika

Wszystkie komunikaty używają teraz `custom_messagebox`:
- Typy: info, error, warning, question, yesnocancel
- Centrowanie względem okna głównego
- Jednolity styl

### Przykłady komunikatów:
- "Makro zostało zapisane z X akcjami."
- "Usunięto X pustych stron."
- "Scalono X plików PDF. Zapisano do: [ścieżka]"
- "PDF z hasłem zapisany do: [ścieżka]"
- "Czy na pewno usunąć makro '[nazwa]'?" (pytanie)

## Zmiany w istniejących funkcjach

### Eksport stron do PDF
- **Przed:** Zawsze eksportowało wszystkie strony do jednego pliku
- **Po:** Dialog wyboru między jednym plikiem a wieloma plikami

### Eksport stron jako obrazy PNG
- **Przed:** Zawsze każda strona do osobnego pliku
- **Po:** Dialog informacyjny (w przyszłości możliwość scalania)

## Uwagi implementacyjne

1. Wszystkie nowe dialogi są centrowane względem okna głównego
2. Obsługa klawiszy Enter i Escape we wszystkich dialogach
3. Walidacja wprowadzanych danych
4. Potwierdzenia dla operacji destrukcyjnych
5. Komunikaty o błędach z opisem problemu
