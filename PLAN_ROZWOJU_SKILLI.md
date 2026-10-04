# Plan zmian w skillach

Plan modyfikacji i nowych skilli w pluginie `java-backend`, na podstawie notatki o brakujących krokach procesu (4 repozytoria, kontrakt API → backend, Liquibase, reguły REG, pliki Bruno).

## Mapowanie notatki na repo

| # | Pomysł z notatki | Decyzja | Gdzie |
|---|---|---|---|
| 1 | Pytania do analityka | **Zmiana** istniejącego skilla | `analyzing-confluence-feasibility` |
| 2 | Macierz reguł z testami | **Zmiana** dwóch skilli | `planning-jira-implementation` + `reviewing-java-commits` |
| 5 | Smoke test lokalnie | **Nowy** skill | `java-backend:smoke-testing-locally` |
| 6 | Pętla po review | **Zmiana** istniejącego skilla | `reviewing-java-commits` (tryb przyrostowy) |
| 8 | Security review | **Zmiana**, bez osobnego skilla | `reviewing-java-commits`, checklista B |
| 9 | Retro | **Nowy** skill | `java-backend:running-task-retro` |

---

## Faza 1: zalecana na start (punkt 2)

### A. Macierz wymagań i testów (punkt 2)

**`planning-jira-implementation`:**

- Nowy krok procesu po zestawieniu źródeł: wypisanie każdej reguły REG i każdego kryterium akceptacji z ID i linkiem do lokalnej kopii analizy (`.analiza/...md:<linia>`).
- Nowa sekcja szablonu **„Macierz wymagań i testów”** z kolumnami: ID wymagania, cytat lub skrót, typ testu (IT albo unit), proponowana klasa i metoda testu, numer kroku, który je realizuje.
- Każdy krok implementacyjny dostaje pole **„Testy (pisane przed kodem)”** z odnośnikiem do wierszy macierzy.
- Reguła: wymaganie bez przypisanego testu musi mieć jawne uzasadnienie albo trafia do pytań.
- Nowe pozycje w „Częstych błędach”.

**`reviewing-java-commits`:**

- Nowa pozycja w checkliście C, **„Pokrycie macierzy testami”**. Jeśli w repo jest `IMPLEMENTATION_PLAN_<KLUCZ>.md` (klucz z nazwy gałęzi), skill sprawdza, czy każdy wiersz macierzy ma w PR test, który faktycznie weryfikuje regułę, a nie tylko istnieje.
- W raporcie nowa tabela: wymaganie, test, status (pokryte / brak / test nie weryfikuje reguły).

---

## Faza 2

### B. `analyzing-confluence-feasibility`: pytania do analityka (punkt 1)

- Wszystko zostaje w jednym raporcie `.md`. Nie powstają osobne pliki z pytaniami.
- Do raportu dochodzi czwarta, ostatnia sekcja **„Pytania do analityka”**. Wymóg „dokładnie trzy sekcje” zmienia się na „trzy sekcje analizy + sekcja pytań”. Zakaz dodawania podsumowań, rekomendacji i kolejnych kroków zostaje bez zmian.
- Sekcja zawiera jeden blok kodu (```` ```text ````), który można skopiować jednym kliknięciem i wkleić jako komentarz w Jirze lub Confluence. W bloku są tylko blokady i pozycje „do uzupełnienia” z trzech sekcji analizy, ponumerowane. Każde pytanie ma cytat, miejsce w dokumencie i hipotezę (ten sam format co w skillu planowania). Treść jest napisana do analityka, bez odwołań do kodu i nazw klas.
- Szablon w skillu dostaje przykład tej sekcji, a „Częste błędy” nowe pozycje: pytanie bez miejsca w dokumencie, pytanie, którego nie ma w żadnej z trzech sekcji analizy, oraz rozbicie pytań na kilka bloków.
- Opcjonalnie skill sam publikuje komentarz, ale tylko po wyraźnej zgodzie.
- `planning-jira-implementation` sprawdza, czy raport z tą sekcją już istnieje, i nie zadaje ponownie tych samych pytań.

### C. `reviewing-java-commits`: tryb przyrostowy (punkt 6)

- Raport już zapisuje „ostatni przeglądany commit”. Jeśli `CODE_REVIEW/<gałąź>.md` istnieje, a gałąź ma nowe commity, skill:
  1. przegląda tylko diff `<poprzedni commit>..HEAD`;
  2. dla każdej wcześniejszej uwagi ustala status: naprawiona, nienaprawiona albo naprawiona częściowo, z linią;
  3. dopisuje sekcję „Weryfikacja poprzednich uwag”.
- Skill review zostaje tylko do odczytu. Poprawki robi zwykła sesja („popraw uwagi z CODE_REVIEW/x.md”). Nie używam wbudowanego `/code-review --fix`, bo nie zna checklist A i C.

### D. `reviewing-java-commits`: autoryzacja (punkt 8)

- Rozszerzenie punktu 8 (Bezpieczeństwo) albo nowa pozycja „Autoryzacja”:
  - czy nowy endpoint ma kontrolę uprawnień (`@PreAuthorize` lub odpowiednik);
  - czy brak uprawnień daje 403 zgodnie z analizą;
  - czy da się dostać do cudzego zasobu przez podmianę ID (IDOR);
  - czy istnieje test negatywny 403.
- Do tego jedno zdanie w skillu: przy zmianach uprawnień zalecane jest też uruchomienie `/security-review`.

---

## Faza 3

### E. Nowy skill `smoke-testing-locally` (punkt 5)

Kroki:

1. **Ustalenie zakresu.** Skill sprawdza, które projekty zostały zmodyfikowane w ramach zadania (gałąź z kluczem zadania, diff względem gałęzi bazowej w każdym repozytorium, opcjonalnie lista repozytoriów z `IMPLEMENTATION_PLAN_<KLUCZ>.md`). Do uruchomienia trafiają tylko te projekty, które da się uruchomić jako usługę. Zmienione biblioteki, np. kontrakt API, nie są uruchamiane, ale ich nowa wersja musi być widoczna dla usług.
2. **Reset baz** dla uruchamianych usług. Wymaga potwierdzenia przy pierwszym uruchomieniu w sesji.
3. **Uruchomienie usług** i czekanie na health-check każdej z nich.
4. **`bru run`** dla kolekcji lub folderu nowych albo zmienionych endpointów.
5. **Raport** z odpowiedziami oraz **zatrzymanie usług**.

Ten skill najbardziej zależy od środowiska, dlatego jest ostatni (patrz pytania niżej).

### F. Nowy skill `running-task-retro` (punkt 9)

- Wejście: klucz zadania. Skill porównuje plan, finalny diff (to, co weszło spoza planu), raporty review (to, co review złapało, a czego plan nie przewidział) i pytania zadane w trakcie.
- Wynik: `RETRO/<KLUCZ>.md` oraz konkretne propozycje zmian w skillach tego repo w formie gotowej łatki. Skill niczego nie zmienia automatycznie, bo skille są instalowane z marketplace i zmiana musi przejść przez commit tutaj.

---

## Zmiany wspólne

- README: tabela pluginów, ściągawka komend, struktura repo.
- `plugin.json` dla `java-backend`: nowy opis.
- Każdy nowy skill w tym samym stylu co obecne: sekcja dostępu (MCP, CLI, REST), tabela „Kiedy zapytać”, „Częste błędy”, raport po polsku bez skrótowców.
- Na koniec `claude plugin validate`.

## Otwarte pytania przed implementacją

**Do punktu 5 (smoke test, może poczekać do fazy 3):**

1. Jak uruchamiasz poszczególne usługi (`bootRun`, docker compose) i jak rozpoznać, które repozytorium jest usługą, a które biblioteką? Jak resetujesz bazy? Gdzie leży kolekcja Bruno?

## Kolejność realizacji

1. Faza 1, punkt A (macierz testów): nie wymaga odpowiedzi na pytania.
2. Faza 2: B, C, D.
3. Faza 3: E (po odpowiedzi na pytanie 1), F.
