# 分析框架整合指南

> 创建日期: 2026-03-28
> 目标: 建立个股分析、年报分析、风险分析的协作机制
> 核心理念: 避免重复分析，复用已有成果

---

## 一、分析缓存机制

### 1.1 缓存目录结构

```
/Users/jw/.openclaw/workspace/
├─ analysis_cache/                    # 分析缓存目录
│   ├─ 603993_CMOC/                   # 洛阳钼业
│   │   ├─ annual_2025.md             # 2025年年报分析报告
│   │   ├─ quarterly_2025Q3.md        # 2025年三季报分析报告
│   │   ├─ risk_basic.json            # 基本面风控评分（低频）
│   │   ├─ last_update.txt            # 最后更新时间
│   │   └─ key_metrics.json           # 关键指标快查
│   │
│   ├─ 002594_BYD/                    # 比亚迪
│   │   └─ ...
│   │
│   └─ ...
│
├─ reports/                           # 完整报告目录
│   ├─ BYD_2025_annual_report_analysis.md
│   └─ CMOC_2025_annual_report_analysis.md
│
├─ stock_analysis_framework.md        # 个股分析框架V3.1
├─ annual_report_analysis_framework.md # 年报分析框架V1.0
└─ risk_defense_framework.md          # 风险防御框架V2.0
```

### 1.2 缓存文件格式

**risk_basic.json（基本面风控评分）**：
```json
{
  "stock_code": "603993",
  "stock_name": "洛阳钼业",
  "update_date": "2026-03-28",
  "report_period": "2025年年报",
  "financial_risk": {
    "debt_ratio": 50.34,
    "current_ratio": 1.55,
    "fcf": 39.14,
    "net_cash_ratio": 1.02,
    "score": 15
  },
  "operating_risk": {
    "industry_cycle": "成长期",
    "market_share": "全球第一钴生产商",
    "customer_concentration": "低",
    "score": 12
  },
  "management_risk": {
    "strategy_execution": "优秀",
    "governance": "良好",
    "related_party": "正常",
    "score": 8
  },
  "basic_risk_score": 35,
  "risk_level": "低风险",
  "position_limit": 12
}
```

**key_metrics.json（关键指标快查）**：
```json
{
  "stock_code": "603993",
  "update_date": "2026-03-28",
  "report_period": "2025年年报",
  "metrics": {
    "revenue": "2066.84亿",
    "revenue_growth": "-2.98%",
    "net_profit": "203.39亿",
    "net_profit_growth": "+50.30%",
    "roe": "26.61%",
    "gross_margin": "23.93%",
    "net_margin": "11.63%",
    "debt_ratio": "50.34%",
    "pe_ttm": "18.5",
    "pb": "2.0",
    "peg": "0.92"
  },
  "highlights": [
    "净利润+50%，连续五年刷新历史佳绩",
    "ROE提升至26.61%",
    "FCF为正（+39亿）",
    "全球第一大钴生产商"
  ],
  "red_flags": [
    "存货周转天数增加19天"
  ]
}
```

**last_update.txt**：
```
annual_2025: 2026-03-28
quarterly_2025Q3: 2025-10-30
risk_basic: 2026-03-28
```

---

## 二、个股分析调用年报/季报结果的流程

### 2.1 标准调用流程

```
┌─────────────────────────────────────────────────────────────┐
│  个股分析流程（整合版）                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 0: 检查缓存                                           │
│    ├─ 检查 analysis_cache/{stock_code}/                    │
│    ├─ 判断缓存有效性：                                      │
│    │   ├─ 年报分析：有效期内（年报发布后1季度）             │
│    │   ├─ 季报分析：有效期内（季报发布后1个月）             │
│    │   └─ 风险评分：有效期内（财务数据未更新）              │
│    └─ 输出：缓存状态                                        │
│                                                             │
│  Step 1-6: 个股分析（标准流程）                              │
│    ├─ 基本信息：从key_metrics.json快速获取                 │
│    ├─ 财务分析：                                            │
│    │   ├─ 有年报缓存 → 引用年报分析Part A结论              │
│    │   └─ 无缓存 → 执行完整财务分析                        │
│    ├─ 行业研究：                                            │
│    │   ├─ 有年报缓存 → 引用年报分析Part B结论              │
│    │   └─ 无缓存 → 执行完整行业研究                        │
│    └─ 估值分析：                                            │
│        ├─ 有年报缓存 → 引用年报分析Part F结论              │
│        └─ 无缓存 → 执行完整估值分析                        │
│                                                             │
│  Step 7: 风险防御                                           │
│    ├─ 有缓存 → 使用risk_basic.json的评分                   │
│    │   └─ 仅更新技术面风险（市场+技术）                    │
│    └─ 无缓存 → 执行完整风险分析                            │
│                                                             │
│  Step 8: 投资建议                                           │
│    └─ 整合分析结论                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 个股分析报告模板（整合版）

```markdown
# [股票名称](代码) 分析报告

> 分析日期: YYYY-MM-DD
> 分析框架: V3.1（八步法 + 风险防御）
> 数据来源: stock_db / 年报分析缓存 / 季报分析缓存
> 📋 引用缓存：annual_2025.md（更新于2026-03-28）

---

## 快速摘要（来自年报/季报分析缓存）

> 📊 以下内容引用自年报分析报告

**核心财务表现**：
- 净利润：XX亿（同比+XX%） ✅ 来自年报分析
- ROE：XX%
- 毛利率：XX%

**年报分析核心结论**：
- 业务亮点：XXX ✅ 来自年报分析Part B
- 现金流评估：XXX ✅ 来自年报分析Part C
- 前瞻指引：XXX ✅ 来自年报分析Part D

**风险信号**：
- 🔴 XXX ✅ 来自年报分析Part E

> ⚠️ 如需完整年报分析，请查看：reports/XXX_annual_report_analysis.md

---

## 一、基本信息
- 股价、市值、行业
- 历史最高最低价、概念板块

## 二、量价分析
- K线统计、量价配合
- 资金流向、龙虎榜分析

## 三、财务分析（引用年报分析）

### 核心指标（引用年报分析Part A）
| 指标 | 2025年 | 2024年 | 变化 | 来源 |
|------|--------|--------|------|------|
| 营收 | XX亿 | XX亿 | XX% | 年报分析 |
| 净利润 | XX亿 | XX亿 | XX% | 年报分析 |
| ... | ... | ... | ... | ... |

### 详细分析
> 📋 详细财务分析请查看年报分析报告Part A

## 四、行业研究（引用年报分析）
> 📋 业务定性分析请查看年报分析报告Part B

## 五、估值分析（引用年报分析）
> 📋 估值逻辑链条请查看年报分析报告Part F

## 六、风险防御

### 基本面风控评分（引用年报分析+风险框架）
| 维度 | 评分 | 来源 |
|------|------|------|
| 财务风险 | XX/10 | 年报分析Part A+E |
| 经营风险 | XX/10 | 年报分析Part B |
| 管理层风险 | XX/10 | 年报分析Part B |
| **基本面总分** | **XX/30** | 年报分析缓存 |

### 交易面风控评分（实时计算）
| 维度 | 评分 | 说明 |
|------|------|------|
| 市场风险 | XX/10 | 估值分位、流动性 |
| 技术面风险 | XX/10 | 趋势、支撑压力 |

### 综合风险等级：XX

## 七、投资建议
...
```

---

## 三、缓存更新策略

### 3.1 触发更新的条件

| 缓存类型 | 有效期 | 触发更新条件 |
|----------|--------|--------------|
| 年报分析 | 1季度 | 新年报发布 |
| 季报分析 | 1个月 | 新季报发布 |
| 基本面风控 | 财务数据未更新 | 财务数据更新 |
| 关键指标 | 同上 | 同上 |

### 3.2 更新优先级

```
年报发布季（3-4月）：
├─ 优先级最高：年报分析框架V1.0
├─ 更新缓存：annual_YYYY.md
├─ 更新缓存：risk_basic.json
└─ 更新缓存：key_metrics.json

季报发布后：
├─ 优先级中：更新季报分析
├─ 更新缓存：quarterly_YYYYQX.md
└─ 检查是否需要更新risk_basic.json

日常个股分析：
├─ 优先级低：直接使用缓存
└─ 仅更新技术面风险评分
```

---

## 四、实操流程

### 4.1 年报发布后的完整流程

```
Day 1: 年报发布
├─ Step 1: 执行年报分析框架V1.0
├─ Step 2: 生成年报分析报告 → reports/XXX_annual_report_analysis.md
├─ Step 3: 提取关键结论 → analysis_cache/XXX/
│   ├─ risk_basic.json
│   ├─ key_metrics.json
│   └─ last_update.txt
└─ Step 4: 通知用户年报分析完成

Day 2+: 日常个股分析
├─ Step 1: 检查缓存（有效期检查）
├─ Step 2: 引用年报分析结论
├─ Step 3: 执行个股分析剩余步骤
│   ├─ 量价分析（实时）
│   ├─ 短线分析（实时）
│   └─ 交易面风控（实时）
└─ Step 4: 输出综合投资建议
```

### 4.2 非年报季的个股分析

```
个股分析请求
├─ 检查缓存
│   ├─ 有缓存且有效 → 引用缓存
│   └─ 无缓存或过期 → 执行完整分析
│
├─ 执行个股分析框架V3.1
│   ├─ 基本信息（实时获取）
│   ├─ 量价分析（实时获取）
│   ├─ 财务分析（引用缓存或实时计算）
│   ├─ 行业研究（引用缓存或实时分析）
│   ├─ 估值分析（实时计算）
│   ├─ 风险防御（引用缓存+实时计算）
│   └─ 投资建议（综合输出）
│
└─ 输出分析报告
```

---

## 五、缓存引用格式

### 5.1 在个股分析报告中引用

```markdown
<!-- 引用年报分析 -->
> 📋 财务分析详细内容来自年报分析报告：[2025年年报分析](../reports/XXX_2025_annual_report_analysis.md)

<!-- 引用关键指标 -->
> 💰 关键指标来自年报分析缓存：净利润203.39亿（+50.30%）

<!-- 引用风险评分 -->
> 🛡️ 基本面风控评分来自风险分析缓存：35分（低风险）
```

### 5.2 缓存时效性声明

```markdown
> ⚠️ 数据时效性说明
> - 年报分析更新于：2026-03-28
> - 财务数据截至：2025年12月31日
> - 技术面数据：实时获取
> - 如财务数据已更新，建议重新执行年报分析
```

---

## 六、自动化实现（伪代码）

```python
def analyze_stock(stock_code, force_refresh=False):
    """
    个股分析（整合缓存机制）
    """
    
    # Step 0: 检查缓存
    cache = check_cache(stock_code)
    
    if not force_refresh and cache.is_valid():
        # 使用缓存
        print(f"📋 使用缓存（更新于 {cache.last_update}）")
        annual_analysis = cache.get('annual')
        risk_basic = cache.get('risk_basic')
        key_metrics = cache.get('key_metrics')
    else:
        # 执行完整分析
        print("⏳ 执行完整分析...")
        annual_analysis = run_annual_analysis(stock_code)
        risk_basic = run_risk_analysis(stock_code)
        key_metrics = extract_key_metrics(annual_analysis)
        
        # 更新缓存
        update_cache(stock_code, {
            'annual': annual_analysis,
            'risk_basic': risk_basic,
            'key_metrics': key_metrics
        })
    
    # Step 1-6: 个股分析（引用缓存）
    analysis = {
        'basic_info': get_basic_info(stock_code),
        'price_volume': analyze_price_volume(stock_code),  # 实时
        'financial': annual_analysis['Part_A'],  # 引用年报
        'industry': annual_analysis['Part_B'],   # 引用年报
        'valuation': calculate_valuation(stock_code),  # 实时
        'risk': {
            'basic': risk_basic,  # 引用缓存
            'trading': analyze_trading_risk(stock_code)  # 实时
        }
    }
    
    # Step 7-8: 输出报告
    return generate_report(analysis)
```

---

## 七、总结

### 核心优势

| 优势 | 说明 |
|------|------|
| **避免重复分析** | 年报分析成果可复用 |
| **保持数据一致性** | 统一数据来源 |
| **提高效率** | 日常分析引用缓存，耗时减少50% |
| **清晰溯源** | 每个结论都标注来源 |

### 使用场景

| 场景 | 策略 |
|------|------|
| 年报发布后 | 执行完整年报分析，更新缓存 |
| 季报发布后 | 执行季报分析，更新部分缓存 |
| 日常个股分析 | 检查缓存，引用结论，仅更新实时数据 |
| 风险重评 | 引用年报缓存的基本面风控，更新交易面风控 |

---

*创建日期: 2026-03-28*
*版本: V1.0*