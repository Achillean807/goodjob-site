# 村山良作 (Murayama Goodjob)

> **變更記錄 (Changelog)**
> - 2026-04-17: 從 monorepo 拆分為獨立 repo（`goodjob-site`），圖片遷移至 Cloudflare R2 CDN，admin 上傳端點走 R2，新增 migrate/rewrite/cleanup/upload helper 腳本。
> - 2026-04-16: 新增 `/works/{id}` 動態 SSR 頁面與 `sitemap.xml` 端點、server.py 更新至 ~730 行（含 WebP 轉換、Pillow 可選依賴）。
> - 2026-04-05: 修正文章數量為 27 篇、補充 AEO 設定、新增 outdoor.html、新增 works/ 圖片目錄。
> - 2026-04-03: 初次建立 CLAUDE.md。

## 專案職責

品牌活動、主題場景、展場空間的作品集展示站，搭配輕量 REST API 做文章管理。Netflix 深色主題設計風格。

- **Live**: https://goodjob.weddingwishlove.com/
- **Origin (source)**: https://github.com/Achillean807/goodjob-site
- **Archive (monorepo 時期歷史)**: https://github.com/Achillean807/weddingwish-archive

## 入口與啟動

- **伺服器:** `server.py`（~770 行）— Python 3 stdlib HTTP server
  - 預設 port: 10814（正式環境），可透過 `--port` 設定
  - 提供靜態檔案服務 + JSON API + 動態 SSR（`/works/{id}` + `/sitemap.xml`）
- **前端入口:** `index.html` — SPA，hash-based routing
- **SPA 邏輯:** `assets/site.js`（~1030 行）— fetch `/api/articles`、渲染作品方格、詳情 modal

### 本機開發

```bash
python3 server.py --port 8000
# → http://localhost:8000
```

## 對外接口（REST API）

| 方法 | 端點 | 驗證 | 說明 |
|------|------|------|------|
| GET | `/api/articles` | 否 | 列出全部文章 |
| GET | `/api/images/{id}` | 否 | 特定文章的圖片清單 |
| POST | `/api/articles` | Basic | 新增文章 |
| PUT | `/api/articles/{id}` | Basic | 更新文章欄位 |
| DELETE | `/api/articles/{id}` | Basic | 刪除文章 |
| POST | `/api/upload/{id}` | Basic | 上傳圖片（multipart → WebP q90 → R2） |
| GET | `/works/{id}` | 否 | 動態 SSR 作品頁（含 JSON-LD `CreativeWork`） |
| GET | `/sitemap.xml` | 否 | 動態生成站點地圖 |

驗證方式：HTTP Basic Auth，salted SHA-256 hash 儲存於 `data/config.json`。

## 圖片 CDN（R2）

從 2026-04-17 起，作品圖全部走 Cloudflare R2 + custom domain：

- **Bucket**: `goodjob-images`（APAC 區）
- **CDN**: `https://goodjob-img.weddingwishlove.com`
- **URL 結構**: `{CDN}/works/{article.id}/{hero|detail-N|scene-N}.webp`
- **Admin 上傳**：走 rclone subprocess，圖片 Pillow 轉 WebP q90 後直接上 R2
- **維運手冊**：`docs/村山良作-R2-CDN-維運手冊-20260417.md`

保留本機的項目：favicon、logo、og-default、teabar/、wedding-packages/images/（見手冊 §八）。

## 關鍵依賴

| 依賴 | 用途 | 必要性 |
|------|------|--------|
| Python stdlib | server.py 主體 | 必要 |
| Pillow | WebP 轉檔 | 強建議（admin 上傳會用到）|
| pillow-avif-plugin | AVIF 偽裝 jpg 解碼 | 建議（歷史圖片有 AVIF 誤命名）|
| rclone | R2 上傳（subprocess 呼叫）| 主機必要，本機可選 |

### 主機環境變數（systemd override `/etc/systemd/system/murayama-goodjob.service.d/r2.conf`）

```ini
[Service]
Environment="GOODJOB_RCLONE_BIN=/home/achilean/bin/rclone"
Environment="GOODJOB_R2_REMOTE=r2:goodjob-images"
Environment="GOODJOB_CDN_DOMAIN=https://goodjob-img.weddingwishlove.com"
Environment="GOODJOB_WEBP_QUALITY=90"
Environment="HOME=/home/achilean"
```

## 資料模型

**`data/articles.json`** 結構：`{ "articles": [ ... ] }`

```json
{
  "id": "kebab-case-slug",
  "title": "顯示標題",
  "description": "HTML 描述文字",
  "category": "party" | "business" | "civil" | "magic",
  "featured": true/false,
  "featuredOrder": 0,
  "heroImage": "https://goodjob-img.weddingwishlove.com/works/{id}/hero.webp",
  "images": ["https://goodjob-img.weddingwishlove.com/..."],
  "linkUrl": "/pages/{id}.html",
  "videoId": "youtube-id 或 null",
  "videoVertical": true/false,
  "sortOrder": number,
  "updatedAt": "ISO datetime"
}
```

分類：`business`（主題活動）、`party`（春酒尾牙）、`magic`（魔法學院）、`civil`（戶政改造）

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

## 部署

- **主機**：`achilean@100.102.51.64`（Tailscale）
- **路徑**：`/srv/weddingwish/goodjob-sit/`
- **Service**：`murayama-goodjob.service`（systemd，監聽 127.0.0.1:10814）
- **通道**：Cloudflare Tunnel → goodjob.weddingwishlove.com

```bash
scp <files> achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
```

## 維運腳本

| 腳本 | 用途 |
|------|------|
| `migrate_to_r2.py` | 批次將 `assets/images/` 轉 WebP + 上傳 R2，輸出 `path-map.json` |
| `rewrite_paths.py` | 依 path-map 改寫 `articles.json` + HTML 的圖片引用 |
| `cleanup_migrated.py` | 刪除已上 R2 的本機原檔（有 R2 存在驗證）|
| `cleanup_orphans.py` | 搬走沒在源碼引用的孤兒檔到 trash 隔離區（`--restore` / `--purge`）|
| `upload_asset.py` | 單檔上傳 helper（新頁面插圖拿 R2 URL）|
| `convert_images_to_webp.py` | 舊的 WebP 批次轉檔（已被 migrate_to_r2 取代，保留歷史參考）|

## 測試與品質

無自動化測試。手動流程：
1. 本機跑 `python3 server.py --port 8000`
2. 瀏覽器視覺檢查
3. `/admin/` 測 CRUD
4. 部署後確認線上

## 編碼規範

- **HTML**: 語意化 HTML5，lang `zh-Hant`，完整 OG + Twitter Card meta
- **CSS**: 單一 `site.css`，CSS Custom Properties，無預處理器
- **JS**: ES5 IIFE，`'use strict'`，無模組打包
- **Python**: stdlib-only 原則；`_write_json_atomic` 保護資料檔
- **快取清除**: 編輯 CSS/JS 後更新所有 HTML 引用的 `?v=YYYYMMDD[字母]`
- **Commit**: 繁體中文

## 常見問題 (FAQ)

**Q: 如何新增作品？**
A: `/admin/` CMS 後台上傳。圖片自動轉 WebP + 上 R2，articles.json 自動更新。

**Q: 圖片部署後沒更新？**
A: R2 URL 不變所以圖片本身快取沒問題。若是 CSS/JS 要升 `?v=...` 查詢字串強制 CF edge 重抓。

**Q: 路由如何運作？**
A: `site.js` hash-based SPA routing（`#detail/{id}`）前端互動 + server.py 動態 SSR `/works/{id}` 供 SEO/AEO 索引。

**Q: wedding-packages 的圖片在哪？**
A: `wedding-packages/images/` 下的 `classic/`、`deluxe/`、`carousel/`（暫未遷 R2，保留本機）。

## 核心檔案清單

| 檔案 | 行數 | 用途 |
|------|------|------|
| `server.py` | ~770 | HTTP 伺服器 + REST API + R2 upload + SSR |
| `assets/site.js` | ~1030 | SPA 前端邏輯 |
| `assets/site.css` | ~1260 | 所有樣式 |
| `index.html` | ~120 | 首頁模板 |
| `data/articles.json` | - | 作品資料（單一資料來源） |
| `data/config.json` | 5 | 管理員驗證設定 |
| `llms.txt` | ~65 | LLM 可讀品牌摘要 |
| `robots.txt` | 6 | 爬蟲規則 + LLMs-Txt 指向 |
| `DESIGN.md` | - | 設計決策文件 |
| `docs/村山良作-R2-CDN-維運手冊-20260417.md` | - | R2 遷移與維運完整說明 |
