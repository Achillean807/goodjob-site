# Phase 2: P1-A 內容集群骨架建立 — Context

**Gathered:** 2026-05-14
**Status:** Ready for planning
**Source:** ROADMAP.md § Phase 2 + cannibalization-report-20260514.md §6.1 + GATE-2B 三項決策（村長 2026-05-14 8:40am confirm）

---

<domain>
## Phase Boundary

**範疇：** 在 2-3 週內上線 5 個 pillar hub 頁，建立服務主題集群的 URL 骨架（4 個全新 `/services/*/` + 1 個既有 `/wedding-packages/` 升格 pillar 但保留現有路徑），讓 GSC 看得到完整的 site structure，並依 cannibalization 處置方向把 atelier 搶不到的 4 個純藍海主題與 1 個 cannibalization 處置主題各自有獨立 hub 收斂作品內鏈與 FAQ placeholder。

**不在範疇：**
- 作品個別頁的 6 區塊模板擴充 → Phase 3
- FAQ schema 完整 5 cluster 內容（本 phase 只放 placeholder） → Phase 3
- PostgreSQL `articles` 表新增 `cluster` 欄位 migration → Phase 3
- atelier 主域的 outbound CTA 加裝（cannibalization §6.2 第 1-3 點） → Phase 3
- AI bot allowlist robots.txt、llms.txt 更新、AI citation baseline → Phase 4
- 作品個別頁路徑改造（`/works/{id}` 路徑不動，仍由 server.py SSR 動態生成）

**REQ 對應：**
1. `REQ-gsc-query-export` — ✅ 已於 GATE-2A 完成（domain-all-6mo-20260514 CSVs + cannibalization-report-20260514.md），本 phase 不再執行
2. `REQ-pillar-pages-five` — 5 個 pillar URL HTTP 200，含服務介紹、代表案例內鏈 ≥ 3、FAQ placeholder、相關作品列表，且 sitemap 收錄

**對應方向性決策（本 phase 升格 LOCKED）：**
- `DEC-pillar-structure-five-clusters` (proposed → locked)
- `DEC-strategy-seo-before-aeo` (proposed → locked)

</domain>

<decisions>
## Implementation Decisions

### URL Namespace（GATE-2B 決策 #1）

- **LOCKED** 4 個新 pillar 一律使用 `/services/{slug}/` 命名空間（村長 2026-05-14 confirm）
- **LOCKED** Pillar slug 對應作品 `category` 欄位（保留人類可讀性，便於後續 cluster mapping）：

  | Pillar Slug | Cluster 主題 | 對應作品 | 競爭定位 |
  |-------------|------------|----------|---------|
  | `business-event` | 主題化品牌活動 | 27 件 `category="business"` | 純藍海（atelier top 1000 完全沒搶到「主題場景」「主題佈置」） |
  | `party-spring-banquet` | 春酒尾牙派對 | 16 件 `category="party"` | 純藍海 |
  | `magic-academy` | 魔法學院 IP | 5 件 `category="magic"` + `/sort-hat/` | 純藍海 |
  | `civil-makeover` | 戶政空間改造 | 14 件 `category="civil"`（含 zhongshan-civil） | 純藍海 |
  | `wedding-tea-flower` | 婚禮花果茶 + 場景佈置 hub | 既有 `/teabar.html` + 既有 `/wedding-packages/*` | cannibalization 處置 3.1（迎賓茶 CRITICAL）、3.2（囍茶 CRITICAL） |

- **LOCKED** 4 個藍海 pillar 為**全新 HTML 檔**（`/services/business-event/index.html`、`/services/party-spring-banquet/index.html`、`/services/magic-academy/index.html`、`/services/civil-makeover/index.html`）
- **LOCKED** 第 5 個 pillar `wedding-tea-flower` 為**全新 hub 頁** `/services/wedding-tea-flower/index.html`，串接既有 `/teabar.html` 與 `/wedding-packages/`（不破壞既有 URL 結構）
- **LOCKED** `/services/{slug}/` 不在 server.py 既有 routing handler（已驗證 do_GET L1575 / _serve_works_page L1651 / _serve_sitemap L1800 範圍無衝突），靜態檔自然由 `super().do_GET()` 提供

### Rendering（GATE-2B 決策 #2）

- **LOCKED** Pillar 頁一律**靜態 HTML**（村長 2026-05-14 confirm）
- **LOCKED** 跟 `teabar.html` / `workflow.html` / `wedding-packages/index.html` 同 pattern：完整 head + 服務介紹 hero + 案例 grid（透過 `<script>` 在 client-side fetch `/api/articles?category={slug}` 渲染）+ FAQ placeholder + Breadcrumb + JSON-LD schema
- **LOCKED** Server-side 不改 do_GET 路由，server.py 修改僅限 `_serve_sitemap`（補 5 條 URL）
- **NEW** 案例 grid 用 `fetch('/api/articles')` + 前端 filter `a.category === slug` 渲染（既有 `/api/articles` 端點已支援，無需後端改動）；若 JS 失效，hero + FAQ + 已硬編碼的 3 件代表作品 anchor 仍可見（fallback）

### Cluster Mapping（GATE-2B 決策 #3）

- **LOCKED** 採用 cannibalization-report-20260514.md §6.1 五大 pillar 架構，僅將 `/pillar/` 命名空間替換為 `/services/`：

  ```
  goodjob.weddingwishlove.com
  ├── /services/business-event/          ← 27 件 business 作品（純藍海）
  ├── /services/party-spring-banquet/    ← 16 件 party 作品（純藍海）
  ├── /services/magic-academy/           ← 5 件 magic + /sort-hat/ 串接（純藍海）
  ├── /services/civil-makeover/          ← 14 件 civil 作品（純藍海）
  └── /services/wedding-tea-flower/      ← 婚禮花果茶 hub（cannibalization 處置）
      ├── (向下串) /teabar.html           ← 既有，不動
      └── (向下串) /wedding-packages/*    ← 既有 4 套組，不動
  ```

- **LOCKED** Cluster 與 PostgreSQL `category` 欄位 1:1 對應：`business` / `party` / `magic` / `civil` 直接對應前 4 個 pillar slug；`wedding-tea-flower` 為 hub 概念，不對應單一 category，而是串既有 `/teabar.html` + `/wedding-packages/*`（這些頁面不持有 articles `category`）

### 內容骨架（每個 pillar 共通結構）

每個 pillar `/services/{slug}/index.html` 必含 6 區塊（對應 ROADMAP Success Criteria）：

1. **Hero 區** — pillar 主題定位句（30-50 字）+ 主視覺圖
2. **服務介紹** — 200-400 字描述 pillar 涵蓋的服務範疇、適用場景、執行方式
3. **代表案例內鏈** — **≥ 3 件**（從該 cluster 作品中挑 hero 圖最完整、`featured=true` 優先），每件含 `<a href="/works/{id}">` + 縮圖 + 標題；JS 失效時這 3 件硬編碼仍可見
4. **相關作品列表** — 用 `fetch('/api/articles')` 渲染該 cluster 全部作品（client-side），含分類過濾邏輯
5. **FAQ placeholder** — Phase 3 才填內容，本 phase 先放空 `<section id="faq">` + 註解標記 `<!-- TODO Phase 3: FAQ × 5 -->`
6. **Cross-link CTA** — pillar 底部加「想看完整合作流程」→ `/workflow.html`、「囍茶方案」→ `/teabar.html`（限 wedding-tea-flower）等戰略 cross-link

### Schema 要求（每個 pillar 頁）

- **LOCKED** `Service` schema（serviceType / name / description / provider / areaServed / hasOfferCatalog itemListElement 3 件代表作品）
- **LOCKED** `BreadcrumbList` schema（村山良作 → {pillar 中文名}）
- **LOCKED** `FAQPage` placeholder schema（空 mainEntity 陣列，Phase 3 填，**但本 phase 不放 schema**避免 Rich Results Test 報 empty mainEntity error；放 HTML 註解 placeholder 標記位置即可）
- **LOCKED** 每頁 `<link rel="canonical">` 指自身 `/services/{slug}/`
- **LOCKED** 完整 OG + Twitter card（title / description / image / url / image:alt）
- **LOCKED** description 70-110 中文字（同 Phase 1 支援頁規格）

### Wedding-tea-flower Pillar 特殊處理

- **LOCKED** `/services/wedding-tea-flower/index.html` 為**新建 hub 頁**，不替換或破壞既有 `/teabar.html` 與 `/wedding-packages/` 結構
- **LOCKED** Hub 內容以「婚禮花果茶 + 婚禮場景佈置」雙主題整合呈現，明確 cross-link 到既有 `/teabar.html`（迎賓茶詳細方案）與 `/wedding-packages/` + `/wedding-packages/outdoor.html`（場景套組）
- **LOCKED** 既有 `/teabar.html`、`/wedding-packages/index.html`、`/wedding-packages/outdoor.html` 三頁加上對應 hub cross-link「回到婚禮花果茶 pillar」，形成內鏈閉環
- **LOCKED** Hub 頁不執行作品 fetch（沒對應 articles category），但展示 teabar 3 款茶飲圖卡 + wedding-packages 4 套組圖卡作為 OfferCatalog 子項目

### Sitemap 收錄

- **LOCKED** `server.py:_serve_sitemap` 補入 5 條 pillar URL：`/services/business-event/`、`/services/party-spring-banquet/`、`/services/magic-academy/`、`/services/civil-makeover/`、`/services/wedding-tea-flower/`
- **LOCKED** 既有 7 條靜態頁 + 62 條 `/works/{id}` 不動
- **NEW** 預期部署後 sitemap `<loc>` 數量從 69 升至 **74**（62 + 7 + 5）

### Claude's Discretion

- Pillar Hero 圖：可從既有作品 hero 中挑代表性最強的（business 用 `zhongshan-civil` 或 `taipei-101-spring`、party 用某春酒主視覺、magic 用魔法學院主場景、civil 用戶政改造前後對比、wedding-tea-flower 用 teabar/brand-event.jpg）
- CSS：可全部 inline 在 pillar HTML 的 `<style>` block 內（避免污染 site.css），或加 `<link rel="stylesheet" href="/services/services.css?v=20260514">` 統一樣式（傾向後者，乾淨）
- `fetch('/api/articles')` filter 邏輯可寫在每個 pillar 的 inline `<script>` 內（client-side）或抽到 `/services/services.js`（傾向 inline，避免額外 HTTP request）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 主輸入文件
- `.planning/intel/gsc-export/cannibalization-report-20260514.md` — GATE-2A 產出，§6.1 五大 pillar 架構、§6.2 cross-link 策略、§6.3 atelier 避戰列表
- `.planning/intel/gsc-export/domain-all-6mo-20260514/` — 7 個 CSV 原始資料（查詢、網頁、裝置、國家、搜尋外觀、圖表、篩選器）
- `.planning/REQUIREMENTS.md` — REQ-pillar-pages-five 完整驗收條件
- `.planning/ROADMAP.md` § Phase 2 — 4 條 Success Criteria + GATE-2A/B/C
- `.planning/intel/decisions.md` — DEC-pillar-structure-five-clusters / DEC-strategy-seo-before-aeo
- `.planning/STATE.md` — Phase 1 完成狀態、62 篇作品分類分布

### Codebase 關鍵檔
- `CLAUDE.md` — 部署細節、API 端點清單、systemd 服務、R2 CDN 邏輯
- `server.py:1800-` — `_serve_sitemap` 動態 sitemap 生成（**本 phase 需擴充**）
- `server.py:1605-` — `_serve_homepage_ssr` SSR 注入 pattern（pillar 用不到，但格式可參考）
- `server.py:1651-` — `_serve_works_page` 作品頁動態 SSR（pillar 不走，僅參考）
- `server.py:do_GET` — 路由優先序確認 `/services/*/` 落入 `super().do_GET()` 靜態檔 fallback
- `teabar.html` — 既有支援頁 metadata + schema 範本（Phase 1.3 已補完整）
- `workflow.html` — 既有支援頁範本（Phase 1.4 驗收已通過）
- `wedding-packages/index.html` / `wedding-packages/outdoor.html` — 套組頁範本（Phase 1.3 已補完整）
- `sort-hat/index.html` — 互動工具頁範本（Phase 1.3 已補完整）
- `index.html` L1-135 — 首頁 head metadata + JSON-LD schema 範本
- `assets/site.css` — 共用樣式（pillar 可參考 color tokens）
- `/api/articles` 端點 — server.py 既有實作，回傳全部 62 篇（含 `category` 欄位），pillar client-side filter 即可

### 外部規範
- Google Rich Results Test：https://search.google.com/test/rich-results
- Schema.org Service：https://schema.org/Service
- Schema.org OfferCatalog：https://schema.org/OfferCatalog
- Schema.org BreadcrumbList：https://schema.org/BreadcrumbList

### 部署與環境
- `docs/村山良作-部署資訊清單.md` — 正式環境結構、PostgreSQL 設定
- Cloudflare API 憑證 `~/.claude/.cf-env` — purge cache 用
- `scripts/cf-purge.ps1` — Phase 1.1 產出的 purge 腳本（本 phase 直接使用）

</canonical_refs>

<specifics>
## Specific Ideas

### Pillar HTML 骨架模板（可複製給 4 個藍海 pillar）

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{Pillar 中文名}｜村山良作 MURAYAMA GOODJOB</title>
  <meta name="description" content="{70-110 中文字描述 pillar 涵蓋的服務範疇與適用場景}" />
  <link rel="canonical" href="https://goodjob.weddingwishlove.com/services/{slug}/" />

  <!-- OG / Twitter（同 Phase 1.3 規格）-->
  <meta property="og:type" content="website" />
  <meta property="og:title" content="..." />
  <meta property="og:description" content="..." />
  <meta property="og:image" content="https://goodjob-img.weddingwishlove.com/services/{slug}/og.jpg" />
  <meta property="og:url" content="https://goodjob.weddingwishlove.com/services/{slug}/" />
  <meta property="og:site_name" content="村山良作 MURAYAMA GOODJOB" />
  <meta property="og:locale" content="zh_TW" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="..." />
  <meta name="twitter:description" content="..." />
  <meta name="twitter:image" content="https://goodjob-img.weddingwishlove.com/services/{slug}/og.jpg" />

  <!-- Service schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Service",
    "serviceType": "{中文服務類型}",
    "name": "{pillar 名}",
    "description": "{70-110 字描述}",
    "provider": { "@type": "Organization", "name": "村山良作 MURAYAMA GOODJOB", "url": "https://goodjob.weddingwishlove.com/" },
    "areaServed": { "@type": "Country", "name": "台灣" },
    "url": "https://goodjob.weddingwishlove.com/services/{slug}/",
    "hasOfferCatalog": {
      "@type": "OfferCatalog",
      "name": "{pillar 名}代表案例",
      "itemListElement": [
        { "@type": "Offer", "itemOffered": { "@type": "CreativeWork", "name": "{案例 1 標題}", "url": "https://goodjob.weddingwishlove.com/works/{id1}" } },
        { "@type": "Offer", "itemOffered": { "@type": "CreativeWork", "name": "{案例 2 標題}", "url": "https://goodjob.weddingwishlove.com/works/{id2}" } },
        { "@type": "Offer", "itemOffered": { "@type": "CreativeWork", "name": "{案例 3 標題}", "url": "https://goodjob.weddingwishlove.com/works/{id3}" } }
      ]
    }
  }
  </script>

  <!-- Breadcrumb -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "村山良作", "item": "https://goodjob.weddingwishlove.com/" },
      { "@type": "ListItem", "position": 2, "name": "{pillar 中文名}", "item": "https://goodjob.weddingwishlove.com/services/{slug}/" }
    ]
  }
  </script>

  <link rel="stylesheet" href="/services/services.css?v=20260514" />
  <!-- GA4 + Clarity（Phase 1.6 既有片段，從 teabar.html copy）-->
</head>
<body>
  <header><!-- nav copy from teabar.html --></header>
  <main>
    <section class="pillar-hero">
      <h1>{Pillar 中文名}</h1>
      <p class="hero-tagline">{30-50 字定位句}</p>
    </section>

    <section class="pillar-intro">
      <h2>關於這項服務</h2>
      <p>{200-400 字服務介紹}</p>
    </section>

    <section class="pillar-featured">
      <h2>代表案例</h2>
      <div class="featured-grid">
        <!-- 3 件硬編碼（fallback，JS 失效也可見）-->
        <a class="case-card" href="/works/{id1}">
          <img src="{hero}" alt="{title}" loading="lazy" />
          <h3>{title}</h3>
        </a>
        <!-- × 3 -->
      </div>
    </section>

    <section class="pillar-related" id="related-works">
      <h2>其他{pillar 中文名}作品</h2>
      <div class="related-grid" data-category="{slug}">
        <!-- JS 渲染 -->
      </div>
    </section>

    <section class="pillar-faq" id="faq">
      <h2>常見問題</h2>
      <!-- TODO Phase 3: FAQ × 5 + FAQPage schema -->
    </section>

    <section class="pillar-cta">
      <h2>下一步</h2>
      <a href="/workflow.html">看合作流程</a>
      <!-- wedding-tea-flower 額外加 teabar / wedding-packages 連結 -->
    </section>
  </main>
  <footer><!-- copy from teabar.html --></footer>

  <script>
    (function () {
      'use strict';
      var slug = '{slug}';
      fetch('/api/articles')
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var arts = (data.articles || []).filter(function (a) { return a.category === slug; });
          var grid = document.querySelector('.related-grid[data-category="' + slug + '"]');
          if (!grid) return;
          arts.forEach(function (a) {
            var card = document.createElement('a');
            card.className = 'case-card';
            card.href = '/works/' + a.id;
            card.innerHTML = '<img src="' + a.heroImage + '" alt="' + a.title + '" loading="lazy"/><h3>' + a.title + '</h3>';
            grid.appendChild(card);
          });
        })
        .catch(function () { /* fallback to hardcoded 3 cards */ });
    })();
  </script>
</body>
</html>
```

### Wedding-tea-flower Hub 特殊版本

去掉 `pillar-related` 區塊（無對應 category）、`pillar-featured` 改為「茶飲方案 + 場景套組」雙欄展示：

```html
<section class="pillar-featured">
  <h2>婚禮花果茶</h2>
  <div class="featured-grid">
    <a class="case-card" href="/teabar.html#brand-event">
      <img src="https://goodjob-img.weddingwishlove.com/teabar/brand-event-card.jpg" alt="六月青果" loading="lazy" />
      <h3>六月青果</h3>
    </a>
    <!-- × 3（teabar 3 款茶飲）-->
  </div>
  <a class="cta-link" href="/teabar.html">看完整茶飲方案</a>
</section>

<section class="pillar-featured">
  <h2>婚禮場景套組</h2>
  <div class="featured-grid">
    <a class="case-card" href="/wedding-packages/#classic">
      <img src="https://goodjob.weddingwishlove.com/wedding-packages/images/classic/hero.jpg" alt="經典套組" loading="lazy" />
      <h3>經典送客背景</h3>
    </a>
    <!-- × 4（wedding-packages 4 套組）-->
  </div>
  <a class="cta-link" href="/wedding-packages/">看完整場景套組</a>
  <a class="cta-link" href="/wedding-packages/outdoor.html">看戶外證婚套組</a>
</section>
```

### 既有頁面回鏈 Hub 補丁

加在 `/teabar.html`、`/wedding-packages/index.html`、`/wedding-packages/outdoor.html` 三頁的 hero 上方或 footer 上方：

```html
<nav class="pillar-breadcrumb">
  <a href="/services/wedding-tea-flower/">← 回到婚禮花果茶 pillar</a>
</nav>
```

同步在 `/sort-hat/index.html` 加：
```html
<nav class="pillar-breadcrumb">
  <a href="/services/magic-academy/">← 回到魔法學院 pillar</a>
</nav>
```

### Sitemap 擴充

`server.py:_serve_sitemap` 的靜態 URL list 從 7 條擴到 12 條：

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

預期部署後：`curl -s https://.../sitemap.xml | grep -c '<loc>'` = **74**（62 works + 12 static）

### Pillar 代表案例選定（依 `featured=true ORDER BY featured_order` + 視覺完整度）

實作前先跑：
```bash
ssh achilean@100.102.51.64 'psql -d goodjob_site -t -c "SELECT id, title, category, featured_order FROM articles WHERE category IN ('business','party','magic','civil') AND featured = 1 ORDER BY category, featured_order, row_index;"'
```

從結果依每 category 取 featured 前 3 件作為硬編碼代表案例（fallback 用）。

### Cloudflare Purge

部署後：
```powershell
pwsh scripts/cf-purge.ps1 -Paths "/sitemap.xml,/services/business-event/,/services/party-spring-banquet/,/services/magic-academy/,/services/civil-makeover/,/services/wedding-tea-flower/,/teabar.html,/wedding-packages/,/wedding-packages/outdoor.html,/sort-hat/"
```

</specifics>

<deferred>
## Deferred Ideas

明確排除在 Phase 2 之外、留給後續 phase：

- **作品 6 區塊模板擴充**（hero / context / process / outcome / specs / next case） → Phase 3（REQ-case-template-expansion）
- **FAQPage schema 完整 5 cluster 內容**（每 pillar 5 題答案 60-120 字） → Phase 3（REQ-faq-per-cluster）
- **PostgreSQL `articles` 表 `cluster` 欄位 migration** → Phase 3（GATE-3B）
- **atelier 主域 outbound CTA 加裝**（cannibalization §6.2 第 1-3 點：迎賓茶 / 囍茶 / 婚禮佈置文章底部加 goodjob CTA） → Phase 3
- **AI bot allowlist robots.txt 擴充**（OAI-SearchBot / PerplexityBot / ClaudeBot） → Phase 4（REQ-robots-waf-bot-allow）
- **llms.txt 更新**（補 5 個 pillar URL + cluster 對應） → Phase 4（REQ-llms-txt-update）
- **AI citation baseline 測試**（ChatGPT / Perplexity / Claude / Gemini × 8 query × 月） → Phase 4
- **Cloudflare WAF AI bot allowlist audit** → Phase 4 GATE-4C
- **Pillar 頁 hero 圖客製攝影 / 設計圖**（本 phase 直接用既有作品 hero） → 暫不排程，視 GSC 表現決定

</deferred>

---

*Phase: 02-p1a-content-cluster*
*Context gathered: 2026-05-14 8:50am GMT+8 via GATE-2A 報告整合 + GATE-2B 三項村長決策*
