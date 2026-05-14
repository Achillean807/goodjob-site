# Phase 3: P1-B 作品模板擴充 + Cluster Mapping + FAQ — Context

**Gathered:** 2026-05-14
**Status:** Ready for planning
**Source:** ROADMAP.md § Phase 3 + Phase 2 SUMMARY §5 交接清單 + intel/requirements.md REQ-works-cluster-mapping / REQ-case-template-expansion / REQ-faq-per-cluster

---

<domain>
## Phase Boundary

**範疇：** 在 2-3 週內，把 Phase 2 上線的 5 個 pillar hub 從「骨架」推進到「肉」，具體交付：
1. **Cluster mapping 內鏈閉環** — PostgreSQL 62 件作品全部歸到 5 cluster；每件作品頁回鏈所屬 pillar；每個 pillar 至少 3 件代表案例（Phase 2 已硬編碼 5×3=15 件，但「相關作品列表」仍是 client-side `/api/articles` filter，本 phase 評估升級成 SSR 預渲染）
2. **作品頁 6 區塊模板擴充** — `server.py _serve_works_page` 動態 SSR 模板從現有的 `CreativeWork` JSON-LD + 圖片清單，擴充為 6 區塊：**背景 / 限制 / 策略 / 亮點 / 產業 / 成果**；先解決資料儲存模型（PostgreSQL schema 或 JSONB），再讓既有 62 件中至少 10 件補完
3. **5 cluster × 4-6 題 FAQ** — Phase 2 留下的 `<section class="pillar-faq"><!-- TODO Phase 3 -->` placeholder 全部補完答案（60-120 中文字），並包 `FAQPage` JSON-LD schema

**不在範疇：**
- Atelier 主域 outbound CTA 改造（cannibalization §6.2 #1-3） → 下波決定
- AI 引用 baseline、llms.txt 更新、robots/WAF 調整 → **Phase 4 並行**
- 答案型長文（REQ-lost-prompts-answer-content） / 比較頁（REQ-comparison-pages） → Phase 5（P2-B）
- 既有 62 件超過 10 件以外的逐一補完 → 漸進式，本 phase 只交付前 10 件 + 模板能力

**REQ 對應：**
1. `REQ-works-cluster-mapping` — 每件作品 metadata 含 cluster 標記 + 每件回鏈 pillar + 每 pillar ≥ 3 代表
2. `REQ-case-template-expansion` — 6 區塊模板 + 必填「背景／限制／策略／成果」4 項 + ≥ 10 件補完
3. `REQ-faq-per-cluster` — 5 cluster × 4-6 題 FAQ + 60-120 字答案 + FAQPage schema

**對應已 LOCKED 決策：**
- `DEC-pillar-structure-five-clusters`（Phase 2 升格 LOCKED）— 5 cluster slug 對應 PostgreSQL `category` 欄位 1:1（business / party / magic / civil），wedding-tea-flower 為 hub
- `DEC-strategy-seo-before-aeo`（Phase 2 升格 LOCKED）— Phase 3 仍屬 SEO 軌道，FAQPage schema 為 AEO 預備地基

</domain>

<decisions>
## Implementation Decisions（待 GATE-3A / 3B 確認後升 LOCKED）

### GATE-3A：作品總數基準（已交付）

- **資料來源：** GATE-1A 已實測 PostgreSQL `goodjob_site.articles` 共 **62 篇**（business 27 / party 16 / civil 14 / magic 5）
- **Phase 3 採用基準：** 62 篇全數歸入 4 個既有 cluster（wedding-tea-flower hub 不對應 articles category）
- **驗收基準：** REQ-works-cluster-mapping「每件作品 metadata 含 cluster 標記」以 PostgreSQL `category` 欄位即視為達標（既有，無需 migration）

### GATE-3B：Cluster mapping 儲存模型（待村長決策）

提案 3 個方向，**本小姐推薦方案 A（沿用 `category`）**，理由：零 migration、零 risk、與 Phase 2 LOCKED `DEC-pillar-structure-five-clusters` 1:1 對應：

| 方案 | 做法 | 優點 | 缺點 |
|------|------|------|------|
| **A（推薦）** | 沿用既有 `articles.category`（business/party/magic/civil） | 零 migration、零 risk、`/api/articles` 既有 filter 即時可用 | 一件作品只能歸一個 cluster（單一分類） |
| B | 新增 `articles.cluster` 欄位（VARCHAR），與 category 並存 | 解耦展示用 category 與 SEO cluster；未來可改 cluster 不動 category | 需要 PostgreSQL ALTER TABLE + server.py /api/articles 加欄位回傳 + admin UI 改 |
| C | 新增 `articles.clusters JSONB`（多對多） | 一件作品可屬多 cluster（例如「企業活動 + 春酒」） | 過度設計；現有 62 件無一件需要跨 cluster；增加維護成本 |

**Phase 3 預設採方案 A**，PLAN 內若村長改判 B 或 C，重排 plan 3.1。

### GATE-3C：6 區塊資料儲存（待村長決策）

PostgreSQL `articles` 表目前主要欄位：`id, title, description, category, hero_image, images[], video_id, ...`。**6 區塊新內容存哪裡？** 提案：

| 方案 | 做法 | 優點 | 缺點 |
|------|------|------|------|
| **A（推薦）** | 新增 `articles.case_blocks JSONB`（背景/限制/策略/亮點/產業/成果 6 keys） | 單欄存全部、向後相容、未填則 fallback 顯示既有 description | 需要 admin UI 加 6 個 textarea |
| B | 各區塊獨立欄位（6 個 TEXT column） | schema 結構清晰、可單獨索引查詢 | 6 個 ALTER TABLE + admin UI 改、未來改區塊需要再 migration |
| C | 走 markdown frontmatter 存在獨立 `case_studies` 表 | 完全解耦，方便多語版本 | 跨表 JOIN、過度設計 |

**Phase 3 預設採方案 A（JSONB）**，未填區塊在 `_serve_works_page` SSR 時 fallback 顯示既有 description。

### GATE-3D：FAQ 內容儲存（待村長決策）

| 方案 | 做法 | 優點 | 缺點 |
|------|------|------|------|
| **A（推薦）** | FAQ 寫在 5 個 pillar `index.html` 內（硬編碼 + 同檔 FAQPage JSON-LD） | 零 migration、與 Phase 2 placeholder 同檔即補、即可上線 | 改 FAQ 要改 HTML（但 FAQ 改動頻率低） |
| B | 新增 `cluster_faqs` PostgreSQL 表，server.py 加端點 | 後台可改、未來 admin UI 整合 | 跨檔追蹤、需要 server.py routing 改、本 phase 範疇外 |
| C | 寫在 `data/faqs.json`，pillar HTML 抓 | 介於 A/B 之間 | 引入新檔案、git-track 與否要決定 |

**Phase 3 預設採方案 A（硬編碼 HTML）**，5 pillar × 4-6 題 = 20-30 題 FAQ，內容由村長提供或本小姐草擬村長 review。

### Rendering（內鏈與 SSR 邊界）

- **LOCKED（沿用 Phase 2）** Pillar 頁靜態 HTML + `<section class="pillar-related">` client-side fetch `/api/articles` filter；本 phase 不改為 SSR（評估成本過高，待 Phase 5+ 視 indexing 成效再評）
- **NEW** 作品個別頁 `/works/{id}` 走 server.py `_serve_works_page` SSR（既有），擴充 6 區塊渲染邏輯：讀 `articles.case_blocks` JSONB，渲染 6 個 `<section>`，含結構化資料 schema（建議用 `CreativeWork` 既有 + 自訂 properties，或補 `Article` schema）
- **NEW** 作品頁底部加「← 返回 pillar」CTA 連回所屬 cluster pillar（依 `category` 對應 `/services/{slug}/`）
- **NEW** 作品頁 `<head>` 加 `<link rel="up" href="/services/{slug}/">` 信號 + breadcrumb schema 補 pillar 層級

### FAQ Schema 規格

- 每個 pillar `<section class="pillar-faq">` 內：4-6 個 `<details>` / `<dl>` 結構（人類可讀）
- 同檔同步 `<script type="application/ld+json">` 帶 `FAQPage`：
  ```json
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "問題文字",
        "acceptedAnswer": { "@type": "Answer", "text": "60-120 字答案" }
      }
    ]
  }
  ```
- 5 pillar 合計 5 個 FAQPage schema，需通過 Google Rich Results Test 0 error

</decisions>

<canonical_refs>
## Canonical References

### Phase 2 既有交付（基礎）

| 檔案 | 角色 |
|------|------|
| `services/business-event/index.html` | 27 件 business 作品 hub（含 FAQ placeholder） |
| `services/party-spring-banquet/index.html` | 16 件 party hub（FAQ placeholder） |
| `services/magic-academy/index.html` | 5 件 magic hub + sort-hat 入口（FAQ placeholder） |
| `services/civil-makeover/index.html` | 14 件 civil hub（FAQ placeholder） |
| `services/wedding-tea-flower/index.html` | 婚禮花果茶 hub（FAQ placeholder） |
| `services/services.css` | 5 pillar 共用樣式 |

### server.py 既有 SSR

- `_serve_works_page` (L1651-) — `/works/{id}` 動態 SSR，目前輸出 hero + description + 圖片清單 + `CreativeWork` JSON-LD
- `_serve_sitemap` (L1800-) — 動態 sitemap，已含 5 pillar URL（Phase 2 Plan 2.7.4 補完）

### 資料源

- PostgreSQL `goodjob_site.articles` 表（62 篇，`category` 欄位已對齊 5 pillar slug 中的前 4 個）
- `/api/articles` REST 端點（既有，無需改）

### 對應 ROADMAP 條目

- ROADMAP § Phase 3「P1-B 作品模板與 FAQ」
- ROADMAP success criteria（5 條）：
  1. 每件作品含 cluster 標記
  2. 每件作品內鏈所屬 pillar
  3. 每 pillar ≥ 3 件代表作品
  4. ≥ 10 件作品補完 6 區塊
  5. 5 cluster × 4-6 FAQ + FAQPage schema 全部通過 Rich Results Test

</canonical_refs>

<specifics>
## Specifics

### Plan 切割建議（PLAN.md 細寫）

| Plan | 主題 | 主要動作 | 預估時數 |
|------|------|---------|---------|
| 3.0 | GATE 決策對齊 | 跑 GATE-3B/3C/3D 三選擇向村長確認，鎖定儲存模型 | 30 min |
| 3.1 | PostgreSQL schema 擴充 | `ALTER TABLE articles ADD COLUMN case_blocks JSONB DEFAULT '{}'`（若選 A）+ admin 後台補 6 個 textarea | 2-3h |
| 3.2 | server.py `_serve_works_page` SSR 6 區塊渲染 | 讀 case_blocks JSONB，render 6 sections + breadcrumb pillar 層級 + 返回 pillar CTA | 3-4h |
| 3.3 | 5 pillar FAQ 內容撰寫（每 cluster 4-6 題） | 村長提供題目素材 / 本小姐草擬 / 村長 review；寫進 5 pillar HTML | 4-6h（依村長 review 節奏） |
| 3.4 | 5 pillar FAQPage JSON-LD schema 包覆 | 把 FAQ section 對應 JSON 寫進 `<script type="application/ld+json">` | 1h |
| 3.5 | 既有 10 件作品補完 6 區塊內容（村長選代表作品） | admin 後台輸入 / 直接 SQL UPDATE 都行；村長提供文案或本小姐萃取既有 description 補完 | 6-10h |
| 3.6 | 作品頁回鏈 pillar + breadcrumb schema | `_serve_works_page` 模板再擴充：自動依 `category` 映射 `/services/{slug}/` 補 breadcrumb + 返回 CTA | 1-2h |
| 3.7 | 部署 + Rich Results Test + Production smoke test | scp → systemctl restart → 跑 5 pillar + 10 件作品 URL 過 Rich Results Test | 2-3h |

### Success Criteria 驗收清單

1. **每件作品含 cluster 標記** → SELECT COUNT(*) FROM articles WHERE category IS NULL = 0
2. **每件作品內鏈 pillar** → curl `/works/{id}` 含 `<a href="/services/{slug}/">` 至少 1 個（自動依 category 映射）
3. **每 pillar ≥ 3 件代表** → 5 pillar HTML grep 三個硬編碼 `case-card`（Phase 2 已達成，本 phase 維持）
4. **≥ 10 件作品補完 6 區塊** → SELECT COUNT(*) FROM articles WHERE case_blocks ?& array['background','constraint','strategy','outcome'] >= 10
5. **5 FAQPage schema 通過 Rich Results Test** → 手動跑 5 個 pillar URL；0 error / 0 critical warning

### 量化指標目標

| 指標 | Phase 2 結束 | Phase 3 結束目標 |
|------|--------------|-----------------|
| 作品頁含 cluster 內鏈 | 0/62 | **62/62**（依 category 自動映射） |
| 作品頁 6 區塊補完 | 0/62 | **≥ 10/62** |
| pillar FAQ 題目數 | 0（全 placeholder） | **20-30 題** |
| FAQPage JSON-LD schema | 0 | **5** |
| Pillar 頁 schema 總數 | 11（5 Service + 5 Breadcrumb + 1 OfferCatalog） | **16**（+5 FAQPage） |

### 預估時程

- **總工時：** 20-30h（含 Plan 3.5 文案輸入大頭）
- **Calendar 預估：** 2-3 週（Phase 4 並行不會搶 server.py / PostgreSQL，只動 robots.txt / llms.txt / 外部 prompt 測試）
- **GATE-3B/3C/3D 對齊：** 預計 Phase 3 開工前 30 min 內三選一鎖定（本小姐推薦組合：A + A + A）

</specifics>

<deferred>
## Deferred to Later Phases

| 項目 | 推遲到 | 原因 |
|------|--------|------|
| 既有 62 件超出 10 件以外的逐一補完 | 漸進補完（Phase 5+ 或日常運營） | 量太大，本 phase 先交付模板能力 + 前 10 件 |
| Atelier 主域 outbound CTA | Phase 5 或獨立任務 | cannibalization §6.2 處置方向，與本 phase 解耦 |
| `pillar-related` SSR 預渲染（取代 client-side fetch） | Phase 5 視 indexing 成效再評 | 現有 client-side filter 對 Google 已 OK；改 SSR 需 server.py 大幅改寫 |
| FAQ 後台管理 UI | Phase 5+ | 本 phase FAQ 採硬編碼 HTML，村長手動改頻率低 |
| 答案型長文（lost prompts 修補） | Phase 5（P2-B） | 依賴 Phase 4 baseline 結果 |
| 比較頁 / 決策框架 | Phase 5（P2-B） | 依賴 Phase 4 baseline 結果 |

</deferred>

---

*Phase: 03-p1b-works-faq*
*Context written: 2026-05-14 21:39 GMT+8（compaction 後恢復進度）*
