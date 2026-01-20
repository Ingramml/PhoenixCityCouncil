#!/usr/bin/env python3
"""
Parallelized Phoenix City Council meeting data fetcher.
Combines API data with website scraping for complete vote information.

Features:
- Parallel processing using multiprocessing (separate browser per process)
- Configurable number of workers
- Supports both 2020 and 2024 council rosters

Performance: ~2-3x faster than sequential version
"""

import requests
import csv
import time
import re
import argparse
from datetime import datetime
from multiprocessing import Pool, cpu_count
from playwright.sync_api import sync_playwright

BASE_URL = "https://webapi.legistar.com/v1/phoenix"
WEBSITE_BASE = "https://phoenix.legistar.com"

# Council rosters by year
# Note: Phoenix council elections are staggered - odd districts (1,3,5,7) elect in one cycle,
# even districts (2,4,6,8) in another, with Mayor every 4 years
COUNCIL_ROSTERS = {
    2020: {
        "members": [
            "Kate Gallego (Mayor)",
            "Thelda Williams (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Sal DiCiccio (D6)",
            "Michael Nowakowski (D7)",
            "Carlos Garcia (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Thelda Williams": "Thelda Williams (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Sal DiCiccio": "Sal DiCiccio (D6)",
            "Michael Nowakowski": "Michael Nowakowski (D7)",
            "Carlos Garcia": "Carlos Garcia (D8)"
        }
    },
    # 2021 uses same roster as 2020 (no elections changed composition)
    2021: {
        "members": [
            "Kate Gallego (Mayor)",
            "Thelda Williams (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Sal DiCiccio (D6)",
            "Michael Nowakowski (D7)",
            "Carlos Garcia (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Thelda Williams": "Thelda Williams (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Sal DiCiccio": "Sal DiCiccio (D6)",
            "Michael Nowakowski": "Michael Nowakowski (D7)",
            "Carlos Garcia": "Carlos Garcia (D8)"
        }
    },
    2022: {
        "members": [
            "Kate Gallego (Mayor)",
            "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Sal DiCiccio (D6)",
            "Yassamin Ansari (D7)",
            "Carlos Garcia (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Ann O'Brien": "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Sal DiCiccio": "Sal DiCiccio (D6)",
            "Yassamin Ansari": "Yassamin Ansari (D7)",
            "Carlos Garcia": "Carlos Garcia (D8)"
        }
    },
    2023: {
        "members": [
            "Kate Gallego (Mayor)",
            "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Kevin Robinson (D6)",
            "Yassamin Ansari (D7)",
            "Kesha Hodge Washington (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Ann O'Brien": "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Kevin Robinson": "Kevin Robinson (D6)",
            "Yassamin Ansari": "Yassamin Ansari (D7)",
            "Kesha Hodge Washington": "Kesha Hodge Washington (D8)"
        }
    },
    2024: {
        "members": [
            "Kate Gallego (Mayor)",
            "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Kevin Robinson (D6)",
            "Yassamin Ansari (D7)",
            "Kesha Hodge Washington (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Ann O'Brien": "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Kevin Robinson": "Kevin Robinson (D6)",
            "Yassamin Ansari": "Yassamin Ansari (D7)",
            "Kesha Hodge Washington": "Kesha Hodge Washington (D8)"
        }
    },
    # 2025: Anna Hernandez replaced Yassamin Ansari in D7
    2025: {
        "members": [
            "Kate Gallego (Mayor)",
            "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring (D2)",
            "Debra Stark (D3)",
            "Laura Pastor (D4)",
            "Betty Guardado (D5)",
            "Kevin Robinson (D6)",
            "Anna Hernandez (D7)",
            "Kesha Hodge Washington (D8)"
        ],
        "mapping": {
            "Kate Gallego": "Kate Gallego (Mayor)",
            "Ann O'Brien": "Ann O'Brien (D1-Vice Mayor)",
            "Jim Waring": "Jim Waring (D2)",
            "Debra Stark": "Debra Stark (D3)",
            "Laura Pastor": "Laura Pastor (D4)",
            "Betty Guardado": "Betty Guardado (D5)",
            "Kevin Robinson": "Kevin Robinson (D6)",
            "Anna Hernandez": "Anna Hernandez (D7)",
            "Kesha Hodge Washington": "Kesha Hodge Washington (D8)"
        }
    }
}


def fetch_json(url, retries=3):
    """Fetch JSON from URL with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
    return None


def get_events(year, start_month=1, end_month=4):
    """Get City Council Formal Meeting events for specified period."""
    start_date = f"{year}-{start_month:02d}-01"
    end_date = f"{year}-{end_month:02d}-01"
    url = f"{BASE_URL}/events?$filter=EventBodyId eq 138 and EventDate ge datetime'{start_date}' and EventDate lt datetime'{end_date}'&$orderby=EventDate asc"
    print(f"Fetching events from {start_date} to {end_date}...")
    events = fetch_json(url)
    if events:
        print(f"  Found {len(events)} events")
    return events or []


def get_event_items(event_id):
    """Get all agenda items for an event."""
    url = f"{BASE_URL}/events/{event_id}/eventitems"
    return fetch_json(url) or []


def format_date(date_str):
    """Format ISO date to YYYY-MM-DD."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str[:10] if date_str else ""


def extract_index_from_title(title):
    """Extract district/index from item title."""
    if not title:
        return ""
    for i in range(1, 9):
        if f"District {i}" in title:
            return f"District {i}"
    if "Citywide" in title:
        return "Citywide"
    return ""


def extract_link_href(page, text_pattern):
    """Extract href from a link containing the text pattern."""
    try:
        links = page.query_selector_all("a")
        for link in links:
            text = link.text_content() or ""
            if text_pattern.lower() in text.lower():
                href = link.get_attribute("href")
                if href and "View.ashx" in href:
                    if href.startswith("/"):
                        return WEBSITE_BASE + href
                    return href
    except:
        pass
    return ""


def extract_votes_from_popup(page):
    """Extract individual votes from the action details popup."""
    votes = {}
    try:
        frames = page.frames
        for frame in frames:
            try:
                rows = frame.query_selector_all("table tr")
                for row in rows:
                    cells = row.query_selector_all("td")
                    if len(cells) == 2:
                        name = (cells[0].text_content() or "").strip()
                        vote = (cells[1].text_content() or "").strip()
                        if name and vote and name != "Person Name":
                            votes[name] = vote
            except:
                continue
    except:
        pass
    return votes


def scrape_meeting(page, meeting_url):
    """
    Scrape a meeting page to get:
    - Document URLs (Agenda, Minutes, Results)
    - Individual votes for each agenda item
    - Absent members
    """
    try:
        page.goto(meeting_url, wait_until="networkidle", timeout=60000)
        time.sleep(1.5)

        meeting_data = {
            "agenda_url": "",
            "minutes_url": "",
            "results_url": "",
            "item_votes": {},
            "item_detail_urls": {},
            "absent_members": set()
        }

        # Extract document URLs
        meeting_data["agenda_url"] = extract_link_href(page, "Agenda")
        meeting_data["minutes_url"] = extract_link_href(page, "Minutes")
        meeting_data["results_url"] = extract_link_href(page, "Results")

        # Get all agenda items and their action details
        item_votes = {}
        item_detail_urls = {}
        absent_members = set()

        # Collect file numbers and detail URLs
        rows = page.query_selector_all("table tr")
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 7:
                file_link = cells[0].query_selector("a")
                if file_link:
                    file_text = (file_link.text_content() or "").strip()
                    if re.match(r'^\d{2}-\d+$', file_text):
                        href = file_link.get_attribute("href")
                        if href:
                            if not href.startswith("http"):
                                href = WEBSITE_BASE + ("/" if not href.startswith("/") else "") + href.lstrip("/")
                            item_detail_urls[file_text] = href

        # Find Action details links
        page.wait_for_selector("table tr", timeout=10000)
        time.sleep(2)

        action_detail_links = page.locator("a:has-text('Action details')").all()

        # Click each and extract votes
        for i, link in enumerate(action_detail_links[:100]):
            try:
                row_text = link.evaluate("el => el.closest('tr')?.textContent || ''")
                agenda_match = re.search(r'(\d{2}-\d+)', row_text)
                file_number = agenda_match.group(1) if agenda_match else f"item_{i}"

                link.click()
                time.sleep(0.6)

                try:
                    page.wait_for_selector("dialog, [role='dialog'], .RadWindow", timeout=3000)
                except:
                    pass

                votes = extract_votes_from_popup(page)
                if votes:
                    item_votes[file_number] = votes
                    for member, vote in votes.items():
                        if vote.lower() == "absent":
                            absent_members.add(member)

                # Close popup
                try:
                    close_btn = page.locator("button:has-text('Close'), .rwCloseButton, [title='Close']").first
                    close_btn.click(timeout=1500)
                    time.sleep(0.2)
                except:
                    page.keyboard.press("Escape")
                    time.sleep(0.2)

            except Exception:
                try:
                    page.keyboard.press("Escape")
                except:
                    pass

        meeting_data["item_votes"] = item_votes
        meeting_data["item_detail_urls"] = item_detail_urls
        meeting_data["absent_members"] = absent_members

        return meeting_data

    except Exception as e:
        print(f"    Error scraping meeting: {e}")
        return None


def process_meeting_worker(args):
    """
    Worker function that processes a single meeting.
    Each worker creates its own browser instance.
    """
    event, worker_id, headless = args

    event_id = event.get("EventId")
    event_date = format_date(event.get("EventDate"))
    meeting_url = event.get("EventInSiteURL", "")

    print(f"  [Worker {worker_id}] Processing: {event_date} (ID: {event_id})")

    # Create browser for this worker
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    page = browser.new_page()

    try:
        # Scrape meeting page
        meeting_data = None
        if meeting_url:
            meeting_data = scrape_meeting(page, meeting_url)

        # Convert set to list for pickling
        if meeting_data and "absent_members" in meeting_data:
            meeting_data["absent_members"] = list(meeting_data["absent_members"])

        # Get event items from API
        items = get_event_items(event_id)

        result = {
            "event": event,
            "items": items,
            "meeting_data": meeting_data,
            "event_date": event_date
        }

        print(f"  [Worker {worker_id}] Completed: {event_date} ({len(items)} items)")
        return result

    finally:
        browser.close()
        playwright.stop()


def build_row(event, item, council_members, name_mapping, absent_members=None, item_votes=None, meeting_data=None):
    """Build a CSV row from event, item, and scraped data."""
    absent_members = absent_members or set()
    item_votes = item_votes or {}
    meeting_data = meeting_data or {}

    # Get file number
    file_number = ""
    matter_file = item.get("EventItemMatterFile", "") or ""
    if matter_file:
        file_number = matter_file
    else:
        title = item.get("EventItemTitle", "") or ""
        match = re.search(r'(\d{2}-\d+)', title)
        if match:
            file_number = match.group(1)

    votes_for_item = item_votes.get(file_number, {})

    # Build council member vote columns
    council_votes = []
    for col_name in council_members:
        vote = ""
        for api_name, mapped_name in name_mapping.items():
            if mapped_name == col_name:
                if api_name in absent_members:
                    vote = "Absent"
                    break
                if api_name in votes_for_item:
                    vote = votes_for_item[api_name]
                    break

        if not vote:
            if item.get("EventItemConsent") == 1:
                vote = "Consent"
            elif item.get("EventItemPassedFlag") == 1 and item.get("EventItemActionText"):
                vote = "Voice Vote"

        council_votes.append(vote)

    index_name = extract_index_from_title(item.get("EventItemTitle", ""))

    # Document URLs
    agenda_url = meeting_data.get("agenda_url", "") or event.get("EventAgendaFile", "") or ""
    minutes_url = meeting_data.get("minutes_url", "") or event.get("EventMinutesFile", "") or ""
    results_url = meeting_data.get("results_url", "") or ""

    if agenda_url and not agenda_url.startswith("http"):
        agenda_url = WEBSITE_BASE + "/" + agenda_url.lstrip("/")
    if minutes_url and not minutes_url.startswith("http"):
        minutes_url = WEBSITE_BASE + "/" + minutes_url.lstrip("/")
    if results_url and not results_url.startswith("http"):
        results_url = WEBSITE_BASE + "/" + results_url.lstrip("/")

    file_detail_url = meeting_data.get("item_detail_urls", {}).get(file_number, "")
    if file_detail_url and not file_detail_url.startswith("http"):
        file_detail_url = WEBSITE_BASE + "/" + file_detail_url.lstrip("/")

    row = [
        format_date(event.get("EventDate")),
        "Formal",
        event.get("EventBodyName", ""),
        event.get("EventInSiteURL", ""),
        agenda_url,
        minutes_url,
        event.get("EventVideoPath", "") or "",
        item.get("EventItemMatterType", "") or "",
        "",
        item.get("EventItemAgendaNumber", "") or "",
        item.get("EventItemTitle", "") or "",
        "",  # AgendaItemDescription
        "",
        "",
        item.get("EventItemConsent", ""),
        item.get("EventItemPassedFlag", "") if item.get("EventItemPassedFlag") is not None else "",
        item.get("EventItemTally", "") or "",
        index_name,
        item.get("EventItemActionName", "") or "",
        item.get("EventItemActionText", "") or "",
        item.get("EventItemAgendaNote", "") or "",
        item.get("EventItemMinutesNote", "") or "",
        item.get("EventItemMover", "") or "",
        item.get("EventItemSeconder", "") or "",
        "",
        "",
        item.get("EventItemVideo", "") or "",
        results_url,
        file_number,
        file_detail_url,
    ] + council_votes

    return row


def main():
    """Main function with parallel processing."""
    parser = argparse.ArgumentParser(description='Parallel Phoenix City Council meeting data fetcher')
    parser.add_argument('--year', type=int, required=True, help='Year to fetch (2020 or 2024)')
    parser.add_argument('--start-month', type=int, default=1, help='Start month (1-12)')
    parser.add_argument('--end-month', type=int, default=4, help='End month (1-12, exclusive)')
    parser.add_argument('--output', type=str, help='Output CSV file path')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers (default: 3)')
    parser.add_argument('--headed', action='store_true', help='Run browser in headed mode')
    args = parser.parse_args()

    # Validate year
    if args.year not in COUNCIL_ROSTERS:
        print(f"Error: Year {args.year} not supported. Use 2020 or 2024.")
        return

    roster = COUNCIL_ROSTERS[args.year]
    council_members = roster["members"]
    name_mapping = roster["mapping"]

    # Default output filename
    if not args.output:
        quarter = (args.start_month - 1) // 3 + 1
        args.output = f"phoenix_council_{args.year}_Q{quarter}_parallel.csv"

    # CSV headers
    headers = [
        "MeetingDate", "MeetingType", "BodyName", "EventInSiteURL",
        "EventAgendaFile", "EventMinutesFile", "EventVideoPath",
        "MatterTypeName", "MatterRequester", "AgendaItemNumber",
        "AgendaItemTitle", "AgendaItemDescription", "MatterPassedDate",
        "MatterNotes", "EventItemConsent", "EventItemPassedFlag",
        "EventItemTally", "IndexName", "ActionName", "ActionText",
        "EventItemAgendaNote", "EventItemMinutesNote", "Mover", "Seconder",
        "MatterSponsors", "MatterAttachmentURLs", "EventItemVideo",
        "ResultsURL", "FileNumber", "FileDetailURL"
    ] + council_members

    # Get events
    events = get_events(args.year, start_month=args.start_month, end_month=args.end_month)
    if not events:
        print("No events found!")
        return

    print(f"\nStarting parallel extraction with {args.workers} workers...")
    start_time = time.time()

    # Prepare arguments for each worker
    headless = not args.headed
    worker_args = [(event, i % args.workers, headless) for i, event in enumerate(events)]

    # Process meetings in parallel
    all_results = []
    with Pool(processes=args.workers) as pool:
        results = pool.map(process_meeting_worker, worker_args)
        all_results = [r for r in results if r is not None]

    # Sort results by date to maintain order
    all_results.sort(key=lambda x: x["event_date"])

    # Build all rows
    all_rows = []
    for result in all_results:
        event = result["event"]
        items = result["items"]
        meeting_data = result["meeting_data"]

        absent_members = set()
        item_votes = {}
        if meeting_data:
            # Convert list back to set
            absent_members = set(meeting_data.get("absent_members", []))
            item_votes = meeting_data.get("item_votes", {})

        for item in items:
            row = build_row(
                event, item, council_members, name_mapping,
                absent_members=absent_members,
                item_votes=item_votes,
                meeting_data=meeting_data
            )
            all_rows.append(row)

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

    elapsed = time.time() - start_time
    print(f"\nComplete! Wrote {len(all_rows)} rows to {args.output}")
    print(f"Time elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Workers used: {args.workers}")
    if len(events) > 0:
        print(f"Average per meeting: {elapsed/len(events):.1f} seconds")


if __name__ == "__main__":
    main()
