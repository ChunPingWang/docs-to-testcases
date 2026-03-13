# 地端模型部署指南 — GMK EVO x2 (128GB RAM)

## 硬體規格分析

| 項目 | GMK EVO x2 規格 |
|------|-----------------|
| RAM | 128GB DDR5 |
| CPU | Intel Core Ultra / AMD Ryzen (依版本) |
| GPU | 內建 iGPU（無獨立顯卡） |
| 推論方式 | **純 CPU 推論**（使用 llama.cpp / Ollama） |

> **關鍵限制**：無獨立 GPU，所有推論走 CPU + RAM。128GB RAM 可載入約 **70B Q4 量化模型**（~40GB），剩餘 RAM 給 OS、ChromaDB、PostgreSQL、應用服務使用。

---

## 推薦模型組合

### 方案一：效能優先（推薦）

| 用途 | 模型 | 量化 | VRAM/RAM 需求 | 說明 |
|------|------|------|---------------|------|
| **Chat / 測試案例生成** | `qwen2.5:32b-instruct-q4_K_M` | Q4_K_M | ~20GB | 中文最強、程式碼能力優秀 |
| **程式碼生成** | `qwen2.5-coder:32b-instruct-q4_K_M` | Q4_K_M | ~20GB | 專門針對程式碼生成最佳化 |
| **Embedding** | `bge-m3` | FP16 | ~2.4GB | 多語言（中英日韓）、1024 維度 |

### 方案二：最大模型（追求品質）

| 用途 | 模型 | 量化 | VRAM/RAM 需求 | 說明 |
|------|------|------|---------------|------|
| **Chat / 測試案例生成** | `qwen2.5:72b-instruct-q4_K_M` | Q4_K_M | ~42GB | 最高品質中文輸出 |
| **Embedding** | `bge-m3` | FP16 | ~2.4GB | 同上 |

> 72B 模型在純 CPU 上推論速度約 **2-5 tokens/sec**，適合非即時場景（批次產生測試案例）。
> 32B 模型在純 CPU 上推論速度約 **5-12 tokens/sec**，適合互動式使用。

### 方案三：輕量快速（開發測試用）

| 用途 | 模型 | 量化 | VRAM/RAM 需求 | 說明 |
|------|------|------|---------------|------|
| **Chat** | `qwen2.5:14b-instruct-q4_K_M` | Q4_K_M | ~9GB | 快速回應、品質仍佳 |
| **Embedding** | `bge-m3` | FP16 | ~2.4GB | 同上 |

### 模型選擇理由

**為什麼選 Qwen2.5？**
1. **中文能力業界第一**：阿里巴巴通義千問團隊，中文訓練資料最豐富
2. **程式碼生成優秀**：在 HumanEval、MBPP 等 benchmark 表現頂尖
3. **Ollama 原生支援**：一行指令即可部署
4. **支援長上下文**：32K-128K context window，適合 RAG 場景
5. **指令遵循能力強**：Gherkin 格式輸出穩定

**為什麼選 BGE-M3 做 Embedding？**
1. **多語言支援**：中英混合文件處理能力強
2. **高維度（1024）**：語意區分度高，提升 RAG 檢索品質
3. **Ollama 直接支援**：`ollama pull bge-m3`

---

## 執行步驟

### Phase 1：環境準備

```bash
# 1. 安裝 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. 下載模型
ollama pull qwen2.5:32b-instruct-q4_K_M
ollama pull qwen2.5-coder:32b-instruct-q4_K_M
ollama pull bge-m3

# 3. 驗證模型可用
ollama list
ollama run qwen2.5:32b-instruct-q4_K_M "用中文說明什麼是 BDD 測試"
```

### Phase 2：修改 `.env` 配置

```bash
# .env - 地端模型配置
LLM_API_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama                          # Ollama 不需 API key，填任意值
LLM_MODEL=qwen2.5:32b-instruct-q4_K_M
EMBEDDING_MODEL=bge-m3
```

> 本專案的 `ollama_client.py` 已經使用 OpenAI-compatible API 格式，Ollama 的 `/v1` endpoint 完全相容。

### Phase 3：用公有雲模型產出 System Prompt（推薦流程）

**為什麼要先用公有雲模型？**
- 公有雲模型（如 GPT-4o、Claude、Gemini）能力更強，能產出**更精準的 system prompt**
- 地端模型的表現高度依賴 system prompt 品質
- 公有雲模型能更好地理解你的文件內容，萃取關鍵領域知識

#### 步驟 3.1：準備 Prompt 產生請求

向公有雲模型（GPT-4o / Claude / Gemini）發送以下請求：

```
我正在建立一個「自動化測試案例產生系統」，需要你幫我產出一個 Ollama Modelfile
裡的 SYSTEM prompt。

系統用途：
- 從系統設計文件（SDD/SRS/API Spec）自動產生 BDD/Gherkin 測試案例
- 產生可執行的測試程式碼（Python pytest-bdd / JavaScript Cucumber.js）
- 基於 RAG 回答關於系統設計的問題
- 支援正面測試、負面測試、API 測試、E2E 測試

以下是我的系統設計文件摘要（貼上你的文件摘要或前幾個 chunk 的內容）：
---
[在此貼上文件內容摘要]
---

要求：
1. System prompt 必須是繁體中文
2. 明確定義模型的角色與專業能力
3. 包含領域知識摘要（從文件中萃取）
4. 規範 Gherkin 輸出格式
5. 規範測試程式碼輸出格式（含 ===FILE: xxx=== 標記）
6. 約 2000-4000 字，足以涵蓋關鍵知識但不超過 token 限制
7. 包含錯誤處理和邊界條件的測試思維指引
```

#### 步驟 3.2：審核與調整

收到公有雲模型的 system prompt 後：
1. 人工審核內容是否涵蓋你的領域知識
2. 確認 Gherkin 格式規範是否正確
3. 調整用語和術語使其符合團隊習慣
4. 用地端模型實際測試幾次，根據輸出品質微調

#### 步驟 3.3：寫入 Modelfile

```
FROM qwen2.5:32b-instruct-q4_K_M
SYSTEM """
（貼入公有雲模型產出並經你調整後的 system prompt）
"""
PARAMETER temperature 0.3
PARAMETER num_predict 8192
PARAMETER num_ctx 32768
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

### Phase 4：建立並註冊自訂模型

```bash
# 用 Ollama 建立自訂模型
ollama create my-qa-engineer -f /path/to/Modelfile

# 驗證
ollama run my-qa-engineer "請根據以下需求產生 Gherkin 測試案例：用戶登入功能需支援 OAuth2.0"
```

### Phase 5：整合到本專案

更新 `.env`：
```bash
LLM_MODEL=my-qa-engineer    # 使用自訂模型
```

啟動服務：
```bash
docker-compose up -d
```

---

## Modelfile 參數建議

```
FROM qwen2.5:32b-instruct-q4_K_M

SYSTEM """
（見下方 system prompt 範本）
"""

# 測試案例生成用較低溫度，確保格式一致
PARAMETER temperature 0.3

# 最大輸出 token 數
PARAMETER num_predict 8192

# 上下文視窗（32K 足夠 RAG 場景）
PARAMETER num_ctx 32768

# Top-P 採樣
PARAMETER top_p 0.9

# 避免重複輸出
PARAMETER repeat_penalty 1.1

# CPU 執行緒數（依 GMK EVO 核心數調整，建議 CPU 核心數 - 2）
PARAMETER num_thread 14
```

### 參數說明

| 參數 | 建議值 | 說明 |
|------|--------|------|
| `temperature` | 0.3 | 測試案例生成需低溫度確保格式穩定；QA 場景可調高至 0.7 |
| `num_predict` | 8192 | Gherkin + 測試程式碼輸出需要足夠 token |
| `num_ctx` | 32768 | RAG 注入上下文 + prompt 需較大 context window |
| `top_p` | 0.9 | 略低於 1.0，減少低機率 token |
| `repeat_penalty` | 1.1 | 防止重複生成相同的 Given/When/Then |
| `num_thread` | CPU 核心-2 | 預留 2 核心給 OS 和其他服務 |

---

## System Prompt 範本

以下是一個通用範本，**建議先用公有雲模型根據你的實際文件產出專屬版本**：

```
你是一位資深的 QA 自動化測試工程師，專精於 BDD（行為驅動開發）測試方法論。

## 你的核心能力

1. **系統分析**：深入理解系統設計文件（SDD、SRS、API 規格書），識別功能點、業務規則、邊界條件和異常場景。

2. **Gherkin 測試案例撰寫**：
   - 使用標準 Gherkin 語法（Feature / Scenario / Given / When / Then / And / But）
   - 每個 Feature 包含正面測試（Happy Path）和負面測試（Edge Cases）
   - 使用 Scenario Outline + Examples 處理參數化測試
   - 使用 @tag 標記測試類別（@positive, @negative, @api, @e2e, @smoke）

3. **可執行測試程式碼生成**：
   - Python：使用 pytest-bdd 框架
   - JavaScript：使用 Cucumber.js 框架
   - 程式碼包含完整的 step definitions、fixtures、assertions

4. **RAG 問答**：根據提供的系統文件上下文，精確回答關於系統設計和實作的技術問題。

## 輸出格式規範

### Gherkin 輸出格式
```gherkin
@api @positive
Feature: [功能名稱]
  As a [角色]
  I want to [操作]
  So that [目的]

  Background:
    Given [前置條件]

  Scenario: [正面測試情境描述]
    Given [前置條件]
    When [操作步驟]
    Then [預期結果]
    And [額外驗證]

  Scenario Outline: [參數化測試]
    Given [前置條件]
    When [操作 "<param>"]
    Then [預期結果]

    Examples:
      | param   | expected |
      | value1  | result1  |
      | value2  | result2  |
```

### 測試程式碼輸出格式
使用以下標記分隔多個檔案：
===FILE: tests/features/login.feature ===
（檔案內容）
===END_FILE===

===FILE: tests/step_defs/test_login_steps.py ===
（檔案內容）
===END_FILE===

## 測試設計原則

1. **等價類別劃分**：識別有效與無效的輸入範圍
2. **邊界值分析**：測試邊界條件（最小值、最大值、邊界±1）
3. **錯誤猜測**：基於常見錯誤模式設計測試（null、空字串、特殊字元、超長輸入）
4. **狀態轉換測試**：對有狀態的流程設計狀態轉換覆蓋
5. **API 測試**：驗證 HTTP 狀態碼、Response Body、Header、認證/授權
6. **E2E 測試**：完整用戶流程的端對端驗證

## 回應語言

- 所有回應使用**繁體中文**
- 程式碼中的變數名稱和註解使用英文
- Gherkin 的 Feature/Scenario 描述使用繁體中文
```

---

## 完整執行流程總覽

```
┌────────────────────────────────────────────────────────────┐
│                     完整部署流程                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Step 1: 安裝 Ollama + 下載基礎模型                         │
│    ollama pull qwen2.5:32b-instruct-q4_K_M                 │
│    ollama pull bge-m3                                      │
│         │                                                  │
│         ▼                                                  │
│  Step 2: 上傳文件到系統 → RAG 處理 → ChromaDB               │
│    docker-compose up → 前端上傳文件 → 自動分塊/嵌入          │
│         │                                                  │
│         ▼                                                  │
│  Step 3: 用公有雲模型產出 System Prompt                      │
│    把文件摘要給 GPT-4o / Claude / Gemini                    │
│    → 產出領域專屬的 system prompt                            │
│         │                                                  │
│         ▼                                                  │
│  Step 4: 人工審核 + 調整 system prompt                      │
│    確認領域知識正確、格式規範完整                              │
│         │                                                  │
│         ▼                                                  │
│  Step 5: 寫入 Modelfile + 建立自訂模型                      │
│    ollama create my-qa-engineer -f Modelfile                │
│         │                                                  │
│         ▼                                                  │
│  Step 6: 準備 Fine-tune 訓練資料                             │
│    POST /ai/finetune/prepare                               │
│    → 產出 train.jsonl / val.jsonl                           │
│         │                                                  │
│         ▼                                                  │
│  Step 7: 用訓練資料進一步優化                                │
│    選項 A: 用 train.jsonl 做 few-shot 範例加入 Modelfile     │
│    選項 B: 用 Unsloth/LoRA 做真正的 fine-tune               │
│         │                                                  │
│         ▼                                                  │
│  Step 8: 評估 RAG + 模型品質                                │
│    POST /ai/eval → Ragas 指標                              │
│    (faithfulness, relevancy, precision, recall)             │
│         │                                                  │
│         ▼                                                  │
│  Step 9: 迭代優化                                           │
│    調整 chunk_size、top_k、system prompt、temperature       │
│    → 重新評估 → 達到品質要求                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Fine-tune 進階選項

### 選項 A：Modelfile Few-shot（輕量，推薦起步）

在 Modelfile 的 SYSTEM prompt 中嵌入高品質的範例：

```
SYSTEM """
（前面的 system prompt 內容）

## 範例輸出

以下是高品質的 Gherkin 測試案例範例，請參考此格式：

### 範例 1：用戶登入
Feature: 用戶登入功能
  @positive @api
  Scenario: 使用有效帳號密碼登入
    Given 用戶已註冊帳號 "testuser@example.com"
    When 用戶使用帳號 "testuser@example.com" 和密碼 "ValidPass123!" 登入
    Then 回應狀態碼應為 200
    And 回應應包含有效的 JWT token

  @negative @api
  Scenario: 使用錯誤密碼登入
    Given 用戶已註冊帳號 "testuser@example.com"
    When 用戶使用帳號 "testuser@example.com" 和密碼 "WrongPass" 登入
    Then 回應狀態碼應為 401
    And 回應訊息應為 "帳號或密碼錯誤"

（更多範例...）
"""
```

### 選項 B：LoRA Fine-tune（深度客製）

```bash
# 使用 Unsloth 進行 LoRA fine-tune（需要足夠 RAM）
pip install unsloth

# 準備 train.jsonl（由 /ai/finetune/prepare 產出）
# 執行 fine-tune 腳本
python scripts/finetune_lora.py \
  --base-model qwen2.5:32b-instruct \
  --train-data /data/finetune/{project_id}/train.jsonl \
  --output-dir /data/finetune/{project_id}/lora_output \
  --epochs 3 \
  --lora-rank 16

# 合併 LoRA 權重並匯入 Ollama
# （需使用 llama.cpp 的 convert 工具）
```

> **注意**：在 128GB RAM 純 CPU 環境下，LoRA fine-tune 32B 模型可能需要數小時至數天。建議先用 **選項 A（Modelfile Few-shot）** 快速驗證效果。

---

## RAM 使用規劃

| 服務 | 預估 RAM 使用 |
|------|--------------|
| OS + 系統服務 | ~4GB |
| Ollama（32B Q4 模型） | ~20GB |
| Ollama（BGE-M3 embedding） | ~2.4GB |
| ChromaDB | ~2-4GB（依文件量） |
| PostgreSQL | ~1-2GB |
| Docker 容器（前端+API Gateway+AI Service） | ~2-4GB |
| **總計** | **~32-36GB** |
| **剩餘可用** | **~92-96GB** |

> 即使使用 72B 模型（~42GB），總計也只約 **55-60GB**，仍有充裕空間。

---

## 常見問題

### Q: 為什麼不用 DeepSeek？
A: DeepSeek-V2/V3 的中文能力也很好，但 Qwen2.5 在 Ollama 生態系中支援更完整，且模型大小選擇更靈活（7B/14B/32B/72B）。若偏好 DeepSeek，`deepseek-v2.5:32b` 也是可行選項。

### Q: Embedding 可以用 Ollama 的 qwen2.5 嗎？
A: 可以但不建議。專門的 embedding 模型（如 BGE-M3）在檢索任務上表現遠優於通用 LLM 的 embedding。

### Q: 需要調整 ChromaDB 的 embedding 維度嗎？
A: BGE-M3 輸出 1024 維度，ChromaDB 會自動適配。但注意：切換 embedding 模型後，所有已嵌入的文件需要**重新處理**，因為維度和語意空間不同。

### Q: 推論速度太慢怎麼辦？
A:
1. 降級到更小的模型（32B → 14B）
2. 使用更激進的量化（Q4_K_M → Q4_0）
3. 確認 `num_thread` 設定為 CPU 核心數 - 2
4. 批次處理：非互動場景使用批次 API 呼叫
