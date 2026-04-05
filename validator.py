import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path

MATCH_URL = "https://www.mlssoccer.com/competitions/mls-regular-season/2025/matches/nshvsmia-10-18-2025/"
FEED_FILE = "clean_feed.xml"

#################################################
# Normalize text
#################################################

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()

#################################################
# Fetch webpage
#################################################

def fetch_match_page_html(url):
    print("Fetching MLS webpage...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=120000
        )

        page.wait_for_timeout(5000)

        html = page.content()
        print("HTML length:", len(html))

        browser.close()

    return html

#################################################
# Extract website events
#################################################

def extract_website_events(html):
    print("Extracting website events...")

    soup = BeautifulSoup(html, "html.parser")

    events = []
    seen = set()

    full_text = soup.get_text("\n")
    lines = full_text.split("\n")

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if len(line) > 120:
            continue

        if re.search(r"\d{1,3}'", line):
            clean = normalize_text(line)

            if clean not in seen:
                seen.add(clean)
                events.append(line)

    return events

#################################################
# Extract XML feed events
#################################################

def extract_feed_events():
    print("Reading feed file...")

    raw_text = Path(FEED_FILE).read_text(
        encoding="utf-8",
        errors="ignore"
    )

    events = []

    matches = re.findall(
        r'EventTime="([^"]+)"[^>]*EventId="([^"]+)"',
        raw_text,
        re.IGNORECASE
    )

    for event_time, event_id in matches:
        events.append(f"{event_time} | {event_id}")

    return events

#################################################
# Compare events
#################################################

def compare_events(web_events, feed_events):
    matched = []
    missing = []

    for web_event in web_events:
        web_clean = normalize_text(web_event)
        found = False

        for feed_event in feed_events:
            feed_clean = normalize_text(feed_event)

            if web_clean and web_clean in feed_clean:
                matched.append((web_event, feed_event))
                found = True
                break

        if not found:
            missing.append(web_event)

    return matched, missing

#################################################
# Print report
#################################################

def print_report(website_events, feed_events, matched, missing):
    print("\n================================================")
    print("VALIDATION REPORT")
    print("================================================")

    print("Website events found:", len(website_events))
    print("PutDataRequest items found:", len(feed_events))
    print("Matched items:", len(matched))
    print("Missing website events in XML:", len(missing))

    if len(website_events) == 0:
        print("\nWARNING: No website events detected")

    print("\nPASS Items:")
    if matched:
        for web_event, feed_event in matched[:10]:
            print(f"PASS: {web_event}")
            print(f"      XML: {feed_event}")
    else:
        print("No matches found.")

    print("\nFAIL Items:")
    if missing:
        for item in missing[:10]:
            print(f"FAIL: {item}")
    else:
        print("No missing items found.")

#################################################
# Main execution
#################################################

def main():
    html = fetch_match_page_html(MATCH_URL)
    website_events = extract_website_events(html)
    feed_events = extract_feed_events()

    matched, missing = compare_events(
        website_events,
        feed_events
    )

    print_report(
        website_events,
        feed_events,
        matched,
        missing
    )

#################################################

if __name__ == "__main__":
    main()