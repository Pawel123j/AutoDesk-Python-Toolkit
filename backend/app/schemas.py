from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    docs_url: str


class CleanCsvResponse(BaseModel):
    file_name: str
    original_rows: int
    cleaned_rows: int
    empty_rows_removed: int
    duplicate_rows_removed: int
    columns: list[str]
    preview: list[dict[str, Any]]


class FileSorterRequest(BaseModel):
    file_names: list[str] = Field(..., min_length=1, description="Example file names to categorize.")


class FileSorterResponse(BaseModel):
    categories: dict[str, list[str]]
    total_files: int


class HistoryItem(BaseModel):
    id: int
    created_at: str
    action_type: str
    file_name: str
    details: dict[str, Any] = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class MessageResponse(BaseModel):
    message: str
