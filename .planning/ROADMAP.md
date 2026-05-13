# Milestone v1.0：SEO / AEO 90 天能見度提升

> 由 `/gsd-ingest-docs` 於 2026-05-13 從 1 份外部 PRD（`docs/seo-aeo-improvement-plan-20260513.html`）合成建立。7 個 phase 採用 `.planning/intel/SYNTHESIS.md` 推薦切分，覆蓋 19 條需求。
>
> **下游消費者**：`/gsd-plan-phase` 會解析 `## Phase N:` 標頭、引用本 milestone 的 phase ID、success criteria 與前置 gate。

---

## Milestone 概覽

| 欄位 | 值 |
|------|----|
| Milestone | v1.0 |
| 主題 | SEO / AEO 90 天能見度提升 |
| 期間 | 90 天（12 週） |
| 起始日 | 待 Phase 1 啟動時補上 |
| KPI | SEO 估分 7.4 → 8.5+ ／ AEO 估分 6.2 → 8.5+ |
| Phase 數 | 7 |
| REQ 覆蓋 | 19 / 19 ✓ |
| Granularity | standard（與 PRD 既有 P0~P3 對齊，部分 P 段拆 A/B 子 phase） |

---

## Phases（總覽 Checklist）

- [ ] **Phase 1：P0 技術修補** — sitemap 驗證、admin noindex、支援頁 metadata、Rich Results 驗證、首頁 SSR 案例
- [ ] **Phase 2：P1-A 內容集群骨架建立** — GSC 匯出與 cannibalization、5 個 pillar 頁上線
- [ ] **Phase 3：P1-B 作品模板擴充與 FAQ** — 作品 cluster mapping、6 區塊模板、5 cluster × 4-6 題 FAQ
- [ ] **Phase 4：P2-A AI Citation Baseline** — 4 平台 × 20-40 題、robots/WAF AI bot 允許、llms.txt 更新
- [ ] **Phase 5：P2-B AI 引用修補包** — lost-prompts 答案型長文、2 個比較頁
- [ ] **Phase 6：P3 權威訊號與外部訊號** — 得獎媒體頁、GBP / 媒體稿、月度長尾內容節奏
- [ ] **Phase 7：90 天驗收與週報** — Looker Studio 或表格週報、5 大面向 baseline vs 結束值報告

---

## Phase Details

### Phase 1: P0 技術修補

- **Goal**：在 7 天內完成索引安全與技術基礎修補，讓 Google 與 AI crawler 都能正確抓取、正確排除私有頁。
- **時間區間**：第 1-2 週
- **Depends on**：無（首 phase）
- **Requirements**：REQ-prod-sitemap-verify、REQ-admin-noindex、REQ-support-pages-metadata、REQ-rich-results-validation、REQ-homepage-server-rendered-cases
- **對應方向性決策**：DEC-private-pages-noindex-policy（proposed）
- **前置資料 gate**：
  - **GATE-1A（必須）**：村長 SSH 至 ACH-ClawHome（`ssh achilean@100.102.51.64`）執行 `psql -d goodjob_site -c "SELECT COUNT(*) FROM articles WHERE published = true"`（或等價查詢），取得正式作品數作為 REQ-prod-sitemap-verify 驗收基準
  - **GATE-1B（建議）**：清掉 Cloudflare CDN 對 `/sitemap.xml` 的快取（dev cache purge），避免驗收 stale 內容
- **Success Criteria**（必須全綠才能進 Phase 2）：
  1. `curl https://goodjob.weddingwishlove.com/sitemap.xml | grep -c '<loc>'` ≥ PostgreSQL `published=true` 作品數
  2. `curl -I https://goodjob.weddingwishlove.com/admin/` response header 含 `X-Robots-Tag: noindex, nofollow, noarchive`
  3. 4 個支援頁（sort-hat、wedding-packages、wedding-packages/outdoor、teabar）均通過 Rich Results Test 0 error
  4. `curl https://goodjob.weddingwishlove.com/` 不執行 JS 即可看到 ≥ 3 個精選作品標題與內鏈
  5. 首頁 + 合作流程 + MUSE + 5 個代表作品 8 個 URL Rich Results Test 全綠
- **Plans**：TBD（由 `/gsd-plan-phase 1` 產出）
- **UI hint**：yes（首頁 server-rendered 案例摘要、支援頁 metadata/OG 影響可見頁面結構）

---

### Phase 2: P1-A 內容集群骨架建立

- **Goal**：上線 5 個 pillar 頁，建立服務主題集群的 URL 骨架，並用 GSC 資料找出 cannibalization 修補方向。
- **時間區間**：第 3-4 週
- **Depends on**：Phase 1（sitemap.xml 已可信、私有頁已 noindex）
- **Requirements**：REQ-gsc-query-export、REQ-pillar-pages-five
- **對應方向性決策**：DEC-pillar-structure-five-clusters（proposed）、DEC-strategy-seo-before-aeo（proposed）
- **前置資料 gate**：
  - **GATE-2A（必須）**：取得 GSC 最近 3-6 個月 `page + query` 匯出檔（CSV 或 Looker Studio）；村長需確認 GSC property 已加 Achillean 為 owner / full user
  - **GATE-2B（必須）**：server.py route 設計確認 — 4 個新 `/services/*/` 路徑與既有 `/works/{id}` / `/wedding-packages/` routing 不衝突；sitemap 生成邏輯擴充收錄 5 個 pillar 頁
  - **GATE-2C（建議）**：若 GSC 資料不足 3 個月（站存在期不夠長），改以「現有 URL 列表 × Bing/Yandex impression」做替代分析，並在報告註明資料限制
- **Success Criteria**：
  1. cannibalization 報告產出（≥ 2 個 URL 競爭同一 query 案例 + 處置方向）
  2. 5 個 pillar URL 全部 HTTP 200（4 新建 + 1 既有 wedding-packages 強化）
  3. 每個 pillar 頁含：服務介紹、代表案例內鏈 ≥ 3、FAQ placeholder（內容會在 Phase 3 填）、相關作品列表
  4. `/sitemap.xml` 收錄 5 個 pillar URL
- **Plans**：TBD
- **UI hint**：yes（5 個 pillar 頁全新前端頁面 + 內鏈版塊）

---

### Phase 3: P1-B 作品模板擴充與 FAQ

- **Goal**：把既有作品歸入 5 大 cluster、擴充作品頁為 6 區塊案例模板、補完每個 cluster 的 FAQ 內容。
- **時間區間**：第 5-8 週（可與 Phase 2 末端重疊，但須等 pillar URL 就緒）
- **Depends on**：Phase 2（pillar URL 必須存在以供作品頁回連）
- **Requirements**：REQ-works-cluster-mapping、REQ-case-template-expansion、REQ-faq-per-cluster
- **對應限制**：CONSTR-faq-answer-length（FAQ 答案 60-120 字 + FAQPage schema）
- **前置資料 gate**：
  - **GATE-3A（必須）**：Phase 1 GATE-1A 確認的「正式作品數」作為 cluster mapping 完整性基準
  - **GATE-3B（必須）**：PostgreSQL `articles` 表新增 `cluster` 欄位 migration 設計確認（或用既有 `category` 欄位映射）
- **Success Criteria**：
  1. 每件作品 metadata 含 cluster 標記（PostgreSQL 欄位或前端標籤一致）
  2. 每件作品 SSR 頁含 1 個指向對應 pillar 頁的內鏈
  3. 每個 pillar 頁列出該 cluster ≥ 3 個代表作品
  4. 既有作品 ≥ 10 件已補完 6 區塊（背景／限制／策略／亮點／產業／成果）
  5. 5 個 cluster 各 4-6 題 FAQ 上線，答案 60-120 字，FAQPage schema 通過 Rich Results Test
- **Plans**：TBD
- **UI hint**：yes（作品 SSR 模板擴充 6 區塊版面 + cluster pillar 上的 FAQ accordion）

---

### Phase 4: P2-A AI Citation Baseline

- **Goal**：建立 4 大 AI 平台引用 baseline、確保 AI crawler 不被 WAF 擋、更新 llms.txt，為 Phase 5 修補包提供 lost-prompts 清單。
- **時間區間**：第 5-8 週（與 Phase 3 並行）
- **Depends on**：Phase 1（站點技術基礎乾淨，不會干擾 AI baseline 結果）
- **Requirements**：REQ-ai-citation-baseline、REQ-robots-waf-bot-allow、REQ-llms-txt-update
- **對應方向性決策**：DEC-baseline-before-optimization（proposed）、DEC-ai-crawler-allowlist（proposed）、DEC-non-deterministic-disclaimer（proposed）
- **對應限制**：CONSTR-ai-crawler-allowlist、CONSTR-non-deterministic-ai
- **前置資料 gate**：
  - **GATE-4A（必須）**：4 平台（ChatGPT、Claude、Gemini、Perplexity）20-40 題 prompt 組設計完成並由村長確認；prompt 須涵蓋 5 個 cluster 主要場景 + 競品場景
  - **GATE-4B（必須）**：測試協議文件就緒（如何記錄是否提及／是否引用／競品名單；同一 prompt 是否重測幾次取多數）
  - **GATE-4C（建議）**：Cloudflare WAF 規則 audit 完成（確認沒誤擋 OAI-SearchBot 與 PerplexityBot）
- **Success Criteria**：
  1. 4 平台 × 20-40 題 prompt 完成測試；每筆紀錄含 prompt / 平台 / 是否提及 / 是否引用 / 競品
  2. baseline 報告含 lost-prompts 清單（明確標出哪些題目村山未被提及／未被引用），供 Phase 5 製作答案型內容
  3. 更新後 robots.txt 含 `OAI-SearchBot` 與 `PerplexityBot` 個別段落上線
  4. Cloudflare WAF 經 audit 確認不阻擋兩者 user-agent 或官方 IP 段
  5. `llms.txt` 含 5 cluster 條目、代表作品 URL、獎項頁、聯絡資訊、`Last-Updated:` 欄位
- **Plans**：TBD
- **UI hint**：no（純 metadata / 文字檔 + 外部測試流程）

---

### Phase 5: P2-B AI 引用修補包

- **Goal**：依 Phase 4 lost-prompts 清單，產出 4 篇答案型長文與 2 個比較頁，提升 AI 引用率。
- **時間區間**：第 6-10 週
- **Depends on**：Phase 4（lost-prompts 清單就緒）、Phase 2（pillar 頁可供答案文章回連）
- **Requirements**：REQ-lost-prompts-answer-content、REQ-comparison-pages
- **對應限制**：CONSTR-faq-answer-length（答案型文章內含結構化 FAQ）
- **前置資料 gate**：
  - **GATE-5A（必須）**：Phase 4 baseline 報告的 lost-prompts 清單已交付；至少 ≥ 12 個 lost prompts 才能合理分配到 4 篇長文（每篇對應 ≥ 3 個 lost prompts）
- **Success Criteria**：
  1. 上線 ≥ 4 篇答案型長文，每篇對應 ≥ 3 個 lost prompts；含明確答案區塊、結構化 FAQ、來源／案例引用
  2. 上線 2 個中立比較頁：「品牌活動佈置 vs 展場設計」、「客製佈置 vs 套組方案」
  3. 每個比較頁含可機讀 HTML `<table>`，必要時附 schema
  4. 4 篇長文與 2 個比較頁全部被 sitemap.xml 收錄
- **Plans**：TBD
- **UI hint**：yes（4 篇長文 + 2 個比較頁需有文章版型與比較表組件）

---

### Phase 6: P3 權威訊號與外部訊號

- **Goal**：建立外部可被引用的權威訊號（得獎、媒體、GBP、合作單位回連），並建立月度長尾內容節奏。
- **時間區間**：第 9-12 週
- **Depends on**：Phase 3（作品 cluster 已完整可作為媒體稿素材）、Phase 5（答案型內容已建，可作為媒體稿引用）
- **Requirements**：REQ-awards-media-page、REQ-external-trust-signals、REQ-monthly-longtail-content
- **前置資料 gate**：
  - **GATE-6A（建議）**：MUSE / 既有得獎清單盤點完整；至少 1 篇媒體稿或合作單位回連的窗口已聯絡
  - **GATE-6B（建議）**：Google Business Profile 帳號擁有權確認（村長確認 owner email 與 2FA 通過）
- **Success Criteria**：
  1. `/awards/` 或 `/press/` 頁上線；列出 ≥ 1 個第三方媒體報導 + 既有 MUSE 條目；含 `Organization` + `Award`/`Article` schema
  2. Google Business Profile 完整資料（網址、營業時間、相片）已驗證
  3. ≥ 1 篇媒體稿或合作單位頁面有回連到村山良作
  4. 主要社群（IG / FB / LINE）固定貼文含官網內鏈
  5. Phase 6 期間（第 9-12 週）至少發布 4 篇長尾文章（每月 ≥ 2 篇）
- **Plans**：TBD
- **UI hint**：yes（`/awards/` 或 `/press/` 為新頁面 + GBP 雖屬外部但會反映回首頁可見的口碑區塊）

---

### Phase 7: 90 天驗收與週報機制

- **Goal**：建立可持續運作的週報 dashboard，並產出 90 天 milestone 完整驗收報告（5 大面向 baseline vs 結束值）。
- **時間區間**：第 11-12 週
- **Depends on**：Phase 1 ~ Phase 6（所有資料源就緒）
- **Requirements**：REQ-weekly-report-dashboard
- **對應限制**：CONSTR-indexation-targets、CONSTR-technical-cwv-good、CONSTR-non-deterministic-ai
- **前置資料 gate**：
  - **GATE-7A（必須）**：GA4 property 已串接 goodjob.weddingwishlove.com；自然搜尋、ChatGPT/Perplexity referral（`utm_source=chatgpt.com` 等）、LINE CTA 點擊 3 條資料管線都有資料可查
  - **GATE-7B（必須）**：Looker Studio 或等價工具 access 就緒（村長 Google 帳號 + GSC/GA4 連結器）
  - **GATE-7C（必須）**：Phase 4 AI baseline 已存檔，Phase 7 需用同一組 prompts 重測作為「結束值」（CONSTR-non-deterministic-ai 要求）
- **Success Criteria**：
  1. 週報 dashboard 自動或半自動更新，覆蓋 GSC（impressions / clicks / CTR）+ GA4（自然搜尋 + AI referral）+ CTA 點擊
  2. 每週可由 1 個 URL 看到該週數據
  3. 90 天 milestone 驗收報告產出：5 大面向（Indexation / Technical CWV / Content / AEO / Authority）的 baseline vs 結束值
  4. SEO 估分 ≥ 8.5（自評 + Rich Results / PageSpeed 客觀指標）
  5. AEO 估分 ≥ 8.5（4 平台 recheck 引用率變化 + 品牌提及率變化）
- **Plans**：TBD
- **UI hint**：no（週報為外部 dashboard，不在站內）

---

## 進度表

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. P0 技術修補 | 0/? | Not started | — |
| 2. P1-A 內容集群骨架 | 0/? | Not started | — |
| 3. P1-B 作品模板與 FAQ | 0/? | Not started | — |
| 4. P2-A AI Citation Baseline | 0/? | Not started | — |
| 5. P2-B AI 引用修補包 | 0/? | Not started | — |
| 6. P3 權威訊號 | 0/? | Not started | — |
| 7. 90 天驗收與週報 | 0/? | Not started | — |

---

## 依賴關係圖

```
Phase 1 (P0 基礎)
  ├─→ Phase 2 (Pillar 骨架)
  │     └─→ Phase 3 (作品模板 + FAQ)
  │           └─→ Phase 6 (權威訊號)
  │                 └─→ Phase 7 (驗收與週報)
  └─→ Phase 4 (AI Baseline)
        └─→ Phase 5 (AI 修補包)
              └─→ Phase 6
```

Phase 3 與 Phase 4 可並行（皆只依賴 Phase 1 與各自前置 gate）。

---

## 變更紀錄

- 2026-05-13：由 `/gsd-ingest-docs` 從 PRD 首次建立；7 phase 結構採用 SYNTHESIS 推薦切分，與 PRD 原 P0~P3 對齊，僅將 P1 拆成 2A/2B（骨架 vs 內容）、P2 拆成 4A/4B（baseline vs 修補）以反映依賴序。
