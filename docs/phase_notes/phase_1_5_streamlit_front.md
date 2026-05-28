# Phase 1.5 Notes — Minimal Technical Streamlit Front

## 1. What was implemented

Phase 1.5 adds a minimal technical Streamlit inspection UI for Phase 1 processed outputs. It displays dataset availability, high-level KPIs, SKU feature previews, zone utilization, location utilization, and simple native Streamlit charts.

The UI is descriptive only. It does not implement diagnostics, optimization, simulation, authentication, production deployment, or final business workflows.

## 2. What files were created

- `src/slotting_optimization_engine/app/dashboard_data.py`
- `src/slotting_optimization_engine/app/streamlit_app.py`
- `tests/unit/test_dashboard_data.py`
- `docs/DESIGN.md`
- `docs/phase_notes/phase_1_5_streamlit_front.md`
- `docs/phase_logs/phase_1_5_terminal_log.md`

## 3. What each file is for

- `dashboard_data.py` loads processed outputs, reports availability, computes dashboard KPIs, and prepares bounded previews/chart inputs.
- `streamlit_app.py` renders the technical Streamlit UI and delegates data work to `dashboard_data.py`.
- `test_dashboard_data.py` verifies pure helper behavior without requiring Streamlit runtime.
- `docs/DESIGN.md` defines the lightweight operational/control-tower visual system.
- This phase note records decisions, limitations, and evidence.
- The terminal log records commands, results, errors, and resolutions.

## 4. How the flow works

```text
data/processed/slotting_features.parquet
data/processed/location_utilization.csv
data/processed/zone_utilization.csv
        │
        ▼
app/dashboard_data.py
  - load_dashboard_data()
  - compute_kpis()
  - status_table()
  - chart/previews helpers
        │
        ▼
app/streamlit_app.py
  - Streamlit layout
  - KPI cards
  - dataset status
  - native charts and tables
```

If processed outputs are missing or unreadable, the UI shows the exact commands to regenerate them:

```powershell
python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
```

## 5. Main functions/classes

- `DatasetStatus`: immutable metadata for one output file.
- `DashboardData`: loaded dataframe bundle plus statuses.
- `inspect_processed_output()`: safe file availability and loading check.
- `load_dashboard_data()`: loads all expected Phase 1 outputs.
- `missing_outputs()`: returns missing/unreadable outputs.
- `status_table()`: converts statuses into a display dataframe.
- `compute_kpis()`: computes SKU, zone, location, average utilization, and over-capacity counts from processed outputs.
- `preview_table()`: returns bounded dataframe previews.
- `zone_chart_data()` and `location_chart_data()`: prepare native Streamlit chart inputs.
- `main()`: Streamlit page renderer.

## 6. Technical decisions

- Business/data inspection logic lives in `dashboard_data.py`, not the Streamlit file.
- Streamlit is used only as the rendering layer.
- Native Streamlit charts are used to avoid heavy visualization dependencies.
- Missing files are represented as status rows and regeneration commands instead of crashing the UI.
- The preliminary alignment score is explicitly labeled as non-prescriptive.
- `docs/DESIGN.md` defines a compact operational/logistics aesthetic: control-tower feel, dense analyst layout, restrained teal accents, low-elevation panels.

## 7. Assumptions

- Phase 1 processed outputs are the source of truth for Phase 1.5.
- Optional Streamlit dependency may not be installed in every development environment.
- The app is meant for local technical inspection, not production users.

## 8. Remaining limitations

- Streamlit runtime was not launched because `streamlit` is not installed in the active Python environment.
- No advanced diagnostics, recommendations, scenario comparison, optimization, simulation, authentication, or deployment were added.
- Charts remain intentionally simple and native to Streamlit.

## 9. What is missing for the next phase

- Phase 2 should add advanced slotting diagnostics in dedicated modules, not inside the UI.
- If the UI grows, add integration or smoke tests around the Streamlit entrypoint once Streamlit is installed in CI/dev environments.
- Consider expanding design documentation only if the technical front evolves into a broader product UI.

## 10. How to run related scripts

```powershell
python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
pip install -e ".[streamlit]"
streamlit run src/slotting_optimization_engine/app/streamlit_app.py
```

## 11. Expected output

- Dataset availability table for all three processed outputs.
- KPI cards for SKU count, zones, locations, average utilization, and over-capacity locations.
- Zone utilization chart and table.
- Top utilized location chart and table.
- SKU feature preview table.
- Clear warning and commands when required outputs are missing.

## 12. Common errors

- `No module named streamlit`: optional Streamlit dependency is not installed.
- Missing processed output files: Phase 1 scripts have not been run or outputs were deleted.
- Parquet read errors: `pyarrow` missing or the parquet output is corrupt.
- Windows `UnicodeEncodeError` in Graphify query output: terminal encoding is not UTF-8.

## 13. How to resolve common errors

- Install UI dependency: `pip install -e ".[streamlit]"`.
- Regenerate processed outputs with the three Phase 1 commands shown above.
- Reinstall project dependencies if parquet loading fails.
- For Graphify query output on Windows PowerShell, set `$env:PYTHONIOENCODING='utf-8'` before running the query.

## 14. Tests covering the phase

- `tests/unit/test_dashboard_data.py`
- Updated `tests/unit/test_project_structure.py`

## 15. Evidence that the phase works

- `python scripts/build_features.py` completed and produced the three expected processed outputs.
- `python -m ruff check src tests scripts` passed.
- `python -m pytest -v` passed with `152 passed` after the phase note and terminal log were created.
- `python -c "from slotting_optimization_engine.app.dashboard_data import load_dashboard_data; data = load_dashboard_data(); print('ok', len(data.statuses))"` returned `ok 3`.
- `python -m streamlit --version` confirmed Streamlit is not installed, so long-running UI launch was not attempted.
- Graphify was queried before implementation per manager context, then `graphify update .` was run after code changes and the updated graph was queried again with UTF-8 output.
