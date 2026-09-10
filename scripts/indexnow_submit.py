# -*- coding: utf-8 -*-
"""IndexNow 提交器：抓正式站 sitemap.xml 的頁面網址，一次推送給 IndexNow。

只用標準函式庫（urllib / xml.etree），不引入任何第三方套件。

用法：
    python scripts/indexnow_submit.py --dry-run   # 只印抓到幾條，不送出
    python scripts/indexnow_submit.py             # 真的 POST
    python scripts/indexnow_submit.py --key <32位hex>  # 覆蓋自動偵測
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

# Windows 主控台預設 cp950，中文／emoji 會噴 UnicodeEncodeError，強制轉 UTF-8
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

HOST = "goodjob.weddingwishlove.com"
SITE = f"https://{HOST}"
SITEMAP_URL = f"{SITE}/sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE_RE = re.compile(r"^[0-9a-f]{32}\.txt$")
# Cloudflare 會擋掉 urllib 預設的 "Python-urllib/3.x" UA 回 403（實測），要自報名號
USER_AGENT = "murayama-goodjob-indexnow/1.0 (+https://goodjob.weddingwishlove.com/)"


def find_key_file():
    """掃描 repo 根目錄，找出 IndexNow 金鑰檔（檔名即金鑰）。回傳 (檔名, 金鑰)。"""
    names = sorted(n for n in os.listdir(REPO_ROOT) if KEY_FILE_RE.match(n))
    if not names:
        raise SystemExit(f"找不到金鑰檔：{REPO_ROOT} 下沒有符合 ^[0-9a-f]{{32}}\\.txt$ 的檔案")
    if len(names) > 1:
        raise SystemExit(f"根目錄有多個金鑰檔，請用 --key 指定：{names}")
    with open(os.path.join(REPO_ROOT, names[0]), "rb") as fh:
        return names[0], fh.read().decode("utf-8").strip()


def extract_locs(xml_bytes):
    """取出 sitemap 的頁面網址。

    只認 <url>／<sitemap> 的「直接子層」<loc>；<image:loc> 巢狀在
    <image:image> 裡屬於孫層，結構上就抓不到——本 repo 之前用寬鬆字串比對
    誤把圖片網址一起抓進來過（2026-09-10 踩坑），故改用結構比對。
    """
    root = ET.fromstring(xml_bytes)
    locs = []
    for entry in root:
        for child in entry:
            if child.tag.rpartition("}")[2] == "loc" and child.text:
                locs.append(child.text.strip())
                break  # 一個 <url> 只取第一個 <loc>
    return locs


def submit(urls, key, key_filename):
    """把網址清單 POST 給 IndexNow，回傳 (狀態碼, 回應內容)。"""
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"{SITE}/{key_filename}",
        "urlList": urls,
    }
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        # IndexNow 用 4xx 表達「金鑰不符／格式錯」，要看得到 body 才知道原因
        return exc.code, exc.read().decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser(description="提交 sitemap 網址給 IndexNow")
    ap.add_argument("--dry-run", action="store_true", help="只印抓到幾條網址，不送出")
    ap.add_argument("--key", help="覆蓋自動偵測的金鑰（32 位 hex）")
    args = ap.parse_args()

    if args.key:
        key, key_filename = args.key, f"{args.key}.txt"
    else:
        key_filename, key = find_key_file()

    sitemap_req = urllib.request.Request(SITEMAP_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(sitemap_req, timeout=30) as resp:
        urls = extract_locs(resp.read())

    print(f"sitemap：{SITEMAP_URL}")
    print(f"抓到 {len(urls)} 條頁面網址（已排除 <image:loc> 圖片網址）")
    print(f"金鑰檔：{key_filename}　keyLocation：{SITE}/{key_filename}")

    if args.dry_run:
        # ponytail: --dry-run 就是本檔的自我檢查——抓取＋解析全跑過，只跳過送出
        print("[dry-run] 未送出。")
        return

    if not urls:
        raise SystemExit("網址清單是空的，不送出。")

    status, body = submit(urls, key, key_filename)
    print(f"HTTP {status}")
    print(body or "(回應 body 為空)")


if __name__ == "__main__":
    main()
