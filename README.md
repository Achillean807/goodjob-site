# 村山良作 MURAYAMA GOODJOB

品牌活動・主題場景・展場空間 — 作品集展示網站。

## 概述

村山良作是「村花弄囍」旗下的活動佈置品牌官網。以 Netflix 深色主題風格呈現，採用純 HTML/CSS/JS 靜態站架構，搭配 Python stdlib HTTP server 提供 REST API，實現零框架、零依賴的輕量部署。

## 特性

- **Netflix 風格介面**：深色主題（`#141414`）搭配金色強調（`#c4a44a`），作品以橫向捲軸展示
- **四大分類**：主題活動、春酒尾牙、魔法學院、戶政改造
- **SPA 架構**：Hash-based routing，作品詳情以 modal 呈現，含 YouTube 影片嵌入與 Lightbox 圖庫
- **CMS 後台**：`/admin/` 單頁管理介面，支援拖曳排序、圖片上傳、即時預覽
- **零依賴部署**：Python 3 stdlib 即可運行，無需 pip install

## 快速開始

```bash
# 本地開發
cd src
python3 server.py --port 8000
# 瀏覽 http://localhost:8000

# 正式環境
python3 server.py --port 10814
```

## 頁面總覽

| 路徑 | 說明 |
|------|------|
| `/` | 首頁 — Hero 輪播 + 精選作品 + 四大分類作品列 |
| `/teabar.html` | 村花囍茶 — 迎賓花果茶方案展示 |
| `/workflow.html` | 合作流程 — 四步合作說明 + FAQ |
| `/admin/` | CMS 後台 — 文章 CRUD、圖片管理 |
| `/sort-hat/` | 分類帽 — 婚禮座位查詢互動系統（銷售頁） |
| `/wedding-packages/` | 婚禮套組 — 室內/戶外佈置方案展示 |

## REST API

| 方法 | 端點 | 驗證 | 說明 |
|------|------|------|------|
| GET | `/api/articles` | 否 | 取得全部作品 |
| GET | `/api/images/{id}` | 否 | 特定作品圖片清單 |
| POST | `/api/articles` | Basic | 新增作品 |
| PUT | `/api/articles/{id}` | Basic | 更新作品 |
| DELETE | `/api/articles/{id}` | Basic | 刪除作品 |
| POST | `/api/upload/{id}` | Basic | 上傳圖片 |

驗證方式：HTTP Basic Auth，密碼以 salted SHA-256 hash 儲存於 `data/config.json`。

## 目錄結構

```
src/
├── index.html              # 首頁（SPA 入口）
├── teabar.html             # 村花囍茶
├── workflow.html           # 合作流程
├── server.py               # Python HTTP server + REST API（~550 行）
├── robots.txt              # 爬蟲規則
├── sitemap.xml             # 站點地圖
├── llms.txt                # LLM 可讀品牌摘要（AEO）
├── assets/
│   ├── site.css            # 全站樣式（~1260 行）
│   ├── site.js             # SPA 前端邏輯（~1030 行）
│   ├── images/             # 作品圖片
│   └── *.png               # Logo 與 favicon
├── data/
│   ├── articles.json       # 作品資料（27 篇，API 資料來源）
│   ├── config.json         # 管理員帳密設定
│   └── wp_texts.json       # WordPress 原始文案備份
├── admin/
│   └── index.html          # CMS 後台（單檔）
├── sort-hat/
│   ├── index.html          # 分類帽銷售頁（單檔）
│   └── images/             # 銷售頁用圖
└── wedding-packages/
    ├── index.html           # 室內婚禮套組
    ├── outdoor.html         # 戶外婚禮套組
    └── images/              # 套組展示圖
```

## 資料模型

每篇作品（`articles.json`）包含以下欄位：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | string | 唯一識別（kebab-case） |
| `title` | string | 顯示標題 |
| `description` | string | HTML 描述文字 |
| `category` | enum | `business` / `party` / `magic` / `civil` |
| `featured` | boolean | 是否為精選作品 |
| `featuredOrder` | number | 精選排序 |
| `heroImage` | string | 主視覺圖片路徑 |
| `images` | string[] | 圖庫圖片路徑陣列 |
| `videoId` | string? | YouTube 影片 ID |
| `videoVertical` | boolean | 是否為直式影片 |
| `sortOrder` | number | 分類內排序 |

## 部署

```bash
# SCP 部署到正式主機
scp -r src/* achilean@100.102.51.64:/srv/weddingwish/murayama-goodjob-site/

# 若修改 server.py，需重啟服務
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
```

**快取注意**：修改 `site.css` 或 `site.js` 後，須更新所有 HTML 中的 `?v=YYYYMMDD` 查詢字串以清除 Cloudflare 快取。

## 線上網址

- 官網：https://goodjob.weddingwishlove.com/
- 分類帽 Demo：https://g-skyview.weddingwishlove.com/
