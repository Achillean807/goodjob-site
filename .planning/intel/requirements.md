# 需求清單

> 由 `gsd-doc-synthesizer` 從 PRD `docs/seo-aeo-improvement-plan-20260513.html` 萃取。所有需求皆來自同一份 PRD，無跨檔 acceptance 衝突。需求 ID 以 `REQ-{slug}` 命名，slug 為任務語意縮寫。

---

## P0 ─ 7 天內：索引安全與技術基礎

### REQ-prod-sitemap-verify

- **描述：** 驗證正式站 `/sitemap.xml` 是否包含 PostgreSQL 內所有正式作品頁，並排除舊靜態 sitemap 被 Cloudflare CDN 快取的可能。
- **驗收條件：**
  - `curl https://goodjob.weddingwishlove.com/sitemap.xml` 回傳的 URL 數 ≥ PostgreSQL 內作品數
  - sitemap 不含舊靜態 `data/articles.json` 中已下架條目
  - 已在 Google Search Console 提交並顯示「成功」狀態
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「Sitemap」、§ 三 P0、§ 六「必要資料缺口」
- **範圍：** server.py 動態 sitemap、CDN cache 設定

### REQ-admin-noindex

- **描述：** `/admin/` 全部 response 需帶 `X-Robots-Tag: noindex, nofollow, noarchive`，robots.txt 同步 disallow。
- **驗收條件：**
  - `curl -I https://goodjob.weddingwishlove.com/admin/` response header 含 `X-Robots-Tag: noindex, nofollow, noarchive`
  - robots.txt 含 `Disallow: /admin/`
  - GSC URL Inspection 顯示 `/admin/` 為「Excluded by 'noindex' tag」
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「Robots / 私有頁」、§ 三 P0、§ 三 robots.txt 調整方向

### REQ-support-pages-metadata

- **描述：** 為 `/sort-hat/`、`/wedding-packages/`、`/wedding-packages/outdoor.html`、`/teabar.html` 補齊 description、canonical、OG/Twitter，並加入 Product/Service/FAQ/Breadcrumb schema。
- **驗收條件：**
  - 每頁 `<meta name="description">` 70-110 中文字
  - 每頁 `<link rel="canonical">` 指向自身 production URL
  - 每頁 OG/Twitter card meta 齊全（title/description/image/url）
  - 每頁至少 1 個 schema（Product 或 Service 或 FAQ 或 Breadcrumb）通過 Google Rich Results Test 無錯誤
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「支援銷售頁」、§ 三 P0

### REQ-rich-results-validation

- **描述：** 用 Google Rich Results Test 驗證首頁、合作流程頁、MUSE 頁與 5 個代表作品頁的 JSON-LD，確認 schema 內容與頁面可見文字一致。
- **驗收條件：**
  - 8 個 URL 全數通過 Rich Results Test，0 個 error
  - schema 中聲明的內容（標題、描述、圖片）皆出現於頁面可見文字
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P0

### REQ-homepage-server-rendered-cases

- **描述：** 首頁加入伺服器端或靜態 HTML 即可讀的精選案例摘要與服務內鏈，降低純 JS 渲染對 AI crawler 的不確定性。
- **驗收條件：**
  - `curl https://goodjob.weddingwishlove.com/` 不執行 JS 即可看到至少 3 個精選作品標題與內鏈
  - 內鏈指向具體作品頁（`/works/{id}`）或服務 pillar 頁
  - 首頁 description 擴充到 70-110 中文字
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二「首頁基礎 SEO」、§ 三 P0

---

## P1 ─ 30 天內：服務主題集群與內容 ownership

### REQ-gsc-query-export

- **描述：** 從 Google Search Console 匯出最近 3 個月 `page + query` 資料，做 cannibalization audit。
- **驗收條件：**
  - 取得至少 3 個月 GSC 匯出檔（CSV / Looker Studio）
  - 產出 cannibalization 報告：標出 ≥ 2 個 URL 競爭同一 query 的案例與處置方向（合併、改 title、改 H1）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1、§ 六「必要資料缺口」

### REQ-pillar-pages-five

- **描述：** 建立 5 個 pillar 頁，分別對應 5 大服務集群。
- **驗收條件：**
  - 5 個 URL 上線且 HTTP 200：
    1. `/services/brand-event-decoration/`（品牌活動佈置）
    2. `/services/exhibition-space-design/`（展場空間設計）
    3. `/services/year-end-party-decoration/`（春酒尾牙佈置）
    4. `/services/civil-office-transformation/`（戶政空間改造）
    5. `/wedding-packages/`（婚禮場景佈置，沿用既有頁強化）
  - 每個 pillar 頁含：服務介紹、代表案例內鏈、FAQ 區塊、相關作品列表
  - sitemap.xml 收錄全部 5 頁
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1、§ 四 內容集群表

### REQ-works-cluster-mapping

- **描述：** 將 29+ 件作品頁歸到對應 cluster；作品頁加回連到 pillar 頁，pillar 頁連到代表作品與 FAQ。
- **驗收條件：**
  - 每件作品 metadata 含 cluster 標記（資料庫欄位或前端標籤）
  - 每件作品頁含 1 個指向 pillar 頁的內鏈
  - 每個 pillar 頁列出該 cluster ≥ 3 個代表作品
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1

### REQ-case-template-expansion

- **描述：** 作品頁模板擴充為案例格式：活動背景、場地限制、設計策略、製作亮點、適合產業、成果照片。
- **驗收條件：**
  - 作品頁模板支援 6 個區塊欄位：背景／限制／策略／亮點／產業／成果
  - 每件作品至少必填「背景、限制、解法、結果」4 區塊
  - 既有 29+ 件作品中至少 10 件已補完 6 區塊（其餘漸進補完）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1、§ 四「作品頁模板建議」

### REQ-faq-per-cluster

- **描述：** 每個服務 cluster 建立 4-6 題實務 FAQ，答案以 60-120 字直接回答，方便 AI 摘錄。
- **驗收條件：**
  - 5 個 cluster 各有 4-6 題 FAQ
  - 每題答案長度 60-120 中文字
  - FAQ 區塊以 `FAQPage` schema 標記
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P1

---

## P2 ─ 60 天內：AEO / GEO 引用率提升

### REQ-ai-citation-baseline

- **描述：** 建立跨平台 citation baseline：ChatGPT、Claude、Gemini、Perplexity 各測 20-40 題，記錄品牌是否被提及、被引用、競品是誰。
- **驗收條件：**
  - 4 個平台 × 20-40 題 prompt 完成測試
  - 每筆紀錄：prompt / 平台 / 是否提及村山良作 / 是否引用站內 URL / 競品名單
  - baseline 報告含 lost prompts 清單（村山未被提及或未被引用的題目）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五 Baseline prompt 組、§ 六「必要資料缺口」

### REQ-lost-prompts-answer-content

- **描述：** 針對 lost prompts 製作答案型內容（活動佈置公司怎麼選、品牌活動佈置預算、展場設計與拍照牆差異、春酒尾牙主題提案等）。
- **驗收條件：**
  - 依 baseline 產出至少 4 篇答案型長文，每篇對應 ≥ 3 個 lost prompts
  - 每篇含明確答案區塊、結構化 FAQ、來源／案例引用
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五「Prompt-matched FAQ」修補包

### REQ-comparison-pages

- **描述：** 新增比較表與決策框架，讓 AI 有可摘錄 criteria，例如預算區間、施工時間、撤場、場地尺寸、互動需求。
- **驗收條件：**
  - 至少 2 個中立比較頁上線：「品牌活動佈置 vs 展場設計」、「客製佈置 vs 套組方案」
  - 每頁含可機讀的比較表（HTML `<table>` + 必要時 schema）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五「Comparison pages」修補包

### REQ-llms-txt-update

- **描述：** 更新 `llms.txt`：加入服務分類、代表作品 URL、獎項頁、聯絡方式與最近更新日期；每月檢查一次。
- **驗收條件：**
  - `llms.txt` 含 5 個 cluster 條目與代表作品 URL
  - 含獎項頁 URL（MUSE 等）與聯絡資訊
  - 含 `Last-Updated:` 欄位，每月手動或腳本更新
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五「Entity clarity」修補包

### REQ-robots-waf-bot-allow

- **描述：** 確認 robots.txt 與 Cloudflare WAF 允許 `OAI-SearchBot`、`PerplexityBot` 與一般搜尋 crawler 讀取公開內容。
- **驗收條件：**
  - robots.txt 含 `OAI-SearchBot` 與 `PerplexityBot` 個別段落（Allow `/`、Disallow `/quote/`、`/admin/`）
  - Cloudflare WAF 沒有 block 兩者 user-agent 或官方 IP 段
  - robots.txt 結尾含 `Sitemap:` 與 `LLMs-Txt:` 指向 production URL
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 三 robots.txt 調整方向

---

## P3 ─ 90 天內：權威訊號與持續成長

### REQ-awards-media-page

- **描述：** 建立「得獎與媒體」頁，集中 MUSE、合作策展、第三方報導與高可信外部連結。
- **驗收條件：**
  - 至少 1 個 `/awards/` 或 `/press/` 頁上線
  - 頁面列出 ≥ 1 個第三方媒體報導 + 既有 MUSE 得獎條目
  - 含 `Organization` 與 `Award` 或 `Article` schema
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P3、§ 五「Third-party proof」修補包

### REQ-external-trust-signals

- **描述：** 推動可被引用的外部訊號：合作單位頁面、媒體稿、案例採訪、Google Business Profile、社群固定貼文。
- **驗收條件：**
  - Google Business Profile 完整資料（含網址、營業時間、相片）已驗證
  - 至少 1 篇媒體稿或合作單位頁面回連
  - 主要社群（IG / FB / LINE）固定貼文含官網內鏈
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P3、§ 五「Third-party proof」修補包

### REQ-monthly-longtail-content

- **描述：** 每月發布 2 篇長尾內容，聚焦真實業主問題，不做泛用靈感文。
- **驗收條件：**
  - 每月 ≥ 2 篇文章上線
  - 每篇對應 1 個明確業主問題（題目以「怎麼／多少／要準備什麼」開頭較佳）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P3

### REQ-weekly-report-dashboard

- **描述：** 建立 Looker Studio 或表格週報，追蹤 GSC、GA4、AI referral、表單／LINE 點擊。
- **驗收條件：**
  - 週報自動或半自動更新，覆蓋下列來源：GSC（impressions / clicks / CTR）、GA4（自然搜尋 + AI referral）、CTA 點擊
  - 每週可由 1 個 URL 看到該週數據
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P3、§ 六「必要資料缺口」

---

## 競合需求 / 多版 acceptance 標記

無。本批僅 1 份 PRD，無跨檔需求重疊。
