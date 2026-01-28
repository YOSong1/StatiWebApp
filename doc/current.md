# Current State - DOE Desktop App

- Goal: desktop DOE/statistics tool for sales/marketing/R&D use, built with Python + Qt; MVC refactor underway (controllers for project/data/analysis/chart).
- Structure: `src/main.py` boots PySide6 app and `MainWindow`; controllers live in `src/controllers`, models in `src/models`, utils in `src/utils`, views under `src/views`; sample data in `data/`; tests skeleton in `test/`.

## What Looks Ready
- Project controller handles new/open/save of `.doeproj` JSON using `Project` model; file dialogs and dirty-checking implemented.
- Data controller loads/saves CSV/XLSX with encoding fallbacks, basic validation (duplicate columns, empty files, huge row warning) and emits status/signals.
- Analysis controller sketches basic stats/correlation/ANOVA/regression flows with signals and status updates.
- Docs: multiple planning guides (`MenuReadme.md`, `refactoring.md`, etc.) describe intended menus, refactor plan, and feature roadmap.

## Problems and Redundancies
- Encoding corruption across many strings (Korean text garbled in README, controllers, views) makes UI messages and docs unreadable.
- `src/views/data_view.py` is heavily duplicated and malformed (multiple full copies concatenated, PyQt5 imports while rest of app uses PySide6, many `pass` stubs like `insert_row`, broken strings/quotes). File will not execute as-is.
- `src/controllers/analysis_controller.py` ends with unterminated strings and would fail to import; regression/ANOVA descriptions contain broken f-strings/quotes.
- Dependency list conflicts: both PyQt5 and PySide6 declared; pandas listed twice; optional heavy libs (great-expectations) included with no usage; versions unpinned in code.
- `main.py` expects `resources/icons/app_icon.png` and `resources/styles/main_style.qss`, but no `resources/` directory exists in repo (only `icon/`), so icons/styles fall back.
- README and other guides list extensive features (DOE designs, advanced charts, data quality) that are not implemented in code; risk of scope drift.
- Tests in `test/` likely outdated: they target controllers, but current code contains syntax/encoding errors and PyQt/PySide mismatch, so they probably fail.

## Gaps to Fill
- Decide on single Qt binding (PySide6 preferred) and align all views/controllers/tests; rewrite `data_view.py` accordingly.
- Fix encoding: normalize source files to UTF-8, replace garbled Korean text with readable strings, and clean docs.
- Finish data table behaviors: insert row/column, context menus, type change, selection copy/paste; ensure DataFrame sync is robust.
- Stabilize analysis flows: close strings, add error handling, and expand beyond placeholders (e.g., allow choosing variables, returning structured results).
- Implement DOE-specific features promised in docs (design generation: factorial/response-surface/Taguchi/CCD; design evaluation; DOE plots) or trim promises until implemented.
- Add real resource assets (icons, QSS) or update code paths to existing `icon/` directory.
- Simplify `requirements.txt`: remove duplicates, drop unused heavy deps, and ensure build uses a consistent Qt stack.
- Restore/build tests to run headless where possible (controllers/utils), and add smoke tests for data import/export and analyses.

## Suggested Next Steps
1) Clean and rewrite `src/views/data_view.py` with PySide6, removing duplicates and filling stubs; add unit tests around table <-> DataFrame sync.  
2) Repair `src/controllers/analysis_controller.py` strings and extend to handle variable selection; add deterministic sample datasets for tests.  
3) Normalize encoding/docs (README, menu guides) to UTF-8 and trim claims to match implemented scope; document actual feature roadmap.  
4) Rationalize dependencies (drop PyQt5, dedupe pandas, separate optional extras) and add a minimal install path.  
5) Add missing resources or adjust paths; wire a simple style/icon so the app has a stable default.  
6) Run and update `test/run_tests.py` suite after fixes; add CI later if desired. 
