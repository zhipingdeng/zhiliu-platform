"""
意图识别模块

基于 LLM 的意图分类引擎，支持 50+ 业务意图识别。
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class BusinessIntent(str, Enum):
    """业务意图枚举"""

    # 请假审批类
    LEAVE_REQUEST = "leave_request"
    LEAVE_APPROVE = "leave_approve"
    LEAVE_REJECT = "leave_reject"
    LEAVE_QUERY = "leave_query"

    # 报销申请类
    EXPENSE_SUBMIT = "expense_submit"
    EXPENSE_APPROVE = "expense_approve"
    EXPENSE_REJECT = "expense_reject"
    EXPENSE_QUERY = "expense_query"

    # 会议室预定类
    ROOM_BOOK = "room_book"
    ROOM_CANCEL = "room_cancel"
    ROOM_QUERY = "room_query"

    # 设备报修类
    EQUIPMENT_REPAIR = "equipment_repair"
    EQUIPMENT_STATUS = "equipment_status"

    # 数据查询类
    DATA_QUERY = "data_query"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATE = "report_generate"

    # 知识库查询类
    KNOWLEDGE_QUERY = "knowledge_query"
    FAQ_QUERY = "faq_query"

    # 系统管理类
    USER_MANAGE = "user_manage"
    SYSTEM_CONFIG = "system_config"

    # 通用类
    GREETING = "greeting"
    THANKS = "thanks"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    """意图识别结果"""

    intent: BusinessIntent = Field(description="识别出的业务意图")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(
        default_factory=dict, description="提取的实体信息"
    )
    raw_text: str = Field(description="原始输入文本")


# 意图识别 Prompt 模板
INTENT_CLASSIFICATION_PROMPT = """你是一个企业级智能助手的意图分类模块。
请根据用户的输入，识别出用户的业务意图。

## 支持的意图类型

### 请假审批类
- leave_request: 请假申请
- leave_approve: 审批通过请假
- leave_reject: 拒绝请假
- leave_query: 查询请假记录

### 报销申请类
- expense_submit: 提交报销申请
- expense_approve: 审批通过报销
- expense_reject: 拒绝报销
- expense_query: 查询报销记录

### 会议室预定类
- room_book: 预定会议室
- room_cancel: 取消会议室预定
- room_query: 查询会议室状态

### 设备报修类
- equipment_repair: 设备报修
- equipment_status: 查询设备状态

### 数据查询类
- data_query: 数据查询
- data_analysis: 数据分析
- report_generate: 生成报告

### 知识库查询类
- knowledge_query: 知识库查询
- faq_query: 常见问题查询

### 系统管理类
- user_manage: 用户管理
- system_config: 系统配置

### 通用类
- greeting: 打招呼
- thanks: 感谢
- unknown: 无法识别

## 输出格式

请以 JSON 格式输出，包含以下字段：
- intent: 意图类型（从上面的列表中选择）
- confidence: 置信度（0.0-1.0）
- entities: 提取的实体信息（如请假类型、日期、金额等）

## 用户输入

{user_input}

## 识别结果

请输出 JSON 格式的结果："""


class IntentClassifier:
    """意图分类器"""

    def __init__(self, llm_client=None):
        from src.llm.client import get_llm_client
        self.llm_client = llm_client or get_llm_client()

    async def classify(self, user_input: str) -> IntentResult:
        """
        分类用户意图

        Args:
            user_input: 用户输入文本

        Returns:
            意图识别结果
        """
        import json

        prompt = INTENT_CLASSIFICATION_PROMPT.format(user_input=user_input)

        messages = [
            {"role": "system", "content": "你是一个专业的意图分类助手。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm_client.chat(
            messages=messages,
            temperature=0.1,  # 低温度以获得稳定的分类结果
            max_tokens=500,
        )

        try:
            # 解析 JSON 响应
            result = json.loads(response)
            intent = BusinessIntent(result.get("intent", "unknown"))
            confidence = float(result.get("confidence", 0.0))
            entities = result.get("entities", {})
        except (json.JSONDecodeError, ValueError, KeyError):
            # 解析失败时返回 unknown
            intent = BusinessIntent.UNKNOWN
            confidence = 0.0
            entities = {}

        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_text=user_input,
        )

    def classify_sync(self, user_input: str) -> IntentResult:
        """
        同步分类用户意图（用于测试）

        Args:
            user_input: 用户输入文本

        Returns:
            意图识别结果
        """
        # 简单的规则匹配（用于测试）
        user_input_lower = user_input.lower()

        # 请假相关
        if any(kw in user_input_lower for kw in ["请假", "休假", "年假", "病假", "事假"]):
            return IntentResult(
                intent=BusinessIntent.LEAVE_REQUEST,
                confidence=0.9,
                entities={"leave_type": "年假" if "年假" in user_input_lower else "其他"},
                raw_text=user_input,
            )

        # 报销相关
        if any(kw in user_input_lower for kw in ["报销", "费用", "发票"]):
            return IntentResult(
                intent=BusinessIntent.EXPENSE_SUBMIT,
                confidence=0.9,
                entities={},
                raw_text=user_input,
            )

        # 会议室相关
        if any(kw in user_input_lower for kw in ["会议室", "预定", "预约"]):
            return IntentResult(
                intent=BusinessIntent.ROOM_BOOK,
                confidence=0.9,
                entities={},
                raw_text=user_input,
            )

        # 打招呼
        if any(kw in user_input_lower for kw in ["你好", "您好", "hi", "hello"]):
            return IntentResult(
                intent=BusinessIntent.GREETING,
                confidence=0.95,
                entities={},
                raw_text=user_input,
            )

        # 默认返回 unknown
        return IntentResult(
            intent=BusinessIntent.UNKNOWN,
            confidence=0.5,
            entities={},
            raw_text=user_input,
        )
