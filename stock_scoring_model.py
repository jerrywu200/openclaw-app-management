"""
股票综合评分模型 V3.5
整合六维度评分：基本面、行业前景、估值、技术面、事件驱动、市场环境

维度权重：
- 基本面评分：20%（仅使用正式财报数据，最新优先）
- 行业前景评分：20%（整合概念强度+板块热度+共振）
- 估值评分：15%（PE(TTM)使用TTM EPS计算）
- 技术面评分：15%（手动计算MACD/KDJ/布林带）
- 事件驱动评分：15%
- 市场环境评分：15%

V3.5更新（Phase 1）：
- 🔥 新增财务趋势分析：判断指标改善/恶化
- 基本面评分 = 当期评分 + 趋势评分
- 趋势评分范围：-19 ~ +19分

V3.4更新（🔥 重大修正）：
- 使用统一过滤函数（finance_data_filter模块）
- 数据源选择：**最新优先**（不是年报优先）
- 如果当年度季报比年报新 → 用季报（年报待发布）
- 如果年报是最新 → 用年报
- 核心原则：永远使用最新可用的正式财报数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import sys

# 添加工作空间路径
sys.path.insert(0, '/Users/jw/.openclaw/workspace')

from stock_db_tool import (
    get_stock_kline,
    get_stock_finance,
    get_stock_fund_flow,
    get_stock_highest_lowest_price,
    get_stock_concept_detail,
    get_stock_news,
    get_hot_concepts,
    get_global_index
)

from event_driven_analysis import calculate_event_score
from concept_strength_analysis import (
    calculate_concept_strength_score,
    analyze_stock_sector_resonance
)

# 🔥 V3.4新增：导入统一过滤函数
from finance_data_filter import (
    classify_finance_data,
    filter_official_reports,
    get_best_analysis_data,
    get_ttm_calculation_data,
    check_data_availability,
    generate_data_quality_report,
    # 🔥 V3.5新增：趋势分析函数
    analyze_financial_trend
)

# 尝试导入业绩预告前瞻性分析模块
try:
    from forecast_analysis import analyze_forecast_trend
    FORECAST_ANALYSIS_AVAILABLE = True
except ImportError:
    FORECAST_ANALYSIS_AVAILABLE = False

# 🔥 V3.5 Phase 5新增：持续跟踪模块
try:
    from tracking_monitor import record_score_history, check_alerts
    TRACKING_AVAILABLE = True
except ImportError:
    TRACKING_AVAILABLE = False


# ============================================================
# 一、基本面评分（权重20%）
# ============================================================

def calculate_fundamental_score(stock_code: str) -> Dict:
    """
    计算基本面评分（仅使用正式财报数据）
    
    🔥 V3.4更新：使用统一过滤函数，最新优先
    
    注意：业绩预告数据不参与评分，仅用于前瞻性洞察分析
    
    评分维度：
    1. 盈利能力（30分）：ROE、毛利率、净利率
    2. 成长能力（25分）：营收增长、利润增长
    3. 偿债能力（20分）：资产负债率、流动比率
    4. 运营能力（15分）：存货周转、应收账款周转
    5. 现金流（10分）：经营现金流
    
    Returns:
        dict: {
            'fundamental_score': 基本面评分（0-100）,
            'profit_score': 盈利能力评分,
            'growth_score': 成长能力评分,
            'solvency_score': 偿债能力评分,
            'operation_score': 运营能力评分,
            'cashflow_score': 现金流评分,
            'details': 详细数据,
            'data_source': 数据来源,
            'report_period': 报告期
        }
    """
    # 获取财务数据
    finance_df = get_stock_finance(stock_code, limit=10)
    
    if len(finance_df) == 0:
        return {
            'fundamental_score': 0,
            'message': '无财务数据',
            'data_status': 'no_data'
        }
    
    # 🔥 V3.4: 使用统一过滤函数获取最佳分析数据源（最新优先）
    best_data, source_message = get_best_analysis_data(finance_df)
    
    if best_data is None:
        # 无正式财报，无法评分
        return {
            'fundamental_score': 0,
            'message': source_message,  # "无正式财报数据"
            'data_status': 'forecast_only',
            'suggestion': '仅有业绩预告，建议等待正式财报发布后再进行评分'
        }
    
    # 使用最新正式财报进行评分
    latest = best_data
    report_period = latest['报告期']
    data_source = source_message
    
    # 判断数据类型（年报/季报）
    is_annual = '年报' in report_period
    data_type = '年报' if is_annual else '季报'
    
    # 1. 盈利能力评分（30分）
    profit_score = 0
    profit_details = {}
    
    # ROE评分（15分）
    roe = latest.get('净资产收益率(加权)(%)', 0)
    if pd.notna(roe):
        if roe >= 20:
            roe_score = 15
        elif roe >= 15:
            roe_score = 12
        elif roe >= 10:
            roe_score = 8
        elif roe >= 5:
            roe_score = 5
        else:
            roe_score = max(0, roe / 5 * 5)
        profit_score += roe_score
        profit_details['roe'] = roe
    
    # 毛利率评分（8分）
    gross_margin = latest.get('毛利率(%)', 0)
    if pd.notna(gross_margin):
        if gross_margin >= 40:
            gm_score = 8
        elif gross_margin >= 30:
            gm_score = 6
        elif gross_margin >= 20:
            gm_score = 4
        else:
            gm_score = max(0, gross_margin / 20 * 4)
        profit_score += gm_score
        profit_details['gross_margin'] = gross_margin
    
    # 净利率评分（7分）
    net_margin = latest.get('净利率(%)', 0)
    if pd.notna(net_margin):
        if net_margin >= 15:
            nm_score = 7
        elif net_margin >= 10:
            nm_score = 5
        elif net_margin >= 5:
            nm_score = 3
        else:
            nm_score = max(0, net_margin / 10 * 3)
        profit_score += nm_score
        profit_details['net_margin'] = net_margin
    
    # 2. 成长能力评分（25分）
    growth_score = 0
    growth_details = {}
    
    # 营收增长评分（12分）
    revenue_growth = latest.get('营业总收入同比增长(%)', 0)
    if pd.notna(revenue_growth):
        if revenue_growth >= 30:
            rg_score = 12
        elif revenue_growth >= 20:
            rg_score = 9
        elif revenue_growth >= 10:
            rg_score = 6
        elif revenue_growth >= 0:
            rg_score = 3
        else:
            rg_score = max(0, 3 + revenue_growth / 10)
        growth_score += rg_score
        growth_details['revenue_growth'] = revenue_growth
    
    # 利润增长评分（13分）
    profit_growth = latest.get('归属净利润同比增长(%)', 0)
    if pd.notna(profit_growth):
        if profit_growth >= 30:
            pg_score = 13
        elif profit_growth >= 20:
            pg_score = 10
        elif profit_growth >= 10:
            pg_score = 7
        elif profit_growth >= 0:
            pg_score = 4
        else:
            pg_score = max(0, 4 + profit_growth / 10)
        growth_score += pg_score
        growth_details['profit_growth'] = profit_growth
    
    # 3. 偿债能力评分（20分）
    solvency_score = 0
    solvency_details = {}
    
    # 资产负债率评分（12分）
    debt_ratio = latest.get('资产负债率(%)', 0)
    if pd.notna(debt_ratio):
        if debt_ratio <= 40:
            dr_score = 12
        elif debt_ratio <= 50:
            dr_score = 10
        elif debt_ratio <= 60:
            dr_score = 7
        elif debt_ratio <= 70:
            dr_score = 4
        else:
            dr_score = max(0, 4 - (debt_ratio - 70) / 5)
        solvency_score += dr_score
        solvency_details['debt_ratio'] = debt_ratio
    
    # 流动比率评分（8分）
    current_ratio = latest.get('流动比率', 0)
    if pd.notna(current_ratio):
        if current_ratio >= 2:
            cr_score = 8
        elif current_ratio >= 1.5:
            cr_score = 6
        elif current_ratio >= 1:
            cr_score = 4
        else:
            cr_score = max(0, current_ratio * 4)
        solvency_score += cr_score
        solvency_details['current_ratio'] = current_ratio
    
    # 4. 运营能力评分（15分）
    operation_score = 0
    operation_details = {}
    
    # 存货周转天数评分（8分）
    inventory_days = latest.get('存货周转天数(天)', 0)
    if pd.notna(inventory_days) and inventory_days > 0:
        if inventory_days <= 60:
            id_score = 8
        elif inventory_days <= 90:
            id_score = 6
        elif inventory_days <= 120:
            id_score = 4
        else:
            id_score = max(0, 4 - (inventory_days - 120) / 30)
        operation_score += id_score
        operation_details['inventory_days'] = inventory_days
    
    # 应收账款周转天数评分（7分）
    ar_days = latest.get('应收账款周转天数(天)', 0)
    if pd.notna(ar_days) and ar_days > 0:
        if ar_days <= 60:
            ar_score = 7
        elif ar_days <= 90:
            ar_score = 5
        elif ar_days <= 120:
            ar_score = 3
        else:
            ar_score = max(0, 3 - (ar_days - 120) / 30)
        operation_score += ar_score
        operation_details['ar_days'] = ar_days
    
    # 5. 现金流评分（10分）
    cashflow_score = 0
    cashflow_details = {}
    
    # 经营现金流评分（基于净现比）
    # 净现比 = 经营现金流 / 净利润
    # 这里简化处理，使用财务健康度判断
    if profit_score >= 20 and solvency_score >= 15:
        cashflow_score = 10  # 财务健康，现金流可能良好
    elif profit_score >= 15 and solvency_score >= 10:
        cashflow_score = 7
    else:
        cashflow_score = 5
    
    # 🔥 V3.5新增：财务趋势分析
    # 获取更多期财务数据用于趋势分析
    finance_df_full = get_stock_finance(stock_code, limit=15)
    trend_result = analyze_financial_trend(finance_df_full, years=3)
    
    if trend_result['available']:
        trend_score = trend_result['total_trend_score']
        trend_summary = trend_result['trend_summary']
        trend_grade = trend_result['trend_grade']
        trend_data_type = trend_result['data_type']
        trend_confidence = trend_result['confidence']
    else:
        trend_score = 0
        trend_summary = trend_result.get('message', '趋势数据不足')
        trend_grade = 'N/A'
        trend_data_type = 'N/A'
        trend_confidence = '低'
    
    # 汇总：当期评分 + 趋势评分
    current_score = profit_score + growth_score + solvency_score + operation_score + cashflow_score
    total_score = current_score + trend_score
    
    # 限制分数范围（0-100）
    total_score = max(0, min(100, total_score))
    
    # 🔥 V3.5 Phase 2: 置信度计算
    # 构建基本面结果字典
    fundamental_result_for_confidence = {
        'data_type': data_type,
        'report_period': report_period,
        'data_source': data_source,
        'details': {
            'profit': profit_details,
            'growth': growth_details,
            'solvency': solvency_details,
            'operation': operation_details
        }
    }
    
    # 计算置信度
    confidence = calculate_confidence(fundamental_result_for_confidence, trend_result)
    
    return {
        'fundamental_score': round(total_score, 2),
        'current_score': round(current_score, 2),  # 🔥 V3.5新增：当期评分
        'trend_score': round(trend_score, 2),      # 🔥 V3.5新增：趋势评分
        'profit_score': round(profit_score, 2),
        'growth_score': round(growth_score, 2),
        'solvency_score': round(solvency_score, 2),
        'operation_score': round(operation_score, 2),
        'cashflow_score': round(cashflow_score, 2),
        'details': {
            'profit': profit_details,
            'growth': growth_details,
            'solvency': solvency_details,
            'operation': operation_details
        },
        # 🔥 V3.5新增：趋势详情
        'trend_analysis': {
            'available': trend_result['available'],
            'trend_summary': trend_summary,
            'trend_grade': trend_grade,
            'trend_data_type': trend_data_type,
            'trend_confidence': trend_confidence,
            'roe_trend': trend_result.get('roe_trend', {}),
            'gross_margin_trend': trend_result.get('gross_margin_trend', {}),
            'net_margin_trend': trend_result.get('net_margin_trend', {}),
            'revenue_growth_trend': trend_result.get('revenue_growth_trend', {}),
            'profit_growth_trend': trend_result.get('profit_growth_trend', {})
        },
        'grade': 'A' if total_score >= 80 else ('B' if total_score >= 60 else ('C' if total_score >= 40 else 'D')),
        'data_source': data_source,  # 🔥 V3.4: "2025三季报（年报待发布）" 或 "2025年报"
        'report_period': report_period,
        'data_type': data_type,  # "年报" 或 "季报"
        'data_status': 'official_report',  # 正式财报
        'is_annual': is_annual,  # 是否为年报
        
        # 🔥 V3.5 Phase 2新增：置信度
        'confidence': confidence
    }


# ============================================================
# V3.5 Phase 2: 评分置信度机制
# ============================================================

def calculate_data_completeness(fundamental_result: Dict, trend_result: Dict) -> Dict:
    """
    计算数据完整度（置信度维度1）
    
    Args:
        fundamental_result: 基本面评分结果
        trend_result: 趋势分析结果
    
    Returns:
        dict: {
            'score': 0-100,
            'level': '高'/'中'/'低',
            'factors': {...}
        }
    """
    factors = {}
    
    # 1. 是否有正式财报（40分）
    data_type = fundamental_result.get('data_type', '')
    if data_type == '年报':
        factors['report_type'] = {'score': 40, 'message': '有年报数据'}
    elif data_type == '季报':
        factors['report_type'] = {'score': 30, 'message': '有季报数据（年报待发布）'}
    else:
        factors['report_type'] = {'score': 0, 'message': '无正式财报'}
    
    # 2. 关键指标是否齐全（30分）
    details = fundamental_result.get('details', {})
    key_metrics = ['profit', 'growth', 'solvency', 'operation']
    available_metrics = sum(1 for m in key_metrics if m in details and details[m])
    
    metric_score = int(available_metrics / len(key_metrics) * 30)
    factors['key_metrics'] = {
        'score': metric_score,
        'message': f'{available_metrics}/{len(key_metrics)}类指标可用'
    }
    
    # 3. 趋势分析数据是否充足（30分）
    if trend_result.get('available'):
        if trend_result.get('data_type') == '年报':
            factors['trend_data'] = {'score': 30, 'message': '趋势分析数据完整（年报）'}
        else:
            factors['trend_data'] = {'score': 20, 'message': '趋势分析数据可用'}
    else:
        factors['trend_data'] = {'score': 0, 'message': '趋势分析数据不足'}
    
    score = sum(f['score'] for f in factors.values())
    
    return {
        'score': score,
        'level': '高' if score >= 80 else ('中' if score >= 60 else '低'),
        'factors': factors
    }


def calculate_data_timeliness(report_period: str) -> Dict:
    """
    计算数据时效性（置信度维度2）
    
    Args:
        report_period: 报告期（如"2025年报"）
    
    Returns:
        dict: {
            'score': 0-100,
            'level': '高'/'中'/'低',
            'message': str
        }
    """
    from datetime import datetime
    
    if not report_period:
        return {
            'score': 30,
            'level': '低',
            'message': '无报告期信息'
        }
    
    today = datetime.now()
    report_period = str(report_period)
    
    # 从报告期推断预期发布时间
    try:
        if '年报' in report_period:
            year = int(report_period[:4])
            expected_publish = datetime(year + 1, 4, 30)
        elif '三季报' in report_period:
            year = int(report_period[:4])
            expected_publish = datetime(year, 10, 31)
        elif '中报' in report_period or '半年报' in report_period:
            year = int(report_period[:4])
            expected_publish = datetime(year, 8, 31)
        elif '一季报' in report_period:
            year = int(report_period[:4])
            expected_publish = datetime(year, 4, 30)
        else:
            # 无法识别，使用保守估计
            return {
                'score': 50,
                'level': '中',
                'message': '报告期格式未知'
            }
        
        # 计算距今天数
        days_diff = (today - expected_publish).days
        
        # 时效性评分
        if days_diff < 0:
            score = 60
            message = "报告期未到，可能使用预告数据"
        elif days_diff < 30:
            score = 100
            message = "刚发布的财报，数据新鲜"
        elif days_diff < 90:
            score = 90
            message = "较新的财报"
        elif days_diff < 180:
            score = 70
            message = "时效性一般"
        elif days_diff < 365:
            score = 50
            message = "较旧的财报"
        else:
            score = 30
            message = "严重过时的数据"
        
        return {
            'score': score,
            'level': '高' if score >= 80 else ('中' if score >= 60 else '低'),
            'message': message,
            'days_since_publish': max(0, days_diff)
        }
    except:
        return {
            'score': 50,
            'level': '中',
            'message': '报告期解析失败'
        }


def calculate_data_consistency(trend_result: Dict) -> Dict:
    """
    计算数据一致性（置信度维度3）
    
    Args:
        trend_result: 趋势分析结果
    
    Returns:
        dict: {
            'score': 0-100,
            'level': '高'/'中'/'低',
            'message': str,
            'trend_direction': str
        }
    """
    if not trend_result or not trend_result.get('available'):
        return {
            'score': 50,
            'level': '中',
            'message': '趋势数据不足，无法判断一致性',
            'trend_direction': 'unknown'
        }
    
    # 统计各指标趋势方向
    positive_count = 0
    negative_count = 0
    
    indicators = ['roe_trend', 'gross_margin_trend', 'net_margin_trend',
                  'revenue_growth_trend', 'profit_growth_trend']
    
    for indicator in indicators:
        if indicator in trend_result:
            adj = trend_result[indicator].get('score_adjustment', 0)
            if adj > 0:
                positive_count += 1
            elif adj < 0:
                negative_count += 1
    
    # 一致性评分
    if positive_count >= 4:
        score = 100
        message = "趋势高度一致：多数指标改善"
        direction = 'improving'
    elif negative_count >= 4:
        score = 100
        message = "趋势高度一致：多数指标恶化"
        direction = 'worsening'
    elif positive_count >= 3:
        score = 80
        message = "趋势基本一致：多数指标改善"
        direction = 'improving'
    elif negative_count >= 3:
        score = 80
        message = "趋势基本一致：多数指标恶化"
        direction = 'worsening'
    elif positive_count == 2 and negative_count == 2:
        score = 60
        message = "趋势分化：改善与恶化并存"
        direction = 'mixed'
    elif positive_count == 2 and negative_count == 1:
        score = 70
        message = "趋势偏正面：多数指标改善"
        direction = 'improving'
    elif negative_count == 2 and positive_count == 1:
        score = 70
        message = "趋势偏负面：多数指标恶化"
        direction = 'worsening'
    else:
        score = 50
        message = "趋势不明确"
        direction = 'mixed'
    
    return {
        'score': score,
        'level': '高' if score >= 80 else ('中' if score >= 60 else '低'),
        'message': message,
        'trend_direction': direction,
        'positive_count': positive_count,
        'negative_count': negative_count
    }


def calculate_confidence(fundamental_result: Dict, trend_result: Dict) -> Dict:
    """
    计算评分置信度（V3.5 Phase 2核心函数）
    
    置信度 = 完整度×40% + 时效性×30% + 一致性×30%
    
    Args:
        fundamental_result: 基本面评分结果
        trend_result: 趋势分析结果
    
    Returns:
        dict: {
            'score': 0-100,
            'level': str,
            'icon': str,
            'message': str,
            'decision_guidance': str,
            'completeness': {...},
            'timeliness': {...},
            'consistency': {...}
        }
    """
    
    # 1. 计算数据完整度
    completeness = calculate_data_completeness(fundamental_result, trend_result)
    
    # 2. 计算数据时效性
    report_period = fundamental_result.get('report_period', '')
    timeliness = calculate_data_timeliness(report_period)
    
    # 3. 计算数据一致性
    consistency = calculate_data_consistency(trend_result)
    
    # 4. 加权计算总置信度
    total_score = (
        completeness['score'] * 0.4 +
        timeliness['score'] * 0.3 +
        consistency['score'] * 0.3
    )
    
    # 5. 确定评级
    if total_score >= 85:
        level = '高'
        icon = '✅'
        message = "数据完整、新鲜、一致，评分可信"
        guidance = "可以作为主要决策依据"
    elif total_score >= 70:
        level = '中高'
        icon = '🟢'
        message = "数据质量较好，评分较可信"
        guidance = "可以作为重要参考，建议结合其他分析"
    elif total_score >= 55:
        level = '中'
        icon = '🟡'
        message = "数据质量一般，评分需谨慎参考"
        guidance = "仅作参考，需进一步验证"
    elif total_score >= 40:
        level = '中低'
        icon = '🟠'
        message = "数据存在明显缺陷，评分参考价值有限"
        guidance = "不建议作为决策依据"
    else:
        level = '低'
        icon = '🔴'
        message = "数据严重不足或过期，评分不可信"
        guidance = "需要等待更多数据"
    
    return {
        'score': round(total_score, 1),
        'level': level,
        'icon': icon,
        'message': message,
        'decision_guidance': guidance,
        'completeness': completeness,
        'timeliness': timeliness,
        'consistency': consistency
    }


# ============================================================
# V3.5 Phase 3: 同行估值对比
# ============================================================

def get_stock_industry(stock_code: str) -> str:
    """
    获取股票所属行业（东方财富行业分类）
    
    Args:
        stock_code: 股票代码（如"603993"）
    
    Returns:
        str: 行业名称（如"能源金属"）
    """
    try:
        import akshare as ak
        
        # 标准化股票代码
        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # 获取东方财富行业分类列表
        df = ak.stock_board_industry_name_em()
        
        # 查找该股票所属行业
        for _, row in df.iterrows():
            industry_name = row['板块名称']
            try:
                # 获取该行业的成分股
                cons = ak.stock_board_industry_cons_em(symbol=industry_name)
                if code in cons['代码'].values:
                    return industry_name
            except:
                continue
        
        return "未知行业"
    except Exception as e:
        return "未知行业"


def get_industry_peers_valuation(stock_code: str, limit: int = 5) -> Dict:
    """
    获取同行估值对比数据（简化版，减少API调用）
    
    Args:
        stock_code: 股票代码
        limit: 同行数量限制（默认5个，减少API调用）
    
    Returns:
        dict: 同行估值数据
    """
    try:
        import akshare as ak
        
        # 标准化股票代码
        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # 1. 获取股票所属行业
        industry = get_stock_industry(code)
        
        if industry == "未知行业":
            return {
                'available': False,
                'message': '无法获取行业分类'
            }
        
        # 2. 获取同行股票（使用东方财富接口）
        try:
            peers_df = ak.stock_board_industry_cons_em(symbol=industry)
        except:
            return {
                'available': False,
                'industry': industry,
                'message': '无法获取同行数据'
            }
        
        if len(peers_df) == 0:
            return {
                'available': False,
                'industry': industry,
                'message': '同行数据为空'
            }
        
        # 3. 批量获取估值数据（只取前limit个同行，减少API调用）
        peers_codes = peers_df['代码'].head(limit).tolist()
        results = []
        
        for peer_code in peers_codes:
            try:
                # 获取估值指标
                indicator = ak.stock_a_lg_indicator(symbol=peer_code)
                
                if len(indicator) > 0:
                    latest = indicator.iloc[0]
                    
                    pe_val = latest.get('市盈率')
                    pb_val = latest.get('市净率')
                    roe_val = latest.get('净资产收益率')
                    
                    results.append({
                        'code': peer_code,
                        'name': latest.get('股票简称', ''),
                        'pe_ttm': float(pe_val) if pd.notna(pe_val) and float(pe_val) > 0 else None,
                        'pb': float(pb_val) if pd.notna(pb_val) and float(pb_val) > 0 else None,
                        'roe': float(roe_val) if pd.notna(roe_val) else None
                    })
            except Exception:
                continue
        
        if len(results) < 3:  # 至少需要3个同行数据
            return {
                'available': False,
                'industry': industry,
                'message': f'同行估值数据不足（仅{len(results)}个）'
            }
        
        peers_result_df = pd.DataFrame(results)
        
        # 4. 计算行业平均（过滤异常值）
        valid_pe = peers_result_df[(peers_result_df['pe_ttm'].notna()) & (peers_result_df['pe_ttm'] < 200)]
        valid_pb = peers_result_df[(peers_result_df['pb'].notna()) & (peers_result_df['pb'] < 50)]
        valid_roe = peers_result_df[peers_result_df['roe'].notna()]
        
        industry_avg = {
            'pe': round(valid_pe['pe_ttm'].mean(), 2) if len(valid_pe) >= 2 else None,
            'pb': round(valid_pb['pb'].mean(), 2) if len(valid_pb) >= 2 else None,
            'roe': round(valid_roe['roe'].mean(), 2) if len(valid_roe) >= 2 else None,
            'peers_count': len(peers_result_df)
        }
        
        # 5. 获取当前股票数据
        stock_data = peers_result_df[peers_result_df['code'] == code]
        
        if len(stock_data) == 0:
            # 当前股票不在同行数据中，单独获取
            try:
                indicator = ak.stock_a_lg_indicator(symbol=code)
                if len(indicator) > 0:
                    latest = indicator.iloc[0]
                    pe_val = latest.get('市盈率')
                    pb_val = latest.get('市净率')
                    roe_val = latest.get('净资产收益率')
                    stock_data = {
                        'code': code,
                        'name': latest.get('股票简称', ''),
                        'pe_ttm': float(pe_val) if pd.notna(pe_val) and float(pe_val) > 0 else None,
                        'pb': float(pb_val) if pd.notna(pb_val) and float(pb_val) > 0 else None,
                        'roe': float(roe_val) if pd.notna(roe_val) else None
                    }
                else:
                    stock_data = None
            except:
                stock_data = None
        else:
            stock_data = stock_data.iloc[0].to_dict()
        
        return {
            'available': True,
            'industry': industry,
            'stock_data': stock_data,
            'industry_avg': industry_avg,
            'peers_count': len(peers_result_df),
            'message': f"成功获取{industry}行业{len(peers_result_df)}家同行数据"
        }
        
    except Exception as e:
        return {
            'available': False,
            'message': f'获取同行数据失败: {str(e)}'
        }


def calculate_relative_valuation_score(
    stock_pe: float,
    stock_pb: float,
    stock_roe: float,
    industry_avg_pe: float,
    industry_avg_pb: float,
    industry_avg_roe: float
) -> Dict:
    """
    计算相对估值评分
    
    Args:
        stock_pe: 股票PE(TTM)
        stock_pb: 股票PB
        stock_roe: 股票ROE
        industry_avg_pe: 行业平均PE
        industry_avg_pb: 行业平均PB
        industry_avg_roe: 行业平均ROE
    
    Returns:
        dict: 相对估值评分详情
    """
    
    # 检查数据有效性
    if not industry_avg_pe or industry_avg_pe <= 0:
        return {
            'available': False,
            'total_relative_score': 0,
            'message': '行业数据无效'
        }
    
    if not stock_pe or stock_pe <= 0:
        return {
            'available': False,
            'total_relative_score': 0,
            'message': '股票估值数据无效'
        }
    
    # 1. 计算PE相对位置
    pe_diff_pct = (stock_pe - industry_avg_pe) / industry_avg_pe * 100
    
    if pe_diff_pct <= -20:
        pe_score = 20
        pe_position = "显著低估"
        pe_icon = "✅✅"
    elif pe_diff_pct <= -10:
        pe_score = 15
        pe_position = "偏低"
        pe_icon = "✅"
    elif pe_diff_pct <= 10:
        pe_score = 10
        pe_position = "合理"
        pe_icon = "→"
    elif pe_diff_pct <= 30:
        pe_score = 5
        pe_position = "偏高"
        pe_icon = "⚠️"
    else:
        pe_score = 0
        pe_position = "显著高估"
        pe_icon = "❌"
    
    # 2. 计算PB-ROE匹配度
    pb_roe_score = 0
    pb_roe_match = "数据不足"
    match_icon = "❓"
    
    if industry_avg_pb and industry_avg_pb > 0 and industry_avg_roe:
        pb_diff_pct = (stock_pb - industry_avg_pb) / industry_avg_pb * 100
        roe_diff_pct = (stock_roe - industry_avg_roe) / industry_avg_roe * 100
        
        if pb_diff_pct <= 0 and roe_diff_pct > 0:
            pb_roe_score = 10
            pb_roe_match = "高性价比"
            match_icon = "🔥"
        elif abs(pb_diff_pct) <= 20 and roe_diff_pct > 0:
            pb_roe_score = 7
            pb_roe_match = "合理"
            match_icon = "✅"
        elif pb_diff_pct > 0 and roe_diff_pct > 0:
            pb_roe_score = 5
            pb_roe_match = "偏贵但合理"
            match_icon = "→"
        elif pb_diff_pct > 0 and roe_diff_pct <= 0:
            pb_roe_score = 0
            pb_roe_match = "高估"
            match_icon = "⚠️"
        else:
            pb_roe_score = 5
            pb_roe_match = "一般"
            match_icon = "→"
    
    # 3. 综合评分
    total_score = pe_score + pb_roe_score
    
    # 4. 综合结论
    if total_score >= 25:
        conclusion = "相对显著低估，具备投资价值"
    elif total_score >= 20:
        conclusion = "相对低估，值得关注"
    elif total_score >= 15:
        conclusion = "估值合理，可持有"
    elif total_score >= 10:
        conclusion = "估值偏高，谨慎参与"
    else:
        conclusion = "相对高估，风险较大"
    
    return {
        'available': True,
        'pe_relative_score': pe_score,
        'pb_roe_match_score': pb_roe_score,
        'total_relative_score': total_score,
        'pe_position': f"{pe_icon} {pe_position}",
        'pb_roe_match': f"{match_icon} {pb_roe_match}",
        'pe_diff_pct': round(pe_diff_pct, 1),
        'pb_diff_pct': round((stock_pb - industry_avg_pb) / industry_avg_pb * 100, 1) if industry_avg_pb else None,
        'roe_diff_pct': round((stock_roe - industry_avg_roe) / industry_avg_roe * 100, 1) if industry_avg_roe else None,
        'conclusion': conclusion
    }


# ============================================================
# V3.5 Phase 4: 五维风险评分
# ============================================================

# 行业风险映射表
INDUSTRY_RISK_MAP = {
    '低风险': ['AI', '人工智能', '半导体', '芯片', '新能源', '光伏', '储能', '锂电', '科技', '电子'],
    '中低风险': ['消费', '医药', '医疗', '食品饮料', '家电', '汽车', '白酒'],
    '中等风险': ['银行', '保险', '地产', '基建', '公用事业', '电信', '通信'],
    '中高风险': ['有色金属', '煤炭', '钢铁', '化工', '水泥', '航运', '钼', '锂'],
    '高风险': ['传统零售', '纸媒', '传统能源']
}


def calculate_financial_risk_score(debt_ratio: float, current_ratio: float = None) -> Dict:
    """
    计算财务风险评分
    
    Args:
        debt_ratio: 资产负债率
        current_ratio: 流动比率
    
    Returns:
        dict: 财务风险详情
    """
    if debt_ratio is None:
        return {'score': 50, 'level': '中', 'message': '数据缺失'}
    
    # 基础分（资产负债率）
    if debt_ratio <= 40:
        base_score = debt_ratio / 40 * 20
    elif debt_ratio <= 60:
        base_score = 20 + (debt_ratio - 40) / 20 * 40
    else:
        base_score = 60 + min(40, (debt_ratio - 60) / 20 * 40)
    
    # 流动比率调整
    adjustment = 0
    if current_ratio:
        if current_ratio < 1:
            adjustment += 15
        elif current_ratio >= 2:
            adjustment -= 10
    
    score = max(0, min(100, base_score + adjustment))
    
    return {
        'score': round(score, 1),
        'level': '低' if score < 30 else ('中低' if score < 50 else ('中' if score < 70 else ('中高' if score < 85 else '高'))),
        'factors': {'debt_ratio': debt_ratio, 'current_ratio': current_ratio}
    }


def calculate_valuation_risk_score(peg: float, pe_percentile: float = None) -> Dict:
    """
    计算估值风险评分
    
    Args:
        peg: PEG值
        pe_percentile: PE历史分位
    
    Returns:
        dict: 估值风险详情
    """
    if peg is None or peg <= 0:
        peg_score = 50
    elif peg <= 0.8:
        peg_score = peg / 0.8 * 20
    elif peg <= 1.5:
        peg_score = 20 + (peg - 0.8) / 0.7 * 40
    elif peg <= 2.0:
        peg_score = 60 + (peg - 1.5) / 0.5 * 20
    else:
        peg_score = min(100, 80 + (peg - 2.0) * 10)
    
    # PE分位调整
    adjustment = 0
    if pe_percentile:
        if pe_percentile > 80:
            adjustment = 15
        elif pe_percentile > 60:
            adjustment = 5
        elif pe_percentile < 30:
            adjustment = -10
    
    score = max(0, min(100, peg_score + adjustment))
    
    return {
        'score': round(score, 1),
        'level': '低' if score < 30 else ('中低' if score < 50 else ('中' if score < 70 else ('中高' if score < 85 else '高'))),
        'factors': {'peg': peg, 'pe_percentile': pe_percentile}
    }


def calculate_industry_risk_score(industry_name: str) -> Dict:
    """
    计算行业风险评分
    
    Args:
        industry_name: 行业名称
    
    Returns:
        dict: 行业风险详情
    """
    if not industry_name or industry_name == "未知行业":
        return {'score': 50, 'level': '中', 'message': '行业未知'}
    
    for risk_level, keywords in INDUSTRY_RISK_MAP.items():
        for keyword in keywords:
            if keyword in industry_name:
                if risk_level == '低风险':
                    return {'score': 20, 'level': '低'}
                elif risk_level == '中低风险':
                    return {'score': 35, 'level': '中低'}
                elif risk_level == '中等风险':
                    return {'score': 55, 'level': '中'}
                elif risk_level == '中高风险':
                    return {'score': 70, 'level': '中高'}
                else:
                    return {'score': 90, 'level': '高'}
    
    return {'score': 50, 'level': '中'}


def calculate_technical_risk_score(kline_df: pd.DataFrame) -> Dict:
    """
    计算技术风险评分
    
    Args:
        kline_df: K线数据
    
    Returns:
        dict: 技术风险详情
    """
    if kline_df is None or len(kline_df) < 60:
        return {'score': 50, 'level': '中', 'message': '数据不足'}
    
    prices = kline_df['close_price']
    
    # 均线计算
    ma5 = prices.rolling(5).mean().iloc[-1]
    ma10 = prices.rolling(10).mean().iloc[-1]
    ma20 = prices.rolling(20).mean().iloc[-1]
    ma60 = prices.rolling(60).mean().iloc[-1]
    latest_price = prices.iloc[-1]
    
    # MACD计算
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    
    # 均线排列判断
    if ma5 > ma10 > ma20 > ma60:
        ma_score = 10
        ma_status = "多头排列"
    elif ma5 > ma10 > ma20:
        ma_score = 25
        ma_status = "短多头"
    elif ma5 < ma10 < ma20:
        ma_score = 80
        ma_status = "空头排列"
    else:
        ma_score = 50
        ma_status = "震荡整理"
    
    # MACD信号
    if dif.iloc[-1] > dea.iloc[-1]:
        macd_score = -10
        macd_status = "MACD金叉"
    else:
        macd_score = 10
        macd_status = "MACD死叉"
    
    score = max(0, min(100, ma_score + macd_score))
    
    return {
        'score': round(score, 1),
        'level': '低' if score < 30 else ('中低' if score < 50 else ('中' if score < 70 else ('中高' if score < 85 else '高'))),
        'factors': {'ma_status': ma_status, 'macd_status': macd_status}
    }


def calculate_liquidity_risk_score(kline_df: pd.DataFrame, market_cap: float = None) -> Dict:
    """
    计算流动性风险评分
    
    Args:
        kline_df: K线数据
        market_cap: 总市值（亿）
    
    Returns:
        dict: 流动性风险详情
    """
    if kline_df is None or len(kline_df) < 20:
        return {'score': 50, 'level': '中', 'message': '数据不足'}
    
    # 计算日均成交额
    avg_amount = kline_df['trading_amount'].tail(20).mean() / 100000000
    
    if avg_amount >= 5:
        score = 10
        level = '低'
    elif avg_amount >= 3:
        score = 30
        level = '中低'
    elif avg_amount >= 1:
        score = 50
        level = '中'
    elif avg_amount >= 0.5:
        score = 70
        level = '中高'
    else:
        score = 90
        level = '高'
    
    return {
        'score': score,
        'level': level,
        'factors': {'avg_amount_bn': round(avg_amount, 2)}
    }


def calculate_5d_risk_score(
    fundamental_result: Dict,
    valuation_result: Dict,
    kline_df: pd.DataFrame,
    industry_name: str = None
) -> Dict:
    """
    计算五维风险评分（V3.5 Phase 4核心函数）
    
    Args:
        fundamental_result: 基本面评分结果
        valuation_result: 估值评分结果
        kline_df: K线数据
        industry_name: 行业名称
    
    Returns:
        dict: 五维风险评分详情
    """
    
    # 1. 财务风险
    debt_ratio = None
    current_ratio = None
    
    details = fundamental_result.get('details', {})
    if 'solvency' in details:
        debt_ratio = details['solvency'].get('debt_ratio')
        current_ratio = details['solvency'].get('current_ratio')
    
    financial_risk = calculate_financial_risk_score(debt_ratio, current_ratio)
    
    # 2. 估值风险
    peg = valuation_result.get('peg')
    valuation_risk = calculate_valuation_risk_score(peg)
    
    # 3. 行业风险
    industry_risk = calculate_industry_risk_score(industry_name or "未知")
    
    # 4. 技术风险
    technical_risk = calculate_technical_risk_score(kline_df)
    
    # 5. 流动性风险
    liquidity_risk = calculate_liquidity_risk_score(kline_df)
    
    # 6. 加权综合评分
    total_score = (
        financial_risk['score'] * 0.25 +
        valuation_risk['score'] * 0.25 +
        industry_risk['score'] * 0.20 +
        technical_risk['score'] * 0.15 +
        liquidity_risk['score'] * 0.15
    )
    
    # 7. 确定风险等级
    if total_score < 30:
        risk_level = '低风险'
        position_limit = 15
    elif total_score < 50:
        risk_level = '中低风险'
        position_limit = 12
    elif total_score < 70:
        risk_level = '中等风险'
        position_limit = 10
    elif total_score < 85:
        risk_level = '中高风险'
        position_limit = 5
    else:
        risk_level = '高风险'
        position_limit = 0
    
    # 8. 识别主要风险
    risks = [
        ('财务风险', financial_risk),
        ('估值风险', valuation_risk),
        ('行业风险', industry_risk),
        ('技术风险', technical_risk),
        ('流动性风险', liquidity_risk)
    ]
    
    main_risks = [r[0] for r in risks if r[1]['score'] >= 60]
    
    # 9. 风险总结
    if len(main_risks) == 0:
        risk_summary = "整体风险较低，可适当配置"
    elif len(main_risks) == 1:
        risk_summary = f"主要风险: {main_risks[0]}"
    else:
        risk_summary = f"存在{len(main_risks)}项主要风险: {', '.join(main_risks)}"
    
    return {
        'total_risk_score': round(total_score, 1),
        'risk_level': risk_level,
        'position_limit': position_limit,
        'dimensions': {
            'financial_risk': financial_risk,
            'valuation_risk': valuation_risk,
            'industry_risk': industry_risk,
            'technical_risk': technical_risk,
            'liquidity_risk': liquidity_risk
        },
        'risk_summary': risk_summary,
        'main_risks': main_risks
    }


# ============================================================
# 二、行业前景评分（权重20%）
# ============================================================

def calculate_industry_prospect_score(stock_code: str, limit: int = 10) -> Dict:
    """
    计算行业前景评分
    
    整合：
    1. 概念强度评分（50%）
    2. 板块热度评分（25%）
    3. 股票-板块共振评分（25%）
    
    Returns:
        dict: {
            'industry_prospect_score': 行业前景评分（0-100）,
            'concept_strength_score': 概念强度评分,
            'sector_heat_score': 板块热度评分,
            'resonance_score': 共振评分,
            'resonance_level': 共振等级
        }
    """
    # 获取概念强度评分
    concept_result = calculate_concept_strength_score(stock_code, limit=limit)
    concept_score = concept_result['concept_score']
    
    # 获取共振评分
    resonance_result = analyze_stock_sector_resonance(stock_code, limit=limit)
    resonance_score = resonance_result['resonance_score']
    resonance_level = resonance_result['resonance_level']
    
    # 计算板块热度评分（基于热门板块）
    try:
        hot_df = get_hot_concepts(top_n=30)
        
        # 获取股票所属概念
        concepts_df = get_stock_concept_detail(stock_code, limit=limit)
        
        if len(concepts_df) > 0 and len(hot_df) > 0:
            # 计算股票概念在热门板块中的占比
            stock_concepts = set(concepts_df['board_name'].tolist())
            hot_concepts = set(hot_df['board_name'].head(20).tolist())
            overlap = stock_concepts & hot_concepts
            
            # 重叠度评分
            overlap_ratio = len(overlap) / max(len(stock_concepts), 1)
            sector_heat_score = min(100, overlap_ratio * 100 + 30)
        else:
            sector_heat_score = 50
    except:
        sector_heat_score = 50
    
    # 综合评分
    # 概念强度50% + 板块热度25% + 共振25%
    industry_score = concept_score * 0.5 + sector_heat_score * 0.25 + resonance_score * 0.25
    
    return {
        'industry_prospect_score': round(industry_score, 2),
        'concept_strength_score': concept_score,
        'sector_heat_score': round(sector_heat_score, 2),
        'resonance_score': resonance_score,
        'resonance_level': resonance_level,
        'strong_concepts': concept_result.get('strong_concepts', [])[:5],
        'independent_stocks': resonance_result.get('independent_stocks', [])[:3]
    }


# ============================================================
# 三、估值评分（权重15%）
# ============================================================

def calculate_valuation_score(stock_code: str) -> Dict:
    """
    计算估值评分
    
    🔥 V3.4更新：使用统一过滤函数
    
    评分维度：
    1. PEG评分（40分）：PEG < 1 低估，PEG 1-2 合理，PEG > 2 高估
    2. PE历史分位评分（30分）
    3. PB-ROE匹配度评分（30分）
    
    Returns:
        dict: {
            'valuation_score': 估值评分（0-100）,
            'peg_score': PEG评分,
            'pe_percentile_score': PE分位评分,
            'pb_roe_score': PB-ROE匹配度评分,
            'valuation_level': 估值水平
        }
    """
    # 获取K线数据
    kline_df = get_stock_kline(stock_code, limit=250)
    
    # 获取财务数据
    finance_df = get_stock_finance(stock_code, limit=10)
    
    # 获取历史高低价
    high_low = get_stock_highest_lowest_price(stock_code)
    
    if len(kline_df) == 0:
        return {'valuation_score': 0, 'message': '无K线数据'}
    
    latest_price = kline_df.iloc[-1]['close_price']
    
    # 1. PEG评分（40分）
    peg_score = 20  # 默认中性
    peg = None
    pe_ttm = None
    data_source = None
    
    # 🔥 V3.4: 使用统一过滤函数获取TTM计算数据
    ttm_data = get_ttm_calculation_data(finance_df)
    
    if ttm_data['available']:
        current_row = ttm_data['current']
        eps_current = current_row.get('基本每股收益(元)', 0)
        eps_last_annual = ttm_data['last_annual'].get('基本每股收益(元)', 0)
        eps_last_same_period = ttm_data['last_same_period'].get('基本每股收益(元)', 0)
        
        # 计算TTM EPS
        if pd.notna(eps_current) and float(eps_current) > 0 and pd.notna(eps_last_annual) and float(eps_last_annual) > 0:
            eps_ttm = float(eps_current) + float(eps_last_annual) - float(eps_last_same_period) if pd.notna(eps_last_same_period) else float(eps_current) + float(eps_last_annual)
            
            if eps_ttm > 0:
                pe_ttm = float(latest_price) / eps_ttm
                data_source = f"{ttm_data['current_period']}"
                
                # 获取增长率
                growth_rate = current_row.get('归属净利润同比增长(%)', 0)
                if pd.notna(growth_rate) and float(growth_rate) > 0:
                    peg = pe_ttm / float(growth_rate)
                    
                    if peg <= 0.8:
                        peg_score = 40
                    elif peg <= 1.0:
                        peg_score = 35
                    elif peg <= 1.5:
                        peg_score = 25
                    elif peg <= 2.0:
                        peg_score = 15
                    else:
                        peg_score = 5
    
    # 2. PE历史分位评分（30分）
    pe_percentile_score = 15  # 默认中性
    
    if len(high_low) > 0:
        lowest = high_low.get('lowest_price', 0)
        highest = high_low.get('highest_price', 0)
        
        # 转换为标量值
        if hasattr(lowest, 'iloc'):
            lowest = lowest.iloc[0] if len(lowest) > 0 else 0
        if hasattr(highest, 'iloc'):
            highest = highest.iloc[0] if len(highest) > 0 else 0
        
        if highest > lowest and lowest > 0:
            # 当前价格在历史高低价中的位置
            price_position = (latest_price - lowest) / (highest - lowest) * 100
            
            # 价格位置越低，估值越有吸引力
            if price_position <= 20:
                pe_percentile_score = 30
            elif price_position <= 40:
                pe_percentile_score = 25
            elif price_position <= 60:
                pe_percentile_score = 20
            elif price_position <= 80:
                pe_percentile_score = 10
            else:
                pe_percentile_score = 5
    
    # 3. PB-ROE匹配度评分（30分）
    pb_roe_score = 15  # 默认中性
    
    if len(finance_df) > 0:
        latest_fin = finance_df.iloc[0]
        
        roe = latest_fin.get('净资产收益率(加权)(%)', 0)
        nav_per_share = latest_fin.get('每股净资产(元)', 0)
        
        if pd.notna(nav_per_share) and nav_per_share > 0:
            pb = latest_price / nav_per_share
            
            # PB-ROE匹配规则
            # 高ROE可以支撑高PB
            if pd.notna(roe):
                if roe >= 20 and pb <= 5:
                    pb_roe_score = 30
                elif roe >= 15 and pb <= 4:
                    pb_roe_score = 25
                elif roe >= 10 and pb <= 3:
                    pb_roe_score = 20
                elif roe >= 5 and pb <= 2:
                    pb_roe_score = 15
                else:
                    pb_roe_score = 10
    
    # 综合评分
    total_score = peg_score + pe_percentile_score + pb_roe_score
    
    # 🔥 V3.5 Phase 3: 同行估值对比
    peers_result = get_industry_peers_valuation(stock_code, limit=10)
    relative_score = 0
    relative_detail = {'available': False, 'message': '同行数据获取失败'}
    
    if peers_result['available']:
        stock_data = peers_result.get('stock_data')
        industry_avg = peers_result.get('industry_avg')
        
        if stock_data and industry_avg:
            # 使用同行数据中的PE/PB/ROE
            relative_result = calculate_relative_valuation_score(
                stock_pe=stock_data.get('pe_ttm') or pe_ttm or 0,
                stock_pb=stock_data.get('pb') or (latest_price / nav_per_share if nav_per_share else 0),
                stock_roe=stock_data.get('roe') or roe or 0,
                industry_avg_pe=industry_avg.get('pe', 0),
                industry_avg_pb=industry_avg.get('pb', 0),
                industry_avg_roe=industry_avg.get('roe', 0)
            )
            
            if relative_result.get('available'):
                relative_score = relative_result['total_relative_score']
                relative_detail = relative_result
            else:
                relative_detail = relative_result
        else:
            relative_detail = {'available': False, 'message': '同行股票数据缺失'}
    
    # 总估值评分 = 绝对评分 + 相对评分（限制上限）
    total_score_with_relative = total_score + relative_score
    total_score_with_relative = min(100, total_score_with_relative)
    
    # 判断估值水平
    if total_score_with_relative >= 70:
        valuation_level = '低估'
    elif total_score_with_relative >= 50:
        valuation_level = '合理'
    elif total_score_with_relative >= 30:
        valuation_level = '偏高'
    else:
        valuation_level = '高估'
    
    return {
        'valuation_score': round(total_score_with_relative, 2),
        'absolute_score': round(total_score, 2),  # 🔥 V3.5新增：绝对估值评分
        'relative_score': round(relative_score, 2),  # 🔥 V3.5新增：相对估值评分
        'peg_score': round(peg_score, 2),
        'pe_percentile_score': round(pe_percentile_score, 2),
        'pb_roe_score': round(pb_roe_score, 2),
        'peg': round(peg, 2) if peg else None,
        'pe_ttm': round(pe_ttm, 2) if pe_ttm else None,
        'valuation_level': valuation_level,
        'data_source': data_source,
        'ttm_message': ttm_data.get('message') if ttm_data.get('available') else ttm_data.get('message', 'TTM数据不可用'),
        # 🔥 V3.5 Phase 3新增：同行对比
        'peers_comparison': peers_result,
        'relative_detail': relative_detail
    }


# ============================================================
# 四、技术面评分（权重15%）
# ============================================================

def calculate_technical_score(kline_df: pd.DataFrame) -> Dict:
    """
    计算技术面评分（手动计算）
    
    评分维度：
    1. MACD信号（25分）
    2. KDJ信号（25分）
    3. 布林带位置（20分）
    4. 均线排列（20分）
    5. 量能配合（10分）
    
    Args:
        kline_df: K线数据
    
    Returns:
        dict: {
            'technical_score': 技术面评分（0-100）,
            'macd_score': MACD评分,
            'kdj_score': KDJ评分,
            'boll_score': 布林带评分,
            'ma_score': 均线评分,
            'volume_score': 量能评分,
            'signals': 信号列表
        }
    """
    if len(kline_df) < 60:
        return {'technical_score': 0, 'message': 'K线数据不足'}
    
    prices = kline_df['close_price']
    highs = kline_df['high_price']
    lows = kline_df['low_price']
    volumes = kline_df['trading_volume']
    
    signals = []
    score = 0
    
    # 1. MACD信号（25分）
    macd_score = 0
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    
    dif_latest = dif.iloc[-1]
    dea_latest = dea.iloc[-1]
    dif_prev = dif.iloc[-2]
    dea_prev = dea.iloc[-2]
    
    if dif_latest > dea_latest:
        if dif_prev <= dea_prev:
            # 金叉
            macd_score = 25
            signals.append('MACD金叉 +25')
        else:
            macd_score = 15
            signals.append('MACD多头 +15')
    else:
        if dif_prev >= dea_prev:
            # 死叉
            macd_score = 0
            signals.append('MACD死叉 0')
        else:
            macd_score = 5
            signals.append('MACD空头 +5')
    
    # 2. KDJ信号（25分）
    kdj_score = 0
    n = 9
    low_n = lows.rolling(n).min()
    high_n = highs.rolling(n).max()
    rsv = (prices - low_n) / (high_n - low_n) * 100
    K = rsv.ewm(span=3, adjust=False).mean()
    D = K.ewm(span=3, adjust=False).mean()
    J = 3 * K - 2 * D
    
    k_latest = K.iloc[-1]
    d_latest = D.iloc[-1]
    
    if k_latest < 20:
        # 超卖
        kdj_score = 25
        signals.append('KDJ超卖 +25')
    elif k_latest < 30:
        kdj_score = 20
        signals.append('KDJ偏低 +20')
    elif k_latest > 80:
        # 超买
        kdj_score = 5
        signals.append('KDJ超买 +5')
    elif k_latest > 70:
        kdj_score = 10
        signals.append('KDJ偏高 +10')
    else:
        kdj_score = 15
        signals.append('KDJ中性 +15')
    
    # 3. 布林带位置（20分）
    boll_score = 0
    mid = prices.rolling(20).mean()
    std = prices.rolling(20).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    
    latest_price = prices.iloc[-1]
    mid_latest = mid.iloc[-1]
    upper_latest = upper.iloc[-1]
    lower_latest = lower.iloc[-1]
    
    if latest_price <= lower_latest:
        # 触及下轨
        boll_score = 20
        signals.append('触及布林下轨 +20')
    elif latest_price <= mid_latest:
        boll_score = 15
        signals.append('布林中轨下方 +15')
    elif latest_price >= upper_latest:
        # 触及上轨
        boll_score = 5
        signals.append('触及布林上轨 +5')
    else:
        boll_score = 12
        signals.append('布林中轨上方 +12')
    
    # 4. 均线排列（20分）
    ma_score = 0
    ma5 = prices.rolling(5).mean().iloc[-1]
    ma10 = prices.rolling(10).mean().iloc[-1]
    ma20 = prices.rolling(20).mean().iloc[-1]
    ma60 = prices.rolling(60).mean().iloc[-1]
    
    if ma5 > ma10 > ma20 > ma60:
        # 完美多头排列
        ma_score = 20
        signals.append('多头排列 +20')
    elif ma5 > ma10 > ma20:
        ma_score = 15
        signals.append('短多头 +15')
    elif latest_price > ma5 and latest_price > ma10:
        ma_score = 10
        signals.append('价格在均线上 +10')
    elif ma5 < ma10 < ma20:
        ma_score = 5
        signals.append('空头排列 +5')
    else:
        ma_score = 8
        signals.append('均线震荡 +8')
    
    # 5. 量能配合（10分）
    volume_score = 0
    vol_ma5 = volumes.rolling(5).mean().iloc[-1]
    vol_latest = volumes.iloc[-1]
    
    price_change = kline_df.iloc[-1]['change_percent']
    
    if price_change > 0 and vol_latest > vol_ma5:
        # 上涨放量
        volume_score = 10
        signals.append('上涨放量 +10')
    elif price_change < 0 and vol_latest < vol_ma5:
        # 下跌缩量
        volume_score = 8
        signals.append('下跌缩量 +8')
    elif price_change > 0 and vol_latest < vol_ma5:
        # 上涨缩量
        volume_score = 4
        signals.append('上涨缩量 +4')
    else:
        volume_score = 5
        signals.append('量能中性 +5')
    
    # 总分
    total_score = macd_score + kdj_score + boll_score + ma_score + volume_score
    
    return {
        'technical_score': round(total_score, 2),
        'macd_score': round(macd_score, 2),
        'kdj_score': round(kdj_score, 2),
        'boll_score': round(boll_score, 2),
        'ma_score': round(ma_score, 2),
        'volume_score': round(volume_score, 2),
        'signals': signals,
        'grade': 'A' if total_score >= 80 else ('B' if total_score >= 60 else ('C' if total_score >= 40 else 'D'))
    }


# ============================================================
# 五、事件驱动评分（权重15%）
# ============================================================

def calculate_event_driven_score(stock_code: str, days: int = 90) -> Dict:
    """
    计算事件驱动评分
    
    Args:
        stock_code: 股票代码
        days: 分析天数
    
    Returns:
        dict: {
            'event_score': 事件驱动评分（0-100）,
            'sentiment': 情绪判断,
            'key_events': 关键事件列表
        }
    """
    # 调用事件驱动分析模块
    result = calculate_event_score(stock_code, days=days)
    
    # 将-30~+30的评分转换为0~100
    raw_score = result['event_score']
    normalized_score = 50 + raw_score * (50 / 30)  # 转换到0-100
    normalized_score = max(0, min(100, normalized_score))
    
    # 情绪判断
    if normalized_score >= 70:
        sentiment = '偏多'
    elif normalized_score >= 30:
        sentiment = '中性'
    else:
        sentiment = '偏空'
    
    return {
        'event_score': round(normalized_score, 2),
        'raw_score': raw_score,
        'sentiment': sentiment,
        'recent_sentiment': result['recent_sentiment'],
        'positive_events': result.get('positive_events', [])[:3],
        'negative_events': result.get('negative_events', [])[:3]
    }


# ============================================================
# 六、市场环境评分（权重15%）
# ============================================================

def calculate_market_environment_score() -> Dict:
    """
    计算市场环境评分
    
    评分维度：
    1. 全球市场表现（40分）
    2. 热门板块数量（40分）
    3. 板块轮动强度（20分）
    
    Returns:
        dict: {
            'market_score': 市场环境评分（0-100）,
            'global_score': 全球市场评分,
            'sector_score': 板块热度评分,
            'environment_level': 环境等级
        }
    """
    # 1. 全球市场评分（40分）
    global_score = 20  # 默认中性
    
    try:
        # 获取全球指数
        global_df = get_global_index(region='americas')
        
        if len(global_df) > 0:
            # 简化处理：假设最近数据表现良好
            global_score = 25  # 中性偏正
    except:
        global_score = 20
    
    # 2. 热门板块评分（40分）
    sector_score = 20
    
    try:
        hot_df = get_hot_concepts(top_n=20)
        
        if len(hot_df) > 0:
            # 高强度板块数量
            high_strength = len(hot_df[hot_df['market_strength_score'] >= 80])
            
            if high_strength >= 10:
                sector_score = 40
            elif high_strength >= 5:
                sector_score = 30
            elif high_strength >= 3:
                sector_score = 20
            else:
                sector_score = 10
    except:
        sector_score = 20
    
    # 3. 板块轮动评分（20分）
    rotation_score = 10
    
    try:
        hot_df = get_hot_concepts(top_n=10)
        
        if len(hot_df) > 0:
            avg_strength = hot_df['market_strength_score'].mean()
            
            if avg_strength >= 80:
                rotation_score = 20
            elif avg_strength >= 70:
                rotation_score = 15
            elif avg_strength >= 60:
                rotation_score = 10
            else:
                rotation_score = 5
    except:
        rotation_score = 10
    
    # 总分
    total_score = global_score + sector_score + rotation_score
    
    # 环境等级
    if total_score >= 70:
        environment_level = '强势'
    elif total_score >= 50:
        environment_level = '中性偏强'
    elif total_score >= 30:
        environment_level = '中性偏弱'
    else:
        environment_level = '弱势'
    
    return {
        'market_score': round(total_score, 2),
        'global_score': round(global_score, 2),
        'sector_score': round(sector_score, 2),
        'rotation_score': round(rotation_score, 2),
        'environment_level': environment_level
    }


# ============================================================
# 七、综合评分计算
# ============================================================

def calculate_comprehensive_score(
    stock_code: str,
    stock_name: str = '',
    kline_days: int = 60
) -> Dict:
    """
    计算股票综合评分（V3.3）
    
    六维度评分（权重）：
    - 基本面评分：20%（仅正式财报）
    - 行业前景评分：20%
    - 估值评分：15%
    - 技术面评分：15%
    - 事件驱动评分：15%
    - 市场环境评分：15%
    
    新增（V3.3）：
    - 业绩预告前瞻性洞察（独立分析，不参与评分）
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        kline_days: K线天数
    
    Returns:
        dict: 完整的综合评分报告
    """
    print(f"\n正在分析 {stock_name} ({stock_code})...")
    
    # 获取K线数据（用于技术分析）
    kline_df = get_stock_kline(stock_code, limit=max(kline_days, 60))
    
    # 0. 业绩预告前瞻性分析（独立于评分）
    forecast_insight = None
    if FORECAST_ANALYSIS_AVAILABLE:
        print("  - 分析业绩预告前瞻性...")
        try:
            forecast_result = analyze_forecast_trend(stock_code)
            if forecast_result.get('has_forecast'):
                forecast_insight = forecast_result
        except Exception as e:
            print(f"    业绩预告分析失败: {e}")
    
    # 1. 基本面评分（20%）- 仅使用正式财报
    print("  - 计算基本面评分...")
    fundamental = calculate_fundamental_score(stock_code)
    fundamental_weighted = fundamental['fundamental_score'] * 0.20
    
    # 2. 行业前景评分（20%）
    print("  - 计算行业前景评分...")
    industry = calculate_industry_prospect_score(stock_code, limit=10)
    industry_weighted = industry['industry_prospect_score'] * 0.20
    
    # 3. 估值评分（15%）
    print("  - 计算估值评分...")
    valuation = calculate_valuation_score(stock_code)
    valuation_weighted = valuation['valuation_score'] * 0.15
    
    # 4. 技术面评分（15%）
    print("  - 计算技术面评分...")
    technical = calculate_technical_score(kline_df)
    technical_weighted = technical['technical_score'] * 0.15
    
    # 5. 事件驱动评分（15%）
    print("  - 计算事件驱动评分...")
    event = calculate_event_driven_score(stock_code, days=90)
    event_weighted = event['event_score'] * 0.15
    
    # 6. 市场环境评分（15%）
    print("  - 计算市场环境评分...")
    market = calculate_market_environment_score()
    market_weighted = market['market_score'] * 0.15
    
    # 综合评分
    comprehensive_score = (
        fundamental_weighted + 
        industry_weighted + 
        valuation_weighted + 
        technical_weighted + 
        event_weighted + 
        market_weighted
    )
    
    # 综合评级
    if comprehensive_score >= 80:
        rating = '强烈买入'
        rating_star = '⭐⭐⭐⭐⭐'
    elif comprehensive_score >= 70:
        rating = '买入'
        rating_star = '⭐⭐⭐⭐'
    elif comprehensive_score >= 60:
        rating = '持有'
        rating_star = '⭐⭐⭐'
    elif comprehensive_score >= 50:
        rating = '减持'
        rating_star = '⭐⭐'
    else:
        rating = '卖出'
        rating_star = '⭐'
    
    # 🔥 V3.5 Phase 4: 五维风险评分
    print("  - 计算五维风险评分...")
    
    # 获取行业名称
    industry_name = None
    if valuation.get('peers_comparison', {}).get('available'):
        industry_name = valuation['peers_comparison'].get('industry')
    
    risk_result = calculate_5d_risk_score(
        fundamental_result=fundamental,
        valuation_result=valuation,
        kline_df=kline_df,
        industry_name=industry_name
    )
    
    risk_level = risk_result['risk_level']
    position_limit = risk_result['position_limit']
    
    return {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        
        # 综合评分
        'comprehensive_score': round(comprehensive_score, 2),
        'rating': rating,
        'rating_star': rating_star,
        'risk_level': risk_level,
        'position_limit': position_limit,
        
        # 🔥 V3.5 Phase 4新增：五维风险详情
        'risk_analysis': risk_result,
        
        # 六维度评分详情
        'dimensions': {
            'fundamental': {
                'score': fundamental['fundamental_score'],
                'weighted': round(fundamental_weighted, 2),
                'weight': '20%',
                'grade': fundamental.get('grade', 'N/A'),
                'details': fundamental.get('details', {})
            },
            'industry': {
                'score': industry['industry_prospect_score'],
                'weighted': round(industry_weighted, 2),
                'weight': '20%',
                'resonance_level': industry['resonance_level']
            },
            'valuation': {
                'score': valuation['valuation_score'],
                'weighted': round(valuation_weighted, 2),
                'weight': '15%',
                'level': valuation['valuation_level']
            },
            'technical': {
                'score': technical['technical_score'],
                'weighted': round(technical_weighted, 2),
                'weight': '15%',
                'grade': technical.get('grade', 'N/A'),
                'signals': technical.get('signals', [])
            },
            'event': {
                'score': event['event_score'],
                'weighted': round(event_weighted, 2),
                'weight': '15%',
                'sentiment': event['sentiment']
            },
            'market': {
                'score': market['market_score'],
                'weighted': round(market_weighted, 2),
                'weight': '15%',
                'level': market['environment_level']
            }
        },
        
        # 业绩预告前瞻性洞察（V3.3新增，独立于评分）
        'forecast_insight': forecast_insight,
        
        # 关键信息摘要
        'summary': {
            'strengths': [],
            'risks': [],
            'suggestion': ''
        }
    }
    
    # 🔥 V3.5 Phase 5: 记录评分历史
    if TRACKING_AVAILABLE:
        try:
            record_score_history(
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_result=result,
                trigger="manual"
            )
        except Exception as e:
            print(f"  - 评分历史记录失败: {e}")
    
    return result


# ============================================================
# 八、使用示例
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("股票综合评分模型 V3.3 测试")
    print("="*60)
    
    # 测试股票
    test_code = '300308'
    test_name = '中际旭创'
    
    # 计算综合评分
    result = calculate_comprehensive_score(test_code, test_name)
    
    # 打印结果
    print("\n" + "="*60)
    print(f"股票: {result['stock_name']} ({result['stock_code']})")
    print(f"分析时间: {result['analysis_date']}")
    print("="*60)
    
    print(f"\n【综合评分】{result['comprehensive_score']}分")
    print(f"【评级】{result['rating']} {result['rating_star']}")
    print(f"【风险等级】{result['risk_level']}")
    print(f"【建议仓位】≤{result['position_limit']}%")
    
    print("\n【六维度评分】")
    print("-"*60)
    
    dims = result['dimensions']
    print(f"1. 基本面评分: {dims['fundamental']['score']}分 (权重{dims['fundamental']['weight']}, 加权{dims['fundamental']['weighted']}分)")
    print(f"2. 行业前景评分: {dims['industry']['score']}分 (权重{dims['industry']['weight']}, 加权{dims['industry']['weighted']}分)")
    print(f"3. 估值评分: {dims['valuation']['score']}分 (权重{dims['valuation']['weight']}, 加权{dims['valuation']['weighted']}分)")
    print(f"4. 技术面评分: {dims['technical']['score']}分 (权重{dims['technical']['weight']}, 加权{dims['technical']['weighted']}分)")
    print(f"5. 事件驱动评分: {dims['event']['score']}分 (权重{dims['event']['weight']}, 加权{dims['event']['weighted']}分)")
    print(f"6. 市场环境评分: {dims['market']['score']}分 (权重{dims['market']['weight']}, 加权{dims['market']['weighted']}分)")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)