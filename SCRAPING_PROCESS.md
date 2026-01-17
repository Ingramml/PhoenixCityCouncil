# Phoenix City Council Data Scraping Process

This document details the data scraping process for Phoenix City Council meeting information, explaining what data comes from the API vs. website scraping, and where each piece of information is found.

## Overview

Phoenix City Council meeting data is available from two sources:

1. **Legistar Web API** - Structured JSON data (fast, reliable, but incomplete)
2. **Legistar Website** - HTML pages (slower, requires scraping, but has complete data)

The enhanced script (`fetch_2024_data_enhanced.py`) combines both sources to get complete meeting data.

---

## Data Source 1: Legistar Web API

**Base URL:** `https://webapi.legistar.com/v1/phoenix`

### Available Endpoints

| Endpoint | Data Retrieved |
|----------|----------------|
| `/events` | Meeting list with dates, body, basic info |
| `/events/{id}/eventitems` | Agenda items for a meeting |
| `/eventitems/{id}/rollcalls` | Roll call votes (attendance only) |
| `/matters/{id}` | Detailed matter information |
| `/matters/{id}/indexes` | District/index assignments |
| `/persons` | Council member information |
| `/bodies` | Meeting body types |

### Data Available from API

| Field | API Endpoint | Notes |
|-------|--------------|-------|
| MeetingDate | `/events` → `EventDate` | ISO format |
| BodyName | `/events` → `EventBodyName` | "City Council Formal Meeting" |
| EventInSiteURL | `/events` → `EventInSiteURL` | Link to meeting page |
| MatterTypeName | `/eventitems` → `EventItemMatterType` | "Ordinance", "Resolution", etc. |
| AgendaItemNumber | `/eventitems` → `EventItemAgendaNumber` | "1", "2", "3", etc. |
| AgendaItemTitle | `/eventitems` → `EventItemTitle` | Short title |
| EventItemConsent | `/eventitems` → `EventItemConsent` | 0=Regular, 1=Consent |
| EventItemPassedFlag | `/eventitems` → `EventItemPassedFlag` | 0=Failed, 1=Passed |
| EventItemTally | `/eventitems` → `EventItemTally` | "7-0", "8-1", etc. |
| ActionName | `/eventitems` → `EventItemActionName` | "approved", "adopted", etc. |
| ActionText | `/eventitems` → `EventItemActionText` | Motion text |
| Mover | `/eventitems` → `EventItemMover` | Council member who made motion |
| Seconder | `/eventitems` → `EventItemSeconder` | Council member who seconded |
| EventItemVideo | `/eventitems` → `EventItemVideo` | Video timestamp |

### Data NOT Available from API (Always Empty/Null)

| Field | Reason |
|-------|--------|
| EventAgendaFile | Phoenix doesn't populate this field |
| EventMinutesFile | Phoenix doesn't populate this field |
| EventVideoPath | Phoenix doesn't populate this field |
| Individual Votes | API only has roll call (attendance), not item votes |
| Full Item Summary | API only has title, not full description |

---

## Data Source 2: Website Scraping

**Base URL:** `https://phoenix.legistar.com`

### Page Types and Data Locations

#### 1. Meeting Detail Page
**URL Pattern:** `MeetingDetail.aspx?LEGID={EventId}&GID=485&G={GUID}`

**Location on Page:**
```
+----------------------------------------------------------+
|  Meeting Header                                           |
|  - Meeting Name: City Council Formal Meeting             |
|  - Date: 1/3/2024                                        |
|  - Agenda status: Final-revised                          |
+----------------------------------------------------------+
|  Document Links (top section):                           |
|  [Agenda PDF] [Minutes PDF] [Results PDF] [Video]        |
+----------------------------------------------------------+
|  Meeting Items Table:                                     |
|  +------+--------+------+-------+--------+---------------+
|  |File #|Agenda #| Type | Title | Action |Action Details |
|  +------+--------+------+-------+--------+---------------+
|  |23-110|   1    | Min  | For...| approved| [link]       |
|  |23-234|   2    | Res  | Auth..| adopted | [link]       |
|  +------+--------+------+-------+--------+---------------+
+----------------------------------------------------------+
```

**Data Extracted:**
| Data | HTML Element | Extraction Method |
|------|--------------|-------------------|
| Agenda PDF URL | `<a>` containing "Agenda" | Text match + href extraction |
| Minutes PDF URL | `<a>` containing "Minutes" | Text match + href extraction |
| Results PDF URL | `<a>` containing "Results" | Text match + href extraction |
| File Numbers | First column of items table | `<a>` with pattern `XX-XXXX` |
| Item Detail URLs | File # links | `LegislationDetail.aspx?ID=...` |

**Document URL Patterns:**
- Agenda: `View.ashx?M=A&ID={MeetingId}&GUID={MeetingGuid}`
- Minutes: `View.ashx?M=M&ID={MeetingId}&GUID={MeetingGuid}`
- Results: `View.ashx?M=E2&ID={MeetingId}&GUID={MeetingGuid}`

---

#### 2. Action Details Popup
**Triggered By:** Clicking "Action details" link in Meeting Items table

**Popup Structure:**
```
+--------------------------------------------------+
| City of Phoenix - Action Details           [X]   |
+--------------------------------------------------+
| File #: 23-3110                                  |
| Type: Minutes                                    |
| Title: For Approval or Correction, the Minutes  |
|        of the Formal Meeting on March 3, 2021   |
+--------------------------------------------------+
| Mover: Jim Waring    Seconder: Debra Stark      |
+--------------------------------------------------+
| Action: approved                                 |
| Action text: A motion was made by Councilman    |
|              Waring, seconded by Councilwoman   |
|              Stark, that this item be approved. |
+--------------------------------------------------+
| Votes (8:0)                                      |
| +----------------------------+--------+         |
| | Person Name                | Vote   |         |
| +----------------------------+--------+         |
| | Betty Guardado             | Absent |         |
| | Kesha Hodge Washington     | Yes    |         |
| | Ann O'Brien                | Yes    |         |
| | Laura Pastor               | Yes    |         |
| | Kevin Robinson             | Yes    |         |
| | Debra Stark                | Yes    |         |
| | Jim Waring                 | Yes    |         |
| | Yassamin Ansari            | Yes    |         |
| | Kate Gallego               | Yes    |         |
| +----------------------------+--------+         |
+--------------------------------------------------+
```

**Data Extracted:**
| Data | Location | Notes |
|------|----------|-------|
| Individual Votes | Vote table in popup | Name → Vote mapping |
| Absent Members | Vote = "Absent" | Used for ALL items in meeting |
| Mover/Seconder | Popup fields | Confirms API data |

**Critical Insight:** The **individual votes** (Yes/No/Absent per council member per item) are ONLY available from the Action Details popup. The API does not provide this data.

---

#### 3. Item Detail Page (Legislation Detail)
**URL Pattern:** `LegislationDetail.aspx?ID={MatterId}&GUID={MatterGuid}`

**Page Structure:**
```
+----------------------------------------------------------+
| File #: 23-3110                                           |
| Type: Minutes        Status: Approved                     |
| Meeting Body: City Council Formal Meeting                 |
| On agenda: 1/3/2024  Final action: 1/3/2024              |
+----------------------------------------------------------+
| Title: For Approval or Correction, the Minutes of the    |
|        Formal Meeting on March 3, 2021                   |
+----------------------------------------------------------+
| [History] [Item Summary]                                  |
+----------------------------------------------------------+
| Item Summary:                                             |
| Title: For Approval or Correction...                     |
|                                                          |
| Report Summary:                                          |
| This item transmits the minutes of the Formal Meeting    |
| of March 3, 2021, for review, correction and/or         |
| approval by the City Council. The minutes are available  |
| for review in the City Clerk Department, 200 W.         |
| Washington Street, 15th Floor.                          |
|                                                          |
| Department                                               |
| Responsible Department                                   |
| This item is submitted by Deputy City Manager Ginger    |
| Spencer and the City Clerk Department.                  |
+----------------------------------------------------------+
```

**Data Extracted:**
| Data | Location | Notes |
|------|----------|-------|
| Full Item Summary | "Item Summary" tab content | Complete description |
| Report Summary | Paragraphs after "Report Summary" | Detailed explanation |
| Department | "Responsible Department" section | Submitting department |

---

## Scraping Process Flow

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 1. FETCH EVENTS FROM API                                │
│    GET /events?$filter=EventBodyId eq 138...            │
│    Returns: List of meetings with EventId, Date, URL    │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 2. FOR EACH MEETING:                                    │
│                                                         │
│    a) Navigate to meeting page (EventInSiteURL)         │
│                                                         │
│    b) Extract document URLs:                            │
│       - Find <a> containing "Agenda" → agenda_url       │
│       - Find <a> containing "Minutes" → minutes_url     │
│       - Find <a> containing "Results" → results_url     │
│                                                         │
│    c) Collect File # links:                             │
│       - Find all <a> matching "XX-XXXX" pattern         │
│       - Store file_number → detail_url mapping          │
│                                                         │
│    d) Click each "Action details" link:                 │
│       - Wait for popup/iframe to load                   │
│       - Extract vote table (Name → Vote)                │
│       - Track absent members                            │
│       - Close popup                                     │
│                                                         │
│    e) GET /events/{EventId}/eventitems from API         │
│       Returns: All agenda items for meeting             │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 3. FOR EACH AGENDA ITEM:                                │
│                                                         │
│    a) Get API data (title, action, mover, etc.)         │
│                                                         │
│    b) Look up individual votes from scraped data        │
│       - Match by file number                            │
│       - If member in absent_members → "Absent"          │
│       - Else use scraped vote (Yes/No/etc.)            │
│       - Else use item-level (Consent/Voice Vote)       │
│                                                         │
│    c) (Optional) Scrape item summary:                   │
│       - Navigate to LegislationDetail page              │
│       - Extract "Item Summary" content                  │
│       - Navigate back to meeting page                   │
│                                                         │
│    d) Build CSV row with combined data                  │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 4. WRITE CSV FILE                                       │
│    All rows with combined API + scraped data            │
└─────────────────────────────────────────────────────────┘
  │
  ▼
END
```

---

## Data Completeness Summary

| Data Field | API | Website | Final Source |
|------------|-----|---------|--------------|
| Meeting Date | ✅ | ✅ | API |
| Meeting Body | ✅ | ✅ | API |
| Agenda Item Title | ✅ | ✅ | API |
| Agenda Item Number | ✅ | ✅ | API |
| Matter Type | ✅ | ✅ | API |
| Passed Flag | ✅ | ✅ | API |
| Tally (7-0, etc.) | ✅ | ✅ | API |
| Action Name | ✅ | ✅ | API |
| Action Text | ✅ | ✅ | API |
| Mover/Seconder | ✅ | ✅ | API |
| Consent Flag | ✅ | ❌ | API |
| Agenda PDF URL | ❌ | ✅ | **Website** |
| Minutes PDF URL | ❌ | ✅ | **Website** |
| Results PDF URL | ❌ | ✅ | **Website** |
| Individual Votes | ❌ | ✅ | **Website** |
| Absent Members | ❌ | ✅ | **Website** |
| Full Item Summary | ❌ | ✅ | **Website** |
| File Detail URL | ❌ | ✅ | **Website** |

---

## Usage

### Basic Usage (Q1 2024)
```bash
python fetch_2024_data_enhanced.py
```

### With Item Summaries (Slow)
```bash
python fetch_2024_data_enhanced.py --scrape-summaries
```

### Custom Date Range
```bash
python fetch_2024_data_enhanced.py --start-month 1 --end-month 7
```

### Custom Output File
```bash
python fetch_2024_data_enhanced.py --output my_data.csv
```

---

## Technical Notes

### Browser Automation
- Uses **Playwright** for browser automation
- Runs in **headless mode** by default
- Handles JavaScript-rendered content and popups

### Rate Limiting
- 1 second delay between meetings
- 0.5 second delay between action detail popups
- Respects server timeouts

### Error Handling
- Retries API calls up to 3 times
- Gracefully handles missing popups
- Continues processing if individual items fail

---

## Council Member Roster (2024)

| Position | Name |
|----------|------|
| Mayor | Kate Gallego |
| District 1 (Vice Mayor) | Ann O'Brien |
| District 2 | Jim Waring |
| District 3 | Debra Stark |
| District 4 | Laura Pastor |
| District 5 | Betty Guardado |
| District 6 | Kevin Robinson |
| District 7 | Yassamin Ansari |
| District 8 | Kesha Hodge Washington |

**Note:** District 7 changed from Yassamin Ansari (2024) to Anna Hernandez (2025).

---

## Output CSV Columns

The enhanced script produces a CSV with the following columns:

| Column | Source | Description |
|--------|--------|-------------|
| MeetingDate | API | Meeting date (YYYY-MM-DD) |
| MeetingType | Static | "Formal" |
| BodyName | API | Body name (City Council Formal Meeting) |
| EventInSiteURL | API | Link to meeting on Legistar |
| EventAgendaFile | Website | Agenda PDF URL |
| EventMinutesFile | Website | Minutes PDF URL |
| EventVideoPath | API | Video path (usually empty) |
| MatterTypeName | API | Type (Ordinance, Resolution, etc.) |
| MatterRequester | - | Not populated |
| AgendaItemNumber | API | Agenda item number |
| AgendaItemTitle | API | Short title |
| AgendaItemDescription | Website | Full item summary (with --scrape-summaries) |
| MatterPassedDate | - | Not populated |
| MatterNotes | - | Not populated |
| EventItemConsent | API | 0=Regular, 1=Consent |
| EventItemPassedFlag | API | 0=Failed, 1=Passed |
| EventItemTally | API | Vote tally (e.g., "7-0") |
| IndexName | API | District extracted from title |
| ActionName | API | Action (approved, adopted, etc.) |
| ActionText | API | Motion text |
| EventItemAgendaNote | API | Agenda notes |
| EventItemMinutesNote | API | Minutes notes |
| Mover | API | Council member who made motion |
| Seconder | API | Council member who seconded |
| MatterSponsors | - | Not populated |
| MatterAttachmentURLs | - | Not populated |
| EventItemVideo | API | Video timestamp |
| ResultsURL | Website | Results PDF URL |
| FileNumber | Website | File number (e.g., "23-3110") |
| FileDetailURL | Website | Link to item detail page |
| Kate Gallego (Mayor) | Website | Individual vote |
| Ann O'Brien (D1-Vice Mayor) | Website | Individual vote |
| Jim Waring (D2) | Website | Individual vote |
| Debra Stark (D3) | Website | Individual vote |
| Laura Pastor (D4) | Website | Individual vote |
| Betty Guardado (D5) | Website | Individual vote |
| Kevin Robinson (D6) | Website | Individual vote |
| Yassamin Ansari (D7) | Website | Individual vote |
| Kesha Hodge Washington (D8) | Website | Individual vote |
