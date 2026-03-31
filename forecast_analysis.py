"""
业绩预告前瞻性分析模块 V1.0
=====================================

用于分析业绩预告的前瞻性价值，独立于正式财报评分。

核心功能：
1. 趋势判断：加速/持平/放缓
2. 确定性评估
3. 前瞻性结论
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import sys
sys.path.insert(0, '/Users/jw/.openclaw/workspace')

from stock_db_tool import get_stock_finance


def analyze_forecast_trend(stock_code: str) -> Dict:
    """
    业绩预告前瞻性趋势分析
    """
    finance_df = get_stock_finance(stock_code, limit=8)
    
    if finance_df is None or len(finance_df) == 0:
        return {'error': '无财务数据'}
    
    # 分离预告和正式财报
    forecast_row = None
    official_rows = []
    
    for i in range(len(finance_df)):
        row = finance_df.iloc[i]
        period = str(row.get('报告期', ''))
        
        if '预告' in period:
            if forecast_row is None:
                forecast_row = row
        else:
            official_rows.append(row)
    
    if forecast_row is None:
        return {
            'has_forecast': False,
            'message': '当前无业绩预告数据',
            'latest_official': official_rows[0]['报告期'] if official_rows else None
        }
    
    result = {
        'has_forecast': True,
        'forecast_period': forecast_row['报告期'],
        'analysis': {}
    }
    
    # 1. 预告基本信息
    forecast_info = extract_forecast_info(forecast_row)
    result['forecast_info'] = forecast_info
    
    # 2. 趋势分析
    if len(official_rows) >= 1:
        trend_analysis = analyze_growth_trend(forecast_info, official_rows)
        result['analysis']['trend'] = trend_analysis
    
    # 3. 确定性评估
    certainty = evaluate_forecast_certainty(forecast_info)
    result['analysis']['certainty'] = certainty
    
    # 4. 前瞻性结论
    conclusion = generate_forward_looking_conclusion(result)
    result['conclusion'] = conclusion
    
    return result


def extract_forecast_info(row: pd.Series) -> Dict:
    """提取预告核心信息"""
    
    def safe_float(val, default=0):
        if pd.isna(val) or str(val) in ['nan', 'None', '']:
            return default
        try:
            return float(val)
        except:
            return default
    
    info = {'period': row.get('报告期', '未知')}
    
    # 净利润预告
    net_profit = row.get('归母净利润(元)')
    if pd.notna(net_profit):
        np_str = str(net_profit)
        if '亿' in np_str:
            info['net_profit'] = float(np_str.replace('亿', '').strip())
        else:
            info['net_profit'] = safe_float(net_profit) / 1e8
    
    # 预告区间
    np_low = row.get('归母净利润_预告下限(万)')
    np_high = row.get('归母净利润_预告上限(万)')
    if pd.notna(np_low) and pd.notna(np_high):
        info['net_profit_low'] = safe_float(np_low) / 10000
        info['net_profit_high'] = safe_float(np_high) / 10000
        info['net_profit_mid'] = (info['net_profit_low'] + info['net_profit_high']) / 2
    
    # 增长率
    growth = row.get('归属净利润同比增长(%)')
    growth_low = row.get('归属净利润同比_预告下限(%)')
    growth_high = row.get('归属净利润同比_预告上限(%)')
    
    if pd.notna(growth):
        info['growth_rate'] = safe_float(growth)
    elif pd.notna(growth_low) and pd.notna(growth_high):
        info['growth_rate'] = (safe_float(growth_low) + safe_float(growth_high)) / 2
    
    if pd.notna(growth_low) and pd.notna(growth_high):
        info['growth_low'] = safe_float(growth_low)
        info['growth_high'] = safe_float(growth_high)
    
    return info


def analyze_growth_trend(forecast_info: Dict, official_rows: List) -> Dict:
    """分析增速趋势"""
    
    def safe_float(val, default=0):
        if pd.isna(val) or str(val) in ['nan', 'None', '']:
            return default
        try:
            return float(val)
        except:
            return default
    
    forecast_growth = forecast_info.get('growth_rate', 0)
    if forecast_growth == 0:
        forecast_growth = forecast_info.get('growth_mid', 0)
    
    historical_growth = []
    for row in official_rows[:4]:
        g = safe_float(row.get('归属净利润同比增长(%)'))
        if g != 0:
            historical_growth.append({
                'period': row['报告期'],
                'growth': g
            })
    
    if not historical_growth:
        return {'trend': 'unknown', 'message': '无历史数据对比'}
    
    latest_growth = historical_growth[0]['growth']
    diff = forecast_growth - latest_growth
    
    if diff > 10:
        trend = '加速'
        signal = 'positive'
        message = f"预告增速{forecast_growth:.1f}% > 前期{latest_growth:.1f}%，业绩加速向上 🔥"
    elif diff > -10:
        trend = '持平'
        signal = 'neutral'
        message = f"预告增速{forecast_growth:.1f}% ≈ 前期{latest_growth:.1f}%，增速平稳"
    else:
        trend = '放缓'
        signal = 'negative'
        message = f"预告增速{forecast_growth:.1f}% < 前期{latest_growth:.1f}%，增速放缓 ⚠️"
    
    return {
        'trend': trend,
        'signal': signal,
        'message': message,
        'forecast_growth': forecast_growth,
        'latest_growth': latest_growth,
        'diff': diff,
        'historical_growth': historical_growth
    }


def evaluate_forecast_certainty(forecast_info: Dict) -> Dict:
    """评估业绩确定性"""
    
    growth_low = forecast_info.get('growth_low')
    growth_high = forecast_info.get('growth_high')
    
    if growth_low is None or growth_high is None:
        return {'certainty': 'unknown', 'message': '无预告区间数据'}
    
    gap = growth_high - growth_low
    
    if gap <= 20:
        certainty = '高'
        score = 90
        message = f"预告区间差距{gap:.1f}个百分点，确定性强"
    elif gap <= 40:
        certainty = '中等'
        score = 70
        message = f"预告区间差距{gap:.1f}个百分点，确定性中等"
    else:
        certainty = '低'
        score = 50
        message = f"预告区间差距{gap:.1f}个百分点，不确定性较高"
    
    return {'certainty': certainty, 'score': score, 'gap': gap, 'message': message}


def generate_forward_looking_conclusion(result: Dict) -> Dict:
    """生成前瞻性结论"""
    
    analysis = result.get('analysis', {})
    signals = []
    insights = []
    risks = []
    
    trend = analysis.get('trend', {})
    if trend.get('trend') == '加速':
        signals.append('positive')
        insights.append(f"业绩加速：{trend.get('message')}")
    elif trend.get('trend') == '放缓':
        signals.append('negative')
        risks.append(f"增速放缓：{trend.get('message')}")
    
    certainty = analysis.get('certainty', {})
    if certainty.get('certainty') == '低':
        risks.append(f"确定性低：{certainty.get('message')}")
    elif certainty.get('certainty') == '高':
        insights.append(f"确定性强：{certainty.get('message')}")
    
    positive_count = signals.count('positive')
    negative_count = signals.count('negative')
    
    if positive_count > negative_count:
        outlook = 'positive'
        outlook_text = '偏多'
    elif negative_count > positive_count:
        outlook = 'negative'
        outlook_text = '偏空'
    else:
        outlook = 'neutral'
        outlook_text = '中性'
    
    return {
        'outlook': outlook,
        'outlook_text': outlook_text,
        'insights': insights,
        'risks': risks,
        'summary': f"业绩预告显示{trend.get('trend', '未知')}趋势，确定性{certainty.get('certainty', '未知')}"
    }