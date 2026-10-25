from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .database import add_history, clear_history, fetch_history, init_db
from .schemas import (
    CleanCsvResponse,
    FileSorterRequest,
    FileSorterResponse,
    HealthResponse,
    HistoryResponse,
    MessageResponse,
)
from .services import (
    build_report,
    categorize_file_names,
    clean_csv,
    make_generated_path,
    read_csv_upload,
    write_excel_values,
)

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = Path(os.getenv("AUTODESK_GENERATED_DIR", str(BASE_DIR / "generated")))
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def temporary_download(
    file_name: str, extension: str, media_type: str, write: Callable[[Path, str], None],
) -> FileResponse:
    """Retain only this request's export until its response has been sent.

    Existing files in GENERATED_DIR are never scanned or removed. The owned
    temporary directory is also cleaned if generation/history fails.
    """
    temporary = TemporaryDirectory(prefix="export-", dir=GENERATED_DIR)
    try:
        output, download_name = make_generated_path(Path(temporary.name), file_name, extension)
        write(output, download_name)
        return FileResponse(
            path=output, filename=download_name, media_type=media_type,
            headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
            background=BackgroundTask(temporary.cleanup),
        )
    except BaseException:
        temporary.cleanup()
        raise


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="AutoDesk Python Toolkit API",
    version="1.0.0",
    description="FastAPI backend for CSV cleaning, conversion, reporting, file sorting, and history logging.",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=MessageResponse, tags=["System"])
def root() -> MessageResponse:
    return MessageResponse(
        message="AutoDesk Python Toolkit API is running. Open /docs for interactive API docs."
    )


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="AutoDesk Python Toolkit API", docs_url="/docs")


@app.post("/api/csv/clean", response_model=CleanCsvResponse, tags=["CSV"])
async def clean_csv_endpoint(file: UploadFile = File(...)) -> CleanCsvResponse:
    dataframe, file_name = await read_csv_upload(file)
    result = clean_csv(dataframe)
    add_history(
        action_type="CSV Cleaner",
        file_name=file_name,
        details={
            "original_rows": result["original_rows"],
            "cleaned_rows": result["cleaned_rows"],
            "empty_rows_removed": result["empty_rows_removed"],
            "duplicate_rows_removed": result["duplicate_rows_removed"],
        },
    )

    return CleanCsvResponse(
        file_name=file_name,
        original_rows=result["original_rows"],
        cleaned_rows=result["cleaned_rows"],
        empty_rows_removed=result["empty_rows_removed"],
        duplicate_rows_removed=result["duplicate_rows_removed"],
        columns=result["columns"],
        preview=result["preview"],
    )


@app.post("/api/csv/to-excel", tags=["CSV"])
async def csv_to_excel_endpoint(file: UploadFile = File(...)) -> FileResponse:
    dataframe, file_name = await read_csv_upload(file)

    def write(output_path: Path, download_name: str) -> None:
        try:
            write_excel_values(dataframe, output_path)
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail="Could not convert CSV to Excel. Please retry."
            ) from exc
        add_history(
            action_type="CSV to Excel", file_name=file_name,
            details={
                "download_name": download_name, "rows": len(dataframe), "columns": len(dataframe.columns),
            },
        )

    return temporary_download(
        file_name, ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", write,
    )


@app.post("/api/reports/generate", tags=["Reports"])
async def report_generator_endpoint(
    file: UploadFile = File(...),
    report_format: Literal["txt", "html"] = Query("txt", alias="format"),
) -> FileResponse:
    dataframe, file_name = await read_csv_upload(file)
    extension = ".html" if report_format == "html" else ".txt"

    def write(output_path: Path, download_name: str) -> None:
        try:
            report = build_report(dataframe, file_name, report_format)
            output_path.write_text(report, encoding="utf-8")
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Could not generate report. Please retry.") from exc
        add_history(
            action_type="Report Generator", file_name=file_name,
            details={"download_name": download_name, "format": report_format, "rows": len(dataframe)},
        )

    media_type = "text/html" if report_format == "html" else "text/plain"
    return temporary_download(file_name, extension, media_type, write)


@app.post("/api/file-sorter/simulate", response_model=FileSorterResponse, tags=["File Sorter"])
def file_sorter_endpoint(payload: FileSorterRequest) -> FileSorterResponse:
    categories = categorize_file_names(payload.file_names)
    total_files = sum(len(files) for files in categories.values())
    if total_files == 0:
        raise HTTPException(status_code=400, detail="Enter at least one valid file name.")

    add_history(
        action_type="File Sorter Simulation",
        file_name="manual-input",
        details={"total_files": total_files},
    )
    return FileSorterResponse(categories=categories, total_files=total_files)


@app.get("/api/history", response_model=HistoryResponse, tags=["History"])
def history_endpoint(limit: int = Query(100, ge=1, le=250)) -> HistoryResponse:
    return HistoryResponse(items=fetch_history(limit=limit))


@app.delete("/api/history", response_model=MessageResponse, tags=["History"])
def clear_history_endpoint() -> MessageResponse:
    clear_history()
    return MessageResponse(message="History cleared.")
