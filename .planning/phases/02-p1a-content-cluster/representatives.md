# Phase 2 Pillar 代表案例對照表

**Created:** 2026-05-14
**Source:** PostgreSQL `goodjob_site.articles` 查詢結果（GATE-1A 校正後 62 篇基準）

挑選原則：
1. 優先 `featured = 1`
2. 其次 `hero_image` 路徑為 `/hero.webp`（標準命名，視覺最完整）
3. 主題與 pillar 定位契合（非邊緣案例）
4. 每 pillar 取 3 件作為硬編碼 fallback；JS 啟用後 client-side fetch 會渲染該 cluster 全部作品

---

## Pillar 1: `business-event`（27 件 business 作品中選 3 件）

| 案例 ID | 標題 | featured | hero_image |
|--------|------|----------|------------|
| `gd-home-sweet-home` | G-Dragon 台北演唱會丨應援佈置 | ✅ order=1 | `https://goodjob-img.weddingwishlove.com/works/gd-home-sweet-home/hero.webp` |
| `chengmei-insect-exhibition` | 成美文化園昆蟲展丨園區佈置 | ✅ order=2 | `https://goodjob-img.weddingwishlove.com/works/chengmei-insect-exhibition/hero.webp` |
| `cxo-female-founders-club` | CXO 女創俱樂部 品牌活動佈置 | ✅ order=4 | `https://goodjob-img.weddingwishlove.com/works/cxo-female-founders-club/hero.webp` |

備註：跳過 featured order=3 `42103369`（電影拍攝場景，ID 為 hash 不易記，URL 為 `42103369-1.webp` 非標準 `hero.webp`），改取 order=4 `cxo-female-founders-club`，三件分別代表「演唱會應援」「展覽園區」「女創品牌活動」三種主題場景，命中 cannibalization §5 純藍海「主題場景」「主題佈置」關鍵字。

---

## Pillar 2: `party-spring-banquet`（16 件 party 作品中選 3 件）

| 案例 ID | 標題 | featured | hero_image |
|--------|------|----------|------------|
| `nccu-emba-42-graduation` | 政大企家班42屆畢業晚會 | ✅ order=5 | `https://goodjob-img.weddingwishlove.com/works/nccu-emba-42-graduation/hero.webp` |
| `spy-party` | 奇技邦舞會丨2025特務派對 | ❌ | `https://goodjob-img.weddingwishlove.com/works/spy-party/spy-party-4.webp` |
| `vegas-prom` | 賭城風雲畢業舞會 | ❌ | `https://goodjob-img.weddingwishlove.com/works/vegas-prom/hero.webp` |

備註：party category 僅 1 件 featured，補非 featured 但主題明確的 2 件（特務派對、賭城風雲），三件分別代表「企業 EMBA 晚會」「主題派對」「賭場主題舞會」，命中「春酒尾牙」「企業派對」純藍海關鍵字。`spy-party` hero 用 `spy-party-4.webp`（無 `/hero.webp`，已驗證該檔存在）。

---

## Pillar 3: `magic-academy`（5 件 magic 作品全部展示）

| 案例 ID | 標題 | featured | hero_image | 主題對齊 |
|--------|------|----------|------------|---------|
| `c35fa390` | 海運尾牙丨航向魔法學院 | ✅ order=1 | `https://goodjob-img.weddingwishlove.com/works/c35fa390/c35fa390-1.webp` | ⭐⭐⭐ 純魔法主題 |
| `lativ-magic-platform` | Lativ 魔法月台派對 | ❌ | `https://goodjob-img.weddingwishlove.com/works/lativ-magic-platform/hero.webp` | ⭐⭐⭐ 純魔法主題 |
| `3f65f0ab` | 花博婚禮展 展區佈置 | ❌ | `https://goodjob-img.weddingwishlove.com/works/3f65f0ab/3f65f0ab-1.webp` | ⭐ 主題不純（待 Phase 3 重新分類） |

備註：⚠️ magic category 只有 5 件作品，且其中 3 件（`3f65f0ab` 花博婚禮展、`48235c66` 中研院會議、`54da6457` 企業尾牙）主題與「魔法學院」契合度低，疑似 category 誤分類。Phase 2 先用前 2 件純魔法主題 + 1 件補位（取 `3f65f0ab` 因 hero 最完整），並於 pillar 頁加入既有 `/sort-hat/` 互動工具作為第 4 個展示點補強。Phase 3 GATE-3B `cluster` 欄位 migration 時應重新檢視這 3 件分類。

---

## Pillar 4: `civil-makeover`（14 件 civil 作品中選 3 件）

| 案例 ID | 標題 | featured | hero_image |
|--------|------|----------|------------|
| `bc700965` | 北市信義戶政・絕美101 | ✅ order=6 | `https://goodjob-img.weddingwishlove.com/works/bc700965/bc700965-1.webp` |
| `daan-civil` | 北市大安戶政・森林拱門 | ❌ | `https://goodjob-img.weddingwishlove.com/works/daan-civil/hero.webp` |
| `zhongshan-civil` | 基隆中山戶政・燈塔風景 | ❌ | `https://goodjob-img.weddingwishlove.com/works/zhongshan-civil/hero.webp` |

備註：civil category 僅 1 件 featured，補 2 件 hero 完整且主題具代表性的（北市大安森林、基隆中山燈塔），三件分別涵蓋「都會型戶政」「自然主題戶政」「地方特色戶政」三種定位，命中 cannibalization §5 純藍海「戶政事務所」「公部門空間翻新」關鍵字。`zhongshan-civil` 為 cannibalization 報告明列代表作品。

---

## Pillar 5: `wedding-tea-flower`（hub 頁，無對應 articles category）

### 茶飲 3 款（既有 `/teabar.html`）

| ID | 名稱 | 圖卡 URL（暫定） |
|----|------|----------------|
| `liu-yue-qing-guo` | 六月青果 | `https://goodjob-img.weddingwishlove.com/teabar/brand-event.jpg` |
| `xian-guo-mi-jing` | 鮮果蜜境 | （從 teabar.html 取對應圖檔 URL，部署前確認） |
| `mei-mu-qing-xiu` | 玫目清秀 | （同上） |

### 場景套組 4 種（既有 `/wedding-packages/`）

| ID | 名稱 | 圖卡 URL |
|----|------|---------|
| `classic` | 經典送客背景 | `/wedding-packages/images/classic/hero.jpg`（本機，未上 R2） |
| `deluxe` | 華麗舞台走道 | `/wedding-packages/images/deluxe/hero.jpg` |
| `outdoor-ceremony` | 戶外證婚套組 | `/wedding-packages/images/outdoor/ceremony.jpg`（部署前確認檔名） |
| `outdoor-send-off` | 戶外送客套組 | `/wedding-packages/images/outdoor/send-off.jpg`（部署前確認檔名） |

備註：wedding-tea-flower hub 不從 `/api/articles` fetch（無對應 category），純展示 teabar + wedding-packages 既有方案，Plan 2.5 寫 hub 時需從 `teabar.html` 與 `wedding-packages/index.html` 既有 markup 對照確認茶飲與套組圖卡 URL。

---

## 部署前驗證清單

```bash
# 驗證 15 件代表案例 hero_image 全部 HTTP 200
for url in \
  "https://goodjob-img.weddingwishlove.com/works/gd-home-sweet-home/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/chengmei-insect-exhibition/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/cxo-female-founders-club/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/nccu-emba-42-graduation/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/spy-party/spy-party-4.webp" \
  "https://goodjob-img.weddingwishlove.com/works/vegas-prom/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/c35fa390/c35fa390-1.webp" \
  "https://goodjob-img.weddingwishlove.com/works/lativ-magic-platform/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/3f65f0ab/3f65f0ab-1.webp" \
  "https://goodjob-img.weddingwishlove.com/works/bc700965/bc700965-1.webp" \
  "https://goodjob-img.weddingwishlove.com/works/daan-civil/hero.webp" \
  "https://goodjob-img.weddingwishlove.com/works/zhongshan-civil/hero.webp"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  echo "$code  $url"
done
# 預期：12 件全 200
```

---

*Phase: 02-p1a-content-cluster*
*Source query: `SELECT id, title, category, featured, featured_order, hero_image FROM articles WHERE category IN ('business','party','magic','civil') ORDER BY category, featured DESC, COALESCE(featured_order, 9999), row_index;`*
