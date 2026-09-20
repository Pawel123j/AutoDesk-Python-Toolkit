"""
Testy warstwy przetwarzania danych.

To jest sedno tego projektu: użytkownik wrzuca plik CSV i dostaje z powrotem
„posprzątane" dane. Błąd tutaj nie wywala aplikacji — zwraca dane, które
wyglądają poprawnie, a nie są. Tego rodzaju błąd wychodzi najpóźniej.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest
from app.services import (
    build_html_report,
    build_report,
    build_text_report,
    calculate_report_stats,
    categorize_file_names,
    clean_csv,
    dataframe_preview,
    make_generated_path,
    normalize_column_names,
    sanitize_original_filename,
    to_json_safe,
)

# ── normalizacja nazw kolumn ────────────────────────────────────────────

class TestNormalizeColumnNames:
    def test_sprowadza_do_malych_liter_i_podkreslen(self):
        result = normalize_column_names(pd.Index(["First Name", "E-mail Address", "  Age  "]))
        assert result == ["first_name", "e_mail_address", "age"]

    def test_usuwa_znaki_specjalne(self):
        result = normalize_column_names(pd.Index(["Price ($)", "Qty #", "Ratio %"]))
        assert result == ["price", "qty", "ratio"]

    def test_obcina_podkreslenia_z_brzegow(self):
        assert normalize_column_names(pd.Index(["__name__"])) == ["name"]

    def test_kolumna_bez_znakow_alfanumerycznych_dostaje_nazwe_zastepcza(self):
        # Pusta nazwa kolumny zepsułaby zapis do Excela i odwołania w kodzie.
        assert normalize_column_names(pd.Index(["###", "  "])) == ["column", "column_2"]

    def test_duplikaty_dostaja_numerowane_przyrostki(self):
        # To jest ważniejsze, niż wygląda: dwie kolumny o tej samej nazwie
        # sprawiłyby, że jedna po cichu przesłania drugą przy konwersji
        # do słownika — dane znikają bez żadnego komunikatu.
        result = normalize_column_names(pd.Index(["Name", "name", "NAME"]))
        assert result == ["name", "name_2", "name_3"]
        assert len(set(result)) == 3

    def test_rozne_nazwy_zbiegajace_sie_do_jednej_tez_sa_rozroznione(self):
        result = normalize_column_names(pd.Index(["First Name", "first-name", "FIRST_NAME"]))
        assert len(set(result)) == 3

    def test_wynik_zawsze_jest_unikalny_dla_dowolnego_wejscia(self):
        columns = pd.Index(["a", "A", "a!", "!a", "a_2", "a 2", "###", "  ", ""])
        result = normalize_column_names(columns)
        assert len(result) == len(columns)
        assert len(set(result)) == len(result)


# ── czyszczenie CSV ─────────────────────────────────────────────────────

class TestCleanCsv:
    def test_usuwa_wiersze_calkowicie_puste(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", None, "z"]})
        result = clean_csv(df)

        assert result["original_rows"] == 3
        assert result["empty_rows_removed"] == 1
        assert result["cleaned_rows"] == 2

    def test_nie_usuwa_wiersza_czesciowo_wypelnionego(self):
        # `dropna(how="all")`, nie `how="any"` — wiersz z jedną brakującą
        # wartością to nadal dane użytkownika.
        df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
        result = clean_csv(df)

        assert result["empty_rows_removed"] == 0
        assert result["cleaned_rows"] == 2

    def test_usuwa_duplikaty(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        result = clean_csv(df)

        assert result["duplicate_rows_removed"] == 1
        assert result["cleaned_rows"] == 2

    def test_wiersz_rozniacy_sie_jedna_kolumna_nie_jest_duplikatem(self):
        df = pd.DataFrame({"a": [1, 1], "b": ["x", "y"]})
        assert clean_csv(df)["duplicate_rows_removed"] == 0

    def test_normalizuje_nazwy_kolumn(self):
        df = pd.DataFrame({"First Name": ["a"], "E-mail": ["b"]})
        assert clean_csv(df)["columns"] == ["first_name", "e_mail"]

    def test_liczby_sie_zgadzaja(self):
        # Niezmiennik: wiersze wyjściowe = wejściowe minus usunięte.
        df = pd.DataFrame({"a": [1, 1, None, 2, None], "b": ["x", "x", None, "y", None]})
        r = clean_csv(df)

        assert r["cleaned_rows"] == r["original_rows"] - r["empty_rows_removed"] - r["duplicate_rows_removed"]

    def test_nie_modyfikuje_ramki_wejsciowej(self):
        # Wołający może chcieć użyć oryginału później — np. do porównania.
        df = pd.DataFrame({"First Name": [1, 1]})
        before = list(df.columns)
        clean_csv(df)
        assert list(df.columns) == before

    def test_pusta_ramka_nie_wybucha(self):
        result = clean_csv(pd.DataFrame())
        assert result["original_rows"] == 0
        assert result["cleaned_rows"] == 0
        assert result["preview"] == []

    def test_indeks_jest_przenumerowany_od_zera(self):
        df = pd.DataFrame({"a": [1, None, 3]})
        assert list(clean_csv(df)["dataframe"].index) == [0, 1]


# ── podgląd i bezpieczna serializacja ───────────────────────────────────

class TestPreview:
    def test_ogranicza_liczbe_wierszy(self):
        df = pd.DataFrame({"a": range(100)})
        assert len(dataframe_preview(df, limit=5)) == 5

    def test_zamienia_brakujace_wartosci_na_none(self):
        # NaN nie jest poprawnym JSON-em — przeszedłby do frontendu jako
        # `NaN` i wywalił parsowanie odpowiedzi.
        df = pd.DataFrame({"a": [1.0, None]})
        preview = dataframe_preview(df)
        assert preview[1]["a"] is None

    def test_wartosci_sa_typami_pythona_a_nie_numpy(self):
        df = pd.DataFrame({"a": [1, 2], "b": [1.5, 2.5]})
        for row in dataframe_preview(df):
            assert type(row["a"]) is int
            assert type(row["b"]) is float


class TestToJsonSafe:
    def test_nan_staje_sie_none(self):
        assert to_json_safe(float("nan")) is None

    def test_none_zostaje_none(self):
        assert to_json_safe(None) is None

    def test_timestamp_staje_sie_napisem_iso(self):
        assert to_json_safe(pd.Timestamp("2026-09-20")) == "2026-09-20T00:00:00"

    def test_zwykle_wartosci_przechodza_bez_zmian(self):
        assert to_json_safe("tekst") == "tekst"
        assert to_json_safe(True) is True

    def test_nieskonczonosc_przechodzi_bez_zmian(self):
        # Udokumentowanie stanu faktycznego: inf NIE jest zamieniany na None,
        # w odróżnieniu od NaN. Gdyby kiedyś trafił do danych, JSON go nie
        # zniesie — ten test pokaże, gdzie szukać.
        assert math.isinf(to_json_safe(float("inf")))


# ── statystyki i raporty ────────────────────────────────────────────────

class TestReportStats:
    def test_liczy_wiersze_kolumny_i_braki(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
        stats = calculate_report_stats(df)

        assert stats["row_count"] == 3
        assert stats["column_count"] == 2
        assert stats["missing_values"] == {"a": 1, "b": 1}

    def test_srednie_liczy_tylko_dla_kolumn_liczbowych(self):
        df = pd.DataFrame({"liczby": [2, 4], "tekst": ["a", "b"]})
        stats = calculate_report_stats(df)

        assert stats["numeric_averages"] == {"liczby": 3.0}
        assert "tekst" not in stats["numeric_averages"]

    def test_kolumna_liczbowa_z_samymi_brakami_daje_none_a_nie_nan(self):
        df = pd.DataFrame({"pusta": [None, None]}, dtype="float64")
        assert calculate_report_stats(df)["numeric_averages"]["pusta"] is None

    def test_srednia_pomija_braki(self):
        df = pd.DataFrame({"a": [2.0, None, 4.0]})
        assert calculate_report_stats(df)["numeric_averages"]["a"] == 3.0


class TestReports:
    df = pd.DataFrame({"kwota": [10, 20], "nazwa": ["a", None]})

    def test_raport_tekstowy_zawiera_nazwe_pliku_i_liczby(self):
        report = build_text_report("dane.csv", calculate_report_stats(self.df))

        assert "dane.csv" in report
        assert "Row count: 2" in report
        assert "Column count: 2" in report

    def test_raport_tekstowy_informuje_o_braku_kolumn_liczbowych(self):
        stats = calculate_report_stats(pd.DataFrame({"tekst": ["a"]}))
        assert "No numeric columns detected." in build_text_report("x.csv", stats)

    def test_raport_html_escapuje_nazwe_pliku(self):
        # Nazwa pliku pochodzi od użytkownika i trafia wprost do HTML-a.
        # Bez escapowania byłoby to XSS w wygenerowanym raporcie.
        stats = calculate_report_stats(self.df)
        report = build_html_report("<script>alert(1)</script>.csv", stats)

        assert "<script>alert(1)</script>" not in report
        assert "&lt;script&gt;" in report

    def test_raport_html_escapuje_nazwy_kolumn(self):
        df = pd.DataFrame({"<img onerror=x>": [1]})
        report = build_html_report("ok.csv", calculate_report_stats(df))

        assert "<img onerror=x>" not in report
        assert "&lt;img" in report

    @pytest.mark.parametrize("fmt,marker", [("txt", "AutoDesk Python Toolkit Report"), ("html", "<!doctype html>")])
    def test_build_report_wybiera_format(self, fmt, marker):
        assert marker in build_report(self.df, "dane.csv", fmt)


# ── kategoryzacja plików ────────────────────────────────────────────────

class TestCategorizeFileNames:
    def test_rozpoznaje_kazda_kategorie(self):
        result = categorize_file_names(["a.png", "b.pdf", "c.csv", "d.zip", "e.exe"])

        assert result["Images"] == ["a.png"]
        assert result["Documents"] == ["b.pdf"]
        assert result["Spreadsheets"] == ["c.csv"]
        assert result["Archives"] == ["d.zip"]
        assert result["Other"] == ["e.exe"]

    def test_rozszerzenie_bez_wzgledu_na_wielkosc_liter(self):
        assert categorize_file_names(["FOTO.PNG"])["Images"] == ["FOTO.PNG"]

    def test_pomija_puste_nazwy_i_same_biale_znaki(self):
        result = categorize_file_names(["", "   ", "a.png"])
        assert sum(len(v) for v in result.values()) == 1

    def test_plik_bez_rozszerzenia_trafia_do_other(self):
        assert categorize_file_names(["README"])["Other"] == ["README"]

    def test_zawsze_zwraca_komplet_kategorii(self):
        # Frontend renderuje wszystkie pięć sekcji — brakujący klucz
        # wywaliłby widok.
        result = categorize_file_names([])
        assert set(result) == {"Images", "Documents", "Spreadsheets", "Archives", "Other"}

    def test_zadna_nazwa_nie_ginie_i_zadna_nie_dubluje_sie(self):
        names = ["a.png", "b.PDF", "c.csv", "d.7z", "e", "f.xyz"]
        result = categorize_file_names(names)
        flat = [n for group in result.values() for n in group]

        assert sorted(flat) == sorted(names)


# ── nazwy plików ────────────────────────────────────────────────────────

class TestFileNames:
    def test_sanitize_obcina_sciezke(self):
        # Klasyczne przejście po katalogach: bez tego nazwa "../../etc/passwd"
        # trafiłaby do ścieżki zapisu.
        assert sanitize_original_filename("../../etc/passwd") == "passwd"
        assert sanitize_original_filename("/tmp/dane.csv") == "dane.csv"

    def test_sanitize_odrzuca_brak_nazwy(self):
        from fastapi import HTTPException

        for value in (None, ""):
            with pytest.raises(HTTPException):
                sanitize_original_filename(value)

    def test_make_generated_path_tworzy_katalog(self, tmp_path):
        target = tmp_path / "generated"
        path, name = make_generated_path(target, "dane.csv", ".xlsx")

        assert target.is_dir()
        assert path.parent == target
        assert name.endswith(".xlsx")

    def test_make_generated_path_czysci_nazwe_i_dokleja_losowy_przyrostek(self, tmp_path):
        _, name = make_generated_path(tmp_path, "Moje Dane (2026)!.csv", ".xlsx")

        assert name.startswith("Moje-Dane-2026")
        assert " " not in name

    def test_make_generated_path_daje_rozne_nazwy_przy_tym_samym_wejsciu(self, tmp_path):
        # Bez losowego przyrostka drugi użytkownik nadpisałby plik pierwszego.
        _, first = make_generated_path(tmp_path, "dane.csv", ".xlsx")
        _, second = make_generated_path(tmp_path, "dane.csv", ".xlsx")

        assert first != second

    def test_make_generated_path_radzi_sobie_z_nazwa_bez_dozwolonych_znakow(self, tmp_path):
        _, name = make_generated_path(tmp_path, "###.csv", ".txt")
        assert name.startswith("processed-")
