# 村山良作（Murayama Goodjob）— Project Charter

> 由 `/gsd-ingest-docs` 於 2026-05-13 從 1 份外部 PRD（`docs/seo-aeo-improvement-plan-20260513.html`）合成建立。本檔記錄專案身分、技術棧與非功能性需求底線；部署細節、API 端點清單以 `CLAUDE.md` 為準，不於此重複。

---

## 專案身分

| 欄位 | 值 |
|------|----|
| 專案名稱 | 村山良作（MURAYAMA GOODJOB） |
| 專案 slug | `murayama-goodjob` / `goodjob-site` |
| 母品牌 | 村花弄囍（WeddingWish Love） |
| 創辦人 / 產品負責人 | 秦壽崙（村長 / Achillean） |
| Live URL | https://goodjob.weddingwishlove.com/ |
| Origin（source） | https://github.com/Achillean807/goodjob-site |
| 設計風格 | Netflix 深色主題 |
| 專案性質 | 既已上線運行；當前 milestone 為 SEO/AEO 90 天改善 |

---

## 產品描述

村山良作是村花弄囍旗下的「品牌活動、主題場景、展場空間」作品集展示站，搭配輕量 REST API 做文章管理。對外服務五大內容集群：品牌活動佈置、展場空間設計、春酒尾牙佈置、戶政空間改造、婚禮場景佈置。站上集結品牌活動（Lativ / Wacoal / CXO / 瓶蓋工廠）、戶政空間改造（大安／中正／暖暖／仁愛／中山／大同／七堵）、春酒尾牙、魔法學院主題派對等案例，並透過 `/works/{id}` SSR、`/sitemap.xml` 動態生成支援搜尋引擎與 AI 引擎索引。Milestone v1.0 的目標是 90 天內把 SEO 估分 7.4 推到 8.5+、AEO 估分 6.2 推到 8.5+。

---

## 技術棧（高階）

| 層級 | 技術 | 備註 |
|------|------|------|
| 伺服器 | Python 3 stdlib HTTP server（`server.py`，1099 行） | 無 framework；REST API + 動態 SSR |
| 渲染策略 | SSR + SPA 混合 | `/works/{id}`、`/sitemap.xml` 為 SSR；首頁為 hash-based SPA |
| 資料庫 | PostgreSQL 16（runtime 正式資料源） | 作品文案、相簿、帳號、權限、設定 |
| 舊備份資料 | `data/articles.json`、`data/accounts.json`、`data/config.json` | 僅作備份／參考，不再是正式資料源 |
| 圖片 CDN | Cloudflare R2 + custom domain（`goodjob-img.weddingwishlove.com`） | 全部作品圖；wedding-packages 圖檔暫留本機 |
| 圖片轉檔 | Pillow（WebP q90） + rclone（R2 上傳） | admin 上傳鏈路 |
| 部署 | systemd `murayama-goodjob.service` → Cloudflare Tunnel | 主機 ACH-ClawHome（Tailscale `100.102.51.64`），:10814 |
| 驗證 | HTTP Basic Auth + salted SHA-256 | `accounts.json`（多帳號 + 5 種 permission） |
| 既有 SEO/AEO 資產 | `robots.txt`（6 行）、`llms.txt`（~65 行）、JSON-LD（LocalBusiness / Service / FAQPage / CreativeWork） | `/quote/` 已有 noindex；`/admin/` 尚未補 |

部署、API 端點完整清單、權限模型細節、維運腳本：以 `CLAUDE.md` 為唯一來源。

---

## Locked Decisions

> 本批 ingest 僅匯入 1 份 PRD（precedence=0，locked=false），未產生 ADR 等級的 LOCKED 決策。
>
> 6 條方向性 proposed 決策已收錄於 `.planning/STATE.md` 的「待升格 ADR 候選」段落，實作期間若村長要求鎖定，可由後續 `/gsd-ingest-docs adr/...` 升格為正式 ADR。

| ADR ID | 標題 | 狀態 |
|--------|------|------|
| — | （尚無 LOCKED 決策） | — |

---

## Non-Functional Requirements（NFR）

以下 9 條限制由本批 PRD 萃取，定義 v1.0 全期間必須遵守的底線；完整內容見 `.planning/intel/constraints.md`。

### 索引與可爬性

- **CONSTR-indexation-targets** — 公開頁 90%+ 可索引；私有頁（`/admin/`、`/quote/`）索引筆數須為 0。
- **CONSTR-private-page-noindex** — 私有頁必須 robots disallow **與** `X-Robots-Tag: noindex, nofollow, noarchive` 雙保險，缺一不可。
- **CONSTR-ai-crawler-allowlist** — `OAI-SearchBot`、`PerplexityBot` 在公開區段必須可抓；Cloudflare WAF 不可 block；robots.txt 結尾保留 `Sitemap:` 與 `LLMs-Txt:` production URL。
- **CONSTR-non-js-readable** — 首頁精選案例與服務內鏈須在 server-rendered HTML 可見；動態作品頁 `/works/{id}` 必須維持 SSR，不可改成純 SPA。

### 結構化資料與內容規格

- **CONSTR-schema-text-consistency** — JSON-LD 宣告的標題、描述、圖片必須在頁面可見區塊真實出現；違反者會被視為 spammy structured data。
- **CONSTR-faq-answer-length** — FAQ 答案 60-120 中文字直接回答，並以 `FAQPage` schema 標記。
- **CONSTR-description-length** — 首頁與支援頁 meta description 須擴充到 70-110 中文字，避免過短被 Google 重寫。

### 技術品質與 KPI 紀律

- **CONSTR-technical-cwv-good** — LCP / INP / CLS 三項 Core Web Vitals 全達 Good；公開頁均為 HTTP 200；主要 schema 通過 validation 無錯誤。
- **CONSTR-non-deterministic-ai** — AI 引用為非決定性；對外不承諾保證引用率；AEO/GEO KPI 採「先建 baseline、後追蹤變化」策略，每次重測使用同一組 prompts。

### 資料前置依賴（Gate）

- **CONSTR-data-availability-gaps** — 啟動 P1/P2 前必須備齊：
  1. GSC 最近 3-6 個月 query/page 資料
  2. GA4 或 server log（自然搜尋、ChatGPT/Perplexity referral、LINE CTA 點擊）
  3. 正式 PostgreSQL 作品數與正式 sitemap 實際輸出
  4. 4 個 AI 平台同一組 prompts 的 citation baseline

  資料未就緒 → 對應 phase 不可啟動或不可驗收。本約束於 ROADMAP 對應 phase 的「前置 gate」欄位明確展開。

---

## 範圍邊界（v1.0）

| 包含 | 不包含 |
|------|--------|
| SEO 技術修補（sitemap、noindex、metadata、schema） | 全站改版 / 重寫前端框架 |
| 5 大 pillar 頁新建 + 作品 cluster 對應 | 第三方 CMS 遷移 |
| AI citation baseline + lost-prompts 修補包 | 跨語系（英文站）擴充 |
| 權威訊號頁（awards / press / GBP） | 付費廣告投放 |
| GSC / GA4 / AI referral 週報 dashboard | CRM 整合、自動化行銷 |

---

## 變更紀錄

- 2026-05-13：由 `/gsd-ingest-docs` 從 PRD `docs/seo-aeo-improvement-plan-20260513.html` 首次建立。
