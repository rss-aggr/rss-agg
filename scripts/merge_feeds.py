import feedparser
import requests
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import os

FEED_GROUPS = {
    "ai": [
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "https://oneusefulthing.substack.com/feed",
        "https://simonwillison.net/tags/ai.atom",
        "https://rsshub.bestblogs.dev/deeplearning/the-batch",
        "https://tldr.tech/api/rss/ai",
    ],
    "seo": [
        "https://www.growth-memo.com/feed",
        "http://feeds.searchengineland.com/searchengineland",
    ],
    "accessibility": [
        "https://medium.com/feed/tag/accessibility",
        "http://adrianroselli.com/feed",
        "https://www.matuzo.at/feed.xml",
        "http://webaim.org/blog/feed",
        "https://medium.com/feed/design-ibm/tagged/accessibility",
        "https://www.smashingmagazine.com/categories/accessibility/index.xml",
        "https://blogs.microsoft.com/accessibility/feed/",
        "https://www.sarasoueidan.com/blog/index.xml",
        "http://www.scottohara.me/feed.xml",
        "https://www.a11yproject.com/feed/feed.xml",
        "http://www.tpgi.com/feed/",
        "http://www.deque.com/feed",
        "http://www.w3.org/QA/atom.xml",
        "http://www.w3.org/2000/08/w3c-synd/home.rss",
    ],
}

OUTPUT_DIR = "feeds"


def fetch_feed(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSSAggregator/1.0)"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None


def build_rss(entries, title):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = "https://github.com"
    SubElement(channel, "description").text = f"Combined feed: {title}"
    SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    for entry in entries:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = entry.get("title", "No title")
        SubElement(item, "link").text = entry.get("link", "")
        SubElement(item, "description").text = entry.get("summary", "")
        SubElement(item, "guid").text = entry.get("id", entry.get("link", ""))

        published = entry.get("published", "") or entry.get("updated", "")
        if published:
            SubElement(item, "pubDate").text = published

    xml_str = minidom.parseString(tostring(rss, encoding="unicode")).toprettyxml(
        indent="  "
    )
    # Remove extra XML declaration added by toprettyxml
    lines = xml_str.split("\n")
    return "\n".join(lines[1:])


def merge_group(group_name, urls):
    print(f"\nProcessing: {group_name}")
    all_entries = []

    for url in urls:
        print(f"  Fetching: {url}")
        feed = fetch_feed(url)
        if feed and feed.entries:
            print(f"    Got {len(feed.entries)} entries")
            all_entries.extend(feed.entries)
        else:
            print(f"    No entries found")

    # Sort by published date, newest first
    def get_date(entry):
        date_str = entry.get("published_parsed") or entry.get("updated_parsed")
        if date_str:
            try:
                return datetime(*date_str[:6], tzinfo=timezone.utc)
            except Exception:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    all_entries.sort(key=get_date, reverse=True)

    # Keep max 100 most recent entries
    all_entries = all_entries[:100]

    print(f"  Total entries after merge: {len(all_entries)}")

    titles = {
        "ai": "AI Combined Feed",
        "seo": "SEO/AEO Combined Feed",
        "accessibility": "Accessibility Combined Feed",
    }

    xml_content = build_rss(all_entries, titles.get(group_name, group_name))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{group_name}_combined.xml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"  Saved to {output_path}")


def main():
    for group_name, urls in FEED_GROUPS.items():
        merge_group(group_name, urls)
    print("\nDone.")


if __name__ == "__main__":
    main()
