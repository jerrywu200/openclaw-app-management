"""
事件驱动分析模块 - V3.2新增
用于分析新闻、公告等事件对股价的影响

功能：
1. 新闻情感分析
2. 公告影响评估
3. 事件-股价关联分析
4. 事件评分计算
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import sys
import os

# 添加工作空间路径
sys.path.insert(0, '/Users/jw/.openclaw/workspace')
from stock_db_tool import get_stock_news, get_stock_kline


# ============================================================
# 一、新闻情感分析
# ============================================================

# 正面关键词库
POSITIVE_KEYWORDS = {
    # 业绩相关
    '预增': 15, '增长': 10, '扭亏': 15, '盈利': 8, '大增': 12,
    '超预期': 12, '高增长': 10, '翻倍': 15, '创新高': 10,
    
    # 订单/合同
    '中标': 12, '签订': 8, '合同': 8, '订单': 10, '大单': 12,
    '合作': 8, '战略合作': 10, '框架协议': 8,
    
    # 资本运作
    '回购': 10, '增持': 12, '并购': 10, '重组': 12, '注入': 10,
    
    # 技术/产品
    '突破': 10, '首发': 10, '量产': 8, '新品': 8, '研发成功': 10,
    
    # 政策利好
    '补贴': 8, '扶持': 8, '利好': 10, '政策支持': 10,
    
    # 行业地位
    '龙头': 8, '领先': 8, '第一': 10, '市场份额提升': 10,
}

# 负面关键词库
NEGATIVE_KEYWORDS = {
    # 业绩相关
    '预亏': -15, '亏损': -12, '预降': -12, '下滑': -10, '下降': -8,
    '不及预期': -10, '暴雷': -15, '减值': -10,
    
    # 风险事件
    '诉讼': -12, '处罚': -15, '立案': -15, '违规': -12,
    '调查': -10, '警示': -8, '监管': -8,
    
    # 经营风险
    '停产': -15, '停工': -12, '裁员': -10, '欠薪': -12,
    '债务': -10, '违约': -15, '担保风险': -12,
    
    # 股权风险
    '减持': -10, '质押风险': -10, '冻结': -12, '拍卖': -12,
    
    # 行业风险
    '退市': -20, 'ST': -15, '*ST': -15, '风险警示': -12,
}

# 中性但需关注的关键词
NEUTRAL_KEYWORDS = {
    '公告': 0, '披露': 0, '报告': 0, '说明': 0,
    '股东大会': 0, '董事会': 0, '换届': 0,
}


def analyze_news_sentiment(title: str, content: Optional[str] = None) -> Dict:
    """
    分析单条新闻的情感倾向
    
    Args:
        title: 新闻标题
        content: 新闻内容（可选）
    
    Returns:
        dict: {
            'sentiment': 'positive/negative/neutral',
            'score': 情感得分,
            'matched_keywords': 匹配的关键词列表,
            'impact_level': 影响等级（高/中/低）
        }
    """
    text = str(title) if title else ''
    if content and pd.notna(content):
        text += ' ' + str(content)
    
    score = 0
    matched_positive = []
    matched_negative = []
    
    # 检查正面关键词
    for keyword, keyword_score in POSITIVE_KEYWORDS.items():
        if keyword in text:
            score += keyword_score
            matched_positive.append((keyword, keyword_score))
    
    # 检查负面关键词
    for keyword, keyword_score in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            score += keyword_score
            matched_negative.append((keyword, keyword_score))
    
    # 判断情感倾向
    if score >= 10:
        sentiment = 'positive'
    elif score <= -10:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    # 判断影响等级
    abs_score = abs(score)
    if abs_score >= 20:
        impact_level = '高'
    elif abs_score >= 10:
        impact_level = '中'
    else:
        impact_level = '低'
    
    return {
        'sentiment': sentiment,
        'score': score,
        'matched_positive': matched_positive,
        'matched_negative': matched_negative,
        'impact_level': impact_level
    }


def analyze_news_batch(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    批量分析新闻情感
    
    Args:
        news_df: 新闻DataFrame（包含title, content列）
    
    Returns:
        DataFrame: 添加了情感分析结果的新闻数据
    """
    results = []
    
    for idx, row in news_df.iterrows():
        title = row.get('title', '')
        content = row.get('content', '')
        
        analysis = analyze_news_sentiment(title, content)
        
        results.append({
            'publish_date': row.get('publish_date'),
            'publish_time': row.get('publish_time'),
            'news_type': row.get('news_type'),
            'title': title,
            'sentiment': analysis['sentiment'],
            'sentiment_score': analysis['score'],
            'impact_level': analysis['impact_level'],
            'positive_keywords': [k[0] for k in analysis['matched_positive']],
            'negative_keywords': [k[0] for k in analysis['matched_negative']],
        })
    
    return pd.DataFrame(results)


# ============================================================
# 二、公告影响评估
# ============================================================

# 公告类型影响权重
ANNOUNCEMENT_WEIGHTS = {
    'forecast': {
        'name': '业绩预告',
        'weight': 1.5,  # 影响权重
        'watch_keywords': ['预增', '预亏', '扭亏', '下降', '增长']
    },
    'notice': {
        'name': '重要公告',
        'weight': 1.3,
        'watch_keywords': ['重大', '收购', '出售', '投资', '重组']
    },
    'event': {
        'name': '公司事件',
        'weight': 1.2,
        'watch_keywords': ['中标', '合同', '合作', '诉讼', '处罚']
    },
    'report': {
        'name': '研报',
        'weight': 0.8,
        'watch_keywords': ['买入', '增持', '推荐', '下调']
    },
    'industry': {
        'name': '行业新闻',
        'weight': 0.6,
        'watch_keywords': ['政策', '补贴', '限制', '利好']
    },
    'news': {
        'name': '新闻报道',
        'weight': 0.5,
        'watch_keywords': []
    },
}


def evaluate_announcement_impact(news_row: pd.Series) -> Dict:
    """
    评估单条公告的影响
    
    Args:
        news_row: 新闻数据行
    
    Returns:
        dict: {
            'announcement_type': 公告类型,
            'impact_score': 影响分数,
            'impact_direction': 影响方向（正面/负面/中性）,
            'importance': 重要程度,
            'suggested_action': 建议行动
        }
    """
    news_type = news_row.get('news_type', 'news')
    title = news_row.get('title', '')
    
    # 获取公告类型权重
    type_info = ANNOUNCEMENT_WEIGHTS.get(news_type, ANNOUNCEMENT_WEIGHTS['news'])
    
    # 分析情感
    sentiment_analysis = analyze_news_sentiment(title)
    
    # 计算加权影响分数
    weight = type_info['weight']
    base_score = sentiment_analysis['score']
    impact_score = base_score * weight
    
    # 判断重要程度
    abs_score = abs(impact_score)
    if abs_score >= 15:
        importance = '高'
    elif abs_score >= 8:
        importance = '中'
    else:
        importance = '低'
    
    # 判断影响方向
    if impact_score >= 8:
        impact_direction = '正面'
        suggested_action = '关注买入机会'
    elif impact_score <= -8:
        impact_direction = '负面'
        suggested_action = '注意风险'
    else:
        impact_direction = '中性'
        suggested_action = '持续关注'
    
    return {
        'announcement_type': type_info['name'],
        'impact_score': round(impact_score, 2),
        'impact_direction': impact_direction,
        'importance': importance,
        'suggested_action': suggested_action,
        'sentiment': sentiment_analysis['sentiment']
    }


# ============================================================
# 三、事件-股价关联分析
# ============================================================

def analyze_event_price_correlation(
    stock_code: str,
    news_df: pd.DataFrame,
    kline_df: pd.DataFrame,
    window_days: int = 5
) -> List[Dict]:
    """
    分析事件与股价的关联关系
    
    Args:
        stock_code: 股票代码
        news_df: 新闻数据
        kline_df: K线数据
        window_days: 分析窗口天数
    
    Returns:
        List[Dict]: 事件影响分析结果列表
    """
    results = []
    
    # 确保K线数据按日期排序
    kline_df = kline_df.sort_values('date').reset_index(drop=True)
    kline_df['date'] = pd.to_datetime(kline_df['date'])
    
    for idx, news in news_df.iterrows():
        news_date = news.get('publish_date')
        if not news_date:
            continue
        
        try:
            news_date = pd.to_datetime(news_date)
        except:
            continue
        
        # 评估事件影响
        impact = evaluate_announcement_impact(news)
        
        # 查找事件后的股价表现
        news_kline = kline_df[kline_df['date'] >= news_date].head(window_days + 1)
        
        if len(news_kline) >= 2:
            # 事件当天
            event_day = news_kline.iloc[0]
            
            # N天后
            after_days = news_kline.iloc[-1] if len(news_kline) > 1 else event_day
            
            # 计算涨跌幅
            price_change = (after_days['close_price'] - event_day['close_price']) / event_day['close_price'] * 100
            
            results.append({
                'date': news_date.strftime('%Y-%m-%d'),
                'title': news.get('title', ''),
                'news_type': news.get('news_type'),
                'impact_score': impact['impact_score'],
                'impact_direction': impact['impact_direction'],
                'importance': impact['importance'],
                'price_change_5d': round(price_change, 2),
                'correlation': '一致' if (impact['impact_score'] > 0 and price_change > 0) or 
                                          (impact['impact_score'] < 0 and price_change < 0) else '背离'
            })
    
    return results


# ============================================================
# 四、事件评分计算
# ============================================================

def calculate_event_score(
    stock_code: str,
    days: int = 90,
    limit: int = 30
) -> Dict:
    """
    计算股票的事件驱动评分
    
    Args:
        stock_code: 股票代码
        days: 分析天数（默认90天）
        limit: 新闻条数限制
    
    Returns:
        dict: {
            'event_score': 事件评分（-30~30）,
            'positive_events': 正面事件列表,
            'negative_events': 负面事件列表,
            'key_events': 关键事件列表,
            'recent_sentiment': 近期情绪（偏多/偏空/中性）
        }
    """
    # 获取新闻数据
    news_df = get_stock_news(stock_code, limit=limit)
    
    if len(news_df) == 0:
        return {
            'event_score': 0,
            'positive_events': [],
            'negative_events': [],
            'key_events': [],
            'recent_sentiment': '中性',
            'message': '无近期新闻数据'
        }
    
    # 批量分析情感
    analyzed_news = analyze_news_batch(news_df)
    
    # 计算总评分
    total_score = 0
    positive_events = []
    negative_events = []
    key_events = []
    
    for idx, row in analyzed_news.iterrows():
        score = row['sentiment_score']
        impact = evaluate_announcement_impact(news_df.iloc[idx])
        
        total_score += impact['impact_score']
        
        # 收集重要事件
        if impact['importance'] == '高':
            event_info = {
                'date': row['publish_date'],
                'title': row['title'],
                'impact': impact['impact_direction'],
                'score': impact['impact_score']
            }
            key_events.append(event_info)
            
            if impact['impact_direction'] == '正面':
                positive_events.append(event_info)
            elif impact['impact_direction'] == '负面':
                negative_events.append(event_info)
    
    # 限制评分范围
    event_score = max(-30, min(30, round(total_score, 2)))
    
    # 判断近期情绪
    if event_score >= 10:
        recent_sentiment = '偏多'
    elif event_score <= -10:
        recent_sentiment = '偏空'
    else:
        recent_sentiment = '中性'
    
    return {
        'event_score': event_score,
        'positive_events': positive_events[:5],
        'negative_events': negative_events[:5],
        'key_events': key_events[:5],
        'recent_sentiment': recent_sentiment,
        'news_count': len(analyzed_news),
        'positive_count': len(analyzed_news[analyzed_news['sentiment'] == 'positive']),
        'negative_count': len(analyzed_news[analyzed_news['sentiment'] == 'negative'])
    }


# ============================================================
# 五、综合事件分析报告
# ============================================================

def generate_event_analysis_report(
    stock_code: str,
    stock_name: str = '',
    days: int = 90
) -> Dict:
    """
    生成事件分析报告
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        days: 分析天数
    
    Returns:
        dict: 完整的事件分析报告
    """
    # 获取事件评分
    event_result = calculate_event_score(stock_code, days=days)
    
    # 获取新闻详情
    news_df = get_stock_news(stock_code, limit=20)
    
    # 分析新闻情感
    if len(news_df) > 0:
        analyzed_news = analyze_news_batch(news_df)
    else:
        analyzed_news = pd.DataFrame()
    
    # 生成报告
    report = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        'analysis_period': f'近{days}天',
        
        # 事件评分
        'event_score': event_result['event_score'],
        'recent_sentiment': event_result['recent_sentiment'],
        
        # 关键事件
        'key_events': event_result['key_events'],
        
        # 正面事件
        'positive_events': event_result['positive_events'],
        
        # 负面事件
        'negative_events': event_result['negative_events'],
        
        # 统计信息
        'statistics': {
            'total_news': event_result.get('news_count', 0),
            'positive_news': event_result.get('positive_count', 0),
            'negative_news': event_result.get('negative_count', 0),
            'neutral_news': event_result.get('news_count', 0) - 
                           event_result.get('positive_count', 0) - 
                           event_result.get('negative_count', 0)
        },
        
        # 新闻详情
        'news_details': analyzed_news.to_dict('records') if len(analyzed_news) > 0 else []
    }
    
    return report


# ============================================================
# 六、使用示例
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("事件驱动分析模块测试")
    print("="*60)
    
    # 测试股票
    test_code = '300308'
    test_name = '中际旭创'
    
    # 1. 测试单条新闻情感分析
    print("\n【1. 单条新闻情感分析】")
    test_title = "中际旭创2025年净利润同比增长47.74%，业绩超预期"
    result = analyze_news_sentiment(test_title)
    print(f"标题: {test_title}")
    print(f"情感: {result['sentiment']}")
    print(f"得分: {result['score']}")
    print(f"匹配关键词: {result['matched_positive']}")
    
    # 2. 测试事件评分计算
    print("\n【2. 事件评分计算】")
    event_result = calculate_event_score(test_code, days=90)
    print(f"事件评分: {event_result['event_score']}")
    print(f"近期情绪: {event_result['recent_sentiment']}")
    print(f"正面事件数: {len(event_result['positive_events'])}")
    print(f"负面事件数: {len(event_result['negative_events'])}")
    
    # 3. 测试完整报告生成
    print("\n【3. 事件分析报告】")
    report = generate_event_analysis_report(test_code, test_name, days=90)
    print(f"股票: {report['stock_name']} ({report['stock_code']})")
    print(f"事件评分: {report['event_score']}")
    print(f"近期情绪: {report['recent_sentiment']}")
    print(f"新闻统计: {report['statistics']}")
    
    if report['key_events']:
        print("\n关键事件:")
        for event in report['key_events'][:3]:
            print(f"  [{event['date']}] {event['title'][:30]}... ({event['impact']})")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)