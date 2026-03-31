#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析同步工具 - 将个股分析结果同步到组合管理系统

功能：
1. 从缓存读取分析结果
2. 更新 positions.csv
3. 更新评分、止损位、目标价
4. 生成同步报告

使用方法：
    python3 analysis_sync.py --code 300308 --sync-all
    python3 analysis_sync.py --code 300308 --sync-score
    python3 analysis_sync.py --code 300308 --sync-stop
    python3 analysis_sync.py --code 300308 --sync-target
"""

import argparse
import json
import pandas as pd
import os
from datetime import datetime

# 路径配置
CACHE_DIR = '/Users/jw/.openclaw/workspace/analysis_cache'
POSITIONS_CSV = '/Users/jw/.openclaw/workspace/portfolio/positions.csv'


def load_cache(stock_code):
    """加载缓存数据"""
    # 查找缓存目录
    cache_subdirs = [d for d in os.listdir(CACHE_DIR) 
                     if os.path.isdir(os.path.join(CACHE_DIR, d)) 
                     and d.startswith(stock_code)]
    
    if not cache_subdirs:
        print(f"❌ 未找到 {stock_code} 的缓存")
        return None
    
    cache_path = os.path.join(CACHE_DIR, cache_subdirs[0])
    
    # 加载缓存文件
    risk_file = os.path.join(cache_path, 'risk_basic.json')
    metrics_file = os.path.join(cache_path, 'key_metrics.json')
    
    result = {}
    
    if os.path.exists(risk_file):
        with open(risk_file, 'r', encoding='utf-8') as f:
            result['risk'] = json.load(f)
    
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r', encoding='utf-8') as f:
            result['metrics'] = json.load(f)
    
    return result


def check_in_positions(stock_code):
    """检查股票是否在持仓中"""
    if not os.path.exists(POSITIONS_CSV):
        return False
    
    df = pd.read_csv(POSITIONS_CSV, dtype={'股票代码': str})
    return stock_code in df['股票代码'].values


def update_score(stock_code, score, rating):
    """更新评分"""
    # 先检查是否在持仓中
    if not check_in_positions(stock_code):
        print(f"ℹ️ {stock_code} 不在持仓中，跳过评分同步")
        return None
    
    df = pd.read_csv(POSITIONS_CSV, dtype={'股票代码': str})
    
    # 确保"最后分析日期"列为字符串类型
    if '最后分析日期' in df.columns:
        df['最后分析日期'] = df['最后分析日期'].astype(str)
    
    idx = df[df['股票代码'] == stock_code].index
    if len(idx) == 0:
        print(f"❌ {stock_code} 不在持仓中")
        return False
    
    idx = idx[0]
    old_score = df.loc[idx, '评分']
    df.loc[idx, '评分'] = score
    df.loc[idx, '建议'] = rating
    df.loc[idx, '更新日期'] = datetime.now().strftime('%Y-%m-%d')
    
    # 更新最后分析日期
    if '最后分析日期' in df.columns:
        df.loc[idx, '最后分析日期'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    df.to_csv(POSITIONS_CSV, index=False, encoding='utf-8')
    print(f"✅ {stock_code} 评分已更新: {old_score} → {score}")
    return True


def update_stop(stock_code, stop_price, stop_percent):
    """更新止损位"""
    # 先检查是否在持仓中
    if not check_in_positions(stock_code):
        print(f"ℹ️ {stock_code} 不在持仓中，跳过止损位同步")
        return None
    
    df = pd.read_csv(POSITIONS_CSV, dtype={'股票代码': str})
    
    # 确保"最后分析日期"列为字符串类型
    if '最后分析日期' in df.columns:
        df['最后分析日期'] = df['最后分析日期'].astype(str)
    
    idx = df[df['股票代码'] == stock_code].index
    if len(idx) == 0:
        print(f"❌ {stock_code} 不在持仓中")
        return False
    
    idx = idx[0]
    old_stop = df.loc[idx, '止损价']
    df.loc[idx, '止损价'] = stop_price
    df.loc[idx, '止损比例'] = stop_percent
    df.loc[idx, '更新日期'] = datetime.now().strftime('%Y-%m-%d')
    
    # 更新最后分析日期
    if '最后分析日期' in df.columns:
        df.loc[idx, '最后分析日期'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    df.to_csv(POSITIONS_CSV, index=False, encoding='utf-8')
    print(f"✅ {stock_code} 止损位已更新: {old_stop} → {stop_price} ({stop_percent}%)")
    return True


def update_target(stock_code, target_low, target_high):
    """更新目标价"""
    # 先检查是否在持仓中
    if not check_in_positions(stock_code):
        print(f"ℹ️ {stock_code} 不在持仓中，跳过目标价同步")
        return None
    
    df = pd.read_csv(POSITIONS_CSV, dtype={'股票代码': str})
    
    # 确保"最后分析日期"列为字符串类型
    if '最后分析日期' in df.columns:
        df['最后分析日期'] = df['最后分析日期'].astype(str)
    
    idx = df[df['股票代码'] == stock_code].index
    if len(idx) == 0:
        print(f"❌ {stock_code} 不在持仓中")
        return False
    
    idx = idx[0]
    target_str = f"{target_low}-{target_high}"
    df.loc[idx, '目标价'] = target_str
    df.loc[idx, '更新日期'] = datetime.now().strftime('%Y-%m-%d')
    
    # 更新最后分析日期
    if '最后分析日期' in df.columns:
        df.loc[idx, '最后分析日期'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    df.to_csv(POSITIONS_CSV, index=False, encoding='utf-8')
    print(f"✅ {stock_code} 目标价已更新: {target_str}")
    return True


def sync_all(stock_code):
    """同步所有数据"""
    # 先检查是否在持仓中
    if not check_in_positions(stock_code):
        print(f"\n{'='*60}")
        print(f"ℹ️ {stock_code} 不在持仓中")
        print(f"{'='*60}")
        print(f"\n仅保存分析报告和缓存，不执行同步操作")
        print(f"如需买入，请先添加到持仓后重新同步")
        return None
    
    cache = load_cache(stock_code)
    
    if not cache:
        print(f"❌ 无法加载缓存")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 同步分析结果到组合管理系统")
    print(f"{'='*60}\n")
    
    success_count = 0
    
    # 同步评分
    if 'metrics' in cache:
        rating_data = cache['metrics'].get('investment_rating', {})
        score = rating_data.get('score')
        rating = rating_data.get('rating')
        
        if score and rating:
            if update_score(stock_code, score, rating):
                success_count += 1
    
    # 同步止损位
    if 'risk' in cache:
        atr_data = cache['risk'].get('atr_stop_loss', {})
        stop_price = atr_data.get('stop_loss_price')
        stop_percent = atr_data.get('stop_loss_percent')
        
        if stop_price:
            if update_stop(stock_code, stop_price, stop_percent):
                success_count += 1
    
    # 同步目标价
    if 'metrics' in cache:
        rating_data = cache['metrics'].get('investment_rating', {})
        target_low = rating_data.get('target_price_low')
        target_high = rating_data.get('target_price_high')
        
        if target_low:
            if update_target(stock_code, target_low, target_high):
                success_count += 1
    
    print(f"\n✅ 同步完成: {success_count}/3 项更新成功")
    return success_count == 3


def get_position_status(stock_code):
    """获取股票持仓状态"""
    if check_in_positions(stock_code):
        df = pd.read_csv(POSITIONS_CSV, dtype={'股票代码': str})
        row = df[df['股票代码'] == stock_code].iloc[0]
        return {
            'in_position': True,
            'name': row['股票名称'],
            'shares': row['股数'],
            'cost': row['成本价'],
            'current': row['现价'],
            'profit_pct': row['盈亏%']
        }
    return {'in_position': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='分析同步工具')
    parser.add_argument('--code', type=str, required=True, help='股票代码')
    parser.add_argument('--sync-all', action='store_true', help='同步所有数据')
    parser.add_argument('--sync-score', action='store_true', help='仅同步评分')
    parser.add_argument('--sync-stop', action='store_true', help='仅同步止损位')
    parser.add_argument('--sync-target', action='store_true', help='仅同步目标价')
    parser.add_argument('--score', type=float, help='评分')
    parser.add_argument('--rating', type=str, help='评级')
    parser.add_argument('--stop', type=float, help='止损价')
    parser.add_argument('--stop-pct', type=float, help='止损比例')
    parser.add_argument('--target-low', type=float, help='目标价下限')
    parser.add_argument('--target-high', type=float, help='目标价上限')
    
    args = parser.parse_args()
    
    if args.sync_all:
        sync_all(args.code)
    elif args.sync_score and args.score:
        update_score(args.code, args.score, args.rating or '持有')
    elif args.sync_stop and args.stop:
        update_stop(args.code, args.stop, args.stop_pct)
    elif args.sync_target and args.target_low:
        update_target(args.code, args.target_low, args.target_high)
    else:
        print("请指定同步操作: --sync-all, --sync-score, --sync-stop, --sync-target")