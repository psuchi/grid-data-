# WindSight: UK National Wind Generation Forecast Monitoring & Accuracy Evaluation

**WindSight** is an enterprise-grade analytics application designed for UK electricity utility trading and procurement desks to monitor national wind generation forecasts and evaluate historical day-ahead forecast accuracy during the delivery month of **January 1–31, 2026**.

Built with **FastAPI** (Python 3.12, Pandas) and **React** (Vite, Recharts), WindSight ingests official Balancing Mechanism Reporting Service (**Elexon BMRS**) datasets, enforces strict day-ahead decision cutoffs, and calculates forecast performance metrics.

---

## 1. Business Problem & Objectives

### The Procurement Challenge
UK electricity utilities must commit to day-ahead physical and financial electricity positions prior to power exchange auctions (such as EPEX SPOT and Nord Pool GB day-ahead auctions at 11:00 / 12:00 UTC) and National Energy System Operator (NESO) gate closures. Wind generation represents a significant share of Great Britain's generation mix but exhibits high meteorological volatility:
- **Overforecasting ($F_t > A_t$):** The desk expects high wind outturn and procures less dispatchable thermal generation or sells surplus energy forward. When outturn falls short, the utility is caught short in cashout/balancing settlement, incurring costly System Buy Prices (SBP).
- **Underforecasting ($F_t < A_t$):** The utility procures excess thermal or import energy. At outturn, excess wind causes a long position liquidated at System Sell Prices (SSP), depressing realized margins.

### How WindSight Solves It
WindSight provides:
1. **Decision Cutoff Enactment:** Evaluates the forecast snapshot that was **actually available** to the procurement desk at the time trading decisions were made (e.g. Day-Ahead 12:00 UTC auction cutoff), rather than silently utilizing the latest intraday forecast.
2. **Forecast Evolution History:** Allows trading analysts to inspect how forecast runs shifted across successive submissions (e.g. 48h out, 24h out, 12h out, 4h out) leading up to any specific delivery interval.
3. **Statistical Accuracy Evaluation:** Computes Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Signed Error / Bias, Matched Sample Count, and Mean Absolute Percentage Error (MAPE) with zero-actual safeguards.

---

## 2. Architecture & Data Flow

```
   ┌────────────────────────────────────────────────────────┐
   │             Official Elexon BMRS API (v1)              │
   │  https://data.elexon.co.uk/bmrs/api/v1/datasets/       │
   └───────────────┬────────────────────────┬───────────────┘
                   │                        │
       FUELHH/stream (Actuals)   WINDFOR/stream (Forecasts)
       [fuelType: WIND, 30m SP]   [Multi-run submissions, 1h]
                   │                        │
                   ▼                        ▼
   ┌────────────────────────────────────────────────────────┐
   │             WindSight Backend (FastAPI)                │
   │  • Timezone Standardization (UTC Storage / UK Display) │
   │  • Decision Cutoff Selection Engine                    │
   │  • Local High-Performance File Cache (backend/data/)   │
   │  • Robust Fallback Safeguards & Duplicate Handling     │
   └──────────────────────────┬─────────────────────────────┘
                              │ REST JSON API
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │              WindSight Frontend (React + Vite)         │
   │  • Enterprise Energy Theme (Dark Glassmorphism)        │
   │  • Metric KPI Cards (MAE, RMSE, Bias, Matched Periods) │
   │  • Actual vs Forecast Time-Series Chart (Recharts)     │
   │  • Signed Forecast Error Divergence Chart              │
   │  • Interactive Forecast Evolution Modal                │
   │  • Filterable & Exportable Settlement Data Table       │
   └────────────────────────────────────────────────────────┘
```

### Data Flow Stages
1. **Data Ingestion:**
   - **Actuals:** Queried from `GET /datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31`. Filtered to `fuelType == 'WIND'`.
   - **Forecasts:** Queried from `GET /datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z` to capture all multi-day and day-ahead forecast runs.
2. **Caching & Resilience:** Raw records are processed and cached in `backend/data/` for rapid development and container resilience. If the remote API times out or is offline, the cached Elexon dataset is loaded automatically.
3. **Cutoff Processing:** For each delivery interval, candidates are filtered to those where `publishTime <= cutoff_time`. The candidate with $\max(\text{publishTime})$ is selected.
4. **Accuracy Computation:** Matched pairs are piped into the statistical analytics engine.

---

## 3. API Sources & Critical Data Limitations

### Official Elexon BMRS Endpoints
| Dataset | Purpose | Resolution | Filter Parameters |
| :--- | :--- | :--- | :--- |
| **`FUELHH/stream`** | Half-hourly national outturn by fuel type | 30-minute Settlement Periods | `settlementDateFrom`, `settlementDateTo` |
| **`WINDFOR/stream`** | Day-ahead & 2-day ahead wind generation forecast | Hourly delivery intervals | `publishDateTimeFrom`, `publishDateTimeTo` |

### Critical Disclosures & Data Boundaries
1. **Procurement Volume & Cost Boundaries:**
   - **WindSight explicitly does not claim to compute net procurement imbalance volumes or financial balancing costs.**
   - Calculating cashout costs or energy deficit/surplus trades requires **national gross electricity demand, thermal unit generation, interconnector schedules, and System Buy/Sell Prices (SBP/SSP)**. These are not present in Elexon's isolated `FUELHH` and `WINDFOR` feeds.
2. **Temporal Resolution Mismatch (30-Minute vs Hourly):**
   - In Elexon BMRS, `FUELHH` actuals are published at 30-minute settlement period resolution (48 settlement periods per day = 1,488 half-hour periods in January 2026).
   - In contrast, the national `WINDFOR/stream` publishes wind forecasts at **hourly delivery start times** (`:00:00Z`).
   - Consequently, exact delivery `startTime` matching yields **744 matched hourly delivery periods** (50% settlement period coverage). Unforecasted half-hourly settlement periods (`:30:00Z`) are transparently labeled as unforecasted rather than fabricating interpolated numbers.
3. **Timezone Handling:**
   - All timestamps are stored and manipulated internally in **UTC**.
   - Timestamps are formatted and displayed in **UK Local Time (GMT in January)** with explicit GMT/BST indicators.

---

## 4. Forecast Cutoff Selection Methodology

In wholesale energy trading, selecting the latest historical forecast timestamp is a **lookahead bias fallacy**; it evaluates intraday forecast runs that were not available when day-ahead procurement decisions were finalized.

WindSight implements a **configurable Day-Ahead Decision Cutoff**:

$$\text{Cutoff Timestamp} = (D - 1\text{ day}) \text{ at } H_{\text{cutoff}}\text{ UTC}$$

### Supported Cutoff Rules
1. **`day_ahead_1200` (Default):** Day D-1 at 12:00:00 UTC. Represents the standard UK Day-Ahead Power Exchange (EPEX / Nord Pool) auction gate closure.
2. **`day_ahead_1700`:** Day D-1 at 17:00:00 UTC. Represents the post-auction evening planning gate closure.
3. **`day_ahead_2300`:** Day D-1 at 23:00:00 UTC. Represents end-of-day planning.
4. **`hours_prior_24`:** Exactly 24 hours prior to each delivery interval's `startTime`.
5. **`hours_prior_12`:** Exactly 12 hours prior to delivery interval.
6. **`hours_prior_4`:** Exactly 4 hours prior (Intraday Gate Closure).
7. **`latest_available`:** Unrestricted latest historical forecast prior to delivery (included strictly as a benchmark for comparison).

### Selection Algorithm
For each delivery interval $T$ with `startTime` $t_{\text{delivery}}$:
1. Determine cutoff timestamp $t_{\text{cutoff}}$ according to the active cutoff rule.
2. Filter candidate forecasts for $T$ to those satisfying:
   $$\text{publishTime} \le t_{\text{cutoff}}$$
3. If valid candidates exist, select the latest published:
   $$F^* = \arg\max_{\text{publishTime}} \{\text{publishTime} \le t_{\text{cutoff}}\}$$
4. Calculate lead time:
   $$\text{Lead Time (hours)} = \frac{t_{\text{delivery}} - \text{publishTime}}{3600}$$
5. If no forecast was published at or before the cutoff, the delivery period is marked as `is_matched = False`, and excluded from error metrics with transparent disclosure.

---

## 5. Metric Definitions

Let $A_t$ be actual generation (MW) and $F_t$ be the selected eligible forecast (MW) for matched sample $t \in \{1, \dots, N\}$:

### 1. Mean Absolute Error (MAE)
Quantifies the average magnitude of forecast errors without regard to sign:
$$\text{MAE} = \frac{1}{N} \sum_{t=1}^{N} |F_t - A_t|$$

### 2. Root Mean Squared Error (RMSE)
Heavily penalizes larger forecast deviations due to quadratic squaring:
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^{N} (F_t - A_t)^2}$$

### 3. Mean Signed Error (Bias)
Indicates directional systematic error:
$$\text{Bias} = \frac{1}{N} \sum_{t=1}^{N} (F_t - A_t)$$
- $\text{Bias} > 0$: **Overforecasting** (forecast higher than actuals; utility faces risk of purchasing too little thermal backup or selling excess power forward).
- $\text{Bias} < 0$: **Underforecasting** (forecast lower than actuals; utility faces risk of over-procuring thermal generation).

### 4. Mean Absolute Percentage Error (MAPE) with Safeguards
$$\text{MAPE} = \frac{100\%}{M} \sum_{t \in \{A_t > 1.0\}} \frac{|F_t - A_t|}{A_t}$$
- **Zero-Denominator Safeguard:** Calm wind conditions can drop national wind outturn close to 0 MW. Any period where $A_t \le 1.0\text{ MW}$ is excluded from the percentage denominator, and the count of zero-actual periods is tracked and displayed.

### 5. Matched Sample Count & Coverage
Tracks the number of delivery periods $N$ where both actuals and an eligible forecast existed, alongside the coverage ratio $N / N_{\text{total}}$.

---

## 6. Project Structure

```
windsight/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application setup, CORS, lifespan
│   │   ├── config.py                   # Pydantic configuration settings
│   │   ├── schemas.py                  # Pydantic API response models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py               # /health, /forecasts, /accuracy, /forecast-history
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── elexon_client.py        # Async client for Elexon BMRS streams
│   │   │   └── data_store.py           # In-memory store, caching, UTC/GMT processing
│   │   └── analytics/
│   │       ├── __init__.py
│   │       ├── metrics.py              # MAE, RMSE, Bias, MAPE calculations
│   │       └── cutoff_selector.py      # Cutoff selection & time-series matching
│   ├── data/                           # Authentic cached Elexon JSON datasets
│   │   ├── fuelhh_jan2026.json         # 1,488 WIND actuals records
│   │   └── windfor_jan2026.json        # 19,272 WINDFOR forecast records
│   ├── scripts/
│   │   └── fetch_elexon_data.py        # Offline cache ingestion script
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_metrics.py             # Unit tests for MAE, RMSE, bias, zero actuals
│   │   ├── test_cutoff_selector.py     # Unit tests for cutoff logic & exclusion
│   │   └── test_api.py                 # Integration tests for FastAPI endpoints
│   ├── Dockerfile                      # Production backend Docker image
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx              # Brand header, time badge, status indicator
│   │   │   ├── DisclosureBanner.jsx    # Transparency banner on methodology & bounds
│   │   │   ├── FilterControls.jsx      # Cutoff selector, date range, quick presets
│   │   │   ├── KpiCards.jsx            # MAE, RMSE, Bias, Matched, MAPE cards
│   │   │   ├── TimeSeriesChart.jsx     # Recharts actual vs forecast with brush
│   │   │   ├── ErrorDistributionChart.jsx # Recharts signed error bar chart
│   │   │   ├── ForecastHistoryModal.jsx# Forecast evolution trajectory modal
│   │   │   └── DataTable.jsx           # Sortable, filterable interval data table
│   │   ├── services/
│   │   │   └── api.js                  # Frontend API client
│   │   ├── App.jsx                     # Top-level application coordinator
│   │   ├── main.jsx                    # React DOM entry
│   │   └── index.css                   # High-polish dark enterprise CSS system
│   ├── index.html                      # Semantic HTML with SEO & Google Fonts
│   ├── package.json                    # Frontend npm dependencies
│   ├── vite.config.js                  # Vite configuration
│   ├── nginx.conf                      # Nginx SPA & reverse proxy config
│   ├── Dockerfile                      # Multi-stage frontend Docker image
│   ├── vercel.json                     # Vercel deployment rewrites
│   └── .env.example                    # Frontend environment template
├── docker-compose.yml                  # Full-stack container orchestration
├── .env.example                        # Root environment template
└── README.md                           # Documentation
```

---

## 7. Local Installation & Docker Instructions

### Prerequisites
- **Python 3.12+** (tested with Python 3.12.10)
- **Node.js 20+** (tested with Node.js v24.18.0 and npm 11.16.0)
- (Optional) **Docker & Docker Compose**

---

### Option A: Local Development Setup (Quickstart)

#### 1. Start Backend
```bash
# Navigate to backend directory and create virtual environment
cd backend
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# Or on Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Backend will be available at: `http://localhost:8000` (API documentation at `http://localhost:8000/docs`).

#### 2. Start Frontend
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install npm packages
npm install

# Start Vite dev server
npm run dev
```
Frontend will be available at: `http://localhost:5173`.

---

### Option B: Docker Compose Setup

Run both frontend and backend in isolated production-grade containers:

```bash
# Build and start all services
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

- **Frontend Application:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **Backend Health Check:** `http://localhost:8000/api/health`

To stop:
```bash
docker compose down
```

---

## 8. Backend Test Suite

The test suite covers:
1. **`test_metrics.py`**:
   - Exact numerical calculation of MAE and RMSE on known vectors.
   - Positive bias validation for overforecast conditions ($F > A$).
   - Negative bias validation for underforecast conditions ($F < A$).
   - Zero-actual denominator safeguards for MAPE.
   - All-zero actuals handling without division-by-zero crashes.
   - Missing data (NaN) filtering and array length mismatch handling.
2. **`test_cutoff_selector.py`**:
   - Exact Day-Ahead 12:00 UTC and 17:00 UTC cutoff timestamp calculations.
   - Relative 24h prior cutoff timestamp calculations.
   - Selection of latest forecast submitted at or before the cutoff.
   - Exclusion of forecasts submitted after the cutoff.
   - Time-series matching across delivery periods with unforecasted gaps.
3. **`test_api.py`**:
   - `/api/health` response verification.
   - `/api/cutoffs` configuration list.
   - `/api/accuracy` calculation over date ranges and cutoff types.
   - `/api/forecasts` time-series structure.
   - `/api/forecast-history` evolution retrieval.
   - Validation errors: invalid cutoffs (HTTP 400), invalid date formats (HTTP 400), and `start_date > end_date` (HTTP 400).

### Running Tests
```bash
# Set PYTHONPATH to project root and run pytest
cd "c:\Users\suchi pujar\OneDrive\Desktop\New folder"
$env:PYTHONPATH="."
.\backend\venv\Scripts\pytest.exe backend\tests -v
```

**Results:**
```
======================== 23 passed in 1.11s ========================
```

---

## 9. Deployment Guide

The frontend and backend are decoupled and deployment-ready for independent hosting services.

### Frontend Deployment (Vercel)
1. Push repository to GitHub/GitLab.
2. In the Vercel dashboard, click **Add New Project** and select the repository.
3. Set **Root Directory** to `frontend`.
4. Configure Build & Output:
   - Framework Preset: **Vite**
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Configure Environment Variables:
   - `VITE_API_BASE_URL`: URL of your deployed Python backend (e.g. `https://windsight-api.onrender.com`).
6. Deploy. Vercel will automatically read `frontend/vercel.json` for client-side single page app routing rewrites.

### Backend Deployment (Render / Railway / Fly.io / AWS ECS)
1. **Render / Railway:**
   - Select Docker deployment pointing to `backend/Dockerfile`.
   - Set Environment Variables:
     - `PORT`: `8000`
     - `CORS_ORIGINS`: `["https://your-frontend.vercel.app","http://localhost:5173"]`
2. **Health Check Endpoint:** Configure `/api/health` as the HTTP liveness probe.
3. **Live App URL Placeholder:**
   - Frontend: `https://windsight.vercel.app` (Placeholder)
   - Backend API: `https://windsight-api.onrender.com` (Placeholder)

---

## 10. AI-Assisted Development Disclosure

In full compliance with assessment standards and professional transparency guidelines:
- **Development Tool:** This project was developed with assistance from Google DeepMind's **Antigravity** coding assistant using **Gemini 3.8 Flash**.
- **Human Guidance & Review:** Architectural decisions (data normalization, cutoff selector design, Elexon BMRS endpoint inspection, metric edge-case safeguards, and enterprise styling) were formulated, implemented, reviewed, and verified directly against live BMRS APIs and automated test suites.
