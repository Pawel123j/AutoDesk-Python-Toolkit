# Zrzuty ekranu

Ten katalog jest pusty celowo.

Zrzuty wymagają uruchomionej aplikacji z interfejsem — środowisko, w którym
przygotowywano to repozytorium, nie ma przeglądarki ani demona Dockera.
Wizualizacja zamiast prawdziwego zrzutu byłaby gorsza niż brak obrazka.

## Jak je zrobić

Najprościej przez Dockera — jedna komenda stawia backend i frontend:

```bash
docker compose up --build
```

Frontend: http://localhost:5173, dokumentacja API: http://localhost:8000/docs

Albo bez Dockera, w dwóch terminalach:

```bash
# terminal 1
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir backend

# terminal 2
cd frontend && npm install && npm run dev
```

## Co warto pokazać

| Plik | Widok |
|---|---|
| `dashboard.png` | strona główna z kafelkami narzędzi |
| `csv-cleaner.png` | wynik czyszczenia CSV: liczby usuniętych wierszy i podgląd |
| `excel-export.png` | konwersja CSV na XLSX |
| `report.png` | wygenerowany raport HTML |
| `file-sorter.png` | symulacja sortowania plików wg kategorii |
| `history.png` | historia operacji z SQLite |
| `api-docs.png` | automatyczna dokumentacja FastAPI pod `/docs` |

Dobry plik testowy do zrzutów: taki z duplikatami, pustymi wierszami
i kolumnami o nazwach `First Name`, `E-mail Address` — widać wtedy,
co narzędzie faktycznie robi.
