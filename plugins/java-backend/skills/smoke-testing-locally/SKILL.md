---
name: smoke-testing-locally
description: Use when asked to smoke test a Jira task locally before a pull request or before handing it over — "przetestuj lokalnie", "smoke test", "odpal bruno dla zadania". Works out which repositories were modified for the task (branch with the task key, diff against the base branch in every repository of the workspace, optionally the repository list from the implementation plan), starts only those that are runnable services (changed libraries such as the API contract are not started, but services must see their new version), resets their databases after confirmation, waits for health checks, runs the Bruno collection or folder for new and changed endpoints with `bru run`, writes a Polish-language report and stops the services it started.
disable-model-invocation: true
argument-hint: "[KLUCZ-ZADANIA]"
---

# Smoke Testing Locally

## Overview

Runs a quick end-to-end check of one Jira task on the developer's machine: every service modified in the task is started from its task branch, its database is reset to a clean state, and the Bruno requests for the endpoints touched by the task are executed against it. The result is a report in `SMOKE_TEST/<KLUCZ-ZADANIA>.md` with every request, its status code and the assertion results.

The skill does not assume which services exist. It finds out from the repositories which projects the task modified and which of them are runnable services. Anything about the local environment that cannot be read from the repositories (how a service is started, how its database is reset, where the Bruno collection lives) is asked once and saved in `SMOKE_TEST/srodowisko.md`, so later runs do not ask again.

## When to Use

- User asks for a local smoke test of a task, "przetestuj lokalnie", "odpal bruno", "sprawdź, czy to wstaje", usually after the implementation and before the pull request or after review fixes.
- The task key is given as an argument, or can be read from the current branch name (for example `feature/PROJ-123-opis` → `PROJ-123`). If neither works, ask for the key.
- Not for: unit or integration tests (`gradle test`, `gradle check`) — those are part of the implementation; code review (`/java-backend:reviewing-java-commits`); testing on shared environments (DEV, TEST) — this skill only touches the local machine.

## Bezpieczeństwo

- **Tylko lokalnie.** Skill uruchamia usługi i resetuje bazy wyłącznie na maszynie programisty. Jeżeli konfiguracja wskazuje na bazę danych lub adres, który nie jest lokalny (`localhost`, `127.0.0.1`, nazwa kontenera z lokalnego docker compose), zatrzymaj się i zapytaj. Nigdy nie resetuj bazy na wspólnym środowisku.
- **Reset baz za zgodą.** Przed pierwszym resetem w sesji pokaż listę baz, które zostaną wyczyszczone, i dokładne komendy, i poczekaj na potwierdzenie. Kolejne uruchomienia w tej samej sesji nie wymagają ponownej zgody, chyba że zmieniła się lista baz.
- **Bez zmian w kodzie.** Skill nie poprawia kodu, nie commituje i nie przełącza gałęzi bez pytania. Jeżeli repozytorium jest na innej gałęzi niż gałąź zadania albo ma niezacommitowane zmiany, zgłoś to i zapytaj, co zrobić.
- **Sprzątanie.** Na końcu zatrzymaj każdy proces i kontener, który skill sam uruchomił, także gdy test się nie powiódł. Nie zatrzymuj niczego, co działało przed startem skilla.
- Nie wypisuj haseł ani tokenów z plików konfiguracyjnych i środowisk Bruno w odpowiedziach ani w raporcie.

## Process

1. **Ustal klucz zadania** z argumentu albo z nazwy bieżącej gałęzi.
2. **Wczytaj konfigurację środowiska** z `SMOKE_TEST/srodowisko.md` w katalogu roboczym (katalog, w którym leżą repozytoria, albo katalog główny repozytorium, jeżeli pracujesz w jednym). Jeżeli pliku nie ma, przejdź dalej — powstanie w kroku 6.
3. **Ustal, które projekty zmodyfikowano w zadaniu.** Dla każdego repozytorium git w katalogu roboczym (i w jego bezpośrednich podkatalogach):
   - znajdź gałąź zawierającą klucz zadania, lokalną albo zdalną (`git -C <repo> branch -a --list "*<KLUCZ>*"`);
   - wyznacz gałąź bazową (domyślna gałąź zdalna, `git -C <repo> symbolic-ref refs/remotes/origin/HEAD`, albo gałąź docelowa podana w planie) i policz zmiany: `git -C <repo> diff --name-status $(git -C <repo> merge-base <bazowa> <gałąź-zadania>) <gałąź-zadania>`;
   - repozytorium z gałęzią zadania i niepustym diffem jest **zmodyfikowane w zadaniu**.
   Jeżeli istnieje `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md`, porównaj tę listę z repozytoriami wymienionymi w krokach planu. Repozytorium z planu bez gałęzi albo bez zmian zgłoś w raporcie jako „zaplanowane, ale niezmienione” — to sygnał, że część zadania mogła zostać pominięta. Nie przerywaj z tego powodu testu.
4. **Podziel zmodyfikowane projekty na usługi i biblioteki** — samodzielnie, bez pytania. W tym zespole usługi to aplikacje Java uruchamiane przez Gradle, a biblioteki to projekty Gradle bez kodu wykonywalnego. Rozpoznawaj po kolei:
   - wpis w `SMOKE_TEST/srodowisko.md`, jeżeli jest — ma pierwszeństwo;
   - projekt ma kod wykonywalny: klasę z metodą `main` albo z `@SpringBootApplication`, plugin `org.springframework.boot` lub `application` w `build.gradle(.kts)` → **usługa**;
   - projekt Gradle bez kodu wykonywalnego (brak klasy z `main`, plugin `java-library` lub `maven-publish`, na przykład sama specyfikacja OpenAPI z generowaniem kodu) → **biblioteka** (na przykład kontrakt API);
   - pytaj tylko wtedy, gdy projekt ma kod wykonywalny, ale jest wyraźnie narzędziem, a nie usługą HTTP (na przykład moduł z samymi testami albo generator).
   W raporcie wypisz obie grupy.
5. **Zapewnij widoczność zmienionych bibliotek.** Biblioteki nie są uruchamiane, ale każda usługa, która od nich zależy, musi zbudować się z ich wersją z gałęzi zadania, a nie z wersją z repozytorium artefaktów. Sprawdź, jak usługa deklaruje zależność:
   - composite build (`includeBuild` w `settings.gradle`) albo zależność projektowa — nic nie trzeba robić;
   - zależność po współrzędnych Maven — opublikuj bibliotekę lokalnie (`./gradlew publishToMavenLocal` w repozytorium biblioteki) i upewnij się, że usługa ma `mavenLocal()` w repozytoriach oraz że wersja w usłudze odpowiada opublikowanej. Jeżeli wersje się nie zgadzają albo nie ma `mavenLocal()`, nie zmieniaj plików budowania — zapytaj, czy uruchomić usługę z parametrem nadpisującym wersję (na przykład `--include-build ../<biblioteka>`), czy przerwać.
6. **Uzupełnij brakującą konfigurację jednym pytaniem.** Dla każdej usługi potrzebujesz: komendy startu, adresu health-checku, sposobu resetu bazy i komendy zatrzymania; dla całości — ścieżki do kolekcji Bruno i nazwy środowiska Bruno. Najpierw spróbuj odczytać to z repozytoriów:
   - start usługi: zawsze przez Gradle w katalogu repozytorium — `./gradlew bootRun`, z profilem lokalnym, jeżeli istnieje plik `application-local.yml` (`--args='--spring.profiles.active=local'`); usług nie uruchamiaj w Dockerze;
   - baza danych: działa w Dockerze, zwykle z pliku docker compose w repozytorium `crypto-async-api`. Znajdź ten plik (albo inny `docker-compose.yml`/`compose.yaml` z usługą bazy danych w repozytoriach katalogu roboczego) i **zawsze zapytaj przy pierwszym uruchomieniu**, czy to właściwa baza dla uruchamianych usług — z hipotezą: ścieżka pliku, nazwa usługi bazy, port. Sprawdź też, czy kontener bazy już działa (`docker ps`); jeżeli tak, nie uruchamiaj drugiego;
   - health-check: `/actuator/health` na porcie z `server.port` w konfiguracji profilu lokalnego (domyślnie `8080`), jeżeli zależność `spring-boot-starter-actuator` jest w projekcie;
   - reset bazy: usługa bazy w docker compose (`docker compose -f <plik> rm -sfv <usługa-bazy>` i ponowne `docker compose -f <plik> up -d <usługa-bazy>`) albo `liquibase dropAll update` z konfiguracją lokalną — tylko jeżeli wynika to wprost z repozytorium. Jeżeli kilka usług korzysta z jednej bazy, resetuj ją raz, przed startem pierwszej usługi;
   - Bruno: katalog z plikiem `bruno.json` w repozytoriach albo obok nich, środowisko z `environments/` o nazwie wskazującej na lokalne (`local`, `localhost`).
   Wszystko, czego nie udało się ustalić, zbierz w **jedno pytanie** z hipotezą przy każdej pozycji (tak jak w skillu planowania — programista ma potwierdzić albo poprawić, a nie pisać od zera). Po odpowiedzi zapisz pełną konfigurację w `SMOKE_TEST/srodowisko.md` według szablonu poniżej i dopisz `SMOKE_TEST/` do `.gitignore`, jeżeli katalog leży w repozytorium.
7. **Sprawdź stan repozytoriów.** Każda uruchamiana usługa i każda zmieniona biblioteka musi być na gałęzi zadania, bez niezacommitowanych zmian albo ze zmianami, o których programista wie. Rozbieżności zgłoś i zapytaj, czy kontynuować.
8. **Uruchom i zresetuj bazy** uruchamianych usług (kontener z docker compose ustalonego w kroku 6; poczekaj, aż port bazy przyjmuje połączenia) (po potwierdzeniu, patrz „Bezpieczeństwo”). Migracje Liquibase wykonają się przy starcie usługi — błąd migracji to wynik testu, nie powód do ręcznej naprawy.
9. **Uruchom usługi** w kolejności zależności (usługa, którą inne wywołują, startuje pierwsza; jeżeli nie da się tego ustalić, startuj w kolejności z pliku konfiguracji). Procesy uruchamiaj w tle, z wyjściem przekierowanym do `SMOKE_TEST/logi/<usługa>.log`. Czekaj na health-check każdej usługi (odpytuj co kilka sekund, limit 3 minuty na usługę). Jeżeli usługa nie wstanie, przeczytaj koniec jej logu, wpisz przyczynę do raportu, zatrzymaj to, co już uruchomiono, i zakończ na kroku 12 — nie uruchamiaj Bruno na połowie środowiska.
10. **Wybierz zakres Bruno.** Ustal endpointy dodane lub zmienione w zadaniu: kontrolery i specyfikacje OpenAPI z diffu z kroku 3, ścieżki z kroków planu. Dopasuj je do plików `.bru` (po metodzie i ścieżce URL, a także do plików `.bru` dodanych lub zmienionych w samym zadaniu). Uruchom `bru run <folder-lub-pliki> --env <środowisko> --reporter-json SMOKE_TEST/<KLUCZ>-bruno.json` z katalogu kolekcji. Jeżeli dla nowego endpointu nie ma żadnego pliku `.bru`, nie twórz go — zapisz to w raporcie jako brak pokrycia. Jeżeli programista poprosi o całą kolekcję, uruchom całą.
11. **Zapisz raport** `SMOKE_TEST/<KLUCZ>.md` według szablonu z sekcji Output.
12. **Zatrzymaj usługi**, które skill uruchomił (komenda zatrzymania z konfiguracji; dla procesów `bootRun` — zakończ proces i sprawdź, że port jest wolny). Zgłoś w czacie: ścieżkę raportu, liczbę żądań zakończonych sukcesem i porażką, najważniejszy problem jednym zdaniem.

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Nie wiadomo, jak uruchomić usługę, jak zresetować jej bazę albo gdzie jest kolekcja Bruno | Zapytaj raz, zbiorczo, z hipotezą; zapisz odpowiedź w `SMOKE_TEST/srodowisko.md`. |
| Konfiguracja jest już w `SMOKE_TEST/srodowisko.md` | Nie pytaj — użyj jej. Zapytaj tylko o nową usługę, której tam brakuje. |
| Pierwsze uruchomienie, baza danych z docker compose (zwykle `crypto-async-api`) | Zapytaj, czy to właściwy plik i usługa bazy, z hipotezą (ścieżka, nazwa usługi, port); zapisz odpowiedź w `SMOKE_TEST/srodowisko.md`. |
| Nie wiadomo, czy projekt jest usługą, czy biblioteką | Nie pytaj — kod wykonywalny (klasa z `main`) oznacza usługę, jego brak bibliotekę. |
| Pierwszy reset bazy w sesji | Pokaż listę baz i komendy, poczekaj na zgodę. |
| Adres bazy albo usługi nie jest lokalny | Zatrzymaj się i zapytaj. |
| Repozytorium jest na innej gałęzi niż gałąź zadania albo ma niezacommitowane zmiany | Zapytaj, czy przełączyć gałąź, testować bieżący stan, czy pominąć repozytorium. |
| Usługa nie wstaje albo migracja się nie wykonuje | Nie pytaj i nie naprawiaj — zapisz przyczynę z logu w raporcie i zakończ. |
| Nowy endpoint nie ma pliku `.bru` | Nie pytaj — zapisz brak pokrycia w raporcie. |
| Repozytorium z planu nie ma gałęzi zadania | Nie pytaj — zapisz w raporcie jako „zaplanowane, ale niezmienione”. |
| Wersja zmienionej biblioteki nie trafia do usługi | Zapytaj, czy uruchomić z nadpisaniem wersji, czy przerwać. Nie zmieniaj plików budowania. |

## Output

**Język:** polski, zwykłym językiem, bez skrótowców.

**Lokalizacja:** `SMOKE_TEST/<KLUCZ-ZADANIA>.md` w katalogu roboczym. Obok: `SMOKE_TEST/<KLUCZ-ZADANIA>-bruno.json` (surowy wynik `bru run`), `SMOKE_TEST/logi/<usługa>.log` i `SMOKE_TEST/srodowisko.md`. Ponowny test tego samego zadania nadpisuje raport — data i commity są w nagłówku.

**Szablon raportu:**

```markdown
# Smoke test – <KLUCZ-ZADANIA>

Data: <data i godzina>
Wynik: <„zaliczony” | „niezaliczony — <N> z <M> żądań zakończonych błędem” | „przerwany — <usługa> nie wstała”>

## Zakres

| Repozytorium | Gałąź | Commit | Rodzaj | Uruchomione |
|---|---|---|---|---|
| <nazwa> | <gałąź> | <skrócony hash> | usługa | tak |
| <nazwa> | <gałąź> | <skrócony hash> | biblioteka | nie — wersja dostarczona przez <composite build / publishToMavenLocal> |

Zaplanowane, ale niezmienione: <repozytoria z planu bez gałęzi lub zmian — albo „brak”>

## Uruchomienie

| Usługa | Reset bazy | Start | Health-check |
|---|---|---|---|
| <nazwa> | <wykonany / pominięty> | <komenda> | <OK po N s / błąd> |

<jeżeli usługa nie wstała: przyczyna z logu, 5–15 najważniejszych linii, i ścieżka do pełnego logu>

## Żądania Bruno

Kolekcja: <ścieżka>, środowisko: <nazwa>, zakres: <folder lub lista plików>

| Żądanie | Metoda i ścieżka | Status | Asercje | Wynik |
|---|---|---|---|---|
| <nazwa pliku .bru> | POST /api/... | 201 | 3/3 | OK |
| <nazwa pliku .bru> | GET /api/... | 500 | 0/2 | błąd |

### Błędy

#### 1. <nazwa żądania>

- **Oczekiwano:** <status lub asercja>
- **Otrzymano:** <status, fragment odpowiedzi bez danych wrażliwych>
- **Log usługi:** <najważniejsza linia wyjątku z logu, ścieżka do logu>

## Endpointy bez pokrycia w Bruno

<endpointy dodane lub zmienione w zadaniu, dla których nie znaleziono pliku `.bru` — albo „brak”>
```

**Szablon `SMOKE_TEST/srodowisko.md`:**

```markdown
# Konfiguracja smoke testów

Kolekcja Bruno: <ścieżka>
Środowisko Bruno: <nazwa>

## <nazwa-repozytorium>

- Rodzaj: <usługa | biblioteka>
- Start: <komenda Gradle, uruchamiana w katalogu repozytorium, na przykład `./gradlew bootRun --args='--spring.profiles.active=local'`>
- Baza danych: <plik docker compose i nazwa usługi bazy, na przykład `../crypto-async-api/docker-compose.yml`, usługa `postgres`, port 5432>
- Health-check: <adres>
- Reset bazy: <komenda albo „brak bazy”>
- Zatrzymanie: <komenda>
- Zależy od usług: <nazwy albo „brak”>
```

## Częste błędy

- Uruchamianie z góry ustalonej listy usług zamiast tych, które zostały zmodyfikowane w zadaniu.
- Uruchamianie usług w Dockerze zamiast przez Gradle albo przyjęcie bazy z `crypto-async-api` bez potwierdzenia przy pierwszym uruchomieniu.
- Pytanie programisty, czy projekt jest usługą, czy biblioteką, gdy wynika to z kodu (klasa z `main` albo jej brak).
- Uruchamianie biblioteki (na przykład kontraktu API) jako usługi albo pominięcie tego, że usługa buduje się ze starą wersją biblioteki z repozytorium artefaktów.
- Reset bazy bez potwierdzenia albo na bazie, która nie jest lokalna.
- Uruchomienie Bruno, zanim wszystkie usługi przeszły health-check, albo po tym, jak jedna z nich nie wstała.
- Naprawianie kodu, migracji albo plików budowania w trakcie testu — skill tylko raportuje.
- Tworzenie brakujących plików `.bru` zamiast zgłoszenia braku pokrycia.
- Pozostawienie uruchomionych procesów lub kontenerów po zakończeniu, także po błędzie.
- Ponowne pytanie o konfigurację, która jest już w `SMOKE_TEST/srodowisko.md`.
- Wklejenie do raportu haseł, tokenów albo pełnych odpowiedzi z danymi osobowymi.
