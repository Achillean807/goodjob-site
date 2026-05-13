## Conflict Detection Report

本次 `gsd-ingest-docs` 處理 1 份外部 PRD（`docs/seo-aeo-improvement-plan-20260513.html`），模式 `new`，無既有 `.planning/` context 比對。所有衝突檢測皆與既有 codebase（特別是 `CLAUDE.md`）對照。

### BLOCKERS (0)

無。本批僅 1 份 PRD，無跨檔 LOCKED-vs-LOCKED 衝突；既有 `.planning/` 為首次建立，無既有 locked 決策可衝突；classifier 已確認 type=PRD high confidence，無 UNKNOWN-low 條目；cross_refs 圖無迴圈。

### WARNINGS (2)

[WARNING] 作品數來源未對齊
  Found: PRD § 二「動態作品頁」推估「本地舊資料有 29 件作品」；CLAUDE.md 明確記載「正式環境 PostgreSQL 27 篇」
  Source: docs/seo-aeo-improvement-plan-20260513.html, E:/ai_website/goodjob-site/CLAUDE.md
  Impact: 後續 P0 驗收（sitemap URL 數 ≥ 作品數）無法判定基準；pillar 頁規劃「將 29+ 件歸入 cluster」可能虛報數字
  → 在 Phase 1（P0）啟動前由村長 SSH 至 ACH-ClawHome 對 PostgreSQL 跑 `SELECT COUNT(*) FROM articles WHERE published = true` 校正；以查詢結果為唯一基準更新 `requirements.md`

[WARNING] 啟動 P1 / P2 須前置資料未就緒
  Found: PRD § 六「必要資料缺口」列出 4 項前置：GSC 3-6 個月資料、GA4/server log referral、正式 PostgreSQL 作品數與 sitemap、4 個 AI 平台 baseline
  Source: docs/seo-aeo-improvement-plan-20260513.html § 六
  Impact: 缺資料則 Phase 2 cannibalization audit、Phase 4 AI baseline、Phase 7 週報三項無法驗收
  → roadmapper 需在對應 phase 加上「前置條件未就緒則延後」的明確 gate；建議 Phase 1 同步補資料管線（GSC 連線、GA4 export、PostgreSQL count 查詢腳本）

### INFO (5)

[INFO] 首頁 SPA 渲染與作品頁 SSR 一致性釐清
  Note: PRD § 二指出「首頁作品卡由 JS/API 渲染，非 Google 類 crawler 可能較難完整讀到」；CLAUDE.md 確認首頁為 SPA hash routing 但 `/works/{id}` 為 SSR。兩者一致，僅首頁的 SPA 段需要被 server-rendered 案例摘要強化（REQ-homepage-server-rendered-cases 已涵蓋）。無實質衝突。
  Source: docs/seo-aeo-improvement-plan-20260513.html § 二、E:/ai_website/goodjob-site/CLAUDE.md 入口與啟動

[INFO] 5 個新 pillar 路徑與既有 routing 並存
  Note: PRD 建議新建 `/services/brand-event-decoration/`、`/services/exhibition-space-design/`、`/services/year-end-party-decoration/`、`/services/civil-office-transformation/`；既有 `/wedding-packages/`、`/teabar.html`、`/sort-hat/` 不受影響。server.py 需新增 4 條 route 與動態 sitemap 收錄，無衝突。
  Source: docs/seo-aeo-improvement-plan-20260513.html § 四、E:/ai_website/goodjob-site/CLAUDE.md 子頁面

[INFO] data/articles.json 退役狀態雙方一致
  Note: PRD 提到「本地舊資料有 29 件作品；README 顯示正式環境改用 PostgreSQL」；CLAUDE.md 已明確「作品文案、相簿圖片 URL/順序、帳號、權限與設定都在 PostgreSQL；`data/articles.json` 只作為舊資料/備份材料，不再是正式資料源」。雙方共識，僅作為背景。
  Source: docs/seo-aeo-improvement-plan-20260513.html § 二、E:/ai_website/goodjob-site/CLAUDE.md 開頭聲明

[INFO] robots.txt 從 6 行擴充到含 AI bot 段落
  Note: 既有 robots.txt 6 行（disallow /quote/、指向 LLMs-Txt）；PRD 建議擴充含 `OAI-SearchBot` 與 `PerplexityBot` 段落、補 `Disallow: /admin/`、結尾保留 `Sitemap:` 與 `LLMs-Txt:`。屬於擴增非取代，無衝突。
  Source: docs/seo-aeo-improvement-plan-20260513.html § 三 robots.txt 調整方向、E:/ai_website/goodjob-site/CLAUDE.md 核心檔案清單

[INFO] PRD 未產生 LOCKED 決策
  Note: PRD 預設 precedence=0 但 locked=false（classifier JSON 確認）；本批未匯入 ADR 等級文件。`decisions.md` 列出的 6 條為 proposed 方向性決策，後續實作期間若村長要求鎖定可升格寫成正式 ADR。
  Source: .planning/intel/classifications/seo-aeo-improvement-plan-20260513.json
