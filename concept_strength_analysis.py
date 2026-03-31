"""
概念强度量化评分模块 - V3.2新增
用于分析股票概念强度、板块轮动、股票-板块共振

功能：
1. 概念强度量化评分
2. 板块轮动分析
3. 股票-板块共振分析
4. 热门板块识别
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import sys

# 添加工作空间路径
sys.path.insert(0, '/Users/jw/.openclaw/workspace')
from stock_db_tool import (
    get_stock_concept_detail,
    get_hot_concepts,
    get_concept_market_strength,
    get_concept_kline
)


# ============================================================
# 一、概念强度量化评分
# ============================================================

def calculate_concept_strength_score(stock_code: str, limit: int = 10) -> Dict:
    """
    计算股票概念强度量化评分
    
    Args:
        stock_code: 股票代码
        limit: 返回概念数量限制
    
    Returns:
        dict: {
            'concept_score': 概念强度评分（0-100）,
            'strong_concepts': 强势概念列表,
            'avg_strength': 平均强度,
            'max_strength': 最强概念强度,
            'concept_count': 概念总数
        }
    """
    # 获取股票概念详情
    concepts_df = get_stock_concept_detail(stock_code, limit=limit)
    
    if len(concepts_df) == 0:
        return {
            'concept_score': 0,
            'strong_concepts': [],
            'avg_strength': 0,
            'max_strength': 0,
            'concept_count': 0,
            'message': '无概念数据'
        }
    
    # 计算各项指标
    avg_strength = concepts_df['strength_score'].mean()
    max_strength = concepts_df['strength_score'].max()
    
    # 强势概念（strength_level == '强势'）
    strong_concepts = concepts_df[concepts_df['strength_level'] == '强势']
    strong_count = len(strong_concepts)
    
    # 计算概念强度评分
    # 维度1：平均强度（40分）
    avg_score = min(40, avg_strength * 0.5)
    
    # 维度2：强势概念数量（30分）
    strong_score = min(30, strong_count * 6)
    
    # 维度3：最强概念强度（30分）
    max_score = min(30, max_strength * 0.3)
    
    concept_score = round(avg_score + strong_score + max_score, 2)
    
    return {
        'concept_score': concept_score,
        'strong_concepts': strong_concepts[['board_name', 'strength_score', 'strength_level']].to_dict('records'),
        'avg_strength': round(avg_strength, 2),
        'max_strength': round(max_strength, 2),
        'concept_count': len(concepts_df),
        'strong_count': strong_count
    }


def get_concept_strength_detail(stock_code: str, limit: int = 8) -> pd.DataFrame:
    """
    获取概念强度详情（带评分等级）
    
    Args:
        stock_code: 股票代码
        limit: 返回数量
    
    Returns:
        DataFrame: 概念强度详情
    """
    concepts_df = get_stock_concept_detail(stock_code, limit=limit)
    
    if len(concepts_df) == 0:
        return pd.DataFrame()
    
    # 添加评分等级
    def get_strength_grade(score):
        if score >= 75:
            return 'A+'
        elif score >= 65:
            return 'A'
        elif score >= 55:
            return 'B+'
        elif score >= 45:
            return 'B'
        elif score >= 35:
            return 'C'
        else:
            return 'D'
    
    concepts_df['strength_grade'] = concepts_df['strength_score'].apply(get_strength_grade)
    
    return concepts_df[['board_name', 'strength_score', 'strength_level', 'strength_grade', 
                        'total_return', 'excess_5d', 'excess_20d', 'rank_in_board']]


# ============================================================
# 二、板块轮动分析
# ============================================================

def analyze_sector_rotation(top_n: int = 20) -> Dict:
    """
    分析板块轮动情况
    
    Args:
        top_n: 分析的热门板块数量
    
    Returns:
        dict: {
            'hot_sectors': 热门板块列表,
            'sector_rotation_score': 板块轮动评分,
            'leading_sectors': 领涨板块,
            'suggested_focus': 建议关注板块
        }
    """
    # 获取热门概念板块
    hot_df = get_hot_concepts(top_n=top_n)
    
    if len(hot_df) == 0:
        return {
            'hot_sectors': [],
            'sector_rotation_score': 0,
            'leading_sectors': [],
            'suggested_focus': [],
            'message': '无板块数据'
        }
    
    # 分析板块强度分布
    high_strength = hot_df[hot_df['market_strength_score'] >= 80]
    medium_strength = hot_df[(hot_df['market_strength_score'] >= 60) & 
                             (hot_df['market_strength_score'] < 80)]
    
    # 板块轮动评分
    # 高强度板块占比
    high_ratio = len(high_strength) / len(hot_df) * 100
    
    # 平均强度
    avg_strength = hot_df['market_strength_score'].mean()
    
    # 轮动评分 = 平均强度 * 0.5 + 高强度占比 * 0.5
    rotation_score = round(avg_strength * 0.5 + high_ratio * 0.5, 2)
    
    # 领涨板块（强度前5）
    leading = hot_df.head(5)
    
    return {
        'hot_sectors': hot_df[['board_name', 'market_strength_score']].to_dict('records'),
        'sector_rotation_score': rotation_score,
        'high_strength_count': len(high_strength),
        'medium_strength_count': len(medium_strength),
        'avg_strength': round(avg_strength, 2),
        'leading_sectors': leading[['board_name', 'market_strength_score']].to_dict('records'),
        'suggested_focus': leading[['board_name', 'market_strength_score']].to_dict('records')[:3]
    }


def get_sector_strength_trend(board_code: str, days: int = 30) -> Dict:
    """
    获取板块强度趋势
    
    Args:
        board_code: 板块代码
        days: 分析天数
    
    Returns:
        dict: 板块强度趋势分析
    """
    # 获取板块K线
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    kline_df = get_concept_kline(board_code, start_date=start_date, end_date=end_date)
    
    if len(kline_df) == 0:
        return {'trend': '无数据', 'strength': 0}
    
    # 计算趋势
    recent_5d = kline_df.tail(5)
    recent_10d = kline_df.tail(10)
    
    # 5日涨跌幅
    change_5d = (recent_5d.iloc[-1]['close_price'] - recent_5d.iloc[0]['close_price']) / recent_5d.iloc[0]['close_price'] * 100
    
    # 10日涨跌幅
    change_10d = (recent_10d.iloc[-1]['close_price'] - recent_10d.iloc[0]['close_price']) / recent_10d.iloc[0]['close_price'] * 100
    
    # 判断趋势
    if change_5d > 3 and change_10d > 5:
        trend = '强势上涨'
        strength = 80
    elif change_5d > 0 and change_10d > 0:
        trend = '温和上涨'
        strength = 60
    elif change_5d < -3 and change_10d < -5:
        trend = '弱势下跌'
        strength = 20
    elif change_5d < 0 and change_10d < 0:
        trend = '温和下跌'
        strength = 40
    else:
        trend = '震荡整理'
        strength = 50
    
    return {
        'trend': trend,
        'strength': strength,
        'change_5d': round(change_5d, 2),
        'change_10d': round(change_10d, 2),
        'board_code': board_code
    }


# ============================================================
# 三、股票-板块共振分析
# ============================================================

def analyze_stock_sector_resonance(stock_code: str, limit: int = 10) -> Dict:
    """
    分析股票与板块的共振情况
    
    Args:
        stock_code: 股票代码
        limit: 分析的概念数量
    
    Returns:
        dict: {
            'resonance_score': 共振评分,
            'resonance_level': 共振等级,
            'strong_resonance': 强共振概念列表,
            'weak_resonance': 弱共振概念列表,
            'independent_stocks': 独立行情概念（股票强板块弱）,
            'analysis': 分析结论
        }
    """
    # 获取股票概念详情
    concepts_df = get_stock_concept_detail(stock_code, limit=limit)
    
    if len(concepts_df) == 0:
        return {
            'resonance_score': 0,
            'resonance_level': '无数据',
            'strong_resonance': [],
            'weak_resonance': [],
            'independent_stocks': [],
            'analysis': '该股票无概念数据'
        }
    
    # 共振分析
    strong_resonance = []
    weak_resonance = []
    independent_stocks = []  # 股票强、板块弱（独立行情）
    lagging_stocks = []  # 股票弱、板块强（滞后）
    
    for _, row in concepts_df.iterrows():
        stock_strength = row['strength_score']
        # 使用实际的板块市场强度
        sector_strength = row.get('market_strength_score', 50)
        if pd.isna(sector_strength):
            sector_strength = 50
        strength_level = row['strength_level']
        
        # 判断共振情况（四个象限）
        if stock_strength >= 60 and sector_strength >= 60:
            # 股票强 + 板块强 = 强共振
            resonance_type = '强共振'
            strong_resonance.append({
                'board_name': row['board_name'],
                'stock_strength': round(stock_strength, 2),
                'sector_strength': round(sector_strength, 2),
                'resonance_type': resonance_type,
                'score': round(min(100, (stock_strength + sector_strength) / 2), 2)
            })
        elif stock_strength >= 60 and sector_strength < 60:
            # 股票强 + 板块弱 = 独立行情
            resonance_type = '独立行情'
            independent_stocks.append({
                'board_name': row['board_name'],
                'stock_strength': round(stock_strength, 2),
                'sector_strength': round(sector_strength, 2),
                'resonance_type': resonance_type,
                'score': round(stock_strength, 2)
            })
        elif stock_strength < 40 and sector_strength >= 60:
            # 股票弱 + 板块强 = 滞后
            resonance_type = '滞后'
            lagging_stocks.append({
                'board_name': row['board_name'],
                'stock_strength': round(stock_strength, 2),
                'sector_strength': round(sector_strength, 2),
                'resonance_type': resonance_type
            })
        elif stock_strength < 40 and sector_strength < 40:
            # 股票弱 + 板块弱 = 弱共振
            resonance_type = '弱共振'
            weak_resonance.append({
                'board_name': row['board_name'],
                'stock_strength': round(stock_strength, 2),
                'sector_strength': round(sector_strength, 2),
                'resonance_type': resonance_type,
                'score': round((stock_strength + sector_strength) / 2, 2)
            })
    
    # 计算共振评分
    # 基准分50，根据各种情况加减分
    resonance_score = 50
    
    # 强共振加分
    for item in strong_resonance:
        resonance_score += item['score'] * 0.15
    
    # 独立行情小幅加分（股票自身强势）
    for item in independent_stocks:
        resonance_score += item['stock_strength'] * 0.05
    
    # 弱共振减分
    for item in weak_resonance:
        resonance_score -= (100 - item['score']) * 0.1
    
    resonance_score = max(0, min(100, round(resonance_score, 2)))
    
    # 判断共振等级和分析结论
    if len(strong_resonance) >= 2:
        resonance_level = '强共振'
        analysis = f'股票与{len(strong_resonance)}个概念形成强共振，上涨动能充足'
    elif len(strong_resonance) >= 1:
        resonance_level = '偏强共振'
        analysis = f'股票与{strong_resonance[0]["board_name"]}形成强共振，有望跟随板块上涨'
    elif len(independent_stocks) >= 3:
        resonance_level = '独立行情'
        analysis = f'股票在{len(independent_stocks)}个概念中表现强势但板块偏弱，属独立行情'
    elif resonance_score >= 55:
        resonance_level = '偏强共振'
        analysis = '股票与板块共振偏强，有望跟随板块上涨'
    elif resonance_score >= 45:
        resonance_level = '中性'
        analysis = '股票与板块共振不明显，需关注个股自身逻辑'
    elif resonance_score >= 30:
        resonance_level = '偏弱共振'
        analysis = '股票与板块共振偏弱，注意下跌风险'
    else:
        resonance_level = '弱共振'
        analysis = '股票与板块形成弱共振，下跌风险较大'
    
    return {
        'resonance_score': resonance_score,
        'resonance_level': resonance_level,
        'strong_resonance': sorted(strong_resonance, key=lambda x: x['score'], reverse=True)[:5],
        'weak_resonance': weak_resonance[:5],
        'independent_stocks': sorted(independent_stocks, key=lambda x: x['score'], reverse=True)[:5],
        'independent_count': len(independent_stocks),
        'analysis': analysis
    }


# ============================================================
# 四、综合概念分析报告
# ============================================================

def generate_concept_analysis_report(stock_code: str, stock_name: str = '') -> Dict:
    """
    生成概念分析综合报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
    
    Returns:
        dict: 完整的概念分析报告
    """
    # 1. 概念强度评分
    strength_result = calculate_concept_strength_score(stock_code, limit=10)
    
    # 2. 共振分析
    resonance_result = analyze_stock_sector_resonance(stock_code, limit=10)
    
    # 3. 板块轮动
    rotation_result = analyze_sector_rotation(top_n=10)
    
    # 4. 概念详情
    concepts_detail = get_concept_strength_detail(stock_code, limit=8)
    
    # 5. 综合评分
    # 概念强度评分权重50%，共振评分权重50%
    combined_score = round(
        strength_result['concept_score'] * 0.5 + 
        resonance_result['resonance_score'] * 0.5, 
        2
    )
    
    return {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        
        # 综合评分
        'combined_concept_score': combined_score,
        
        # 概念强度
        'concept_strength': {
            'score': strength_result['concept_score'],
            'avg_strength': strength_result['avg_strength'],
            'strong_count': strength_result.get('strong_count', 0),
            'total_count': strength_result['concept_count']
        },
        
        # 共振分析
        'resonance': {
            'score': resonance_result['resonance_score'],
            'level': resonance_result['resonance_level'],
            'analysis': resonance_result['analysis'],
            'strong_resonance': resonance_result['strong_resonance']
        },
        
        # 板块轮动
        'sector_rotation': {
            'score': rotation_result['sector_rotation_score'],
            'leading_sectors': rotation_result['leading_sectors'][:3]
        },
        
        # 概念详情
        'concepts_detail': concepts_detail.to_dict('records') if len(concepts_detail) > 0 else []
    }


# ============================================================
# 五、使用示例
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("概念强度量化评分模块测试")
    print("="*60)
    
    # 测试股票
    test_code = '300308'
    test_name = '中际旭创'
    
    # 1. 测试概念强度评分
    print("\n【1. 概念强度评分】")
    result = calculate_concept_strength_score(test_code, limit=10)
    print(f"概念强度评分: {result['concept_score']}")
    print(f"平均强度: {result['avg_strength']}")
    print(f"强势概念数: {result.get('strong_count', 0)}")
    if result['strong_concepts']:
        print("强势概念:")
        for c in result['strong_concepts'][:3]:
            print(f"  - {c['board_name']}: {c['strength_score']}")
    
    # 2. 测试板块轮动
    print("\n【2. 板块轮动分析】")
    rotation = analyze_sector_rotation(top_n=10)
    print(f"板块轮动评分: {rotation['sector_rotation_score']}")
    print(f"高强度板块数: {rotation['high_strength_count']}")
    print("领涨板块:")
    for s in rotation['leading_sectors'][:3]:
        print(f"  - {s['board_name']}: {s['market_strength_score']}")
    
    # 3. 测试共振分析
    print("\n【3. 股票-板块共振分析】")
    resonance = analyze_stock_sector_resonance(test_code, limit=10)
    print(f"共振评分: {resonance['resonance_score']}")
    print(f"共振等级: {resonance['resonance_level']}")
    print(f"分析结论: {resonance['analysis']}")
    if resonance['strong_resonance']:
        print("强共振概念:")
        for r in resonance['strong_resonance'][:3]:
            print(f"  - {r['board_name']}: 股票{r['stock_strength']:.1f} + 板块{r['sector_strength']:.1f}")
    
    # 4. 测试综合报告
    print("\n【4. 概念分析综合报告】")
    report = generate_concept_analysis_report(test_code, test_name)
    print(f"股票: {report['stock_name']} ({report['stock_code']})")
    print(f"综合概念评分: {report['combined_concept_score']}")
    print(f"概念强度评分: {report['concept_strength']['score']}")
    print(f"共振评分: {report['resonance']['score']}")
    print(f"共振等级: {report['resonance']['level']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)