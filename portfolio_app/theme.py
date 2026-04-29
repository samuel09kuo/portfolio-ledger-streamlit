from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

BG = "#000000"
SURFACE = "#1c1c1e"
SURFACE2 = "#2c2c2e"
SEPARATOR = "#3a3a3c"
LABEL = "#ffffff"
LABEL2 = "#ebebf5"
LABEL3 = "#8e8e93"
BLUE = "#0a84ff"
GREEN = "#30d158"
RED = "#ff453a"
ORANGE = "#ff9f0a"
PURPLE = "#bf5af2"
TEAL = "#5ac8f5"

APPLE_DARK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #000000;
    --surface: #1c1c1e;
    --surface2: #2c2c2e;
    --surface3: #111113;
    --sep: #3a3a3c;
    --label: #ffffff;
    --label2: #ebebf5;
    --label3: #8e8e93;
    --blue: #0a84ff;
    --green: #30d158;
    --red: #ff453a;
    --orange: #ff9f0a;
    --purple: #bf5af2;
    --teal: #5ac8f5;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(10, 132, 255, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(48, 209, 88, 0.10), transparent 26%),
        linear-gradient(180deg, #050505 0%, #000000 42%, #050505 100%) !important;
}

[data-testid="stAppViewContainer"] {
    min-height: 100dvh !important;
    color: var(--label) !important;
    scroll-padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 6rem) !important;
}

@supports (padding: max(0px)) {
    .stApp {
        padding-bottom: max(16px, env(safe-area-inset-bottom)) !important;
    }

    .block-container {
        padding-bottom: calc(max(1.2rem, env(safe-area-inset-bottom)) + 4.8rem) !important;
    }
}

header,
header[data-testid="stHeader"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stAppHeader,
#MainMenu {
    display: none !important;
    height: 0 !important;
    visibility: hidden !important;
    overflow: hidden !important;
}

.block-container {
    max-width: 1180px !important;
    padding-top: 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

h1, h2, h3, h4, h5, h6, p, label, input, textarea, button,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
[data-testid="stMarkdownContainer"],
[data-testid="stText"],
[data-testid="stCaption"],
[data-testid="stExpander"] summary p,
.stRadio label, .stCheckbox label,
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

[data-testid="stSidebar"] {
    background: rgba(28, 28, 30, 0.88) !important;
    border-right: 1px solid rgba(58, 58, 60, 0.75) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: var(--label2) !important;
}

.app-shell {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.hero-card {
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    background:
        linear-gradient(135deg, rgba(10, 132, 255, 0.18), rgba(191, 90, 242, 0.12)),
        rgba(28, 28, 30, 0.94);
    border: 1px solid rgba(58, 58, 60, 0.95);
    padding: 1.05rem 1rem 1rem 1rem;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.hero-card::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 85% 12%, rgba(90, 200, 245, 0.22), transparent 20%),
        radial-gradient(circle at 0% 100%, rgba(48, 209, 88, 0.14), transparent 24%);
    pointer-events: none;
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--label3);
    margin-bottom: 0.65rem;
}

.hero-title {
    margin: 0;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--label);
}

.hero-copy {
    margin: 0.5rem 0 0 0;
    max-width: 50rem;
    font-size: 0.93rem;
    line-height: 1.72;
    color: var(--label2);
}

.hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 0.85rem;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    min-height: 2rem;
    padding: 0.28rem 0.72rem;
    border-radius: 999px;
    border: 1px solid rgba(58, 58, 60, 0.9);
    background: rgba(255, 255, 255, 0.05);
    color: var(--label2);
    font-size: 0.76rem;
}

.panel-card,
.info-card {
    border-radius: 18px;
    background: rgba(28, 28, 30, 0.92);
    border: 1px solid rgba(58, 58, 60, 0.82);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
}

.panel-card {
    padding: 0.95rem;
}

.info-card {
    padding: 0.85rem 0.95rem;
    margin-bottom: 0.8rem;
}

.section-kicker {
    margin-bottom: 0.45rem;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--label3);
}

.section-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--label);
}

.section-copy {
    margin: 0.35rem 0 0 0;
    font-size: 0.82rem;
    line-height: 1.65;
    color: var(--label3);
}

[data-testid="stMetric"] {
    background: rgba(28, 28, 30, 0.94) !important;
    border-radius: 16px !important;
    padding: 0.95rem 1rem !important;
    min-height: 82px !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
    box-shadow: none !important;
}

[data-testid="metric-container"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', 'Menlo', monospace !important;
    font-size: 1.38rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.03em !important;
    color: var(--label) !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--label3) !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', 'Menlo', monospace !important;
    font-size: 0.76rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(28, 28, 30, 0.94) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 0 !important;
    border-bottom: none !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: var(--label3) !important;
    padding: 0.52rem 0.85rem !important;
    min-height: 38px !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(44, 44, 46, 0.96) !important;
    color: var(--label) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 0.95rem !important;
}

.stAlert,
[data-testid="stNotification"] {
    background: rgba(28, 28, 30, 0.94) !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
    color: var(--label) !important;
    border-radius: 16px !important;
}

.stCaption,
[data-testid="stCaptionContainer"] {
    color: var(--label3) !important;
    font-size: 0.72rem !important;
}

.streamlit-expanderHeader {
    background: rgba(28, 28, 30, 0.94) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
    color: var(--label) !important;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
[data-baseweb="base-input"] > div,
.stFileUploader section {
    background: rgba(44, 44, 46, 0.92) !important;
    color: var(--label) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--label3) !important;
}

.stButton > button,
.stDownloadButton > button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    border-radius: 14px !important;
    min-height: 42px !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
}

.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"],
[data-testid="baseButton-primary"] {
    background: linear-gradient(180deg, #0a84ff, #0066d6) !important;
    color: white !important;
    border: none !important;
}

.stButton > button[kind="secondary"],
.stDownloadButton > button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background: rgba(44, 44, 46, 0.94) !important;
    color: var(--label) !important;
}

.stDataFrame,
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid rgba(58, 58, 60, 0.82) !important;
}

div[data-testid="stDataFrame"] div[role="grid"],
div[data-testid="stDataEditor"] div[role="grid"] {
    background: rgba(28, 28, 30, 0.96) !important;
}

.mono-note {
    font-family: 'JetBrains Mono', 'Menlo', monospace !important;
}

@media (max-width: 768px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-bottom: calc(max(1rem, env(safe-area-inset-bottom)) + 5rem) !important;
    }

    .hero-card {
        border-radius: 18px;
        padding: 0.95rem 0.85rem;
    }

    .hero-title {
        font-size: 1.32rem;
    }

    .hero-copy {
        font-size: 0.88rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.14rem !important;
    }

    [data-testid="stMetric"] {
        min-height: 74px !important;
        padding: 0.8rem 0.85rem !important;
    }
}
"""


def inject_theme() -> None:
    st.markdown(f"<style>{APPLE_DARK_CSS}</style>", unsafe_allow_html=True)


def apply_dark_figure_style(
    fig: go.Figure,
    *,
    height: int = 360,
    title: str = "",
    legend_orientation: str = "h",
) -> go.Figure:
    axis_style = dict(
        gridcolor=SEPARATOR,
        zeroline=False,
        showgrid=True,
        color=LABEL3,
        tickfont=dict(color=LABEL3),
        title_font=dict(color=LABEL3),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        font=dict(color=LABEL, size=11, family="JetBrains Mono, Menlo, monospace"),
        height=height,
        margin=dict(l=20, r=18, t=48 if title else 18, b=56),
        legend=dict(
            bgcolor="rgba(28,28,30,0.96)",
            bordercolor=SEPARATOR,
            borderwidth=1,
            font=dict(size=10, color=LABEL2),
            orientation=legend_orientation,
            yanchor="top",
            y=-0.18 if legend_orientation == "h" else 1.0,
            xanchor="left",
            x=0,
        ),
        hovermode="x unified",
    )
    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=13, color=LABEL3, family="Inter, sans-serif"),
                x=0,
                xanchor="left",
            )
        )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    return fig
