# Supabase Cloud Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the `portfolio-ledger-streamlit` app ready for Streamlit Community Cloud by replacing local-only ledger persistence with a Supabase-backed storage option while preserving a local CSV fallback for development and recovery.

**Architecture:** Extend `portfolio_app.storage` into a dual-backend module that chooses Supabase when valid Streamlit secrets are present and otherwise falls back to the existing CSV ledger. Keep the app UI mostly unchanged, but expose storage backend health, add Supabase schema files, and update docs so the GitHub repo can be deployed directly on Community Cloud with secrets configured separately.

**Tech Stack:** Python, Streamlit, pandas, Supabase Python client, pytest

---

### Task 1: Add tests for backend selection and Supabase fallback behavior

**Files:**
- Create: `tests/test_storage_backend.py`
- Modify: `portfolio_app/storage.py`

**Step 1: Write the failing test**

Add tests that cover:
- invalid Supabase URL falls back to local CSV
- missing Supabase key falls back to local CSV
- backend status reports local mode when no secrets exist
- backend status reports warning on invalid Supabase config
- a fake Supabase client can be used to save and load ledger rows

**Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_storage_backend.py -v`
Expected: FAIL because the storage module does not yet expose Supabase helpers or backend status.

**Step 3: Write minimal implementation**

Add helper functions in `portfolio_app/storage.py` for:
- reading `st.secrets["supabase"]`
- validating credentials
- creating a cached Supabase client
- reporting backend health
- reading and writing ledger rows through Supabase when configured

**Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_storage_backend.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_storage_backend.py portfolio_app/storage.py
git commit -m "test: cover supabase storage backend behavior"
```

### Task 2: Implement a Supabase ledger backend with local CSV fallback

**Files:**
- Modify: `portfolio_app/storage.py`
- Modify: `portfolio_app/models.py`

**Step 1: Write the failing test**

Add or extend tests for:
- `load_ledger()` returns Supabase data when the backend is active
- `save_ledger()` overwrites remote ledger rows deterministically
- `append_records()` still de-duplicates correctly against remote rows

**Step 2: Run targeted tests to verify the new cases fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_storage_backend.py -v`
Expected: FAIL on not-yet-implemented remote ledger behavior.

**Step 3: Write minimal implementation**

Implement a single-table Supabase ledger backend using a dedicated table name for this app, separate from the tables in `自動化交易2.0`. Keep:
- current CSV normalization logic
- deterministic row ordering
- same public storage API (`load_ledger`, `save_ledger`, `append_records`)

**Step 4: Run tests to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_storage_backend.py tests\test_performance.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add portfolio_app/storage.py portfolio_app/models.py tests/test_storage_backend.py
git commit -m "feat: add supabase-backed ledger storage"
```

### Task 3: Surface backend status in the UI and prepare deployment assets

**Files:**
- Modify: `app.py`
- Modify: `README.md`
- Modify: `requirements.txt`
- Create: `.streamlit/config.toml`
- Create: `.streamlit/secrets.toml.example`
- Create: `supabase/portfolio_ledger.sql`

**Step 1: Write the failing test**

Document a manual checklist for:
- backend status is visible in the app
- local mode message is shown without secrets
- deployment docs explain Community Cloud and Supabase secrets clearly

**Step 2: Reproduce the current gap**

Run the app locally and note that:
- there is no backend health indicator
- there is no deploy-ready secrets example
- there is no schema file for this app

**Step 3: Write minimal implementation**

Add:
- a backend status callout in the app shell or settings section
- `supabase` to `requirements.txt`
- `.streamlit/secrets.toml.example` with `[supabase] url/key`
- `.streamlit/config.toml` for Streamlit-friendly defaults
- `supabase/portfolio_ledger.sql` to create the dedicated table for this app
- README sections for local mode, Supabase mode, and Community Cloud deployment

**Step 4: Verify manually**

Run the app locally and confirm the status callout and docs assets exist.

**Step 5: Commit**

```bash
git add app.py README.md requirements.txt .streamlit/config.toml .streamlit/secrets.toml.example supabase/portfolio_ledger.sql
git commit -m "feat: prepare streamlit app for cloud deployment"
```

### Task 4: Final verification

**Files:**
- Verify: `app.py`
- Verify: `portfolio_app/storage.py`
- Verify: `tests/test_theme.py`
- Verify: `tests/test_performance.py`
- Verify: `tests/test_storage_backend.py`

**Step 1: Run automated tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_theme.py tests\test_performance.py tests\test_storage_backend.py -v`
Expected: PASS

**Step 2: Run syntax verification**

Run: `.\.venv\Scripts\python.exe -m py_compile app.py portfolio_app\storage.py portfolio_app\theme.py`
Expected: PASS

**Step 3: Launch the app**

Run: `.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8507`
Expected: HTTP 200 from `http://127.0.0.1:8507`

**Step 4: Commit**

```bash
git add docs/plans/2026-04-29-supabase-cloud-readiness.md
git commit -m "docs: add supabase cloud readiness plan"
```
