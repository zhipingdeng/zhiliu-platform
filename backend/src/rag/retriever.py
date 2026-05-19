"""
RAG 检索模块

实现三路混合检索策略：
1. 向量检索（语义相似度）
2. BM25 检索（关键词匹配）
3. 知识图谱检索（实体关系）
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import json


@dataclass
class Document:
    """文档片段"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    source: str = ""


class RetrievalResult(BaseModel):
    """检索结果"""
    query: str = Field(description="查询文本")
    documents: List[Document] = Field(default_factory=list, description="检索到的文档")
    total: int = Field(default=0, description="总文档数")


class VectorStore:
    """向量存储基类"""

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档

        Args:
            documents: 文档列表

        Returns:
            文档 ID 列表
        """
        raise NotImplementedError

    async def search(
        self, query: str, top_k: int = 5
    ) -> List[Document]:
        """
        搜索相似文档

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            文档列表
        """
        raise NotImplementedError

    async def delete(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 文档 ID 列表

        Returns:
            是否成功
        """
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """内存向量存储（用于测试）"""

    def __init__(self):
        self.documents: Dict[str, Document] = {}

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        ids = []
        for doc in documents:
            self.documents[doc.id] = doc
            ids.append(doc.id)
        return ids

    async def search(
        self, query: str, top_k: int = 5
    ) -> List[Document]:
        """搜索相似文档（简单关键词匹配）"""
        query_lower = query.lower()
        results = []

        for doc in self.documents.values():
            # 简单的关键词匹配
            content_lower = doc.content.lower()
            if query_lower in content_lower:
                score = 1.0
            else:
                # 计算关键词重叠度
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                overlap = len(query_words & content_words)
                score = overlap / max(len(query_words), 1)

            if score > 0:
                results.append(Document(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    score=score,
                    source=doc.source,
                ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    async def delete(self, ids: List[str]) -> bool:
        """删除文档"""
        for doc_id in ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
        return True


class HybridRetriever:
    """混合检索器"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        use_bm25: bool = True,
        use_kg: bool = False,
    ):
        self.vector_store = vector_store or InMemoryVectorStore()
        self.use_bm25 = use_bm25
        self.use_kg = use_kg

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            检索结果
        """
        # 向量检索
        vector_results = await self.vector_store.search(query, top_k=top_k)

        # BM25 检索（如果启用）
        bm25_results = []
        if self.use_bm25:
            bm25_results = await self._bm25_search(query, top_k=top_k)

        # 知识图谱检索（如果启用）
        kg_results = []
        if self.use_kg:
            kg_results = await self._kg_search(query, top_k=top_k)

        # 合并结果
        all_results = self._merge_results(
            vector_results, bm25_results, kg_results
        )

        # 应用过滤
        if filters:
            all_results = self._apply_filters(all_results, filters)

        # 去重并排序
        unique_results = self._deduplicate(all_results)
        unique_results.sort(key=lambda x: x.score, reverse=True)

        return RetrievalResult(
            query=query,
            documents=unique_results[:top_k],
            total=len(unique_results),
        )

    async def _bm25_search(
        self, query: str, top_k: int = 5
    ) -> List[Document]:
        """BM25 检索（简化实现）"""
        # 实际项目中应使用 rank_bm25 库
        return await self.vector_store.search(query, top_k=top_k)

    async def _kg_search(
        self, query: str, top_k: int = 5
    ) -> List[Document]:
        """知识图谱检索（简化实现）"""
        # 实际项目中应查询 Neo4j
        return []

    def _merge_results(
        self,
        vector_results: List[Document],
        bm25_results: List[Document],
        kg_results: List[Document],
    ) -> List[Document]:
        """合并检索结果"""
        # 简单合并，实际项目中应使用 RRF 或加权融合
        all_results = []

        # 向量结果权重 0.5
        for doc in vector_results:
            doc.score *= 0.5
            all_results.append(doc)

        # BM25 结果权重 0.3
        for doc in bm25_results:
            doc.score *= 0.3
            all_results.append(doc)

        # KG 结果权重 0.2
        for doc in kg_results:
            doc.score *= 0.2
            all_results.append(doc)

        return all_results

    def _apply_filters(
        self, documents: List[Document], filters: Dict[str, Any]
    ) -> List[Document]:
        """应用过滤条件"""
        filtered = []
        for doc in documents:
            match = True
            for key, value in filters.items():
                if key in doc.metadata and doc.metadata[key] != value:
                    match = False
                    break
            if match:
                filtered.append(doc)
        return filtered

    def _deduplicate(self, documents: List[Document]) -> List[Document]:
        """去重"""
        seen = set()
        unique = []
        for doc in documents:
            if doc.id not in seen:
                seen.add(doc.id)
                unique.append(doc)
        return unique


class RAGService:
    """RAG 服务"""

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or HybridRetriever()
        self.llm_client = None

    async def _get_llm_client(self):
        """获取 LLM 客户端"""
        if not self.llm_client:
            from src.llm.client import get_llm_client
            self.llm_client = get_llm_client()
        return self.llm_client

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        RAG 查询

        Args:
            question: 用户问题
            top_k: 检索数量
            filters: 过滤条件

        Returns:
            包含答案和来源的结果
        """
        # 检索相关文档
        retrieval_result = await self.retriever.retrieve(
            question, top_k=top_k, filters=filters
        )

        if not retrieval_result.documents:
            return {
                "answer": "抱歉，没有找到相关信息。",
                "sources": [],
                "confidence": 0.0,
            }

        # 构建上下文
        context = "\n\n".join([
            f"[来源: {doc.source}]\n{doc.content}"
            for doc in retrieval_result.documents
        ])

        # 生成答案
        prompt = f"""基于以下参考信息，回答用户的问题。

## 参考信息

{context}

## 用户问题

{question}

## 回答要求

1. 基于参考信息回答，不要编造
2. 如果参考信息不足以回答，明确说明
3. 引用来源时使用 [来源: xxx] 格式
4. 语言简洁专业

## 回答

请回答用户的问题："""

        llm_client = await self._get_llm_client()
        messages = [
            {"role": "system", "content": "你是一个专业的知识助手。"},
            {"role": "user", "content": prompt},
        ]

        answer = await llm_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        # 计算置信度
        avg_score = sum(d.score for d in retrieval_result.documents) / len(retrieval_result.documents)

        return {
            "answer": answer,
            "sources": [
                {
                    "id": doc.id,
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "score": doc.score,
                    "source": doc.source,
                }
                for doc in retrieval_result.documents
            ],
            "confidence": avg_score,
        }

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """
        添加文档到知识库

        Args:
            documents: 文档列表，每个文档包含 content, metadata, source

        Returns:
            文档 ID 列表
        """
        docs = []
        for i, doc_data in enumerate(documents):
            doc = Document(
                id=doc_data.get("id", f"doc_{i}"),
                content=doc_data["content"],
                metadata=doc_data.get("metadata", {}),
                source=doc_data.get("source", ""),
            )
            docs.append(doc)

        return await self.retriever.vector_store.add_documents(docs)
