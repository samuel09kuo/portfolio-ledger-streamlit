from __future__ import annotations

import io
import re
from functools import lru_cache
from datetime import date

import pandas as pd
import requests

from .models import MARKET_TO_CURRENCY

_CATHAY_FEE_RATE = 0.001425 * 0.28
_CATHAY_TAX_COLS = ["交易稅", "證交稅", "稅額", "稅費"]
_BUY_WORDS = ("現買", "零股買", "買進", "融資買進", "BUY", "B")
_SELL_WORDS = ("現賣", "零股賣", "賣出", "融資賣出", "SELL", "S")


def _decode_csv_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp950", "big5", "utf-8"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8-sig", errors="ignore")


def normalize_symbol(symbol: object) -> str:
    text = str(symbol or "").strip().upper()
    text = text.replace(".TW", "").replace(".TWO", "")
    return re.sub(r"[^A-Z0-9]", "", text)


def infer_market(symbol: str, market: str | None = None) -> str:
    if market:
        return str(market).strip().upper()
    return "TW" if symbol.isdigit() else "US"


def infer_currency(market: str) -> str:
    return MARKET_TO_CURRENCY.get(market.upper(), "TWD")


def build_manual_trade(
    *,
    trade_date: date,
    symbol: str,
    market: str,
    action: str,
    shares: float,
    price: float,
    fee: float = 0.0,
    tax: float = 0.0,
    name: str = "",
    order_id: str = "",
    broker: str = "",
    account: str = "",
    note: str = "",
    source: str = "manual",
) -> dict:
    clean_symbol = normalize_symbol(symbol)
    clean_market = infer_market(clean_symbol, market)
    return {
        "trade_date": pd.Timestamp(trade_date).strftime("%Y-%m-%d"),
        "symbol": clean_symbol,
        "market": clean_market,
        "name": name.strip(),
        "action": action.strip().upper(),
        "shares": float(shares),
        "price": float(price),
        "fee": float(fee),
        "tax": float(tax),
        "currency": infer_currency(clean_market),
        "order_id": order_id.strip(),
        "broker": broker.strip(),
        "account": account.strip(),
        "source": source,
        "note": note.strip(),
    }


def _parse_optional_number(value: object, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    text = str(value).replace(",", "").strip()
    if not text:
        return default
    return float(text)


def _fallback_cathay_fee(price: float, shares: float) -> float:
    notional = price * shares
    if notional <= 0:
        return 0.0
    return float(max(1, int(notional * _CATHAY_FEE_RATE)))


def _resolve_action(text: object) -> str | None:
    value = str(text or "").strip().upper()
    if any(word in value for word in _BUY_WORDS):
        return "BUY"
    if any(word in value for word in _SELL_WORDS):
        return "SELL"
    return None


def _public_get_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.exceptions.SSLError:
        response = requests.get(url, timeout=20, verify=False)
        response.raise_for_status()
        return response.text


@lru_cache(maxsize=1)
def _load_tw_name_symbol_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for mode in (2, 4, 5):
        html = _public_get_text(f"https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}")
        tables = pd.read_html(io.StringIO(html), flavor="lxml")
        if not tables:
            continue
        table = tables[0]
        table.columns = table.iloc[0]
        table = table.iloc[1:].copy()
        security_col = next((column for column in table.columns if "有價證券代號及名稱" in str(column)), None)
        if security_col is None:
            continue
        for value in table[security_col].dropna().astype(str):
            text = value.strip()
            if "　" in text:
                symbol, name = text.split("　", 1)
            elif " " in text:
                symbol, name = text.split(" ", 1)
            else:
                continue
            clean_symbol = normalize_symbol(symbol)
            clean_name = name.strip()
            if clean_symbol and clean_name:
                lookup.setdefault(clean_name, clean_symbol)
    return lookup


def lookup_tw_symbol_by_name(name: object) -> str:
    clean_name = str(name or "").strip()
    if not clean_name:
        return ""
    return _load_tw_name_symbol_lookup().get(clean_name, "")


def parse_cathay_csv(content: bytes) -> list[dict]:
    text = _decode_csv_bytes(content)
    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if "股名" in line or "股票名稱" in line), None)
    if header_idx is None:
        return []

    df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    if df.empty:
        return []

    name_col = next((col for col in ["股名", "股票名稱", "證券名稱"] if col in df.columns), None)
    symbol_col = next((col for col in ["股號", "股票代號", "證券代號", "代號"] if col in df.columns), None)
    action_col = next((col for col in ["買賣別", "交易別", "交易種類"] if col in df.columns), None)
    shares_col = next((col for col in ["成交股數", "股數", "成交數量"] if col in df.columns), None)
    price_col = next((col for col in ["成交價", "價格", "成交價格"] if col in df.columns), None)
    date_col = next((col for col in ["日期", "成交日期", "交易日期"] if col in df.columns), None)
    order_col = next((col for col in ["委託書號", "委託單號", "訂單編號"] if col in df.columns), None)
    fee_col = "手續費" if "手續費" in df.columns else None
    tax_col = next((col for col in _CATHAY_TAX_COLS if col in df.columns), None)

    required = [name_col, action_col, shares_col, price_col, date_col]
    if any(column is None for column in required):
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        action = _resolve_action(row[action_col])
        symbol = normalize_symbol(row[symbol_col]) if symbol_col else lookup_tw_symbol_by_name(row[name_col])
        if not action or not symbol:
            continue
        shares = _parse_optional_number(row[shares_col])
        price = _parse_optional_number(row[price_col])
        if shares <= 0 or price <= 0:
            continue
        fee = _parse_optional_number(row[fee_col], default=-1.0) if fee_col else -1.0
        if fee < 0:
            fee = _fallback_cathay_fee(price, shares)
        tax = _parse_optional_number(row[tax_col]) if tax_col else 0.0
        trade_date = pd.to_datetime(row[date_col], errors="coerce")
        if pd.isna(trade_date):
            continue
        rows.append(
            {
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "market": "TW",
                "name": str(row[name_col]).strip(),
                "action": action,
                "shares": shares,
                "price": price,
                "fee": fee,
                "tax": tax,
                "currency": "TWD",
                "order_id": str(row[order_col]).strip() if order_col else "",
                "broker": "Cathay",
                "account": "",
                "source": "cathay_csv",
                "note": "",
            }
        )
    return rows


def parse_generic_csv(content: bytes) -> list[dict]:
    df = pd.read_csv(io.BytesIO(content))
    df.columns = [str(column).strip().lower() for column in df.columns]
    aliases = {
        "date": "trade_date",
        "交易日期": "trade_date",
        "stock": "symbol",
        "ticker": "symbol",
        "代號": "symbol",
        "市場": "market",
        "名稱": "name",
        "side": "action",
        "數量": "shares",
        "股數": "shares",
        "qty": "shares",
        "成交價": "price",
        "手續費": "fee",
        "證交稅": "tax",
        "currency": "currency",
        "委託單號": "order_id",
        "brokerage": "broker",
        "備註": "note",
    }
    df = df.rename(columns={column: aliases.get(column, column) for column in df.columns})

    required = {"trade_date", "symbol", "market", "action", "shares", "price"}
    if not required.issubset(set(df.columns)):
        missing = ", ".join(sorted(required - set(df.columns)))
        raise ValueError(f"通用 CSV 缺少必要欄位: {missing}")

    rows: list[dict] = []
    for _, row in df.iterrows():
        symbol = normalize_symbol(row["symbol"])
        market = infer_market(symbol, row.get("market"))
        action = _resolve_action(row.get("action")) or str(row.get("action", "")).strip().upper()
        trade_date = pd.to_datetime(row.get("trade_date"), errors="coerce")
        if not symbol or pd.isna(trade_date):
            continue
        rows.append(
            {
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "market": market,
                "name": str(row.get("name", "")).strip(),
                "action": action,
                "shares": _parse_optional_number(row.get("shares")),
                "price": _parse_optional_number(row.get("price")),
                "fee": _parse_optional_number(row.get("fee")),
                "tax": _parse_optional_number(row.get("tax")),
                "currency": str(row.get("currency", "")).strip().upper() or infer_currency(market),
                "order_id": str(row.get("order_id", "")).strip(),
                "broker": str(row.get("broker", "")).strip(),
                "account": str(row.get("account", "")).strip(),
                "source": str(row.get("source", "")).strip() or "generic_csv",
                "note": str(row.get("note", "")).strip(),
            }
        )
    return rows
