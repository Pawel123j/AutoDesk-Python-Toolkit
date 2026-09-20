# Nazwa projektu — propozycja zmiany

**Nic nie zostało zmienione.** Ten dokument opisuje problem i możliwe
rozwiązania; decyzja należy do autora.

## Problem

Projekt nazywa się **AutoDesk Python Toolkit**. **Autodesk, Inc.** to
istniejąca firma i zarejestrowany znak towarowy — twórca AutoCAD-a, Mayi,
Fusion 360 i 3ds Maxa.

Ten projekt nie ma z nią żadnego związku. Jest to lokalne narzędzie do
czyszczenia plików CSV, konwersji do Excela i generowania raportów.

Konsekwencje są dwie i obie realne:

1. **Praktyczna.** Ktoś, kto zobaczy tę nazwę w portfolio, spodziewa się
   integracji z produktami Autodesku albo pracy z plikami DWG. Dostaje
   narzędzie do arkuszy — i przez pierwszą minutę zastanawia się, czy
   czegoś nie przeoczył. To jest odwrotność tego, do czego służy portfolio.
2. **Prawna.** Używanie cudzego znaku towarowego w nazwie własnego
   projektu bywa problematyczne, nawet przy braku złej woli i przy
   projekcie niekomercyjnym. Nie jest to porada prawna — to sygnał, że
   warto się nad tym zastanowić, zanim projekt gdziekolwiek pójdzie dalej.

Prawdopodobne źródło nazwy: „auto" jak automatyzacja + „desk" jak biurko.
Zbieżność wygląda na przypadkową.

## Co nazwa musiałaby objąć

Słowo „AutoDesk" występuje w 16 miejscach:

| Gdzie | Co dokładnie |
|---|---|
| `backend/app/main.py` | tytuł API (widoczny w `/docs`), komunikaty dwóch endpointów |
| `backend/app/services.py` | nagłówek raportu TXT, `<title>` i `<h1>` raportu HTML |
| `backend/app/__init__.py` | docstring pakietu |
| `frontend/src/App.tsx` | nagłówek strony i etykieta w pasku bocznym |
| `frontend/package.json` | nazwa pakietu |
| `README.md` | tytuł i opis |
| nazwa repozytorium | `AutoDesk-Python-Toolkit` |

Zmiana w kodzie to kilkanaście podmian tekstu — technicznie prosta.
Zmiana nazwy repozytorium oznacza nowy adres URL; GitHub ustawia
przekierowanie ze starego, ale wszystkie linki w CV, na LinkedInie i
w wiadomościach do rekruterów prowadzą wtedy przez przekierowanie.

## Propozycje

| Nazwa | Dlaczego |
|---|---|
| **DeskFlow Toolkit** | zachowuje „desk" i skojarzenie z pracą biurową, bez kolizji |
| **DataDesk Toolkit** | mówi wprost, czym projekt jest: biurko do pracy z danymi |
| **CSV Workbench** | najbardziej dosłowna; oglądający wie, co dostanie, zanim kliknie |
| **AutoSheet Toolkit** | zachowuje „auto" jak automatyzacja, zamienia mylące „desk" |

Rekomendacja: **CSV Workbench** albo **DataDesk Toolkit**. Pierwsza jest
uczciwsza wobec czytelnika, druga ładniej brzmi.

## Dlaczego nic nie zmieniono

Nazwa projektu to decyzja autora, nie sprzątanie po kodzie. Zmiana
identyfikatora repozytorium ma też konsekwencje poza nim — w linkach,
które ktoś już gdzieś umieścił. Takich rzeczy nie robi się za kogoś.
