# Retail CRM Project (FastAPI + MLFlow + React + Jenkins)

This project is a complete starter CRM system built around your `online_retail_listing.csv` dataset.

It includes:
- Backend CRM API with customer analytics endpoints.
- ML pipeline tracked with MLFlow and model artifact generation.
- Frontend dashboard for customer listing, insights, and prediction.
- Jenkins CI/CD pipeline (`Jenkinsfile`) that works with either GitHub or Bitbucket repository hosting.

## Architecture

### Backend (`backend/`)
- Framework: FastAPI
- Dataset parsing: `;` delimiter + decimal comma support
- Core features:
  - Customer list with filters
  - Customer detail analytics
  - Customer value prediction endpoint

### ML (`backend/ml/`)
- Tooling: scikit-learn + MLFlow
- Training script: `backend/ml/train.py`
- Output model: `backend/ml/artifacts/customer_value_model.joblib`
- Tracking directory: `backend/ml/mlruns`

### Frontend (`frontend/`)
- Stack: React + Vite
- Dashboard views:
  - KPI cards
  - Customer list and filters
  - Customer detail panel
  - On-demand prediction call

### CI/CD (`Jenkinsfile`)
- Checkout
- Install backend dependencies
- Run backend tests
- Train ML model
- Build frontend
- Archive build artifacts

## Quick Start (Local)

## 1. Backend setup

From project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run tests:

```powershell
pytest tests -q
```

Train model (creates MLFlow run + joblib artifact):

```powershell
python ml/train.py
```

Run API:

```powershell
uvicorn app.main:app --reload --port 8000
```

## 2. Frontend setup

Open a new terminal from project root:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173` and expects backend on `http://127.0.0.1:8000`.

## 3. API endpoints

- `GET /health`
- `GET /api/countries`
- `GET /api/customers?search=&country=&limit=&offset=`
- `GET /api/customers/{customer_id}`
- `POST /api/customers/{customer_id}/prediction`

## GitHub / Bitbucket Code Storage

This project works with both providers.

## GitHub

```bash
git init
git add .
git commit -m "Initial CRM project"
git remote add origin https://github.com/<username>/<repo>.git
git branch -M main
git push -u origin main
```

## Bitbucket

```bash
git init
git add .
git commit -m "Initial CRM project"
git remote add origin https://bitbucket.org/<workspace>/<repo>.git
git branch -M main
git push -u origin main
```

## Jenkins CI/CD Setup

1. Create a Jenkins Pipeline job.
2. Connect the repository (GitHub or Bitbucket).
3. Ensure Jenkins agent has:
   - Python 3
   - pip
   - Node.js + npm
4. Set Pipeline Script from SCM and point to `Jenkinsfile` in repo root.
5. Add webhook from GitHub/Bitbucket to Jenkins for automatic builds on push.
6. On Windows agents, if Python is not available in `PATH`, set build parameter `WINDOWS_PYTHON` to full `python.exe` path (for example `C:\\Python312\\python.exe`).
7. If you installed Python after Jenkins was already running, restart the Jenkins service so new `PATH` values are picked up.

## Notes

- The backend has a fallback heuristic scoring mode if model artifact is not present.
- Once `python ml/train.py` runs, prediction endpoint automatically uses the trained model.
- Dataset cleaning follows your project rules:
  - day-first date parsing
  - non-positive quantity filtering
  - decimal comma parsing for `Price`
