# 村山良作 設計文件

## 設計概述

### 目標

以最低複雜度建構一個視覺精緻的作品集網站，讓業主（非技術人員）能自行管理內容，同時確保部署與維護的簡易性。

### 非目標

- 不做 SSR / SSG 框架整合
- 不做使用者帳號系統（僅單一管理員）
- 不做即時通訊或預約系統
- 不做多語系支援

## 架構設計

### 整體架構

```
┌──────────────────────────────────────────────────┐
│                  Cloudflare Tunnel                │
│         goodjob.weddingwishlove.com               │
└────────────────────┬─────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   server.py :10814  │
          │  (Python stdlib)    │
          ├─────────┬───────────┤
          │ Static  │ REST API  │
          │ Files   │ /api/*    │
          └────┬────┴─────┬─────┘
               │          │
    ┌──────────▼──┐  ┌────▼────────┐
    │  HTML/CSS   │  │ articles.   │
    │  /JS 靜態頁 │  │ json        │
    └─────────────┘  └─────────────┘

    瀏覽器端：
    ┌─────────────────────────────────────┐
    │  site.js (SPA)                      │
    │  ┌──────────┐  ┌────────────────┐   │
    │  │ fetch    │→ │ DOM render     │   │
    │  │ /api/    │  │ hash routing   │   │
    │  │ articles │  │ #detail/{id}   │   │
    │  └──────────┘  └────────────────┘   │
    └─────────────────────────────────────┘
```

### 核心元件

| 元件 | 職責 |
|------|------|
| **server.py** | HTTP 靜態檔案伺服 + REST API（CRUD + 圖片上傳）。使用 `SimpleHTTPRequestHandler` 擴展，JSON 以 atomic write（temp file + `os.replace`）確保資料安全 |
| **site.js** | SPA 前端：fetch API 資料 → 動態渲染精選列、分類列、詳情 modal、Lightbox、YouTube 播放器。IIFE 封裝，ES5 語法 |
| **site.css** | 全站樣式，使用 CSS Custom Properties 管理主題色。Netflix 深色風格，響應式設計 |
| **admin/index.html** | 單檔 CMS：登入驗證 → 文章列表 → 表單編輯 → 拖曳排序 → 圖片上傳。sessionStorage 存 auth token |

### 資料流

```
articles.json ──GET /api/articles──→ site.js ──DOM render──→ 瀏覽器畫面
                                                              │
                                                   使用者點擊卡片
                                                              │
                                                   hash 變更 #detail/{id}
                                                              │
                                                   渲染 modal + Lightbox
```

```
admin UI ──PUT /api/articles/{id}──→ server.py ──→ atomic write ──→ articles.json
admin UI ──POST /api/upload/{id}──→ server.py ──→ 存檔 assets/images/ ──→ 更新 articles.json
```

## 設計決策

| 日期 | 決策 | 理由 | 影響 |
|------|------|------|------|
| 2026-03 | 採用純 HTML/CSS/JS，不用框架 | 業主非技術人員，維護門檻須最低；主機資源有限 | 無 build step，SCP 即部署 |
| 2026-03 | Python stdlib HTTP server | 零依賴，主機不需 pip install | 功能受限於 stdlib，但對靜態站足夠 |
| 2026-03 | Netflix 深色主題 | 作品以攝影為主，深色背景凸顯圖片質感 | 所有頁面統一暗色調 |
| 2026-03 | Hash-based SPA routing | 單一 index.html 即可處理所有作品頁，無需產生靜態頁 | SEO 不可見，需另行產生 `/works/*.html` 靜態頁（待辦） |
| 2026-03 | JSON 檔案作為資料庫 | 27 篇文章規模不需 SQL，JSON 檔直接版控 | 不支援併發寫入，但單一管理員場景足夠 |
| 2026-04 | 移除 `WWW-Authenticate` header | 避免瀏覽器彈出原生登入視窗，改由前端 CMS 自行處理 401 | 前端需自行管理 auth 狀態 |
| 2026-04 | 圖片上傳改為扁平目錄 | 原本存到 `images/{id}/` 子目錄，前端讀取路徑不一致 | 所有圖片統一存放 `assets/images/` |

### 技術選型

| 層級 | 選擇 | 替代方案 | 選擇理由 |
|------|------|----------|----------|
| 伺服器 | Python 3 stdlib | Node.js, Nginx | 零安裝、零依賴、業主主機已有 Python |
| 前端 | Vanilla JS (ES5 IIFE) | React, Vue | 無 build step、檔案即部署、長期維護無框架升級壓力 |
| 樣式 | 單檔 CSS + Custom Properties | Tailwind, SCSS | 單一檔案易維護，Custom Properties 提供足夠的主題管理能力 |
| 資料 | JSON 檔案 | SQLite, PostgreSQL | 資料量小（<30 篇），JSON 可直接編輯和版控 |
| 部署 | SCP + systemd | Docker, CI/CD | 最低複雜度，適合單人維護 |
| CDN | Cloudflare Tunnel | 自架 Nginx + Let's Encrypt | 免費 SSL、DDoS 防護、零設定 |

## 權衡取捨

### 已知限制

| 限制 | 原因 | 緩解措施 |
|------|------|----------|
| **Hash routing 不利 SEO** | SPA 的 `#detail/{id}` 路由對搜尋引擎不可見 | 計畫產生 `/works/*.html` 靜態頁（見 HANDOVER_PLAN.md） |
| **無併發寫入保護** | JSON 檔案不支援多人同時寫入 | 僅單一管理員使用，實務上無問題 |
| **Cloudflare 快取** | CSS/JS 修改後需手動更新 `?v=` 查詢字串 | 文件已記錄，列入部署 checklist |
| **無自動化測試** | 靜態作品集網站，投入測試的 ROI 低 | 手動測試 + 部署後目視確認 |

### 技術債務

| 債務 | 原因 | 計畫處理時間 |
|------|------|-------------|
| ES5 語法（無模組化） | 初期快速開發，避免 build step | 當 site.js 超過 1500 行時考慮重構 |
| 單檔 CSS 1260 行 | 單一作者維護，尚在可管理範圍 | 當多人協作時拆分為模組 |
| admin 前端內嵌在 HTML | 避免額外建構流程 | 維持現狀，功能穩定 |

## 安全考量

### 認證機制

- HTTP Basic Auth，密碼以 `salt + password` 的 SHA-256 hash 儲存
- `data/config.json` 排除在 git 追蹤之外（`.gitignore`）
- 401 回應不帶 `WWW-Authenticate` header，避免瀏覽器原生彈窗干擾前端認證流程
- admin 前端以 `sessionStorage` 暫存 auth header，關閉分頁即失效

### 已處理風險

| 風險 | 處理方式 |
|------|----------|
| API 未授權存取 | POST/PUT/DELETE/UPLOAD 皆需 Basic Auth |
| JSON 寫入中斷 | Atomic write（temp file + `os.replace`） |
| 圖片上傳惡意檔名 | `re.sub(r"[^\w.\-]", "_", filename)` 過濾 |
| Admin 頁面曝光 | `robots.txt` 禁止爬蟲存取 `/admin` |

### 待改善

- 密碼強度未檢查（目前為簡單密碼）
- 無 HTTPS 層級的 token（依賴 Cloudflare Tunnel 提供 TLS）
- 無上傳檔案大小限制
- 無 rate limiting
