# better_UI 迴圈 Round 3（2026-07-15）

## Round log

`第 3 輪|複查 5 項：4 落地 1 未生效(root cause: CSS 蓋掉 hidden)|新發現 2 件(P2)|修復 3 件(L0 親自)|business-event 導覽體檢通過`

## 複查結果

| 上輪修復 | 結果 |
|----------|------|
| 有聲自動播放 | ✓ mute=1 靜音自動播 |
| 選單四子項 | ✓ 全站統一（衍生 P2：工具列順序不一） |
| wedding-packages 破圖 | ✓ 移除 |
| wedding-packages 逃生口 | ✓ 村山良作首頁直達 |
| 幽靈播放按鈕 | ✗ **修了沒好**——JS hidden=true 生效，但 site.css `.detail-link{display:inline-flex}` 蓋掉 UA 的 `[hidden]{display:none}`（同檔 .detail-modal[hidden] 有 !important 防護，唯獨這顆沒有） |

## 修復（L0 親自，3 件）

- site.css:872 補 `.detail-link[hidden] { display: none !important; }`
- 工具列順序全站統一：婚禮花果茶→分類帽→合作流程（workflow/teabar/muse/sort-hat 四頁換序）
- hero「隱於村山，現於良作。」逗號後 `<br>` 強制斷行（原 1920 寬被硬拆成「現／於良作」）
- css 版號 → 20260715a（index/workflow/muse + server.py css_v）

## 驗收教訓（重要）

- **驗 hidden 要驗視覺，不驗 property**：上輪 Playwright 驗 `btn.hidden === true` 通過，
  但畫面上按鈕照樣顯示。正確驗法：`offsetParent !== null` + `getBoundingClientRect()` 寬高。
  property 為 true 與使用者看不到是兩回事。
- 本輪部署後視覺級複驗：幽靈按鈕 `{visible: False, w: 0, h: 0}` ✓

## 回歸計數

幽靈播放按鈕：第 1 次重開（修復未生效非回歸）。再被重開 1 次即觸發保險絲停止硬修。
