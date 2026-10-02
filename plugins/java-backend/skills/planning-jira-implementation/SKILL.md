---
name: planning-jira-implementation
description: Use when asked to turn a Jira ticket/issue into a backend implementation plan, or to plan how a Jira issue should be implemented before writing code. This team implements backend only, using jOOQ/Hibernate and a package-by-feature structure, and treats the ticket's linked system-analysis document (usually Confluence) as the source of truth, not the ticket description alone.
disable-model-invocation: false
---

# Planning Jira Implementation

## Overview

Turns one Jira issue into a step-by-step backend implementation plan, sourced from the issue and the system-analysis document it links to (the actual source of truth), saved as `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md`, with a local markdown copy of the analysis cached alongside it so questions can cite it by line. Never guess at requirements or the data model — stop and ask the developer whenever the source material is missing, contradictory, or doesn't match what already exists in the codebase.

## When to Use

- User gives a Jira key or link (or says "to zadanie", "ten ticket") and asks for an implementation plan, or "jak to zaimplementować".
- Scope is backend only. If the ticket also describes frontend/UI behavior, plan only the backend portion and list the rest under "Poza zakresem" in the output — do not plan frontend steps.
- This skill only produces the plan file, it does not write code.

## Dostęp do Jiry i Confluence

Skill nie zależy od konkretnego serwera MCP ani narzędzia. Przed krokiem 1 sprawdź, czym dysponujesz w bieżącej sesji, i użyj pierwszej dostępnej opcji:

1. **Narzędzia MCP do Jiry i Confluence** — dowolny skonfigurowany serwer (na przykład `mcp-atlassian`, oficjalny serwer Atlassian Rovo albo inny). Rozpoznaj je po nazwach narzędzi zawierających `jira`, `confluence` lub `atlassian`. Jeśli narzędzia są dostępne tylko jako odroczone (deferred), najpierw załaduj ich schematy przez wyszukiwarkę narzędzi.
2. **Narzędzie wiersza poleceń**, jeśli jest zainstalowane i zalogowane (na przykład `acli` albo `jira`).
3. **REST API Atlassiana** przez `curl`, jeśli w środowisku są ustawione adres instancji i token (na przykład zmienne `JIRA_URL`, `JIRA_API_TOKEN`, `CONFLUENCE_URL`). Nie wypisuj tokenu w odpowiedziach ani w pliku planu.

Jeśli nie ma żadnego dostępu, zatrzymaj się i poproś użytkownika o wklejenie treści zadania oraz analizy systemowej (razem z komentarzami) albo o skonfigurowanie dostępu. Nie planuj na podstawie samego klucza zadania.

Kroki poniżej opisują, **jakie dane** pobrać. Konkretną nazwę narzędzia lub endpointu dobierz do dostępnej opcji.

## Process

1. **Pobierz zadanie Jira** razem z komentarzami i linkami zewnętrznymi (remote links / web links). Zbierz opis, kryteria akceptacji, powiązane zadania/epik oraz linki zewnętrzne — link do analizy systemowej bywa dodany jako "web link" w Jirze, a nie tylko wklejony w treści opisu.
2. **Znajdź link do analizy systemowej.** Szukaj adresu Confluence w opisie zadania, w komentarzach Jiry i w linkach zewnętrznych zadania. Jeżeli żadnego linku nie ma — **zatrzymaj się i zapytaj użytkownika o link do analizy systemowej**. Nie planuj na podstawie samego opisu zadania z Jiry — to nie jest źródło prawdy, źródłem prawdy jest analiza systemowa.
3. **Pobierz analizę systemową** (treść strony Confluence) oraz **komentarze do niej**, zarówno zwykłe (footer), jak i inline. Jeśli wybrane narzędzie nie udostępnia komentarzy inline, zaznacz w planie, że nie zostały sprawdzone. Jeśli link prowadzi donikąd (strona przeniesiona/usunięta), spróbuj odnaleźć ją przez wyszukiwanie w Confluence (po tytule lub kluczu zadania), zanim zapytasz użytkownika.
4. **Zapisz lokalną kopię analizy** do `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` (utwórz folder `.analiza`, jeśli nie istnieje). Dzięki tej kopii cytujesz analizę przez `ścieżka:linia`, a programista czyta ją w edytorze obok terminala, zamiast szukać fragmentu w przeglądarce.
   - Zapisz treść strony jako markdown i **zachowaj nagłówki sekcji z oryginału** — po nich budujesz anchory do linkowania w pytaniach.
   - Komentarze wstaw przy akapitach, do których należą: komentarz inline bezpośrednio pod cytowanym fragmentem (wyraźnie oznaczony, na przykład `> [komentarz inline – <autor>, <data>] ...`), komentarze footer w sekcji `## Komentarze` na końcu pliku.
   - Na początku pliku zapisz nagłówek: link do strony Confluence, tytuł, datę pobrania i informację, czy komentarze inline udało się pobrać.
   - Plik jest cache'em, nie źródłem prawdy. Jeśli już istnieje dla tego zadania, nadpisz go świeżo pobraną treścią.
   - Jeśli repozytorium ma `.gitignore`, dopisz do niego `IMPLEMENTATION_PLAN/.analiza/`, jeśli jeszcze go tam nie ma — to lokalny cache, a nie artefakt do commitowania.
5. **Zestaw źródła ze sobą:** opis zadania, komentarze Jiry, treść analizy, komentarze do analizy. Traktuj analizę systemową jako źródło prawdy o wymaganiach, ale nowszy komentarz korygujący jej treść ma pierwszeństwo przed nieaktualnym fragmentem głównego dokumentu. Jeśli źródła są sprzeczne w sposób zmieniający zakres lub kształt rozwiązania, a żaden komentarz tego nie rozstrzyga — nie wybieraj samodzielnie która wersja obowiązuje, zapytaj użytkownika.
6. **Sprawdź model danych.** Ustal, jakie encje/tabele/pola opisuje zadanie lub analiza, i poszukaj w kodzie projektu (klasy encji, definicje tabel jOOQ, migracje SQL) odpowiadającej im, już istniejącej struktury.
   - Jeśli istniejący model pasuje — w planie podaj dokładnie, gdzie w kodzie on się znajduje (pakiet, klasa, tabela), żeby programista tego nie szukał od nowa.
   - Jeśli model z zadania lub analizy **nie pasuje** do tego, co jest w kodzie (inna nazwa tabeli, inne pola, kolizja z tabelą używaną już przez inną funkcjonalność), **a ani zadanie, ani analiza, ani żaden komentarz tego nie tłumaczy** — zatrzymaj się i zapytaj programistę, gdzie jest właściwy model danych. Nie zakładaj samodzielnie, że trzeba stworzyć nową tabelę czy encję.
7. **Rozbij pracę na kroki.** Każdy krok to jedna, konkretna, możliwa do zweryfikowania zmiana (na przykład: dodanie migracji SQL, dodanie metody w konkretnej klasie, implementacja jednego endpointu kontraktu w konkretnym repozytorium). Dla każdego kroku podaj: repozytorium/moduł, od czego zależy (numery innych kroków) i czy może iść równolegle z innym krokiem.
8. **Wyznacz grupy równoległe.** Dwa kroki mogą iść równolegle, jeśli żaden z nich nie czeka na wynik drugiego. Typowy przypadek z tego projektu: gdy kształt kontraktu (np. specyfikacja API) został ustalony jako osobny, wcześniejszy krok, to implementacja w repozytorium dostarczającym kontrakt i implementacja w repozytorium, które ten kontrakt konsumuje, mogą iść równolegle — obie strony pracują od ustalonego kształtu kontraktu, nie czekając na scalenie kodu tej drugiej strony. Oznacz takie grupy jawnie w planie.
9. **Zbierz wszystkie pytania i zadaj je przed zapisaniem planu**, jeśli poprzednie kroki wygenerowały wątpliwość (brak linku do analizy, sprzeczne źródła, niedopasowany model danych, niejasny podział na repozytoria). Zadaj je razem, jednym zestawem, zanim zapiszesz plik — nie publikuj planu opartego na założeniach, które dało się łatwo zweryfikować pytaniem. **Każde pytanie musi przyjść z dowodem** w formacie z sekcji "Format pytań" — programista nie ma odtwarzać kontekstu, który już masz w sesji. Zanim zapytasz, przeszukaj lokalną kopię analizy i komentarze — nie zadawaj pytania, na które odpowiedź jest w pobranych źródłach.
10. **Zapisz plan** w pliku `IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md` (na przykład `IMPLEMENTATION_PLAN_PROJ-777.md`) w folderze `IMPLEMENTATION_PLAN` w katalogu głównym repozytorium, w którym aktualnie pracujesz. Jeśli folder `IMPLEMENTATION_PLAN` nie istnieje w katalogu głównym repozytorium, utwórz go. Jeśli praca obejmuje kilka repozytoriów, zapisz jeden plan w repozytorium wiodącym dla tej funkcjonalności, a kroki dotyczące pozostałych repozytoriów opisz w tym samym pliku, jawnie podając nazwę repozytorium przy każdym z nich.

## Format pytań

Każde pytanie zadane programiście składa się z czterech elementów:

- **Cytat** — dosłowny fragment (1–3 zdania) analizy, zadania lub komentarza, którego dotyczy wątpliwość.
- **Skąd pochodzi** — nazwa sekcji plus link do anchora na stronie Confluence (`<link-strony>#<Nazwa-Sekcji>`) oraz odnośnik do lokalnej kopii w formacie `IMPLEMENTATION_PLAN/.analiza/<KLUCZ>-analiza.md:<linia>`. Dla komentarza podaj autora i datę. Dla kodu podaj ścieżkę pliku i numer linii.
- **Co jest niejasne** — jedno zdanie.
- **Hipoteza** — Twoja najlepsza odpowiedź, sformułowana tak, żeby programista mógł ją potwierdzić jednym słowem, a nie pisać wyjaśnienie od zera. Jeśli sensownych odpowiedzi jest kilka, wypisz je jako warianty do wyboru.

Przykład:

```
Pytanie 2 — model danych

Cytat (analiza, sekcja "Model danych"):
> Harmonogram zapisujemy w tabeli `payment_schedule` z polami `due_date`,
> `amount_net`, `amount_gross`.

Skąd: https://confluence.firma.pl/pages/12345#Model-danych
      IMPLEMENTATION_PLAN/.analiza/PROJ-777-analiza.md:142
W kodzie: PaymentScheduleEntity (com.firma.payments.schedule), tabela
`payments_schedule` — pole `amount`, bez rozbicia na netto/brutto.

Niejasne: czy analiza opisuje nową tabelę, czy rozszerzenie istniejącej.

Hipoteza: rozszerzamy istniejącą `payments_schedule` (migracja dodająca
`amount_net`/`amount_gross`), bo nazwa i przeznaczenie się pokrywają.
Warianty: (a) rozszerzyć istniejącą, (b) nowa tabela obok istniejącej.
```

## Kiedy zapytać, a kiedy nie

| Sytuacja | Reakcja |
|---|---|
| Zadanie nie zawiera linku do analizy systemowej | Zapytaj o link — nie planuj na podstawie samego opisu zadania. |
| Analiza systemowa jest sprzeczna z opisem zadania w sposób zmieniający zakres, a żaden komentarz tego nie rozstrzyga | Zapytaj, które źródło jest aktualne. |
| Komentarz w Jirze lub pod stroną Confluence koryguje treść dokumentu (na przykład zmienia nazwę pola) | Nie pytaj — zastosuj poprawkę z komentarza, ale zaznacz w planie, że pochodzi z komentarza, a nie z głównej treści dokumentu. |
| Model danych z zadania lub analizy nie pasuje do istniejącego kodu, a nic tego nie tłumaczy | Zapytaj programistę, gdzie jest właściwy model danych — nie zakładaj tworzenia nowej tabeli lub encji. |
| Nie wiadomo, w którym repozytorium ma powstać dany fragment zmiany | Zapytaj, chyba że analiza jednoznacznie to określa. |
| Masz wątpliwość, ale odpowiedź jest w pobranej analizie lub w komentarzach | Nie pytaj — przeszukaj lokalną kopię analizy i użyj tego, co w niej jest. |
| Zadanie opisuje też zmiany frontendowe | Nie pytaj — zaplanuj tylko część backendową, resztę wypisz w sekcji "Poza zakresem". |

## Output

**Język:** polski.

**Lokalizacja:** `IMPLEMENTATION_PLAN/IMPLEMENTATION_PLAN_<KLUCZ-ZADANIA>.md` w katalogu głównym repozytorium (utwórz folder `IMPLEMENTATION_PLAN`, jeśli nie istnieje).

**Plik pomocniczy:** `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` — lokalna kopia analizy systemowej z komentarzami (krok 4). Nie jest częścią planu, służy do cytowania w pytaniach i do czytania obok terminala.

**Szablon:**

```markdown
# Plan implementacji – <KLUCZ-ZADANIA>: <tytuł zadania>

Źródła:
- Zadanie Jira: <link>
- Analiza systemowa: <link>
- Lokalna kopia analizy: `IMPLEMENTATION_PLAN/.analiza/<KLUCZ-ZADANIA>-analiza.md` (pobrana <data>)
- Istotne komentarze uwzględnione w planie: <krótka lista, z autorem i datą jeśli dostępne>

## Zakres

<krótki opis funkcjonalności backendowej objętej planem>

## Poza zakresem

<elementy z zadania, których ten plan nie obejmuje, na przykład frontend — albo "brak", jeśli całe zadanie jest backendowe>

## Model danych

<gdzie w kodzie żyje odpowiedni model danych, z podaniem pakietu/klasy/tabeli; jeśli programista wskazał to miejsce w odpowiedzi na pytanie, zaznacz to>

## Kroki

### Krok 1: <tytuł>

- **Repozytorium/moduł:** <nazwa>
- **Zależy od:** <numery kroków albo "brak">
- **Może być wykonywany równolegle z:** <numery kroków albo "brak">
- **Opis:** <precyzyjny opis tego, co trzeba zrobić>
- **Źródło wymagania:** <która część analizy, zadania albo komentarza jest podstawą tego kroku>

(kolejne kroki w tym samym formacie, ponumerowane)

## Grupy równoległe

<na przykład: "Krok 2 i krok 3 mogą być realizowane równocześnie w różnych repozytoriach, ponieważ oba zależą tylko od kroku 1 (ustalenie kontraktu), a nie od siebie nawzajem.">
```

## Częste błędy

- Traktowanie opisu zadania Jira jako źródła prawdy zamiast analizy systemowej, do której zadanie linkuje.
- Pominięcie komentarzy — zarówno w Jirze, jak i pod stroną Confluence — mimo że mogą zmieniać treść analizy.
- Wymyślenie nowej tabeli lub encji "na wszelki wypadek" zamiast zapytania programisty, gdy model danych z zadania nie pasuje do istniejącego kodu.
- Oznaczenie dwóch kroków jako równoległych, mimo że jeden w rzeczywistości czeka na wynik drugiego (na przykład implementacja konsumenta kontraktu, zanim kształt kontraktu został ustalony).
- Zapisanie planu mimo nierozwiązanych wątpliwości, zamiast zapytania użytkownika przed zapisaniem pliku.
- Zadanie pytania bez cytatu i bez odnośnika do miejsca w analizie — programista musi wtedy odtworzyć kontekst, który jest już w sesji.
- Zadanie pytania bez hipotezy, czyli zmuszenie programisty do napisania odpowiedzi od zera, zamiast potwierdzenia lub odrzucenia propozycji.
- Pominięcie kroku 4 (lokalna kopia analizy) i cytowanie analizy "z pamięci", bez odnośnika, który programista mógłby otworzyć.
- Zaplanowanie kroków frontendowych, mimo że ten zespół implementuje wyłącznie backend.
- Uznanie, że nie ma dostępu do Jiry lub Confluence, tylko dlatego, że brakuje jednego konkretnego serwera MCP — sprawdź wszystkie opcje z sekcji "Dostęp do Jiry i Confluence".
