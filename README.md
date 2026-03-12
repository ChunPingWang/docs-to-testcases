# Docs-to-TestCases

RAG + LLM 驅動的自動化測試案例生成平台。上傳系統設計文件，自動產生 Gherkin 格式測試案例與可執行測試程式碼。

## 架構概覽

```
                         ┌──────────────────────────────┐
                         │   MiniMax API (Cloud)        │
                         │   Chat: /v1/chat/completions │
                         │   Embed: /v1/embeddings      │
                         └──────────────▲───────────────┘
                                        │ HTTPS
┌────────────┐     ┌──────────────┐     │  ┌─────────────┐
│  Frontend   │────▶│  API Gateway │────▶│──│  AI Service │
│  Next.js    │     │  NestJS      │     │  │  FastAPI     │
│  :3000      │     │  :4000       │     │  │  :8000       │
└────────────┘     └──────┬───────┘     │  └──────┬──────┘
                          │             │         │
                   ┌──────▼───────┐     │  ┌──────▼──────┐
                   │  PostgreSQL  │     │  │  ChromaDB   │
                   │  :5432       │     │  │  :8200      │
                   └──────────────┘     │  └─────────────┘
                                        │
```

### 服務說明

| 服務 | 技術 | 用途 |
|------|------|------|
| **Frontend** | Next.js 16, React 19, Tailwind CSS, Shadcn/ui | 使用者介面 |
| **API Gateway** | NestJS 11, TypeORM, PostgreSQL 16 | 商業邏輯、資料持久化、檔案上傳 |
| **AI Service** | FastAPI, Python 3.12, ChromaDB, Langchain | LLM 整合、RAG 管線、文件解析 |
| **PostgreSQL** | PostgreSQL 16 Alpine | 專案、文件、測試案例等關聯式資料 |
| **ChromaDB** | ChromaDB latest | 文件向量儲存與語意搜尋 |
| **LLM Provider** | MiniMax API (OpenAI-compatible) | 文字生成 (MiniMax-M2.5) 與嵌入 (embo-01) |

### 請求流程

```
使用者上傳文件 → Frontend → API Gateway (儲存檔案 + DB) → AI Service
    AI Service: 解析文件 → 切塊 → MiniMax Embedding API → 存入 ChromaDB

使用者產生測試 → Frontend → API Gateway → AI Service
    AI Service: ChromaDB 語意檢索 → 組合 Prompt → MiniMax Chat API → 回傳 Gherkin
```

## 主要功能

- **文件管理** — 上傳 PDF、Word (.docx)、Excel (.xlsx)、Markdown、純文字，自動解析、切塊、向量化
- **測試案例生成** — 基於 RAG 檢索文件上下文，產生 Gherkin (BDD) 格式測試案例
- **測試程式碼生成** — 從 Gherkin 產生 Python (pytest-bdd) 或 JavaScript (Cucumber.js) 測試程式
- **文件問答 (Q&A)** — 針對已上傳文件進行語意搜尋問答，支援 SSE 串流回應
- **模型微調** — 從文件自動產生 QA/Gherkin 訓練資料對，產生 Modelfile
- **參數設定** — 即時調整 LLM 模型、溫度、Token 上限、RAG 參數（chunk size / overlap / top_k）

### 文件解析器

| 格式 | 套件 | 說明 |
|------|------|------|
| PDF | pdfplumber | 逐頁提取文字與表格 |
| Word (.docx) | python-docx | 依 Heading 層級拆分段落，提取表格 |
| Excel (.xlsx) | openpyxl | 逐 sheet 提取表格資料 |
| Markdown | markdown + beautifulsoup4 | 解析標題結構與內容 |
| 純文字 (.txt) | 內建 | 直接讀取 |

> **注意：** Word 僅支援 `.docx` 格式，不支援舊版 `.doc`。

### 測試案例狀態流程

```
draft → in_review → approved / rejected → code_generated
```

## 目錄結構

```
docs-to-testcases/
├── frontend/                   # Next.js 前端
│   └── src/
│       ├── app/                # App Router 頁面
│       │   ├── page.tsx        #   Dashboard
│       │   ├── projects/       #   專案管理 (CRUD、文件、生成、QA、微調)
│       │   └── settings/       #   模型參數設定
│       ├── components/         # UI 元件 (Sidebar, Shadcn/ui)
│       ├── lib/                # api-client.ts, utils.ts
│       └── types/              # TypeScript 型別定義
│
├── api-gateway/                # NestJS 後端
│   └── src/
│       ├── modules/            # projects, documents, features,
│       │                       # code-generation, qa, finetune, settings
│       ├── services/           # ai-service.client.ts (HTTP proxy)
│       └── config/             # configuration.ts
│
├── ai-service/                 # FastAPI AI 服務
│   └── app/
│       ├── api/routes/         # documents, generation, qa, finetune,
│       │                       # settings, health
│       ├── core/
│       │   ├── parsers/        # pdf, docx, xlsx, markdown, text
│       │   ├── chunking/       # 文件切塊 (by sections / general)
│       │   ├── embedding/      # MiniMax Embedding API 整合
│       │   ├── llm/            # MiniMax Chat API 整合 + prompt 模板
│       │   ├── rag/            # retriever + chain (QA 管線)
│       │   ├── vectorstore/    # ChromaDB 操作封裝
│       │   └── runtime_settings.py  # 可動態調整的執行期參數
│       └── models/             # Pydantic request/response schemas
│
├── scripts/
│   └── init-db.sql             # PostgreSQL Schema (8 張表)
│
├── docker-compose.yml          # 5 個容器編排
├── .env.example                # 環境變數範本
└── README.md
```

## 資料庫 Schema

```
projects
  ├── documents
  │     └── document_chunks
  ├── features
  │     ├── scenarios
  │     └── generated_code
  ├── finetune_jobs
  └── qa_history
```

共 8 張表，以 `project_id` 為核心隔離維度。詳見 `scripts/init-db.sql`。

## 快速開始

### 前置需求

- Docker & Docker Compose
- MiniMax API Key（至 [MiniMax 平台](https://platform.minimax.io) 取得）

### 啟動

```bash
# 1. 複製環境變數範本
cp .env.example .env

# 2. 編輯 .env，填入你的 API Key
#    LLM_API_KEY=your-api-key-here

# 3. 啟動所有服務（首次會自動 build images）
docker compose up -d

# 4. 查看日誌
docker compose logs -f

# 5. 停止服務
docker compose down
```

### 存取服務

| 服務 | URL |
|------|-----|
| Frontend | http://localhost:3000 |
| API Gateway (Swagger) | http://localhost:4000/api/docs |
| AI Service (Docs) | http://localhost:8000/ai/docs |
| ChromaDB | http://localhost:8200 |
| PostgreSQL | localhost:5432 |

### 本機開發

```bash
# Frontend
cd frontend && npm install && npm run dev

# API Gateway（需要 PostgreSQL 運行中）
cd api-gateway && npm install && npm run start:dev

# AI Service（需要 ChromaDB 運行中）
cd ai-service && pip install -e . && uvicorn app.main:app --reload --port 8000
```

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `POSTGRES_USER` | `appuser` | 資料庫使用者 |
| `POSTGRES_PASSWORD` | `apppass` | 資料庫密碼 |
| `POSTGRES_DB` | `docstest` | 資料庫名稱 |
| `LLM_API_BASE_URL` | `https://api.minimax.io/v1` | LLM API 基礎 URL (OpenAI-compatible) |
| `LLM_API_KEY` | — | LLM API 金鑰（**必填**） |
| `LLM_MODEL` | `MiniMax-M2.5` | 聊天 / 生成模型 |
| `EMBEDDING_MODEL` | `embo-01` | 嵌入模型 |
| `CHROMA_HOST` | `chromadb` | ChromaDB 主機 |
| `CHROMA_PORT` | `8000` | ChromaDB 連接埠 |
| `AI_SERVICE_URL` | `http://ai-service:8000` | AI Service 內部位址 |
| `NEXT_PUBLIC_API_URL` | `http://localhost:4000` | 前端連接 API 位址 |

## 技術細節

### LLM 整合

AI Service 透過 OpenAI-compatible HTTP API 與 MiniMax 通訊：

- **Chat Completions** (`/v1/chat/completions`) — 測試案例生成、Q&A、程式碼生成
- **Embeddings** (`/v1/embeddings`) — 文件向量化（使用 `texts` + `type` 參數，回傳 `vectors`）
- MiniMax-M2.5 回應包含 `<think>` 推理區塊，系統會自動過濾

### RAG 管線

```
查詢 → embed_single(query, type="query")
     → ChromaDB cosine similarity search (top_k)
     → 格式化 context
     → Chat Completion with system prompt + context + user query
```

### Docker 容器

| Container | Image | 備註 |
|-----------|-------|------|
| frontend | node:20-alpine | Next.js production build |
| api-gateway | node:20-alpine | Multi-stage build (builder + runtime) |
| ai-service | python:3.12-slim | Memory limit: 8GB |
| chromadb | chromadb/chroma:latest | Persistent volume |
| postgres | postgres:16-alpine | Health check + init SQL |

## 授權

Private
