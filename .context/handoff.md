# 收工交接｜2026-11-03（涵蓋 11-02 下半場）

- Repo：`D:\AI_Site\goodjob-site`
- 分支：`master`
- 交接檔寫入前 HEAD：`6baa813`（CLAUDE.md 11-02(J)）；收工時本機與 `origin/master` 雙向差 0
- 工作區：沒有未提交的 tracked 變更
- 測試：`python -m unittest discover -s tests` 52 tests OK
- `.gitignore` 仍忽略 `.context/`；本檔已被追蹤，要用 `git add -u` 或指定路徑加 `-f`

## 本場完成（全部已上正式站，詳細數字見 CLAUDE.md changelog 11-02(F)～(J)）

| commit | 內容 |
|--------|------|
| `55c6dc0` | 新增作品「葳格國際學校 2026 畢業典禮佈置・萊特薇庭」（school，71 篇／school 10）。2 張合照的人物用 AI 重新合成（未成年、無肖像授權）；服務頁、llms.txt、README、AGENTS 同步 |
| `5d07482` | `server.py` 分段圖庫：張數是 2 的倍數、但不是 3 的倍數時，每排 2 張（`_section_gallery_class`，附測試） |
| DB（無 commit） | 葳格文案 v3→v4（段落短標題）→v5（加入木製扶手介紹，md5 `631da932…`） |
| DB＋R2（無 commit） | 葳格拿掉第 9 張（座位牌讀得出姓名），13→12 張，重新編號，後 4 張加 `?v=20261102d` |
| `9dab60b`／`f1252d8`／`9213628` | SOP：標題行格式、2 欄規則、選圖準則第 5 條（AI 重新合成人物）與第 6 條（名牌 1:1 讀得出就整張不收） |
| `e6449b4` | 全站頂部導覽「主題活動佈置」「春酒尾牙佈置」改為「主題活動」「春酒尾牙」（12 檔 48 處，含 SSR 作品頁） |
| `4e88586`／`f0b20fb`／`3b5d317`／`6baa813` | CLAUDE.md changelog 11-02(F)～(J)；內文作品數 70→71 |

全域制度檔（`~/.claude/refs/`，備份在 `~/.claude/backups/*.bak-20261103`）：
- `model-dispatch.md`：派工單「對外 0 處」驗收條件要先查不准改的來源輸出到哪裡，基準寫成「改前計數減預期變化量」
- `windows-pitfalls.md`：網址清單 CRLF 讓 curl 回 000；`python -c` 跳脫 `\r` 變成真的控制字元

素材留存：AI 合成人物 4 檔放在 NAS 照片原檔資料夾 `260604_葳格國際學校_萊特薇庭\AI合成人物_官網用\`（村長同意寫入）。

## 部署狀態

- 正式站流程：staging `git pull --ff-only` → 回歸閘門（staging 對 prod 全部作品頁）→ prod 漂移檢查 → 備份 → 從 staging `cp` → md5 對 HEAD → restart（`server.py` 有改才做）→ purge
- 備份：`/srv/raid1/backups/goodjob-add-wagor-20261102/`（`before.sql`、`pre/`、`pre-2col/`、`article-before-v4.tsv`、`article-before-v5.tsv`、`before-remove9-*`、`r2-before-remove9/`）、`/srv/raid1/backups/goodjob-navlabel-20261102/pre/`
- 驗收：葳格整篇 Opus 9/10（第 10 項隱私已修）→ 拿掉第 9 張後 Haiku 5/5；扶手文案主對話對外複驗；導覽改字主對話對外複驗 83/83
- DB 現況：business 26／party 16／school 10／magic 5／civil 14，共 71 篇、圖片 717 列

## 未竟事項

1. **村長可選**：16 篇春酒尾牙作品頁的麵包屑與「服務入口」仍寫「春酒尾牙佈置」（`server.py` `CLUSTER_PILLAR_MAP`）。其他分類這兩處本來就用長名稱，所以預設不改；要改的話會連帶改 `/api/works-search` 的 theme 欄位
2. 首頁章末「看完整 N 件主題活動佈置作品」（`assets/site.js` `anchorLabel`）沒改，理由同上
3. 訪客瀏覽器若在 11-02 拿掉照片前快取過不帶 `?v` 的舊第 9 張，最多保留 4 小時；作品頁已改用 `?v` 網址
4. **HelpDesk 部署注意事項（村長選 A）還沒寫**：`docs/conventions/deploy-host.md` 要補「restart 前也要看最近約 10 秒有沒有 `Webhook received`」。11-03 查：另一個 session 的未推送 commit 已推送（本機領先 0），但 HelpDesk 工作區仍有大量別人的未提交變更，動手時只 stage 這一個檔
5. 11-02 上半場留下、仍未驗證：被中斷的 outbound sync（群組 `…1a04`）有沒有補齊；小村子收到「畢業典禮佈置」會不會用 scope=commercial 查作品
6. 已知風險（村長裁示不改）：分類帽頁麵包屑上距寫死 108px；≤900px 小標靠左
7. 舊未竟（10-28 起，沒查證現況）：AEO 重新檢測待村長按；遠端分支 `origin/aeo/idaeo-gaps-20261028` 刪除需村長同意；GSC sitemap 重新提交；IDAEO 每月 AI 點名率實測
