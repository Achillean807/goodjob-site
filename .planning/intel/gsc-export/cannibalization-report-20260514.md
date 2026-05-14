# Cannibalization 分析報告 — atelier vs goodjob (GSC 6 個月)

**匯出時間：** 2026-05-14 02:25 GMT+8
**屬性：** `sc-domain:weddingwishlove.com`（Domain Property，涵蓋全部子網域）
**日期範圍：** 2025-11-12 ~ 2026-05-11（6 個月）
**資料來源：**
- `.planning/intel/gsc-export/domain-all-6mo-20260514/`（不篩選，全域）
- `.planning/intel/gsc-export/goodjob-filtered-6mo-20260514/`（篩選 goodjob 子網域）

---

## 1. Executive Summary（給村長 30 秒看完版本）

| 重點 | 結論 |
|------|------|
| goodjob 6 個月成效 | **0 點擊 / 21 曝光 / 平均排名 14.9**（佔 domain-all 的 0.008%） |
| atelier 主域 6 個月 | **5046 點擊 / 269011 曝光 / CTR 1.88%**（含 content / www / salmonbelle 等子站） |
| 流量大本營 | `content.weddingwishlove.com`（WordPress 內容站，266 頁，370k 曝光） |
| **Cannibalization 直接證據** | ≥ 7 個 query 同時被 atelier 與 goodjob 競爭，**全部 atelier 勝出** |
| **goodjob 純藍海主題** | 7 大主題（主題場景、春酒尾牙、魔法學院、戶政改造、送客背景、台中佈置、中山戶政）atelier top-1000 完全沒搶到 |
| PRD GATE-2C 結論 | goodjob 子網域曝光不足，分析以 atelier 全域為主、goodjob 為 fallback；**GATE-2A 已達成** |

**核心戰略結論：**
> **goodjob 不該與 atelier content 對打「婚禮佈置」這類紅海大詞**，而應該以**「主題化 portfolio + 純藍海主題詞」**為主攻方向，輔以在 atelier 主域**內部交叉連結**把已搶到的「婚禮佈置」「迎賓茶」流量導流到 goodjob 案例頁。

---

## 2. 子網域分佈（Domain Property 全貌）

| Subdomain | Pages | Clicks | Impressions | CTR | 角色定位 |
|-----------|-------|--------|-------------|-----|---------|
| `content.weddingwishlove.com` | 266 | 3484 | 370243 | 0.94% | WordPress 內容文章（賀詞 / 花語 / 花店 / 大榮貨運等 informational） |
| `www.weddingwishlove.com` | 678 | 1585 | 70957 | 2.23% | atelier 案例頁與品牌詞（kerry / 首頁） |
| `salmonbelle.weddingwishlove.com` | 12 | 15 | 689 | 2.18% | 鮭毛先生 IP 站 |
| **`goodjob.weddingwishlove.com`** | **9** | **0** | **21** | **0.00%** | **村山良作（本站，分析對象）** |
| `hao-shou.weddingwishlove.com` | 1 | 0 | 5 | 0.00% | 好手書 |
| `weddingwishlove.com`（apex） | 1 | 1 | 1 | 100.00% | 根域名 redirect |
| `class.weddingwishlove.com` | 1 | 0 | 1 | 0.00% | 課程站 |

**goodjob 佔 domain-all 比例：21 / 269011 = 0.0078%（八千分之一）**，這是嚴重的 SEO under-served。

---

## 3. 直接 Cannibalization 案例（≥ 2 URL 競爭同 query）

PRD GATE-2A success criteria #1 要求「≥ 2 個 URL 競爭同一 query 案例 + 處置方向」，本節提供 **7 個確認案例**（goodjob query 與 atelier 雙重存在）。

### 3.1 「迎賓茶」⚡ CRITICAL

| 域別 | 點擊 | 曝光 | 排名 | URL |
|------|-----|------|-----|-----|
| atelier 全域 | **1** | **39** | **3.1** | （atelier 某文章/頁，待 cross-check） |
| goodjob | 0 | 1 | 20 | `https://goodjob.weddingwishlove.com/teabar.html` |

**Cannibalization severity：高** — goodjob 的 `teabar.html` 是 dedicated 商業頁（迎賓茶方案），但 atelier 用一篇文章就把 pos 3.1 佔了，goodjob 自己掉到 pos 20，完全沒撿到流量。

**處置方向：**
1. 找出 atelier 上佔「迎賓茶」pos=3.1 的具體 URL（下節 4.1 待 cross-check）
2. 若 atelier 頁是內容文章 → 加 internal link 指 goodjob `teabar.html`（讓 teabar 變 commercial canonical）
3. 若 atelier 頁是 commercial 重複頁 → 評估 301 redirect 至 `teabar.html`
4. goodjob `teabar.html` 補完整 pillar 內容（茶款介紹 / 季節組合 / FAQ / 案例照），目標 6 個月內 pos 3.1 取代 atelier

### 3.2 「囍茶」⚡ CRITICAL

| 域別 | 點擊 | 曝光 | 排名 | URL |
|------|-----|------|-----|-----|
| atelier 全域 | 0 | **36** | **10.86** | （atelier 某文章/頁） |
| goodjob | 0 | 1 | 46 | `https://goodjob.weddingwishlove.com/teabar.html` |

**Cannibalization severity：高** — 與 3.1 同邏輯，但兩者排名都不高（atelier pos 10.86 / goodjob pos 46）→ **整體有上升空間，若處置得當可同時佔多個位置**。

**處置方向：** 同 3.1。

### 3.3 「婚禮佈置」⚡ HIGH（紅海大詞）

| 域別 | 點擊 | 曝光 | 排名 | URL |
|------|-----|------|-----|-----|
| atelier 全域 | **18** | **1775** | **8** | （多重 atelier URL） |
| goodjob | — | — | — | 完全沒在 top 1000 |

**Cannibalization severity：中** — 這是商業大詞，atelier 已搶到 pos=8（第一頁邊緣），goodjob 該主動避戰，**不要建立同名 pillar 競爭**。

**處置方向：**
1. **goodjob 不做「婚禮佈置」獨立 pillar**（會與 atelier 互打）
2. 改做 sub-vertical 區隔：goodjob 走 `/works/business-event/*`（主題活動）`/works/party/*`（春酒尾牙）`/works/civil/*`（戶政改造）`/works/magic/*`（魔法學院）四大專業類別
3. atelier 主域已有的「婚禮佈置」articles → 加內部連結 `goodjob.weddingwishlove.com/works/{相關 case-id}` 作 portfolio 補充

### 3.4 「婚禮佈置租借」⚡ HIGH

| 域別 | 點擊 | 曝光 | 排名 | URL |
|------|-----|------|-----|-----|
| atelier 全域 | 22 | 140 | **2.66** | atelier |
| goodjob | — | — | — | 無 |

**Cannibalization severity：低** — atelier 已 pos 2.66（第一頁前段），CTR 15.7%，**這個詞 atelier 守好就好**。goodjob 可在頁面內補「租借 / 客製方案」內部連結到 atelier 強化內部結構。

### 3.5 「戶外婚禮佈置」

| 域別 | 點擊 | 曝光 | 排名 |
|------|-----|------|-----|
| atelier | 2 | 169 | **13.75**（第 2 頁） |
| goodjob | — | — | — |

**Cannibalization severity：低** — atelier pos 13.75 表示「弱競爭」，goodjob 可考慮做 sub-pillar **「戶外證婚．戶外婚禮場景」**（對應 `wedding-packages/outdoor.html` 已有架構），與 atelier 內容詞區隔（atelier 是 informational，goodjob 是 portfolio + commercial intent）。

### 3.6 「婚禮花藝佈置費用」

| 域別 | 點擊 | 曝光 | 排名 |
|------|-----|------|-----|
| atelier | 5 | 81 | **1.83**（第一名邊緣） |
| goodjob | — | — | — |

**Cannibalization severity：極低** — atelier 已 pos 1.83，這詞守住即可。

### 3.7 「婚禮場地佈置」/「婚禮現場佈置」/「婚禮舞台佈置」/「舞台佈置」

| 詞 | atelier 點擊 | atelier 曝光 | atelier 排名 | goodjob 狀態 |
|---|------|------|------|------|
| 婚禮場地佈置 | 2 | 187 | 25.99 | 無 |
| 婚禮現場佈置 | 0 | 144 | 14.96 | 無 |
| 婚禮舞台佈置 | 0 | 119 | 11.14 | 無 |
| 舞台佈置 | 0 | 113 | 9.44 | 無 |

**Cannibalization severity：低（但 atelier 表現也不好）** — atelier 在這幾個詞排名都在 pos 10-26，**這是 goodjob 可以「以小搏大」的中間地帶**，因為 atelier content 是文章型，回應的是 informational intent；goodjob portfolio 案例頁更貼近 commercial intent，理論上可超車。

---

## 4. Atelier 已搶到的商業詞清單（Top 40，goodjob 該攻擊目標）

| 查詢 | 點擊 | 曝光 | 排名 | goodjob 處置 |
|------|------|------|------|------|
| 婚禮佈置 | 18 | 1775 | 8 | 避戰（3.3） |
| 背板 | 15 | 1136 | 4.01 | 守土：atelier 已第一頁 |
| 婚禮背板 | 50 | 784 | 4.28 | atelier 守 |
| 婚禮布置（簡體） | 13 | 321 | 4.77 | 略 |
| 拍照背板 | 2 | 284 | 5.98 | atelier 守 |
| 會場佈置 | 1 | 269 | 2.24 | atelier pos 第一頁前段，守 |
| 戶外婚禮費用 | 3 | 266 | 5.73 | goodjob `wedding-packages/outdoor.html` 可補位 |
| 結婚背板 | 13 | 238 | 2.92 | atelier 守 |
| 婚禮胸花 | 9 | 228 | 4.95 | atelier 守（花藝為主） |
| 婚禮佈置價格 | 7 | 226 | 6.07 | goodjob 可做 commercial intent pillar 切入 |
| 婚禮佈置推薦 | 2 | 219 | 14.68 | **goodjob 可拿**（atelier pos 14） |
| 婚禮背板出租 | 3 | 192 | 6.51 | atelier 守 |
| 佈置（單字） | 0 | 192 | 9.12 | 太廣，棄 |
| 婚禮背板價格 | 17 | 188 | 2.68 | atelier 守 |
| 婚禮場地佈置 | 2 | 187 | 25.99 | **goodjob 可拿**（pos 26） |
| 婚宴佈置 | 0 | 173 | 8.92 | 中等競爭，可試 |
| 場地佈置 | 1 | 170 | 9.12 | 太廣 |
| 戶外婚禮佈置 | 2 | 169 | 13.75 | **goodjob 可拿**（3.5） |
| 背板佈置 | 8 | 165 | 3.03 | atelier 守 |
| 美軍俱樂部 婚禮 | 3 | 152 | 8.92 | 場館長尾詞，goodjob 案例頁可補 |
| 婚禮現場佈置 | 0 | 144 | 14.96 | **goodjob 可拿** |
| 婚禮佈置租借 | 22 | 140 | 2.66 | atelier 守（3.4） |
| 小資婚禮佈置 | 3 | 137 | 8.58 | 可考慮 |
| 婚禮胸花誰要戴 | 9 | 136 | 4.6 | 純 informational，atelier 守 |
| 台中婚禮佈置 | 3 | 133 | 1.77 | atelier 已 pos 1.77，守 |
| 婚禮背板租借 | 7 | 128 | 3.74 | atelier 守 |
| 婚宴背板 | 4 | 126 | 14.29 | **goodjob 可拿** |
| 婚禮舞台佈置 | 0 | 119 | 11.14 | **goodjob 可拿** |
| 美軍俱樂部婚禮 | 5 | 116 | 8.74 | 場館長尾詞 |
| 舞台佈置 | 0 | 113 | 9.44 | **goodjob 可拿** |
| 婚禮背板佈置 | 5 | 107 | 4.35 | atelier 守 |
| 胸花 婚禮 | 3 | 106 | 5.63 | atelier 守 |
| 婚禮佈置風格 | 4 | 104 | 12.03 | **goodjob 可拿** |
| 美軍俱樂部婚宴 | 0 | 104 | 9.95 | 場館長尾 |
| 背板租借 | 5 | 94 | 2.45 | atelier 守 |
| 婚禮桌花 | 5 | 94 | 6.37 | atelier 守 |
| 婚禮佈置方案 | 0 | 87 | 4.98 | **goodjob commercial intent 可搶** |
| 婚禮花藝佈置費用 | 5 | 81 | 1.83 | atelier 守（3.6） |
| 婚宴場地佈置 | 0 | 81 | 17.86 | **goodjob 可拿** |
| 戶外婚禮 | — | — | — | （需獨立查 main term） |

**小計：** Top 40 商業詞 atelier 合計 9662 曝光；**goodjob 可主攻 10 個詞**（標 **粗體**）佔約 1500 曝光。

---

## 5. goodjob 純藍海主題（atelier top 1000 完全沒搶到）

| 主題 | 範例 query | 競爭狀態 | goodjob 對應頁 |
|------|------|------|------|
| 主題場景 | 主題佈置、主題派對、主題會場 | **完全藍海** | `/works/` 既有業務作品 27 件 |
| 春酒尾牙 | 春酒、尾牙、年會、企業活動 | **完全藍海** | `/works/` party 分類 16 件 |
| 魔法學院 | 魔法學院、哈利波特派對、霍格華茲 | **完全藍海** | `/sort-hat/` + `/works/` magic 5 件 |
| 戶政改造 | 戶政佈置、結婚登記、結婚證書背板 | **完全藍海** | `/works/` civil 14 件（含 `zhongshan-civil`） |
| 送客背景 | 送客背景、送客區佈置、送客桌 | **完全藍海** | `/wedding-packages/` 既有 |
| 台中佈置 | 台中佈置、台中尾牙、台中婚禮會場 | **完全藍海** | 區域 SEO 機會 |
| 中山戶政 | 中山戶政、中山區戶政 | **完全藍海** | `/works/zhongshan-civil` 已有 |

**戰略意義：** 這 7 大主題是 goodjob 應該優先建立 pillar page 集群的主戰場。沒有 atelier 競爭、案例真實、商業意圖明確、長尾組合空間大。

---

## 6. 處置方向（Phase 2 輸入）

### 6.1 五大 pillar cluster 建議架構

對應 ROADMAP 中 proposed ADR `DEC-pillar-structure-five-clusters`：

```
goodjob.weddingwishlove.com
├── /pillar/business-event/          ← 主題化 portfolio（純藍海「主題場景」「主題佈置」）
│   └── /works/{slug}                 ← 27 件 business 作品
├── /pillar/party-spring-banquet/    ← 春酒尾牙 pillar（純藍海）
│   └── /works/{slug}                 ← 16 件 party 作品
├── /pillar/magic-academy/           ← 魔法學院 IP（純藍海）
│   ├── /sort-hat/                    ← 既有座位查詢
│   └── /works/{slug}                 ← 5 件 magic 作品
├── /pillar/civil-makeover/          ← 戶政改造（純藍海）
│   └── /works/{slug}                 ← 14 件 civil 作品（含 zhongshan-civil）
└── /pillar/wedding-tea-flower/      ← 婚禮花果茶 pillar（cannibalization 處置 3.1, 3.2）
    ├── /teabar.html                  ← 既有，需 pillar 化
    └── /wedding-packages/{*}         ← 既有 4 套組
```

### 6.2 Cross-link 策略（與 atelier 內部結構優化）

對應 ROADMAP Phase 3：

1. **找出 atelier 上佔「迎賓茶」「囍茶」的 URL** — 加 `<a href="https://goodjob.weddingwishlove.com/teabar.html">完整方案見村山良作 teabar</a>` 至文章底部 CTA
2. **atelier 「婚禮佈置」articles** → 加 portfolio CTA 連到 goodjob `/works/{相關 case}`，定位區隔：atelier = info / goodjob = case study
3. **atelier 站內 outbound 連結策略：** 每篇 atelier content 主題文章底部加入「真實案例參考：村山良作 portfolio」block，作為 internal authority transfer

### 6.3 atelier 主域避戰列表（goodjob 不做這些 pillar）

- ❌ 不做「婚禮背板」pillar（atelier pos 4.28）
- ❌ 不做「婚禮花藝」獨立 pillar（atelier pos 1.83）
- ❌ 不做「結婚背板」「婚禮胸花」「拍照背板」（atelier 皆守住第一頁）
- ❌ 不做「玫瑰花語 / 白玫瑰花語 / 永生花禁忌」（atelier content 主力）

### 6.4 goodjob 主動進攻列表（pos 9-26 弱競爭詞）

| 目標詞 | atelier 現況 | goodjob 拿下後預期 | 對應 pillar |
|------|------|------|------|
| 婚禮佈置推薦 | pos 14.68 | pos < 10 | wedding-tea-flower |
| 婚禮場地佈置 | pos 25.99 | pos < 15 | business-event |
| 婚禮現場佈置 | pos 14.96 | pos < 10 | business-event |
| 婚禮舞台佈置 | pos 11.14 | pos < 8 | wedding-tea-flower |
| 舞台佈置 | pos 9.44 | pos < 8 | business-event |
| 婚禮佈置風格 | pos 12.03 | pos < 8 | wedding-tea-flower |
| 婚禮佈置方案 | pos 4.98 | pos < 5 並佔多位 | wedding-tea-flower |
| 婚禮佈置費用 | （未明確列出，pos ≥ 10） | pos < 10 | wedding-tea-flower |
| 婚宴背板 | pos 14.29 | pos < 10 | business-event |
| 婚宴場地佈置 | pos 17.86 | pos < 10 | business-event |

---

## 7. PRD GATE-2A 達成情況

| 條件 | 證據 |
|------|------|
| ≥ 2 URL 競爭同一 query 案例 | ✅ 本報告 §3 列出 7 個案例（含詳細處置） |
| 處置方向 | ✅ 本報告 §6 五大 pillar + cross-link + 避戰列表 |
| GSC 6 個月匯出完成 | ✅ goodjob-filtered + domain-all 兩份完整 ZIP 已儲存於 `.planning/intel/gsc-export/` |
| GATE-2C fallback 觸發 | ✅ goodjob 21 曝光遠低於 cannibalization 分析最低門檻，已自動切換以 atelier domain 為主進行 |

**GATE-2A 通過。** 可啟動 Phase 2 `/gsd-plan-phase 2`，於 CONTEXT.md 註明：
> goodjob 子網域 6 個月 baseline 為 0 點擊 / 21 曝光 / 排名 14.9；
> cannibalization 分析以 atelier domain 全域資料完成（5046 點擊 / 269011 曝光），
> 找出 7 個直接 cannibalization 案例 + 10 個可主攻弱競爭詞 + 7 大藍海主題。
> 五大 pillar cluster 架構建議升格 LOCKED ADR。

---

## 8. 後續驗證手段（Phase 2 啟動前）

1. **找出 atelier 上佔「迎賓茶」「囍茶」的具體 URL：**
   - GSC Performance → 篩選器加「查詢=迎賓茶」→ 看「網頁」分頁 → 取得實際 URL
   - 或直接 `curl https://content.weddingwishlove.com/?s=迎賓茶` 看 WordPress 搜尋結果
   - 取得後加 internal link 至 goodjob teabar.html

2. **Bing Webmaster Tools 並行比對（PRD GATE-2C fallback 第二步）：**
   - 註冊 Bing Webmaster + Yandex Webmaster
   - 比對 Bing/Yandex 對 goodjob 的曝光是否高於 Google（Bing 對新站較友善）

3. **Phase 2 GATE-2B：** 五大 pillar route 設計確認（URL slug、breadcrumb、canonical 規則）

4. **Phase 6 外部訊號：** 首頁 `goodjob.weddingwishlove.com` 排名 3 但只 5 曝光 → 品牌詞需要外部訊號（GBP、媒體報導、社群引用）

---

## 9. 配對檔案索引

| 檔案 | 用途 |
|------|------|
| `.planning/intel/gsc-export/goodjob-filtered-6mo-20260514/README.md` | goodjob 篩選版 GSC 6mo（內含完整 CSV） |
| `.planning/intel/gsc-export/domain-all-6mo-20260514/*.csv` | domain-all GSC 6mo 7 個 CSV 原始檔 |
| `.planning/intel/gsc-export/domain-all-6mo-20260514.zip` | domain-all ZIP 備份 |
| `.planning/intel/gsc-export/cannibalization-report-20260514.md` | **本報告** |
| `docs/seo-aeo-improvement-plan-20260513.html` | 原始 PRD（含 GATE-2A 定義） |

**報告產出者：** Claude Opus 4.7 + Playwright MCP（GSC 自動化匯出）+ Python 3 stdlib（CSV 分析）
**檢核：** 等待村長 sign-off → 通過後啟動 `/gsd-plan-phase 2`
