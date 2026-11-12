import csv
from io import BytesIO, StringIO

import pandas as pd
import pytest
from app import database, main
from fastapi.testclient import TestClient
from openpyxl import load_workbook


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "data/toolkit.db")
    monkeypatch.setattr(main, "GENERATED_DIR", tmp_path / "generated")
    with TestClient(main.app) as test_client:
        yield test_client


def test_non_finite_csv_values_produce_valid_json(client):
    response = client.post("/api/csv/clean", files={"file": ("values.csv", b"amount\ninf\n-inf\n2\n")})
    assert response.status_code == 200
    assert response.json()["preview"] == [{"amount": None}, {"amount": None}, {"amount": 2.0}]


@pytest.mark.parametrize("text", [
    "=1+1", "+1+1", "-1+1", "@SUM(1)", " =1+1", "\t=1+1", "\r=1+1", "Zażółć gęślą",
])
def test_excel_preserves_untrusted_cells_and_headers_as_text(client, text):
    source = StringIO(newline="")
    writer = csv.writer(source)
    writer.writerow([text, "amount"])
    writer.writerow([text, -12.5])
    response = client.post("/api/csv/to-excel", files={"file": ("values.csv", source.getvalue().encode())})
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.content), data_only=False)
    sheet = workbook.active
    for address in ["A1", "A2"]:
        # XML readers normalize literal CR to LF in openpyxl's XML output.
        assert sheet[address].value == text.replace("\r", "\n")
        assert sheet[address].data_type == "s"
    assert sheet["B2"].value == -12.5
    assert sheet["B2"].data_type == "n"
    workbook.close()
    assert len(client.get("/api/history").json()["items"]) == 1
    assert list(main.GENERATED_DIR.iterdir()) == []


@pytest.mark.parametrize("endpoint,target", [
    ("/api/csv/to-excel", "excel"), ("/api/reports/generate", "report"),
])
def test_processing_failure_does_not_expose_server_details(client, monkeypatch, endpoint, target):
    def fail(*args, **kwargs):
        raise OSError("private-server-path-and-sensitive-value")

    if target == "excel":
        monkeypatch.setattr(pd.DataFrame, "to_excel", fail)
    else:
        monkeypatch.setattr(main, "build_report", fail)
    response = client.post(endpoint, files={"file": ("input.csv", b"amount\n1\n")})
    assert response.status_code == 500
    assert "private-server-path" not in response.text
    assert client.get("/api/history").json()["items"] == []
    assert list(main.GENERATED_DIR.iterdir()) == []


@pytest.mark.parametrize("endpoint,prefix", [
    ("/api/csv/to-excel", b"PK"),
    ("/api/reports/generate?format=html", b"<!DOCTYPE"),
    ("/api/reports/generate?format=txt", b"Report"),
])
def test_download_is_complete_and_only_request_export_is_cleaned(client, endpoint, prefix):
    existing = main.GENERATED_DIR / "existing-user-file.txt"
    existing.write_text("keep this file")
    response = client.post(endpoint, files={"file": ("input.csv", b"amount\n1\n2\n")})
    assert response.status_code == 200
    assert len(response.content) > 20
    if prefix == b"PK":
        from io import BytesIO
        from zipfile import ZipFile
        with ZipFile(BytesIO(response.content)) as archive:
            assert "xl/workbook.xml" in archive.namelist()
    else:
        assert "amount" in response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "attachment" in response.headers["Content-Disposition"]
    assert list(main.GENERATED_DIR.iterdir()) == [existing]
    assert existing.read_text() == "keep this file"
    assert len(client.get("/api/history").json()["items"]) == 1
