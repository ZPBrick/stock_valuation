import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class DCFModel:
    def __init__(self, ticker: str, data: Dict):
        """
        初始化DCF模型
        
        Args:
            ticker (str): 股票代码
            data (Dict): 包含公司财务数据和概览信息的字典
        """
        self.ticker = ticker
        self.financials = data.get('financials', {})
        self.overview = data.get('overview', {})
        
        # 设置默认参数
        self.set_default_parameters()
        
    def set_default_parameters(self):
        """设置行业特定参数"""
        self.industry = self.overview.get('Industry', '').upper()
        self.sector = self.overview.get('Sector', '').upper()
        
        # 通用参数
        self.risk_free_rate = 0.04  # 10年期美债收益率
        self.market_risk_premium = 0.05  # 市场风险溢价
        self.terminal_growth_rate = 0.03  # 科技行业永续增长率
        
        # 行业覆盖（重点修改半导体）
        if "SEMICONDUCTOR" in self.industry:
            self.revenue_growth = 0.25  # 基准增长率
            self.fcf_margin = 0.25      # 自由现金流利润率
            self.beta = 1.6             # NVDA实际beta约1.6
        else:
            self.revenue_growth = 0.10
            self.fcf_margin = 0.15
            self.beta = 1.0
        
    def calculate_wacc(self) -> float:
        """更合理的WACC计算"""
        cost_of_equity = self.risk_free_rate + self.beta * self.market_risk_premium
        total_debt = float(self.overview.get('TotalDebt', 0))
        interest_expense = float(self.overview.get('InterestExpense', 0))
        cost_of_debt = 0.04 if total_debt == 0 else min(interest_expense / total_debt, 0.08)
        
        market_cap = float(self.overview.get('MarketCapitalization', 1e10))  # 默认100亿
        debt_ratio = min(total_debt / (market_cap + total_debt), 0.3)  # 负债率上限30%
        equity_ratio = 1 - debt_ratio
        
        return (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt * 0.79)  # 21%税率
    
    def get_historical_fcf(self) -> List[float]:
        """修正自由现金流计算"""
        cash_flow = self.financials.get('cash_flow', [])
        return [
            float(year.get('operatingCashflow', 0)) - abs(float(year.get('capitalExpenditures', 0)))
            for year in cash_flow
            if 'operatingCashflow' in year
        ]
    
    def calculate_growth_rates(self) -> Tuple[float, float, float]:
        """覆盖高增长行业逻辑"""
        if "SEMICONDUCTOR" in self.industry:
            return 0.25, 0.35, 0.15  # 基准/乐观/悲观
        
        fcf_list = self.get_historical_fcf()
        if len(fcf_list) >= 2:
            growth_rates = [(fcf_list[i] / fcf_list[i-1] - 1) for i in range(1, len(fcf_list))]
            avg_growth = np.mean(growth_rates)
            return avg_growth, avg_growth * 1.5, avg_growth * 0.5
        return self.revenue_growth, self.revenue_growth * 1.5, self.revenue_growth * 0.5
    
    def calculate_terminal_value(self, fcf: float, growth_rate: float, wacc: float) -> float:
        """计算永续价值"""
        try:
            # 使用戈登增长模型
            terminal_growth = min(growth_rate * 0.3, self.terminal_growth_rate)  # 永续增长率不超过2%
            terminal_value = fcf * (1 + terminal_growth) / (wacc - terminal_growth)
            return terminal_value
            
        except Exception as e:
            print(f"计算永续价值时出错: {str(e)}")
            return 0
    
    def calculate_present_value(self, cash_flows: List[float], wacc: float) -> float:
        """计算现值"""
        try:
            present_value = 0
            for i, cf in enumerate(cash_flows):
                present_value += cf / ((1 + wacc) ** (i + 1))
            return present_value
            
        except Exception as e:
            print(f"计算现值时出错: {str(e)}")
            return 0
    
    def value(self, scenario: str = 'base', debug: bool = False) -> Dict:
        """
        执行DCF估值
        
        Args:
            scenario (str): 情景类型 ('base', 'optimistic', 'pessimistic')
            debug (bool): 是否打印调试信息
            
        Returns:
            Dict: 包含估值结果的字典
        """
        try:
            current_fcf = self.get_historical_fcf()[0] if self.get_historical_fcf() else 0
            if debug:
                print(f"[DCF模型调试] 当前自由现金流: {current_fcf}")
            
            wacc = self.calculate_wacc()
            growth_rate = self.calculate_growth_rates()[0]  # 使用基准情景
            
            if debug:
                print(f"[DCF模型调试] WACC: {wacc:.2%}")
                print(f"[DCF模型调试] 使用增长率: {growth_rate:.2%}")

            # 获取不同情景下的增长率
            base_growth, optimistic_growth, pessimistic_growth = self.calculate_growth_rates()
            
            # 选择对应情景的增长率
            if scenario == 'optimistic':
                growth_rate = optimistic_growth
            elif scenario == 'pessimistic':
                growth_rate = pessimistic_growth
            
            # 预测未来5年现金流
            projected_cash_flows = []
            for i in range(5):
                fcf = current_fcf * (1 + growth_rate) ** (i + 1)
                projected_cash_flows.append(fcf)
            
            # 计算永续价值
            terminal_value = self.calculate_terminal_value(projected_cash_flows[-1], growth_rate, wacc)
            
            # 计算现值
            fcf_present_value = self.calculate_present_value(projected_cash_flows, wacc)
            terminal_present_value = terminal_value / ((1 + wacc) ** 5)
            
            # 计算企业价值
            enterprise_value = fcf_present_value + terminal_present_value
            
            # 获取净债务
            total_debt = float(self.overview.get('TotalDebt', 0))
            cash = float(self.overview.get('TotalCash', 0))
            net_debt = total_debt - cash
            
            # 计算股权价值
            equity_value = enterprise_value - net_debt
            
            # 计算每股价值
            shares_outstanding = float(self.overview.get('SharesOutstanding', 1))
            price_per_share = equity_value / shares_outstanding
            
            # 获取当前股价
            current_price = float(self.overview.get('MarketPrice', 0))
            if current_price <= 0:
                current_price = float(self.overview.get('Price', 0))
            
            # 计算上涨空间
            upside = ((price_per_share / current_price) - 1) * 100 if current_price > 0 else 0
            
            return {
                'scenario': scenario,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'price_per_share': price_per_share,
                'current_price': current_price,
                'upside': upside,
                'wacc': wacc,
                'growth_rate': growth_rate,
                'terminal_growth': self.terminal_growth_rate
            }
            
        except Exception as e:
            if debug:
                print(f"[DCF模型调试] 错误: {str(e)}")
            return {'error': str(e)} 