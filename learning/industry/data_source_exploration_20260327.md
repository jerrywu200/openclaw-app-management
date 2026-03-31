# 装机数据/招标数据/行业研报获取方式探索报告

> 探索日期: 2026-03-27
> 目标: 找到可行的数据获取方案

---

## 一、探索结果汇总

### 1. 装机数据

| 方案 | 结果 | 说明 |
|------|------|------|
| akshare | ❌ 无直接接口 | 无装机数据 |
| web_search | ❌ bot检测 | DuckDuckGo触发验证 |
| web_fetch | ❌ 反爬机制 | 政府网站403/404 |
| efinance | ❌ 无直接接口 | 无装机数据 |

**结论**: 装机数据无法自动获取，需人工录入

### 2. 招标数据

| 方案 | 结果 | 说明 |
|------|------|------|
| akshare | ❌ 无接口 | 无招标数据 |
| web_search | ❌ bot检测 | - |
| 招标平台 | ⚠️ 需登录 | 中国电力招标网等需账号 |

**结论**: 招标数据无法自动获取，需人工跟踪

### 3. 行业研报

| 方案 | 结果 | 数据量 | 说明 |
|------|------|--------|------|
| akshare - 研报快讯 | ✅ 可用 | 100条 | stock_news_main_cx() |
| akshare - 公司新闻 | ✅ 可用 | - | stock_news_em() |
| akshare - 业绩预告 | ✅ 可用 | 2387条 | stock_yjyg_em() |
| efinance - 业绩数据 | ✅ 可用 | 527条 | get_all_company_performance() |
| efinance - 龙虎榜 | ✅ 可用 | 33条 | get_daily_billboard() |
| 完整券商研报 | ❌ 需账号 | - | Wind/iFinD等 |

**结论**: 部分研报相关数据可用，完整研报需付费服务

---

## 二、可用数据源清单

### akshare 可用接口

| 数据类型 | 函数 | 状态 | 用途 |
|----------|------|------|------|
| 行业板块列表 | stock_board_industry_name_em() | ✅ | 行业分类 |
| 概念板块列表 | stock_board_concept_name_em() | ✅ | 概念分类 |
| 概念板块成分股 | stock_board_concept_cons_em() | ✅ | 板块股票 |
| 概念板块行情 | stock_board_concept_hist_em() | ✅ | 板块走势 |
| 能源指数 | macro_china_energy_index() | ✅ | 能源趋势 |
| 研报快讯 | stock_news_main_cx() | ✅ | 研报动态 |
| 公司新闻 | stock_news_em() | ✅ | 公司动态 |
| 业绩预告 | stock_yjyg_em() | ✅ | 业绩预期 |
| 财务报告 | stock_financial_report_sina() | ✅ | 财务数据 |

### efinance 可用接口

| 数据类型 | 函数 | 状态 | 用途 |
|----------|------|------|------|
| 股票行情 | get_quote_history() | ✅ | K线数据 |
| 股票所属板块 | get_belong_board() | ✅ | 板块归属 |
| 龙虎榜 | get_daily_billboard() | ✅ | 机构行为 |
| 业绩数据 | get_all_company_performance() | ✅ | 业绩汇总 |
| IPO信息 | get_latest_ipo_info() | ✅ | 新股动态 |
| 十大股东 | get_top10_stock_holder_info() | ✅ | 股东结构 |

---

## 三、推荐方案

### 短期方案（当前可用）

```python
# 1. 使用akshare获取板块和新闻数据
import akshare as ak

# 板块数据
wind_stocks = ak.stock_board_concept_cons_em(symbol="风能")
wind_kline = ak.stock_board_concept_hist_em(symbol="风能", ...)

# 新闻数据
company_news = ak.stock_news_em(symbol="中际联合")
research_news = ak.stock_news_main_cx()

# 2. 使用efinance获取补充数据
import efinance as ef

# 股票所属板块
boards = ef.stock.get_belong_board('605305')

# 龙虎榜
billboard = ef.stock.get_daily_billboard()
```

### 中期方案（需建立机制）

1. **装机数据**
   - 定期人工录入国家能源局月度数据
   - 存储到本地数据库
   - 更新频率: 每月

2. **招标数据**
   - 建立重点公司招标跟踪表
   - 人工录入重要招标信息
   - 更新频率: 每周

### 长期方案（专业服务）

| 数据源 | 费用 | 特点 |
|--------|------|------|
| Wind | 高 | 专业、全面 |
| 同花顺iFinD | 中 | 性价比好 |
| 东方财富Choice | 中 | 数据丰富 |
| 聚宽JQData | 低 | 量化友好 |

---

## 四、数据获取代码模板

```python
# industry_data_collector.py
import akshare as ak
import efinance as ef
import pandas as pd
from datetime import datetime

class IndustryDataCollector:
    """行业数据收集器"""
    
    def __init__(self):
        self.update_time = datetime.now()
    
    def get_wind_power_stocks(self):
        """获取风能板块成分股"""
        return ak.stock_board_concept_cons_em(symbol="风能")
    
    def get_wind_power_kline(self, start_date="20260101"):
        """获取风能板块K线"""
        return ak.stock_board_concept_hist_em(
            symbol="风能",
            period="daily",
            start_date=start_date,
            end_date=datetime.now().strftime("%Y%m%d")
        )
    
    def get_company_news(self, symbol):
        """获取公司新闻"""
        return ak.stock_news_em(symbol=symbol)
    
    def get_research_news(self):
        """获取研报快讯"""
        return ak.stock_news_main_cx()
    
    def get_company_boards(self, code):
        """获取公司所属板块"""
        return ef.stock.get_belong_board(code)
    
    def get_billboard(self):
        """获取龙虎榜"""
        return ef.stock.get_daily_billboard()
    
    def get_performance(self):
        """获取业绩数据"""
        return ef.stock.get_all_company_performance()

# 使用示例
collector = IndustryDataCollector()
print(collector.get_wind_power_stocks())
```

---

## 五、结论

| 数据类型 | 可获取性 | 方案 |
|----------|----------|------|
| 装机数据 | ❌ 不可自动获取 | 人工录入 |
| 招标数据 | ❌ 不可自动获取 | 人工跟踪 |
| 行业研报 | ⚠️ 部分可用 | akshare + efinance |
| 板块数据 | ✅ 可获取 | akshare |
| 公司新闻 | ✅ 可获取 | akshare |
| 龙虎榜 | ✅ 可获取 | efinance |

---

*探索完成时间: 2026-03-27*