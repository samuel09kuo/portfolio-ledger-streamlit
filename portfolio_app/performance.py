from __future__ import annotations

from collections import defaultdict

import pandas as pd

from .market_data import symbol_key


def validate_trades(trades: pd.DataFrame) -> list[str]:
    problems: list[str] = []
    if trades.empty:
        return problems
    frame = trades.copy()
    for column, default in [("created_at", ""), ("trade_id", "")]:
        if column not in frame.columns:
            frame[column] = default

    for row in frame.itertuples(index=False):
        if row.action not in {"BUY", "SELL", "SPLIT"}:
            problems.append(f"{row.trade_date} {row.symbol}: 不支援 action={row.action}")
        if row.action in {"BUY", "SELL"} and (row.shares <= 0 or row.price <= 0):
            problems.append(f"{row.trade_date} {row.symbol}: 股數與價格需大於 0")
        if row.market not in {"TW", "US"}:
            problems.append(f"{row.trade_date} {row.symbol}: 不支援 market={row.market}")

    quantities: dict[str, float] = defaultdict(float)
    ordered = frame.sort_values(["trade_date", "created_at", "trade_id"])
    for row in ordered.itertuples(index=False):
        key = symbol_key(row.market, row.symbol)
        if row.action == "BUY":
            quantities[key] += row.shares
        elif row.action == "SELL":
            if quantities[key] <= 0 or row.shares > quantities[key]:
                problems.append(f"{row.trade_date} {row.symbol}: 賣出股數超過持倉，這通常代表匯入的對帳單不是完整歷史。")
            else:
                quantities[key] -= row.shares
        elif row.action == "SPLIT" and quantities[key] > 0 and row.shares > 0:
            quantities[key] *= row.shares
    return problems


def _rate_on_or_before(series: pd.Series, when: pd.Timestamp) -> float:
    if series.empty:
        return 1.0
    aligned = series.loc[:when].dropna()
    if aligned.empty:
        later = series.loc[when:].dropna()
        return float(later.iloc[0]) if not later.empty else 1.0
    return float(aligned.iloc[-1])


def _empty_state() -> dict[str, float]:
    return {
        "quantity": 0.0,
        "cost_local": 0.0,
        "cost_base": 0.0,
        "realized_base": 0.0,
        "fees_local": 0.0,
        "tax_local": 0.0,
    }


def build_current_snapshot(
    trades: pd.DataFrame,
    quotes: pd.DataFrame,
    fx_history: dict[str, pd.Series],
    base_currency: str = "TWD",
) -> tuple[dict[str, float | str | int], pd.DataFrame]:
    if trades.empty:
        empty_summary = {
            "market_value": 0.0,
            "open_cost": 0.0,
            "unrealized_pnl": 0.0,
            "realized_pnl": 0.0,
            "total_pnl": 0.0,
            "holding_count": 0,
            "trade_count": 0,
            "as_of": "",
            "base_currency": base_currency,
        }
        return empty_summary, pd.DataFrame()

    states: dict[str, dict[str, float]] = defaultdict(_empty_state)
    symbol_meta: dict[str, dict[str, str]] = {}
    quote_lookup = quotes.set_index("key").to_dict("index") if not quotes.empty else {}

    for row in trades.sort_values(["trade_date", "created_at", "trade_id"]).itertuples(index=False):
        key = symbol_key(row.market, row.symbol)
        state = states[key]
        symbol_meta[key] = {
            "symbol": row.symbol,
            "market": row.market,
            "name": row.name,
            "currency": row.currency,
        }
        fx_series = fx_history.get(row.currency, pd.Series(dtype=float))
        rate = _rate_on_or_before(fx_series, pd.Timestamp(row.trade_date))

        if row.action == "BUY":
            total_local = row.price * row.shares + row.fee + row.tax
            state["quantity"] += row.shares
            state["cost_local"] += total_local
            state["cost_base"] += total_local * rate
            state["fees_local"] += row.fee
            state["tax_local"] += row.tax
        elif row.action == "SELL":
            if state["quantity"] <= 0 or row.shares > state["quantity"]:
                raise ValueError(f"{row.trade_date} {row.symbol} 賣出股數超過持倉，請先修正台帳。")
            avg_local = state["cost_local"] / state["quantity"]
            avg_base = state["cost_base"] / state["quantity"]
            proceeds_base = (row.price * row.shares - row.fee - row.tax) * rate
            state["realized_base"] += proceeds_base - (avg_base * row.shares)
            state["cost_local"] -= avg_local * row.shares
            state["cost_base"] -= avg_base * row.shares
            state["quantity"] -= row.shares
            state["fees_local"] += row.fee
            state["tax_local"] += row.tax
        elif row.action == "SPLIT":
            if state["quantity"] > 0 and row.shares > 0:
                state["quantity"] *= row.shares

    rows: list[dict] = []
    total_market_value = 0.0
    total_open_cost = 0.0
    total_realized = 0.0
    latest_as_of = ""

    for key, state in states.items():
        if state["quantity"] <= 0:
            total_realized += state["realized_base"]
            continue
        meta = symbol_meta[key]
        quote = quote_lookup.get(key, {})
        last_price = float(quote.get("last_price") or 0.0)
        previous_close = float(quote.get("previous_close") or 0.0)
        latest_as_of = max(latest_as_of, str(quote.get("as_of") or ""))

        fx_series = fx_history.get(meta["currency"], pd.Series(dtype=float))
        latest_rate = float(fx_series.dropna().iloc[-1]) if not fx_series.empty else 1.0
        market_value = state["quantity"] * last_price * latest_rate
        unrealized = market_value - state["cost_base"]
        price_change_pct = None
        if previous_close > 0 and last_price > 0:
            price_change_pct = (last_price / previous_close) - 1.0

        total_market_value += market_value
        total_open_cost += state["cost_base"]
        total_realized += state["realized_base"]

        rows.append(
            {
                "symbol": meta["symbol"],
                "market": meta["market"],
                "name": meta["name"],
                "currency": meta["currency"],
                "quantity": state["quantity"],
                "avg_cost_local": (state["cost_local"] / state["quantity"]) if state["quantity"] else 0.0,
                "open_cost_base": state["cost_base"],
                "last_price": last_price,
                "market_value_base": market_value,
                "unrealized_pnl_base": unrealized,
                "realized_pnl_base": state["realized_base"],
                "fees_local": state["fees_local"],
                "tax_local": state["tax_local"],
                "price_change_pct": price_change_pct,
                "as_of": quote.get("as_of", ""),
            }
        )

    positions = pd.DataFrame(rows)
    if not positions.empty:
        total_mv = positions["market_value_base"].sum()
        positions["weight_pct"] = positions["market_value_base"] / total_mv if total_mv > 0 else 0.0
        positions = positions.sort_values("market_value_base", ascending=False).reset_index(drop=True)

    unrealized = total_market_value - total_open_cost
    summary = {
        "market_value": total_market_value,
        "open_cost": total_open_cost,
        "unrealized_pnl": unrealized,
        "realized_pnl": total_realized,
        "total_pnl": total_realized + unrealized,
        "holding_count": int(len(positions)),
        "trade_count": int(len(trades)),
        "as_of": latest_as_of,
        "base_currency": base_currency,
    }
    return summary, positions


def build_portfolio_history(
    trades: pd.DataFrame,
    price_history: dict[str, pd.Series],
    fx_history: dict[str, pd.Series],
    base_currency: str = "TWD",
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["date", "market_value", "open_cost", "realized_pnl", "unrealized_pnl", "total_pnl"])

    all_dates = set()
    for series in price_history.values():
        all_dates.update(pd.to_datetime(series.index).tolist())
    if not all_dates:
        return pd.DataFrame(columns=["date", "market_value", "open_cost", "realized_pnl", "unrealized_pnl", "total_pnl"])

    dates = pd.DatetimeIndex(sorted(all_dates))
    aligned_prices: dict[str, pd.Series] = {}
    for key, series in price_history.items():
        aligned_prices[key] = pd.to_numeric(series, errors="coerce").reindex(dates).ffill()

    aligned_fx: dict[str, pd.Series] = {}
    for currency, series in fx_history.items():
        aligned_fx[currency] = pd.to_numeric(series, errors="coerce").reindex(dates).ffill().bfill()

    grouped_trades: dict[pd.Timestamp, list] = defaultdict(list)
    currency_by_key = {}
    for row in trades.sort_values(["trade_date", "created_at", "trade_id"]).itertuples(index=False):
        grouped_trades[pd.Timestamp(row.trade_date)].append(row)
        currency_by_key[symbol_key(row.market, row.symbol)] = row.currency

    states: dict[str, dict[str, float]] = defaultdict(_empty_state)
    rows: list[dict] = []

    for current_date in dates:
        for trade in grouped_trades.get(current_date.normalize(), []):
            key = symbol_key(trade.market, trade.symbol)
            state = states[key]
            rate = _rate_on_or_before(aligned_fx.get(trade.currency, pd.Series(dtype=float)), current_date)

            if trade.action == "BUY":
                total_local = trade.price * trade.shares + trade.fee + trade.tax
                state["quantity"] += trade.shares
                state["cost_local"] += total_local
                state["cost_base"] += total_local * rate
                state["realized_base"] += 0.0
            elif trade.action == "SELL":
                if state["quantity"] <= 0 or trade.shares > state["quantity"]:
                    raise ValueError(f"{trade.trade_date} {trade.symbol} 賣出股數超過持倉，請先修正台帳。")
                avg_local = state["cost_local"] / state["quantity"]
                avg_base = state["cost_base"] / state["quantity"]
                proceeds_base = (trade.price * trade.shares - trade.fee - trade.tax) * rate
                state["realized_base"] += proceeds_base - (avg_base * trade.shares)
                state["cost_local"] -= avg_local * trade.shares
                state["cost_base"] -= avg_base * trade.shares
                state["quantity"] -= trade.shares
            elif trade.action == "SPLIT":
                if state["quantity"] > 0 and trade.shares > 0:
                    state["quantity"] *= trade.shares

        market_value = 0.0
        open_cost = 0.0
        realized = 0.0
        for key, state in states.items():
            if state["quantity"] <= 0:
                realized += state["realized_base"]
                continue
            trade_currency = currency_by_key.get(key, base_currency)
            px_series = aligned_prices.get(key, pd.Series(dtype=float))
            fx_series = aligned_fx.get(trade_currency, pd.Series(dtype=float))
            price = float(px_series.loc[current_date]) if current_date in px_series.index and pd.notna(px_series.loc[current_date]) else 0.0
            fx_rate = float(fx_series.loc[current_date]) if current_date in fx_series.index and pd.notna(fx_series.loc[current_date]) else 1.0
            market_value += state["quantity"] * price * fx_rate
            open_cost += state["cost_base"]
            realized += state["realized_base"]

        unrealized = market_value - open_cost
        rows.append(
            {
                "date": current_date,
                "market_value": market_value,
                "open_cost": open_cost,
                "realized_pnl": realized,
                "unrealized_pnl": unrealized,
                "total_pnl": realized + unrealized,
            }
        )

    history = pd.DataFrame(rows)
    if history.empty:
        return history
    history["portfolio_return_pct"] = history["total_pnl"] / history["open_cost"].replace(0, pd.NA)
    return history
