# Apple Dark Mobile Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the `股票積效` Streamlit interface in the same Apple Dark visual language as `自動化交易2.0`, with mobile-first layout decisions and no changes to the portfolio calculation workflow.

**Architecture:** Add a shared theme module under `portfolio_app` to centralize Apple Dark CSS and Plotly styling, then refactor `app.py` to use that theme for layout, cards, tabs, forms, and charts. Keep data and import logic intact while reorganizing presentation for thumb-friendly mobile use and strong parity with the reference app.

**Tech Stack:** Python, Streamlit, Plotly, pandas, pytest

---

### Task 1: Add regression tests for the new shared theme helpers

**Files:**
- Create: `tests/test_theme.py`
- Create: `portfolio_app/theme.py`

**Step 1: Write the failing test**

Add tests that assert:
- the injected CSS contains Apple Dark tokens like `--bg`, `--surface`, and `safe-area-inset-bottom`
- the Plotly helper applies dark `paper_bgcolor`, `plot_bgcolor`, and mono font defaults

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_theme.py -v`
Expected: FAIL because `portfolio_app.theme` does not exist yet.

**Step 3: Write minimal implementation**

Create `portfolio_app/theme.py` with:
- shared Apple Dark color constants
- a CSS string for Streamlit layout, tabs, metrics, forms, tables, and mobile safe area
- `inject_theme()` to emit CSS
- `apply_dark_figure_style(fig, ...)` to normalize Plotly charts

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_theme.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_theme.py portfolio_app/theme.py
git commit -m "test: add apple dark theme helpers"
```

### Task 2: Refactor the main app shell to use the Apple Dark mobile-first system

**Files:**
- Modify: `app.py`
- Modify: `portfolio_app/theme.py`

**Step 1: Write the failing test**

Document a manual regression checklist for:
- app loads without syntax errors
- overview renders with Apple Dark cards and charts
- import and ledger tabs remain interactive
- layout remains usable at narrow mobile widths

**Step 2: Run app to capture current baseline**

Run: `.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8502`
Expected: current app loads with old light theme.

**Step 3: Write minimal implementation**

Refactor `app.py` to:
- call `inject_theme()` at startup
- replace the light hero section with a dark compact hero
- add reusable section wrappers and helper text blocks
- reduce multi-column density on small screens
- keep overview/import/ledger tabs but align them to the Apple segmented style
- move secondary controls into less visually dominant surfaces
- apply dark figure styling to all Plotly charts

**Step 4: Run app to verify the redesign**

Run: `.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8502`
Expected: app loads and renders with Apple Dark styling.

**Step 5: Commit**

```bash
git add app.py portfolio_app/theme.py
git commit -m "feat: redesign streamlit shell with apple dark theme"
```

### Task 3: Tune data tables, forms, and import workflow for mobile-first ergonomics

**Files:**
- Modify: `app.py`

**Step 1: Write the failing test**

Add a manual checklist for:
- import controls are readable without horizontal chaos on mobile
- ledger editor is still reachable and understandable
- empty states remain helpful in dark mode

**Step 2: Reproduce the mobile usability pain points**

Run the app and inspect:
- overview with no trades
- import tab with form controls
- ledger tab with editor present

**Step 3: Write minimal implementation**

Adjust the Streamlit layout so that:
- primary actions sit above dense forms
- input groups collapse into 1-column or 2-column rhythms that survive mobile widths
- captions and warnings use dark-surface callouts
- tables receive better section framing instead of relying on raw default Streamlit spacing

**Step 4: Verify manually**

Run the app and confirm the mobile-first checklist is satisfied.

**Step 5: Commit**

```bash
git add app.py
git commit -m "feat: optimize portfolio workflows for mobile dark mode"
```

### Task 4: Final verification

**Files:**
- Verify: `app.py`
- Verify: `portfolio_app/theme.py`
- Verify: `tests/test_performance.py`
- Verify: `tests/test_theme.py`

**Step 1: Run automated tests**

Run: `pytest tests/test_performance.py tests/test_theme.py -v`
Expected: PASS

**Step 2: Run the app**

Run: `.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8503`
Expected: HTTP 200 from `http://127.0.0.1:8503`

**Step 3: Verify functional smoke checks**

Confirm:
- tabs switch normally
- charts render
- empty states still display
- no obvious theme regressions in import and ledger sections

**Step 4: Commit**

```bash
git add app.py portfolio_app/theme.py tests/test_theme.py docs/plans/2026-04-29-apple-dark-mobile-redesign.md
git commit -m "docs: record apple dark mobile redesign plan"
```
