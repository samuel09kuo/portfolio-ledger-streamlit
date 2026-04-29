from __future__ import annotations

import uuid
from datetime import datetime

import pandas as pd

from .models import DATA_DIR, LEDGER_COLUMNS, LEDGER_PATH


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        pd.DataFrame(columns=LEDGER_COLUMNS).to_csv(LEDGER_PATH, index=False, encoding="utf-8-sig")


def _coerce_ledger_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    for column in LEDGER_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[LEDGER_COLUMNS]
    if frame.empty:
        return frame

    text_columns = [
        "trade_id",
        "trade_date",
        "symbol",
        "market",
        "name",
        "action",
        "currency",
        "order_id",
        "broker",
        "account",
        "source",
        "note",
        "created_at",
    ]
    for column in text_columns:
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    numeric_columns = ["shares", "price", "fee", "tax"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    missing_ids = frame["trade_id"] == ""
    if missing_ids.any():
        frame.loc[missing_ids, "trade_id"] = [str(uuid.uuid4()) for _ in range(int(missing_ids.sum()))]

    missing_created = frame["created_at"] == ""
    if missing_created.any():
        now = datetime.now().isoformat(timespec="seconds")
        frame.loc[missing_created, "created_at"] = now

    frame["symbol"] = frame["symbol"].str.upper()
    frame["market"] = frame["market"].str.upper()
    frame["action"] = frame["action"].str.upper()
    frame["currency"] = frame["currency"].str.upper()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    frame = frame.dropna(subset=["trade_date"])
    frame = frame.sort_values(["trade_date", "created_at", "trade_id"]).reset_index(drop=True)
    return frame


def load_ledger() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(LEDGER_PATH, encoding="utf-8-sig")
    return _coerce_ledger_frame(df)


def save_ledger(df: pd.DataFrame) -> None:
    ensure_storage()
    clean = _coerce_ledger_frame(df)
    clean.to_csv(LEDGER_PATH, index=False, encoding="utf-8-sig")


def normalize_records(records: list[dict], source: str) -> pd.DataFrame:
    now = datetime.now().isoformat(timespec="seconds")
    rows: list[dict] = []
    for record in records:
        row = {column: "" for column in LEDGER_COLUMNS}
        row.update(record)
        row["trade_id"] = str(row.get("trade_id") or uuid.uuid4())
        row["trade_date"] = str(row.get("trade_date", "")).strip()
        row["symbol"] = str(row.get("symbol", "")).strip().upper()
        row["market"] = str(row.get("market", "")).strip().upper()
        row["name"] = str(row.get("name", "")).strip()
        row["action"] = str(row.get("action", "")).strip().upper()
        row["shares"] = float(row.get("shares", 0) or 0)
        row["price"] = float(row.get("price", 0) or 0)
        row["fee"] = float(row.get("fee", 0) or 0)
        row["tax"] = float(row.get("tax", 0) or 0)
        row["currency"] = str(row.get("currency", "")).strip().upper()
        row["order_id"] = str(row.get("order_id", "")).strip()
        row["broker"] = str(row.get("broker", "")).strip()
        row["account"] = str(row.get("account", "")).strip()
        row["source"] = str(row.get("source", "")).strip() or source
        row["note"] = str(row.get("note", "")).strip()
        row["created_at"] = str(row.get("created_at", "")).strip() or now
        rows.append(row)
    return _coerce_ledger_frame(pd.DataFrame(rows, columns=LEDGER_COLUMNS))


def append_records(records: list[dict], source: str) -> int:
    if not records:
        return 0
    ledger = load_ledger()
    incoming = normalize_records(records, source=source)
    dedupe_keys = [
        "trade_date",
        "symbol",
        "market",
        "action",
        "shares",
        "price",
        "fee",
        "tax",
        "order_id",
        "broker",
        "account",
        "source",
    ]
    existing_keys = set(
        tuple(ledger[column].iloc[i] for column in dedupe_keys)
        for i in range(len(ledger))
    )
    append_mask = []
    for i in range(len(incoming)):
        key = tuple(incoming[column].iloc[i] for column in dedupe_keys)
        append_mask.append(key not in existing_keys)
        existing_keys.add(key)
    added = incoming.loc[append_mask].copy()
    if added.empty:
        return 0
    save_ledger(pd.concat([ledger, added], ignore_index=True))
    return len(added)
