# 限制清單

> 由 `gsd-doc-synthesizer` 從 PRD `docs/seo-aeo-improvement-plan-20260513.html` § 六 KPI 與必要資料缺口萃取。

---

## CONSTR-indexation-targets

- **類型：** nfr（非功能性需求，索引）
- **標題：** 索引覆蓋率與私有頁排除
- **內容：**
  - 公開頁需達 90%+ 可索引（以 GSC URL Inspection / Coverage 報告為準）
  - 私有頁（`/admin/`、`/quote/`）需為 0 筆索引
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 六 KPI Indexation 列

---

## CONSTR-technical-cwv-good

- **類型：** nfr（Core Web Vitals）
- **標題：** Core Web Vitals 須達 Good
- **內容：**
  - LCP、INP、CLS 三項皆達 Google「Good」門檻
  - HTTP 響應碼正常（公開頁均為 200）
  - 主要 schema 通過 validation 無錯誤
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 六 KPI Technical 列

---

## CONSTR-schema-text-consistency

- **類型：** api-contract（結構化資料一致性）
- **標題：** Schema 內容須與頁面可見文字一致
- **內容：**
  - JSON-LD 中宣告的標題、描述、圖片必須在頁面 HTML 可見區塊中真實出現
  - 違反此原則會被 Google 視為 spammy structured data，影響整站信譽
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P0「用 Rich Results Test 驗證」、§ 七 Google Search Central 參考

---

## CONSTR-non-js-readable

- **類型：** nfr（可爬性）
- **標題：** 重要內容須在非 JS 渲染狀態下可讀
- **內容：**
  - 首頁精選案例與服務內鏈須在 server-rendered HTML 中可見（不依賴 JS 執行）
  - 動態作品頁 `/works/{id}` 必須是 SSR，不可改成純 SPA
  - 理由：降低 AI crawler 與部分搜尋引擎 fetch 失敗風險
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「首頁基礎 SEO」、§ 三 P0

---

## CONSTR-private-page-noindex

- **類型：** schema（HTTP header / robots）
- **標題：** 私有頁雙保險
- **內容：**
  - `robots.txt` Disallow 不等於 noindex；不可僅靠 robots
  - 私有頁必須同時加 `X-Robots-Tag: noindex, nofollow, noarchive` 或 `<meta name="robots" content="noindex">`
  - 適用對象：`/admin/`、`/quote/`
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 robots.txt 調整方向 註解

---

## CONSTR-ai-crawler-allowlist

- **類型：** protocol（robots / WAF）
- **標題：** 不可阻擋 AI crawler 公開內容
- **內容：**
  - `OAI-SearchBot`、`PerplexityBot` 在公開區段必須可抓
  - Cloudflare WAF 不可 block 上述 user-agent 或官方 IP 段
  - robots.txt 必須結尾含 `Sitemap:` 與 `LLMs-Txt:` 指向 production
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 七 OpenAI / Perplexity 參考

---

## CONSTR-faq-answer-length

- **類型：** schema（FAQ 內容規格）
- **標題：** FAQ 答案 60-120 字直接回答
- **內容：**
  - 每題 FAQ 答案以 60-120 中文字回答，避免廢話開頭
  - 必須以 `FAQPage` schema 標記
  - 適用對象：5 個 cluster 各 4-6 題
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1

---

## CONSTR-description-length

- **類型：** schema（metadata 規格）
- **標題：** Meta description 70-110 中文字
- **內容：**
  - 首頁與支援頁 description 須擴充到 70-110 中文字（避免過短被 Google 重寫）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「首頁基礎 SEO」、§ 三 P0

---

## CONSTR-data-availability-gaps

- **類型：** nfr（前置資料缺口）
- **標題：** 啟動 P1/P2 前必要資料
- **內容：**
  - Google Search Console 最近 3-6 個月 query/page 資料（驅動 P1 cannibalization audit）
  - GA4 或伺服器 log：自然搜尋、ChatGPT / Perplexity referral、LINE CTA 點擊（驅動 P3 週報）
  - 正式 PostgreSQL 作品數與正式 sitemap 實際輸出（驅動 P0 sitemap 驗證）
  - 4 個 AI 平台同一組 prompts 的 citation baseline（驅動 P2 lost-prompts 修補）
- **影響：** 若資料未就緒，對應 phase 無法啟動或驗收
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 六「必要資料缺口」

---

## CONSTR-non-deterministic-ai

- **類型：** nfr（KPI 訂定）
- **標題：** AI 引用為非決定性，不承諾引用率
- **內容：**
  - 不對外宣稱可保證 AI 引用率
  - AEO/GEO KPI 採「先建 baseline、後追蹤變化」策略
  - 每次重測使用同一組 prompts 才有可比性
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 七 footer-note、§ 六 KPI AEO/GEO 列
