from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from portfolio_app.importers import (
    build_manual_trade,
    detect_cathay_statement_notice,
    parse_cathay_csv,
    parse_generic_csv,
)
from portfolio_app.market_data import (
    build_symbol_catalog,
    fetch_current_quotes,
    fetch_fx_history,
    fetch_price_history,
)
from portfolio_app.models import TEMPLATE_PATH, VISIBLE_LEDGER_COLUMNS
from portfolio_app.ocr import ocr_image_to_text, parse_trades_from_ocr_text
from portfolio_app.performance import (
    build_current_snapshot,
    build_portfolio_history,
    validate_trades,
)
from portfolio_app.storage import append_records, load_ledger, save_ledger
from portfolio_app.storage import get_storage_backend_status
from portfolio_app.theme import (
    BLUE,
    GREEN,
    LABEL3,
    ORANGE,
    PURPLE,
    SURFACE,
    SURFACE2,
    TEAL,
    apply_dark_figure_style,
    inject_theme,
)

st.set_page_config(
    page_title="股票績效總覽",
    page_icon="📈",
    layout="wide",
)


def fmt_money(value: float, currency: str) -> str:
    return f"{value:,.0f} {currency}"


def fmt_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value * 100:+.2f}%"


def fmt_security(name: object, symbol: object) -> str:
    clean_name = str(name or "").strip()
    clean_symbol = str(symbol or "").strip().upper()
    return f"{clean_name}（{clean_symbol}）" if clean_name and clean_symbol else clean_name or clean_symbol


def chart_config() -> dict:
    return {
        "displayModeBar": False,
        "scrollZoom": False,
        "doubleClick": False,
        "staticPlot": True,
    }


def render_shell_start() -> None:
    inject_theme()
    st.markdown('<div class="app-shell">', unsafe_allow_html=True)


def render_shell_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_hero(trades: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <section class="hero-card">
            <h1 class="hero-title">股票績效</h1>
            <div class="hero-meta">
                <span class="hero-pill">交易筆數 {len(trades):,}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(kicker: str, title: str, copy: str = "") -> None:
    st.markdown(
        f"""
        <section class="info-card">
            {"<div class='section-kicker'>" + kicker + "</div>" if kicker else ""}
            <p class="section-title">{title}</p>
            {"<p class='section-copy'>" + copy + "</p>" if copy else ""}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_compact_note(text: str) -> None:
    st.markdown(
        f"""
        <section class="info-card">
            <p class="section-copy mono-note">{text}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_settings(trades: pd.DataFrame) -> tuple[str, int]:
    with st.expander("顯示設定", expanded=False):
        base_currency = st.selectbox("總覽基準幣別", ["TWD", "USD"], index=0, key="base_currency_select")
        refresh_seconds = st.select_slider("自動刷新報價", options=[0, 15, 30, 60], value=30, key="refresh_seconds_select")
    if trades.empty:
        st.info("目前台帳是空的，先到「匯入交易」。")
    return base_currency, int(refresh_seconds)


def render_storage_status() -> None:
    status = get_storage_backend_status()
    summary = status.get("summary", "")
    detail = status.get("detail", "")
    if status.get("level") == "success":
        st.success(f"{summary}\n\n{detail}")
    elif status.get("level") == "warning":
        st.warning(f"{summary}\n\n{detail}")
    else:
        st.info(f"{summary}\n\n{detail}")


def load_market_context(
    trades: pd.DataFrame,
    base_currency: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    catalog = build_symbol_catalog(trades)
    if catalog.empty:
        return catalog, pd.DataFrame(), {}, {}
    start_date = str(pd.to_datetime(trades["trade_date"]).min().date())
    end_date = str((pd.Timestamp.today().normalize() + pd.Timedelta(days=1)).date())
    currencies = set(catalog["currency"].dropna().astype(str).str.upper().tolist())
    currencies.add(base_currency.upper())
    quotes = fetch_current_quotes(catalog)
    price_history = fetch_price_history(catalog, start_date, end_date)
    fx_history = fetch_fx_history(currencies, start_date, end_date, base_currency)
    return catalog, quotes, price_history, fx_history


def render_summary_metrics(summary: dict[str, float | str | int], base_currency: str) -> None:
    row1_col1, row1_col2 = st.columns(2)
    row1_col1.metric("目前淨值", fmt_money(float(summary["market_value"]), base_currency))
    row1_col2.metric(
        "未實現損益",
        fmt_money(float(summary["unrealized_pnl"]), base_currency),
        fmt_pct(float(summary["unrealized_pnl"]) / float(summary["open_cost"]) if float(summary["open_cost"]) else None),
    )

    row2_col1, row2_col2 = st.columns(2)
    row2_col1.metric("已實現損益", fmt_money(float(summary["realized_pnl"]), base_currency))
    row2_col2.metric(
        "總損益",
        fmt_money(float(summary["total_pnl"]), base_currency),
        fmt_pct(float(summary["total_pnl"]) / float(summary["open_cost"]) if float(summary["open_cost"]) else None),
    )

    st.metric(
        "持有標的 / 交易筆數",
        f"{summary['holding_count']} 檔",
        f"{summary['trade_count']} 筆交易",
    )


def render_overview(trades: pd.DataFrame, base_currency: str) -> None:
    problems = validate_trades(trades)
    if problems:
        st.error("台帳內有需要先修正的資料，否則績效會不準。")
        st.write("\n".join(f"- {problem}" for problem in problems[:10]))
        return

    catalog, quotes, price_history, fx_history = load_market_context(trades, base_currency)
    summary, positions = build_current_snapshot(trades, quotes, fx_history, base_currency)
    history = build_portfolio_history(trades, price_history, fx_history, base_currency)

    render_section_intro(
        "總覽",
        "績效摘要",
    )
    render_summary_metrics(summary, base_currency)

    if summary["as_of"]:
        render_compact_note(
            f"報價更新：{summary['as_of']}"
        )

    chart_col, allocation_col = st.columns([1.2, 1.0])
    with chart_col:
        render_section_intro(
            "走勢",
            "績效圖",
        )
        if history.empty:
            st.info("目前還沒有足夠的歷史價格可繪製績效圖。")
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=history["date"],
                    y=history["total_pnl"],
                    mode="lines",
                    name="總損益",
                    line=dict(color=GREEN, width=3),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=history["date"],
                    y=history["unrealized_pnl"],
                    mode="lines",
                    name="未實現",
                    line=dict(color=BLUE, width=2),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=history["date"],
                    y=history["realized_pnl"],
                    mode="lines",
                    name="已實現",
                    line=dict(color=ORANGE, width=2, dash="dot"),
                )
            )
            fig.add_hline(y=0, line_dash="dot", line_color=LABEL3)
            apply_dark_figure_style(fig, height=400)
            st.plotly_chart(fig, use_container_width=True, config=chart_config())

    with allocation_col:
        render_section_intro(
            "配置",
            "持倉分布",
        )
        if positions.empty:
            st.info("目前沒有持倉。")
        else:
            treemap = px.treemap(
                positions,
                path=[px.Constant("持倉"), "display_name"],
                values="market_value_base",
                color="market_value_base",
                color_continuous_scale=["#163a66", "#0a84ff", "#64d2ff"],
            )
            treemap.update_traces(
                root_color=SURFACE2,
                textinfo="label+percent parent",
                marker=dict(line=dict(color=SURFACE2, width=1)),
                hovertemplate="%{label}<br>占比 %{percentParent:.1%}<br>淨值 %{value:,.0f}<extra></extra>",
            )
            apply_dark_figure_style(treemap, height=400)
            treemap.update_layout(coloraxis_showscale=False, margin=dict(l=8, r=8, t=18, b=8))
            st.plotly_chart(treemap, use_container_width=True, config=chart_config())

    render_section_intro(
        "持倉",
        "持倉明細",
    )
    if positions.empty:
        st.info("尚無持股明細。")
    else:
        display = positions.copy()
        display["標的"] = display.apply(lambda row: fmt_security(row["name"], row["symbol"]), axis=1)
        display["quantity"] = display["quantity"].map(lambda value: f"{value:,.4f}".rstrip("0").rstrip("."))
        display["avg_cost_local"] = display["avg_cost_local"].map(lambda value: f"{value:,.2f}")
        display["last_price"] = display["last_price"].map(lambda value: f"{value:,.2f}")
        display["market_value_base"] = display["market_value_base"].map(lambda value: fmt_money(value, base_currency))
        display["unrealized_pnl_base"] = display["unrealized_pnl_base"].map(lambda value: fmt_money(value, base_currency))
        display["realized_pnl_base"] = display["realized_pnl_base"].map(lambda value: fmt_money(value, base_currency))
        display["weight_pct"] = display["weight_pct"].map(fmt_pct)
        display["price_change_pct"] = display["price_change_pct"].map(fmt_pct)
        st.dataframe(
            display[
                [
                    "標的",
                    "market_value_base",
                    "unrealized_pnl_base",
                    "realized_pnl_base",
                    "weight_pct",
                    "quantity",
                    "avg_cost_local",
                    "last_price",
                    "price_change_pct",
                ]
            ].rename(
                columns={
                    "market_value_base": "目前淨值",
                    "unrealized_pnl_base": "未實現損益",
                    "realized_pnl_base": "已實現損益",
                    "weight_pct": "權重",
                    "quantity": "股數",
                    "avg_cost_local": "均價",
                    "last_price": "現價",
                    "price_change_pct": "漲跌幅",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_section_intro(
        "排行",
        "持倉市值排行",
    )
    if positions.empty:
        st.info("尚無排行資料。")
    else:
        bars = positions.sort_values("market_value_base", ascending=True).tail(10)
        fig = px.bar(
            bars,
            x="market_value_base",
            y="display_name",
            orientation="h",
            text="market_value_base",
            color="market",
            color_discrete_map={"TW": BLUE, "US": GREEN},
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        apply_dark_figure_style(fig, height=430)
        st.plotly_chart(fig, use_container_width=True, config=chart_config())


def render_import_tab() -> None:
    render_section_intro(
        "匯入",
        "建立或補齊交易台帳",
    )
    subtab_csv, subtab_manual, subtab_photo = st.tabs(["上傳對帳單", "手動輸入", "照片輸入"])

    with subtab_csv:
        render_compact_note("支援國泰對帳單 CSV 與通用交易 CSV。")
        if TEMPLATE_PATH.exists():
            st.link_button(
                "下載通用交易模板",
                "https://raw.githubusercontent.com/samuel09kuo/portfolio-ledger-streamlit/main/templates/trades_template.csv",
                type="primary",
                use_container_width=True,
            )
        import_type = st.radio("匯入格式", ["國泰對帳單 CSV", "通用交易 CSV"], horizontal=True)
        uploaded = st.file_uploader("選擇檔案", type=["csv"], key="csv_import")
        if uploaded is not None:
            try:
                uploaded_bytes = uploaded.getvalue()
                if import_type == "國泰對帳單 CSV":
                    notice = detect_cathay_statement_notice(uploaded_bytes)
                    if notice:
                        st.warning(f"{notice}\n\n這種檔案通常只包含部分歷史，若有先賣後買，請把更早的交易也一併匯入。")
                records = (
                    parse_cathay_csv(uploaded_bytes)
                    if import_type == "國泰對帳單 CSV"
                    else parse_generic_csv(uploaded_bytes)
                )
                preview = pd.DataFrame(records)
                if preview.empty:
                    st.warning("這份檔案沒有解析到交易紀錄。")
                else:
                    preview["標的"] = preview.apply(lambda row: fmt_security(row.get("name"), row.get("symbol")), axis=1)
                    preview["動作"] = preview["action"].map({"BUY": "買進", "SELL": "賣出", "SPLIT": "分割"}).fillna(preview["action"])
                    st.dataframe(
                        preview[
                            ["trade_date", "標的", "動作", "shares", "price", "fee", "tax", "order_id"]
                        ].rename(
                            columns={
                                "trade_date": "交易日期",
                                "shares": "股數",
                                "price": "成交價",
                                "fee": "手續費",
                                "tax": "交易稅",
                                "order_id": "委託單號",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if st.button("匯入這批交易", key="import_csv_button", type="primary", use_container_width=True):
                        source = "cathay_csv" if import_type == "國泰對帳單 CSV" else "generic_csv"
                        added = append_records(records, source=source)
                        st.success(f"已匯入 {added} 筆新交易。")
            except Exception as exc:
                st.error(f"匯入失敗：{exc}")

    with subtab_manual:
        render_compact_note("手動輸入。")
        with st.form("manual_trade_form", clear_on_submit=True):
            action_options = {"買進": "BUY", "賣出": "SELL", "分割": "SPLIT"}
            col1, col2 = st.columns(2)
            trade_date = col1.date_input("交易日期", value=date.today())
            market = col2.selectbox("市場", ["TW", "US"])

            col3, col4 = st.columns(2)
            symbol = col3.text_input("股票代號", placeholder="2330 或 AAPL")
            action_label = col4.selectbox("動作", list(action_options))
            action = action_options[action_label]

            col5, col6 = st.columns(2)
            shares = col5.number_input("股數 / 分割倍率", min_value=0.0, value=0.0, step=1.0)
            price = col6.number_input("成交價", min_value=0.0, value=0.0, step=0.01)

            col7, col8 = st.columns(2)
            fee = col7.number_input("手續費", min_value=0.0, value=0.0, step=0.01)
            tax = col8.number_input("交易稅", min_value=0.0, value=0.0, step=0.01)

            col9, col10 = st.columns(2)
            name = col9.text_input("股票名稱", placeholder="可空白")
            order_id = col10.text_input("委託單號", placeholder="可空白")

            col11, col12 = st.columns(2)
            broker = col11.text_input("券商", placeholder="國泰 / 盈透...")
            account = col12.text_input("帳戶", placeholder="主帳 / 美股 ...")

            note = st.text_area("備註", placeholder="例如：盤前加碼、手動補登")
            submitted = st.form_submit_button("新增交易", type="primary", use_container_width=True)
            if submitted:
                try:
                    record = build_manual_trade(
                        trade_date=trade_date,
                        symbol=symbol,
                        market=market,
                        action=action,
                        shares=shares,
                        price=price if action != "SPLIT" else 1.0,
                        fee=fee,
                        tax=tax,
                        name=name,
                        order_id=order_id,
                        broker=broker,
                        account=account,
                        note=note,
                        source="manual",
                    )
                    added = append_records([record], source="manual")
                    st.success(f"已新增 {added} 筆交易。")
                except Exception as exc:
                    st.error(f"新增失敗：{exc}")

    with subtab_photo:
        render_compact_note("照片 OCR。")
        image_file = st.file_uploader("上傳照片 / 截圖", type=["png", "jpg", "jpeg"], key="photo_import")
        if image_file is not None and st.button("執行 OCR", key="run_ocr", type="primary", use_container_width=True):
            try:
                text = ocr_image_to_text(image_file.getvalue())
                parsed = parse_trades_from_ocr_text(text)
                st.session_state["ocr_raw_text"] = text
                st.session_state["ocr_records"] = parsed
            except Exception as exc:
                st.error(f"OCR 失敗：{exc}")
        if st.session_state.get("ocr_raw_text"):
            st.text_area("OCR 原始文字", value=st.session_state["ocr_raw_text"], height=180)
            parsed = st.session_state.get("ocr_records", [])
            if parsed:
                preview = pd.DataFrame(parsed)
                edited = st.data_editor(preview, use_container_width=True, num_rows="dynamic", key="ocr_preview_editor")
                if st.button("匯入 OCR 交易", key="import_ocr_button", type="primary", use_container_width=True):
                    added = append_records(edited.to_dict("records"), source="photo_ocr")
                    st.success(f"已匯入 {added} 筆 OCR 交易。")
            else:
                st.warning("OCR 有讀到文字，但沒有成功辨識出可匯入的交易列。")


def render_ledger_tab(trades: pd.DataFrame) -> None:
    render_section_intro(
        "台帳",
        "直接修正交易台帳",
    )
    if trades.empty:
        st.info("台帳目前是空的，先到上方匯入第一批交易。")
        return

    render_compact_note("`trade_id` 與 `created_at` 為唯讀。")
    editable = trades.copy()
    edited = st.data_editor(
        editable,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_order=["trade_id", *VISIBLE_LEDGER_COLUMNS, "created_at"],
        disabled=["trade_id", "created_at"],
        key="ledger_editor",
    )
    if st.button("儲存台帳變更", type="primary", use_container_width=True):
        try:
            save_ledger(edited)
            st.success("台帳已更新。")
        except Exception as exc:
            st.error(f"儲存失敗：{exc}")


def main() -> None:
    trades = load_ledger()
    render_shell_start()
    render_hero(trades)
    render_storage_status()
    base_currency, refresh_seconds = render_settings(trades)
    overview_tab, import_tab, ledger_tab = st.tabs(["總覽", "匯入交易", "交易台帳"])

    with overview_tab:
        if trades.empty:
            render_section_intro(
                "開始",
                "尚無交易資料",
            )
            st.info("先到「匯入交易」。")
        else:
            if refresh_seconds > 0:
                render_compact_note(f"總覽每 {refresh_seconds} 秒更新一次。")

                @st.fragment(run_every=refresh_seconds)
                def _live_overview() -> None:
                    render_overview(load_ledger(), base_currency)

                _live_overview()
            else:
                render_overview(trades, base_currency)
    with import_tab:
        render_import_tab()
    with ledger_tab:
        render_ledger_tab(trades)

    render_shell_end()


if __name__ == "__main__":
    main()
