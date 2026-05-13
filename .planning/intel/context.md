# 專案背景脈絡

> 由 `gsd-doc-synthesizer` 從 PRD `docs/seo-aeo-improvement-plan-20260513.html` 與既有專案 `CLAUDE.md` 對照後萃取，作為 roadmapper 撰寫 PROJECT.md / CONTEXT.md 的素材。

---

## 專案身分

- **品牌：** 村山良作（MURAYAMA GOODJOB）
- **母品牌：** 村花弄囍
- **網站：** https://goodjob.weddingwishlove.com/
- **定位：** 品牌活動、主題場景、展場空間的作品集展示站，搭配輕量 REST API 做文章管理
- **設計風格：** Netflix 深色主題

來源：PRD § 一執行摘要、CLAUDE.md 專案職責

---

## 技術棧現況

| 層級 | 技術 | 備註 |
|------|------|------|
| 伺服器 | Python 3 stdlib HTTP server（`server.py`，1099 行） | port 10814，無 framework |
| 渲染 | SSR + SPA 混合 | `/works/{id}` 與 `/sitemap.xml` 由 server.py 動態 SSR；首頁為 SPA hash routing |
| 資料庫 | PostgreSQL 16（正式環境） | `data/articles.json` 已退役為備份／舊資料源 |
| 圖片 CDN | Cloudflare R2 + custom domain（`goodjob-img.weddingwishlove.com`） | 全部作品圖；wedding-packages 圖檔暫留本機 |
| 部署 | systemd `murayama-goodjob.service` → Cloudflare Tunnel | 主機 ACH-ClawHome（Tailscale `100.102.51.64`） |
| 圖片轉檔 | Pillow（WebP q90） + rclone（R2 上傳） | admin 上傳走此鏈路 |
| 驗證 | HTTP Basic Auth + salted SHA-256 | `accounts.json`（多帳號 + 5 種 permission） |

來源：CLAUDE.md 入口、依賴、部署章節；PRD § 二「動態作品頁」「Sitemap」

---

## 既有 SEO/AEO 基礎建設

- **既有 metadata：** 首頁、合作流程、囍茶、MUSE 與作品 SSR 已有 title / description / canonical / OG / Twitter / 部分 schema
- **既有 schema：** LocalBusiness、Service、FAQPage、CreativeWork
- **既有 AI 資產：** `llms.txt`（約 65 行，LLM 可讀品牌摘要）、`robots.txt`（6 行）
- **既有私有頁保護：** `/quote/` 已加 robots Disallow + `X-Robots-Tag`
- **既有 SSR：** `/works/{id}` 動態 SSR（含 JSON-LD CreativeWork）、`/sitemap.xml` 動態生成

來源：PRD § 一執行摘要、§ 二現況發現；CLAUDE.md SEO 端點

---

## 評分現況與目標

| 項目 | 當前推估 | 90 天目標 |
|------|----------|-----------|
| SEO 現況 | 7.4 / 10 | 8.5+ |
| AEO / GEO 現況 | 6.2 / 10 | 8.5+ |

- SEO 缺口集中在：支援頁 metadata、私有頁 noindex、內容集群、Search Console 驗證
- AEO 缺口：未建立 4 大 AI 平台（ChatGPT / Claude / Gemini / Perplexity）的引用 baseline，無法量化能見度

來源：PRD § 一執行摘要 評分卡

---

## 內容資產現況

- **既有作品數：** 27 件（CLAUDE.md）／ 29 件（PRD 推估）— **待正式環境 PostgreSQL 確認**
- **分類欄位：** `business`（主題活動）、`party`（春酒尾牙）、`magic`（魔法學院）、`civil`（戶政改造）
- **既有支援頁：**
  - `/teabar.html` ─ 村花囍茶
  - `/workflow.html` ─ 合作流程
  - `/sort-hat/` ─ 分類帽（婚禮座位查詢，Harry Potter 主題）
  - `/wedding-packages/` ─ 婚禮套組（室內）
  - `/wedding-packages/outdoor.html` ─ 婚禮套組（戶外）
  - `/admin/` ─ CMS 後台

來源：CLAUDE.md 子頁面、資料模型；PRD § 二「動態作品頁」

---

## 90 天路線圖（PRD 提案的高階分段）

| 階段 | 期間 | 主軸 |
|------|------|------|
| P0 | 第 1-2 週（7 天起跑） | 技術修補、正式 sitemap 驗證、admin noindex、支援頁 metadata/schema、GSC URL Inspection |
| P1 | 第 3-4 週與第 5-8 週 | GSC 匯出、cannibalization map、服務 pillar 架構、內鏈規劃、上線 pillar 頁、改作品案例模板、補 FAQ／比較表、更新 llms.txt |
| P2 | 第 5-8 週（與 P1 重疊） | AI citation baseline、lost prompts 修補包、比較頁、robots/WAF 允許 AI bots |
| P3 | 第 9-12 週 | AI citation recheck、競品 gap、外部權威訊號（得獎媒體頁 / GBP / 媒體稿）、月報與下一輪內容排程 |

來源：PRD § 三 改善計畫、§ 六 時程

---

## 5 大內容集群（規劃中）

| Cluster | Pillar 路徑（建議新建） | 既有支援作品 |
|---------|--------------------------|--------------|
| 品牌活動佈置 | `/services/brand-event-decoration/` | Lativ、Wacoal、CXO、瓶蓋工廠、曾師傅 |
| 展場空間設計 | `/services/exhibition-space-design/` | 成美文化園昆蟲展、MUSE 得獎頁 |
| 春酒尾牙佈置 | `/services/year-end-party-decoration/` | 海運尾牙、特務舞會、政大企家班 |
| 戶政空間改造 | `/services/civil-office-transformation/` | 大安、中正、暖暖、仁愛、中山、大同、七堵戶政案例 |
| 婚禮場景佈置 | `/wedding-packages/` + `/teabar.html`（既有） | 送客背景、戶外證婚、套組、迎賓茶 |

來源：PRD § 四 內容集群與頁面規劃

---

## 必要外部資料源（前置依賴）

PRD § 六 列出啟動 P1/P2 前必須備齊的資料：

1. **Google Search Console** 最近 3-6 個月 `page + query` 資料
2. **GA4 或 server log**：自然搜尋、ChatGPT/Perplexity referral、LINE CTA 點擊
3. **正式 PostgreSQL 作品數** 與**正式 sitemap 實際輸出**
4. **4 個 AI 平台**（ChatGPT、Claude、Gemini、Perplexity）同一組 prompts 的 citation baseline

來源：PRD § 六「必要資料缺口」

---

## AEO 修補包 4 大類

1. **Entity clarity** — 統一品牌名「村山良作 MURAYAMA GOODJOB」、母品牌「村花弄囍」、服務範圍、所在地、sameAs
2. **Prompt-matched FAQ** — 把「怎麼選、多少錢、要準備什麼、多久前洽詢、適合哪些活動」做成短答案
3. **Comparison pages** — 「品牌活動佈置 vs 展場設計」、「客製佈置 vs 套組方案」等中立比較頁
4. **Third-party proof** — 整理 MUSE 得獎、合作單位、媒體報導、社群案例，並取得外部頁面連回

來源：PRD § 五 AI 引用修補包

---

## 官方規範參考

PRD § 七 列出 5 個權威來源，後續實作須對齊：

- Google Search Central — AI features and your website
- Google Search Technical Requirements
- Google Structured Data Markup Supported Features
- OpenAI Publishers and Developers FAQ（含 `utm_source=chatgpt.com` referral 追蹤）
- Perplexity Crawlers（含 `PerplexityBot` 與官方 IP 允許）
