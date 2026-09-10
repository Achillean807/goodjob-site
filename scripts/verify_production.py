#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗收員腳本：驗證 goodjob.weddingwishlove.com 全部作品頁 SSR 內容
輸出：表格格式檢驗結果
"""

import json
import re
import subprocess
import sys
import io
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Windows 編碼修復
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "https://goodjob.weddingwishlove.com"
API_ENDPOINT = f"{BASE_URL}/api/articles"

# 簡體字檢測正則
SIMPLIFIED_CHARS = re.compile(r'[设务场动艺术体历实进画图规办]')

@dataclass
class VerifyResult:
    slug: str
    category: str
    passed: bool
    errors: List[str]

def fetch_articles() -> List[dict]:
    """從 API 取得 64 篇作品"""
    try:
        result = subprocess.run(
            ['curl', '-s', f'{API_ENDPOINT}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        data = json.loads(result.stdout)
        articles = data.get('articles', [])
        print(f"✓ 取得 {len(articles)} 篇作品")
        return articles
    except Exception as e:
        print(f"✗ 無法取得作品清單：{e}")
        return []

def verify_article(article: dict) -> VerifyResult:
    """驗證單篇作品頁"""
    slug = article.get('slug') or article.get('id')
    category = article.get('category', 'unknown')

    url = f"{BASE_URL}/works/{slug}"
    errors = []

    try:
        # 取頁面（禁快取）
        result = subprocess.run(
            ['curl', '-s', '-H', 'Cache-Control: no-cache', url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )

        content = result.stdout

        # 檢查 HTTP 狀態（curl 無狀態碼直接取，用另一個請求確認）
        status_result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-H', 'Cache-Control: no-cache', url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        status_code = status_result.stdout.strip()

        if status_code != '200':
            errors.append(f"HTTP {status_code}")

        # 檢查 works-pillar 恰好 1 次
        pillar_count = content.count('class="works-pillar"')
        if pillar_count != 1:
            errors.append(f"works-pillar 出現 {pillar_count} 次（應為 1 次）")

        # 檢查 pillar 連結與分類對應
        if pillar_count == 1:
            category_map = {
                'business': '/services/business-event/',
                'party': '/services/party-spring-banquet/',
                'magic': '/services/magic-academy/',
                'civil': '/services/civil-makeover/'
            }
            expected_url = category_map.get(category, '')
            if expected_url and expected_url not in content:
                errors.append(f"pillar 連結缺失或不符（分類 {category}→{expected_url}）")

        # 檢查 JSON-LD
        json_ld_blocks = re.findall(r'<script type="application/ld\+json">(.+?)</script>', content, re.DOTALL)
        for i, block in enumerate(json_ld_blocks):
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                errors.append(f"JSON-LD 區塊 {i} 解析失敗：{e}")

        # 檢查 \r（CR 字元）
        if '\r' in content:
            cr_count = content.count('\r')
            errors.append(f"包含 {cr_count} 個 CR 字元")

        # 檢查簡體字
        if SIMPLIFIED_CHARS.search(content):
            matches = SIMPLIFIED_CHARS.findall(content)
            errors.append(f"含簡體字：{set(matches)}")

    except Exception as e:
        errors.append(f"請求異常：{e}")

    return VerifyResult(
        slug=slug,
        category=category,
        passed=len(errors) == 0,
        errors=errors
    )

def verify_llms_txt() -> Tuple[bool, List[str]]:
    """驗證 /llms.txt 含「不承接」3 次"""
    errors = []
    try:
        result = subprocess.run(
            ['curl', '-s', f'{BASE_URL}/llms.txt'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        content = result.stdout
        count = content.count('不承接')
        if count < 3:
            errors.append(f"llms.txt 「不承接」出現 {count} 次（應 ≥3 次）")
    except Exception as e:
        errors.append(f"llms.txt 請求異常：{e}")

    return len(errors) == 0, errors

def verify_sitemap() -> Tuple[int, List[str]]:
    """驗證 /sitemap.xml 內 <loc> 數量"""
    errors = []
    loc_count = 0
    try:
        result = subprocess.run(
            ['curl', '-s', f'{BASE_URL}/sitemap.xml'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        content = result.stdout
        loc_tags = re.findall(r'<loc>([^<]+)</loc>', content)
        loc_count = len(loc_tags)
    except Exception as e:
        errors.append(f"sitemap.xml 請求異常：{e}")

    return loc_count, errors

def main():
    print("=" * 70)
    print("【村山良作 goodjob.weddingwishlove.com 作品頁 SSR 驗收】")
    print("=" * 70)
    print()

    # 1. 取作品清單
    articles = fetch_articles()
    if not articles:
        print("✗ 無法取得作品清單，中止驗收")
        return

    total_count = len(articles)

    # 2. 驗證每篇作品頁（並行）
    print(f"\n開始驗收 {total_count} 篇作品頁（並行）...\n")
    results: List[VerifyResult] = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(verify_article, article): article for article in articles}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            article = futures[future]
            slug = article.get('slug') or article.get('id')
            result = future.result()
            results.append(result)
            status = "✓ 通過" if result.passed else f"✗ 失敗 ({len(result.errors)} 項)"
            print(f"[{completed:2d}/{total_count}] {slug:40} {status}", flush=True)

    # 3. 驗證 llms.txt
    print(f"\n驗證 /llms.txt...", end=" ", flush=True)
    llms_passed, llms_errors = verify_llms_txt()
    print("✓ 通過" if llms_passed else f"✗ 失敗")
    if llms_errors:
        for err in llms_errors:
            print(f"  └ {err}")

    # 4. 驗證 sitemap.xml
    print(f"驗證 /sitemap.xml...", end=" ", flush=True)
    sitemap_count, sitemap_errors = verify_sitemap()
    print(f"✓ 通過（{sitemap_count} 個 <loc>）")
    if sitemap_errors:
        for err in sitemap_errors:
            print(f"  └ {err}")

    # 5. 統計與輸出表格
    print("\n" + "=" * 70)
    print("【驗收結果表格】")
    print("=" * 70)

    passed_count = sum(1 for r in results if r.passed)
    failed_results = [r for r in results if not r.passed]

    print(f"\n總篇數：{total_count}")
    print(f"全通過篇數：{passed_count}")
    print(f"失敗篇數：{len(failed_results)}")

    if failed_results:
        print("\n【失敗清單】")
        print("-" * 70)
        print(f"{'Slug':<40} | {'分類':<8} | {'失敗項'}")
        print("-" * 70)
        for result in failed_results:
            errors_str = " | ".join(result.errors)
            print(f"{result.slug:<40} | {result.category:<8} | {errors_str}")
    else:
        print("\n✓ 所有作品頁驗收通過！")

    print("\n" + "=" * 70)

    # 6. 最終判定
    all_passed = passed_count == total_count and llms_passed and sitemap_count >= 64
    final_status = "✓ PASS" if all_passed else "✗ FAIL"
    print(f"\n【最終結果】{final_status}")
    print("=" * 70)

    if not all_passed:
        if passed_count < total_count:
            print(f"⚠ 作品頁驗收未全通過（{len(failed_results)} 篇失敗）")
        if not llms_passed:
            print(f"⚠ llms.txt 驗證未通過")
        if sitemap_count < 64:
            print(f"⚠ sitemap.xml 地址數不足（{sitemap_count} < 64）")

if __name__ == '__main__':
    main()
