# Phase 4: P2-A AI Citation Baseline + llms.txt + robots/WAF — Context

**Gathered:** 2026-05-14
**Status:** Ready for planning
**Source:** ROADMAP.md § Phase 4 + intel/requirements.md REQ-ai-citation-baseline / REQ-llms-txt-update / REQ-robots-waf-bot-allow + intel/decisions.md DEC-ai-crawler-allowlist / DEC-baseline-before-optimization / DEC-non-deterministic-disclaimer

---

<domain>
## Phase Boundary

**範疇：** 在 2-3 週內，建立 AEO/GEO 軌道的「測量地基」與「爬蟲入口」，具體交付：
1. **AI Citation Baseline 報告** — 4 平台（ChatGPT / Claude / Gemini / Perplexity）× 每平台 20-40 題 prompt，記錄品牌是否被提及、是否被引用、競品名單；產出 lost prompts 清單供 Phase 5 修補
2. **llms.txt 升格** — 補 Last-Updated 欄位、5 cluster 完整資訊（Phase 2 Plan 2.7.5 已補 pillar section，本 phase 補獎項頁 / 聯絡 / 月度更新機制）
3. **robots.txt + Cloudflare WAF 雙保險** — robots.txt 補 OAI-SearchBot / PerplexityBot 個別 Allow 段落 + Sitemap/LLMs-Txt 指向；WAF audit 確認 user-agent 與官方 IP 段未被擋

**不在範疇：**
- Lost prompts 修補答案型長文 → Phase 5（P2-B REQ-lost-prompts-answer-content）
- 比較頁 / 決策框架 → Phase 5（P2-B REQ-comparison-pages）
- 第三方媒體 / Google Business Profile → Phase 6（P3 REQ-awards-media-page / REQ-external-trust-signals）
- Phase 3 作品模板擴充 / FAQ 撰寫 → **Phase 3 並行**（server.py + PostgreSQL 路徑，本 phase 不碰）

**REQ 對應：**
1. `REQ-ai-citation-baseline` — 4 平台 × 20-40 題 + 每題紀錄 5 欄位 + lost prompts 清單
2. `REQ-llms-txt-update` — 5 cluster 條目 + 獎項頁 + 聯絡 + Last-Updated
3. `REQ-robots-waf-bot-allow` — robots.txt 三段落（OAI / Perplexity / general） + Cloudflare WAF audit

**對應 proposed 決策（本 phase 升格 LOCKED 候選）：**
- `DEC-ai-crawler-allowlist`（robots.txt + WAF 雙處）
- `DEC-baseline-before-optimization`（強制先建 baseline 才修內容）
- `DEC-non-deterministic-disclaimer`（KPI 第一次只建 baseline，不承諾引用率）

</domain>

<decisions>
## Implementation Decisions（待 GATE-4A/4B/4C 確認後升 LOCKED）

### GATE-4A：Prompt 組設計（待村長 review）

**規格基線：**
- 4 平台 × 每平台同一份 prompt 組（便於跨平台比較）
- 每平台 **20-40 題**（PRD 規定區間；本小姐建議首輪取下限 **20 題** = 5 cluster × 4 題，避免疲勞 + 控制 Plan 4.2 執行時數）
- Prompt 組 = 5 cluster × 4 題 × 4 平台 = **80 次測試**（首輪）
- 每 cluster 4 題分配（建議）：
  - **1 題泛問**（例：「台北有哪些品牌活動佈置團隊？」）
  - **1 題比較**（例：「品牌活動佈置如何選擇？」）
  - **1 題情境**（例：「公司尾牙想做魔法主題該找誰？」）
  - **1 題長尾**（例：「戶政事務所結婚登記專區佈置怎麼做？」）

**草擬 5 cluster × 4 題（**村長 review 後鎖定**，可改可加可刪）：**

| Cluster | 泛問 | 比較 | 情境 | 長尾 |
|---------|------|------|------|------|
| business-event | 台北品牌活動佈置公司有哪些推薦？ | 品牌活動佈置與展場設計差別？ | 新品發表會想做沉浸式現場，找誰？ | 汽車品牌新車發表會佈置案例 |
| party-spring-banquet | 春酒尾牙主題佈置公司推薦？ | 春酒尾牙找佈置公司 vs 場地內建？ | 想做復古港風的春酒主題，找誰？ | 100 人規模公司尾牙主題佈置預算？ |
| magic-academy | 魔法學院主題派對佈置誰做？ | 魔法主題派對 vs 一般生日派對佈置差別？ | 學校畢業典禮想做哈利波特風，找誰？ | 分院帽座位查詢工具哪裡可以用？ |
| civil-makeover | 戶政事務所空間改造案例 | 戶政空間改造找誰承包？ | 結婚登記專區想做夢幻拍照點，找誰？ | 台北信義戶政結婚登記怎麼預約佈置？ |
| wedding-tea-flower | 婚禮迎賓茶哪裡訂？ | 婚禮花果茶 vs 一般迎賓飲料差別？ | 婚禮想要客製化 LOGO 茶飲，找誰？ | 50 瓶起訂的婚禮迎賓花果茶推薦 |

**勘誤注意：** 上述 20 題草擬版**請村長逐題 review**，特別檢查：
- 是否反映真實業主搜尋意圖
- 是否會踩到競品名（避免變廣告測試）
- 是否避免「村山良作」品牌詞（baseline 要測「未指名情況下會不會被提及」）

### GATE-4B：測試協議文件（待村長確認）

提案測試協議規格：

| 項目 | 規格建議 |
|------|---------|
| **執行方式** | 人工執行（4 平台無統一 API；ChatGPT Plus / Claude Pro / Gemini Advanced / Perplexity Pro 訂閱已有） |
| **每題重複次數** | **3 次取多數**（AI 非決定性，單次結果不可靠） |
| **記錄欄位** | prompt 文字 / 平台 / 執行時間 / 是否提及「村山良作」/ 是否引用站內 URL（含 URL）/ 提到的競品名單（最多 3 個）/ 結果截圖路徑 |
| **截圖儲存** | `.planning/phases/04-p2a-ai-citation-baseline/evidence/screenshots/{platform}/{prompt-slug}-{run}.png` |
| **資料格式** | CSV（便於後續樞紐分析）+ markdown summary |
| **重複測試規則** | 同 prompt 不可 follow-up（每題開新 chat / 新 session）；同題 3 次 run 間隔 ≥ 1 小時避免快取 |
| **Lost prompts 判定** | 3 次 run 都未提及村山良作即為 lost prompt |

**Phase 4 預設採上述協議**，PLAN 4.2 內具體執行。

### GATE-4C：Cloudflare WAF audit（待 audit 後）

**audit checklist（本小姐先草擬，PLAN 4.5 執行）：**

1. **robots.txt 配置確認** —
   - 既有：`User-agent: *` + `Disallow: /admin/` + `Sitemap:` + `LLMs-Txt:`（Phase 1 已驗）
   - **新增段落：** `User-agent: OAI-SearchBot` + `Allow: /` + `Disallow: /quote/` + `Disallow: /admin/`
   - **新增段落：** `User-agent: PerplexityBot` + `Allow: /` + `Disallow: /quote/` + `Disallow: /admin/`
   - **保留：** GPTBot（OpenAI 訓練爬蟲）視政策決定 allow/disallow（建議 allow，與 search 一致）
2. **Cloudflare WAF Bot Fight Mode 檢查** —
   - 進 Cloudflare dashboard → Security → Bots → 確認 Bot Fight Mode 不擋 OAI-SearchBot / PerplexityBot / GPTBot
   - 若有自訂 firewall rule 擋 user-agent 含 "bot" → 加 exception
3. **Cloudflare WAF Managed Rules 檢查** —
   - 確認 AI Bot ruleset（若有訂閱）未誤擋 OAI / Perplexity 官方 IP
4. **驗證測試** —
   - `curl -A "OAI-SearchBot/1.0" https://goodjob.weddingwishlove.com/` → 200
   - `curl -A "PerplexityBot/1.0" https://goodjob.weddingwishlove.com/` → 200
   - `curl -A "GPTBot/1.0" https://goodjob.weddingwishlove.com/` → 200
   - Cloudflare logs 確認 3 個 UA 未被 challenge / block

### llms.txt 升級規格

**Phase 2 Plan 2.7.5 已補：** 「服務介紹 Pillar Pages」section（5 cluster URL + 描述）

**Phase 4 補：**
- `Last-Updated: 2026-XX-XX` 欄位（top of file，每月更新一次）
- `## 獎項與媒體` section（MUSE Design Awards 等，需向村長確認獎項清單）
- `## 聯絡` section（已部分有；補 LINE 官方帳號連結、回應時間）
- 月度更新機制：建議走 git commit 觸發（手動 / Cron skill）

</decisions>

<canonical_refs>
## Canonical References

### Phase 1-2 既有交付（基礎）

| 檔案 | 角色 |
|------|------|
| `robots.txt`（6 行） | 既有 `User-agent: *` + Disallow + Sitemap + LLMs-Txt |
| `llms.txt`（73 行） | Phase 2 Plan 2.7.5 已補 5 pillar pages section |
| 5 個 `/services/{slug}/index.html` | Phase 2 已上線，含 Service + Breadcrumb schema |

### 對應 ROADMAP 條目

- ROADMAP § Phase 4「P2-A AI Citation Baseline」
- ROADMAP success criteria（5 條）：
  1. 4 平台 × 20-40 prompts 測試完成
  2. lost-prompts 清單交付（含每題平台、競品名單）
  3. robots.txt 含 OAI-SearchBot / PerplexityBot 個別段落
  4. Cloudflare WAF audit 通過（不擋 AI bot UA + IP）
  5. llms.txt 含 5 cluster + Last-Updated 欄位 + 獎項頁 + 聯絡

### 外部資源

- ChatGPT Plus 訂閱（村長已有，需確認登入帳號）
- Claude Pro 訂閱（村長已有 — Claude Code 帳號）
- Gemini Advanced 訂閱（待確認）
- Perplexity Pro 訂閱（待確認）
- Cloudflare dashboard `dash.cloudflare.com`（憑證在 `~/.claude/.cf-env`）

</canonical_refs>

<specifics>
## Specifics

### Plan 切割建議（PLAN.md 細寫）

| Plan | 主題 | 主要動作 | 預估時數 | 並行 with Phase 3？ |
|------|------|---------|---------|---------------------|
| 4.0 | GATE 對齊 | GATE-4A prompt 組 review + GATE-4B 測試協議 + GATE-4C WAF checklist | 30 min（村長 review） | ✅ 完全獨立 |
| 4.1 | robots.txt 更新（OAI / Perplexity 段落） | 改 robots.txt + scp + smoke test | 1h | ✅ |
| 4.2 | AI Citation Baseline 測試執行（80 次 × 3 重複 = 240 次） | 人工跑 prompt + 截圖 + 填 CSV | 12-20h（最大工時項） | ✅ |
| 4.3 | Baseline 報告產出 | CSV → markdown summary + lost prompts 清單 | 3-4h | ✅ |
| 4.4 | llms.txt 升級（Last-Updated + 獎項 + 聯絡） | 改 llms.txt + 建立月度更新機制 | 1-2h | ✅ |
| 4.5 | Cloudflare WAF audit | 跑 audit checklist + 必要時改 firewall rule | 2-3h | ✅ |
| 4.6 | 部署 + 驗證 | robots.txt / llms.txt scp + curl smoke test + report commit | 1h | ✅ |

### Success Criteria 驗收清單

1. **4 平台 × 20-40 prompts 完成** → CSV 列數 ≥ 80（首輪 20 題 × 4 平台）× 3 重複 = 240 列
2. **Lost prompts 清單** → markdown `04-baseline-report.md §6` 列出未被提及村山良作的 prompts（含平台、競品）
3. **robots.txt 三段落** → `curl https://goodjob.weddingwishlove.com/robots.txt` 含 OAI-SearchBot + PerplexityBot 段落
4. **WAF audit 通過** → 4.5 audit checklist 全綠（3 個 UA `curl` 都 200）
5. **llms.txt 升級** → grep `Last-Updated` + `## 獎項` + 5 cluster URLs 完整

### 量化指標目標

| 指標 | Phase 2 結束 | Phase 4 結束目標 |
|------|--------------|-----------------|
| AI 平台 citation baseline | 0 baseline | **4 平台 × 20 prompts × 3 重複** |
| Lost prompts 清單 | 0 | **完整 markdown 報告** |
| robots.txt 段落數 | 1（`User-agent: *`） | **3**（+ OAI-SearchBot / PerplexityBot） |
| llms.txt section 數 | 7（已含 pillar pages） | **9**（+ 獎項 + Last-Updated） |
| WAF AI bot allowlist 驗證 | 未審 | **3 UA 全綠** |

### 預估時程

- **總工時：** 20-30h（Plan 4.2 是大頭，依村長執行節奏可拆 5 天 × 4h）
- **Calendar 預估：** 2-3 週（與 Phase 3 完全並行，不搶 server.py / PostgreSQL 路徑）
- **GATE-4A 對齊：** 預計 Phase 4 開工前村長逐題 review 20 題 prompt 組（30 min）
- **執行模型：** Plan 4.2 為人工密集（村長 / 本小姐輔助）；其餘 Plan 都可 Sonnet / codex 派發

### 風險與緩解

| 風險 | 緩解 |
|------|------|
| 4 平台訂閱不全（Gemini / Perplexity） | Plan 4.0 確認；缺平台改用 free tier（接受結果可能受限）或先測 3 平台 |
| AI 平台政策變動（搜尋結果結構變） | Plan 4.2 執行期間若遇變動，記錄 evidence/screenshots 並標註版本 |
| Cloudflare WAF 規則複雜（不確定哪條擋了 bot） | Plan 4.5 預留時數 + 必要時 escalate Cloudflare support |
| 村長無時間逐題 review 20 題 | Fallback：本小姐草擬 + 走 AskUserQuestion 批次確認，省 review 時間 |

</specifics>

<deferred>
## Deferred to Later Phases

| 項目 | 推遲到 | 原因 |
|------|--------|------|
| Lost prompts 修補答案型長文（≥ 4 篇） | Phase 5（P2-B REQ-lost-prompts-answer-content） | 依賴本 phase baseline 結果 |
| 比較頁（≥ 2 篇）/ 決策框架 | Phase 5（P2-B REQ-comparison-pages） | 依賴 baseline 反饋 |
| Baseline 第二輪重測（追蹤引用率變化） | Phase 5 / Phase 6 | DEC-baseline-before-optimization：第一次只建 baseline |
| 第三方媒體頁 / 獎項頁 | Phase 6（P3 REQ-awards-media-page） | 需要村長提供素材，本 phase llms.txt 先補連結即可 |
| Google Business Profile 驗證 | Phase 6（P3 REQ-external-trust-signals） | 需要村長配合驗證流程 |
| 週報 dashboard / Looker Studio | Phase 7（P3 REQ-weekly-report-dashboard） | 依賴 GA4 + GSC 累積數據 |
| 月度長尾內容（每月 2 篇） | Phase 7（P3 REQ-monthly-longtail-content） | 持續運營，本 phase 範疇外 |

</deferred>

---

*Phase: 04-p2a-ai-citation-baseline*
*Context written: 2026-05-14 21:39 GMT+8（compaction 後恢復進度）*
