# Statistical Arbitrage (Pairs Trading) Backtesting Engine

## Project Goal

Build a end-to-end statistical arbitrage backtesting engine screening S&P 500 equity pairs via cointegration testing. The project demonstrates proficiency in quantitative finance, time series analysis, software engineering, and risk management — targeting entry-level quant finance roles.

**Background:** BS in Computer Science, incoming MS in Quantitative Finance at Rutgers University.

---

## Project Structure

```
pairs_trader/
├── src/
│   └── data_pipeline.py       # Phase 1 engine
├── run_pipeline.py            # Phase 1 entry point
├── data/
│   ├── prices/                # Parquet files, one per ticker (~117 KB each)
│   └── db/                    # SQLite metadata database
├── .vscode/
│   └── launch.json            # VS Code debug configurations
├── venv/                      # Virtual environment (not committed to git)
├── requirements.txt
└── .gitignore
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Data download | yfinance |
| Data manipulation | pandas, NumPy |
| Storage | Parquet (pyarrow) + SQLite |
| Stats / signals | statsmodels, SciPy |
| Backtesting | Custom vectorized engine |
| Dashboard | Streamlit or Plotly Dash |
| Version control | Git + GitHub |

---

## Data & Storage

- **Universe:** S&P 500 (~500 stocks)
- **History:** 2014–present (~10 years of daily OHLCV)
- **Rows:** ~1.26 million (500 tickers × 252 trading days × 10 years)
- **Storage format:** One Parquet file per ticker + SQLite metadata DB
- **Projected disk usage:** ~57 MB total (trivial)
- **Why Parquet:** Columnar format, fast reads for bulk numerical operations, industry standard in quant shops

---

## Project Phases

### Phase 1 — Data Pipeline
**Timeline: ~1 week**

Download, clean, and store historical price data for all S&P 500 constituents.

**Key tasks:**
- Fetch S&P 500 ticker list from Wikipedia
- Download adjusted OHLCV data via yfinance (`2014-01-01` to present)
- Clean data: drop zero/NaN adj_close rows, flag zero-volume days, forward-fill 1-day gaps (business day calendar), detect unadjusted splits (>±50% single-day return)
- Save to Parquet (one file per ticker)
- Track download status in SQLite metadata DB (status, row count, date range, missing days)

**Key concepts:**
- Adjusted close price vs. raw close (splits, dividends)
- Trading calendar and business day frequency
- Corporate actions and why they corrupt backtests

**Skills demonstrated:** Python, pandas, APIs, data cleaning, file I/O, SQLite

---

### Phase 2 — Pair Selection via Cointegration
**Timeline: ~2 weeks**

Screen all possible ticker pairs for statistical cointegration — the mathematical basis for pairs trading.

**Key tasks:**
- Compute all pairwise combinations within sectors (reduce from ~125,000 to a manageable subset)
- Run Engle-Granger cointegration test on each pair using `statsmodels`
- Optionally run Johansen test for robustness
- Calculate half-life of mean reversion by fitting an Ornstein-Uhlenbeck (OU) process
- Rank pairs by: p-value, half-life (target 5–30 days), same sector/industry, correlation stability
- Output a ranked list of candidate pairs

**Key concepts:**
- Cointegration vs. correlation (correlation is not enough — two series can be correlated but diverge forever)
- Engle-Granger two-step test
- Ornstein-Uhlenbeck process and half-life: `half_life = -log(2) / log(beta)` where beta is the AR(1) coefficient of the spread
- Stationarity and the ADF test

**Skills demonstrated:** statsmodels, time series econometrics, hypothesis testing, combinatorics

---

### Phase 3 — Signal Generation & Backtesting
**Timeline: ~3 weeks**

Model the spread between each pair as a z-score and build a vectorized backtester with realistic trading costs.

**Key tasks:**
- Compute the spread: `spread = price_A - hedge_ratio * price_B`
- Estimate hedge ratio via OLS regression (or Kalman filter for dynamic ratio)
- Normalize spread to z-score: `z = (spread - mean) / std` using a rolling window
- Define entry/exit rules:
  - Enter long/short when `|z| > 2.0`
  - Exit at `z = 0` (full mean reversion) or `|z| < 0.5`
  - Stop loss at `|z| > 3.5`
- Build a vectorized backtester (no loops — use NumPy/pandas vectorized operations for speed)
- Model transaction costs: bid-ask spread (~2–5 bps), commissions, slippage
- Track position state, P&L, and trade log

**Key concepts:**
- Z-score normalization and rolling statistics
- Long/short equity — buying the underperformer, shorting the outperformer
- Hedge ratio and dollar neutrality
- Vectorized backtesting vs. event-driven (speed tradeoff)
- Kalman filter for dynamic hedge ratio estimation (stretch goal)

**Skills demonstrated:** NumPy, signal processing, backtesting, transaction cost modeling

---

### Phase 4 — Risk & Performance Analytics
**Timeline: ~2 weeks**

Evaluate strategy performance rigorously and guard against overfitting.

**Key tasks:**
- Compute standard performance metrics on the equity curve:
  - Sharpe ratio (annualized): `(mean_return - rf) / std_return * sqrt(252)`
  - Sortino ratio (downside deviation only)
  - Maximum drawdown and Calmar ratio
  - Hit rate (% of winning trades)
  - Average holding period
- Run walk-forward analysis: train on rolling 2-year window, test on next 6 months — never peek at future data
- Bootstrap confidence intervals on Sharpe ratio to assess statistical significance
- Compare in-sample vs. out-of-sample performance to detect overfitting

**Key concepts:**
- Sharpe ratio and its limitations (assumes normality)
- Drawdown and why max drawdown matters more than average return in practice
- Walk-forward validation (the quant equivalent of train/test split)
- Overfitting in financial models — the primary way backtests lie

**Skills demonstrated:** Performance attribution, risk metrics, statistical validation, avoiding look-ahead bias

---

### Phase 5 — Dashboard & Write-Up
**Timeline: ~1 week**

Communicate results professionally via an interactive dashboard and a written research memo.

**Key tasks:**
- Build a Streamlit or Plotly Dash app displaying:
  - Equity curve for each pair strategy
  - Spread and z-score chart with entry/exit markers
  - Pair correlation heatmap
  - Performance metrics table
  - Live signal state (which pairs are currently triggered)
- Write a 2-page research memo (PDF) covering:
  - Hypothesis and methodology
  - Pair selection criteria and results
  - Backtest performance summary
  - Limitations and risks
  - Next steps
- Polish GitHub README with setup instructions, architecture diagram, and sample results

**Skills demonstrated:** Data visualization, Streamlit, scientific writing, communication

---

## Stretch Goals

These differentiate a good project from a great one:

- **Kalman filter** for dynamic hedge ratio estimation instead of fixed OLS (more adaptive, more impressive)
- **ML-based pair selection** — cluster stocks by return correlation using k-means or hierarchical clustering before cointegration testing
- **Live paper trading** via Alpaca API — connect the signal engine to real-time data and execute paper trades automatically
- **Crypto pairs** — extend the universe to BTC/ETH or other crypto pairs (24/7 markets, different dynamics)
- **Options on the spread** — instead of trading the spread directly, buy/sell straddles when z-score is extreme

---

## Resume Bullets (draft)

- Built end-to-end statistical arbitrage backtesting engine screening 500+ equity pairs via Engle-Granger cointegration tests across 10 years of daily price data
- Engineered vectorized backtester with transaction cost modeling achieving [X] Sharpe ratio on out-of-sample walk-forward validation (2014–2024)
- Deployed interactive performance dashboard (Streamlit) with real-time Alpaca paper trading integration, visualizing equity curves, z-score signals, and pair correlations

---

## Key Reference Material

- *Algorithmic Trading* — Ernest Chan (pairs trading bible, Chapter 3)
- *Quantitative Trading* — Ernest Chan
- `statsmodels` docs: Cointegration tests — https://www.statsmodels.org
- Quantopian lecture series on mean reversion (archived on GitHub)
- Alpaca API docs for paper trading — https://alpaca.markets/docs

---

## Environment Setup

```bash
# Clone and set up
git clone <your-repo>
cd pairs_trader
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run Phase 1 (test mode — 10 tickers)
python run_pipeline.py --test

# Run Phase 1 (full S&P 500, ~20-30 min)
python run_pipeline.py
```

### `.gitignore`
```
venv/
data/prices/
data/db/
__pycache__/
*.pyc
.DS_Store
```