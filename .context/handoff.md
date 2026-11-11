# 交接檔

- 日期：2026-11-11
- repo：goodjob-site　分支：master
- 程式 HEAD：`cd24b50`（本檔 commit 之後另有 docs commit，以 git log 為準）

## 本 session 做了什麼
後台「提案管理」（`/controlcenter`）改版，已上正式站：
1. 10 份只有代號的提案標題依內文改名（manifest，prod 資料；備份 `data/quote_manifest.json.bak-20261111-titles`）。
2. 列表加 Banner 縮圖（`GET /api/quotes/{id}/banner`）。
3. 加「顯示：全部／啟用／隱藏」篩選。
4. 每列：狀態開關、「編輯」「刪除」按鈕；編輯改彈窗，右側卡片已移除。
5. 刪除改完整刪除（資料夾＋manifest 紀錄＋task-state），無法復原。

## 部署狀態
- prod 三個檔（`server.py`、`admin/app.js`、`admin/index.html`）md5 等於 repo HEAD；服務 active。
- prod 備份：`/srv/raid1/backups/goodjob-quotemgr-20261111/`。
- 測試：`tests.test_quote_auth`、`tests.test_admin_quote_ui` 32 項 OK。

## 未竟事項／待確認
- **未驗證**：後台畫面、狀態開關、編輯彈窗、刪除按鈕沒人實際點過（沒有登入密碼）。請村長 Ctrl+Shift+R 後試用。
- **未驗收**：沒有 fresh-context agent 驗收。
- `quote/_deleted/` 內 3 份舊資料夾（260815-tasks、260815int-k7q2、261129）未動，待村長決定是否永久刪除。
- 編輯彈窗仍保留「狀態」下拉，與列表開關重複；村長要拿掉再說。
- 無 Banner 的 4 份提案：260613、260815mini、apple、millenniumtaichung。
