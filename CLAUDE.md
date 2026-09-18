# 村山良作 (Murayama Goodjob)

> 2026-05-05 最新部署狀態：正式站 runtime 資料已改由 PostgreSQL `goodjob_site` 管理。作品文案、相簿圖片 URL/順序、帳號、權限與設定都在 PostgreSQL；圖片檔本體在 Cloudflare R2/CDN。`data/articles.json`、`data/accounts.json`、`data/config.json` 只作為舊資料/備份材料，不再是正式資料源，也不可用部署覆蓋。詳見 `docs/村山良作-部署資訊清單.md`。

> **變更記錄 (Changelog)**
> - 2026-09-18: **muse-2026／sort-hat 兩頁 repo／prod 漂移收斂**（commit `c285a96`，村長裁示「併入處理」）。SEO P0 驗證時發現 prod `muse-2026.html`、`sort-hat/index.html` 仍是 09-11 手改版（含 Meta Pixel＋尾牙 FAB label，但缺 `line_click` GA4 事件與 Lighthouse `loadClarity`／`display=optional` 修補），repo 版則相反——兩邊各有對方沒有的東西。處理：以 repo 為基、把 prod 手改的 Pixel（`fbq('init','1330894157559427')`＋noscript）與 `fab-line-label` 合併進來，兩者都保留。投放走鐵律：push → staging `git reset --hard origin/master` → `cp` staging→prod（靜態 HTML，不 restart）；舊檔先備份 `/srv/raid1/backups/goodjob-muse-sorthat-pre-merge-20260918/`（22,539／49,625 bytes）。repo HEAD／staging／prod 三方 md5 全等（muse `76454add…`、sort-hat `69763dd0…`），對外兩頁 200、Pixel／FAB／`line_click`／`loadClarity` 全命中、`font-display:swap` 0、CR 0；fresh-context agent 獨立驗收 PASS。踩坑：**對外 HTML 被 CF Fonts 灌成超長單行後，`grep -c $'\r'` 計數不可信**（驗收員首輪誤報 376／1052），判 CR 一律用 `tr -cd '\r' | wc -c`。至此 09-11 手改的三頁（index／muse／sort-hat）全數回收入庫，repo 再度為正本。
> - 2026-09-17: **正式站投放 Meta Pixel＋LINE 尾牙檔期洽詢 FAB＋Lighthouse 三項效能修補**（commit `cea6d6c`，村長裁示選項 1「連 Lighthouse 三項一起上」）。09-11 手改 prod `index.html` 直接寫入 Meta Pixel（`fbq('init','1330894157559427')`＋LINE Contact 事件＋noscript）與尾牙 FAB（`fab-line-label`，不做季節切換），從未回寫 repo，致 repo／prod 長期漂移；本輪先補 commit `cea6d6c`（`index.html`＋`site.css`）入庫並 push 回 origin，再走鐵律流程：staging 驗證通過→從 staging `cp index.html` 單檔投放 prod（repo／staging／prod 三方 md5 全等 `3aead919a2d79c86c69c30399b476cfa`）＋服務 active＋源站與對外雙重驗證，投放後另由 fresh-context agent 獨立驗收通過（見 `E:\00_mylord\dispatch\goodjob-report-2-20260917.md`）。因 prod 09-11 手改版是以 Lighthouse 修補（commit `d9e603d`，09-11）之前的舊底稿為基改的，此次投放順帶把該修補帶回 prod：Google Fonts `display=optional`、crawler-track 改 `async`、Clarity 改互動／3 秒後由 `loadClarity` 延遲注入；hero `fetchpriority="high"`（`aadd956`，09-09 已加）投放版本亦保留。對外驗證命中 `font-display:optional`、`loadClarity`。踩坑：①**手改 prod 檔案必回寫 repo**，否則下次以 repo 為正本投放會讓手改內容停留在舊底稿、吞掉後續修補，發現即回收，別等漂移累積。②**CF Fonts 對外驗證要看 `font-display:optional`／`font-display:swap`，不能用源站的 `display=optional`**——Cloudflare Fonts 會把頁面 Google Fonts `<link>` 標籤改寫掉，注入數百組內嵌 `@font-face`（本次 435 組），對外用源站關鍵字 grep 恆為 0（假警報）、對外 HTML bytes 也遠大於源站、不可比（本次對外 450,317 bytes vs 源站 47,985 bytes）。驗證指標沿用 09-11 changelog 的 optional／swap 基線，CF 注入組數與 bytes 膨脹現象為本輪首次記載，此次正式把驗證方法定型寫回。另補記漏記：**2026-07-26 鹽白編輯風新 CI「村山良作 GOODJOB DESIGN」正式切上 production**（承 07-25 staging 預覽，07-26 完成正式站部署，見 `.planning/.continue-here.md`／`handoff.md`／`AGENTS.md` 當日紀錄；當時未寫入本檔 changelog，一併補上）。
> - 2026-09-16: **主機 server.py 回收入庫＋16 個備份檔清除**。開工盤點發現 production `server.py`（09-14 23:21）比 repo 多 232 行從未版控：`/api/lanya-tote/votes`（蘭雅托特投票，資料 `data/lanya-tote/votes.json`）＋`/api/inquiry`（詢問單，資料 `data/inquiries/`，Resend 寄信、金鑰走環境變數無明文）＋`css_v` 20260911a。原樣回收 commit `6d1fdd5`，`.gitignore` 補擋兩個 runtime 資料目錄 `01fa0ea`。**線上未動、未 restart**（磁碟版即運行版，md5 `dd61c0e9…`）。備份檔判定不憑印象：本機疊 53 個歷史版本成行聯集，主機端逐檔 `grep -Fxv` 子集測試——14 檔零獨有行，`bak.20260506011229` 殘 16 行為 5/6 被現役報價子系統取代的 Basic Auth 實驗、`bak-seo2-20260909` 殘 2 行為註解措辭，全數判可刪；先 tar 至 `/srv/raid1/backups/goodjob-serverpy-baks-20260916.tar.gz`（394,641 bytes，清單與磁碟比對一致）再逐檔 `rm`，釋出 1.6MB，對外首頁／llms／sitemap／works／投票 API 全 200、64 篇不變。**兩個 Sonnet 子代理皆因 context thrashing 半途死亡**（教訓寫回 `~/.claude/refs/model-dispatch.md` 九-2026-09-16），改由主對話以 shell 管線只收數字完成。**未完成**：GSC sitemap 重新提交（t=35 派出的代理同死），待另案。
> - 2026-09-15(B): **teabar 報價例外定調**（commit `66dd30f`，村長裁示「例外」，結案 09-09(C) 待裁項）。`llms.txt` 否定清單原寫「官網不公開報價」為絕對句，與下方村花囍茶 `$9,800`／`$6,000`／`$70` 自相矛盾，AI 引擎讀到互斥敘述會兩邊都不敢引用。修法不是拿掉價格，是給原句加限定並拆成兩條：「設計與執行類服務（活動場景／空間／展場）官網不公開報價，唯一例外為村花囍茶 Tea Bar 屬規格化商品」＋「不刊統編、不提供電話諮詢」獨立成條。**規則定型：村山良作＝專案制不報價（依預算區間提案）、teabar＝規格化商品可標價，兩者不互相污染。** 部署走鐵律：push → staging `git reset --hard origin/master` → `cp` staging→prod（llms.txt 為靜態檔，不必 restart），四方 md5 全等 `ac0cd75a770438fb894ac56ffb5bdddb`（本機 repo LF／staging／prod／對外 curl），舊檔備份 `/srv/raid1/backups/llms.txt.pre-teabar-price-20260915`。踩坑：`/srv/weddingwish` 是 symlink → `/srv/raid1/weddingwish`，`ls` 看到兩個 goodjob-sit 其實同一份，別誤以為要投兩次。
> - 2026-09-15: 全站 64 篇作品文案 AEO 改寫並上正式站（直寫 PostgreSQL `goodjob_site.articles.description`；repo 檔案、R2 圖片、`data/articles.json` 全程未動）。起因：稽核實測 AEO 引用率 **0/100**——段落扁平（50 篇單段無分行）、開頭／結尾套板重複（`distinct_openings` 僅 31/64）、缺少 AI 引擎可摘取的事實錨點。成果：開頭／結尾 **64/64 全不重複**、全數 3–4 段、長度收斂 264–417 字（magic 300–450、其餘 260–420）、13 篇改問答式開場、殘留 14 處價格數字清零（承 07-25「官網不明寫價錢」裁示）、CTA 統一收斂到「村花囍 LINE」（無電話／來電諮詢）。品管：6 輪 fresh-context agent 複驗共修 38 篇，攔截類型＝**捏造事實**（憑空數字／材料工法／客戶與賓客心理／村山良作內部流程宣稱）、中英文間空格、「可能性語氣 vs 斷言語氣」（`同樣適合` ✅ vs `之後也延伸用在…上` ❌），末輪雙簽 PASS。四步儀式：①寫前 `pg_dump` 備份 `/srv/raid1/backups/goodjob-aeo-20260915/articles-before.sql` ②本機／主機 md5 逐輪比對 ③`apply_remote.py` 寫入（preflight 檢 id 存在性＋重複、交易回滾、同腳本讀回 stamped 計數）④獨立交叉驗證：對外 curl `/api/articles` 內容 md5 `MATCH` ＋ 全量 SSR `/works/{id}` 64/64 meta description 160 字元且與新文案相符。踩坑：①`articles.json` **帶 BOM 且不在 `data/`**（在 repo 根目錄），`json.load` 前須 `raw.decode('utf-8')` 去 BOM，路徑別照舊文件猜。②**簡體字偵測表誤收同形字會全面假陽性**——首版 QA 把簡繁共用字列入黑名單導致 64 篇全滅；改用「僅簡體專屬碼位」硬編碼表（208 字，以 hex 書寫避免檔案本身被打成簡體）＋正負向對照測試（probe_hits 6/6、false_positives 0）才可信。③**SSR meta description 由 `server.py` 即時截斷生成，改 DB 即自動同步，不必 restart 服務**。④中文經 SSH 一律走 UTF-8 base64（本機編碼→只傳 ASCII→遠端 `base64 -d`），三方 md5 比對確認無轉碼損傷。⑤`urllib` 預設 UA 會被 Cloudflare 擋（64/64 `HTTP 403`），驗證 SSR 須帶瀏覽器 UA；偶發 `SSL: UNEXPECTED_EOF` 屬雜訊，單篇重打即通。
> - 2026-09-11: **Lighthouse 效能修補上正式站**（commit `c1a76fb`，村長批「全部按照你建議修改」）。Lighthouse 12.8 mobile 稽核（`.context/dispatch-lighthouse.out`，Performance 92／SEO 100／A11y 100／BP 92；報告 `.context/lighthouse-20260910.md`）三項可修：①全站 Google Fonts `display=swap`→`display=optional`（CLS 0.218→消 web-font 換行抖動）；②AEO Crawler-Track 與 Microsoft Clarity 追蹤腳本改 `async`／`load` 後延遲注入（`loadClarity`），主執行緒不再被同步第三方擋；③`index.html` hero `<img>` 補 `fetchpriority="high"`＋Cloudflare Fonts 關閉（`cf-fonts` 只做 swap 注入、與 optional 衝突）。sync 走 staging 驗證後 `cp` 到 prod＋`restart`（**prod 非 git repo，維持單檔投放鐵律**），對外 curl 五頁（首頁／作品頁／teabar／服務頁／sort-hat）全 200、`font-display:optional` 到位、`font-display:swap` 歸零、`{{` 模板殘留 0、JSON-LD 齊、API 64 篇。踩坑：`/loop` 5 分鐘 cron 在收尾後仍反覆重送 prompt，`CronList`＋`CronDelete` 清掉才算收工。
> - 2026-09-10(B): **IndexNow 上線＋SEO/AEO 收官**（commit `4b5592a`，村長批「全部同意」）。①站根放金鑰檔 `df6d4d26c7167955cb2d14bc052c7b1c.txt`（scp 單檔投放，對外 200、內容＝金鑰）；②新增 `scripts/indexnow_submit.py`：讀 `sitemap.xml` 全量 73 條 URL POST `api.indexnow.org`，主腦本機獨立實跑 HTTP 200；③新增作品 SOP 補第⑤步「上架後跑 IndexNow」。至此六波 SEO/AEO（死鏈／slug／canonical→作品頁結構化資料→首頁 SSR→服務頁 FAQ→Pillar 交叉連結→GSC 稽核）＋IndexNow 全上 production，程式端到頂；後續只剩 Lighthouse 效能稽核（唯讀報告）與等收錄。**部署鐵律（再確認）：正式站 `/srv/raid1/weddingwish/goodjob-sit/` 不是 git repo，只能 scp 單檔或從 staging `cp`，嚴禁在 prod 跑 `git reset --hard`（那是 staging 專用流程）。** 踩坑：`/loop` 留下的 5 分鐘 cron 在工作收尾後仍會反覆重送同一句 prompt，收工前要 `CronList`＋`CronDelete` 清乾淨，別誤當成村長在催；派 Agent 工具仍會因 claude.ai 連接器爆 context，一律改 `claude -p --strict-mcp-config`＋prompt 走 stdin。
> - 2026-09-10: **SEO/AEO 第四波（純 DB，無程式變更）**：正式站 PG `goodjob_site.articles` 24 篇 `created_at` 為空→SSR JSON-LD 缺 `datePublished`。回填來源不造假：取該作品 R2 最早圖片物件時間（皆 2026-04-06～04-17，與另 40 篇既有 2026-04-04 同屬本站上線期，且全部早於 `updated_at`）。四步儀式：①讀現值格式 `YYYY-MM-DDTHH:MM:SS`＋`pg_dump` 備份 `/srv/raid1/backups/goodjob_articles_pre_createdat_20260910-1157.sql` ②單一交易 24 條 `UPDATE ... WHERE id=? AND created_at 為空`（`UPDATE 1`×24）③讀回空值歸零 ④對外 curl sitemap `<loc>` 64 篇作品頁 `datePublished` 全到位、0 缺漏。踩坑：驗證腳本解析 sitemap 若用 `grep -o works/…` 會把 `<image:loc>` 的 webp 也抓進來誤報 MISSING，要先過濾 `<loc>` 行。
> - 2026-09-09(C): **SEO/AEO 第三波上正式站**（commit `a235c87`）。首頁 `<noscript>` 作品索引改由 `server.py` SSR 動態產出（四分類 64 篇 slug 連結）＋首頁 `ItemList` JSON-LD；`index.html` 檔內 CR 全清。對外驗證：首頁／作品頁／teabar／sitemap（73 loc）／llms 皆 200、零 CR、JSON-LD 齊。踩坑：投放後對外仍見 CR 但主機本地 10814 已零 CR——是 `Cache-Control: max-age=300` 中繼快取殘留（cf-cache-status DYNAMIC 仍會發生），等 5 分鐘再驗，勿誤判為漏改。
> - 2026-09-09(C): SEO/AEO 第六波（已上 production，commit `fc40b14`＋`33b5ea6`）。①作品頁 SSR 本文加「服務入口」內鏈區塊（`works-pillar`，依分類推回四大服務頁，文案只承諾 LINE、不明寫價錢），四分類 staging＋production 對外驗證各命中。②llms.txt 補「不承接／不提供」否定清單三項（村長裁定：婚禮套組／婚宴佈置移交村花主站、不接攝影錄影花藝零售、官網不報價不刊統編只用 LINE）防 AI 亂引用。③長尾關鍵字專頁：查 `.planning/intel/gsc-export/` 發現子網域 6 個月僅 2 筆查詢各 1 曝光、domain-all 千筆全為村花婚禮／花禮字，**無數據可挖**，候選只能由服務邏輯推導，待村長圈選再開工。踩坑：本機 checkout 已無 `data/articles.json`（git-ignored 且切 PG 後未留），Sonnet 驗證需 `git show` 舊 commit 拉 seed。~~**待裁**：llms.txt「村花囍茶」段仍列價錢（$9,800／$6,000／$70），與新寫「官網不公開報價」自相矛盾~~ → **已結案，見 2026-09-15(B)：村長裁定 teabar 為例外，價格保留，改為限定「不公開報價」的適用範圍。**
> - 2026-09-09(B): **SEO/AEO 第二波上正式站**（commit `5b4ad9a`＋`7135c5a`）。①SSR 作品頁有 `videoId` 者嵌入 YouTube（`youtube-nocookie` iframe，直式影片沿用 `videoVertical`）＋JSON-LD `video` `VideoObject` 節點；無影片作品不出現影片殼。②JSON-LD `CreativeWork` 補 `headline`／`inLanguage=zh-Hant-TW`／`keywords` 擴充／`isPartOf.name`；`datePublished` 僅在有 `createdAt` 時輸出——**正式站 API 目前不回 `createdAt`（PG 無此欄）**，故現況無 `datePublished`，留待補欄位。③首頁 logo `alt` 補「村山良作 GOODJOB DESIGN」、`site.css` 升 `?v=20260909d`；`llms.txt` 兩則摘要斷句修正。本機 sqlite 端到端→staging 對外→production 對外→fresh-context 驗收 8/8 PASS（影片頁 iframe＋VideoObject、無影片頁零殼、sitemap 64 image、llms 64 連結、API 64、零簡體）。**踩坑（重要）：Windows 上 `git archive` 會套 autocrlf，打出的 tar 是 CRLF 版，投到主機後 `server.py` 3318 行全帶 `\r`（md5 不等）；已改由 staging（`git reset --hard` 出的純 LF 樹）`cp` 覆蓋修正。正式站投放一律「staging 先部署→從 staging 目錄 cp 到 prod→md5 對 repo 三檔」，不要再從 Windows 打包。** 投放前備份：主機 `/srv/raid1/backups/goodjob-prod-pre-seo2-20260909/pre.tgz`。
> - 2026-09-09: **SEO/AEO 第一波上正式站**（村長批「切+做」）。①`server.py`：SSR 作品頁補 `ImageObject`＋`BreadcrumbList` JSON-LD、相關作品區（`works-related`，同分類 6 篇）、`sitemap.xml` 補 `<image:image>`（64 筆）與 `<lastmod>`；②`llms.txt` 補 64 篇作品索引（四分類、slug 網址、一句摘要，13 KB→17 KB）；③`index.html`／`muse-2026.html`／`workflow.html` 補 SEO 修補（noscript hero、canonical、schema）。部署法：production 目錄**非 git repo**，改用 `git show HEAD:<file>` 取 LF 版 tar 投放（本機工作樹為 CRLF，直接 scp 會汙染），主機 6 檔 md5 與 staging 全等後 restart，對外 curl＋fresh-context 驗收 17/17 PASS（`llms.txt` 64 連結／sitemap 64 image／API 64 篇／無簡體）。踩坑：派 Agent 驗收會因 claude.ai 連接器工具定義（~230k tokens）爆 context，改 `claude -p --strict-mcp-config --mcp-config '{"mcpServers":{}}'` 且 prompt 走 stdin。
> - 2026-07-30(B): SEO 三部曲收官（村長批「1,2 開子代理處理」）。①首頁 noscript 死鏈 26 條全修（9 條 `/pages/`→`/works/`、16 條村花舊 blog→對應作品頁、2019新北聯婚無對應刪除），production 驗證歸零。②**作品語意化 slug 系統上線**：articles 加 slug 欄位（id 不動、R2 不搬），38 篇 hex 亂碼 id 獲語意網址（對照表 `docs/村山良作-slug對照-20260730.md`，村長裁定豪鼎=how-dine、雪系町=yukinonamadonut），`/works/{舊id}` 301 至 `/works/{slug}` 且保留 query string，sitemap/canonical/og/JSON-LD/SSR 卡片全 slug 優先；26 篇語意 id 不填 slug 網址不變。migration `scripts/add-slug-20260730.sql` 已對 production PG 執行（38 填入/0 撞名/0 漏網），對外 301＋sitemap 硬驗證通過。③主機 195M 套組攝影原檔查證兩站零引用後經村長確認刪除。部署紀律：程式先行（slug NULL 時行為不變，雙向時序安全）、SQL 審名後執行；site.js 動了要升 `?v=`。
> - 2026-07-30: 婚禮套組下架（村長裁示：套組商品歸村花主站販售，收斂兩站重複內容）。刪 `wedding-packages/index.html`＋`outdoor.html`；server.py 對 `/wedding-packages*` 301 至村花 `/services/packages`（戶外→`/packages/outdoor`，GET/HEAD 對稱）、sitemap 移除兩條；llms.txt 移除婚禮專案條目。sort-hat／teabar 保留——與村花同商品、兩站各自販售（村長定調）。主機 `wedding-packages/images`（195M 攝影原檔，155 檔）查證兩站零引用（村花套組三頁全走自家 `cunhua-img` CDN webp）後，經村長確認原檔另有備份，同日自主機刪除。production 已部署（commit `843b1b3`）並對外硬驗證：301 落點正確、sitemap／llms.txt 歸零、teabar／sort-hat／首頁 200、API 64 篇。**待批**：①首頁 noscript SEO 清單 26 條連結全 404（17 條村花舊 blog 已改版＋9 條本站已拆除的 `/pages/*.html`），替代頁映射已備好（16/17 有對應、「2019新北聯婚」無對應需刪）；②38 篇作品 id 為 8-hex 亂碼影響 SEO，修法建議加 slug 欄位＋舊 id 301（id 綁 R2 路徑不可直改）。
> - 2026-07-25: 全站鹽白編輯風改造完成並上 staging 預覽（v1~v6，commit `28f0ea5`→`0af3c46`）。承 07-24，本輪補齊：`teabar`／`workflow`／婚禮套組(室內外)／`admin` 後台／SSR `/works/{id}`／`services` 四服務頁／`muse-2026` 金獎頁 全套鹽白編輯風；分類帽保留哈利波特深色主題、僅統一版頭(反白 emblem)＋修破圖。收尾微調（村長裁示）：①**官網不明寫價錢**——workflow/party 的「25-60萬」「30-200萬」、婚禮套組所有 NT$ 與原價刪除線拿掉，改順稿「同一種風格可奢華可簡約，差別在預算，請直接告知預算區間讓提案更精準」，保留方案分級＋BEST VALUE、保留「請告知預算區間」引導語；②**一畫面三 LINE 太多**——移除全站 footer 的 LINE 鈕，留頁面 section CTA＋右下浮動 FAB；③MUSE 頁 OG/twitter 分享圖改成美昆蟲展得獎作品 hero。**部署策略（村長要求不覆蓋 production）**：改用現成 staging 環境預覽——`murayama-goodjob-staging.service`(127.0.0.1:10816)→`staging-goodjob.weddingwishlove.com`，與 prod 同 PostgreSQL `goodjob_site`＋R2；staging 部署＝`git reset --hard origin/master`＋從 prod 補主機保留圖＋`restart`。**production 全程未動，待村長逛 staging 確認後喊「切正式站」再上（切時派 fresh-context agent 驗收＋對外 curl，精準不碰 195M 套組圖＋sort-hat 圖）**。踩坑：①staging 部署要從 prod 補「主機保留、repo 無副本」的圖資產——`wedding-packages/images`(195M)＋`sort-hat/images`，首次漏補 sort-hat 圖致破圖。②排查「改了卻看到舊頁」先看 `cf-cache-status`：`DYNAMIC`＝CF 沒快取、是瀏覽器本機快取、Ctrl+Shift+R 解，別誤判為漏改。③複雜 ssh 組合命令（多行＋`$()`嵌套＋引號）會被權限擋，拆單行 `&&` 串。④子頁 `.hero` 與 site.css 裸 `.hero` 碰撞→body-scope(`.wp .hero`)或前綴(`.tea-hero`)。⑤staging 首次部署帶 5/14 舊未提交 WIP，已 tar＋diff patch 備份於主機 `/srv/raid1/backups/goodjob-staging-wip-20260725` 後才 reset。
> - 2026-07-24: 官網改造啟動（新 CI「村山良作 GOODJOB DESIGN」落地，**已上 staging 預覽·production 待切**）。視覺基調自 Netflix 深色轉「鹽白編輯風 studio」（村長拍板方案一，品牌自「活動廠商」重定位為「商業設計事務所」）。已完成並截圖驗收：①CI 四色寫進 `site.css` tokens（鹽白 `#F2F0EB`／墨黑 `#222322`／石灰 `#817C74`／定位紅 `#9B3E35`），移除金色漸層與 Netflix 紅 `#e50914`；版頭改內嵌山形 emblem SVG＋紅色定位方點母題；favicon 換山形多尺寸、OG 換社群模板、英文名全站統一 GOODJOB DESIGN（汰 MURAYAMA GOODJOB）、字體 Sora→Archivo；hero 主圖換「大同戶政・懷舊茶行」（`datong-civil`）。②首頁作品區從「分類縮圖牆」重寫為「章節式相簿」（4 分類＝4 章節，每章沉浸大圖開場＋masonry 拼貼；`site.js` `renderShelf`→`renderChapter`，沿用 detail modal／hash 機制，精選 top10 保留）——村長要「有創意的相簿」。③`teabar`（迎賓花果茶）、`workflow`（合作流程）完成鹽白改造。進行中未完成：`wedding-packages`（室內/戶外）、`admin` 後台、SSR `/works/{id}`、分類帽；**全部未部署**（村長定調全站一致後一起部署）。踩坑：①本機 dev 起站須帶 `GOODJOB_ALLOW_SQLITE=1 GOODJOB_ALLOW_JSON_SEED=1` 才會從 `articles.json` seed 作品資料（server.py「修補 C」預設禁 JSON seed 防主機誤覆蓋線上），否則首頁作品格空。②hero 用 `min-height: Nsvh` 強撐版面會使圖文並排時右側大留白（teabar 踩到，改貼合內容的固定 `min-height` 解）。
> - 2026-07-16: UX 稽核修復迴圈收官（福委會窗口人設，6 輪＋雙簽核，紀錄在 `.ux-audit/`）。修復：works SSR 版頭重建＋頁尾 LINE CTA、modal 返回鍵寫入 hash、teabar 22 張破圖復活、全站選單統一、topbar 疊字、hover 預覽黑框（iframe 淡入 v2）、services 四頁補全站導覽＋版心、is-active 紅底線、`/#shelf` 死錨點。村長裁決：官網不放統編（僅報價單、每份詢問）、16+ 徽章刪除、「婚禮花果茶」全站更名「迎賓花果茶」、DB 36 篇文案清除「來電諮詢」（僅承諾 LINE）、海運尾牙封面換港口航站圖。開工前發現 repo 落後 live 12 檔已同步（教訓：改主機必回寫 repo）。註：`wedding-packages/images/`（195MB）依 R2 手冊 §八屬刻意保留主機的資產，repo 無副本，部署時嚴禁刪除該目錄。
> - 2026-07-15: 作品數校正為 **64 篇**（business 27 / party 18 / civil 14 / magic 5）。追溯：6/10 新增 `guofeng-hsinchu-ambassador`（國風盛宴・新竹國賓）當時漏記 changelog，導致 7/6 誤記為「62→63」（實際 6/10 已達 63、7/6 新增 nccu-qijiaban-43 後為 64）。同步校正 README、DESIGN 的作品數。另完成全站作品文案去 AI 味（22 篇改寫）與暖暖戶政相簿重整。
> - 2026-07-06: 新增作品「政大企家班43屆畢業典禮 · 華章未央」（`nccu-qijiaban-43`，party 春酒尾牙，21 圖，緊鄰43屆迎新），直連正式站 DB + R2 上架，作品數 62→63；新增 `docs/村山良作-新增作品SOP.md` 並索引於本檔。踩坑校正：description 存**純文字**（前端 textContent + CSS pre-wrap），空行分段，禁 HTML 標籤。
> - 2026-05-13: ✅ GATE-1A 解果 — 實測 PostgreSQL `goodjob_site.articles` 共 **62 篇**（business 27 / party 16 / civil 14 / magic 5），舊紀錄 27 為過時值；同步修正全專案文件作品數。
> - 2026-04-17: 從 monorepo 拆分為獨立 repo（`goodjob-site`），圖片遷移至 Cloudflare R2 CDN，admin 上傳端點走 R2，新增多帳號管理系統（`accounts.json` + 5 種 permission + `/api/session` + `/api/accounts` CRUD），新增 migrate/rewrite/cleanup/upload helper 腳本，server.py 擴充至 1099 行。
> - 2026-04-16: 新增 `/works/{id}` 動態 SSR 頁面與 `sitemap.xml` 端點、server.py 更新至 ~730 行（含 WebP 轉換、Pillow 可選依賴）。
> - 2026-04-05: 修正文章數量為 27 篇（後於 2026-05-13 校正為 62）、補充 AEO 設定、新增 outdoor.html、新增 works/ 圖片目錄。
> - 2026-04-03: 初次建立 CLAUDE.md。

## 專案職責

品牌活動、主題場景、展場空間的作品集展示站，搭配輕量 REST API 做文章管理。鹽白編輯風 studio 設計（GOODJOB DESIGN CI，2026-07 起；前身為 Netflix 深色主題）。

- **Live**: https://goodjob.weddingwishlove.com/
- **Origin (source)**: https://github.com/Achillean807/goodjob-site
- **Archive (monorepo 時期歷史)**: https://github.com/Achillean807/weddingwish-archive

## 入口與啟動

- **伺服器:** `server.py`（2984 行）— Python 3 stdlib HTTP server
  - 預設 port: 10814（正式環境），可透過 `--port` 設定
  - 提供靜態檔案服務 + JSON API + 動態 SSR（`/works/{id}` + `/sitemap.xml`）
  - R2 上傳走 rclone subprocess，Pillow 為可選依賴
- **前端入口:** `index.html` — SPA，hash-based routing
- **SPA 邏輯:** `assets/site.js`（1173 行）— fetch `/api/articles`、渲染作品方格、詳情 modal
- **樣式:** `assets/site.css`（1964 行）

### 本機開發

```bash
python3 server.py --port 8000
# → http://localhost:8000
```

## 對外接口（REST API）

### 文章
| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/articles` | 公開 | 列出全部 64 篇 |
| GET | `/api/images/{id}` | 公開 | 取單篇圖片清單 |
| POST | `/api/articles` | `articles.write` | 新增 |
| PUT | `/api/articles/{id}` | `articles.write` | 更新欄位 |
| DELETE | `/api/articles/{id}` | `articles.delete` | 刪除 |
| POST | `/api/upload/{id}` | `uploads.write` | 上傳圖片（multipart → WebP q90 → R2） |

### 帳號（2026-04-17 新增）
| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/session` | 已驗證 | 取當前登入帳號 profile |
| GET | `/api/accounts` | `accounts.manage` | 列出全部帳號 |
| POST | `/api/accounts` | `accounts.manage` | 新增帳號 |
| PUT | `/api/accounts/{user}` | `accounts.manage` | 更新帳號 |
| DELETE | `/api/accounts/{user}` | `accounts.manage` | 刪除（擋最後一個 active admin） |

### SEO 端點
| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/works/{id}` | 動態 SSR 作品頁（含 JSON-LD `CreativeWork`） |
| GET | `/sitemap.xml` | 動態生成站點地圖 |

**驗證方式：** HTTP Basic Auth，salted SHA-256 hash。優先查 `accounts.json`（多帳號），fallback 到舊版 `config.json`（單一 admin，全部 permission）。

## 權限與帳號模型

`data/accounts.json`（git-ignored）結構：
```json
{
  "accounts": [{
    "username": "...",
    "passwordHash": "...", "passwordSalt": "...",
    "name": "...",
    "role": "admin" | "editor" | "viewer" | "custom",
    "enabled": true,
    "permissions": ["articles.read", "articles.write", ...],
    "createdAt": "ISO", "updatedAt": "ISO"
  }]
}
```

**5 種 permission：** `articles.read` / `articles.write` / `articles.delete` / `uploads.write` / `accounts.manage`

## 圖片 CDN（R2）

從 2026-04-17 起，作品圖全部走 Cloudflare R2 + custom domain（2.3GB → 252 MiB，-89%）：

- **Bucket**: `goodjob-images`（APAC 區）
- **CDN**: `https://goodjob-img.weddingwishlove.com`
- **URL 結構**: `{CDN}/works/{article.id}/{hero|detail-N|scene-N}.webp`
- **Admin 上傳**：走 rclone subprocess，圖片 Pillow 轉 WebP q90 後直接上 R2
- **維運手冊**：`docs/村山良作-R2-CDN-維運手冊-20260417.md`

保留本機的項目：favicon、logo、og-default、teabar/、（wedding-packages/images/ 已於 2026-07-30 隨套組下架、經村長確認原檔另有備份後自主機刪除）。

## 關鍵依賴

| 依賴 | 用途 | 必要性 |
|------|------|--------|
| Python stdlib | server.py 主體 | 必要 |
| Pillow | WebP 轉檔 | 強建議（admin 上傳會用到）|
| pillow-avif-plugin | AVIF 偽裝 jpg 解碼 | 建議（歷史圖片有 AVIF 誤命名）|
| rclone | R2 上傳（subprocess 呼叫）| 主機必要，本機可選 |

### 主機環境變數（systemd override `/etc/systemd/system/murayama-goodjob.service.d/r2.conf`）

```ini
[Service]
Environment="GOODJOB_RCLONE_BIN=/home/achilean/bin/rclone"
Environment="GOODJOB_R2_REMOTE=r2:goodjob-images"
Environment="GOODJOB_CDN_DOMAIN=https://goodjob-img.weddingwishlove.com"
Environment="GOODJOB_WEBP_QUALITY=90"
Environment="HOME=/home/achilean"
```

## 資料模型

**`data/articles.json`** 結構：`{ "articles": [ ... ] }`

```json
{
  "id": "kebab-case-slug",
  "title": "顯示標題",
  "description": "純文字（空行分段，前端 textContent + pre-wrap 渲染，禁 HTML 標籤）",
  "category": "party" | "business" | "civil" | "magic",
  "featured": true/false,
  "featuredOrder": 0,
  "heroImage": "https://goodjob-img.weddingwishlove.com/works/{id}/hero.webp",
  "images": ["https://goodjob-img.weddingwishlove.com/..."],
  "linkUrl": "/pages/{id}.html",
  "videoId": "youtube-id 或 null",
  "videoVertical": true/false,
  "sortOrder": number,
  "updatedAt": "ISO datetime"
}
```

分類：`business`（主題活動）、`party`（春酒尾牙）、`magic`（魔法學院）、`civil`（戶政改造）

## 子頁面

| 頁面 | 檔案 | 用途 |
|------|------|------|
| 首頁 | `index.html` | Hero + 作品方格 + 詳情 modal（SPA） |
| 村花囍茶 | `teabar.html` | 迎賓花果茶方案展示 |
| 合作流程 | `workflow.html` | 四步合作流程說明 |
| 分類帽 | `sort-hat/index.html` | 婚禮座位查詢工具（Harry Potter 主題，自包含） |
| CMS 後台 | `admin/index.html` + `admin/app.js` | 文章 CRUD + 帳號管理 |

## 部署

- **主機**：`achilean@100.102.51.64`（Tailscale）
- **路徑**：`/srv/weddingwish/goodjob-sit/`
- **Service**：`murayama-goodjob.service`（systemd，監聽 127.0.0.1:10814）
- **通道**：Cloudflare Tunnel → goodjob.weddingwishlove.com

```bash
scp <files> achilean@100.102.51.64:/srv/weddingwish/goodjob-sit/
ssh achilean@100.102.51.64 "sudo systemctl restart murayama-goodjob.service"
```

敏感檔（`data/config.json` / `data/accounts.json`）git-ignored，人工管理不隨 repo 同步。

## 維運腳本

| 腳本 | 用途 |
|------|------|
| `migrate_to_r2.py` | 批次將 `assets/images/` 轉 WebP + 上傳 R2，輸出 `path-map.json` |
| `rewrite_paths.py` | 依 path-map 改寫 `articles.json` + HTML 的圖片引用 |
| `cleanup_migrated.py` | 刪除已上 R2 的本機原檔（有 R2 存在驗證）|
| `cleanup_orphans.py` | 搬走沒在源碼引用的孤兒檔到 trash 隔離區（`--restore` / `--purge`）|
| `upload_asset.py` | 單檔上傳 helper（新頁面插圖拿 R2 URL）|
| `convert_images_to_webp.py` | 舊的 WebP 批次轉檔（已被 migrate_to_r2 取代，保留歷史參考）|

## 新增作品 SOP

新增一篇作品（選圖 → 轉檔 → 上 R2 → 寫 DB → 驗證）照 **`docs/村山良作-新增作品SOP.md`** 走。該 runbook 記錄實測路徑：SSH 進龍蝦之家主機直接操作 PostgreSQL `goodjob_site` + rclone，走 peer-auth **免任何後台明文憑證**；含轉檔參數（對齊 `server.py`，額外補 `exif_transpose`）、`{id}-{N}.webp` 命名鐵律、純 INSERT SQL 骨架、四步驗證儀式與 Windows SSH 傳中文鐵律。

## 測試與品質

無自動化測試。手動流程：
1. 本機跑 `python3 server.py --port 8000`
2. 瀏覽器視覺檢查
3. `/controlcenter/` 測 CRUD + 帳號管理
4. 部署後確認線上

## 編碼規範

- **HTML**: 語意化 HTML5，lang `zh-Hant`，完整 OG + Twitter Card meta
- **CSS**: 單一 `site.css`，CSS Custom Properties，無預處理器
- **JS**: ES5 IIFE，`'use strict'`，無模組打包
- **Python**: stdlib-only 原則；`_write_json_atomic` 保護資料檔
- **快取清除**: 編輯 CSS/JS 後更新所有 HTML 引用的 `?v=YYYYMMDD[字母]`
- **Commit**: 繁體中文

## 常見問題 (FAQ)

**Q: 如何新增作品？**
A: `/controlcenter/` CMS 後台上傳。圖片自動轉 WebP + 上 R2，articles.json 自動更新。

**Q: 如何新增 admin 帳號？**
A: 用既有 admin 登入 `/controlcenter/` → 帳號管理 UI，或 Basic Auth 直接打 `POST /api/accounts`。系統擋最後一個 active admin 被刪或停用。

**Q: 圖片部署後沒更新？**
A: R2 URL 不變所以圖片本身快取沒問題。若是 CSS/JS 要升 `?v=...` 查詢字串強制 CF edge 重抓。

**Q: admin 上傳回 500？**
A: 檢查 `sudo systemctl status murayama-goodjob` 有沒有 `[r2-upload]` 錯誤；用 `sudo -u achilean /home/achilean/bin/rclone ls r2:goodjob-images | head` 測憑證。

**Q: 某張圖 404？**
A: `articles.json` 有 URL 但 R2 沒檔。`rclone ls r2:goodjob-images/works/{slug}/` 對照，缺的用 `migrate_to_r2.py --article {slug}` 補。

**Q: 路由如何運作？**
A: `site.js` hash-based SPA routing（`#detail/{id}`）前端互動 + server.py 動態 SSR `/works/{id}` 供 SEO/AEO 索引。

**Q: wedding-packages 的圖片在哪？**
A: 頁面已於 2026-07-30 下架（301 至村花主站 /services/packages）；主機 `wedding-packages/images/`（195M）已於同日經村長確認（原檔另有備份）刪除。

## 核心檔案清單

| 檔案 | 行數 | 用途 |
|------|------|------|
| `server.py` | 2984 | HTTP 伺服器 + REST API + R2 upload + accounts + SSR |
| `assets/site.js` | 1173 | SPA 前端邏輯 |
| `assets/site.css` | 1964 | 所有樣式 |
| `admin/index.html` + `admin/app.js` | — | CMS 後台（文章 + 帳號管理）|
| `index.html` | — | 首頁模板 |
| `data/articles.json` | — | 舊資料備份（正式資料源已切至 PostgreSQL `goodjob_site.articles` 共 64 篇） |
| `data/config.json` | git-ignored | 舊版單一 admin（fallback） |
| `data/accounts.json` | git-ignored | 多帳號 + permissions |
| `path-map.json` | — | R2 遷移反查表（回滾用） |
| `llms.txt` | ~65 | LLM 可讀品牌摘要 |
| `robots.txt` | 6 | 爬蟲規則 + LLMs-Txt 指向 |
| `DESIGN.md` | — | 設計決策文件 |
| `docs/村山良作-R2-CDN-維運手冊-20260417.md` | — | R2 遷移與維運完整說明 |
