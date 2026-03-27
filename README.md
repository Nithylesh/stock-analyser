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
| Data Source | Yahoo Finance |
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

**4. (Optional) Configure API keys:**(Not yet supported....)

If using a premium data provider like Alpha Vantage, create a `.env` file in the root directory:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

---

## Usage

### Basic Stock Analysis (Showing the most effective arguments)

```bash
python analyzer.py --trending
```
Summary of how it works: This scrapes trending news snippets and identifies the stocks associated with the news. Deep research (where 10 full news articles based on that issue/stock are scraped) is then conducted. The complete summary is sent to an LLM along with statistical stock data, such as the 50-day average, to generate a prediction.

### Compare Single or Multiple Stocks

```bash
python analyser.py --tickers AAPL MSFT GOOGL # (could have single stock too)
```
Summary of how it works: Same as above but deep research is done on only the specified stocks
NOTE: for Indian stock it should end with .NS(eg: WIPRO.NS)
## Project Structure(kinda follows this ig)

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
kinda fine ig.....did predict dollar strengthening.
update it to become a hosted app on vercel with front end and stuff
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


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
TODO list:
Add a lot more scrapers than yf...like reddit(may bee)....other dorking like nyt, bloomberg , etc.....keep on adding legitimate sites here
addition: for now if i run with --trending arg it fetches trending news from google news and uses those titles and some content(1000chars) and crafts search queries...
and it uses these search queries and gathers more data in each trend and put's all together and goal is to send each trend to llm for decision making.
need to add support for specific stock rather than general/trending ones
## Author

**Nithylesh** — [GitHub Profile](https://github.com/Nithylesh)

---

> ⚠️ **Disclaimer:** This tool is intended for educational and informational purposes only. It does not constitute financial advice. Always do your own research before making investment decisions.
