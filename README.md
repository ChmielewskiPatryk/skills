# skills — marketplace skilli do Claude Code

To repozytorium to **marketplace pluginów Claude Code**. Każdy plugin to paczka skilli. Claude Code klonuje repo przez Gita — repo jest publiczne, więc instalacja nie wymaga żadnej dodatkowej konfiguracji dostępu.

- Nazwa marketplace: `chmielewski-skills`
- Repo: `ChmielewskiPatryk/skills`

## Spis treści

1. [Struktura repo](#1-struktura-repo)
2. [Wymagania](#2-wymagania)
3. [Instalacja skilli](#3-instalacja-skilli)
4. [Używanie skilli](#4-używanie-skilli)
5. [Aktualizacje](#5-aktualizacje)
6. [Zarządzanie pluginami](#6-zarządzanie-pluginami)
7. [Dodawanie nowego skilla](#7-dodawanie-nowego-skilla)
8. [Dodawanie nowego pluginu](#8-dodawanie-nowego-pluginu)
9. [Wersjonowanie](#9-wersjonowanie)
10. [Włączanie pluginów dla konkretnego projektu](#10-włączanie-pluginów-dla-konkretnego-projektu)
11. [Rozwiązywanie problemów](#11-rozwiązywanie-problemów)
12. [Ściągawka komend](#12-ściągawka-komend)

---

## 1. Struktura repo

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # katalog: lista pluginów w tym repo
└── plugins/
    ├── claude-setup/             # plugin = grupa skilli
    │   ├── .claude-plugin/
    │   │   └── plugin.json       # metadane pluginu
    │   └── skills/
    │       └── context-statusline/
    │           └── SKILL.md      # pojedynczy skill
    └── java-backend/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            ├── analyzing-confluence-feasibility/
            │   └── SKILL.md
            ├── planning-jira-implementation/
            │   └── SKILL.md
            ├── reviewing-java-commits/
            │   └── SKILL.md
            ├── smoke-testing-locally/
            │   └── SKILL.md
            └── running-task-retro/
                └── SKILL.md
```

Pojęcia:

| Pojęcie | Co to jest | Gdzie |
| --- | --- | --- |
| **Marketplace** | Katalog pluginów. Dodajesz go raz. | `.claude-plugin/marketplace.json` |
| **Plugin** | Jednostka instalacji. Zawiera jeden lub więcej skilli. | `plugins/<plugin>/` |
| **Skill** | Instrukcja dla Claude'a, wywoływana jako `/<plugin>:<skill>`. | `plugins/<plugin>/skills/<skill>/SKILL.md` |

Aktualne pluginy:

| Plugin | Skille | Opis |
| --- | --- | --- |
| `claude-setup` | `/claude-setup:context-statusline` | Konfiguruje `ccstatusline`, żeby status line pokazywał zużycie kontekstu |
| `java-backend` | `/java-backend:planning-jira-implementation` | Tworzy plan implementacji backendu z zadania Jira i powiązanej analizy systemowej w Confluence → `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ>.md`. Wymaga dostępu do Jiry i Confluence (dowolny serwer MCP, CLI albo REST API z tokenem). Zapisuje też lokalną kopię analizy w `IMPLEMENTATION_PLAN/.analiza/` i zadaje pytania z cytatem oraz odnośnikiem do konkretnego fragmentu. Plan zawiera macierz wymagań i testów: każda reguła REG i każde kryterium akceptacji ma identyfikator, źródło i test pisany przed kodem. |
| | `/java-backend:reviewing-java-commits` | Code review pull requesta Java z Bitbucketa (standardy projektu + jakość kodu + zgodność z analizą systemową z Confluence), raport po polsku → `CODE_REVIEW/<gałąź>.md`. Przyjmuje dwa linki: pull request i analizę; bez linku do analizy przegląd nadal się wykonuje, ale raport to odnotowuje. Sprawdza też autoryzację i pokrycie macierzy testami z planu. Gdy raport dla gałęzi już istnieje, działa przyrostowo: przegląda tylko nowe commity i weryfikuje, czy poprzednie uwagi zostały naprawione. |
| | `/java-backend:analyzing-confluence-feasibility` | Analiza wykonalności rozwiązania opisanego na stronie Confluence — zgodność z modelem bazy danych, spójność kontraktu backend–frontend, wykonalność logiki biznesowej. Raport po polsku: trzy sekcje analizy i sekcja „Pytania do analityka” z blokiem gotowym do wklejenia jako komentarz w Jirze lub Confluence → `ANALIZA_WYKONALNOSCI/<tytuł-strony>.md`. Nie tworzy planu implementacji. |
| | `/java-backend:smoke-testing-locally` | Lokalny smoke test zadania: ustala, które projekty zmodyfikowano w zadaniu, publikuje zmienione biblioteki do Maven Local, stawia bazę w Dockerze od zera (po potwierdzeniu), uruchamia usługi przez Gradle, sam wyznacza nowe i zmienione endpointy i wywołuje je `curl`-em (ścieżka szczęśliwa i przypadki negatywne z analizy) → `SMOKE_TEST/<KLUCZ>.md` oraz skrypt żądań do ponownego uruchomienia. Konfigurację środowiska zapamiętuje w `SMOKE_TEST/srodowisko.md`. Tylko ręczne wywołanie. |
| | `/java-backend:running-task-retro` | Retrospektywa zadania: porównuje plan z finalnym kodem, raportami review, pytaniami i smoke testem → `RETRO/<KLUCZ>.md` oraz propozycje zmian w skillach jako łatka `RETRO/<KLUCZ>-skille.patch` do nałożenia w tym repo. Niczego nie zmienia sam. Tylko ręczne wywołanie. |

---

## 2. Wymagania

- **Claude Code** — w miarę aktualna wersja (sprawdź: `claude --version`, aktualizacja: `claude update`).
- **Git** w `PATH` (Claude Code klonuje repo gitem).

---

## 3. Instalacja skilli

### Krok 1: dodaj marketplace (raz na maszynę)

W sesji Claude Code:

```
/plugin marketplace add ChmielewskiPatryk/skills
```

albo z terminala:

```bash
claude plugin marketplace add ChmielewskiPatryk/skills
```

To tylko rejestruje katalog — nic jeszcze nie jest zainstalowane.

### Krok 2: zainstaluj plugin

**Interaktywnie** — w sesji Claude Code:

```
/plugin
```

Przejdź do zakładki **Discover** (Tab przełącza zakładki), wybierz plugin z `chmielewski-skills`, naciśnij Enter i wybierz zakres instalacji.

**Komendą w sesji:**

```
/plugin install claude-setup@chmielewski-skills
```

**Z terminala (bez interakcji):**

```bash
claude plugin install claude-setup@chmielewski-skills                  # zakres user (domyślny)
claude plugin install claude-setup@chmielewski-skills --scope project  # dla projektu (commitowane)
claude plugin install claude-setup@chmielewski-skills --scope local    # dla projektu, tylko dla mnie
```

Zakresy instalacji:

| Zakres | Gdzie działa | Plik ustawień |
| --- | --- | --- |
| `user` | We wszystkich projektach na tej maszynie | `~/.claude/settings.json` |
| `project` | W tym repo, dla każdego kto je sklonuje | `.claude/settings.json` |
| `local` | W tym repo, tylko dla ciebie (gitignored) | `.claude/settings.local.json` |

### Krok 3: aktywuj

- Instalacja przez `/plugin` zwykle aktywuje plugin od razu. Jeśli zobaczysz `Run /reload-plugins to activate.` — wpisz `/reload-plugins` (albo `/reload-plugins --force`, jeśli pojawi się ostrzeżenie o cache).
- Instalacja przez `claude plugin install` w terminalu działa od **następnej sesji** albo po `/reload-plugins` w otwartej sesji.

### Krok 4: sprawdź

```
/plugin list
```

Wpisz `/claude-setup:` — autouzupełnianie powinno pokazać skille z pluginu.

---

## 4. Używanie skilli

Skille z pluginów mają przedrostek nazwy pluginu:

```
/claude-setup:context-statusline
```

Można dopisać argumenty po nazwie: `/plugin:skill argument1 argument2`.

Skille **bez** `disable-model-invocation: true` w nagłówku Claude może też uruchomić sam, kiedy uzna, że pasują do prośby (na podstawie pola `description`). Skille z `disable-model-invocation: true` uruchamiasz tylko ręcznie.

---

## 5. Aktualizacje

Po wypchnięciu zmian do repo (`git push`) trzeba je pobrać na maszynach, gdzie plugin jest zainstalowany.

### Ręcznie

W sesji Claude Code:

```
/plugin marketplace update chmielewski-skills
/reload-plugins
```

albo z terminala:

```bash
claude plugin marketplace update chmielewski-skills
claude plugin update claude-setup@chmielewski-skills
```

### Automatycznie (zalecane)

Auto-update jest **domyślnie wyłączony**. Włącz go raz na maszynę:

1. `/plugin`
2. Zakładka **Marketplaces**
3. Wybierz `chmielewski-skills`
4. **Enable auto-update**

Claude Code sprawdza aktualizacje w tle po starcie sesji (z losowym opóźnieniem do ~10 min). Gdy coś się zaktualizuje, zobaczysz prośbę o `/reload-plugins` — albo nowa wersja załaduje się przy następnym uruchomieniu.

---

## 6. Zarządzanie pluginami

Najprościej: `/plugin` → zakładka **Installed** → Enter na pluginie → enable / disable / uninstall.

Komendy:

```
/plugin list                                         # lista zainstalowanych
/plugin disable claude-setup@chmielewski-skills      # wyłącz bez odinstalowania
/plugin enable claude-setup@chmielewski-skills       # włącz ponownie
/plugin uninstall claude-setup@chmielewski-skills    # odinstaluj
/plugin marketplace list                             # lista marketplace'ów
/plugin marketplace remove chmielewski-skills        # usuń marketplace
```

> ⚠️ Usunięcie marketplace **odinstalowuje wszystkie pluginy** z niego zainstalowane.

Te same operacje z terminala: `claude plugin list | enable | disable | uninstall | update`, `claude plugin marketplace list | update | remove`.

---

## 7. Dodawanie nowego skilla

Przykład: skill `commit-message` w istniejącym pluginie `claude-setup`.

### 1. Utwórz katalog i `SKILL.md`

```
plugins/claude-setup/skills/commit-message/SKILL.md
```

```markdown
---
name: commit-message
description: Pisze komunikat commita na podstawie zmian w stage. Użyj, gdy użytkownik prosi o commit message.
---

# Komunikat commita

1. Uruchom `git diff --cached`.
2. Napisz komunikat w formacie Conventional Commits...
```

Zasady:

- `SKILL.md` musi leżeć **bezpośrednio** w katalogu skilla, a nagłówek `---` musi zaczynać się w **pierwszej linii**.
- `name` — kebab-case, zgodny z nazwą katalogu. To część komendy: `/claude-setup:commit-message`.
- `description` — kiedy skill ma być użyty. Claude widzi opis zawsze, pełną treść dopiero po uruchomieniu skilla. Limit: 1536 znaków.
- Treść `SKILL.md` najlepiej poniżej ~500 linii. Dłuższe materiały przenieś do osobnych plików obok (np. `reference.md`) i odwołaj się do nich z `SKILL.md`.
- Skrypty trzymaj w katalogu skilla (np. `scripts/`) i odwołuj się przez `${CLAUDE_SKILL_DIR}/scripts/nazwa.sh`.

Przydatne pola nagłówka:

| Pole | Działanie |
| --- | --- |
| `disable-model-invocation: true` | Tylko ręczne wywołanie (`/plugin:skill`), Claude nie uruchomi sam |
| `user-invocable: false` | Ukryte w menu `/`, tylko Claude może użyć |
| `argument-hint: "[plik]"` | Podpowiedź argumentów w autouzupełnianiu |
| `allowed-tools: Bash(git diff *) Read` | Narzędzia dozwolone bez pytania w trakcie skilla |
| `model`, `effort` | Wymuszenie modelu / poziomu effort |
| `context: fork` | Uruchom skill w osobnym subagencie |

Pełna lista: https://code.claude.com/docs/en/skills

### 2. Przetestuj lokalnie (bez pushowania)

Z katalogu repo:

```bash
claude plugin validate ./plugins/claude-setup
claude --plugin-dir ./plugins/claude-setup
```

`--plugin-dir` ładuje plugin prosto z dysku na czas sesji. Zmiany w skillach działają od razu, bez reinstalacji. Wywołaj `/claude-setup:commit-message` i sprawdź działanie.

> Jeśli masz ten sam plugin zainstalowany z marketplace, na czas testów wyłącz go (`/plugin disable claude-setup@chmielewski-skills`), żeby nie mieszać wersji.

### 3. Zatwierdź i wypchnij

```bash
claude plugin validate .
git add plugins/claude-setup/skills/commit-message
git commit -m "Add commit-message skill"
git push
```

### 4. Pobierz na maszynach

Patrz [Aktualizacje](#5-aktualizacje). Nowy skill w już zainstalowanym pluginie pojawi się po aktualizacji — nie trzeba nic doinstalowywać.

---

## 8. Dodawanie nowego pluginu

Nowy plugin warto zrobić, gdy skille tworzą osobną grupę, którą chcesz instalować / wyłączać niezależnie (np. `frontend`, `git-tools`).

### 1. Struktura

```
plugins/git-tools/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── commit-message/
        └── SKILL.md
```

### 2. `plugins/git-tools/.claude-plugin/plugin.json`

```json
{
  "name": "git-tools",
  "description": "Skille do pracy z gitem",
  "author": {
    "name": "Patryk Chmielewski"
  }
}
```

`name` musi być w kebab-case — to przedrostek komend (`/git-tools:commit-message`), więc warto, żeby był krótki.

### 3. Dopisz plugin do `.claude-plugin/marketplace.json`

```json
{
  "name": "chmielewski-skills",
  "owner": { "name": "Patryk Chmielewski" },
  "plugins": [
    {
      "name": "claude-setup",
      "source": "./plugins/claude-setup",
      "description": "Skille do konfiguracji samego Claude Code (status line itp.)"
    },
    {
      "name": "git-tools",
      "source": "./plugins/git-tools",
      "description": "Skille do pracy z gitem"
    }
  ]
}
```

- `name` w marketplace powinien być taki sam jak w `plugin.json`.
- `source` — ścieżka względna od katalogu głównego repo, zaczynająca się od `./`, z `/` (także na Windows), bez `../`.
- Plugin jest kopiowany do cache — pliki spoza jego katalogu (np. `../shared`) **nie trafią** do instalacji.

### 4. Walidacja, commit, push, instalacja

```bash
claude plugin validate .
claude plugin validate ./plugins/git-tools
git add . && git commit -m "Add git-tools plugin" && git push
```

Na maszynie docelowej:

```
/plugin marketplace update chmielewski-skills
/plugin install git-tools@chmielewski-skills
```

---

## 9. Wersjonowanie

Claude Code ustala wersję pluginu w tej kolejności:

1. `version` w `plugin.json`
2. `version` we wpisie w `marketplace.json`
3. **SHA commita** (jeśli nie ma żadnego pola `version`)

**Obecnie pluginy nie mają pola `version`** — więc każdy commit to nowa wersja i aktualizacje przychodzą same po `git push`. To najwygodniejsze rozwiązanie.

Dlatego `claude plugin validate` pokazuje ostrzeżenie `No version specified` — to celowe i można je zignorować (nie używaj `--strict`, bo zamieni je w błąd).

Jeśli kiedyś dodasz `"version": "1.0.0"` do `plugin.json`:

- ⚠️ **Każda zmiana wymaga podbicia wersji**, inaczej zainstalowane kopie się nie zaktualizują.
- Pole `version` w `plugin.json` ma pierwszeństwo przed wersją w `marketplace.json`.

---

## 10. Włączanie pluginów dla konkretnego projektu

Żeby projekt sam proponował ten marketplace i pluginy (np. po sklonowaniu na nowej maszynie), dodaj do `.claude/settings.json` **w tamtym projekcie**:

```json
{
  "extraKnownMarketplaces": {
    "chmielewski-skills": {
      "source": {
        "source": "github",
        "repo": "ChmielewskiPatryk/skills"
      }
    }
  },
  "enabledPlugins": {
    "claude-setup@chmielewski-skills": true
  }
}
```

Po zaufaniu folderowi projektu Claude Code doda marketplace automatycznie. Jeśli zgłosi plugin jako niezainstalowany, uruchom podaną komendę, np.:

```bash
claude plugin install claude-setup@chmielewski-skills --scope project
```

---

## 11. Rozwiązywanie problemów

| Problem | Rozwiązanie |
| --- | --- |
| Ręczna aktualizacja działa, automatyczna nie | Sprawdź, czy auto-update jest włączony ([krok 5](#5-aktualizacje)). |
| Plugin się nie ładuje | `claude plugin validate .` i `claude plugin validate ./plugins/<plugin>` — pokażą błędy JSON / ścieżek. Szczegóły w `/plugin` → zakładka **Errors**. |
| Skill nie pojawia się po aktualizacji | `/plugin marketplace update chmielewski-skills`, potem `/reload-plugins`. Sprawdź, czy `SKILL.md` ma nagłówek `---` w 1. linii i pole `name`. |
| Nadal nie widać zmian | Wyczyść cache i zainstaluj ponownie: usuń `~/.claude/plugins/cache` (Windows: `%USERPROFILE%\.claude\plugins\cache`), zrestartuj Claude Code, zainstaluj plugin od nowa. |
| Zmiany nie przychodzą mimo pusha | Jeśli dodałeś `version` w `plugin.json` — podbij ją ([krok 9](#9-wersjonowanie)). |
| `/plugin` nie istnieje | Zaktualizuj Claude Code (`claude update`) i uruchom ponownie. |
| Potrzebujesz szczegółowych logów | `claude --debug` (albo `claude --debug --plugin-dir ./plugins/<plugin>` przy testach lokalnych). |

---

## 12. Ściągawka komend

```bash
# --- Nowa maszyna ---
claude plugin marketplace add ChmielewskiPatryk/skills        # dodaj marketplace
claude plugin install claude-setup@chmielewski-skills         # zainstaluj plugin

# --- Aktualizacja ---
claude plugin marketplace update chmielewski-skills
claude plugin update claude-setup@chmielewski-skills

# --- Rozwój ---
claude plugin validate .                                      # waliduj marketplace
claude plugin validate ./plugins/claude-setup                 # waliduj plugin
claude --plugin-dir ./plugins/claude-setup                    # testuj lokalnie

# --- W sesji Claude Code ---
/plugin                                                       # menu pluginów
/reload-plugins                                               # przeładuj po zmianach
/claude-setup:context-statusline                              # użyj skilla
/java-backend:planning-jira-implementation PROJ-123           # plan implementacji z Jiry
/java-backend:reviewing-java-commits <link-PR> <link-analizy>  # code review pull requesta
/java-backend:analyzing-confluence-feasibility <link-strony>  # analiza wykonalności
/java-backend:smoke-testing-locally PROJ-123                  # lokalny smoke test zadania
/java-backend:running-task-retro PROJ-123                     # retrospektywa zadania
```

Dokumentacja:

- Marketplace'y: https://code.claude.com/docs/en/plugin-marketplaces
- Instalacja pluginów: https://code.claude.com/docs/en/discover-plugins
- Pluginy (referencja): https://code.claude.com/docs/en/plugins-reference
- Skille: https://code.claude.com/docs/en/skills
