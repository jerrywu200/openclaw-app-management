# 个股分析标准流程（V3.5 - 智能化评分升级）

> 更新日期: 2026-03-30
> 版本: V3.5
> 
> **🎉 V3.5 重大升级**（2026-03-30）：
> - 🔥 **财务趋势分析**（Phase 1）
>   - 多期财务指标对比，判断改善/恶化
>   - 基本面评分 = 当期评分 + 趋势评分（-19 ~ +19分）
> - ✅ **评分置信度机制**（Phase 2）
>   - 三维度评估：完整度×40% + 时效性×30% + 一致性×30%
>   - 五级置信度：高/中高/中/中低/低
> - 📊 **同行估值对比**（Phase 3）
>   - PE/PB相对位置评分
>   - PB-ROE匹配度分析
> - ⚠️ **五维风险分解**（Phase 4）
>   - 财务风险(25%) + 估值风险(25%) + 行业风险(20%) + 技术风险(15%) + 流动性风险(15%)
>   - 五级风险等级：低/中低/中/中高/高
> - 🔔 **持续跟踪机制**（Phase 5）
>   - 评分历史记录 + 预警检测
>   - 心跳自动检查
> 
> **🔥 V3.4 重大更新**：
> - 🔥 **最新优先机制**（修正之前的"年报优先"）
>   - 如果当年度季报比年报新 → 用季报（年报待发布）
>   - 如果年报是最新 → 用年报
>   - **核心原则：永远使用最新可用的正式财报数据**
> - 🆕 统一数据过滤函数（`finance_data_filter.py`）
> - 🆕 数据用途矩阵（明确预告不参与评分）
> - 🆕 数据来源标注规范
> 
> **V3.3.3 新增**：
> - 财务数据优先使用年报（如有）
> - 年报优先于季报的分析机制
> 
> **V3.3 新增**：
> - 业绩预告分离分析（前瞻性洞察）
> - 基本面评分仅使用正式财报数据
> 
> **V3.3.1 新增**：
> - PE(TTM)计算修正（TTM EPS公式）

---

## 分析流程（十步法 V3.5）

```
┌─────────────────────────────────────────────────────────────┐
│               个股分析十步法 V3.5                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ 分析前必做：检查缓存                                    │
│    ├─ Step 0.1: 读取缓存索引（analysis_cache/README.md）    │
│    ├─ Step 0.2: 查找目标股票是否在缓存中                    │
│    └─ Step 0.3: 有缓存则读取，无缓存则分析后创建            │
│                                                             │
│  Step 0: 数据获取与预处理 🔥 V3.4升级                       │
│    ├─ 🔥 最新优先机制（使用最新正式财报）                   │
│    ├─ 🆕 统一数据过滤（finance_data_filter.py）             │
│    ├─ 一站式数据获取                                        │
│    ├─ 数据质量检查                                          │
│    └─ 重大事件扫描                                          │
│                                                             │
│  Step 1: 基本信息 + 前瞻性洞察                              │
│    ├─ 股价、市值、行业                                      │
│    ├─ 历史最高最低价、概念板块列表                          │
│    ├─ 近期重大事件摘要                                      │
│    └─ 🔮 业绩预告前瞻性洞察（独立分析，不参与评分）         │
│                                                             │
│  Step 2: 量价分析                                           │
│    ├─ K线形态 + 资金流向                                    │
│    └─ 龙虎榜深度分析                                        │
│                                                             │
│  Step 2.5: 短线分析                                         │
│    ├─ 分时图分析（黄白线、形态）                            │
│    ├─ 盘口分析（委比委差）                                  │
│    ├─ 技术信号（手动计算MACD/KDJ/布林带）                   │
│    └─ T+0机会评估                                           │
│                                                             │
│  Step 2.6: 事件驱动分析                                     │
│    ├─ 新闻情感分析                                          │
│    ├─ 公告影响评估                                          │
│    └─ 事件评分计算                                          │
│                                                             │
│  Step 3: 财务分析 ⭐ V3.5升级                               │
│    ├─ 🔥 使用最新正式财报（统一过滤函数）                   │
│    ├─ 仅使用正式财报数据（过滤预告/快报）                   │
│    ├─ 三表分析 + 关键指标                                   │
│    ├─ 🆕 V3.5 财务趋势分析（多期对比）                      │
│    └─ 红旗信号检测                                          │
│                                                             │
│  Step 4: 行业研究                                           │
│    ├─ 行业周期 + 竞争格局                                   │
│    ├─ 概念强度量化评分                                      │
│    ├─ 板块轮动分析                                          │
│    └─ 股票-板块共振分析                                     │
│                                                             │
│  Step 5: 估值分析 ⭐ V3.5升级                               │
│    ├─ 🔥 TTM计算使用统一过滤函数                           │
│    ├─ PE(TTM)使用TTM EPS计算                               │
│    ├─ PE/PB/PEG + 历史分位                                  │
│    ├─ 🆕 V3.5 同行估值对比                                  │
│    └─ 交叉验证                                              │
│                                                             │
│  Step 6: 市场环境分析                                       │
│    ├─ 全球指数                                              │
│    ├─ 热门概念板块                                          │
│    └─ 情绪判断                                              │
│                                                             │
│  Step 7: 风险防御 ⭐ V3.5升级                               │
│    ├─ 🆕 V3.5 五维风险分解                                  │
│    │   ├─ 财务风险(25%)                                     │
│    │   ├─ 估值风险(25%)                                     │
│    │   ├─ 行业风险(20%)                                     │
│    │   ├─ 技术风险(15%)                                     │
│    │   └─ 流动性风险(15%)                                   │
│    ├─ 风险等级判定                                          │
│    ├─ 仓位建议 + ATR止损                                    │
│    └─ 基本面止损条件                                        │
│                                                             │
│  Step 8: 投资建议 ⭐ V3.5升级                               │
│    ├─ 六维度综合评分                                        │
│    ├─ 🆕 V3.5 评分置信度                                    │
│    ├─ 风险等级 + 仓位建议                                   │
│    └─ 止损止盈策略                                          │
│                                                             │
│  Step 9: 🆕 V3.5 持续跟踪记录                               │
│    ├─ 检查历史评分（tracking/{code}_history.json）          │
│    ├─ 记录本次评分（record_score_history）                  │
│    ├─ 预警检测（check_alerts）                              │
│    └─ 关键指标监控（monitor_key_metrics）                   │
│                                                             │
│  Step 10: ⚠️ 分析报告同步（仅持仓股票）                     │
│    ├─ 检查股票是否在持仓中                                  │
│    ├─ 在持仓 → 同步评分/止损/目标价                         │
│    └─ 不在持仓 → 跳过同步                                   │
│                                                             │
│  附录: 数据质量报告                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块依赖关系

```
stock_analysis_framework.md (V3.4 主框架)
├── stock_db_tool.py              # 数据库工具
├── finance_data_filter.py        # 🆕 V3.4 统一数据过滤模块
├── event_driven_analysis.py      # 事件驱动分析模块
├── concept_strength_analysis.py  # 概念强度量化评分模块
├── forecast_analysis.py          # 业绩预告前瞻性分析模块
├── stock_scoring_model.py        # 综合评分模型（V3.4）
├── annual_report_analysis_framework.md  # 年报分析框架
├── risk_defense_framework.md     # 风险防御框架
└── industry_analysis_framework.md # 行业分析框架
```

---

## 🔥 数据用途矩阵（V3.4 新增）

```
┌─────────────────────────────────────────────────────────────┐
│                  数据用途矩阵 V3.4                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  分析模块          │ 年报 │ 季报 │ 业绩预告 │ 业绩快报 │     │
│  ─────────────────────────────────────────────────────────  │
│  基本面评分        │  ✅  │  ✅  │   ❌     │   ❌     │     │
│  估值评分          │  ✅  │  ✅  │   ❌     │   ❌     │     │
│  财务指标分析      │  ✅  │  ✅  │   ❌     │   ❌     │     │
│  三表分析          │  ✅  │  ✅  │   ❌     │   ❌     │     │
│  ─────────────────────────────────────────────────────────  │
│  前瞻性洞察        │  ❌  │  ❌  │   ✅     │   ✅     │     │
│  趋势判断          │  ❌  │  ❌  │   ✅     │   ✅     │     │
│  确定性评估        │  ❌  │  ❌  │   ✅     │   ✅     │     │
│  ─────────────────────────────────────────────────────────  │
│  报告期标注        │  ✅  │  ✅  │   ✅     │   ✅     │     │
│  数据来源说明      │  ✅  │  ✅  │   ✅     │   ✅     │     │
│                                                             │
│  ✅ = 用于计算/分析                                          │
│  ❌ = 不用于该模块                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心原则

1. **正式财报（年报/季报）** → 用于评分计算
2. **业绩预告/快报** → 仅用于前瞻性洞察，不参与评分

---

## 数据源优先级（V3.4）

### 一、数据获取层级

```
┌─────────────────────────────────────────────────────────────┐
│                    数据源优先级 V3.4                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🥇 第一优先级：stock_db（可信度最高）                       │
│     ├─ K线/分时/盘口 → get_stock_kline()                   │
│     ├─ 财务数据 → get_stock_finance()                      │
│     ├─ 资金流向 → get_stock_fund_flow()                    │
│     ├─ 概念强度 → get_stock_concept_detail()               │
│     ├─ 新闻资讯 → get_stock_news()                         │
│     └─ 龙虎榜 → get_dragon_tiger()                         │
│                                                             │
│  🥈 第二优先级：akshare（补充验证）                          │
│     ├─ 股本验证 → stock_individual_info_em()                │
│     ├─ 研报预测 → stock_research_report_em()                │
│     └─ 行业分类 → stock_board_industry_name_ths()           │
│                                                             │
│  🥉 第三优先级：web_search（深度研究补充）                   │
│     ├─ 行业深度分析                                         │
│     ├─ 公司战略解读                                         │
│     └─ 竞争格局研究                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 二、数据质量检查

| 数据类型 | 检查项 | 处理方式 |
|----------|--------|----------|
| K线数据 | 最新日期 ≤ 昨天 | 正常使用 |
| 财务数据 | 报告期是否最新 | 使用最新可用 |
| 概念强度 | 评分日期 | 正常使用 |
| 新闻资讯 | 过滤未来日期 | 自动过滤 |

### 三、导入方式

```python
import sys
sys.path.insert(0, '/Users/jw/.openclaw/workspace')

# 数据库工具
from stock_db_tool import (
    get_stock_kline,
    get_stock_finance,
    get_stock_fund_flow,
    get_stock_concept_detail,
    get_stock_news,
    get_stock_analysis_data  # 一站式数据获取
)

# 🆕 V3.2新增模块
from event_driven_analysis import calculate_event_score
from concept_strength_analysis import calculate_concept_strength_score, analyze_stock_sector_resonance
from stock_scoring_model import calculate_comprehensive_score
```

---

## ⚠️ 分析前必做：检查缓存

**每次个股分析前，必须先检查缓存！**

### 缓存检查流程

```
┌─────────────────────────────────────────────────────────────┐
│                  分析前缓存检查流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 0.1: 读取缓存索引                                     │
│     文件: analysis_cache/README.md                          │
│     查看"缓存股票列表"表格                                  │
│                                                             │
│  Step 0.2: 在表格中查找目标股票代码                         │
│     ├─ 找到 → 有缓存                                        │
│     │   └─ ✅ 完整 → 直接引用缓存数据                       │
│     └─ 未找到 → 无缓存，分析后创建缓存                      │
│                                                             │
│  Step 0.3: 读取缓存文件（有缓存时）                          │
│     ├─ risk_basic.json → 风险评分、仓位、止损位             │
│     └─ key_metrics.json → 关键财务指标                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 缓存使用示例

```python
import json

# 1. 检查缓存索引
# 手动读取 analysis_cache/README.md，查找目标股票

# 2. 如有缓存，读取缓存文件
with open('analysis_cache/300308_INNOLIGHT/risk_basic.json') as f:
    risk_basic = json.load(f)

# 3. 引用缓存数据
basic_risk_score = risk_basic['basic_risk_score']  # 21
risk_level = risk_basic['basic_risk_level']  # "低风险"
position_limit = risk_basic['position_limit']  # 15
stop_loss = risk_basic['atr_stop_loss']['stop_loss_price']  # 519.88

# 4. 在报告中标注来源
# "来源：年报分析缓存" 或 "来源：个股分析缓存"
```

### 缓存状态说明

| 状态 | 说明 | 操作 |
|------|------|------|
| ✅ 完整 | 已有年报分析缓存 | 直接引用 |
| ⚠️ 待年报补充 | 仅有个股分析缓存 | 引用缓存，年报后更新 |
| ❌ 无缓存 | 未分析过 | 分析后创建缓存 |

---

## Step 0: 数据获取与预处理

### 一、⚠️ 年报优先机制（V3.3.3核心更新）

**原则**：财务数据优先使用年报，年报优于季报

```python
from stock_db_tool import get_stock_finance

# 获取财务数据
finance = get_stock_finance('603993', limit=10)

# 过滤正式财报
def is_official(row):
    period = str(row.get('报告期', ''))
    return '预告' not in period and '快报' not in period

official = finance[finance.apply(is_official, axis=1)]

# ⭐ 优先查找年报
annual_reports = official[official['报告期'].str.contains('年报')]

if len(annual_reports) > 0:
    # 有年报 → 使用最新年报数据
    latest_annual = annual_reports.iloc[0]
    print(f"使用年报数据: {latest_annual['报告期']}")
else:
    # 无年报 → 使用最新季报数据
    latest = official.iloc[0]
    print(f"使用季报数据: {latest['报告期']}")
```

**为什么要年报优先**：
| 年报 | 季报 |
|------|------|
| 完整审计 | 未审计 |
| 数据完整 | 部分数据缺失 |
| 年度指标准确 | 累计值需计算 |

### 二、一站式数据获取

```python
from stock_db_tool import get_stock_analysis_data

# 一次性获取分析所需的全部数据
data = get_stock_analysis_data('300308', kline_days=60)

# 返回数据结构
{
    'stock_code': '300308.SZ',
    'kline': DataFrame,           # K线数据
    'finance': DataFrame,         # 财务数据
    'fund_flow': DataFrame,       # 资金流向
    'highest_lowest': dict,       # 历史高低价
    'concepts': DataFrame,        # 概念详情
    'news': list,                 # 新闻列表
    'dragon_tiger': list          # 龙虎榜
}
```

### 二、数据质量检查

| 检查项 | 标准 | 处理 |
|--------|------|------|
| K线数据 | 最新日期 ≥ 昨天-1 | ✅ 可用 |
| 财务数据 | 至少1个报告期 | ✅ 可用 |
| 概念强度 | 有数据 | ✅ 可用 |
| 新闻数据 | 已过滤异常日期 | ✅ 可用 |

---

## Step 1: 基本信息 + 前瞻性洞察 ⭐ V3.3升级

### 一、核心数据

| 数据项 | 数据来源 | 函数 |
|--------|----------|------|
| 最新股价 | stock_db | `get_stock_kline()` |
| 总市值 | 计算 | 股价 × 股本 |
| 历史最高最低价 | stock_db | `get_stock_highest_lowest_price()` |
| 所属行业 | akshare | `stock_board_industry_name_ths()` |
| 概念板块 | stock_db | `get_stock_concept_detail()` |
| 近期新闻 | stock_db | `get_stock_news()` |

### 二、🆕 前瞻性洞察（业绩预告分析）⭐ V3.3核心更新

**设计原则**：业绩预告与正式财报分离处理

| 数据类型 | 定位 | 用途 |
|----------|------|------|
| **正式财报** | 评分计算依据 | 基本面评分、估值计算 |
| **业绩预告** | 前瞻性洞察 | 趋势判断、预期分析 |

**使用方法**：

```python
from forecast_analysis import analyze_forecast_trend

# 分析业绩预告前瞻性
forecast = analyze_forecast_trend('300308')

if forecast.get('has_forecast'):
    info = forecast['forecast_info']
    print(f"预告期: {info['period']}")
    print(f"预告增速: {info['growth_rate']}%")
    
    # 趋势分析
    trend = forecast['analysis']['trend']
    print(f"趋势: {trend['trend']}")  # 加速/持平/放缓
    print(f"判断: {trend['message']}")
    
    # 前瞻性结论
    conclusion = forecast['conclusion']
    print(f"综合判断: {conclusion['outlook_text']}")  # 偏多/偏空/中性
```

**报告展示格式**：

```markdown
## 🔮 前瞻性洞察（业绩预告）

| 项目 | 数据 |
|------|------|
| 预告期 | 2025年报预告 |
| 预告增速 | 115.9% |
| 趋势判断 | 加速 🔥 |
| 确定性 | 中等 |
| 前瞻性结论 | 偏多 |
```

---

## ⚠️ 缓存更新规则（重要）

**缓存用途**：存储正式发布的最新年报数据

### 更新条件

| 条件 | 操作 |
|------|------|
| **有正式年报数据** | 分析完成后更新缓存 |
| **无正式年报数据** | 分析完成后**不更新**缓存 |

### 判断方法

```python
from stock_db_tool import get_stock_finance

finance = get_stock_finance('300308', limit=10)

# 过滤正式财报
def is_official_report(row):
    period = str(row.get('报告期', ''))
    return '预告' not in period and '快报' not in period

official = finance[finance.apply(is_official_report, axis=1)]

# 检查是否有年报
has_annual = any('年报' in p for p in official['报告期'].tolist())

if has_annual:
    print("✅ 有正式年报 → 分析后更新缓存")
else:
    print("⚠️ 无正式年报 → 分析后不更新缓存")
```

### 缓存状态说明

| 状态 | 含义 | 是否更新 |
|------|------|----------|
| ✅ 完整 | 已有年报分析缓存 | 有新版年报时更新 |
| ⚠️ 待年报补充 | 仅有个股分析缓存，无年报 | 发布年报后更新 |

---

## Step 2: 量价分析

### 一、核心数据

| 数据项 | 数据来源 | 函数 |
|--------|----------|------|
| K线数据 | stock_db | `get_stock_kline()` |
| 资金流向 | stock_db | `get_stock_fund_flow()` |
| 龙虎榜 | stock_db | `get_dragon_tiger()` |

### 二、K线统计（近30日）

```python
kline = get_stock_kline('605305', limit=30)

# 统计指标
阳天数 = len(kline[kline['change_percent'] > 0])
阴天数 = len(kline[kline['change_percent'] < 0])
涨跌幅 = (kline.iloc[-1]['close_price'] - kline.iloc[0]['close_price']) / kline.iloc[0]['close_price'] * 100
成交额变化 = kline['trading_amount'].mean()

# 量价配合判断
上涨放量比例 = len(kline[(kline['change_percent'] > 0) & (kline['trading_amount'] > kline['trading_amount'].shift(1))]) / 阳天数
```

---

## Step 2.5: 短线分析

### 一、数据来源

| 数据项 | 数据来源 | 函数 | 实时性 |
|--------|----------|------|--------|
| K线数据 | stock_db | `get_stock_kline()` | 盘后数据 |
| 资金流向 | stock_db | `get_stock_fund_flow()` | 盘后数据 |

> ⚠️ **注意**：当前stock_db数据为盘后数据，实时数据需手工提供。

### 二、技术指标计算（手动计算）

```python
# MACD计算
prices = kline['close_price']
ema12 = prices.ewm(span=12, adjust=False).mean()
ema26 = prices.ewm(span=26, adjust=False).mean()
dif = ema12 - ema26
dea = dif.ewm(span=9, adjust=False).mean()
macd = (dif - dea) * 2

# KDJ计算
n = 9
low_n = kline['low_price'].rolling(n).min()
high_n = kline['high_price'].rolling(n).max()
rsv = (kline['close_price'] - low_n) / (high_n - low_n) * 100
K = rsv.ewm(span=3, adjust=False).mean()
D = K.ewm(span=3, adjust=False).mean()
J = 3 * K - 2 * D

# 布林带计算
mid = prices.rolling(20).mean()
std = prices.rolling(20).std()
upper = mid + 2 * std
lower = mid - 2 * std
```

---

## Step 2.6: 🆕 事件驱动分析

### 一、分析框架

```
┌─────────────────────────────────────────────────────────────┐
│              Step 2.6: 事件驱动分析                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📰 新闻分析                                                │
│    ├─ 近期重大新闻提取                                      │
│    ├─ 新闻类型分类（事件/公告/研报/行业）                   │
│    ├─ 情感倾向判断（正面/中性/负面）                        │
│    └─ 新闻-股价关联分析                                     │
│                                                             │
│  📢 公告影响评估                                            │
│    ├─ 业绩预告/快报                                         │
│    ├─ 重大事项公告                                          │
│    └─ 风险提示公告                                          │
│                                                             │
│  🔔 事件评分计算                                            │
│    ├─ 事件评分：-30 ~ +30分                                │
│    └─ 情绪判断：偏多/偏空/中性                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 二、使用方法

```python
from event_driven_analysis import calculate_event_score, generate_event_analysis_report

# 计算事件评分
event_score = calculate_event_score('300308', days=90)

# 生成完整报告
report = generate_event_analysis_report('300308', '中际旭创', days=90)
```

### 三、事件影响评估模板

| 事件类型 | 重要度 | 典型影响 | 持续时间 |
|----------|--------|----------|----------|
| 业绩预告/快报 | ⭐⭐⭐⭐⭐ | 直接影响 | 1-5日 |
| 重大合同/订单 | ⭐⭐⭐⭐ | 正面 | 3-10日 |
| 股权变动 | ⭐⭐⭐⭐ | 视情况 | 5-20日 |
| 行业政策 | ⭐⭐⭐⭐ | 板块联动 | 10-30日 |
| 研报覆盖 | ⭐⭐⭐ | 短期刺激 | 1-3日 |

---

## Step 3: 财务分析 ⭐ V3.5升级

### 一、⚠️ 核心更新：仅使用正式财报

**V3.3原则**：基本面评分仅使用正式财报数据，过滤业绩预告/快报

```python
from stock_db_tool import get_stock_finance

finance = get_stock_finance('300308', limit=10)

# 过滤正式财报
def is_official_report(row):
    period = str(row.get('报告期', ''))
    return '预告' not in period and '快报' not in period

official_finance = finance[finance.apply(is_official_report, axis=1)]

# 使用正式财报数据进行评分
latest = official_finance.iloc[0]  # 最新正式财报
```

**原因说明**：

| 数据类型 | 特点 | 用途 |
|----------|------|------|
| 正式财报 | 完整、审计验证 | 评分计算 |
| 业绩预告 | 不完整、有不确定性 | 前瞻性洞察（Step 1） |

### 二、核心数据

| 数据项 | 数据来源 | 函数 |
|--------|----------|------|
| 财务数据 | stock_db | `get_stock_finance()` |

### 三、关键指标

| 指标 | 计算方式 | 判断标准 |
|------|----------|----------|
| ROE | 净利润/净资产 | ≥15%优秀 |
| 毛利率 | 毛利/营收 | ≥30%优秀 |
| 净利率 | 净利润/营收 | ≥10%优秀 |
| 资产负债率 | 负债/资产 | ≤60%健康 |
| 营收增长 | 同比 | ≥20%优秀 |
| 利润增长 | 同比 | ≥20%优秀 |

### 四、🆕 V3.5 财务趋势分析

**设计目标**：不仅看当期值，还要判断指标是在改善还是恶化

#### 1. 趋势分析指标（5项）

| 指标 | 趋势重要性 | 趋势加分范围 | 说明 |
|------|------------|--------------|------|
| ROE | ⭐⭐⭐⭐⭐ | -5 ~ +5分 | 核心盈利指标 |
| 毛利率 | ⭐⭐⭐⭐ | -3 ~ +3分 | 盈利质量 |
| 净利率 | ⭐⭐⭐ | -3 ~ +3分 | 盈利效率 |
| 营收增长 | ⭐⭐⭐ | -3 ~ +3分 | 成长性 |
| 利润增长 | ⭐⭐⭐⭐ | -5 ~ +5分 | 成长性核心 |
| **合计** | | **-19 ~ +19分** | |

#### 2. 趋势判断规则

| 趋势类型 | 判断条件 | 图标 | 加分 |
|----------|----------|------|------|
| **连续改善** | 连续3期上升 | 🔥 | +5分（ROE）/ +3分（其他） |
| **改善放缓** | 上升但速度减缓 | 📈↓ | +2分 |
| **持平** | 波动<5% | → | 0分 |
| **波动** | 忽上忽下 | ↔ | 0分 |
| **恶化放缓** | 下降但速度减缓 | 📉↑ | -2分 |
| **连续恶化** | 连续3期下降 | ⚠️ | -5分（ROE）/ -3分（其他） |

#### 3. 使用方法

```python
from finance_data_filter import analyze_financial_trend

# 分析财务趋势
trend_result = analyze_financial_trend(finance_df)

# 返回结构
{
    'trend_score': 8,              # 趋势评分（-19 ~ +19）
    'trends': {
        'roe': {'trend': '改善', 'score': 5, 'history': [22.5, 24.8, 26.6]},
        'gross_margin': {'trend': '改善', 'score': 3, 'history': [17.2, 18.5, 19.9]},
        ...
    },
    'summary': '财务指标多数改善',
    'total_records': 5             # 用于趋势分析的期数
}
```

#### 4. 报告展示格式

```markdown
### 📊 V3.5 财务趋势分析

#### ROE趋势
```
2023年报: 22.5%  ███████████████
2024年报: 24.8%  █████████████████
2025年报: 26.6%  ██████████████████
```
趋势：🔥 连续3年改善 → 趋势加分 +5分

#### 毛利率趋势
```
2023年报: 17.2%  ███████████
2024年报: 18.5%  ████████████
2025年报: 19.9%  █████████████
```
趋势：🔥 连续3年改善 → 趋势加分 +3分

**趋势总评**：财务指标多数改善 → 趋势加分 +8分
```

#### 5. 基本面评分公式

```
基本面评分 = 当期评分 + 趋势评分
```

**示例**：
- 当期评分：72.7分（ROE、毛利率等当期值评分）
- 趋势评分：+8分（多指标改善）
- **总分**：80.7分

---

## Step 4: 行业研究 🆕 升级

### 一、传统分析

- 行业周期：成长期/成熟期/衰退期
- 竞争格局：龙头/跟随者/挑战者
- 市场空间：天花板/增长率

### 二、🆕 概念强度量化评分

```python
from concept_strength_analysis import calculate_concept_strength_score

# 计算概念强度评分
result = calculate_concept_strength_score('300308', limit=10)

# 返回结构
{
    'concept_score': 84.98,        # 概念强度评分（0-100）
    'avg_strength': 64.08,         # 平均强度
    'strong_count': 9,             # 强势概念数量
    'strong_concepts': [...]       # 强势概念列表
}
```

**评分规则**：
- 平均强度（40分）+ 强势概念数量（30分）+ 最强概念强度（30分）

### 三、🆕 股票-板块共振分析

```python
from concept_strength_analysis import analyze_stock_sector_resonance

# 共振分析
resonance = analyze_stock_sector_resonance('300308', limit=10)

# 返回结构
{
    'resonance_score': 67.42,      # 共振评分（0-100）
    'resonance_level': '独立行情', # 共振等级
    'strong_resonance': [...],     # 强共振概念
    'independent_stocks': [...],   # 独立行情概念
    'analysis': '股票在5个概念中表现强势...'  # 分析结论
}
```

**四象限模型**：

| 股票强度 | 板块强度 | 共振类型 | 说明 |
|----------|----------|----------|------|
| ≥60 | ≥60 | 强共振 | 上涨动能充足 |
| ≥60 | <60 | 独立行情 | 个股自身逻辑 |
| <40 | ≥60 | 滞后 | 跟随性弱 |
| <40 | <40 | 弱共振 | 下跌风险大 |

---

## Step 5: 估值分析 ⭐ V3.3.1升级

### 一、⚠️ 核心修正：PE(TTM)必须使用TTM EPS

**V3.3.1修正**：PE(TTM) = 股价 / TTM EPS（严禁用季度累计EPS）

**TTM EPS计算公式**：
```
TTM EPS = 最新累计EPS + 去年年报EPS - 去年同期累计EPS
```

**示例（中际旭创）**：
```python
# 错误做法 ❌
eps = latest_fin.get('基本每股收益(元)')  # 6.48元（季度累计）
pe_wrong = price / eps  # 92.3倍（错误）

# 正确做法 ✅
eps_current = 6.48      # 2025三季报累计
eps_last_annual = 4.72  # 2024年报
eps_last_same = 3.42    # 2024三季报（去年同期）

eps_ttm = eps_current + eps_last_annual - eps_last_same  # 7.78元
pe_ttm = price / eps_ttm  # 76.9倍（正确）
```

**代码实现**：

```python
from stock_db_tool import get_stock_finance

finance = get_stock_finance('300308', limit=10)

# 过滤正式财报
official = finance[finance.apply(is_official_report, axis=1)]

current = official.iloc[0]
current_period = str(current['报告期'])
eps_current = float(current['基本每股收益(元)'])

# 动态判断年份
current_year = '2025' if '2025' in current_period else '2024'
last_year = str(int(current_year) - 1)

# 查找去年年报和去年同期
eps_last_annual = 0
eps_last_same = 0

for i in range(len(official)):
    row = official.iloc[i]
    period = str(row['报告期'])
    eps = row.get('基本每股收益(元)', 0)
    
    if pd.notna(eps) and eps != 0:
        if '年报' in period and last_year in period:
            eps_last_annual = float(eps)
        if period == current_period.replace(current_year, last_year):
            eps_last_same = float(eps)

# 计算TTM EPS
eps_ttm = eps_current + eps_last_annual - eps_last_same
pe_ttm = latest_price / eps_ttm
```

### 二、核心数据

| 数据项 | 数据来源 | 函数 |
|--------|----------|------|
| K线数据 | stock_db | `get_stock_kline()` |
| 财务数据 | stock_db | `get_stock_finance(limit=10)` |
| 历史高低价 | stock_db | `get_stock_highest_lowest_price()` |

### 三、估值指标

| 指标 | 计算方式 | 判断标准 |
|------|----------|----------|
| PE(TTM) | 股价/EPS | 行业对比 |
| PEG | PE/增长率 | <1低估 |
| PB | 股价/净资产 | ROE匹配 |
| 历史分位 | 当前位置 | <30%低估 |

### 四、🆕 V3.5 同行估值对比

**设计目标**：不仅看绝对估值，还要与同行对比判断相对估值是否合理

#### 1. 数据获取

```python
from finance_data_filter import get_stock_industry, get_industry_peers_valuation

# 获取股票所属行业
industry = get_stock_industry('603993')  # "有色金属-钼"

# 获取同行估值数据
peers = get_industry_peers_valuation('603993', industry)

# 返回结构
{
    'stock_code': '603993',
    'industry': '有色金属-钼',
    'peers': [
        {'code': '601899', 'name': '紫金矿业', 'pe': 20.5, 'pb': 4.2, 'roe': 25.0},
        {'code': '600362', 'name': '江西铜业', 'pe': 12.3, 'pb': 1.1, 'roe': 8.5},
        ...
    ],
    'industry_avg_pe': 18.5,
    'industry_avg_pb': 2.8,
    'industry_avg_roe': 15.2
}
```

#### 2. 相对估值评分

| 维度 | 评分规则 | 分数 |
|------|----------|------|
| **PE相对评分** | PE低于行业平均20%以上 | +15分 |
| | PE低于行业平均10-20% | +10分 |
| | PE与行业平均接近（±10%） | 0分 |
| | PE高于行业平均10-20% | -10分 |
| | PE高于行业平均20%以上 | -15分 |
| **PB-ROE匹配** | 高ROE(>行业平均) + 低PB(<行业平均) | +20分 ✅ |
| | ROE与PB匹配（都高于/低于行业） | 0分 |
| | 低ROE + 高PB | -20分 ⚠️ |

#### 3. 使用方法

```python
from finance_data_filter import calculate_relative_valuation_score

# 计算相对估值评分
result = calculate_relative_valuation_score(
    stock_code='603993',
    stock_pe=18.51,
    stock_pb=4.57,
    stock_roe=26.61,
    industry_avg_pe=18.5,
    industry_avg_pb=2.8,
    industry_avg_roe=15.2
)

# 返回结构
{
    'pe_relative_score': 0,        # PE相对评分
    'pb_roe_score': 20,            # PB-ROE匹配评分
    'total_relative_score': 20,    # 总相对评分
    'analysis': 'PE与行业持平，但ROE远高于行业平均，PB-ROE匹配优秀'
}
```

#### 4. 报告展示格式

```markdown
### 📊 V3.5 同行估值对比

| 指标 | 洛阳钼业 | 行业平均 | 相对位置 |
|------|----------|----------|----------|
| PE(TTM) | 18.51倍 | 18.5倍 | 持平 |
| PB | 4.57倍 | 2.8倍 | 高63% ⚠️ |
| ROE | 26.61% | 15.2% | 高75% 🔥 |

**PB-ROE匹配分析**：
- ROE远高于行业平均 → 理应享受更高PB
- PB-ROE匹配度：优秀 ✅
- 相对估值评分：+20分
```

---

## Step 6: 市场环境分析 🆕 升级

### 一、核心数据

| 数据项 | 数据来源 | 函数 |
|--------|----------|------|
| 全球指数 | stock_db | `get_global_index()` |
| 🆕 热门板块 | stock_db | `get_hot_concepts()` |

### 二、🆕 热门板块识别

```python
from stock_db_tool import get_hot_concepts

# 获取热门板块
hot = get_hot_concepts(top_n=10)

# 返回字段
{
    'board_name': '概念名称',
    'market_strength_score': 86.5  # 市场强度评分
}
```

---

## Step 7: 风险防御 ⭐ V3.5升级

### 一、🆕 V3.5 五维风险分解

**设计目标**：将单一风险等级分解为五维风险评分，更精准地评估风险

#### 1. 五维风险框架

| 维度 | 权重 | 核心指标 | 评分范围 |
|------|------|----------|----------|
| 财务风险 | 25% | 资产负债率、流动比率 | 0-100分 |
| 估值风险 | 25% | PEG、PE分位 | 0-100分 |
| 行业风险 | 20% | 行业周期、政策风险 | 0-100分 |
| 技术风险 | 15% | 均线状态、MACD | 0-100分 |
| 流动性风险 | 15% | 日均成交额、换手率 | 0-100分 |

**综合风险评分 = Σ(维度评分 × 权重)**

#### 2. 各维度评分规则

**财务风险评分**：

| 资产负债率 | 流动比率 | 风险评分 |
|------------|----------|----------|
| ≤40% | ≥1.5 | 10分（低风险） |
| 40-60% | 1.0-1.5 | 25分（中低） |
| 60-75% | 0.8-1.0 | 50分（中等） |
| >75% | <0.8 | 80分（高风险） |

**估值风险评分**：

| PEG | PE分位 | 风险评分 |
|-----|--------|----------|
| <0.5 | <30% | 10分（低估） |
| 0.5-1.0 | 30-60% | 25分（合理） |
| 1.0-2.0 | 60-80% | 50分（偏高） |
| >2.0 | >80% | 80分（高估） |

#### 3. 使用方法

```python
from stock_scoring_model import calculate_5d_risk_score

# 计算五维风险评分
result = calculate_5d_risk_score(
    stock_code='603993',
    debt_ratio=50.34,
    current_ratio=1.55,
    peg=0.37,
    industry_stage='成长期',
    ma_status='空头',
    daily_volume=25.6
)

# 返回结构
{
    'financial_risk': 25,
    'valuation_risk': 10,
    'industry_risk': 15,
    'technical_risk': 60,
    'liquidity_risk': 10,
    'total_risk_score': 24.75,
    'risk_level': '低风险',
    'position_limit': 15
}
```

#### 4. 风险评分与仓位映射

| 综合风险评分 | 风险等级 | 仓位建议 |
|--------------|----------|----------|
| 0-30分 | 低风险 ✅ | ≤15% |
| 30-50分 | 中低风险 🟢 | ≤12% |
| 50-70分 | 中等风险 🟡 | ≤10% |
| 70-85分 | 中高风险 🟠 | ≤5% |
| ≥85分 | 高风险 🔴 | 0% |

### 二、5项核心风险指标（传统）

| 风险项 | 核心指标 | 数据来源 | 评分标准 |
|--------|----------|----------|----------|
| 偿债风险 | 资产负债率 | stock_finance | ≤60%健康 |
| 现金流风险 | 净现比 | stock_finance | >1健康 |
| 行业周期 | 行业阶段 | 行业研究 | 成长期低风险 |
| 估值风险 | PEG | 计算 | <1低风险 |
| 技术趋势 | 均线状态 | K线计算 | 多头低风险 |

### 三、🆕 事件风险因素

| 风险类型 | 触发条件 | 处理建议 |
|----------|----------|----------|
| 重大负面事件 | 事件评分<-15 | 提高风险等级 |
| 业绩预告亏损 | 预亏公告 | 提高风险等级 |
| 行业政策利空 | 行业负面政策 | 提高风险等级 |

### 四、ATR止损计算

```python
# ATR计算
import pandas as pd
kline = get_stock_kline('300308', limit=60)

kline['TR'] = pd.concat([
    kline['high_price'] - kline['low_price'],
    abs(kline['high_price'] - kline['close_price'].shift(1)),
    abs(kline['low_price'] - kline['close_price'].shift(1))
], axis=1).max(axis=1)
kline['ATR14'] = kline['TR'].rolling(14).mean()

latest = kline.iloc[-1]
atr_stop_loss = latest['close_price'] - 2 * latest['ATR14']
```

---

## Step 8: 投资建议 ⭐ V3.5升级

### 一、🆕 六维度综合评分

```python
from stock_scoring_model import calculate_comprehensive_score

# 计算综合评分
result = calculate_comprehensive_score('300308', '中际旭创')

# 返回结构
{
    'comprehensive_score': 71.88,
    'rating': '买入',
    'rating_star': '⭐⭐⭐⭐',
    'risk_level': '低风险',
    'position_limit': 15,
    'dimensions': {...}
}
```

### 二、🆕 V3.5 评分置信度

**设计目标**：输出评分的同时，输出置信度，让用户知道评分有多可靠

#### 置信度三维度

| 维度 | 权重 | 评估内容 |
|------|------|----------|
| 数据完整度 | 40% | 财务数据是否完整 |
| 数据时效性 | 30% | 财务数据是否新鲜 |
| 数据一致性 | 30% | 指标趋势是否一致 |

**总置信度 = 完整度×40% + 时效性×30% + 一致性×30%**

#### 使用方法

```python
from finance_data_filter import calculate_confidence

result = calculate_confidence(
    finance_data=finance_df,
    trend_result=trend_result,
    latest_period='2025年报'
)

# 返回：{'completeness': 90, 'timeliness': 95, 'consistency': 70, 'total_confidence': 85, 'level': '高'}
```

### 三、六维度权重

| 维度 | 权重 | 评分内容 |
|------|------|----------|
| 基本面 | 20% | 盈利/成长/偿债/运营/现金流 |
| 行业前景 | 20% | 概念强度+板块热度+共振 |
| 估值 | 15% | PEG/PE分位/PB-ROE |
| 技术面 | 15% | MACD/KDJ/布林带/均线/量能 |
| 事件驱动 | 15% | 新闻情感分析 |
| 市场环境 | 15% | 全球市场+板块轮动 |

### 四、评级标准

| 分数 | 评级 | 星级 | 建议 |
|------|------|------|------|
| ≥80 | 强烈买入 | ⭐⭐⭐⭐⭐ | 积极布局 |
| 70-79 | 买入 | ⭐⭐⭐⭐ | 逢低布局 |
| 60-69 | 持有 | ⭐⭐⭐ | 持有观望 |
| 50-59 | 减持 | ⭐⭐ | 考虑减仓 |
| <50 | 卖出 | ⭐ | 建议卖出 |

---

## Step 9: 🆕 V3.5 持续跟踪记录

### ⚠️ 重要提示

**每次个股分析完成后，必须执行持续跟踪记录！**

### 一、跟踪记录流程

| 步骤 | 内容 | 函数 |
|------|------|------|
| 9.1 | 检查历史评分 | 读取 `tracking/{code}_history.json` |
| 9.2 | 记录本次评分 | `record_score_history()` |
| 9.3 | 预警检测 | `check_alerts()` |
| 9.4 | 关键指标监控 | `monitor_key_metrics()` |

### 二、使用方法

```python
from tracking_monitor import record_score_history, check_alerts

# 1. 记录评分历史
record_score_history(
    stock_code='603993',
    stock_name='洛阳钼业',
    analysis_result={
        'comprehensive_score': 77.25,
        'rating': '买入',
        'risk_level': '中等风险'
    }
)

# 2. 预警检测
alerts = check_alerts(stock_code='603993', current_result=analysis_result)
```

### 三、预警级别

| 级别 | 触发条件 | 处理方式 |
|------|----------|----------|
| 🔴 critical | 止损触发、评级降至"卖出" | 立即通知 |
| 🟡 warning | 评分下降>10分、评级下调 | 汇总通知 |
| 🟢 info | 评分小幅变化 | 每日汇总 |

### 四、检查清单

- [ ] 历史评分已检查
- [ ] 本次评分已记录
- [ ] 预警检测已执行
- [ ] 如有预警，已通知用户

---

## Step 10: ⚠️ 分析报告同步（仅持仓股票）

### ⚠️ 重要提示

**分析报告完成后，必须检查股票是否在持仓中！**

```
┌─────────────────────────────────────────────────────────────┐
│                  分析报告同步流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  检查股票是否在持仓中（positions.csv）？                      │
│     │                                                       │
│     ├─ ✅ 是 → 执行同步流程                                 │
│     │    │                                                  │
│     │    ├─ 同步评分                                        │
│     │    ├─ 同步止损位                                      │
│     │    └─ 同步目标价                                      │
│     │                                                       │
│     └─ ❌ 否 → 跳过同步，仅保存报告和缓存                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 一、同步命令

```bash
# 一键同步（推荐）
python3 /Users/jw/.openclaw/workspace/analysis_sync.py --code {代码} --sync-all

# 分别同步
python3 analysis_sync.py --code {代码} --sync-score --score {评分} --rating {评级}
python3 analysis_sync.py --code {代码} --sync-stop --stop {止损价} --stop-pct {止损比例}
python3 analysis_sync.py --code {代码} --sync-target --target-low {下限} --target-high {上限}
```

### 二、同步检查清单

**仅持仓股票需要同步！**

- [ ] 分析报告已保存 → `reports/{股票名称}_{代码}_分析报告_{日期}.md`
- [ ] 缓存已创建 → `analysis_cache/{代码}_{英文名}/`
- [ ] 股票在持仓中？
  - ✅ 是 → 执行同步
    - [ ] 评分已同步
    - [ ] 止损位已同步
    - [ ] 目标价已同步
    - [ ] 最后分析日期已更新 🆕
  - ❌ 否 → 跳过同步

### 三、同步示例

```bash
# 完成中际联合分析后
# 1. 保存报告
# 2. 创建缓存
# 3. 检查持仓（中际联合在持仓中）
# 4. 执行同步

python3 analysis_sync.py --code 605305 --sync-all --score 82.10 --rating "强烈买入" --stop 37.8 --target-low 50 --target-high 55
```

### 四、注意事项

1. **同步时机**：分析报告完成后立即执行
2. **同步范围**：仅持仓股票，非持仓股票跳过
3. **同步内容**：评分、止损位、目标价、最后分析日期
4. **同步验证**：检查 `portfolio/positions.csv` 确认更新成功

---

## 附录: 🆕 数据质量报告

### 报告模板

```markdown
## 数据质量报告（V3.2新增）

### 数据时效性
| 数据类型 | 最新日期 | 状态 | 备注 |
|----------|----------|------|------|
| K线数据 | 2026-03-27 | ✅ 新鲜 | 滞后1天 |
| 财务数据 | 2025-12-31 | ✅ 完整 | 年报已发布 |
| 概念强度 | 2026-03-28 | ✅ 新鲜 | 实时更新 |
| 新闻资讯 | 2026-03-28 | ✅ 新鲜 | 已过滤异常 |

### 数据缺失说明
- 无

### 数据异常说明
- 无
```

---

## 完整分析示例

```python
import sys
sys.path.insert(0, '/Users/jw/.openclaw/workspace')

# 1. 一站式数据获取
from stock_db_tool import get_stock_analysis_data
data = get_stock_analysis_data('300308', kline_days=60)

# 2. 事件驱动分析
from event_driven_analysis import calculate_event_score
event_score = calculate_event_score('300308', days=90)
print(f"事件评分: {event_score['event_score']}")
print(f"近期情绪: {event_score['recent_sentiment']}")

# 3. 概念强度分析
from concept_strength_analysis import calculate_concept_strength_score, analyze_stock_sector_resonance
concept = calculate_concept_strength_score('300308', limit=10)
print(f"概念强度评分: {concept['concept_score']}")

resonance = analyze_stock_sector_resonance('300308', limit=10)
print(f"共振等级: {resonance['resonance_level']}")

# 4. 综合评分
from stock_scoring_model import calculate_comprehensive_score
result = calculate_comprehensive_score('300308', '中际旭创')
print(f"综合评分: {result['comprehensive_score']}")
print(f"评级: {result['rating']} {result['rating_star']}")
print(f"建议仓位: ≤{result['position_limit']}%")
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| **V3.5** | 2026-03-30 | 🎉 **五大模块升级**：财务趋势分析、评分置信度、同行估值对比、五维风险分解、持续跟踪机制 |
| V3.4 | 2026-03-30 | 🔥 最新优先机制（修正年报优先）；统一数据过滤函数；数据用途矩阵 |
| V3.3.3 | 2026-03-29 | 年报优先机制（财务数据优先使用年报） |
| V3.3.2 | 2026-03-29 | 新增分析前缓存检查机制（Step 0.1-0.3） |
| V3.3.1 | 2026-03-29 | 修正PE(TTM)计算（TTM EPS公式） |
| V3.3 | 2026-03-29 | 业绩预告分离分析、基本面仅用正式财报 |
| V3.2 | 2026-03-29 | 新增事件驱动分析、概念强度量化、六维度评分 |

---

## V3.5 核心变更说明

### 🎉 五大模块升级

| Phase | 模块 | 新增内容 |
|-------|------|----------|
| Phase 1 | 财务趋势分析 | 多期对比，趋势评分（-19~+19分） |
| Phase 2 | 评分置信度 | 三维度评估（完整度+时效性+一致性） |
| Phase 3 | 同行估值对比 | PE相对评分、PB-ROE匹配分析 |
| Phase 4 | 五维风险分解 | 财务/估值/行业/技术/流动性风险量化 |
| Phase 5 | 持续跟踪机制 | 评分历史记录、预警检测、心跳集成 |

### 新增步骤

- **Step 3** 新增"财务趋势分析"子步骤
- **Step 5** 新增"同行估值对比"子步骤
- **Step 7** 新增"五维风险分解"子步骤
- **Step 8** 新增"评分置信度"子步骤
- **Step 9** 新增"持续跟踪记录"步骤
- 原 Step 9 改为 Step 10

---

*最后更新: 2026-03-30*
*版本: V3.5*