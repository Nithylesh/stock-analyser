# 📈 Stock Analyser

A Python-based stock analysis tool designed to help investors and traders analyze stock market data with ease.

---

## Overview

Stock Analyser is a comprehensive toolkit for analyzing stock performance, trends, and technical indicators. Whether you're a beginner investor or an experienced trader, this tool provides actionable insights to support your investment decisions.

---

## Features

- **Stock Data Analysis** — Retrieve and analyze historical stock data from major markets
- **Technical Indicators** — Calculate key technical indicators including RSI, MACD, Bollinger Bands, and moving averages
- **Performance Metrics** — Evaluate stock performance over custom time periods (daily, weekly, monthly, yearly)
- **Data Visualization** — Generate interactive charts and graphs for better insights
- **Easy-to-use Interface** — Simple command-line interface for quick and efficient analysis
- **Multi-stock Comparison** — Compare performance across multiple tickers simultaneously

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.8+ |
| Data Source | Yahoo Finance / Alpha Vantage |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib, Plotly |
| Technical Analysis | TA-Lib / pandas-ta |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup

**1. Clone the repository:**

```bash
git clone https://github.com/Nithylesh/stock-analyser.git
cd stock-analyser
```

**2. Create a virtual environment (recommended):**

```bash
python -m venv venv
source venv/bin/activate        # On macOS/Linux
venv\Scripts\activate           # On Windows
```

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

**4. (Optional) Configure API keys:**

If using a premium data provider like Alpha Vantage, create a `.env` file in the root directory:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

---

## Usage

### Basic Stock Analysis

```bash
python analyser.py --ticker AAPL
```

### Specify a Date Range

```bash
python analyser.py --ticker TSLA --start 2023-01-01 --end 2024-01-01
```

### Compare Multiple Stocks

```bash
python analyser.py --tickers AAPL MSFT GOOGL --period 6mo
```

### Generate a Full Report with Charts

```bash
python analyser.py --ticker NVDA --report --charts
```

### Available Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--ticker` | Single stock ticker symbol | `--ticker AAPL` |
| `--tickers` | Multiple ticker symbols | `--tickers AAPL MSFT` |
| `--start` | Start date (YYYY-MM-DD) | `--start 2023-01-01` |
| `--end` | End date (YYYY-MM-DD) | `--end 2024-01-01` |
| `--period` | Predefined period | `--period 1y` |
| `--report` | Export full analysis report | `--report` |
| `--charts` | Generate visual charts | `--charts` |
| `--indicator` | Specific technical indicator | `--indicator RSI` |

---

## Technical Indicators Supported

- **Moving Averages** — SMA (Simple), EMA (Exponential)
- **RSI** — Relative Strength Index
- **MACD** — Moving Average Convergence Divergence
- **Bollinger Bands** — Volatility bands around a moving average
- **Volume Analysis** — On-Balance Volume (OBV), VWAP
- **Momentum** — Stochastic Oscillator, Williams %R

---

## Project Structure

```
stock-analyser/
├── analyser.py          # Main entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── README.md            # Project documentation
│
├── src/
│   ├── data/            # Data fetching and processing modules
│   ├── indicators/      # Technical indicator calculations
│   ├── visualization/   # Chart and graph generation
│   └── reports/         # Report generation utilities
│
├── tests/               # Unit tests
│   └── test_indicators.py
│
└── outputs/             # Generated charts and reports (gitignored)
```
---
## How to Run(currently)
python analyzer.py --trending (this picks the recent stocks wrt to trending news and takes financial stock data too and sends everything to LLM....this is kinda a very basic summary doesn't exactly do that)

evaluator.py - Parses yesterday's predictions and grades them against today's actual market data

run analyzer first and run evaluator next day to see how good the result is..
P.S tried it once and everything was a miss so 100% ig
---

---

## Example Output

Running a full analysis on AAPL produces:

- Price history chart with volume overlay
- RSI and MACD indicator panels
- Support and resistance levels
- 30/60/90-day performance summary
- Exportable PDF or CSV report

---

## Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please make sure your code follows the existing style and includes relevant tests.

---

## Roadmap

- [ ] Portfolio tracking and analysis
- [ ] Sentiment analysis from news headlines
- [ ] Machine learning price prediction models
- [ ] Web dashboard interface (Flask/Streamlit)
- [ ] Email/Slack alert notifications

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
TODO list:
Add a lot more scrapers than yf...like reddit(may bee)....other dorking like nyt, bloomberg , etc.....keep on adding legitimate sites here
addition: for now if i run with --trending arg it fetches trending news from google news and uses those titles and some content(1000chars) and crafts search queries...
and it uses these search queries and gathers more data in each trend and put's all together and goal is to send each trend to llm for decision making.
## Author

**Nithylesh** — [GitHub Profile](https://github.com/Nithylesh)

---

> ⚠️ **Disclaimer:** This tool is intended for educational and informational purposes only. It does not constitute financial advice. Always do your own research before making investment decisions.
