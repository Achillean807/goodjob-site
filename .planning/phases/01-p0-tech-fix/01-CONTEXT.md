# Phase 1: P0 技術修補 — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Source:** PRD Express Path（`docs/seo-aeo-improvement-plan-20260513.html`）+ codebase baseline 探查

---

<domain>
## Phase Boundary

**範疇：** 在 7-14 天內完成 5 個索引安全與技術基礎修補項目，讓 Google 與 AI crawler 都能正確抓取公開頁、正確排除私有頁（admin / quote），並建立 SSR fallback 讓非 JS crawler 看到精選作品。

**不在範疇：**
- Phase 2 才建立的 `/services/*` pillar 頁
- Phase 3 才做的作品 6 區塊模板擴充
- AI baseline 測試（Phase 4）

**REQ 對應：**
1. `REQ-prod-sitemap-verify` — sitemap URL 數 ≥ 62
2. `REQ-admin-noindex` — X-Robots-Tag header + robots.txt disallow
3. `REQ-support-pages-metadata` — 4 個支援頁補齊 metadata + schema
4. `REQ-rich-results-validation` — 8 個 URL Rich Results Test 全綠
5. `REQ-homepage-server-rendered-cases` — 首頁不執行 JS 也看得到 ≥ 3 件精選作品

</domain>

<decisions>
## Implementation Decisions

### Sitemap（REQ-prod-sitemap-verify）

- **LOCKED** sitemap 維持動態端點 `/sitemap.xml` 由 `server.py:_serve_sitemap` 生成（已實作於 L1699-1723），不退回靜態檔
- **LOCKED** sitemap 資料源 = `_load_articles()` → PostgreSQL（GATE-1A 解果：62 篇）
- **LOCKED** sitemap 收錄項目：所有 `/works/{id}` 動態頁 + 既有靜態頁（首頁、teabar、workflow、wedding-packages、wedding-packages/outdoor）
- **NEW** 補收錄：`/sort-hat/`、`/muse-2026.html`（hero 引用頁面）
- **DEFERRED** Phase 2 才加 `/services/*` pillar 5 個 URL（本 phase 不動）
- **NEW** Cloudflare CDN cache purge：本 phase 部署後立即執行 `POST /zones/{zoneId}/purge_cache` 對 `/sitemap.xml` 與 `/robots.txt` 各 purge 一次

### Admin Noindex（REQ-admin-noindex）

- **LOCKED** 三層保護策略（DEC-private-pages-noindex-policy proposed → 本 phase 升格 locked）：
  1. HTTP response header `X-Robots-Tag: noindex, nofollow, noarchive`
  2. `robots.txt` 加 `Disallow: /admin/`
  3. （已存在）admin 頁 Basic Auth 阻擋未登入存取
- **CODEBASE BUG 必修** `server.py:_is_admin_page()`（L935-938）只匹配 `/admin` 與 `/admin/`，**未涵蓋 `/admin/index.html`、`/admin/app.js` 等子路徑**；同時 `end_headers()`（L953）目前只對 `quote` 路徑加 X-Robots-Tag，**完全沒對 admin 加**。兩處都要修。
- **LOCKED** 同步用既有 `_is_quote_path` 樣式新增 `_is_admin_path`（更廣的判斷），覆蓋所有 `/admin*` 子路徑
- **NEW** 為一致性順便對 `/admin*` 加上 `Cache-Control: private, no-store` 防止公共 cache 緩存

### Support Pages Metadata（REQ-support-pages-metadata）

支援頁基線：

| 頁面 | description | canonical | OG/Twitter | schema |
|------|------------|-----------|-----------|--------|
| `/sort-hat/` | ✓ 短描述 | ✗ | ✗ | ✗ |
| `/teabar.html` | ✓ 完整 | ✓ | ✓ | ✗ |
| `/wedding-packages/` | ✗ | ✗ | ✗ | ✗ |
| `/wedding-packages/outdoor.html` | ✗ | ✗ | ✗ | ✗ |

- **LOCKED** 每頁 `<meta name="description">` 70-110 中文字（同時統一首頁從 30 字 → 80-100 字，作為 REQ-homepage 一併處理）
- **LOCKED** 每頁 canonical 指向自身 production URL（不可指首頁）
- **LOCKED** 每頁完整 OG + Twitter card（title / description / image / url / image:alt）
- **LOCKED** schema 對應：
  - `sort-hat`：`WebApplication` 或 `Service`（互動工具）+ `BreadcrumbList`
  - `teabar`：`Product` + `Offer` + `FAQPage`（保留既有 4 題或新加）+ `BreadcrumbList`
  - `wedding-packages/` + `outdoor.html`：`Service` + `Offer` × N 套組 + `BreadcrumbList`

### Rich Results Validation（REQ-rich-results-validation）

- **LOCKED** 驗收 8 個 URL：首頁、`/workflow.html`、`/muse-2026.html` + 5 個代表作品頁（從 PostgreSQL 取 `featured=true` 前 5 件依 `featuredOrder`）
- **LOCKED** 驗收方式：用 Google Rich Results Test（`https://search.google.com/test/rich-results`）人工驗證每個 URL，截圖 0 error 為通過
- **LOCKED** schema 中 `name` / `description` / `image` 三個欄位的文字必須出現於頁面可見文字（Google 規則）

### Homepage Server-Rendered Cases（REQ-homepage-server-rendered-cases）

- **LOCKED** 改造 `index.html` serving：`server.py` 在回 `/` 時 inject SSR `<section id="featured-cases">`，內含 ≥ 3 件精選作品（從 PostgreSQL `WHERE featured = true ORDER BY featuredOrder LIMIT 6`）的標題、縮圖、`/works/{id}` 內鏈
- **LOCKED** 不破壞既有 SPA 行為：SSR 區塊位於 `#works` 上方或作為其初始 HTML，site.js 渲染時可保留或覆蓋；JS 失效時這段仍可見
- **LOCKED** 首頁 description 從現有 30 字（"村山良作——把品牌活動、主題場景與展場空間，做成真的現場。"）擴充到 70-110 字（同支援頁規格）

### Claude's Discretion

- SSR 注入機制：可選 (A) Python `_serve_homepage` 自定義 handler 讀 index.html 模板 + 注入 placeholder，(B) `string.Template` 替換 `{{FEATURED_CASES}}` 標記。本小姐傾向 (B) 更乾淨。
- Cloudflare purge 寫成 deploy 腳本 step 還是手動指令 — 本小姐傾向寫進 `scripts/deploy.ps1` 或新建 `scripts/cf-purge.ps1`
- Rich Results 驗證的截圖存放：`.planning/phases/01-p0-tech-fix/evidence/`（git-ignored）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### PRD 與 ingest 產出
- `docs/seo-aeo-improvement-plan-20260513.html` — 原 PRD（§ 三 P0 優先級改善計畫）
- `.planning/REQUIREMENTS.md` — REQ-prod-sitemap-verify、REQ-admin-noindex、REQ-support-pages-metadata、REQ-rich-results-validation、REQ-homepage-server-rendered-cases 完整驗收條件
- `.planning/ROADMAP.md` § Phase 1 — 5 條 Success Criteria + GATE-1A/B
- `.planning/intel/decisions.md` — DEC-private-pages-noindex-policy（本 phase 升格 locked）
- `.planning/intel/constraints.md` — CONSTR-* SEO/AEO 限制
- `.planning/STATE.md` — GATE-1A 解果（62 篇 + 分類分布）

### Codebase 關鍵檔
- `CLAUDE.md` — 部署細節、API 端點清單、systemd 服務、R2 CDN 邏輯
- `server.py:935-938` — `_is_admin_page` 既有實作（**待修 bug**）
- `server.py:953-988` — `end_headers` 既有 quote 路徑 X-Robots-Tag 範例（**模板可複製給 admin**）
- `server.py:779-790` — `_load_articles` PostgreSQL 與 SQLite fallback
- `server.py:1566-1697` — `_serve_works_page` 動態 SSR pattern（首頁 SSR 可仿）
- `server.py:1699-1723` — `_serve_sitemap` 動態 sitemap 生成
- `robots.txt` — 既有 6 行，需擴充 `Disallow: /admin/`
- `index.html` L1-135 — 首頁 head metadata + 3 個 JSON-LD schema（LocalBusiness / Service / FAQPage）
- `sort-hat/index.html`、`teabar.html`、`wedding-packages/index.html`、`wedding-packages/outdoor.html` — 4 個支援頁 head 段

### 外部規範
- Google Rich Results Test：https://search.google.com/test/rich-results
- robots.txt 規範：https://developers.google.com/search/docs/crawling-indexing/robots/intro
- X-Robots-Tag：https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag

### 部署與環境
- `docs/村山良作-部署資訊清單.md` — 正式環境結構、PostgreSQL 設定
- Cloudflare API 憑證 `~/.claude/.cf-env` — purge cache 用
- Tailscale IP `100.102.51.64` (ach-clawhome) — 驗證 production curl 用

</canonical_refs>

<specifics>
## Specific Ideas

### sitemap 收錄補完整

當前 `_serve_sitemap` 漏掉的靜態頁：
- `/sort-hat/`
- `/muse-2026.html`（hero 直接引用，村長重要 PR 頁面）

補完後預期：`5 個原靜態 + 2 個新靜態 + 62 個 works = 69 個 URL`，預期 sitemap `<loc>` 至少 69 個。

### admin X-Robots-Tag 三步驟修法

1. `_is_admin_page` → 新增 `_is_admin_path`（startswith `/admin`），保留原 `_is_admin_page` 給 path rewrite 用
2. `end_headers` 加 `elif self._is_admin_path():` 分支，注入 `X-Robots-Tag: noindex, nofollow, noarchive` + `Cache-Control: private, no-store`
3. `robots.txt` L2 後加 `Disallow: /admin/`

### homepage SSR 注入 pattern

```python
# server.py 在 do_GET 開頭，先過 admin/sitemap/api 之後新增：
if clean_path in ("/", "/index.html"):
    self._serve_homepage_ssr(); return

def _serve_homepage_ssr(self):
    template = (HERE / "index.html").read_text(encoding="utf-8")
    featured = _load_featured_articles(limit=6)
    cases_html = "\n".join(
        f'<a class="featured-case" href="/works/{a["id"]}">'
        f'<img src="{a["heroImage"]}" alt="{html_escape(a["title"])}" loading="lazy"/>'
        f'<h3>{html_escape(a["title"])}</h3></a>'
        for a in featured
    )
    body = template.replace("<!--{{SSR_FEATURED_CASES}}-->", cases_html)
    # ... 標準 200 response
```

在 `index.html` 的 `#works` section 之前放一個註解 placeholder：
```html
<!--{{SSR_FEATURED_CASES}}-->
```

`assets/site.js` 不需修改；JS 渲染時會根據 hash route 切回完整作品方格，SSR 區塊保留也無妨。

### Cloudflare purge 指令

```bash
set -a && source ~/.claude/.cf-env && set +a
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE/purge_cache" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  --data '{"files":["https://goodjob.weddingwishlove.com/sitemap.xml","https://goodjob.weddingwishlove.com/robots.txt"]}'
```

### Rich Results 8 URL 清單

從 PostgreSQL 取得 `featured=true ORDER BY featuredOrder LIMIT 5` 後組合：

```
1. https://goodjob.weddingwishlove.com/
2. https://goodjob.weddingwishlove.com/workflow.html
3. https://goodjob.weddingwishlove.com/muse-2026.html
4. https://goodjob.weddingwishlove.com/works/{featured[0].id}
5. https://goodjob.weddingwishlove.com/works/{featured[1].id}
6. https://goodjob.weddingwishlove.com/works/{featured[2].id}
7. https://goodjob.weddingwishlove.com/works/{featured[3].id}
8. https://goodjob.weddingwishlove.com/works/{featured[4].id}
```

</specifics>

<deferred>
## Deferred Ideas

明確排除在 Phase 1 之外、留給後續 phase：

- **`/services/*` pillar 頁建立** → Phase 2（REQ-pillar-pages-five）
- **作品 6 區塊模板擴充** → Phase 3（REQ-case-template-expansion）
- **FAQPage schema 完整 5 cluster** → Phase 3（REQ-faq-per-cluster），但 sort-hat/teabar 個別頁的 FAQ schema 仍在 Phase 1 修
- **AI bot allowlist robots.txt** → Phase 4（REQ-robots-waf-bot-allow），Phase 1 只動 admin 段落，不動 OAI/Perplexity 段
- **llms.txt 更新** → Phase 4（REQ-llms-txt-update）
- **AI citation baseline 測試** → Phase 4
- **PostgreSQL `cluster` 欄位 migration** → Phase 3
- **Cloudflare WAF AI bot allowlist audit** → Phase 4 GATE-4C

</deferred>

---

*Phase: 01-p0-tech-fix*
*Context gathered: 2026-05-13 via codebase baseline 探查 + PRD 推導*
