# GSC Export — goodjob.weddingwishlove.com 篩選版（6 個月）

**匯出時間：** 2026-05-14 02:25 GMT+8
**屬性：** `sc-domain:weddingwishlove.com`（Domain Property）
**篩選器：** 頁包含 `goodjob.weddingwishlove.com`
**日期範圍：** 前 6 個月（約 2025-11-12 ~ 2026-05-11）
**搜尋類型：** 網路

## 總體數據

| 指標 | 值 |
|------|----|
| 總點擊次數 | **0** |
| 曝光總數 | **21** |
| 平均點閱率 | 0% |
| 平均排序 | **14.9** |

## 資料量充足度評估

⚠️ **GATE-2C fallback 條件觸發**：goodjob 子網域 6 個月內僅 21 個曝光、0 個點擊，
不足以做 cannibalization 分析。屬於 PRD GATE-2C 列出的「站存在期不夠長」狀況。

## 查詢 CSV（goodjob 篩選版）— 完整內容

```csv
熱門查詢項目,點擊,曝光,點閱率,排名
迎賓茶,0,1,0%,20
囍茶,0,1,0%,46
```

## 網頁 CSV（goodjob 篩選版）— 完整內容

```csv
熱門網頁,點擊,曝光,點閱率,排名
https://goodjob.weddingwishlove.com/teabar.html,0,8,0%,31.75
https://goodjob.weddingwishlove.com/,0,5,0%,3
https://goodjob.weddingwishlove.com/works/zhongshan-civil,0,2,0%,4
https://goodjob.weddingwishlove.com/works/6031ac6a,0,1,0%,3
https://goodjob.weddingwishlove.com/works/1c45c415,0,1,0%,4
https://goodjob.weddingwishlove.com/works/59483d61,0,1,0%,5
https://goodjob.weddingwishlove.com/works/ee7a6a84,0,1,0%,6
https://goodjob.weddingwishlove.com/works/cxo-female-founders-club,0,1,0%,8
https://goodjob.weddingwishlove.com/works/48235c66,0,1,0%,9
```

## 裝置 CSV — 完整內容

```csv
裝置,點擊,曝光,點閱率,排名
行動裝置,0,1,0%,20
桌面,0,1,0%,46
```

## 觀察與洞見

1. **唯一有真實 query impression 的兩個詞**：「迎賓茶」與「囍茶」—— 對應 `teabar.html`
   - 「迎賓茶」排名 20，仍可推進到第一頁
   - 「囍茶」排名 46，需顯著優化
2. **首頁 `/` 排名 3 但只 5 曝光** — 表示品牌詞曝光低，需要外部訊號（Phase 6 處理）
3. **作品頁排名都在 top 10**（3-9 名）但每個都只有 1-2 曝光 — query 太長尾或太冷門
4. **`teabar.html` 是唯一有「中量級」曝光的非首頁**（8 個）— 可作為 Phase 2 pillar 「婚禮花果茶」cluster 的起點
5. **`/works/zhongshan-civil` 2 曝光** — 「中山戶政」query 有少量需求，配合 `civil` cluster

## Phase 2 GATE-2A 對應結論

依 PRD GATE-2C：「若 GSC 資料不足 3 個月（站存在期不夠長），改以『現有 URL 列表 ×
Bing/Yandex impression』做替代分析」。

本資料證實此 fallback 應啟動。`/gsd-plan-phase 2` 啟動時應在 CONTEXT.md 註明：
> GSC 6 個月 goodjob 子網域 baseline = 0 點擊 / 21 曝光 / 排名 14.9，
> cannibalization 分析使用 atelier domain 全域資料 + Bing/Yandex fallback。

## 配對檔案

下一步：取得**整個 sc-domain:weddingwishlove.com 6 個月資料**（不篩選），
用於 atelier vs goodjob 子網域 cannibalization 分析。
