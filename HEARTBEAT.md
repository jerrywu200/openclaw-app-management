# HEARTBEAT.md

# 每日自动检查项（心跳触发时执行）

---

## 🔔 持续跟踪检查（V3.5新增）

### 每次心跳执行
检查持仓股票的评分变化和预警：
```bash
python3 /Users/jw/.openclaw/workspace/tracking_monitor.py
```

### 预警处理
- 🔴 critical级别 → 立即通知用户
- 🟡 warning级别 → 记录并汇总通知
- 🟢 info级别 → 记录，每日汇总

---

## 📊 组合管理检查（最高优先级）

### 每日检查
1. **更新持仓价格**：
   ```bash
   cd /Users/jw/.openclaw/workspace
   python3 portfolio/portfolio_manager.py --action update_prices
   ```

2. **检查止损触发**：
   ```bash
   python3 portfolio/portfolio_manager.py --action check_stop
   ```

3. **检查仓位限制**：
   ```bash
   python3 portfolio/portfolio_manager.py --action check_limits
   ```

### 如有异常
- 🔴 止损触发 → 立即通知用户
- 🔴 仓位超限 → 生成调仓建议
- 🟢 目标价到达 → 通知用户考虑止盈

---

## 🔔 每日复盘（交易日 16:00）

1. 运行每日报告：
   ```bash
   python3 /Users/jw/.openclaw/workspace/daily_review_tool.py --report
   ```
2. 发送报告给用户

---

## 📊 价格预警（交易日 15:30）

1. 运行预警检查：
   ```bash
   python3 /Users/jw/.openclaw/workspace/price_monitor.py --check
   ```
2. 如有预警触发，通知用户

---

## 📝 其他检查

- 交易记录更新提醒
- 重要新闻关注
- 目标进度追踪

---

## ⏰ 定时任务（Cron）

| 任务 | 时间 | Job ID | 说明 |
|------|------|--------|------|
| 周复盘 | 每周六 12:00 | `0c5bfc50` | 自动运行周复盘脚本 |

---

## 📋 心跳检查状态追踪

记录最近检查时间到 `memory/heartbeat-state.json`：

```json
{
  "lastChecks": {
    "portfolio_prices": "2026-03-28T21:48:00",
    "stop_loss": "2026-03-28T21:48:00",
    "position_limits": "2026-03-28T21:48:00"
  }
}
```

---

# 注意

- **交易时间**：执行所有检查
- **非交易时间**：仅执行组合管理检查，其他回复 HEARTBEAT_OK
- **发现异常**：立即通知用户，不等待报告