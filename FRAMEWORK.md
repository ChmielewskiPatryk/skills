# Framework „Ledger zadania” — jak używać skilli w procesie developmentu

Dokument projektowy. Opisuje docelową architekturę użycia skilli z pluginu `java-backend` w cyklu życia jednego zadania Jira, wynik analizy obecnego stanu oraz kolejność wdrożenia. Nie jest instrukcją dla modelu — instrukcje trafią do skilli w `plugins/java-backend/`.

Decyzje podjęte 2026-10-21:

| Decyzja | Wybór |
|---|---|
| Gdzie żyją artefakty zadania | w repozytorium produktowym, katalog `.task/<KLUCZ>/`, w `.gitignore` |
| Dwa skille review | zostają oba; naprawa ścieżek, żeby retro i tryb przyrostowy czytały oba raporty |
| Nić identyfikatorów REG/AC | w nazwie metody testu i w treści commita, bez adnotacji |
| Automatyzacja | router `/task`, review w osobnym kontekście (fork), subagenci dla grup równoległych, hooki wymuszające bramki |

---

## 1. Analiza stanu

### Co działa

- Pełny cykl zadania w siedmiu skillach: wyjaśnienie analizy → wykonalność → plan → implementacja → review → smoke test → retro.
- Nić identyfikatorów REG/AC: analiza → macierz wymagań i testów w planie → testy pisane przed kodem → pokrycie macierzy w review → przypadki negatywne w smoke teście → retro. To jest rdzeń wartości całego pluginu.
- Pytania jako artefakt o stałym formacie (cytat, skąd, co niejasne, hipoteza) w czterech skillach.
- Retro produkuje łatkę na skille: pętla samodoskonalenia istnieje, choć zamykana ręcznie.

### Co nie działa

| # | Problem | Skutek |
|---|---|---|
| 1 | Kontrakt między skillami jest niejawny: ścieżki plików i nazwy sekcji Markdown (`## Macierz wymagań i testów`, `## Odstępstwa od planu`) są jedynym interfejsem, każdy skill opisuje je od nowa | zmiana nagłówka w jednym skillu to cicha awaria w trzech innych |
| 2 | `implementing-jira-task` kieruje na `java-code-review` (pisze `CODE_REVIEW/<gałąź>-java-code-review.html`), a `running-task-retro` i tryb przyrostowy `reviewing-java-commits` czytają tylko `CODE_REVIEW/<gałąź>.md` | wynik review przed pull requestem nie trafia do retro ani do weryfikacji poprzednich uwag |
| 3 | Dwa skille review mają około 70% wspólnej treści (weryfikacja biznesowa, sześć standardów, autoryzacja), różne formaty raportu i różne skale wag | routing dla modelu niejasny, dwa raporty o tej samej zmianie nieporównywalne |
| 4 | Duplikacja: sekcja „Dostęp do Jiry i Confluence” w pięciu skillach, „Format pytań” w trzech, tabela sześciu standardów w trzech, zasady stylu w sześciu | z 2041 linii około 600 to kopie; każda poprawka w sześciu miejscach; każde wywołanie ładuje powtórzony tekst do kontekstu |
| 5 | Artefakty w siedmiu katalogach repozytorium produktowego z niespójnym `.gitignore` (`.analiza/`, `RETRO/`, `SMOKE_TEST/` ignorowane; `IMPLEMENTATION_LOG/` commitowany; `IMPLEMENTATION_PLAN/`, `CODE_REVIEW/` nieokreślone) | bałagan w repozytorium i w pull requestach |
| 6 | „Grupy równoległe” z planu nikt nie konsumuje: implementacja wykonuje je sekwencyjnie | plan niesie informację, z której nic nie wynika |
| 7 | Dashboard sesji rozpoznaje tylko etapy wykonalność, plan i implementacja (regex na `ANALIZA_WYKONALNOSCI` i `IMPLEMENTATION_PLAN`, mapa nazw skilli); review, smoke i retro są niewidoczne mimo opisu w README | dashboard nie pokazuje, gdzie zadanie jest naprawdę |
| 8 | Pokrycie macierzy ocenia wyłącznie model: identyfikator reguły nie występuje w teście ani w commicie w sposób sprawdzalny | ocena nieodtwarzalna, kosztowna, podatna na „test o pasującej nazwie” |
| 9 | Bramki procesu („bez planu nie implementuj”, „nie pushuj”) istnieją tylko w tekście skilla | nic ich nie wymusza; użytkownik musi pamiętać kolejność siedmiu komend |

---

## 2. Architektura docelowa

Idea w jednym zdaniu: **zadanie Jira jest obiektem pierwszej klasy z manifestem; skille to operacje na tym obiekcie; nić REG/AC jest sprawdzalna skryptem; pętla retro jest mierzona.**

```
                ┌──────────────── /java-backend:task PROJ-123 (router, bramki) ────────────────┐
                │                                                                              │
 Confluence ──► explaining ──► analyzing-feasibility ──► planning ──► implementing ──► review ──► smoke ──► retro
 Jira                 │                 │                   │             │  (fork)    │   (fork)    │        │
                      ▼                 ▼                   ▼             ▼            ▼            ▼        ▼
                .task/PROJ-123/ : task.yaml · analiza.md · wykonalnosc.md · plan.md · matrix.yaml · log.md · review/ · smoke.md · retro.md · questions.yaml
                                                                                                              │
                                                              trace.py (nić REG) ◄────────────────────────────┘
                                                              hooks (git commit / push) ◄── task.yaml
                                                              dashboard ◄── task.yaml ze wszystkich repozytoriów
                                                              repo skilli ◄── retro: łatka + metrics.jsonl
```

### 2.1 Ledger zadania: `.task/<KLUCZ>/`

Jeden katalog na zadanie w repozytorium wiodącym (tym, w którym leży plan). Katalog `.task/` jest w `.gitignore` repozytorium produktowego — pierwszy skill, który go tworzy, dopisuje wpis.

| Plik | Pisze | Czyta | Zastępuje dzisiejsze |
|---|---|---|---|
| `task.yaml` | każdy skill (swoją sekcję) | router, hooki, dashboard, retro | rozpoznawanie etapu po istnieniu plików |
| `analiza.md` | planning (cache strony Confluence z komentarzami) | planning, implementing, review, smoke, retro | `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md` |
| `wyjasnienie.html` | explaining | człowiek | `<OPERACJA>_<wersja>_wyjasnienie.html` w katalogu workspace (opcjonalnie nadal tam, z kopią tutaj) |
| `wykonalnosc.md` | analyzing-feasibility | planning, retro | `ANALIZA_WYKONALNOSCI/<KLUCZ>.md` |
| `plan.md` | planning | implementing, review, smoke, retro | `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` |
| `matrix.yaml` | planning; stan aktualizuje implementing i review | implementing, review, smoke, retro, `trace.py` | tabela „Macierz wymagań i testów” w planie (plan nadal ją renderuje jako tabelę, ale źródłem prawdy jest YAML) |
| `log.md` | implementing | review, smoke, retro, hooki | `IMPLEMENTATION_LOG/<KLUCZ>.md` |
| `review/local-<N>.html` | java-code-review | retro, reviewing-java-commits (weryfikacja poprzednich uwag) | `CODE_REVIEW/<gałąź>-java-code-review.html` |
| `review/pr-<N>.md` | reviewing-java-commits | retro, reviewing-java-commits (tryb przyrostowy) | `CODE_REVIEW/<gałąź>.md` |
| `smoke.md`, `smoke-zadania.sh`, `smoke-logi/` | smoke-testing-locally | retro | `SMOKE_TEST/<KLUCZ>.md`, `SMOKE_TEST/<KLUCZ>-zadania.sh`, `SMOKE_TEST/logi/` |
| `retro.md`, `retro-skille.patch`, `metrics.json` | running-task-retro | człowiek, repo skilli, dashboard | `RETRO/<KLUCZ>.md`, `RETRO/<KLUCZ>-skille.patch` |
| `questions.yaml` | każdy skill, który zadaje pytania | planning (nie pyta ponownie), implementing, retro | pytania rozsiane po czterech raportach |

Konfiguracja wspólna dla wszystkich zadań (dziś `SMOKE_TEST/srodowisko.md`) przechodzi do `.task/_srodowisko.md` w katalogu workspace albo repozytorium wiodącym. Numer `<N>` w raportach review rośnie z każdą rundą; „ostatni raport” to najwyższy numer w danym trybie.

Konsekwencja wyboru „gitignore”: wiedza o zadaniu żyje na jednej maszynie. Dlatego retro przekazuje to, co ma przetrwać (łatka, metryki), do repozytorium skilli (sekcja 2.8). Jeżeli zespół zechce kiedyś dzielić plan i dziennik w pull requeście, wystarczy usunąć wpis z `.gitignore` — układ katalogu się nie zmienia.

### 2.2 Manifest `task.yaml`

Mały, płaski, żeby model edytował go bez błędów. Skille dopisują tylko własne klucze.

```yaml
klucz: PROJ-123
tytul: Harmonogram płatności
repozytoria:
  - nazwa: payments-service
    galaz: feature/PROJ-123-harmonogram
    bazowa: main
    rola: wiodace
  - nazwa: payments-api-contract
    galaz: feature/PROJ-123-harmonogram
    bazowa: main
    rola: biblioteka
zrodla:
  jira: https://jira.firma.pl/browse/PROJ-123
  confluence: https://confluence.firma.pl/pages/12345
  confluence_wersja: 7
  pobrano: 2026-10-21
etapy:                      # brak klucza = etap nie zaczęty
  wykonalnosc: { stan: zrobiony, data: 2026-10-20, plik: wykonalnosc.md, blokady: 1, pytania: 3 }
  plan:        { stan: zrobiony, data: 2026-10-21, plik: plan.md, kroki: 6 }
  implementacja: { stan: w_trakcie, krok_biezacy: 3, kroki_zrobione: [1, 2], kroki_zablokowane: [] }
  review:      { stan: brak }
  smoke:       { stan: brak }
  retro:       { stan: brak }
pytania_otwarte: 2          # liczba wpisów w questions.yaml bez odpowiedzi
```

Stany etapu: `brak`, `w_trakcie`, `zrobiony`, `zablokowany`. Router i hooki czytają tylko ten plik; nigdy nie parsują Markdown.

### 2.3 `matrix.yaml` i `questions.yaml`

```yaml
# matrix.yaml
- id: REG-03
  tresc: Rata nie może mieć daty wymagalności w przeszłości
  zrodlo: analiza.md:142
  typ: IT
  test: PaymentScheduleIT.shouldReject_whenDueDateInPast_REG03
  krok: 3
  stan: zielony           # planowany → czerwony → zielony → (review) pokryty | nie_weryfikuje | brak
- id: REG-04
  tresc: ...
  typ: brak_testu
  uzasadnienie: wymusza ograniczenie unikalności z kroku 2, sprawdzane testem REG-02
  krok: 2
```

```yaml
# questions.yaml
- nr: 1
  etap: wykonalnosc        # wykonalnosc | plan | implementacja | review | smoke
  temat: model danych
  cytat: "Harmonogram zapisujemy w tabeli payment_schedule z polami amount_net, amount_gross."
  skad: analiza.md:142
  niejasne: czy to nowa tabela, czy rozszerzenie istniejącej payments_schedule
  hipoteza: rozszerzamy istniejącą
  odpowiedz: rozszerzamy istniejącą
  kto: programista
  data: 2026-10-21
```

Jeden rejestr zamiast czterech sekcji w czterech raportach. Planning nie zadaje pytania, które już jest w rejestrze; retro liczy pytania na etap i ocenia, czy mogły paść wcześniej, bez zbierania ich z pięciu plików.

### 2.4 Wspólny rdzeń pluginu: `plugins/java-backend/shared/`

Wyciągnięta treść, do której skille odsyłają przez `${CLAUDE_SKILL_DIR}/../../shared/<plik>` (katalog pluginu jest kopiowany do cache w całości; `running-task-retro` już korzysta z `../<skill>/`). Do potwierdzenia przez `claude plugin validate` i jedno wywołanie z `--plugin-dir`.

| Plik | Treść | Dziś powielone w |
|---|---|---|
| `access.md` | kolejność sprawdzania dostępu: MCP → CLI → REST z tokenem; zakaz wypisywania tokenów; co zrobić bez dostępu | 5 skillach |
| `questions.md` | format pytania (cytat, skąd, niejasne, hipoteza), zasada „zbieraj i pytaj zestawem”, zapis do `questions.yaml` | 3 skillach |
| `standards.md` | sześć standardów w dwóch kolumnach: jak pisać (implementacja) i co sprawdzać (review); autoryzacja; Liquibase | 3 skillach |
| `style.md` | polski, pełne zdania, bez skrótowców, neutralny ton, bez ocen osób | 6 skillach |
| `ledger.md` | kontrakt `.task/`: nazwy plików, schemat `task.yaml`, `matrix.yaml`, `questions.yaml`, kto co pisze i czyta, reguła `.gitignore` | 7 skillach (rozproszone opisy ścieżek) |
| `scripts/task.py` | odczyt i aktualizacja `task.yaml` (`status`, `set etap=...`), żeby model nie edytował YAML ręcznie | — |
| `scripts/trace.py` | nić REG (sekcja 2.5) | — |

Każdy `SKILL.md` chudnie do: kiedy użyć, proces, checklisty własne, szablon raportu, częste błędy. Szacunek: z 2041 do około 1300 linii.

### 2.5 Nić REG sprawdzalna skryptem

Konwencja (bez adnotacji, zgodnie z decyzją):

- **nazwa metody testu** kończy się identyfikatorem bez myślnika: `shouldReject_whenDueDateInPast_REG03`, `shouldSplitAmount_AC1`, `shouldKeepOrder_W2`. Jeden test może nieść kilka identyfikatorów: `..._REG03_REG05`;
- **treść commita** zawiera numer kroku i identyfikatory: `Krok 3; REG-03, AC-1` (dziś już wymagane przez `implementing-jira-task`).

`shared/scripts/trace.py <repo> .task/<KLUCZ>/matrix.yaml`:

1. szuka w źródłach testowych metod z sufiksem identyfikatora (regex na `void\s+\w+_(REG|AC|W)\d+`),
2. szuka w `git log <bazowa>..<gałąź>` identyfikatorów w treści commitów,
3. wypisuje tabelę: wiersz macierzy → test znaleziony (plik, linia) → commit → stan: `pokryty`, `brak testu`, `test bez commita`, `commit bez testu`, `test spoza macierzy` (nowy identyfikator, którego plan nie zna → kandydat na nowy wiersz).

Podział pracy: skrypt odpowiada deterministycznie „czy istnieje i gdzie”, model odpowiada tylko „czy test naprawdę weryfikuje regułę” (pozycja 18 checklisty C). Smoke test bierze przypadki negatywne wprost z `matrix.yaml`, bez parsowania tabeli Markdown.

### 2.6 Router `/java-backend:task`

Nowy skill, jedyny punkt wejścia dla programisty. `disable-model-invocation: true`, `argument-hint: "[KLUCZ] [status|next|init|<etap>]"`.

| Wywołanie | Działanie |
|---|---|
| `/task PROJ-123` albo `/task` na gałęzi zadania | pokazuje status: tabela etapów ze stanami, otwarte pytania, wiersze macierzy bez zielonego testu, ostatni raport review; proponuje następny krok |
| `/task PROJ-123 next` | uruchamia następny skill w kolejności, po potwierdzeniu |
| `/task PROJ-123 init <link Jira>` | tworzy `.task/PROJ-123/`, manifest, wpis w `.gitignore`; pobiera z Jiry tytuł i link do analizy |
| `/task PROJ-123 review` | uruchamia wskazany etap, jeżeli bramki na to pozwalają |

Bramki (w tekście routera, egzekwowane twardo przez hooki z sekcji 2.9):

| Etap | Wymaga |
|---|---|
| plan | `wykonalnosc.md` nie jest wymagana, ale jeśli istnieje, jej pytania są w `questions.yaml` |
| implementacja | `plan.md` i `matrix.yaml`; brak pytań o stanie „blokuje krok” dla kroku bieżącego |
| review lokalny | `log.md` z co najmniej jednym krokiem zrobionym |
| push gałęzi | co najmniej jeden raport `review/local-*.html` dla bieżącego końca gałęzi |
| review pull requesta | pull request istnieje (link w manifeście) |
| smoke | co najmniej jeden krok zrobiony; usługi i biblioteki z planu mają gałąź zadania |
| retro | pull request scalony albo programista potwierdza, że zadanie zamknięte |

Router nie powiela logiki skilli — tylko czyta manifest i wywołuje właściwy skill z argumentami.

### 2.7 Review w osobnym kontekście

Oba skille review dostają `context: fork` w nagłówku. Raport wraca do sesji jako plik i krótkie podsumowanie; pełne pliki klas i 300–520 linii instrukcji nie obciążają sesji implementacyjnej.

Konsekwencja: skill w forku nie może zadać pytania użytkownikowi w trakcie. Dlatego:

- `reviewing-java-commits` przyjmuje oba linki jako argumenty (`argument-hint: "<link pull request> [<link analizy>]"`); bez linku do pull requesta kończy się od razu z prośbą o argument, bez linku do analizy działa jak dziś (checklisty A i B, adnotacja w raporcie);
- `java-code-review` bierze klucz z argumentu albo z gałęzi, resztę z manifestu;
- wszystko, co dziś jest pytaniem w trakcie review, staje się pozycją w sekcji „Pytania i luki w analizie” raportu i wpisem w `questions.yaml` z etapem `review`.

Naprawa niezgodności numer 2: oba skille piszą do `.task/<KLUCZ>/review/`, retro czyta oba tryby, a `reviewing-java-commits` w sekcji „Weryfikacja poprzednich uwag” bierze pod uwagę także ostatni raport lokalny.

### 2.8 Subagenci dla grup równoległych

Plan już oznacza grupy równoległe. `implementing-jira-task` dostaje argument `rownolegle`:

- równoległość tylko **między repozytoriami** (typowy przypadek: kontrakt API i usługa, która go konsumuje). Jedna gałąź nie może być wymeldowana w dwóch worktree naraz, więc kroki w jednym repozytorium zawsze idą sekwencyjnie;
- dla każdego repozytorium z grupy orkiestrator uruchamia agenta w `isolation: worktree` na gałęzi zadania tego repozytorium, z promptem: kroki grupy, wiersze macierzy, `standards.md`, fragment analizy, zasada „nie pytaj — zwróć listę blokad”;
- agent zwraca: commity, fragment dziennika, odstępstwa, pytania, stan wierszy macierzy;
- orkiestrator scala fragmenty do `log.md`, aktualizuje `matrix.yaml` i manifest, zbiera pytania wszystkich agentów i zadaje je zestawem, po odpowiedziach uruchamia ponownie tylko kroki zablokowane;
- jeżeli grupa zależy od biblioteki z innej grupy, orkiestrator najpierw publikuje ją do Maven Local, tak jak dziś.

Bez argumentu skill działa jak dzisiaj. Koszt: dwa do trzech razy więcej tokenów na zadanie z dwoma repozytoriami; zysk: czas ścienny i czysty kontekst na każdy krok.

### 2.9 Hooki wymuszające bramki

Plugin dostarcza `plugins/java-backend/hooks/hooks.json` z hookiem `PreToolUse` na narzędzie `Bash` i skrypt `hooks/gate.sh`. Skrypt czyta z wejścia polecenie, reaguje tylko na `git commit` i `git push` wykonywane na gałęzi z kluczem zadania (`feature/<KLUCZ>-...`):

| Polecenie | Warunek przepuszczenia | Komunikat blokady |
|---|---|---|
| `git commit` | `.task/<KLUCZ>/task.yaml` istnieje i etap `implementacja` jest `w_trakcie` albo `zrobiony` | „Brak planu lub dziennika dla PROJ-123. Uruchom `/java-backend:task PROJ-123`.” |
| `git push` | istnieje `review/local-*.html` nowszy niż ostatni commit | „Gałąź nie przeszła review lokalnego. Uruchom `/java-backend:java-code-review PROJ-123`.” |

Zasady:

- blokada to kod wyjścia 2 z komunikatem; wszystko inne przepuszcza bez słowa, żeby hook nie spowalniał pracy poza procesem;
- wyjście awaryjne: zmienna `TASK_GATE=off` albo gałąź bez klucza zadania w nazwie — hook milczy;
- hook nie czyta Markdown, tylko `task.yaml` i listę plików; cały kod to kilkadziesiąt linii bash i `python3 -I`;
- wdrożenie dopiero po ustabilizowaniu manifestu (faza 5), bo fałszywa blokada kosztuje więcej zaufania niż brak bramki.

Do zweryfikowania: czy zainstalowana wersja Claude Code ładuje hooki z pluginu (`hooks/hooks.json` w katalogu pluginu) — jeżeli nie, instrukcja w README dla `settings.json`.

### 2.10 Zamknięta, mierzona pętla retro

Retro dodatkowo:

1. zapisuje `metrics.json` do `.task/<KLUCZ>/`: pytania na etap, rundy review, uwagi na checklistę, zmiany spoza planu według klas, wiersze macierzy bez testu, kroki pominięte, dni między etapami;
2. za zgodą programisty kopiuje `metrics.json` do repozytorium skilli jako wiersz w `retro/metrics.jsonl` oraz tworzy gałąź `retro/<KLUCZ>` z nałożoną łatką i otwiera pull request (zamiast pliku `.patch` do ręcznego nałożenia). Skills repo jest jedynym miejscem, gdzie wiedza z retro przetrwa, bo `.task/` jest lokalne;
3. nie zmienia niczego w zainstalowanej kopii pluginu — jak dziś.

Dashboard (sekcja 2.11) pokazuje trend metryk po zadaniach: czy liczba pytań przesuwa się z review w stronę wykonalności, czy maleje liczba zmian spoza planu. To zamienia skille w produkt z mierzalną skutecznością.

### 2.11 Dashboard czyta manifesty

`session-dashboard/build.py` dostaje drugie źródło: dla każdego katalogu roboczego z transkryptów szuka `.task/*/task.yaml` i buduje kolumny etapów wprost z manifestu. Etapy review, smoke i retro pojawiają się bez regexów na nazwy plików. Sekcja „Skuteczność procesu” czyta `retro/metrics.jsonl` z repozytorium skilli, jeżeli jest sklonowane lokalnie.

---

## 3. Mapowanie zmian na skille

| Skill | Zmiany |
|---|---|
| wszystkie w `java-backend` | odwołania do `shared/`; ścieżki według `ledger.md`; aktualizacja własnej sekcji `task.yaml` na końcu; pytania do `questions.yaml` |
| `explaining-confluence-analysis` | kopia pliku HTML do `.task/<KLUCZ>/wyjasnienie.html`, gdy klucz zadania znany |
| `analyzing-confluence-feasibility` | raport do `wykonalnosc.md`; pytania do `questions.yaml` z etapem `wykonalnosc` |
| `planning-jira-implementation` | cache do `analiza.md`; plan do `plan.md`; macierz do `matrix.yaml` (tabela w planie renderowana z niej); nazwy testów z sufiksem identyfikatora; `questions.yaml` zamiast dwóch sekcji w planie; manifest `init`, jeżeli router go nie utworzył |
| `implementing-jira-task` | dziennik do `log.md`; stan wierszy w `matrix.yaml`; commity z `Krok N; REG-xx`; argument `rownolegle` (sekcja 2.8); `trace.py` po ostatnim kroku zamiast ręcznego przejścia macierzy |
| `java-code-review` | `context: fork`; klucz z argumentu lub gałęzi; raport do `review/local-<N>.html`; `trace.py` przed oceną pokrycia |
| `reviewing-java-commits` | `context: fork`; linki jako argumenty; raport do `review/pr-<N>.md`; tryb przyrostowy względem ostatniego raportu obu trybów; `trace.py` |
| `smoke-testing-locally` | przypadki negatywne z `matrix.yaml`; raport, skrypt i logi do `.task/<KLUCZ>/`; środowisko do `.task/_srodowisko.md` |
| `running-task-retro` | źródła z `.task/<KLUCZ>/` i `questions.yaml`; `metrics.json`; pull request do repozytorium skilli za zgodą |
| **nowy** `task` | router (sekcja 2.6) |
| `session-dashboard` | źródło `task.yaml`; sekcja metryk |
| `plugin.json`, README, `PLAN_ROZWOJU_SKILLI.md` | opis, ściągawka komend, migracja katalogów |

Migracja istniejących zadań: jednorazowy skrypt `shared/scripts/migrate.py`, który przenosi pliki z siedmiu starych katalogów do `.task/<KLUCZ>/` według tabeli z sekcji 2.1 i buduje manifest z tego, co znajdzie. Stare ścieżki przestają być wspierane po fazie 1.

---

## 4. Kolejność wdrożenia

| Faza | Zakres | Dlaczego w tej kolejności |
|---|---|---|
| 1 | `shared/` (access, questions, standards, style, ledger); kontrakt `.task/`; `task.py`; migracja ścieżek we wszystkich skillach; `migrate.py`; naprawa niezgodności review → retro | niskie ryzyko, usuwa duplikację i jedyny znany błąd; fundament dla reszty |
| 2 | router `/task`; `context: fork` w obu skillach review z argumentami; dashboard czyta manifesty | widoczna zmiana dla użytkownika, bez zmian w kodzie zespołu |
| 3 | konwencja sufiksów identyfikatorów w testach i commitach; `trace.py`; smoke z `matrix.yaml` | wymaga jednej decyzji zespołu o nazwach testów |
| 4 | subagenci dla grup równoległych w implementacji | opcjonalny argument, nie zmienia domyślnego zachowania |
| 5 | hooki bramek | dopiero gdy manifest jest stabilny i router sprawdzony w kilku zadaniach |
| 6 | `metrics.json`, `retro/metrics.jsonl`, pull request z retro do repozytorium skilli, sekcja trendów w dashboardzie | zamyka pętlę; potrzebuje danych z kilku zadań, żeby mieć sens |

Każda faza kończy się `claude plugin validate .` i przejściem jednego zadania testowego przez cały cykl z `--plugin-dir`.

---

## 5. Ryzyka i rzeczy do zweryfikowania

| Ryzyko | Jak sprawdzić lub ograniczyć |
|---|---|
| `${CLAUDE_SKILL_DIR}/../../shared/` nie rozwiązuje się w cache pluginu | test z `--plugin-dir` i po instalacji z marketplace; awaryjnie `shared/` jako ukryty skill `user-invocable: false` z plikami obok |
| Model psuje YAML przy ręcznej edycji | skille edytują manifest wyłącznie przez `task.py set ...`; `matrix.yaml` pisze tylko planning, inni zmieniają pole `stan` przez skrypt |
| Skill w forku nie może dopytać | wszystkie wejścia jako argumenty; pytania zamiast blokady idą do `questions.yaml` |
| Hook blokuje fałszywie | wyjście `TASK_GATE=off`; hook aktywny tylko na gałęziach z kluczem; wdrożenie w fazie 5 |
| Worktree i Gradle: dwa demony, kolizje portów, wspólny `~/.m2` | równoległość tylko między repozytoriami; biblioteki publikowane przed startem grupy; `bootRun` nigdy w agentach (smoke pozostaje osobnym skillem) |
| `.task/` lokalne: utrata wiedzy przy zmianie maszyny | retro przenosi łatkę i metryki do repozytorium skilli; decyzja o commitowaniu `.task/` odwracalna jednym wpisem w `.gitignore` |
| Pluginy nie mogą ładować hooków w używanej wersji Claude Code | sprawdzić `claude --version` i dokumentację pluginów; awaryjnie wpis w `settings.json` opisany w README |
| Wzrost liczby plików na zadanie (12+) | router jako jedyny interfejs; programista nie musi znać układu katalogu |

---

## 6. Otwarte pytania

1. Czy pliki `wyjasnienie.html` mają zostać także w katalogu workspace (czyta je cały zespół), czy wyłącznie w `.task/`?
2. Czy retro ma otwierać pull request w repozytorium skilli automatycznie (za zgodą w sesji), czy tylko tworzyć gałąź?
3. Czy nazwa routera to `task`, czy coś, co nie zderzy się z przyszłymi skillami (`zadanie`, `tor`)?
4. Czy hook na `git push` ma wymagać review lokalnego, czy wystarczy review pull requesta po pushu (wtedy bramka tylko na commit)?
