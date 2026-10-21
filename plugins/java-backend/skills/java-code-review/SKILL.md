---
name: java-code-review
description: Conducts multi-axis code review including this project's Java backend standards (package-by-feature, jOOQ for reads, JPA/Hibernate for writes, MapStruct, no needless interfaces, Liquibase conventions) and business verification against the Jira ticket and the linked system-analysis document in Confluence. Use before merging any change. Use when reviewing code written by yourself, another agent, or a human. Use when you need to assess code quality across multiple dimensions before it enters the main branch, and to check whether the implemented functionality actually matches the business requirements. Use when asked to review a diff or a pull request, even when the diff is pasted inline.
---

# Code Review and Quality

## Overview

Multi-dimensional code review with quality gates. Every change gets reviewed before merge — no exceptions. Review covers seven axes: business compliance, correctness, readability, architecture, security, performance, and this project's own coding standards (package-by-feature, jOOQ for reads, JPA/Hibernate for writes, MapStruct mapping, no needless interfaces, Liquibase changeset conventions).

Business compliance is checked against the Jira ticket and the system-analysis document it links to in Confluence. The analysis is the source of truth about what the change was supposed to do — not the pull request description and not the code itself.

**The approval standard:** Approve a change when it definitely improves overall code health, even if it isn't perfect. Perfect code doesn't exist — the goal is continuous improvement. Don't block a change because it isn't exactly how you would have written it. If it improves the codebase and follows the project's conventions, approve it. A change that does not implement the required business behavior is never approvable, however clean the code is.

## When to Use

- Before merging any PR or change
- After completing a feature implementation
- When another agent or model produced code you need to evaluate
- When refactoring existing code
- After any bug fix (review both the fix and the regression test)

## The Seven-Axis Review

Every review evaluates code across these dimensions:

### 0. Business Compliance

Does the code do what the business asked for? See **Step 2: Business Verification** below for the full procedure.

- Is every requirement (REG rule, acceptance criterion) from the analysis implemented?
- Does the implemented behavior match the analysis in detail — validations, statuses and transitions, permissions, calculations, error codes and messages?
- Does the backend–frontend contract match the analysis (endpoint, field names, types, required/optional, enums)?
- Does the code implement behavior that no requirement asks for?
- Is every requirement covered by a test that actually verifies the rule?

### 1. Correctness

Does the code do what it claims to do?

- Does it match the spec or task requirements?
- Are edge cases handled (null, empty, boundary values)?
- Are error paths handled (not just the happy path)?
- Does it pass all tests? Are the tests actually testing the right things?
- Are there off-by-one errors, race conditions, or state inconsistencies?

### 2. Readability & Simplicity

Can another engineer (or agent) understand this code without the author explaining it?

- Are names descriptive and consistent with project conventions? (No `temp`, `data`, `result` without context)
- Is the control flow straightforward (avoid nested ternaries, deep callbacks)?
- Is the code organized logically (related code grouped, clear module boundaries)?
- Are there any "clever" tricks that should be simplified?
- **Could this be done in fewer lines?** (1000 lines where 100 suffice is a failure)
- **Are abstractions earning their complexity?** (Don't generalize until the third use case)
- Would comments help clarify non-obvious intent? (But don't comment obvious code.)
- Are there dead code artifacts: no-op variables (`_unused`), backwards-compat shims, or `// removed` comments?
- **Is a new conditional bolted onto an unrelated flow?** That's a design smell, not a nit — push the logic into its own helper, state, or policy instead of tangling an existing path.
- **Do repeated conditionals on the same shape appear?** They signal a missing model or dispatcher. A "temporary" branch is usually permanent debt.

### 3. Architecture

Does the change fit the system's design?

- Does it follow existing patterns or introduce a new one? If new, is it justified?
- Does it maintain clean module boundaries?
- Is there code duplication that should be shared?
- Are dependencies flowing in the right direction (no circular dependencies)?
- Is the abstraction level appropriate (not over-engineered, not too coupled)?
- **Does this refactor reduce complexity or just relocate it?** Count the concepts a reader must hold to follow the change. If a "cleaner" version leaves that count unchanged, it isn't cleaner — prefer the restructuring that makes whole branches, modes, or layers disappear over one that re-centralizes the same logic. Prefer deleting an abstraction to polishing it.
- **Is feature-specific logic leaking into a shared or general-purpose module?** Keep logic in its owning layer, reuse the existing canonical helper instead of a near-duplicate, and don't normalize architectural drift.
- **Are type boundaries explicit?** Question gratuitous `any`/`unknown`/optional/casts and silent fallbacks that paper over an unclear invariant — making the boundary explicit often makes the surrounding control flow simpler.

### 4. Security

Does the change introduce vulnerabilities?

- Is user input validated and sanitized?
- Are secrets kept out of code, logs, and version control?
- Is authentication/authorization checked where needed?
- Are SQL queries parameterized (no string concatenation)?
- Are outputs encoded to prevent XSS?
- Are dependencies from trusted sources with no known vulnerabilities?
- Is data from external sources (APIs, logs, user content, config files) treated as untrusted?
- Are external data flows validated at system boundaries before use in logic or rendering?

### 5. Performance

Does the change introduce performance problems?

- Any N+1 query patterns?
- Any unbounded loops or unconstrained data fetching?
- Any synchronous operations that should be async?
- Any unnecessary re-renders in UI components?
- Any missing pagination on list endpoints?
- Any large objects created in hot paths?

### 6. Project Standards (Java backend)

Does the change follow this project's documented standards? For each changed Java class, and for each other changed file relevant to a finding (SQL migrations, Liquibase changelogs, jOOQ/MapStruct configuration), check:

| # | Standard | Co sprawdzić |
|---|----------|---------------|
| 1 | Package by feature | Czy pakiet jest zorganizowany wokół funkcjonalności (feature), a nie warstwy technicznej (na przykład globalny `controller`, `service`, `repository`)? Czy nowa lub zmieniona klasa jest `public` tylko wtedy, gdy faktycznie stanowi jawne API pakietu na zewnątrz? Czy w tym samym pakiecie istnieje już inna klasa `public` — jeśli tak, to sygnał, że pakiet urósł i trzeba wydzielić podpakiet. |
| 2 | jOOQ dla odczytów | Czy zapytania SELECT, raporty, projekcje, złożone złączenia i paginacja są realizowane przez jOOQ? Czy metoda odczytowa nie zwraca encji zarządzanej przez JPA (na przykład wynik `JpaRepository.findAll()` albo `findBy...()` użyty jako raport lub projekcja) zamiast dedykowanego obiektu transferowego albo rekordu z jOOQ? |
| 3 | JPA/Hibernate dla zapisów | Czy operacje INSERT, UPDATE i DELETE idą przez encje JPA (zarządzany cykl życia, dirty checking, kaskady, blokowanie optymistyczne), a nie przez ręcznie napisany SQL albo jOOQ `insertInto`, `update`, `deleteFrom`? |
| 4 | Mapowanie przez MapStruct | Czy mapowanie obiektów korzysta z interfejsu oznaczonego `@Mapper(config = MapStructConfig.class)`, a nie z ręcznie napisanej klasy albo metody przepisującej pola jedno po drugim? |
| 5 | Brak zbędnych interfejsów | Czy dla klasy z jedną implementacją sztucznie utworzono interfejs bez uzasadnienia (na przykład `XxxService` oraz `XxxServiceImpl`, gdzie nic poza tą jedną implementacją tego interfejsu nie używa)? Wyjątek: interfejsy wymagane przez framework (na przykład `JpaRepository<T, ID>` w Spring Data) nie są naruszeniem tej zasady. |
| 6 | Konwencje changesetów Liquibase | Czy nowy plik changesetu trzyma numerację katalogu (kolejny numer `NNN-opis.sql`, bez luk i bez duplikatu numeru już istniejącego w katalogu)? Czy nagłówek ma poprawny format (`-- liquibase formatted sql`, `-- changeset autor:identyfikator` z unikalnym identyfikatorem, nieskopiowanym z innego changesetu, oraz `-- comment:` opisujący zmianę)? Czy wstawienie albo aktualizacja danych jest idempotentna (`ON CONFLICT DO NOTHING` albo analogiczne zabezpieczenie), skoro `runOnChange:true` pozwala na wielokrotne uruchomienie? Czy nowy plik albo katalog jest faktycznie dołączony do master changeloga — sprawdź, czy katalog nadrzędny jest objęty `includeAll`, czy wymaga jawnego wpisu `include: file:` w changelogu nadrzędnym (część katalogów w repozytorium może mieć własny changelog, na przykład `<moduł>/<moduł>-changelog.yaml`, zamiast `includeAll`). Jeśli wymaga jawnego wpisu, a zmiana go nie dodała, changeset nigdy się nie wykona. |

Pułapki przy tej osi:

- Czytaj całe zmienione pliki i sąsiednie klasy w pakiecie, nie tylko diff — naruszenie package-by-feature (standard 1) często widać dopiero po klasie spoza diffu.
- Nie zawężaj przeglądu do plików `.java` — migracje SQL, changelogi Liquibase i konfiguracja też podlegają standardom.
- Nie zgłaszaj interfejsu wymaganego przez framework (Spring Data i podobne) jako zbędnego.
- Ta oś to nie linter: zgodność ze standardami nie zastępuje pozostałych osi.

**Kontrole obejmujące wiele plików.** Standard 1 (czy klasa jest używana spoza pakietu) i standard 5 (ile implementacji ma interfejs) wymagają wiedzy spoza diffu. Jeśli w katalogu głównym repozytorium istnieje `graphify-out/`, zapytaj graf wiedzy (skill `graphify`) o te relacje. Jeśli nie istnieje, nie buduj go tylko na potrzeby jednego przeglądu — użyj `git grep` albo `rg`.

## Structural Remedies

When you flag a structural problem, propose the move — not just the problem. A review that only says "this is complex" leaves the author guessing. Reach for a named restructuring:

- **Replace a chain of conditionals** with a typed model or an explicit dispatcher.
- **Collapse duplicate branches** into a single clearer flow.
- **Separate orchestration from business logic** so each reads on its own.
- **Move feature-specific logic** out of a shared module into the package that owns the concept.
- **Reuse the canonical helper** instead of a bespoke near-duplicate.
- **Make a type boundary explicit** so downstream branching disappears.
- **Delete a pass-through wrapper** that adds indirection without clarifying the API.
- **Extract a helper, or split a large file** into focused modules.

Prefer the remedy that removes moving pieces over one that spreads the same complexity around.

## Change Sizing

Small, focused changes are easier to review, faster to merge, and safer to deploy. Target these sizes:

```
~100 lines changed   → Good. Reviewable in one sitting.
~300 lines changed   → Acceptable if it's a single logical change.
~1000 lines changed  → Too large. Split it.
```

**Watch file size, not just diff size.** A small diff can still push a file past a healthy boundary — around 1000 *total* lines in a single file (distinct from the ~1000 *changed*-lines threshold above) is a common inspection signal, not a hard cap. When a change materially grows an already-large file, ask whether to extract helpers, subcomponents, or modules *first*, before piling more on. Decompose, then add.

**What counts as "one change":** A single self-contained modification that addresses one thing, includes related tests, and keeps the system functional after submission. One part of a feature — not the whole feature.

**Splitting strategies when a change is too large:**

| Strategy | How | When |
|----------|-----|------|
| **Stack** | Submit a small change, start the next one based on it | Sequential dependencies |
| **By file group** | Separate changes for groups needing different reviewers | Cross-cutting concerns |
| **Horizontal** | Create shared code/stubs first, then consumers | Layered architecture |
| **Vertical** | Break into smaller full-stack slices of the feature | Feature work |

**When large changes are acceptable:** Complete file deletions and automated refactoring where the reviewer only needs to verify intent, not every line.

**Separate refactoring from feature work.** A change that refactors existing code and adds new behavior is two changes — submit them separately. Small cleanups (variable renaming) can be included at reviewer discretion.

## Change Descriptions

Every change needs a description that stands alone in version control history.

**First line:** Short, imperative, standalone. "Delete the FizzBuzz RPC" not "Deleting the FizzBuzz RPC." Must be informative enough that someone searching history can understand the change without reading the diff.

**Body:** What is changing and why. Include context, decisions, and reasoning not visible in the code itself. Link to bug numbers, benchmark results, or design docs where relevant. Acknowledge approach shortcomings when they exist.

**Anti-patterns:** "Fix bug," "Fix build," "Add patch," "Moving code from A to B," "Phase 1," "Add convenience functions."

## Review Process

### Step 1: Understand the Context

Before looking at code, understand the intent:

```
- What is this change trying to accomplish?
- What spec or task does it implement?
- What is the expected behavior change?
```

### Step 2: Business Verification (Jira + Confluence)

Ustal, czy zmiana realizuje to, czego wymaga biznes. Źródłem prawdy jest analiza systemowa w Confluence, nie opis pull requesta, nie opis zadania w Jirze i nie sam kod.

1. **Ustal klucz zadania Jira.** Weź go od użytkownika; jeśli go nie podał, poszukaj w nazwie gałęzi (np. `feature/PROJ-123-...`), w tytule pull requesta i w komunikatach commitów. Jeśli znajdziesz klucz w ten sposób, zapisz w raporcie, skąd pochodzi. Jeśli nie znajdziesz żadnego albo znajdziesz kilka różnych — zapytaj użytkownika.
2. **Pobierz zadanie.** `mcp__mcp-atlassian__jira_get_issue(issue_key, include="comments,remote_links")`. Zbierz opis, kryteria akceptacji, komentarze i `remote_links` — link do analizy bywa dodany jako web link, a nie wklejony w opis.
3. **Znajdź link do analizy systemowej** w opisie, komentarzach i `remote_links`. Jeśli go nie ma — zapytaj użytkownika o link.
4. **Pobierz analizę** (`mcp__mcp-atlassian__confluence_get_page`) oraz komentarze do niej: zwykłe (`confluence_get_comments`) i inline (`confluence_get_inline_comments`). Jeśli link nie działa (strona przeniesiona lub usunięta), spróbuj `confluence_search`, zanim zapytasz użytkownika.
5. **Zestaw źródła.** Nowszy komentarz korygujący treść analizy ma pierwszeństwo przed nieaktualnym fragmentem dokumentu — oznacz w raporcie, że wymaganie pochodzi z komentarza. Jeśli źródła są sprzeczne, a żaden komentarz tego nie rozstrzyga, nie wybieraj wersji samodzielnie: oceń kod względem obu wariantów i wpisz sprzeczność do pytań do analityka.
6. **Rozpisz wymagania.** Każda reguła biznesowa (REG) i każde kryterium akceptacji dostaje identyfikator i źródło (analiza / komentarz / Jira). Jeśli w repozytorium istnieje plan `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` z macierzą wymagań i testów, użyj jego identyfikatorów zamiast tworzyć nowe.
7. **Zweryfikuj każde wymaganie w kodzie.** Dla każdego podaj:
   - status: **Spełnione** / **Częściowo** / **Brak** / **Niezgodne** (kod robi coś innego niż analiza) / **Nie do ustalenia** (analiza niejasna);
   - miejsce w kodzie (`plik:linia`), które je realizuje;
   - test, który je faktycznie weryfikuje (nie tylko wywołuje kod — sprawdza regułę), albo informację o braku testu.

   Sprawdzaj szczegóły, nie tylko istnienie funkcji: walidacje i ich warunki brzegowe, statusy i dozwolone przejścia, uprawnienia (kto może wykonać operację), wyliczenia i zaokrąglenia, kody i komunikaty błędów, zapisy do bazy (które tabele i pola), kontrakt backend–frontend (ścieżka, metoda, nazwy i typy pól, wymagalność, wartości enumów).
8. **Sprawdź w drugą stronę.** Zachowanie w kodzie, którego nie wymaga żadne wymaganie (dodatkowa walidacja, inny domyślny status, dodatkowe pole w odpowiedzi), to uwaga: albo wykracza poza zakres, albo analiza jest niekompletna — zapytaj, które z dwóch.
9. **Zakres zadania.** Jeśli zadanie obejmuje też frontend albo inne repozytoria, weryfikuj tylko część realizowaną w przeglądanej zmianie, a resztę wypisz jako „Poza zakresem przeglądu”. Nie oznaczaj jej jako „Brak”.

**Waga uwag biznesowych:**

| Sytuacja | Waga |
|---|---|
| Wymaganie niezrealizowane (`Brak`) albo kod działa inaczej niż analiza (`Niezgodne`) | **Critical** |
| Wymaganie zrealizowane częściowo albo bez testu weryfikującego regułę | Required (bez prefiksu) |
| Zachowanie spoza wymagań | Required — do wyjaśnienia z autorem lub analitykiem |
| Analiza niejasna lub sprzeczna | Pytanie do analityka, nie blokuje zmiany sam w sobie |

**Gdy nie ma analizy.** Jeśli użytkownik potwierdzi, że analizy nie ma albo prosi o przegląd bez niej — weryfikuj względem opisu i kryteriów akceptacji z Jiry i **jawnie zaznacz w raporcie**, że zgodność z analizą systemową nie została sprawdzona. Jeśli nie ma ani zadania w Jirze, ani analizy — pomiń ten krok, wykonaj przegląd techniczny i napisz w raporcie wprost, że weryfikacji biznesowej nie wykonano. Nie pisz raportu tak, żeby czytelnik mógł uznać, że zgodność biznesowa została sprawdzona.

### Step 3: Review the Tests First

Tests reveal intent and coverage:

```
- Do tests exist for the change?
- Do they test behavior (not implementation details)?
- Are edge cases covered?
- Do tests have descriptive names?
- Would the tests catch a regression if the code changed?
- Does every business requirement from Step 2 have a test that verifies the rule?
```

Answer the last-but-one question by experiment, not by reading. Invert one condition the change adds (drop a negation, swap `&&` for `||`), run the suite, then restore the file from a copy. A mutation that stays green is a finding: name the test case that is missing. Prefer mutating conditions that implement business rules from Step 2.

### Step 4: Review the Implementation

Walk through the code with the seven axes in mind:

```
For each file changed:
0. Business compliance: Which requirement from Step 2 does this implement, and does it match?
1. Correctness: Does this code do what the test says it should?
2. Readability: Can I understand this without help?
3. Architecture: Does this fit the system?
4. Security: Any vulnerabilities?
5. Performance: Any bottlenecks?
6. Project standards: Package-by-feature, jOOQ reads, JPA writes, MapStruct, no needless interfaces, Liquibase?
```

### Step 5: Categorize Findings

Label every comment with its severity so the author knows what's required vs optional:

| Prefix | Meaning | Author Action |
|--------|---------|---------------|
| *(no prefix)* | Required change | Must address before merge |
| **Critical:** | Blocks merge | Security vulnerability, data loss, broken functionality, missing or contradicting business requirement |
| **Nit:** | Minor, optional | Author may ignore — formatting, style preferences |
| **Optional:** / **Consider:** | Suggestion | Worth considering but not required |
| **FYI** | Informational only | No action needed — context for future reference |

This prevents authors from treating all feedback as mandatory and wasting time on optional suggestions.

**Lead with what matters.** Order findings by leverage: business compliance, correctness and security first, then structural regressions and missed simplifications, then everything else. Don't bury a real issue under cosmetic nits — a few high-conviction comments beat a long list. If you have one structural problem and ten nits, the structural problem *is* the review.

### Step 6: Verify the Verification

Check the author's verification story:

```
- What tests were run?
- Did the build pass?
- Was the change tested manually?
- Are there screenshots for UI changes?
- Is there a before/after comparison?
```

### Step 7: Write the Report

Zapisz raport HTML według sekcji „Output”. Checklista z „The Review Checklist” to treść raportu, nie osobny wynik w czacie.

## Output

**Format:** jeden samodzielny plik HTML, po polsku. Wynik przeglądu zawsze trafia do tego pliku; w czacie tylko krótkie podsumowanie (werdykt, liczba uwag Critical i Required, liczba wymagań spełnionych) i ścieżka do pliku.

**Lokalizacja:** `CODE_REVIEW/<nazwa-gałęzi>-java-code-review.html` w katalogu głównym przeglądanego repozytorium. Utwórz folder `CODE_REVIEW`, jeśli nie istnieje. W nazwie gałęzi zamień `/` na `-` (na przykład `feature/PROJ-123-x` → `CODE_REVIEW/feature-PROJ-123-x-java-code-review.html`). Sufiks `-java-code-review` chroni przed nadpisaniem raportu skilla `reviewing-java-commits`. Gdy przegląd nie dotyczy gałęzi (diff wklejony w czacie), użyj klucza zadania albo krótkiego opisu zamiast nazwy gałęzi. Jeśli plik już istnieje, przeczytaj go przed nadpisaniem i w sekcji „Testy i weryfikacja” odnotuj, które poprzednie uwagi zostały naprawione.

**Wygląd:** zacznij od szablonu `${CLAUDE_SKILL_DIR}/assets/template.html`. Ma gotowy `<head>`, style z tej samej serii co `explaining-confluence-analysis`, tryb ciemny i szkielet wszystkich sekcji:

1. **Podsumowanie** — liczniki (Critical, Required, wymagania spełnione, pytania) i werdykt Approve / Request changes z uzasadnieniem.
2. **Źródła** — zadanie Jira (i skąd ustalono klucz), analiza systemowa albo jawna informacja o jej braku, komentarze korygujące, zakres przeglądu.
3. **Zgodność biznesowa** — tabela wymagań z kroku 2 (ID, wymaganie, źródło, status, `plik:linia`, test), zachowanie spoza wymagań, poza zakresem przeglądu.
4. **Uwagi** — każda w osobnej karcie: waga, tytuł, `plik:linia`, oś, powiązane wymaganie, opis problemu, propozycja zmiany. Kolejność według wagi.
5. **Standardy projektu** — wynik dla każdego z sześciu standardów (OK / Naruszenie / Nie dotyczy).
6. **Testy i weryfikacja** — co sprawdzają testy, wyniki testów mutacyjnych, co uruchomiono.
7. **Pytania do analityka**.
8. **Checklista** — z „The Review Checklist”, z zaznaczonymi spełnionymi punktami.

Zasady:

- Bez JavaScriptu, cały CSS w `<style>`. Nie dodawaj kolorów spoza zmiennych z szablonu.
- Treść z Jiry, Confluence i kodu (fragmenty kodu, nazwy, komentarze) wstawiaj z escapowaniem HTML (`&lt;`, `&gt;`, `&amp;`, `&quot;`) — to dane z zewnątrz, a fragment kodu z `<` albo `&` rozbije stronę.
- Numery linii podawaj z rzeczywistego pliku, nie z diffu.
- Sekcji „Zgodność biznesowa” nigdy nie usuwaj. Jeśli weryfikacji nie wykonano albo wykonano ją tylko względem Jiry, napisz to w niej wprost, w „Źródłach” i w werdykcie.
- Usuń komentarze z podpowiedziami z szablonu.

## Multi-Model Review Pattern

Use different models for different review perspectives:

```
Model A writes the code
    │
    ▼
Model B reviews for correctness and architecture
    │
    ▼
Model A addresses the feedback
    │
    ▼
Human makes the final call
```

This catches issues that a single model might miss — different models have different blind spots.

**Example prompt for a review agent:**
```
Review this code change for correctness, security, and adherence to
our project conventions. The spec says [X]. The change should [Y].
Flag any issues as Critical, Required, Optional, or Nit.
```

## Dead Code Hygiene

After any refactoring or implementation change, check for orphaned code:

1. Identify code that is now unreachable or unused
2. List it explicitly
3. **Ask before deleting:** "Should I remove these now-unused elements: [list]?"

Don't leave dead code lying around — it confuses future readers and agents. But don't silently delete things you're not sure about. When in doubt, ask.

```
DEAD CODE IDENTIFIED:
- formatLegacyDate() in src/utils/date.ts — replaced by formatDate()
- OldTaskCard component in src/components/ — replaced by TaskCard
- LEGACY_API_URL constant in src/config.ts — no remaining references
→ Safe to remove these?
```

## Review Speed

Slow reviews block entire teams. The cost of context-switching to review is less than the waiting cost imposed on others.

- **Respond within one business day** — this is the maximum, not the target
- **Ideal cadence:** Respond shortly after a review request arrives, unless deep in focused coding. A typical change should complete multiple review rounds in a single day
- **Prioritize fast individual responses** over quick final approval. Quick feedback reduces frustration even if multiple rounds are needed
- **Large changes:** Ask the author to split them rather than reviewing one massive changeset

## Handling Disagreements

When resolving review disputes, apply this hierarchy:

1. **Technical facts and data** override opinions and preferences
2. **Style guides** are the absolute authority on style matters
3. **Software design** must be evaluated on engineering principles, not personal preference
4. **Codebase consistency** is acceptable if it doesn't degrade overall health

Disputes about *what the feature should do* are not resolved between author and reviewer — they go to the analyst, and the system analysis (or its correcting comment) decides.

**Don't accept "I'll clean it up later."** Experience shows deferred cleanup rarely happens. Require cleanup before submission unless it's a genuine emergency. If surrounding issues can't be addressed in this change, require filing a bug with self-assignment.

## Honesty in Review

When reviewing code — whether written by you, another agent, or a human:

- **Don't rubber-stamp.** "LGTM" without evidence of review helps no one.
- **Don't soften real issues.** "This might be a minor concern" when it's a bug that will hit production is dishonest.
- **Quantify problems when possible.** "This N+1 query will add ~50ms per item in the list" is better than "this could be slow."
- **Push back on approaches with clear problems.** Sycophancy is a failure mode in reviews. If the implementation has issues, say so directly and propose alternatives.
- **Accept override gracefully.** If the author has full context and disagrees, defer to their judgment. Comment on code, not people — reframe personal critiques to focus on the code itself.

## Dependency Discipline

Part of code review is dependency review:

**Before adding any dependency:**
1. Does the existing stack solve this? (Often it does.)
2. How large is the dependency? (Check bundle impact.)
3. Is it actively maintained? (Check last commit, open issues.)
4. Does it have known vulnerabilities? (`npm audit`)
5. What's the license? (Must be compatible with the project.)

**Rule:** Prefer standard library and existing utilities over new dependencies. Every dependency is a liability.

**Upgrading an existing dependency** is a code change like any other, and the riskiest upgrades are the ones merged in bulk with a message like "bump deps." Review them with the same discipline:

1. **Read the changelog, not just the version number.** Semver is a promise the maintainer may not have kept — a "patch" can carry a behavioral change. For a major bump, read the migration notes and find what breaks.
2. **One dependency per change.** Upgrade and merge them individually (or in small related groups). When a bulk bump breaks the build, you've lost which package did it; a single-package change makes the cause obvious and the revert clean.
3. **Let the tests decide.** The upgrade is verified by a green suite before *and* after, not by "it installed." If coverage around the dependency's behavior is thin, that gap is the real finding — add a test first.
4. **Mind the transitive graph.** Most installed packages are ones nobody chose directly. Review the lockfile diff, not just `package.json`; a single direct bump can pull in dozens of indirect changes.
5. **Keep the lockfile honest.** Commit it, review its diff, and never hand-edit it. The lockfile is the thing that actually pins what ships.

## The Review Checklist

```markdown
## Review: [PR/Change title]

### Context
- [ ] I understand what this change does and why

### Źródła
- Zadanie Jira: <link> (klucz ustalony z: użytkownik / gałąź / PR / commit)
- Analiza systemowa: <link> | brak — weryfikacja biznesowa wykonana tylko względem Jiry / nie wykonana
- Uwzględnione komentarze korygujące: <lista z autorem i datą>

### Zgodność biznesowa
| ID | Wymaganie | Źródło | Status | Kod | Test |
|----|-----------|--------|--------|-----|------|
| REG-1 | ... | analiza §3.2 | Spełnione / Częściowo / Brak / Niezgodne / Nie do ustalenia | `Plik.java:42` | `PlikTest#metoda` / brak |

- [ ] Every requirement implemented and matching the analysis
- [ ] No behavior outside the requirements (or explained)
- [ ] Every requirement covered by a test that verifies the rule
- Poza zakresem przeglądu: <...>
- Pytania do analityka: <...>

### Correctness
- [ ] Change matches spec/task requirements
- [ ] Edge cases handled
- [ ] Error paths handled
- [ ] Tests cover the change adequately

### Readability
- [ ] Names are clear and consistent
- [ ] Logic is straightforward
- [ ] No unnecessary complexity

### Architecture
- [ ] Follows existing patterns
- [ ] No unnecessary coupling or dependencies
- [ ] Appropriate abstraction level
- [ ] Refactors reduce complexity rather than relocate it
- [ ] No feature logic in shared modules; file stays within a healthy size

### Security
- [ ] No secrets in code
- [ ] Input validated at boundaries
- [ ] No injection vulnerabilities
- [ ] Auth checks in place
- [ ] External data sources treated as untrusted

### Performance
- [ ] No N+1 patterns
- [ ] No unbounded operations
- [ ] Pagination on list endpoints

### Project Standards
- [ ] Package by feature; `public` only for the package's real API
- [ ] Reads via jOOQ, no JPA entities returned as reports/projections
- [ ] Writes via JPA/Hibernate entities, no hand-written SQL or jOOQ DML
- [ ] Mapping via MapStruct `@Mapper(config = MapStructConfig.class)`
- [ ] No single-implementation interfaces (framework interfaces excepted)
- [ ] Liquibase: numbering, header, idempotent data changes, included in the master changelog

### Verification
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Manual verification done (if applicable)

### Verdict
- [ ] **Approve** — Ready to merge
- [ ] **Request changes** — Issues must be addressed
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works, that's good enough" | Working code that's unreadable, insecure, or architecturally wrong creates debt that compounds. |
| "The code is clean, so the feature is done" | Clean code that implements the wrong rule is a wrong feature. Check it against the analysis. |
| "The PR description says it implements PROJ-123" | The description is the author's claim, not evidence. Verify each requirement against the code. |
| "I wrote it, so I know it's correct" | Authors are blind to their own assumptions. Every change benefits from another set of eyes. |
| "We'll clean it up later" | Later never comes. The review is the quality gate — use it. Require cleanup before merge, not after. |
| "AI-generated code is probably fine" | AI code needs more scrutiny, not less. It's confident and plausible, even when wrong. |
| "The tests pass, so it's good" | Tests are necessary but not sufficient. They don't catch architecture problems, security issues, readability concerns, or a misread requirement the tests encode too. |
| "The refactor makes it cleaner" | Relocating complexity isn't reducing it. If the reader still holds the same number of concepts, the structure didn't improve — look for the version where branches disappear. |
| "It's only a small addition to this file" | Small diffs still push files past a healthy size and bolt branches onto unrelated flows. Judge the resulting structure, not the diff size. |
| "It's just a version bump" | A bump is a behavior change you didn't write. Read the changelog; semver doesn't guarantee no breakage. |
| "I'll upgrade everything in one PR to save time" | A bulk bump that breaks the build hides which package did it. One dependency per change keeps the cause and the revert clean. |

## Red Flags

- PRs merged without any review
- Review that only checks if tests pass (ignoring other axes)
- Review that never opened the Jira ticket or the analysis, yet implies the feature is complete
- "LGTM" without evidence of actual review
- Security-sensitive changes without security-focused review
- Large PRs that are "too big to review properly" (split them)
- No regression tests with bug fix PRs
- Review comments without severity labels — makes it unclear what's required vs optional
- Accepting "I'll fix it later" — it never happens
- A refactor that moves code around without reducing the number of concepts a reader must hold
- A change that grows an already-large file instead of decomposing it
- New conditionals scattered into unrelated code paths (a missing abstraction)
- A bespoke helper that duplicates an existing canonical one, or feature logic placed in a shared module
- A bulk "bump dependencies" PR with no changelog review and no per-package isolation
- A lockfile change that's hand-edited, uncommitted, or merged without reviewing its diff
- A new Liquibase changeset in a directory that needs an explicit `include:` entry, without that entry — it never runs, silently

## Verification

After review is complete:

- [ ] All Critical issues are resolved
- [ ] All Required (no-prefix) changes are resolved or explicitly deferred with justification
- [ ] Every business requirement is `Spełnione`, or its gap is a resolved finding or an open question to the analyst
- [ ] Tests pass
- [ ] Build succeeds
- [ ] The verification story is documented (what changed, how it was verified)
- [ ] The HTML report is written to `CODE_REVIEW/<nazwa-gałęzi>-java-code-review.html`
- [ ] Dependency upgrades were reviewed against their changelog, isolated per package, and verified by a green suite with the lockfile diff reviewed

**Presumptive blockers:** surface and propose the simpler design for each of these; escalate to Required only when the change actively makes structure worse: a refactor that relocates complexity instead of reducing it; a change that pushes a file past the size boundary with no decomposition; feature logic added to a shared module; a near-duplicate of an existing canonical helper; a silent fallback that hides an unclear invariant.
