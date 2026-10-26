import os
import sys
from pathlib import Path

from accessibility import assert_accessible
from browser_support import application, browser, static_site
from playwright.sync_api import expect

REPO = Path(__file__).resolve().parents[1]


def test_autodesk_csv_history(tmp_path):
    with static_site(REPO / "frontend/dist") as url:
        env = {
            "AUTODESK_DATA_DIR": str(tmp_path / "data"),
            "AUTODESK_GENERATED_DIR": str(tmp_path / "generated"),
            "CORS_ORIGINS": url,
        }
        with (
            application(
                "autodesk",
                [
                    os.environ.get("E2E_API_PYTHON", sys.executable),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "18320",
                ],
                REPO / "backend",
                "http://127.0.0.1:18320/api/health",
                env,
            ),
            browser() as b,
        ):
            page = b.new_page(viewport={"width": 390, "height": 844})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            assert_accessible(page, REPO, "home")
            page.get_by_role("button", name="CSV Cleaner", exact=True).click()
            page.locator("#cleaner-file").set_input_files(
                {
                    "name": "regression.csv",
                    "mimeType": "text/csv",
                    "buffer": b"Name,Amount\nAlice,10\nAlice,10\nBob,20\n",
                }
            )
            page.get_by_role("button", name="Clean CSV", exact=True).click()
            expect(page.get_by_text("Duplicates removed", exact=True).locator("..")).to_contain_text("1")
            expect(page.get_by_text("Cleaned rows", exact=True).locator("..")).to_contain_text("2")
            assert_accessible(page, REPO, "current-tool")
            page.get_by_role("button", name="History", exact=True).click()
            expect(page.get_by_role("cell", name="regression.csv")).to_be_visible()
            page.reload()
            assert_accessible(page, REPO, "current-tool")
            page.get_by_role("button", name="History", exact=True).click()
            expect(page.get_by_role("cell", name="regression.csv")).to_be_visible()
            assert (tmp_path / "data/toolkit.db").exists()

            fixture = {
                "name": "exports.csv", "mimeType": "text/csv",
                "buffer": b"Name,Amount\nAlice,10\nBob,20\n",
            }
            page.get_by_role("button", name="CSV to Excel", exact=True).click()
            page.locator("#converter-file").set_input_files(fixture)
            with page.expect_download() as download:
                page.get_by_role("button", name="Convert and Download", exact=True).click()
            workbook = Path(download.value.path())
            from zipfile import ZipFile
            with ZipFile(workbook) as archive:
                assert "xl/workbook.xml" in archive.namelist()
            page.get_by_role("button", name="Reports", exact=True).click()
            page.locator("#report-file").set_input_files(fixture)
            for report_format in ["txt", "html"]:
                page.get_by_role("button", name=report_format.upper(), exact=True).click()
                with page.expect_download() as download:
                    page.get_by_role("button", name="Generate Report", exact=True).click()
                assert "Amount" in Path(download.value.path()).read_text()
            assert list((tmp_path / "generated").iterdir()) == []
            page.get_by_role("button", name="File Sorter", exact=True).click()
            page.locator("textarea").fill("photo.png, budget.xlsx, archive.zip")
            page.get_by_role("button", name="Sort File Names", exact=True).click()
            expect(page.get_by_text("photo.png", exact=True)).to_be_visible()
            assert_accessible(page, REPO, "current-tool")
            page.get_by_role("button", name="History", exact=True).click()
            expect(page.get_by_role("row")).to_have_count(6)
            page.get_by_role("button", name="Clear", exact=True).click()
            expect(page.get_by_text("No processing history yet.", exact=True)).to_be_visible()
            assert_accessible(page, REPO, "empty-history")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not errors, errors
