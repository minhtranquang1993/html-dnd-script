#!/usr/bin/env python3
"""
Fetch https://matquoctednd.vn/post-sitemap.xml, filter out non-knowledge posts
(events, workshops, promos, news, KOL reviews), and append new knowledge articles
to references/internal-links.json.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple

SITEMAP_URL = "https://matquoctednd.vn/post-sitemap.xml"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Slug tokens that indicate non-knowledge articles (events, promos, news, reviews)
EXCLUDED_SLUG_PATTERNS = [
    r"^\d+(-\d+)*$",
    r"\b\d{1,2}-\d{1,2}-20\d{2}\b",
    r"\bworkshop\b",
    r"\bhoi-thao\b",
    r"\bhtkx\b",
    r"\brecap\b",
    r"\btalkshow\b",
    r"\bhoi-nghi\b",
    r"\bapao\b",
    r"\bvos-\d+\b",
    r"\bhorizon-\d+\b",
    r"\bsymposium\b",
    r"\ble-khanh-thanh\b",
    r"\bkhanh-thanh\b",
    r"\bkhai-truong\b",
    r"\ble-ky-ket\b",
    r"\bra-mat-trung-tam\b",
    r"\btong-ket-hoi-thao\b",
    r"\bbao-cao-khoa-hoc\b",
    r"\bsmile-days?\b",
    r"\bfemto-days?\b",
    r"\bmung-sinh-nhat\b",
    r"\bvoucher\b",
    r"\bvalentine\b",
    r"\bmung-thang\b",
    r"\buu-dai\b",
    r"\bthang-vang\b",
    r"\bbo-kinh-can-tang-kinh-mat\b",
    r"\bboc-tham\b",
    r"\blich-lam-viec\b",
    r"\bnghi-tet\b",
    r"\bdua-phong-mo-len-non-cao\b",
    r"\bmat-sang-cong-dong\b",
    r"\bmat-sang-nguoi-cao-tuoi\b",
    r"\bmat-sang-cho-nguoi-cao-tuoi\b",
    r"\bhuman-act-prize\b",
    r"\bkmols-awards\b",
    r"\bvinh-danh\b",
    r"\balobacsi-dua-tin\b",
    r"\bdai-truyen-hinh\b",
    r"\btruong-thpt\b",
    r"\bkhong-gian-kham-chua-benh\b",
    r"\bdoi-ngu-tu-van-cham-soc-khach-hang\b",
    r"\bstreamer-\b",
    r"\btiktoker-\b",
    r"\bmc-thu-ha\b",
    r"\breview-mo-can\b",
    r"\bquyen-doan\b",
    r"\bkat-luu\b",
    r"\btruc-ly\b",
    r"\bhai-yen-mo-can\b",
    r"\bmie-cua-linh\b",
    r"\ble-thi-thu-ha\b",
    r"\bditi-thoat-kinh\b",
    r"\bquang-my-thien\b",
    r"\bteam-can-noi-gi\b",
    r"^giai-ma-phau-thuat-khuc-xa-hanh-trinh-thoat-kinh-trong-24h$",
    r"^kham-va-tam-soat-toan-dien-suc-khoe-doi-mat$",
]

EXCLUDED_TITLE_PATTERNS = [
    r"\bworkshop\b",
    r"\bhội thảo\b",
    r"\bhtkx\b",
    r"\btalkshow\b",
    r"\brecap\b",
    r"\bưu đãi\b",
    r"\bkhuyến mãi\b",
    r"\bvoucher\b",
    r"\bmùa vu lan\b",
    r"\bnghỉ tết\b",
    r"\bkhai trương\b",
    r"\bkhánh thành\b",
    r"\blễ ký kết\b",
    r"\bvinh danh\b",
    r"\bhội nghị\b",
    r"\bbốc thăm\b",
]


def is_excluded_slug(slug: str) -> bool:
    for pat in EXCLUDED_SLUG_PATTERNS:
        if re.search(pat, slug, flags=re.IGNORECASE):
            return True
    return False


def is_excluded_title(title: str) -> bool:
    for pat in EXCLUDED_TITLE_PATTERNS:
        if re.search(pat, title, flags=re.IGNORECASE):
            return True
    return False


def fetch_url(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_sitemap_vi_urls(xml_text: str) -> List[str]:
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: List[str] = []
    for el in root.findall(".//sm:loc", ns):
        if not el.text:
            continue
        u = el.text.strip()
        if "/en/" in u or u.rstrip("/") == "https://matquoctednd.vn/tin-tuc":
            continue
        urls.append(u)
    return urls


def fetch_article_title(url: str, fallback_slug: str) -> str:
    try:
        page = fetch_url(url, timeout=10)
        m_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S | re.I)
        if m_h1:
            raw = html.unescape(re.sub(r"<[^>]+>", "", m_h1.group(1)).strip())
            raw = re.sub(r"\s+", " ", raw)
            if raw:
                return raw
        m_title = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
        if m_title:
            raw = html.unescape(m_title.group(1).strip())
            raw = re.sub(r"\s*[-|–]\s*Bệnh viện Mắt.*$", "", raw, flags=re.I)
            raw = re.sub(r"\s+", " ", raw)
            if raw:
                return raw
    except Exception:
        pass
    return fallback_slug.replace("-", " ").capitalize()


def infer_topics_and_keywords(title: str, slug: str) -> Tuple[List[str], List[str]]:
    text = f"{title.lower()} {slug.replace('-', ' ').lower()}"
    topics: List[str] = []

    if any(k in text for k in ["đục thủy tinh thể", "duc thuy tinh the", "cườm khô", "cuom kho", "phaco", "thủy tinh thể", "kinh noi nhan", "kính nội nhãn"]):
        topics.append("phaco")
    if any(k in text for k in ["lão thị", "lao thi"]):
        topics.append("lao-thi")
    if any(k in text for k in ["giác mạc", "giac mac"]):
        topics.append("giac-mac")
    if any(k in text for k in ["võng mạc", "vong mac", "đáy mắt", "day mat", "chụp oct", "chup oct"]):
        topics.append("vong-mac")
    if any(k in text for k in ["siêu âm mắt", "sieu am mat", "chẩn đoán hình ảnh", "chụp ảnh đáy mắt"]):
        topics.append("chan-doan")
    if any(
        k in text
        for k in [
            "cận thị",
            "can thi",
            "cận nặng",
            "can nang",
            "tái cận",
            "tai can",
            "mổ cận",
            "mo can",
            "mổ mắt",
            "mo mat",
            "thoát cận",
            "thoat can",
            "khúc xạ",
            "khuc xa",
            "loạn thị",
            "loan thi",
            "viễn thị",
            "vien thi",
            "smile pro",
            "smartsight",
            "femto",
            "lasik",
            "phakic",
        ]
    ):
        topics.append("khuc-xa")

    if not topics:
        topics.append("general")

    # Build concise Vietnamese keywords from title
    clean_title = re.split(r"[?:–\-|]", title)[0].strip().lower()
    clean_title = re.sub(r"\s+tại\s+dnd.*$", "", clean_title, flags=re.I).strip()
    keywords: List[str] = []
    if clean_title and len(clean_title) <= 60:
        keywords.append(clean_title)

    keyword_candidates = [
        ("mổ cận có đau không", ["mổ cận có đau không", "mổ cận", "phẫu thuật khúc xạ"]),
        ("cận nặng", ["cận nặng có mổ mắt được không", "cận nặng", "mổ mắt cận"]),
        ("cận thị 1 bên mắt", ["cận thị 1 bên mắt", "cận lệch", "cận thị"]),
        ("tái cận", ["mổ mắt có bị tái cận không", "tái cận", "mổ cận thị"]),
        ("giác mạc mỏng", ["giác mạc mỏng có mổ cận được không", "giác mạc mỏng", "mổ cận"]),
        ("mổ lão thị", ["mổ lão thị giá bao nhiêu", "mổ lão thị", "chi phí mổ lão thị"]),
        ("điều trị lão thị", ["điều trị lão thị", "phương pháp điều trị lão thị", "lão thị"]),
        ("di truyền", ["cận thị có di truyền không", "cận thị di truyền", "cận thị"]),
        ("tiểu đường", ["đục thủy tinh thể ở người tiểu đường", "đục thủy tinh thể", "tiểu đường"]),
        ("cườm khô", ["cườm khô", "đục thủy tinh thể"]),
        ("đục thủy tinh thể", ["đục thủy tinh thể", "mổ đục thủy tinh thể"]),
        ("lão thị", ["lão thị", "điều trị lão thị"]),
        ("loạn thị", ["loạn thị", "điều trị loạn thị"]),
        ("viễn thị", ["viễn thị", "điều trị viễn thị"]),
        ("nhược thị", ["nhược thị", "điều trị nhược thị"]),
        ("giác mạc", ["giác mạc", "bệnh lý giác mạc"]),
        ("võng mạc", ["võng mạc", "bệnh lý võng mạc"]),
        ("khô mắt", ["khô mắt", "điều trị khô mắt"]),
        ("mổ cận", ["mổ cận", "phẫu thuật khúc xạ"]),
        ("cận thị", ["cận thị", "điều trị cận thị"]),
    ]
    for trigger, kw_list in keyword_candidates:
        if trigger in title.lower():
            for kw in kw_list:
                if kw not in keywords:
                    keywords.append(kw)
            break

    if not keywords:
        keywords.append(slug.replace("-", " "))

    return topics, keywords[:4]


def format_internal_links_json(data: dict) -> str:
    lines = ["{"]
    note = json.dumps(data.get("_note", ""), ensure_ascii=False)
    lines.append(f'  "_note": {note},')
    if "_updated_at" in data:
        updated = json.dumps(data["_updated_at"], ensure_ascii=False)
        lines.append(f'  "_updated_at": {updated},')
    lines.append('  "articles": [')
    articles = data.get("articles", [])
    for idx, art in enumerate(articles):
        comma = "," if idx < len(articles) - 1 else ""
        art_str = (
            f'    {{ "url": {json.dumps(art["url"], ensure_ascii=False)}, '
            f'"title": {json.dumps(art["title"], ensure_ascii=False)}, '
            f'"topics": {json.dumps(art["topics"], ensure_ascii=False)}, '
            f'"keywords": {json.dumps(art["keywords"], ensure_ascii=False)} }}{comma}'
        )
        lines.append(art_str)
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Update internal-links.json from matquoctednd.vn/post-sitemap.xml")
    parser.add_argument(
        "--json-path",
        default=str(Path(__file__).resolve().parent.parent / "references" / "internal-links.json"),
        help="Path to references/internal-links.json",
    )
    parser.add_argument(
        "--sitemap-url",
        default=SITEMAP_URL,
        help="Sitemap URL (default: https://matquoctednd.vn/post-sitemap.xml)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview new articles without writing file")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(json.dumps({"ok": False, "error": f"File not found: {json_path}"}, ensure_ascii=False))
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles: List[Dict] = data.get("articles", [])
    existing_urls: Set[str] = {a["url"].rstrip("/") + "/" for a in articles}

    try:
        xml_text = fetch_url(args.sitemap_url, timeout=15)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"Failed to fetch sitemap: {exc}"}, ensure_ascii=False))
        return 1

    vi_urls = extract_sitemap_vi_urls(xml_text)
    added_articles: List[Dict] = []
    skipped_non_knowledge = 0

    for u in vi_urls:
        norm_u = u.rstrip("/") + "/"
        if norm_u in existing_urls:
            continue
        slug = norm_u.rstrip("/").split("/")[-1]
        if is_excluded_slug(slug):
            skipped_non_knowledge += 1
            continue

        title = fetch_article_title(norm_u, slug)
        if is_excluded_title(title):
            skipped_non_knowledge += 1
            continue

        topics, keywords = infer_topics_and_keywords(title, slug)
        new_entry = {
            "url": norm_u,
            "title": title,
            "topics": topics,
            "keywords": keywords,
        }
        articles.append(new_entry)
        existing_urls.add(norm_u)
        added_articles.append(new_entry)

    if not args.dry_run and added_articles:
        data["articles"] = articles
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(format_internal_links_json(data))

    result = {
        "ok": True,
        "sitemap_url": args.sitemap_url,
        "total_sitemap_vi_urls": len(vi_urls),
        "skipped_non_knowledge": skipped_non_knowledge,
        "added_count": len(added_articles),
        "total_articles": len(articles),
        "added_articles": added_articles,
        "dry_run": args.dry_run,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
