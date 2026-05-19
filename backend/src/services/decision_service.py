"""
决策支持服务模块

提供决策分析、风险评估等业务逻辑。
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.decision.engine import (
    DecisionEngine,
    DecisionRequest,
    DecisionResult,
    DecisionType,
)
from src.rag.retriever import RAGService


class DecisionService:
    """决策支持服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag_service = RAGService()
        self.decision_engine = DecisionEngine(rag_service=self.rag_service)

    async def analyze_decision(
        self, request: DecisionRequest
    ) -> DecisionResult:
        """
        分析决策

        Args:
            request: 决策请求

        Returns:
            决策结果
        """
        return await self.decision_engine.analyze_decision(request)

    async def assess_risk(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        风险评估

        Args:
            decision_type: 决策类型
            context: 上下文信息

        Returns:
            风险评估结果
        """
        return await self.decision_engine.assess_risk(decision_type, context)

    async def add_knowledge(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """
        添加知识到知识库

        Args:
            documents: 文档列表

        Returns:
            文档 ID 列表
        """
        return await self.rag_service.add_documents(documents)

    async def query_knowledge(
        self,
        question: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        查询知识库

        Args:
            question: 用户问题
            top_k: 返回数量

        Returns:
            查询结果
        """
        return await self.rag_service.query(question, top_k=top_k)
