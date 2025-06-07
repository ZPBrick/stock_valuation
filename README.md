# Stock Valuation (股票估值分析)

A comprehensive stock valuation toolkit that implements various valuation models and analysis tools.

## Features

- DCF (Discounted Cash Flow) Model
  - Multi-scenario analysis
  - Business segment analysis
  - AI impact consideration
  - Competitive advantage analysis
  - Company type specific parameters

## Project Structure

```
stock_valuation/
├── models/          # Valuation models
│   └── dcf_model.py
├── data/           # Data storage and caching
├── utils/          # Utility functions
├── examples/       # Example scripts
│   └── dcf_analyzer.py
└── tests/          # Test cases
```

## Requirements

- Python 3.8+
- pandas
- numpy
- requests
- alpha_vantage

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

1. Set your Alpha Vantage API key:
```bash
export ALPHA_VANTAGE_API_KEY="your_api_key"
```

2. Run the DCF analysis:
```bash
python3 examples/dcf_analyzer.py
```

## Example Output

```
分析股票: NVDA
==================================================
公司基本信息:
Name: NVIDIA Corporation
Sector: MANUFACTURING
Industry: SEMICONDUCTORS & RELATED DEVICES
MarketCapitalization: $3444.02B
...

估值分析:
BASE情景:
估计内在价值: $228.83
当前股价: $141.92
上涨空间: 61.2%
...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 