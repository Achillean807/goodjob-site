# Phase 3: P1-B 作品模板 + Cluster Mapping + FAQ — Execution Plan

**Phase ID:** 3
**Planning written:** 2026-05-14 21:42 GMT+8
**Based on:** 03-CONTEXT.md（domain / decisions / specifics）
**Status:** Ready for execution（待 GATE-3B/3C/3D 三項決策村長 confirm 後啟動）

---

## 執行原則

- 每 plan 標 `autonomous=true / partial / false` 指引派發方式
- `autonomous=true` → Opus 直接派 codex CLI（spec heredoc）或 Sonnet subagent
- `autonomous=partial` → 部分機械化動作派發，最終決策 / 文案輸入 Opus 親自
- `autonomous=false` → 純人工執行（村長 / Opus）
- 順序執行，3.0 GATE 解鎖前不啟 3.1+

---

## Plan 3.0 — GATE-3B/3C/3D 三項決策對齊（30 min）

**Type:** `autonomous=false`（純人工，村長決策）

**目標：** 把 3 個儲存模型決策三選一鎖定，避免後續 plan 重排。

**動作：**
1. Opus 透過 `AskUserQuestion` 一次呈現 3 個 GATE 給村長：
   - GATE-3B：cluster mapping 用 `category` / 新欄位 `cluster` / JSONB `clusters[]`？
   - GATE-3C：6 區塊存 `case_blocks JSONB` / 6 個獨立 column / 獨立 `case_studies` 表？
   - GATE-3D：FAQ 寫 HTML 硬編碼 / 新表 `cluster_faqs` / `data/faqs.json`？
2. 村長 confirm 後，本小姐升 3 條 LOCKED decision 寫進 `.planning/intel/decisions.md`

**驗收：** 3 條 LOCKED decision 寫入 + 03-CONTEXT.md `<decisions>` 段標 LOCKED + commit `docs(planning): GATE-3B/3C/3D LOCKED`

**Blocker for:** 3.1, 3.2, 3.4

---

## Plan 3.1 — PostgreSQL schema 擴充 + admin UI 補欄位（2-3h）

**Type:** `autonomous=true`（codex 派發；spec 明確）

**前置：** 3.0 LOCKED 採方案 A（推薦）— 沿用 `category` + 新增 `case_blocks JSONB`

**目標：** PostgreSQL `articles` 表加 `case_blocks JSONB` 欄位 + admin 後台 6 個 textarea 可編輯

**動作：**
1. 連 ach-clawhome ssh achilean@100.102.51.64
2. `psql goodjob_site` 跑 `ALTER TABLE articles ADD COLUMN case_blocks JSONB NOT NULL DEFAULT '{}'`
3. 驗證 `\d articles` 含 case_blocks 欄位
4. `server.py` `/api/articles` PUT handler 加 case_blocks 欄位寫入 + GET 回傳
5. `admin/app.js` + `admin/index.html` 編輯介面加 6 個 textarea（背景 / 限制 / 策略 / 亮點 / 產業 / 成果）
6. 本機 server.py + admin 測試：建立 / 編輯 / 讀取 case_blocks 都正常

**驗收：**
- `psql goodjob_site -c "SELECT case_blocks FROM articles LIMIT 1"` 回 `{}`
- admin 後台編輯任一作品 → 填 6 區塊 → save → reload 後資料完整保留
- `curl /api/articles` JSON 回應含 `case_blocks` 物件

**Commit:** `feat(db): articles 表加 case_blocks JSONB + admin UI 6 區塊編輯`

---

## Plan 3.2 — server.py `_serve_works_page` SSR 6 區塊渲染 + pillar breadcrumb（3-4h）

**Type:** `autonomous=true`（codex 派發；spec 明確）

**前置：** 3.1 完成

**目標：** `/works/{id}` SSR 動態頁渲染 6 區塊 + 自動依 category 補 pillar breadcrumb + 返回 pillar CTA

**動作：**
1. 改 `_serve_works_page`（server.py L1651-）：
   - 讀 `articles.case_blocks` JSONB
   - 6 個 `<section class="case-block">`（背景 / 限制 / 策略 / 亮點 / 產業 / 成果），未填區塊 fallback 顯示既有 description（只第一次）
   - 補 BreadcrumbList JSON-LD：村山良作 → /services/{category-slug}/ → 作品標題（3 層）
   - 頁面底加 `<aside class="back-to-pillar">` 含「← 返回 {pillar 名稱}」CTA
   - `<head>` 加 `<link rel="up" href="/services/{slug}/">`
2. cluster slug 映射表（hardcoded 在 server.py）：
   - `business` → `business-event`
   - `party` → `party-spring-banquet`
   - `civil` → `civil-makeover`
   - `magic` → `magic-academy`
3. 5 個樣本 URL 本機驗證：`curl http://localhost:10814/works/{id}` 確認 6 區塊 + breadcrumb 渲染正常

**驗收：**
- 5 個 sample `/works/{id}` curl 結果含 `<section class="case-block">` × 6
- BreadcrumbList JSON-LD 含 3 層
- 返回 pillar CTA 連結正確

**Commit:** `feat(seo): /works/{id} SSR 補 6 區塊 + pillar breadcrumb + 返回 CTA`

---

## Plan 3.3 — 5 cluster × 4-6 題 FAQ 內容撰寫（4-6h）

**Type:** `autonomous=partial`（內容草擬可 Sonnet/codex；最終 review 必須村長）

**前置：** 3.0 LOCKED 採方案 A（推薦）— HTML 硬編碼

**目標：** 5 pillar HTML 內 `<section class="pillar-faq">` placeholder 全部填上 4-6 題答案（60-120 字）

**動作：**
1. Opus 草擬 5 cluster × 5 題 = 25 題 FAQ + 答案（每題 60-120 字）
   - 派 Sonnet subagent 草擬第一版（依 Phase 2 服務介紹文案 + 既有作品 description）
   - Opus 親自 review 修辭、刪冗、補事實
2. AskUserQuestion 整批呈給村長 review（每 cluster 一輪）
3. 確認後寫進 5 個 pillar `index.html` 對應 `<section class="pillar-faq">`
4. 結構建議：`<details><summary>` 配 `<div class="faq-answer">`（人類可讀）

**驗收：**
- 5 pillar HTML grep `<details>` 各 ≥ 4 個
- 每個答案中文字數 60-120（用 Python 腳本確認）
- 村長確認文案

**Commit:** `feat(seo): 5 pillar FAQ 內容上線（5 cluster × 4-6 題 / 60-120 字）`

---

## Plan 3.4 — 5 pillar FAQPage JSON-LD schema 包覆（1h）

**Type:** `autonomous=true`（codex 派發）

**前置：** 3.3 完成

**目標：** 5 pillar 各補 1 個 `FAQPage` schema，內容與 HTML FAQ 1:1 對應

**動作：**
1. 從 3.3 寫好的 FAQ HTML 萃取 question / answer 字串
2. 5 pillar HTML 內 `</head>` 前補 `<script type="application/ld+json">` 段：
   ```json
   { "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [...] }
   ```
3. 跑 Google Rich Results Test 線上工具驗 5 個 URL

**驗收：**
- 5 pillar HTML grep `"@type": "FAQPage"` 各 1
- Rich Results Test 5 URL 全綠（0 error）

**Commit:** `feat(seo): 5 pillar FAQPage JSON-LD schema 上線`

---

## Plan 3.5 — 既有 10 件作品補完 6 區塊（6-10h）

**Type:** `autonomous=partial`（資料萃取可派 Sonnet；文案 review 由村長）

**前置：** 3.1 + 3.2 完成

**目標：** 從 62 件中選出代表性 10 件（每 cluster ≥ 2 件），補完 6 區塊內容

**動作：**
1. 村長選 10 件代表作品（或 Opus 推薦 + 村長 confirm）
2. 對每件作品：
   - 派 Sonnet 從既有 description + 圖片 caption 萃取「背景 / 限制 / 策略 / 成果」4 必填區塊
   - Opus review + 補「亮點 / 產業」2 選填區塊
3. 透過 admin UI 或 SQL UPDATE 批次寫入 case_blocks JSONB
4. 線上驗 10 個 `/works/{id}` 都渲染 6 區塊

**驗收：**
- `SELECT COUNT(*) FROM articles WHERE case_blocks ?& array['background','constraint','strategy','outcome']` ≥ 10
- 10 個 URL curl 確認 6 區塊內容齊全

**Commit:** `content(works): 10 件代表作品補完 6 區塊（4 必填 + 2 選填）`

---

## Plan 3.6 — 作品頁回鏈 pillar 補完（已整合於 3.2，本 plan 為驗證）

**Type:** `autonomous=true`

**前置：** 3.2 完成

**目標：** 確認 62 件作品全部回鏈所屬 pillar（依 category 自動映射）

**動作：**
1. Sonnet 跑 62 件作品全量 curl：`for id in $(SELECT id FROM articles); do curl /works/$id | grep -c "services/$slug/"; done`
2. 統計達標數量
3. 若有 `category` 為 NULL 或非預期值的作品 → 補修

**驗收：**
- 62 / 62 件作品 SSR HTML 含 `<a href="/services/{slug}/">` 至少 1 個

**Commit:**（無需單獨 commit，Plan 3.2 已涵蓋；本 plan 僅驗證）

---

## Plan 3.7 — 部署 + Rich Results Test + Production smoke test（2-3h）

**Type:** `autonomous=partial`（部署可派 codex；Rich Results 人工跑）

**前置：** 3.1-3.6 全部完成

**目標：** Phase 3 成果全部上 production，並通過 Rich Results 驗證

**動作：**
1. scp server.py + admin/* + 5 pillar HTML 到 ach-clawhome `/srv/weddingwish/goodjob-sit/`
2. ssh `sudo systemctl restart murayama-goodjob.service`
3. Cloudflare CDN purge（5 pillar URL + 10 件作品 URL）
4. Production smoke test：
   - 5 pillar 含 FAQ（grep `<details>` × 4+）
   - 10 件作品 `/works/{id}` 含 6 區塊（grep `case-block` × 6）
5. Rich Results Test 跑 15 個 URL（5 pillar + 10 works）→ 0 error

**驗收：**
- 全部 Production URL HTTP 200
- 15 URL 過 Rich Results Test
- GA4 / Clarity 確認流量未掉

**Commit:** `chore(deploy): Phase 3 部署 + Rich Results 驗證`

---

## Success Criteria 驗收對照（最終）

| # | 條件 | 驗收方式 |
|---|------|---------|
| 1 | 每件作品含 cluster 標記 | `SELECT COUNT(*) FROM articles WHERE category IS NULL` = 0 |
| 2 | 每件作品內鏈所屬 pillar | 62 件 curl 結果均含 `<a href="/services/{slug}/">` |
| 3 | 每 pillar ≥ 3 件代表 | Phase 2 已交付，本 phase 維持 |
| 4 | ≥ 10 件作品補完 6 區塊 | PostgreSQL JSONB query 達標數 |
| 5 | 5 cluster × 4-6 FAQ + FAQPage schema | grep + Rich Results Test 5 URL |

---

## 風險與緩解

| 風險 | 緩解 |
|------|------|
| GATE-3B/3C/3D 三項村長改判方向 A 以外 | 重排 3.1/3.2/3.3，最壞情況增 4-6h |
| Plan 3.3 文案 review 拖延 | Sonnet 草擬 + AskUserQuestion 批次 review，控制在 1-2 輪 |
| Plan 3.5 文案輸入超時 | 拆 2 批：先補 5 件，剩 5 件本 phase 結束前漸進補 |
| Rich Results Test 出錯 | 預留 buffer 30 min 修 schema 細節 |

---

*Phase: 03-p1b-works-faq*
*PLAN written: 2026-05-14 21:42 GMT+8*
