# 村山良作 (Murayama Goodjob)

> 2026-05-05 最新部署狀態：正式站 runtime 資料已改由 PostgreSQL `goodjob_site` 管理。作品文案、相簿圖片 URL/順序、帳號、權限與設定都在 PostgreSQL；圖片檔本體在 Cloudflare R2/CDN。`data/articles.json`、`data/accounts.json`、`data/config.json` 只作為舊資料/備份材料，不再是正式資料源，也不可用部署覆蓋。詳見 `docs/村山良作-部署資訊清單.md`。

> **變更記錄 (Changelog)**
> - 2026-07-25: 全站鹽白編輯風改造完成並上 staging 預覽（v1~v6，commit `28f0ea5`→`0af3c46`）。承 07-24，本輪補齊：`teabar`／`workflow`／婚禮套組(室內外)／`admin` 後台／SSR `/works/{id}`／`services` 四服務頁／`muse-2026` 金獎頁 全套鹽白編輯風；分類帽保留哈利波特深色主題、僅統一版頭(反白 emblem)＋修破圖。收尾微調（村長裁示）：①**官網不明寫價錢**——workflow/party 的「25-60萬」「30-200萬」、婚禮套組所有 NT$ 與原價刪除線拿掉，改順稿「同一種風格可奢華可簡約，差別在預算，請直接告知預算區間讓提案更精準」，保留方案分級＋BEST VALUE、保留「請告知預算區間」引導語；②**一畫面三 LINE 太多**——移除全站 footer 的 LINE 鈕，留頁面 section CTA＋右下浮動 FAB；③MUSE 頁 OG/twitter 分享圖改成美昆蟲展得獎作品 hero。**部署策略（村長要求不覆蓋 production）**：改用現成 staging 環境預覽——`murayama-goodjob-staging.service`(127.0.0.1:10816)→`staging-goodjob.weddingwishlove.com`，與 prod 同 PostgreSQL `goodjob_site`＋R2；staging 部署＝`git reset --hard origin/master`＋從 prod 補主機保留圖＋`restart`。**production 全程未動，待村長逛 staging 確認後喊「切正式站」再上（切時派 fresh-context agent 驗收＋對外 curl，精準不碰 195M 套組圖＋sort-hat 圖）**。踩坑：①staging 部署要從 prod 補「主機保留、repo 無副本」的圖資產——`wedding-packages/images`(195M)＋`sort-hat/images`，首次漏補 sort-hat 圖致破圖。②排查「改了卻看到舊頁」先看 `cf-cache-status`：`DYNAMIC`＝CF 沒快取、是瀏覽器本機快取、Ctrl+Shift+R 解，別誤判為漏改。③複雜 ssh 組合命令（多行＋`$()`嵌套＋引號）會被權限擋，拆單行 `&&` 串。④子頁 `.hero` 與 site.css 裸 `.hero` 碰撞→body-scope(`.wp .hero`)或前綴(`.tea-hero`)。⑤staging 首次部署帶 5/14 舊未提交 WIP，已 tar＋diff patch 備份於主機 `/srv/raid1/backups/goodjob-staging-wip-20260725` 後才 reset。
> - 2026-07-24: 官網改造啟動（新 CI「村山良作 GOODJOB DESIGN」落地，**已上 staging 預覽·production 待切**）。視覺基調自 Netflix 深色轉「鹽白編輯風 studio」（村長拍板方案一，品牌自「活動廠商」重定位為「商業設計事務所」）。已完成並截圖驗收：①CI 四色寫進 `site.css` tokens（鹽白 `#F2F0EB`／墨黑 `#222322`／石灰 `#817C74`／定位紅 `#9B3E35`），移除金色漸層與 Netflix 紅 `#e50914`；版頭改內嵌山形 emblem SVG＋紅色定位方點母題；favicon 換山形多尺寸、OG 換社群模板、英文名全站統一 GOODJOB DESIGN（汰 MURAYAMA GOODJOB）、字體 Sora→Archivo；hero 主圖換「大同戶政・懷舊茶行」（`datong-civil`）。②首頁作品區從「分類縮圖牆」重寫為「章節式相簿」（4 分類＝4 章節，每章沉浸大圖開場＋masonry 拼貼；`site.js` `renderShelf`→`renderChapter`，沿用 detail modal／hash 機制，精選 top10 保留）——村長要「有創意的相簿」。③`teabar`（迎賓花果茶）、`workflow`（合作流程）完成鹽白改造。進行中未完成：`wedding-packages`（室內/戶外）、`admin` 後台、SSR `/works/{id}`、分類帽；**全部未部署**（村長定調全站一致後一起部署）。踩坑：①本機 dev 起站須帶 `GOODJOB_ALLOW_SQLITE=1 GOODJOB_ALLOW_JSON_SEED=1` 才會從 `articles.json` seed 作品資料（server.py「修補 C」預設禁 JSON seed 防主機誤覆蓋線上），否則首頁作品格空。②hero 用 `min-height: Nsvh` 強撐版面會使圖文並排時右側大留白（teabar 踩到，改貼合內容的固定 `min-height` 解）。
> - 2026-07-16: UX 稽核修復迴圈收官（福委會窗口人設，6 輪＋雙簽核，紀錄在 `.ux-audit/`）。修復：works SSR 版頭重建＋頁尾 LINE CTA、modal 返回鍵寫入 hash、teabar 22 張破圖復活、全站選單統一、topbar 疊字、hover 預覽黑框（iframe 淡入 v2）、services 四頁補全站導覽＋版心、is-active 紅底線、`/#shelf` 死錨點。村長裁決：官網不放統編（僅報價單、每份詢問）、16+ 徽章刪除、「婚禮花果茶」全站更名「迎賓花果茶」、DB 36 篇文案清除「來電諮詢」（僅承諾 LINE）、海運尾牙封面換港口航站圖。開工前發現 repo 落後 live 12 檔已同步（教訓：改主機必回寫 repo）。註：`wedding-packages/images/`（195MB）依 R2 手冊 §八屬刻意保留主機的資產，repo 無副本，部署時嚴禁刪除該目錄。
> - 2026-07-15: 作品數校正為 **64 篇**（business 27 / party 18 / civil 14 / magic 5）。追溯：6/10 新增 `guofeng-hsinchu-ambassador`（國風盛宴・新竹國賓）當時漏記 changelog，導致 7/6 誤記為「62→63」（實際 6/10 已達 63、7/6 新增 nccu-qijiaban-43 後為 64）。同步校正 README、DESIGN 的作品數。另完成全站作品文案去 AI 味（22 篇改寫）與暖暖戶政相簿重整。
> - 2026-07-06: 新增作品「政大企家班43屆畢業典禮 · 華章未央」（`nccu-qijiaban-43`，party 春酒尾牙，21 圖，緊鄰43屆迎新），直連正式站 DB + R2 上架，作品數 62→63；新增 `docs/村山良作-新增作品SOP.md` 並索引於本檔。踩坑校正：description 存**純文字**（前端 textContent + CSS pre-wrap），空行分段，禁 HTML 標籤。
> - 2026-05-13: ✅ GATE-1A 解果 — 實測 PostgreSQL `goodjob_site.articles` 共 **62 篇**（business 27 / party 16 / civil 14 / magic 5），舊紀錄 27 為過時值；同步修正全專案文件作品數。
> - 2026-04-17: 從 monorepo 拆分為獨立 repo（`goodjob-site`），圖片遷移至 Cloudflare R2 CDN，admin 上傳端點走 R2，新增多帳號管理系統（`accounts.json` + 5 種 permission + `/api/session` + `/api/accounts` CRUD），新增 migrate/rewrite/cleanup/upload helper 腳本，server.py 擴充至 1099 行。
> - 2026-04-16: 新增 `/works/{id}` 動態 SSR 頁面與 `sitemap.xml` 端點、server.py 更新至 ~730 行（含 WebP 轉換、Pillow 可選依賴）。
> - 2026-04-05: 修正文章數量為 27 篇（後於 2026-05-13 校正為 62）、補充 AEO 設定、新增 outdoor.html、新增 works/ 圖片目錄。
> - 2026-04-03: 初次建立 CLAUDE.md。

## 專案職責

品牌活動、主題場景、展場空間的作品集展示站，搭配輕量 REST API 做文章管理。Netflix 深色主題設計風格。

- **Live**: https://goodjob.weddingwishlove.com/
- **Origin (source)**: https://github.com/Achillean807/goodjob-site
- **Archive (monorepo 時期歷史)**: https://github.com/Achillean807/weddingwish-archive

## 入口與啟動

- **伺服器:** `server.py`（1099 行）— Python 3 stdlib HTTP server
  - 預設 port: 10814（正式環境），可透過 `--port` 設定
  - 提供靜態檔案服務 + JSON API + 動態 SSR（`/works/{id}` + `/sitemap.xml`）
  - R2 上傳走 rclone subprocess，Pillow 為可選依賴
- **前端入口:** `index.html` — SPA，hash-based routing
- **SPA 邏輯:** `assets/site.js`（1054 行）— fetch `/api/articles`、渲染作品方格、詳情 modal
- **樣式:** `assets/site.css`（1254 行）

### 本機開發

```bash
python3 server.py --port 8000
# → http://localhost:8000
```

## 對外接口（REST API）

### 文章
| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/articles` | 公開 | 列出全部 64 篇 |
| GET | `/api/images/{id}` | 公開 | 取單篇圖片清單 |
| POST | `/api/articles` | `articles.write` | 新增 |
| PUT | `/api/articles/{id}` | `articles.write` | 更新欄位 |
| DELETE | `/api/articles/{id}` | `articles.delete` | 刪除 |
| POST | `/api/upload/{id}` | `uploads.write` | 上傳圖片（multipart → WebP q90 → R2） |

### 帳號（2026-04-17 新增）
| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/session` | 已驗證 | 取當前登入帳號 profile |
| GET | `/api/accounts` | `accounts.manage` | 列出全部帳號 |
| POST | `/api/accounts` | `accounts.manage` | 新增帳號 |
| PUT | `/api/accounts/{user}` | `accounts.manage` | 更新帳號 |
| DELETE | `/api/accounts/{user}` | `accounts.manage` | 刪除（擋最後一個 active admin） |

### SEO 端點
| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/works/{id}` | 動態 SSR 作品頁（含 JSON-LD `CreativeWork`） |
| GET | `/sitemap.xml` | 動態生成站點地圖 |

**驗證方式：** HTTP Basic Auth，salted SHA-256 hash。優先查 `accounts.json`（多帳號），fallback 到舊版 `config.json`（單一 admin，全部 permission）。

## 權限與帳號模型

`data/accounts.json`（git-ignored）結構：
```json
{
  "accounts": [{
    "username": "...",
    "passwordHash": "...", "passwordSalt": "...",
    "name": "...",
    "role": "admin" | "editor" | "viewer" | "custom",
    "enabled": true,
    "permissions": ["articles.read", "articles.write", ...],
    "createdAt": "ISO", "updatedAt": "ISO"
  }]
}
```

**5 種 permission：** `articles.read` / `articles.write` / `articles.delete` / `uploads.write` / `accounts.manage`

## 圖片 CDN（R2）

從 2026-04-17 起，作品圖全部走 Cloudflare R2 + custom domain（2.3GB → 252 MiB，-89%）：

- **Bucket**: `goodjob-images`（APAC 區）
- **CDN**: `https://goodjob-img.weddingwishlove.com`
- **URL 結構**: `{CDN}/works/{article.id}/{hero|detail-N|scene-N}.webp`
- **Admin 上傳**：走 rclone subprocess，圖片 Pillow 轉 WebP q90 後直接上 R2
- **維運手冊**：`docs/村山良作-R2-CDN-維運手冊-20260417.md`

保留本機的項目：favicon、logo、og-default、teabar/、wedding-packages/images/（見手冊 §八；頁面已於 2026-07-30 下架，images 目錄仍在主機保留、部署仍不可刪）。

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
  "description": "純文字（空行分段，前端 textContent + pre-wrap 渲染，禁 HTML 標籤）",
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
| CMS 後台 | `admin/index.html` + `admin/app.js` | 文章 CRUD + 帳號管理 |

## 部署

- **主機**：`achilean@100.102.51.64`（Tailscale）
- **路徑**：`/srv/weddingwish/goodjob-sit/`
- **Service**：`murayama-goodjob.service`（systemd，監聽 127.0.0.1:10814）
- **通道**：Cloudflare Tunnel → goodjob.weddingwishlove.com

```bash
scp <files> achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
```

敏感檔（`data/config.json` / `data/accounts.json`）git-ignored，人工管理不隨 repo 同步。

## 維運腳本

| 腳本 | 用途 |
|------|------|
| `migrate_to_r2.py` | 批次將 `assets/images/` 轉 WebP + 上傳 R2，輸出 `path-map.json` |
| `rewrite_paths.py` | 依 path-map 改寫 `articles.json` + HTML 的圖片引用 |
| `cleanup_migrated.py` | 刪除已上 R2 的本機原檔（有 R2 存在驗證）|
| `cleanup_orphans.py` | 搬走沒在源碼引用的孤兒檔到 trash 隔離區（`--restore` / `--purge`）|
| `upload_asset.py` | 單檔上傳 helper（新頁面插圖拿 R2 URL）|
| `convert_images_to_webp.py` | 舊的 WebP 批次轉檔（已被 migrate_to_r2 取代，保留歷史參考）|

## 新增作品 SOP

新增一篇作品（選圖 → 轉檔 → 上 R2 → 寫 DB → 驗證）照 **`docs/村山良作-新增作品SOP.md`** 走。該 runbook 記錄實測路徑：SSH 進龍蝦之家主機直接操作 PostgreSQL `goodjob_site` + rclone，走 peer-auth **免任何後台明文憑證**；含轉檔參數（對齊 `server.py`，額外補 `exif_transpose`）、`{id}-{N}.webp` 命名鐵律、純 INSERT SQL 骨架、四步驗證儀式與 Windows SSH 傳中文鐵律。

## 測試與品質

無自動化測試。手動流程：
1. 本機跑 `python3 server.py --port 8000`
2. 瀏覽器視覺檢查
3. `/controlcenter/` 測 CRUD + 帳號管理
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
A: `/controlcenter/` CMS 後台上傳。圖片自動轉 WebP + 上 R2，articles.json 自動更新。

**Q: 如何新增 admin 帳號？**
A: 用既有 admin 登入 `/controlcenter/` → 帳號管理 UI，或 Basic Auth 直接打 `POST /api/accounts`。系統擋最後一個 active admin 被刪或停用。

**Q: 圖片部署後沒更新？**
A: R2 URL 不變所以圖片本身快取沒問題。若是 CSS/JS 要升 `?v=...` 查詢字串強制 CF edge 重抓。

**Q: admin 上傳回 500？**
A: 檢查 `sudo systemctl status murayama-goodjob` 有沒有 `[r2-upload]` 錯誤；用 `sudo -u achilean /home/achilean/bin/rclone ls r2:goodjob-images | head` 測憑證。

**Q: 某張圖 404？**
A: `articles.json` 有 URL 但 R2 沒檔。`rclone ls r2:goodjob-images/works/{slug}/` 對照，缺的用 `migrate_to_r2.py --article {slug}` 補。

**Q: 路由如何運作？**
A: `site.js` hash-based SPA routing（`#detail/{id}`）前端互動 + server.py 動態 SSR `/works/{id}` 供 SEO/AEO 索引。

**Q: wedding-packages 的圖片在哪？**
A: 頁面已於 2026-07-30 下架（301 至村花主站 /services/packages），主機 `wedding-packages/images/`（195M）暫保留原地未刪。

## 核心檔案清單

| 檔案 | 行數 | 用途 |
|------|------|------|
| `server.py` | 1099 | HTTP 伺服器 + REST API + R2 upload + accounts + SSR |
| `assets/site.js` | 1054 | SPA 前端邏輯 |
| `assets/site.css` | 1254 | 所有樣式 |
| `admin/index.html` + `admin/app.js` | — | CMS 後台（文章 + 帳號管理）|
| `index.html` | — | 首頁模板 |
| `data/articles.json` | — | 舊資料備份（正式資料源已切至 PostgreSQL `goodjob_site.articles` 共 64 篇） |
| `data/config.json` | git-ignored | 舊版單一 admin（fallback） |
| `data/accounts.json` | git-ignored | 多帳號 + permissions |
| `path-map.json` | — | R2 遷移反查表（回滾用） |
| `llms.txt` | ~65 | LLM 可讀品牌摘要 |
| `robots.txt` | 6 | 爬蟲規則 + LLMs-Txt 指向 |
| `DESIGN.md` | — | 設計決策文件 |
| `docs/村山良作-R2-CDN-維運手冊-20260417.md` | — | R2 遷移與維運完整說明 |
