# better_UI 迴圈 Round 1（2026-07-15）

**畫像**：陳雅婷（福委會窗口，幫老闆比較尾牙佈置廠商）｜桌機 Chrome 1920×1080

## Round log

`第 1 輪|審查員發現 14 件(P0 0/P1 6/P2 8)|修復 9 件(codex 7/L0 親自 2)|待決 4 件+1 件掛下輪`

## L1 稽核摘要（首輪完整報告）

- 10 秒理解：低空飛過（靠副標+「64 件作品」+導覽「春酒尾牙」救回）
- 核心任務：①尾牙案例 ✅ ②可信度 ⚠️ ③比較表資訊 ⚠️ ④聯絡窗口 ✅
- Onboarding 評分 A（2 點擊 2 分鐘到案例剖析）
- 系統性風險：#1+#2+#4+#6 同屬「信任證據鏈」破口

## 開工前的地基工程（不在稽核清單但必要）

- **repo 落後 live 12 檔**（LINE 連結統一 P2HRySj、quote serving、pillar CTA 等
  都只在主機上）→ 全數同步回版控（commit 33a0020），否則部署即回歸災難
- 首頁 logo（murayama-logo-white.png）只存在主機 → 收回版控

## 修復明細（commit 8745fbb + 81e4c34，已部署並 live 驗證）

| 熱點 | 修法 | 執行者 |
|------|------|--------|
| #1 works 版頭破圖+裸文字 | SSR 模板換首頁 .topbar 結構 + murayama-logo-white.png | codex |
| #2 works 無聯絡元件 | 補頁尾 LINE CTA（P2HRySj）+ fab-line 浮動鈕 | codex |
| #3 modal 返回鍵離站 | 開 modal 寫入 #detail/{id}，back=關 modal 留頁；深連結關閉走 replaceState | codex |
| #4 teabar 22 張全破 | 8 張原檔 E 槽尋回轉 WebP + 11 張語意替補 + 2 張同場補位，src 全改本地 | L0 |
| #5 選單不一致 | workflow/teabar/muse 統一 canonical 六項 | codex |
| #9 魔法學院藏尾牙 | party filter 納入標題含「尾牙」的跨分類案例 | codex |
| #10 預算線索埋深 | workflow 加「預算怎麼抓?」段（抄 services FAQ 原文 25-60 萬） | codex |
| #12 pillar 術語 | sort-hat 字樣去 pillar | codex |
| #14 回到影片語意 | →「▶ 播放影片」 | codex |

## 待決（村長拍板，不阻塞迴圈）

- #6 公司基本資料（統編/地址/電話/email/關於我們）——信任內容缺口
- #7 「16+」徽章——Netflix 主題品牌梗，拆留由村長定
- #8 魔法學院/分類帽命名副標——品牌命名層級
- #13 聯絡 CTA 顏色統一——品牌色決策（選項：統一 LINE 綠）

## 掛下輪

- #11 services 頁無全站版頭（P2）——需 site.css/services.css 整合測試，不與 P1 混跑

## 驗收證據

- 語法：server.py AST pass、site.js node --check pass
- 行為（本地 Playwright）：modal 點開 hash=#detail/xxx → back → modal 關且留首頁 ✓
- 視覺（截圖親驗）：works 版頭/頁尾完整、teabar 捲動後破圖 0/23
- live 部署後六項硬驗證全過（topbar 4 元素、幽靈 logo 0、site.js 新邏輯 9 命中、
  teabar 新圖 200×3、wp-content 殘留 0、workflow nav+預算段 2 命中）

## 教訓

- **修 UX 前先驗 repo/live 同步**——這次 12 檔不同步，直接改 repo 部署會把
  live 半年的熱修全部蓋掉
- Playwright 量 naturalWidth 要先捲動觸發 lazy load，否則 16/23 假破圖
