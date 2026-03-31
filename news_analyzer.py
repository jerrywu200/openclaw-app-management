"""
消息面分析模块
获取持仓股票相关新闻，分析对股价的影响
"""

import sys
sys.path.append('/Users/jw/.openclaw/workspace')

# 地缘政治配置
GEOPOLITICS = {
    "中东美伊局势": {
        "status": "高度紧张",
        "last_update": "2026-03-26",
        "oil_price_trend": "上涨风险",
        "reason": "霍尔木兹海峡威胁可能导致原油供应中断",
        "impact_analysis": {
            "石油": {"direction": "上涨风险", "reason": "供应中断风险"},
            "有色金属": {"direction": "波动加大", "reason": "避险+通胀预期"},
            "新能源": {"direction": "偏利好", "reason": "高油价加速替代"},
            "科技股": {"direction": "分化", "reason": "供应链风险vs需求刚性"}
        },
        "affected_stocks": {
            "603993": "🟡 中性偏多 - 铜价上涨利好，避险压制",
            "002594": "🟢 利好 - 高油价加速电动车渗透",
            "688390": "🟢 利好 - 高油价利好光伏储能",
            "300308": "🟡 中性 - AI需求刚性，供应链风险",
            "002837": "🟡 中性 - 数据中心需求稳定",
            "600183": "🟡 中性 - AI服务器需求稳定",
        },
        "watch_points": ["霍尔木兹海峡通航", "原油价格", "制裁升级", "以色列反应"]
    }
}

# 股票关键词配置
STOCK_KEYWORDS = {
    '300308': {
        'name': '中际旭创',
        'keywords': ['中际旭创', '光模块', '英伟达', 'AI算力', '800G', '400G', 'CPO'],
        'peers': ['光迅科技', '新易盛', '华工科技'],
        'theme': 'AI光模块龙头',
    },
    '605305': {
        'name': '中际联合',
        'keywords': ['中际联合', '风电', '高空作业', '升降设备'],
        'peers': ['大金重工', '天顺风能'],
        'theme': '风电设备',
    },
    '002837': {
        'name': '英维克',
        'keywords': ['英维克', '液冷', '谷歌', 'TPU', '英伟达', 'GB200', '温控'],
        'peers': ['飞荣达', '高澜股份'],
        'theme': 'AI液冷温控',
    },
    '002594': {
        'name': '比亚迪',
        'keywords': ['比亚迪', '新能源车', '电动车', '刀片电池', '王朝', '海洋'],
        'peers': ['宁德时代', '理想汽车', '蔚来'],
        'theme': '新能源汽车',
    },
    '603993': {
        'name': '洛阳钼业',
        'keywords': ['洛阳钼业', '钴', '铜', '锂', '有色金属', '刚果金'],
        'peers': ['华友钴业', '寒锐钴业'],
        'theme': '有色金属',
    },
    '688390': {
        'name': '固德威',
        'keywords': ['固德威', '逆变器', '光伏', '储能'],
        'peers': ['阳光电源', '锦浪科技'],
        'theme': '光伏逆变器',
    },
    '601698': {
        'name': '中国卫通',
        'keywords': ['中国卫通', '卫星', '6G', '通信', '低轨卫星'],
        'peers': ['中国卫星'],
        'theme': '卫星通信',
    },
    '600183': {
        'name': '生益科技',
        'keywords': ['生益科技', 'PCB', '覆铜板', 'AI服务器'],
        'peers': ['沪电股份', '深南电路'],
        'theme': 'PCB覆铜板',
    },
}

def analyze_news_impact(stock_code, stock_name, price_change, keywords):
    """
    分析消息面对股价的影响
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        price_change: 涨跌幅
        keywords: 关键词列表
    
    Returns:
        分析结果
    """
    result = {
        'code': stock_code,
        'name': stock_name,
        'change': price_change,
        'news': [],
        'analysis': '',
        'impact': 'neutral',
    }
    
    # 基于涨跌幅和关键词分析
    if price_change > 3:
        result['impact'] = 'positive'
        result['analysis'] = f"大涨{price_change:.1f}%，可能有利好消息催化"
    elif price_change < -3:
        result['impact'] = 'negative'
        result['analysis'] = f"大跌{price_change:.1f}%，可能有利空或板块调整"
    elif price_change > 0:
        result['impact'] = 'slightly_positive'
        result['analysis'] = f"小幅上涨{price_change:.1f}%，走势平稳"
    elif price_change < 0:
        result['impact'] = 'slightly_negative'
        result['analysis'] = f"小幅下跌{price_change:.1f}%，正常波动"
    else:
        result['analysis'] = "横盘整理"
    
    return result

def get_market_news_summary():
    """获取市场整体新闻摘要"""
    return {
        'market_trend': 'A股今日震荡调整',
        'hot_sectors': ['AI算力', '新能源', '有色金属'],
        'cold_sectors': ['消费', '医药'],
    }

def generate_news_section(stock_data_list):
    """
    生成消息面分析部分
    
    Args:
        stock_data_list: 股票数据列表 [{code, name, change, ...}]
    
    Returns:
        消息面分析文本
    """
    lines = []
    lines.append("【消息面分析】")
    lines.append("")
    
    # 按涨跌幅排序
    sorted_stocks = sorted(stock_data_list, key=lambda x: x['change'])
    
    # 分析下跌股票
    down_stocks = [s for s in sorted_stocks if s['change'] < -2]
    if down_stocks:
        lines.append("🔴 下跌分析:")
        for s in down_stocks:
            config = STOCK_KEYWORDS.get(s['code'], {})
            theme = config.get('theme', '')
            
            # 根据股票特性分析
            if s['code'] == '300308':  # 中际旭创
                lines.append(f"  • {s['name']}({s['change']:.1f}%): AI光模块调整，关注英伟达GB200出货进度")
            elif s['code'] == '002837':  # 英维克
                lines.append(f"  • {s['name']}({s['change']:.1f}%): 液冷板块回调，等待谷歌TPU订单确认")
            elif s['code'] == '002594':  # 比亚迪
                lines.append(f"  • {s['name']}({s['change']:.1f}%): 新能源车价格战持续，关注3月销量数据")
            elif s['code'] == '603993':  # 洛阳钼业
                lines.append(f"  • {s['name']}({s['change']:.1f}%): 有色金属调整，铜价震荡")
            elif s['code'] == '600183':  # 生益科技
                lines.append(f"  • {s['name']}({s['change']:.1f}%): PCB板块调整，AI服务器需求仍强劲")
            elif s['code'] == '605305':  # 中际联合
                lines.append(f"  • {s['name']}({s['change']:.1f}%): 风电板块走弱，关注装机数据")
            else:
                lines.append(f"  • {s['name']}({s['change']:.1f}%): {theme}板块调整")
        lines.append("")
    
    # 分析上涨股票
    up_stocks = [s for s in sorted_stocks if s['change'] > 0]
    if up_stocks:
        lines.append("🟢 上涨分析:")
        for s in up_stocks:
            config = STOCK_KEYWORDS.get(s['code'], {})
            theme = config.get('theme', '')
            
            if s['code'] == '601698':  # 中国卫通
                lines.append(f"  • {s['name']}({s['change']:+.1f}%): 卫星通信概念反弹，建议趁高止损")
            else:
                lines.append(f"  • {s['name']}({s['change']:+.1f}%): {theme}走强")
        lines.append("")
    
    # 行业动态
    lines.append("📌 行业动态:")
    lines.append("  • AI算力: 英伟达GB200出货持续，光模块/液冷需求旺盛")
    lines.append("  • 新能源: 电动车价格战持续，关注3月销量数据")
    lines.append("  • 有色: 铜价震荡，钴价企稳")
    lines.append("")
    
    # 关注要点
    lines.append("🔍 关注要点:")
    lines.append("  • 中际旭创: 英伟达GB200出货量")
    lines.append("  • 英维克: 谷歌TPU液冷订单进展")
    lines.append("  • 比亚迪: 3月销量数据")
    lines.append("  • 洛阳钼业: 铜/钴价格走势")
    lines.append("")
    
    # 地缘政治分析
    lines.append("🌍 地缘政治影响:")
    for event, config in GEOPOLITICS.items():
        lines.append(f"  【{event}】状态: {config['status']}")
        lines.append(f"    石油影响: {config['impact_analysis']['石油']['direction']} - {config['impact_analysis']['石油']['reason']}")
        lines.append(f"    对持仓影响:")
        for code, impact in config['affected_stocks'].items():
            stock_name = STOCK_KEYWORDS.get(code, {}).get('name', code)
            lines.append(f"      • {stock_name}: {impact}")
        lines.append(f"    关注: {', '.join(config['watch_points'])}")
    
    return "\n".join(lines)

def get_stock_specific_news(stock_code):
    """获取单只股票的相关新闻（预留接口）"""
    config = STOCK_KEYWORDS.get(stock_code, {})
    return {
        'name': config.get('name', ''),
        'theme': config.get('theme', ''),
        'keywords': config.get('keywords', []),
        'peers': config.get('peers', []),
        'recent_news': [],  # 可通过web_search填充
    }

if __name__ == "__main__":
    # 测试
    test_data = [
        {'code': '300308', 'name': '中际旭创', 'change': -2.26},
        {'code': '002837', 'name': '英维克', 'change': -3.04},
        {'code': '002594', 'name': '比亚迪', 'change': -3.25},
        {'code': '601698', 'name': '中国卫通', 'change': 0.34},
    ]
    
    print(generate_news_section(test_data))