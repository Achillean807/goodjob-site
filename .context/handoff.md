# 交接檔

- 日期：2026-11-11（第二次收工）
- repo：goodjob-site　分支：master
- 程式 HEAD：`d6e9667`（本檔 commit 之後另有 docs commit，以 git log 為準）

## 本 session 做了什麼
1. 後台「提案管理」改版（上午，已收工過）：Banner 縮圖、啟用/隱藏篩選、狀態開關、列尾「編輯」「刪除」、完整刪除。commit `e71442e`、`eaa41f2`、`cd24b50`。
2. SEO 健康檢查：sitemap 83 頁全部通過（title、meta、canonical、h1、JSON-LD 皆正常，無重複內容）。
3. GSC 近 28 天：曝光 1,547、點擊 77、平均排名 6.7；「尾牙布置」平均排名 7.6、「尾牙佈置」10.2。
4. 尾牙服務頁 title／meta 加「2026–2027」（commit `6c615fc`）。
5. 新增指南頁 `/services/party-spring-banquet/planning-guide/`（七步驟、FAQ、時程）；sitemap、llms.txt 已同步。
6. 指南頁加 9 張實拍作品卡片與宣傳區塊；尾牙頁 hero 加指南入口按鈕（commit `d6e9667`）。

## 部署狀態
- prod：`server.py`、`llms.txt`、尾牙頁、指南頁 md5 與 staging 一致；服務 active；CF purge 成功；IndexNow HTTP 200。
- 備份：`/srv/raid1/backups/goodjob-quotemgr-20261111/`、`goodjob-seo-planguide-20261111/`（含 `b2/`）。
- 測試：全套 113 項 OK。

## 未竟事項／待確認
- **未驗證**：後台提案管理畫面（開關、彈窗、刪除）沒人實際點過。
- **未驗證**：指南頁與新 title 的收錄與排名變化，約 2～4 週後用 GSC 比對；「要求建立索引」未送。
- 指南頁宣傳區最後一張（`874c65e1-7`）拱門上看得到一家銀行英文名稱，待村長決定是否換圖。
- `quote/_deleted/` 內 3 份舊資料夾未動，待村長決定是否永久刪除。
- 提案編輯彈窗仍保留「狀態」下拉，與列表開關重複。
- 沒做：尾牙服務頁補「提前多久準備」段落（指南頁已涵蓋）、首頁與頂部導覽的指南入口。
- 排名對手名單（2 張截圖）只來自村長手動搜尋，Firecrawl 額度 11-15 才重置。
- 本 session 兩次改動都沒有 fresh-context agent 驗收。
