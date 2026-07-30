# 村山良作 GOODJOB DESIGN

[正式官網](https://goodjob.weddingwishlove.com/) · 品牌活動、主題場景與展場空間作品集

村山良作是「村花弄囍」旗下的活動設計品牌。網站以鹽白編輯風 CI 呈現作品，前端不需要建置流程；Python 服務負責靜態檔案、作品 API、管理後台與 SEO 作品頁。

## 目前狀態

- 正式站：`https://goodjob.weddingwishlove.com/`
- 正式資料：PostgreSQL `goodjob_site`（64 篇作品）
- 作品圖片：Cloudflare R2／`goodjob-img.weddingwishlove.com`
- 正式服務：`murayama-goodjob.service`，監聽 `127.0.0.1:10814`
- 視覺系統：SALT `#F2F0EB`、INK `#222322`、STONE `#817C74`、POINT `#9B3E35`

> `data/articles.json`、`data/accounts.json`、`data/config.json` 只供舊資料或本機 fallback 使用，不是正式資料源，部署時不可覆蓋 production runtime。

## 功能

- 章節式作品相簿、hover 預覽、詳情 modal、Lightbox 與 YouTube 播放
- 主題活動、春酒尾牙、魔法學院、戶政改造四類作品
- `/works/{id}` 動態 SSR 作品頁與 JSON-LD `CreativeWork`
- `/sitemap.xml` 動態站點地圖
- `/controlcenter/` CMS：作品、相簿、帳號、權限與報價單管理
- 圖片上傳自動轉 WebP 並寫入 Cloudflare R2

## 架構

```text
Cloudflare Tunnel
        │
        ▼
server.py :10814
├── HTML / CSS / Vanilla JS
├── REST API /api/*
├── SSR /works/{id}
└── sitemap.xml
        │
        ├── PostgreSQL goodjob_site（內容、排序、帳號與設定）
        └── Cloudflare R2（作品圖片本體）
```

| 元件 | 用途 |
|---|---|
| `index.html` | 首頁與 SPA 外殼 |
| `assets/site.js` | 作品資料、章節相簿、詳情 modal 與 hash routing |
| `assets/site.css` | 全站 CI tokens 與響應式樣式 |
| `server.py` | 靜態服務、REST API、PostgreSQL、R2 上傳與 SSR |
| `admin/` | `/controlcenter/` 管理介面 |
| `services/` | 四類服務落地頁 |
| `docs/` | 部署、R2、作品新增與災難復原手冊 |

## 頁面

| 路徑 | 說明 |
|---|---|
| `/` | 首頁、精選作品與四類章節式相簿 |
| `/services/business-event/` | 主題活動 |
| `/services/party-spring-banquet/` | 春酒尾牙 |
| `/services/magic-academy/` | 魔法學院 |
| `/services/civil-makeover/` | 戶政改造 |
| `/teabar.html` | 迎賓花果茶 |
| `/workflow.html` | 合作流程 |
| `/sort-hat/` | 分類帽互動工具 |
| `/controlcenter/` | CMS 後台 |

## 本機開發

正式環境要求 PostgreSQL。單純做本機前端 smoke test 時，請明確允許獨立 SQLite，避免碰到 production 資料：

```bash
GOODJOB_ALLOW_SQLITE=1 \
GOODJOB_DB_PATH=/tmp/goodjob-local.sqlite3 \
python3 server.py --port 8000
```

開啟 `http://localhost:8000/`。如需把舊 JSON 備份 seed 到這個暫存 DB，另加 `GOODJOB_ALLOW_JSON_SEED=1`；正式主機不可設定這個值。

## 測試

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

前端變更仍需做瀏覽器視覺驗收；CSS／JS 更新後要同步提升所有 HTML 引用的 `?v=YYYYMMDD[a-z]` cache-bust 版本。

## REST API 摘要

| 方法 | 端點 | 權限 |
|---|---|---|
| `GET` | `/api/articles`、`/api/images/{id}` | 公開 |
| `POST/PUT/DELETE` | `/api/articles...` | 作品寫入／刪除權限 |
| `POST` | `/api/upload/{id}` | 上傳權限 |
| `GET` | `/api/session` | 已驗證 |
| `GET/POST/PUT/DELETE` | `/api/accounts...` | 帳號管理權限 |
| `GET/PUT/DELETE` | `/api/quotes...` | 報價單管理權限 |

## 安全部署

正式路徑是 `/srv/weddingwish/goodjob-sit/`。每次只傳送本次明確變更的檔案，先備份遠端同名檔，再重啟服務並核對 PostgreSQL 筆數。

```bash
# 範例：只部署一個已確認的靜態檔
scp assets/site.css achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/assets/site.css
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
```

禁止使用 `scp -r *`、整站 `rsync --delete` 或在 production 目錄直接 `git pull`。這些作法可能覆蓋 runtime 或主機保留資產。

完整流程請依序閱讀：

1. [`docs/村山良作-部署資訊清單.md`](docs/村山良作-部署資訊清單.md)
2. [`docs/村山良作-部署護欄與復原-20260506.md`](docs/村山良作-部署護欄與復原-20260506.md)
3. [`docs/村山良作-R2-CDN-維運手冊-20260417.md`](docs/村山良作-R2-CDN-維運手冊-20260417.md)
4. [`docs/村山良作-新增作品SOP.md`](docs/村山良作-新增作品SOP.md)

## 專案規範與交接

- [`AGENTS.md`](AGENTS.md)：專案架構、資料邊界與操作規則
- [`DESIGN.md`](DESIGN.md)：品牌視覺與技術設計決策
- [`.planning/.continue-here.md`](.planning/.continue-here.md)：最近一次完成狀態
- [`.planning/HANDOFF.json`](.planning/HANDOFF.json)：結構化交接狀態
