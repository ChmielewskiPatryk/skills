---
name: auto-cr
description: Automatyczne code review otwartych pull requestów w bieżącym repozytorium Bitbucket Data Center, w których użytkownik jest recenzentem i jeszcze nie zatwierdził zmian. Dla każdego nowego albo zmienionego od ostatniego przeglądu pull requesta uruchamia java-code-review-on-bb w osobnym subagencie i osobnym worktree, więc wynikiem są wyłącznie komentarze pending na Bitbucket. Pamięta, które commity już przejrzał. Uruchamiane ręcznie (/java-backend:auto-cr) albo cyklicznie (/loop 30m /java-backend:auto-cr).
argument-hint: "[ID-PR ...] [--force]"
---

# Auto CR: przegląd kolejki pull requestów

## Zasada

Ten skill niczego nie recenzuje sam. Wybiera pull requesty do przeglądu i dla każdego uruchamia skill `java-backend:java-code-review-on-bb` w subagencie. Wszystkie reguły tamtego skilla (tylko komentarze PENDING, zabezpieczenie po pierwszym POST, brak raportu) obowiązują bez zmian.

W czacie na końcu tylko krótka tabela: PR, tytuł, wynik (liczba komentarzy pending / pominięty / pytanie blokujące). Bez treści uwag.

## Argumenty

- brak: wszystkie kwalifikujące się pull requesty (patrz krok 2);
- `ID-PR ...`: tylko te pull requesty, nawet jeśli użytkownik nie jest w nich recenzentem;
- `--force`: przejrzyj ponownie także pull requesty, których ostatni commit był już przejrzany.

## Przebieg

### 1. Repozytorium i dostęp

1. Bieżący katalog musi być repozytorium git z remote `origin` na Bitbucket Data Center. Wyciągnij `PROJECT` i `REPO` z `git remote get-url origin`:
   - `ssh://git@host:7999/<project>/<repo>.git`
   - `https://host/scm/<project>/<repo>.git`

   `PROJECT` zapisz wielkimi literami. Jeśli nie da się ustalić, zapytaj o ścieżkę do repozytorium.
2. Wymagane zmienne `BITBUCKET_URL`, `BITBUCKET_TOKEN` oraz `jq`, tak jak w `java-code-review-on-bb`. Brak → zatrzymaj się i powiedz, czego brakuje. Tokenu nigdzie nie wypisuj.
3. `git fetch origin --prune`.

### 2. Kolejka pull requestów

Bez argumentów ID pobierz pull requesty, w których bieżący użytkownik (właściciel tokenu) jest recenzentem i jeszcze nie zatwierdził:

```bash
curl -sf -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  "$BITBUCKET_URL/rest/api/latest/dashboard/pull-requests?role=REVIEWER&state=OPEN&participantStatus=UNAPPROVED&limit=100" |
jq --arg p "$PROJECT" --arg r "$REPO" '[.values[]
   | select((.toRef.repository.project.key|ascii_upcase)==$p and (.toRef.repository.slug|ascii_downcase)==($r|ascii_downcase))
   | select(.draft != true)
   | {id, title, from: .fromRef.displayId, to: .toRef.displayId, commit: .fromRef.latestCommit,
      url: .links.self[0].href}]'
```

Z ID w argumentach pobierz każdy pull request z `.../projects/$PROJECT/repos/$REPO/pull-requests/<ID>` i zbuduj ten sam obiekt.

**Stan przejrzanych:** plik `$(git rev-parse --git-common-dir)/auto-cr/state.json` (poza drzewem roboczym, nie trafia do commitów), postać `{"<PROJECT>/<REPO>/<ID>": "<commit>"}`. Brak pliku = pusty stan. Pomiń pull request, gdy zapisany commit jest równy `commit` (chyba że `--force`). Każdy nowy `commit` oznacza ponowny przegląd; duplikatów komentarzy pilnuje `java-code-review-on-bb`.

Pusta kolejka → jedna linia „Brak nowych PR do przeglądu” i koniec.

### 3. Przegląd każdego pull requesta

Pull requesty przeglądaj **po kolei, nie równolegle** (każdy przegląd uruchamia testy i testy mutacyjne; równolegle przeciążą maszynę i pomieszają wyniki). Dla każdego uruchom narzędzie **Agent** z `isolation: "worktree"` (własna kopia repozytorium, drzewo robocze użytkownika zostaje nietknięte) i promptem:

```
W tym worktree wykonaj: git fetch origin && git checkout --detach origin/<from>.
Następnie wywołaj narzędziem Skill skill "java-backend:java-code-review-on-bb" z argumentem "<url>"
i wykonaj go w całości. Lokalnym repozytorium z gałęzią pull requesta jest bieżący katalog (worktree).
Nie zadawaj pytań użytkownikowi: jeśli skill wymaga odpowiedzi (brak klucza Jira, brak analizy,
serwer nie obsługuje PENDING), nie dodawaj komentarzy, przerwij i zwróć pytanie.
Zwróć dokładnie jedną linię JSON: {"status":"ok"|"blocked"|"error","pending":N,"critical":N,"note":"..."}
```

Po powrocie subagenta:

- `ok` → zapisz `commit` do `state.json` (utwórz katalog, jeśli go nie ma);
- `blocked` / `error` → nie zapisuj stanu, przenieś `note` do tabeli końcowej;
- jeśli `note` mówi, że serwer nie obsługuje komentarzy PENDING, **zatrzymaj całą kolejkę**: kolejne przeglądy skończyłyby się tak samo.

### 4. Podsumowanie

Tabela: `PR` (link), `tytuł`, `wynik`. Pod tabelą pytania blokujące, jeśli były, każde z ID pull requesta, żeby użytkownik mógł odpowiedzieć i uruchomić `/java-backend:auto-cr <ID>` ponownie.

## Tryb cykliczny

`/loop 30m /java-backend:auto-cr` sprawdza kolejkę co 30 minut w otwartej sesji. Przejrzane commity są w `state.json`, więc kolejne przebiegi biorą tylko nowe pull requesty i nowe pushe. Przy pustej kolejce odpowiedź to jedna linia.

## Czerwone flagi

- Przegląd w drzewie roboczym użytkownika zamiast w worktree subagenta (checkout cudzej gałęzi, testy mutacyjne na jego plikach).
- Równoległe subagenty przeglądające różne pull requesty.
- Zapisanie commitu do `state.json` dla przeglądu `blocked` albo `error`.
- Wypisanie treści uwag w czacie albo w pliku.
- Użycie narzędzi MCP `bitbucket_add_pull_request_comment` / `…_file_line_comment`, zatwierdzanie lub odrzucanie pull requesta.
