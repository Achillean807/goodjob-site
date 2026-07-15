# better_UI 迴圈 Round 2（2026-07-15）

## Round log

`第 2 輪|複查 9 項：8 落地 1 部分|新發現 5 件(P0 0/P1 2/P2 3)|修復派工 5 件(codex)|資產債 +1`

## 複查結果（對 live）

| 上輪修復 | 結果 |
|----------|------|
| works 版頭破圖/裸文字 | ✓ 消失（logo naturalWidth 1351，樣式與首頁一致） |
| works 無 LINE 入口 | ✓ 消失（頁尾 CTA + 浮動鈕） |
| modal 返回鍵離站 | ✓ 消失（實測 go_back()：關窗留頁） |
| teabar 全頁破圖 | ✓ 消失（23/23 正常） |
| 選單不一致 | ⚠ 部分（主選單統一；殘留：囍茶方案↔婚禮花果茶雙名、合作流程一頁兩處、MUSE 缺分類帽、sort-hat 選單自成一格）|
| 魔法學院藏尾牙 | ✓ 消失（春酒尾牙區 20 卡含跨分類尾牙） |
| 預算線索埋深 | ✓ 可接受（FAQ 標題自明，一鍵展開） |
| pillar 術語 | ✓ 消失 |
| 回到影片語意 | ✓ 消失（但衍生 N1，見下） |

## 新發現與 L0 仲裁

| # | 問題 | 仲裁後機制definition | 級 |
|---|------|---------------------|----|
| N1 | 無影片案例顯示可點「▶ 播放影片」，點了沒反應 | **狀態殘留 bug**：hidden 邏輯只在 setDetailMode 內，openDetailModal 開窗不重設——非稽核員猜的「按鈕永遠顯示」，是上一案例殘留 | P1 |
| N2 | 開窗即有聲自動播放 | 證實：detail modal embed `autoplay=1&mute=0`（首頁 hero 是 mute=1，行為不一致）| P1 |
| N3 | wedding-packages 頁尾破圖 | 證實：images/1774609062333.png live 404、repo 無檔 → 移除 | P2 |
| N4 | wedding-packages 孤島（無村山識別、回首頁二跳） | 補「村山良作首頁」連結；品牌敘事（村花弄囍頁面本體）不動 | P2 |
| N5 | 選單殘留四子項 | 文字/連結級統一（teabar、sort-hat 不載 site.css，禁換結構）| P2 |

## 本輪資產債（記帳，非稽核項）

- `wedding-packages/images/` 整個目錄只存在主機、repo 沒有（同 murayama-logo 舊案）。
  收工時應把主機資產拉回版控。

## 修復（codex batch：6 spec）

N1 開窗重設按鈕三狀態、N2 mute=1、N5 四頁文字級統一（囍茶方案→婚禮花果茶、
去重合作流程、MUSE 補分類帽、sort-hat 換絕對連結）、N3 移除破圖 img、
N4 補回首頁連結、site.js ?v→20260715b。
