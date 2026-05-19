"""
RAG 检索测试
"""

import pytest
import pytest_asyncio
from src.rag.retriever import (
    Document,
    InMemoryVectorStore,
    HybridRetriever,
    RAGService,
)


@pytest.mark.asyncio
class TestInMemoryVectorStore:
    """内存向量存储测试类"""

    async def test_add_documents(self):
        """测试添加文档"""
        store = InMemoryVectorStore()

        documents = [
            Document(
                id="doc1",
                content="这是第一个文档",
                metadata={"type": "test"},
                source="test",
            ),
            Document(
                id="doc2",
                content="这是第二个文档",
                metadata={"type": "test"},
                source="test",
            ),
        ]

        ids = await store.add_documents(documents)

        assert len(ids) == 2
        assert "doc1" in ids
        assert "doc2" in ids
        assert len(store.documents) == 2

    async def test_search(self):
        """测试搜索"""
        store = InMemoryVectorStore()

        documents = [
            Document(
                id="doc1",
                content="Python 是一种编程语言",
                metadata={"type": "tech"},
                source="wiki",
            ),
            Document(
                id="doc2",
                content="Java 也是一种编程语言",
                metadata={"type": "tech"},
                source="wiki",
            ),
            Document(
                id="doc3",
                content="今天天气很好",
                metadata={"type": "weather"},
                source="news",
            ),
        ]

        await store.add_documents(documents)

        # 搜索编程相关
        results = await store.search("Python 编程", top_k=2)

        assert len(results) > 0
        assert any("Python" in doc.content for doc in results)

    async def test_delete(self):
        """测试删除"""
        store = InMemoryVectorStore()

        documents = [
            Document(id="doc1", content="test1", source="test"),
            Document(id="doc2", content="test2", source="test"),
        ]

        await store.add_documents(documents)
        assert len(store.documents) == 2

        result = await store.delete(["doc1"])
        assert result is True
        assert len(store.documents) == 1
        assert "doc1" not in store.documents


@pytest.mark.asyncio
class TestHybridRetriever:
    """混合检索器测试类"""

    async def test_retrieve(self):
        """测试检索"""
        store = InMemoryVectorStore()
        retriever = HybridRetriever(vector_store=store)

        documents = [
            Document(
                id="doc1",
                content="企业流程自动化",
                metadata={"category": "workflow"},
                source="docs",
            ),
            Document(
                id="doc2",
                content="数据分析平台",
                metadata={"category": "analytics"},
                source="docs",
            ),
        ]

        await store.add_documents(documents)

        result = await retriever.retrieve("流程自动化", top_k=2)

        assert result.query == "流程自动化"
        assert result.total > 0
        assert len(result.documents) > 0

    async def test_retrieve_with_filters(self):
        """测试带过滤的检索"""
        store = InMemoryVectorStore()
        retriever = HybridRetriever(vector_store=store)

        documents = [
            Document(
                id="doc1",
                content="工作流引擎",
                metadata={"category": "workflow"},
                source="docs",
            ),
            Document(
                id="doc2",
                content="数据分析",
                metadata={"category": "analytics"},
                source="docs",
            ),
        ]

        await store.add_documents(documents)

        # 只检索 workflow 类别
        result = await retriever.retrieve(
            "工作流", top_k=5, filters={"category": "workflow"}
        )

        for doc in result.documents:
            assert doc.metadata.get("category") == "workflow"


@pytest.mark.asyncio
class TestRAGService:
    """RAG 服务测试类"""

    async def test_add_documents(self):
        """测试添加文档"""
        service = RAGService()

        documents = [
            {
                "id": "doc1",
                "content": "智流平台是一个企业级智能流程自动化系统",
                "metadata": {"type": "intro"},
                "source": "docs",
            },
        ]

        ids = await service.add_documents(documents)

        assert len(ids) == 1
        assert "doc1" in ids
