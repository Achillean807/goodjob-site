# 提案管理後台設計

## 目的

在既有 `/admin/` 後台加入提案管理能力，讓放在 `quote/` 資料夾的一層提案目錄可以由後台控制開放狀態、個別密碼與刪除流程。目標是降低客戶把提案連結轉交其他廠商比價的風險，同時保留提案頁目前「不被搜尋引擎索引、不快取」的行為。

## 已確認決策

- 每個提案資料夾使用各自的密碼。
- 隱藏提案時，客戶開啟網址會看到「此提案暫停開放」。
- 刪除提案時，不做永久刪除，而是把資料夾移到 `quote/_deleted/` 下。
- 新提案資料夾放進 `quote/` 後，如果尚未在後台設定密碼，預設不開放，顯示「此提案暫停開放」。

## 推薦架構

新增 `data/quote_manifest.json` 作為提案管理狀態來源。提案本身仍然維持目前的靜態檔案結構，例如 `quote/260606/index.html`、`quote/260606/images/003.jpg`。`server.py` 在處理 `/quote/...` 請求前先讀取 manifest，依照提案狀態決定要顯示密碼頁、暫停頁或實際靜態內容。

這個做法比把設定寫入每個提案資料夾更安全，避免日後打包或搬移提案時把密碼雜湊與管理狀態一起帶出；也比直接存 SQLite 更貼近此功能的檔案型資料來源，實作與備份都比較直覺。

## 資料模型

`data/quote_manifest.json` 使用單一物件包住提案清單：

```json
{
  "quotes": {
    "260606": {
      "id": "260606",
      "title": "260606",
      "status": "active",
      "passwordSalt": "hex-or-url-safe-salt",
      "passwordHash": "sha256-hash",
      "createdAt": "2026-05-17T00:00:00",
      "updatedAt": "2026-05-17T00:00:00",
      "deletedAt": null,
      "deletedPath": null
    }
  }
}
```

`status` 只允許三種值：

- `active`: 已設定密碼且可輸入密碼瀏覽。
- `hidden`: 顯示「此提案暫停開放」。
- `deleted`: 後台不列在可操作提案清單的主要區塊，資料夾已移到 `quote/_deleted/`。

manifest 不儲存明文密碼，只儲存 salt 與 hash。雜湊方式沿用現有帳號系統的 salted SHA-256 helper，保持專案內一致。

## 權限模型

新增後台權限 `quotes.manage`。既有 `admin` 角色預設包含此權限；`editor` 與 `viewer` 預設不包含。使用自訂角色時，可在帳戶管理中勾選此權限。

有 `quotes.manage` 權限者可以：

- 讀取提案清單。
- 設定或重設單一提案密碼。
- 切換 `active` / `hidden`。
- 將提案移到 `quote/_deleted/`。

沒有 `quotes.manage` 權限者不會看到提案管理入口，直接呼叫 API 會得到 `403 Forbidden`。

## 後台介面

在 `/admin/` 既有版面新增「提案管理」入口。入口只對有 `quotes.manage` 權限的帳號顯示。

提案管理畫面列出 `quote/` 下一層資料夾，排除 `_deleted` 與非資料夾項目。每列顯示：

- 提案 ID，例如 `260606`。
- 標題，預設等於資料夾名稱，可由後台修改。
- 狀態：啟用、隱藏、未設定密碼。
- 提案網址，例如 `/quote/260606/`。
- 操作按鈕：設定密碼、啟用、隱藏、刪除。

未設定密碼的提案即使資料夾存在，也顯示為不可開放。後台必須設定密碼後才能切到 `active`。

## API 設計

新增以下 API，全部需要 HTTP Basic Auth 且需要 `quotes.manage` 權限：

- `GET /api/quotes`: 掃描 `quote/` 並合併 manifest 狀態後回傳清單。
- `PUT /api/quotes/{id}`: 更新標題、狀態或密碼。若要切到 `active`，該提案必須已有密碼或本次請求同時提供新密碼。
- `DELETE /api/quotes/{id}`: 將資料夾移到 `quote/_deleted/{id}-{YYYYMMDD-HHMMSS}/`，並把 manifest 狀態標記為 `deleted`。

API 不回傳 `passwordHash` 或 `passwordSalt`，只回傳 `hasPassword: true/false`。

## 客戶瀏覽流程

使用者開啟 `/quote/{id}/` 或其子資源時，伺服器先解析第一層提案 ID。

處理規則：

- 資料夾不存在：維持 `404 Not Found`。
- manifest 沒有紀錄，或紀錄沒有密碼：回傳暫停頁。
- `status` 是 `hidden`：回傳暫停頁。
- `status` 是 `deleted`：回傳暫停頁。
- `status` 是 `active` 且沒有有效通行 cookie：回傳密碼頁。
- `status` 是 `active` 且 cookie 有效：回傳原始靜態檔案。

密碼頁使用 `POST /quote/{id}/auth` 驗證密碼。密碼正確時設定 HttpOnly cookie，cookie 只對 `/quote/{id}/` 路徑有效，避免用一份提案的通行狀態瀏覽另一份提案。密碼錯誤時仍停留在密碼頁並顯示錯誤訊息。

提案頁與提案資源保留現有標頭：

- `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex`
- `Cache-Control: private, no-store, max-age=0`
- `Pragma: no-cache`
- `Expires: 0`

## 刪除流程

後台刪除提案時，伺服器執行同一檔案系統內的 rename/move：

```text
quote/260606/
quote/_deleted/260606-20260517-153000/
```

若目標資料夾已存在，API 回傳錯誤，不覆蓋既有資料。manifest 更新為：

- `status: "deleted"`
- `deletedAt`: 刪除時間
- `deletedPath`: 實際移動後的相對路徑

刪除後原網址 `/quote/260606/` 會優先依 manifest 的 `deleted` 紀錄顯示「此提案暫停開放」。只有在 manifest 不可用或紀錄不存在、且資料夾也不存在時，才回到一般 `404 Not Found`。

## 錯誤處理

- 無效提案 ID：API 回傳 `400`，只允許安全的一層資料夾名稱，例如英數、底線、連字號。
- 找不到提案資料夾：API 回傳 `404`。
- 切換啟用但沒有密碼：API 回傳 `400`。
- 權限不足：API 回傳 `403`。
- 未登入或密碼錯誤：後台 API 回傳 `401`；客戶提案密碼錯誤回到密碼頁。
- manifest 讀取失敗：採保守策略，所有提案視為未開放。
- manifest 寫入失敗或搬移資料夾失敗：API 回傳 `500`，不改變原資料夾位置。

## 測試策略

更新 `tests/test_quote_auth.py`，把目前「提案頁公開」的預期改為「未設定密碼時不開放」。新增測試覆蓋：

- 未設定 manifest 的提案顯示暫停開放。
- 已隱藏提案顯示暫停開放。
- 已啟用但未帶 cookie 時顯示密碼頁。
- 錯誤密碼不產生通行 cookie。
- 正確密碼產生只作用於該提案路徑的 cookie。
- 有效 cookie 可讀取該提案 HTML 與圖片資源。
- 另一份提案不能沿用前一份提案的 cookie。
- `GET /api/quotes` 需要 `quotes.manage`。
- `PUT /api/quotes/{id}` 可設定密碼與切換狀態。
- `DELETE /api/quotes/{id}` 會把資料夾移到 `quote/_deleted/` 並更新 manifest。
- 所有 `/quote/` 回應維持 noindex 與 no-store 標頭。

## 不在本次範圍

- 線上新增或上傳整份提案資料夾。
- 從後台復原 `_deleted` 內的提案。
- 每個提案多組客戶帳號。
- 提案瀏覽紀錄、登入紀錄或通知。
