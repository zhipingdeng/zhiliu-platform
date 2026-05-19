"""
决策支持引擎模块

提供多源数据融合、风险评估、方案推荐等决策支持功能。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum
import json


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    """决策类型"""
    INVESTMENT = "investment"       # 投资决策
    HIRING = "hiring"               # 招聘决策
    PROJECT = "project"             # 项目决策
    BUDGET = "budget"               # 预算决策
    STRATEGY = "strategy"           # 战略决策


@dataclass
class RiskFactor:
    """风险因素"""
    name: str
    description: str
    probability: float  # 0.0-1.0
    impact: float       # 0.0-1.0
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass
class DecisionOption:
    """决策选项"""
    id: str
    name: str
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[RiskFactor] = field(default_factory=list)
    score: float = 0.0
    estimated_cost: float = 0.0
    estimated_benefit: float = 0.0


class DecisionRequest(BaseModel):
    """决策请求"""
    decision_type: DecisionType = Field(description="决策类型")
    title: str = Field(description="决策标题")
    description: str = Field(description="决策描述")
    context: Dict[str, Any] = Field(default_factory=dict, description="决策上下文")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    options: List[Dict[str, Any]] = Field(default_factory=list, description="可选方案")


class DecisionResult(BaseModel):
    """决策结果"""
    recommended_option: str = Field(description="推荐选项")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    analysis: str = Field(description="分析说明")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="风险评估")
    options_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="方案对比")


# 决策分析 Prompt 模板
DECISION_ANALYSIS_PROMPT = """你是一个专业的决策分析专家。请根据提供的决策信息，分析各个选项并给出推荐。

## 决策信息

- 类型: {decision_type}
- 标题: {title}
- 描述: {description}
- 上下文: {context}
- 约束条件: {constraints}

## 可选方案

{options}

## 分析要求

1. 分析每个选项的优缺点
2. 评估每个选项的风险
3. 基于约束条件进行筛选
4. 给出明确的推荐和理由
5. 使用数据和逻辑支持分析

## 输出格式

请以 JSON 格式输出，包含以下字段：
- recommended_option: 推荐选项的 ID
- confidence: 置信度（0.0-1.0）
- analysis: 详细分析说明
- risk_assessment: 风险评估（包含 overall_risk_level 和 risk_factors）
- options_comparison: 选项对比列表

## 分析结果

请输出 JSON 格式的结果："""


class DecisionEngine:
    """决策支持引擎"""

    def __init__(self, llm_client=None, rag_service=None):
        from src.llm.client import get_llm_client
        self.llm_client = llm_client or get_llm_client()
        self.rag_service = rag_service

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
        # 格式化选项信息
        options_text = ""
        for i, option in enumerate(request.options, 1):
            options_text += f"\n### 选项 {i}: {option.get('name', '未命名')}\n"
            options_text += f"描述: {option.get('description', '')}\n"
            if option.get('pros'):
                options_text += f"优点: {', '.join(option['pros'])}\n"
            if option.get('cons'):
                options_text += f"缺点: {', '.join(option['cons'])}\n"
            if option.get('estimated_cost'):
                options_text += f"预估成本: {option['estimated_cost']}\n"
            if option.get('estimated_benefit'):
                options_text += f"预估收益: {option['estimated_benefit']}\n"

        # 构建 Prompt
        prompt = DECISION_ANALYSIS_PROMPT.format(
            decision_type=request.decision_type.value,
            title=request.title,
            description=request.description,
            context=json.dumps(request.context, ensure_ascii=False),
            constraints=", ".join(request.constraints) if request.constraints else "无",
            options=options_text if options_text else "无",
        )

        # 检索相关知识（如果有 RAG 服务）
        context = ""
        if self.rag_service:
            retrieval_result = await self.rag_service.retriever.retrieve(
                f"{request.title} {request.description}", top_k=3
            )
            if retrieval_result.documents:
                context = "\n\n## 相关知识\n\n"
                for doc in retrieval_result.documents:
                    context += f"- {doc.content[:200]}...\n"

        # 调用 LLM 分析
        messages = [
            {"role": "system", "content": "你是一个专业的决策分析专家。"},
            {"role": "user", "content": prompt + context},
        ]

        response = await self.llm_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        try:
            result = json.loads(response)
            return DecisionResult(
                recommended_option=result.get("recommended_option", ""),
                confidence=float(result.get("confidence", 0.0)),
                analysis=result.get("analysis", ""),
                risk_assessment=result.get("risk_assessment", {}),
                options_comparison=result.get("options_comparison", []),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return DecisionResult(
                recommended_option="",
                confidence=0.0,
                analysis="决策分析失败，请重试。",
                risk_assessment={},
                options_comparison=[],
            )

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
        prompt = f"""请对以下决策进行风险评估。

## 决策类型

{decision_type.value}

## 上下文信息

{json.dumps(context, ensure_ascii=False)}

## 评估要求

1. 识别主要风险因素
2. 评估每个风险的概率和影响
3. 计算整体风险等级
4. 提供应对建议

## 输出格式

请以 JSON 格式输出，包含以下字段：
- overall_risk_level: 整体风险等级（low/medium/high/critical）
- risk_factors: 风险因素列表
- mitigation_strategies: 应对策略列表

## 风险评估

请输出 JSON 格式的结果："""

        messages = [
            {"role": "system", "content": "你是一个专业的风险评估专家。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        try:
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            return {
                "overall_risk_level": "medium",
                "risk_factors": [],
                "mitigation_strategies": [],
            }

    def analyze_decision_sync(
        self, request: DecisionRequest
    ) -> DecisionResult:
        """
        同步分析决策（用于测试，基于规则）

        Args:
            request: 决策请求

        Returns:
            决策结果
        """
        if not request.options:
            return DecisionResult(
                recommended_option="",
                confidence=0.0,
                analysis="没有可选方案",
                risk_assessment={},
                options_comparison=[],
            )

        # 简单的规则：选择成本最低或收益最高的选项
        best_option = None
        best_score = float('-inf')

        for option in request.options:
            cost = option.get('estimated_cost', 0)
            benefit = option.get('estimated_benefit', 0)
            score = benefit - cost

            if score > best_score:
                best_score = score
                best_option = option

        if best_option:
            return DecisionResult(
                recommended_option=best_option.get('id', ''),
                confidence=0.7,
                analysis=f"基于成本收益分析，推荐 {best_option.get('name', '')}",
                risk_assessment={"overall_risk_level": "medium"},
                options_comparison=[
                    {
                        "id": opt.get('id', ''),
                        "name": opt.get('name', ''),
                        "score": opt.get('estimated_benefit', 0) - opt.get('estimated_cost', 0),
                    }
                    for opt in request.options
                ],
            )

        return DecisionResult(
            recommended_option=request.options[0].get('id', '') if request.options else "",
            confidence=0.5,
            analysis="默认选择第一个选项",
            risk_assessment={},
            options_comparison=[],
        )
