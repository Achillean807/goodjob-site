# 專案狀態（STATE）

> 此檔為「專案記憶體」，由 `/gsd-*` 系列工作流寫入；每次任務開始與結束時讀寫，作為 cross-session continuity。

---

## Project Reference

| 欄位 | 值 |
|------|----|
| 專案名稱 | 村山良作（Murayama Goodjob） |
| 專案 slug | `goodjob-site` |
| Core Value | 把品牌活動 / 主題場景 / 展場空間作品集，以高 SEO/AEO 能見度被搜尋引擎與 AI 引擎正確引用，為村花弄囍母品牌帶來高質量業務洽詢 |
| Live URL | https://goodjob.weddingwishlove.com/ |
| 當前焦點 | SEO/AEO 90 天改善（Milestone v1.0） |

---

## Current Position

| 欄位 | 值 |
|------|----|
| 當前 Milestone | v1.0 — SEO / AEO 90 天能見度提升 |
| 當前 Phase | Phase 2（P1-A 內容集群骨架）— **✅ 全部完成（5 pillar production 部署 + sitemap + 入口閉環 + IP/在地/UX 收尾）** |
| 當前 Plan | `.planning/phases/02-p1a-content-cluster/02-SUMMARY.md`（執行總結；6/6 plans + 2 插隊任務全綠） |
| 狀態 | 5/5 pillar HTTP 200 + sitemap 74 URL + SC 4/4 達標 + 首頁 5 入口閉環 |
| 進度條 | `[▓▓▓▓▓▓░░░░░░░░░░░░░░] 2 / 7 phases（Phase 2 結束，準備 Phase 3 / Phase 4）` |

### 下一步動作

1. ✅ Phase 1（P0 技術修補）— **2026-05-14 02:00 完成**
2. ✅ Phase 2（P1-A 內容集群骨架）— **2026-05-14 13:42 完成**（5 pillar production 部署）
3. **下一步抉擇**（Phase 3 與 Phase 4 可並行，皆只依賴 Phase 1 + Phase 2）：
   - 🅐 **Phase 3（P1-B 作品模板與 FAQ）**：5 cluster × 4-6 題 FAQ + 作品 SSR 6 區塊模板
   - 🅑 **Phase 4（P2-A AI Citation Baseline）**：4 平台 × 20-40 prompts baseline 測試
   - 🅒 兩個並行（Phase 3 由 codex 跑 FAQ 內容、Phase 4 由 Playwright 跑 prompt 測試）
4. **任一啟動前** 跑各自前置 gate（Phase 3：GATE-3A/3B；Phase 4：GATE-4A/4B/4C）

Phase 2 的前置 gate：
- **GATE-2A** ✅ **完成 2026-05-14**：cannibalization 報告產出（`.planning/intel/gsc-export/cannibalization-report-20260514.md`，commit `5b45a82`）
- **GATE-2B** ✅ **LOCKED 2026-05-14**：URL = `/services/{slug}/`、靜態 HTML、cluster mapping 採 §6.1 架構

Phase 1 的前置 gate（保留紀錄）：
- **GATE-1A** ✅ **已解果 2026-05-13**：SSH ach-clawhome → `SELECT COUNT(*) FROM articles` 結果為 **62 篇**
  - 分類細項：`business` 27 / `party` 16 / `civil` 14 / `magic` 5
  - 影響：sitemap 驗收基準 = ≥ 69（62 篇 works + 7 個靜態頁）
- **GATE-1B**：Cloudflare CDN 對 `/sitemap.xml` cache purge（Phase 1.1 部署後執行，PLAN 已含 `scripts/cf-purge.ps1` 設計）

---

## Ingest 來源

本次 `.planning/` 由 `/gsd-ingest-docs` 在 2026-05-13 首次建立。

| 文件 | 類型 | precedence | locked | 路徑 |
|------|------|-----------|--------|------|
| 村山良作搜尋與 AI 引用能見度改善計畫 | PRD | 0 | false | `docs/seo-aeo-improvement-plan-20260513.html` |

**萃取產出：**

| Intel 檔 | 條目數 |
|----------|--------|
| `.planning/intel/decisions.md` | 6 條 proposed 決策 |
| `.planning/intel/requirements.md` | 19 條需求（P0×5 + P1×5 + P2×5 + P3×4） |
| `.planning/intel/constraints.md` | 9 條限制 |
| `.planning/intel/context.md` | 9 段背景 |

**衝突檢測：** BLOCKER 0、WARNING 2、INFO 5（見 `.planning/INGEST-CONFLICTS.md`）

---

## Performance Metrics

| 指標 | Baseline (2026-05-13) | 目標 (T+90 天) | 當前 |
|------|----------------------|---------------|------|
| SEO 估分 | 7.4 / 10 | 8.5+ | 7.4 |
| AEO / GEO 估分 | 6.2 / 10 | 8.5+ | 6.2 |
| 公開頁索引覆蓋 | 待 GSC 確認 | 90%+ | — |
| 私有頁索引筆數 | 待 GSC 確認 | 0 | — |
| 4 平台 AI baseline | 尚未建立 | 已建立並可重測 | 尚未建立 |
| Core Web Vitals | 未量測 | LCP/INP/CLS 全 Good | — |
| GA4 Measurement ID | — | 已部署 | `G-FVG726LELF`（2026-05-14 上線）|
| Microsoft Clarity Project ID | — | 已部署 | `wqkwwcp7kt`（2026-05-14 上線）|

---

## 待升格 ADR 候選

> PRD 本身未產生 ADR 等級的 LOCKED 決策，但內部有 6 條方向性 proposed 決策可能影響跨檔結構。實作期間若村長要求鎖定方向，可由 `/gsd-ingest-docs adr/<slug>.md` 或人工撰寫 ADR 將下列任一項升格為 LOCKED。

| DEC ID | 標題 | 影響範圍 | 升格優先序 |
|--------|------|---------|----------|
| DEC-strategy-seo-before-aeo | 先修 SEO 技術基礎，再建立 AEO 引用機制 | 整個 milestone 排序 | 中（已隱含於 phase 順序，可選擇性升格） |
| DEC-pillar-structure-five-clusters | 以 5 大服務集群作為內容組織主軸 | server.py routing、sitemap 邏輯、內鏈策略 | **高（Phase 2 啟動前建議升格）** |
| DEC-private-pages-noindex-policy | 私有頁 robots disallow + X-Robots-Tag 雙保險 | server.py X-Robots-Tag 邏輯、robots.txt | **高（Phase 1 啟動前建議升格）** |
| DEC-ai-crawler-allowlist | 明確允許 OAI-SearchBot、PerplexityBot | robots.txt、Cloudflare WAF（跨處） | **高（Phase 4 啟動前建議升格）** |
| DEC-baseline-before-optimization | AEO 強制先建立 baseline 才動內容 | Phase 4/5/7 KPI 設計 | 中 |
| DEC-non-deterministic-disclaimer | AI 引用為非決定性，不承諾保證引用率 | KPI 對外溝通、Phase 7 報告口徑 | 低（屬溝通原則） |

完整決策內文見 `.planning/intel/decisions.md`。

---

## Accumulated Context

### 已知資料缺口（須在對應 phase 啟動前補齊）

| 缺口 | 對應 Gate | 對應 Phase |
|------|----------|-----------|
| ~~PostgreSQL 正式作品數（27 vs 29 未對齊）~~ ✅ 已解果：62 篇 | GATE-1A | Phase 1（已通過） |
| Google Search Console 3-6 個月 query/page 匯出 | GATE-2A | Phase 2（必須） |
| GA4 自然搜尋 / AI referral / LINE CTA 串接 | GATE-7A | Phase 7（必須） |
| 4 平台 AI baseline prompt 組（20-40 題/平台） | GATE-4A | Phase 4（必須） |
| Cloudflare WAF AI bot allowlist audit | GATE-4C | Phase 4（建議） |

### 已做的決定

- 採用 SYNTHESIS 推薦的 7 phase 切分（未調整順序與依賴）
- 19 條 REQ 全數對應 phase，無 orphan、無重複
- LOCKED 決策數為 0；6 條 proposed 決策不寫進 PROJECT.md，集中在本 STATE.md 的「待升格 ADR 候選」段落

### Roadmap 調整紀錄

本批未對 SYNTHESIS 推薦切分做任何結構性調整（phase 順序、phase 數、依賴關係皆與 SYNTHESIS 一致）。若後續村長要求調整（例如壓縮為 5 phase 或拆出 Phase 0），需在本段落補上理由與時間戳。

### TODO（給後續 `/gsd-*` 工作流）

1. **Phase 1 啟動前**：跑 GATE-1A（PostgreSQL COUNT）、GATE-1B（CF cache purge），把實際作品數寫回 REQ-prod-sitemap-verify 驗收條件
2. **Phase 2 啟動前**：跑 GATE-2A（GSC 匯出）、GATE-2B（pillar route 設計）
3. **Phase 4 啟動前**：跑 GATE-4A（prompt 組設計）、GATE-4B（測試協議）、GATE-4C（WAF audit）
4. **Phase 7 啟動前**：跑 GATE-7A（GA4 串接）、GATE-7B（Looker Studio access）、GATE-7C（Phase 4 baseline 留存）
5. **任何時點**：村長要求把任一 proposed 決策升格 ADR → 用 `/gsd-ingest-docs` 處理新 ADR 檔

### 已知阻塞

無。

---

## Session Continuity

### 最近活動

- 2026-05-13 22:42：`gsd-doc-synthesizer` 完成 intel 萃取（6 個檔、715 行）
- 2026-05-13 22:44：`gsd-roadmapper` 確認衝突 gate 通過、PROJECT.md 欄位收集完成
- 2026-05-13 22:44+：本次 ingest 寫出 PROJECT.md / REQUIREMENTS.md / ROADMAP.md / STATE.md
- 2026-05-13 23:09：✅ **GATE-1A 解果** — SSH `ach-clawhome` 跑 `SELECT COUNT(*) FROM articles` 得 **62 篇**（business 27 / party 16 / civil 14 / magic 5）；同步修正 CLAUDE.md / README.md / DESIGN.md 過時值（27/29 → 62）
- 2026-05-13 23:20：📋 Phase 1 規劃完成 — `01-CONTEXT.md`（216 行）+ `01-PLAN.md`（640 行，5 plans）+ `01-CHECK.md` goal-backward 驗證
- 2026-05-13 23:30：✅ `gsd-plan-checker` 找出 1 Blocker（SQL camelCase 拼錯部署即崩）+ 3 Warning（teabar FAQPage 漏實作、sitemap URL 數歧義、缺 Rollback）；Opus 親自修正並 spot-check 全綠 → PLAN PASS-AFTER-REVISION
- 2026-05-14 00:00：🚀 **Phase 1 執行開始** — 依序部署 Plan 1.2 → 1.5 → 1.1 → 1.3，每個都 commit + push + CF purge + curl 驗證
- 2026-05-14 00:33：✅ **Plan 1.3 完成** — 4 支援頁 metadata + 9 個 JSON-LD schema 上線（sort-hat 2、teabar 3 含 FAQPage、wedding-packages × 2 各 2）
- 2026-05-14 00:35：✅ **Plan 1.4 自動化前置完成** — 8 URL 線上 HTML 抓取 + JSON-LD parse 全綠；報告骨架 `01-RICH-RESULTS-REPORT.md` 已建好供村長手動填截圖結果
- 2026-05-14 00:38：📝 **Phase 1 SUMMARY 產出** — 5 plans 自動化部分全綠；STATE 進度條 0/7 → 1/7
- 2026-05-14 01:30：✅ **Phase 1.4 完整收尾** — Playwright MCP 對 12 URL（8 必驗 + 4 支援頁）跑 Google Rich Results Test 全綠；過程中發現 teabar.html Product schema 3 critical errors（Offer 缺 `price`），改寫為 Service+OfferCatalog（B2B 客製化服務語義更貼），部署 + CF purge + 重測 → 2 個有效項目 0 錯誤 0 警告；evidence/ 內 13 張截圖（含修補前後對照）
- 2026-05-14 02:00：✅ **Phase 1.6 GA4 + Microsoft Clarity 埋碼完成** — Playwright 自動化建立兩家帳號／專案：GA4 `村山良作 - GA4` Measurement ID `G-FVG726LELF`（藝術與娛樂分類，台灣時區，目標 lead generation + traffic）+ Clarity 專案 `村山良作 Goodjob` Project ID `wqkwwcp7kt`（娛樂分類）；雙追蹤碼埋入 7 個對外 HTML（index, teabar, workflow, muse-2026, sort-hat, wedding-packages × 2）+ `server.py` `_serve_works_page` SSR 模板（f-string `{{` escape 通過 syntax check），共 8 檔 +128 行；部署 + cf-purge 8 URL + Playwright 跑 production 驗 `window.dataLayer`（含 `config G-FVG726LELF`）/ `window.gtag` / `window.clarity` 皆已 ready；Cloudflare Rocket Loader 雖改了 script type 但仍正確 evaluate，不需加 `data-cfasync="false"`
- 2026-05-14 08:40：✅ **GATE-2A 達成** — Playwright 自動匯出 GSC 6 個月 query + page CSV → cannibalization-report-20260514.md 產出（commit `5b45a82`）
- 2026-05-14 08:57：⚖️ **DEC-pillar-structure-five-clusters 鎖定** — 5 pillar `/services/{slug}/` 架構 LOCKED；02-CONTEXT.md + 02-PLAN.md 規劃完成（commit `f4d78e0`）
- 2026-05-14 09:30：✅ **Plan 2.0 完成** — services.css 共用樣式 + representatives.md 15 件代表案例對照（commit `532514d`）
- 2026-05-14 10:00：✅ **Plan 2.1-2.5 codex 並行交付** — 5 個 pillar HTML 全部寫完並補 3 個既有頁 breadcrumb（commit `3aa8664`）
- 2026-05-14 11:00：🟣 **Plan 2.8 IP/在地/UX 收尾** — magic-academy IP 用語去除 + civil-makeover 台北信義在地 SEO + 手機 A/B/C 實驗
- 2026-05-14 12:21：✅ **手機 A 案 2 欄精簡卡定稿** — services.css 收編，B/C 實驗碼清理完畢
- 2026-05-14 12:55：✅ **Phase 2 主體完成並 commit** — 變數 A 手機排版 + 實驗清理（commit `d0fb90a`）
- 2026-05-14 13:42：✅ **Phase 2 入口閉環收尾** — 5 pillar production 部署 + sitemap 補 5 條 + 首頁 nav/topbar 5 入口補完 + 4 pillar 重複作品去除 + sort-hat 縮圖換成自家頁面截圖 + llms.txt 補 pillar section（commit `e121d77`）
- 2026-05-14 14:13：📝 **Phase 2 SUMMARY 產出** — 6/6 plans + 2 插隊任務全綠；STATE 進度條 1/7 → 2/7

### 下次 Session 必讀

開啟新 session 時優先讀：
1. `.planning/STATE.md`（本檔，定位用）
2. `.planning/ROADMAP.md`（milestone 結構）
3. `.planning/PROJECT.md`（NFR 底線）
4. `CLAUDE.md`（部署細節、API 端點清單）
