-- 村山良作 — articles 加 slug 語意化網址欄位（2026-07-30）
--
-- 目的：38 篇「8 位 hex 亂碼 id」的作品改用語意化 URL /works/{slug}。
--       id 欄位不動（它同時是 R2 圖片路徑 works/{id}/… 與前端 hash routing 的 key）。
--       26 篇 id 已語意化的作品刻意不填 slug，維持原網址、不產生無謂 301。
--
-- 目標：PostgreSQL `goodjob_site`（正式站 runtime 資料源）。SQLite 開發庫由
--       server.py 的 _init_db() 自動補欄位與索引，不需要跑這支。
--
-- 部署時序：先跑這支 SQL 或先上 server.py 都安全（兩邊都用 IF NOT EXISTS，
--          且唯一索引名一致為 articles_slug_key，先後執行都收斂到同一結果）。
--
-- 用法（在龍蝦之家主機上走 peer-auth，免明文憑證）：
--   psql -d goodjob_site -v ON_ERROR_STOP=1 -f scripts/add-slug-20260730.sql

BEGIN;

-- 1) 欄位與唯一索引 --------------------------------------------------------
-- 唯一性用具名索引而非 ADD COLUMN ... UNIQUE，才能和 server.py 的
-- CREATE UNIQUE INDEX IF NOT EXISTS articles_slug_key 對齊（PG 對 UNIQUE 欄位
-- 自動產生的索引名正好也是 articles_slug_key）。NULL 在唯一索引下互不相衝，
-- 所以 26 篇沒填 slug 的作品可以同時存在。
ALTER TABLE articles ADD COLUMN IF NOT EXISTS slug TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS articles_slug_key ON articles (slug);

-- 2) 38 篇 slug ------------------------------------------------------------
-- 魔法學院 magic
UPDATE articles SET slug='maritime-magic-academy-party'    WHERE id='c35fa390';
UPDATE articles SET slug='flora-expo-wedding-fair-booth'   WHERE id='3f65f0ab';
UPDATE articles SET slug='academia-sinica-conference-venue' WHERE id='48235c66';
UPDATE articles SET slug='corporate-year-end-gala-dinner'  WHERE id='54da6457';

-- 戶政改造 civil（沿用站內既有 {區名拼音}-civil 慣例）
UPDATE articles SET slug='qidu-civil'               WHERE id='9f7de577';
UPDATE articles SET slug='anle-civil'               WHERE id='d579ef80';
UPDATE articles SET slug='keelung-zhongzheng-civil' WHERE id='95deb3cd';
UPDATE articles SET slug='keelung-xinyi-civil'      WHERE id='27137c13';
UPDATE articles SET slug='xinyi-civil'              WHERE id='bc700965';
UPDATE articles SET slug='linkou-civil'             WHERE id='d42dfa46';
UPDATE articles SET slug='xinzhuang-civil'          WHERE id='62e743ef';
UPDATE articles SET slug='xindian-civil'            WHERE id='7369ddb5';

-- 春酒尾牙 party
UPDATE articles SET slug='qijibang-2023-timewarp-ball'    WHERE id='d65a02f9';
UPDATE articles SET slug='qijibang-2026-wild-beasts-ball' WHERE id='6031ac6a';
UPDATE articles SET slug='yingcun-appreciation-festival'  WHERE id='def9a3d9';
UPDATE articles SET slug='hotel-lunar-new-year-decor'     WHERE id='1c45c415';
UPDATE articles SET slug='corporate-year-end-party-decor' WHERE id='92387fe2';
UPDATE articles SET slug='lianyun-logistics-2024-year-end' WHERE id='9c529934';
UPDATE articles SET slug='lianyun-logistics-2025-year-end' WHERE id='f8b4b9f4';
UPDATE articles SET slug='twtc-corporate-year-end-party'  WHERE id='874c65e1';
UPDATE articles SET slug='auto-brand-year-end-party'      WHERE id='ff14fcca';
UPDATE articles SET slug='nccu-qijiaban-43-welcome-party' WHERE id='6854a5a1';

-- 主題活動 business
UPDATE articles SET slug='love-and-deepspace-shinkong-tour' WHERE id='ee7a6a84';
UPDATE articles SET slug='taichung-baby-expo-booth'         WHERE id='3d9f4fed';
UPDATE articles SET slug='double-happiness-film-set'        WHERE id='42103369';
UPDATE articles SET slug='parenting-brand-expo-booth'       WHERE id='2c7a16f6';
UPDATE articles SET slug='how-dine-hotel-2025-brand-day'     WHERE id='59483d61';
UPDATE articles SET slug='how-dine-hotel-2024-brand-day'     WHERE id='172eeceb';
UPDATE articles SET slug='how-dine-hotel-2023-brand-day'     WHERE id='6d34499b';
UPDATE articles SET slug='how-dine-hotel-2022-brand-day'     WHERE id='33def7c7';
UPDATE articles SET slug='christmas-series-decor'           WHERE id='2c4af1fc';
UPDATE articles SET slug='small-banquet-celebration-party'  WHERE id='5a1e1bc3';
UPDATE articles SET slug='songshan-park-zhiling-popup-store' WHERE id='0e8bdfac';
UPDATE articles SET slug='taroko-market-outdoor-booth'      WHERE id='956cfb73';
UPDATE articles SET slug='nangang-ling-orm-fanmeeting'      WHERE id='56571f26';
UPDATE articles SET slug='auto-brand-new-year-showroom'     WHERE id='81bf85d4';
UPDATE articles SET slug='school-graduation-photo-zone'     WHERE id='f9146762';
UPDATE articles SET slug='yukinonamadonut-counter-display'        WHERE id='d0e7d8c4';

COMMIT;

-- 3) 驗證 ------------------------------------------------------------------
-- 期望：slug_filled = 38
SELECT COUNT(*) AS slug_filled FROM articles WHERE slug IS NOT NULL;

-- 期望：slug_id_collision = 0
-- （任何一篇的 slug 都不可以等於某篇作品的 id，否則 /works/{x} 路由會有歧義）
SELECT COUNT(*) AS slug_id_collision
FROM articles a
WHERE EXISTS (SELECT 1 FROM articles b WHERE b.id = a.slug);

-- 期望：not_updated = 0（確認 38 條 UPDATE 都有打中，沒有打錯 id）
SELECT COUNT(*) AS not_updated
FROM articles
WHERE slug IS NULL
  AND id ~ '^[0-9a-f]{8}$';
