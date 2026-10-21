---
name: implementing-jira-task
description: "Use when asked to implement a Jira task that already has an implementation plan — \"zaimplementuj PROJ-123\", \"zrób krok 3 z planu\", \"kontynuuj implementację\". Executes `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` step by step in the repositories it names: task branch, tests from the requirements-to-tests matrix written and failing before the code, code written to this team's standards (package-by-feature, jOOQ for reads, JPA/Hibernate for writes, MapStruct, no needless interfaces, Liquibase changeset conventions), green module tests and one commit per step. Keeps a Polish-language log in `IMPLEMENTATION_LOG/<KLUCZ>.md` (step status, commits, deviations from the plan, questions and answers) so a later session can resume and the retro can compare plan with reality. Stops and asks when the plan does not match the code. Never pushes, never opens a pull request. Without a plan it points to planning-jira-implementation instead of coding from the ticket."
disable-model-invocation: true
argument-hint: "[KLUCZ-ZADANIA] [numer-kroku]"
---

# Implementing Jira Task

## Overview

Turns the implementation plan of one Jira task into code. The plan (`IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md`, written by `planning-jira-implementation`) is the work order: its steps set the order, its requirements-to-tests matrix says which test proves each step, its "Model danych" section says where the code lives. The local copy of the system analysis (`IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md`) is the source of truth about behavior whenever a step leaves a detail open.

Each step goes the same way: read the step and its matrix rows, look at the neighbouring code for conventions, write the tests and watch them fail, write the smallest code that makes them pass to this team's standards, run the module's tests, commit. Everything that happens is written to `IMPLEMENTATION_LOG/<KLUCZ-ZADANIA>.md`, so the next session continues from the first unfinished step and `running-task-retro` can later compare the plan with what was actually done.

The skill writes code and commits on the task branch. It never pushes, never opens a pull request, never touches other branches, and never reconciles a plan-versus-code conflict on its own — it asks.

## When to Use

- User asks to implement a task, continue an implementation, or do one step of the plan: "zaimplementuj PROJ-123", "kontynuuj PROJ-123", "zrób krok 4".
- A plan exists. If it does not, do not implement from the Jira ticket or from the Confluence page alone — say that the plan is missing and propose `/java-backend:planning-jira-implementation <KLUCZ>` first. The plan is where questions get asked and where the matrix is built; coding without it skips both.
- Scope is backend only, as in the plan. Anything in "Poza zakresem" stays untouched.
- Not for: planning (`planning-jira-implementation`), review (`java-code-review`, `reviewing-java-commits`), local end-to-end check (`smoke-testing-locally`), fixing review findings on a branch without a plan — that is an ordinary session ("popraw uwagi z CODE_REVIEW/x.html").

## Bezpieczeństwo

- **Tylko gałąź zadania.** Kod powstaje na gałęzi z kluczem zadania w każdym repozytorium z planu. Skill nie commituje na gałęzi bazowej, nie zmienia innych gałęzi, nie używa `git push`, `git rebase`, `git reset --hard` ani `git checkout -- <plik>` na plikach, których sam nie zmienił.
- **Bez pushowania i bez pull requesta.** Wypchnięcie gałęzi i otwarcie pull requesta to decyzja programisty po review. Jeżeli poprosi, podaj komendę, nie wykonuj jej w ramach tego skilla.
- **Niezacommitowane zmiany** w repozytorium przed startem to własność programisty: nie dotykaj ich, nie dodawaj do commitów skilla (`git add` tylko plików, które skill zmienił) i zapytaj, czy kontynuować.
- **Bez zmian poza planem.** Refaktoryzacja sąsiedniego kodu, porządki, aktualizacje zależności i „przy okazji” nie wchodzą do zadania. Jeżeli krok wymaga zmiany, której plan nie przewiduje, to odstępstwo — zapisz je w dzienniku i, gdy zmienia zakres, zapytaj.
- **Bez nowych zależności bez pytania.** Nowa biblioteka w `build.gradle(.kts)` albo w katalogu wersji wymaga zgody, z uzasadnieniem, dlaczego obecny stos nie wystarcza.
- Nie wpisuj do kodu, testów, dziennika ani commitów haseł, tokenów i danych osobowych z analizy.

## Process

1. **Ustal klucz zadania** z argumentu albo z nazwy bieżącej gałęzi (`feature/PROJ-123-opis` → `PROJ-123`). Drugi argument, jeżeli jest, to numer kroku: wykonaj tylko ten krok (po sprawdzeniu, że kroki, od których zależy, są w dzienniku oznaczone jako zrobione, a gdy nie są — zapytaj). Bez klucza zapytaj.
2. **Wczytaj plan i dziennik.** Znajdź `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` w bieżącym repozytorium, a gdy go tam nie ma — w repozytoriach sąsiednich w katalogu roboczym (plan leży w repozytorium wiodącym). Brak planu kończy skill (patrz „When to Use”). Wczytaj z planu: kroki z zależnościami, grupy równoległe, macierz wymagań i testów, „Model danych”, „Rozstrzygnięte pytania”, „Otwarte pytania do analityka”. Wczytaj lokalną kopię analizy. Jeżeli istnieje `IMPLEMENTATION_LOG/<KLUCZ>.md`, to kontynuacja: przejmij status kroków z dziennika, a nie z stanu kodu, i zacznij od pierwszego kroku bez statusu „zrobiony” lub „pominięty”.
3. **Sprawdź, czy plan jest aktualny.** Jeżeli w sesji jest dostęp do Jiry i Confluence (narzędzia MCP, CLI albo REST API z tokenem — tak samo jak w `planning-jira-implementation`), pobierz komentarze do zadania i do strony analizy nowsze niż data pobrania kopii z nagłówka planu. Komentarz, który zmienia wymaganie, krok albo model danych, zatrzymuje skill: pokaż go i zapytaj, czy najpierw zaktualizować plan (`planning-jira-implementation`), czy wykonać krok według komentarza i zapisać odstępstwo w dzienniku. Bez dostępu zapisz w dzienniku, że aktualności planu nie sprawdzono. Kroki zależne od pytania z „Otwartych pytań do analityka” bez odpowiedzi wykonuj dopiero po pytaniach z kroku 5 — nie zgaduj odpowiedzi.
4. **Przygotuj repozytoria.** Dla każdego repozytorium wymienionego w krokach planu:
   - sprawdź `git status`; niezacommitowane zmiany zgłoś i zapytaj (kontynuować obok nich, czy przerwać);
   - znajdź gałąź z kluczem zadania (`git branch -a --list "*<KLUCZ>*"`) i przełącz się na nią; jeżeli nie istnieje, utwórz ją od aktualnej gałęzi bazowej (`origin/HEAD`, a gdy plan wskazuje inną gałąź docelową — tej) według konwencji nazw już obecnych w repozytorium (`git branch -r` — na przykład `feature/<KLUCZ>-<krótki-opis>`);
   - ustal komendę testów i budowania: Gradle wrapper (`./gradlew test`, `./gradlew check` albo zadanie, którego używa CI w repozytorium — sprawdź pliki potoku), oraz czy testy integracyjne wymagają uruchomionej bazy (Testcontainers nie wymaga; profil wskazujący na `localhost` wymaga — wtedy postaw bazę tak, jak opisuje `SMOKE_TEST/srodowisko.md`, jeżeli istnieje, albo zapytaj);
   - uruchom testy modułów, których dotyczą kroki, **przed pierwszą zmianą** i zapisz wynik w dzienniku. Testy czerwone przed startem nie są częścią zadania — zapisz je i nie naprawiaj, chyba że krok planu tego dotyczy.
5. **Zbierz pytania przed kodowaniem.** Przejdź wszystkie kroki do wykonania i dla każdego sprawdź, czy da się go wykonać tak, jak jest napisany: czy wskazana klasa, pakiet, tabela i kontrakt istnieją tam, gdzie mówi plan; czy wiersze macierzy przypisane do kroku mają oczekiwany wynik; czy krok nie zależy od otwartego pytania. Wątpliwości zadaj razem, jednym zestawem, w formacie z „Format pytań”, zanim zmienisz pierwszy plik. Odpowiedzi zapisz w dzienniku w sekcji „Pytania”.
6. **Wykonaj kroki w kolejności zależności.** Krok z grupy równoległej wykonuj po kolei z pozostałymi z tej grupy, chyba że programista uruchomił osobne sesje z numerami kroków (argument drugi). Jeżeli krok w jednym repozytorium zależy od zmienionej biblioteki z innego (na przykład kontraktu API), opublikuj bibliotekę do Maven Local (`./gradlew publishToMavenLocal`) i sprawdź, że usługa buduje się z tą wersją — bez zmian w plikach budowania; niezgodność wersji to pytanie. Dla każdego kroku:
   1. **Przeczytaj kontekst.** Krok planu, wiersze macierzy z pola „Testy (pisane przed kodem)”, fragment analizy wskazany w „Źródle wymagania” (po odnośniku `ścieżka:linia` do lokalnej kopii), oraz sąsiedni kod: klasy w pakiecie docelowym, istniejące testy w tym pakiecie (klasa bazowa testów integracyjnych, nazewnictwo, sposób tworzenia danych), mapper i konfiguracja MapStruct, katalog changesetów Liquibase i to, jak jest dołączony do changeloga. Konwencje bierzesz z kodu, nie z pamięci.
   2. **Napisz testy** dla każdego wiersza macierzy przypisanego do kroku, w klasie i metodzie z macierzy (albo w nazwie zgodnej z konwencją pakietu, jeżeli macierz podała nazwę, której tam nie ma — zapisz różnicę w dzienniku). Test sprawdza regułę i jej oczekiwany wynik z analizy, a nie tylko to, że metoda się wykonuje. Wiersz „brak testu” z uzasadnieniem w macierzy nie dostaje testu.
   3. **Uruchom testy i potwierdź, że są czerwone** z powodu brakującej implementacji (błąd kompilacji brakującej klasy też się liczy). Test, który przechodzi od razu, nic nie sprawdza: albo zachowanie już istnieje (zapisz w dzienniku i zapytaj, czy krok jest potrzebny), albo test jest źle napisany (popraw).
   4. **Napisz kod** — najmniejszą zmianę, która spełnia testy i opis kroku, według tabeli „Standardy projektu w praktyce”. Nie dodawaj zachowań, których nie wymaga żaden wiersz macierzy ani opis kroku (dodatkowa walidacja, dodatkowe pole w odpowiedzi, „na przyszłość”). Jeżeli krok wymaga zmiany, której plan nie przewidział (brakująca migracja, dodatkowa klasa w innym pakiecie, poprawka w innym repozytorium), to **odstępstwo**: wykonaj je, gdy bez niego krok nie działa i nie zmienia ono zakresu, i zapisz w dzienniku z przyczyną; gdy zmienia zakres albo model danych — zapytaj.
   5. **Uruchom testy kroku, a potem testy całego modułu.** Zielone testy kroku i brak nowych czerwonych w module zamykają krok. Nowy czerwony test spoza kroku to skutek Twojej zmiany — napraw w ramach kroku, a jeżeli naprawa wymaga zmiany, której plan nie przewiduje, zapisz odstępstwo. Nie wyłączaj, nie usuwaj i nie oznaczaj testów jako ignorowane.
   6. **Przejdź zmienione pliki checklistą** z „Standardów projektu w praktyce” i „Zanim zamkniesz krok”. Popraw, co widać, zanim zacommitujesz.
   7. **Zacommituj krok** (`git add` tylko plików zmienionych w kroku, dziennik osobno w kroku 8). Komunikat według konwencji z `git log` repozytorium; gdy jej nie widać: pierwsza linia `<KLUCZ> <tryb rozkazujący, co zmienia>` (na przykład `PROJ-123 Add payment schedule validation`), w treści numer kroku planu i identyfikatory wierszy macierzy, które krok realizuje. Jeden krok to jeden commit; krok w dwóch repozytoriach to dwa commity o tej samej treści.
   8. **Zapisz postęp w dzienniku** po każdym kroku, nie na końcu — sesja może się urwać.
7. **Po ostatnim kroku** uruchom pełne budowanie z testami w każdym zmienionym repozytorium (zadanie z CI, a gdy go nie ma — `./gradlew check`), i przejdź macierz wiersz po wierszu: każdy wiersz ma zielony test w kodzie albo uzasadnienie „brak testu” z planu. Wiersz bez jednego i drugiego to niezamknięty krok — wróć do niego. Wypisz w dzienniku pliki zmienione w zadaniu, które nie należą do żadnego kroku planu (powinny być tylko odstępstwami już opisanymi).
8. **Zgłoś się w czacie:** ścieżka dziennika, kroki zrobione / pominięte / zablokowane, liczba commitów w każdym repozytorium, liczba odstępstw od planu, wiersze macierzy bez zielonego testu, wynik pełnego budowania. Zaproponuj następne kroki łańcucha: `/java-backend:java-code-review <KLUCZ>` (review przed pull requestem) i `/java-backend:smoke-testing-locally <KLUCZ>`. Nie pushuj.

## Standardy projektu w praktyce

Te same sześć standardów sprawdza później `java-code-review`. Tu są zapisane od strony pisania kodu.

| # | Standard | Jak pisać |
|---|---|---|
| 1 | Package by feature | Nowa klasa trafia do pakietu funkcjonalności wskazanego w „Modelu danych” planu, nie do pakietu warstwy (`controller`, `service`, `repository`). Klasa jest pakietowa (bez `public`), chyba że jest używana spoza pakietu — wtedy sprawdź, czy w pakiecie jest już inna klasa `public`; dwie publiczne klasy to sygnał, że funkcjonalność potrzebuje podpakietu. |
| 2 | jOOQ dla odczytów | Odczyt na potrzeby odpowiedzi, raportu, listy, paginacji albo złączenia piszesz w jOOQ i zwracasz rekord lub obiekt transferowy, nie encję JPA. Encję JPA wczytujesz tylko wtedy, gdy zaraz ją zmienisz. Wygenerowane klasy jOOQ dla nowej tabeli pojawiają się po migracji — sprawdź, jak repozytorium generuje kod jOOQ (zadanie Gradle), i uruchom je po dodaniu changesetu. |
| 3 | JPA/Hibernate dla zapisów | Wstawienie, zmiana i usunięcie idą przez encję i `JpaRepository` (albo `EntityManager`), z dirty checkingiem i blokowaniem optymistycznym, jeżeli encja je ma. Nie piszesz `insertInto`, `update`, `deleteFrom` w jOOQ ani ręcznego SQL. Granica transakcji na metodzie serwisu, nie na kontrolerze. |
| 4 | MapStruct | Mapowanie między encją, rekordem jOOQ, obiektem transferowym i klasą kontraktu to interfejs `@Mapper(config = MapStructConfig.class)` w pakiecie funkcjonalności. Nie przepisujesz pól ręcznie w serwisie ani w kontrolerze. Nowe pole w kontrakcie oznacza nowe pole w mapperze — kompilacja z `unmappedTargetPolicy = ERROR` (jeżeli konfiguracja ją ma) powie, czego brakuje. |
| 5 | Brak zbędnych interfejsów | Serwis z jedną implementacją to klasa, bez pary `XxxService` i `XxxServiceImpl`. Interfejsy frameworka (`JpaRepository`, mapper MapStruct) to nie wyjątek od zasady, tylko jej poprawne użycie. |
| 6 | Changesety Liquibase | Nowy plik w katalogu changesetów dostaje kolejny numer bez luki i duplikatu (`NNN-opis.sql`; sprawdź też numery na gałęzi bazowej i w otwartych gałęziach, jeżeli repozytorium je ma). Nagłówek: `-- liquibase formatted sql`, `-- changeset <autor>:<unikalny-identyfikator>`, `-- comment: <co zmienia>`. Zapis danych idempotentny (`ON CONFLICT DO NOTHING` albo warunek). Sprawdź, jak katalog jest dołączony do changeloga: `includeAll` nie wymaga nic, jawny `include: file:` wymaga wpisu — bez niego changeset nigdy się nie wykona. Po migracji wygeneruj kod jOOQ (standard 2). |

Obok standardów: walidacja wejścia na granicy (adnotacje na obiekcie żądania albo walidacja w serwisie, zgodnie z tym, jak robi to pakiet obok); kody błędów i komunikaty dokładnie takie, jak w analizie; autoryzacja endpointu (`@PreAuthorize` albo mechanizm z sąsiednich kontrolerów) z testem 403, jeżeli analiza opisuje uprawnienia; parametryzowane zapytania; brak logowania danych osobowych.

## Zanim zamkniesz krok

- Każdy wiersz macierzy z pola „Testy (pisane przed kodem)” ma zielony test, który był czerwony przed implementacją.
- Nazwy testów mówią, jaką regułę sprawdzają (`shouldReject_whenAmountExceedsLimit`), zgodnie z konwencją pakietu.
- Zachowanie, którego nie ma w macierzy ani w opisie kroku, nie weszło do kodu — albo jest w dzienniku jako odstępstwo.
- Nowe klasy leżą w pakiecie funkcjonalności i są `public` tylko z powodu.
- Odczyt przez jOOQ, zapis przez JPA, mapowanie przez MapStruct, bez interfejsu dla jednej implementacji.
- Changeset ma numer, nagłówek, idempotentny zapis danych i jest dołączony do changeloga; kod jOOQ wygenerowany.
- Kontrakt (ścieżka, metoda, nazwy i typy pól, wymagalność, wartości enumów) zgadza się z analizą co do znaku.
- Testy modułu zielone, nic nie zignorowane, nic nie usunięte.
- Commit zawiera tylko pliki kroku; dziennik zaktualizowany.

## Format pytań

Taki sam jak w `planning-jira-implementation`: **cytat** (z planu, analizy albo kodu), **skąd** (`IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md:<linia>`, `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md:<linia>` albo `ścieżka/Plik.java:<linia>`), **co jest niejasne** (jedno zdanie), **hipoteza** do potwierdzenia jednym słowem, z wariantami, gdy jest ich kilka. Pytania zbieraj i zadawaj zestawem: przed pierwszą zmianą (krok 5) i w trakcie tylko wtedy, gdy blokują bieżący krok.

Przykład:

```
Pytanie 1 — krok 3, model danych

Cytat (plan, krok 3):
> Dodaj pole `settlement_date` do encji `PaymentScheduleEntity`.

Skąd: IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_PROJ-777.md:58
W kodzie: encja `PaymentScheduleEntity` (com.firma.payments.schedule) ma już
pole `settledAt` typu `Instant` — src/main/java/.../PaymentScheduleEntity.java:41.

Niejasne: czy `settlement_date` z analizy to to samo pole, czy nowe.

Hipoteza: to samo pole — używam `settledAt`, bez migracji; w dzienniku
zapisuję odstępstwo od kroku 3.
Warianty: (a) to samo pole, (b) nowe pole `settlement_date` typu DATE obok.
```

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Nie ma planu implementacji | Nie implementuj — zaproponuj `/java-backend:planning-jira-implementation <KLUCZ>`. |
| Komentarz w Jirze lub Confluence nowszy niż plan zmienia wymaganie | Zatrzymaj się, pokaż komentarz, zapytaj: aktualizacja planu czy odstępstwo. |
| Repozytorium ma niezacommitowane zmiany | Zapytaj, czy pracować obok nich, czy przerwać. Nie dodawaj ich do commitów. |
| Klasa, tabela lub pakiet z planu nie istnieje tam, gdzie plan mówi, a w kodzie jest odpowiednik pod inną nazwą | Zapytaj, z cytatem kroku i hipotezą (odpowiednik, który znalazłeś). |
| Krok wymaga drobnej zmiany spoza planu, bez której nie działa (brakujący import changelogu, dodatkowa metoda w mapperze) | Nie pytaj — zrób i zapisz odstępstwo w dzienniku. |
| Krok wymaga zmiany, która zmienia zakres albo model danych (nowa tabela, nowy endpoint, zmiana kontraktu) | Zapytaj. |
| Test z macierzy przechodzi przed implementacją | Sprawdź test; jeżeli jest poprawny, zapytaj, czy krok jest potrzebny. |
| Testy modułu były czerwone przed Twoją pierwszą zmianą | Nie naprawiaj — zapisz w dzienniku; pytaj tylko, gdy blokują uruchomienie testów kroku. |
| Potrzebna nowa zależność | Zapytaj, z uzasadnieniem, dlaczego obecny stos nie wystarcza. |
| Testy integracyjne wymagają bazy, a nie ma jej jak uruchomić | Zapytaj, z hipotezą (plik docker compose z `SMOKE_TEST/srodowisko.md` albo znaleziony w repozytoriach). |
| Krok zależy od otwartego pytania do analityka bez odpowiedzi | Zapytaj programistę, czy odpowiedź już jest; bez niej oznacz krok „zablokowany” i idź dalej z krokami niezależnymi. |
| Wersja zmienionej biblioteki nie trafia do usługi | Zapytaj, nie zmieniaj plików budowania. |
| Programista prosi o push albo pull request | Podaj komendę, nie wykonuj jej w ramach skilla. |
| Odpowiedź jest w planie, w „Rozstrzygniętych pytaniach”, w lokalnej kopii analizy albo w sąsiednim kodzie | Nie pytaj — użyj jej i podaj źródło w dzienniku. |

## Output

**Język:** polski, zwykłym językiem, bez skrótowców.

**Kod i commity:** na gałęzi zadania w każdym repozytorium z planu, jeden commit na krok.

**Dziennik:** `IMPLEMENTATION_LOG/<KLUCZ-ZADANIA>.md` w repozytorium wiodącym (tam, gdzie leży plan). Aktualizowany po każdym kroku. Commitowany razem z krokiem, którego dotyczy, chyba że repozytorium ma `IMPLEMENTATION_LOG/` w `.gitignore` — wtedy zostaje lokalny. Kontynuacja w nowej sesji czyta z niego status kroków.

**Szablon dziennika:**

```markdown
# Implementacja – <KLUCZ-ZADANIA>: <tytuł zadania>

Plan: `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` (data planu: <data z nagłówka planu>)
Aktualność planu: <sprawdzono <data>, brak nowych komentarzy | nowe komentarze: <lista, decyzja> | nie sprawdzono — brak dostępu>
Repozytoria: <nazwa (gałąź, gałąź bazowa, komenda testów)>, ...
Testy przed startem: <repozytorium: zielone | czerwone: <lista testów>>

## Kroki

| Krok | Tytuł | Repozytorium | Status | Commit | Testy (wiersze macierzy) |
|---|---|---|---|---|---|
| 1 | <tytuł z planu> | <repo> | zrobiony | `<skrócony hash>` | REG-01 zielony, AC-1 zielony |
| 2 | <tytuł> | <repo> | w trakcie | — | REG-02 czerwony (test napisany) |
| 3 | <tytuł> | <repo> | zablokowany — pytanie 2 | — | — |
| 4 | <tytuł> | <repo> | pominięty — <przyczyna, kto zdecydował> | — | — |

## Odstępstwa od planu

| Nr | Krok | Co zrobiono inaczej | Przyczyna | Zakres | Plik |
|---|---|---|---|---|---|
| 1 | 3 | użyto istniejącego pola `settledAt` zamiast nowego `settlement_date` | pole już istnieje | bez zmiany zakresu, potwierdzone (pytanie 1) | `src/main/java/.../PaymentScheduleEntity.java:41` |

## Pytania

### Pytanie 1 — <krok, temat>

<cytat, skąd, co niejasne, hipoteza — jak w „Format pytań”>

**Odpowiedź (<kto>, <data>):** <treść>

## Macierz wymagań i testów — stan

| ID | Test | Stan | Krok |
|---|---|---|---|
| REG-01 | `PaymentScheduleIT.shouldReject_whenDueDateInPast` | zielony, był czerwony przed krokiem 3 | 3 |
| REG-02 | brak testu — uzasadnienie z planu | — | 2 |

## Pliki spoza kroków planu

<pliki zmienione w zadaniu, które nie należą do żadnego kroku, z numerem odstępstwa — albo „brak”>

## Wynik końcowy

<data; pełne budowanie: repozytorium → zielone / czerwone (co); kroki zrobione / pominięte / zablokowane; następny krok: review>
```

## Częste błędy

- Implementowanie z opisu zadania w Jirze albo ze strony Confluence, bo planu nie ma — plan jest tam, gdzie padają pytania i powstaje macierz; bez niego wróć do planowania.
- Pisanie kodu przed testem albo test napisany po kodzie, „żeby był” — test ma być czerwony przed implementacją, a jego kolor przed i po jest w dzienniku.
- Test, który wywołuje metodę i sprawdza, że nie rzuca wyjątku, zamiast sprawdzić regułę i oczekiwany wynik z analizy.
- Nazwy testów i klas z pamięci zamiast z konwencji sąsiedniego kodu w pakiecie.
- Dodanie „przy okazji” walidacji, pola albo refaktoryzacji, których nie wymaga żaden wiersz macierzy — review zgłosi to jako zachowanie spoza wymagań.
- Ciche dopasowanie planu do kodu (inna tabela, inne pole, inny pakiet) bez wpisu w odstępstwach i bez pytania, gdy zmienia to zakres.
- Odczyt przez `JpaRepository.findAll()` zwracany jako odpowiedź, zapis przez jOOQ, ręczne przepisywanie pól zamiast MapStruct, para `Service` i `ServiceImpl`.
- Changeset z numerem już zajętym na gałęzi bazowej, bez nagłówka, bez idempotentnego zapisu albo w katalogu wymagającym jawnego `include:`, którego nie dodano.
- Brak ponownego wygenerowania kodu jOOQ po migracji — kompilacja przechodzi na starych klasach, a kod nie widzi nowej kolumny.
- Naprawianie testów, które były czerwone przed startem, albo wyłączanie testów, które poczerwieniały po zmianie.
- Jeden commit na całe zadanie albo commit obejmujący pliki spoza kroku — review przyrostowy w `reviewing-java-commits` pracuje po commitach.
- `git push`, otwarcie pull requesta, `rebase` albo `reset --hard` w ramach skilla.
- Dziennik aktualizowany dopiero na końcu — po urwanej sesji kolejna zaczyna od zera.
- Kontynuacja na podstawie stanu kodu zamiast dziennika, przez co krok „w trakcie” z napisanymi testami liczy się jako zrobiony.
- Zmiana plików budowania, żeby usługa widziała zmienioną bibliotekę, zamiast publikacji do Maven Local i pytania, gdy wersje się nie zgadzają.
