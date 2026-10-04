---
name: running-task-retro
description: Use when asked for a retrospective of a finished (or almost finished) Jira task — "retro", "retrospektywa zadania", "co poszło nie tak w PROJ-123", "czego plan nie przewidział". Takes the task key and compares the implementation plan with what actually happened — the final diff in every repository (what was added outside the plan, which planned steps were skipped), the code review reports (what review caught that the plan did not foresee), the questions asked during planning and implementation, and the smoke test report. Writes a Polish-language report to `RETRO/<KLUCZ>.md` and proposes concrete changes to the skills of the java-backend plugin as a ready-to-apply patch, without applying it — skills are installed from the marketplace, so every change must go through a commit in the skills repository.
disable-model-invocation: true
argument-hint: "[KLUCZ-ZADANIA]"
---

# Running Task Retro

## Overview

Closes the loop on one Jira task. The other skills of this plugin leave artifacts behind: a feasibility report with questions for the analyst, an implementation plan with a requirements-to-tests matrix and the questions resolved during planning, code review reports, a smoke test report. This skill reads them together with the final code, finds where the plan and reality diverged, and turns every recurring divergence into a concrete proposal: a change in the skill that should have prevented it.

The output is `RETRO/<KLUCZ-ZADANIA>.md` plus `RETRO/<KLUCZ-ZADANIA>-skille.patch`. The skill is read-only with respect to code and skills: it never applies the patch.

## When to Use

- User asks for a retrospective of a task, usually after merging the pull requests or after the last review round.
- The task key is given as an argument or can be read from the current branch name. If neither works, ask for the key.
- Not for: team or sprint retrospectives (this is about one task and the tooling), code review (`/java-backend:reviewing-java-commits`), rewriting the plan after the fact.

## Źródła

Zbierz wszystko, co istnieje — brak pojedynczego źródła nie blokuje retrospektywy, ale musi być odnotowany w raporcie.

| Źródło | Gdzie | Co z niego bierzesz |
|---|---|---|
| Plan implementacji | `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md` w repozytorium wiodącym (sprawdź też repozytoria sąsiednie) | Kroki, macierz wymagań i testów, „Rozstrzygnięte pytania”, „Otwarte pytania do analityka”, „Poza zakresem” |
| Lokalna kopia analizy | `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md` | Treść wymagań do porównania; jeżeli analiza w Confluence zmieniła się od pobrania kopii, to osobne ustalenie |
| Analiza wykonalności | `ANALIZA_WYKONALNOSCI/<KLUCZ>.md` albo plik nazwany tytułem strony | Pytania do analityka i to, czy dostały odpowiedź |
| Finalny kod | gałąź zadania w każdym repozytorium (albo commit scalenia, jeżeli pull request jest już scalony) | Diff względem punktu rozejścia z gałęzią bazową |
| Raporty code review | `CODE_REVIEW/<gałąź>.md` w każdym repozytorium | Uwagi, ich kategorie (checklisty A, B, C), sekcja „Weryfikacja poprzednich uwag”, pokrycie macierzy testami |
| Komentarze w pull requestach | Bitbucket (MCP, REST albo CLI — jak w skillu review) | Uwagi recenzentów-ludzi, których nie było w raportach |
| Smoke test | `SMOKE_TEST/<KLUCZ>.md` | Niezgodności żądań, pozycje „do oceny przez programistę”, repozytoria „zaplanowane, ale niezmienione” |
| Zadanie Jira i strona Confluence | MCP, REST albo CLI | Komentarze dodane po zapisaniu planu (zmiany wymagań w trakcie) |
| Bieżące skille | `${CLAUDE_SKILL_DIR}/../<skill>/SKILL.md` | Aktualna treść skilli, do której odnoszą się propozycje zmian |

Dostęp do Jiry, Confluence i Bitbucketa ustalaj tak samo jak w pozostałych skillach pluginu: najpierw narzędzia MCP, potem CLI, potem REST API z tokenem ze zmiennych środowiskowych. Nie wypisuj tokenów.

## Process

1. **Ustal klucz zadania** i znajdź repozytoria, w których jest gałąź z tym kluczem (`git -C <repo> branch -a --list "*<KLUCZ>*"`). Jeżeli gałęzi już nie ma (usunięta po scaleniu), znajdź commity zadania w gałęzi bazowej po kluczu w komunikatach (`git -C <repo> log --oneline --grep=<KLUCZ> <bazowa>`).
2. **Zbierz źródła** z tabeli powyżej. Dla każdego zapisz, czy zostało znalezione.
3. **Plan a kod.** Dla każdego kroku planu ustal, czy został zrealizowany: znajdź odpowiadające mu zmiany w diffie (repozytorium, pliki, klasy). Następnie przejdź diff w drugą stronę i wypisz zmiany, które nie należą do żadnego kroku planu. Każdą rozbieżność zaklasyfikuj:
   - **zmiana spoza planu, wymuszona** — bez niej zadanie nie działało (brakujący krok, nieprzewidziana migracja, poprawka w innym repozytorium);
   - **zmiana spoza planu, z review** — dodana w odpowiedzi na uwagę z raportu review albo z komentarza w pull requeście;
   - **zmiana wymagań** — wynika z komentarza analityka lub zmiany analizy po zapisaniu planu;
   - **krok pominięty** — zaplanowany, a niezrealizowany; ustal z komentarzy, commitów albo rozstrzygniętych pytań, czy świadomie;
   - **szum** — formatowanie, porządki, zmiany niezwiązane z zadaniem (wypisz zbiorczo, nie analizuj).
4. **Macierz a testy.** Dla każdego wiersza macierzy wymagań i testów sprawdź, czy w finalnym kodzie jest zaplanowany test (albo inny, który weryfikuje tę regułę). Wypisz też testy dodane w trakcie review i reguły, które pojawiły się w trakcie (nowy wiersz, którego nie było w planie). Weź pod uwagę tabelę „Pokrycie macierzy testami” z ostatniego raportu review — nie powtarzaj jej, odwołaj się do niej.
5. **Review a plan.** Dla każdej uwagi z raportów review i z komentarzy w pull requestach ustal, czy plan albo wcześniejszy etap mógł jej zapobiec:
   - uwaga z checklisty C (niezgodność z analizą) → czy wymaganie było w planie i w macierzy;
   - uwaga z checklisty A (standardy projektu) → czy plan wskazywał miejsce w kodzie i konwencję;
   - uwaga z checklisty B (jakość, bezpieczeństwo) → czy to błąd implementacji, czy luka w planie (na przykład brak kroku autoryzacji);
   - uwaga, która wróciła jako „nienaprawiona” albo „naprawiona częściowo” w trybie przyrostowym → osobno, bo to koszt kolejnej rundy.
6. **Pytania.** Zestaw wszystkie pytania: z raportu wykonalności, „Rozstrzygnięte pytania” i „Otwarte pytania do analityka” z planu, pytania z review („Pytania i luki w analizie”). Ustal dla każdego: kiedy zostało zadane (wykonalność, planowanie, implementacja, review), czy mogło zostać zadane wcześniej (na przykład pytanie zadane dopiero w review, a sformułowanie analizy było niejasne już w momencie planowania), czy dostało odpowiedź i od kogo.
7. **Smoke test.** Jeżeli raport istnieje, wypisz niezgodności żądań, endpointy pominięte albo bez oczekiwanego wyniku i repozytoria „zaplanowane, ale niezmienione”, i powiąż je z krokami planu.
8. **Wnioski.** Z ustaleń z kroków 3–7 wybierz te, które mają wspólną przyczynę leżącą w procesie, a nie w jednorazowym błędzie. Dla każdego wniosku wskaż etap i skill, który powinien był to wychwycić. Jednorazowe pomyłki implementacyjne wypisz, ale nie twórz z nich propozycji zmian w skillach.
9. **Propozycje zmian w skillach.** Dla każdego wniosku z kroku 8, który da się przełożyć na instrukcję, przeczytaj aktualną treść odpowiedniego skilla (`${CLAUDE_SKILL_DIR}/../<skill>/SKILL.md`) i przygotuj konkretną zmianę: nowy punkt w „Częstych błędach”, nowy wiersz w tabeli „Kiedy zapytać”, nowa pozycja checklisty, doprecyzowanie kroku procesu. Zmiana ma być w stylu i języku zmienianej sekcji, minimalna i uzasadniona przypadkiem z tego zadania. Zapisz wszystkie zmiany jako jeden plik w formacie unified diff, ze ścieżkami względnymi od katalogu głównego repozytorium skilli (`plugins/java-backend/skills/<skill>/SKILL.md`), żeby dało się go nałożyć przez `git apply` w tym repozytorium. Sprawdź, czy kontekst każdego hunka dokładnie odpowiada aktualnej treści pliku.
10. **Zapisz raport** `RETRO/<KLUCZ>.md` i łatkę `RETRO/<KLUCZ>-skille.patch` w katalogu głównym repozytorium wiodącego (tam, gdzie leży plan; jeżeli planu nie ma — w bieżącym repozytorium). Dopisz `RETRO/` do `.gitignore`, jeżeli go tam nie ma.
11. **Zgłoś się w czacie:** ścieżka raportu, liczba rozbieżności według klas z kroku 3, liczba propozycji zmian i dla każdej jedno zdanie, którego skilla dotyczy i co zmienia. Podaj komendę do nałożenia łatki: `git -C <repozytorium-skilli> apply --check <ścieżka-łatki> && git -C <repozytorium-skilli> apply <ścieżka-łatki>`. Nie nakładaj jej sam.

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Nie ma planu implementacji | Nie pytaj — zrób retrospektywę z tego, co jest (kod, review, pytania), i zaznacz w raporcie, że porównania z planem nie było. |
| Nie ma żadnego raportu review ani komentarzy w pull requestach | Nie pytaj — zaznacz w raporcie. |
| Nie wiadomo, czy pominięty krok został pominięty świadomie | Zapytaj, z cytatem kroku i hipotezą (na przykład „przeniesiony do osobnego zadania”). Zbierz takie pytania w jedno. |
| Zmiana spoza planu nie ma oczywistej przyczyny w commitach, review ani komentarzach | Zapytaj zbiorczo, razem z pytaniami o pominięte kroki. |
| Programista prosi o nałożenie łatki na skille | Odmów nałożenia w ramach tego skilla — podaj komendę i wyjaśnij, że zmiana idzie przez commit w repozytorium skilli. Jeżeli programista pracuje właśnie w repozytorium skilli i wprost tego chce poza retrospektywą, to zwykła edycja, nie część tego skilla. |
| Wniosek dotyczy procesu zespołu, a nie skilla (na przykład analityk odpowiada za późno) | Nie twórz łatki — wpisz go w raporcie w sekcji „Wnioski poza skillami”. |

## Output

**Język:** polski, zwykłym językiem, bez skrótowców. Bez ocen ludzi — opisuj, co się stało i który etap mógł to złapać.

**Lokalizacja:** `RETRO/<KLUCZ-ZADANIA>.md` i `RETRO/<KLUCZ-ZADANIA>-skille.patch` w katalogu głównym repozytorium wiodącego.

**Szablon raportu:**

```markdown
# Retrospektywa – <KLUCZ-ZADANIA>: <tytuł zadania>

Data: <data>
Repozytoria: <nazwa (gałąź, zakres commitów)>, ...
Źródła: plan — <jest/brak>; analiza wykonalności — <jest/brak>; raporty review — <liczba, rundy>; komentarze w pull requestach — <sprawdzone/niedostępne>; smoke test — <jest/brak>

## Liczby

| Miara | Wartość |
|---|---|
| Kroki planu zrealizowane / pominięte | <N> / <M> |
| Zmiany spoza planu (wymuszone / z review / zmiana wymagań) | <a> / <b> / <c> |
| Wiersze macierzy pokryte testem / bez testu / dodane w trakcie | <x> / <y> / <z> |
| Rundy review | <N> |
| Pytania zadane w: wykonalności / planowaniu / implementacji / review | <a> / <b> / <c> / <d> |

## Plan a kod

### Zmiany spoza planu

| Zmiana | Repozytorium i plik | Klasa | Przyczyna | Kto mógł to przewidzieć |
|---|---|---|---|---|
| <opis> | <repo>: `<ścieżka>` | wymuszona | <commit, uwaga review, komentarz> | <etap / skill> |

### Kroki pominięte

<krok, przyczyna, czy świadomie — albo „brak”>

## Macierz a testy

<wiersze bez testu, testy dodane w review, nowe reguły dodane w trakcie — z odnośnikiem do tabeli pokrycia w ostatnim raporcie review>

## Review a plan

| Uwaga | Raport i numer | Checklista | Czy plan mógł jej zapobiec | Jak |
|---|---|---|---|---|

## Pytania

| Pytanie | Zadane na etapie | Mogło być zadane na etapie | Odpowiedź (kto) |
|---|---|---|---|

## Smoke test

<niezgodności, endpointy pominięte lub bez oczekiwania, repozytoria zaplanowane, ale niezmienione — albo „brak raportu”>

## Wnioski

### 1. <krótki tytuł wniosku>

- **Co się stało:** <fakty z tego zadania, z odnośnikami>
- **Etap, który mógł to złapać:** <wykonalność / planowanie / implementacja / review / smoke test>
- **Propozycja:** <jednozdaniowy opis zmiany w skillu, numer hunka w łatce — albo „poza skillami”>

## Wnioski poza skillami

<wnioski dotyczące procesu zespołu, nie instrukcji skilli — albo „brak”>

## Pomyłki jednorazowe

<krótka lista, bez propozycji zmian>
```

## Częste błędy

- Opisanie przebiegu zadania zamiast porównania planu z rzeczywistością — każda pozycja ma wskazywać rozbieżność i jej przyczynę.
- Propozycja zmiany w skillu ogólnikowa („dokładniej analizować model danych”) zamiast konkretnej instrukcji w konkretnym miejscu pliku.
- Propozycja zmiany z jednorazowej pomyłki, która nie powtórzy się w kolejnych zadaniach.
- Nałożenie łatki na skille albo edycja zainstalowanej kopii skilla w katalogu pluginów — zmiana musi przejść przez commit w repozytorium skilli.
- Łatka ze ścieżkami, które nie pasują do repozytorium skilli, albo z kontekstem, który nie zgadza się z aktualną treścią pliku — `git apply --check` musi przejść.
- Liczenie formatowania i porządków jako zmian spoza planu.
- Powtórzenie całej tabeli pokrycia macierzy z raportu review zamiast odwołania do niej i opisania tylko różnic.
- Pominięcie komentarzy w pull requestach — uwagi recenzentów-ludzi często nie trafiają do raportów review.
- Ocena osób zamiast opisu etapu procesu, który mógł problem wychwycić.
