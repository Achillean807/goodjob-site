# 方向性決策清單

> 由 `gsd-doc-synthesizer` 從本批匯入文件萃取。本檔僅蒐集 ADR 等級的決策；PRD 預設不產生 LOCKED 決策，下列項目為 PRD 內部隱含的「策略性方向」，狀態統一為 `proposed`，可在後續 ADR 文件中被升格或推翻。

---

## 來源彙整

| 文件 | 類型 | precedence | locked | 路徑 |
|------|------|------------|--------|------|
| 村山良作搜尋與 AI 引用能見度改善計畫 | PRD | 0 | false | docs/seo-aeo-improvement-plan-20260513.html |

---

## DEC-strategy-seo-before-aeo

- **標題：** 先修 SEO 技術基礎，再建立 AEO 引用機制
- **狀態：** proposed（PRD 提出，非 LOCKED）
- **範圍：** 90 天 SEO/AEO 路線圖整體排序
- **決策陳述：** 先做 P0 索引安全與技術基礎（sitemap、私有頁 noindex、支援頁 metadata/schema），再建立服務主題集群（P1），再針對 AI 引用做 baseline 與修補（P2），最後鋪設權威訊號（P3）。
- **理由：** SEO 與 AEO 互補；索引與可信度未到位，AEO 修補無法被 AI 引擎讀取／引用。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 一、執行摘要 主要策略

---

## DEC-pillar-structure-five-clusters

- **標題：** 以 5 大服務集群作為內容組織主軸
- **狀態：** proposed
- **範圍：** 內容資訊架構、URL 規劃、內鏈策略
- **決策陳述：** 建立 5 個 pillar 頁：品牌活動佈置、展場空間設計、春酒尾牙佈置、戶政空間改造、婚禮場景佈置；既有 29+ 件作品歸到對應 cluster。
- **建議路徑：**
  - `/services/brand-event-decoration/`
  - `/services/exhibition-space-design/`
  - `/services/year-end-party-decoration/`
  - `/services/civil-office-transformation/`
  - `/wedding-packages/`（既有）+ `/teabar.html`（既有）
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 四、內容集群與頁面規劃

---

## DEC-private-pages-noindex-policy

- **標題：** 私有頁採 robots disallow + X-Robots-Tag 雙保險
- **狀態：** proposed
- **範圍：** `/admin/`、`/quote/`
- **決策陳述：** `/quote/` 既有 X-Robots-Tag，仍保留；`/admin/` 補上 `X-Robots-Tag: noindex, nofollow, noarchive` 與 robots.txt disallow。
- **理由：** robots 不等於 noindex；需 response header 才能擋住已被連結的私有頁進入索引。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 二、現況發現「Robots / 私有頁」、§ 三 P0、§ 三 robots.txt 調整方向

---

## DEC-ai-crawler-allowlist

- **標題：** 明確允許 OAI-SearchBot 與 PerplexityBot 抓取公開內容
- **狀態：** proposed
- **範圍：** robots.txt、Cloudflare WAF
- **決策陳述：** robots.txt 列出 `OAI-SearchBot`、`PerplexityBot` 個別段落（Disallow `/quote/`、`/admin/`，Allow `/`），並確認 Cloudflare 沒有阻擋兩者；保留 `Sitemap` 與 `LLMs-Txt` 指向 production URL。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 三 robots.txt 調整方向

---

## DEC-baseline-before-optimization

- **標題：** AEO 強制先建立 baseline 才動內容
- **狀態：** proposed
- **範圍：** ChatGPT、Claude、Gemini、Perplexity 4 平台
- **決策陳述：** 每個平台跑 20-40 題 prompt 實測，記錄品牌是否被提及、是否被引用、競品是誰；依 lost prompts 決定內容修補優先序。
- **理由：** 沒有 baseline 無法量化改善；AI 引用具非決定性，需固定 prompt 組重測。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 三 P2、§ 五 Baseline prompt 組、§ 七 footer-note

---

## DEC-non-deterministic-disclaimer

- **標題：** AI 引用為非決定性，不承諾保證引用率
- **狀態：** proposed
- **範圍：** KPI 設定、對客戶／村長的承諾溝通
- **決策陳述：** AEO/GEO KPI 第一次只建 baseline，第二次起追蹤引用率與品牌提及率變化；不承諾「保證被引用」。
- **來源：** docs/seo-aeo-improvement-plan-20260513.html § 七 footer-note、§ 六 KPI AEO/GEO 列

---

## 待升格為 ADR 的候選項

下列 PRD 內主張屬於可能跨檔影響的方向性決策，建議於 P0 / P1 啟動前，由村長確認後寫成正式 ADR：

1. **DEC-pillar-structure-five-clusters** — 新建 4 個 `/services/*/` 路徑會對 server.py routing / sitemap 邏輯造成結構性影響。
2. **DEC-private-pages-noindex-policy** — server.py 需新增 `/admin/` 的 X-Robots-Tag 邏輯，屬於跨檔影響。
3. **DEC-ai-crawler-allowlist** — robots.txt 與 Cloudflare WAF 雙處修改，需有單一決策來源避免漂移。
