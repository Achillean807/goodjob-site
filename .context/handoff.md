# 收工交接｜2026-11-10（涵蓋 11-06～11-10）

- Repo：`D:\AI_Site\goodjob-site`
- 分支：`master`
- 交接檔寫入前 HEAD：`f094d1a`（CLAUDE.md 11-10(F)）；收工時本機與 `origin/master` 雙向差 0
- 工作區：沒有未提交的 tracked 變更
- 測試：`python -m unittest discover -s tests` 112 tests OK
- `.gitignore` 仍忽略 `.context/`；本檔已被追蹤，要用 `git add -u`

## 本場完成（全部已上正式站，詳細數字見 CLAUDE.md changelog 11-06～11-10(F)）

| 日期 | 內容 |
|---|---|
| 11-06 | SEO／AEO 週報網頁版（Artifact `https://claude.ai/artifact/H6oyADXtfmSkN84beGbMhj`）；聖誕節佈置服務頁改寫成五主題實拍指南（`80d0bb9`） |
| 11-06(B)(C) | 新作品「台中賓士 春節佈置」（`benz-taichung-lunar-new-year-decor`），小桌花補第 12 張 |
| 11-09 | 頂部導覽改四字（`e6449b4`，11-02(J)）之後：首頁季節入口（hero 聖誕按鈕＋橫幅）、春酒尾牙代表案例換入台中賓士 |
| 11-09(D) | **收回 11-04 正式站資安修補入庫**（`800a897`，server.py／admin／tests 6 檔）；合併重複作品 `81bf85d4`→台中賓士（301，`MERGED_WORKS`） |
| 11-10 | 三篇合輯整理：`5a1e1bc3` 301 到喆園；`92387fe2` 留 4 張＋兩個分段；`1c45c415` 改「天玥泉 2024 龍年」3 張 |
| 11-10(B)～(F) | 春節佈置主題頁 `/services/lunar-new-year-decor/`（2027 丁未羊年）；新作品「企業大廳春節佈置」（`corporate-lobby-lunar-new-year-decor`）；4 篇春節作品服務入口改連春節頁（`PILLAR_OVERRIDES`）；首頁橫幅改聖誕卡＋春節卡並排（`be4aa08`）；fresh 驗收 13 項 12 PASS（第 13 項村長裁示保留） |

制度與文件：
- SOP 選圖準則第 7 條：上架前用感知雜湊查重複（`923755e`）
- `~/.claude/refs/ga-analytics-access.md`：GSC 帳號表更正（google-ga profile 是 achillean807）、用網域資源送索引的做法與 3 個坑
- `~/.claude/refs/model-dispatch.md`：驗收單「對外 0 處」條件、追蹤像素排除規則
- `~/.claude/refs/windows-pitfalls.md`：網址清單 CRLF、`python -c` 跳脫字元

## 部署狀態

- 作品數 71 篇：business 24／party 18／school 10／magic 5／civil 14
- 正式站 `server.py` 等於 repo HEAD，且含 11-04 資安修補（PBKDF2、CF-Connecting-IP）。**投放 server.py 前一律先做漂移檢查**，退版會讓 7 份 PBKDF2 提案的客人登不進去
- 301：`81bf85d4`、`auto-brand-new-year-showroom` → 台中賓士；`5a1e1bc3`、`small-banquet-celebration-party` → 喆園
- 主機備份：`/srv/raid1/backups/goodjob-dedup-benz-20261109/`、`goodjob-cleanup-20261110/`、`goodjob-cny-20261110/`、`goodjob-entries-20261109/`（pre～pre5）、`goodjob-xmas-20261106/`、`goodjob-add-benz-20261106/`

## 未竟事項

1. **季節入口撤下**：聖誕卡＋hero 聖誕按鈕預計 2027-01 初撤下；春節卡預計 2027-02 底撤下。撤下方法見 CLAUDE.md 11-09(B)、11-10(F)（`grep data-season`）
2. **GSC 收錄追蹤**：聖誕頁 11-06 送索引後到 11-10 仍「已找到 - 目前尚未建立索引」；春節頁與企業大廳春節作品 11-10 剛送。台中賓士已收錄。建議 11-13 左右跑週報（`D:/AI_Work/MyLord/scripts/goodjob_seo_check.py --out-dir <scratchpad>`，NAS 只讀所以不寫預設路徑）時一起查；聖誕頁仍未收錄就查原因
3. 正式站 6 份文件是 5～7 月舊副本（`.gitattributes`、`.gitignore`、`CLAUDE.md`、`DESIGN.md`、`README.md`、`handoff.md`），不影響網站，未動
4. `92387fe2` 第 1 張底片條有客戶活動真人照（疑似含小孩，未驗證），村長 11-10 裁示保留
5. 本機 `test_quote_auth` 偶發失敗（測試伺服器 5 秒內沒起來、WinError 10053），乾淨 worktree 全過，根因未查
6. 手機版 3 張的段落排成 2＋1（聖誕頁、春節頁）；春酒服務頁 1000px 代表案例 3＋3＋2；村長未要求處理
7. **HelpDesk 部署注意事項（村長選 A）還沒寫**：`docs/conventions/deploy-host.md` 補「restart 前看最近約 10 秒有沒有 `Webhook received`」；該 repo 有別的 session 的未提交變更，只 stage 這一個檔
8. 舊未竟：AEO 重新檢測待村長按；IDAEO 每月 AI 點名率實測；舊 Meta Pixel `1330894157559427` 等尾牙廣告結束後移除（日期村長決定）
