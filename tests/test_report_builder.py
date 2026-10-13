from types import SimpleNamespace

import pytest

import report_builder as rb


def test_build_reports_names_missing_oecd_file_and_writes_nothing(tmp_path):
    proc = SimpleNamespace(results={"pisa_context": {"mathematics": {"2022": {"portugal": 472}}},
                                    "pisa_oecd_check": None})
    with pytest.raises(ValueError, match="oecd_pisa2025_table_I1.csv"):
        rb.build_reports(proc, tmp_path)
    assert list(tmp_path.iterdir()) == []
