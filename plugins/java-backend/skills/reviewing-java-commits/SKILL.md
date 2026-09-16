---
name: reviewing-java-commits
description: Use when asked to review a specific Java commit (by hash, tag, or branch name) — a full code review of that commit covering correctness, security, performance and maintainability, as well as compliance with this project's own coding standards (package-by-feature, jOOQ for reads, JPA/Hibernate for writes, MapStruct mapping, no needless interfaces, Liquibase changeset conventions). Static analysis only; produces a Polish-language Markdown report with class and line references, not inline PR/Bitbucket comments.
disable-model-invocation: false
---

# Reviewing Java Commits

## Overview

Full static code review of ONE commit: both compliance with this project's documented standards (Java 25, jOOQ, Hibernate/JPA, package-by-feature, Liquibase) and a genuine code review of the change itself — correctness, security, performance, resource/thread safety, error handling, readability. This is not a compliance checklist alone; treat it like a real senior-engineer review of the diff. Output is a single human-readable Markdown file, written in Polish, listing findings with the exact class and line number. No dynamic analysis — do not run the build, tests, or the application.

## When to Use

- User names a commit (hash, tag, branch, "HEAD", "ostatni commit") and asks for a code review.
- Do NOT use for reviewing a whole PR/branch diff against main unless the user explicitly wants a single commit reviewed — ask which commit if ambiguous.
- If the target directory is not a git repository, or the commit does not exist, tell the user and stop — do not guess.

## Process

1. **Resolve the commit and the branch.** Confirm the repo path and commit identifier with `git -C <repo> rev-parse <commit>`. If the user gave no commit, ask for one — do not review "recent changes" instead. Also resolve the current branch name with `git -C <repo> branch --show-current` — this drives the output file name (see Output).
2. **List every changed file**, not only `.java` files. `git -C <repo> diff-tree --no-commit-id --name-status -r <commit>`. This is a Java project, but a commit routinely also carries SQL migration scripts, jOOQ code-generation configuration, persistence/mapping configuration and similar files that bear directly on these standards — do not filter them out. Decide relevance per file:
   - `.java` files — always reviewed against both checklists below.
   - `.sql` files (migrations, schema scripts) — check whether the script is consistent with the Java change in the same commit (for example: a new column a jOOQ read or a new JPA entity field in this commit depends on, or a schema change that should have come with a corresponding entity/mapping update but didn't), and against the Liquibase standard below.
   - Liquibase master/parent changelog files (`db.changelog-master.yaml` or similar) — check whether a new changeset file added in this commit is actually wired in (see Liquibase standard below).
   - Any other changed file (build files, XML/YAML config, jOOQ-generated sources, `MapStructConfig`) — skim it only to confirm or rule out a finding tied to the standards or quality checklist below. Do not write a separate uwaga for a file that merely accompanies the change without itself violating a standard or containing a real defect.
3. **Read full file content at that commit**, not just the diff hunk — package-by-feature and encapsulation checks, and most correctness/quality checks, require seeing the whole class and its package siblings. Use `git -C <repo> show <commit>:<path>` for the changed file, and `git -C <repo> show <commit>:<dir>` (or list the working tree at that commit) to see what other classes already exist in the same package.
4. **Get real line numbers** from the file content in step 3 (line numbers in a unified diff hunk are relative/offset and easy to misreport — always number from the full file, not the patch).
5. **Apply both checklists below** — project standards (A) and general code quality (B) — to every changed/added Java class in the commit, and to any other changed file flagged as relevant in step 2. Read the diff as a reviewer would, not as a linter: ask "would I approve this?" and "what could go wrong with this change in production?", not just "does it match the six named rules?".
6. **Write the report** using the template below, in Polish, to a Markdown file (see Output Location).
7. **Report back to the user** in the chat: file path, number of findings, one-line summary of the most severe issue (if any).

### Speeding up cross-file checks with graphify

Two checks in checklist A below need to know things the diff alone can't show: whether a class is actually used from outside its package (standard 1), and whether an interface has more than one implementation anywhere in the codebase (standard 5). If the repository already has a knowledge graph built by the `graphify` skill (a `graphify-out/` directory at the repo root), query it for these cross-file questions instead of grepping the whole codebase by hand — it already indexes call and usage relationships and answers "who references this class" or "how many implementations does this interface have" faster than a manual search. If `graphify-out/` does not exist, do not build one just to review a single commit — fall back to `git grep`/`rg` across the repository as usual.

## Checklist A — this project's documented standards

For each changed Java class, and for each other changed file flagged as relevant (SQL migrations, Liquibase changelogs, jOOQ/MapStruct configuration), check:

| # | Standard | Co sprawdzić |
|---|----------|---------------|
| 1 | Package by feature | Czy pakiet jest zorganizowany wokół funkcjonalności (feature), a nie warstwy technicznej (np. globalny `controller`, `service`, `repository`)? Czy nowa/zmieniona klasa jest `public` tylko wtedy, gdy faktycznie stanowi jawne API pakietu na zewnątrz? Czy w tym samym pakiecie istnieje już inna klasa `public` — jeśli tak, to sygnał, że pakiet urósł i trzeba wydzielić podpakiet. |
| 2 | jOOQ dla odczytów | Czy zapytania SELECT, raporty, projekcje, złożone JOIN-y i paginacja są realizowane przez jOOQ? Czy metoda odczytowa nie zwraca encji zarządzanej przez JPA (np. wynik `JpaRepository.findAll()`/`findBy...()` używany jako raport lub projekcja) zamiast dedykowanego DTO/rekordu z jOOQ? |
| 3 | JPA/Hibernate dla zapisów | Czy INSERT/UPDATE/DELETE idą przez encje JPA (zarządzany cykl życia, dirty checking, kaskady, optimistic locking), a nie przez ręczny SQL lub jOOQ `insertInto`/`update`/`deleteFrom`? |
| 4 | Mapowanie przez MapStruct | Czy mapowanie obiektów korzysta z interfejsu oznaczonego `@Mapper(config = MapStructConfig.class)`, a nie z ręcznie napisanej klasy/metody przepisującej pola jedno po drugim? |
| 5 | Brak zbędnych interfejsów | Czy dla klasy z jedną implementacją sztucznie utworzono interfejs bez uzasadnienia (np. `XxxService` + `XxxServiceImpl`, gdzie nic poza tą jedną implementacją tego interfejsu nie używa)? Wyjątek: interfejsy wymagane przez framework (np. `JpaRepository<T, ID>` w Spring Data) nie są naruszeniem tej zasady. |
| 6 | Konwencje changesetów Liquibase | Czy nowy plik changesetu trzyma numerację katalogu (kolejny numer `NNN-opis.sql`, bez luk i bez duplikatu numeru już istniejącego w katalogu)? Czy nagłówek ma poprawny format (`-- liquibase formatted sql`, `-- changeset autor:identyfikator` z unikalnym identyfikatorem — nie kopiuje identyfikatora/autora z innego changesetu, `-- comment:` opisujący zmianę)? Czy insert/update danych jest idempotentny (`ON CONFLICT DO NOTHING` lub analogiczne zabezpieczenie), skoro `runOnChange:true` pozwala na wielokrotne uruchomienie? Czy nowy plik/katalog jest faktycznie dołączony do master changeloga — sprawdź, czy katalog nadrzędny jest objęty `includeAll`, czy wymaga jawnego wpisu `include: file:` w changelogu nadrzędnym (część katalogów w repozytorium może mieć własny changelog, na przykład `<moduł>/<moduł>-changelog.yaml`, zamiast `includeAll`) — jeśli tak, a commit nie dodał takiego wpisu, changeset nigdy się nie wykona. |

## Checklist B — ogólna jakość kodu (jak w każdym prawdziwym code review)

Zastosuj to niezależnie od standardów A — nawet commit w pełni zgodny z package-by-feature/jOOQ/JPA/MapStruct może zawierać błąd logiczny, lukę bezpieczeństwa albo problem wydajnościowy. Oceniaj to, co komit faktycznie wprowadza lub zmienia (włącznie z całą zmienioną metodą, nie tylko dosłownie zmienioną linią), nie plik jako całość, jeśli reszta pliku nie została dotknięta.

| # | Kategoria | Co sprawdzić |
|---|-----------|---------------|
| 7 | Poprawność logiki | Czy zmieniona logika obsługuje przypadki brzegowe (`null`, pusta kolekcja/`Optional`, wartości graniczne, pusty string)? Czy nie ma oczywistych błędów: złego warunku, odwróconej logiki, off-by-one, nieobsłużonej gałęzi `switch`/`if`, założenia o kolejności wykonania, które nie jest gwarantowane? Czy nowy kod robi to, co według nazwy metody/commita miał robić? |
| 8 | Bezpieczeństwo | Czy dane wejściowe od użytkownika są walidowane przed użyciem (długość, format, zakres)? Czy nie ma możliwości wstrzyknięcia (konkatenacja SQL zamiast parametrów, budowanie filtra LDAP przez konkatenację zamiast `LdapEncoder`/parametryzacji, path traversal przy operacjach na plikach)? Czy dane wrażliwe (hasła, tokeny, dane osobowe) nie trafiają do logów ani komunikatów wyjątków? Czy nie ma zahardkodowanych sekretów/haseł w kodzie produkcyjnym (w jawnych danych testowych — na przykład w plikach `test-data` — to nie jest naruszenie). |
| 9 | Wydajność | Czy nie ma zapytania N+1 (pętla wykonująca zapytanie do bazy albo wywołanie LDAP/HTTP per element kolekcji)? Czy kolekcja/strumień nie jest przetwarzany w sposób bez potrzeby wielokrotny (to samo obliczenie lub zapytanie powtórzone w pętli zamiast policzone raz)? Czy nowy kod nie ładuje do pamięci całego, potencjalnie dużego zbioru danych tam, gdzie wystarczyłaby paginacja lub strumieniowanie? |
| 10 | Zarządzanie zasobami i wątki | Czy zasoby (strumienie, połączenia, kontekst LDAP, transakcje) są zamykane przez try-with-resources albo kontener, a nie ręcznie i warunkowo? Czy pole instancyjne komponentu singletonowego (Spring bean) nie przechowuje mutowalnego stanu współdzielonego między żądaniami/wątkami bez synchronizacji? |
| 11 | Obsługa błędów | Czy wyjątki nie są połykane w pustym `catch` ani logowane bez kontekstu pozwalającego zdiagnozować przyczynę? Czy nie łapie się nadmiernie ogólnego `Exception`/`RuntimeException` tam, gdzie da się złapać konkretny typ? Czy komunikat nowego wyjątku (np. własnej klasy `XxxException`) niesie wystarczający kontekst (jaka wartość, jaki identyfikator), a nie tylko ogólnikowy tekst? |
| 12 | Czytelność i utrzymywalność | Czy nazwy klas/metod/zmiennych jasno opisują ich rolę, bez skrótów niejasnych poza zespołem? Czy nowa metoda nie robi zbyt wielu rzeczy naraz (wysoka złożoność cyklomatyczna, długość utrudniająca zrozumienie za jednym czytaniem)? Czy commit nie wprowadza kodu niemal identycznego do istniejącego gdzie indziej, który powinien być wspólną metodą zamiast kopii? |

Report only what the diff actually introduces or changes — do not flag pre-existing code in unrelated classes the commit did not touch, unless a change in this commit makes an existing violation worse or directly relevant.

## Output

**Language:** Polish. **Precision rule:** in every explanation of what is wrong and why, write out full words — do not use abbreviations (no "np." as a stand-in for a real example, no "itd.", "itp.", "tzn." etc.). Explain as if to someone who has never seen this class before: what the rule is, what the code does instead, and why that is a problem in concrete terms (not just "narusza zasadę X").

**File location:** `<repo-root>/CODE_REVIEW/<branch-name>.md` (create the `CODE_REVIEW/` directory if missing). `<branch-name>` is the current branch resolved in step 1 (`git -C <repo> branch --show-current`), with any `/` replaced by `-` so it is a valid single filename (for example branch `feature/PROJ-123` writes to `CODE_REVIEW/feature-PROJ-123.md`). If the repo is in a detached HEAD state (no current branch — reviewing a tag or a raw hash directly), use the short commit hash instead: `CODE_REVIEW/<short-hash>.md`. If the user specifies a different path, use that instead. Reviewing the same branch again overwrites the previous report at this path by design — the file tracks the latest review for that branch, not a running history of every past review; keep the commit hash inside the report body (see template) so the reader can tell which commit the current report covers.

**Template:**

```markdown
# Code review – commit <hash> ("<temat commita>")

Data przeglądu: <YYYY-MM-DD>
Zakres: <lista zmienionych plików istotnych dla przeglądu, na przykład klasy .java oraz skrypty .sql>

## Uwagi

### 1. <krótki, konkretny tytuł uwagi>

- **Klasa:** `pełna.ścieżka.pakietu.NazwaKlasy`
- **Linia:** <numer linii w pliku>
- **Standard/Kategoria:** <jedna z pozycji checklisty A (1–6) albo checklisty B (7–12), np. "jOOQ dla odczytów" albo "Bezpieczeństwo">
- **Co jest nie tak:** <precyzyjny, prosty opis problemu, bez skrótów>
- **Dlaczego to problem:** <konkretna konsekwencja — na przykład jaką kontrolę tracimy, jaki błąd może powstać w produkcji, jaki jest scenariusz jego wystąpienia>
- **Rekomendacja:** <konkretna zmiana do wprowadzenia>

(kolejne uwagi w tym samym formacie, ponumerowane; uporządkuj od najpoważniejszej do najmniej istotnej)

## Inne istotne obserwacje

<tylko jeśli w przeglądanym kodzie widać coś wyraźnie błędnego spoza dwunastu pozycji powyżej — na przykład kod, który się nie skompiluje, brakującą adnotację wymaganą przez JPA, albo oczywisty błąd logiczny nieujęty gdzie indziej. Opisz to tym samym sposobem: klasa, linia, co jest nie tak, dlaczego to problem. Pomiń tę sekcję całkowicie, jeśli nic takiego nie zauważono — nie szukaj na siłę dodatkowych uwag.>

## Podsumowanie

- Liczba uwag: <N>
- Standardy/kategorie naruszone w tym commicie: <lista>
```

If no violations are found, still write the file, stating explicitly that the reviewed commit complies with all standards from checklist A and raises no concerns under checklist B, and list which classes were checked.

## Common Mistakes

- Reporting line numbers from the diff patch instead of the actual file — always re-derive from `git show <commit>:<path>`.
- Reviewing the whole branch/working tree instead of the one named commit.
- Using abbreviations in the Polish explanation text ("np.", "itd." used as a substitute for spelling things out) — write full sentences instead.
- Flagging a Spring Data / framework-required interface as an unnecessary interface (standard 5's exception).
- Skipping the "read full file" step and missing a package-by-feature violation because a sibling class outside the diff wasn't checked.
- Filtering the commit down to only `.java` files and silently skipping SQL migrations, Liquibase changelogs, or config files that are relevant to a finding.
- Adding a new Liquibase changeset file and not checking whether its parent directory needs an explicit `include:` entry (some directories in a given repo use `includeAll`, others don't) — a changeset that is never included never runs, silently.
- Being purely mechanical about checklist A while missing an obvious bug, security hole, or performance problem in the same diff that checklist B would have caught — this skill is a real code review, not only a standards linter.
- Flagging a checklist B issue (performance, style, error handling) in code the commit did not touch, just because it was visible while reading the surrounding file for context.
- Spending time building a graphify knowledge graph for a repository that doesn't already have one, just to review one commit — only use graphify when `graphify-out/` already exists.
- Naming the output file after the commit hash instead of the current branch, or writing it outside `CODE_REVIEW/` — the location is `CODE_REVIEW/<branch-name>.md`, created if missing.
- Using a branch name containing `/` as-is in the file path (it would create an unwanted subdirectory) instead of replacing `/` with `-` first.
