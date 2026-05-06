from __future__ import annotations

import html
import io
import math
import re
import uuid
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PREVIEW_LIMIT = 25

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".tiff"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"}
SPREADSHEET_EXTENSIONS = {".csv", ".xls", ".xlsx", ".ods", ".tsv"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}


async def read_csv_upload(upload: UploadFile) -> tuple[pd.DataFrame, str]:
    file_name = sanitize_original_filename(upload.filename)
    if not file_name.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV file is too large. The limit is 10 MB.")

    try:
        dataframe = pd.read_csv(io.BytesIO(data))
    except pd.errors.EmptyDataError as exc:
        raise HTTPException(status_code=400, detail="The CSV file has no readable columns.") from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="The CSV encoding is not supported.") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV file: {exc}") from exc

    return dataframe, file_name


def clean_csv(dataframe: pd.DataFrame) -> dict[str, Any]:
    original_rows = len(dataframe)
    without_empty_rows = dataframe.dropna(how="all")
    empty_rows_removed = original_rows - len(without_empty_rows)

    without_duplicates = without_empty_rows.drop_duplicates()
    duplicate_rows_removed = len(without_empty_rows) - len(without_duplicates)

    cleaned = without_duplicates.reset_index(drop=True).copy()
    cleaned.columns = normalize_column_names(cleaned.columns)

    return {
        "dataframe": cleaned,
        "original_rows": original_rows,
        "cleaned_rows": len(cleaned),
        "empty_rows_removed": empty_rows_removed,
        "duplicate_rows_removed": duplicate_rows_removed,
        "columns": list(cleaned.columns),
        "preview": dataframe_preview(cleaned),
    }


def normalize_column_names(columns: pd.Index) -> list[str]:
    normalized: list[str] = []
    seen: dict[str, int] = {}

    for column in columns:
        value = str(column).strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = value.strip("_") or "column"

        seen[value] = seen.get(value, 0) + 1
        normalized.append(value if seen[value] == 1 else f"{value}_{seen[value]}")

    return normalized


def dataframe_preview(dataframe: pd.DataFrame, limit: int = PREVIEW_LIMIT) -> list[dict[str, Any]]:
    rows = dataframe.head(limit).where(pd.notnull(dataframe.head(limit)), None)
    records = rows.to_dict(orient="records")
    return [{key: to_json_safe(value) for key, value in row.items()} for row in records]


def to_json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def build_report(dataframe: pd.DataFrame, file_name: str, report_format: Literal["txt", "html"]) -> str:
    stats = calculate_report_stats(dataframe)
    if report_format == "html":
        return build_html_report(file_name, stats)
    return build_text_report(file_name, stats)


def calculate_report_stats(dataframe: pd.DataFrame) -> dict[str, Any]:
    numeric = dataframe.select_dtypes(include="number")
    averages = {
        column: None if pd.isna(value) else round(float(value), 4)
        for column, value in numeric.mean(numeric_only=True).items()
    }

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "missing_values": {column: int(dataframe[column].isna().sum()) for column in dataframe.columns},
        "numeric_averages": averages,
    }


def build_text_report(file_name: str, stats: dict[str, Any]) -> str:
    lines = [
        "AutoDesk Python Toolkit Report",
        "=" * 34,
        f"Source file: {file_name}",
        "",
        f"Row count: {stats['row_count']}",
        f"Column count: {stats['column_count']}",
        "",
        "Missing values:",
    ]

    for column, count in stats["missing_values"].items():
        lines.append(f"- {column}: {count}")

    lines.extend(["", "Numeric column averages:"])
    if stats["numeric_averages"]:
        for column, average in stats["numeric_averages"].items():
            lines.append(f"- {column}: {average if average is not None else 'n/a'}")
    else:
        lines.append("- No numeric columns detected.")

    lines.append("")
    return "\n".join(lines)


def build_html_report(file_name: str, stats: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"<tr><td>{html.escape(str(column))}</td><td>{count}</td></tr>"
        for column, count in stats["missing_values"].items()
    )
    average_rows = "\n".join(
        f"<tr><td>{html.escape(str(column))}</td><td>{average if average is not None else 'n/a'}</td></tr>"
        for column, average in stats["numeric_averages"].items()
    ) or "<tr><td colspan=\"2\">No numeric columns detected.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoDesk Python Toolkit Report</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; margin: 40px; color: #171717; background: #fafafa; }}
    main {{ max-width: 880px; margin: 0 auto; background: #fff; border: 1px solid #e5e5e5; padding: 32px; }}
    h1 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #e5e5e5; padding: 10px 12px; text-align: left; }}
    th {{ background: #f4f4f5; }}
    .stats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }}
    .stat {{ border: 1px solid #e5e5e5; padding: 16px; background: #fafafa; }}
    .label {{ color: #525252; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }}
    .value {{ font-size: 28px; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>AutoDesk Python Toolkit Report</h1>
    <p><strong>Source file:</strong> {html.escape(file_name)}</p>
    <section class="stats">
      <div class="stat"><div class="label">Rows</div><div class="value">{stats['row_count']}</div></div>
      <div class="stat"><div class="label">Columns</div><div class="value">{stats['column_count']}</div></div>
    </section>
    <h2>Missing values</h2>
    <table><thead><tr><th>Column</th><th>Missing values</th></tr></thead><tbody>{missing_rows}</tbody></table>
    <h2>Numeric averages</h2>
    <table><thead><tr><th>Column</th><th>Average</th></tr></thead><tbody>{average_rows}</tbody></table>
  </main>
</body>
</html>
"""


def categorize_file_names(file_names: list[str]) -> dict[str, list[str]]:
    categories = {
        "Images": [],
        "Documents": [],
        "Spreadsheets": [],
        "Archives": [],
        "Other": [],
    }

    for raw_name in file_names:
        file_name = raw_name.strip()
        if not file_name:
            continue

        extension = Path(file_name).suffix.lower()
        if extension in IMAGE_EXTENSIONS:
            categories["Images"].append(file_name)
        elif extension in DOCUMENT_EXTENSIONS:
            categories["Documents"].append(file_name)
        elif extension in SPREADSHEET_EXTENSIONS:
            categories["Spreadsheets"].append(file_name)
        elif extension in ARCHIVE_EXTENSIONS:
            categories["Archives"].append(file_name)
        else:
            categories["Other"].append(file_name)

    return categories


def sanitize_original_filename(file_name: str | None) -> str:
    if not file_name:
        raise HTTPException(status_code=400, detail="Missing file name.")
    return Path(file_name).name


def make_generated_path(directory: Path, original_name: str, extension: str) -> tuple[Path, str]:
    directory.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(original_name).stem).strip("-") or "processed"
    download_name = f"{stem}-{uuid.uuid4().hex[:8]}{extension}"
    return directory / download_name, download_name
