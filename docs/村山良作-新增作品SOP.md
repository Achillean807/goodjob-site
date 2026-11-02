# 村山良作 — 新增作品 SOP（直連正式站 DB + R2）

> 給未來 session 照做的 runbook：SSH 進龍蝦之家主機，**直接操作** PostgreSQL `goodjob_site` + rclone 上 R2，走主機自身 peer-auth，**不需交換任何後台明文憑證**、不走 admin API。
> 首次落地：2026-07-06 新增「政大企家班43屆畢業典禮 · 華章未央」（`nccu-qijiaban-43`，21 圖）。
> 本文檔**不含任何密碼**；主機連線與 DB 皆靠免密機制。

---

## 0. 動手前先問村長

| 項目 | 說明 |
|------|------|
| 原圖位置 | Synology 路徑（例：`F:\SynologyDrive\Share\13 商業佈置\...`） |
| 選圖配比 | 各場景各挑幾張、封面用哪張（**hero = position 0**） |
| 分類 | `business`（主題活動）/ `party`（春酒尾牙）/ `school`（學校活動，2026-11-02 起）/ `magic`（魔法學院）/ `civil`（戶政改造） |
| 文案 | 哈雷醬寫初稿 → 村長審（title / slug / description） |

slug 用 kebab-case、純 ASCII（當圖片目錄名與 DB 主鍵）。

---

## 1. 主機 / DB / R2（免憑證）

| 資源 | 值 |
|------|----|
| SSH | `achilean@100.102.51.64`（Tailscale，**單 L** achilean） |
| DB | `psql goodjob_site`（peer-auth，本機 socket，免密） |
| rclone | `/home/achilean/bin/rclone`，remote `r2:goodjob-images` |
| CDN | `https://goodjob-img.weddingwishlove.com` |
| service | `murayama-goodjob.service`（改 DB 後 restart 讓 server 重讀） |

---

## 2. Schema（純 INSERT 新列，**絕不 UPDATE/DELETE 既有資料**）

**`articles`**（15 欄）：`id`(PK,text)、`title`、`description`(**純文字**，空行分段，禁 HTML 標籤)、`category`、`featured`(int)、`featured_order`(int)、`hero_image`(text)、`link_url`(null)、`video_id`(null)、`video_vertical`(int)、`sort_order`(int)、`created_at`(ISO text)、`updated_at`(ISO text)、`row_index`(int)、`case_blocks`(jsonb)。

**`article_images`**：`(article_id, position, url)`，PK `(article_id, position)`，position **0-based**。

鐵律：
- `hero_image` == position 0 的 URL。
- 圖片命名：**`{id}-{N}.webp`（N = position+1）**，thumb `{id}-{N}-thumb.webp`。URL base `{CDN}/works/{id}/`。
- 新篇欄值慣例：`featured=0`、`featured_order=0`、`video_id=NULL`、`link_url=NULL`、`case_blocks='{}'`。
- `sort_order` / `row_index` 用 `(SELECT COALESCE(MAX(...),0)+1 FROM articles)` **動態取**，避免撞號。
- `created_at`/`updated_at` 用台北時間：`to_char(now() AT TIME ZONE 'Asia/Taipei','YYYY-MM-DD"T"HH24:MI:SS')`。

---

## 3. 轉檔（對齊 `server.py` `_api_upload`）

| 參數 | 值 |
|------|----|
| 主圖 | `WEBP quality=90 method=4`；寬 > 3000 先 `thumbnail((3000,30000), LANCZOS)` |
| thumb | `thumbnail((400,4000), LANCZOS)` + `WEBP quality=75 method=4` |
| **額外** | 加 `ImageOps.exif_transpose`（server.py **沒做**，豎版照片會躺倒） |

腳本模板 `build_webp.py`（每次改 `BASE` / `ID` / `SEL` 三處）：

```python
import os, glob, re
from PIL import Image, ImageOps
BASE = "F:/.../原圖資料夾"          # ← 改
ID   = "nccu-qijiaban-43"           # ← 改（= slug）
SEL  = [("典禮", 4), ("典禮", 3), ...]  # ← 改：(場景子夾, 檔名編號) 依最終順序，[0]=hero
WEBP = "webp"; os.makedirs(WEBP, exist_ok=True)
def natkey(p):
    m = re.search(r"\((\d+)\)", os.path.basename(p)); return int(m.group(1)) if m else -1
scene = {}
for s in set(x[0] for x in SEL):
    d = {}
    for f in glob.glob(os.path.join(BASE, s, "*")):
        e = f.rsplit(".",1)[-1].lower()
        if e in ("jpg","jpeg","png"):
            n = natkey(f)
            if n not in d or e in ("jpg","jpeg"): d[n] = f   # 同號 jpg 優先
    scene[s] = d
for pos, (s, n) in enumerate(SEL):
    im = ImageOps.exif_transpose(Image.open(scene[s][n])).convert("RGB")
    if im.width > 3000: im.thumbnail((3000, 30000), Image.LANCZOS)
    idx = pos + 1
    im.save(f"{WEBP}/{ID}-{idx}.webp", "WEBP", quality=90, method=4)
    t = im.copy(); t.thumbnail((400, 4000), Image.LANCZOS)
    t.save(f"{WEBP}/{ID}-{idx}-thumb.webp", "WEBP", quality=75, method=4)
```

> 選圖前先跑一張 contact sheet（每場景縮圖拼帶編號）給村長挑，再定 `SEL`。

**選圖準則（村長 2026-09-30 定，The Roman 刪圖時訂立）：**

1. **角度相近、內容類似的照片只留一張**——同一面背板換個距離或左右偏移都算相近，不為湊數硬放。
2. **有人物的照片，只收「人臉清楚且看著鏡頭」的**；沒看鏡頭、遮臉、側臉都不收（不用模糊或裁切去救）。
3. **小孩一律不能入鏡**（裁掉也不用，整張不收）。
4. 另沿用：畫面內不得出現簡體字（投影幕歌詞等），出現就裁掉或不收。
5. 沒有肖像授權的人物照（例如未成年學生）：經村長同意，可用 AI 重新合成人物，人物以外用原圖像素合成回去（佈置不可被 AI 改動），文案加註『為保護未成年人，圖中人物皆為 AI 重新合成。』。2026-11-02 葳格國際學校案例：做法與檢查見 CLAUDE.md 11-02(F)。
6. 座位牌、名牌、識別證上的姓名，在原尺寸（1:1）讀得出就整張不收。選圖要逐張用原尺寸檢查，不能只看縮圖總表。2026-11-02 葳格案例：主對話只看縮圖總表選了典禮走道全景，上線後獨立驗收在 1:1 讀出座位牌姓名，當天拿掉並重新編號。

---

## 4. 上架（四步儀式）

```bash
ID=nccu-qijiaban-43
H=achilean@100.102.51.64
RC=/home/achilean/bin/rclone

# ── scp 圖上主機 ──
ssh $H "rm -rf /tmp/$ID && mkdir -p /tmp/$ID"
scp webp/*.webp $H:/tmp/$ID/

# ①→② R2 上傳 + 讀回 + CDN 交叉驗證
ssh $H "$RC ls r2:goodjob-images/works/$ID/ | wc -l"          # 上傳前應 0
ssh $H "$RC copy /tmp/$ID/ r2:goodjob-images/works/$ID/"
ssh $H "$RC ls r2:goodjob-images/works/$ID/ | wc -l"          # 讀回 = 檔數
curl -sI https://goodjob-img.weddingwishlove.com/works/$ID/$ID-1.webp | head -1  # 200

# ③ 寫 DB：本機生成 UTF-8 insert.sql → scp 傳檔 → psql -f
#   ⚠ 中文鐵律：SQL 檔用 scp 傳（二進制不轉碼）或 UTF-8 base64，
#     禁 here-string / stdin / pipe（會把中文寫成亂碼）
python make_sql.py                       # 產 insert.sql（見附錄）
scp insert.sql $H:/tmp/$ID/
ssh $H "file /tmp/$ID/insert.sql; head -12 /tmp/$ID/insert.sql"   # 確認 UTF-8 中文沒壞
ssh $H "psql goodjob_site -f /tmp/$ID/insert.sql"                # 事務：INSERT 0 1 / INSERT 0 N / COMMIT
ssh $H "sudo systemctl restart murayama-goodjob.service"

# ④ 對外交叉驗證（獨立來源，不信 DB 回報）
B=https://goodjob.weddingwishlove.com
curl -s $B/api/articles | grep -o $ID | head -1
curl -s -o /dev/null -w '%{http_code}\n' $B/works/$ID          # 200
curl -s $B/sitemap.xml | grep -o $ID | head -1

# ⑤ IndexNow 主動通知搜尋引擎（Bing／Yandex 等，Google 不吃但無害）
#   讀 sitemap 全量提交，期望印出 HTTP 200 或 202；金鑰檔在站根，2026-09-10 上線
PYTHONIOENCODING=utf-8 python scripts/indexnow_submit.py

# 收尾
ssh $H "rm -rf /tmp/$ID"
```

`insert.sql` 用 `make_sql.py` 程序化生成（避免手寫 N 筆 image 出錯），骨架：

```sql
\set ON_ERROR_STOP on
SET client_encoding = 'UTF8';
BEGIN;
INSERT INTO articles (id,title,description,category,featured,featured_order,hero_image,
  link_url,video_id,video_vertical,sort_order,created_at,updated_at,row_index,case_blocks)
VALUES ('{id}','{標題}','{純文字描述·空行分段·禁HTML標籤}','{category}',0,0,'{CDN}/works/{id}/{id}-1.webp',
  NULL,NULL,0,
  (SELECT COALESCE(MAX(sort_order),0)+1 FROM articles),
  to_char(now() AT TIME ZONE 'Asia/Taipei','YYYY-MM-DD"T"HH24:MI:SS'),
  to_char(now() AT TIME ZONE 'Asia/Taipei','YYYY-MM-DD"T"HH24:MI:SS'),
  (SELECT COALESCE(MAX(row_index),0)+1 FROM articles),
  '{}');
INSERT INTO article_images (article_id,position,url) VALUES
  ('{id}',0,'{CDN}/works/{id}/{id}-1.webp'),
  ...                                              -- position 0..N-1
  ('{id}',N-1,'{CDN}/works/{id}/{id}-N.webp');
COMMIT;
```

> 描述若含單引號要 `''` 轉義（生成腳本可 `assert "'" not in ...` 擋掉）。

### 4-1. 分段配圖（`case_blocks.sections`，2026-11-02 起）

作品頁預設是「整段文案 → 最後一個精彩花絮圖庫」。要讓每段文字後面直接接該段照片，照下面設定：

- **資料**：寫在 `articles.case_blocks`（jsonb）的 `sections` 鍵。description **不加任何標記**（description 會進 meta、JSON-LD、works-search、SPA）。
  格式：`{"sections": [{"label": "主背板", "images": [1, 2, 4]}, ...]}`。`images` 是 1-based 圖片序號（＝position+1），依陣列順序顯示。
- **label 對應**：description 中以「【label】其餘文字」開頭的行是段落標題。標題行之前的文字是開場段，不配圖。標題顯示為「label 小標籤｜其餘文字」，不顯示【】。
- **標題行格式**：標題行只寫「【label】短標題」（約 10～20 字），正文從下一行開始。整段正文寫在標題行，會被當成粗體小標題。2026-11-02 葳格案例：v3 標題行 51～204 字，412px「大書背板」小標題高 402px；v4 改成短標題（例：「【大書背板】一本翻開的大書」）。
- **圖庫欄數（2026-11-02 起）**：分段圖庫桌面預設每排 3 張。某段張數 n ≥ 2、不是 3 的倍數、但是 2 的倍數時（2、4、8、10…），div 多一個 `works-gallery--2col` class，>600px 改每排 2 張（4 張→2×2、8 張→2×4）。≤600px 本來就是 1 欄，不受影響。`wide` 段落維持單欄，不套這條。最後的精彩花絮與非分段作品不套。判斷在 `server.py` `_section_gallery_class`，測試 `tests/test_section_gallery_class.py`。其他張數（5、7…）最後一排仍會留空。
- **啟用條件**：`sections` 是非空陣列，且 description 至少有一行符合 `^【([^】]+)】(.*)$`。不符合就照舊版面輸出，逐字不變。有 6 鍵案例區塊（background…outcome）的作品不啟用。
- **保底規則**（`server.py` `_plan_work_sections`）：每張圖只出現一次。重複序號只取第一次；超出範圍、非整數的序號忽略；沒被認領的圖放最後的「精彩花絮」，一張都沒有就省略該區塊；找不到對應 label 的段落只顯示文字。序號對應錯只會放錯位置，照片不會消失。
- **後台**：`admin/app.js` 儲存時保留 `sections`，只覆寫表單的 6 個鍵。後台沒有編輯 `sections` 的介面，改序號要直寫 DB（UPDATE 帶舊值條件、交易內驗證序號 1～N 各一次）。
- **`"wide": true`（2026-11-02 起）**：段落物件加 `"wide": true`，該段圖庫改單欄，圖片依原比例完整顯示，不裁成 4:3（div 多一個 `works-gallery--wide` class，燈箱照常收圖）。用在說明圖、設計稿這類不能裁切的圖。值必須是 JSON `true`，字串 `"true"` 不算。
- **範例（蘭雅，23 張，desc v7）**：`{"sections": [{"label": "設計巧思", "images": [2], "wide": true}, {"label": "主背板", "images": [1, 4, 14, 3, 20, 5, 13, 6, 7, 21, 8, 22]}, {"label": "學院錦旗", "images": [9, 10, 23, 11, 12, 15, 16, 17, 18]}, {"label": "舞台", "images": [19]}]}`；description 另有【洽詢】段，沒有配圖。
- **結尾 CTA 要給自己的標題行**（例如「【洽詢】想讓學校的週年慶也有自己的時間故事」）：最後一個標題段會一路收到 description 結尾，CTA 沒有自己的標題行，就會被併進最後一段、排在該段照片前面。`sections` 不必列【洽詢】，沒有對應的段落只顯示文字（蘭雅 desc v6 即此做法）。
- **結尾 CTA 文字（2026-11-02 起全站統一）**：引導讀者按頁面右下浮動按鈕，品牌名寫全「村花弄囍」。範例：「點選「洽詢檔期」，透過村花弄囍 LINE 告訴我們活動日期與場地。」不要寫成「村花囍 LINE」（少「弄」字）；「村花囍茶」是產品名，不在此列。

---

## 5. 鐵律速查

1. **四步儀式**：讀現值核對「名稱與值都一致」→ 寫 → 讀回 → 獨立來源交叉驗證。數字對但名字不對＝立刻停。
2. **純 INSERT** 新列，絕不 UPDATE/DELETE 既有資料。事務包裹，`ON_ERROR_STOP` 出錯自動 rollback。
3. **Windows SSH 傳中文**：scp 傳檔 或 UTF-8 base64；**禁** here-string / stdin / pipe。
4. **憑證**：主機 peer-auth + rclone 已設定，無明文；本文檔與 commit 不得出現任何密碼。
5. 轉檔記得 `exif_transpose`（server.py 未做，直傳 admin 會躺倒豎圖，本 SOP 手動補正）。
6. 上架後**視覺驗收**：Read 幾張 webp + 開 `/works/{id}` 確認方向、順序、封面對。
7. **description 存純文字**（前端 `textContent` + CSS `white-space:pre-wrap`），段落用**空行**分隔，**嚴禁 `<p>`／HTML 標籤**——否則會原樣顯示成文字（2026-07-06 踩坑）。SSR `/works/{id}` 由 server.py 自己包一層 `<p class="works-desc">`，你只需給乾淨純文字。
8. **覆蓋既有圖檔（同名重傳）後必須 CF purge**：R2 CDN 對 GET 快取 4 小時（HEAD 會顯示 DYNAMIC，不可信），用 `~/.claude/.cf-env` 的 `CLOUDFLARE_PURGE_TOKEN_MULTI` 對該批 URL 定點 purge，再以對外 GET 的 `size_download` 對本機檔案大小逐檔比對（2026-09-30 The Roman 擴圖實踩）。
9. **改 DB 或文案後，必須 purge 該頁、首頁、服務頁的 HTML 邊緣快取**（2026-10-05 起 CF Cache Rule 對 `/`、`/works/*`、`/services/*` 的 HTML 快取 300 秒）：新增作品、改 `articles` 欄位、改服務頁文案後，用 `~/.claude/.cf-env` 的 `CLOUDFLARE_PURGE_TOKEN_MULTI` 對 `POST /zones/${CLOUDFLARE_ZONE_ID_WEDDINGWISHLOVE}/purge_cache` 帶 `{"files":[".../works/<id>", ".../", ".../services/<該分類>/"]}`（新增作品要清首頁與其分類服務頁，因為兩頁都有作品清單），再對外 GET 兩次確認新內容。不 purge 最多舊 5 分鐘，會自然過期。規則本體與坑見 `~/.claude/refs/ach-clawhome.md`「goodjob HTML 邊緣快取」。
10. **description 用「【段落標題】」分段時，第一段要夠長**：`server.py` `_meta_summary` 先把全文壓成單行，再在前 160 字內收到**最後一個**「。！？」。第一段太短時，視窗會吃進下一段的「【標題】」和第一句，標題與內文被接成一句，出現在 meta／og／twitter／JSON-LD 共 4 處。第一段約 125 字以上，且「第一段＋空格＋下一段到第一個句末標點」超過 160 字，摘要才會收在第一段的句末標點。上架前用同一份函式模擬一次：`python -c "import server; print(server._meta_summary(open('desc.txt',encoding='utf-8').read().strip()))"`（在 repo 根目錄跑），確認摘要不含「【」。2026-11-02 蘭雅案例：分段版第一段 106 字，摘要 146 字，結尾吃進「【主背板】一道時空裂縫，隔開兩個年代 背板窗外…」；第一段補一句「現場分成主背板、學院錦旗與舞台三個區塊。」後，摘要 126 字、收在第一段，HTML 內「【主背板】」只剩正文 1 次。
11. **刪圖或重新編號後，必須同步更新 `case_blocks.sections` 的序號**（序號＝position+1）。沒改的話，照片會跑到錯的段落或掉進最後的精彩花絮（見 4-1 保底規則）。
12. **同名覆蓋或重新編號的圖片，CF purge 清不到訪客瀏覽器的快取**：R2 圖片 `Cache-Control: max-age=14400`，訪客瀏覽器最多 4 小時仍顯示舊圖。DB 網址要加 `?v=日期字母`（例：`-2.webp?v=20261102c`），或改用新檔名。`hero_image` 與 position 0 要同步改，維持兩者相等。2026-11-02 蘭雅案例：一天內重新編號三次，村長瀏覽器仍顯示舊的 `-2.webp`，第 2～23 張加 `?v=20261102c` 解決。
