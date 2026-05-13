# 合成摘要（Synthesis Entry Point）

> 此檔為 `gsd-roadmapper` 的單一入口。所有細節在同目錄下的 per-type intel 檔，本檔只做總覽 + 路由建議。
>
> 來源：本批 `gsd-ingest-docs` 在 2026-05-13 處理 1 份外部文件，模式 `new`，`.planning/` 首次建立。

---

## 文件統計

| 類型 | 數量 | 範例 |
|------|------|------|
| PRD | 1 | docs/seo-aeo-improvement-plan-20260513.html |
| ADR | 0 | — |
| SPEC | 0 | — |
| DOC | 0 | — |

- LOCKED 決策：0（PRD 預設不產生 LOCKED）
- 方向性 proposed 決策：6（見 `decisions.md`）

---

## 萃取產出總覽

| Intel 檔 | 條目數 | 主要分布 |
|----------|--------|----------|
| `decisions.md` | 6 條 proposed 決策 | 策略排序、5 集群結構、私有頁、AI bots、baseline 紀律、非決定性免責 |
| `requirements.md` | 17 條需求 | P0×5 + P1×5 + P2×5 + P3×4 |
| `constraints.md` | 9 條限制 | 索引、CWV、schema 一致性、非 JS 可讀、私有頁雙保險、AI 允許、FAQ 規格、description 長度、資料缺口、非決定性 |
| `context.md` | 9 個主題段落 | 專案身分、技術棧、既有 SEO 基礎、評分、內容資產、90 天路線、5 集群、外部資料源、AEO 修補包、官方規範 |

---

## 衝突報告摘要

- **BLOCKER：** 0
- **WARNING：** 2
- **INFO：** 5
- 詳見 `.planning/INGEST-CONFLICTS.md`

WARNING 主題：
1. 作品數雙來源未對齊（27 vs 29，需從正式 PostgreSQL 確認）
2. 啟動 P1 / P2 須先取得 GSC / GA4 / 4 平台 baseline 等前置資料，當下未就緒

INFO 主題：
1. 首頁 SPA 渲染 vs `/works/{id}` SSR 一致性釐清
2. 5 個新 pillar 路徑與既有 routing 並存（無衝突，但需 server.py 新增 route）
3. `data/articles.json` 已退役為備份（CLAUDE.md 與 PRD 一致）
4. robots.txt 從 6 行擴充到含 AI bot 段落
5. PRD 未提供 ADR 等級的 LOCKED 決策（後續實作可能會升格）

---

## 推薦 Roadmap Phase 切分（供 `gsd-roadmapper` 參考）

PRD 提供 P0~P3 四段時程；考量資料前置依賴與資源並行性，建議 roadmapper 切成 7 個 phase：

### Phase 1：P0 技術修補（第 1-2 週）

- 對應需求：`REQ-prod-sitemap-verify`、`REQ-admin-noindex`、`REQ-support-pages-metadata`、`REQ-rich-results-validation`、`REQ-homepage-server-rendered-cases`
- 對應決策：`DEC-private-pages-noindex-policy`、`DEC-ai-crawler-allowlist`
- 驗收：sitemap 驗證 + admin noindex header 上線 + 4 支援頁 metadata 通過 Rich Results Test
- 前置：CLAUDE.md 已說明 PostgreSQL 為正式資料源，但實際正式作品數需 SSH 確認

### Phase 2：P1-A 內容集群骨架建立（第 3-4 週）

- 對應需求：`REQ-gsc-query-export`、`REQ-pillar-pages-five`
- 對應決策：`DEC-pillar-structure-five-clusters`、`DEC-strategy-seo-before-aeo`
- 驗收：GSC 匯出 + cannibalization 報告 + 5 個 pillar 頁上線（HTTP 200）
- 前置：須先取得 GSC 3-6 個月資料；server.py 需擴充 `/services/*/` route

### Phase 3：P1-B 作品模板擴充與 FAQ（第 5-8 週，可與 Phase 2 部分重疊）

- 對應需求：`REQ-works-cluster-mapping`、`REQ-case-template-expansion`、`REQ-faq-per-cluster`
- 驗收：10+ 件作品補完 6 區塊；5 個 cluster 各 4-6 題 FAQ；FAQPage schema 全綠
- 前置：Phase 2 pillar URL 就緒（供作品頁回連）

### Phase 4：P2-A AI Citation Baseline（第 5-8 週）

- 對應需求：`REQ-ai-citation-baseline`、`REQ-robots-waf-bot-allow`、`REQ-llms-txt-update`
- 對應決策：`DEC-baseline-before-optimization`、`DEC-ai-crawler-allowlist`、`DEC-non-deterministic-disclaimer`
- 驗收：4 平台 × 20-40 題完成測試；lost-prompts 清單產出；robots.txt 含 AI bot 段落上線；llms.txt 更新
- 前置：須有可重現的 prompt 組（人工或半自動）

### Phase 5：P2-B AI 引用修補包（第 6-10 週）

- 對應需求：`REQ-lost-prompts-answer-content`、`REQ-comparison-pages`
- 驗收：4 篇答案型長文 + 2 個比較頁上線
- 前置：Phase 4 lost-prompts 清單

### Phase 6：P3 權威訊號與外部訊號（第 9-12 週）

- 對應需求：`REQ-awards-media-page`、`REQ-external-trust-signals`、`REQ-monthly-longtail-content`
- 驗收：得獎媒體頁上線、GBP 完整資料、月度長尾內容節奏建立
- 前置：可能需要對外溝通（媒體窗口、合作單位）

### Phase 7：90 天驗收與週報機制（第 11-12 週）

- 對應需求：`REQ-weekly-report-dashboard`
- 對應限制：`CONSTR-indexation-targets`、`CONSTR-technical-cwv-good`
- 驗收：Looker Studio 或表格週報運轉、90 天 KPI 報告（5 大面向 × baseline vs 結束值）
- 前置：GA4 / GSC / AI referral 三條資料管線都通

---

## 路由建議給 `gsd-roadmapper`

- `PROJECT.md`：用 `context.md` 的「專案身分」「技術棧」「既有 SEO/AEO 基礎」3 段做骨架；不要重複 CLAUDE.md 已有的部署細節
- `REQUIREMENTS.md`：直接引用 `requirements.md` 的 17 條，按 P0/P1/P2/P3 分群；保留 REQ ID 以利追蹤
- `ROADMAP.md`：採用上方 7 個 phase 切分；標註 Phase 2/3 的前置資料依賴（GSC、PostgreSQL 確認）以免空轉
- `CONTEXT.md`：把 `decisions.md` 6 條 proposed 決策搬進來作為「待升格 ADR 候選」段落，提示村長後續可能要寫正式 ADR
- 限制檔（如 `constraints.md` → roadmapper 自行決定是否合入 PROJECT.md NFR 章節）

---

## Per-Type Intel 檔指引

- `decisions.md` — 6 條 proposed 決策（PRD 隱含的策略方向，可升格 ADR）
- `requirements.md` — 17 條可驗收需求（P0~P3）
- `constraints.md` — 9 條 NFR/schema/protocol 限制
- `context.md` — 專案背景、技術棧、評分現況、5 集群、外部資料源
- `INGEST-CONFLICTS.md`（位於 `.planning/`）— 衝突分析報告
