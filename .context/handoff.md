# 收工交接｜2026-11-02

- Repo：`D:\AI_Site\goodjob-site`
- 分支：`master`
- 交接檔寫入前 HEAD：`42aaa9c`（CLAUDE.md 11-02(E)）；收工時本機與 `origin/master` 雙向差 0
- 工作區：沒有未提交的 tracked 變更
- `.gitignore` 第 58 行仍忽略 `.context/`；本檔已被追蹤，照常 commit（該目錄其他暫存檔不該入庫，所以規則保留）

## 本場完成（全部已上正式站，詳細數字見 CLAUDE.md changelog 2026-11-02 到 11-02(E)）

| commit | 內容 |
|--------|------|
| `b2a9483` 起多個 | 新增作品「蘭雅國中 50 週年校慶佈置」：刪 3 張、分段配圖（`case_blocks.sections`，`server.py` `_plan_work_sections`）、合成說明圖獨立「設計巧思」段（`wide`）、舞台圖寬幅、文案 v8 |
| DB（無 commit） | 全站 55 篇作品結尾「村花囍 LINE」→「村花弄囍 LINE」＋「點選「洽詢檔期」」引導 |
| `4ee0425`／`461038e`／`876855f`／`519312a` | 新分類「學校活動」（`school`，9 篇）＋服務頁 `/services/school-event/`；全站導覽、浮動按鈕統一「洽詢檔期」 |
| `ec4e1ed` | 學校活動頁拿掉企家班的「EMBA」誤植；teabar、workflow 浮動按鈕補字 |
| `1451474` | 首頁章末「看完整 N 件」只算本分類（春酒章節顯示 18 張、連結寫 16 件） |
| `e41ef3c` | 分類帽頁 ≤980px 改用橫向快捷列 |
| `3879d68` | 分類帽頁麵包屑不再被版頭蓋住；快捷列右緣淡出（共用 `quick-fade.js`） |
| `1b5e4c5`／`81efb2a`／`42aaa9c` | CLAUDE.md changelog 11-02(B)～(E)、資料模型加 `school` |

跨 repo（HelpDesk `D:/AI_Code/HelpDesk_服務櫃台`，已部署 `line-helpdesk`）：
- `fc03da1`：官網聊天提示詞的商業佈置加「畢業典禮、迎新、校慶」
- `843943c`：`works_search` 工具說明補商業佈置範圍（LINE 與官網共用）
- `4c41be8`／`9cce19e`／`b02a6f1`：`docs/conventions/village-web-chat.md` 紀錄（`4c41be8` 誤把整檔改成 CRLF，`9cce19e` 已改回 LF）

全域制度檔（`~/.claude/refs/`）：
- `model-dispatch.md`：新規則「🔴 檔只給草稿」＋例外（專案 CLAUDE.md 只新增 changelog 條目時，主對話備份後直接套用、事後回報；村長 11-02 同意）
- `maintenance-protocol.md`：🔴 列補同一個例外
- `windows-pitfalls.md`：Edit 工具 LF→CRLF 第三次踩坑（檢查和 commit 寫在同一個指令裡擋不住）

## 部署狀態

- 正式站：每一輪都是 staging `git pull --ff-only` → prod 漂移檢查 → 備份 → 從 staging `cp` → md5 對 HEAD → purge
- 備份：`/srv/raid1/backups/goodjob-add-lanya-20261102/`、`goodjob-cta-20261102/`、`goodjob-school-20261102/`、`goodjob-fix3-20261102/`（`pre/`、`pre2/`）
- fresh-context 驗收：學校活動 9/10（2 項已修並複驗 7/7）、首頁＋分類帽 5/5、分類帽第二輪 4/4、HelpDesk 提示詞 5/6（FAIL 項為重啟時舊行程的錯誤，已查證）、HelpDesk schema 7/7
- DB 現況：business 26／party 16／school 9／magic 5／civil 14，共 70 篇

## 未竟事項

1. **HelpDesk 部署注意事項（村長選 A）還沒寫**：`docs/conventions/deploy-host.md` 要補「restart 前的忙碌判斷，也要看最近約 10 秒有沒有 `Webhook received`」。原因：11-02 16:33:53 restart 時，4 秒前的 webhook 觸發了單一聊天 outbound sync，被中斷（舊 PID 記 `TargetClosedError`）。沒寫的原因：HelpDesk 本機 master 有另一個 session 的 1 個 commit 還沒 push，現在 push 會把它一起推上去。等那邊 push 後再補。
2. 被中斷的那次 outbound sync（群組 `…1a04`），後續 sweep 有沒有補齊：未驗證
3. 小村子收到「畢業典禮佈置」時，實際會不會用 scope=commercial 查作品：未驗證（沒有不影響真實客人的測試管道）
4. 已知風險（村長裁示不改）：分類帽頁麵包屑上距寫死 108px，只比版頭多 0.87px；改版頭時要一起改
5. 村長裁示不改：分類帽頁 ≤900px 小標靠左、主標置中
6. 舊未竟（10-28 交接留下，本場沒處理，也沒查證現況）：
   - AEO 報告「重新檢測」待村長按
   - 遠端分支 `origin/aeo/idaeo-gaps-20261028` 還在，刪除前需村長同意
   - GSC sitemap 重新提交（09-16 起）
   - IDAEO 每月 AI 點名率實測、第三方平台 NAP 一致性
