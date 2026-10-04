---
name: planning-jira-implementation
description: Use when asked to turn a Jira ticket/issue into a backend implementation plan, or to plan how a Jira issue should be implemented before writing code. This team implements backend only, using jOOQ/Hibernate and a package-by-feature structure, and treats the ticket's linked system-analysis document (usually Confluence) as the source of truth, not the ticket description alone. The plan includes a requirements-to-tests matrix: every business rule (REG) and acceptance criterion gets an ID, a source line and a test planned before the code.
disable-model-invocation: false
---

# Planning Jira Implementation

## Overview

Turns one Jira issue into a step-by-step backend implementation plan, sourced from the issue and the system-analysis document it links to (the actual source of truth), saved as `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md`, with a local markdown copy of the analysis cached alongside it so questions can cite it by line. Never guess at requirements or the data model — stop and ask the developer whenever the source material is missing, contradictory, or doesn't match what already exists in the codebase.

## When to Use

- User gives a Jira key or link (or says "to zadanie", "ten ticket") and asks for an implementation plan, or "jak to zaimplementować".
- Scope is backend only. If the ticket also describes frontend/UI behavior, plan only the backend portion and list the rest under "Poza zakresem" in the output — do not plan frontend steps.
- This skill only produces the plan file, it does not write code.

## Dostęp do Jiry i Confluence

Skill nie zależy od konkretnego serwera MCP ani narzędzia. Przed krokiem 1 sprawdź, czym dysponujesz w bieżącej sesji, i użyj pierwszej dostępnej opcji:

1. **Narzędzia MCP do Jiry i Confluence** — dowolny skonfigurowany serwer (na przykład `mcp-atlassian`, oficjalny serwer Atlassian Rovo albo inny). Rozpoznaj je po nazwach narzędzi zawierających `jira`, `confluence` lub `atlassian`. Jeśli narzędzia są dostępne tylko jako odroczone (deferred), najpierw załaduj ich schematy przez wyszukiwarkę narzędzi.
2. **Narzędzie wiersza poleceń**, jeśli jest zainstalowane i zalogowane (na przykład `acli` albo `jira`).
3. **REST API Atlassiana** przez `curl`, jeśli w środowisku są ustawione adres instancji i token (na przykład zmienne `JIRA_URL`, `JIRA_API_TOKEN`, `CONFLUENCE_URL`). Nie wypisuj tokenu w odpowiedziach ani w pliku planu.

Jeśli nie ma żadnego dostępu, zatrzymaj się i poproś użytkownika o wklejenie treści zadania oraz analizy systemowej (razem z komentarzami) albo o skonfigurowanie dostępu. Nie planuj na podstawie samego klucza zadania.

Kroki poniżej opisują, **jakie dane** pobrać. Konkretną nazwę narzędzia lub endpointu dobierz do dostępnej opcji.

## Process

1. **Pobierz zadanie Jira** razem z komentarzami i linkami zewnętrznymi (remote links / web links). Zbierz opis, kryteria akceptacji, powiązane zadania/epik oraz linki zewnętrzne — link do analizy systemowej bywa dodany jako "web link" w Jirze, a nie tylko wklejony w treści opisu.
2. **Znajdź link do analizy systemowej.** Szukaj adresu Confluence w opisie zadania, w komentarzach Jiry i w linkach zewnętrznych zadania. Jeżeli żadnego linku nie ma — **zatrzymaj się i zapytaj użytkownika o link do analizy systemowej**. Nie planuj na podstawie samego opisu zadania z Jiry — to nie jest źródło prawdy, źródłem prawdy jest analiza systemowa.
3. **Pobierz analizę systemową** (treść strony Confluence) oraz **komentarze do niej**, zarówno zwykłe (footer), jak i inline. Jeśli wybrane narzędzie nie udostępnia komentarzy inline, zaznacz w planie, że nie zostały sprawdzone. Jeśli link prowadzi donikąd (strona przeniesiona/usunięta), spróbuj odnaleźć ją przez wyszukiwanie w Confluence (po tytule lub kluczu zadania), zanim zapytasz użytkownika.
4. **Zapisz lokalną kopię analizy** do `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` (utwórz folder `.analiza`, jeśli nie istnieje). Dzięki tej kopii cytujesz analizę przez `ścieżka:linia`, a programista czyta ją w edytorze obok terminala, zamiast szukać fragmentu w przeglądarce.
   - Zapisz treść strony jako markdown i **zachowaj nagłówki sekcji z oryginału** — po nich budujesz anchory do linkowania w pytaniach.
   - Komentarze wstaw przy akapitach, do których należą: komentarz inline bezpośrednio pod cytowanym fragmentem (wyraźnie oznaczony, na przykład `> [komentarz inline – <autor>, <data>] ...`), komentarze footer w sekcji `## Komentarze` na końcu pliku.
   - Na początku pliku zapisz nagłówek: link do strony Confluence, tytuł, datę pobrania i informację, czy komentarze inline udało się pobrać.
   - Plik jest cache'em, nie źródłem prawdy. Jeśli już istnieje dla tego zadania, nadpisz go świeżo pobraną treścią.
   - Jeśli repozytorium ma `.gitignore`, dopisz do niego `IMPLEMENTATION_PLAN/.analiza/`, jeśli jeszcze go tam nie ma — to lokalny cache, a nie artefakt do commitowania.
5. **Zestaw źródła ze sobą:** opis zadania, komentarze Jiry, treść analizy, komentarze do analizy. Traktuj analizę systemową jako źródło prawdy o wymaganiach, ale nowszy komentarz korygujący jej treść ma pierwszeństwo przed nieaktualnym fragmentem głównego dokumentu. Jeśli źródła są sprzeczne w sposób zmieniający zakres lub kształt rozwiązania, a żaden komentarz tego nie rozstrzyga — nie wybieraj samodzielnie która wersja obowiązuje, zapytaj użytkownika.
6. **Wypisz wymagania.** Z analizy i zadania wypisz każdą regułę biznesową (REG) i każde kryterium akceptacji jako osobną pozycję z identyfikatorem i źródłem:
   - Reguły z analizy mają identyfikatory nadane przez analityka (na przykład `REG-03`) — użyj ich bez zmian. Jeżeli analiza opisuje regułę bez identyfikatora, nadaj własny w formacie `W-1`, `W-2` i zaznacz w planie, że identyfikator nadano w planie, a nie w analizie.
   - Kryteria akceptacji z Jiry oznacz `AC-1`, `AC-2` w kolejności z zadania, chyba że zadanie ma własną numerację.
   - Źródłem reguły jest odnośnik do lokalnej kopii analizy w formacie `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md:<linia>`, a kryterium akceptacji — „zadanie Jira, kryteria akceptacji, punkt N”. Jeżeli regułę zmienia komentarz, podaj odnośnik do linii komentarza w lokalnej kopii.
   - Wypisuj tylko wymagania dotyczące backendu. Reguły czysto frontendowe trafiają do sekcji „Poza zakresem”.
   Ta lista staje się wierszami macierzy wymagań i testów (krok 9).
7. **Sprawdź model danych.** Ustal, jakie encje/tabele/pola opisuje zadanie lub analiza, i poszukaj w kodzie projektu (klasy encji, definicje tabel jOOQ, migracje SQL) odpowiadającej im, już istniejącej struktury.
   - Jeśli istniejący model pasuje — w planie podaj dokładnie, gdzie w kodzie on się znajduje (pakiet, klasa, tabela), żeby programista tego nie szukał od nowa.
   - Jeśli model z zadania lub analizy **nie pasuje** do tego, co jest w kodzie (inna nazwa tabeli, inne pola, kolizja z tabelą używaną już przez inną funkcjonalność), **a ani zadanie, ani analiza, ani żaden komentarz tego nie tłumaczy** — zatrzymaj się i zapytaj programistę, gdzie jest właściwy model danych. Nie zakładaj samodzielnie, że trzeba stworzyć nową tabelę czy encję.
8. **Rozbij pracę na kroki.** Każdy krok to jedna, konkretna, możliwa do zweryfikowania zmiana (na przykład: dodanie migracji SQL, dodanie metody w konkretnej klasie, implementacja jednego endpointu kontraktu w konkretnym repozytorium). Dla każdego kroku podaj: repozytorium/moduł, od czego zależy (numery innych kroków) i czy może iść równolegle z innym krokiem.
9. **Zbuduj macierz wymagań i testów.** Dla każdego wymagania z kroku 6 ustal:
   - **typ testu** — test integracyjny (IT), gdy reguła przechodzi przez bazę danych, kontrakt HTTP, kody statusu, migrację Liquibase albo transakcję; test jednostkowy, gdy reguła jest czystą logiką bez zależności zewnętrznych;
   - **proponowaną klasę i metodę testu** — według konwencji już obecnych w repozytorium. Zanim zaproponujesz nazwę, sprawdź istniejące testy w tym pakiecie (przyrostek `Test` albo `IT`, wspólne klasy bazowe testów integracyjnych, sposób nazywania metod) i trzymaj się ich. Nazwa metody ma mówić, jaką regułę weryfikuje, na przykład `shouldReject_whenAmountExceedsLimit`;
   - **krok planu**, który realizuje to wymaganie.
   Każdy krok implementacyjny dostaje pole „Testy (pisane przed kodem)” z identyfikatorami wierszy macierzy, które ten krok ma pokryć. Test powstaje przed kodem, który go spełnia. Wymaganie bez przypisanego testu musi mieć w macierzy jawne uzasadnienie (na przykład „wymusza to ograniczenie unikalności w bazie danych dodane w kroku 2, sprawdzane testem `...` z wiersza REG-02”). Jeżeli uzasadnienia nie ma, bo nie wiadomo, jak regułę sprawdzić (reguła jest nieostra, nie ma oczekiwanego wyniku), wymaganie trafia do pytań w kroku 11.
10. **Wyznacz grupy równoległe.** Dwa kroki mogą iść równolegle, jeśli żaden z nich nie czeka na wynik drugiego. Typowy przypadek z tego projektu: gdy kształt kontraktu (np. specyfikacja API) został ustalony jako osobny, wcześniejszy krok, to implementacja w repozytorium dostarczającym kontrakt i implementacja w repozytorium, które ten kontrakt konsumuje, mogą iść równolegle — obie strony pracują od ustalonego kształtu kontraktu, nie czekając na scalenie kodu tej drugiej strony. Oznacz takie grupy jawnie w planie.
11. **Zbierz wszystkie pytania i zadaj je przed zapisaniem planu**, jeśli poprzednie kroki wygenerowały wątpliwość (brak linku do analizy, sprzeczne źródła, niedopasowany model danych, niejasny podział na repozytoria, wymaganie bez sposobu sprawdzenia testem). Zadaj je razem, jednym zestawem, zanim zapiszesz plik — nie publikuj planu opartego na założeniach, które dało się łatwo zweryfikować pytaniem. **Każde pytanie musi przyjść z dowodem** w formacie z sekcji "Format pytań" — programista nie ma odtwarzać kontekstu, który już masz w sesji. Zanim zapytasz:
    - przeszukaj lokalną kopię analizy i komentarze — nie zadawaj pytania, na które odpowiedź jest w pobranych źródłach;
    - sprawdź, czy w katalogu głównym repozytorium istnieje raport z analizy wykonalności tej strony (`ANALIZA_WYKONALNOSCI/<KLUCZ-ZADANIA>.md` albo plik nazwany tytułem strony Confluence) z sekcją „Pytania do analityka”. Pytania, które już tam są, nie są zadawane ponownie. Jeżeli komentarze pod stroną lub w zadaniu zawierają odpowiedź analityka — zastosuj ją i zaznacz źródło. Jeżeli odpowiedzi nadal nie ma, wpisz pytanie do sekcji „Otwarte pytania do analityka” w planie, z numerem pytania z raportu wykonalności, i oznacz kroki, które od niego zależą.
    Po otrzymaniu odpowiedzi zapisz każde pytanie razem z odpowiedzią w sekcji „Rozstrzygnięte pytania” planu — to materiał dla retrospektywy zadania.
12. **Zapisz plan** w pliku `IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md` (na przykład `IMPLEMENTATION_PLAN_PROJ-777.md`) w folderze `IMPLEMENTATION_PLAN` w katalogu głównym repozytorium, w którym aktualnie pracujesz. Jeśli folder `IMPLEMENTATION_PLAN` nie istnieje w katalogu głównym repozytorium, utwórz go. Jeśli praca obejmuje kilka repozytoriów, zapisz jeden plan w repozytorium wiodącym dla tej funkcjonalności, a kroki dotyczące pozostałych repozytoriów opisz w tym samym pliku, jawnie podając nazwę repozytorium przy każdym z nich.

## Format pytań

Każde pytanie zadane programiście składa się z czterech elementów:

- **Cytat** — dosłowny fragment (1–3 zdania) analizy, zadania lub komentarza, którego dotyczy wątpliwość.
- **Skąd pochodzi** — nazwa sekcji plus link do anchora na stronie Confluence (`<link-strony>#<Nazwa-Sekcji>`) oraz odnośnik do lokalnej kopii w formacie `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md:<linia>`. Dla komentarza podaj autora i datę. Dla kodu podaj ścieżkę pliku i numer linii.
- **Co jest niejasne** — jedno zdanie.
- **Hipoteza** — Twoja najlepsza odpowiedź, sformułowana tak, żeby programista mógł ją potwierdzić jednym słowem, a nie pisać wyjaśnienie od zera. Jeśli sensownych odpowiedzi jest kilka, wypisz je jako warianty do wyboru.

Przykład:

```
Pytanie 2 — model danych

Cytat (analiza, sekcja "Model danych"):
> Harmonogram zapisujemy w tabeli `payment_schedule` z polami `due_date`,
> `amount_net`, `amount_gross`.

Skąd: https://confluence.firma.pl/pages/12345#Model-danych
      IMPLEMENTATION_PLAN/.analiza/PROJ-777-analiza.md:142
W kodzie: PaymentScheduleEntity (com.firma.payments.schedule), tabela
`payments_schedule` — pole `amount`, bez rozbicia na netto/brutto.

Niejasne: czy analiza opisuje nową tabelę, czy rozszerzenie istniejącej.

Hipoteza: rozszerzamy istniejącą `payments_schedule` (migracja dodająca
`amount_net`/`amount_gross`), bo nazwa i przeznaczenie się pokrywają.
Warianty: (a) rozszerzyć istniejącą, (b) nowa tabela obok istniejącej.
```

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Zadanie nie zawiera linku do analizy systemowej | Zapytaj o link — nie planuj na podstawie samego opisu zadania. |
| Analiza systemowa jest sprzeczna z opisem zadania w sposób zmieniający zakres, a żaden komentarz tego nie rozstrzyga | Zapytaj, które źródło jest aktualne. |
| Komentarz w Jirze lub pod stroną Confluence koryguje treść dokumentu (na przykład zmienia nazwę pola) | Nie pytaj — zastosuj poprawkę z komentarza, ale zaznacz w planie, że pochodzi z komentarza, a nie z głównej treści dokumentu. |
| Model danych z zadania lub analizy nie pasuje do istniejącego kodu, a nic tego nie tłumaczy | Zapytaj programistę, gdzie jest właściwy model danych — nie zakładaj tworzenia nowej tabeli lub encji. |
| Nie wiadomo, w którym repozytorium ma powstać dany fragment zmiany | Zapytaj, chyba że analiza jednoznacznie to określa. |
| Masz wątpliwość, ale odpowiedź jest w pobranej analizie lub w komentarzach | Nie pytaj — przeszukaj lokalną kopię analizy i użyj tego, co w niej jest. |
| Zadanie opisuje też zmiany frontendowe | Nie pytaj — zaplanuj tylko część backendową, resztę wypisz w sekcji "Poza zakresem". |
| Reguła jest sformułowana tak, że nie da się dla niej zapisać oczekiwanego wyniku testu | Zapytaj, z cytatem reguły i hipotezą oczekiwanego wyniku. |
| Pytanie jest już w sekcji „Pytania do analityka” raportu wykonalności | Nie pytaj ponownie — sprawdź komentarze pod stroną i w zadaniu; bez odpowiedzi wpisz je do „Otwartych pytań do analityka” w planie. |

## Output

**Język:** polski.

**Lokalizacja:** `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md` w katalogu głównym repozytorium (utwórz folder `IMPLEMENTATION_PLAN`, jeśli nie istnieje).

**Plik pomocniczy:** `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` — lokalna kopia analizy systemowej z komentarzami (krok 4). Nie jest częścią planu, służy do cytowania w pytaniach i do czytania obok terminala.

**Szablon:**

```markdown
# Plan implementacji – <KLUCZ-ZADANIA>: <tytuł zadania>

Źródła:
- Zadanie Jira: <link>
- Analiza systemowa: <link>
- Lokalna kopia analizy: `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` (pobrana <data>)
- Istotne komentarze uwzględnione w planie: <krótka lista, z autorem i datą jeśli dostępne>

## Zakres

<krótki opis funkcjonalności backendowej objętej planem>

## Poza zakresem

<elementy z zadania, których ten plan nie obejmuje, na przykład frontend — albo "brak", jeśli całe zadanie jest backendowe>

## Model danych

<gdzie w kodzie żyje odpowiedni model danych, z podaniem pakietu/klasy/tabeli; jeśli programista wskazał to miejsce w odpowiedzi na pytanie, zaznacz to>

## Macierz wymagań i testów

| ID | Wymaganie (cytat albo skrót) | Źródło | Typ testu | Klasa i metoda testu | Krok |
|---|---|---|---|---|---|
| REG-01 | <cytat albo jednozdaniowy skrót reguły> | `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md:<linia>` | IT | `PaymentScheduleIT.shouldReject_whenDueDateInPast` | 3 |
| AC-1 | <treść kryterium akceptacji> | zadanie Jira, kryteria akceptacji, punkt 1 | unit | `ScheduleCalculatorTest.shouldSplitAmountIntoInstallments` | 4 |
| REG-02 | <...> | <...> | brak testu | — uzasadnienie: <dlaczego test nie jest potrzebny albo czym innym jest to wymaganie sprawdzone> | 2 |

## Kroki

### Krok 1: <tytuł>

- **Repozytorium/moduł:** <nazwa>
- **Zależy od:** <numery kroków albo "brak">
- **Może być wykonywany równolegle z:** <numery kroków albo "brak">
- **Testy (pisane przed kodem):** <identyfikatory wierszy macierzy, na przykład "REG-01, AC-1" — albo "brak, krok nie realizuje żadnego wymagania wprost (na przykład konfiguracja)">
- **Opis:** <precyzyjny opis tego, co trzeba zrobić>
- **Źródło wymagania:** <która część analizy, zadania albo komentarza jest podstawą tego kroku>

(kolejne kroki w tym samym formacie, ponumerowane)

## Grupy równoległe

<na przykład: "Krok 2 i krok 3 mogą być realizowane równocześnie w różnych repozytoriach, ponieważ oba zależą tylko od kroku 1 (ustalenie kontraktu), a nie od siebie nawzajem.">

## Rozstrzygnięte pytania

<każde pytanie zadane w trakcie planowania, w skrócie, z odpowiedzią i tym, kto jej udzielił (programista, analityk w komentarzu) — albo "brak">

## Otwarte pytania do analityka

<pytania bez odpowiedzi, z numerem pytania w raporcie `ANALIZA_WYKONALNOSCI/...md`, jeżeli tam występuje, i numerami kroków, które od odpowiedzi zależą — albo "brak">
```

## Częste błędy

- Traktowanie opisu zadania Jira jako źródła prawdy zamiast analizy systemowej, do której zadanie linkuje.
- Pominięcie komentarzy — zarówno w Jirze, jak i pod stroną Confluence — mimo że mogą zmieniać treść analizy.
- Wymyślenie nowej tabeli lub encji "na wszelki wypadek" zamiast zapytania programisty, gdy model danych z zadania nie pasuje do istniejącego kodu.
- Oznaczenie dwóch kroków jako równoległych, mimo że jeden w rzeczywistości czeka na wynik drugiego (na przykład implementacja konsumenta kontraktu, zanim kształt kontraktu został ustalony).
- Zapisanie planu mimo nierozwiązanych wątpliwości, zamiast zapytania użytkownika przed zapisaniem pliku.
- Zadanie pytania bez cytatu i bez odnośnika do miejsca w analizie — programista musi wtedy odtworzyć kontekst, który jest już w sesji.
- Zadanie pytania bez hipotezy, czyli zmuszenie programisty do napisania odpowiedzi od zera, zamiast potwierdzenia lub odrzucenia propozycji.
- Pominięcie kroku 4 (lokalna kopia analizy) i cytowanie analizy "z pamięci", bez odnośnika, który programista mógłby otworzyć.
- Zaplanowanie kroków frontendowych, mimo że ten zespół implementuje wyłącznie backend.
- Pominięcie reguły albo kryterium akceptacji w macierzy wymagań i testów — każda reguła REG i każde kryterium z zadania ma swój wiersz, także te, które wydają się oczywiste.
- Wiersz macierzy bez testu i bez uzasadnienia. Brak testu jest dopuszczalny tylko z jawnym uzasadnieniem, a wymaganie, którego nie wiadomo jak sprawdzić, trafia do pytań.
- Krok implementacyjny bez pola „Testy (pisane przed kodem)” albo z testem, który powstaje w osobnym, późniejszym kroku „napisz testy” — test należy do kroku, który realizuje wymaganie.
- Nazwa testu, która nie mówi, jaką regułę sprawdza (na przykład `testSave`), albo nazwa niezgodna z konwencją testów już obecnych w repozytorium.
- Test jednostkowy zaplanowany dla reguły, która zależy od bazy danych, kodu statusu HTTP albo migracji — taka reguła wymaga testu integracyjnego.
- Ponowne zadanie pytania, które jest już w sekcji „Pytania do analityka” raportu wykonalności dla tej strony.
- Uznanie, że nie ma dostępu do Jiry lub Confluence, tylko dlatego, że brakuje jednego konkretnego serwera MCP — sprawdź wszystkie opcje z sekcji "Dostęp do Jiry i Confluence".
