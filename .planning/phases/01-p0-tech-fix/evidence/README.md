# Phase 1 Evidence Files

此目錄存放 Phase 1 驗收用截圖。檔案本身 git-ignored（見專案 `.gitignore`），但目錄保留 + 本 README 記錄期望檔名供村長對照。

## Rich Results Test 截圖（Plan 1.4）

對每個 URL 在 https://search.google.com/test/rich-results 跑完後，截圖存成：

| URL | 截圖檔名 | 預期偵測類型 |
|-----|----------|------------|
| `/` | `rich-results-home.png` | LocalBusiness + Service + FAQPage |
| `/workflow.html` | `rich-results-workflow.png` | FAQPage |
| `/muse-2026.html` | `rich-results-muse-2026.png` | CreativeWork |
| `/works/gd-home-sweet-home` | `rich-results-work-gd.png` | CreativeWork |
| `/works/c35fa390` | `rich-results-work-c35fa390.png` | CreativeWork |
| `/works/chengmei-insect-exhibition` | `rich-results-work-chengmei.png` | CreativeWork |
| `/works/42103369` | `rich-results-work-42103369.png` | CreativeWork |
| `/works/cxo-female-founders-club` | `rich-results-work-cxo.png` | CreativeWork |

### 截圖內容必含
1. **Detected items** 區塊（顯示 schema 類型清單）
2. **Errors** 欄位（理想 = 0）
3. **Warnings** 欄位（有則記錄但不阻擋 phase 通過）
4. URL bar 顯示對應 URL（佐證測試對象）

### 補充：4 個支援頁（Plan 1.3 新加）

雖然 Plan 1.4 acceptance 只列 8 個代表 URL，4 個支援頁也建議村長順手驗證：

| URL | 截圖檔名 | 預期偵測類型 |
|-----|----------|------------|
| `/sort-hat/` | `rich-results-sort-hat.png` | WebApplication + BreadcrumbList |
| `/teabar.html` | `rich-results-teabar.png` | Product + BreadcrumbList + FAQPage |
| `/wedding-packages/` | `rich-results-wp-indoor.png` | Service + BreadcrumbList |
| `/wedding-packages/outdoor.html` | `rich-results-wp-outdoor.png` | Service + BreadcrumbList |

驗收結果填入上層 `01-RICH-RESULTS-REPORT.md`。
