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
| 分類 | `business`（主題活動）/ `party`（春酒尾牙）/ `magic`（魔法學院）/ `civil`（戶政改造） |
| 文案 | 哈雷酱寫初稿 → 村長審（title / slug / description） |

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

---

## 5. 鐵律速查

1. **四步儀式**：讀現值核對「名稱與值都一致」→ 寫 → 讀回 → 獨立來源交叉驗證。數字對但名字不對＝立刻停。
2. **純 INSERT** 新列，絕不 UPDATE/DELETE 既有資料。事務包裹，`ON_ERROR_STOP` 出錯自動 rollback。
3. **Windows SSH 傳中文**：scp 傳檔 或 UTF-8 base64；**禁** here-string / stdin / pipe。
4. **憑證**：主機 peer-auth + rclone 已設定，無明文；本文檔與 commit 不得出現任何密碼。
5. 轉檔記得 `exif_transpose`（server.py 未做，直傳 admin 會躺倒豎圖，本 SOP 手動補正）。
6. 上架後**視覺驗收**：Read 幾張 webp + 開 `/works/{id}` 確認方向、順序、封面對。
7. **description 存純文字**（前端 `textContent` + CSS `white-space:pre-wrap`），段落用**空行**分隔，**嚴禁 `<p>`／HTML 標籤**——否則會原樣顯示成文字（2026-07-06 踩坑）。SSR `/works/{id}` 由 server.py 自己包一層 `<p class="works-desc">`，你只需給乾淨純文字。
