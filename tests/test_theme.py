from __future__ import annotations

import plotly.graph_objects as go

from portfolio_app.theme import APPLE_DARK_CSS, BG, SURFACE, apply_dark_figure_style


def test_apple_dark_css_includes_mobile_safe_area_and_dark_tokens():
    assert "--bg: #000000;" in APPLE_DARK_CSS
    assert "--surface: #1c1c1e;" in APPLE_DARK_CSS
    assert "--accent: #0a84ff;" in APPLE_DARK_CSS
    assert "safe-area-inset-bottom" in APPLE_DARK_CSS
    assert '[data-testid="stMetric"]' in APPLE_DARK_CSS


def test_apply_dark_figure_style_sets_dark_plotly_defaults():
    fig = go.Figure()

    apply_dark_figure_style(fig, height=420, title="Example")

    assert fig.layout.paper_bgcolor == BG
    assert fig.layout.plot_bgcolor == SURFACE
    assert fig.layout.height == 420
    assert fig.layout.font.family == "JetBrains Mono, Menlo, monospace"
    assert fig.layout.title.text == "Example"
