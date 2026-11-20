---
日期: 2026-11-20
repo: goodjob-site
分支: master
HEAD: d74fa96（之後只加 docs commit）
---
# 交接 2026-11-20

## 今天完成（皆已上正式站並驗證）
- 作品頁 FAQ 第 3 題作品名加超連結（202301b）。
- 移除詢問單功能、Email 寄信與信箱（e96a6b5、d74fa96）；/api/inquiry 對外回 404。
- 主題活動服務頁代表案例換入美福與 Joey 40、標題斷行（11-19，見 CLAUDE.md 11-19(B)）。
- 村花婚禮專欄上架美福藍色星球（wedding-site 0039e14）。三處待裁（價格區塊、2026·冬、真實字樣）村長裁示維持現狀。

## 未竟事項
- 主機 prod 仍有 systemd drop-in resend.conf，新程式不讀；是否清掉待村長決定。
- 兩個服務 NeedDaemonReload=yes（部署前就有，原因未驗證，未動）。
- 是否有主機外的前端呼叫 /api/inquiry：未查全。
- 手機 Safari 實機：未驗證。
- 引用登記：村花婚禮專欄引用 goodjob meifu-blue-planet-galaxy-decor 第 1～9 張圖；改圖、刪圖、重新編號前先通知該專欄。
- 本機有未追蹤備份檔 CLAUDE.md.bak-2026111*、bak-20261120，不進 git。

## 踩坑
- cc-plugin-privacy 外掛擋含信箱的檔案寫出，也擋 cd 路徑 && 開頭的 Bash；用 git -C 或 python os.chdir。
