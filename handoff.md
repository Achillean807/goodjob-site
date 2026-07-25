> **2026-07-26 01:27 最新交接：** 本檔以下內容保留為 PostgreSQL 災難護欄歷史紀錄；目前 production 已完成官方 CI 色票／方格紋、相簿與詳情 CI、四類服務頁各 4 案例、完整設計字標 topbar 與首頁兩行文案。最新狀態請先讀 [`.planning/.continue-here.md`](.planning/.continue-here.md) 與 [`.planning/HANDOFF.json`](.planning/HANDOFF.json)。

# 部署清空 PostgreSQL 災難護欄 — Handoff

**日期：** 2026-05-06
**Commit：** `8719878 fix(deploy): 加入多層護欄防止部署清空 PostgreSQL runtime`
**Reviewer：** OpenAI Codex
**Author：** 哈雷酱（Claude Opus 4.7）+ 村長

## 1. 任務目的

過去 3 次部署誤覆蓋 PostgreSQL（相簿/文案被清空）。本次工作：
- 找出根因
- 加入多層護欄
- 把 systemd / kernel 層的 sleep 漏洞一併補完
- 留下災難復原 runbook

## 2. 根因鑑定（過去 3 次災難最可能的成因）

### 主因 — 三條鏈路任一發生即清空 runtime

1. **`data/articles.json` 被 git 追蹤** — `scp -r *` / 主機端 `git pull` 把 master 上過時的 JSON 蓋過主機 runtime 副本
2. **PostgreSQL 環境變數失效時靜默 fallback SQLite** — `_using_postgres()` 偵測 `GOODJOB_DATABASE_URL` 為空就走 SQLite 路徑，systemd override 失效時無聲無息切到 SQLite
3. **SQLite 為空時自動從 JSON seed** — `_init_db()` 看到 `COUNT == 0` 就 `_replace_articles(JSON)`，把過時 articles.json 灌進去

→ 這三條鏈路同時湊齊就是災難現場。

### 副因 — 主機 suspend 喚醒失敗（5/6 最近一次的引爆點）

5/6 19:06:55 GNOME 透過 `systemd-logind` 直接呼叫 `systemd-suspend.service`（**繞過已 mask 的 `sleep.target`**）。SATA controller resume 失敗（`ata4: failed to resume link (SControl 30)`）導致系統卡死，村長在 19:12 reboot。

漏洞點：
- `sleep.target` mask 不夠 — `systemd-suspend.service` 直接被 logind 叫起來
- GNOME `lid-close-ac-action='suspend'`、`sleep-inactive-battery-type='suspend'` 兩個 settings 還在 default

## 3. 變更清單（commit `8719878`）

| 檔案 | 變更 | 為什麼 |
|---|---|---|
| `.gitignore` | +`data/articles.json`、+`data/wp_texts.json`、+`backups/`、+`analysis_tmp/` | 阻止 runtime / 備份檔被 git 散播 |
| `data/articles.json` | `git rm --cached`（保留本機檔） | repo 不再有舊副本可被 `git pull` / `scp -r` 覆蓋主機 |
| `data/wp_texts.json` | `git rm --cached`（保留本機檔） | 同上，純歷史備份 |
| `server.py` `main()` 開頭 | 加 fail-fast：`GOODJOB_DATABASE_URL` 沒設且未顯式 `GOODJOB_ALLOW_SQLITE=1` 即 exit 1 | 禁止靜默 fallback SQLite |
| `server.py` `_init_db()` SQLite 分支 | SQLite 從 JSON seed 預設禁用，需 `GOODJOB_ALLOW_JSON_SEED=1` | 雙重保險，即使 B 護欄被繞過也擋下 |
| `server.py` argparse | 新增 `--force-replace` flag | migrate 動作的安全閥 |
| `server.py` `main()` migrate 分支 | 偵測目標 PG 已有資料時，未帶 `--force-replace` 即 exit 1 | 防誤跑 `--migrate-runtime-to-postgres` 蒸發線上資料 |
| `server.py` 新增 `_pg_count_articles()` helper | 給防呆檢查用；psycopg2 import 失敗會 raise（不 swallow） | 避免「環境壞掉」被誤判成「target 是空」而繞過防呆 |
| `docs/村山良作-部署資訊清單.md` | 補上新環境變數、新護欄行為、`.gitignore` 兩層說明 | 同步維運文件 |
| `docs/村山良作-部署護欄與復原-20260506.md` | 新增（138 行） | 災難復原 runbook、驗證 checklist、回滾步驟 |

## 4. 部署狀態（已生效）

| 動作 | 狀態 |
|---|---|
| 本地 commit `8719878` | ✅ |
| `git archive` 打包 HEAD（自動套 `.gitattributes export-ignore`）| ✅ tar 內無 `data/` 任何檔案 |
| `scp` + `tar -xf /tmp/goodjob-site-deploy.tar -C /srv/weddingwish/goodjob-sit/` | ✅ |
| 主機 `server.py` 部署前備份至 `server.py.before_8719878` | ✅ 秒回滾保險 |
| `sudo systemctl restart murayama-goodjob.service` | ✅ |
| 線上驗證 | HTTP 200、`articles count: 49`、`DB backend : PostgreSQL` |

## 5. Suspend 補強（已生效）

| 動作 | 狀態 |
|---|---|
| `systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target` | ✅（先前已 mask，本次重 mask 確認）|
| `systemctl mask systemd-suspend.service systemd-hibernate.service systemd-hybrid-sleep.service systemd-suspend-then-hibernate.service` | ✅ 新做 — 補 sleep.target mask 漏洞 |
| GNOME `lid-close-ac-action` / `lid-close-battery-action` → `nothing` | ✅ |
| GNOME `sleep-inactive-ac-type` / `sleep-inactive-battery-type` → `nothing` | ✅ |
| GNOME `idle-delay` → `0`（永不 idle）| ✅ |

## 6. 相簿圖片數差異追查（已結案 — 非災難）

過程中發現兩個相簿圖片數比 `docs/村山良作-部署資訊清單.md` 寫的 2026-05-05 基準少。比對 5/5 與 5/6 兩份 PG 備份：

| 相簿 | 5/5 18:45 (PG dump) | 5/6 19:15 (PG dump) | 差 | updated_at |
|---|---|---|---|---|
| `nccu-emba-41-party` | 42 | 20 | **-22** | 2026-05-06T12:49:49 |
| `nccu-emba-42-graduation` | 21 | 12 | **-9** | 2026-05-06T14:07:03 |
| `gd-home-sweet-home` | 8 | 8 | 0 | 2026-05-06T13:40:39 |

兩個變少的相簿 `updated_at` 都是 5/6 今天，且 5/5 數字跟 docs 基準完全一致 → **是村長今天主動在後台編輯，不是部署清空**。已向村長報告。

## 7. 已發現但未修的問題（請村長定奪）

### 🟡 host-gdrive-backup 漏備份 `goodjob_site` 資料庫

`/srv/raid1/backups/postgresql/backup.sh` 只 `pg_dump weddingwish_v2`：

```bash
sudo -u postgres pg_dump weddingwish_v2 | gzip > "${BACKUP_DIR}/pg_${DATE}.sql.gz"
```

→ `goodjob_site` 完全沒進入每日 Google Drive 備份鏈路。如果 `goodjob_site` 被刪／毀，沒有 host-gdrive-backup 可救。修法：在 backup.sh 多加一行：

```bash
sudo -u postgres pg_dump goodjob_site | gzip > "${BACKUP_DIR}/pg_goodjob_${DATE}.sql.gz"
```

未動，等村長批准。

## 8. 給 Codex 審查的重點

1. **`server.py` 的 fail-fast 順序**：`--migrate-runtime-to-postgres` 分支會主動設 `GOODJOB_ALLOW_SQLITE=1` 跟 `GOODJOB_ALLOW_JSON_SEED=1` 然後 `return`，所以後面的 fail-fast 不會擋它。請確認這個順序對所有合法路徑都通。
2. **`_pg_count_articles()` 的 `except RuntimeError: raise`** — 用 `RuntimeError` 是因為 `_pg_connect()` 在 psycopg2 缺失時 raise `RuntimeError`。如果未來 `_pg_connect()` 改用其他例外類別，這條判斷會失效。
3. **`.gitattributes` 跟 `.gitignore` 是兩層獨立護欄** — `.gitattributes export-ignore` 只擋 `git archive`，`.gitignore` 擋 git tracking。不是擇一，要兩層都在。
4. **本機開發環境**現在需要顯式 `GOODJOB_ALLOW_SQLITE=1` 才能跑 SQLite，需要 `GOODJOB_ALLOW_JSON_SEED=1` 才能首次 seed。可在 `README` 或啟動 wrapper 補一段說明。
5. **本次 commit 沒動到 `--migrate-runtime-to-postgres` 從 SQLite source 的能力** — 該 flag 仍然會跑 `_init_db()` 走 SQLite + JSON seed（被自動 enable 的 env 解鎖）→ `_export_runtime_data()` → 灌 PG。但建議未來 deprecate，改成直接 `pg_restore` 從 dump 還原。

## 9. 後續行動（村長）

- [ ] 看完 handoff，決定要不要：
  - 修 `host-gdrive-backup` 把 `goodjob_site` 加進備份
  - 處理新發現的 `goodjob_site_test` 資料庫（看清單時瞄到，用途不明）
- [ ] 5/6 在後台編輯 `nccu-emba-41-party` 跟 `nccu-emba-42-graduation` 是不是預期的？如果不是（例如手滑刪錯），可從 `goodjob_site.pre_manual_copy_20260505_184526.sql` 還原這兩個相簿的圖片清單

## 10. 還原指南（萬一新護欄反而擋住合法操作）

回滾本次部署：

```bash
ssh achilean@100.102.51.64 "sudo cp /srv/weddingwish/goodjob-sit/server.py.before_8719878 /srv/weddingwish/goodjob-sit/server.py && sudo systemctl restart murayama-goodjob.service"
```

回滾 commit：

```bash
git revert 8719878
```

回滾 sleep mask：

```bash
ssh achilean@100.102.51.64 "sudo systemctl unmask systemd-suspend.service systemd-hibernate.service systemd-hybrid-sleep.service systemd-suspend-then-hibernate.service"
```
