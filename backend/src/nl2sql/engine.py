"""
NL2SQL 引擎模块

将自然语言问题转换为 SQL 查询语句。
采用 Schema Linking + Chain-of-Thought 两阶段策略。
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import json


@dataclass
class ColumnInfo:
    """列信息"""
    name: str
    data_type: str
    description: str = ""
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None


@dataclass
class TableInfo:
    """表信息"""
    name: str
    description: str = ""
    columns: List[ColumnInfo] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    """数据库 Schema"""
    tables: List[TableInfo] = field(default_factory=list)

    def to_prompt(self) -> str:
        """转换为 Prompt 字符串"""
        lines = ["## 数据库 Schema\n"]

        for table in self.tables:
            lines.append(f"### 表: {table.name}")
            if table.description:
                lines.append(f"描述: {table.description}")
            lines.append("\n列信息:")
            lines.append("| 列名 | 类型 | 描述 |")
            lines.append("|------|------|------|")
            for col in table.columns:
                pk = " (主键)" if col.is_primary_key else ""
                fk = f" (外键 -> {col.foreign_table}.{col.foreign_column})" if col.is_foreign_key else ""
                lines.append(f"| {col.name} | {col.data_type} | {col.description}{pk}{fk} |")
            lines.append("")

        return "\n".join(lines)


class SQLQueryResult(BaseModel):
    """SQL 查询结果"""
    sql: str = Field(description="生成的 SQL 语句")
    explanation: str = Field(description="SQL 解释")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    tables_used: List[str] = Field(default_factory=list, description="使用的表")


# NL2SQL Prompt 模板
NL2SQL_PROMPT = """你是一个专业的 SQL 专家。请根据用户的自然语言问题和数据库 Schema，生成对应的 SQL 查询语句。

{schema}

## 用户问题

{question}

## 生成要求

1. 使用标准 SQL 语法（MySQL 兼容）
2. 只输出 SQL 语句，不要输出其他内容
3. 如果问题不明确，生成最合理的查询
4. 使用表别名提高可读性
5. 添加必要的注释

## 输出格式

请以 JSON 格式输出，包含以下字段：
- sql: 生成的 SQL 语句
- explanation: SQL 的简要解释
- confidence: 置信度（0.0-1.0）
- tables_used: 使用的表名列表

## SQL 查询

请输出 JSON 格式的结果："""


class NL2SQLEngine:
    """NL2SQL 引擎"""

    def __init__(self, llm_client=None):
        from src.llm.client import get_llm_client
        self.llm_client = llm_client or get_llm_client()

    async def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
    ) -> SQLQueryResult:
        """
        生成 SQL 查询

        Args:
            question: 自然语言问题
            database_schema: 数据库 Schema

        Returns:
            SQL 查询结果
        """
        prompt = NL2SQL_PROMPT.format(
            schema=schema.to_prompt(),
            question=question,
        )

        messages = [
            {"role": "system", "content": "你是一个专业的 SQL 专家。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm_client.chat(
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
        )

        try:
            result = json.loads(response)
            return SQLQueryResult(
                sql=result.get("sql", ""),
                explanation=result.get("explanation", ""),
                confidence=float(result.get("confidence", 0.0)),
                tables_used=result.get("tables_used", []),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return SQLQueryResult(
                sql="",
                explanation="Failed to parse LLM response",
                confidence=0.0,
                tables_used=[],
            )

    async def explain_sql(self, sql: str) -> str:
        """
        解释 SQL 语句

        Args:
            sql: SQL 语句

        Returns:
            解释文本
        """
        prompt = f"""请用简洁的中文解释以下 SQL 语句的作用：

```sql
{sql}
```

解释："""

        messages = [
            {"role": "system", "content": "你是一个 SQL 专家。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        return response

    def generate_sql_sync(
        self,
        question: str,
        schema: DatabaseSchema,
    ) -> SQLQueryResult:
        """
        同步生成 SQL（用于测试，基于规则）

        Args:
            question: 自然语言问题
            schema: 数据库 Schema

        Returns:
            SQL 查询结果
        """
        question_lower = question.lower()

        # 简单的规则匹配
        if any(kw in question_lower for kw in ["查询", "查看", "显示", "列出"]):
            # 查询类
            if any(kw in question_lower for kw in ["用户", "员工"]):
                table = "users"
                if schema.tables and any(t.name == "users" for t in schema.tables):
                    return SQLQueryResult(
                        sql="SELECT * FROM users LIMIT 100",
                        explanation="查询所有用户信息",
                        confidence=0.8,
                        tables_used=["users"],
                    )

            if any(kw in question_lower for kw in ["工作流", "流程"]):
                table = "workflows"
                if schema.tables and any(t.name == "workflows" for t in schema.tables):
                    return SQLQueryResult(
                        sql="SELECT * FROM workflows LIMIT 100",
                        explanation="查询所有工作流信息",
                        confidence=0.8,
                        tables_used=["workflows"],
                    )

        if any(kw in question_lower for kw in ["统计", "数量", "总数"]):
            return SQLQueryResult(
                sql="SELECT COUNT(*) as count FROM users",
                explanation="统计用户总数",
                confidence=0.7,
                tables_used=["users"],
            )

        # 默认返回空
        return SQLQueryResult(
            sql="",
            explanation="无法解析问题",
            confidence=0.0,
            tables_used=[],
        )
