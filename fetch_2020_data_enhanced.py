#!/usr/bin/env python3
"""
Enhanced Phoenix City Council meeting data fetcher for 2020.
Combines API data with website scraping for complete vote information.

Council Members for 2020:
- Kate Gallego (Mayor)
- Thelda Williams (D1-Vice Mayor)
- Jim Waring (D2)
- Debra Stark (D3)
- Laura Pastor (D4)
- Betty Guardado (D5)
- Sal DiCiccio (D6)
- Michael Nowakowski (D7)
- Carlos Garcia (D8)
"""

import requests
import csv
import time
import re
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://webapi.legistar.com/v1/phoenix"
WEBSITE_BASE = "https://phoenix.legistar.com"

# Council members for 2020
COUNCIL_MEMBERS_2020 = [
    "Kate Gallego (Mayor)",
    "Thelda Williams (D1-Vice Mayor)",
    "Jim Waring (D2)",
    "Debra Stark (D3)",
    "Laura Pastor (D4)",
    "Betty Guardado (D5)",
    "Sal DiCiccio (D6)",
    "Michael Nowakowski (D7)",
    "Carlos Garcia (D8)"
]

# Mapping from API names to column names
NAME_MAPPING_2020 = {
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


def fetch_json(url):
    """Fetch JSON from URL with retry logic."""
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    return None


def get_2020_events(start_month=1, end_month=4):
    """Get City Council Formal Meeting events for specified period in 2020."""
    start_date = f"2020-{start_month:02d}-01"
    end_date = f"2020-{end_month:02d}-01"
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


class WebScraper:
    """Scrapes Phoenix Legistar website for additional data."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.current_meeting_data = {}

    def start(self, headless=True):
        """Start the browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        print(f"Browser started (headless={headless})")

    def stop(self):
        """Stop the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Browser stopped")

    def scrape_meeting(self, meeting_url):
        """
        Scrape a meeting page to get:
        - Document URLs (Agenda, Minutes, Results)
        - Individual votes for each agenda item
        - Absent members
        """
        print(f"  Scraping meeting page...")
        try:
            self.page.goto(meeting_url, wait_until="networkidle", timeout=60000)
            time.sleep(2)

            meeting_data = {
                "agenda_url": "",
                "minutes_url": "",
                "results_url": "",
                "item_votes": {},
                "item_detail_urls": {},
                "absent_members": set()
            }

            # Extract document URLs
            meeting_data["agenda_url"] = self._extract_link_href("Agenda")
            meeting_data["minutes_url"] = self._extract_link_href("Minutes")
            meeting_data["results_url"] = self._extract_link_href("Results")

            # Get all agenda items and their action details
            meeting_data["item_votes"], meeting_data["absent_members"] = self._scrape_all_action_details()
            meeting_data["item_detail_urls"] = getattr(self, 'item_detail_urls', {})

            self.current_meeting_data = meeting_data
            return meeting_data

        except Exception as e:
            print(f"    Error scraping meeting: {e}")
            return None

    def _extract_link_href(self, text_pattern):
        """Extract href from a link containing the text pattern."""
        try:
            links = self.page.query_selector_all("a")
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

    def _scrape_all_action_details(self):
        """Scrape Action Details for all agenda items to get individual votes."""
        item_votes = {}
        item_detail_urls = {}
        absent_members = set()

        try:
            # Collect file numbers and detail URLs
            rows = self.page.query_selector_all("table tr")
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
                                    if href.startswith("/"):
                                        href = WEBSITE_BASE + href
                                    else:
                                        href = WEBSITE_BASE + "/" + href
                                item_detail_urls[file_text] = href

            # Find all Action details links
            self.page.wait_for_selector("table tr", timeout=10000)
            time.sleep(3)

            action_detail_links = self.page.locator("a:has-text('Action details')").all()
            print(f"    Found {len(action_detail_links)} Action details links, {len(item_detail_urls)} item detail URLs")

            for i, link in enumerate(action_detail_links[:100]):
                try:
                    row_text = link.evaluate("el => el.closest('tr')?.textContent || ''")
                    agenda_match = re.search(r'(\d{2}-\d+)', row_text)
                    file_number = agenda_match.group(1) if agenda_match else f"item_{i}"

                    link.click()
                    time.sleep(0.8)

                    try:
                        self.page.wait_for_selector("dialog, [role='dialog'], .RadWindow", timeout=5000)
                    except:
                        pass

                    votes = self._extract_votes_from_popup()
                    if votes:
                        item_votes[file_number] = votes
                        for member, vote in votes.items():
                            if vote.lower() == "absent":
                                absent_members.add(member)

                    close_btn = self.page.locator("button:has-text('Close'), .rwCloseButton, [title='Close']").first
                    try:
                        close_btn.click(timeout=2000)
                        time.sleep(0.3)
                    except:
                        self.page.keyboard.press("Escape")
                        time.sleep(0.3)

                except Exception as e:
                    try:
                        self.page.keyboard.press("Escape")
                    except:
                        pass

            self.item_detail_urls = item_detail_urls
            return item_votes, absent_members

        except Exception as e:
            print(f"    Error scraping action details: {e}")
            return {}, set()

    def _extract_votes_from_popup(self):
        """Extract individual votes from the action details popup."""
        votes = {}
        try:
            frames = self.page.frames
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

    # Get individual votes for this item
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

    # Extract index/district
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
        "",  # MatterRequester
        item.get("EventItemAgendaNumber", "") or "",
        item.get("EventItemTitle", "") or "",
        "",  # AgendaItemDescription
        "",  # MatterPassedDate
        "",  # MatterNotes
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
        "",  # MatterSponsors
        "",  # MatterAttachmentURLs
        item.get("EventItemVideo", "") or "",  # EventItemVideo - will be updated with YouTube URL
        results_url,
        file_number,
        file_detail_url,
    ] + council_votes

    return row


def main():
    parser = argparse.ArgumentParser(description='Fetch Phoenix City Council meeting data for 2020')
    parser.add_argument('--start-month', type=int, default=1, help='Start month (1-12)')
    parser.add_argument('--end-month', type=int, default=4, help='End month (1-12, exclusive)')
    parser.add_argument('--output', type=str,
                        default="/Users/michaelingram/Documents/GitHub/PhoenixCityCouncil/phoenix_council_2020_Q1_enhanced.csv",
                        help='Output CSV file path')
    parser.add_argument('--headed', action='store_true', help='Run browser in headed mode')
    args = parser.parse_args()

    council_members = COUNCIL_MEMBERS_2020
    name_mapping = NAME_MAPPING_2020

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

    events = get_2020_events(start_month=args.start_month, end_month=args.end_month)

    if not events:
        print("No events found!")
        return

    scraper = WebScraper()
    scraper.start(headless=not args.headed)

    all_rows = []

    try:
        for i, event in enumerate(events):
            event_id = event.get("EventId")
            event_date = format_date(event.get("EventDate"))
            meeting_url = event.get("EventInSiteURL", "")

            print(f"\nProcessing event {i+1}/{len(events)}: {event_date} (ID: {event_id})")

            meeting_data = None
            if meeting_url:
                meeting_data = scraper.scrape_meeting(meeting_url)

            absent_members = set()
            item_votes = {}
            if meeting_data:
                absent_members = meeting_data.get("absent_members", set())
                item_votes = meeting_data.get("item_votes", {})
                if absent_members:
                    print(f"    Absent members: {', '.join(absent_members)}")

            items = get_event_items(event_id)
            print(f"    Found {len(items)} agenda items")

            for item in items:
                row = build_row(
                    event, item, council_members, name_mapping,
                    absent_members=absent_members,
                    item_votes=item_votes,
                    meeting_data=meeting_data
                )
                all_rows.append(row)

            time.sleep(1)

    finally:
        scraper.stop()

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

    print(f"\nComplete! Wrote {len(all_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
