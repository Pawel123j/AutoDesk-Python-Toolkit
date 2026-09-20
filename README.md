# AutoDesk Python Toolkit

AutoDesk Python Toolkit is a local full-stack automation dashboard for beginner and intermediate portfolio work. It combines a FastAPI backend with a React, TypeScript, Tailwind CSS frontend to clean CSV files, convert CSV to Excel, generate simple reports, simulate file sorting, and store action history in SQLite.

No paid APIs are required. Everything runs locally.

> **Uwaga co do nazwy.** Ten projekt nie ma żadnego związku z firmą
> **Autodesk, Inc.** (AutoCAD, Maya, Fusion 360). Zbieżność nazw jest
> przypadkowa i **nazwa powinna zostać zmieniona** — propozycje
> i uzasadnienie: [docs/NAZWA.md](docs/NAZWA.md).

## Features

- Homepage with a polished dashboard overview
- CSV cleaner with upload, empty row removal, duplicate removal, normalized column names, and preview table
- CSV to Excel converter with downloadable XLSX output
- Report generator with downloadable TXT or HTML reports
- File sorter simulation for images, documents, spreadsheets, archives, and other files
- SQLite history page with date, action type, file name, and details
- FastAPI automatic documentation at `/docs`
- Loading states and friendly error messages in the frontend

## Tech Stack

Backend:

- Python
- FastAPI
- Pandas
- SQLite
- Uvicorn
- Pydantic

Frontend:

- React
- TypeScript
- Tailwind CSS
- Vite

## Project Structure

```text
AutoDesk-Python-Toolkit/
  backend/
    app/
      main.py
      database.py
      schemas.py
      services.py
    data/
    generated/
  examples/
    sample_sales.csv
  frontend/
    src/
      components/
      lib/
      App.tsx
      main.tsx
    package.json
  requirements.txt
  README.md
  .gitignore
```

## Uruchomienie przez Dockera

Najszybsza droga — jedna komenda stawia backend i frontend:

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API i dokumentacja: http://localhost:8000/docs

Obraz backendu działa **bez roota** i ma healthcheck; frontend jest
budowany w osobnym etapie, więc do obrazu wynikowego nie trafia ani
`node_modules`, ani kod źródłowy — sam katalog `dist` serwowany przez nginx.

Adres backendu wchodzi do bundla frontendu **w czasie budowania** (Vite
podmienia `import.meta.env.*` na stałe), więc zmiana `VITE_API_BASE_URL`
wymaga przebudowania obrazu, nie tylko restartu.

## Testy, lint i CI

```bash
# backend
pip install -r requirements.txt pytest ruff
ruff check .
pytest                    # 46 testów

# frontend
cd frontend && npm ci
npm run lint              # ESLint
npm run typecheck         # tsc --noEmit
npm run build
```

CI uruchamia to wszystko na każdej gałęzi, plus buduje oba obrazy Dockera
**i sprawdza, że backend odpowiada** — obraz, którego nikt nie uruchomił,
nie jest dowodem na nic.

Wcześniej jedynym sprawdzeniem backendu było `python -m compileall`.
Sprawdzanie, czy kod daje się sparsować, nie mówi nic o tym, czy robi to,
co powinien — a to jest aplikacja do przetwarzania danych, w której błąd
niczego nie wywala, tylko zwraca złe liczby.

### Co pokrywają testy

Testy dotyczą warstwy przetwarzania danych, bo tam błąd jest najdroższy
i najtrudniejszy do zauważenia:

| Obszar | Przykład tego, co jest sprawdzane |
|---|---|
| Normalizacja nazw kolumn | wynik **zawsze unikalny** — dwie kolumny o tej samej nazwie sprawiają, że przy zamianie wiersza na słownik jedna po cichu przesłania drugą |
| Czyszczenie CSV | usuwany jest wiersz *całkowicie* pusty, nie taki z jedną brakującą wartością; liczby się bilansują; ramka wejściowa nie jest modyfikowana |
| Podgląd | `NaN` zamieniany na `null` (inaczej frontend nie sparsuje odpowiedzi), wartości jako typy Pythona a nie numpy |
| Raporty | nazwa pliku i nazwy kolumn **escapowane** w HTML — oba pochodzą od użytkownika |
| Nazwy plików | `../../etc/passwd` sprowadzane do `passwd`; losowy przyrostek, żeby drugi użytkownik nie nadpisał pliku pierwszego |

Podczas pisania tych testów wyszedł **realny błąd** w normalizacji nazw
kolumn: dla `["Name", "name_2", "NAME"]` powstawały dwie kolumny `name_2`.
Licznik wystąpień nazwy bazowej nie sprawdzał, czy wygenerowany przyrostek
nie koliduje z nazwą, która wystąpiła w pliku dosłownie. Naprawione.

## Backend Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Backend URLs:

- API root: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

Optional CORS configuration:

```powershell
$env:CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

## Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

If your backend runs on another host or port, create `frontend/.env`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Try It Quickly

1. Start the backend.
2. Start the frontend.
3. Open `http://127.0.0.1:5173`.
4. Upload `examples/sample_sales.csv` in the CSV Cleaner, Converter, or Report Generator.
5. Visit the History page to see the saved SQLite log.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/csv/clean` | Clean CSV and return preview JSON |
| `POST` | `/api/csv/to-excel` | Convert CSV to downloadable XLSX |
| `POST` | `/api/reports/generate?format=txt` | Generate downloadable text report |
| `POST` | `/api/reports/generate?format=html` | Generate downloadable HTML report |
| `POST` | `/api/file-sorter/simulate` | Categorize example file names |
| `GET` | `/api/history` | Read processing history |
| `DELETE` | `/api/history` | Clear processing history |

## Development Notes

- Uploaded CSV files are processed in memory and capped at 10 MB.
- Generated downloads are written to `backend/generated/`, which is ignored by Git.
- SQLite history is stored in `backend/data/toolkit.db`, which is ignored by Git.
- The backend is split into routes, services, schemas, and database helpers for readability.
- The frontend uses reusable upload, status, and preview components.

## Production Ideas

- Add authentication for multi-user use
- Add background cleanup for generated files
- Add unit tests for CSV processing and sorter categorization
- Add Docker Compose for one-command startup
- Add richer report templates and chart exports

## Licencja

MIT — patrz [LICENSE](LICENSE).
