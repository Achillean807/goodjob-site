# 村山良作官網 SEO / AEO 審計與改善手冊

更新日期：2026-04-01
站台網址：https://goodjob.weddingwishlove.com
適用範圍：村山良作獨立站（murayama-goodjob-site）

---

## 一、審計結果總覽

| 大項 | 評分 | 說明 |
|------|------|------|
| **SEO 總分** | **6.5 / 10** | 基礎 HTML 結構良好，但缺少社群分享標籤與搜尋引擎引導檔 |
| **AEO 總分** | **5.5 / 10** | AI 搜尋引擎（Perplexity、ChatGPT Search）無法正確擷取結構化資訊 |

---

## 二、SEO 各項評分明細

### 已達標項目

| 項目 | 分數 | 說明 |
|------|------|------|
| 頁面標題 `<title>` | 9/10 | 每頁都有獨立且描述性的標題 |
| Meta Description | 9/10 | 每頁都有適當的描述 |
| 語意化 HTML | 8/10 | 使用 `<header>`, `<main>`, `<section>`, `<footer>` |
| 標題層級 h1-h2 | 8/10 | 層級清楚，h1 唯一 |
| 圖片 alt 文字 | 7/10 | 大部分圖片有 alt，hero 裝飾圖適當用 `aria-hidden` |
| 行動裝置適配 | 8/10 | 有 viewport meta，CSS 有 RWD 斷點 |
| 字型載入 | 7/10 | 使用 `preconnect` 加速 Google Fonts |

### 缺失項目（急需修復）

| 項目 | 分數 | 影響 |
|------|------|------|
| Open Graph 標籤 | 0/10 | Facebook/LINE 分享無預覽圖和摘要 |
| Twitter Card 標籤 | 0/10 | Twitter/X 分享無卡片預覽 |
| JSON-LD 結構化資料 | 0/10 | Google 搜尋結果無 rich snippet |
| sitemap.xml | 0/10 | 搜尋引擎無法發現所有頁面 |
| robots.txt | 0/10 | 搜尋引擎無抓取指引 |
| Canonical URL | 0/10 | 可能被判為重複內容 |
| Favicon 完整性 | 5/10 | 只有 PNG favicon，缺 apple-touch-icon |

---

## 三、AEO 各項評分明細

AEO（Answer Engine Optimization）指針對 AI 搜尋引擎的優化。

| 項目 | 分數 | 說明 |
|------|------|------|
| 頁面內容可讀性 | 7/10 | 文字內容清楚，但部分由 JS 動態渲染 |
| FAQ 結構化資料 | 0/10 | 無 FAQPage schema，AI 無法擷取問答 |
| LocalBusiness Schema | 0/10 | 無商家結構化資料（名稱、地址、服務範圍） |
| Service Schema | 0/10 | 無服務描述的結構化資料 |
| 內容語義密度 | 7/10 | articles.json 有豐富描述和關鍵字 |
| 導航可爬取性 | 6/10 | JS 渲染卡片，純爬蟲可能看不到內容 |

---

## 四、改善清單與實作指南

### 優先級 1：立即修復（影響最大）

#### 4.1 新增 Open Graph + Twitter Card 標籤

在每個 HTML 的 `<head>` 中加入：

```html
<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="村山良作｜品牌活動・主題場景・展場空間">
<meta property="og:description" content="把品牌活動、主題場景與展場空間，做成真的現場。">
<meta property="og:image" content="https://goodjob.weddingwishlove.com/assets/images/factory-hero.jpg">
<meta property="og:url" content="https://goodjob.weddingwishlove.com/">
<meta property="og:site_name" content="村山良作 MURAYAMA GOODJOB">
<meta property="og:locale" content="zh_TW">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="村山良作｜品牌活動・主題場景・展場空間">
<meta name="twitter:description" content="把品牌活動、主題場景與展場空間，做成真的現場。">
<meta name="twitter:image" content="https://goodjob.weddingwishlove.com/assets/images/factory-hero.jpg">
```

每頁需要各自的 title / description / image / url。
- `index.html` — 用首頁標題和 hero 圖
- `workflow.html` — 用合作流程標題和對應圖片
- `teabar.html` — 用囍茶方案標題和茶吧圖片

**驗證方式：**
- Facebook: https://developers.facebook.com/tools/debug/
- Twitter: https://cards-dev.twitter.com/validator
- LINE: 貼連結到 LINE 聊天看預覽

#### 4.2 新增 Canonical URL

每頁 `<head>` 加入：

```html
<link rel="canonical" href="https://goodjob.weddingwishlove.com/">
```

每頁的 href 要對應該頁的完整 URL。

#### 4.3 建立 robots.txt

在站台根目錄建立 `robots.txt`：

```
User-agent: *
Allow: /

Sitemap: https://goodjob.weddingwishlove.com/sitemap.xml
```

檔案位置：`murayama-goodjob-site/robots.txt`

#### 4.4 建立 sitemap.xml

在站台根目錄建立 `sitemap.xml`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://goodjob.weddingwishlove.com/</loc>
    <lastmod>2026-04-01</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://goodjob.weddingwishlove.com/workflow.html</loc>
    <lastmod>2026-04-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://goodjob.weddingwishlove.com/teabar.html</loc>
    <lastmod>2026-04-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

**注意：** 新增頁面時要同步更新 sitemap。

### 優先級 2：結構化資料（SEO + AEO 雙效）

#### 4.5 新增 JSON-LD：LocalBusiness

在 `index.html` 的 `<head>` 中加入：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "村山良作 MURAYAMA GOODJOB",
  "description": "品牌活動、主題場景與展場空間的專業佈置團隊",
  "url": "https://goodjob.weddingwishlove.com",
  "image": "https://goodjob.weddingwishlove.com/assets/images/factory-hero.jpg",
  "telephone": "",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "台北市",
    "addressRegion": "台灣"
  },
  "parentOrganization": {
    "@type": "Organization",
    "name": "村花弄囍",
    "url": "https://www.weddingwishlove.com"
  },
  "sameAs": [
    "https://www.facebook.com/weddingwishlove/",
    "https://www.instagram.com/weddingwishlove/"
  ]
}
</script>
```

#### 4.6 新增 JSON-LD：FAQPage（AEO 關鍵）

在 `workflow.html` 加入常見問答 schema：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "村山良作的合作流程是什麼？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "合作流程分四步：需求收集、方向對齊、內容確認、現場落地。從初次聯繫到活動完成，通常需要2-4週。"
      }
    },
    {
      "@type": "Question",
      "name": "村山良作提供哪些服務？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "我們提供品牌活動佈置、主題場景設計、展場空間規劃、春酒尾牙佈置、戶政空間改造等服務。"
      }
    },
    {
      "@type": "Question",
      "name": "如何聯絡村山良作？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可透過 LINE 官方帳號聯絡我們，或透過村花弄囍主站的聯絡表單。"
      }
    }
  ]
}
</script>
```

#### 4.7 新增 JSON-LD：Service（每項服務）

在 `index.html` 加入服務 schema：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Service",
  "provider": {
    "@type": "LocalBusiness",
    "name": "村山良作 MURAYAMA GOODJOB"
  },
  "serviceType": ["品牌活動佈置", "主題場景設計", "展場空間規劃", "春酒尾牙佈置", "戶政空間改造"],
  "areaServed": {
    "@type": "Country",
    "name": "台灣"
  }
}
</script>
```

### 優先級 3：進階優化

#### 4.8 Apple Touch Icon

在 `<head>` 加入：

```html
<link rel="apple-touch-icon" sizes="180x180" href="/assets/images/apple-touch-icon.png">
```

需要製作 180x180 的 PNG icon。

#### 4.9 提升 JS 渲染內容的可爬取性

目前作品卡片由 `site.js` 讀取 `articles.json` 動態渲染，純 HTML 爬蟲看不到。

改善方式：
- 在 `<noscript>` 標籤中放入基本的作品列表 HTML
- 或在 server.py 中實作 SSR（server-side rendering）— 偵測爬蟲 User-Agent 時回傳預渲染的 HTML

#### 4.10 提交至 Google Search Console

1. 前往 https://search.google.com/search-console
2. 新增資源 `https://goodjob.weddingwishlove.com`
3. 透過 DNS TXT 或 HTML meta 驗證擁有權
4. 提交 sitemap.xml
5. 使用「網址檢查」工具要求建立索引

---

## 五、改善後預期效果

| 項目 | 改善前 | 改善後（預期） |
|------|--------|---------------|
| SEO 總分 | 6.5/10 | 9/10 |
| AEO 總分 | 5.5/10 | 8.5/10 |
| LINE/FB 分享 | 無預覽 | 有標題+圖片+摘要 |
| Google 搜尋 | 基本索引 | Rich Snippet 顯示 |
| AI 搜尋引擎 | 無法擷取結構化答案 | 可回答「村山良作提供什麼服務」等問題 |

---

## 六、維護提醒

1. **新增頁面時**：同步更新 sitemap.xml、加入 OG/Twitter/Canonical 標籤
2. **更新內容時**：更新 sitemap.xml 的 `<lastmod>` 日期
3. **新增服務項目時**：更新 JSON-LD 中的 serviceType
4. **定期檢查**：每季用 Google Search Console 確認索引狀態
5. **分享測試**：重要頁面更新後，用 FB Debug Tool 重新抓取

---

## 七、技術資訊

| 項目 | 值 |
|------|-----|
| 站台目錄 | `/srv/weddingwish/murayama-goodjob-site/` |
| 服務 | `murayama-goodjob.service` (port 10814) |
| 外部 URL | `https://goodjob.weddingwishlove.com` |
| Cloudflare Tunnel | `goodjob.weddingwishlove.com → localhost:10814` |
| 需修改的檔案 | `index.html`, `workflow.html`, `teabar.html`, 新增 `robots.txt`, `sitemap.xml` |
| 部署方式 | SCP 上傳後即生效，不需重啟服務 |
