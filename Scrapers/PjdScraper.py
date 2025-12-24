import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

RSS_URL_TEMPLATE = "https://www.pjd.ma/feed?page={page}"
OUTPUT_FILE = "feed_all_pages.json"


def fetch_rss(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def parse_rss_items(xml_text: str) -> List[Dict]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        items.append({
            "title": item.findtext("title"),
            "link": item.findtext("link"),
            "description": item.findtext("description"),
            "pubDate": item.findtext("pubDate"),
            "guid": item.findtext("guid"),
            "categories": [c.text for c in item.findall("category")]
        })

    return items


def load_existing_items(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_items(path: Path, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def crawl_all_pages():
    output_path = Path(OUTPUT_FILE)
    all_items = load_existing_items(output_path)

    page = 1

    while True:
        url = RSS_URL_TEMPLATE.format(page=page)
        xml_data = fetch_rss(url)
        page_items = parse_rss_items(xml_data)

        if not page_items:
            break

        all_items.extend(page_items)
        save_items(output_path, all_items)

        print(f"[+] Page {page}: saved {len(page_items)} items "
              f"(total: {len(all_items)})")

        page += 1


if __name__ == "__main__":
    crawl_all_pages()
