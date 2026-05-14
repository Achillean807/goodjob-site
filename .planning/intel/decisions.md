# 方向性決策清單

> 由 `gsd-doc-synthesizer` 從本批匯入文件萃取。本檔僅蒐集 ADR 等級的決策；PRD 預設不產生 LOCKED 決策，下列項目為 PRD 內部隱含的「策略性方向」，狀態統一為 `proposed`，可在後續 ADR 文件中被升格或推翻。

---

## 來源彙整

| 文件 | 類型 | precedence | locked | 路徑 |
|------|------|------------|--------|------|
| 村山良作搜尋與 AI 引用能見度改善計畫 | PRD | 0 | false | docs/seo-aeo-improvement-plan-20260513.html |

---

## DEC-strategy-seo-before-aeo

- **標題：** 先修 SEO 技術基礎，再建立 AEO 引用機制
- **狀態：** proposed（PRD 提出，非 LOCKED）
- **範圍：** 90 天 SEO/AEO 路線圖整體排序
- **決策陳述：** 先做 P0 索引安全與技術基礎（sitemap、私有頁 noindex、支援頁 metadata/schema），再建立服務主題集群（P1），再針對 AI 引用做 baseline 與修補（P2），最後鋪設權威訊號（P3）。
- **理由：** SEO 與 AEO 互補；索引與可信度未到位，AEO 修補無法被 AI 引擎讀取／引用。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 一、執行摘要 主要策略

---

## DEC-pillar-structure-five-clusters

- **標題：** 以 5 大服務集群作為內容組織主軸
- **狀態：** proposed
- **範圍：** 內容資訊架構、URL 規劃、內鏈策略
- **決策陳述：** 建立 5 個 pillar 頁：品牌活動佈置、展場空間設計、春酒尾牙佈置、戶政空間改造、婚禮場景佈置；既有 29+ 件作品歸到對應 cluster。
- **建議路徑：**
  - `/services/brand-event-decoration/`
  - `/services/exhibition-space-design/`
  - `/services/year-end-party-decoration/`
  - `/services/civil-office-transformation/`
  - `/wedding-packages/`（既有）+ `/teabar.html`（既有）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 四、內容集群與頁面規劃

---

## DEC-private-pages-noindex-policy

- **標題：** 私有頁採 robots disallow + X-Robots-Tag 雙保險
- **狀態：** proposed
- **範圍：** `/admin/`、`/quote/`
- **決策陳述：** `/quote/` 既有 X-Robots-Tag，仍保留；`/admin/` 補上 `X-Robots-Tag: noindex, nofollow, noarchive` 與 robots.txt disallow。
- **理由：** robots 不等於 noindex；需 response header 才能擋住已被連結的私有頁進入索引。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二、現況發現「Robots / 私有頁」、§ 三 P0、§ 三 robots.txt 調整方向

---

## DEC-ai-crawler-allowlist

- **標題：** 明確允許 OAI-SearchBot 與 PerplexityBot 抓取公開內容
- **狀態：** proposed
- **範圍：** robots.txt、Cloudflare WAF
- **決策陳述：** robots.txt 列出 `OAI-SearchBot`、`PerplexityBot` 個別段落（Disallow `/quote/`、`/admin/`，Allow `/`），並確認 Cloudflare 沒有阻擋兩者；保留 `Sitemap` 與 `LLMs-Txt` 指向 production URL。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 三 robots.txt 調整方向

---

## DEC-baseline-before-optimization

- **標題：** AEO 強制先建立 baseline 才動內容
- **狀態：** proposed
- **範圍：** ChatGPT、Claude、Gemini、Perplexity 4 平台
- **決策陳述：** 每個平台跑 20-40 題 prompt 實測，記錄品牌是否被提及、是否被引用、競品是誰；依 lost prompts 決定內容修補優先序。
- **理由：** 沒有 baseline 無法量化改善；AI 引用具非決定性，需固定 prompt 組重測。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五 Baseline prompt 組、§ 七 footer-note

---

## DEC-non-deterministic-disclaimer

- **標題：** AI 引用為非決定性，不承諾保證引用率
- **狀態：** proposed
- **範圍：** KPI 設定、對客戶／村長的承諾溝通
- **決策陳述：** AEO/GEO KPI 第一次只建 baseline，第二次起追蹤引用率與品牌提及率變化；不承諾「保證被引用」。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 七 footer-note、§ 六 KPI AEO/GEO 列

---

## 待升格為 ADR 的候選項

下列 PRD 內主張屬於可能跨檔影響的方向性決策，建議於 P0 / P1 啟動前，由村長確認後寫成正式 ADR：

1. **DEC-pillar-structure-five-clusters** — 新建 4 個 `/services/*/` 路徑會對 server.py routing / sitemap 邏輯造成結構性影響。
2. **DEC-private-pages-noindex-policy** — server.py 需新增 `/admin/` 的 X-Robots-Tag 邏輯，屬於跨檔影響。
3. **DEC-ai-crawler-allowlist** — robots.txt 與 Cloudflare WAF 雙處修改，需有單一決策來源避免漂移。

---

## DEC-cluster-mapping-storage-category

- **標題：** Phase 3 cluster mapping 沿用既有 `articles.category` 欄位，不新增儲存欄位
- **狀態：** **LOCKED**（村長 2026-05-15 confirm，GATE-3B）
- **範圍：** PostgreSQL `goodjob_site.articles` 表、Phase 3 server.py SSR `/works/{id}`、5 pillar 內鏈映射
- **決策陳述：** 不新增 `cluster` 或 `clusters JSONB` 欄位；沿用既有 `category`（business/party/civil/magic）作為 cluster 識別。Cluster slug 與 PostgreSQL `category` 1:1 映射：business → business-event / party → party-spring-banquet / civil → civil-makeover / magic → magic-academy。Wedding-tea-flower 為 hub 概念不對應 articles category。
- **理由：** 零 migration risk、零 admin UI 改動、與 Phase 2 `DEC-pillar-structure-five-clusters` 已 LOCKED 的 5 cluster 設計 1:1 對齊；現有 62 件作品全部單一分類即可達標 REQ-works-cluster-mapping「每件作品 metadata 含 cluster 標記」。
- **取捨：** 一件作品只能歸一個 cluster；未來若有跨 cluster 需求（例如「企業活動 + 春酒」），需另啟 ADR 評估升格為 `clusters JSONB`。
- **來源：** 03-CONTEXT.md GATE-3B + 村長 2026-05-15 AskUserQuestion confirm

---

## DEC-case-blocks-storage-jsonb

- **標題：** Phase 3 作品 6 區塊內容存 `articles.case_blocks JSONB` 單欄
- **狀態：** **LOCKED**（村長 2026-05-15 confirm，GATE-3C）
- **範圍：** PostgreSQL `goodjob_site.articles` 表、admin/* 編輯介面、server.py `_serve_works_page` SSR
- **決策陳述：** PostgreSQL `articles` 表新增 `case_blocks JSONB NOT NULL DEFAULT '{}'` 單欄，存 6 個 key：`background / constraint / strategy / highlight / industry / outcome`（背景 / 限制 / 策略 / 亮點 / 產業 / 成果）。Admin 後台加 6 個 textarea；未填區塊在 `_serve_works_page` SSR 時 fallback 顯示既有 description（只第一次）。
- **理由：** 單欄存全部、向後相容（既有 62 件 DEFAULT '{}' 不破壞）、可漸進補完；未來改區塊鍵名只需改 server.py + admin UI，無需 PostgreSQL migration。
- **取捨：** JSONB 不便單 key 索引查詢（但本 phase 無此需求）；schema 結構不顯示在 `\d articles`，需在 server.py / admin 文件註明 6 key 規格。
- **來源：** 03-CONTEXT.md GATE-3C + 村長 2026-05-15 AskUserQuestion confirm

---

## DEC-faq-storage-html-hardcode

- **標題：** Phase 3 FAQ 內容以 HTML 硬編碼存在 5 pillar `index.html`
- **狀態：** **LOCKED**（村長 2026-05-15 confirm，GATE-3D）
- **範圍：** 5 個 `/services/{slug}/index.html`（business-event / party-spring-banquet / magic-academy / civil-makeover / wedding-tea-flower）
- **決策陳述：** FAQ 內容寫進 5 pillar HTML 內 `<section class="pillar-faq">`（`<details>` / `<dl>` 結構，人類可讀），並在同檔 `<script type="application/ld+json">` 包 `FAQPage` schema 對應 1:1。不建 `cluster_faqs` PostgreSQL 表，不建 `data/faqs.json`。
- **理由：** 零 migration、Phase 2 留下的 placeholder 同檔即補、即可上線；FAQ 改動頻率低（≤ 1 次/季），硬編碼維護成本可接受。
- **取捨：** 改 FAQ 要改 HTML 並重新部署（無法後台改）；若未來引入後台管理 UI 需要另啟 ADR migration。
- **來源：** 03-CONTEXT.md GATE-3D + 村長 2026-05-15 AskUserQuestion confirm

---

## DEC-baseline-prompt-design-direction

- **標題：** Phase 4 AI Citation Baseline prompt 組以「5 cluster × 4 類型 = 20 題」結構設計
- **狀態：** **LOCKED**（村長 2026-05-15 confirm GATE-4A 方向，個別題目文字待 Plan 4.0 逐題 review）
- **範圍：** 4 平台（ChatGPT / Claude / Gemini / Perplexity）AI Citation Baseline 首輪測試
- **決策陳述：** Prompt 組結構固定為「5 cluster × 每 cluster 4 題」，每題對應 1 個類型：
  - **泛問**：「台北有哪些 [服務類型] 公司推薦？」
  - **比較**：「[服務 A] 與 [服務 B] 差別？」
  - **情境**：「想做 [具體主題] 該找誰？」
  - **長尾**：具體場景 + 規模 + 預算
- **理由：** 4 類型覆蓋從泛搜尋到長尾意圖光譜；20 題首輪採 PRD 下限（節省 4 平台執行工時 12-20h）；後續 phase 可擴充至 40 題上限。
- **取捨：** 首輪僅 20 題可能對 lost prompts 涵蓋不全；可在 Phase 5 baseline 第二輪擴充。
- **來源：** 04-CONTEXT.md GATE-4A + 村長 2026-05-15 AskUserQuestion confirm

---

## DEC-baseline-platforms-three-paid-perplexity-free

- **標題：** Phase 4 baseline 測試採 3 平台付費訂閱 + Perplexity free tier
- **狀態：** **LOCKED**（村長 2026-05-15 confirm）
- **範圍：** Plan 4.2 baseline 240 次測試執行
- **決策陳述：** 4 平台訂閱狀況：ChatGPT Plus ✅ / Claude Pro ✅ / Gemini Advanced ✅ / Perplexity Pro ❌。Perplexity 改用 free tier 執行（單日 5 次 Pro Search 限制 → 每日跑 5 題，4 天跑完 20 題）。
- **理由：** 不為 baseline 一次性任務升 Perplexity Pro；free tier 已能取得自然搜尋結果，僅 Sonar 模型版本受限（free 用 Sonar / Pro 可選 Sonar Reasoning Pro 等），對 baseline 「品牌是否被提及」測試影響可接受。
- **取捨：** Perplexity baseline 受限於 free tier rate limit（5 題/日），Plan 4.2 Perplexity 段需拆 4 天執行；結果可信度需在 04-baseline-report.md 註明「Perplexity 採 Sonar free tier」避免後續第二輪重測不一致。
- **緩解：** CSV `notes` 欄位每題記錄當天 Perplexity 使用的模型版本（free Sonar 預設模型名）；若後續 Phase 5 需要與 Pro 一致，再升訂閱。
- **來源：** 村長 2026-05-15 AskUserQuestion 訂閱清單 confirm
