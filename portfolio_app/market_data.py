from __future__ import annotations

import time
from functools import lru_cache

import pandas as pd
import yfinance as yf

from .importers import infer_currency


def symbol_key(market: str, symbol: str) -> str:
    return f"{market.upper()}:{symbol.upper()}"


def build_symbol_catalog(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["key", "symbol", "market", "name", "currency", "yahoo_symbol"])
    catalog = (
        trades.sort_values(["trade_date", "created_at"])
        .drop_duplicates(subset=["market", "symbol"], keep="last")
        [["symbol", "market", "name", "currency"]]
        .copy()
    )
    catalog["currency"] = catalog["currency"].fillna("")
    catalog["currency"] = catalog["currency"].where(catalog["currency"] != "", catalog["market"].map(infer_currency))
    catalog["key"] = catalog.apply(lambda row: symbol_key(row["market"], row["symbol"]), axis=1)
    catalog["yahoo_symbol"] = catalog.apply(lambda row: resolve_yahoo_symbol(row["symbol"], row["market"]), axis=1)
    return catalog.reset_index(drop=True)


def _ticker_candidates(symbol: str, market: str) -> list[str]:
    clean_symbol = str(symbol).strip().upper()
    clean_market = str(market).strip().upper()
    if clean_market == "TW":
        if clean_symbol.endswith(".TW") or clean_symbol.endswith(".TWO"):
            return [clean_symbol]
        return [f"{clean_symbol}.TW", f"{clean_symbol}.TWO"]
    return [clean_symbol]


@lru_cache(maxsize=512)
def resolve_yahoo_symbol(symbol: str, market: str) -> str:
    for candidate in _ticker_candidates(symbol, market):
        try:
            hist = yf.Ticker(candidate).history(period="5d", interval="1d", auto_adjust=True)
            if not hist.empty:
                return candidate
        except Exception:
            continue
    return _ticker_candidates(symbol, market)[0]


@lru_cache(maxsize=2048)
def _download_history_cached(yahoo_symbol: str, start_date: str, end_date: str) -> pd.Series:
    history = yf.Ticker(yahoo_symbol).history(
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=True,
    )
    if history.empty:
        return pd.Series(dtype=float)
    series = history["Close"].rename(yahoo_symbol).astype(float)
    series.index = pd.to_datetime(series.index).tz_localize(None)
    return series.sort_index()


def fetch_price_history(catalog: pd.DataFrame, start_date: str, end_date: str) -> dict[str, pd.Series]:
    history: dict[str, pd.Series] = {}
    for row in catalog.itertuples(index=False):
        series = _download_history_cached(row.yahoo_symbol, start_date, end_date)
        history[row.key] = series
    return history


@lru_cache(maxsize=64)
def _current_quote_cached(yahoo_symbol: str, cache_bucket: int) -> dict:
    ticker = yf.Ticker(yahoo_symbol)
    try:
        fast = dict(ticker.fast_info)
    except Exception:
        fast = {}

    last_price = float(fast.get("lastPrice") or 0.0)
    previous_close = float(
        fast.get("previousClose")
        or fast.get("regularMarketPreviousClose")
        or 0.0
    )
    currency = str(fast.get("currency") or "").upper()

    if last_price <= 0:
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if not hist.empty:
            last_price = float(hist["Close"].dropna().iloc[-1])
            if len(hist) >= 2:
                previous_close = float(hist["Close"].dropna().iloc[-2])

    change_pct = None
    if previous_close > 0 and last_price > 0:
        change_pct = (last_price / previous_close) - 1.0

    return {
        "last_price": last_price,
        "previous_close": previous_close,
        "currency": currency,
        "change_pct": change_pct,
        "as_of": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_current_quotes(catalog: pd.DataFrame, ttl_seconds: int = 30) -> pd.DataFrame:
    if catalog.empty:
        return pd.DataFrame(columns=["key", "last_price", "previous_close", "change_pct", "as_of"])

    cache_bucket = int(time.time() // max(ttl_seconds, 1))
    rows = []
    for row in catalog.itertuples(index=False):
        quote = _current_quote_cached(row.yahoo_symbol, cache_bucket)
        rows.append(
            {
                "key": row.key,
                "symbol": row.symbol,
                "market": row.market,
                "name": row.name,
                "currency": row.currency,
                "yahoo_symbol": row.yahoo_symbol,
                **quote,
            }
        )
    return pd.DataFrame(rows)


@lru_cache(maxsize=256)
def _fx_history_cached(pair: str, start_date: str, end_date: str) -> pd.Series:
    history = yf.Ticker(pair).history(start=start_date, end=end_date, interval="1d", auto_adjust=True)
    if history.empty:
        return pd.Series(dtype=float)
    series = history["Close"].rename(pair).astype(float)
    series.index = pd.to_datetime(series.index).tz_localize(None)
    return series.sort_index()


def fetch_fx_history(currencies: set[str], start_date: str, end_date: str, base_currency: str) -> dict[str, pd.Series]:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    dates = pd.date_range(start, end, freq="B")
    base = base_currency.upper()
    fx_map: dict[str, pd.Series] = {base: pd.Series(1.0, index=dates)}

    needs_usd_twd = (
        ("USD" in currencies and base == "TWD")
        or ("TWD" in currencies and base == "USD")
    )
    usd_twd = None
    if needs_usd_twd:
        usd_twd = _fx_history_cached("USDTWD=X", start_date, end_date).reindex(dates).ffill().bfill()

    for currency in currencies:
        cur = currency.upper()
        if cur == base:
            continue
        if cur == "USD" and base == "TWD" and usd_twd is not None:
            fx_map[cur] = usd_twd
        elif cur == "TWD" and base == "USD" and usd_twd is not None:
            fx_map[cur] = (1.0 / usd_twd).replace([pd.NA, pd.NaT], float("nan")).ffill().bfill()
        else:
            fx_map[cur] = pd.Series(1.0, index=dates)
    return fx_map


def latest_fx_rates(fx_history: dict[str, pd.Series], base_currency: str) -> dict[str, float]:
    rates: dict[str, float] = {base_currency.upper(): 1.0}
    for currency, series in fx_history.items():
        if series.empty:
            rates[currency] = 1.0
        else:
            rates[currency] = float(series.dropna().iloc[-1])
    return rates
