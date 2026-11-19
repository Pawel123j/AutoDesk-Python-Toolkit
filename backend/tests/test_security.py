"""Regresje bezpieczeństwa: AD-01 (ekspozycja lokalnej usługi) i AD-02 (formula injection)."""

from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from app import database, main
from app.services import neutralize_formulas
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "data/toolkit.db")
    monkeypatch.setattr(main, "GENERATED_DIR", tmp_path / "generated")
    with TestClient(main.app) as test_client:
        yield test_client


def test_formula_like_text_is_neutralized_but_numbers_are_not():
    frame = pd.DataFrame({"=evil()": ["=HYPERLINK(\"http://x\")", "+1+1", "@SUM(A1)", "-2", "ok"], "n": [1, -2, 3, 4, 5]})
    safe = neutralize_formulas(frame)
    assert list(safe.columns) == ["'=evil()", "n"]
    assert safe.iloc[:, 0].tolist() == ["'=HYPERLINK(\"http://x\")", "'+1+1", "'@SUM(A1)", "'-2", "ok"]
    assert safe["n"].tolist() == [1, -2, 3, 4, 5]
    assert frame.iloc[0, 0].startswith("=")  # oryginał nienaruszony


def test_excel_export_contains_no_formulas(client):
    csv = b'name,link\nAlice,"=HYPERLINK(""http://attacker.test"",""x"")"\nBob,=1+1\n'
    response = client.post("/api/csv/to-excel", files={"file": ("data.csv", csv)})
    assert response.status_code == 200
    sheet = openpyxl.load_workbook(BytesIO(response.content)).active
    values = [cell.value for row in sheet.iter_rows(min_row=2) for cell in row]
    assert not any(isinstance(v, str) and v.startswith("=") for v in values)
    assert "'=1+1" in values


def test_cross_site_write_is_rejected(client):
    response = client.delete("/api/history", headers={"Origin": "https://attacker.test"})
    assert response.status_code == 403
    upload = client.post(
        "/api/csv/clean",
        files={"file": ("x.csv", b"a\n1\n")},
        headers={"Origin": "https://attacker.test"},
    )
    assert upload.status_code == 403


def test_same_origin_write_is_allowed(client):
    response = client.delete("/api/history", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200


def test_unexpected_host_header_is_rejected(client):
    """Ochrona przed DNS rebinding: obca nazwa hosta nie dociera do API."""
    response = client.get("/api/history", headers={"Host": "rebind.attacker.test"})
    assert response.status_code == 400
