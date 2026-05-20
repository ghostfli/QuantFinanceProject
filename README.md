# Statistical Arbitrage Backtesting Engine

A production-ready **quantitative finance project** demonstrating end-to-end statistical arbitrage (pairs trading) on S&P 500 equities. Built to showcase proficiency in quantitative finance, time series analysis, software engineering, and risk management — targeting entry-level quant finance roles.

---

## 🎯 Project Overview

This project builds a **pairs trading backtesting engine** that:

1. **Downloads & cleans** historical price data for 500+ S&P 500 stocks (10+ years of daily OHLCV)
2. **Screens pairs** via Engle-Granger cointegration tests to identify mean-reverting relationships
3. **Generates signals** based on z-score thresholds of the price spread
4. **Backtests** with realistic transaction costs (bid-ask, commissions, slippage)
5. **Analyzes performance** using walk-forward validation and bootstrap confidence intervals
6. **Visualizes results** on an interactive dashboard

### Key Insight: Why Pairs Trading?

Pairs trading exploits **market inefficiencies** by identifying two stocks that move together (cointegrated). When they diverge, we bet they'll revert to their mean relationship:
- **Buy the underperformer, short the outperformer** → market-neutral long/short position
- **Dollar-neutral** → removes systematic market risk
- **Mean reversion** → profits when the spread normalizes

---

## 📊 Tech Stack

| Layer | Tools |
|-------|-------|
| **Language** | Python 3.11+ |
| **Data Pipeline** | yfinance, pandas, NumPy |
| **Storage** | Parquet (columnar), SQLite |
| **Time Series / Stats** | statsmodels, SciPy |
| **Backtesting** | Vectorized NumPy/pandas (no loops) |
| **Dashboard** | Streamlit / Plotly Dash (Phase 5) |
| **Version Control** | Git + GitHub |

---

## 📁 Project Structure

```
QuantFinanceProject/
├── src/
│   └── data_pipeline.py           # Phase 1: Download, clean, store prices
├── run_pipeline.py                # CLI entry point
├── project_outline.md             # Full roadmap & requirements
├── requirements.txt               # Python dependencies
├── data/
│   ├── prices/                    # Parquet files (one per ticker)
│   └── db/                        # SQLite metadata database
└── .gitignore
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ghostfli/QuantFinanceProject
cd QuantFinanceProject

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Phase 1 (Data Pipeline)

```bash
# Test mode: Download 10 representative tickers (fast)
python run_pipeline.py --test

# Full mode: Download all 500 S&P 500 stocks (~20-30 min)
python run_pipeline.py

# Custom tickers
python run_pipeline.py --tickers AAPL MSFT GOOG JPM
```

### Output

After running, you'll see:
- **Parquet files** in `data/prices/` (one per ticker, ~117 KB each)
- **SQLite database** in `data/db/metadata.db` tracking download status, date ranges, and data quality
- **Console summary** showing success/failure counts and sample data

---

## 📈 Project Phases

### Phase 1: Data Pipeline ✅ (Complete)
- Fetch S&P 500 tickers from Wikipedia
- Download adjusted OHLCV data via yfinance
- Clean: drop NaNs/zeros, forward-fill gaps, detect unadjusted splits
- Save to Parquet; track metadata in SQLite

**Skills:** Python, pandas, APIs, data cleaning, SQL

### Phase 2: Pair Selection via Cointegration (In Progress)
- Compute pairwise Engle-Granger cointegration tests
- Calculate half-life of mean reversion (Ornstein-Uhlenbeck process)
- Rank pairs by p-value, half-life, sector, correlation stability
- Output ranked candidate pairs

**Skills:** statsmodels, time series econometrics, hypothesis testing

### Phase 3: Signal Generation & Backtesting (Planned)
- Compute spread and z-score with rolling normalization
- Define entry/exit rules based on z-score thresholds
- Build vectorized backtester (NumPy/pandas, no loops)
- Model transaction costs (bid-ask, commissions, slippage)

**Skills:** Signal processing, NumPy, vectorized backtesting

### Phase 4: Risk & Performance Analytics (Planned)
- Compute Sharpe, Sortino, Calmar ratios
- Run walk-forward validation (2-year train, 6-month test windows)
- Bootstrap confidence intervals on Sharpe ratio
- Compare in-sample vs. out-of-sample (overfitting detection)

**Skills:** Performance attribution, risk metrics, statistical validation

### Phase 5: Dashboard & Write-Up (Planned)
- Interactive Streamlit/Dash app with equity curves, signals, correlations
- 2-page research memo (hypothesis, methodology, limitations)
- Polish README with architecture diagrams and results

**Skills:** Data visualization, Streamlit, scientific writing

---

## 🧪 Key Concepts

### Cointegration vs. Correlation
- **Correlation alone is not enough** — two stocks can be correlated but diverge forever
- **Cointegration** means the spread between two prices is stationary (mean-reverting)
- **Engle-Granger test** checks if a linear combination of two series is stationary

### Z-Score Signals
```
z = (spread - rolling_mean) / rolling_std
Entry:  |z| > 2.0    (2-sigma, high conviction)
Exit:   z = 0.0      (full mean reversion)
Stop:   |z| > 3.5    (emergency exit)
```

### Vectorized Backtesting
- All trades computed at once using NumPy arrays (no for-loops)
- **1000x faster** than event-driven backtesting for fast iteration
- Trade-off: Less flexibility for complex order logic

### Walk-Forward Validation
- Train on rolling 2-year window, test on next 6 months
- **Never peek at future data** (eliminates look-ahead bias)
- Compare in-sample vs. out-of-sample performance to detect overfitting

---

## 📚 References

- *Algorithmic Trading* — Ernest Chan (Chapter 3: Pairs Trading)
- *Quantitative Trading* — Ernest Chan
- [statsmodels Cointegration Tests](https://www.statsmodels.org/stable/tsa_tests.html)
- [Quantopian Lectures on Mean Reversion](https://github.com/quantopian)
- [Alpaca API Docs](https://alpaca.markets/docs) (for live paper trading)

---

## 🎓 Resume Bullets

- Built end-to-end statistical arbitrage backtesting engine screening 500+ equity pairs via Engle-Granger cointegration tests across 10 years of daily price data
- Engineered vectorized backtester with transaction cost modeling achieving [X] Sharpe ratio on out-of-sample walk-forward validation (2014–2024)
- Deployed interactive performance dashboard (Streamlit) with real-time Alpaca paper trading integration, visualizing equity curves, z-score signals, and pair correlations

---

## 🔄 Next Steps

1. **Phase 2**: Build pair screening pipeline with cointegration ranking
2. **Phase 3**: Implement vectorized backtest engine with realistic costs
3. **Phase 4**: Validate statistical significance and guard against overfitting
4. **Phase 5**: Deploy Streamlit dashboard and live paper trading via Alpaca

See `project_outline.md` for detailed specifications and architecture.

---

## 📝 License

This project is open source and available under the MIT License.

---

**Author:** Geoff B  
**Status:** Active Development (Phase 1 Complete)  
**Background:** BS Computer Science, MS Quantitative Finance (Rutgers University)
