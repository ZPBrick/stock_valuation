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
        """设置模型默认参数"""
        # 获取行业和部门信息
        self.industry = self.overview.get('Industry', '').upper()
        self.sector = self.overview.get('Sector', '').upper()
        
        # 设置行业特定参数
        self.set_industry_parameters()
        
        # 设置通用参数
        self.risk_free_rate = 0.04  # 10年期美债收益率
        self.market_risk_premium = 0.06  # 市场风险溢价
        self.terminal_growth_rate = 0.02  # 永续增长率
        
    def set_industry_parameters(self):
        """根据行业设置特定参数"""
        # 默认参数
        self.beta = float(self.overview.get('Beta', 1.0))
        self.revenue_growth = 0.10
        self.fcf_margin = 0.15
        self.target_debt_ratio = 0.20
        
        # 科技行业
        if 'SOFTWARE' in self.industry or 'SEMICONDUCTOR' in self.industry:
            self.revenue_growth = 0.15
            self.fcf_margin = 0.20
            self.target_debt_ratio = 0.15
            
        # 制造业
        elif 'MANUFACTURING' in self.sector:
            self.revenue_growth = 0.08
            self.fcf_margin = 0.12
            self.target_debt_ratio = 0.30
            
        # 消费品行业
        elif 'CONSUMER' in self.sector:
            self.revenue_growth = 0.06
            self.fcf_margin = 0.10
            self.target_debt_ratio = 0.25
    
    def calculate_wacc(self) -> float:
        """计算加权平均资本成本(WACC)"""
        try:
            # 计算股权成本
            cost_of_equity = self.risk_free_rate + self.beta * self.market_risk_premium
            
            # 获取当前负债成本
            total_debt = float(self.overview.get('TotalDebt', 0))
            interest_expense = float(self.overview.get('InterestExpense', 0))
            cost_of_debt = 0.04  # 默认负债成本
            
            if total_debt > 0 and interest_expense > 0:
                cost_of_debt = min(interest_expense / total_debt, 0.10)  # 限制最高10%
            
            # 获取市值
            market_cap = float(self.overview.get('MarketCapitalization', 0))
            
            # 计算目标资本结构
            total_capital = market_cap + total_debt
            if total_capital > 0:
                debt_ratio = min(total_debt / total_capital, self.target_debt_ratio)
            else:
                debt_ratio = self.target_debt_ratio
            
            equity_ratio = 1 - debt_ratio
            
            # 计算WACC
            tax_rate = 0.21  # 假设美国企业税率21%
            wacc = equity_ratio * cost_of_equity + debt_ratio * cost_of_debt * (1 - tax_rate)
            
            return min(max(wacc, 0.06), 0.15)  # 限制WACC在6%-15%之间
            
        except Exception as e:
            print(f"计算WACC时出错: {str(e)}")
            return 0.10  # 返回默认值
    
    def get_historical_fcf(self) -> List[float]:
        """获取历史自由现金流"""
        try:
            cash_flow = self.financials.get('cash_flow', [])
            fcf_list = []
            
            for year_data in cash_flow:
                operating_cash_flow = float(year_data.get('operatingCashflow', 0))
                capex = float(year_data.get('capitalExpenditures', 0))
                fcf = operating_cash_flow + capex  # capex通常为负值
                fcf_list.append(fcf)
            
            return fcf_list
            
        except Exception as e:
            print(f"获取历史自由现金流时出错: {str(e)}")
            return []
    
    def calculate_growth_rates(self) -> Tuple[float, float, float]:
        """计算不同情景下的增长率"""
        try:
            # 获取历史增长数据
            fcf_list = self.get_historical_fcf()
            if len(fcf_list) >= 2:
                # 计算历史增长率
                growth_rates = []
                for i in range(1, len(fcf_list)):
                    if fcf_list[i-1] > 0 and fcf_list[i] > 0:
                        growth_rate = (fcf_list[i] / fcf_list[i-1]) - 1
                        growth_rates.append(growth_rate)
                
                if growth_rates:
                    avg_growth = np.mean(growth_rates)
                    std_growth = np.std(growth_rates)
                    
                    # 基准情景：行业预期增长率
                    base_growth = self.revenue_growth
                    
                    # 乐观情景：历史平均增长率和行业预期的较高值
                    optimistic_growth = max(base_growth, min(avg_growth + std_growth, base_growth * 1.5))
                    
                    # 悲观情景：行业预期的一半
                    pessimistic_growth = base_growth * 0.5
                    
                    return base_growth, optimistic_growth, pessimistic_growth
            
            # 如果没有足够的历史数据，使用默认值
            return self.revenue_growth, self.revenue_growth * 1.5, self.revenue_growth * 0.5
            
        except Exception as e:
            print(f"计算增长率时出错: {str(e)}")
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
    
    def value(self, scenario: str = 'base') -> Dict:
        """
        执行DCF估值
        
        Args:
            scenario (str): 情景类型 ('base', 'optimistic', 'pessimistic')
            
        Returns:
            Dict: 包含估值结果的字典
        """
        try:
            # 获取当前自由现金流
            fcf_list = self.get_historical_fcf()
            if not fcf_list:
                return {'error': '无法获取历史现金流数据'}
            
            current_fcf = fcf_list[0] if fcf_list else 0
            if current_fcf <= 0:
                return {'error': '当前自由现金流为负或为零'}
            
            # 计算WACC
            wacc = self.calculate_wacc()
            
            # 获取不同情景下的增长率
            base_growth, optimistic_growth, pessimistic_growth = self.calculate_growth_rates()
            
            # 选择对应情景的增长率
            if scenario == 'optimistic':
                growth_rate = optimistic_growth
            elif scenario == 'pessimistic':
                growth_rate = pessimistic_growth
            else:
                growth_rate = base_growth
            
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
            return {'error': f'估值计算出错: {str(e)}'} 