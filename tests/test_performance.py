from __future__ import annotations

import pandas as pd

from portfolio_app.performance import build_current_snapshot, build_portfolio_history, validate_trades


def test_build_current_snapshot_handles_tw_and_us_positions():
    trades = pd.DataFrame(
        [
            {
                "trade_id": "1",
                "trade_date": "2026-04-01",
                "symbol": "2330",
                "market": "TW",
                "name": "台積電",
                "action": "BUY",
                "shares": 1000.0,
                "price": 800.0,
                "fee": 20.0,
                "tax": 0.0,
                "currency": "TWD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-04-01T09:00:00",
            },
            {
                "trade_id": "2",
                "trade_date": "2026-04-02",
                "symbol": "AAPL",
                "market": "US",
                "name": "Apple",
                "action": "BUY",
                "shares": 10.0,
                "price": 190.0,
                "fee": 1.0,
                "tax": 0.0,
                "currency": "USD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-04-02T09:00:00",
            },
        ]
    )
    quotes = pd.DataFrame(
        [
            {
                "key": "TW:2330",
                "last_price": 820.0,
                "previous_close": 810.0,
                "as_of": "2026-04-29 13:20:00",
            },
            {
                "key": "US:AAPL",
                "last_price": 200.0,
                "previous_close": 198.0,
                "as_of": "2026-04-29 09:30:00",
            },
        ]
    )
    idx = pd.to_datetime(["2026-04-01", "2026-04-02", "2026-04-29"])
    fx_history = {
        "TWD": pd.Series([1.0, 1.0, 1.0], index=idx),
        "USD": pd.Series([31.5, 31.6, 31.8], index=idx),
    }

    summary, positions = build_current_snapshot(trades, quotes, fx_history, "TWD")

    assert summary["holding_count"] == 2
    assert positions.iloc[0]["market_value_base"] > 0
    assert summary["market_value"] > summary["open_cost"]
    assert positions["market_value_base"].sum() < positions["gross_market_value_base"].sum()


def test_build_portfolio_history_tracks_realized_and_unrealized():
    trades = pd.DataFrame(
        [
            {
                "trade_id": "1",
                "trade_date": "2026-04-01",
                "symbol": "2330",
                "market": "TW",
                "name": "台積電",
                "action": "BUY",
                "shares": 100.0,
                "price": 100.0,
                "fee": 0.0,
                "tax": 0.0,
                "currency": "TWD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-04-01T09:00:00",
            },
            {
                "trade_id": "2",
                "trade_date": "2026-04-03",
                "symbol": "2330",
                "market": "TW",
                "name": "台積電",
                "action": "SELL",
                "shares": 40.0,
                "price": 120.0,
                "fee": 0.0,
                "tax": 0.0,
                "currency": "TWD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-04-03T09:00:00",
            },
        ]
    )
    idx = pd.to_datetime(["2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04"])
    price_history = {
        "TW:2330": pd.Series([100.0, 110.0, 120.0, 125.0], index=idx),
    }
    fx_history = {
        "TWD": pd.Series([1.0, 1.0, 1.0, 1.0], index=idx),
    }

    history = build_portfolio_history(trades, price_history, fx_history, "TWD")

    assert not history.empty
    assert history.iloc[-1]["realized_pnl"] == 800.0
    assert history.iloc[-1]["unrealized_pnl"] == 1500.0


def test_validate_trades_flags_sell_that_exceeds_holdings():
    trades = pd.DataFrame(
        [
            {
                "trade_date": "2026-04-08",
                "symbol": "00631L",
                "market": "TW",
                "name": "元大台灣50正2",
                "action": "SELL",
                "shares": 1000.0,
                "price": 30.0,
                "fee": 10.0,
                "tax": 0.0,
                "currency": "TWD",
                "created_at": "2026-04-08T09:00:00",
            }
        ]
    )

    problems = validate_trades(trades)

    assert any("賣出股數超過持倉" in problem for problem in problems)


def test_validate_trades_allows_00631l_sell_after_known_split():
    trades = pd.DataFrame(
        [
            {
                "trade_id": "1",
                "trade_date": "2026-03-24",
                "symbol": "00631L",
                "market": "TW",
                "name": "元大台灣50正2",
                "action": "BUY",
                "shares": 570.0,
                "price": 140.0,
                "fee": 0.0,
                "tax": 0.0,
                "currency": "TWD",
                "created_at": "2026-03-24T09:00:00",
            },
            {
                "trade_id": "2",
                "trade_date": "2026-04-08",
                "symbol": "00631L",
                "market": "TW",
                "name": "元大台灣50正2",
                "action": "SELL",
                "shares": 1000.0,
                "price": 30.0,
                "fee": 10.0,
                "tax": 0.0,
                "currency": "TWD",
                "created_at": "2026-04-08T09:00:00",
            },
        ]
    )

    problems = validate_trades(trades)

    assert not any("賣出股數超過持倉" in problem for problem in problems)


def test_build_current_snapshot_applies_known_00631l_split():
    trades = pd.DataFrame(
        [
            {
                "trade_id": "1",
                "trade_date": "2026-03-24",
                "symbol": "00631L",
                "market": "TW",
                "name": "元大台灣50正2",
                "action": "BUY",
                "shares": 570.0,
                "price": 140.0,
                "fee": 0.0,
                "tax": 0.0,
                "currency": "TWD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-03-24T09:00:00",
            },
            {
                "trade_id": "2",
                "trade_date": "2026-04-08",
                "symbol": "00631L",
                "market": "TW",
                "name": "元大台灣50正2",
                "action": "SELL",
                "shares": 1000.0,
                "price": 30.0,
                "fee": 10.0,
                "tax": 0.0,
                "currency": "TWD",
                "order_id": "",
                "broker": "",
                "account": "",
                "source": "manual",
                "note": "",
                "created_at": "2026-04-08T09:00:00",
            },
        ]
    )
    quotes = pd.DataFrame(
        [
            {
                "key": "TW:00631L",
                "last_price": 28.0,
                "previous_close": 27.5,
                "as_of": "2026-04-29 13:20:00",
            }
        ]
    )
    idx = pd.to_datetime(["2026-03-24", "2026-03-31", "2026-04-08", "2026-04-29"])
    fx_history = {
        "TWD": pd.Series([1.0, 1.0, 1.0, 1.0], index=idx),
    }

    summary, positions = build_current_snapshot(trades, quotes, fx_history, "TWD")

    assert summary["holding_count"] == 1
    assert positions.iloc[0]["quantity"] == 11540.0
