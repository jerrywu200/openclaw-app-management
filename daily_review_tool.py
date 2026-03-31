"""
每日复盘报告生成器
自动生成持仓报告、预警检查、操作建议
"""

import sys
sys.path.append('/Users/jw/.openclaw/workspace')
from stock_db_tool import *
from news_analyzer import generate_news_section
from datetime import datetime, timedelta
import json

# 持仓基线
POSITIONS = [
    {'code': '300308', 'name': '中际旭创', 'shares': 600, 'cost': 695.89},
    {'code': '605305', 'name': '中际联合', 'shares': 6500, 'cost': 40.80},
    {'code': '002837', 'name': '英维克', 'shares': 2200, 'cost': 110.63},
    {'code': '002594', 'name': '比亚迪', 'shares': 2000, 'cost': 104.02},
    {'code': '603993', 'name': '洛阳钼业', 'shares': 8500, 'cost': 23.28},
    {'code': '688390', 'name': '固德威', 'shares': 492, 'cost': 161.22},
    {'code': '601698', 'name': '中国卫通', 'shares': 600, 'cost': 119.99},
    {'code': '600183', 'name': '生益科技', 'shares': 300, 'cost': 143.73},
]

CASH = 498655
BASELINE_ASSETS = 1775134
TARGET_ASSETS = 2307674
TARGET_DATE = '2026-06-30'
BASELINE_DATE = '2026-03-26'

# 预警配置
STOP_LOSS = {
    '300308': 500, '605305': 32, '002837': 85, '002594': 90,
    '603993': 13, '688390': 70, '600183': 45,
}
BUY_ZONE = {
    '605305': [38, 36], '603993': [16], '600183': [52, 50],
}
SELL_ZONE = {
    '601698': 35, '002837': [110, 120],
}
TARGET_PRICE = {
    '300308': 660, '605305': 50, '603993': 25,
}

def get_current_prices():
    """获取当前价格"""
    prices = {}
    for p in POSITIONS:
        kline = get_stock_kline(p['code'], limit=1)
        if len(kline) > 0:
            prices[p['code']] = {
                'price': kline.iloc[-1]['close_price'],
                'change': kline.iloc[-1]['change_percent'],
            }
    return prices

def calculate_portfolio(prices):
    """计算持仓"""
    total_cost = 0
    total_value = 0
    details = []
    
    for p in POSITIONS:
        code = p['code']
        cost = p['cost'] * p['shares']
        value = prices[code]['price'] * p['shares'] if code in prices else 0
        profit = value - cost
        profit_pct = (prices[code]['price'] - p['cost']) / p['cost'] * 100 if code in prices else 0
        
        total_cost += cost
        total_value += value
        
        details.append({
            'code': code,
            'name': p['name'],
            'shares': p['shares'],
            'cost_price': p['cost'],
            'current_price': prices[code]['price'] if code in prices else 0,
            'change': prices[code]['change'] if code in prices else 0,
            'cost_value': cost,
            'current_value': value,
            'profit': profit,
            'profit_pct': profit_pct,
        })
    
    return details, total_cost, total_value

def check_alerts(prices):
    """检查预警"""
    alerts = {'stop_loss': [], 'buy_zone': [], 'sell_zone': [], 'target': []}
    
    for code, price_data in prices.items():
        price = price_data['price']
        
        # 止损检查
        if code in STOP_LOSS and price <= STOP_LOSS[code]:
            alerts['stop_loss'].append({
                'code': code, 'price': price, 'target': STOP_LOSS[code]
            })
        
        # 加仓检查
        if code in BUY_ZONE:
            for target in BUY_ZONE[code]:
                if price <= target * 1.05:  # 接近加仓位5%内
                    alerts['buy_zone'].append({
                        'code': code, 'price': price, 'target': target
                    })
        
        # 卖出检查
        if code in SELL_ZONE:
            targets = SELL_ZONE[code] if isinstance(SELL_ZONE[code], list) else [SELL_ZONE[code]]
            for target in targets:
                if price >= target * 0.95:  # 接近卖出位5%内
                    alerts['sell_zone'].append({
                        'code': code, 'price': price, 'target': target
                    })
        
        # 目标价检查
        if code in TARGET_PRICE and price >= TARGET_PRICE[code] * 0.9:
            alerts['target'].append({
                'code': code, 'price': price, 'target': TARGET_PRICE[code]
            })
    
    return alerts

def get_stock_name(code):
    """获取股票名称"""
    for p in POSITIONS:
        if p['code'] == code:
            return p['name']
    return code

def generate_daily_report():
    """生成每日报告"""
    now = datetime.now()
    prices = get_current_prices()
    details, total_cost, total_value = calculate_portfolio(prices)
    alerts = check_alerts(prices)
    
    total_assets = total_value + CASH
    daily_change = total_assets - BASELINE_ASSETS
    daily_pct = daily_change / BASELINE_ASSETS * 100
    
    # 计算剩余天数
    target_date = datetime.strptime(TARGET_DATE, '%Y-%m-%d')
    remaining_days = (target_date - now).days
    required_daily_return = (TARGET_ASSETS / total_assets - 1) / remaining_days * 100 if remaining_days > 0 else 0
    
    report = []
    report.append(f"📊 每日持仓报告 ({now.strftime('%Y-%m-%d')})")
    report.append("━" * 50)
    report.append("")
    
    # 今日表现
    report.append("【今日表现】")
    up_stocks = [d for d in details if d['change'] > 0]
    down_stocks = [d for d in details if d['change'] < 0]
    
    for d in sorted(details, key=lambda x: x['change'], reverse=True):
        icon = "✅" if d['change'] > 0 else "🔴" if d['change'] < 0 else "➖"
        report.append(f"  {icon} {d['name']}: {d['current_price']:.2f}元 ({d['change']:+.2f}%)")
    report.append("")
    
    # 持仓变化
    report.append("【持仓概况】")
    report.append(f"  股票市值: {total_value:,.0f}元")
    report.append(f"  现金: {CASH:,.0f}元")
    report.append(f"  总资产: {total_assets:,.0f}元")
    report.append("")
    
    # 目标进度
    report.append("【目标进度】")
    progress = (total_assets - BASELINE_ASSETS) / (TARGET_ASSETS - BASELINE_ASSETS) * 100
    report.append(f"  起点: {BASELINE_ASSETS:,}元")
    report.append(f"  当前: {total_assets:,.0f}元 ({daily_pct:+.2f}%)")
    report.append(f"  目标: {TARGET_ASSETS:,}元")
    report.append(f"  进度: {progress:.1f}% | 剩余{remaining_days}天")
    report.append("")
    
    # 预警状态
    report.append("【预警状态】")
    if any(alerts.values()):
        if alerts['stop_loss']:
            report.append("  🔴 止损触发:")
            for a in alerts['stop_loss']:
                report.append(f"     {get_stock_name(a['code'])}: {a['price']:.2f}元 < {a['target']:.2f}元")
        if alerts['buy_zone']:
            report.append("  🟢 接近加仓位:")
            for a in alerts['buy_zone']:
                report.append(f"     {get_stock_name(a['code'])}: {a['price']:.2f}元 → 加仓位{a['target']:.2f}元")
        if alerts['sell_zone']:
            report.append("  🔔 接近卖出位:")
            for a in alerts['sell_zone']:
                report.append(f"     {get_stock_name(a['code'])}: {a['price']:.2f}元 → 卖出{a['target']:.2f}元")
    else:
        report.append("  ✅ 今日无预警触发")
    report.append("")
    
    # 操作建议
    report.append("【操作建议】")
    suggestions = []
    
    # 中国卫通卖出
    if '601698' in prices:
        price = prices['601698']['price']
        if price < 40:
            suggestions.append(f"  🔴 中国卫通({price:.2f}元): 建议卖出止损")
    
    # 加仓建议
    for code in ['605305', '603993', '600183']:
        if code in prices:
            price = prices[code]['price']
            if code in BUY_ZONE and price <= BUY_ZONE[code][0] * 1.05:
                suggestions.append(f"  🟢 {get_stock_name(code)}({price:.2f}元): 接近加仓位")
    
    if suggestions:
        report.extend(suggestions)
    else:
        report.append("  📌 暂无操作建议")
    report.append("")
    
    # 消息面分析
    stock_data_for_news = [
        {'code': d['code'], 'name': d['name'], 'change': d['change']}
        for d in details
    ]
    news_section = generate_news_section(stock_data_for_news)
    report.append(news_section)
    
    return "\n".join(report)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', action='store_true', help='生成每日报告')
    parser.add_argument('--alerts', action='store_true', help='仅检查预警')
    args = parser.parse_args()
    
    if args.report or not args.alerts:
        report = generate_daily_report()
        print(report)
    
    if args.alerts:
        prices = get_current_prices()
        alerts = check_alerts(prices)
        if any(alerts.values()):
            print("\n⚠️ 预警提醒:")
            for alert_type, items in alerts.items():
                if items:
                    for a in items:
                        print(f"  {alert_type}: {get_stock_name(a['code'])} {a['price']:.2f}元")
        else:
            print("✅ 当前无预警")