#!/usr/bin/env python3
"""
Fetch Phoenix City Council meeting data for 2024 from Legistar API
and generate a CSV file.
"""

import requests
import csv
import time
from datetime import datetime

BASE_URL = "https://webapi.legistar.com/v1/phoenix"

# Current council members for 2024
COUNCIL_MEMBERS = [
    "Kate Gallego (Mayor)",
    "Ann O'Brien (D1-Vice Mayor)",
    "Jim Waring (D2)",
    "Debra Stark (D3)",
    "Laura Pastor (D4)",
    "Betty Guardado (D5)",
    "Kevin Robinson (D6)",
    "Anna Hernandez (D7)",
    "Kesha Hodge Washington (D8)"
]

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

def get_2024_events():
    """Get City Council Formal Meeting events for Q1 2024 (Jan-Mar)."""
    url = f"{BASE_URL}/events?$filter=EventBodyId eq 138 and EventDate ge datetime'2024-01-01' and EventDate lt datetime'2024-04-01'&$orderby=EventDate asc"
    print(f"Fetching Q1 2024 events (Jan-Mar)...")
    events = fetch_json(url)
    if events:
        print(f"  Found {len(events)} events")
    return events or []

def get_event_items(event_id):
    """Get all agenda items for an event."""
    url = f"{BASE_URL}/events/{event_id}/eventitems"
    return fetch_json(url) or []

def get_roll_calls(event_item_id):
    """Get roll call votes for an event item."""
    url = f"{BASE_URL}/eventitems/{event_item_id}/rollcalls"
    return fetch_json(url) or []

def get_matter_indexes(matter_id):
    """Get district/index for a matter."""
    if not matter_id:
        return ""
    url = f"{BASE_URL}/matters/{matter_id}/indexes"
    indexes = fetch_json(url)
    if indexes and len(indexes) > 0:
        return indexes[0].get("IndexName", "")
    return ""

def format_date(date_str):
    """Format ISO date to YYYY-MM-DD."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str[:10] if date_str else ""

def build_row(event, item, roll_calls):
    """Build a CSV row from event and item data."""

    # Build council member vote columns
    vote_dict = {}
    for rc in roll_calls:
        name = rc.get("RollCallPersonName", "")
        vote = rc.get("RollCallValueName", "")
        vote_dict[name] = vote

    # Map to our column names
    council_votes = []
    name_mapping = {
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

    for col_name in COUNCIL_MEMBERS:
        # Find matching vote
        vote = ""
        for api_name, mapped_name in name_mapping.items():
            if mapped_name == col_name and api_name in vote_dict:
                vote = vote_dict[api_name]
                break

        # If no roll call, determine vote type from item
        if not vote:
            if item.get("EventItemConsent") == 1:
                vote = "Consent"
            elif item.get("EventItemPassedFlag") == 1 and item.get("EventItemActionText"):
                vote = "Voice Vote"

        council_votes.append(vote)

    # Get index/district (cache to avoid too many API calls)
    index_name = ""
    matter_id = item.get("EventItemMatterId")

    # Extract district from title if present
    title = item.get("EventItemTitle", "") or ""
    if "District 1" in title:
        index_name = "District 1"
    elif "District 2" in title:
        index_name = "District 2"
    elif "District 3" in title:
        index_name = "District 3"
    elif "District 4" in title:
        index_name = "District 4"
    elif "District 5" in title:
        index_name = "District 5"
    elif "District 6" in title:
        index_name = "District 6"
    elif "District 7" in title:
        index_name = "District 7"
    elif "District 8" in title:
        index_name = "District 8"
    elif "Citywide" in title:
        index_name = "Citywide"

    row = [
        format_date(event.get("EventDate")),  # MeetingDate
        "Formal",  # MeetingType
        event.get("EventBodyName", ""),  # BodyName
        event.get("EventInSiteURL", ""),  # EventInSiteURL
        event.get("EventAgendaFile", "") or "",  # EventAgendaFile
        event.get("EventMinutesFile", "") or "",  # EventMinutesFile
        event.get("EventVideoPath", "") or "",  # EventVideoPath
        item.get("EventItemMatterType", "") or "",  # MatterTypeName
        "",  # MatterRequester (would need separate API call)
        item.get("EventItemAgendaNumber", "") or "",  # AgendaItemNumber
        item.get("EventItemTitle", "") or "",  # AgendaItemTitle
        "",  # AgendaItemDescription
        "",  # MatterPassedDate
        "",  # MatterNotes
        item.get("EventItemConsent", ""),  # EventItemConsent
        item.get("EventItemPassedFlag", "") if item.get("EventItemPassedFlag") is not None else "",  # EventItemPassedFlag
        item.get("EventItemTally", "") or "",  # EventItemTally
        index_name,  # IndexName
        item.get("EventItemActionName", "") or "",  # ActionName
        item.get("EventItemActionText", "") or "",  # ActionText
        item.get("EventItemAgendaNote", "") or "",  # EventItemAgendaNote
        item.get("EventItemMinutesNote", "") or "",  # EventItemMinutesNote
        item.get("EventItemMover", "") or "",  # Mover
        item.get("EventItemSeconder", "") or "",  # Seconder
        "",  # MatterSponsors
        "",  # MatterAttachmentURLs
        item.get("EventItemVideo", "") or "",  # EventItemVideo
    ] + council_votes

    return row

def main():
    # CSV headers
    headers = [
        "MeetingDate", "MeetingType", "BodyName", "EventInSiteURL",
        "EventAgendaFile", "EventMinutesFile", "EventVideoPath",
        "MatterTypeName", "MatterRequester", "AgendaItemNumber",
        "AgendaItemTitle", "AgendaItemDescription", "MatterPassedDate",
        "MatterNotes", "EventItemConsent", "EventItemPassedFlag",
        "EventItemTally", "IndexName", "ActionName", "ActionText",
        "EventItemAgendaNote", "EventItemMinutesNote", "Mover", "Seconder",
        "MatterSponsors", "MatterAttachmentURLs", "EventItemVideo"
    ] + COUNCIL_MEMBERS

    # Get all 2024 events
    events = get_2024_events()

    all_rows = []

    for i, event in enumerate(events):
        event_id = event.get("EventId")
        event_date = format_date(event.get("EventDate"))
        print(f"Processing event {i+1}/{len(events)}: {event_date} (ID: {event_id})")

        # Get event items
        items = get_event_items(event_id)
        print(f"  Found {len(items)} agenda items")

        for item in items:
            item_id = item.get("EventItemId")

            # Get roll calls if this is a roll call item
            roll_calls = []
            if item.get("EventItemRollCallFlag") == 1:
                roll_calls = get_roll_calls(item_id)

            # Build row
            row = build_row(event, item, roll_calls)
            all_rows.append(row)

        # Small delay to be nice to the API
        time.sleep(0.5)

    # Write CSV
    output_file = "/Users/michaelingram/Documents/GitHub/PhoenixCityCouncil/phoenix_council_2024_Q1.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

    print(f"\nComplete! Wrote {len(all_rows)} rows to {output_file}")

if __name__ == "__main__":
    main()
