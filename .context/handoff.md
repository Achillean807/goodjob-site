# 收工交接｜2026-09-26

- Repo：`D:\AI_Site\goodjob-site`
- 分支：`master`
- HEAD：`cb62c22`（收工時雙向比對 `origin/master` 皆 0，工作區乾淨）
- 本檔為本場新建；`.gitignore` 忽略 `.context/`，本檔用 `git add -f` 強制追蹤，是否改規則由村長決定。

## 本場完成

- `cf3b01e`：新增 `GET /api/works-search?q=&limit=`（給村花官網 HelpDesk 的 `works_search(scope=commercial)` 工具）。中文 2-gram 計分：分類中文名×3／標題×2／內文×1，哈利波特／魔法／霍格華茲視為魔法學院同義詞；回 `{results:[{title,url,theme,styles,summary,date}]}`。`CLUSTER_PILLAR_MAP` 拉到模組層級供 SSR 與端點共用。測試 `tests/test_works_search.py` 11 題。
- `cb62c22`：CLAUDE.md API 對照表與變更紀錄補記。

## 部署證據

- staging（`/srv/raid1/weddingwish/goodjob-staging`，git repo）`reset --hard origin/master` 到 `cf3b01e`，驗 400／200／200 後 `cp server.py` 到 prod（`/srv/raid1/weddingwish/goodjob-sit`，非 git；備份 `server.py.bak-20260924`）。prod 舊檔 md5 等於 `cf3b01e~1` 的 `server.py`，證實這次是乾淨落差、沒有未回寫的手改。
- 金鑰 `GOODJOB_WORKS_SEARCH_KEY` 寫在 `/etc/systemd/system/murayama-goodjob{,-staging}.service.d/works-search.conf`（600 root），值與 HelpDesk `LH_VILLAGE_CHAT_PROXY_KEY` 同一把（末 4 碼 f047）。prod 不帶金鑰 403、帶金鑰 200；對外站 200。

## 待辦

- 無。之後若 HelpDesk 輪替 proxy key，這兩個 override 要同步換並 `daemon-reload` + restart。
