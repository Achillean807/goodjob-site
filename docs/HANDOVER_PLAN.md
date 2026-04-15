# 村山良作官網 — AI 交接計劃書

> 最後更新：2026-04-01
> 前一位 AI 完成範圍：topbar 統一、26 篇文案重寫、圖片批量修復、CMS 帳號修改

---

## 一、專案基本資訊

| 項目 | 內容 |
|------|------|
| 網站 URL | `https://goodjob.weddingwishlove.com/` |
| 遠端主機 | `achilean@100.102.51.64`（Tailscale IP）|
| 站台根目錄 | `/srv/weddingwish/murayama-goodjob-site/` |
| 服務 | `murayama-goodjob.service`，port `127.0.0.1:10814` |
| 對外 | Cloudflare Tunnel → `goodjob.weddingwishlove.com` |
| CMS 後台 | `/admin/`，帳號 `ac` / 密碼 `iamach` |
| CSS 快取版本 | `site.css?v=20260401c`（改 CSS 後必須更新此版號） |

### WordPress 舊站（資料來源）
| 項目 | 內容 |
|------|------|
| 舊站 URL | `https://www.weddingwishlove.com/` |
| WP 後台 | `/controlcenter/` |
| REST API 帳號 | `clwadbot_editor` |
| Application Password | `rUhd icuh U7cb TuwK WUIB r0GV` |
| Base64 認證 | `Y2x3YWRib3RfZWRpdG9yOnJVaGQgaWN1aCBVN2NiIFR1d0sgV1VJQiByMEdW` |
| 作品分類 ID | `950`（商業佈置專欄，共 26 篇）|

---

## 二、關鍵檔案結構

```
/srv/weddingwish/murayama-goodjob-site/
├── index.html              # 首頁（Netflix 風格作品牆）
├── teabar.html             # 囍茶方案頁
├── workflow.html           # 合作流程頁
├── sort-hat/index.html     # 分類帽（婚禮座位查詢）
├── admin/index.html        # CMS 後台
├── server.py               # Python stdlib HTTP server + REST API
├── data/
│   ├── articles.json       # ★ 唯一資料源（26 篇作品）
│   ├── config.json         # 管理員帳密（sha256 hash）
│   └── wp_texts.json       # WP 原始文案備份（供參考）
├── assets/
│   ├── site.css            # 全站 CSS
│   ├── site.js             # 前端渲染邏輯
│   └── images/
│       ├── works/          # ★ 作品圖片目錄
│       │   ├── lativ-magic-platform/
│       │   ├── gd-home-sweet-home/
│       │   ├── ... (共 26 個子目錄)
│       │   └── datong-civil/
│       └── ...             # 其他 UI 圖片
```

---

## 三、26 篇作品現況總覽

| # | article ID | 標題 | 分類 | 目錄圖片數 | JSON引用 | 精選 | 精選排序 |
|---|------------|------|------|-----------|---------|------|---------|
| 1 | lativ-magic-platform | Lativ 魔法月台派對 | party | 13 | 13 | ✅ | 1 |
| 2 | gd-home-sweet-home | G-Dragon 應援佈置 | business | 15 | 15 | ✅ | 2 |
| 3 | chengmei-insect-exhibition | 成美文化園昆蟲展 | business | 24 | 24 | ✅ | 3 |
| 4 | cxo-female-founders-club | CXO 女創俱樂部 | business | 10 | 10 | ✅ | 4 |
| 5 | factory-brand-event | 瓶蓋工廠品牌活動 | business | 23 | 23 | ✅ | 5 |
| 6 | nccu-emba-42-graduation | 政大企家班42屆畢業晚會 | party | 25 | 25 | ✅ | 6 |
| 7 | apple-class-event | 曾蘋果老師課程活動 | business | 19 | 19 | ❌ | — |
| 8 | spy-party | 特務舞會派對 | party | 21 | 21 | ❌ | — |
| 9 | chef-popup | 曾師傅新光三越快閃 | business | 16 | 16 | ❌ | — |
| 10 | keelung-wedding-112 | 基隆112年市民聯合婚禮 | party | 13 | 13 | ❌ | — |
| 11 | nccu-emba-41-ceremony | 政大企家班41屆結業典禮 | party | 11 | 11 | ❌ | — |
| 12 | nccu-emba-41-party | 政大企家班41屆畢業晚會 | party | 20 | 20 | ❌ | — |
| 13 | vegas-prom | 賭城風雲畢業舞會 | party | 14 | 14 | ❌ | — |
| 14 | love-and-deepspace-floral | 戀與深空 花藝佈置 | party | 13 | 13 | ❌ | — |
| 15 | wacoal-2024-anniversary | 2024華歌爾週年慶活動佈置 | business | 17 | 17 | ❌ | — |
| 16 | xinbin-social-wall | 新濱食府網美牆 | business | 11 | 11 | ❌ | — |
| 17 | qijibang-masquerade | 奇技邦舞會背板佈置 | party | 8 | 8 | ❌ | — |
| 18 | wacoal-press-conference | 華歌爾週年慶記者會 | business | 8 | 8 | ❌ | — |
| 19 | new-taipei-joint-wedding-2019 | 2019新北市聯合婚禮 | party | 7 | 7 | ❌ | — |
| 20 | daan-civil | 大安戶政拍照區 | civil | 11 | 11 | ❌ | — |
| 21 | zhongzheng-civil | 中正戶政・幸福開市 | civil | 16 | 16 | ❌ | — |
| 22 | nuannuan-civil | 暖暖戶政變身 | civil | 13 | 13 | ❌ | — |
| 23 | renai-civil | 基隆仁愛戶政打卡牆 | civil | 16 | 16 | ❌ | — |
| 24 | zhongshan-civil | 基隆中山戶政打卡牆 | civil | 16 | 16 | ❌ | — |
| 25 | qidu-civil | 七堵戶政櫻花鐵道 | civil | 11 | 11 | ❌ | — |
| 26 | datong-civil | 大同戶政茶行佈置 | civil | 16 | 16 | ❌ | — |

**合計：387 張圖片**

---

## 四、待辦任務

### 🔴 任務 A：WP 媒體庫圖片核對補齊（優先）

**問題**：用 WP REST API `?search=日期前綴` 搜尋部分作品回傳 0 張，因為 WP 媒體庫用「資料夾分類」而非檔名前綴。需改用 WP 後台媒體庫的資料夾功能逐一核對。

**已確認缺圖的作品**：
| 作品 | WP 媒體庫數量 | 新站目錄數量 | 缺少 |
|------|-------------|-----------|------|
| gd-home-sweet-home | 21 | 15 | **6 張** |
| cxo-female-founders-club | 14 | 10 | **4 張** |
| love-and-deepspace-floral | 15 | 13 | **2 張** |
| zhongzheng-civil | 18 | 16 | **2 張** |

**搜尋失敗需人工核對的作品**（API 搜尋前綴返回 0 張，但實際有照片）：

| 作品 | 嘗試的搜尋前綴 | 新站目錄數量 | 需核對 |
|------|-------------|-----------|--------|
| lativ-magic-platform | 250121 | 13 | 需確認 WP 媒體庫資料夾名稱 |
| chengmei-insect-exhibition | 251014 | 24 | 同上 |
| apple-class-event | 250728 | 19 | 同上 |
| spy-party | 250301 | 21 | 同上 |
| chef-popup | 240731 | 16 | 同上 |
| nccu-emba-41-party | 240531 | 20 | 同上 |
| vegas-prom | 230610 | 14 | 同上 |
| wacoal-2024-anniversary | 241016 | 17 | 同上 |
| qijibang-masquerade | 240203 | 8 | 同上 |
| wacoal-press-conference | 231003 | 8 | 同上（不確定，API 回傳 4） |
| new-taipei-joint-wedding-2019 | 190916 | 7 | 同上 |
| qidu-civil | 231101 | 11 | 同上 |
| datong-civil | 240926 | 16 | 同上 |

**WP 媒體庫資料夾結構**（從截圖得知）：
```
媒體庫 > 村山良作 > 專欄 >
  ├── 260123 陽明海運 (31)
  ├── 251014 成美文化園 (34)
  ├── 250728 矽谷曾蘋果 (21)
  ├── 250823 CXO女創 (15)
  ├── 250712 政大42畢業晚會 (24) ✅ 已處理
  ├── 250704 戀與深空 (15)
  ├── 250710 GD粉絲應援 (21)
  ├── 250610 台北中正戶政 (16)
  └── ... (更多資料夾需展開查看)
```

**做法**：
1. 登入 WP 後台 → 媒體庫 → 村山良作 → 專欄
2. 逐一展開每個資料夾，記錄圖片總數
3. 與新站目錄數量比對
4. 差額的圖片，用 WP REST API 下載：
   ```bash
   # 範例：搜尋 GD 應援的圖片
   curl -s "https://www.weddingwishlove.com/wp-json/wp/v2/media?search=250710&per_page=100&_fields=id,source_url" \
     -H "Authorization: Basic Y2x3YWRib3RfZWRpdG9yOnJVaGQgaWN1aCBVN2NiIFR1d0sgV1VJQiByMEdW" \
     -H "User-Agent: Mozilla/5.0"
   ```
5. 下載到新站目錄，更新 articles.json

**注意**：
- WP 圖片 URL 如含中文字，需用 `urllib.parse.quote()` 處理 path 部分
- 新站圖片命名規則：`hero.jpg` + `01.jpg`, `02.jpg`, ...
- 建議分組排列：舞台/場景 → 活動/人物 → 桌花/細節 → 餐點

---

### 🔴 任務 B：產生 26 個靜態作品頁（SEO/AEO 關鍵）

**問題**：目前所有作品都在 `index.html` 裡以 JavaScript modal 呈現，URL 為 `#detail/作品ID`。
- Google 爬蟲**不會讀取 hash fragment**
- 所有文案在 `articles.json` 裡，爬蟲讀不到
- AI 搜尋引擎（ChatGPT/Perplexity/Google AI Overview）也無法索引
- 等於 26 篇 SEO 優化文案**完全白費**

**解決方案**：為每篇作品生成獨立 HTML 靜態頁面。

**目標結構**：
```
/works/
├── lativ-magic-platform.html
├── gd-home-sweet-home.html
├── chengmei-insect-exhibition.html
├── ... (共 26 個 .html)
```

**每個靜態頁面應包含**：
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>{作品標題}｜村山良作</title>
  <meta name="description" content="{description 前 155 字}">
  <link rel="canonical" href="https://goodjob.weddingwishlove.com/works/{id}.html">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{作品標題}｜村山良作">
  <meta property="og:description" content="{description 前 155 字}">
  <meta property="og:image" content="https://goodjob.weddingwishlove.com{heroImage}">
  <meta property="og:url" content="https://goodjob.weddingwishlove.com/works/{id}.html">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{作品標題}｜村山良作">
  <meta name="twitter:image" content="https://goodjob.weddingwishlove.com{heroImage}">

  <!-- Schema.org -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "name": "{作品標題}",
    "description": "{description}",
    "image": "https://goodjob.weddingwishlove.com{heroImage}",
    "author": {"@type": "Organization", "name": "村山良作"},
    "url": "https://goodjob.weddingwishlove.com/works/{id}.html"
  }
  </script>

  <link rel="stylesheet" href="../assets/site.css?v=20260401c">
</head>
<body>
  <!-- 統一 topbar（同 index.html） -->
  <header class="topbar">...</header>

  <!-- 作品內容（純 HTML，不靠 JS） -->
  <main>
    <h1>{作品標題}</h1>
    <p class="category">{分類}</p>
    <img src="{heroImage}" alt="{作品標題}" loading="eager">
    <div class="description">{完整 description}</div>

    <!-- 圖片 gallery -->
    <div class="gallery">
      <img src="{images[0]}" alt="{作品標題} 1" loading="lazy">
      <img src="{images[1]}" alt="{作品標題} 2" loading="lazy">
      ...
    </div>
  </main>

  <!-- 返回首頁 CTA -->
  <a href="../index.html">← 返回全部作品</a>

  <!-- LINE 諮詢 CTA -->
  <a href="https://lin.ee/OG1T3R5" class="btn-line">LINE 諮詢</a>
</body>
</html>
```

**自動化腳本思路**：
```python
#!/usr/bin/env python3
"""Generate static work pages from articles.json"""
import json, os

ROOT = '/srv/weddingwish/murayama-goodjob-site'
with open(f'{ROOT}/data/articles.json') as f:
    articles = json.load(f)['articles']

os.makedirs(f'{ROOT}/works', exist_ok=True)

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}｜村山良作</title>
  <meta name="description" content="{meta_desc}">
  <!-- ... og/twitter/schema tags ... -->
  <link rel="stylesheet" href="../assets/site.css?v=20260401c">
</head>
<body>
  <header class="topbar"><!-- copy from index.html --></header>
  <main class="work-detail">
    <h1>{title}</h1>
    <img src="../{heroImage}" alt="{title}">
    <div class="description">{description}</div>
    <div class="gallery">{gallery_html}</div>
  </main>
</body>
</html>'''

for a in articles:
    gallery = '\n'.join(
        f'<img src="../{img}" alt="{a["title"]} {i+1}" loading="lazy">'
        for i, img in enumerate(a.get('images', []))
    )
    html = TEMPLATE.format(
        title=a['title'],
        meta_desc=a.get('description', '')[:155],
        heroImage=a.get('heroImage', ''),
        description=a.get('description', ''),
        gallery_html=gallery,
    )
    with open(f'{ROOT}/works/{a["id"]}.html', 'w') as f:
        f.write(html)
    print(f'Generated {a["id"]}.html')
```

**還需要**：
- 在 `site.css` 加上 `.work-detail` 相關樣式
- 修改 `site.js` 裡 `#detail/` 的連結行為，改為跳轉到 `/works/{id}.html`
- 或者保留 modal 功能，同時有靜態頁供 SEO

---

### 🔴 任務 C：建立 sitemap.xml + robots.txt

**sitemap.xml**：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://goodjob.weddingwishlove.com/</loc><priority>1.0</priority></url>
  <url><loc>https://goodjob.weddingwishlove.com/teabar.html</loc></url>
  <url><loc>https://goodjob.weddingwishlove.com/workflow.html</loc></url>
  <url><loc>https://goodjob.weddingwishlove.com/sort-hat/</loc></url>
  <!-- 26 篇作品 -->
  <url><loc>https://goodjob.weddingwishlove.com/works/lativ-magic-platform.html</loc></url>
  <url><loc>https://goodjob.weddingwishlove.com/works/gd-home-sweet-home.html</loc></url>
  ... (共 26 篇)
</urlset>
```

**robots.txt**：
```
User-agent: *
Allow: /
Sitemap: https://goodjob.weddingwishlove.com/sitemap.xml

# 不讓爬蟲進後台
Disallow: /admin/
Disallow: /data/
```

---

### 🟡 任務 D：修改 server.py 路由支援 /works/

`server.py` 目前是 `SimpleHTTPRequestHandler` 提供靜態檔案，應該已經能自動 serve `/works/*.html`。確認即可。

如果需要 clean URL（`/works/lativ-magic-platform` 不帶 `.html`），需在 server.py 加：
```python
# 在 do_GET 裡加上
if path.startswith('/works/') and not os.path.exists(translated_path):
    # Try .html extension
    html_path = translated_path + '.html'
    if os.path.exists(html_path):
        self.path = path + '.html'
```

---

### 🟡 任務 E：提交 Google Search Console

1. 在 Google Search Console 確認 `goodjob.weddingwishlove.com` 已驗證
2. 提交 sitemap.xml
3. 使用「網址檢查」工具抽查幾篇作品頁
4. 確認 Googlebot 能正常讀取 HTML 內容

---

## 五、技術注意事項

### SSH 連線
```bash
ssh achilean@100.102.51.64
# Tailscale IP，需在同一 Tailscale 網路
```

### 部署流程
```bash
# 編輯完成後，CSS 改動需更新版號
# 在 HTML 裡找 site.css?v=XXXXXXXX 改新版號
# 重啟服務（通常不需要，靜態檔案直接生效）
sudo systemctl restart murayama-goodjob.service
```

### WP REST API 常用指令
```bash
# 搜尋媒體庫
curl -s "https://www.weddingwishlove.com/wp-json/wp/v2/media?search=KEYWORD&per_page=100&_fields=id,source_url,title" \
  -H "Authorization: Basic Y2x3YWRib3RfZWRpdG9yOnJVaGQgaWN1aCBVN2NiIFR1d0sgV1VJQiByMEdW" \
  -H "User-Agent: Mozilla/5.0"

# 取得作品文章
curl -s "https://www.weddingwishlove.com/wp-json/wp/v2/posts?categories=950&per_page=30&_fields=id,slug,title,content" \
  -H "Authorization: Basic Y2x3YWRib3RfZWRpdG9yOnJVaGQgaWN1aCBVN2NiIFR1d0sgV1VJQiByMEdW" \
  -H "User-Agent: Mozilla/5.0"
```

### 已知坑
1. **WP 媒體 URL 含中文字**：下載時需 URL encode path 部分，用 curl 比較穩
2. **Cloudflare 快取**：改完 CSS/HTML 後若沒更新 `?v=` 版號，用戶可能看到舊版
3. **articles.json 是唯一資料源**：前端 JS 和後台 CMS 都讀這個檔案
4. **圖片命名**：目錄內固定用 `hero.jpg` + `01.jpg`, `02.jpg`... 排序
5. **Windows 本地 Python 跑中文輸出**會遇 cp950 編碼錯誤，需加 `sys.stdout` UTF-8 wrapper

---

## 六、WP 媒體庫搜尋前綴對照表

以下是 26 篇作品對應的 WP 媒體庫搜尋關鍵字。部分前綴已驗證，部分需要從 WP 後台媒體庫資料夾確認正確名稱。

| # | article ID | WP blog slug | 媒體搜尋前綴 | API 搜尋結果 | 狀態 |
|---|------------|-------------|------------|------------|------|
| 1 | lativ-magic-platform | blog_20250121 | 250121 | 0 | ❓需確認資料夾名 |
| 2 | gd-home-sweet-home | blog_20250711 | 250710 | 21 | ✅ 已驗證 |
| 3 | chengmei-insect-exhibition | blog_1014 | 251014 | 0 | ❓WP 資料夾顯示 34 張 |
| 4 | cxo-female-founders-club | blog_250823 | 250823 | 14→15 | ✅ 已驗證（WP 資料夾 15 張）|
| 5 | factory-brand-event | blog_20240923 | 240923 | 2 | ❓需確認 |
| 6 | nccu-emba-42-graduation | blog_250712 | 250712 | 24 | ✅ 已處理完成 |
| 7 | apple-class-event | blog_0728 | 250728 | 0 | ❓WP 資料夾顯示 21 張 |
| 8 | spy-party | blog_250301 | 250301 | 0 | ❓需確認（已有 21 張）|
| 9 | chef-popup | blog_20240731 | 240731 | 0 | ❓需確認 |
| 10 | keelung-wedding-112 | blog_20230920 | 230920 | 13 | ✅ 數量一致 |
| 11 | nccu-emba-41-ceremony | blog_20240713_2 | 240713 | 2 | ❓需確認 |
| 12 | nccu-emba-41-party | blog_20240531 | 240531 | 0 | ❓需確認 |
| 13 | vegas-prom | blog_20230610 | 230610 | 0 | ❓需確認 |
| 14 | love-and-deepspace-floral | blog_20250704 | 250704 | 15 | ⚠️ 新站 13，差 2 |
| 15 | wacoal-2024-anniversary | blog_20241016 | 241016 | 0 | ❓需確認 |
| 16 | xinbin-social-wall | blog_20240417 | 240417 | 6 | ✅ 新站 11 更多 |
| 17 | qijibang-masquerade | blog_20240203 | 240203 | 0 | ❓需確認 |
| 18 | wacoal-press-conference | blog_20231003 | 231003 | 4 | ✅ 新站 8 更多 |
| 19 | new-taipei-joint-wedding-2019 | blog_190916 | 190916 | 0 | ❓需確認 |
| 20 | daan-civil | blog_20241107 | 241107 | 1 | ✅ 新站 11 |
| 21 | zhongzheng-civil | blog_250610 | 250610 | 18 | ⚠️ 新站 16，差 2 |
| 22 | nuannuan-civil | blog_20240801 | 240801 | 6 | ✅ 新站 13 更多 |
| 23 | renai-civil | blog_20240702 | 240702 | 3 | ✅ 新站 16 更多 |
| 24 | zhongshan-civil | blog_20240515 | 240515 | 1 | ✅ 新站 16 更多 |
| 25 | qidu-civil | blog_20231101 | 231101 | 0 | ❓需確認 |
| 26 | datong-civil | blog_20240926 | 240926 | 0 | ❓需確認 |

**核對方法**：
1. 打開 WP 後台 → 媒體庫 → 左側「Folders」→ 村山良作 → 專欄
2. 逐一點開每個資料夾，看實際圖片數
3. API 搜尋有時搜不到是因為檔名前綴不是日期（可能是中文或英文）
4. 用資料夾名稱的前幾個字作為 API 搜尋關鍵字重新搜

---

## 七、已完成的工作清單

- [x] 四頁 topbar 統一（index/teabar/sort-hat/workflow）
- [x] Logo 全白 38px、品牌名「村山良作」
- [x] 移除所有頁面的紅色 M avatar
- [x] 加入 LINE 諮詢綠色按鈕到所有 topbar
- [x] 加入跨頁導航（村山良作/囍茶方案/分類帽/合作流程）
- [x] articles.json images 陣列批量修復（98 → 387 張）
- [x] 26 篇文案 SEO/AEO 重寫
- [x] WP 原始文案備份至 wp_texts.json
- [x] spy-party 從 WP 媒體庫補充至 21 張
- [x] nccu-emba-42-graduation 從 WP 媒體庫換成全解析度 24 張原圖
- [x] CMS 帳號改為 ac / iamach
- [x] CSS 版本更新至 20260401c

---

## 八、優先順序建議

1. **任務 B（靜態作品頁）** — 最大 SEO 影響，所有文案目前對搜尋引擎不可見
2. **任務 C（sitemap + robots）** — 搭配任務 B，讓 Google 知道有頁面
3. **任務 A（圖片核對）** — 補齊缺圖，確保品質
4. **任務 D（server 路由）** — 確認靜態頁能正常存取
5. **任務 E（Search Console）** — 提交索引
