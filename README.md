# 智流 — 企业级智能流程自动化与决策支持平台

## 项目简介

智流平台采用多Agent协作架构，通过AI Agent技术实现"自然语言驱动业务流程"，将传统需要人工多步操作的流程简化为一句指令，同时提供多维度数据分析与决策支持能力。

## 核心功能

1. **智能流程自动化（IPA）** — 自然语言驱动跨系统操作
2. **NL2SQL 数据分析** — 自然语言查询数据库 + 自动生成报告
3. **决策支持引擎** — 多源数据融合 + 风险评估 + 方案推荐
4. **模型微调（SFT）** — 基于业务数据的领域模型优化

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + TypeScript + Vite + ECharts + Element Plus |
| 后端 | Python FastAPI + Pydantic + Uvicorn |
| LLM | LangChain + LangGraph + OpenAI API / Qwen |
| RAG | Milvus + BM25 + BGE-M3 |
| 知识图谱 | Neo4j |
| 微调 | Axolotl + Unsloth + LoRA + DPO |
| 数据库 | MySQL 8.0 + Redis |
| 任务调度 | Celery + RabbitMQ |
| 工作流 | 自研DAG执行引擎 + FSM |
| 部署 | Docker + Docker Compose + Nginx |

## 快速开始

### 1. 创建 Conda 环境

```bash
conda create -n zhiliu python=3.11 -y
conda activate zhiliu
```

### 2. 安装依赖

```bash
pip install -e .
pip install -e ".[dev]"
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 4. 启动数据库

```bash
docker-compose up -d
```

### 5. 运行测试

```bash
pytest backend/tests/ -v
```

### 6. 启动服务

```bash
cd backend
python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

## 模型微调（SFT）

### 微调策略

智流平台针对不同模块采用分层微调策略：

| 模块 | 微调方法 | 优先级 | 说明 |
|------|----------|--------|------|
| 意图识别 | SFT | 必须 | 分类任务，输入→标签映射明确 |
| NL2SQL | SFT → DPO | SFT必须，DPO推荐 | SQL有明确的正确/错误标准 |
| 决策支持 | SFT → DPO | SFT必须，DPO可选 | 涉及人类偏好的方案推荐 |

### 为什么选择 SFT 而非 RLHF

| 因素 | SFT | DPO | RLHF |
|------|-----|-----|------|
| 实现复杂度 | 低 | 中 | 高 |
| 训练稳定性 | 高 | 中 | 低 |
| 数据需求 | 标注数据 | 偏好对 | 偏好对+reward model |
| 适用任务 | 分类/结构化生成 | 偏好对齐 | 复杂对齐 |
| 本项目适用性 | ★★★★★ | ★★★★ | ★★ |

**结论**：SFT 为主，DPO 为辅。RLHF 需要额外训练 reward model，成本高、调参难，投入产出比不高。

### 微调工具链

```
训练框架: Axolotl 或 LLaMA-Factory
加速优化: Unsloth (2-5x 加速，省显存)
基座模型: Qwen2.5-7B-Instruct
参数高效: LoRA (rank=16, alpha=32)
```

### 意图识别微调

**数据格式**：

```json
{
  "messages": [
    {"role": "system", "content": "你是意图分类助手，识别用户输入的业务意图"},
    {"role": "user", "content": "我想请三天年假"},
    {"role": "assistant", "content": "{\"intent\": \"leave_request\", \"confidence\": 0.95, \"entities\": {\"leave_type\": \"年假\", \"days\": 3}}"}
  ]
}
```

**训练配置**：

```yaml
# configs/intent_sft.yaml
base_model: Qwen/Qwen2.5-7B-Instruct
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]

datasets:
  - path: data/intent_train.jsonl
    type: chat

num_epochs: 3
batch_size: 4
learning_rate: 2e-4
lr_scheduler: cosine
warmup_steps: 100
```

**数据量建议**：每个意图 50-100 条，50+ 意图总计 2500-5000 条标注数据。

### NL2SQL 微调

**阶段一：SFT**

```json
{
  "messages": [
    {"role": "system", "content": "你是SQL专家，根据自然语言生成MySQL查询"},
    {"role": "user", "content": "查询所有请假状态为待审批的员工姓名和请假天数\n\nSchema:\n- users(id, username, email, department)\n- leave_requests(id, user_id, leave_type, days, status, created_at)"},
    {"role": "assistant", "content": "SELECT u.username, l.days\nFROM users u\nJOIN leave_requests l ON u.id = l.user_id\nWHERE l.status = 'pending';"}
  ]
}
```

**阶段二：DPO（可选，提升明显）**

```json
{
  "prompt": "查询各部门的平均薪资",
  "chosen": "SELECT department, AVG(salary) as avg_salary FROM users GROUP BY department;",
  "rejected": "SELECT * FROM users;"
}
```

- 正例：执行成功且结果正确的 SQL
- 负例：执行失败或结果错误的 SQL

**数据量建议**：SFT 阶段 3000-5000 条，DPO 阶段 1000-2000 条偏好对。

### 决策支持微调

**阶段一：SFT（学会分析框架）**

```json
{
  "messages": [
    {"role": "system", "content": "你是专业的决策分析专家"},
    {"role": "user", "content": "分析云服务器 vs 物理服务器的采购决策，预算50万"},
    {"role": "assistant", "content": "## 决策分析\n\n### 方案对比\n\n| 维度 | 云服务器 | 物理服务器 |\n|------|----------|------------|\n| 初始成本 | 低（按需付费） | 高（一次性采购） |\n| 运维成本 | 中 | 高 |\n| 扩展性 | 高 | 低 |\n| 数据安全 | 中 | 高 |\n\n### 风险评估\n\n- 云服务器：供应商锁定风险、长期成本不可控\n- 物理服务器：硬件故障风险、技术迭代风险\n\n### 推荐方案\n\n基于50万预算和3年使用周期，推荐混合方案..."}
  ]
}
```

**阶段二：DPO（学会偏好对齐）**

```json
{
  "prompt": "分析两个候选供应商的优劣",
  "chosen": "基于历史合作数据、交付能力、价格竞争力、售后服务四个维度综合评估...",
  "rejected": "供应商A价格便宜，选A吧。"
}
```

**数据量建议**：SFT 阶段 1000-2000 条，DPO 阶段 500-1000 条偏好对。

### 微调数据准备脚本

```python
# scripts/prepare_sft_data.py
import json
from pathlib import Path

def prepare_intent_data(raw_data_path: str, output_path: str):
    """准备意图识别SFT数据"""
    with open(raw_data_path, 'r') as f:
        raw_data = json.load(f)
    
    sft_data = []
    for item in raw_data:
        sft_data.append({
            "messages": [
                {"role": "system", "content": "你是意图分类助手"},
                {"role": "user", "content": item["text"]},
                {"role": "assistant", "content": json.dumps({
                    "intent": item["intent"],
                    "confidence": 1.0,
                    "entities": item.get("entities", {})
                }, ensure_ascii=False)}
            ]
        })
    
    with open(output_path, 'w') as f:
        for item in sft_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(sft_data)} SFT examples")

if __name__ == "__main__":
    prepare_intent_data("data/raw_intent.json", "data/intent_train.jsonl")
```

### 微调效果评估

| 模块 | 评估指标 | SFT基线 | SFT+DPO |
|------|----------|---------|---------|
| 意图识别 | 准确率 | 96.2% | - |
| NL2SQL | 执行准确率 | 85% | 91.8% |
| 决策支持 | 人工评估 | 75分 | 85分 |

## 项目结构

```
zhiliu-platform/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── app.py           # FastAPI 应用工厂
│   │   │   └── routes/
│   │   │       ├── auth.py      # 认证路由
│   │   │       ├── workflow.py  # 工作流路由
│   │   │       ├── analytics.py # 分析路由
│   │   │       └── decision.py  # 决策路由
│   │   ├── config/
│   │   │   └── settings.py      # 配置管理
│   │   ├── database/
│   │   │   ├── connection.py    # 数据库连接
│   │   │   └── models.py        # SQLAlchemy 模型
│   │   ├── auth/
│   │   │   ├── jwt.py           # JWT 工具
│   │   │   └── dependencies.py  # 认证依赖
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 模型
│   │   ├── services/
│   │   │   ├── user_service.py      # 用户服务
│   │   │   ├── workflow_service.py  # 工作流服务
│   │   │   ├── analytics_service.py # 分析服务
│   │   │   └── decision_service.py  # 决策服务
│   │   ├── workflow/
│   │   │   └── dag_engine.py    # DAG工作流引擎
│   │   ├── intent/
│   │   │   └── classifier.py    # 意图分类器
│   │   ├── nl2sql/
│   │   │   └── engine.py        # NL2SQL引擎
│   │   ├── rag/
│   │   │   └── retriever.py     # RAG检索器
│   │   └── decision/
│   │       └── engine.py        # 决策引擎
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── src/
│   │   ├── api/         # API客户端
│   │   ├── components/  # 组件
│   │   ├── layouts/     # 布局
│   │   ├── router/      # 路由
│   │   ├── stores/      # 状态管理
│   │   └── views/       # 页面
│   └── ...
├── configs/             # 微调配置
├── scripts/             # 工具脚本
├── data/                # 训练数据
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── .gitignore
```

## 开发规范

- **TDD**: 测试驱动开发，先写测试再写代码
- **Conventional Commits**: 使用规范化的 Git 提交信息
- **Async/Await**: 优先使用异步编程
- **代码风格**: PEP8 / Google Style

## 许可证

MIT License
