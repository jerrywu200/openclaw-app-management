#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周复盘脚本 - 每周六12:00自动执行
对持仓股票进行系统性复盘分析
"""

import sys
sys.path.append('/Users/jw/.openclaw/workspace')

from stock_db_tool import *
import pandas as pd
from datetime import datetime, timedelta
import os

# 持仓股票列表
PORTFOLIO = [
    {'code': '300308', 'name': '中际旭创', 'shares': 600, 'cost': 695.89},
    {'code': '605305', 'name': '中际联合', 'shares': 6500, 'cost': 40.80},
    {'code': '002837', 'name': '英维克', 'shares': 2200, 'cost': 110.63},
    {'code': '002594', 'name': '比亚迪', 'shares': 2000, 'cost': 104.02},
    {'code': '603993', 'name': '洛阳钼业', 'shares': 8500, 'cost': 23.28},
    {'code': '688390', 'name': '固德威', 'shares': 492, 'cost': 161.22},
    {'code': '601698', 'name': '中国卫通', 'shares': 600, 'cost': 119.99},
    {'code': '600183', 'name': '生益科技', 'shares': 300, 'cost': 143.73},
]

def get_stock_data(code):
    """获取股票数据"""
    try:
        kline = get_stock_kline(code, limit=5)
        finance = get_stock_finance(code, limit=3)
        high_low = get_stock_highest_lowest_price(code)
        return kline, finance, high_low
    except Exception as e:
        print(f"  获取数据失败: {e}")
        return None, None, None

def analyze_technical(kline):
    """技术面分析"""
    if kline is None or len(kline) == 0:
        return None
    
    # 均线
    kline['MA5'] = kline['close_price'].rolling(5).mean()
    kline['MA10'] = kline['close_price'].rolling(10).mean()
    
    # 量比
    kline['vol_ma5'] = kline['trading_volume'].rolling(5).mean()
    kline['vol_ratio'] = kline['trading_volume'] / kline['vol_ma5']
    
    # KDJ
    low_n = kline['low_price'].rolling(9).min()
    high_n = kline['high_price'].rolling(9).max()
    rsv = (kline['close_price'] - low_n) / (high_n - low_n) * 100
    K = rsv.ewm(span=3, adjust=False).mean()
    D = K.ewm(span=3, adjust=False).mean()
    
    # RSI
    close = kline['close_price']
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'ma5': kline['MA5'].iloc[-1],
        'ma10': kline['MA10'].iloc[-1] if len(kline) >= 10 else None,
        'vol_ratio': kline['vol_ratio'].iloc[-1],
        'kdj_k': K.iloc[-1],
        'kdj_d': D.iloc[-1],
        'rsi': rsi.iloc[-1],
    }

def review_single_stock(stock):
    """复盘单只股票"""
    code = stock['code']
    name = stock['name']
    cost = stock['cost']
    shares = stock['shares']
    
    print(f"\n{'='*60}")
    print(f"【{name}({code})】持仓{shares}股 成本{cost:.2f}元")
    print('='*60)
    
    # 获取数据
    kline, finance, high_low = get_stock_data(code)
    
    if kline is None or len(kline) == 0:
        print("  数据获取失败，跳过")
        return None
    
    # 当前价格
    current_price = kline['close_price'].iloc[-1]
    change_1d = kline['change_percent'].iloc[-1]
    
    # 盈亏计算
    profit_pct = (current_price / cost - 1) * 100
    profit_amt = (current_price - cost) * shares
    
    print(f"\n【价格表现】")
    print(f"  当前价: {current_price:.2f}元 ({change_1d:+.2f}%)")
    print(f"  持仓盈亏: {profit_pct:+.2f}% ({profit_amt:+.2f}元)")
    
    # 周涨跌
    if len(kline) >= 5:
        week_change = (kline['close_price'].iloc[-1] / kline['close_price'].iloc[0] - 1) * 100
        print(f"  本周涨跌: {week_change:+.2f}%")
    
    # 历史分位
    if high_low is not None and len(high_low) > 0:
        highest = high_low['highest_price'].values[0]
        lowest = high_low['lowest_price'].values[0]
        position = (current_price - lowest) / (highest - lowest) * 100
        print(f"  历史分位: {position:.1f}% (最高{highest:.2f}/最低{lowest:.2f})")
    
    # 技术面分析
    print(f"\n【技术面】")
    tech = analyze_technical(kline)
    if tech:
        ma10_str = f"{tech['ma10']:.2f}" if tech['ma10'] is not None else 'N/A'
        print(f"  MA5: {tech['ma5']:.2f}  MA10: {ma10_str}")
        print(f"  量比: {tech['vol_ratio']:.2f}")
        print(f"  KDJ: K={tech['kdj_k']:.1f} D={tech['kdj_d']:.1f}")
        print(f"  RSI: {tech['rsi']:.1f}")
        
        # 信号判断
        signals = []
        if current_price > tech['ma5']:
            signals.append("站上MA5 ✅")
        else:
            signals.append("跌破MA5 ⚠️")
        
        if tech['rsi'] < 30:
            signals.append("RSI超卖 🟢")
        elif tech['rsi'] > 70:
            signals.append("RSI超买 🔴")
        
        if tech['kdj_k'] > tech['kdj_d'] and tech['kdj_k'] < 30:
            signals.append("KDJ低位金叉 🟢")
        elif tech['kdj_k'] < tech['kdj_d'] and tech['kdj_k'] > 80:
            signals.append("KDJ高位死叉 🔴")
        
        print(f"  信号: {' | '.join(signals) if signals else '中性'}")
    
    # 财务分析
    if finance is not None and len(finance) > 0:
        print(f"\n【财务面】")
        latest_fin = finance.iloc[0]
        print(f"  最新财报: {latest_fin['报告期']}")
        
        if pd.notna(latest_fin['归属净利润同比增长(%)']):
            profit_yoy = latest_fin['归属净利润同比增长(%)']
            print(f"  净利润同比: {profit_yoy:+.1f}%")
        
        if pd.notna(latest_fin['净资产收益率(加权)(%)']):
            roe = latest_fin['净资产收益率(加权)(%)']
            print(f"  ROE: {roe:.2f}%")
    
    # 操作建议
    print(f"\n【操作建议】")
    if profit_pct < -20:
        print(f"  ⚠️ 深度套牢，建议评估是否止损或加仓摊薄")
    elif profit_pct < -10:
        print(f"  ⚠️ 浅套，关注支撑位，考虑补仓")
    elif profit_pct > 20:
        print(f"  ✅ 盈利较好，可考虑分批止盈")
    else:
        print(f"  ⚪ 持有观望，关注关键位置")
    
    return {
        'code': code,
        'name': name,
        'price': current_price,
        'profit_pct': profit_pct,
        'profit_amt': profit_amt,
    }

def main():
    """主函数"""
    print("=" * 70)
    print(f"周复盘报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    results = []
    
    for stock in PORTFOLIO:
        result = review_single_stock(stock)
        if result:
            results.append(result)
    
    # 汇总
    print("\n" + "=" * 70)
    print("【持仓汇总】")
    print("=" * 70)
    
    total_profit = sum([r['profit_amt'] for r in results])
    total_market_value = sum([r['price'] * next(s['shares'] for s in PORTFOLIO if s['code'] == r['code']) for r in results])
    
    print(f"\n持仓股票数: {len(results)}只")
    print(f"持仓市值: {total_market_value:.2f}元")
    print(f"总盈亏: {total_profit:+.2f}元")
    
    # 盈亏排行
    print(f"\n盈亏排行:")
    sorted_results = sorted(results, key=lambda x: x['profit_pct'], reverse=True)
    for i, r in enumerate(sorted_results, 1):
        status = "✅" if r['profit_pct'] > 0 else "🔴"
        print(f"  {i}. {r['name']}: {r['profit_pct']:+.2f}% ({r['profit_amt']:+.2f}元) {status}")
    
    # 保存报告
    report_dir = '/Users/jw/.openclaw/workspace/learning/review/weekly'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f"{report_dir}/weekly_review_{datetime.now().strftime('%Y%m%d')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 周复盘报告 - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"## 持仓汇总\n\n")
        f.write(f"- 持仓股票数: {len(results)}只\n")
        f.write(f"- 持仓市值: {total_market_value:.2f}元\n")
        f.write(f"- 总盈亏: {total_profit:+.2f}元\n\n")
        f.write(f"## 个股明细\n\n")
        for r in sorted_results:
            f.write(f"- {r['name']}({r['code']}): {r['profit_pct']:+.2f}%\n")
    
    print(f"\n报告已保存: {report_file}")
    
    return results

if __name__ == '__main__':
    main()