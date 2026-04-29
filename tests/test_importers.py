from __future__ import annotations

from portfolio_app.importers import parse_cathay_csv


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
