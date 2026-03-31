"""
持续跟踪监控模块 V1.0
=====================

V3.5 Phase 5新增模块

核心功能：
1. record_score_history() - 记录评分历史
2. check_alerts() - 检测预警
3. monitor_key_metrics() - 监控关键指标
4. get_tracking_summary() - 获取跟踪摘要
5. heartbeat_tracking_check() - 心跳触发的跟踪检查

使用示例：
```python
from tracking_monitor import record_score_history, check_alerts

# 记录评分历史
result = record_score_history(stock_code, stock_name, analysis_result)

# 检测预警
alerts = check_alerts(stock_code, history, analysis_result, position_data)
```
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

sys.path.insert(0, '/Users/jw/.openclaw/workspace')

# ============================================================
# 常量定义
# ============================================================

TRACKING_DIR = "/Users/jw/.openclaw/workspace/tracking"
MAX_HISTORY_RECORDS = 50  # 最大历史记录数


# ============================================================
# 一、评分历史记录器
# ============================================================

def record_score_history(
    stock_code: str,
    stock_name: str,
    analysis_result: Dict,
    trigger: str = "manual"
) -> Dict:
    """
    记录评分历史
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        analysis_result: 分析结果
        trigger: 触发方式（manual/heartbeat/cron）
    
    Returns:
        dict: {
            'recorded': bool,
            'history_file': str,
            'changes': {...},
            'total_records': int
        }
    """
    # 创建tracking目录
    os.makedirs(TRACKING_DIR, exist_ok=True)
    
    # 标准化股票代码
    code = stock_code.split('.')[0] if '.' in stock_code else stock_code
    
    # 历史文件路径
    history_file = f"{TRACKING_DIR}/{code}_history.json"
    
    # 读取或创建历史数据
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = None
    else:
        history = None
    
    if history is None:
        history = {
            'stock_code': code,
            'stock_name': stock_name,
            'created_at': datetime.now().isoformat(),
            'score_history': [],
            'score_changes': [],
            'metric_history': []
        }
    
    # 创建新记录
    new_record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'comprehensive_score': analysis_result.get('comprehensive_score'),
        'rating': analysis_result.get('rating'),
        'rating_star': analysis_result.get('rating_star'),
        'risk_level': analysis_result.get('risk_level'),
        'position_limit': analysis_result.get('position_limit'),
        'trigger': trigger
    }
    
    # 提取维度评分
    dimensions = analysis_result.get('dimensions', {})
    if dimensions:
        new_record['dimensions'] = {
            'fundamental': dimensions.get('fundamental', {}).get('score'),
            'industry': dimensions.get('industry', {}).get('score'),
            'valuation': dimensions.get('valuation', {}).get('score'),
            'technical': dimensions.get('technical', {}).get('score'),
            'event': dimensions.get('event', {}).get('score'),
            'market': dimensions.get('market', {}).get('score')
        }
    
    # 提取置信度
    confidence = analysis_result.get('confidence') or analysis_result.get('dimensions', {}).get('fundamental', {}).get('confidence')
    if confidence:
        new_record['confidence'] = {
            'score': confidence.get('score') if isinstance(confidence, dict) else None,
            'level': confidence.get('level') if isinstance(confidence, dict) else None
        }
    
    # 计算变化
    changes = {}
    if history['score_history']:
        last_record = history['score_history'][-1]
        
        # 评分变化
        last_score = last_record.get('comprehensive_score')
        current_score = new_record.get('comprehensive_score')
        
        if last_score is not None and current_score is not None:
            score_change = current_score - last_score
            if abs(score_change) >= 0.1:
                changes['score_change'] = round(score_change, 2)
        
        # 评级变化
        last_rating = last_record.get('rating')
        current_rating = new_record.get('rating')
        if last_rating and current_rating and last_rating != current_rating:
            changes['rating_change'] = f"{last_rating} → {current_rating}"
        
        # 风险变化
        last_risk = last_record.get('risk_level')
        current_risk = new_record.get('risk_level')
        if last_risk and current_risk and last_risk != current_risk:
            changes['risk_change'] = f"{last_risk} → {current_risk}"
        
        # 记录变化
        if changes:
            history['score_changes'].append({
                'date': new_record['date'],
                'timestamp': new_record['timestamp'],
                **changes
            })
    
    # 添加记录
    history['score_history'].append(new_record)
    history['last_updated'] = datetime.now().isoformat()
    
    # 限制历史记录数量
    if len(history['score_history']) > MAX_HISTORY_RECORDS:
        history['score_history'] = history['score_history'][-MAX_HISTORY_RECORDS:]
    
    # 保存文件
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return {
        'recorded': True,
        'history_file': history_file,
        'changes': changes,
        'total_records': len(history['score_history'])
    }


# ============================================================
# 二、预警检测器
# ============================================================

def check_alerts(
    stock_code: str,
    analysis_result: Dict,
    position_data: Dict = None
) -> List[Dict]:
    """
    检测预警
    
    Args:
        stock_code: 股票代码
        analysis_result: 分析结果
        position_data: 持仓数据（止损位、目标价）
    
    Returns:
        List[Dict]: 预警列表
    """
    alerts = []
    code = stock_code.split('.')[0] if '.' in stock_code else stock_code
    
    # 读取历史数据
    history_file = f"{TRACKING_DIR}/{code}_history.json"
    
    if not os.path.exists(history_file):
        return alerts
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        return alerts
    
    if not history.get('score_history'):
        return alerts
    
    last_record = history['score_history'][-1]
    
    # 1. 评分下降预警
    last_score = last_record.get('comprehensive_score')
    current_score = analysis_result.get('comprehensive_score')
    
    if last_score is not None and current_score is not None:
        score_change = current_score - last_score
        
        if score_change <= -10:
            alerts.append({
                'alert_type': 'score_drop',
                'alert_level': 'warning',
                'message': f"评分下降{abs(score_change):.1f}分，从{last_score:.1f}降至{current_score:.1f}"
            })
        elif score_change <= -5:
            alerts.append({
                'alert_type': 'score_drop',
                'alert_level': 'info',
                'message': f"评分下降{abs(score_change):.1f}分，从{last_score:.1f}降至{current_score:.1f}"
            })
    
    # 2. 评级下调预警
    last_rating = last_record.get('rating')
    current_rating = analysis_result.get('rating')
    
    rating_order = ['强烈买入', '买入', '持有', '减持', '卖出']
    
    if last_rating and current_rating:
        if last_rating in rating_order and current_rating in rating_order:
            last_idx = rating_order.index(last_rating)
            current_idx = rating_order.index(current_rating)
            
            if current_idx > last_idx:
                alerts.append({
                    'alert_type': 'rating_downgrade',
                    'alert_level': 'warning',
                    'message': f"评级下调：{last_rating} → {current_rating}"
                })
    
    # 3. 风险上升预警
    last_risk = last_record.get('risk_level')
    current_risk = analysis_result.get('risk_level')
    
    risk_order = ['低风险', '中低风险', '中等风险', '中高风险', '高风险']
    
    if last_risk and current_risk:
        if last_risk in risk_order and current_risk in risk_order:
            last_idx = risk_order.index(last_risk)
            current_idx = risk_order.index(current_risk)
            
            if current_idx > last_idx:
                alerts.append({
                    'alert_type': 'risk_increase',
                    'alert_level': 'warning',
                    'message': f"风险上升：{last_risk} → {current_risk}"
                })
    
    # 4. 止损触发预警
    if position_data:
        stop_loss = position_data.get('stop_loss')
        current_price = position_data.get('current_price')
        
        if stop_loss and current_price:
            if current_price <= stop_loss:
                alerts.append({
                    'alert_type': 'stop_loss_trigger',
                    'alert_level': 'critical',
                    'message': f"🔴 止损触发：当前价{current_price:.2f} ≤ 止损位{stop_loss:.2f}"
                })
    
    # 5. 目标价到达提醒
    if position_data:
        target_high = position_data.get('target_high')
        current_price = position_data.get('current_price')
        
        if target_high and current_price:
            if current_price >= target_high:
                alerts.append({
                    'alert_type': 'target_reached',
                    'alert_level': 'info',
                    'message': f"🟢 目标价到达：当前价{current_price:.2f} ≥ 目标价{target_high:.2f}"
                })
    
    return alerts


# ============================================================
# 三、关键指标监控器
# ============================================================

def record_metric_history(
    stock_code: str,
    metrics: Dict
) -> Dict:
    """
    记录关键指标历史
    
    Args:
        stock_code: 股票代码
        metrics: 关键指标（ROE、毛利率等）
    
    Returns:
        dict: 记录结果
    """
    code = stock_code.split('.')[0] if '.' in stock_code else stock_code
    history_file = f"{TRACKING_DIR}/{code}_history.json"
    
    if not os.path.exists(history_file):
        return {'recorded': False, 'message': '历史文件不存在'}
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        return {'recorded': False, 'message': '读取历史失败'}
    
    # 添加指标记录
    metric_record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        **metrics
    }
    
    if 'metric_history' not in history:
        history['metric_history'] = []
    
    history['metric_history'].append(metric_record)
    
    # 限制记录数量
    if len(history['metric_history']) > MAX_HISTORY_RECORDS:
        history['metric_history'] = history['metric_history'][-MAX_HISTORY_RECORDS:]
    
    # 保存
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return {'recorded': True, 'total_records': len(history['metric_history'])}


def monitor_key_metrics(
    stock_code: str,
    current_metrics: Dict = None
) -> List[Dict]:
    """
    监控关键指标变化
    
    Args:
        stock_code: 股票代码
        current_metrics: 当前指标（可选，如提供则记录）
    
    Returns:
        List[Dict]: 指标变化预警
    """
    alerts = []
    code = stock_code.split('.')[0] if '.' in stock_code else stock_code
    history_file = f"{TRACKING_DIR}/{code}_history.json"
    
    if not os.path.exists(history_file):
        return alerts
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        return alerts
    
    metric_history = history.get('metric_history', [])
    
    if len(metric_history) < 2:
        return alerts
    
    # 1. ROE趋势监控
    roe_values = [m.get('roe') for m in metric_history[-3:] if m.get('roe') is not None]
    if len(roe_values) >= 2:
        if all(roe_values[i] > roe_values[i+1] for i in range(len(roe_values)-1)):
            alerts.append({
                'alert_type': 'roe_decline',
                'alert_level': 'warning',
                'message': f"ROE连续{len(roe_values)}期下降：{' → '.join([f'{v:.1f}%' for v in roe_values])}"
            })
    
    # 2. 毛利率趋势监控
    gm_values = [m.get('gross_margin') for m in metric_history[-3:] if m.get('gross_margin') is not None]
    if len(gm_values) >= 2:
        if all(gm_values[i] > gm_values[i+1] for i in range(len(gm_values)-1)):
            alerts.append({
                'alert_type': 'gross_margin_decline',
                'alert_level': 'warning',
                'message': f"毛利率连续{len(gm_values)}期下降"
            })
    
    # 3. 营收增长趋势监控
    rg_values = [m.get('revenue_growth') for m in metric_history[-3:] if m.get('revenue_growth') is not None]
    if len(rg_values) >= 2:
        if all(rg_values[i] > rg_values[i+1] for i in range(len(rg_values)-1)):
            alerts.append({
                'alert_type': 'revenue_growth_decline',
                'alert_level': 'info',
                'message': f"营收增速连续{len(rg_values)}期放缓"
            })
    
    return alerts


# ============================================================
# 四、跟踪摘要生成
# ============================================================

def get_tracking_summary(stock_code: str) -> Dict:
    """
    获取跟踪摘要
    
    Args:
        stock_code: 股票代码
    
    Returns:
        dict: 跟踪摘要
    """
    code = stock_code.split('.')[0] if '.' in stock_code else stock_code
    history_file = f"{TRACKING_DIR}/{code}_history.json"
    
    if not os.path.exists(history_file):
        return {
            'available': False,
            'message': '无历史数据'
        }
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        return {
            'available': False,
            'message': '读取历史失败'
        }
    
    score_history = history.get('score_history', [])
    score_changes = history.get('score_changes', [])
    
    if not score_history:
        return {
            'available': False,
            'message': '无评分记录'
        }
    
    # 最新记录
    latest = score_history[-1]
    
    # 评分统计
    scores = [r.get('comprehensive_score') for r in score_history if r.get('comprehensive_score') is not None]
    
    summary = {
        'available': True,
        'stock_code': code,
        'stock_name': history.get('stock_name'),
        'total_records': len(score_history),
        'first_record_date': score_history[0].get('date') if score_history else None,
        'last_record_date': latest.get('date'),
        'latest_score': latest.get('comprehensive_score'),
        'latest_rating': latest.get('rating'),
        'latest_risk_level': latest.get('risk_level'),
        'score_stats': {
            'max': max(scores) if scores else None,
            'min': min(scores) if scores else None,
            'avg': round(sum(scores) / len(scores), 2) if scores else None
        },
        'recent_changes': score_changes[-5:] if score_changes else []
    }
    
    return summary


# ============================================================
# 五、心跳触发的跟踪检查
# ============================================================

def heartbeat_tracking_check() -> Dict:
    """
    心跳触发的跟踪检查
    
    扫描所有持仓股票，检查评分变化和预警
    
    Returns:
        dict: 检查结果
    """
    import csv
    
    # 读取持仓
    positions_file = "/Users/jw/.openclaw/workspace/portfolio/positions.csv"
    
    if not os.path.exists(positions_file):
        return {
            'status': 'no_positions',
            'message': '持仓文件不存在'
        }
    
    alerts_summary = []
    positions = []
    
    try:
        with open(positions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            positions = list(reader)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'读取持仓失败: {str(e)}'
        }
    
    # 检查每个持仓
    for position in positions:
        # 使用中文列名（positions.csv使用中文）
        code = position.get('股票代码', '') or position.get('code', '')
        name = position.get('股票名称', '') or position.get('name', '')
        
        if not code:
            continue
        
        # 检查历史文件
        history_file = f"{TRACKING_DIR}/{code}_history.json"
        
        if not os.path.exists(history_file):
            continue
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            continue
        
        # 检查最近的评分变化
        score_changes = history.get('score_changes', [])
        
        for change in score_changes:
            change_date = change.get('date', '')
            
            # 检查是否是今天的记录
            today = datetime.now().strftime('%Y-%m-%d')
            
            if change_date == today:
                alerts_summary.append({
                    'stock_code': code,
                    'stock_name': history.get('stock_name', name),
                    'change': change
                })
    
    return {
        'status': 'checked',
        'check_time': datetime.now().isoformat(),
        'positions_count': len(positions),
        'alerts_count': len(alerts_summary),
        'alerts': alerts_summary
    }


# ============================================================
# 六、通知生成
# ============================================================

def generate_alert_notification(alerts: List[Dict], stock_name: str = "") -> str:
    """
    生成预警通知文本
    
    Args:
        alerts: 预警列表
        stock_name: 股票名称
    
    Returns:
        str: 通知文本
    """
    if not alerts:
        return ""
    
    # 分类预警
    critical = [a for a in alerts if a.get('alert_level') == 'critical']
    warning = [a for a in alerts if a.get('alert_level') == 'warning']
    info = [a for a in alerts if a.get('alert_level') == 'info']
    
    lines = []
    
    if stock_name:
        lines.append(f"## 📊 {stock_name} 监控预警\n")
    
    lines.append(f"**检查时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    if critical:
        lines.append("### 🔴 重要预警（需立即关注）\n")
        for alert in critical:
            lines.append(f"- {alert.get('message', '')}")
        lines.append("")
    
    if warning:
        lines.append("### 🟡 一般预警\n")
        for alert in warning:
            lines.append(f"- {alert.get('message', '')}")
        lines.append("")
    
    if info:
        lines.append("### 🟢 提醒\n")
        for alert in info:
            lines.append(f"- {alert.get('message', '')}")
        lines.append("")
    
    lines.append("---\n*持续跟踪机制自动生成*")
    
    return "\n".join(lines)


# ============================================================
# 七、使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("持续跟踪监控模块 V1.0 测试")
    print("=" * 60)
    
    # 测试心跳检查
    print("\n【心跳跟踪检查】")
    result = heartbeat_tracking_check()
    print(f"状态: {result.get('status')}")
    print(f"持仓数量: {result.get('positions_count')}")
    print(f"预警数量: {result.get('alerts_count')}")
    
    if result.get('alerts'):
        print("\n【预警详情】")
        for alert in result['alerts']:
            print(f"  {alert['stock_name']}: {alert['change']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)