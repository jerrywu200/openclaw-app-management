"""
交易日志分析工具
用于分析交易记录，计算胜率、盈亏比等指标
"""

import pandas as pd
import os
from datetime import datetime

TRADE_LOG_PATH = '/Users/jw/.openclaw/workspace/trade_log.csv'

def load_trade_log():
    """加载交易日志"""
    if not os.path.exists(TRADE_LOG_PATH):
        print("交易日志文件不存在，请先创建")
        return None
    
    df = pd.read_csv(TRADE_LOG_PATH)
    return df

def analyze_trades():
    """分析交易记录"""
    df = load_trade_log()
    if df is None or len(df) == 0:
        print("暂无交易记录")
        return
    
    print("=" * 70)
    print("📊 交易日志分析")
    print("=" * 70)
    
    # 基本统计
    print(f"\n【基本统计】")
    print(f"交易次数: {len(df)}笔")
    print(f"买入次数: {len(df[df['操作'] == '买入'])}笔")
    print(f"卖出次数: {len(df[df['操作'] == '卖出'])}笔")
    
    # 资金统计
    buy_amount = df[df['操作'] == '买入']['金额'].sum()
    sell_amount = df[df['操作'] == '卖出']['金额'].sum()
    total_fee = df['手续费'].sum()
    
    print(f"\n【资金统计】")
    print(f"买入金额: {buy_amount:,.0f}元")
    print(f"卖出金额: {sell_amount:,.0f}元")
    print(f"手续费: {total_fee:,.0f}元")
    print(f"净流入: {sell_amount - buy_amount - total_fee:,.0f}元")
    
    # 策略分析
    print(f"\n【策略分布】")
    strategy_counts = df.groupby('策略').size()
    for strategy, count in strategy_counts.items():
        print(f"  {strategy}: {count}笔")
    
    # 情绪分析
    print(f"\n【情绪评分】")
    avg_emotion = df['情绪评分'].mean()
    print(f"  平均情绪评分: {avg_emotion:.1f}分")
    
    # 各股票交易统计
    print(f"\n【各股票交易】")
    stock_summary = df.groupby('股票名称').agg({
        '操作': 'count',
        '金额': 'sum'
    })
    for stock, row in stock_summary.iterrows():
        print(f"  {stock}: {row['操作']}笔, {row['金额']:,.0f}元")

def add_trade(date, code, name, action, price, shares, reason, strategy, emotion):
    """添加交易记录"""
    amount = price * shares
    fee = max(amount * 0.0003, 5)  # 佣金最低5元
    if action == '卖出':
        fee += amount * 0.001  # 印花税
    
    new_trade = pd.DataFrame([{
        '日期': date,
        '股票代码': code,
        '股票名称': name,
        '操作': action,
        '价格': price,
        '数量': shares,
        '金额': amount,
        '手续费': fee,
        '原因': reason,
        '策略': strategy,
        '情绪评分': emotion
    }])
    
    if os.path.exists(TRADE_LOG_PATH):
        df = pd.read_csv(TRADE_LOG_PATH)
        df = pd.concat([df, new_trade], ignore_index=True)
    else:
        df = new_trade
    
    df.to_csv(TRADE_LOG_PATH, index=False)
    print(f"✅ 已添加交易记录: {name} {action} {shares}股 @{price}元")

def show_recent_trades(n=10):
    """显示最近N笔交易"""
    df = load_trade_log()
    if df is None:
        return
    
    print("=" * 70)
    print(f"📋 最近{n}笔交易")
    print("=" * 70)
    
    recent = df.tail(n)
    for _, row in recent.iterrows():
        action_icon = "🟢" if row['操作'] == '买入' else "🔴"
        print(f"{row['日期']} {action_icon} {row['股票名称']} {row['操作']} {row['数量']}股 @{row['价格']:.2f}元 = {row['金额']:,.0f}元")
        print(f"   原因: {row['原因']} | 情绪: {row['情绪评分']}分")
        print()

if __name__ == "__main__":
    print("交易日志分析工具")
    print("\n用法:")
    print("1. analyze_trades() - 分析所有交易")
    print("2. add_trade(date, code, name, action, price, shares, reason, strategy, emotion) - 添加交易")
    print("3. show_recent_trades(n) - 显示最近N笔交易")
    print("\n示例:")
    print("add_trade('2026-03-26', '601698', '中国卫通', '卖出', 32.07, 600, '止损离场', '风控止损', 3)")