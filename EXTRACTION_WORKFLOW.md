# Phoenix City Council Data Extraction Workflow

A complete technical reference for the three-phase data extraction pipeline.

---

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run extraction for a specific quarter (e.g., Q2 2020)
python fetch_2020_data_enhanced.py --start-month 4 --end-month 7 --output phoenix_council_2020_Q2_enhanced.csv

# Add video links (optional)
python fetch_youtube_videos.py --update-csv
```

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA EXTRACTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PHASE 1: Legistar API          PHASE 2: Website Scraping                  │
│   ──────────────────────         ────────────────────────                   │
│   ~2 minutes                     ~30-60 minutes                             │
│                                                                              │
│   ┌─────────────────────┐        ┌─────────────────────┐                    │
│   │ fetch_XXXX_data_    │───────▶│ (same script)       │                    │
│   │ enhanced.py         │        │ Playwright browser  │                    │
│   └─────────────────────┘        └─────────────────────┘                    │
│            │                              │                                  │
│            ▼                              ▼                                  │
│   ┌─────────────────────┐        ┌─────────────────────┐                    │
│   │ Meeting metadata    │        │ Individual votes    │                    │
│   │ Agenda items        │        │ Document URLs       │                    │
│   │ Vote tallies        │        │ Item detail URLs    │                    │
│   │ Actions/Movers      │        │ Absent members      │                    │
│   └─────────────────────┘        └─────────────────────┘                    │
│                                                                              │
│                           PHASE 3: Video Links                              │
│                           ───────────────────                               │
│                           ~10 minutes                                       │
│                                                                              │
│                           ┌─────────────────────┐                           │
│                           │ fetch_youtube_      │                           │
│                           │ videos.py           │                           │
│                           └─────────────────────┘                           │
│                                    │                                         │
│                                    ▼                                         │
│                           ┌─────────────────────┐                           │
│                           │ YouTube video URLs  │                           │
│                           └─────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Legistar API

### What It Does
Fetches structured meeting data from the Legistar REST API. This is fast and reliable but incomplete.

### API Endpoint
```
Base URL: https://webapi.legistar.com/v1/phoenix
```

### Key Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/events?$filter=EventBodyId eq 138...` | Get formal meeting list |
| `/events/{EventId}/eventitems` | Get agenda items for a meeting |
| `/eventitems/{EventItemId}/rollcalls` | Get roll call attendance (NOT item votes) |

### Data Retrieved

| Field | API Path |
|-------|----------|
| MeetingDate | `events.EventDate` |
| BodyName | `events.EventBodyName` |
| EventInSiteURL | `events.EventInSiteURL` |
| AgendaItemNumber | `eventitems.EventItemAgendaNumber` |
| AgendaItemTitle | `eventitems.EventItemTitle` |
| MatterTypeName | `eventitems.EventItemMatterType` |
| EventItemConsent | `eventitems.EventItemConsent` |
| EventItemPassedFlag | `eventitems.EventItemPassedFlag` |
| EventItemTally | `eventitems.EventItemTally` |
| ActionName | `eventitems.EventItemActionName` |
| ActionText | `eventitems.EventItemActionText` |
| Mover | `eventitems.EventItemMover` |
| Seconder | `eventitems.EventItemSeconder` |

### What's NOT Available from API

| Missing Data | Reason |
|--------------|--------|
| Individual votes (Yes/No per member) | API only has attendance, not item-level votes |
| Document URLs (Agenda/Minutes PDFs) | Phoenix doesn't populate these fields |
| Full item summaries | API only has short titles |

---

## Phase 2: Website Scraping

### What It Does
Uses Playwright browser automation to scrape data not available from the API.

### Website Structure

**Meeting Page:** `https://phoenix.legistar.com/MeetingDetail.aspx?ID={EventId}...`

```
┌──────────────────────────────────────────────────────────────────┐
│  MEETING HEADER                                                   │
│  ─────────────────────────────────────────────────────────────── │
│  Meeting: City Council Formal Meeting                             │
│  Date: 1/3/2024                                                   │
│                                                                   │
│  [Agenda PDF]  [Minutes PDF]  [Results PDF]  [Video]             │
├──────────────────────────────────────────────────────────────────┤
│  AGENDA ITEMS TABLE                                               │
│  ─────────────────────────────────────────────────────────────── │
│  │ File #  │ Agenda # │ Type │ Title │ Action │ Action Details │ │
│  ├─────────┼──────────┼──────┼───────┼────────┼────────────────┤ │
│  │ 23-110  │    1     │ Min  │ For...│approved│    [link]      │ │
│  │ 23-234  │    2     │ Res  │ Auth..│adopted │    [link]      │ │
│  └─────────┴──────────┴──────┴───────┴────────┴────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Scraping Process

```
FOR EACH MEETING:
│
├─→ 1. Navigate to meeting page
│
├─→ 2. Extract document URLs from header
│      • Find <a> containing "Agenda" → agenda_url
│      • Find <a> containing "Minutes" → minutes_url
│      • Find <a> containing "Results" → results_url
│
├─→ 3. Collect file numbers and detail URLs
│      • Find all <a> matching pattern "XX-XXXX"
│      • Map file_number → LegislationDetail.aspx URL
│
└─→ 4. FOR EACH "Action details" link:
       │
       ├─→ Click link to open popup
       │
       ├─→ Wait for popup/iframe to load
       │
       ├─→ Extract vote table:
       │   ┌────────────────────────┬────────┐
       │   │ Betty Guardado         │ Absent │
       │   │ Kesha Hodge Washington │ Yes    │
       │   │ Ann O'Brien            │ Yes    │
       │   │ Laura Pastor           │ Yes    │
       │   │ ...                    │ ...    │
       │   └────────────────────────┴────────┘
       │
       ├─→ Track absent members
       │
       └─→ Close popup (Escape key or Close button)
```

### Action Details Popup Structure

```
┌────────────────────────────────────────────────────────┐
│ City of Phoenix - Action Details                  [X]  │
├────────────────────────────────────────────────────────┤
│ File #: 23-3110                                        │
│ Type: Minutes                                          │
│ Title: For Approval or Correction...                   │
├────────────────────────────────────────────────────────┤
│ Mover: Jim Waring    Seconder: Debra Stark             │
├────────────────────────────────────────────────────────┤
│ Action: approved                                       │
│ Action text: A motion was made by Councilman Waring... │
├────────────────────────────────────────────────────────┤
│ Votes (8:0)                                            │
│ ┌────────────────────────────┬────────┐                │
│ │ Person Name                │ Vote   │                │
│ ├────────────────────────────┼────────┤                │
│ │ Betty Guardado             │ Absent │                │
│ │ Kesha Hodge Washington     │ Yes    │                │
│ │ Ann O'Brien                │ Yes    │                │
│ │ Laura Pastor               │ Yes    │                │
│ │ Kevin Robinson             │ Yes    │                │
│ │ Debra Stark                │ Yes    │                │
│ │ Jim Waring                 │ Yes    │                │
│ │ Yassamin Ansari            │ Yes    │                │
│ │ Kate Gallego               │ Yes    │                │
│ └────────────────────────────┴────────┘                │
└────────────────────────────────────────────────────────┘
```

### Data Retrieved from Website

| Data | Source Location |
|------|-----------------|
| Agenda PDF URL | Meeting page header link |
| Minutes PDF URL | Meeting page header link |
| Results PDF URL | Meeting page header link |
| File numbers | Items table, first column |
| Item detail URLs | File # hyperlinks |
| Individual votes | Action Details popup table |
| Absent members | Votes marked "Absent" |

---

## Phase 3: Video Links

### What It Does
Adds YouTube video URLs to the CSV for each meeting.

### Data Sources

| Source | Coverage | Method |
|--------|----------|--------|
| YouTube RSS Feed | Last ~15 videos | Automated XML parsing |
| Phoenix.gov | Historical | Manual/semi-automated |

### YouTube RSS Feed
```
URL: https://www.youtube.com/feeds/videos.xml?channel_id=x7FQNzOFCbtExt_gRub9JQ
```

### Phoenix.gov Archive
```
URL: https://www.phoenix.gov/administration/departments/cityclerk/programs-services/city-council-meetings.html
```

---

## Scripts Reference

### Main Extraction Scripts

| Script | Year | Purpose |
|--------|------|---------|
| `fetch_2024_data_enhanced.py` | 2024 | Phase 1 + Phase 2 combined |
| `fetch_2020_data_enhanced.py` | 2020 | Phase 1 + Phase 2 combined |
| `fetch_2024_data.py` | 2024 | Phase 1 only (API) |
| `fetch_youtube_videos.py` | Any | Phase 3 (video links) |

### Command-Line Options

```bash
python fetch_2024_data_enhanced.py [OPTIONS]

Options:
  --start-month INT    Start month (1-12), default: 1
  --end-month INT      End month (1-12, exclusive), default: 4
  --output PATH        Output CSV file path
  --scrape-summaries   Also scrape item summaries (slow)
  --headed             Run browser in visible mode
```

### Examples

```bash
# Q1 2024 (January-March)
python fetch_2024_data_enhanced.py --start-month 1 --end-month 4

# Q2 2024 (April-June)
python fetch_2024_data_enhanced.py --start-month 4 --end-month 7

# Full year 2024
python fetch_2024_data_enhanced.py --start-month 1 --end-month 13

# Q2 2020 with custom output
python fetch_2020_data_enhanced.py --start-month 4 --end-month 7 --output phoenix_2020_Q2.csv

# With visible browser for debugging
python fetch_2024_data_enhanced.py --headed
```

---

## Output CSV Structure

### Column Groups

**Meeting Info (6 columns)**
- MeetingDate, MeetingType, BodyName, EventInSiteURL, EventAgendaFile, EventMinutesFile

**Item Info (10 columns)**
- EventVideoPath, MatterTypeName, MatterRequester, AgendaItemNumber, AgendaItemTitle
- AgendaItemDescription, MatterPassedDate, MatterNotes, EventItemConsent, EventItemPassedFlag

**Vote Info (8 columns)**
- EventItemTally, IndexName, ActionName, ActionText
- EventItemAgendaNote, EventItemMinutesNote, Mover, Seconder

**Additional (6 columns)**
- MatterSponsors, MatterAttachmentURLs, EventItemVideo, ResultsURL, FileNumber, FileDetailURL

**Individual Votes (9 columns)**
- One column per council member with their vote (Yes/No/Absent/Consent/Voice Vote)

### Council Member Columns

**2024 Roster:**
- Kate Gallego (Mayor)
- Ann O'Brien (D1-Vice Mayor)
- Jim Waring (D2)
- Debra Stark (D3)
- Laura Pastor (D4)
- Betty Guardado (D5)
- Kevin Robinson (D6)
- Yassamin Ansari (D7)
- Kesha Hodge Washington (D8)

**2020 Roster:**
- Kate Gallego (Mayor)
- Thelda Williams (D1-Vice Mayor)
- Jim Waring (D2)
- Debra Stark (D3)
- Laura Pastor (D4)
- Betty Guardado (D5)
- Sal DiCiccio (D6)
- Michael Nowakowski (D7)
- Carlos Garcia (D8)

---

## Technical Details

### Dependencies

```
requests        # HTTP requests to Legistar API
playwright      # Browser automation (Chromium)
csv             # CSV file writing
re              # Regular expression matching
argparse        # Command-line argument parsing
datetime        # Date/time manipulation
```

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install requests playwright
playwright install chromium
```

### Performance Characteristics

| Phase | Time | Bottleneck |
|-------|------|------------|
| Phase 1 (API) | 2-5 min | Network latency |
| Phase 2 (Scraping) | 30-60 min | Browser automation |
| Phase 3 (Videos) | 10 min | Manual collection |
| **Total per quarter** | **45-75 min** | |

### Rate Limiting

- API: 0.5s delay between calls
- Website: 0.8s delay between popup clicks
- Between meetings: 1s delay

---

## Data Flow Diagram

```
                    ┌─────────────────┐
                    │   Legistar API  │
                    │  webapi.legistar│
                    │   .com/v1/      │
                    │    phoenix      │
                    └────────┬────────┘
                             │
                             │ GET /events
                             │ GET /events/{id}/eventitems
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   fetch_XXXX_data_enhanced.py                               │
│                                                              │
│   ┌─────────────────┐         ┌─────────────────┐           │
│   │  API Data       │         │  Scraped Data   │           │
│   │  ───────────    │         │  ────────────   │           │
│   │  • Meetings     │         │  • Votes        │           │
│   │  • Items        │         │  • Documents    │           │
│   │  • Tallies      │         │  • URLs         │           │
│   │  • Actions      │         │  • Absences     │           │
│   └────────┬────────┘         └────────┬────────┘           │
│            │                           │                     │
│            └───────────┬───────────────┘                     │
│                        │                                     │
│                        ▼                                     │
│               ┌────────────────┐                             │
│               │  MERGE DATA    │                             │
│               │  Build CSV Row │                             │
│               └────────┬───────┘                             │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │  phoenix_      │
                │  council_      │
                │  XXXX_QX_      │
                │  enhanced.csv  │
                └────────┬───────┘
                         │
                         │ (optional)
                         ▼
                ┌────────────────┐
                │ fetch_youtube_ │
                │ videos.py      │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │  _with_videos  │
                │  .csv          │
                └────────────────┘
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: playwright` | Not using venv | `source venv/bin/activate` |
| Browser timeout | Slow network | Increase timeout in script |
| Empty votes | Popup didn't load | Add longer sleep times |
| Missing council members | Wrong roster for year | Use correct script (2020 vs 2024) |

### Debug Mode

Run with visible browser to see what's happening:

```bash
python fetch_2024_data_enhanced.py --headed
```

### Check Background Process

```bash
# See if extraction is running
ps aux | grep fetch_

# Check output file size
ls -la phoenix_council_*.csv
```

---

## Output Files

| File Pattern | Description |
|--------------|-------------|
| `phoenix_council_YYYY_QX.csv` | API-only data |
| `phoenix_council_YYYY_QX_enhanced.csv` | API + scraped votes/docs |
| `phoenix_council_YYYY_QX_enhanced_with_videos.csv` | Complete with video URLs |
