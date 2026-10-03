---
name: analyzing-confluence-feasibility
description: Use when asked to analyze whether a solution described on a Confluence page (system analysis, specification, design document) is feasible — "analiza wykonalności", "czy da się to zrobić", "sprawdź tę analizę". Produces a feasibility analysis, NOT an implementation plan: it checks the description against the database model (from the document, or from source code when the document does not describe it — then it asks which repository to use), checks the internal consistency of the backend-to-frontend contract described in the document, and checks whether the described business logic can actually be carried out. Polish-language Markdown report with exactly three sections.
disable-model-invocation: false
---

# Analyzing Confluence Feasibility

## Overview

Bierze jedną stronę Confluence opisującą rozwiązanie i odpowiada na pytanie: czy da się to wykonać tak, jak zostało opisane. To nie jest plan implementacji — nie ma tu kroków, kolejności prac, podziału na repozytoria ani szacowania czasu. Są tylko trzy pytania:

1. Czy opis zgadza się z modelem bazy danych?
2. Czy kontrakt między backendem a frontendem opisany w dokumencie jest spójny i kompletny?
3. Czy opisana logika biznesowa daje się wykonać?

Wynik to jeden plik Markdown w języku polskim, napisany zwykłym językiem, bez skrótowców.

## When to Use

- Użytkownik podaje link do strony Confluence (albo jej tytuł) i prosi o sprawdzenie, ocenę albo analizę wykonalności opisanego tam rozwiązania.
- Użytkownik pyta „czy to się da zrobić", „czy ta analiza trzyma się kupy", „czy tu czegoś nie brakuje" w odniesieniu do dokumentu Confluence.
- Nie używaj tego skilla, gdy użytkownik prosi o plan implementacji albo o to, „jak to zaimplementować" — do tego służy skill `planning-jira-implementation`. Jeżeli prośba miesza jedno z drugim, zapytaj, czego użytkownik potrzebuje, zanim zaczniesz pracę.
- Nie używaj tego skilla do przeglądu kodu — do tego służy skill `reviewing-java-commits`.
- Ten skill niczego nie implementuje i nie zmienia kodu. Jedyny plik, jaki tworzy, to raport z analizy.

## Dostęp do Confluence

Skill nie zależy od konkretnego serwera MCP ani narzędzia. Przed krokiem 1 sprawdź, czym dysponujesz w bieżącej sesji, i użyj pierwszej dostępnej opcji:

1. **Narzędzia MCP do Confluence** — dowolny skonfigurowany serwer (na przykład `mcp-atlassian`, oficjalny serwer Atlassian Rovo albo inny). Rozpoznaj je po nazwach narzędzi zawierających `confluence` lub `atlassian`. Jeśli narzędzia są dostępne tylko jako odroczone (deferred), najpierw załaduj ich schematy przez wyszukiwarkę narzędzi.
2. **Narzędzie wiersza poleceń**, jeśli jest zainstalowane i zalogowane (na przykład `acli`).
3. **REST API Atlassiana** przez `curl`, jeśli w środowisku są ustawione adres instancji i token (na przykład zmienne `CONFLUENCE_URL`, `JIRA_API_TOKEN`). Nie wypisuj tokenu w odpowiedziach ani w pliku raportu.

Jeśli nie ma żadnego dostępu, zatrzymaj się i poproś użytkownika o wklejenie treści strony razem z komentarzami albo o skonfigurowanie dostępu. Nie analizuj wykonalności na podstawie samego tytułu albo linku.

Kroki poniżej opisują, **jakie dane** pobrać. Konkretną nazwę narzędzia lub endpointu dobierz do dostępnej opcji. Nazwy narzędzi podane w nawiasach to przykłady z serwera `mcp-atlassian`.

## Process

1. **Ustal stronę Confluence.** Jeżeli użytkownik podał link albo identyfikator strony — pobierz ją (`mcp__mcp-atlassian__confluence_get_page`). Jeżeli podał tylko tytuł albo opis tematu — znajdź stronę przez wyszukiwanie (`mcp__mcp-atlassian__confluence_search`) i upewnij się u użytkownika, że to właściwa strona, zanim zaczniesz analizę. Jeżeli nie podał niczego jednoznacznego — zapytaj o link. Nie analizuj strony wybranej „na wyczucie".
2. **Pobierz komentarze do strony** — zwykłe (`mcp__mcp-atlassian__confluence_get_comments`) i inline (`mcp__mcp-atlassian__confluence_get_inline_comments`). Komentarz często koryguje treść dokumentu: nowszy komentarz poprawiający jakiś fragment ma pierwszeństwo przed nieaktualnym fragmentem głównej treści. Kiedy opierasz ustalenie na komentarzu, a nie na głównej treści, napisz to wprost w raporcie. Jeżeli dostępne narzędzie nie udostępnia komentarzy inline, zaznacz w raporcie, że nie zostały sprawdzone.
3. **Sprawdź strony podrzędne i linkowane**, jeżeli główna strona wyraźnie się do nich odwołuje w sprawach istotnych dla trzech badanych obszarów (na przykład „model danych opisany jest na stronie X", „kontrakt w załączniku Y"). Użyj listy stron podrzędnych (`mcp__mcp-atlassian__confluence_get_page_children`) albo pobierz linkowaną stronę wprost. Nie wciągaj do analizy całej przestrzeni Confluence — tylko to, do czego dokument realnie odsyła.
4. **Wypisz sobie, co dokument obiecuje.** Zanim zaczniesz cokolwiek oceniać, wypisz na własny użytek: jakie dane rozwiązanie zapisuje i odczytuje, jakie wywołania między frontendem a backendem opisuje, oraz jakie reguły biznesowe wprowadza. To jest materiał wejściowy do trzech sekcji analizy.
5. **Obszar pierwszy — model bazy danych.** Postępuj według zasady poniżej:
   - Jeżeli dokument opisuje model danych (tabele, kolumny, encje, powiązania, diagram) — sprawdzaj opis rozwiązania względem tego modelu, bez zaglądania do kodu. Nie proś wtedy o repozytorium.
   - Jeżeli dokument nie opisuje modelu danych — powiedz to użytkownikowi wprost i poproś o wskazanie repozytorium, w którym model żyje. Dopiero mając ścieżkę do repozytorium, szukaj w kodzie klas encji, definicji tabel, migracji bazy danych i porównuj z nimi opis.
   - Jeżeli użytkownik nie wskaże repozytorium, a dokument modelu nie opisuje — nie zgaduj struktury bazy danych. Napisz w tej sekcji raportu, że nie dało się jej zweryfikować, i dlaczego.
   - Czego szukać: pól, które dokument zakłada, a których model nie ma; typów i długości niepasujących do opisanych wartości; wymaganych pól, dla których opis nie mówi, skąd wziąć wartość; powiązań między danymi, których model nie pozwala wyrazić (na przykład opis zakłada wiele rekordów powiązanych z jednym, a model dopuszcza tylko jeden); danych, które opis każe przechowywać, a nie ma dla nich miejsca; unikalności i ograniczeń, które opisany przepływ by naruszył; usuwania albo zmiany danych, do których przywiązane są inne rekordy.
6. **Obszar drugi — kontrakt między backendem a frontendem.** Sprawdzaj wyłącznie na podstawie samego dokumentu Confluence (wraz z komentarzami i stronami, do których dokument odsyła). Nie zaglądaj w tej sekcji do kodu i nie proś o repozytoria — oceniasz spójność i kompletność tego, co zostało opisane.
   - Czego szukać: pól, które frontend ma wyświetlić albo wysłać, a których opis odpowiedzi lub żądania nie zawiera; niezgodności nazw i typów tego samego pola w różnych miejscach dokumentu; braku opisu zachowania przy błędzie (co dostaje frontend, gdy operacja się nie powiedzie); braku informacji o tym, kto inicjuje wywołanie i kiedy; danych, których frontend potrzebuje, a opis nie mówi, którym wywołaniem je pobiera; niejasności, czy pole jest obowiązkowe czy opcjonalne; opisanych ekranów lub akcji użytkownika, którym nie odpowiada żadne wywołanie po stronie backendu; wywołań opisanych po stronie backendu, których nikt nie używa; braku ustaleń dotyczących stronicowania, sortowania i filtrowania tam, gdzie mowa o listach danych.
7. **Obszar trzeci — logika biznesowa.** Sprawdź, czy opisane reguły da się wykonać: czy z opisu wynika jednoznacznie, co ma się wydarzyć w każdej sytuacji, i czy nie wymagają one danych albo zdarzeń, których rozwiązanie nie ma skąd wziąć.
   - Czego szukać: reguł sprzecznych ze sobą; przypadków brzegowych, o których dokument milczy (brak danych, wartość zerowa, pusta lista, użytkownik bez uprawnień, operacja powtórzona drugi raz); warunków opisanych nieostro, na przykład „system powinien odpowiednio zareagować", gdzie nie wiadomo, co znaczy „odpowiednio"; reguł zależnych od czasu, dla których nie ustalono, co jest punktem odniesienia; kolejności operacji, która nie jest zagwarantowana, a od której wynik zależy; sytuacji, w których dwie osoby robią to samo równocześnie; braku opisu, co dzieje się z danymi już istniejącymi w systemie w chwili wdrożenia zmiany; reguł wymagających danych, których według obszaru pierwszego nie ma gdzie przechowywać.
8. **Oceń wagę każdego ustalenia.** Dla każdego znalezionego problemu rozstrzygnij, czy jest to:
   - **Blokada** — w obecnej postaci opisu nie da się tego wykonać, ktoś musi podjąć decyzję albo uzupełnić dokument.
   - **Ryzyko** — da się wykonać, ale przy pewnym założeniu, które może okazać się błędne, albo kosztem czegoś, o czym dokument nie mówi.
   - **Do uzupełnienia** — brak informacji, który nie zatrzymuje prac, ale zostanie zadany jako pytanie w trakcie pracy, jeżeli nie zostanie wyjaśniony wcześniej.
9. **Wskaż miejsce każdego ustalenia.** Każde ustalenie musi wskazywać miejsce w dokumencie (nazwa sekcji, nagłówek, tabela, akapit), którego dotyczy — czytelnik ma je znaleźć bez zgadywania. Jeżeli ustalenie pochodzi z porównania z kodem, podaj też ścieżkę pliku, klasę albo nazwę tabeli.
10. **Zapisz raport** według szablonu z sekcji „Output".
11. **Odpowiedz w czacie:** ścieżka do zapisanego pliku, liczba blokad, ryzyk i braków do uzupełnienia, oraz jedno zdanie o najpoważniejszym ustaleniu.

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Nie wiadomo, o którą stronę Confluence chodzi | Zapytaj o link. Nie wybieraj strony samodzielnie na podstawie podobnego tytułu. |
| Dokument nie opisuje modelu bazy danych | Zapytaj o repozytorium, w którym model żyje. To jedyny moment w tym skillu, w którym pytasz o kod. |
| Dokument opisuje model bazy danych | Nie pytaj o repozytorium — analizuj to, co opisano w dokumencie. |
| Dokument nie opisuje kontraktu między backendem a frontendem | Nie pytaj i nie szukaj kontraktu w kodzie. Napisz w tej sekcji, że dokument tego nie opisuje, i wypisz, jakich ustaleń brakuje. |
| Znaleziono sprzeczność wewnątrz dokumentu, której nie rozstrzyga żaden komentarz | Nie pytaj w trakcie pracy — to jest właśnie wynik analizy. Opisz obie wersje i oznacz jako blokadę albo ryzyko. |
| Komentarz pod stroną koryguje treść dokumentu | Nie pytaj — zastosuj poprawkę z komentarza i zaznacz w raporcie, że pochodzi ona z komentarza, a nie z głównej treści. |
| Użytkownik prosi jednocześnie o analizę wykonalności i o plan implementacji | Zapytaj, czego potrzebuje teraz. Ten skill nie tworzy planów implementacji. |

## Output

**Język:** polski.

**Sposób pisania:** zwykłym językiem, pełnymi zdaniami, bez skrótowców. Nie pisz „np.", „itd.", „itp.", „tzn.", „m.in.", „ok." — wypisz te słowa w całości albo podaj konkretny przykład. Nie pisz „BE", „FE", „API", „DB", „CRUD" — pisz „backend", „frontend", „interfejs programistyczny", „baza danych", i tak dalej. Nie zakładaj, że czytelnik zna dokument na pamięć: opisując problem, przypomnij w jednym zdaniu, co dokument w tym miejscu mówi, a dopiero potem napisz, co jest z tym nie tak i jaka będzie tego konsekwencja.

**Lokalizacja pliku:** `ANALIZA_WYKONALNOSCI/<tytuł-strony>.md` w katalogu głównym repozytorium, w którym pracujesz (utwórz folder `ANALIZA_WYKONALNOSCI`, jeżeli nie istnieje). Tytuł strony zamień na bezpieczną nazwę pliku: spacje i ukośniki na myślniki, bez polskich znaków diakrytycznych. Jeżeli dokument dotyczy konkretnego zadania i jego klucz jest znany, użyj klucza zadania zamiast tytułu, na przykład `ANALIZA_WYKONALNOSCI/PROJ-777.md`. Jeżeli nie pracujesz w żadnym repozytorium, zapytaj użytkownika, gdzie zapisać plik. Ponowna analiza tej samej strony nadpisuje poprzedni plik — data analizy i wersja strony są w nagłówku raportu.

**Szablon** (raport ma dokładnie te trzy sekcje — nie dodawaj podsumowania, wniosków, rekomendacji ani kolejnych kroków jako osobnych sekcji; wszystko, co masz do powiedzenia, mieści się wewnątrz tych trzech obszarów):

````markdown
# Analiza wykonalności – <tytuł strony Confluence>

Strona: <link>
Wersja strony: <numer wersji, jeżeli dostępny>
Data analizy: <RRRR-MM-DD>
Źródło modelu danych: <"opis w dokumencie" albo "kod źródłowy w repozytorium <nazwa>" albo "niezweryfikowany – brak opisu i brak wskazanego repozytorium">

## Zgodność opisu z modelem bazy danych

### 1. <krótki tytuł ustalenia>

- **Waga:** <blokada / ryzyko / do uzupełnienia>
- **Miejsce w dokumencie:** <nazwa sekcji, nagłówek albo tabela>
- **Miejsce w kodzie:** <ścieżka pliku, klasa albo nazwa tabeli — tylko wtedy, gdy model sprawdzano w kodzie>
- **Co mówi dokument:** <jedno, dwa zdania streszczające ten fragment opisu>
- **Na czym polega niezgodność:** <konkretny opis rozbieżności między opisem a modelem danych>
- **Konsekwencja:** <co się stanie, jeżeli zostanie to tak zrealizowane — jakich danych nie da się zapisać, który zapis się nie powiedzie, która informacja zostanie utracona>
- **Co trzeba rozstrzygnąć:** <pytanie do zespołu albo zmiana, która usuwa problem>

(kolejne ustalenia w tym samym formacie, ponumerowane, od najpoważniejszego)

Jeżeli nie znaleziono żadnych niezgodności, napisz to wprost i wypisz, jakie tabele, encje i pola sprawdzono.

## Zgodność implementacji kontraktu pomiędzy backendem a frontendem

### 1. <krótki tytuł ustalenia>

- **Waga:** <blokada / ryzyko / do uzupełnienia>
- **Miejsce w dokumencie:** <nazwa sekcji, nagłówek albo tabela>
- **Co mówi dokument:** <jedno, dwa zdania streszczające opisany fragment kontraktu>
- **Na czym polega problem:** <czego brakuje albo co jest opisane niespójnie — po której stronie, w którym wywołaniu, w którym polu>
- **Konsekwencja:** <co się stanie przy takim opisie — czego frontend nie będzie mógł wyświetlić, jakiego zachowania nikt nie zaimplementuje, gdzie obie strony zrozumieją opis inaczej>
- **Co trzeba rozstrzygnąć:** <pytanie do zespołu albo uzupełnienie dokumentu, które usuwa problem>

(kolejne ustalenia w tym samym formacie, ponumerowane, od najpoważniejszego)

Jeżeli dokument w ogóle nie opisuje kontraktu, napisz to wprost i wypisz, jakich ustaleń brakuje, żeby obie strony mogły pracować równolegle. Jeżeli kontrakt jest opisany spójnie i kompletnie, napisz to i wypisz, które wywołania sprawdzono.

## Zgodność wykonania logiki biznesowej

### 1. <krótki tytuł ustalenia>

- **Waga:** <blokada / ryzyko / do uzupełnienia>
- **Miejsce w dokumencie:** <nazwa sekcji, nagłówek albo reguła>
- **Co mówi dokument:** <jedno, dwa zdania streszczające opisaną regułę>
- **Na czym polega problem:** <sprzeczność, nieostrość albo brak — z podaniem sytuacji, w której to wychodzi>
- **Konsekwencja:** <jaki będzie wynik w tej sytuacji, jeżeli nikt tego nie rozstrzygnie — jaka decyzja zostanie podjęta przypadkowo przez osobę implementującą>
- **Co trzeba rozstrzygnąć:** <pytanie do zespołu albo doprecyzowanie reguły>

(kolejne ustalenia w tym samym formacie, ponumerowane, od najpoważniejszego)

Jeżeli opisana logika jest spójna i wykonalna, napisz to wprost i wypisz, które reguły oraz które przypadki brzegowe sprawdzono.
````

## Częste błędy

- Napisanie planu implementacji zamiast analizy wykonalności — kroki, kolejność prac, podział na repozytoria i szacowanie czasu nie należą do tego raportu.
- Dodanie do raportu sekcji spoza trzech wymienionych w szablonie, na przykład „Podsumowanie", „Rekomendacje" albo „Kolejne kroki". Raport ma dokładnie trzy sekcje.
- Proszenie o repozytorium, mimo że dokument opisuje model bazy danych — kod sprawdza się tylko wtedy, gdy opisu modelu w dokumencie nie ma.
- Zaglądanie do kodu przy sprawdzaniu kontraktu między backendem a frontendem — ta sekcja opiera się wyłącznie na dokumencie.
- Zgadywanie struktury bazy danych, gdy nie ma ani opisu w dokumencie, ani wskazanego repozytorium, zamiast napisania wprost, że tego obszaru nie dało się zweryfikować.
- Pominięcie komentarzy pod stroną Confluence, przez co raport zgłasza jako problem coś, co komentarz już dawno wyjaśnił.
- Pisanie skrótowcami („BE", „FE", „np.", „itd.") mimo wymogu zwykłego języka.
- Zgłaszanie ustalenia bez wskazania miejsca w dokumencie, przez co czytelnik musi sam szukać, o który fragment chodzi.
- Zrównanie wagi wszystkich ustaleń — drobny brak opisany jako blokada sprawia, że raport przestaje być użyteczny przy podejmowaniu decyzji.
- Doszukiwanie się problemów na siłę, żeby każda sekcja miała jakieś ustalenia. Sekcja bez zastrzeżeń jest prawidłowym wynikiem, pod warunkiem wypisania, co zostało sprawdzone.
- Uznanie, że nie ma dostępu do Confluence, tylko dlatego, że brakuje jednego konkretnego serwera MCP — sprawdź wszystkie opcje z sekcji „Dostęp do Confluence".
