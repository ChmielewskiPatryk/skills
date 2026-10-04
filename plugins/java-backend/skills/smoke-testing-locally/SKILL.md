---
name: smoke-testing-locally
description: Use when asked to smoke test a Jira task locally before a pull request or before handing it over — "przetestuj lokalnie", "smoke test", "sprawdź, czy to wstaje i działa". Works out which repositories were modified for the task (branch with the task key, diff against the base branch in every repository of the workspace, optionally the repository list from the implementation plan), publishes changed libraries such as the API contract to Maven Local, recreates the database containers from scratch after confirmation, starts the modified services with Gradle, works out on its own which endpoints the task added or affected, calls them with curl (happy path plus negative cases from the analysis), writes a Polish-language report with a replayable request script and stops everything it started.
disable-model-invocation: true
argument-hint: "[KLUCZ-ZADANIA]"
---

# Smoke Testing Locally

## Overview

Runs a quick end-to-end check of one Jira task on the developer's machine: changed libraries are published to Maven Local, the database is recreated from scratch in Docker, every service modified in the task is started from its task branch with Gradle, and the endpoints added or affected by the task are called with `curl`. The result is a report in `SMOKE_TEST/<KLUCZ-ZADANIA>.md` with every request, the expected and actual response, plus `SMOKE_TEST/<KLUCZ-ZADANIA>-zadania.sh` — a script that replays the same requests.

There is no request collection to rely on. The skill works out on its own which endpoints to call and with what data, from the code changes, the API contract, the implementation plan and the analysis.

Environment of this team, assumed by default:

- services are Java applications started with Gradle (`./gradlew bootRun`), never in Docker;
- libraries are Gradle projects without executable code (for example the API contract); when changed, they are published with `./gradlew publishToMavenLocal`;
- the database runs in Docker, usually from the docker compose file in the `crypto-async-api` repository;
- resetting the database always means removing its containers and volumes and starting them from scratch;
- start order: database first, then the applications;
- authorization is out of scope.

Anything that cannot be read from the repositories is asked once and saved in `SMOKE_TEST/srodowisko.md`, so later runs do not ask again.

## When to Use

- User asks for a local smoke test of a task, "przetestuj lokalnie", "sprawdź, czy to wstaje", usually after the implementation and before the pull request or after review fixes.
- The task key is given as an argument, or can be read from the current branch name (for example `feature/PROJ-123-opis` → `PROJ-123`). If neither works, ask for the key.
- Not for: unit or integration tests (`gradle test`, `gradle check`) — those are part of the implementation; code review (`/java-backend:reviewing-java-commits`); testing on shared environments (DEV, TEST) — this skill only touches the local machine.

## Bezpieczeństwo

- **Tylko lokalnie.** Skill uruchamia usługi i resetuje bazy wyłącznie na maszynie programisty. Jeżeli konfiguracja wskazuje na bazę danych lub adres, który nie jest lokalny (`localhost`, `127.0.0.1`, nazwa kontenera z lokalnego docker compose), zatrzymaj się i zapytaj. Nigdy nie resetuj bazy na wspólnym środowisku i nie wysyłaj żądań poza `localhost`.
- **Reset baz za zgodą.** Przed pierwszym resetem w sesji pokaż plik docker compose, kontenery i wolumeny, które zostaną usunięte, oraz dokładne komendy, i poczekaj na potwierdzenie. Kolejne uruchomienia w tej samej sesji nie wymagają ponownej zgody, chyba że zmienił się plik albo lista kontenerów.
- **Bez zmian w kodzie.** Skill nie poprawia kodu, nie zmienia plików budowania, nie commituje i nie przełącza gałęzi bez pytania. Jeżeli repozytorium jest na innej gałęzi niż gałąź zadania albo ma niezacommitowane zmiany, zgłoś to i zapytaj, co zrobić.
- **Dane testowe przez API.** Dane potrzebne do testu twórz wywołaniami endpointów. Bezpośredni zapis do bazy (`INSERT`) tylko wtedy, gdy nie da się tego zrobić przez API, i tylko po pokazaniu skryptu programiście i jego zgodzie.
- **Sprzątanie.** Na końcu zatrzymaj każdy proces Gradle, który skill uruchomił, także gdy test się nie powiódł.
- Nie wypisuj haseł ani tokenów z plików konfiguracyjnych w odpowiedziach ani w raporcie.

## Process

1. **Ustal klucz zadania** z argumentu albo z nazwy bieżącej gałęzi.
2. **Wczytaj konfigurację środowiska** z `SMOKE_TEST/srodowisko.md` w katalogu roboczym (katalog, w którym leżą repozytoria, albo katalog główny repozytorium, jeżeli pracujesz w jednym). Jeżeli pliku nie ma, przejdź dalej — powstanie w kroku 6.
3. **Ustal, które projekty zmodyfikowano w zadaniu.** Dla każdego repozytorium git w katalogu roboczym (i w jego bezpośrednich podkatalogach):
   - znajdź gałąź zawierającą klucz zadania, lokalną albo zdalną (`git -C <repo> branch -a --list "*<KLUCZ>*"`);
   - wyznacz gałąź bazową (domyślna gałąź zdalna, `git -C <repo> symbolic-ref refs/remotes/origin/HEAD`, albo gałąź docelowa podana w planie) i policz zmiany: `git -C <repo> diff --name-status $(git -C <repo> merge-base <bazowa> <gałąź-zadania>) <gałąź-zadania>`;
   - repozytorium z gałęzią zadania i niepustym diffem jest **zmodyfikowane w zadaniu**.
   Jeżeli istnieje `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md`, porównaj tę listę z repozytoriami wymienionymi w krokach planu. Repozytorium z planu bez gałęzi albo bez zmian zgłoś w raporcie jako „zaplanowane, ale niezmienione” — to sygnał, że część zadania mogła zostać pominięta. Nie przerywaj z tego powodu testu.
4. **Podziel zmodyfikowane projekty na usługi i biblioteki** — samodzielnie, bez pytania:
   - wpis w `SMOKE_TEST/srodowisko.md`, jeżeli jest — ma pierwszeństwo;
   - projekt ma kod wykonywalny: klasę z metodą `main` albo z `@SpringBootApplication`, plugin `org.springframework.boot` lub `application` w `build.gradle(.kts)` → **usługa**;
   - projekt Gradle bez kodu wykonywalnego (brak klasy z `main`, plugin `java-library` lub `maven-publish`, na przykład sama specyfikacja OpenAPI z generowaniem kodu) → **biblioteka**;
   - pytaj tylko wtedy, gdy projekt ma kod wykonywalny, ale jest wyraźnie narzędziem, a nie usługą HTTP (na przykład generator).
   W raporcie wypisz obie grupy.
5. **Opublikuj zmienione biblioteki do Maven Local.** Dla każdej zmienionej biblioteki uruchom `./gradlew publishToMavenLocal` w jej repozytorium (na gałęzi zadania). Następnie dla każdej usługi, która od niej zależy, sprawdź, że usługa ma `mavenLocal()` w repozytoriach i że wersja biblioteki w usłudze odpowiada opublikowanej (porównaj `version` biblioteki z deklaracją zależności w usłudze, w tym w katalogu wersji `libs.versions.toml`). Jeżeli wersje się nie zgadzają albo nie ma `mavenLocal()`, nie zmieniaj plików budowania — zapytaj, czy uruchomić usługę z nadpisaniem (na przykład `--include-build ../<biblioteka>`), czy przerwać. Błąd publikacji to wynik testu — zapisz go w raporcie i zakończ.
6. **Ustal konfigurację środowiska.** Dla każdej usługi potrzebujesz: komendy startu, portu, sposobu sprawdzenia, że wstała, i bazy danych, z której korzysta. Najpierw odczytaj to z repozytoriów:
   - **start:** `./gradlew bootRun` w katalogu repozytorium, z profilem lokalnym, jeżeli istnieje plik `application-local.yml` (`--args='--spring.profiles.active=local'`); usług nie uruchamiaj w Dockerze;
   - **port:** `server.port` z konfiguracji profilu lokalnego, a gdy go nie ma — z `application.yml` (domyślnie `8080`); sprawdź, czy dwie usługi nie mają tego samego portu;
   - **gotowość:** jeżeli usługa ma `spring-boot-starter-actuator`, odpytuj `/actuator/health`; w przeciwnym razie czekaj na linię `Started <klasa> in` w logu i na otwarty port;
   - **baza danych:** plik docker compose z usługą bazy danych, zwykle w repozytorium `crypto-async-api` (szukaj tam najpierw, potem w pozostałych repozytoriach katalogu roboczego). Sprawdź, czy adres bazy w konfiguracji lokalnej usług wskazuje na port z tego pliku.
   Przy pierwszym uruchomieniu (brak wpisu w `SMOKE_TEST/srodowisko.md`) **zawsze zapytaj, czy znaleziony plik docker compose to właściwa baza** dla uruchamianych usług — z hipotezą: ścieżka pliku, nazwy usług w pliku, porty. W tym samym pytaniu zbierz wszystko inne, czego nie udało się ustalić, każde z hipotezą do potwierdzenia jednym słowem. Po odpowiedzi zapisz konfigurację w `SMOKE_TEST/srodowisko.md` według szablonu poniżej i dopisz `SMOKE_TEST/` do `.gitignore`, jeżeli katalog leży w repozytorium.
7. **Sprawdź stan repozytoriów.** Każda uruchamiana usługa i każda zmieniona biblioteka musi być na gałęzi zadania, bez niezacommitowanych zmian albo ze zmianami, o których programista wie. Rozbieżności zgłoś i zapytaj, czy kontynuować.
8. **Postaw bazę od zera** (po potwierdzeniu, patrz „Bezpieczeństwo”): `docker compose -f <plik> down -v`, a potem `docker compose -f <plik> up -d`. Reset zawsze oznacza usunięcie kontenerów razem z wolumenami — nie czyść tabel ręcznie i nie zostawiaj starego wolumenu. Poczekaj, aż port bazy przyjmuje połączenia (i healthcheck kontenera, jeżeli plik go definiuje), limit 2 minuty.
9. **Uruchom usługi** dopiero po bazie, w kolejności zależności między nimi (usługa, którą inne wywołują, startuje pierwsza; jeżeli nie da się tego ustalić, startuj po kolei w dowolnej kolejności). Procesy uruchamiaj w tle, z wyjściem przekierowanym do `SMOKE_TEST/logi/<usługa>.log`. Czekaj na gotowość każdej usługi (sprawdzaj co kilka sekund, limit 3 minuty na usługę). Migracje Liquibase wykonują się przy starcie — błąd migracji to wynik testu, nie powód do ręcznej naprawy. Jeżeli usługa nie wstanie, przeczytaj koniec jej logu, wpisz przyczynę do raportu, zatrzymaj to, co już uruchomiono, i przejdź do kroku 14 — nie wysyłaj żądań na połowie środowiska.
10. **Ustal endpointy do testu.** Nie ma gotowej kolekcji żądań — wyznacz zakres sam:
    - **nowe i zmienione endpointy:** metody kontrolerów (`@RestController`, `@*Mapping`) dodane lub zmienione w diffie z kroku 3 oraz ścieżki dodane lub zmienione w specyfikacji OpenAPI w zmienionym kontrakcie;
    - **endpointy, których zachowanie zmieniło się pośrednio:** dla zmienionych klas serwisów, repozytoriów, mapperów i encji znajdź kontrolery, które z nich korzystają (wyszukiwanie wywołań w kodzie usługi), i dodaj te endpointy;
    - **endpointy z planu:** ścieżki wymienione w krokach planu, jeżeli plan istnieje — endpoint z planu, którego nie ma w kodzie, to ustalenie do raportu.
    Dla każdego endpointu zapisz: usługę, metodę HTTP, pełną ścieżkę (z prefiksem `server.servlet.context-path`, jeżeli jest), klasę i metodę kontrolera oraz powód, dla którego trafił do zakresu.
11. **Zaprojektuj żądania.** Dla każdego endpointu:
    - **ścieżka szczęśliwa:** co najmniej jedno poprawne żądanie. Ciało i parametry zbuduj z kontraktu (schemat OpenAPI) albo z klasy DTO i jej adnotacji walidacji (`@NotNull`, `@Size`, `@Pattern`, typy pól). Wartości dobieraj tak, żeby miały sens biznesowy według analizy i planu, a nie przypadkowe;
    - **przypadki negatywne:** jedno żądanie na każdą regułę z macierzy wymagań i testów planu, którą da się sprawdzić z zewnątrz (walidacja, warunek brzegowy, nieistniejący zasób → 404, konflikt → 409), oraz jedno żądanie z niepoprawnym ciałem, jeżeli endpoint przyjmuje ciało;
    - **oczekiwany wynik:** kod statusu i kluczowe pola odpowiedzi według analizy i planu, a gdy ich brak — według kontraktu. Zapisz, skąd pochodzi oczekiwanie (wiersz macierzy, sekcja analizy, kontrakt);
    - **dane wstępne:** baza jest pusta, z wyjątkiem danych z migracji. Jeżeli endpoint wymaga istniejącego zasobu, utwórz go najpierw innym endpointem (na przykład `POST` przed `GET`) i użyj identyfikatora z odpowiedzi. Kolejność żądań ma to uwzględniać.
    Autoryzacją się nie zajmuj — nie dodawaj nagłówków uwierzytelniania. Jeżeli endpoint odpowiada 401 albo 403 na każde żądanie, zapisz go w raporcie jako „wymaga autoryzacji — nie przetestowany” i nie próbuj tego obchodzić.
12. **Wykonaj żądania** przez `curl` (`-s -w '%{http_code}'`, `-H 'Content-Type: application/json'`), na `localhost` i porcie usługi, w kolejności z kroku 11. Wszystkie żądania zapisz w `SMOKE_TEST/<KLUCZ>-zadania.sh` jako skrypt do ponownego uruchomienia (bez danych wrażliwych; identyfikatory z wcześniejszych odpowiedzi przekazywane przez zmienne). Przy każdej rozbieżności z oczekiwanym wynikiem przeczytaj log usługi z chwili żądania i wybierz najważniejszą linię wyjątku.
13. **Zapisz raport** `SMOKE_TEST/<KLUCZ>.md` według szablonu z sekcji Output.
14. **Posprzątaj.** Zatrzymaj procesy Gradle, które skill uruchomił (zakończ proces i sprawdź, że port jest wolny; `./gradlew --stop` tylko jeżeli przed startem skilla nie działał żaden demon Gradle). Kontenery bazy zostaw uruchomione, jeżeli działały przed startem skilla; jeżeli skill je uruchomił od zera, zatrzymaj je przez `docker compose -f <plik> down` (bez `-v`, żeby można było obejrzeć dane po teście). Zgłoś w czacie: ścieżkę raportu, liczbę żądań zgodnych i niezgodnych z oczekiwaniem, najważniejszy problem jednym zdaniem.

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Pierwsze uruchomienie, baza danych z docker compose (zwykle `crypto-async-api`) | Zapytaj, czy to właściwy plik, z hipotezą (ścieżka, usługi, porty); razem z tym zapytaj o wszystko inne, czego nie ustalono. Zapisz odpowiedź w `SMOKE_TEST/srodowisko.md`. |
| Konfiguracja jest już w `SMOKE_TEST/srodowisko.md` | Nie pytaj — użyj jej. Zapytaj tylko o nową usługę, której tam brakuje. |
| Nie wiadomo, czy projekt jest usługą, czy biblioteką | Nie pytaj — kod wykonywalny (klasa z `main`) oznacza usługę, jego brak bibliotekę. |
| Pierwszy reset bazy w sesji | Pokaż plik, kontenery, wolumeny i komendy, poczekaj na zgodę. |
| Adres bazy albo usługi nie jest lokalny | Zatrzymaj się i zapytaj. |
| Repozytorium jest na innej gałęzi niż gałąź zadania albo ma niezacommitowane zmiany | Zapytaj, czy przełączyć gałąź, testować bieżący stan, czy pominąć repozytorium. |
| Wersja zmienionej biblioteki nie trafia do usługi | Zapytaj, czy uruchomić z nadpisaniem, czy przerwać. Nie zmieniaj plików budowania. |
| Usługa nie wstaje, migracja albo publikacja biblioteki się nie wykonuje | Nie pytaj i nie naprawiaj — zapisz przyczynę z logu w raporcie i zakończ. |
| Nie wiadomo, jaki wynik jest poprawny (analiza i plan milczą, kontrakt nie opisuje odpowiedzi) | Nie pytaj — wyślij żądanie, zapisz odpowiedź jako „bez oczekiwania” i wypisz w raporcie do oceny przez programistę. |
| Endpoint wymaga danych, których nie da się utworzyć przez API | Pokaż skrypt `INSERT` i zapytaj o zgodę; bez zgody pomiń endpoint i zapisz to w raporcie. |
| Endpoint odpowiada 401 albo 403 na wszystko | Nie pytaj — zapisz jako „wymaga autoryzacji — nie przetestowany”. |
| Repozytorium z planu nie ma gałęzi zadania | Nie pytaj — zapisz w raporcie jako „zaplanowane, ale niezmienione”. |

## Output

**Język:** polski, zwykłym językiem, bez skrótowców.

**Lokalizacja:** `SMOKE_TEST/<KLUCZ-ZADANIA>.md` w katalogu roboczym. Obok: `SMOKE_TEST/<KLUCZ-ZADANIA>-zadania.sh` (żądania do ponownego uruchomienia), `SMOKE_TEST/logi/<usługa>.log` i `SMOKE_TEST/srodowisko.md`. Ponowny test tego samego zadania nadpisuje raport i skrypt — data i commity są w nagłówku.

**Szablon raportu:**

```markdown
# Smoke test – <KLUCZ-ZADANIA>

Data: <data i godzina>
Wynik: <„zaliczony” | „niezaliczony — <N> z <M> żądań niezgodnych z oczekiwaniem” | „przerwany — <przyczyna>”>
Skrypt żądań: `SMOKE_TEST/<KLUCZ-ZADANIA>-zadania.sh`

## Zakres

| Repozytorium | Gałąź | Commit | Rodzaj | Co zrobiono |
|---|---|---|---|---|
| <nazwa> | <gałąź> | <skrócony hash> | biblioteka | opublikowana do Maven Local, wersja <wersja> |
| <nazwa> | <gałąź> | <skrócony hash> | usługa | uruchomiona na porcie <port> |

Zaplanowane, ale niezmienione: <repozytoria z planu bez gałęzi lub zmian — albo „brak”>

## Uruchomienie

| Element | Komenda | Wynik |
|---|---|---|
| Baza danych (<plik>) | `docker compose down -v` + `up -d` | <gotowa po N s / błąd> |
| <usługa> | `./gradlew bootRun ...` | <gotowa po N s / błąd> |

<jeżeli coś nie wstało: przyczyna z logu, 5–15 najważniejszych linii, i ścieżka do pełnego logu>

## Endpointy w zakresie

| Usługa | Metoda i ścieżka | Kontroler | Powód |
|---|---|---|---|
| <nazwa> | POST /api/... | `<Klasa>.<metoda>` | nowy endpoint |
| <nazwa> | GET /api/... | `<Klasa>.<metoda>` | zmieniony serwis `<Klasa>` |

## Żądania

| Nr | Metoda i ścieżka | Przypadek | Oczekiwano (źródło) | Otrzymano | Wynik |
|---|---|---|---|---|---|
| 1 | POST /api/... | ścieżka szczęśliwa | 201, pole `id` (kontrakt) | 201 | OK |
| 2 | POST /api/... | REG-03: kwota powyżej limitu | 422 (macierz, REG-03) | 500 | błąd |
| 3 | GET /api/... | nieistniejący zasób | 404 (analiza, sekcja „Błędy”) | 404 | OK |

### Niezgodności

#### <Nr>. <metoda i ścieżka> — <przypadek>

- **Żądanie:** <ciało albo parametry, bez danych wrażliwych>
- **Oczekiwano:** <status i pola, ze źródłem>
- **Otrzymano:** <status, fragment odpowiedzi>
- **Log usługi:** <najważniejsza linia wyjątku, ścieżka do logu>

## Do oceny przez programistę

<żądania „bez oczekiwania”, endpointy pominięte (autoryzacja, brak danych wstępnych), endpointy z planu, których nie ma w kodzie — albo „brak”>
```

**Szablon `SMOKE_TEST/srodowisko.md`:**

```markdown
# Konfiguracja smoke testów

Baza danych: <plik docker compose, na przykład `../crypto-async-api/docker-compose.yml`; usługi bazy i porty>

## <nazwa-repozytorium>

- Rodzaj: <usługa | biblioteka>
- Start: <komenda Gradle, uruchamiana w katalogu repozytorium, na przykład `./gradlew bootRun --args='--spring.profiles.active=local'`> (dla biblioteki: `./gradlew publishToMavenLocal`)
- Port: <port>
- Gotowość: <`/actuator/health` albo „linia Started w logu i otwarty port”>
- Zależy od usług: <nazwy albo „brak”>
```

## Częste błędy

- Uruchamianie z góry ustalonej listy usług zamiast tych, które zostały zmodyfikowane w zadaniu.
- Uruchamianie usług w Dockerze zamiast przez Gradle albo przyjęcie bazy z `crypto-async-api` bez potwierdzenia przy pierwszym uruchomieniu.
- Uruchomienie usług przed bazą danych albo zanim baza przyjmuje połączenia.
- Pytanie programisty, czy projekt jest usługą, czy biblioteką, gdy wynika to z kodu (klasa z `main` albo jej brak).
- Pominięcie `publishToMavenLocal` dla zmienionej biblioteki albo nieprzypilnowanie, że usługa buduje się z opublikowaną wersją, a nie ze starą z repozytorium artefaktów.
- Reset bazy przez czyszczenie tabel albo bez `-v` — reset to zawsze usunięcie kontenerów i wolumenów i postawienie od zera.
- Reset bazy bez potwierdzenia albo na bazie, która nie jest lokalna.
- Testowanie tylko endpointów, których kontroler się zmienił, z pominięciem endpointów, na które wpływa zmieniony serwis lub repozytorium.
- Żądania z przypadkowymi wartościami zamiast danych zgodnych z analizą, przez co test kończy się błędem walidacji, który nic nie mówi o zmianie.
- Oczekiwany wynik wymyślony bez źródła — każde oczekiwanie ma wskazanie: wiersz macierzy, sekcja analizy albo kontrakt.
- Zapis danych testowych bezpośrednio do bazy bez zgody, gdy dało się je utworzyć przez API.
- Dodawanie nagłówków autoryzacji albo obchodzenie zabezpieczeń — autoryzacja jest poza zakresem.
- Wysyłanie żądań, gdy któraś usługa nie wstała.
- Naprawianie kodu, migracji albo plików budowania w trakcie testu — skill tylko raportuje.
- Pozostawienie uruchomionych procesów Gradle po zakończeniu, także po błędzie.
- Ponowne pytanie o konfigurację, która jest już w `SMOKE_TEST/srodowisko.md`.
- Wklejenie do raportu albo skryptu haseł, tokenów lub pełnych odpowiedzi z danymi osobowymi.
