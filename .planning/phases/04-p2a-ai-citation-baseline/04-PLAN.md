# Phase 4: P2-A AI Citation Baseline + llms.txt + robots/WAF — Execution Plan

**Phase ID:** 4
**Planning written:** 2026-05-14 21:42 GMT+8
**Based on:** 04-CONTEXT.md（domain / decisions / specifics）
**Status:** Ready for execution（待 GATE-4A prompt 組村長 review 後啟動）
**並行性:** ✅ 完全與 Phase 3 並行（server.py / PostgreSQL 路徑無交集）

---

## 執行原則

- 每 plan 標 `autonomous=true / partial / false`
- Plan 4.2（人工跑 prompt）是工時最大頭（12-20h），可拆 5 天 × 4h 進行
- 4.0 GATE 解鎖 → 4.1-4.5 可有限度並行（4.1 改 robots → 4.2 跑 baseline；4.5 WAF audit 獨立）

---

## Plan 4.0 — GATE-4A/4B/4C 三項對齊（30 min）

**Type:** `autonomous=false`（純人工，村長決策）

**目標：** Prompt 組鎖定 + 測試協議鎖定 + WAF audit checklist 鎖定

**動作：**
1. Opus 透過 AskUserQuestion 呈現 04-CONTEXT.md GATE-4A 草擬的 5 cluster × 4 題（20 題）給村長
2. 村長逐 cluster review（可改可加可刪）
3. GATE-4B 測試協議（同題 3 次取多數 + 截圖 + CSV 欄位）村長 confirm
4. GATE-4C WAF audit checklist 村長 confirm
5. 鎖定後 commit `docs(planning): GATE-4A/4B/4C LOCKED` + 升 DEC-ai-crawler-allowlist / DEC-baseline-before-optimization / DEC-non-deterministic-disclaimer 至 LOCKED

**驗收：** 20 題 prompt 組寫入 `.planning/phases/04-p2a-ai-citation-baseline/prompts.md`（新檔）

**Blocker for:** 4.1, 4.2, 4.5

---

## Plan 4.1 — robots.txt 更新（OAI + Perplexity 段落）（1h）

**Type:** `autonomous=true`（codex 派發；spec 明確）

**前置：** 4.0 完成

**目標：** robots.txt 新增 OAI-SearchBot + PerplexityBot 個別 Allow 段落

**動作：**
1. 編輯 `robots.txt`：
   ```
   User-agent: *
   Disallow: /admin/
   Disallow: /quote/

   User-agent: OAI-SearchBot
   Allow: /
   Disallow: /admin/
   Disallow: /quote/

   User-agent: PerplexityBot
   Allow: /
   Disallow: /admin/
   Disallow: /quote/

   User-agent: GPTBot
   Allow: /
   Disallow: /admin/
   Disallow: /quote/

   Sitemap: https://goodjob.weddingwishlove.com/sitemap.xml
   LLMs-Txt: https://goodjob.weddingwishlove.com/llms.txt
   ```
2. scp robots.txt → ach-clawhome
3. Production curl 驗證：`curl https://goodjob.weddingwishlove.com/robots.txt` 含 3 個個別 UA 段落

**驗收：**
- robots.txt grep `User-agent: OAI-SearchBot` = 1
- robots.txt grep `User-agent: PerplexityBot` = 1
- robots.txt grep `User-agent: GPTBot` = 1
- production curl 結果一致

**Commit:** `feat(seo): robots.txt 新增 OAI/Perplexity/GPTBot 段落`

---

## Plan 4.2 — AI Citation Baseline 測試執行（12-20h）

**Type:** `autonomous=false`（純人工，村長或 Opus 操作 4 個 AI 平台 UI）

**前置：** 4.0 完成

**目標：** 4 平台 × 20 題 × 3 重複 = 240 次測試完成 + CSV 紀錄 + 截圖

**動作：**
1. 建立 `.planning/phases/04-p2a-ai-citation-baseline/evidence/baseline-runs.csv`（欄位：run_id / prompt_id / prompt_text / platform / run_round / executed_at / mentioned_murayama / cited_url / competitors / screenshot_path / notes）
2. 4 平台分批執行（建議：1 天 = 1 平台 × 20 題 × 3 round = 60 次，約 4h）：
   - **Day 1 ChatGPT**（Plus 訂閱 / GPT-4 / Web Search 啟用）
   - **Day 2 Claude**（Pro 訂閱 / Sonnet 4.6 + Web Search）
   - **Day 3 Gemini**（Advanced 訂閱 / 2.5 Pro + Web Grounding）
   - **Day 4 Perplexity**（Pro 訂閱）
3. 每次執行：
   - 新 chat / 新 session（避免 context 污染）
   - 截圖（包含 prompt + 完整回答）存 `evidence/screenshots/{platform}/{prompt-slug}-r{round}.png`
   - 填 CSV 一行
4. 結束後核對 CSV 列數 = 240（4 × 20 × 3）

**驗收：**
- CSV 240 列完整
- 截圖 240 張存對應路徑
- 0 列空白關鍵欄位

**Commit:** `data(baseline): AI Citation Baseline 240 次測試結果 CSV + 截圖`

**派發策略：**
- 此 plan **無法派 codex / Sonnet**（需要登入 ChatGPT / Claude / Gemini / Perplexity 訂閱帳號的人類操作）
- 建議村長親自跑 4 平台 × 5 題（90 min），剩 60 題派 Opus 用 Claude Pro 介面協助（Claude 平台本小姐可半自動）
- ChatGPT / Gemini / Perplexity 必須村長親自登入跑

---

## Plan 4.3 — Baseline 報告產出 + lost prompts 清單（3-4h）

**Type:** `autonomous=partial`（CSV → markdown 派 Sonnet，分析洞察 Opus）

**前置：** 4.2 完成

**目標：** 從 240 列 CSV 產出 markdown summary 報告 + lost prompts 清單

**動作：**
1. 派 Sonnet：讀 CSV → 依 cluster / platform 樞紐分析
2. 產出 `04-baseline-report.md`，章節：
   - §1 執行摘要（4 平台整體 mention rate / citation rate）
   - §2 各平台分析（ChatGPT / Claude / Gemini / Perplexity 各 mention rate）
   - §3 各 cluster 分析（5 cluster × 4 platform = 20 cell mention rate matrix）
   - §4 競品排行榜（依出現頻率排序）
   - §5 **Lost prompts 清單**（3 round 全部未提及村山良作的 prompt）
   - §6 Phase 5 修補建議（lost prompts 對應的內容缺口）
3. Opus review + 補寫 §1 / §6 insight 段
4. 報告附 baseline 圖表（簡單表格即可，CSV pivot 後手繪 markdown table）

**驗收：**
- `04-baseline-report.md` 6 章節齊全
- Lost prompts 清單列出具體 prompt + 平台
- §6 修補建議 ≥ 3 條可執行洞察

**Commit:** `docs(baseline): AI Citation Baseline 報告 + lost prompts 清單`

---

## Plan 4.4 — llms.txt 升級（Last-Updated + 獎項 + 月度機制）（1-2h）

**Type:** `autonomous=true`（codex 派發；spec 明確）

**前置：** 無依賴（可與 4.1 / 4.2 並行）

**目標：** llms.txt 補 Last-Updated 欄位 + 獎項頁 section + 月度更新機制（git hook 或 reminder）

**動作：**
1. 編輯 `llms.txt` 頂部加：
   ```
   Last-Updated: 2026-05-14
   ```
2. 新增 `## 獎項與媒體` section：
   - MUSE Design Awards（待村長提供具體年份 / 類別 / URL）
   - 其他媒體報導（待村長補）
3. 補 `## 聯絡` section（補 LINE 官方帳號連結、回應時間範圍）
4. 月度更新機制建議（不強制執行）：
   - 在 `.planning/STATE.md` 設 reminder「每月 1 號跑 `python3 scripts/update_llms_txt_date.py`」
   - 或建立 `scripts/update_llms_txt_date.py` 自動填當天日期
5. scp llms.txt → ach-clawhome

**驗收：**
- `curl https://goodjob.weddingwishlove.com/llms.txt` 含 Last-Updated + `## 獎項`
- 月度更新 script 或 reminder 存在

**Commit:** `feat(aeo): llms.txt 升格（Last-Updated + 獎項 + 聯絡 + 月度機制）`

---

## Plan 4.5 — Cloudflare WAF audit（2-3h）

**Type:** `autonomous=partial`（audit 步驟人工執行，部分驗證可派 codex 跑 curl）

**前置：** 4.1 完成（robots.txt 已更新，避免 WAF 改完 robots 還沒同步）

**目標：** 確認 Cloudflare WAF 不擋 OAI-SearchBot / PerplexityBot / GPTBot

**動作：**
1. 登 dash.cloudflare.com（憑證 `~/.claude/.cf-env`）→ weddingwishlove.com zone
2. **Security → Bots**：確認 Bot Fight Mode 是否啟用；若啟用 → 加 AI bot exception
3. **Security → WAF → Custom Rules**：grep 含 `User-Agent` 含 `bot` 的規則 → 加例外
4. **Security → WAF → Managed Rules**：確認 AI bot ruleset（如有）未誤擋
5. 派 Sonnet 跑驗證 curl：
   ```bash
   for ua in "OAI-SearchBot/1.0" "PerplexityBot/1.0" "GPTBot/1.0"; do
     curl -s -o /dev/null -w "%{http_code}\n" -A "$ua" https://goodjob.weddingwishlove.com/
   done
   ```
6. 若任一回 403 / 1010 → 找對應 WAF 規則修
7. Cloudflare Analytics → Security Events 確認最近 24h 3 個 UA 未被 challenge

**驗收：**
- 3 個 UA curl 全 200
- Cloudflare Analytics 24h 無對應 block / challenge 紀錄
- audit checklist 全綠記錄存 `04-waf-audit-report.md`

**Commit:** `chore(security): Cloudflare WAF audit 通過（OAI/Perplexity/GPTBot allowlist 驗證）`

---

## Plan 4.6 — Phase 4 部署 + 驗證（1h）

**Type:** `autonomous=true`

**前置：** 4.1, 4.4 deployable changes 完成

**目標：** robots.txt + llms.txt 上 production，跑最終驗證

**動作：**
1. 派 codex 把 robots.txt + llms.txt scp → ach-clawhome（若 4.1/4.4 已部署則跳過）
2. Cloudflare CDN purge robots.txt + llms.txt
3. Production smoke test：
   - `curl /robots.txt` 含 3 個 AI bot 段落 + Sitemap + LLMs-Txt
   - `curl /llms.txt` 含 Last-Updated + 5 cluster + 獎項 + 聯絡
4. 跑 GSC URL Inspection（手動）確認 robots.txt 變更被 Google 抓到

**驗收：**
- robots.txt / llms.txt production 內容與本機 1:1
- CDN cache purged
- 4 個 success criteria 對照表全綠

**Commit:** `chore(deploy): Phase 4 部署完成（robots / llms.txt 上 production）`

---

## Success Criteria 驗收對照（最終）

| # | 條件 | 驗收方式 |
|---|------|---------|
| 1 | 4 平台 × 20-40 prompts 完成 | CSV ≥ 240 列（首輪 20 題） |
| 2 | Lost prompts 清單交付 | 04-baseline-report.md §5 |
| 3 | robots.txt 含 OAI/Perplexity 段落 | curl production grep 通過 |
| 4 | Cloudflare WAF audit 通過 | 3 UA curl 全 200 + Analytics 24h 無 block |
| 5 | llms.txt 含 5 cluster + Last-Updated + 獎項 + 聯絡 | curl production grep 全綠 |

---

## 風險與緩解

| 風險 | 緩解 |
|------|------|
| GATE-4A 村長對 20 題草擬大改 | AskUserQuestion 拆 5 cluster 4 輪 review，避免一次性卡住 |
| Gemini / Perplexity 訂閱缺 | 改用 free tier 並標註結果可信度；或先測 3 平台 |
| AI 平台 UI 變動（截圖不一致） | 寬鬆截圖規則，文字內容能對應 prompt + answer 即可 |
| Cloudflare WAF audit 找不到 block 規則 | 預留 buffer 1h + 必要時 escalate Cloudflare support（憑證已有） |
| Plan 4.2 工時超預期 | 拆 5 天 × 4h；首日跑滿 1 平台後評估，必要時砍題目至 15 題（PRD 下限 20，可商量到 18-20 取中） |

---

## 並行性與 Phase 3 互動

| Phase 3 動作 | Phase 4 動作 | 衝突？ |
|--------------|-------------|--------|
| `ALTER TABLE articles` | （無 PG 動作） | ❌ 無衝突 |
| `server.py _serve_works_page` 改 | （無 server.py 動作） | ❌ 無衝突 |
| 5 pillar HTML 改 FAQ | （無 pillar HTML 動作） | ❌ 無衝突 |
| admin/* 改 6 區塊 | （無 admin 動作） | ❌ 無衝突 |
| - | `robots.txt` 改 | ❌ 無衝突 |
| - | `llms.txt` 改 | ❌ 無衝突 |
| - | Cloudflare WAF audit | ❌ 無衝突 |
| - | 4 平台 baseline 測試 | ❌ 純外部執行 |

**結論：** Phase 3 / 4 全程並行，部署可獨立 scp（不同檔案）。

---

*Phase: 04-p2a-ai-citation-baseline*
*PLAN written: 2026-05-14 21:42 GMT+8*
