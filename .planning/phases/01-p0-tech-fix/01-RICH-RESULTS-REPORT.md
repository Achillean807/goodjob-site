# Phase 1.4 Rich Results 驗證報告

**REQ:** `REQ-rich-results-validation`
**狀態:** 🟡 待村長手動驗收（autonomous=false）
**自動化前置:** ✅ 已由 Opus 完成（8 URL 線上 JSON-LD parse 全綠）
**最終人工驗收:** ⏳ 待村長親自跑 Google Rich Results Test

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

### Plan 1.4 必驗 8 URL

| # | URL | Detected items | Errors | Warnings | Pass/Fail |
|---|-----|----------------|--------|----------|-----------|
| 1 | `/` | _填_ | _填_ | _填_ | ⏳ |
| 2 | `/workflow.html` | _填_ | _填_ | _填_ | ⏳ |
| 3 | `/muse-2026.html` | _填_ | _填_ | _填_ | ⏳ |
| 4 | `/works/gd-home-sweet-home` | _填_ | _填_ | _填_ | ⏳ |
| 5 | `/works/c35fa390` | _填_ | _填_ | _填_ | ⏳ |
| 6 | `/works/chengmei-insect-exhibition` | _填_ | _填_ | _填_ | ⏳ |
| 7 | `/works/42103369` | _填_ | _填_ | _填_ | ⏳ |
| 8 | `/works/cxo-female-founders-club` | _填_ | _填_ | _填_ | ⏳ |

### 額外建議驗證 4 個支援頁（Plan 1.3 新加）

| # | URL | Detected items | Errors | Warnings | Pass/Fail |
|---|-----|----------------|--------|----------|-----------|
| 9 | `/sort-hat/` | _填_ | _填_ | _填_ | ⏳ |
| 10 | `/teabar.html` | _填_ | _填_ | _填_ | ⏳ |
| 11 | `/wedding-packages/` | _填_ | _填_ | _填_ | ⏳ |
| 12 | `/wedding-packages/outdoor.html` | _填_ | _填_ | _填_ | ⏳ |

---

## 3. Acceptance Criteria

對應 `REQ-rich-results-validation`：

- [ ] 8 個代表 URL 全數通過 Rich Results Test，0 error
- [ ] schema 中宣告的 title / description / image 都出現於頁面可見文字（spot-check 任 3 URL）
- [ ] teabar FAQPage 4 題答案文字皆在頁面可見區
- [ ] 截圖完整存入 `evidence/` 並更新本報告

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

✅ 8 URL Rich Results Test 0 error
✅ 截圖入庫
✅ 本報告所有 ⏳ 改 ✅
✅ commit `docs(seo): Phase 1.4 Rich Results 驗收報告`
