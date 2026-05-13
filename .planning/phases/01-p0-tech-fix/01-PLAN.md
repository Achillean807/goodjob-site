# Phase 1: P0 技術修補 — PLAN

**Created:** 2026-05-13
**Status:** Ready for execution
**Depends on:** GATE-1A 已通過（62 篇）
**Total plans:** 5（對應 5 條 REQ）
**估時：** 7-14 天（含驗收）

---

## ▶ Plan Index

| Plan ID | REQ | Subject | Files Modified | 估時 |
|---------|-----|---------|----------------|------|
| 1.1 | REQ-prod-sitemap-verify | Sitemap 補完整 + Cloudflare purge | `server.py`、`scripts/cf-purge.ps1` (new) | 0.5d |
| 1.2 | REQ-admin-noindex | X-Robots-Tag + robots.txt + bug fix | `server.py`、`robots.txt` | 1d |
| 1.3 | REQ-support-pages-metadata | 4 個支援頁 metadata + schema | `sort-hat/index.html`、`teabar.html`、`wedding-packages/index.html`、`wedding-packages/outdoor.html` | 2d |
| 1.4 | REQ-rich-results-validation | 8 URL Rich Results 驗證 + 截圖 | `.planning/phases/01-p0-tech-fix/evidence/` | 0.5d |
| 1.5 | REQ-homepage-server-rendered-cases | 首頁 SSR 精選作品 + description 擴充 | `server.py`、`index.html` | 2d |

**執行順序：** 1.2 → 1.5 → 1.1（依賴 1.5 的 SSR fallback 不影響 sitemap）→ 1.3 → 1.4（最後驗收，依賴前面全部上線）

---

## Plan 1.1: Sitemap 補完整 + Cloudflare purge

**REQ:** `REQ-prod-sitemap-verify`
**Owner suggestion:** Sonnet subagent（純文件編輯 + 模板化指令）

### Objective

讓 `/sitemap.xml` 涵蓋 PostgreSQL 全部 62 篇 + 補漏的 2 個靜態頁，並建立 deploy 後可重複執行的 Cloudflare cache purge 腳本。

### Files Modified

- `server.py` — `_serve_sitemap`（~L1699）新增 2 個靜態 URL
- `scripts/cf-purge.ps1` —（新檔）讀 `~/.claude/.cf-env` 然後對 sitemap + robots 發 purge request

### Tasks

1. **Edit `server.py:_serve_sitemap`** L1708 的靜態頁 list：
   ```python
   for loc in ["", "/teabar.html", "/workflow.html",
               "/wedding-packages/", "/wedding-packages/outdoor.html",
               "/sort-hat/", "/muse-2026.html"]:
   ```

2. **建立 `scripts/cf-purge.ps1`**（PowerShell；村長環境）：
   ```powershell
   #!/usr/bin/env pwsh
   # 用法：pwsh scripts/cf-purge.ps1 [-Paths "/sitemap.xml,/robots.txt"]
   param([string]$Paths = "/sitemap.xml,/robots.txt")
   $envFile = "$HOME/.claude/.cf-env"
   if (-not (Test-Path $envFile)) { throw "Missing $envFile" }
   Get-Content $envFile | ForEach-Object {
     if ($_ -match '^([A-Z_]+)=(.+)$') { Set-Item "Env:$($matches[1])" $matches[2] }
   }
   $files = ($Paths.Split(',') | ForEach-Object { "https://goodjob.weddingwishlove.com$_" }) -join '","'
   $body = "{`"files`":[`"$files`"]}"
   $headers = @{
     Authorization = "Bearer $env:CLOUDFLARE_API_TOKEN"
     "Content-Type" = "application/json"
     "User-Agent" = "Mozilla/5.0 (compatible; villager-deploy)"
   }
   $url = "https://api.cloudflare.com/client/v4/zones/$env:CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE/purge_cache"
   Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $body | ConvertTo-Json
   ```

3. **部署 + purge：** scp server.py 到 ach-clawhome → `sudo systemctl restart murayama-goodjob.service` → 本機跑 `pwsh scripts/cf-purge.ps1`

### Verification

```bash
# 1. URL 數驗收
COUNT=$(curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -c '<loc>')
echo "sitemap URL count: $COUNT"
# 預期：≥ 69（62 篇 works + 7 個靜態頁）

# 2. 確認新加的 URL
curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -E "sort-hat|muse-2026"
# 預期：兩條都有

# 3. 確認 GSC 提交（村長手動）
# → 至 https://search.google.com/search-console
# → 提交 https://goodjob.weddingwishlove.com/sitemap.xml
# → 驗收：狀態 = 「成功」
```

### Acceptance Criteria

直接對應 `REQ-prod-sitemap-verify`：
- [ ] `curl -s .../sitemap.xml | grep -c '<loc>'` ≥ **69**（62 篇 works + 7 個靜態頁）
- [ ] 7 個靜態頁全列出：`/`、`/teabar.html`、`/workflow.html`、`/muse-2026.html`、`/sort-hat/`、`/wedding-packages/`、`/wedding-packages/outdoor.html`
  - 驗證命令：
    ```bash
    for path in "/" "/teabar.html" "/workflow.html" "/muse-2026.html" "/sort-hat/" "/wedding-packages/" "/wedding-packages/outdoor.html"; do
      curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -q "goodjob.weddingwishlove.com${path}</loc>" && echo "PASS $path" || echo "FAIL $path"
    done
    ```
    預期：7 個全 PASS
- [ ] sitemap 不含 `data/articles.json` 已下架條目（_load_articles 從 PostgreSQL 拉，自然滿足）
- [ ] GSC URL Inspection 顯示 sitemap 狀態為「成功」

### Risks

- **R1.1.1** GSC 索引狀態可能延遲幾天；驗收條件 3 改為「已提交且狀態非 error」
- **R1.1.2** `scripts/cf-purge.ps1` 寫入失敗時應 exit 非 0；用 `Invoke-RestMethod` 自動 raise on HTTP error

### autonomous

`true`（除了 GSC 提交需村長親自操作）

---

## Plan 1.2: Admin X-Robots-Tag + robots.txt + bug fix

**REQ:** `REQ-admin-noindex`
**Owner suggestion:** Sonnet subagent 寫 patch，Opus review

### Objective

修補 `_is_admin_page` 子路徑覆蓋 bug，在 admin 全部回應加上 `X-Robots-Tag` 與 `Cache-Control`，並補 robots.txt `Disallow: /admin/`。

### Files Modified

- `server.py` L935-938（新增 `_is_admin_path`）+ L953-965（end_headers admin 分支）
- `robots.txt`（加 `Disallow: /admin/`）

### Tasks

1. **Edit `server.py:935`** 新增 `_is_admin_path`（保留舊 `_is_admin_page` 給 path rewrite 用）：
   ```python
   def _is_admin_path(self):
       """Match /admin*  including /admin/index.html, /admin/app.js etc."""
       stripped = unquote(self.path.split("?")[0].split("#")[0])
       return stripped == "/admin" or stripped.startswith("/admin/")
   ```

2. **Edit `server.py:end_headers`（~L953）** 在 `_is_quote_path` 之後加 admin 分支：
   ```python
   def end_headers(self):
       if self._is_quote_path():
           self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet, noimageindex")
           self.send_header("Cache-Control", "private, no-store, max-age=0")
           # ... 既有 Pragma / Expires
       elif self._is_admin_path():
           self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
           self.send_header("Cache-Control", "private, no-store, max-age=0")
           self.send_header("Pragma", "no-cache")
           self.send_header("Expires", "0")
       elif self._is_robots_path():
           # ... 既有
       super().end_headers()
   ```
   保留既有 `_is_quote_path` 與 `_is_robots_path` 分支不動。

3. **Edit `robots.txt`** 加 `Disallow: /admin/`（在 `Disallow: /quote/` 之後）：
   ```
   User-agent: *
   Disallow: /quote/
   Disallow: /admin/
   Allow: /

   Sitemap: https://goodjob.weddingwishlove.com/sitemap.xml
   LLMs-Txt: https://goodjob.weddingwishlove.com/llms.txt
   ```

4. **部署 + purge robots.txt：** scp server.py + robots.txt → restart service → `pwsh scripts/cf-purge.ps1 -Paths "/robots.txt"`

### Verification

```bash
# 1. /admin 根目錄
curl -s -I https://goodjob.weddingwishlove.com/admin/ | grep -i 'x-robots-tag'
# 預期：X-Robots-Tag: noindex, nofollow, noarchive

# 2. /admin/index.html（子路徑）
curl -s -I https://goodjob.weddingwishlove.com/admin/index.html | grep -i 'x-robots-tag'
# 預期：同上（這是 bug 修補的關鍵驗證）

# 3. /admin/app.js
curl -s -I https://goodjob.weddingwishlove.com/admin/app.js | grep -i 'x-robots-tag'
# 預期：同上

# 4. robots.txt
curl -s https://goodjob.weddingwishlove.com/robots.txt | grep -i 'Disallow: /admin'
# 預期：Disallow: /admin/

# 5. /quote/ 仍正常（regression check）
curl -s -I https://goodjob.weddingwishlove.com/quote/ | grep -i 'x-robots-tag'
# 預期：仍有 X-Robots-Tag（不影響既有 quote 行為）

# 6. 公開頁不應有 X-Robots-Tag（regression check）
curl -s -I https://goodjob.weddingwishlove.com/ | grep -i 'x-robots-tag'
# 預期：（無輸出）

# 7. GSC URL Inspection（村長手動）
# → 對 https://goodjob.weddingwishlove.com/admin/ 跑 URL Inspection
# → 預期狀態：「Excluded by 'noindex' tag」
```

### Acceptance Criteria

對應 `REQ-admin-noindex`：
- [ ] `curl -I .../admin/` 含 `X-Robots-Tag: noindex, nofollow, noarchive`
- [ ] `curl -I .../admin/index.html` 同上（bug fix 驗證）
- [ ] `robots.txt` 含 `Disallow: /admin/`
- [ ] GSC URL Inspection `/admin/` 顯示 `Excluded by 'noindex' tag`
- [ ] `/quote/` 與公開頁無 regression（既有行為保留）

### Risks

- **R1.2.1** `unquote` 對 `%2e%2e` 等 URL escape 可能繞過；用 `_is_admin_path` 保守判斷 `startswith("/admin/")`（含尾斜線可防 `/admin-something/`）
- **R1.2.2** Cloudflare cache 可能 hit 舊 header；purge 後跑 verification

### autonomous

`true`

---

## Plan 1.3: 4 個支援頁 metadata + schema

**REQ:** `REQ-support-pages-metadata`
**Owner suggestion:** Codex CLI（按 spec 批次補 metadata，模板化）

### Objective

為 `/sort-hat/`、`/teabar.html`、`/wedding-packages/`、`/wedding-packages/outdoor.html` 4 個頁面補齊 description（70-110 字）、canonical、OG/Twitter card、JSON-LD schema。

### Files Modified

- `sort-hat/index.html` — head 補完整 metadata + 2 個 schema
- `teabar.html` — 補 schema（其他既有）
- `wedding-packages/index.html` — 補 description / canonical / OG / 2 個 schema
- `wedding-packages/outdoor.html` — 同上

### Tasks

#### 1.3.A `/sort-hat/index.html` 補完整

替換 `<head>` 段，加在現有 `<meta name="description">` 之後：

```html
<link rel="canonical" href="https://goodjob.weddingwishlove.com/sort-hat/" />
<meta property="og:type" content="website" />
<meta property="og:title" content="分類帽｜入席預言查詢系統｜村山良作" />
<meta property="og:description" content="用魔法分類帽的互動方式查詢座位，取代傳統紙本座位表，適用婚宴、派對、企業活動。村山良作為村花弄囍婚禮活動打造的座位查詢工具，賓客掃 QR 就能找到自己的桌次。" />
<meta property="og:image" content="https://goodjob.weddingwishlove.com/assets/images/factory-hero.jpg" />
<meta property="og:image:alt" content="分類帽魔法座位查詢系統互動畫面" />
<meta property="og:url" content="https://goodjob.weddingwishlove.com/sort-hat/" />
<meta property="og:site_name" content="村山良作 MURAYAMA GOODJOB" />
<meta property="og:locale" content="zh_TW" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="分類帽｜入席預言查詢系統｜村山良作" />
<meta name="twitter:description" content="用魔法分類帽的互動方式查詢座位，取代傳統紙本座位表，適用婚宴、派對、企業活動。" />
<meta name="twitter:image" content="https://goodjob.weddingwishlove.com/assets/images/factory-hero.jpg" />
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "分類帽入席預言查詢系統",
  "url": "https://goodjob.weddingwishlove.com/sort-hat/",
  "applicationCategory": "BrowserApplication",
  "operatingSystem": "Web",
  "description": "用魔法分類帽的互動方式查詢座位，取代傳統紙本座位表。",
  "publisher": {
    "@type": "Organization",
    "name": "村山良作 MURAYAMA GOODJOB",
    "url": "https://goodjob.weddingwishlove.com/"
  },
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "TWD" }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "村山良作", "item": "https://goodjob.weddingwishlove.com/" },
    { "@type": "ListItem", "position": 2, "name": "分類帽", "item": "https://goodjob.weddingwishlove.com/sort-hat/" }
  ]
}
</script>
```

並把現有 description 擴充到 70-110 字（替換 L7 內容為更完整版本）。

#### 1.3.B `/teabar.html` 補 schema

teabar.html 已有完整 OG/Twitter/canonical/description；缺 schema。在 `<head>` 結尾前加：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "村花囍茶",
  "description": "天然花果迎賓茶，客製化 LOGO 標籤，400ml 瓶裝，50 瓶起訂。",
  "brand": { "@type": "Brand", "name": "村花囍茶" },
  "image": "https://goodjob.weddingwishlove.com/assets/images/teabar/brand-event.jpg",
  "url": "https://goodjob.weddingwishlove.com/teabar.html",
  "offers": [
    { "@type": "Offer", "name": "六月青果", "priceCurrency": "TWD", "availability": "https://schema.org/InStock", "url": "https://goodjob.weddingwishlove.com/teabar.html" },
    { "@type": "Offer", "name": "鮮果蜜境", "priceCurrency": "TWD", "availability": "https://schema.org/InStock", "url": "https://goodjob.weddingwishlove.com/teabar.html" },
    { "@type": "Offer", "name": "玫目清秀", "priceCurrency": "TWD", "availability": "https://schema.org/InStock", "url": "https://goodjob.weddingwishlove.com/teabar.html" }
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "村山良作", "item": "https://goodjob.weddingwishlove.com/" },
    { "@type": "ListItem", "position": 2, "name": "囍茶方案", "item": "https://goodjob.weddingwishlove.com/teabar.html" }
  ]
}
</script>
```

**teabar 專屬 FAQPage（CONTEXT L66 LOCKED — 必含；4 題與首頁 FAQ 不重複，焦點放在囍茶產品本身）：**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "客製 LOGO 標貼最快多久可以交件？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "確認 LOGO 設計稿後，標準工期約 7-10 個工作天。急件視當期排單狀況可壓縮至 5 個工作天，建議活動前 3 週確認設計稿。"
      }
    },
    {
      "@type": "Question",
      "name": "為什麼最低訂量設定 50 瓶？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "客製標貼印刷與冷藏物流的最低成本門檻決定。50 瓶以下因平攤印刷與配送成本，單瓶價格會高於成品店面價，不符合迎賓茶飲的成本效益。"
      }
    },
    {
      "@type": "Question",
      "name": "保冰配送怎麼運作？多久內喝完最好？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "冷藏宅配（4-7°C）配送到指定場地，活動現場放入保冰桶可維持 4 小時最佳口感。建議活動開始前 1 小時送達，活動結束後 24 小時內飲用完畢。"
      }
    },
    {
      "@type": "Question",
      "name": "六月青果、鮮果蜜境、玫目清秀三種口味的差異？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "六月青果為青蘋果柚子基底，口感清爽帶微酸，適合下午茶與夏季戶外場；鮮果蜜境為熱帶水果蜂蜜調，香甜飽滿，適合婚禮與晚宴；玫目清秀為玫瑰荔枝調，優雅微甜，適合主題活動與品牌發表會。"
      }
    }
  ]
}
</script>
```

**重要約束**：4 題的答案文字必須在頁面上「可見」(Google Rich Results Test 規則)。若 teabar.html 既有文案沒覆蓋這些內容，需在 hero / 介紹區補一段 FAQ 折疊區或產品說明段落，不能只塞 JSON-LD。Plan 1.4 驗收時若 Rich Results Test 報 "Missing field" 或 "FAQ answer not visible on page"，回頭補可見文字後再測。

#### 1.3.C `/wedding-packages/index.html` 補完整

`<head>` 在現有 `<title>` 之後加：

```html
<meta name="description" content="送客背景與舞台走道婚禮場景套組，含設計圖、進場動線、撤場計畫。經典與華麗兩種套組，依場地客製化調整，村花弄囍美學團隊執行。" />
<link rel="canonical" href="https://goodjob.weddingwishlove.com/wedding-packages/" />
<meta property="og:type" content="website" />
<meta property="og:title" content="婚禮場景佈置｜送客背景・舞台走道套組｜村花弄囍" />
<meta property="og:description" content="送客背景與舞台走道婚禮場景套組，含設計圖、進場動線、撤場計畫。經典與華麗兩種套組，依場地客製化調整，村花弄囍美學團隊執行。" />
<meta property="og:image" content="https://goodjob.weddingwishlove.com/wedding-packages/images/classic/hero.jpg" />
<meta property="og:image:alt" content="村花弄囍經典送客背景婚禮佈置現場" />
<meta property="og:url" content="https://goodjob.weddingwishlove.com/wedding-packages/" />
<meta property="og:site_name" content="村花弄囍" />
<meta property="og:locale" content="zh_TW" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="婚禮場景佈置｜送客背景・舞台走道套組｜村花弄囍" />
<meta name="twitter:description" content="送客背景與舞台走道婚禮場景套組，含設計圖、進場動線、撤場計畫。" />
<meta name="twitter:image" content="https://goodjob.weddingwishlove.com/wedding-packages/images/classic/hero.jpg" />
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Service",
  "serviceType": "婚禮場景佈置",
  "name": "婚禮場景佈置套組",
  "description": "送客背景與舞台走道婚禮場景套組，含設計圖、進場動線、撤場計畫。",
  "provider": { "@type": "Organization", "name": "村花弄囍", "url": "https://www.weddingwishlove.com/" },
  "areaServed": { "@type": "Country", "name": "台灣" },
  "url": "https://goodjob.weddingwishlove.com/wedding-packages/",
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "婚禮場景套組",
    "itemListElement": [
      { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "經典套組" } },
      { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "華麗套組" } }
    ]
  }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "村山良作", "item": "https://goodjob.weddingwishlove.com/" },
    { "@type": "ListItem", "position": 2, "name": "婚禮場景佈置", "item": "https://goodjob.weddingwishlove.com/wedding-packages/" }
  ]
}
</script>
```

#### 1.3.D `/wedding-packages/outdoor.html` 補完整

同 1.3.C 結構，調整為戶外證婚版本（references `images/outdoor/hero.jpg` 或實際圖檔）。description 文案：「戶外證婚與送客場景套組，含天氣備案、地形評估、進場動線。雙境轉場設計讓儀式與宴客自然銜接，村花弄囍美學團隊執行。」

### Verification

```bash
# 對 4 個 URL 各執行：
for u in "/sort-hat/" "/teabar.html" "/wedding-packages/" "/wedding-packages/outdoor.html"; do
  echo "=== $u ==="
  curl -s "https://goodjob.weddingwishlove.com$u" | grep -E '<meta name="description"|rel="canonical"|og:title|application/ld\+json' | head -10
done

# description 字數驗收（人工或腳本）— 70-110 中文字
# 村長手動：開 https://search.google.com/test/rich-results 跑每個 URL
```

### Acceptance Criteria

對應 `REQ-support-pages-metadata`：
- [ ] 4 頁 `<meta name="description">` 各 70-110 中文字
- [ ] 4 頁 `<link rel="canonical">` 指向自身 production URL
- [ ] 4 頁 OG + Twitter card 齊全（title / description / image / url + alt）
- [ ] 4 頁至少 1 個 schema 通過 Rich Results Test 0 error

### Risks

- **R1.3.1** OG image 路徑若指向不存在圖檔會在 FB debugger 報錯；驗收前先 `curl -I` 確認每個 og:image 都 200
- **R1.3.2** description 字數若以 byte 計會被中文字超出限制；用「中文字」標準（每字 1 個視覺單位）

### autonomous

`true`（純文件編輯，可派 codex CLI 一次寫完 4 個檔的 head 段）

---

## Plan 1.4: 8 個 URL Rich Results 驗證

**REQ:** `REQ-rich-results-validation`
**Owner suggestion:** 村長親自跑 Rich Results Test（人工驗收為主）

### Objective

對 8 個代表 URL（首頁 + workflow + MUSE + 5 個 featured 作品）逐一跑 Rich Results Test，截圖留證，確認 0 error 且 schema 中文字皆出現於頁面可見內容。

### Files Modified

- `.planning/phases/01-p0-tech-fix/evidence/rich-results-*.png`（截圖，git-ignored 但 commit 一個 README.md 記錄結果）
- `.planning/phases/01-p0-tech-fix/01-RICH-RESULTS-REPORT.md`（驗收報告）

### Tasks

1. **取 5 個 featured 作品 ID：**
   ```bash
   ssh achilean@100.102.51.64 'psql -d goodjob_site -t -c "SELECT id FROM articles WHERE featured = 1 ORDER BY featured_order, row_index LIMIT 5;"'
   ```

2. **列出 8 個 URL：**
   ```
   https://goodjob.weddingwishlove.com/
   https://goodjob.weddingwishlove.com/workflow.html
   https://goodjob.weddingwishlove.com/muse-2026.html
   https://goodjob.weddingwishlove.com/works/{id1}
   https://goodjob.weddingwishlove.com/works/{id2}
   https://goodjob.weddingwishlove.com/works/{id3}
   https://goodjob.weddingwishlove.com/works/{id4}
   https://goodjob.weddingwishlove.com/works/{id5}
   ```

3. **村長手動：** 對每個 URL 跑 `https://search.google.com/test/rich-results`，截圖：
   - Detected items 區塊
   - 0 errors（若有 warning 也記錄）
   - 「Test result」section

4. **產出 `01-RICH-RESULTS-REPORT.md`** 記錄 8 個 URL 各自結果（Detected schema 類型、Error 數、Warning 數、Pass/Fail）

### Verification

人工：每個 URL 都有截圖，Report 全綠（0 error）。

### Acceptance Criteria

對應 `REQ-rich-results-validation`：
- [ ] 8 個 URL 全數通過 Rich Results Test，0 error
- [ ] schema 中宣告的 title / description / image 都出現於頁面可見文字（spot-check 任 3 URL）

### Risks

- **R1.4.1** 若有 error → 倒退到 1.1 / 1.3 修 schema 重跑
- **R1.4.2** 若有 warning（如缺 `aggregateRating`）→ 記錄但不阻塞 phase 通過

### autonomous

`false`（需要村長操作 Google 工具）

---

## Plan 1.5: 首頁 SSR 精選作品 + description 擴充

**REQ:** `REQ-homepage-server-rendered-cases`
**Owner suggestion:** Codex CLI（spec 明確、boilerplate 多）

### Objective

讓 `curl https://.../` 不執行 JS 即可看到 ≥ 3 件精選作品（標題 + 內鏈），同時把首頁 description 從 30 字擴到 70-110 字。

### Files Modified

- `server.py` — 新增 `_serve_homepage_ssr()` + `_load_featured_articles()` + do_GET 路由
- `index.html` — 加入 `<!--{{SSR_FEATURED_CASES}}-->` placeholder + description 替換

### Tasks

1. **Edit `index.html` L7-10** description 替換（70-110 中文字）：
   ```html
   <meta
     name="description"
     content="村山良作專注品牌活動佈置、主題場景設計與展場空間規劃，承接春酒尾牙、戶政空間改造與大型展覽。從概念設計到現場執行一條龍，把每個現場做成可被感受、可被記住的體驗。"
   />
   ```

2. **Edit `index.html`** 在 `<section class="featured-grid">` 或 `<main id="home">` 開頭加入 placeholder：
   ```html
   <section id="ssr-featured" class="ssr-featured" aria-label="精選作品概覽">
     <h2 class="ssr-featured-title">精選作品</h2>
     <!--{{SSR_FEATURED_CASES}}-->
   </section>
   ```
   並在 `assets/site.css` 加最小可見的樣式（後續可由 site.js 隱藏或保留）：
   ```css
   .ssr-featured { padding: 60px 20px; }
   .ssr-featured-title { font-size: 1.8rem; color: var(--text); margin-bottom: 24px; }
   .ssr-featured .featured-case { display: inline-block; width: 30%; margin: 1%; vertical-align: top; }
   .ssr-featured .featured-case img { width: 100%; height: 180px; object-fit: cover; border-radius: 8px; }
   .ssr-featured .featured-case h3 { color: var(--text); font-size: 1rem; margin: 12px 0 0; }
   /* JS 啟用後可隱藏；但保留 hidden 屬性給無 JS 用戶 */
   ```

3. **Edit `server.py`** 加入兩個新 function：
   ```python
   def _load_featured_articles(limit=6):
       """Load featured articles for SSR injection.

       Schema 對齊（server.py L227-243 / L406-408）：
       - PostgreSQL: featured = INTEGER(0/1), 欄位 snake_case (featured_order, hero_image)
       - RealDictCursor 回傳 dict，用 r["..."] 取值（不是 tuple index）
       - SQLite fallback 結構欄位名一致
       """
       try:
           if _using_postgres():
               with _pg_connect() as conn:
                   with conn.cursor() as cur:
                       cur.execute(
                           "SELECT id, title, hero_image FROM articles "
                           "WHERE featured = 1 ORDER BY featured_order NULLS LAST, row_index LIMIT %s",
                           (limit,)
                       )
                       return [
                           {"id": r["id"], "title": r["title"], "heroImage": r["hero_image"]}
                           for r in cur.fetchall()
                       ]
           # SQLite fallback
           with _db_connect() as conn:
               rows = conn.execute(
                   "SELECT id, title, hero_image FROM articles "
                   "WHERE featured = 1 ORDER BY featured_order, row_index LIMIT ?",
                   (limit,)
               ).fetchall()
               return [
                   {"id": r["id"], "title": r["title"], "heroImage": r["hero_image"]}
                   for r in rows
               ]
       except Exception:
           return []
   ```

   並在 `do_GET` 加路由（在 admin / sitemap 判斷之後、靜態 fallback 之前）：
   ```python
   if clean_path in ("/", "/index.html"):
       self._serve_homepage_ssr(); return

   def _serve_homepage_ssr(self):
       """Inject featured cases into index.html for non-JS crawlers."""
       import html as _html
       template = (HERE / "index.html").read_text(encoding="utf-8")
       featured = _load_featured_articles(limit=6)
       if featured:
           cases_html = "\n".join(
               f'<a class="featured-case" href="/works/{_html.escape(a["id"])}">'
               f'<img src="{_html.escape(a.get("heroImage") or "")}" alt="{_html.escape(a["title"])}" loading="lazy"/>'
               f'<h3>{_html.escape(a["title"])}</h3></a>'
               for a in featured
           )
       else:
           cases_html = "<!-- no featured articles -->"
       body = template.replace("<!--{{SSR_FEATURED_CASES}}-->", cases_html).encode("utf-8")
       self.send_response(200)
       self.send_header("Content-Type", "text/html; charset=utf-8")
       self.send_header("Content-Length", str(len(body)))
       self.end_headers()
       self.wfile.write(body)
   ```

4. **本機驗證：** `python3 server.py --port 8000` → `curl http://localhost:8000/ | grep featured-case` → 應看到 ≥ 3 個 anchor。

5. **部署 + purge：** scp + restart + `pwsh scripts/cf-purge.ps1 -Paths "/,/index.html"`

### Verification

```bash
# 1. 不執行 JS 看作品
COUNT=$(curl -s https://goodjob.weddingwishlove.com/ | grep -c 'class="featured-case"')
echo "SSR featured cases: $COUNT"
# 預期：≥ 3

# 2. 內鏈是 /works/{id} 格式
curl -s https://goodjob.weddingwishlove.com/ | grep -oE 'href="/works/[^"]+"' | head -5
# 預期：5 個合法 ID

# 3. description 字數
curl -s https://goodjob.weddingwishlove.com/ | grep '<meta name="description"' | head -1
# 預期：70-110 中文字內容

# 4. SPA 仍正常（regression）
# 村長手動：開瀏覽器訪問首頁，作品方格能正常 hover / 點開 modal
```

### Acceptance Criteria

對應 `REQ-homepage-server-rendered-cases`：
- [ ] `curl .../` 不執行 JS 即可看到 ≥ 3 個精選作品標題
- [ ] 每個 SSR case 都有 `<a href="/works/{id}">` 內鏈
- [ ] 首頁 description 70-110 中文字
- [ ] SPA 行為無 regression（瀏覽器仍正常）

### Risks

- **R1.5.1** `index.html` 若被 admin CMS 編輯破壞 placeholder 註解 → 加 `if "{{SSR_FEATURED_CASES}}" not in template: log warning` 但仍 serve（fallback 不破壞）
- **R1.5.2** PostgreSQL 連線失敗時 `_load_featured_articles` 回 `[]`，placeholder 替換為註解，頁面仍可用
- **R1.5.3** SSR 區塊與 site.js 渲染的 `#works` 視覺重複 → 由 site.css `.ssr-featured` 控制（可設 `display: none` 在 site.js 載入後）；本 phase 不做隱藏，留作後續視覺優化

### autonomous

`true`（codex CLI 走 wrapper，分 server.py + index.html + site.css 三個 diff）

---

## Phase 1 整體 Success Criteria（必須全綠才能進 Phase 2）

對應 ROADMAP.md § Phase 1：

1. [ ] `curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -c '<loc>'` ≥ **69**（GATE-1A 解果 62 篇 + 7 個靜態頁）→ 由 Plan 1.1 達成
2. [ ] `curl -I https://goodjob.weddingwishlove.com/admin/` response header 含 `X-Robots-Tag: noindex, nofollow, noarchive` → 由 Plan 1.2 達成
3. [ ] 4 個支援頁均通過 Rich Results Test 0 error → 由 Plan 1.3 + 1.4 達成
4. [ ] `curl https://goodjob.weddingwishlove.com/` 不執行 JS 即可看到 ≥ 3 個精選作品標題與內鏈 → 由 Plan 1.5 達成
5. [ ] 首頁 + 合作流程 + MUSE + 5 個代表作品 8 個 URL Rich Results Test 全綠 → 由 Plan 1.4 達成

---

## Threat Model（簡版）

| 威脅 | 嚴重度 | 緩解 |
|------|--------|------|
| Plan 1.2 `_is_admin_path` 用 `unquote` 後若 path 有 `%2e%2e` 可能繞過 | Low | startswith `/admin/` + 同時前置已有 Basic Auth |
| Plan 1.5 SSR 從 PostgreSQL 拉資料：若 SQL 注入 | Low | `featured = 1` 為 hardcoded INTEGER 常數，無 user input；limit 為 Python int |
| Plan 1.5 `_html.escape` 用於 title / heroImage URL：若 URL 含奇怪字元 | Low | escape 已涵蓋 `<>&'"`; heroImage 為內部 R2 URL 可信 |
| robots.txt 修改後若被 cache 服務舊版 | Med | Plan 1.2 部署後立即 `cf-purge.ps1 -Paths "/robots.txt"` |
| sitemap 部署後 GSC 索引狀態延遲 | Med | 驗收條件允許「已提交且狀態非 error」；7 天後重檢 |

---

## Rollback Strategy

每個 plan 部署後若 Verification 任一條 FAIL，依下列順序回滾：

### 通用流程

```powershell
# 1. 找到觸發問題的 commit
git log --oneline -5

# 2. revert（保留 commit 紀錄，不用 reset --hard）
git revert <commit-sha>
git push

# 3. scp 回滾後檔案到正式機
scp server.py robots.txt index.html achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"

# 4. CF cache purge（避免 edge 快取舊問題版本）
pwsh scripts/cf-purge.ps1 -Paths "/sitemap.xml,/robots.txt,/,/index.html,/admin/,/sort-hat/,/teabar.html,/wedding-packages/,/wedding-packages/outdoor.html"

# 5. 驗證恢復
curl -I https://goodjob.weddingwishlove.com/
curl -s https://goodjob.weddingwishlove.com/sitemap.xml | grep -c '<loc>'  # 應 = 前一版的數字
```

### Per-Plan 回滾要點

| Plan | 若失敗，回到 | 不影響範圍 |
|------|------------|----------|
| 1.1 sitemap | server.py 前版（仍含 62 篇 works，僅缺 2 個新靜態頁） | 公開頁、admin、SSR 全不受影響 |
| 1.2 admin noindex | server.py + robots.txt 前版（admin 暫無 noindex header，但 Basic Auth 仍擋未授權存取） | 不影響 `/quote/` noindex（既有邏輯保留） |
| 1.3 4 頁 metadata | git revert 對應頁面 commit；schema 移除即可，meta tag 補錯不會崩頁 | 完全 client-side，不影響 server |
| 1.4 Rich Results | 純驗證，無 rollback 需求；失敗只代表 Plan 1.3 / 1.5 需補強 | — |
| 1.5 首頁 SSR | 移除 `_serve_homepage_ssr` 路由分支，首頁退回靜態 index.html + SPA 渲染；placeholder 註解保留不影響顯示 | 不影響其他頁面 |

### Rollback 後必做

- 開新 issue 紀錄失敗原因（哪條 Verification 沒過、log 摘錄）
- 在 `01-PLAN.md` 對應 plan 加 `> ⚠️ Rolled back YYYY-MM-DD: <原因>` 段落
- 修正後重新部署前，先在本機 `python3 server.py --port 8000` 跑同樣 Verification 命令確認通過

---

## Plan Index → 對應 REQ → Files Map

| Plan | REQ | server.py | index.html | robots.txt | 支援頁 HTML | scripts/ |
|------|-----|-----------|-----------|-----------|------------|----------|
| 1.1 | sitemap-verify | ✓ L1708 | — | — | — | ✓ new cf-purge.ps1 |
| 1.2 | admin-noindex | ✓ L935/953 | — | ✓ | — | — |
| 1.3 | support-metadata | — | — | — | ✓ 4 檔 | — |
| 1.4 | rich-results | — | — | — | — | — |
| 1.5 | homepage-ssr | ✓ do_GET | ✓ description + placeholder | — | — | — |

**衝突檢測：** 1.1 與 1.2 都動 `server.py` 但行數不衝突；1.5 與 1.1/1.2 並行可（do_GET / `_serve_sitemap` / `end_headers` 三個獨立 method）。建議執行順序：1.2 → 1.5 → 1.1 → 1.3 → 1.4。

---

*Phase: 01-p0-tech-fix*
*Plan written: 2026-05-13*
