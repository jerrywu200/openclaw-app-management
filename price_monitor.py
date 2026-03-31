"""
价格预警监控工具
检查持仓股票是否触及预警价位，并发送提醒
"""

import sys
sys.path.append('/Users/jw/.openclaw/workspace')
from stock_db_tool import *
import json
from datetime import datetime

# 预警配置
ALERTS = {
    '止损预警': [
        {'code': '300308', 'name': '中际旭创', 'price': 500.00, 'type': 'down'},
        {'code': '605305', 'name': '中际联合', 'price': 32.00, 'type': 'down'},
        {'code': '002837', 'name': '英维克', 'price': 85.00, 'type': 'down'},
        {'code': '002594', 'name': '比亚迪', 'price': 90.00, 'type': 'down'},
        {'code': '603993', 'name': '洛阳钼业', 'price': 13.00, 'type': 'down'},
        {'code': '688390', 'name': '固德威', 'price': 70.00, 'type': 'down'},
        {'code': '600183', 'name': '生益科技', 'price': 45.00, 'type': 'down'},
    ],
    '加仓机会': [
        {'code': '605305', 'name': '中际联合', 'price': 38.00, 'type': 'down'},
        {'code': '603993', 'name': '洛阳钼业', 'price': 16.00, 'type': 'down'},
        {'code': '600183', 'name': '生益科技', 'price': 52.00, 'type': 'down'},
    ],
    '卖出机会': [
        {'code': '601698', 'name': '中国卫通', 'price': 35.00, 'type': 'up'},
        {'code': '002837', 'name': '英维克', 'price': 110.00, 'type': 'up'},
    ],
    '止盈提醒': [
        {'code': '300308', 'name': '中际旭创', 'price': 660.00, 'type': 'up'},
        {'code': '605305', 'name': '中际联合', 'price': 50.00, 'type': 'up'},
    ],
}

def check_alerts():
    """检查所有预警"""
    triggered = []
    
    for alert_type, alerts in ALERTS.items():
        for alert in alerts:
            code = alert['code']
            name = alert['name']
            target_price = alert['price']
            alert_direction = alert['type']
            
            # 获取当前价格
            kline = get_stock_kline(code, limit=1)
            if len(kline) == 0:
                continue
            
            current_price = kline.iloc[-1]['close_price']
            
            # 检查是否触发
            triggered_flag = False
            if alert_direction == 'down' and current_price <= target_price:
                triggered_flag = True
                direction = '跌破'
            elif alert_direction == 'up' and current_price >= target_price:
                triggered_flag = True
                direction = '突破'
            
            if triggered_flag:
                triggered.append({
                    'type': alert_type,
                    'code': code,
                    'name': name,
                    'current_price': current_price,
                    'target_price': target_price,
                    'direction': direction,
                    'change_pct': (current_price - target_price) / target_price * 100,
                })
    
    return triggered

def format_alert_message(triggered):
    """格式化预警消息"""
    if not triggered:
        return None
    
    msg = f"📊 价格预警 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
    msg += "=" * 40 + "\n\n"
    
    # 按类型分组
    by_type = {}
    for alert in triggered:
        t = alert['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(alert)
    
    for alert_type, alerts in by_type.items():
        msg += f"【{alert_type}】\n"
        for a in alerts:
            msg += f"  🔔 {a['name']}({a['code']})\n"
            msg += f"     现价: {a['current_price']:.2f}元\n"
            msg += f"     已{a['direction']}预警价: {a['target_price']:.2f}元\n"
            msg += f"     偏离: {a['change_pct']:+.1f}%\n\n"
    
    return msg

def get_portfolio_summary():
    """获取持仓摘要"""
    positions = [
        ('300308', '中际旭创', 600),
        ('605305', '中际联合', 6500),
        ('002837', '英维克', 2200),
        ('002594', '比亚迪', 2000),
        ('603993', '洛阳钼业', 8500),
        ('688390', '固德威', 492),
        ('601698', '中国卫通', 600),
        ('600183', '生益科技', 300),
    ]
    
    total_value = 0
    summary = []
    
    for code, name, shares in positions:
        kline = get_stock_kline(code, limit=1)
        if len(kline) > 0:
            price = kline.iloc[-1]['close_price']
            value = price * shares
            total_value += value
            
            # 获取涨跌幅
            change = kline.iloc[-1]['change_percent']
            
            summary.append({
                'code': code,
                'name': name,
                'shares': shares,
                'price': price,
                'value': value,
                'change': change,
            })
    
    return summary, total_value

def daily_report():
    """生成每日报告"""
    summary, total_value = get_portfolio_summary()
    
    msg = f"📊 每日持仓报告 ({datetime.now().strftime('%Y-%m-%d')})\n"
    msg += "=" * 50 + "\n\n"
    
    msg += "【持仓概览】\n"
    for s in summary:
        change_str = f"+{s['change']:.2f}%" if s['change'] > 0 else f"{s['change']:.2f}%"
        msg += f"  {s['name']}: {s['price']:.2f}元 ({change_str}) | 市值: {s['value']:,.0f}元\n"
    
    msg += f"\n股票市值: {total_value:,.0f}元\n"
    msg += f"现金: 498,655元\n"
    msg += f"总资产: {total_value + 498655:,.0f}元\n"
    
    # 检查预警
    triggered = check_alerts()
    if triggered:
        msg += "\n" + "=" * 50 + "\n"
        msg += "⚠️ 今日预警\n"
        for a in triggered:
            msg += f"  🔔 {a['name']}: {a['direction']}{a['target_price']:.2f}元\n"
    else:
        msg += "\n✅ 今日无预警触发\n"
    
    return msg

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='检查预警')
    parser.add_argument('--report', action='store_true', help='生成每日报告')
    args = parser.parse_args()
    
    if args.check:
        triggered = check_alerts()
        if triggered:
            msg = format_alert_message(triggered)
            print(msg)
        else:
            print("✅ 当前无预警触发")
    
    if args.report:
        msg = daily_report()
        print(msg)
    
    if not args.check and not args.report:
        # 默认：检查预警 + 生成报告
        print("检查预警...")
        triggered = check_alerts()
        if triggered:
            msg = format_alert_message(triggered)
            print(msg)
        else:
            print("✅ 当前无预警触发")
        
        print("\n" + "=" * 50 + "\n")
        
        print("生成每日报告...")
        msg = daily_report()
        print(msg)