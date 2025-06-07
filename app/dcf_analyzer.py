import os
import sys
import argparse
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.dcf_model import DCFModel
from utils.data_fetcher import DataFetcher

def format_currency(value: float) -> str:
    """格式化货币数值"""
    if abs(value) >= 1e12:
        return f"${value/1e12:.2f}T"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:.2f}"

def analyze_stock(ticker: str, data_source: str = 'alpha_vantage', use_cache: bool = True):
    """分析股票并输出DCF估值结果"""
    print(f"\n分析股票: {ticker} (数据源: {data_source}, 缓存: {'启用' if use_cache else '禁用'})")
    print("=" * 50)
    
    try:
        # 获取数据
        fetcher = DataFetcher()
        company_data = fetcher.get_company_overview(ticker, source=data_source, use_cache=use_cache)
        if not company_data:
            print(f"无法获取{ticker}的公司数据")
            return
            
        # 打印公司基本信息
        print("\n公司基本信息:")
        print(f"Name: {company_data.get('Name', 'N/A')}")
        print(f"Sector: {company_data.get('Sector', 'N/A')}")
        print(f"Industry: {company_data.get('Industry', 'N/A')}")
        print(f"MarketCapitalization: {format_currency(float(company_data.get('MarketCapitalization', 0)))}")
        
        # 获取财务数据
        financial_data = fetcher.get_financial_data(ticker, source=data_source, use_cache=use_cache)
        if not financial_data:
            print(f"无法获取{ticker}的财务数据")
            return
            
        # 创建DCF模型
        data = {
            'overview': company_data,
            'financials': financial_data
        }
        model = DCFModel(ticker, data)
        
        # 分析不同情景
        scenarios = ['base', 'optimistic', 'pessimistic']
        
        print("\n估值分析:")
        for scenario in scenarios:
            result = model.value(scenario)
            
            if 'error' in result:
                print(f"\n{scenario.upper()}情景:")
                print(f"错误: {result['error']}")
                continue
                
            print(f"\n{scenario.upper()}情景:")
            print(f"估计内在价值: {format_currency(result['price_per_share'])}")
            print(f"当前股价: {format_currency(result['current_price'])}")
            print(f"上涨空间: {result['upside']:.1f}%")
            print(f"WACC: {result['wacc']*100:.1f}%")
            print(f"增长率: {result['growth_rate']*100:.1f}%")
            print(f"永续增长率: {result['terminal_growth']*100:.1f}%")
            print(f"企业价值: {format_currency(result['enterprise_value'])}")
            print(f"股权价值: {format_currency(result['equity_value'])}")
            
    except Exception as e:
        print(f"分析过程中出错: {str(e)}")

def main():
    """主函数"""
    # 检查API密钥
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print("错误: 请设置ALPHA_VANTAGE_API_KEY环境变量")
        return

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票DCF估值分析工具')
    parser.add_argument('--tickers', nargs='+', required=True, help='股票代码列表，例如 NVDA AAPL META')
    parser.add_argument('--source', choices=['alpha_vantage', 'yfinance'], default='alpha_vantage', 
                       help='数据源 (alpha_vantage 或 yfinance)')
    parser.add_argument('--no-cache', action='store_true', help='强制从API获取数据，忽略缓存')
    args = parser.parse_args()

    # 分析股票
    for ticker in args.tickers:
        analyze_stock(ticker, data_source=args.source, use_cache=not args.no_cache)
        print("\n" + "="*50)

if __name__ == "__main__":
    main() 