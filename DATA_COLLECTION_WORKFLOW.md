# Phoenix City Council Data Collection Workflow

A comprehensive guide for efficiently collecting complete meeting data using the fastest and most reliable methods for each data point.

---

## Quick Reference: Optimal Source for Each Data Point

| Data Point | Best Source | Method | Speed |
|------------|-------------|--------|-------|
| Meeting dates/times | Legistar API | REST call | Fast |
| Agenda items | Legistar API | REST call | Fast |
| Item titles | Legistar API | REST call | Fast |
| Matter type | Legistar API | REST call | Fast |
| Vote tally (7-0) | Legistar API | REST call | Fast |
| Action/Mover/Seconder | Legistar API | REST call | Fast |
| Consent flag | Legistar API | REST call | Fast |
| Passed/failed flag | Legistar API | REST call | Fast |
| **Individual votes** | Legistar Website | Playwright | Slow |
| **Item summaries** | Legistar Website | Playwright | Slow |
| **Document URLs** | Legistar Website | Playwright | Medium |
| **Video links** | Phoenix.gov | Manual/Playwright | Medium |

---

## Phase 1: API Data Collection (Fast - ~2 minutes)

### What You Get
- All meeting metadata
- All agenda items with titles
- Vote tallies, actions, movers, seconders
- Consent/passed flags
- ~90% of needed data

### Script
```bash
python fetch_2024_data.py
```

### API Endpoints Used
```
Base URL: https://webapi.legistar.com/v1/phoenix

1. GET /events?$filter=EventBodyId eq 138 and EventDate ge datetime'2024-01-01'
   → Returns: Meeting list with dates, IDs, URLs

2. GET /events/{EventId}/eventitems
   → Returns: All agenda items for meeting

3. GET /eventitems/{EventItemId}/rollcalls (optional)
   → Returns: Roll call attendance (NOT item votes)
```

### Output
- `phoenix_council_2024_Q1.csv` - Basic data, ~600 rows

---

## Phase 2: Website Scraping (Slow - ~30-60 minutes)

### What You Get
- Individual council member votes per item
- Document URLs (Agenda PDF, Minutes PDF, Results PDF)
- File numbers and detail URLs
- Full item summaries (optional, adds significant time)

### Script
```bash
# Standard run (votes + documents)
python fetch_2024_data_enhanced.py

# With item summaries (slower)
python fetch_2024_data_enhanced.py --scrape-summaries
```

### Process
1. Navigate to each meeting page on phoenix.legistar.com
2. Extract document links from page header
3. Click "Action details" for each item to get individual votes
4. (Optional) Navigate to each item's detail page for full summary

### Output
- `phoenix_council_2024_Q1_enhanced.csv` - Complete data, 639 rows

---

## Phase 3: Video Links (Manual - ~10 minutes)

### Why Manual?
- YouTube RSS only has last ~15 videos (not historical)
- Phoenix.gov scraping is unreliable for container-to-video matching
- Manual collection is faster and more accurate for small datasets

### Process

#### For Recent Meetings (last 2-3 weeks)
Use YouTube RSS feed:
```python
import requests
import xml.etree.ElementTree as ET

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=x7FQNzOFCbtExt_gRub9JQ"
response = requests.get(RSS_URL)
root = ET.fromstring(response.content)

# Extract video IDs and titles, match to meeting dates
```

#### For Historical Meetings
1. Go to: `https://www.phoenix.gov/administration/departments/cityclerk/programs-services/city-council-meetings.html`
2. Use pagination: add `?offsetdynamic-table=130` for older meetings
3. Find target meeting date + "Formal Meeting"
4. Click "See More" to expand
5. Copy YouTube URL from Video row
6. Repeat for each meeting

### Script to Update CSV
```bash
python fetch_youtube_videos.py --update-csv
```

### Output
- `phoenix_council_2024_Q1_enhanced_with_videos.csv` - With video URLs

---

## Complete Workflow Diagram

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: LEGISTAR API (2 minutes)                           │
│                                                             │
│   python fetch_2024_data.py                                 │
│                                                             │
│   ✅ Meeting dates, times, body                             │
│   ✅ Agenda items, titles, numbers                          │
│   ✅ Vote tallies (7-0, 8-1, etc.)                          │
│   ✅ Actions, movers, seconders                             │
│   ✅ Consent/passed flags                                   │
│   ❌ Individual votes                                       │
│   ❌ Document URLs                                          │
│   ❌ Item summaries                                         │
│   ❌ Video links                                            │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: LEGISTAR WEBSITE SCRAPING (30-60 minutes)          │
│                                                             │
│   python fetch_2024_data_enhanced.py                        │
│                                                             │
│   ✅ Individual votes (Yes/No/Absent per member per item)   │
│   ✅ Document URLs (Agenda, Minutes, Results PDFs)          │
│   ✅ File numbers and detail URLs                           │
│   ⚠️  Item summaries (optional, add --scrape-summaries)     │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: VIDEO LINKS (10 minutes manual)                    │
│                                                             │
│   Recent: YouTube RSS feed (automated)                      │
│   Historical: Phoenix.gov manual collection                 │
│                                                             │
│   python fetch_youtube_videos.py --update-csv               │
│                                                             │
│   ✅ YouTube video URL for each meeting                     │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
COMPLETE CSV WITH ALL DATA POINTS
```

---

## Data Point Details

### From Legistar API (Fast)

| Field | API Path | Example |
|-------|----------|---------|
| MeetingDate | `events.EventDate` | "2024-01-03T00:00:00" |
| BodyName | `events.EventBodyName` | "City Council Formal Meeting" |
| EventInSiteURL | `events.EventInSiteURL` | "https://phoenix.legistar.com/..." |
| AgendaItemNumber | `eventitems.EventItemAgendaNumber` | "1" |
| AgendaItemTitle | `eventitems.EventItemTitle` | "For Approval..." |
| MatterTypeName | `eventitems.EventItemMatterType` | "Minutes" |
| EventItemConsent | `eventitems.EventItemConsent` | 1 (consent) or 0 (regular) |
| EventItemPassedFlag | `eventitems.EventItemPassedFlag` | 1 (passed) or 0 (failed) |
| EventItemTally | `eventitems.EventItemTally` | "7-0" |
| ActionName | `eventitems.EventItemActionName` | "approved" |
| ActionText | `eventitems.EventItemActionText` | "A motion was made..." |
| Mover | `eventitems.EventItemMover` | "Jim Waring" |
| Seconder | `eventitems.EventItemSeconder` | "Debra Stark" |

### From Legistar Website (Slow)

| Field | Page Location | Extraction Method |
|-------|---------------|-------------------|
| EventAgendaFile | Meeting page header | Find `<a>` with "Agenda" text |
| EventMinutesFile | Meeting page header | Find `<a>` with "Minutes" text |
| ResultsURL | Meeting page header | Find `<a>` with "Results" text |
| FileNumber | Items table, first column | Parse `<a>` with XX-XXXX pattern |
| FileDetailURL | Items table, file # link | Extract href from file # link |
| Individual Votes | Action Details popup | Click "Action details", parse vote table |
| AgendaItemDescription | Legislation Detail page | Navigate to detail page, parse summary |

### From Phoenix.gov/YouTube (Manual)

| Field | Source | Method |
|-------|--------|--------|
| YouTubeVideoURL | Phoenix.gov | Click "See More", copy Video link |
| (backup) | YouTube RSS | Parse feed for recent videos |

---

## Time Estimates

| Phase | Data Points | Time | Automation |
|-------|-------------|------|------------|
| Phase 1: API | 15+ fields | 2 min | Fully automated |
| Phase 2: Scraping | 10+ fields | 30-60 min | Fully automated |
| Phase 3: Videos | 1 field | 10 min | Semi-manual |
| **Total** | **All fields** | **~45-75 min** | |

---

## Running the Complete Pipeline

### One-Time Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install requests playwright
playwright install chromium
```

### Full Data Collection
```bash
# Activate environment
source venv/bin/activate

# Phase 1: API data (fast)
python fetch_2024_data.py

# Phase 2: Enhanced data with votes (slower)
python fetch_2024_data_enhanced.py

# Phase 3: Add video links
# Option A: Try automated (may need manual fallback)
python fetch_youtube_videos.py --scrape-phoenix --update-csv

# Option B: Manual video collection, then update
python fetch_youtube_videos.py --update-csv
```

### Custom Date Ranges
```bash
# Q2 2024 (April-June)
python fetch_2024_data_enhanced.py --start-month 4 --end-month 7

# Full year 2024
python fetch_2024_data_enhanced.py --start-month 1 --end-month 13
```

---

## Output Files

| File | Phase | Contents |
|------|-------|----------|
| `phoenix_council_2024_Q1.csv` | 1 | API data only |
| `phoenix_council_2024_Q1_enhanced.csv` | 2 | + votes, documents |
| `phoenix_council_2024_Q1_enhanced_with_videos.csv` | 3 | + video URLs |

---

## Troubleshooting

### API Issues
- **Timeout**: Increase timeout in `fetch_json()`, add retry logic
- **Rate limiting**: Add `time.sleep(0.5)` between calls
- **Empty results**: Check EventBodyId (138 = Formal Meetings)

### Scraping Issues
- **Page not loading**: Increase `wait_until="networkidle"` timeout
- **Popup not appearing**: Add longer `time.sleep()` after click
- **Missing votes**: Check if meeting has "Action details" links

### Video Link Issues
- **RSS empty**: RSS only has last ~15 videos, use Phoenix.gov for historical
- **Phoenix.gov wrong URL**: Use manual collection, container matching is unreliable
- **Video not found**: Some meetings may not have video recordings

---

## Council Members (2024)

| Position | Name | CSV Column |
|----------|------|------------|
| Mayor | Kate Gallego | Kate Gallego (Mayor) |
| District 1 (Vice Mayor) | Ann O'Brien | Ann O'Brien (D1-Vice Mayor) |
| District 2 | Jim Waring | Jim Waring (D2) |
| District 3 | Debra Stark | Debra Stark (D3) |
| District 4 | Laura Pastor | Laura Pastor (D4) |
| District 5 | Betty Guardado | Betty Guardado (D5) |
| District 6 | Kevin Robinson | Kevin Robinson (D6) |
| District 7 | Yassamin Ansari | Yassamin Ansari (D7) |
| District 8 | Kesha Hodge Washington | Kesha Hodge Washington (D8) |

**Note:** District 7 changed to Anna Hernandez in 2025.

---

## Final CSV Columns (39 total)

### Meeting Info (6)
MeetingDate, MeetingType, BodyName, EventInSiteURL, EventAgendaFile, EventMinutesFile

### Item Info (10)
EventVideoPath, MatterTypeName, MatterRequester, AgendaItemNumber, AgendaItemTitle, AgendaItemDescription, MatterPassedDate, MatterNotes, EventItemConsent, EventItemPassedFlag

### Vote Info (8)
EventItemTally, IndexName, ActionName, ActionText, EventItemAgendaNote, EventItemMinutesNote, Mover, Seconder

### Additional (6)
MatterSponsors, MatterAttachmentURLs, EventItemVideo, ResultsURL, FileNumber, FileDetailURL

### Individual Votes (9)
Kate Gallego (Mayor), Ann O'Brien (D1-Vice Mayor), Jim Waring (D2), Debra Stark (D3), Laura Pastor (D4), Betty Guardado (D5), Kevin Robinson (D6), Yassamin Ansari (D7), Kesha Hodge Washington (D8)

### Video (1)
YouTubeVideoURL
