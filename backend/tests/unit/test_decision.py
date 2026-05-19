"""
决策支持引擎测试
"""

import pytest
from src.decision.engine import (
    DecisionEngine,
    DecisionRequest,
    DecisionResult,
    DecisionType,
    RiskLevel,
)


class TestDecisionEngine:
    """决策支持引擎测试类"""

    def test_analyze_decision_sync(self):
        """测试同步决策分析"""
        engine = DecisionEngine()

        request = DecisionRequest(
            decision_type=DecisionType.INVESTMENT,
            title="服务器采购决策",
            description="需要采购新的服务器来支持业务增长",
            options=[
                {
                    "id": "option1",
                    "name": "云服务器",
                    "description": "使用云服务提供商",
                    "estimated_cost": 10000,
                    "estimated_benefit": 50000,
                },
                {
                    "id": "option2",
                    "name": "物理服务器",
                    "description": "购买物理服务器",
                    "estimated_cost": 30000,
                    "estimated_benefit": 60000,
                },
            ],
        )

        result = engine.analyze_decision_sync(request)

        assert result is not None
        assert result.recommended_option != ""
        assert result.confidence > 0
        assert result.analysis != ""

    def test_analyze_decision_sync_no_options(self):
        """测试同步决策分析 - 无选项"""
        engine = DecisionEngine()

        request = DecisionRequest(
            decision_type=DecisionType.INVESTMENT,
            title="测试决策",
            description="测试",
            options=[],
        )

        result = engine.analyze_decision_sync(request)

        assert result.recommended_option == ""
        assert result.confidence == 0.0

    def test_decision_request_model(self):
        """测试 DecisionRequest 模型"""
        request = DecisionRequest(
            decision_type=DecisionType.HIRING,
            title="招聘决策",
            description="需要招聘一名高级工程师",
            context={"department": "技术部", "budget": 500000},
            constraints=["预算有限", "需要3年以上经验"],
            options=[
                {
                    "id": "opt1",
                    "name": "校园招聘",
                    "description": "招聘应届生",
                    "estimated_cost": 200000,
                    "estimated_benefit": 300000,
                },
            ],
        )

        assert request.decision_type == DecisionType.HIRING
        assert request.title == "招聘决策"
        assert len(request.constraints) == 2
        assert len(request.options) == 1

    def test_decision_result_model(self):
        """测试 DecisionResult 模型"""
        result = DecisionResult(
            recommended_option="opt1",
            confidence=0.85,
            analysis="基于成本收益分析...",
            risk_assessment={"overall_risk_level": "low"},
            options_comparison=[
                {"id": "opt1", "name": "选项1", "score": 100},
            ],
        )

        assert result.recommended_option == "opt1"
        assert result.confidence == 0.85
