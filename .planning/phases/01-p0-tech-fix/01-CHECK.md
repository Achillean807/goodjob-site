# Phase 1 PLAN Goal-Backward Check

**Checker：** gsd-plan-checker (Opus 親自驗)
**Date：** 2026-05-13
**Subject：** `.planning/phases/01-p0-tech-fix/01-PLAN.md`（5 plans）
**Phase Goal：** 7 天內完成索引安全與技術基礎修補，讓 Google 與 AI crawler 都能正確抓取、正確排除私有頁。

---

## 1. Overall Verdict

**~~NEEDS-REVISION~~ → PASS-AFTER-REVISION**（2026-05-13 23:32 GMT+8 Opus 親自修正並 spot-check 全綠）

| 原問題 | 修法 | Spot-check 結果 |
|--------|------|----------------|
| 🔴 Blocker #1 SQL 欄位名 | L513-528 / L421 改為 `featured_order` / `hero_image` / `featured = 1` / `r["..."]` dict 取值，與 server.py L227-243 + L406-408 對齊 | `grep '"featuredOrder"' 01-PLAN.md` → 0 命中 ✅ |
| ⚠️ Warning #2 teabar FAQPage | L314 加 4 題 teabar 專屬 FAQ schema（客製工期 / 最低訂量 / 保冰配送 / 三口味差異），含「答案必須在頁面可見」約束 | `grep -c 'FAQPage' 01-PLAN.md` → 2 ✅ |
| ⚠️ Warning #3 sitemap 數歧義 | L92 / L605 統一為 ≥ **69**，列出 7 個靜態頁 + 補 for-loop 驗證命令 | `grep '≥ \*\*69\*\*' 01-PLAN.md` → 2 命中 ✅ |
| ⚠️ Warning #4 Rollback | 新增 `## Rollback Strategy` 章節含通用流程 + Per-Plan 回滾要點表 | `grep '## Rollback Strategy' 01-PLAN.md` → 1 命中 ✅ |

**最終結論：可進入 commit + execute 階段。**

---

## 1.1 原始驗證（保留紀錄）

**NEEDS-REVISION**（1 個 blocker、3 個 warning，其餘 PASS）

修掉 Critical Issue #1（SQL 欄位名拼字錯誤）即可進入執行階段；另外 3 個 warning 建議邊執行邊修，不阻塞 Phase 1 出貨。

---

## 2. Goal-Backward Score

| 維度 | 評分 | 一句話總結 |
|------|------|-----------|
| A. 目標回推完整性 | ✅ PASS | 5 條 REQ 全覆蓋、5 條 success criteria 全有對應 plan、無 orphan、無 dead code |
| B. 可量測驗收 | ✅ PASS | 5 個 plan 全部有可執行的 curl/grep 驗證命令與字數限制，B1-B5 全綠 |
| C. 技術可行性 | ❌ FAIL（1 blocker） | server.py 修改點全部存在；但 `_load_featured_articles` SQL 欄位名拼錯，部署即崩 |
| D. 風險與回滾 | ⚠️ WARN | 每個 plan 都有 Risks 段；但沒有明確 rollback strategy（git revert + cf purge 流程） |
| E. 執行順序 | ✅ PASS | 1.2 → 1.5 → 1.1 → 1.3 → 1.4 合理；衝突檢測表呈現得很乾淨 |
| F. 跨檔一致性 | ⚠️ WARN | REQ ID 全對齊；canonical_refs 提到 `_load_featured_articles` SSR pattern 與 PLAN 一致；但 PLAN 1.3 漏掉 CONTEXT 鎖死的 teabar FAQPage schema |

---

## 3. Critical Issues（必修才能進執行階段）

### 🔴 BLOCKER #1：Plan 1.5 `_load_featured_articles` SQL 欄位名拼字錯誤（部署即崩）

**檔案：** `01-PLAN.md` L513-516（PostgreSQL）與 L521-524（SQLite fallback）

**問題：** PLAN 寫的 SQL：
```sql
-- PostgreSQL
SELECT id, title, "heroImage" FROM articles
WHERE featured = true ORDER BY "featuredOrder" NULLS LAST, id LIMIT %s

-- SQLite
SELECT id, title, heroImage FROM articles
WHERE featured = 1 ORDER BY featuredOrder, id LIMIT ?
```

但 `server.py:227-243` 的真實 schema 與 `server.py:541-580` 的 `_pg_article_from_row` 顯示：
- PostgreSQL 欄位名是 **`featured_order`**（snake_case，L233）與 **`hero_image`**（L234），不是 `"featuredOrder"` / `"heroImage"`
- camelCase 是 **Python dict key**（dataclass-shaped 輸出，L576-578），不是 SQL column
- 雙引號 `"featuredOrder"` 在 PostgreSQL = case-sensitive identifier → 會 raise `column "featuredOrder" does not exist`

**影響：** Plan 1.5 部署當下首頁就 500，所有訪客（含 GSC crawler）拿到錯誤頁；首頁 SSR 反而比沒做更糟。

**修法：** 直接改用 snake_case 欄位 + 在 Python 端 rename 成 dict key：

```python
def _load_featured_articles(limit=6):
    try:
        if _using_postgres():
            with _pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'SELECT id, title, hero_image FROM articles '
                        'WHERE featured = 1 ORDER BY featured_order NULLS LAST, row_index LIMIT %s',
                        (limit,)
                    )
                    return [{"id": r["id"], "title": r["title"], "heroImage": r["hero_image"]} for r in cur.fetchall()]
        with _db_connect() as conn:
            rows = conn.execute(
                "SELECT id, title, hero_image FROM articles WHERE featured = 1 ORDER BY featured_order, row_index LIMIT ?",
                (limit,)
            ).fetchall()
            return [{"id": r["id"], "title": r["title"], "heroImage": r["hero_image"]} for r in rows]
    except Exception:
        return []
```

注意點：
1. `featured` 是 INTEGER 0/1（不是 boolean true/false），condition 用 `featured = 1`
2. row 結構是 `cur.fetchall()` 用 `RealDictCursor`，所以 `r["hero_image"]` 用 dict 取（不是 tuple `r[0]`）
3. PostgreSQL 與 SQLite 結構欄位名完全一致（snake_case），不用兩套查詢

---

## 4. Recommended Revisions（不阻塞執行）

### ⚠️ WARNING #2：Plan 1.3 漏實作 CONTEXT 鎖死的 teabar FAQPage schema

**檔案：** `01-PLAN.md` L314 vs `01-CONTEXT.md` L66

CONTEXT L66 LOCKED：「`teabar`：`Product` + `Offer` + `FAQPage`（保留既有 4 題或新加）+ `BreadcrumbList`」

但 PLAN L314 寫：「（若村長批准 4 題 FAQPage schema，可直接套用首頁 FAQPage 模板，**但先不加避免重複內容污染**）」

這違反 CONTEXT 的 LOCKED 決策。Plan 不能單方面降級 LOCKED 決策成 deferred。

**修法：** Plan 1.3.B 加 teabar FAQPage schema，但**問題答案要在頁面可見文字內存在**（Rich Results Test 規則），且避免與首頁 4 題完全重複 — 改成 teabar 專屬 4 題（如「客製 LOGO 多久交件」、「最低訂量為什麼是 50 瓶」、「保冰配送怎麼運作」、「三種口味差異」）。

### ⚠️ WARNING #3：Plan 1.1 sitemap URL 期望數有歧義

**檔案：** `01-PLAN.md` L77 vs L92

- L77（Verification）寫「預期：≥ 69（62 篇 works + 7 個靜態頁）」
- L92（Acceptance Criteria）寫「`curl .../sitemap.xml | grep -c '<loc>'` ≥ 62」

兩者差 7。建議 Acceptance 也改成 ≥ 69 並列出 7 個靜態頁清單（避免哪天 articles 表縮減作品數時，「≥ 62」會誤通過驗收）。

另外 L75 grep 用 `<loc>` 但 L92 寫 `<url>`（檢查命令的兩個版本前後不一）。實際 sitemap 一個 `<url>` 內含一個 `<loc>`，grep 哪個都行但要統一。

### ⚠️ WARNING #4：缺乏 rollback strategy

5 個 plan 都有 Risks 段但都沒寫如何回滾。建議在 PLAN 結尾加 `## Rollback`：

```markdown
## Rollback

若某 plan 部署後驗證 fail：
1. `git revert <commit>` → push
2. scp 回滾後的 server.py / robots.txt → restart service
3. `pwsh scripts/cf-purge.ps1 -Paths "/sitemap.xml,/robots.txt,/,/index.html"`
4. 驗證生產站恢復前一版行為（含 `/quote/` 與公開頁不受影響）

特別注意：
- Plan 1.5 SSR 若崩 → 首頁回到「靜態 index.html + SPA 渲染」，不影響其他頁
- Plan 1.2 admin noindex 若誤擋公開頁 → 移除 `_is_admin_path` 分支即可
```

---

## 5. Strengths（這幾項做得好，不用動）

1. **Plan 1.2 unquote bug awareness（R1.2.1）** — 預料到 `%2e%2e` URL escape 攻擊面，且用 `startswith("/admin/")` 含尾斜線可防 `/admin-something/` false positive，這個 threat-model 等級的細節很罕見。
2. **Plan 1.2 regression check 完整** — Verification 命令 5 含 `/quote/` 仍正常、命令 6 含公開頁不應有 X-Robots-Tag，這兩條 regression check 是 SEO header bug 的經典翻車點，PLAN 提前 cover 了。
3. **Plan 1.4 8 URL 從 DB 動態取得** — 用 `psql -d goodjob_site -t -c "SELECT id FROM articles WHERE featured = true ORDER BY \"featuredOrder\" LIMIT 5;"`（雖然此處 `"featuredOrder"` 同樣有 #1 blocker 的拼字問題 — psql 一執行就 error），但概念上「從生產 DB 動態取 ID 而非寫死」這個設計避免了之後 featured 變動後 plan 過期的問題。**注意：修 #1 時這條 SQL 也要一起改成 `ORDER BY featured_order`。**
4. **Plan 1.5 SSR 三層 fallback（R1.5.1-R1.5.3）** — placeholder 不見、DB 連線失敗、SSR 區塊與 SPA 視覺重複，三種失敗模式都有 graceful degradation，且明確指出視覺優化留給後續 phase（合理 deferred）。
5. **執行順序的論證** — L21 「1.2 → 1.5 → 1.1（依賴 1.5 的 SSR fallback 不影響 sitemap）→ 1.3 → 1.4」每一步都有依賴解釋，不是憑感覺排。
6. **CONTEXT/PLAN/REQUIREMENTS 三方 REQ ID 拼字完全一致** — F1 / F2 全綠（除了 #2 的 teabar FAQPage 漏實作）。

---

## 6. Final Decision

**進入執行階段前必修 1 條（Blocker #1）**：

1. 修正 Plan 1.5 SQL 欄位名：`"featuredOrder"` → `featured_order`，`"heroImage"` → `hero_image`，`featured = true` → `featured = 1`（INTEGER schema）；同步修 Plan 1.4 Task 1 的 psql 指令。

**強烈建議併修 2 條（Warning #2, #3）**：

2. Plan 1.3.B 加 teabar FAQPage schema（CONTEXT LOCKED 決策不可降級）。
3. Plan 1.1 統一 sitemap 驗收 URL 數為 ≥ 69 並列出 7 個靜態頁清單。

**可選（Warning #4）**：補 `## Rollback` 段。

---

## 7. Recheck Plan

修完後（特別是 #1 SQL bug），不需要重跑全部 dimension；只需 spot-check：
- Plan 1.5 修改後 SQL 欄位名 → `grep -E 'featured_order|hero_image' 01-PLAN.md` 確認 snake_case
- Plan 1.4 Task 1 同步 → `grep '"featuredOrder"' 01-PLAN.md` 應該 0 結果
- Plan 1.3 teabar FAQPage → `grep -A 5 'FAQPage' 01-PLAN.md` 應該看到 4 題結構

通過即可 `/gsd-execute-phase 1`。
