# Phase 2: P1-A 內容集群骨架建立 — PLAN

**Created:** 2026-05-14
**Status:** Ready for execution
**Depends on:** Phase 1 全綠（5 plans + GA4/Clarity 已上線）+ GATE-2A 完成（cannibalization-report-20260514.md）+ GATE-2B 三項決策 LOCKED
**Total plans:** 6（5 pillar + 1 共通 deploy/sitemap/驗證）
**估時：** 2-3 週（含驗收）

---

## ▶ Plan Index

| Plan ID | REQ | Subject | Files Modified | 估時 |
|---------|-----|---------|----------------|------|
| 2.0 | REQ-pillar-pages-five | 共用 CSS + 代表案例 ID 取得 + Hero 圖選定 | `services/services.css` (new)、`.planning/phases/02-.../representatives.md` (new) | 0.5d |
| 2.1 | REQ-pillar-pages-five | `/services/business-event/` pillar（27 件） | `services/business-event/index.html` (new) | 1.5d |
| 2.2 | REQ-pillar-pages-five | `/services/party-spring-banquet/` pillar（16 件） | `services/party-spring-banquet/index.html` (new) | 1d |
| 2.3 | REQ-pillar-pages-five | `/services/magic-academy/` pillar（5 件 + sort-hat） | `services/magic-academy/index.html` (new)、`sort-hat/index.html` (補 breadcrumb 回鏈) | 1d |
| 2.4 | REQ-pillar-pages-five | `/services/civil-makeover/` pillar（14 件） | `services/civil-makeover/index.html` (new) | 1d |
| 2.5 | REQ-pillar-pages-five | `/services/wedding-tea-flower/` hub + 既有頁回鏈補丁 | `services/wedding-tea-flower/index.html` (new)、`teabar.html`、`wedding-packages/index.html`、`wedding-packages/outdoor.html` (各補 breadcrumb 回鏈) | 1.5d |
| 2.6 | REQ-pillar-pages-five | Sitemap 補 5 條 URL + 部署 + CF purge + Rich Results 驗證 | `server.py`（`_serve_sitemap`）、`.planning/phases/02-.../02-RICH-RESULTS-REPORT.md` (new) | 1d |

**執行順序：** 2.0（必先） → 2.1 / 2.2 / 2.3 / 2.4 / 2.5（可並行派發 codex）→ 2.6（必後，驗收 phase）

---

## Plan 2.0: 共用 CSS + 代表案例 ID 取得 + Hero 圖選定

**REQ:** `REQ-pillar-pages-five`（前置）
**Owner suggestion:** Opus 親自（需判斷視覺一致性 + 從 PostgreSQL 撈代表案例）

### Objective

為 5 個 pillar 建立共用樣式檔、從 PostgreSQL 撈出每個 cluster 的 featured 作品作為硬編碼代表案例，並選定每個 pillar 的 hero 圖。

### Files Modified

- `services/services.css`（新檔）— 5 個 pillar 共用樣式
- `.planning/phases/02-p1a-content-cluster/representatives.md`（新檔）— 5 個 pillar × 3 件代表案例對照表

### Tasks

1. **撈 featured 作品：**
   ```bash
   ssh achilean@100.102.51.64 'psql -d goodjob_site -t -A -F"|" -c "SELECT id, title, category, hero_image FROM articles WHERE featured = 1 AND category IN (\\"business\\",\\"party\\",\\"magic\\",\\"civil\\") ORDER BY category, featured_order NULLS LAST, row_index;"'
   ```

2. **若某 category featured 不足 3 件（特別是 magic 只有 5 件作品）→** 用該 category 第一張 `featured=true` 補齊；仍不夠就從非 featured 中挑 hero_image 完整的補。

3. **寫 `representatives.md`：**
   ```markdown
   # Phase 2 Pillar 代表案例對照表

   | Pillar | 案例 ID | 標題 | hero_image |
   |--------|--------|------|------------|
   | business-event | {id1} | {title} | {url} |
   | business-event | {id2} | {title} | {url} |
   | business-event | {id3} | {title} | {url} |
   | party-spring-banquet | ... | ... | ... |
   ...
   ```

4. **建立 `services/services.css`**（共用樣式，~150 行）：
   ```css
   /* services/services.css — Pillar 共用樣式（Phase 2） */
   :root {
     --pillar-bg: #0a0a0a;
     --pillar-text: #f5f5f5;
     --pillar-accent: #d4af37;
     --pillar-muted: #888;
   }
   .pillar-breadcrumb { padding: 12px 20px; background: rgba(255,255,255,0.04); font-size: 0.9rem; }
   .pillar-breadcrumb a { color: var(--pillar-accent); text-decoration: none; }
   .pillar-hero { padding: 80px 20px 60px; text-align: center; background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%); }
   .pillar-hero h1 { font-size: 2.4rem; margin: 0 0 16px; color: var(--pillar-text); }
   .hero-tagline { font-size: 1.1rem; color: var(--pillar-muted); max-width: 700px; margin: 0 auto; }
   .pillar-intro { max-width: 800px; margin: 0 auto; padding: 60px 20px; }
   .pillar-intro h2 { font-size: 1.6rem; color: var(--pillar-text); margin: 0 0 24px; }
   .pillar-intro p { line-height: 1.8; color: var(--pillar-muted); }
   .pillar-featured, .pillar-related { padding: 60px 20px; }
   .pillar-featured h2, .pillar-related h2 { font-size: 1.6rem; color: var(--pillar-text); margin: 0 0 32px; text-align: center; }
   .featured-grid, .related-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; max-width: 1200px; margin: 0 auto; }
   .case-card { display: block; background: rgba(255,255,255,0.04); border-radius: 8px; overflow: hidden; text-decoration: none; transition: transform 0.2s, background 0.2s; }
   .case-card:hover { transform: translateY(-4px); background: rgba(255,255,255,0.08); }
   .case-card img { width: 100%; height: 200px; object-fit: cover; display: block; }
   .case-card h3 { padding: 16px; color: var(--pillar-text); font-size: 1rem; margin: 0; }
   .pillar-faq { padding: 60px 20px; max-width: 800px; margin: 0 auto; }
   .pillar-cta { padding: 60px 20px; text-align: center; background: rgba(212,175,55,0.05); }
   .pillar-cta a { display: inline-block; margin: 8px 12px; padding: 12px 24px; border: 1px solid var(--pillar-accent); color: var(--pillar-accent); text-decoration: none; border-radius: 4px; transition: background 0.2s; }
   .pillar-cta a:hover { background: var(--pillar-accent); color: #0a0a0a; }
   .cta-link { display: inline-block; margin-top: 16px; color: var(--pillar-accent); text-decoration: underline; }
   @media (max-width: 640px) {
     .pillar-hero h1 { font-size: 1.8rem; }
     .pillar-intro, .pillar-featured, .pillar-related { padding: 40px 16px; }
   }
   ```

### Verification

- `representatives.md` 含 15 件（5 pillar × 3）案例 ID + hero_image，且圖檔 URL `curl -I` 全部 200
- `services/services.css` 本機跑 `npx stylelint services/services.css`（若 stylelint 不可用則 skip）通過

### Acceptance Criteria

- [ ] `representatives.md` 列出 5 × 3 = 15 件代表案例（含實際存在的 id、title、hero_image）
- [ ] `services/services.css` 檔案存在且 syntax 正確（瀏覽器載入無 console error）

### Risks

- **R2.0.1** magic category 只有 5 件，featured 可能 < 3 → 補非 featured 中 hero_image 最完整的，註明於 representatives.md
- **R2.0.2** hero_image 若為破圖 URL → 改用 R2 既有有效 URL，盡量挑活動主視覺照

### autonomous

`true`（Opus 親自跑 SQL + 寫對照表 + 寫 CSS）

---

## Plan 2.1: `/services/business-event/` pillar（27 件 business）

**REQ:** `REQ-pillar-pages-five`
**Owner suggestion:** Codex CLI（按 CONTEXT specifics 範本批次生成）

### Objective

建立業務主題化品牌活動 pillar hub 頁，涵蓋 27 件 business cluster 作品，定位「主題場景」「主題佈置」純藍海關鍵字。

### Files Modified

- `services/business-event/index.html`（新檔，~400 行）

### Tasks

1. **依 CONTEXT.md `<specifics>` 範本建立 `services/business-event/index.html`**，填入：
   - title: `主題化品牌活動｜主題場景設計｜村山良作 MURAYAMA GOODJOB`
   - description: 「村山良作為品牌活動打造主題化場景，從新品發表到企業大型活動，把品牌敘事轉化成可被體驗的現場。27 件主題活動 portfolio，涵蓋汽車、3C、餐飲、時尚與藝文品牌。」（約 90 字）
   - canonical: `https://goodjob.weddingwishlove.com/services/business-event/`
   - og:image: 從 representatives.md 取 business 第 1 件 hero_image
   - Hero 區 tagline: 「把品牌敘事轉化成可被走進、可被拍下、可被記住的現場。」
   - 服務介紹（~300 字）：說明主題化品牌活動的設計流程、適用場景、執行範疇
   - 3 件硬編碼代表案例（從 representatives.md 取）
   - 相關作品 client-side filter（`a.category === 'business'`）
   - CTA: 「看合作流程」→ `/workflow.html`

2. **Service schema** `hasOfferCatalog.itemListElement` 填入 3 件代表案例 url

3. **GA4 + Clarity snippet** 從 `teabar.html` head 段 copy 過來（Phase 1.6 既有）

### Verification

```bash
# 本機跑：python3 server.py --port 8000
curl -s http://localhost:8000/services/business-event/ | grep -c '<a class="case-card"'
# 預期：≥ 3（硬編碼代表案例）

curl -s http://localhost:8000/services/business-event/ | grep -E 'rel="canonical"|og:title|application/ld\+json'
# 預期：canonical / og / schema 齊備
```

### Acceptance Criteria

- [ ] HTTP 200 + HTML 內 ≥ 3 個 `<a class="case-card" href="/works/{id}">` 硬編碼
- [ ] head 含 canonical、OG/Twitter、Service schema、BreadcrumbList schema
- [ ] description 70-110 中文字
- [ ] body 含 hero / 服務介紹 / 代表案例 / 相關作品 grid / FAQ placeholder / CTA 6 區塊
- [ ] Rich Results Test 0 error（Plan 2.6 統一驗收）

### Risks

- **R2.1.1** Hero 圖若為 R2 上不存在 URL → 部署前先 `curl -I` 確認
- **R2.1.2** Schema 中 `name` / `description` 文字必須在頁面可見（Google 規則）→ 服務介紹文案要包含這些關鍵字

### autonomous

`true`（codex CLI 走 wrapper，按 representatives.md + CONTEXT 範本一次寫完）

---

## Plan 2.2: `/services/party-spring-banquet/` pillar（16 件 party）

**REQ:** `REQ-pillar-pages-five`
**Owner suggestion:** Codex CLI

### Objective

建立春酒尾牙派對 pillar hub 頁，涵蓋 16 件 party cluster 作品，定位「春酒尾牙」「企業派對佈置」純藍海關鍵字。

### Files Modified

- `services/party-spring-banquet/index.html`（新檔，~400 行）

### Tasks

1. **依範本建立檔案**，填入：
   - title: `春酒尾牙｜企業派對主題佈置｜村山良作`
   - description: 「年度春酒、尾牙、企業派對主題佈置，從主視覺、舞台、簽到背板到拍照打卡點全套設計。村山良作 16 件企業派對 portfolio，主題從復古港風到未來科技，把員工感謝晚會做成品牌時刻。」（約 95 字）
   - canonical: `/services/party-spring-banquet/`
   - Hero tagline: 「把年度春酒做成員工最期待的品牌時刻。」
   - 服務介紹（~300 字）：春酒尾牙主題化設計流程、舞台規劃、活動動線
   - 3 件硬編碼 party 代表案例
   - CTA: 「看合作流程」→ `/workflow.html`

2. Schema / OG / GA4 同 Plan 2.1 結構

### Verification

```bash
curl -s http://localhost:8000/services/party-spring-banquet/ | grep -c '<a class="case-card"'  # ≥ 3
curl -s http://localhost:8000/services/party-spring-banquet/ | grep 'category="party"' || grep "'party'"  # client-side filter 程式碼存在
```

### Acceptance Criteria

同 Plan 2.1（六區塊 + schema + canonical + description 字數）

### Risks

- **R2.2.1** party 詞競爭較高（atelier 有些婚禮派對混合詞）→ description 明確強調「春酒尾牙 / 企業派對」與婚禮派對作切割

### autonomous

`true`

---

## Plan 2.3: `/services/magic-academy/` pillar（5 件 magic + sort-hat）

**REQ:** `REQ-pillar-pages-five`
**Owner suggestion:** Codex CLI

### Objective

建立魔法學院 IP pillar hub 頁，涵蓋 5 件 magic cluster 作品 + 內鏈既有 `/sort-hat/` 座位查詢工具，定位「魔法學院」「Harry Potter 主題」純藍海關鍵字。同步在 `/sort-hat/index.html` 加 pillar 回鏈 breadcrumb。

### Files Modified

- `services/magic-academy/index.html`（新檔，~400 行）
- `sort-hat/index.html`（補 `<nav class="pillar-breadcrumb">` 回鏈）

### Tasks

1. **依範本建立 `services/magic-academy/index.html`**：
   - title: `魔法學院主題活動｜Harry Potter 風格場景｜村山良作`
   - description: 「魔法學院主題活動場景設計，從霍格華茲入學儀式、分院帽座位查詢、霍格華茲走廊到魁地奇場域，5 件 IP 主題作品打造可被走進的魔法世界。」（約 80 字）
   - Hero tagline: 「打造可被走進的霍格華茲現場。」
   - 服務介紹（~300 字）：強調 Harry Potter 主題在企業活動、學校活動、生日派對的應用，IP 法律邊界（致敬風格非授權）
   - 3 件硬編碼 magic 代表案例（若 featured < 3 → 補非 featured 中 hero 完整者，於 representatives.md 註明）
   - **特殊區塊** `pillar-tools`：突出展示 `/sort-hat/` 互動工具：
     ```html
     <section class="pillar-tools">
       <h2>互動工具</h2>
       <a class="tool-card" href="/sort-hat/">
         <h3>分類帽入席預言查詢系統</h3>
         <p>用魔法分類帽的互動方式，讓賓客掃 QR 就找到自己的桌次。</p>
       </a>
     </section>
     ```
   - CTA: 「看合作流程」→ `/workflow.html`、「試玩分類帽」→ `/sort-hat/`

2. **Edit `sort-hat/index.html`** 在 `<body>` 開頭 `<header>` 之前（或 hero 上方）加：
   ```html
   <nav class="pillar-breadcrumb">
     <a href="/services/magic-academy/">← 回到魔法學院 pillar</a>
   </nav>
   ```
   並在 head 加 `<link rel="stylesheet" href="/services/services.css?v=20260514" />` 引用 pillar-breadcrumb 樣式（若 sort-hat 已有 inline CSS，可改為在 sort-hat CSS 中加同樣的 `.pillar-breadcrumb` rule）

### Verification

```bash
curl -s http://localhost:8000/services/magic-academy/ | grep -c '<a class="case-card"'  # ≥ 3
curl -s http://localhost:8000/services/magic-academy/ | grep '/sort-hat/' | head -3  # 至少 2 處內鏈
curl -s http://localhost:8000/sort-hat/ | grep 'pillar-breadcrumb'  # 回鏈存在
```

### Acceptance Criteria

- [ ] 六區塊齊全（特別含 pillar-tools 區塊）
- [ ] 內含 `/sort-hat/` 內鏈 ≥ 2 處
- [ ] `/sort-hat/index.html` 含 pillar-breadcrumb 回鏈
- [ ] Schema / canonical / OG 齊備

### Risks

- **R2.3.1** magic 只有 5 件作品，featured 可能不足 3 → Plan 2.0 已處理 fallback
- **R2.3.2** sort-hat/index.html 結構特殊（Harry Potter 主題自包含），補 breadcrumb 時注意不要破壞既有樣式 → 加在 `<body>` 最頂部，獨立區塊

### autonomous

`true`（codex 一次寫 pillar + 補 sort-hat breadcrumb diff）

---

## Plan 2.4: `/services/civil-makeover/` pillar（14 件 civil）

**REQ:** `REQ-pillar-pages-five`
**Owner suggestion:** Codex CLI

### Objective

建立戶政空間改造 pillar hub 頁，涵蓋 14 件 civil cluster 作品（含 zhongshan-civil），定位「戶政事務所改造」「公部門空間翻新」純藍海關鍵字（atelier 完全沒搶到的 B2G 商機）。

### Files Modified

- `services/civil-makeover/index.html`（新檔，~400 行）

### Tasks

1. **依範本建立檔案**：
   - title: `戶政事務所空間改造｜公部門空間翻新｜村山良作`
   - description: 「戶政事務所、區公所、市民服務中心空間改造設計，從等候動線、櫃台美學到拍照打卡點全套規劃。村山良作 14 件公部門空間改造 portfolio，讓辦證件也是一場美好體驗。」（約 95 字）
   - Hero tagline: 「讓辦證件也是一場美好的體驗。」
   - 服務介紹（~300 字）：公部門採購流程適配、空間動線美學、預算內最大化視覺效果
   - 3 件硬編碼 civil 代表案例（zhongshan-civil 應為其中之一）
   - CTA: 「看合作流程」→ `/workflow.html`

2. Schema / OG / GA4 同範本

### Verification

```bash
curl -s http://localhost:8000/services/civil-makeover/ | grep -c '<a class="case-card"'  # ≥ 3
curl -s http://localhost:8000/services/civil-makeover/ | grep -E 'zhongshan-civil|戶政'  # 預期：≥ 2
```

### Acceptance Criteria

同 Plan 2.1（六區塊 + schema + canonical + description）

### Risks

- **R2.4.1** B2G 客戶決策週期長，pillar 上線後短期不會立即帶詢問 → 由 Phase 4 AI baseline 月度追蹤效果

### autonomous

`true`

---

## Plan 2.5: `/services/wedding-tea-flower/` hub + 既有頁回鏈補丁

**REQ:** `REQ-pillar-pages-five`
**Owner suggestion:** Codex CLI（pillar 主檔 + 3 個 patch 一次寫）

### Objective

建立第 5 個 pillar — 婚禮花果茶 hub，定位 cannibalization §3.1/3.2 處置（迎賓茶 CRITICAL / 囍茶 CRITICAL），整合既有 `/teabar.html` 與 `/wedding-packages/*`，並在三個既有頁加 pillar 回鏈 breadcrumb 形成內鏈閉環。

### Files Modified

- `services/wedding-tea-flower/index.html`（新檔，~450 行）
- `teabar.html`（補 `<nav class="pillar-breadcrumb">` 回鏈）
- `wedding-packages/index.html`（補回鏈）
- `wedding-packages/outdoor.html`（補回鏈）

### Tasks

1. **建立 `services/wedding-tea-flower/index.html`**（CONTEXT.md `<specifics>` Wedding-tea-flower 特殊版本範本）：
   - title: `婚禮花果茶與場景佈置｜囍茶迎賓茶｜村山良作`
   - description: 「客製化婚禮迎賓花果茶與婚禮場景套組整合方案。村花囍茶 3 款客製 LOGO 茶飲 + 經典/華麗/戶外/室內 4 種場景套組，從入場迎賓到送客一條龍。」（約 85 字）
   - canonical: `/services/wedding-tea-flower/`
   - Hero tagline: 「從入場迎賓到送客回禮，把婚禮現場做成可被走進的故事。」
   - 服務介紹（~350 字）：強調「花果茶 × 場景佈置」整合敘事，與 atelier 形成「info / case study」區隔（cannibalization §6.2 第 2 點）
   - **婚禮花果茶區塊**：3 張茶飲圖卡（六月青果 / 鮮果蜜境 / 玫目清秀） + 「看完整方案 → /teabar.html」CTA
   - **婚禮場景套組區塊**：4 張套組圖卡（經典 / 華麗 / 戶外證婚 / 戶外送客） + 「看室內套組 → /wedding-packages/」「看戶外套組 → /wedding-packages/outdoor.html」CTA
   - FAQ placeholder
   - CTA: 「看合作流程」→ `/workflow.html`、「囍茶方案」→ `/teabar.html`

2. **Service schema** 用雙 `hasOfferCatalog`：
   ```json
   "hasOfferCatalog": [
     {
       "@type": "OfferCatalog",
       "name": "婚禮花果茶",
       "itemListElement": [
         { "@type": "Offer", "itemOffered": { "@type": "Product", "name": "六月青果", "url": "https://goodjob.weddingwishlove.com/teabar.html" } },
         { "@type": "Offer", "itemOffered": { "@type": "Product", "name": "鮮果蜜境", "url": "https://goodjob.weddingwishlove.com/teabar.html" } },
         { "@type": "Offer", "itemOffered": { "@type": "Product", "name": "玫目清秀", "url": "https://goodjob.weddingwishlove.com/teabar.html" } }
       ]
     },
     {
       "@type": "OfferCatalog",
       "name": "婚禮場景套組",
       "itemListElement": [
         { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "經典送客背景", "url": "https://goodjob.weddingwishlove.com/wedding-packages/" } },
         { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "華麗舞台走道", "url": "https://goodjob.weddingwishlove.com/wedding-packages/" } },
         { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "戶外證婚套組", "url": "https://goodjob.weddingwishlove.com/wedding-packages/outdoor.html" } },
         { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "戶外送客套組", "url": "https://goodjob.weddingwishlove.com/wedding-packages/outdoor.html" } }
       ]
     }
   ]
   ```

3. **Edit `teabar.html`** 在 `<body>` 開頭加 breadcrumb 回鏈：
   ```html
   <nav class="pillar-breadcrumb">
     <a href="/services/wedding-tea-flower/">← 回到婚禮花果茶 pillar</a>
   </nav>
   ```
   若 teabar.html 已 inline css 而沒引 services.css，可直接 inline 同樣的 `.pillar-breadcrumb` 樣式（不破壞既有結構）

4. **Edit `wedding-packages/index.html`** 同上加 breadcrumb 回鏈

5. **Edit `wedding-packages/outdoor.html`** 同上加 breadcrumb 回鏈

### Verification

```bash
curl -s http://localhost:8000/services/wedding-tea-flower/ | grep -c '<a.*href="/teabar.html"'  # ≥ 2
curl -s http://localhost:8000/services/wedding-tea-flower/ | grep -c '<a.*href="/wedding-packages/"'  # ≥ 1
curl -s http://localhost:8000/services/wedding-tea-flower/ | grep -c 'hasOfferCatalog'  # = 1

# 三個既有頁回鏈
for u in "/teabar.html" "/wedding-packages/" "/wedding-packages/outdoor.html"; do
  curl -s "http://localhost:8000$u" | grep 'services/wedding-tea-flower' && echo "PASS $u" || echo "FAIL $u"
done
```

### Acceptance Criteria

- [ ] `/services/wedding-tea-flower/` HTTP 200 + 含茶飲 3 張卡 + 套組 4 張卡
- [ ] 雙 OfferCatalog schema（茶飲 + 場景套組）通過 Rich Results Test
- [ ] `/teabar.html`、`/wedding-packages/`、`/wedding-packages/outdoor.html` 三頁含 pillar-breadcrumb 回鏈
- [ ] Cannibalization §3.1 §3.2 處置已落地（hub 頁與 atelier 形成 info/case study 區隔的文案）

### Risks

- **R2.5.1** Teabar 既有 Product schema（Phase 1 已修）與 wedding-tea-flower hub 的 OfferCatalog 內 Product 重複 → 不衝突（不同 URL 各自宣告自己的 schema），但 Rich Results 報告會顯示重複類型，這是預期行為
- **R2.5.2** wedding-packages 既有 hero 圖路徑 `wedding-packages/images/classic/hero.jpg` 是本機檔（未上 R2，CLAUDE.md §「保留本機的項目」確認）→ hub 引用時用相同路徑 OK

### autonomous

`true`（codex 一次寫 4 個檔的 diff）

---

## Plan 2.6: Sitemap 補 5 條 + 部署 + CF purge + Rich Results 驗證

**REQ:** `REQ-pillar-pages-five`（驗收 phase）
**Owner suggestion:** Opus 親自跑 deploy + 村長手動 Rich Results

### Objective

把 5 條 pillar URL 加進 `_serve_sitemap`、部署所有 pillar 與既有頁 diff、CF purge cache、跑 Rich Results Test 對 5 個 pillar 全綠驗收。

### Files Modified

- `server.py`（`_serve_sitemap` 靜態 URL list 從 7 條擴到 12 條）
- `.planning/phases/02-p1a-content-cluster/02-RICH-RESULTS-REPORT.md`（新檔，驗收報告）

### Tasks

1. **Edit `server.py:_serve_sitemap`**（L1708 附近的靜態頁 list）：
   ```python
   for loc in ["", "/teabar.html", "/workflow.html",
               "/wedding-packages/", "/wedding-packages/outdoor.html",
               "/sort-hat/", "/muse-2026.html",
               # Phase 2: pillar URLs
               "/services/business-event/",
               "/services/party-spring-banquet/",
               "/services/magic-academy/",
               "/services/civil-makeover/",
               "/services/wedding-tea-flower/"]:
   ```

2. **部署：** scp 全部 diff 到 ach-clawhome（5 個 pillar + 4 個 patch + server.py + services.css）→ restart service：
   ```bash
   scp -r services/ server.py teabar.html wedding-packages/ sort-hat/index.html achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
   ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
   ```

3. **CF purge：**
   ```powershell
   pwsh scripts/cf-purge.ps1 -Paths "/sitemap.xml,/services/business-event/,/services/party-spring-banquet/,/services/magic-academy/,/services/civil-makeover/,/services/wedding-tea-flower/,/teabar.html,/wedding-packages/,/wedding-packages/outdoor.html,/sort-hat/"
   ```

4. **線上 sitemap 驗收：**
   ```bash
   COUNT=$(curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -c '<loc>')
   echo "sitemap URL count: $COUNT"  # 預期：74

   for slug in business-event party-spring-banquet magic-academy civil-makeover wedding-tea-flower; do
     curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -q "services/$slug/</loc>" && echo "PASS $slug" || echo "FAIL $slug"
   done
   ```

5. **5 個 pillar URL HTTP 200 驗收：**
   ```bash
   for slug in business-event party-spring-banquet magic-academy civil-makeover wedding-tea-flower; do
     code=$(curl -s -o /dev/null -w "%{http_code}" https://goodjob.weddingwishlove.com/services/$slug/)
     echo "$slug: $code"
   done
   # 預期：5 個全 200
   ```

6. **Rich Results Test 驗收**（村長手動或 Playwright 自動化）：
   - 用 Playwright MCP 對 5 個 pillar URL 各跑一次 `https://search.google.com/test/rich-results`
   - 截圖存 `.planning/phases/02-p1a-content-cluster/evidence/rich-results-{slug}.png`
   - 預期：每個 URL `Detected items` 至少含 Service + BreadcrumbList，0 error

7. **產出 `02-RICH-RESULTS-REPORT.md`** 記錄 5 個 URL 的 Detected schema / Error / Warning / Pass-Fail

8. **GSC 提交（村長手動）：** 至 Search Console → 重新提交 `https://goodjob.weddingwishlove.com/sitemap.xml`，請求重新索引 5 個 pillar URL

### Verification

對應 Phase 2 Success Criteria：

```bash
# 1. cannibalization 報告 ≥ 2 案例 + 處置方向
test -f .planning/intel/gsc-export/cannibalization-report-20260514.md && echo "PASS"
# GATE-2A 已完成

# 2. 5 個 pillar URL 全部 HTTP 200
# 見 task 5

# 3. 每個 pillar 含服務介紹 + 案例內鏈≥3 + FAQ placeholder + 相關作品列表
for slug in business-event party-spring-banquet magic-academy civil-makeover; do
  echo "=== $slug ==="
  curl -s https://goodjob.weddingwishlove.com/services/$slug/ | grep -c '<a class="case-card"'  # ≥ 3
  curl -s https://goodjob.weddingwishlove.com/services/$slug/ | grep -c 'id="faq"'  # = 1
  curl -s https://goodjob.weddingwishlove.com/services/$slug/ | grep -c 'related-grid'  # = 1
done

# 4. /sitemap.xml 收錄 5 個 pillar URL
# 見 task 4
```

### Acceptance Criteria

直接對應 ROADMAP Phase 2 全部 4 條 Success Criteria：

- [ ] **SC2.1**（已達成）cannibalization 報告產出 ≥ 2 案例 + 處置方向 — GATE-2A 已交付
- [ ] **SC2.2** 5 個 pillar URL 全部 HTTP 200（含既有 wedding-packages 強化過的 hub）
- [ ] **SC2.3** 每個 pillar 頁含：服務介紹（200-400 字）、代表案例內鏈 ≥ 3、FAQ placeholder section、相關作品 grid container
- [ ] **SC2.4** `/sitemap.xml` 含 5 條 pillar URL（總數 ≥ 74）
- [ ] Rich Results Test 5 個 pillar 全綠（0 error）
- [ ] 既有 4 頁（teabar / wedding-packages / outdoor / sort-hat）含 pillar-breadcrumb 回鏈無 regression

### Risks

- **R2.6.1** Cloudflare cache 可能 hit 舊 404 → 部署後立即 purge + 等 30 秒再 curl 驗證
- **R2.6.2** sitemap.xml 部署後 GSC 索引狀態延遲 7-30 天 → Phase 2 驗收不依賴 GSC 索引完成（只驗 sitemap 內容正確），實際索引等 Phase 4 評估
- **R2.6.3** Rich Results 若報 `Service` schema 缺欄位 → 倒退到對應 plan 補 schema 必填欄位重部署

### autonomous

`partial`（Opus 親跑 deploy + verification；村長 GSC 提交 + Rich Results 截圖人工）

---

## Phase 2 整體 Success Criteria（必須全綠才能進 Phase 3）

對應 ROADMAP.md § Phase 2 4 條 + 新增驗收項：

1. [x] cannibalization 報告 ≥ 2 案例 + 處置方向 → GATE-2A 已交付（`.planning/intel/gsc-export/cannibalization-report-20260514.md`）
2. [ ] 5 個 pillar URL 全部 HTTP 200 → 由 Plan 2.1-2.6 達成
3. [ ] 每個 pillar 含 6 區塊（服務介紹 + 案例內鏈≥3 + FAQ placeholder + 相關作品 + Hero + CTA） → 由 Plan 2.1-2.5 達成
4. [ ] `/sitemap.xml` 收錄 5 條 pillar URL → 由 Plan 2.6 達成
5. [ ] 5 個 pillar Rich Results Test 全綠 → 由 Plan 2.6 達成
6. [ ] 既有 4 頁 pillar-breadcrumb 回鏈無 regression → 由 Plan 2.3 + 2.5 達成

---

## Threat Model（簡版）

| 威脅 | 嚴重度 | 緩解 |
|------|--------|------|
| Pillar 案例內鏈 `/works/{id}` 若 id 拼錯 → 404 | Med | Plan 2.0 從 PostgreSQL 撈 ID + Plan 2.6 sitemap 對照 |
| Pillar HTML 直接寫 GA4 / Clarity tracking ID → 多人 / 多裝置誤計 | Low | 從 teabar.html 既有 snippet copy，已驗證 quote/admin 不埋 |
| services.css 的 selector 與既有 site.css 衝突 | Low | services.css 用 `.pillar-*` prefix；不污染既有 .featured-grid（site.js 用的） |
| Phase 1 修補的 `_is_admin_path` 邏輯誤把 `/services/admin-event/` 之類擋掉 | Low | `_is_admin_path` 用 `startswith("/admin/")` 含尾斜線，不會誤匹配 `/services/admin-*` |
| Cannibalization §3.1/3.2 處置文案與 atelier 重複內容 | Med | wedding-tea-flower hub 明確強調「case study / portfolio」定位，與 atelier 「info」定位區隔 |
| Rich Results Test 對 OfferCatalog 雙陣列回報 warning | Low | warning 不阻塞 phase 通過；Plan 2.6 acceptance 只要 0 error |

---

## Rollback Strategy

每個 plan 部署後若 Verification 任一條 FAIL，依下列順序回滾：

### 通用流程

```powershell
# 1. revert（保留 commit 紀錄）
git log --oneline -10
git revert <commit-sha>
git push

# 2. scp 回滾後檔案到正式機（services/ 整個目錄回滾或單檔回滾）
scp -r services/ achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"

# 3. CF cache purge
pwsh scripts/cf-purge.ps1 -Paths "/sitemap.xml,/services/business-event/,/services/party-spring-banquet/,/services/magic-academy/,/services/civil-makeover/,/services/wedding-tea-flower/,/teabar.html,/wedding-packages/,/wedding-packages/outdoor.html,/sort-hat/"

# 4. 驗證恢復
curl -s -o /dev/null -w "%{http_code}\n" https://goodjob.weddingwishlove.com/services/business-event/
```

### Per-Plan 回滾要點

| Plan | 若失敗，回到 | 不影響範圍 |
|------|------------|----------|
| 2.0 | 刪 services/services.css + representatives.md | 無 pillar 上線，零影響 |
| 2.1-2.4 | git rm 對應 services/{slug}/ → sitemap 對應 URL 自然 404 | 其他 pillar / 既有頁不受影響 |
| 2.5 | git rm services/wedding-tea-flower/ + revert teabar/wedding-packages 3 個 patch | teabar / wedding-packages 既有 schema 保留（不破壞 Phase 1.3 成果） |
| 2.6 | revert server.py sitemap diff → sitemap 退回 7 條靜態頁 | 其他 plan 已上線 pillar URL 仍可 HTTP 200（直接訪問仍正常，只是 GSC 不會發現） |

### Rollback 後必做

- 開 issue 紀錄失敗原因
- 在 `02-PLAN.md` 對應 plan 加 `> ⚠️ Rolled back YYYY-MM-DD: <原因>` 段落
- 重新部署前本機跑 `python3 server.py --port 8000` 驗證

---

## Plan Index → 對應 REQ → Files Map

| Plan | REQ | services/* | server.py | 既有頁補丁 | 評估文件 |
|------|-----|-----------|-----------|----------|---------|
| 2.0 | pillar-pages-five | ✓ services.css | — | — | ✓ representatives.md |
| 2.1 | pillar-pages-five | ✓ business-event/ | — | — | — |
| 2.2 | pillar-pages-five | ✓ party-spring-banquet/ | — | — | — |
| 2.3 | pillar-pages-five | ✓ magic-academy/ | — | ✓ sort-hat/ breadcrumb | — |
| 2.4 | pillar-pages-five | ✓ civil-makeover/ | — | — | — |
| 2.5 | pillar-pages-five | ✓ wedding-tea-flower/ | — | ✓ teabar + wedding-packages × 2 | — |
| 2.6 | pillar-pages-five | — | ✓ _serve_sitemap | — | ✓ 02-RICH-RESULTS-REPORT.md |

**衝突檢測：** Plan 2.0 必先（其他 plan 都依賴 services.css 與 representatives.md）；Plan 2.1-2.5 完全並行可（不同 services/{slug}/ 目錄）；Plan 2.6 必後（驗收 phase）。建議執行順序：2.0 → (2.1 ∥ 2.2 ∥ 2.3 ∥ 2.4 ∥ 2.5) → 2.6。

---

*Phase: 02-p1a-content-cluster*
*Plan written: 2026-05-14 8:50am GMT+8*
