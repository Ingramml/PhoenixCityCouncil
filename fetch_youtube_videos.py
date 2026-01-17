#!/usr/bin/env python3
"""
Fetch YouTube video links for Phoenix City Council meetings.

This script uses two methods:
1. YouTube RSS feed - for recent videos (last 15 uploads)
2. Phoenix.gov website scraping - for historical videos (requires Playwright)

Usage:
    python fetch_youtube_videos.py                    # List matching videos
    python fetch_youtube_videos.py --update-csv      # Update the CSV file
    python fetch_youtube_videos.py --scrape-phoenix  # Scrape Phoenix.gov for video links
"""

import requests
import xml.etree.ElementTree as ET
import csv
import re
import argparse
import time
from datetime import datetime

# City of Phoenix YouTube channel
CHANNEL_ID = "x7FQNzOFCbtExt_gRub9JQ"  # Found from RSS feed

# RSS feed URL
RSS_FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

# Phoenix.gov meetings page
PHOENIX_GOV_URL = "https://www.phoenix.gov/administration/departments/cityclerk/programs-services/city-council-meetings.html"

CSV_FILE = "/Users/michaelingram/Documents/GitHub/PhoenixCityCouncil/phoenix_council_2024_Q1_enhanced.csv"


def fetch_rss_feed():
    """Fetch and parse YouTube RSS feed for recent videos."""
    try:
        response = requests.get(RSS_FEED_URL, timeout=30)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return None


def extract_videos_from_feed(root):
    """Extract video information from RSS feed XML."""
    videos = []

    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
        'media': 'http://search.yahoo.com/mrss/'
    }

    for entry in root.findall('atom:entry', namespaces):
        video = {}

        video_id_elem = entry.find('yt:videoId', namespaces)
        if video_id_elem is not None:
            video['id'] = video_id_elem.text
            video['url'] = f"https://www.youtube.com/watch?v={video_id_elem.text}"

        title_elem = entry.find('atom:title', namespaces)
        if title_elem is not None:
            video['title'] = title_elem.text

        published_elem = entry.find('atom:published', namespaces)
        if published_elem is not None:
            video['published'] = published_elem.text
            try:
                dt = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                video['published_date'] = dt.strftime('%Y-%m-%d')
            except:
                video['published_date'] = published_elem.text[:10]

        if 'id' in video and 'title' in video:
            videos.append(video)

    return videos


def scrape_phoenix_gov_videos(meeting_dates, headless=True):
    """
    Scrape Phoenix.gov to get video links for specific meeting dates.

    Args:
        meeting_dates: Set of dates in YYYY-MM-DD format to find videos for
        headless: Run browser in headless mode

    Returns:
        Dictionary mapping meeting dates to video URLs
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: Playwright not installed. Run: pip install playwright && playwright install")
        return {}

    video_urls = {}

    # Convert meeting dates to the format used on Phoenix.gov (e.g., "Jan 3, 2024")
    date_patterns = {}
    for date_str in meeting_dates:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # Format: "Jan 3, 2024" (no leading zero on day)
            phoenix_format = dt.strftime('%b %-d, %Y') if hasattr(dt, '__format__') else dt.strftime('%b %d, %Y').replace(' 0', ' ')
            date_patterns[phoenix_format] = date_str
        except:
            pass

    print(f"\nLooking for these meeting dates on Phoenix.gov:")
    for phoenix_fmt, iso_fmt in date_patterns.items():
        print(f"  {phoenix_fmt} -> {iso_fmt}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        found_dates = set()
        max_pages = 60

        for page_num in range(max_pages):
            offset = page_num * 10
            url = f"{PHOENIX_GOV_URL}?offsetdynamic-table={offset}&limitdynamic-table=10"

            print(f"\n  Checking page {page_num + 1} (offset {offset})...")

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(1.5)

                # Get all "See More" buttons and their associated date/type text
                # Each meeting entry has a container with date, type, and See More button
                containers = page.query_selector_all('.cmp-dynamic-table__data-row')

                page_has_target_dates = False

                for container in containers:
                    container_text = container.text_content() or ""

                    # Check each date pattern
                    for phoenix_fmt, iso_fmt in date_patterns.items():
                        if phoenix_fmt in container_text and "Formal Meeting" in container_text:
                            page_has_target_dates = True

                            # Skip if already found
                            if iso_fmt in found_dates:
                                continue

                            print(f"    Found: {phoenix_fmt} - Formal Meeting")

                            # Find and click See More in this specific container
                            see_more = container.query_selector('button:has-text("See More")')
                            if see_more:
                                see_more.click()
                                time.sleep(1)

                                # The expanded content appears right after this container
                                # Look for a table with Video row within the page
                                # The expanded table is a sibling element
                                expanded_tables = page.query_selector_all('table')

                                for table in expanded_tables:
                                    # Look for a row with "Video:" label
                                    video_row = table.query_selector('tr:has-text("Video:")')
                                    if video_row:
                                        video_link = video_row.query_selector('a[href*="youtube"]')
                                        if video_link:
                                            href = video_link.get_attribute("href")
                                            if href:
                                                video_urls[iso_fmt] = href
                                                found_dates.add(iso_fmt)
                                                print(f"      Video URL: {href}")
                                                break

                                # Close expanded row
                                see_less = page.query_selector('button:has-text("See Less")')
                                if see_less:
                                    see_less.click()
                                    time.sleep(0.5)

                            break  # Move to next container after processing this date

                # Check completion
                if found_dates == set(meeting_dates):
                    print("\n  Found all requested meeting dates!")
                    break

                # Check if we've gone too far back
                page_text = page.content()
                if "2023" in page_text and not page_has_target_dates and page_num > 20:
                    print("\n  Reached 2023 meetings, stopping search.")
                    break

            except Exception as e:
                print(f"    Error on page {page_num + 1}: {e}")
                continue

        browser.close()

    return video_urls


def extract_date_from_title(title):
    """Try to extract a meeting date from a video title."""
    patterns = [
        r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[,\s]+(\d{1,2})[,\s]+(\d{4})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})',
    ]

    month_map = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
        'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
        'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }

    title_lower = title.lower()

    match = re.search(patterns[0], title_lower)
    if match:
        month_str, day, year = match.groups()
        month = month_map.get(month_str)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"

    match = re.search(patterns[1], title)
    if match:
        month, day, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    match = re.search(patterns[2], title)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"

    return None


def find_formal_meeting_videos(videos):
    """Filter videos that are City Council Formal Meetings."""
    formal_meetings = []
    keywords = ['formal meeting', 'city council formal', 'council formal meeting']

    for video in videos:
        title_lower = video.get('title', '').lower()
        if any(kw in title_lower for kw in keywords):
            formal_meetings.append(video)

    return formal_meetings


def match_videos_to_meetings(videos, meeting_dates):
    """Match videos to meeting dates based on title parsing."""
    matches = {}

    for video in videos:
        title = video.get('title', '')
        extracted_date = extract_date_from_title(title)

        if extracted_date and extracted_date in meeting_dates:
            matches[extracted_date] = video.get('url', '')
            print(f"  Matched: {extracted_date} -> {title}")
            print(f"           URL: {video.get('url')}")

    return matches


def get_meeting_dates_from_csv(csv_file):
    """Get unique meeting dates from the CSV file."""
    dates = set()
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row.get('MeetingDate', '')
                if date and re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                    dates.add(date)
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return dates


def update_csv_with_videos(csv_file, video_matches, output_file=None):
    """Update the CSV file with YouTube video URLs."""
    if output_file is None:
        output_file = csv_file.replace('.csv', '_with_videos.csv')

    rows = []
    headers = None

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)

        # Add YouTubeVideoURL column if not present
        if 'YouTubeVideoURL' not in headers:
            headers.append('YouTubeVideoURL')

        for row in reader:
            meeting_date = row.get('MeetingDate', '')
            if meeting_date in video_matches:
                row['YouTubeVideoURL'] = video_matches[meeting_date]
            else:
                row['YouTubeVideoURL'] = row.get('YouTubeVideoURL', '')
            rows.append(row)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nUpdated CSV written to: {output_file}")

    # Count how many rows got video URLs
    with_videos = sum(1 for r in rows if r.get('YouTubeVideoURL'))
    print(f"Rows with video URLs: {with_videos}/{len(rows)}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description='Fetch YouTube videos for Phoenix City Council meetings')
    parser.add_argument('--update-csv', action='store_true', help='Update the CSV file with video URLs')
    parser.add_argument('--csv', type=str, default=CSV_FILE, help='Path to CSV file')
    parser.add_argument('--scrape-phoenix', action='store_true',
                        help='Scrape Phoenix.gov for video links (for older meetings)')
    parser.add_argument('--headed', action='store_true', help='Run browser in headed mode (visible)')
    args = parser.parse_args()

    # Get meeting dates from CSV
    print(f"Reading meeting dates from: {args.csv}")
    meeting_dates = get_meeting_dates_from_csv(args.csv)
    print(f"Found {len(meeting_dates)} unique meeting dates: {sorted(meeting_dates)}")

    all_video_matches = {}

    # Method 1: Try RSS feed first (for recent videos)
    print(f"\n=== Method 1: YouTube RSS Feed ===")
    root = fetch_rss_feed()
    if root is not None:
        videos = extract_videos_from_feed(root)
        print(f"Found {len(videos)} videos in RSS feed")

        formal_videos = find_formal_meeting_videos(videos)
        print(f"Found {len(formal_videos)} formal meeting videos")

        if formal_videos:
            print("\nMatching videos to meeting dates...")
            rss_matches = match_videos_to_meetings(formal_videos, meeting_dates)
            all_video_matches.update(rss_matches)
    else:
        print("Could not fetch RSS feed")

    # Method 2: Scrape Phoenix.gov for older videos
    if args.scrape_phoenix:
        print(f"\n=== Method 2: Phoenix.gov Scraping ===")
        remaining_dates = meeting_dates - set(all_video_matches.keys())
        if remaining_dates:
            print(f"Looking for {len(remaining_dates)} remaining dates...")
            phoenix_matches = scrape_phoenix_gov_videos(remaining_dates, headless=not args.headed)
            all_video_matches.update(phoenix_matches)
        else:
            print("All dates already matched from RSS feed")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Meeting dates in CSV: {len(meeting_dates)}")
    print(f"Videos matched: {len(all_video_matches)}")

    if all_video_matches:
        print("\nMatched videos:")
        for date in sorted(all_video_matches.keys()):
            print(f"  {date}: {all_video_matches[date]}")

    unmatched = meeting_dates - set(all_video_matches.keys())
    if unmatched:
        print(f"\nUnmatched dates: {sorted(unmatched)}")

    # Update CSV if requested
    if args.update_csv and all_video_matches:
        update_csv_with_videos(args.csv, all_video_matches)
    elif args.update_csv and not all_video_matches:
        print("\nNo videos found to update CSV with.")


if __name__ == "__main__":
    main()
