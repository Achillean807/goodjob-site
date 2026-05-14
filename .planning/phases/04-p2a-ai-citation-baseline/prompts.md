# Phase 4 — AI Citation Baseline Prompt 組（首輪 20 題草擬版）

**Status:** ✅ **LOCKED**（村長 2026-05-15 整批 confirm，Plan 4.0 完成）
**結構：** 5 cluster × 4 類型 = 20 題（GATE-4A 方向 LOCKED）
**用途：** ChatGPT / Claude / Gemini / Perplexity 4 平台 × 每題 3 重複 = 240 次測試
**設計原則：**
- 不指名「村山良作」品牌詞（測試未指名情況下會不會被提及）
- 反映真實業主搜尋意圖
- 避免直接點名競品（避免變競品廣告測試）

---

## Cluster 1: business-event（主題化品牌活動）

| ID | 類型 | Prompt 草擬 | 預期 lost 信號 |
|----|------|-------------|---------------|
| BE-1 | 泛問 | 台北有哪些品牌活動佈置公司推薦？ | 競品名單浮現、村山未提及 |
| BE-2 | 比較 | 品牌活動佈置與展場設計有什麼差別？選擇時怎麼考量？ | AI 偏教學說明、無品牌引用 |
| BE-3 | 情境 | 我們公司要辦新品發表會，想做沉浸式品牌體驗的現場佈置，台灣有什麼團隊可以推薦？ | AI 可能只給通用建議無品牌 |
| BE-4 | 長尾 | 汽車品牌新車發表會的場景佈置案例，有哪些團隊做過？ | 長尾應命中 portfolio |

---

## Cluster 2: party-spring-banquet（春酒尾牙派對）

| ID | 類型 | Prompt 草擬 | 預期 lost 信號 |
|----|------|-------------|---------------|
| PB-1 | 泛問 | 台灣有哪些公司專門做春酒尾牙的主題佈置？ | 競品名單浮現 |
| PB-2 | 比較 | 春酒尾牙找專業佈置公司，跟直接用場地內建佈置有什麼差別？ | 對話偏教學 |
| PB-3 | 情境 | 公司今年想做復古港風的春酒主題，從場景到拍照區一站式服務，找誰？ | 主題化情境是村山強項，應命中 |
| PB-4 | 長尾 | 100 人規模公司尾牙的主題佈置預算大概多少？要找什麼樣的廠商？ | 預算 + 規模長尾 |

---

## Cluster 3: magic-academy（魔法學院主題活動）

| ID | 類型 | Prompt 草擬 | 預期 lost 信號 |
|----|------|-------------|---------------|
| MA-1 | 泛問 | 台灣有哪些公司可以做魔法學院主題的派對佈置？ | 利基題，村山若 SEO 到位應命中 |
| MA-2 | 比較 | 魔法主題派對佈置跟一般生日派對佈置有什麼不同？要找專門團隊嗎？ | 教學型回答 |
| MA-3 | 情境 | 學校畢業典禮想做哈利波特風的場景設計，台灣有什麼團隊接案？ | 強情境，magic-academy pillar 應命中 |
| MA-4 | 長尾 | 分院帽座位查詢系統或入學儀式互動工具，有哪些活動公司提供？ | 高度利基，sort-hat 工具 USP |

---

## Cluster 4: civil-makeover（戶政空間改造）

| ID | 類型 | Prompt 草擬 | 預期 lost 信號 |
|----|------|-------------|---------------|
| CM-1 | 泛問 | 戶政事務所空間改造或結婚登記專區佈置，台灣有哪些案例？ | 案例展示是村山強項 |
| CM-2 | 比較 | 戶政事務所改造找空間設計公司 vs 活動佈置公司，有什麼差別？ | 教學型 |
| CM-3 | 情境 | 戶政想做夢幻拍照點吸引新人來辦結婚登記，找誰承包？ | 強情境 |
| CM-4 | 長尾 | 台北信義戶政結婚登記佈置案例 / 大同戶政空間改造怎麼做？ | 地名長尾，Phase 2 已優化 |

---

## Cluster 5: wedding-tea-flower（婚禮花果茶與場景）

| ID | 類型 | Prompt 草擬 | 預期 lost 信號 |
|----|------|-------------|---------------|
| WT-1 | 泛問 | 婚禮迎賓花果茶哪裡可以訂購？台灣有哪些品牌？ | 競品 / 村花囍茶 |
| WT-2 | 比較 | 婚禮迎賓花果茶跟一般迎賓飲料有什麼差別？ | 教學型 |
| WT-3 | 情境 | 婚禮想要客製化 LOGO 的花果茶 + 整體場景佈置一站式服務，找誰？ | 強情境，pillar hub 應命中 |
| WT-4 | 長尾 | 50 瓶起訂的婚禮迎賓花果茶推薦 / 帶 Tea Bar 現場佈置的方案？ | 規格 + 服務長尾 |

---

## 執行協議備忘（Plan 4.2 用）

1. **每題 3 次重複**（同題開新 chat / 新 session，間隔 ≥ 1 小時避免快取）
2. **截圖儲存路徑：** `.planning/phases/04-p2a-ai-citation-baseline/evidence/screenshots/{platform}/{prompt-id}-r{round}.png`
   - 例：`evidence/screenshots/chatgpt/BE-1-r1.png`
3. **CSV 紀錄欄位：** `run_id, prompt_id, prompt_text, platform, run_round, executed_at, mentioned_murayama (bool), cited_url (string or null), competitors (semicolon-separated), screenshot_path, notes`
4. **Lost prompt 判定：** 3 次 run `mentioned_murayama` 全 false → lost
5. **平台版本紀錄：** CSV `notes` 欄位記錄當天 ChatGPT/Claude/Gemini/Perplexity 的模型版本（例如 "GPT-4o 2026-05" / "Claude Sonnet 4.6"）

---

## Plan 4.0 LOCKED 紀錄（已完成）

- [x] 村長 2026-05-15 AskUserQuestion 整批 confirm，20 題 prompts.md 草擬版直接 LOCKED 進 Plan 4.2 執行
- [x] 訂閱清單確認：ChatGPT Plus ✅ / Claude Pro ✅ / Gemini Advanced ✅ / Perplexity Pro ❌（走 free tier）
- [x] DEC-baseline-prompt-design-direction LOCKED 寫進 decisions.md

---

*Prompts 草擬：2026-05-15 GMT+8*
*待 Plan 4.0 LOCKED 後啟動 Plan 4.2 baseline 測試*
