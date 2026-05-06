# AutoDesk Python Toolkit

AutoDesk Python Toolkit is a local full-stack automation dashboard for beginner and intermediate portfolio work. It combines a FastAPI backend with a React, TypeScript, Tailwind CSS frontend to clean CSV files, convert CSV to Excel, generate simple reports, simulate file sorting, and store action history in SQLite.

No paid APIs are required. Everything runs locally.

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
