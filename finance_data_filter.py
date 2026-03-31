"""
财务数据过滤工具 V1.2
=====================

V3.4新增模块，统一处理财务数据分类和过滤
V3.5新增：财务趋势分析功能（Phase 1）

核心原则：
- 正式财报（年报/季报）：用于评分计算、估值分析、财务分析
- 业绩预告/快报：仅用于前瞻性洞察分析，不参与评分

🔥 V1.1修正（用户反馈）：
- 数据源选择：**最新优先**（不是年报优先）
- 如果当年度季报比年报新 → 用季报（年报待发布）
- 如果年报是最新 → 用年报
- 核心原则：永远使用最新可用的正式财报数据

核心功能：
1. classify_finance_data() - 统一分类财务数据
2. filter_official_reports() - 过滤正式财报
3. filter_forecasts() - 过滤业绩预告
4. get_best_analysis_data() - 获取最佳分析数据源（最新优先）
5. determine_analysis_source() - 确定分析数据源

使用示例：
```python
from finance_data_filter import classify_finance_data, get_best_analysis_data

# 获取财务数据
finance_df = get_stock_finance('300308', limit=10)

# 分类
classified = classify_finance_data(finance_df)

# 获取最佳分析数据源（最新优先）
best_data, source_message = get_best_analysis_data(finance_df)

if best_data is None:
    # 无正式财报，无法评分
else:
    # 使用最新正式财报进行评分
```

"""

import pandas as pd
from typing import Dict, Optional, Tuple, List
import sys

sys.path.insert(0, '/Users/jw/.openclaw/workspace')


# ============================================================
# 一、核心分类函数
# ============================================================

def classify_finance_data(finance_df: pd.DataFrame) -> Dict:
    """
    将财务数据分类为：正式财报、业绩预告、业绩快报
    
    分类规则：
    - 年报/季报（无"预告"/"快报"关键词） → 正式财报
    - 报告期含"预告" → 业绩预告
    - 报告期含"快报" → 业绩快报
    
    Args:
        finance_df: 贡献数据DataFrame（来自get_stock_finance）
    
    Returns:
        dict: {
            'official_reports': DataFrame,  # 正式财报（年报+季报，按时间降序）
            'forecasts': DataFrame,          # 业绩预告
            'quick_reports': DataFrame,      # 业绩快报
            'latest_annual': Series,         # 最新年报（如有）
            'latest_quarterly': Series,      # 最新季报（如有）
            'latest_forecast': Series,       # 最新预告（如有）
            'latest_quick_report': Series,   # 最新快报（如有）
            'classification_summary': dict   # 分类统计
        }
    """
    
    if finance_df is None or len(finance_df) == 0:
        return {
            'official_reports': pd.DataFrame(),
            'forecasts': pd.DataFrame(),
            'quick_reports': pd.DataFrame(),
            'latest_annual': None,
            'latest_quarterly': None,
            'latest_forecast': None,
            'latest_quick_report': None,
            'classification_summary': {
                'official_count': 0,
                'forecast_count': 0,
                'quick_report_count': 0,
                'has_annual': False,
                'has_quarterly': False,
                'has_forecast': False,
                'has_quick_report': False
            },
            'message': '无财务数据'
        }
    
    # 复制DataFrame避免修改原数据
    df = finance_df.copy()
    
    # 分类规则
    def classify_row(row):
        period = str(row.get('报告期', ''))
        source = str(row.get('数据来源', ''))
        
        # 业绩预告：报告期含"预告"或数据来源含"预告"
        if '预告' in period or '预告' in source:
            return 'forecast'
        
        # 业绩快报：报告期含"快报"或数据来源含"快报"
        elif '快报' in period or '快报' in source:
            return 'quick_report'
        
        # 正式财报：年报或季报
        else:
            return 'official'
    
    # 应用分类
    df['data_class'] = df.apply(classify_row, axis=1)
    
    # 分离数据（保持原始排序，最新数据在前）
    official = df[df['data_class'] == 'official'].reset_index(drop=True)
    forecasts = df[df['data_class'] == 'forecast'].reset_index(drop=True)
    quick_reports = df[df['data_class'] == 'quick_report'].reset_index(drop=True)
    
    # 提取最新各类型（注意：official已按时间降序排列）
    latest_annual = None
    latest_quarterly = None
    
    if len(official) > 0:
        # 年报：查找含"年报"的报告
        annual_mask = official['报告期'].str.contains('年报', na=False)
        annual = official[annual_mask]
        
        if len(annual) > 0:
            latest_annual = annual.iloc[0]  # 最新年报
        
        # 季报：不含"年报"的报告
        quarterly_mask = ~official['报告期'].str.contains('年报', na=False)
        quarterly = official[quarterly_mask]
        
        if len(quarterly) > 0:
            latest_quarterly = quarterly.iloc[0]  # 最新季报
    
    # 预告和快报
    latest_forecast = forecasts.iloc[0] if len(forecasts) > 0 else None
    latest_quick_report = quick_reports.iloc[0] if len(quick_reports) > 0 else None
    
    # 分类统计
    summary = {
        'official_count': len(official),
        'annual_count': len(official[official['报告期'].str.contains('年报', na=False)]),
        'quarterly_count': len(official[~official['报告期'].str.contains('年报', na=False)]),
        'forecast_count': len(forecasts),
        'quick_report_count': len(quick_reports),
        'has_annual': latest_annual is not None,
        'has_quarterly': latest_quarterly is not None,
        'has_forecast': latest_forecast is not None,
        'has_quick_report': latest_quick_report is not None,
        'latest_annual_period': latest_annual['报告期'] if latest_annual is not None else None,
        'latest_quarterly_period': latest_quarterly['报告期'] if latest_quarterly is not None else None,
        'latest_forecast_period': latest_forecast['报告期'] if latest_forecast is not None else None
    }
    
    return {
        'official_reports': official,
        'forecasts': forecasts,
        'quick_reports': quick_reports,
        'latest_annual': latest_annual,
        'latest_quarterly': latest_quarterly,
        'latest_forecast': latest_forecast,
        'latest_quick_report': latest_quick_report,
        'classification_summary': summary
    }


# ============================================================
# 二、过滤函数
# ============================================================

def filter_official_reports(finance_df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤正式财报（年报+季报）
    
    用于：评分计算、估值分析、财务分析
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        DataFrame: 仅包含正式财报的数据（按时间降序）
    """
    classified = classify_finance_data(finance_df)
    return classified['official_reports']


def filter_annual_reports(finance_df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤年报
    
    用于：特定场景需要年报数据
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        DataFrame: 仅包含年报的数据
    """
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) > 0:
        annual_mask = official['报告期'].str.contains('年报', na=False)
        return official[annual_mask].reset_index(drop=True)
    
    return pd.DataFrame()


def filter_quarterly_reports(finance_df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤季报
    
    用于：特定场景需要季报数据
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        DataFrame: 仅包含季报的数据
    """
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) > 0:
        quarterly_mask = ~official['报告期'].str.contains('年报', na=False)
        return official[quarterly_mask].reset_index(drop=True)
    
    return pd.DataFrame()


def filter_forecasts(finance_df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤业绩预告
    
    用于：前瞻性洞察分析（不参与评分）
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        DataFrame: 仅包含业绩预告的数据
    """
    classified = classify_finance_data(finance_df)
    return classified['forecasts']


def filter_quick_reports(finance_df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤业绩快报
    
    用于：前瞻性洞察分析（不参与评分）
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        DataFrame: 仅包含业绩快报的数据
    """
    classified = classify_finance_data(finance_df)
    return classified['quick_reports']


# ============================================================
# 三、数据源选择函数（🔥 最新优先）
# ============================================================

def get_best_analysis_data(finance_df: pd.DataFrame) -> Tuple[Optional[pd.Series], str]:
    """
    获取最佳分析数据源（🔥 最新优先）
    
    正确逻辑（用户修正后）：
    1. 优先使用最新的正式财报（按时间排序）
    2. 如果当年度季报比年报新 → 用季报（年报待发布）
    3. 如果年报是最新 → 用年报
    
    核心原则：永远使用最新可用的正式财报数据
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        Tuple[数据行, 数据来源说明]
        例如：
        - (quarterly_row, "2025三季报（年报待发布）")  # 当年度季报最新
        - (annual_row, "2025年报")                     # 年报最新
        - (annual_row, "2024年报")                     # 当年度无数据，上年年报最新
        - (None, "无正式财报数据")
    """
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) == 0:
        return (None, "无正式财报数据")
    
    # 🔥 永远取最新的正式财报（official已按时间降序排列）
    latest_official = official.iloc[0]
    latest_period = str(latest_official['报告期'])
    
    # 判断是否是年报还是季报
    is_annual = '年报' in latest_period and '预告' not in latest_period
    
    if is_annual:
        # 最新是年报 → 直接使用
        return (latest_official, f"{latest_period}")
    else:
        # 最新是季报 → 标注年报待发布
        return (latest_official, f"{latest_period}（年报待发布）")


def determine_analysis_source(finance_df: pd.DataFrame) -> Dict:
    """
    确定用于分析（评分/估值）的数据源
    
    🔥 正确逻辑（用户修正后）：
    - 优先使用最新的正式财报（按时间排序）
    - 不区分年报/季报优先，永远取最新
    
    返回更详细的数据源信息，包括置信度
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        dict: {
            'source_type': str,          # '年报'/'季报'/None
            'data': Series,              # 数据行
            'period': str,               # 报告期
            'confidence': str,           # '高'/'中'/'无'
            'message': str,              # 说明信息
            'fallback_available': bool,  # 是否有递补数据
            'forecast_available': bool   # 是否有预告数据
        }
    """
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) == 0:
        return {
            'source_type': None,
            'data': None,
            'period': None,
            'confidence': '无',
            'message': "无正式财报数据，仅可进行前瞻性洞察分析",
            'fallback_available': False,
            'forecast_available': classified['classification_summary']['has_forecast'],
            'quality_level': 'none'  # 无正式财报
        }
    
    # 🔥 永远取最新的正式财报
    latest_official = official.iloc[0]
    latest_period = str(latest_official['报告期'])
    
    # 判断是否是年报
    is_annual = '年报' in latest_period and '预告' not in latest_period
    
    if is_annual:
        return {
            'source_type': '年报',
            'data': latest_official,
            'period': latest_period,
            'confidence': '高',
            'message': f"使用{latest_period}数据进行分析",
            'fallback_available': len(official) > 1,  # 有其他数据可递补
            'forecast_available': classified['classification_summary']['has_forecast'],
            'quality_level': 'complete'  # 数据完整
        }
    else:
        return {
            'source_type': '季报',
            'data': latest_official,
            'period': latest_period,
            'confidence': '中',
            'message': f"使用{latest_period}数据进行分析（年报待发布）",
            'fallback_available': classified['classification_summary']['has_annual'],  # 有年报可参考
            'forecast_available': classified['classification_summary']['has_forecast'],
            'quality_level': 'partial'  # 数据部分（待年报补充）
        }


# ============================================================
# 四、数据质量报告
# ============================================================

def generate_data_quality_report(classified: Dict) -> Dict:
    """
    生成数据质量报告
    
    用于在分析报告中展示数据来源和质量
    
    Args:
        classified: classify_finance_data() 返回的分类结果
    
    Returns:
        dict: {
            'overall_status': str,      # 'complete'/'partial'/'forecast_only'
            'status_text': str,         # 状态文本
            'status_icon': str,         # 状态图标（✅/⚠️/❌）
            'data_sources': list,       # 数据来源列表
            'warnings': list,           # 警告信息
            'suggestions': list         # 建议信息
        }
    """
    summary = classified['classification_summary']
    official = classified['official_reports']
    
    # 🔥 判断整体状态（基于最新数据）
    if len(official) > 0:
        latest_period = str(official.iloc[0]['报告期'])
        is_annual = '年报' in latest_period and '预告' not in latest_period
        
        if is_annual:
            overall_status = 'complete'
            status_text = f'{latest_period}数据完整'
            status_icon = '✅'
        else:
            overall_status = 'partial'
            status_text = f'{latest_period}数据（年报待发布）'
            status_icon = '⚠️'
    elif summary['has_forecast']:
        overall_status = 'forecast_only'
        status_text = '仅业绩预告（无正式财报）'
        status_icon = '❌'
    else:
        overall_status = 'none'
        status_text = '无财务数据'
        status_icon = '❌'
    
    # 数据来源列表
    data_sources = []
    
    # 🔥 最新数据源（用于评分）
    if len(official) > 0:
        latest = official.iloc[0]
        latest_period = str(latest['报告期'])
        is_annual = '年报' in latest_period
        
        data_sources.append({
            'type': '年报' if is_annual else '季报',
            'period': latest_period,
            'usage': '评分/估值/分析' + ('（年报待发布）' if not is_annual else ''),
            'quality': '完整审计' if is_annual else '未审计',
            'is_latest': True
        })
    
    # 其他正式财报
    if summary['has_annual'] and len(official) > 0:
        # 如果最新不是年报，列出年报作为参考
        latest_period = str(official.iloc[0]['报告期'])
        if '年报' not in latest_period and summary['latest_annual_period']:
            data_sources.append({
                'type': '年报',
                'period': summary['latest_annual_period'],
                'usage': '历史参考',
                'quality': '完整审计',
                'is_latest': False
            })
    
    # 业绩预告
    if summary['has_forecast']:
        data_sources.append({
            'type': '业绩预告',
            'period': summary['latest_forecast_period'],
            'usage': '前瞻性洞察（不参与评分）',
            'quality': '区间值/不确定',
            'is_latest': False
        })
    
    # 警告信息
    warnings = []
    
    if overall_status == 'partial':
        warnings.append("使用季报数据评分，年报待发布")
    
    if overall_status == 'forecast_only':
        warnings.append("无正式财报，无法进行评分计算")
    
    # 建议信息
    suggestions = []
    
    if overall_status == 'partial':
        suggestions.append("建议关注年报发布时间，年报发布后更新分析")
    
    if overall_status == 'forecast_only':
        suggestions.append("建议等待正式财报发布后再进行完整评分分析")
    
    return {
        'overall_status': overall_status,
        'status_text': status_text,
        'status_icon': status_icon,
        'data_sources': data_sources,
        'warnings': warnings,
        'suggestions': suggestions,
        'classification_summary': summary
    }


# ============================================================
# 五、辅助函数
# ============================================================

def get_report_periods_list(finance_df: pd.DataFrame) -> List[str]:
    """
    获取所有报告期列表（用于展示）
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        List[str]: 报告期列表，如 ['2025年报预告', '2025三季报', '2024年报']
    """
    if finance_df is None or len(finance_df) == 0:
        return []
    
    return finance_df['报告期'].tolist()


def check_data_availability(finance_df: pd.DataFrame) -> Dict:
    """
    检查数据可用性（快速检查）
    
    用于在分析前快速判断数据状态
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        dict: {
            'can_score': bool,          # 是否可以评分
            'has_official': bool,       # 是否有正式财报
            'has_forecast': bool,       # 是否有预告
            'message': str              # 状态说明
        }
    """
    classified = classify_finance_data(finance_df)
    summary = classified['classification_summary']
    official = classified['official_reports']
    
    can_score = len(official) > 0
    has_official = summary['official_count'] > 0
    has_forecast = summary['has_forecast']
    
    # 🔥 基于最新数据判断状态
    if len(official) > 0:
        latest_period = str(official.iloc[0]['报告期'])
        is_annual = '年报' in latest_period
        
        if is_annual:
            message = f"有{latest_period}数据，可进行完整评分"
        else:
            message = f"有{latest_period}数据，可进行评分（年报待发布）"
    elif has_forecast:
        message = "仅业绩预告，无法评分"
    else:
        message = "无财务数据"
    
    return {
        'can_score': can_score,
        'has_official': has_official,
        'has_annual': summary['has_annual'],
        'has_quarterly': summary['has_quarterly'],
        'has_forecast': has_forecast,
        'latest_period': str(official.iloc[0]['报告期']) if len(official) > 0 else None,
        'message': message
    }


def get_ttm_calculation_data(finance_df: pd.DataFrame) -> Dict:
    """
    获取TTM计算所需数据
    
    TTM EPS公式：最新累计EPS + 去年年报EPS - 去年同期累计EPS
    
    Args:
        finance_df: 贡献数据DataFrame
    
    Returns:
        dict: {
            'current': Series,          # 最新累计数据
            'last_annual': Series,      # 去年年报
            'last_same_period': Series, # 去年同期
            'available': bool,          # 是否可用
            'message': str              # 说明
        }
    """
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) < 3:
        return {
            'current': None,
            'last_annual': None,
            'last_same_period': None,
            'available': False,
            'message': '正式财报数据不足（需要至少3期）'
        }
    
    # 🔥 最新数据（取第一条，已按时间降序）
    current = official.iloc[0]
    current_period = str(current['报告期'])
    
    # 判断年份
    current_year = '2025' if '2025' in current_period else '2024'
    last_year = str(int(current_year) - 1)
    
    # 查找去年年报和去年同期
    last_annual = None
    last_same_period = None
    
    for i in range(len(official)):
        row = official.iloc[i]
        period = str(row['报告期'])
        
        # 去年年报
        if '年报' in period and last_year in period:
            last_annual = row
        
        # 去年同期
        last_same = current_period.replace(current_year, last_year)
        if period == last_same:
            last_same_period = row
    
    # 检查是否找到
    if last_annual is None:
        return {
            'current': current,
            'last_annual': None,
            'last_same_period': last_same_period,
            'available': False,
            'message': f'未找到{last_year}年年报数据'
        }
    
    if last_same_period is None:
        return {
            'current': current,
            'last_annual': last_annual,
            'last_same_period': None,
            'available': False,
            'message': f'未找到{last_year}年同期数据'
        }
    
    return {
        'current': current,
        'last_annual': last_annual,
        'last_same_period': last_same_period,  # 🔥 修复：返回Series而不是字符串
        'current_period': current_period,
        'last_annual_period': str(last_annual['报告期']),
        'last_same_period_period': str(last_same_period['报告期']),  # 新增：报告期字符串
        'available': True,
        'message': f'TTM计算数据完整：{current_period} + {last_annual["报告期"]} - {last_same_period["报告期"]}'
    }


# ============================================================
# 六、财务趋势分析（V3.5 Phase 1 新增）
# ============================================================

def determine_trend(values: List[float], threshold: float = 5.0) -> Dict:
    """
    判断单个指标的趋势类型
    
    Args:
        values: 数值列表，按时间升序（最早→最新）
               例如：[22.5, 24.8, 26.61]
        threshold: 持平判断阈值（默认5%，波动<5%视为持平）
    
    Returns:
        dict: {
            'trend_type': str,      # 'improving'/'slowing_improve'/'stable'/'volatile'/'slowing_worsen'/'worsening'/'insufficient_data'
            'trend_text': str,      # '连续改善'/'改善放缓'/...
            'trend_icon': str,      # '🔥'/'→'/'↔'/'⚠️'
            'score_adjustment': int # 加分/减分（-5到+5）
        }
    """
    n = len(values)
    
    if n < 3:
        return {
            'trend_type': 'insufficient_data',
            'trend_text': '数据不足',
            'trend_icon': '❓',
            'score_adjustment': 0
        }
    
    # 过滤None和NaN
    valid_values = [v for v in values if v is not None and pd.notna(v)]
    
    if len(valid_values) < 3:
        return {
            'trend_type': 'insufficient_data',
            'trend_text': '有效数据不足',
            'trend_icon': '❓',
            'score_adjustment': 0
        }
    
    # 计算每期变化
    changes = []
    for i in range(1, len(valid_values)):
        change = valid_values[i] - valid_values[i-1]
        changes.append(change)
    
    # 1. 连续改善：所有变化 > 0
    if all(c > 0 for c in changes):
        # 检查是否改善放缓（增幅变小）
        if len(changes) >= 2 and changes[-1] < changes[-2]:
            return {
                'trend_type': 'slowing_improve',
                'trend_text': '改善放缓',
                'trend_icon': '📈↓',
                'score_adjustment': 2  # 半分（满分5分的话）
            }
        else:
            return {
                'trend_type': 'improving',
                'trend_text': '连续改善',
                'trend_icon': '🔥',
                'score_adjustment': 5  # 满分
            }
    
    # 2. 连续恶化：所有变化 < 0
    if all(c < 0 for c in changes):
        # 检查是否恶化放缓（降幅变小）
        if len(changes) >= 2 and abs(changes[-1]) < abs(changes[-2]):
            return {
                'trend_type': 'slowing_worsen',
                'trend_text': '恶化放缓',
                'trend_icon': '📉↑',
                'score_adjustment': -2  # 半分
            }
        else:
            return {
                'trend_type': 'worsening',
                'trend_text': '连续恶化',
                'trend_icon': '⚠️',
                'score_adjustment': -5  # 满分减分
            }
    
    # 3. 持平：波动 < threshold%
    max_val = max(valid_values)
    if max_val > 0:
        min_val = min(valid_values)
        volatility = (max_val - min_val) / max_val * 100
        
        if volatility < threshold:
            return {
                'trend_type': 'stable',
                'trend_text': '持平',
                'trend_icon': '→',
                'score_adjustment': 0
            }
    
    # 4. 波动：改善-恶化交替
    return {
        'trend_type': 'volatile',
        'trend_text': '波动',
        'trend_icon': '↔',
        'score_adjustment': 0
    }


def analyze_financial_trend(finance_df: pd.DataFrame, years: int = 3) -> Dict:
    """
    分析财务指标趋势（V3.5 Phase 1核心函数）
    
    分析5项核心指标的趋势：
    1. ROE（净资产收益率）- 最重要的盈利指标
    2. 毛利率 - 盈利质量
    3. 净利率 - 盈利效率
    4. 营收增长 - 成长能力
    5. 利润增长 - 成长质量
    
    Args:
        finance_df: 财务数据（来自get_stock_finance）
        years: 分析年数（默认3年，推荐3-5年）
    
    Returns:
        dict: {
            'available': bool,           # 数据是否可用
            'data_periods': list,        # 使用的报告期
            'data_type': str,            # '年报'/'季报'/'混合'
            'confidence': str,           # '高'/'中'/'低'
            
            'roe_trend': {...},          # ROE趋势分析
            'gross_margin_trend': {...}, # 毛利率趋势
            'net_margin_trend': {...},   # 净利率趋势
            'revenue_growth_trend': {...}, # 营收增长趋势
            'profit_growth_trend': {...},  # 利润增长趋势
            
            'total_trend_score': int,    # 总趋势加分
            'trend_summary': str,        # 趋势总结
            'trend_grade': str           # 趋势评级（A/B/C/D）
        }
    """
    
    # 1. 过滤正式财报
    classified = classify_finance_data(finance_df)
    official = classified['official_reports']
    
    if len(official) < years:
        return {
            'available': False,
            'message': f'正式财报数据不足（需要{years}期，当前{len(official)}期）',
            'total_trend_score': 0,
            'trend_grade': 'N/A'
        }
    
    # 2. 优先使用年报（年报数据更完整）
    annual_only = official[official['报告期'].str.contains('年报', na=False)]
    
    if len(annual_only) >= years:
        trend_data = annual_only.head(years)
        data_type = '年报'
        confidence = '高'
    else:
        # 年报不足，尝试使用相同季度的季报
        trend_data = _filter_same_quarter_reports(official, years)
        if trend_data is not None and len(trend_data) >= years:
            data_type = '季报'
            confidence = '中'
        else:
            # 最后尝试：使用所有可用数据
            trend_data = official.head(years)
            data_type = '混合'
            confidence = '低'
    
    # 3. 按时间升序排列（最早→最新）
    trend_data = trend_data.sort_values('报告期', ascending=True)
    periods = trend_data['报告期'].tolist()
    
    # 4. 分析各指标趋势
    trend_results = {}
    
    # 4.1 ROE趋势（满分5分）
    roe_values = []
    for _, row in trend_data.iterrows():
        roe = row.get('净资产收益率(加权)(%)', None)
        roe_values.append(float(roe) if pd.notna(roe) else None)
    
    roe_trend = determine_trend(roe_values)
    trend_results['roe_trend'] = {
        'values': roe_values,
        'trend_type': roe_trend['trend_type'],
        'trend_text': roe_trend['trend_text'],
        'trend_icon': roe_trend['trend_icon'],
        'score_adjustment': roe_trend['score_adjustment'],
        'message': f"ROE{roe_trend['trend_text']}"
    }
    
    # 4.2 毛利率趋势（满分3分）
    gm_values = []
    for _, row in trend_data.iterrows():
        gm = row.get('毛利率(%)', None)
        gm_values.append(float(gm) if pd.notna(gm) else None)
    
    gm_trend = determine_trend(gm_values)
    # 毛利率满分3分，调整加分
    gm_score_adj = int(gm_trend['score_adjustment'] * 3 / 5)
    trend_results['gross_margin_trend'] = {
        'values': gm_values,
        'trend_type': gm_trend['trend_type'],
        'trend_text': gm_trend['trend_text'],
        'trend_icon': gm_trend['trend_icon'],
        'score_adjustment': gm_score_adj,
        'message': f"毛利率{gm_trend['trend_text']}"
    }
    
    # 4.3 净利率趋势（满分3分）
    nm_values = []
    for _, row in trend_data.iterrows():
        nm = row.get('净利率(%)', None)
        nm_values.append(float(nm) if pd.notna(nm) else None)
    
    nm_trend = determine_trend(nm_values)
    nm_score_adj = int(nm_trend['score_adjustment'] * 3 / 5)
    trend_results['net_margin_trend'] = {
        'values': nm_values,
        'trend_type': nm_trend['trend_type'],
        'trend_text': nm_trend['trend_text'],
        'trend_icon': nm_trend['trend_icon'],
        'score_adjustment': nm_score_adj,
        'message': f"净利率{nm_trend['trend_text']}"
    }
    
    # 4.4 营收增长趋势（满分3分）
    rg_values = []
    for _, row in trend_data.iterrows():
        rg = row.get('营业总收入同比增长(%)', None)
        rg_values.append(float(rg) if pd.notna(rg) else None)
    
    rg_trend = determine_trend(rg_values, threshold=10.0)  # 增长率波动阈值放宽到10%
    rg_score_adj = int(rg_trend['score_adjustment'] * 3 / 5)
    trend_results['revenue_growth_trend'] = {
        'values': rg_values,
        'trend_type': rg_trend['trend_type'],
        'trend_text': rg_trend['trend_text'],
        'trend_icon': rg_trend['trend_icon'],
        'score_adjustment': rg_score_adj,
        'message': f"营收增长{rg_trend['trend_text']}"
    }
    
    # 4.5 利润增长趋势（满分5分）
    pg_values = []
    for _, row in trend_data.iterrows():
        pg = row.get('归属净利润同比增长(%)', None)
        pg_values.append(float(pg) if pd.notna(pg) else None)
    
    pg_trend = determine_trend(pg_values, threshold=10.0)  # 增长率波动阈值放宽到10%
    trend_results['profit_growth_trend'] = {
        'values': pg_values,
        'trend_type': pg_trend['trend_type'],
        'trend_text': pg_trend['trend_text'],
        'trend_icon': pg_trend['trend_icon'],
        'score_adjustment': pg_trend['score_adjustment'],
        'message': f"利润增长{pg_trend['trend_text']}"
    }
    
    # 5. 计算总趋势评分
    total_trend_score = sum([
        trend_results['roe_trend']['score_adjustment'],
        trend_results['gross_margin_trend']['score_adjustment'],
        trend_results['net_margin_trend']['score_adjustment'],
        trend_results['revenue_growth_trend']['score_adjustment'],
        trend_results['profit_growth_trend']['score_adjustment']
    ])
    
    # 6. 趋势总结
    positive_count = sum(1 for t in trend_results.values() if t['score_adjustment'] > 0)
    negative_count = sum(1 for t in trend_results.values() if t['score_adjustment'] < 0)
    
    if positive_count >= 4:
        trend_summary = "财务指标整体改善 🔥"
        trend_grade = 'A'
    elif positive_count >= 3:
        trend_summary = "财务指标多数改善"
        trend_grade = 'B'
    elif negative_count >= 4:
        trend_summary = "财务指标整体恶化 ⚠️"
        trend_grade = 'D'
    elif negative_count >= 3:
        trend_summary = "财务指标多数恶化"
        trend_grade = 'C'
    else:
        trend_summary = "财务指标趋势分化"
        trend_grade = 'B'
    
    return {
        'available': True,
        'data_periods': periods,
        'data_type': data_type,
        'confidence': confidence,
        **trend_results,
        'total_trend_score': total_trend_score,
        'trend_summary': trend_summary,
        'trend_grade': trend_grade
    }


def _filter_same_quarter_reports(official_df: pd.DataFrame, min_count: int = 3) -> Optional[pd.DataFrame]:
    """
    过滤相同季度的报告（用于季报趋势分析）
    
    例如：仅保留三季报（2023三季报、2024三季报、2025三季报）
    
    Args:
        official_df: 正式财报DataFrame
        min_count: 最少需要的报告数量
    
    Returns:
        DataFrame或None
    """
    # 排除年报
    quarterly = official_df[~official_df['报告期'].str.contains('年报', na=False)]
    
    if len(quarterly) < min_count:
        return None
    
    # 提取季度类型（如"三季报"、"中报"、"一季报"）
    def get_quarter_type(period):
        period = str(period)
        if '三季报' in period:
            return '三季报'
        elif '中报' in period or '半年报' in period:
            return '中报'
        elif '一季报' in period:
            return '一季报'
        else:
            return '其他'
    
    quarterly = quarterly.copy()
    quarterly['quarter_type'] = quarterly['报告期'].apply(get_quarter_type)
    
    # 找出数量最多的季度类型
    quarter_counts = quarterly['quarter_type'].value_counts()
    
    if len(quarter_counts) == 0:
        return None
    
    most_common = quarter_counts.index[0]
    
    if quarter_counts[most_common] >= min_count:
        return quarterly[quarterly['quarter_type'] == most_common].drop('quarter_type', axis=1)
    
    return None


# ============================================================
# 七、使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("财务数据过滤工具 V1.1 测试（最新优先逻辑）")
    print("=" * 60)
    
    # 测试股票
    test_code = '300308'
    
    # 导入数据库工具
    from stock_db_tool import get_stock_finance
    
    # 获取财务数据
    finance_df = get_stock_finance(test_code, limit=10)
    
    if len(finance_df) == 0:
        print("无财务数据")
    else:
        print(f"\n获取到 {len(finance_df)} 条财务数据")
        print(f"报告期列表: {get_report_periods_list(finance_df)}")
        
        # 分类测试
        classified = classify_finance_data(finance_df)
        summary = classified['classification_summary']
        
        print("\n【分类统计】")
        print(f"正式财报: {summary['official_count']} 条")
        print(f"  - 年报: {summary['annual_count']} 条")
        print(f"  - 季报: {summary['quarterly_count']} 条")
        print(f"业绩预告: {summary['forecast_count']} 条")
        
        print("\n【最新数据】")
        official = classified['official_reports']
        if len(official) > 0:
            print(f"🔥 最新正式财报: {official.iloc[0]['报告期']}")
        if summary['has_annual']:
            print(f"最新年报: {summary['latest_annual_period']}")
        if summary['has_quarterly']:
            print(f"最新季报: {summary['latest_quarterly_period']}")
        if summary['has_forecast']:
            print(f"最新预告: {summary['latest_forecast_period']}")
        
        # 🔥 最佳分析数据源（最新优先）
        best_data, source_message = get_best_analysis_data(finance_df)
        print(f"\n【🔥 最佳分析数据源（最新优先）】")
        print(f"来源: {source_message}")
        
        # 数据可用性检查
        availability = check_data_availability(finance_df)
        print(f"\n【数据可用性】")
        print(f"可评分: {availability['can_score']}")
        print(f"最新数据: {availability.get('latest_period', '无')}")
        print(f"状态: {availability['message']}")
        
        # 数据质量报告
        quality = generate_data_quality_report(classified)
        print(f"\n【数据质量报告】")
        print(f"{quality['status_icon']} {quality['status_text']}")
        
        for source in quality['data_sources']:
            latest_mark = '🔥' if source.get('is_latest') else '  '
            print(f"{latest_mark} {source['type']}: {source['period']} → {source['usage']}")
        
        if quality['warnings']:
            print("⚠️ 警告:")
            for w in quality['warnings']:
                print(f"  - {w}")
        
        if quality['suggestions']:
            print("💡 建议:")
            for s in quality['suggestions']:
                print(f"  - {s}")
        
        # TTM计算数据
        ttm_data = get_ttm_calculation_data(finance_df)
        print(f"\n【TTM计算数据】")
        print(f"可用: {ttm_data['available']}")
        print(f"说明: {ttm_data['message']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)