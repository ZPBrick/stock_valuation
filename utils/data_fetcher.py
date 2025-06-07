import os
import json
import time
import yfinance as yf
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional, Union
from alpha_vantage.fundamentaldata import FundamentalData
from dotenv import load_dotenv

class DataFetcher:
    def __init__(self, api_key: str = None, cache_dir: str = None, cache_hours: int = 24):
        """
        初始化数据获取器
        
        Args:
            api_key (str): Alpha Vantage API密钥
            cache_dir (str): 缓存目录路径
            cache_hours (int): 缓存有效期（小时）
        """
        load_dotenv()
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("请提供Alpha Vantage API密钥")
            
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.cache_hours = cache_hours
        self.fd = FundamentalData(key=self.api_key)
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_path(self, ticker: str, data_type: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{ticker}_{data_type}.json")
    
    def is_cache_valid(self, cache_path: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - file_time
        return age < timedelta(hours=self.cache_hours)
    
    def save_to_cache(self, data: Dict, ticker: str, data_type: str):
        """保存数据到缓存"""
        cache_path = self.get_cache_path(ticker, data_type)
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    
    def load_from_cache(self, ticker: str, data_type: str) -> Optional[Dict]:
        """从缓存加载数据"""
        cache_path = self.get_cache_path(ticker, data_type)
        if not self.is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def get_yfinance_data(self, ticker: str) -> Dict:
        """从Yahoo Finance获取更完整的数据"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # 确保获取完整的财务数据
            financials = {
                'balance_sheet': stock.balance_sheet.to_dict(orient='records'),
                'income_stmt': stock.income_stmt.to_dict(orient='records'),
                'cash_flow': stock.cashflow.to_dict(orient='records')
            }
            return {'overview': info, 'financials': financials}
        except Exception as e:
            print(f"Yahoo Finance数据获取失败: {str(e)}")
            return {}
    
    def get_company_overview(self, ticker: str, source: str = 'alpha_vantage', use_cache: bool = True) -> Dict:
        """获取公司概览数据"""
        if use_cache:
            overview = self.load_from_cache(ticker, 'overview')
            if overview:
                print(f"从缓存加载{ticker}的公司概览数据")
                return overview

        if source == 'yfinance':
            yf_data = self.get_yfinance_data(ticker)
            if yf_data and 'overview' in yf_data:
                self.save_to_cache(yf_data['overview'], ticker, 'overview')
                return yf_data['overview']
        
        print(f"从Alpha Vantage获取{ticker}的数据...")
        try:
            quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.api_key}'
            response = requests.get(quote_url)
            quote_data = response.json()
            current_price = None
            
            if 'Global Quote' in quote_data:
                quote = quote_data['Global Quote']
                current_price = float(quote.get('05. price', 0))
                print(f"成功获取{ticker}的实时价格数据: ${current_price}")
            
            overview_data, _ = self.fd.get_company_overview(ticker)
            print(f"成功获取{ticker}的公司概览数据")
            
            if isinstance(overview_data, dict):
                overview = overview_data
            else:
                overview = overview_data.to_dict(orient='records')[0]
            
            if current_price:
                overview['MarketPrice'] = current_price
            
            self.save_to_cache(overview, ticker, 'overview')
            return overview
            
        except Exception as e:
            print(f"获取公司概览数据时出错: {str(e)}")
            return {}
    
    def get_financial_data(self, ticker: str, source: str, use_cache: bool = True) -> Dict:
        """优先使用Alpha Vantage数据"""
        if use_cache:
            cached_data = self.load_from_cache(ticker, 'financials')
            if cached_data:
                return cached_data

        if source == 'yfinance':
            yf_data = self.get_yfinance_data(ticker)
            if yf_data.get('financials'):
                self.save_to_cache(yf_data['financials'], ticker, 'financials')
                return yf_data['financials']
        
        # Alpha Vantage作为后备
        try:
            cash_flow, _ = self.fd.get_cash_flow_annual(ticker)
            balance_sheet, _ = self.fd.get_balance_sheet_annual(ticker)
            income_stmt, _ = self.fd.get_income_statement_annual(ticker)
            financials = {
                'cash_flow': cash_flow.to_dict(orient='records'),
                'balance_sheet': balance_sheet.to_dict(orient='records'),
                'income_stmt': income_stmt.to_dict(orient='records')
            }
            self.save_to_cache(financials, ticker, 'financials')
            return financials
        except Exception as e:
            print(f"Alpha Vantage数据获取失败: {str(e)}")
            return {} 