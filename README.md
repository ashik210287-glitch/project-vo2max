# VO2MAX AI — Version 1.0 MVP

A locally runnable web application for recording cardiovascular fitness assessments.

## What works in this version

- Streamlit web interface with responsive dashboard layout.
- Rockport 1-mile walk equation-based VO2 max estimate.
- Laboratory CPET measurement entry.
- SQLite persistence on the local computer.
- Assessment history and filtering.
- Progress chart.
- CSV export.
- Scientific methodology and limitations page.
- Automated tests for the Rockport calculation.

## Important scientific boundary

The Rockport result is an equation-based field-test estimate, not a direct CPET measurement.
The app stores CPET entries as user-supplied measured values; it does not verify lab reports.
The machine-learning feature is intentionally disabled until an appropriate documented CPET-labelled
dataset is obtained and the model is independently validated. Do not describe this MVP as a
clinically validated AI predictor.

## Requirements

- Python 3.10 or newer
- Internet connection for the initial package installation only

## Install on Windows

Open PowerShell in this project folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

## Install on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The app normally opens at:

`http://localhost:8501`

## Run tests

```bash
pytest -q
```

## Local database

Records are saved in:

`data/vo2max_ai.sqlite3`

Back up this file regularly. Deleting it deletes the local assessment history.

## Project structure

```text
vo2max_ai_mvp/
├── app.py
├── vo2max.py
├── requirements.txt
├── README.md
├── data/
├── docs/
├── ml/
└── tests/
    └── test_rockport.py
```

## Before public deployment

This MVP does not include authentication, multi-user access controls, encrypted cloud storage,
payment processing, or regulatory review. Do not expose it to the public internet or store
identifiable health information in a shared deployment until those controls are implemented.

## Roadmap

1. Add authentication and role-based access.
2. Add secure cloud database and consent flows.
3. Obtain a documented CPET-labelled dataset with appropriate permissions.
4. Train participant-separated models and perform external validation.
5. Add model versioning, uncertainty and subgroup error monitoring.
6. Add wearable integrations with explicit user permission.
