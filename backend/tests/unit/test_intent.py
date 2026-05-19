"""
意图识别测试
"""

import pytest
from src.intent.classifier import IntentClassifier, BusinessIntent, IntentResult


class TestIntentClassifier:
    """意图分类器测试类"""

    def test_classify_leave_request(self):
        """测试识别请假申请"""
        classifier = IntentClassifier()

        result = classifier.classify_sync("我想请假三天")

        assert result.intent == BusinessIntent.LEAVE_REQUEST
        assert result.confidence > 0.5

    def test_classify_expense_submit(self):
        """测试识别报销申请"""
        classifier = IntentClassifier()

        result = classifier.classify_sync("我要报销餐费")

        assert result.intent == BusinessIntent.EXPENSE_SUBMIT
        assert result.confidence > 0.5

    def test_classify_room_book(self):
        """测试识别会议室预定"""
        classifier = IntentClassifier()

        result = classifier.classify_sync("预定一个会议室")

        assert result.intent == BusinessIntent.ROOM_BOOK
        assert result.confidence > 0.5

    def test_classify_greeting(self):
        """测试识别打招呼"""
        classifier = IntentClassifier()

        result = classifier.classify_sync("你好")

        assert result.intent == BusinessIntent.GREETING
        assert result.confidence > 0.5

    def test_classify_unknown(self):
        """测试识别未知意图"""
        classifier = IntentClassifier()

        result = classifier.classify_sync("今天天气怎么样")

        assert result.intent == BusinessIntent.UNKNOWN

    def test_intent_result_model(self):
        """测试 IntentResult 模型"""
        result = IntentResult(
            intent=BusinessIntent.LEAVE_REQUEST,
            confidence=0.9,
            entities={"leave_type": "年假"},
            raw_text="我想请年假",
        )

        assert result.intent == BusinessIntent.LEAVE_REQUEST
        assert result.confidence == 0.9
        assert result.entities["leave_type"] == "年假"
