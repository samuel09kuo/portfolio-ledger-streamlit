# 股票績效

獨立的 Streamlit webapp，用來集中管理台股與美股交易台帳，並顯示：

- 所有個股的已實現、未實現、總損益
- 持倉圖與績效圖
- 對帳單 CSV、手動輸入、照片 OCR 三種匯入方式
- 台股與美股混合持倉，依報價動態更新

## 啟動

```powershell
cd C:\Users\Sammmy\程式專案\股票積效
python -m pip install -r requirements.txt
streamlit run app.py
```

## 通用交易 CSV 欄位

可直接使用 `templates/trades_template.csv`，必要欄位如下：

- `trade_date`
- `symbol`
- `market`
- `action`
- `shares`
- `price`

## 備註

- 台股與美股價格透過 `yfinance` 抓取，因此即時性可能略有延遲。
- OCR 建議搭配清楚截圖使用，匯入前請再次確認股數、價格與買賣方向。
