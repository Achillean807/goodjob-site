[根目錄](../CLAUDE.md) > **src**

# src（村山良作正式站台）

> **變更記錄 (Changelog)**
> - 2026-04-05: 第二次掃描更新 — 修正文章數量為 27 篇、補充 AEO 設定、新增 outdoor.html、新增 works/ 圖片目錄、文檔改為繁體中文。
> - 2026-04-03: 初次建立模組 CLAUDE.md。

## 模組職責

村山良作 (Murayama Goodjob) 正式站台 — 品牌活動、主題場景與展場空間的作品集展示網站。純靜態站搭配輕量 REST API 進行文章管理。Netflix 深色主題設計風格。

## 入口與啟動

- **伺服器:** `server.py`（550 行）— Python 3 stdlib HTTP server（零外部依賴）
  - 預設 port: 10814（正式環境），可透過 `--port` 設定
  - 同時提供靜態檔案服務與 JSON API 端點
- **前端入口:** `index.html` — SPA，使用 hash-based routing
- **SPA 邏輯:** `assets/site.js`（~1030 行）— fetch `/api/articles`，渲染作品方格與詳情 modal

## 對外接口（REST API）

| 方法 | 端點 | 驗證 | 說明 |
|------|------|------|------|
| GET | `/api/articles` | 否 | 列出全部 27 篇文章 |
| GET | `/api/images/{id}` | 否 | 特定文章的圖片清單 |
| POST | `/api/articles` | Basic | 新增文章 |
| PUT | `/api/articles/{id}` | Basic | 更新文章欄位 |
| DELETE | `/api/articles/{id}` | Basic | 刪除文章 |
| POST | `/api/upload/{id}` | Basic | 上傳圖片（multipart/form-data） |

驗證方式：HTTP Basic Auth，帳密以 salted SHA-256 hash 儲存於 `data/config.json`。

## 關鍵依賴與設定

- **零外部依賴** — 僅使用 Python stdlib
- `data/config.json` — 管理員帳密 hash
- `data/articles.json` — 全部文章資料（單一資料來源）
- `data/wp_texts.json` — WordPress 原始文案備份（僅供參考）
- 字體：Google Fonts（Sora、Noto Sans TC）透過 CDN 載入
- 結構化資料：`index.html` 含 JSON-LD `LocalBusiness`，`workflow.html` 含 JSON-LD `FAQPage`
- AEO：`llms.txt` 提供 LLM 可讀摘要，部分頁面嵌入 Washinmura AEO 爬蟲追蹤碼

## 資料模型

**articles.json** 結構：`{ "articles": [ ... ] }`

每篇文章物件：
```json
{
  "id": "kebab-case-slug",
  "title": "顯示標題",
  "description": "HTML 描述文字",
  "category": "party" | "business" | "civil" | "magic",
  "featured": true/false,
  "featuredOrder": 0,
  "heroImage": "/assets/images/...",
  "images": ["/assets/images/..."],
  "linkUrl": "/pages/{id}.html",
  "videoId": "youtube-id 或 null",
  "videoVertical": true/false,
  "sortOrder": number,
  "updatedAt": "ISO datetime"
}
```

分類：`business`（主題活動）、`party`（春酒尾牙）、`magic`（魔法學院）、`civil`（戶政改造）

圖片儲存方式：
- 舊式：`assets/images/{slug}-hero.jpg`、`{slug}-detail-N.jpg`、`{slug}-scene-N.jpg`（扁平存放）
- 新式：`assets/images/works/{slug}/hero.jpg`、`01.jpg`...（獨立目錄）

## 子頁面

| 頁面 | 檔案 | 用途 |
|------|------|------|
| 首頁 | `index.html` | Hero + 作品方格 + 詳情 modal（SPA） |
| 村花囍茶 | `teabar.html` | 迎賓花果茶方案展示 |
| 合作流程 | `workflow.html` | 四步合作流程說明 |
| 分類帽 | `sort-hat/index.html` | 婚禮座位查詢工具（Harry Potter 主題，自包含） |
| CMS 後台 | `admin/index.html` | 文章 CRUD 管理介面 |
| 婚禮套組（室內） | `wedding-packages/index.html` | 送客背景・舞台走道套組 |
| 婚禮套組（戶外） | `wedding-packages/outdoor.html` | 戶外證婚・送客套組 |

## 測試與品質

無自動化測試。手動測試流程：
1. 本機執行 `python3 server.py --port 8000`
2. 瀏覽器視覺檢查各頁面
3. 透過 `/admin/` 測試 CMS 操作
4. 部署後確認線上網址

## 常見問題 (FAQ)

**Q: 如何新增作品？**
A: 使用 `/admin/` CMS 後台，或以 Basic Auth 呼叫 POST `/api/articles`。

**Q: 圖片部署後沒更新？**
A: Cloudflare 快取積極。更新所有 HTML 檔案中 CSS/JS 引用的 `?v=` 查詢字串。

**Q: 路由如何運作？**
A: `site.js` 中的 hash-based SPA routing。`#detail/{id}` 渲染文章詳情。此路由對搜尋引擎不可見。

**Q: wedding-packages 的圖片在哪？**
A: `wedding-packages/images/` 目錄下，分為 `classic/`、`deluxe/`、`carousel/`（含室內/戶外各套組內容的子目錄）。此子站自帶圖片，與主站 `assets/images/` 分離。

## 相關檔案清單

| 檔案 | 行數 | 用途 |
|------|------|------|
| `server.py` | ~550 | HTTP 伺服器 + REST API |
| `assets/site.js` | ~1030 | SPA 前端邏輯 |
| `assets/site.css` | ~1260 | 所有樣式 |
| `index.html` | ~120 | 首頁模板 |
| `teabar.html` | - | 村花囍茶頁面 |
| `workflow.html` | - | 合作流程頁面 |
| `admin/index.html` | - | CMS 後台（單檔） |
| `sort-hat/index.html` | - | 座位查詢工具（單檔） |
| `wedding-packages/index.html` | - | 室內婚禮套組頁 |
| `wedding-packages/outdoor.html` | - | 戶外婚禮套組頁 |
| `llms.txt` | ~65 | LLM 可讀品牌摘要 |
| `robots.txt` | 6 | 爬蟲規則 + LLMs-Txt 指向 |
| `data/articles.json` | - | 27 篇作品資料 |
| `data/config.json` | 5 | 管理員驗證設定 |
