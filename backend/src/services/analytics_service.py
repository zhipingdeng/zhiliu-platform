"""
数据分析服务模块

提供数据查询、分析、报告生成等业务逻辑。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.nl2sql.engine import NL2SQLEngine, DatabaseSchema, TableInfo, ColumnInfo


class AnalyticsService:
    """数据分析服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.nl2sql_engine = NL2SQLEngine()

    async def get_database_schema(self) -> DatabaseSchema:
        """
        获取数据库 Schema

        Returns:
            数据库 Schema 信息
        """
        # 查询所有表
        result = await self.db.execute(
            text("SELECT table_name, table_comment FROM information_schema.tables WHERE table_schema = DATABASE()")
        )
        tables_data = result.fetchall()

        tables = []
        for table_name, table_comment in tables_data:
            # 查询列信息
            col_result = await self.db.execute(
                text(f"""
                    SELECT column_name, data_type, column_comment,
                           column_key, column_type
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"table_name": table_name}
            )
            columns_data = col_result.fetchall()

            columns = []
            for col_name, col_type, col_comment, col_key, full_type in columns_data:
                is_pk = col_key == "PRI"
                columns.append(ColumnInfo(
                    name=col_name,
                    data_type=full_type or col_type,
                    description=col_comment or "",
                    is_primary_key=is_pk,
                ))

            tables.append(TableInfo(
                name=table_name,
                description=table_comment or "",
                columns=columns,
            ))

        return DatabaseSchema(tables=tables)

    async def query_with_nl(self, question: str) -> Dict[str, Any]:
        """
        使用自然语言查询数据

        Args:
            question: 自然语言问题

        Returns:
            查询结果
        """
        # 获取 Schema
        schema = await self.get_database_schema()

        # 生成 SQL
        sql_result = await self.nl2sql_engine.generate_sql(question, schema)

        if not sql_result.sql:
            return {
                "success": False,
                "error": "无法生成 SQL 查询",
                "sql": "",
                "data": [],
                "columns": [],
            }

        try:
            # 执行 SQL
            result = await self.db.execute(text(sql_result.sql))
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []

            # 转换为字典列表
            data = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "sql": sql_result.sql,
                "explanation": sql_result.explanation,
                "confidence": sql_result.confidence,
                "data": data,
                "columns": columns,
                "row_count": len(data),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql_result.sql,
                "data": [],
                "columns": [],
            }

    async def generate_report(
        self,
        topic: str,
        data: List[Dict[str, Any]],
    ) -> str:
        """
        生成分析报告

        Args:
            topic: 报告主题
            data: 数据

        Returns:
            报告内容（Markdown 格式）
        """
        prompt = f"""请根据以下数据生成一份分析报告。

## 报告主题

{topic}

## 数据

```json
{data[:100]}  # 限制数据量
```

## 报告要求

1. 使用 Markdown 格式
2. 包含数据概览、关键发现、趋势分析、建议
3. 使用表格展示关键数据
4. 语言简洁专业

## 报告内容

请生成完整的分析报告："""

        from src.llm.client import get_llm_client
        llm_client = get_llm_client()

        messages = [
            {"role": "system", "content": "你是一个专业的数据分析师。"},
            {"role": "user", "content": prompt},
        ]

        report = await llm_client.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=2000,
        )

        return report

    async def get_trend_analysis(
        self,
        table: str,
        date_column: str,
        value_column: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        获取趋势分析

        Args:
            table: 表名
            date_column: 日期列
            value_column: 值列
            days: 天数

        Returns:
            趋势分析结果
        """
        sql = f"""
            SELECT DATE({date_column}) as date, 
                   COUNT(*) as count,
                   AVG({value_column}) as avg_value,
                   MIN({value_column}) as min_value,
                   MAX({value_column}) as max_value
            FROM {table}
            WHERE {date_column} >= DATE_SUB(NOW(), INTERVAL {days} DAY)
            GROUP BY DATE({date_column})
            ORDER BY date
        """

        try:
            result = await self.db.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []

            data = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "data": data,
                "columns": columns,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": [],
            }
