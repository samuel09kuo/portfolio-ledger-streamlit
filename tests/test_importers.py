from __future__ import annotations

import pytest

from portfolio_app.importers import (
    detect_cathay_statement_notice,
    lookup_tw_symbol_by_name,
    parse_cathay_csv,
)


def test_parse_cathay_csv_supports_cp950_encoded_statement():
    text = (
        "前言\n"
        "日期,股名,股號,買賣別,成交股數,成交價,手續費,交易稅,委託書號\n"
        "2026/04/29,台積電,2330,現買,\"1,000\",900,4,0,A001\n"
    )

    rows = parse_cathay_csv(text.encode("cp950"))

    assert len(rows) == 1
    assert rows[0]["symbol"] == "2330"
    assert rows[0]["action"] == "BUY"


def test_parse_cathay_csv_resolves_symbol_from_name_when_statement_has_no_code(monkeypatch: pytest.MonkeyPatch):
    text = (
        "前言\n"
        "股名,日期,成交股數,淨收付金額,買賣別,成交價,成本,手續費,交易稅,委託書號\n"
        "台積電,2026/04/29,\"1,000\",\"-900,004\",現買,900,\"900,000\",4,0,A001\n"
    )

    monkeypatch.setattr(
        "portfolio_app.importers.lookup_tw_symbol_by_name",
        lambda name: "2330" if name == "台積電" else "",
    )

    rows = parse_cathay_csv(text.encode("utf-8-sig"))

    assert len(rows) == 1
    assert rows[0]["symbol"] == "2330"
    assert rows[0]["name"] == "台積電"


def test_lookup_tw_symbol_by_name_uses_bundled_lookup_file():
    assert lookup_tw_symbol_by_name("台積電") == "2330"


def test_detect_cathay_statement_notice_returns_partial_export_banner():
    text = (
        "根據您篩選的結果，總計有81筆資料，當前資料為1-50筆，看更多請至國泰證券app查詢\n"
        "股名,日期,成交股數\n"
    )

    notice = detect_cathay_statement_notice(text.encode("utf-8-sig"))

    assert notice == "根據您篩選的結果，總計有81筆資料，當前資料為1-50筆，看更多請至國泰證券app查詢"
