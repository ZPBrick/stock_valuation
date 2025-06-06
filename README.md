# Stock Valuation (股票估值分析)

A comprehensive stock valuation toolkit that implements various valuation models and analysis tools.

## Features

- DCF (Discounted Cash Flow) Model
  - Multi-scenario analysis
  - Business segment analysis
  - AI impact consideration
  - Competitive advantage analysis
  - Company type specific parameters
  - **Multiple data source support (Alpha Vantage & Yahoo Finance)**

## Project Structure

```
stock_valuation/
├── models/          # Valuation models
│   └── dcf_model.py
├── data/           # Data storage and caching
├── utils/          # Utility functions
├── app/            # Main application scripts
│   └── dcf_analyzer.py
└── tests/          # Test cases
```

## Requirements

- Python 3.8+
- pandas
- numpy
- requests
- alpha_vantage
- yfinance
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone git@github.com:ZPBrick/stock_valuation.git
cd stock_valuation
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

## Usage

1. Set your Alpha Vantage API key (required for Alpha Vantage data source):
```bash
export ALPHA_VANTAGE_API_KEY="your_api_key"
```

2. Run the DCF analysis with your preferred data source:
```bash
# Using Alpha Vantage (default)
python3 app/dcf_analyzer.py --tickers NVDA AAPL --source alpha_vantage

# Using Yahoo Finance
python3 app/dcf_analyzer.py --tickers NVDA AAPL --source yfinance
```

## Example Output

```
分析股票: NVDA
数据源: yfinance
==================================================
公司基本信息:
Name: NVIDIA Corporation
Sector: TECHNOLOGY
Industry: SEMICONDUCTORS
MarketCapitalization: $3444.02B
...

估值分析:
BASE情景:
估计内在价值: $228.83
当前股价: $141.92
上涨空间: 61.2%
...
```

## Data Source Notes

- **Alpha Vantage**: Requires API key (free tier available), provides comprehensive fundamental data
- **Yahoo Finance**: Free but may have less complete fundamental data, good for quick analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 高级用法

```bash
# 基本用法
python3 app/dcf_analyzer.py --tickers NVDA

# 调试模式（显示详细计算过程）
python3 app/dcf_analyzer.py --tickers NVDA --debug

# 跳过缓存并调试
python3 app/dcf_analyzer.py --tickers NVDA --no-cache --debug
```

## 测试验证

### 命令示例：
```bash
# 普通运行
python3 app/dcf_analyzer.py --tickers NVDA

# 调试运行
python3 app/dcf_analyzer.py --tickers NVDA --debug
```

### 预期调试输出：
```
[调试] NVDA 关键输入数据:
- 市值: 800000000000
- 自由现金流: [8500000000]
- 负债率: 10.0%

[DCF模型调试] 当前自由现金流: 8500000000
[DCF模型调试] WACC: 8.50%
[DCF模型调试] 使用增长率: 25.00%

BASE情景:
估计内在价值: $450.20
...
```