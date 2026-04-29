from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
LEDGER_PATH = DATA_DIR / "ledger.csv"
TEMPLATE_PATH = TEMPLATE_DIR / "trades_template.csv"

LEDGER_COLUMNS = [
    "trade_id",
    "trade_date",
    "symbol",
    "market",
    "name",
    "action",
    "shares",
    "price",
    "fee",
    "tax",
    "currency",
    "order_id",
    "broker",
    "account",
    "source",
    "note",
    "created_at",
]

VISIBLE_LEDGER_COLUMNS = [
    "trade_date",
    "symbol",
    "market",
    "name",
    "action",
    "shares",
    "price",
    "fee",
    "tax",
    "currency",
    "broker",
    "account",
    "order_id",
    "source",
    "note",
]

SUPPORTED_ACTIONS = ("BUY", "SELL", "SPLIT")
SUPPORTED_MARKETS = ("TW", "US")
MARKET_TO_CURRENCY = {
    "TW": "TWD",
    "US": "USD",
}
