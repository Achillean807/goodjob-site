# 村山良作設計與架構決策

最後更新：2026-07-26

## 品牌方向

網站定位是活動與場景設計事務所的作品集，不是一般活動公司型錄。畫面以留白、編輯感排版與大幅作品攝影建立專業感，紅色只作定位訊號。

### CI 色票

| Token | 色碼 | 用途 |
|---|---|---|
| SALT | `#F2F0EB` | 頁面主底、topbar |
| PAPER | `#FBFAF8` | 卡片與浮起表面 |
| INK | `#222322` | 主文字、深色線條 |
| STONE | `#817C74` | 次要文字、分隔線 |
| POINT | `#9B3E35` | 方形定位點與少量強調 |

全站白底疊加低對比 32px 方格。POINT 不作大面積底色，主要出現在選單 active 狀態、編號、細線與方點。作品影片與大圖舞台可保留黑底，以維持影像對比。

### 排版與圖像

- 中文：`Noto Sans TC`；英文與數字：`Archivo`
- Topbar 使用 `assets/images/logo-topbar-ci.png` 完整品牌字標，不用一般字型重排品牌名稱
- 首頁 Hero 採左文字、右橫式圖片；品牌敘述固定兩行
- 四類作品使用章節式相簿與 masonry 拼貼，不回到等尺寸縮圖牆
- 作品詳情 modal 延續 SALT／INK／STONE／POINT，媒體 stage 保持沉浸式深色
- 分類帽頁保留哈利波特主題，只共用品牌版頭，不強制改成鹽白內容頁

## 系統架構

```text
瀏覽器
├── index.html + assets/site.js + assets/site.css
├── services / teabar / workflow
├── /controlcenter/ 管理後台
└── /works/{id} SSR 作品頁
          │
          ▼
Python server.py（127.0.0.1:10814）
├── 靜態檔案與路由
├── /api/* REST API
├── /works/{id} + JSON-LD
├── /sitemap.xml
├── PostgreSQL goodjob_site
└── rclone → Cloudflare R2
```

### 核心元件

| 元件 | 職責 |
|---|---|
| `server.py` | 靜態服務、文章／相簿／帳號／報價單 API、權限、SSR、sitemap 與 R2 上傳 |
| `assets/site.js` | 取得作品資料、渲染章節相簿、hash routing、預覽、詳情 modal 與 Lightbox |
| `assets/site.css` | CI tokens、共用元件、作品章節與響應式版面 |
| `admin/index.html` + `admin/app.js` | `/controlcenter/` 管理介面 |
| PostgreSQL `goodjob_site` | 正式作品、圖片 URL／順序、帳號、權限與設定 |
| Cloudflare R2 | 作品圖片本體；透過 custom domain 對外提供 |

## 資料流

```text
PostgreSQL ── /api/articles ──> site.js ──> 首頁／分類相簿／詳情 modal
PostgreSQL ── /works/{id} ───> server.py SSR ──> SEO 作品頁
CMS ── 權限 API ─────────────> PostgreSQL
CMS ── 圖片上傳 ─────────────> WebP 轉換 ──> R2 ──> PostgreSQL URL
```

`data/articles.json`、`data/accounts.json`、`data/config.json` 不是 production runtime。正式資料只能透過 PostgreSQL 與既定維運流程處理。

## 關鍵決策

| 日期 | 決策 | 原因 |
|---|---|---|
| 2026-03 | Vanilla HTML／CSS／JS，不設前端 build step | 降低單人長期維護與部署複雜度 |
| 2026-04 | 新增 `/works/{id}` SSR 與動態 sitemap | 讓 hash-based SPA 之外也有可索引的作品網址 |
| 2026-04 | 作品圖遷到 Cloudflare R2 | 降低站台體積並集中圖片交付 |
| 2026-05 | production runtime 切到 PostgreSQL | 支援正式內容、圖片排序、多帳號與權限，隔離舊 JSON 備份 |
| 2026-07 | Netflix 暗色改為鹽白編輯風 CI | 品牌重定位為活動與場景設計事務所 |
| 2026-07 | 首頁改用章節式相簿 | 讓每類作品形成完整世界觀，避免一般縮圖牆感 |
| 2026-07 | 首頁 Hero 改左文右橫圖 | 配合橫式原圖，消除中央空排並讓首屏更緊湊 |

## 維護原則

- 前端維持無打包、無框架；共用視覺先落在 CSS Custom Properties 與既有元件
- `site.js` 維持 IIFE 與既有程式風格，避免為單一功能引入工具鏈
- CSS／JS 變更後更新 HTML 的 `?v=` cache-bust
- 作品 description 存純文字，以空行分段；不可塞 HTML 標籤
- 新增作品遵循 `docs/村山良作-新增作品SOP.md`

## 部署不變條件

1. 禁止整站覆蓋 production，也不可從主機站台目錄直接 `git pull`。
2. 只傳本次明確變更的檔案，先備份遠端同名檔。
3. 部署禁止包含 `data/`；`wedding-packages/images/` 等主機保留資產不可刪除（頁面已於 2026-07-30 下架，images 目錄仍在主機保留、部署仍不可刪）。
4. 部署前後核對 PostgreSQL 的 `articles`、`article_images`、`accounts` 筆數。
5. 重啟 `murayama-goodjob.service` 後，驗證公開 URL、CSS／JS 版本與 service 狀態。

詳見 `docs/村山良作-部署護欄與復原-20260506.md`。
