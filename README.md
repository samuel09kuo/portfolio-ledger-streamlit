# 股票績效

以 Streamlit 製作的股票績效台帳 app，支援台股與美股混合持倉，並提供 Apple Dark、mobile-first 的操作介面。

## 功能

- 所有個股的已實現、未實現、總損益
- 持倉圖與績效圖
- 對帳單 CSV、手動輸入、照片 OCR 三種匯入方式
- 台股與美股混合持倉，依報價動態更新
- Supabase 雲端台帳與本機 CSV fallback

## 本機啟動

```powershell
cd C:\Users\Sammmy\程式專案\股票積效
uv venv .venv
.\.venv\Scripts\activate
uv pip install --link-mode copy -r requirements.txt
streamlit run app.py
```

沒有設定 Supabase secrets 時，app 會自動使用本機 `data/ledger.csv`。

## Supabase 模式

這個 repo 已經準備好切換到 Supabase 後端。做法：

1. 在 Supabase SQL Editor 執行 [supabase/portfolio_ledger.sql](supabase/portfolio_ledger.sql)
2. 複製 [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) 成 `.streamlit/secrets.toml`
3. 填入你的 project URL 與 key

本機 secrets 範例：

```toml
[supabase]
url = "https://your-project-ref.supabase.co"
key = "your-anon-or-service-role-key"
```

## 部署到 Streamlit Community Cloud

這個專案適合直接從 GitHub 部署到 Streamlit Community Cloud：

1. 連接 GitHub 帳號到 Streamlit Community Cloud
2. 選擇這個 repository 與 `app.py`
3. 在 Cloud 的 `Edit Secrets` 貼上 `secrets.toml` 內容
4. 部署

注意：

- `secrets.toml` 不要 commit 到 GitHub
- Community Cloud 執行期間產生的本機檔案不保證持久保存，因此正式部署建議使用 Supabase

## 通用交易 CSV 欄位

可直接使用 `templates/trades_template.csv`，必要欄位如下：

- `trade_date`
- `symbol`
- `market`
- `action`
- `shares`
- `price`

## 備註

- 台股與美股價格透過 `yfinance` 抓取，因此即時性可能略有延遲
- OCR 建議搭配清楚截圖使用，匯入前請再次確認股數、價格與買賣方向
