"""
NL2SQL 引擎测试
"""

import pytest
from src.nl2sql.engine import (
    NL2SQLEngine,
    DatabaseSchema,
    TableInfo,
    ColumnInfo,
    SQLQueryResult,
)


class TestNL2SQLEngine:
    """NL2SQL 引擎测试类"""

    def test_database_schema_to_prompt(self):
        """测试 Schema 转换为 Prompt"""
        schema = DatabaseSchema(
            tables=[
                TableInfo(
                    name="users",
                    description="用户表",
                    columns=[
                        ColumnInfo(
                            name="id",
                            data_type="INT",
                            description="用户ID",
                            is_primary_key=True,
                        ),
                        ColumnInfo(
                            name="username",
                            data_type="VARCHAR(50)",
                            description="用户名",
                        ),
                    ],
                )
            ]
        )

        prompt = schema.to_prompt()

        assert "users" in prompt
        assert "用户表" in prompt
        assert "id" in prompt
        assert "username" in prompt
        assert "主键" in prompt

    def test_generate_sql_sync_query_users(self):
        """测试同步生成 SQL - 查询用户"""
        engine = NL2SQLEngine()

        schema = DatabaseSchema(
            tables=[
                TableInfo(
                    name="users",
                    description="用户表",
                    columns=[
                        ColumnInfo(name="id", data_type="INT"),
                        ColumnInfo(name="username", data_type="VARCHAR(50)"),
                    ],
                )
            ]
        )

        result = engine.generate_sql_sync("查询所有用户", schema)

        assert result.sql != ""
        assert "users" in result.sql
        assert result.confidence > 0

    def test_generate_sql_sync_query_workflows(self):
        """测试同步生成 SQL - 查询工作流"""
        engine = NL2SQLEngine()

        schema = DatabaseSchema(
            tables=[
                TableInfo(
                    name="workflows",
                    description="工作流表",
                    columns=[
                        ColumnInfo(name="id", data_type="INT"),
                        ColumnInfo(name="name", data_type="VARCHAR(100)"),
                    ],
                )
            ]
        )

        result = engine.generate_sql_sync("查看所有工作流", schema)

        assert result.sql != ""
        assert "workflows" in result.sql

    def test_generate_sql_sync_statistics(self):
        """测试同步生成 SQL - 统计"""
        engine = NL2SQLEngine()

        schema = DatabaseSchema(
            tables=[
                TableInfo(
                    name="users",
                    description="用户表",
                    columns=[
                        ColumnInfo(name="id", data_type="INT"),
                    ],
                )
            ]
        )

        result = engine.generate_sql_sync("统计用户数量", schema)

        assert result.sql != ""
        assert "COUNT" in result.sql.upper()

    def test_generate_sql_sync_unknown(self):
        """测试同步生成 SQL - 未知问题"""
        engine = NL2SQLEngine()

        schema = DatabaseSchema(tables=[])

        result = engine.generate_sql_sync("今天天气怎么样", schema)

        assert result.sql == ""
        assert result.confidence == 0.0


class TestSQLQueryResult:
    """SQL 查询结果测试类"""

    def test_sql_query_result_model(self):
        """测试 SQLQueryResult 模型"""
        result = SQLQueryResult(
            sql="SELECT * FROM users",
            explanation="查询所有用户",
            confidence=0.9,
            tables_used=["users"],
        )

        assert result.sql == "SELECT * FROM users"
        assert result.confidence == 0.9
        assert "users" in result.tables_used
