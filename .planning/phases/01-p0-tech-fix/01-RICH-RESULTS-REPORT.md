# Phase 1.4 Rich Results 驗證報告

**REQ:** `REQ-rich-results-validation`
**狀態:** ✅ **已完成（Opus + Playwright 自動跑完 12 個 URL）**
**自動化前置:** ✅ 已由 Opus 完成（8 URL 線上 JSON-LD parse 全綠）
**Google Rich Results Test:** ✅ 12/12 完成，evidence/ 內含全部截圖
**最後修補:** 2026-05-14 — teabar.html Product schema 重大錯誤已換成 Service+OfferCatalog（0 錯誤）

---

## 1. 自動化前置驗證（Opus 已執行）

對 8 個代表 URL 跑 `urllib.request` 抓取線上 HTML，用 Python `json.loads` 驗證每個 `<script type="application/ld+json">` 區塊：

| URL | HTTP | description 字數 | canonical | 偵測 schema 類型 | JSON parse |
|-----|------|------------------|-----------|------------------|------------|
| `/` | 200 | 88 | ✅ self | LocalBusiness, Service, FAQPage | ✅ 全綠 |
| `/workflow.html` | 200 | 61 ⚠️ | ✅ self | FAQPage | ✅ 全綠 |
| `/muse-2026.html` | 200 | 168 | ✅ self | CreativeWork | ✅ 全綠 |
| `/works/gd-home-sweet-home` | 200 | 160 | ✅ self | CreativeWork | ✅ 全綠 |
| `/works/c35fa390` | 200 | 160 | ✅ self | CreativeWork | ✅ 全綠 |
| `/works/chengmei-insect-exhibition` | 200 | 160 | ✅ self | CreativeWork | ✅ 全綠 |
| `/works/42103369` | 200 | 160 | ✅ self | CreativeWork | ✅ 全綠 |
| `/works/cxo-female-founders-club` | 200 | 160 | ✅ self | CreativeWork | ✅ 全綠 |

⚠️ **觀察：** `/workflow.html` description 僅 61 字，未達 spec 70-110 字下限。建議村長手動補到 70 字以上（不阻擋 Phase 1.4 通過，但記入 Phase 2 backlog）。

---

## 2. 待村長手動驗收（Google Rich Results Test）

### 標準操作流程

1. 開 https://search.google.com/test/rich-results
2. 依序輸入下表 URL，按 「TEST URL」
3. 等 Google crawl 完成（30-60 秒/URL）
4. 截圖三項：
   - **Detected items** 區塊（顯示 schema 類型）
   - **Errors / Warnings** 欄位
   - URL 列以佐證
5. 截圖檔存到 `.planning/phases/01-p0-tech-fix/evidence/<檔名>.png`（檔名參考 `evidence/README.md`）
6. 填寫下方表格

### Plan 1.4 必驗 8 URL（Playwright 自動跑完，2026-05-14）

| # | URL | Detected items | Errors | Warnings | Pass/Fail |
|---|-----|----------------|--------|----------|-----------|
| 1 | `/` | LocalBusiness + Service + FAQPage（無 Rich Snippet 候選類型，預期不顯示） | 0 | 0 | ✅ |
| 2 | `/workflow.html` | 常見問題（FAQ）1 個有效 | 0 | 0 | ✅ |
| 3 | `/muse-2026.html` | CreativeWork（不在 Rich Snippet 候選類型） | 0 | 0 | ✅（schema 有效但 Google 不單獨呈現） |
| 4 | `/works/gd-home-sweet-home` | CreativeWork（同上） | 0 | 0 | ✅ |
| 5 | `/works/c35fa390` | CreativeWork（同上） | 0 | 0 | ✅ |
| 6 | `/works/chengmei-insect-exhibition` | CreativeWork（同上） | 0 | 0 | ✅ |
| 7 | `/works/42103369` | CreativeWork（同上） | 0 | 0 | ✅ |
| 8 | `/works/cxo-female-founders-club` | CreativeWork（同上） | 0 | 0 | ✅ |

> **Note**：CreativeWork 不在 Google [Rich Result 候選類型](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)清單內，Rich Results Test 對單一 CreativeWork JSON-LD 會顯示「未偵測到項目」屬正常行為。schema 仍會被 Google 索引並提供給 AI / 知識圖譜引用。

### 額外建議驗證 4 個支援頁（Plan 1.3 新加，Playwright 自動跑完）

| # | URL | Detected items | Errors | Warnings | Pass/Fail |
|---|-----|----------------|--------|----------|-----------|
| 9 | `/sort-hat/` | 導覽標記 1 + 軟體應用程式 1 = 2 有效 | 0 | 0 | ✅ |
| 10 | `/teabar.html` | （修補前 2 紅燈，已換 Service+OfferCatalog）導覽標記 1 + 常見問題 1 = 2 有效 | 0 | 0 | ✅（修補後） |
| 11 | `/wedding-packages/` | 導覽標記 1 有效 | 0 | 0 | ✅ |
| 12 | `/wedding-packages/outdoor.html` | 導覽標記 1 有效 | 0 | 0 | ✅ |

**截圖：** 全部 12 URL 截圖存於 `evidence/`（含 `rich-results-teabar-product-error.png`、`rich-results-teabar-product-detail.png` 記錄修補前錯誤、`rich-results-teabar-fixed.png` 為修補後綠燈截圖）。

---

## 3. Acceptance Criteria

對應 `REQ-rich-results-validation`：

- [x] 8 個代表 URL 全數通過 Rich Results Test，0 error
- [x] schema 中宣告的 title / description / image 都出現於頁面可見文字（spot-check 任 3 URL）
- [x] teabar FAQPage 4 題答案文字皆在頁面可見區
- [x] 截圖完整存入 `evidence/` 並更新本報告

---

## 4. 失敗時 Rollback 路徑

| 失敗類型 | 處理 |
|---------|------|
| FAQ Answer not visible on page | 回 Plan 1.3 補 FAQ 折疊區可見文字 |
| Missing field `image` | 確認 og:image / heroImage URL 200 OK |
| Missing field `priceCurrency` 之類 | 補 schema 必填欄 |
| `Could not fetch` | 確認 robots.txt + CF cache + status 200 |

---

## 5. Phase 1.4 完成標誌

✅ 12 URL Rich Results Test 0 error（8 必驗 + 4 支援頁）
✅ 截圖入庫（含修補前後對照）
✅ 本報告所有 ⏳ 改 ✅
✅ teabar.html Product schema 重大錯誤 → Service+OfferCatalog 修復並重測通過
✅ commit `docs(seo): Phase 1.4 Rich Results 驗收完成（自動化）`

---

## 6. 後續觀察事項

1. `/workflow.html` description 仍 61 字（< spec 70-110）— Phase 2 順手補
2. CreativeWork 不是 Rich Snippet 候選，5 個 works 頁的 schema 仍會提供給 AI / 知識圖譜引用（Phase 3-4 AEO 主戰場）
3. 12 個 URL 全綠，Phase 1 P0 技術修補階段正式收尾
