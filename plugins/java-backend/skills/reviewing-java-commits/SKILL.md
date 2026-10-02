---
name: reviewing-java-commits
description: Use when asked to review a Java pull request from Bitbucket against the system-analysis document in Confluence — a full code review of the pull request covering correctness, security, performance, maintainability, compliance with this project's own coding standards (package-by-feature, jOOQ for reads, JPA/Hibernate for writes, MapStruct mapping, no needless interfaces, Liquibase changeset conventions) and compliance with the linked analysis. Takes two links (Bitbucket pull request, Confluence analysis). Static analysis only; produces a Polish-language Markdown report with class and line references, not inline pull-request comments.
disable-model-invocation: false
---

# Reviewing Java Pull Requests

## Overview

Full static code review of ONE pull request from Bitbucket, against three things at once:

1. this project's documented standards (Java 25, jOOQ, Hibernate/JPA, package-by-feature, Liquibase) — checklist A,
2. general code quality — correctness, security, performance, resource and thread safety, error handling, readability — checklist B,
3. the system-analysis document in Confluence, treated as the source of truth about what the change was supposed to do — checklist C.

This is not a compliance checklist alone; treat it like a real senior-engineer review of the pull request. Output is a single human-readable Markdown file, written in Polish, listing findings with the exact class and line number. No dynamic analysis — do not run the build, tests, or the application.

## When to Use

- User gives a Bitbucket pull request link (or a pull request number together with the repository) and asks for a code review, "review", "przegląd kodu", "sprawdź PR".
- Scope is always the whole pull request: every change the pull request introduces relative to its target branch. Not a single commit, not the whole branch history, not the working tree.
- If the user names a single commit instead of a pull request, ask for the pull request link — this skill reviews pull requests. Only if the user explicitly insists on one commit, review that commit and write in the report that the scope was one commit, not a pull request.
- If the target directory is not a git repository, or the pull request cannot be resolved, tell the user and stop — do not guess.

## Wejście: dwa linki

Skill wymaga **dwóch linków**:

| Link | Czemu służy |
|---|---|
| **Bitbucket — pull request** | Źródło zmian do przeglądu: lista zmienionych plików, gałąź źródłowa, gałąź docelowa, tytuł i opis pull requesta. |
| **Confluence — analiza systemowa** | Źródło prawdy o tym, co ta zmiana miała realizować. Podstawa checklisty C (zgodność z analizą). |

Zasady przyjmowania wejścia:

1. Jeśli użytkownik podał **oba linki** — przejdź do sekcji Process.
2. Jeśli użytkownik podał **tylko jeden link albo żadnego** — zapytaj o **oba** linki jednym pytaniem (nawet jeśli jeden już masz, potwierdź go w tym samym pytaniu, żeby nie pracować na linku wklejonym wcześniej w innym kontekście). Nie zgaduj numeru pull requesta na podstawie bieżącej gałęzi i nie szukaj analizy samodzielnie w Confluence, dopóki użytkownik nie odpowie.
3. Brak linku do analizy **nie blokuje** przeglądu. Jeśli użytkownik odpowie, że analizy nie ma, nie zna jej adresu albo prosi o przegląd bez niej — wykonaj przegląd na podstawie checklisty A i checklisty B, pomiń checklistę C i **jawnie to zaznacz w raporcie**: w nagłówku źródeł (`Analiza systemowa: brak — przegląd wykonany bez weryfikacji zgodności z analizą`), w sekcji "Zgodność z analizą" oraz w podsumowaniu. Nie pisz raportu tak, żeby czytelnik mógł uznać, że zgodność z analizą została sprawdzona.
4. Brak linku do pull requesta **blokuje** przegląd — nie ma czego przeglądać. Zapytaj i zatrzymaj się.
5. Jeśli link do analizy prowadzi donikąd (strona przeniesiona albo usunięta), spróbuj odnaleźć ją przez wyszukiwanie w Confluence (po tytule pull requesta albo po kluczu zadania z nazwy gałęzi), zanim zapytasz użytkownika o nowy link.

## Dostęp do Bitbucketa i Confluence

Skill nie zależy od konkretnego serwera MCP ani narzędzia. Przed krokiem 1 sprawdź, czym dysponujesz w bieżącej sesji, i użyj pierwszej dostępnej opcji.

Do Bitbucketa:

1. **Narzędzia MCP** do Bitbucketa lub Atlassiana (rozpoznaj po nazwach zawierających `bitbucket` albo `atlassian`). Jeśli narzędzia są dostępne tylko jako odroczone, najpierw załaduj ich schematy przez wyszukiwarkę narzędzi.
2. **Lokalny git**, jeśli repozytorium z pull requesta jest sklonowane w katalogu, w którym pracujesz. To preferowane źródło samej treści kodu, ponieważ pozwala przeczytać pełne pliki i policzyć prawdziwe numery linii. Pobierz aktualne gałęzie przez `git -C <repo> fetch`, a punkt rozejścia wyznacz przez `git -C <repo> merge-base <gałąź-docelowa> <gałąź-źródłowa>`.
3. **REST API Bitbucketa** przez `curl`, jeśli w środowisku są ustawione adres instancji i token. Nie wypisuj tokenu w odpowiedziach ani w pliku raportu.
4. **Narzędzie wiersza poleceń**, jeśli jest zainstalowane i zalogowane.

Do Confluence:

1. **Narzędzia MCP** do Confluence lub Atlassiana.
2. **REST API Confluence** przez `curl`, jeśli adres instancji i token są dostępne w środowisku.
3. Jeśli żadna opcja nie działa — poproś użytkownika o wklejenie treści analizy razem z komentarzami, a jeśli tego nie dostarczy, potraktuj sytuację jak brak analizy z punktu 3 sekcji "Wejście: dwa linki" i zaznacz to w raporcie.

Metadane pull requesta (gałąź docelowa, tytuł, opis, komentarze) weź z Bitbucketa. Treść kodu i numery linii bierz z lokalnego repozytorium, jeśli jest dostępne, ponieważ diff z API nie daje pełnych plików.

## Process

1. **Ustal oba linki** według sekcji "Wejście: dwa linki". Dopiero potem rób cokolwiek dalej.
2. **Rozwiąż pull request.** Pobierz z Bitbucketa: numer pull requesta, tytuł, opis, gałąź źródłową, gałąź docelową, listę zmienionych plików oraz komentarze do pull requesta. Komentarz recenzenta może już opisywać problem — jeśli problem nadal jest w kodzie, zgłoś go i zaznacz, że był już podnoszony. Potwierdź, że lokalne repozytorium odpowiada temu pull requestowi, i pobierz aktualne gałęzie przez `git -C <repo> fetch`.
3. **Wyznacz zakres zmian.** `git -C <repo> merge-base <gałąź-docelowa> <gałąź-źródłowa>`, a następnie `git -C <repo> diff --name-status <merge-base> <gałąź-źródłowa>`. To, i tylko to, jest przedmiotem przeglądu. Nie przeglądaj zmian, które weszły do gałęzi docelowej niezależnie od tego pull requesta.
4. **Pobierz analizę systemową** z Confluence: treść strony oraz komentarze do niej, zwykłe (footer) i inline. Jeśli dostępne narzędzie nie udostępnia komentarzy inline, zaznacz w raporcie, że nie zostały sprawdzone. Nowszy komentarz korygujący treść analizy ma pierwszeństwo przed nieaktualnym fragmentem głównego dokumentu — jeśli korzystasz z takiej poprawki, napisz w uwadze, że pochodzi ona z komentarza, a nie z głównej treści.
5. **Wypisz wymagania z analizy.** Zanim przejdziesz do kodu, sporządź dla siebie listę konkretnych, weryfikowalnych wymagań z analizy, których ten pull request dotyczy: nazwy pól i tabel, reguły walidacji, warunki brzegowe, kształt kontraktu (endpointy, nazwy i typy pól), zachowanie w sytuacjach błędnych, wartości domyślne. Tylko takie wymagania można potem rzetelnie skonfrontować z kodem.
6. **Przejrzyj każdy zmieniony plik**, nie tylko pliki `.java`. Pull request rutynowo zawiera także skrypty migracyjne SQL, konfigurację generowania kodu jOOQ, konfigurację mapowania i podobne pliki, które wprost dotyczą tych standardów — nie odfiltrowuj ich. Decyduj o istotności osobno dla każdego pliku:
   - `.java` — zawsze przeglądane według wszystkich trzech checklist.
   - `.sql` (migracje, skrypty schematu) — czy skrypt jest spójny ze zmianą w Javie z tego samego pull requesta (na przykład nowa kolumna, od której zależy odczyt jOOQ albo nowe pole encji JPA, albo zmiana schematu, która powinna przyjść razem z aktualizacją encji lub mapowania, a nie przyszła) i czy jest zgodny ze standardem Liquibase poniżej. Dodatkowo: czy nazwy tabel i kolumn odpowiadają modelowi danych opisanemu w analizie.
   - pliki master lub parent changeloga Liquibase (`db.changelog-master.yaml` albo analogiczne) — czy nowy plik changesetu dodany w tym pull requeście jest faktycznie podłączony (patrz standard Liquibase poniżej).
   - pozostałe zmienione pliki (pliki budowania, konfiguracja XML lub YAML, źródła generowane przez jOOQ, `MapStructConfig`) — przejrzyj pobieżnie, tylko po to, żeby potwierdzić albo wykluczyć uwagę powiązaną ze standardami lub checklistami. Nie pisz osobnej uwagi dla pliku, który jedynie towarzyszy zmianie, a sam nie narusza żadnego standardu i nie zawiera prawdziwego defektu.
7. **Czytaj pełną treść plików** z gałęzi źródłowej, nie tylko fragment diffa — kontrole package-by-feature i enkapsulacji, większość kontroli poprawności oraz cała checklista C wymagają zobaczenia całej klasy i jej sąsiadów w pakiecie. Użyj `git -C <repo> show <gałąź-źródłowa>:<ścieżka>` dla zmienionego pliku oraz `git -C <repo> show <gałąź-źródłowa>:<katalog>` (albo listingu drzewa), żeby zobaczyć, jakie inne klasy już istnieją w tym samym pakiecie.
8. **Policz prawdziwe numery linii** z treści pliku z kroku 7. Numery linii w nagłówkach hunków diffa są względne i łatwo je podać błędnie — numeruj zawsze od początku pełnego pliku, nie od łatki.
9. **Zastosuj trzy checklisty** — standardy projektu (A), ogólna jakość kodu (B) i zgodność z analizą (C) — do każdej zmienionej lub dodanej klasy Java w pull requeście oraz do każdego innego pliku uznanego za istotny w kroku 6. Czytaj zmiany jak recenzent, nie jak linter: pytaj "czy to zaakceptuję?", "co może pójść nie tak na produkcji?" oraz "czy to realizuje to, co opisuje analiza?", a nie tylko "czy zgadza się z sześcioma nazwanymi regułami?".
10. **Napisz raport** według szablonu poniżej, po polsku, do pliku Markdown (patrz Output).
11. **Zgłoś się do użytkownika** w czacie: ścieżka pliku, liczba uwag, jednozdaniowe streszczenie najpoważniejszego problemu (jeśli jest) oraz informacja, czy zgodność z analizą została sprawdzona.

### Speeding up cross-file checks with graphify

Dwie kontrole z checklisty A potrzebują wiedzy, której sam diff nie pokaże: czy klasa jest faktycznie używana spoza swojego pakietu (standard 1) i czy interfejs ma więcej niż jedną implementację w całym repozytorium (standard 5). Przydaje się to także w checkliście C, gdy trzeba sprawdzić, czy wymaganie z analizy nie jest już zrealizowane w innym miejscu kodu. Jeśli repozytorium ma już graf wiedzy zbudowany przez skill `graphify` (katalog `graphify-out/` w katalogu głównym repozytorium), zapytaj graf o te pytania obejmujące wiele plików, zamiast przeszukiwać całe repozytorium ręcznie — graf indeksuje relacje wywołań i użyć, więc odpowiada na pytanie "kto odwołuje się do tej klasy" albo "ile implementacji ma ten interfejs" szybciej niż ręczne wyszukiwanie. Jeśli katalog `graphify-out/` nie istnieje, nie buduj go tylko po to, żeby zrobić jeden przegląd — wróć do `git grep` albo `rg` w repozytorium.

## Checklist A — this project's documented standards

For each changed Java class, and for each other changed file flagged as relevant (SQL migrations, Liquibase changelogs, jOOQ/MapStruct configuration), check:

| # | Standard | Co sprawdzić |
|---|----------|---------------|
| 1 | Package by feature | Czy pakiet jest zorganizowany wokół funkcjonalności (feature), a nie warstwy technicznej (na przykład globalny `controller`, `service`, `repository`)? Czy nowa lub zmieniona klasa jest `public` tylko wtedy, gdy faktycznie stanowi jawne API pakietu na zewnątrz? Czy w tym samym pakiecie istnieje już inna klasa `public` — jeśli tak, to sygnał, że pakiet urósł i trzeba wydzielić podpakiet. |
| 2 | jOOQ dla odczytów | Czy zapytania SELECT, raporty, projekcje, złożone złączenia i paginacja są realizowane przez jOOQ? Czy metoda odczytowa nie zwraca encji zarządzanej przez JPA (na przykład wynik `JpaRepository.findAll()` albo `findBy...()` użyty jako raport lub projekcja) zamiast dedykowanego obiektu transferowego albo rekordu z jOOQ? |
| 3 | JPA/Hibernate dla zapisów | Czy operacje INSERT, UPDATE i DELETE idą przez encje JPA (zarządzany cykl życia, dirty checking, kaskady, blokowanie optymistyczne), a nie przez ręcznie napisany SQL albo jOOQ `insertInto`, `update`, `deleteFrom`? |
| 4 | Mapowanie przez MapStruct | Czy mapowanie obiektów korzysta z interfejsu oznaczonego `@Mapper(config = MapStructConfig.class)`, a nie z ręcznie napisanej klasy albo metody przepisującej pola jedno po drugim? |
| 5 | Brak zbędnych interfejsów | Czy dla klasy z jedną implementacją sztucznie utworzono interfejs bez uzasadnienia (na przykład `XxxService` oraz `XxxServiceImpl`, gdzie nic poza tą jedną implementacją tego interfejsu nie używa)? Wyjątek: interfejsy wymagane przez framework (na przykład `JpaRepository<T, ID>` w Spring Data) nie są naruszeniem tej zasady. |
| 6 | Konwencje changesetów Liquibase | Czy nowy plik changesetu trzyma numerację katalogu (kolejny numer `NNN-opis.sql`, bez luk i bez duplikatu numeru już istniejącego w katalogu)? Czy nagłówek ma poprawny format (`-- liquibase formatted sql`, `-- changeset autor:identyfikator` z unikalnym identyfikatorem, nieskopiowanym z innego changesetu, oraz `-- comment:` opisujący zmianę)? Czy wstawienie albo aktualizacja danych jest idempotentna (`ON CONFLICT DO NOTHING` albo analogiczne zabezpieczenie), skoro `runOnChange:true` pozwala na wielokrotne uruchomienie? Czy nowy plik albo katalog jest faktycznie dołączony do master changeloga — sprawdź, czy katalog nadrzędny jest objęty `includeAll`, czy wymaga jawnego wpisu `include: file:` w changelogu nadrzędnym (część katalogów w repozytorium może mieć własny changelog, na przykład `<moduł>/<moduł>-changelog.yaml`, zamiast `includeAll`). Jeśli wymaga jawnego wpisu, a pull request go nie dodał, changeset nigdy się nie wykona. |

## Checklist B — ogólna jakość kodu (jak w każdym prawdziwym code review)

Zastosuj to niezależnie od standardów A — nawet pull request w pełni zgodny z zasadami package-by-feature, jOOQ, JPA i MapStruct może zawierać błąd logiczny, lukę bezpieczeństwa albo problem wydajnościowy. Oceniaj to, co pull request faktycznie wprowadza lub zmienia (włącznie z całą zmienioną metodą, nie tylko dosłownie zmienioną linią), nie plik jako całość, jeśli reszta pliku nie została dotknięta.

| # | Kategoria | Co sprawdzić |
|---|-----------|---------------|
| 7 | Poprawność logiki | Czy zmieniona logika obsługuje przypadki brzegowe (`null`, pusta kolekcja albo puste `Optional`, wartości graniczne, pusty tekst)? Czy nie ma oczywistych błędów: złego warunku, odwróconej logiki, pomyłki o jeden, nieobsłużonej gałęzi `switch` albo `if`, założenia o kolejności wykonania, które nie jest gwarantowane? Czy nowy kod robi to, co według nazwy metody i tytułu pull requesta miał robić? |
| 8 | Bezpieczeństwo | Czy dane wejściowe od użytkownika są walidowane przed użyciem (długość, format, zakres)? Czy nie ma możliwości wstrzyknięcia (konkatenacja SQL zamiast parametrów, budowanie filtra LDAP przez konkatenację zamiast `LdapEncoder` albo parametryzacji, przejście po katalogach przy operacjach na plikach)? Czy dane wrażliwe (hasła, tokeny, dane osobowe) nie trafiają do logów ani komunikatów wyjątków? Czy nie ma zahardkodowanych sekretów albo haseł w kodzie produkcyjnym (w jawnych danych testowych, na przykład w plikach `test-data`, to nie jest naruszenie). |
| 9 | Wydajność | Czy nie ma zapytania N+1 (pętla wykonująca zapytanie do bazy albo wywołanie LDAP lub HTTP dla każdego elementu kolekcji)? Czy kolekcja albo strumień nie jest przetwarzany bez potrzeby wielokrotnie (to samo obliczenie lub zapytanie powtórzone w pętli zamiast policzone raz)? Czy nowy kod nie ładuje do pamięci całego, potencjalnie dużego zbioru danych tam, gdzie wystarczyłaby paginacja albo strumieniowanie? |
| 10 | Zarządzanie zasobami i wątki | Czy zasoby (strumienie, połączenia, kontekst LDAP, transakcje) są zamykane przez try-with-resources albo przez kontener, a nie ręcznie i warunkowo? Czy pole instancyjne komponentu singletonowego (bean Springa) nie przechowuje mutowalnego stanu współdzielonego między żądaniami albo wątkami bez synchronizacji? |
| 11 | Obsługa błędów | Czy wyjątki nie są połykane w pustym bloku `catch` ani logowane bez kontekstu pozwalającego zdiagnozować przyczynę? Czy nie łapie się nadmiernie ogólnego `Exception` albo `RuntimeException` tam, gdzie da się złapać konkretny typ? Czy komunikat nowego wyjątku (na przykład własnej klasy `XxxException`) niesie wystarczający kontekst (jaka wartość, jaki identyfikator), a nie tylko ogólnikowy tekst? |
| 12 | Czytelność i utrzymywalność | Czy nazwy klas, metod i zmiennych jasno opisują ich rolę, bez skrótów niejasnych poza zespołem? Czy nowa metoda nie robi zbyt wielu rzeczy naraz (wysoka złożoność cyklomatyczna, długość utrudniająca zrozumienie za jednym czytaniem)? Czy pull request nie wprowadza kodu niemal identycznego do istniejącego gdzie indziej, który powinien być wspólną metodą zamiast kopii? |

## Checklist C — zgodność z analizą systemową

Pomiń tę checklistę tylko wtedy, gdy nie ma linku do analizy (patrz punkt 3 sekcji "Wejście: dwa linki"), i wtedy jawnie napisz w raporcie, że nie została zastosowana.

Analiza systemowa jest źródłem prawdy o tym, co ta zmiana miała realizować. Każdą niezgodność raportuj dokładnie tak samo jak uwagę z analizy statycznej: **plik (klasa), numer linii, na czym polega niezgodność**, oraz czego analiza wymaga. Jeśli niezgodność polega na tym, że czegoś **brakuje**, podaj plik i linię miejsca, w którym tego brakuje — na przykład metodę, w której powinna znaleźć się walidacja, albo klasę kontraktu, w której powinno znaleźć się pole. Nie zostawiaj uwagi bez lokalizacji w kodzie.

| # | Kategoria | Co sprawdzić |
|---|-----------|---------------|
| 13 | Kompletność zakresu | Czy każde wymaganie z analizy dotyczące tej zmiany jest zaimplementowane? Czy jakaś opisana ścieżka, warunek albo przypadek brzegowy został pominięty w kodzie? |
| 14 | Model danych i nazewnictwo | Czy nazwy tabel, kolumn, encji, pól i typów odpowiadają temu, co opisuje analiza? Czy typ i obowiązkowość pola (dopuszczalność wartości `null`, długość, precyzja) są zgodne z analizą, a nie dobrane samodzielnie? |
| 15 | Kontrakt | Czy endpointy, metody, nazwy i typy pól żądania oraz odpowiedzi, kody statusu i format błędu odpowiadają kontraktowi z analizy? Czy kod nie dodaje pola albo endpointu, którego analiza nie przewiduje, i nie zmienia istniejącego kontraktu w sposób niezgodny z analizą? |
| 16 | Reguły biznesowe | Czy warunki, progi, wartości domyślne, kolejność kroków i zachowanie w sytuacjach błędnych są dokładnie takie, jak opisuje analiza? Czy kod nie realizuje reguły prawie poprawnie — na przykład porównanie ostre zamiast nieostrego, inna wartość domyślna, inna reakcja na brak danych? |
| 17 | Nadmiarowy zakres | Czy pull request nie wprowadza funkcjonalności, której analiza w ogóle nie opisuje? Taki nadmiar nie jest automatycznie błędem, ale wymaga zgłoszenia jako rozbieżność ze źródłem prawdy. |

Rozstrzyganie wątpliwości w checkliście C:

- Jeśli analiza **nie wypowiada się** na dany temat, nie wymyślaj wymagania — nie zgłaszaj niezgodności tam, gdzie analiza po prostu milczy. Jeśli to milczenie dotyczy czegoś istotnego, na przykład zachowania przy braku danych, napisz o tym w sekcji "Pytania i luki w analizie", a nie jako naruszenie.
- Jeśli analiza jest **sprzeczna z opisem pull requesta albo z komentarzem recenzenta**, zgłoś to jako rozbieżność i napisz, które źródło mówi co. Nie wybieraj samodzielnie, która wersja obowiązuje.
- Jeśli komentarz pod analizą koryguje jej treść, zastosuj poprawkę z komentarza, ale zaznacz w uwadze, że pochodzi ona z komentarza, a nie z głównej treści dokumentu.
- Analiza może opisywać także część frontendową albo zmiany w innym repozytorium. Nie zgłaszaj ich jako braków w tym pull requeście — wypisz je w sekcji "Poza zakresem tego pull requesta".

Report only what the pull request actually introduces or changes — do not flag pre-existing code in unrelated classes the pull request did not touch, unless a change in this pull request makes an existing violation worse or directly relevant.

## Output

**Language:** Polish.

**File location:** `<repo-root>/CODE_REVIEW/<nazwa-gałęzi-źródłowej>.md` (create the `CODE_REVIEW/` directory if missing). `<nazwa-gałęzi-źródłowej>` is the pull request's source branch, with any `/` replaced by `-` so it is a valid single filename (for example branch `feature/PROJ-123` writes to `CODE_REVIEW/feature-PROJ-123.md`). If the source branch name cannot be determined, use the pull request number instead: `CODE_REVIEW/PR-<numer>.md`. If the user specifies a different path, use that instead. Reviewing the same branch again overwrites the previous report at this path by design — the file tracks the latest review for that branch, not a running history of every past review; keep the pull request number and the reviewed head commit inside the report body (see template) so the reader can tell which state the current report covers.

**Template:**

```markdown
# Code review – pull request #<numer> ("<tytuł pull requesta>")

Data przeglądu: <YYYY-MM-DD>
Pull request: <link do Bitbucketa>
Analiza systemowa: <link do Confluence albo "brak — przegląd wykonany bez weryfikacji zgodności z analizą">
Gałąź źródłowa: <nazwa> (ostatni przeglądany commit: <skrócony hash>)
Gałąź docelowa: <nazwa>
Zakres: <lista zmienionych plików istotnych dla przeglądu, na przykład klasy .java oraz skrypty .sql>

## Uwagi

### 1. <krótki, konkretny tytuł uwagi>

- **Klasa:** `pełna.ścieżka.pakietu.NazwaKlasy`
- **Linia:** <numer linii w pliku>
- **Standard/Kategoria:** <jedna z pozycji checklisty A (1–6) albo checklisty B (7–12), na przykład "jOOQ dla odczytów" albo "Bezpieczeństwo">
- **Co jest nie tak:** <precyzyjny, prosty opis problemu, bez skrótów>
- **Dlaczego to problem:** <konkretna konsekwencja — jaką kontrolę tracimy, jaki błąd może powstać w produkcji, jaki jest scenariusz jego wystąpienia>
- **Rekomendacja:** <konkretna zmiana do wprowadzenia>

(kolejne uwagi w tym samym formacie, ponumerowane; uporządkuj od najpoważniejszej do najmniej istotnej)

## Zgodność z analizą

<jeśli nie było linku do analizy, napisz tutaj jedno zdanie: "Nie sprawdzono — do przeglądu nie podano linku do analizy systemowej, więc zgodność implementacji z wymaganiami nie została zweryfikowana." i pomiń resztę tej sekcji>

### C1. <krótki, konkretny tytuł niezgodności>

- **Plik:** `<ścieżka/do/pliku>` (dla pliku Java podaj też klasę `pełna.ścieżka.pakietu.NazwaKlasy`)
- **Linia:** <numer linii w pliku; przy braku implementacji podaj linię miejsca, w którym brakująca logika powinna się znaleźć>
- **Kategoria:** <jedna z pozycji checklisty C (13–17), na przykład "Model danych i nazewnictwo">
- **Czego wymaga analiza:** <dokładne wymaganie, ze wskazaniem fragmentu albo sekcji analizy; jeśli pochodzi z komentarza pod analizą, napisz to>
- **Co robi kod:** <co faktycznie jest zaimplementowane>
- **Na czym polega niezgodność:** <różnica opisana wprost, bez skrótów>
- **Rekomendacja:** <konkretna zmiana, która doprowadzi kod do zgodności z analizą>

(kolejne niezgodności w tym samym formacie, numerowane C2, C3 i dalej; uporządkuj od najpoważniejszej do najmniej istotnej)

### Poza zakresem tego pull requesta

<wymagania z analizy, które dotyczą frontendu albo innego repozytorium i dlatego nie są brakiem w tym pull requeście — albo "brak">

### Pytania i luki w analizie

<miejsca, w których analiza milczy albo jest sprzeczna z opisem pull requesta, i trzeba to rozstrzygnąć z autorem analizy — albo "brak">

## Inne istotne obserwacje

<tylko jeśli w przeglądanym kodzie widać coś wyraźnie błędnego spoza siedemnastu pozycji powyżej — na przykład kod, który się nie skompiluje, brakującą adnotację wymaganą przez JPA, albo oczywisty błąd logiczny nieujęty gdzie indziej. Opisz to tym samym sposobem: plik, klasa, linia, co jest nie tak, dlaczego to problem. Pomiń tę sekcję całkowicie, jeśli nic takiego nie zauważono — nie szukaj na siłę dodatkowych uwag.>

## Podsumowanie

- Liczba uwag (checklisty A i B): <N>
- Liczba niezgodności z analizą (checklista C): <N albo "nie sprawdzono — brak linku do analizy">
- Standardy i kategorie naruszone w tym pull requeście: <lista>
- Zgodność z analizą: <jedno z: "zgodny — nie znaleziono niezgodności"; "niezgodny — <N> niezgodności, najpoważniejsza: <jedno zdanie>"; "nie sprawdzono — do przeglądu nie podano linku do analizy systemowej">
```

If no violations are found, still write the file, stating explicitly that the reviewed pull request complies with all standards from checklist A, raises no concerns under checklist B, and matches the system analysis under checklist C (or that checklist C was not applied, because there was no analysis link), and list which classes were checked.

## Common Mistakes

- Starting the review with only one of the two links, instead of asking for both the Bitbucket pull request link and the Confluence analysis link.
- Silently reviewing without the analysis and leaving the report looking like compliance with the analysis was verified — a missing analysis must be stated in the sources header, in the "Zgodność z analizą" section, and in the summary.
- Refusing to review at all because the analysis link is missing — the review still runs on checklists A and B.
- Writing a checklist C finding without a file and line number (a bare "niezgodne z analizą") — every mismatch is located in the code exactly like a static-analysis finding, including a missing implementation, which is located where it should have been.
- Inventing a requirement the analysis does not state, and reporting it as a mismatch — analysis silence belongs in "Pytania i luki w analizie".
- Reviewing the whole source branch history, or the working tree, instead of the pull request's change set relative to the merge-base with the target branch.
- Reporting line numbers from the diff patch instead of the actual file — always re-derive from `git show <gałąź-źródłowa>:<ścieżka>`.
- Using abbreviations in the Polish text ("np.", "itd." used as a substitute for spelling things out) — write full sentences instead.
- Flagging a Spring Data or other framework-required interface as an unnecessary interface (standard 5's exception).
- Skipping the "read full file" step and missing a package-by-feature violation because a sibling class outside the diff wasn't checked.
- Filtering the pull request down to only `.java` files and silently skipping SQL migrations, Liquibase changelogs, or config files that are relevant to a finding.
- Adding a new Liquibase changeset file and not checking whether its parent directory needs an explicit `include:` entry (some directories in a given repo use `includeAll`, others don't) — a changeset that is never included never runs, silently.
- Being purely mechanical about checklist A while missing an obvious bug, security hole, or performance problem that checklist B would have caught, or a requirement from the analysis that checklist C would have caught — this skill is a real code review, not only a standards linter.
- Flagging a checklist B issue (performance, style, error handling) in code the pull request did not touch, just because it was visible while reading the surrounding file for context.
- Skipping the comments under the Confluence page, even though a comment can change what the analysis requires.
- Spending time building a graphify knowledge graph for a repository that doesn't already have one, just to review one pull request — only use graphify when `graphify-out/` already exists.
- Naming the output file after the pull request number when the source branch name is known, or writing it outside `CODE_REVIEW/` — the location is `CODE_REVIEW/<nazwa-gałęzi-źródłowej>.md`, created if missing.
- Using a branch name containing `/` as-is in the file path (it would create an unwanted subdirectory) instead of replacing `/` with `-` first.

## Styl dokumentu

Cały raport — każda sekcja, każda uwaga, każde zdanie — musi być napisany w sposób neutralny i naturalny, pełnymi słowami:

- **Bez skrótów.** Nie używaj form "np.", "itd.", "itp.", "tzn.", "m.in.", "ew.", "tj.", "ok.". Pisz "na przykład", "i tak dalej", "i tym podobne", "to znaczy", "między innymi", "ewentualnie", "to jest", "około".
- **Neutralny ton.** Opisuj kod i jego konsekwencje, nie autora. Żadnej oceny osoby, żadnej ironii, żadnych wykrzykników, żadnych pochwał ani nagan ("świetnie", "niestety", "okropny kod"). Zamiast "to zły pomysł" napisz, co konkretnie się stanie i dlaczego.
- **Rzeczowo i bez emfazy.** Bez wielkich liter dla podkreślenia, bez wielokrotnych znaków interpunkcyjnych, bez emoji.
- **Pełne, samodzielne zdania.** Wyjaśniaj tak, jakby czytał to ktoś, kto nigdy nie widział tej klasy: jaka jest reguła albo jakie jest wymaganie z analizy, co kod robi zamiast tego, i dlaczego jest to problem w konkretnych kategoriach — nie samo "narusza zasadę numer X" albo "niezgodne z analizą".
- **Bez żargonu bez wyjaśnienia.** Jeśli używasz terminu technicznego, który nie jest nazwą z kodu ani nazwą standardu z checklisty, wyjaśnij go w tym samym zdaniu.
