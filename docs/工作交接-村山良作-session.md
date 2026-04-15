# 工作交接-村山良作 Session

更新日期：2026-03-19

## 1. 目前工作主軸
目前先只做 `村山良作 / goodjob`。
方向已從「掛在舊 WordPress 裡的品牌子頁」轉成「獨立網站 MVP」，主站之後只需要放超連結入口導過去。

目前定案方向：
- 首頁要用圖片先說服客人，並且要有真正的首頁入口感
- 整體調性維持安靜、克制、偏 MUJI 感
- 保留紅點識別，不做大面積紅色
- 單篇作品頁正式方向：`Web Editorial + 文章段落 + 組圖單元`
- 全部作品牆正式採用 `密版 archive.html`
- 移植到獨立站的文章一律使用本地圖片資產，不再熱連 WordPress 圖檔

## 2. 目前主要工作目錄
- 主工作目錄：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網`

## 3. 已完成的獨立站檔案
位置：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site`

已完成：
- `index.html`
- `cases.html`
- `archive.html`
- `workflow.html`
- `pages\lativ-magic-platform.html`
- `pages\gd-home-sweet-home.html`
- `pages\chengmei-insect-exhibition.html`
- `assets\site.css`
- `assets\site.js`
- `assets\murayama-logo.png`
- `assets\images\...` 多張本地案例圖

## 4. 目前可直接 review 的重點頁
- 首頁：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site\index.html`
- 案例精選：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site\cases.html`
- 全部作品：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site\archive.html`
- 合作流程：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site\workflow.html`
- 單篇作品：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\03-prototypes\murayama-standalone-site\pages\lativ-magic-platform.html`

## 5. 已完成的視覺驗證截圖
位置：`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\05-live-check\screens`

目前已有：
- `murayama-home-homefeel.png`
- `murayama-archive.png`
- `murayama-lativ-detail.png`

其中：
- `murayama-home-homefeel.png` 是目前首頁最重要的檢查圖
- 截圖已確認首頁不是文字主導，而是圖片主導

## 6. 內容與文章重寫狀態
已重寫並做成新單篇頁的案例：
- Lativ 魔法月台派對
- G-Dragon 應援佈置
- 成美文化園昆蟲展
- CXO 女創俱樂部拍照區
- 台北中正戶政・幸福開市
- 曾蘋果老師課程活動佈置
- 政大企家班42屆畢業晚會
- 森林仙境・大安戶政拍照區
- 瓶蓋工廠品牌活動佈置

全部作品 archive 目前策略：
- 正式採用 `archive.html` 的密版作品牆
- 9 篇主案例連到新單篇頁
- 已移植文章的圖片放在 `assets\images`，由獨立站直接讀取
- 尚未移植的案例可暫時連回舊站原始專欄文章
- 後續逐篇把舊文改寫進新站後，再把連結改到新單篇頁

## 7. WordPress / 舊站現況
目前 WordPress 舊站仍保留，主站入口暫時不要切換。
村山良作新版 live 頁仍存在：
- Page ID：`21256`
- URL：`https://www.weddingwishlove.com/murayama-muji-home/`

目前決策：
- 先把獨立站做完整
- 等整體完成再決定主站是導向獨立站，還是保留舊 WordPress 頁面

## 8. WordPress REST API 登入資訊
使用者明確允許寫入 handoff。

- 後台網址：`https://www.weddingwishlove.com/controlcenter/`
- 使用者：`clwadbot_editor`
- Application Password / REST API Token：`rUhd icuh U7cb TuwK WUIB r0GV`

注意：
- 這組是 REST API / Application Password，不是一般瀏覽器密碼
- 2026-03-19 已實測可用

## 9. Python 環境
這台電腦已補好最小需要套件：
- `requests`
- `beautifulsoup4`
- `lxml`
- `pillow`

Python 實際路徑：
- `C:\Users\achillean\AppData\Local\Programs\Python\Python312\python.exe`

如果 shell 直接打 `python` 又掉回 WindowsApps 假 alias，請直接用上面這條路徑。

## 10. 本輪已處理的技術問題
- 本地頁面原本圖片不顯示
  - 原因：本地 `file://` 模式下，CSS 變數圖片沒有穩定套上背景
  - 解法：新增 `assets\site.js`，把 `--image` 轉成實際 `background-image`
- 已把主要案例圖下載到本地 `assets\images`
  - 不再依賴主站熱連結

## 11. 下一步建議順序
1. 先移植下一批舊站文章到獨立站
2. 新移植文章同步下載圖片到本地 `assets\images`
3. 把 `archive.html` 裡對應卡片改連到新單篇頁
4. 累積到足夠篇數後，再決定是否擴成 12 篇以上
5. 最後才處理主站入口怎麼切

## 12. 如果換電腦要怎麼接續
直接貼這段給 Codex：

請先讀這份 handoff：
`F:\SynologyDrive\Share\39 Ace 秦天霸\村花弄囍官網\01-docs-archive\docs\工作交接-村山良作-session.md`

目前先只處理村山良作獨立站。
請從 `03-prototypes\murayama-standalone-site` 繼續。
目前首頁要維持圖片主導方向。



## 2026-03-19 獨立站部署狀態
- 已部署獨立站到 `ACH-ClawHome`。
- 公開網址：`https://goodjob.weddingwishlove.com/`
- 遠端站點目錄：`/srv/weddingwish/murayama-goodjob-site`
- systemd service：`murayama-goodjob.service`
- 服務埠：`127.0.0.1:10814`
- Cloudflare Tunnel 已加入 `goodjob.weddingwishlove.com -> http://localhost:10814`
- cloudflared config：`/home/achilean/.cloudflared/config.yml`
- 現況：`murayama-goodjob.service` / `cloudflared.service` 皆為 `active`
- 備註：公開站 console 已清到 0 error；目前 favicon 也已補上。
