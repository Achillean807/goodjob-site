# better_UI 清償輪（2026-07-15）——「處理到好」收官

## Round log

```
重稽核輪|全新完整稽核 P1 2/P2 4(較首輪 6/8 收斂)|修 3 件(L0)|來電文案 36 篇清除(村長裁決)
清償輪  |複查 2 項：services 導覽過、hover 黑框未過(修法反轉)|順路 2 P2|修 5 件(codex 2/L0 3)|接受風險 1
```

## 清償輪明細

| 項 | 結果 |
|----|------|
| services 四頁全站導覽 | ✓ L1 複查四項全過（視覺一致/橫向跳轉/無遮擋/捲動不透字）|
| hover 預覽黑框 v1（延遲藏底圖）| ✗ 複查揪出方向錯誤：底圖從未被藏，真兇是 iframe z-index:1 疊在上方、外殼黑頁即蓋圖 |
| hover 黑框 v2（修法反轉）| iframe opacity:0 → onload+900ms 淡入；底圖常駐底層。headless 實測 onload 不 fire → 加 2.5s 保底 timer（冪等）。live 實測：+1s 透明+底圖在（黑框物理不可能）、+3.5s 淡入中 ✓ |
| services 版心（順路 P2）| .wrap 補進 services.css，left/right 80px 對稱 ✓ |
| is-active 肉眼難辨（順路 P2）| 加 Netflix 紅底線（var(--accent)），live 量測 2px solid rgb(229,9,20) ✓ |
| teabar/workflow/sort-hat 麵包屑 | 接受風險：工具列已高亮、頁標題明確、稽核實測未迷路、三套自帶樣式成本>收益 |

## 簽核狀態

- **L1 側**：services 導覽通過；hover v2 為複查後重修，由 L0 以 L1 同款方法
  （真實 hover＋逐時點 opacity/底圖量測）完成驗證——誠實註記：未再派獨立 L1 看 hover，
  但黑框成因（iframe 蓋底圖）已物理消除且有數據
- **回歸計數**：hover 黑框重開 1 次後由 v2 closed；再開即觸發保險絲

## 驗收方法教訓（新增）

- **修覆蓋層問題前先確認 z-index 疊層關係**——v1 對著被蓋住的底圖下功夫，白修一輪。
  「元素在不在」（property/DOM）與「用戶看不看得到」（疊層/opacity/尺寸）是三件事。
- headless 下 YouTube iframe onload 不可靠——任何依賴 onload 的視覺切換都要配保底 timer。

## 全站現況（村長四裁決後）

官網零統編（僅報價單，proposal skill §3 已寫詢問規則）、16+ 已刪、
迎賓花果茶全站更名、來電諮詢 36 篇清除、海運尾牙封面已換港口航站主視覺。
