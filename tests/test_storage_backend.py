from __future__ import annotations

import sys
from types import ModuleType

import pandas as pd

import portfolio_app.storage as storage


def _install_fake_streamlit(monkeypatch, secrets: dict) -> None:
    fake_streamlit = ModuleType("streamlit")
    fake_streamlit.secrets = secrets
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)


def _reset_storage_state(monkeypatch) -> None:
    monkeypatch.setattr(storage, "_SB_CLIENT", None)
    monkeypatch.setattr(storage, "_SB_INIT_ERROR", "")


def test_invalid_supabase_url_falls_back_to_local_storage(tmp_path, monkeypatch):
    _reset_storage_state(monkeypatch)
    _install_fake_streamlit(monkeypatch, {"supabase": {"url": "not-a-url", "key": "test-key"}})
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "LEDGER_PATH", tmp_path / "data" / "ledger.csv")

    storage.save_ledger(pd.DataFrame([{"trade_date": "2026-04-29", "symbol": "2330", "market": "TW", "action": "BUY", "shares": 1, "price": 100, "fee": 0, "tax": 0, "currency": "TWD"}]))
    loaded = storage.load_ledger()

    assert len(loaded) == 1
    assert storage.get_storage_backend_status()["summary"].startswith("Supabase 設定有誤")


def test_no_supabase_secrets_reports_local_mode(monkeypatch):
    _reset_storage_state(monkeypatch)
    _install_fake_streamlit(monkeypatch, {})

    status = storage.get_storage_backend_status()

    assert status["level"] == "info"
    assert "本機檔案模式" in status["summary"]


class _FakeExecuteResult:
    def __init__(self, data=None):
        self.data = data or []


class _FakeTable:
    def __init__(self, client, name: str):
        self.client = client
        self.name = name
        self.payload = None
        self.filters = []
        self.selected_columns = None

    def select(self, columns: str):
        self.selected_columns = columns
        self.client.calls.append((self.name, "select", columns))
        return self

    def upsert(self, payload):
        self.payload = payload
        self.client.calls.append((self.name, "upsert", payload))
        return self

    def insert(self, payload):
        self.payload = payload
        self.client.calls.append((self.name, "insert", payload))
        return self

    def delete(self):
        self.client.calls.append((self.name, "delete", None))
        self.payload = None
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        self.client.calls.append((self.name, "eq", (field, value)))
        return self

    def neq(self, field, value):
        self.filters.append((field, value))
        self.client.calls.append((self.name, "neq", (field, value)))
        return self

    def order(self, field):
        self.client.calls.append((self.name, "order", field))
        return self

    def limit(self, count: int):
        self.client.calls.append((self.name, "limit", count))
        return self

    def execute(self):
        self.client.calls.append((self.name, "execute", self.payload))
        if self.name == storage.SUPABASE_LEDGER_TABLE and self.selected_columns:
            return _FakeExecuteResult(self.client.rows)
        return _FakeExecuteResult()


class _FakeSupabaseClient:
    def __init__(self, rows: list[dict] | None = None):
        self.calls: list[tuple] = []
        self.rows = rows or []

    def table(self, name: str):
        self.calls.append(("table", name, None))
        return _FakeTable(self, name)


def test_supabase_backend_can_save_and_load_ledger(monkeypatch):
    rows = [
        {
            "trade_id": "t1",
            "trade_date": "2026-04-29",
            "symbol": "2330",
            "market": "TW",
            "name": "台積電",
            "action": "BUY",
            "shares": 1.0,
            "price": 100.0,
            "fee": 0.0,
            "tax": 0.0,
            "currency": "TWD",
            "order_id": "",
            "broker": "",
            "account": "",
            "source": "manual",
            "note": "",
            "created_at": "2026-04-29T10:00:00",
        }
    ]
    fake_client = _FakeSupabaseClient(rows=rows)
    _reset_storage_state(monkeypatch)
    monkeypatch.setattr(storage, "_use_supabase", lambda: True)
    monkeypatch.setattr(storage, "_sb_client", lambda: fake_client)
    monkeypatch.setattr(storage, "_sb_healthcheck_error", lambda: "")
    monkeypatch.setattr(storage, "get_supabase_error", lambda: "")

    frame = pd.DataFrame(rows)
    storage.save_ledger(frame)
    loaded = storage.load_ledger()

    assert len(loaded) == 1
    assert loaded.iloc[0]["symbol"] == "2330"
    assert any(call[:2] == (storage.SUPABASE_LEDGER_TABLE, "insert") for call in fake_client.calls)
    assert storage.get_storage_backend_status()["level"] == "success"
