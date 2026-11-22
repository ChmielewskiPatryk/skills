---
name: java-code-review-on-bb
description: Code review of a Bitbucket pull request (Java backend) whose ONLY result is pending (draft) comments on that pull request, visible only to the reviewer until they publish them in Bitbucket — no HTML/Markdown report, no file, no review written into the chat. Same seven axes as java-code-review (business compliance against Jira + Confluence analysis, correctness, readability, architecture, security, performance, project standards: package-by-feature, jOOQ reads, JPA writes, MapStruct, no needless interfaces, Liquibase) plus an eighth axis: conciseness checked with ponytail (code that should not exist). Use when asked to "zrób review na bb", "dodaj komentarze do PR", "review jako pending comments", or given a Bitbucket pull request link with a request to review it directly in Bitbucket.
---

# Java Code Review → pending comments na Bitbucket

## Zasada

Ten skill to `java-code-review` z innym wyjściem. **Jedynym wynikiem są komentarze w stanie PENDING na pull requeście w Bitbucket.** Autor przeglądu (użytkownik uruchamiający skill) czyta je w Bitbucket, poprawia lub usuwa i sam publikuje. Skill nigdy nie publikuje komentarza, nie zatwierdza, nie odrzuca i nie merguje pull requesta.

Nie tworzysz żadnego pliku z wynikiem (bez `CODE_REVIEW/…`, bez HTML, bez Markdown) i nie wypisujesz przeglądu w czacie. W czacie na końcu tylko jedna linia: liczba dodanych komentarzy pending (w tym ile Critical), link do pull requesta oraz — jeśli tak było — informacja, że weryfikacji biznesowej nie wykonano albo wykonano ją tylko względem Jiry. Pytania blokujące (brak klucza Jira, brak linku do analizy, brak lokalnego repozytorium) zadajesz normalnie.

## Wejście

- Link do pull requesta w Bitbucket Data Center: `<BITBUCKET_URL>/projects/<PROJECT>/repos/<REPO>/pull-requests/<ID>`. Wyciągnij z niego `PROJECT`, `REPO`, `ID`. Bez linku zapytaj o niego.
- Opcjonalnie klucz Jira i link do analizy w Confluence. Jeśli ich nie ma, ustal je jak w kroku 2 `java-code-review`.
- Lokalne repozytorium z gałęzią pull requesta: numery linii, całe pliki i testy mutacyjne bierz z niego, nie z diffu API. Jeśli bieżący katalog nie jest tym repozytorium, zapytaj o ścieżkę. Zrób `git fetch` i przegląd na `origin/<gałąź-źródłowa>`.

## Przebieg

### 1. Przegląd: osie 0–6 z `java-code-review`

Przeczytaj `${CLAUDE_SKILL_DIR}/../java-code-review/SKILL.md` i wykonaj jego kroki 1–6 bez zmian: siedem osi, weryfikacja biznesowa (Jira + Confluence + komentarze korygujące), testy mutacyjne (po każdej mutacji przywróć plik i sprawdź `git status`, czy drzewo robocze jest czyste), wagi uwag, „Structural Remedies”. **Pomiń jego krok 7 i sekcję „Output”**: zamiast nich jest krok 3 poniżej.

Metadane pull requesta (tytuł, opis, gałęzie, dotychczasowe komentarze) weź z MCP: `mcp__mcp-bitbucket__bitbucket_get_pull_request_details`, `…_get_pull_request_diff`, `…_get_pull_request_reviews`. Jeśli te narzędzia są odroczone, najpierw załaduj ich schematy przez ToolSearch.

### 2. Oś 7: Zwięzłość (ponytail)

Dodatkowa oś: czy każda linia jest potrzebna? Jeśli dostępny jest skill `ponytail:ponytail-review`, wywołaj go przez narzędzie Skill na zakresie `origin/<docelowa>...origin/<źródłowa>` w lokalnym repozytorium i weź jego wyniki dotyczące zbędnego kodu. Jeśli go nie ma, sprawdź sam, dla każdego nowego fragmentu, pierwszy pasujący stopień:

1. Czy to w ogóle musi istnieć? Opcje, flagi, konfiguracja, warstwy „na później”, których nie wymaga żadne wymaganie z kroku 2.
2. Czy w repozytorium jest już helper, serwis albo wzorzec, który to robi?
3. Czy robi to biblioteka standardowa, Spring albo już używana zależność?
4. Czy da się to zapisać krócej, i nadal czytelnie?
5. Martwy kod, nieużywane parametry, wrappery przekazujące wywołanie dalej, konwersje typów bez powodu, komentarze opisujące „co” zamiast „dlaczego”.

Czego nie zgłaszaj jako zbędnego: walidacji na granicy zaufania, obsługi błędów chroniącej dane, kontroli uprawnień, testów oraz kodu wymaganego przez standardy projektu (MapStruct, encje JPA, changesety).

Waga: domyślnie **Do przemyślenia:** (zamiast Consider). Bez prefiksu (Required), gdy zbędny kod jest duży (na przykład cała klasa, warstwa albo abstrakcja z jedną implementacją) albo duplikuje istniejący helper. Każdy komentarz tej osi pokazuje, co usunąć albo czym zastąpić, i zaczyna się od `[ponytail]`.

### 3. Komentarze pending na Bitbucket

**Dlaczego REST, a nie MCP:** narzędzia `mcp-bitbucket` (`bitbucket_add_pull_request_comment`, `…_file_line_comment`) publikują komentarz od razu i nie mają stanu pending. **Nigdy ich tu nie używaj.** Komentarze dodawaj przez REST API Bitbucket Data Center z `"state": "PENDING"`.

**Dostęp:** potrzebne są zmienne środowiskowe `BITBUCKET_URL` i `BITBUCKET_TOKEN`. Jeśli ich nie ma, zatrzymaj się i poproś użytkownika, żeby je ustawił (na przykład w `env` w `~/.claude/settings.json`). Nie wyciągaj tokenu z konfiguracji serwerów MCP i nie wypisuj go nigdzie.

**Unikaj duplikatów:** przed dodaniem komentarzy pobierz aktywność pull requesta:

```bash
curl -sf -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  "$BITBUCKET_URL/rest/api/latest/projects/$PROJECT/repos/$REPO/pull-requests/$ID/activities?limit=500"
```

Pomiń uwagę, jeśli w tym samym `path:line` jest już komentarz (Twój albo cudzy, pending albo opublikowany) o tym samym problemie. Jeśli ktoś już zgłosił problem, a kod nadal go ma, dodaj odpowiedź (`"parent": {"id": N}`) zamiast nowego wątku.

**Jedna uwaga to jeden komentarz.** Treść komentarza po polsku, w Markdown:

```
**<Waga>:** <tytuł> · oś: <oś> · <ID wymagania, jeśli dotyczy>

<problem w 1–3 zdaniach, z konkretem: co się stanie, dla jakich danych>

<propozycja zmiany: nazwana restrukturyzacja albo fragment kodu>
```

Wagi i prefiksy jak w `java-code-review` (Critical / bez prefiksu / Kosmetyka / Consider / FYI; zamiast `Nit:` pisz `**Kosmetyka:**`). Nie wklejaj tokenów, haseł ani danych osobowych z kodu albo z Jiry.

**Komentarz liniowy**, gdy linia uwagi jest w diffie:

```bash
jq -n --rawfile text /ścieżka/do/komentarza.md \
      --arg path "$FILE" --argjson line "$LINE" --arg lineType ADDED --arg fileType TO \
  '{text: $text, state: "PENDING",
    anchor: {path: $path, line: $line, lineType: $lineType, fileType: $fileType, diffType: "EFFECTIVE"}}' |
curl -sf -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" -H "Content-Type: application/json" \
  --data @- "$BITBUCKET_URL/rest/api/latest/projects/$PROJECT/repos/$REPO/pull-requests/$ID/comments"
```

- `path` względem katalogu głównego repozytorium. `line` to numer linii w pliku po zmianie (`fileType: TO`) dla linii `ADDED` i `CONTEXT`. Dla usuniętej linii użyj `lineType: REMOVED`, `fileType: FROM` i numeru linii w pliku przed zmianą.
- Gdy linii nie ma w diffie (problem w niezmienionym kodzie albo brak w całym pliku), dodaj komentarz do pliku bez `line`/`lineType` (`anchor: {path, diffType: "EFFECTIVE"}`). Jeśli pliku w ogóle nie ma w diffie, dodaj komentarz ogólny bez `anchor` i podaj w nim `plik:linia`.
- Plik z treścią komentarza trzymaj w katalogu scratchpad, nie w repozytorium.

**Zabezpieczenie przed publikacją (obowiązkowe):** po **pierwszym** POST sprawdź w odpowiedzi `.state`. Jeśli to nie `"PENDING"` (starszy serwer ignoruje to pole i publikuje komentarz):

1. natychmiast usuń ten komentarz: `curl -sf -X DELETE -H "Authorization: Bearer $BITBUCKET_TOKEN" "$BITBUCKET_URL/rest/api/latest/projects/$PROJECT/repos/$REPO/pull-requests/$ID/comments/<id>?version=<version>"`;
2. nie dodawaj kolejnych komentarzy;
3. powiedz użytkownikowi, że ten serwer Bitbucket nie obsługuje komentarzy pending, i zapytaj, co dalej.

Gdy POST zwróci błąd (4xx/5xx), nie ponawiaj go w ciemno: przeczytaj komunikat i popraw anchor (najczęściej numer linii spoza diffu). Jeśli nie da się tego poprawić, dodaj uwagę jako komentarz do pliku.

**Bez komentarza podsumowującego.** Nie dodawaj ogólnego komentarza z werdyktem, tabelą wymagań ani listą uwag. Wymaganie ze statusem `Brak` albo `Niezgodne` to osobna uwaga Critical: komentarz liniowy przy kodzie, który powinien je realizować, a gdy takiego miejsca nie ma, komentarz ogólny z ID wymagania. Pytania do analityka nie trafiają do Bitbucket.

Kolejność dodawania: najpierw najważniejsza uwaga (na niej działa zabezpieczenie), potem reszta według wagi.

## Czerwone flagi

- Użycie narzędzia MCP `bitbucket_add_pull_request_comment` / `…_file_line_comment`: komentarz zostaje opublikowany, a autor nie może go już po cichu poprawić.
- Dodanie kolejnych komentarzy bez sprawdzenia `.state == "PENDING"` w odpowiedzi na pierwszy.
- Zapisanie raportu do pliku albo wypisanie listy uwag w czacie.
- Numery linii wzięte z diffu API zamiast z pliku w lokalnym repozytorium.
- Dodanie komentarza podsumowującego (werdykt, tabela wymagań, liczniki).
- Zgłoszenie walidacji, obsługi błędów albo kontroli uprawnień jako „zbędnego kodu” w osi ponytail.
- Brudne drzewo robocze po testach mutacyjnych.
