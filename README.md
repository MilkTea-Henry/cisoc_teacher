# Cisco Lab Teacher (思科 Lab 助教系統)

一個幫助學習 Cisco 網路設定的智能輔助系統，支援 Lab 題目解析、RAG 問答、CLI 監控與自動輸入。

## 功能特色

- 📄 **Lab 文件解析**：讀取 `.docx` Lab 題目，自動抽取章節、題號、目標、步驟、關鍵指令和評分點
- 💾 **JSON 輸出**：將解析結果輸出為結構化 JSON（schema: lab_id, title, steps, qa）
- 🤖 **RAG 問答**：基於 Lab 內容的智能檢索問答系統
- 💬 **練功房對話**：練習每題指令與操作流程、一般 QA
- 👁️ **CLI 監控**：偵測 Cisco Packet Tracer CLI 視窗文字（OCR），即時比對指令
- ⚠️ **錯誤提示**：標示指令錯字、缺參數
- 📊 **進度追蹤**：顯示步驟進度條與當前步驟提示
- 🚀 **一鍵輸入**：將指令自動輸入到 Packet Tracer CLI

## 專案結構

```
cisoc_teacher/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 應用主程式
│   │   ├── schema.py         # 資料模型定義
│   │   ├── docx_parser.py    # DOCX 文件解析器
│   │   ├── rag.py            # RAG 檢索問答引擎
│   │   ├── cli_watcher.py    # CLI 視窗監控（OCR）
│   │   └── command_sender.py # 指令發送器
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx          # 聊天區面板
│   │   │   ├── StepsProgress.jsx      # 步驟進度組件
│   │   │   ├── CurrentHint.jsx        # 當前提示組件
│   │   │   ├── CommandSuggestions.jsx # 指令建議與一鍵輸入
│   │   │   └── LabSelector.jsx        # Lab 選擇器
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── tests/
│   ├── fixtures/
│   │   └── sample_lab.json   # 測試用 Lab JSON
│   ├── test_schema.py
│   ├── test_docx_parser.py
│   ├── test_rag.py
│   ├── test_cli_watcher.py
│   ├── test_command_sender.py
│   └── test_main.py
├── pytest.ini
└── README.md
```

## 安裝與執行

### 後端 (Backend)

```bash
# 進入後端目錄
cd backend

# 安裝依賴
pip install -r requirements.txt

# 啟動 FastAPI 伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文件將可在 http://localhost:8000/docs 查看。

### 前端 (Frontend)

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

前端將可在 http://localhost:3000 訪問。

## API 端點

### Lab 管理
- `POST /labs/upload` - 上傳 .docx Lab 檔案
- `POST /labs/json` - 載入 Lab JSON
- `GET /labs` - 列出所有 Lab
- `GET /labs/{lab_id}` - 取得特定 Lab
- `DELETE /labs/{lab_id}` - 刪除 Lab

### 進度追蹤
- `GET /labs/{lab_id}/progress` - 取得進度
- `POST /labs/{lab_id}/progress/next` - 前進到下一步
- `POST /labs/{lab_id}/progress/reset` - 重置進度

### 聊天與搜尋
- `POST /chat` - 聊天問答
- `GET /search?query=xxx` - 搜尋 Lab 內容

### CLI 監控
- `GET /cli/capture` - 擷取 CLI 畫面文字
- `POST /cli/compare` - 比較指令
- `POST /cli/send` - 發送指令到 CLI

### 提示
- `GET /labs/{lab_id}/steps/{step_id}/hint` - 取得步驟提示
- `GET /labs/{lab_id}/current-hint` - 取得當前步驟提示

## Lab JSON Schema

```json
{
  "lab_id": "2.1.3",
  "title": "Basic Router Configuration",
  "chapter": "2",
  "objective": "Configure basic router settings",
  "steps": [
    {
      "id": "1",
      "desc": "Enter privileged mode",
      "cmds": ["enable"],
      "checklist": ["Prompt shows #"]
    }
  ],
  "qa": [
    {
      "q": "What command enters privileged mode?",
      "a": "The enable command"
    }
  ]
}
```

## 測試

```bash
# 執行所有測試
cd /path/to/cisoc_teacher
python -m pytest tests/ -v

# 執行特定測試檔案
python -m pytest tests/test_schema.py -v
python -m pytest tests/test_docx_parser.py -v
python -m pytest tests/test_rag.py -v
python -m pytest tests/test_cli_watcher.py -v
python -m pytest tests/test_main.py -v
```

## 技術棧

### 後端
- Python 3.12+
- FastAPI - Web 框架
- Pydantic - 資料驗證
- python-docx - DOCX 解析
- LangChain + FAISS - RAG 向量檢索
- pytesseract - OCR 文字辨識
- pyautogui - 自動化輸入

### 前端
- React 18
- Vite - 建置工具
- Tailwind CSS - 樣式框架

### 測試
- pytest
- pytest-asyncio
- httpx

## 授權

MIT License

