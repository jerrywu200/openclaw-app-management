"""
股票数据库工具 - 连接stock_db获取K线、分时、财务等数据
数据库: 106.14.194.144 / stock_db
"""

import pymysql
import pandas as pd
from typing import Optional, List
from datetime import datetime, timedelta

# 数据库配置
DB_CONFIG = {
    'host': '106.14.194.144',
    'user': 'root',
    'password': 'MySql@888888',
    'database': 'stock_db',
    'charset': 'utf8mb4',
    'connect_timeout': 10
}


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def normalize_stock_code(stock_code: str, with_suffix: bool = True) -> str:
    """
    标准化股票代码
    
    Args:
        stock_code: 股票代码
        with_suffix: 是否添加交易所后缀（数据库中有些表用纯代码，有些用带后缀）
    
    Returns:
        标准化后的股票代码
    """
    stock_code = str(stock_code).strip()
    
    # 去掉已有后缀
    if '.' in stock_code:
        stock_code = stock_code.split('.')[0]
    
    if with_suffix:
        # 添加交易所后缀
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        else:
            return f"{stock_code}.SZ"
    else:
        # 返回纯代码
        return stock_code


# ============================================================
# 一、核心行情数据
# ============================================================

def get_stock_kline(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 250
) -> pd.DataFrame:
    """
    获取股票K线数据
    
    Args:
        stock_code: 股票代码，如 '605305' 或 '605305.SH'
        start_date: 开始日期，如 '2024-01-01'
        end_date: 结束日期，如 '2024-12-31'
        limit: 返回数据条数，默认250条（约一年）
    
    Returns:
        DataFrame: K线数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if start_date and end_date:
        query = f"""
            SELECT * FROM stock_kline 
            WHERE stock_code = '{stock_code}' 
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date DESC
        """
    else:
        query = f"""
            SELECT * FROM stock_kline 
            WHERE stock_code = '{stock_code}' 
            ORDER BY date DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    if len(df) > 0:
        df = df.sort_values('date').reset_index(drop=True)
    
    return df


def get_stock_time_data(
    stock_code: str,
    trade_date: Optional[str] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    获取股票分时数据
    
    Args:
        stock_code: 股票代码
        trade_date: 交易日期，如 '2024-03-25'，默认最新
        limit: 返回数据条数
    
    Returns:
        DataFrame: 分时数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if trade_date:
        query = f"""
            SELECT * FROM stock_time_data 
            WHERE stock_code = '{stock_code}' 
            AND trade_date = '{trade_date}'
            ORDER BY time
        """
    else:
        query = f"""
            SELECT * FROM stock_time_data 
            WHERE stock_code = '{stock_code}' 
            ORDER BY trade_date DESC, time
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_stock_finance(
    stock_code: str,
    limit: int = 10
) -> pd.DataFrame:
    """
    获取股票财务数据
    
    Args:
        stock_code: 股票代码
        limit: 返回报告期数量
    
    Returns:
        DataFrame: 财务数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_finance 
        WHERE stock_code = '{stock_code}' 
        ORDER BY report_date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    # 解析data_json字段
    if len(df) > 0 and 'data_json' in df.columns:
        import json
        expanded = []
        for _, row in df.iterrows():
            try:
                data = json.loads(row['data_json'])
                data['stock_code'] = row['stock_code']
                data['report_date'] = row['report_date']
                expanded.append(data)
            except:
                pass
        if expanded:
            df = pd.DataFrame(expanded)
    
    return df


def get_stock_fund_flow(
    stock_code: str,
    limit: int = 60
) -> pd.DataFrame:
    """
    获取股票资金流向数据
    
    Args:
        stock_code: 股票代码
        limit: 返回天数
    
    Returns:
        DataFrame: 资金流向数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_fund_flow 
        WHERE stock_code = '{stock_code}' 
        ORDER BY date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_stock_highest_lowest_price(stock_code: str) -> pd.DataFrame:
    """
    获取股票历史最高最低价
    
    Args:
        stock_code: 股票代码
    
    Returns:
        DataFrame: 历史最高最低价数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_highest_lowest_price 
        WHERE stock_code = '{stock_code}'
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 二、龙虎榜数据
# ============================================================

def get_dragon_tiger(
    stock_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    获取龙虎榜数据
    
    Args:
        stock_code: 股票代码（可选）
        trade_date: 交易日期（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 龙虎榜数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    if stock_code:
        stock_code = normalize_stock_code(stock_code)
        conditions.append(f"stock_code = '{stock_code}'")
    if trade_date:
        conditions.append(f"trade_date = '{trade_date}'")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT * FROM stock_dragon_tiger 
        WHERE {where_clause}
        ORDER BY trade_date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 三、委托单数据
# ============================================================

def get_order_book(
    stock_code: str,
    trade_date: Optional[str] = None,
    limit: int = 10
) -> pd.DataFrame:
    """
    获取股票五档盘口数据
    
    Args:
        stock_code: 股票代码
        trade_date: 交易日期（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 五档盘口数据
    """
    stock_code = normalize_stock_code(stock_code)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if trade_date:
        query = f"""
            SELECT * FROM stock_order_book 
            WHERE stock_code = '{stock_code}' 
            AND trade_date = '{trade_date}'
        """
    else:
        query = f"""
            SELECT * FROM stock_order_book 
            WHERE stock_code = '{stock_code}' 
            ORDER BY trade_date DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 四、概念板块数据
# ============================================================

def get_concept_board_list(limit: int = 500) -> pd.DataFrame:
    """
    获取概念板块列表
    
    Args:
        limit: 返回条数
    
    Returns:
        DataFrame: 概念板块列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_concept_board 
        ORDER BY market_strength_score DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_concept_board_stocks(board_code: str) -> pd.DataFrame:
    """
    获取概念板块成分股
    
    Args:
        board_code: 板块代码
    
    Returns:
        DataFrame: 板块成分股列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_concept_board_stock 
        WHERE board_code = '{board_code}'
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_concept_kline(
    board_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 250
) -> pd.DataFrame:
    """
    获取概念板块K线数据
    
    Args:
        board_code: 板块代码
        start_date: 开始日期
        end_date: 结束日期
        limit: 返回数据条数
    
    Returns:
        DataFrame: 板块K线数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if start_date and end_date:
        query = f"""
            SELECT * FROM concept_board_kline 
            WHERE board_code = '{board_code}' 
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date DESC
        """
    else:
        query = f"""
            SELECT * FROM concept_board_kline 
            WHERE board_code = '{board_code}' 
            ORDER BY date DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    if len(df) > 0:
        df = df.sort_values('date').reset_index(drop=True)
    
    return df


def get_concept_strength(
    stock_code: Optional[str] = None,
    board_code: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    获取股票概念强度数据
    
    Args:
        stock_code: 股票代码（可选）
        board_code: 板块代码（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 概念强度数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    if stock_code:
        # 概念强度表使用不带后缀的代码
        stock_code = normalize_stock_code(stock_code, with_suffix=False)
        conditions.append(f"stock_code = '{stock_code}'")
    if board_code:
        conditions.append(f"board_code = '{board_code}'")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT * FROM stock_concept_strength 
        WHERE {where_clause}
        ORDER BY strength_score DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 五、全球指数数据
# ============================================================

def get_global_index(region: Optional[str] = None) -> pd.DataFrame:
    """
    获取全球指数实时数据
    
    Args:
        region: 区域筛选（americas/europe/asia/australia）
    
    Returns:
        DataFrame: 全球指数数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if region:
        query = f"""
            SELECT * FROM global_index_realtime 
            WHERE region = '{region}'
            ORDER BY index_name
        """
    else:
        query = """
            SELECT * FROM global_index_realtime 
            ORDER BY region, index_name
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_us_index_kline(
    index_code: str,
    limit: int = 250
) -> pd.DataFrame:
    """
    获取美股指数K线数据
    
    Args:
        index_code: 指数代码
        limit: 返回数据条数
    
    Returns:
        DataFrame: 美股指数K线数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM us_index_kline 
        WHERE index_code = '{index_code}' 
        ORDER BY trade_date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    if len(df) > 0:
        df = df.sort_values('trade_date').reset_index(drop=True)
    
    return df


# ============================================================
# 六、美股数据
# ============================================================

def get_us_stock_kline(
    stock_code: str,
    limit: int = 250
) -> pd.DataFrame:
    """
    获取美股K线数据
    
    Args:
        stock_code: 美股代码（如 'AAPL', 'TSLA'）
        limit: 返回数据条数
    
    Returns:
        DataFrame: 美股K线数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM us_stock_kline 
        WHERE stock_code = '{stock_code}' 
        ORDER BY trade_date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    if len(df) > 0:
        df = df.sort_values('trade_date').reset_index(drop=True)
    
    return df


def get_us_stock_ranking(
    category: Optional[str] = None,
    trade_date: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    获取美股排行榜
    
    Args:
        category: 分类（可选）
        trade_date: 交易日期（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 美股排行榜数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    if category:
        conditions.append(f"category = '{category}'")
    if trade_date:
        conditions.append(f"trade_date = '{trade_date}'")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT * FROM us_stock_ranking 
        WHERE {where_clause}
        ORDER BY trade_date DESC, change_pct DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 七、预测分析数据
# ============================================================

def get_weekly_prediction(
    stock_code: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    获取股票每周预测数据
    
    Args:
        stock_code: 股票代码（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 每周预测数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if stock_code:
        stock_code = normalize_stock_code(stock_code)
        query = f"""
            SELECT * FROM stock_weekly_prediction 
            WHERE stock_code = '{stock_code}' 
            ORDER BY predict_date DESC 
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT * FROM stock_weekly_prediction 
            ORDER BY predict_date DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_canslim_prediction(limit: int = 50) -> pd.DataFrame:
    """
    获取CANSLIM月度预测数据
    
    Args:
        limit: 返回条数
    
    Returns:
        DataFrame: CANSLIM预测数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM canslim_monthly_prediction 
        ORDER BY predict_date DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 八、技术分析数据
# ============================================================

# ⚠️ 已弃用：技术评分数据过期（2026-03-13），不建议使用
# 技术分析请使用手动计算方式（MACD/KDJ/布林带）
def get_technical_score(
    stock_code: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    [已弃用] 获取股票技术评分数据
    
    ⚠️ 警告：此数据已过期（最新日期2026-03-13），请使用手动计算方式
    
    Args:
        stock_code: 股票代码（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 技术评分数据
    """
    import warnings
    warnings.warn("技术评分数据已过期，建议使用手动计算MACD/KDJ/布林带", DeprecationWarning)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if stock_code:
        stock_code = normalize_stock_code(stock_code)
        query = f"""
            SELECT * FROM stock_batch_technical_score 
            WHERE stock_code = '{stock_code}' 
            ORDER BY created_at DESC 
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT * FROM stock_batch_technical_score 
            ORDER BY total_score DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 九、综合信息
# ============================================================

def get_stock_info(stock_code: str) -> dict:
    """
    获取股票综合信息（K线+财务+资金流向）
    
    Args:
        stock_code: 股票代码
    
    Returns:
        dict: 综合信息
    """
    kline = get_stock_kline(stock_code, limit=1)
    finance = get_stock_finance(stock_code, limit=1)
    fund_flow = get_stock_fund_flow(stock_code, limit=1)
    highest_lowest = get_stock_highest_lowest_price(stock_code)
    
    info = {
        'stock_code': stock_code,
        'kline': kline.to_dict('records')[0] if len(kline) > 0 else None,
        'finance': finance.to_dict('records')[0] if len(finance) > 0 else None,
        'fund_flow': fund_flow.to_dict('records')[0] if len(fund_flow) > 0 else None,
        'highest_lowest': highest_lowest.to_dict('records')[0] if len(highest_lowest) > 0 else None
    }
    
    return info


# ============================================================
# 十、新闻资讯数据
# ============================================================

def get_stock_news(
    stock_code: str,
    news_type: Optional[str] = None,
    limit: int = 50,
    days: int = 365,
    filter_empty_content: bool = True
) -> pd.DataFrame:
    """
    获取股票新闻数据
    
    Args:
        stock_code: 股票代码
        news_type: 新闻类型（event/news/notice/industry/report/forecast/ranking）
        limit: 返回条数（默认50）
        days: 时间范围（默认365天，即最近1年）
        filter_empty_content: 是否过滤空内容（默认True）
    
    Returns:
        DataFrame: 新闻数据
        
    Note:
        - 自动过滤未来日期的新闻
        - 默认只获取最近1年内的新闻
        - 默认过滤掉content为空/nan的新闻
    """
    from datetime import datetime, timedelta
    
    stock_code = normalize_stock_code(stock_code)
    
    # 计算日期范围
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 构建查询条件
    # 1. 日期范围过滤
    # 2. 内容非空过滤（如果启用）
    content_filter = ""
    if filter_empty_content:
        content_filter = "AND content IS NOT NULL AND content != '' AND content != 'nan'"
    
    # 添加日期过滤条件：1. 在指定天数内 2. 不超过今天（排除未来日期）
    if news_type:
        query = f"""
            SELECT * FROM stock_news 
            WHERE stock_code = '{stock_code}' 
            AND news_type = '{news_type}'
            AND publish_date >= '{start_date}'
            AND publish_date <= '{today}'
            {content_filter}
            ORDER BY publish_date DESC, publish_time DESC 
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT * FROM stock_news 
            WHERE stock_code = '{stock_code}' 
            AND publish_date >= '{start_date}'
            AND publish_date <= '{today}'
            {content_filter}
            ORDER BY publish_date DESC, publish_time DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_stock_news_by_date(
    stock_code: str,
    start_date: str,
    end_date: Optional[str] = None,
    limit: int = 50
) -> pd.DataFrame:
    """
    按日期范围获取股票新闻
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期（可选，默认到今天）
        limit: 返回条数
    
    Returns:
        DataFrame: 新闻数据
        
    Note:
        - 自动过滤未来日期的新闻
    """
    from datetime import datetime
    
    stock_code = normalize_stock_code(stock_code)
    
    # 确保结束日期不超过今天
    today = datetime.now().strftime('%Y-%m-%d')
    if end_date is None or end_date > today:
        end_date = today
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 添加日期过滤，确保不超过今天
    query = f"""
        SELECT * FROM stock_news 
        WHERE stock_code = '{stock_code}' 
        AND publish_date BETWEEN '{start_date}' AND '{end_date}'
        AND publish_date <= '{today}'
        ORDER BY publish_date DESC, publish_time DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_industry_news(
    industry: str,
    limit: int = 30,
    days: int = 365
) -> pd.DataFrame:
    """
    获取行业新闻
    
    Args:
        industry: 行业关键词
        limit: 返回条数
        days: 时间范围（默认365天）
    
    Returns:
        DataFrame: 行业新闻数据
        
    Note:
        - 自动过滤未来日期的新闻
        - 默认只获取最近1年内的新闻
    """
    from datetime import datetime, timedelta
    
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT * FROM stock_news 
        WHERE news_type = 'industry'
        AND title LIKE '%{industry}%'
        AND publish_date >= '{start_date}'
        AND publish_date <= '{today}'
        ORDER BY publish_date DESC, publish_time DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 十一、概念板块市场强度数据
# ============================================================

def get_concept_market_strength(
    board_code: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 50
) -> pd.DataFrame:
    """
    获取概念板块市场强度数据
    
    Args:
        board_code: 板块代码（可选）
        min_score: 最低强度分（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: 板块市场强度数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    if board_code:
        conditions.append(f"board_code = '{board_code}'")
    if min_score:
        conditions.append(f"market_strength_score >= {min_score}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT * FROM stock_concept_board 
        WHERE {where_clause}
        ORDER BY market_strength_score DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_hot_concepts(top_n: int = 20) -> pd.DataFrame:
    """
    获取热门概念板块（按市场强度排序）
    
    Args:
        top_n: 返回数量
    
    Returns:
        DataFrame: 热门概念板块
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT board_code, board_name, market_strength_score, 
               market_excess_return, market_board_return
        FROM stock_concept_board 
        ORDER BY market_strength_score DESC 
        LIMIT {top_n}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_stock_concept_detail(
    stock_code: str,
    limit: int = 10
) -> pd.DataFrame:
    """
    获取股票所属概念板块详细信息（含强度评分）
    
    Args:
        stock_code: 股票代码
        limit: 返回条数
    
    Returns:
        DataFrame: 股票概念详情
    """
    # 概念强度表使用不带后缀的代码
    stock_code_pure = normalize_stock_code(stock_code, with_suffix=False)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT scs.*, scb.market_strength_score, scb.market_excess_return
        FROM stock_concept_strength scs
        LEFT JOIN stock_concept_board scb ON scs.board_code = scb.board_code
        WHERE scs.stock_code = '{stock_code_pure}'
        ORDER BY scs.strength_score DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 十二、技术分析扩展数据
# ============================================================

def get_kline_screening(
    min_score: Optional[float] = None,
    score_date: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame:
    """
    获取K线筛选结果
    
    Args:
        min_score: 最低评分（可选）
        score_date: 评分日期（可选）
        limit: 返回条数
    
    Returns:
        DataFrame: K线筛选结果
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    if min_score:
        conditions.append(f"kline_score >= {min_score}")
    if score_date:
        conditions.append(f"screen_date = '{score_date}'")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT * FROM stock_kline_screening_history 
        WHERE {where_clause}
        ORDER BY screen_date DESC, kline_score DESC 
        LIMIT {limit}
    """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


def get_top_technical_stocks(
    score_date: Optional[str] = None,
    min_total_score: float = 50,
    limit: int = 50
) -> pd.DataFrame:
    """
    获取技术评分最高的股票
    
    Args:
        score_date: 评分日期（可选，默认最新）
        min_total_score: 最低总分
        limit: 返回条数
    
    Returns:
        DataFrame: 技术评分靠前股票
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if score_date:
        query = f"""
            SELECT * FROM stock_batch_technical_score 
            WHERE score_date = '{score_date}'
            AND total_score >= {min_total_score}
            ORDER BY total_score DESC 
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT * FROM stock_batch_technical_score 
            WHERE total_score >= {min_total_score}
            ORDER BY score_date DESC, total_score DESC 
            LIMIT {limit}
        """
    
    cursor.execute(query)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    
    cursor.close()
    conn.close()
    
    return df


# ============================================================
# 十三、综合分析数据
# ============================================================

def get_stock_analysis_data(
    stock_code: str,
    kline_days: int = 60
) -> dict:
    """
    获取股票分析所需的全部数据（一站式）
    
    Args:
        stock_code: 股票代码
        kline_days: K线天数
    
    Returns:
        dict: 包含K线、财务、资金流向、概念强度、新闻等数据
    """
    stock_code_normalized = normalize_stock_code(stock_code)
    
    # 获取各类数据
    kline = get_stock_kline(stock_code, limit=kline_days)
    finance = get_stock_finance(stock_code, limit=4)
    fund_flow = get_stock_fund_flow(stock_code, limit=30)
    highest_lowest = get_stock_highest_lowest_price(stock_code)
    concept_detail = get_stock_concept_detail(stock_code, limit=8)
    news = get_stock_news(stock_code, limit=10)
    dragon_tiger = get_dragon_tiger(stock_code=stock_code, limit=5)
    # 注：技术评分数据已过期，技术分析请手动计算MACD/KDJ/布林带
    
    return {
        'stock_code': stock_code_normalized,
        'kline': kline,
        'finance': finance,
        'fund_flow': fund_flow,
        'highest_lowest': highest_lowest.to_dict('records')[0] if len(highest_lowest) > 0 else None,
        'concepts': concept_detail,
        'news': news[['publish_date', 'news_type', 'title']].to_dict('records') if len(news) > 0 else [],
        'dragon_tiger': dragon_tiger.to_dict('records') if len(dragon_tiger) > 0 else []
        # 注：technical_score已移除，请手动计算技术指标
    }


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("股票数据库工具测试")
    print("="*60)
    
    # 测试K线
    print("\n【1. K线数据】")
    df = get_stock_kline('300308', limit=5)
    print(df[['date', 'close_price', 'change_percent']])
    
    # 测试财务
    print("\n【2. 财务数据】")
    df = get_stock_finance('300308', limit=2)
    if len(df) > 0:
        print(df[['report_date', '营业总收入(元)', '归母净利润(元)']])
    
    # 测试龙虎榜
    print("\n【3. 龙虎榜】")
    df = get_dragon_tiger(limit=5)
    print(df[['trade_date', 'stock_code', 'stock_name', 'reason']])
    
    # 测试全球指数
    print("\n【4. 全球指数】")
    df = get_global_index(region='americas')
    print(df[['index_name', 'latest_price', 'change_pct']].head(5))
    
    # 测试概念强度
    print("\n【5. 概念强度】")
    df = get_concept_strength(stock_code='300308', limit=5)
    if len(df) > 0:
        print(df[['board_name', 'strength_score', 'strength_level']])
    else:
        print('无数据')
    
    # 测试新闻
    print("\n【6. 新闻数据】")
    df = get_stock_news('300308', limit=3)
    if len(df) > 0:
        print(df[['publish_date', 'news_type', 'title']])
    
    # 测试热门概念
    print("\n【7. 热门概念板块】")
    df = get_hot_concepts(top_n=5)
    print(df[['board_name', 'market_strength_score']])
    
    # 测试综合数据
    print("\n【8. 综合分析数据】")
    data = get_stock_analysis_data('300308', kline_days=5)
    print(f"K线: {len(data['kline'])}条")
    print(f"财务: {len(data['finance'])}期")
    print(f"概念: {len(data['concepts'])}个")
    print(f"新闻: {len(data['news'])}条")
    
    # 注：技术评分已弃用，技术分析请手动计算MACD/KDJ/布林带
    
    # 🆕 测试事件驱动分析
    print("\n【9. 事件驱动分析】")
    try:
        from event_driven_analysis import calculate_event_score
        event_result = calculate_event_score('300308', days=90)
        print(f"事件评分: {event_result['event_score']}")
        print(f"近期情绪: {event_result['recent_sentiment']}")
        print(f"正面事件: {len(event_result['positive_events'])}个")
        print(f"负面事件: {len(event_result['negative_events'])}个")
    except Exception as e:
        print(f"事件驱动分析模块加载失败: {e}")
    
    # 🆕 测试概念强度分析
    print("\n【10. 概念强度分析】")
    try:
        from concept_strength_analysis import calculate_concept_strength_score, analyze_stock_sector_resonance
        
        # 概念强度评分
        concept_result = calculate_concept_strength_score('300308', limit=10)
        print(f"概念强度评分: {concept_result['concept_score']}")
        print(f"平均强度: {concept_result['avg_strength']}")
        print(f"强势概念: {concept_result.get('strong_count', 0)}个")
        
        # 共振分析
        resonance = analyze_stock_sector_resonance('300308', limit=10)
        print(f"共振评分: {resonance['resonance_score']}")
        print(f"共振等级: {resonance['resonance_level']}")
    except Exception as e:
        print(f"概念强度分析模块加载失败: {e}")