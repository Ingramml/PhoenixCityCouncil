# Data Extraction Method Comparison

This document compares the availability and ease of extraction for each data point across different methods.

## Legend

**Availability:**
- ✅ = Available
- ❌ = Not available
- ⚠️ = Partially available / Unreliable

**Ease of Extraction:**
- 🟢 Easy = Direct API call or simple HTML element
- 🟡 Medium = Requires parsing, multiple calls, or JavaScript interaction
- 🔴 Hard = Complex scraping, popups, or unreliable

---

## Data Point Comparison Table

| Data Point | Legistar API | Legistar Website | Phoenix.gov | YouTube | Notes |
|------------|--------------|------------------|-------------|---------|-------|
| **Meeting Information** |||||
| Meeting Date | ✅ 🟢 | ✅ 🟢 | ✅ 🟡 | ✅ 🔴 | API: `EventDate` field |
| Meeting Time | ✅ 🟢 | ✅ 🟢 | ✅ 🟡 | ✅ 🔴 | API: `EventTime` field |
| Body Name | ✅ 🟢 | ✅ 🟢 | ✅ 🟡 | ❌ | API: `EventBodyName` |
| Meeting URL | ✅ 🟢 | ✅ 🟢 | ⚠️ 🔴 | ❌ | API: `EventInSiteURL` |
| **Document URLs** |||||
| Agenda PDF | ❌ | ✅ 🟡 | ✅ 🟡 | ❌ | Website: Parse `<a>` with "Agenda" |
| Minutes PDF | ❌ | ✅ 🟡 | ✅ 🟡 | ❌ | Website: Parse `<a>` with "Minutes" |
| Results PDF | ❌ | ✅ 🟡 | ❌ | ❌ | Website only |
| Video Link | ❌ | ⚠️ 🔴 | ✅ 🟡 | ✅ 🟡 | Phoenix.gov/YouTube preferred |
| **Agenda Item Details** |||||
| Item Number | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemAgendaNumber` |
| Item Title | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemTitle` |
| Item Summary/Description | ⚠️ 🟡 | ✅ 🔴 | ❌ | ❌ | Website: Navigate to detail page |
| Matter Type | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemMatterType` |
| File Number | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemMatterFile` |
| Consent Flag | ✅ 🟢 | ❌ | ❌ | ❌ | API only: `EventItemConsent` |
| **Voting Information** |||||
| Passed/Failed Flag | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemPassedFlag` |
| Vote Tally (7-0, etc.) | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemTally` |
| Action Name | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemActionName` |
| Action Text | ✅ 🟢 | ✅ 🟢 | ❌ | ❌ | API: `EventItemActionText` |
| Mover | ✅ 🟢 | ✅ 🟡 | ❌ | ❌ | API: `EventItemMover` |
| Seconder | ✅ 🟢 | ✅ 🟡 | ❌ | ❌ | API: `EventItemSeconder` |
| **Individual Votes** |||||
| Per-Member Votes (Yes/No) | ❌ | ✅ 🔴 | ❌ | ❌ | Website: Action Details popup only |
| Absent Members | ❌ | ✅ 🔴 | ❌ | ❌ | Website: Action Details popup only |
| Roll Call (Attendance) | ✅ 🟡 | ✅ 🔴 | ❌ | ❌ | API: `/eventitems/{id}/rollcalls` |
| **Other** |||||
| District/Index | ✅ 🟡 | ⚠️ 🔴 | ❌ | ❌ | API: `/matters/{id}/indexes` |
| File Detail URL | ❌ | ✅ 🟡 | ❌ | ❌ | Website: Parse item links |
| Item Video Timestamp | ✅ 🟢 | ✅ 🟡 | ❌ | ❌ | API: `EventItemVideo` |

---

## Extraction Method Details

### 1. Legistar Web API

**Base URL:** `https://webapi.legistar.com/v1/phoenix`

**Pros:**
- Structured JSON data
- Fast and reliable
- No JavaScript required
- Rate-limit friendly

**Cons:**
- Missing document URLs (Phoenix doesn't populate)
- No individual votes per item
- No item summaries/descriptions
- Roll calls only show attendance, not item votes

**Key Endpoints:**
| Endpoint | Data |
|----------|------|
| `/events` | Meeting list |
| `/events/{id}/eventitems` | Agenda items |
| `/eventitems/{id}/rollcalls` | Roll call (attendance only) |
| `/matters/{id}` | Matter details |
| `/matters/{id}/indexes` | District assignments |

---

### 2. Legistar Website Scraping

**Base URL:** `https://phoenix.legistar.com`

**Pros:**
- Complete data including individual votes
- Document URLs available
- Item summaries on detail pages

**Cons:**
- Requires browser automation (Playwright)
- Slower (JavaScript rendering)
- Action Details in popup/iframe
- More fragile to page changes

**Page Types:**
| Page | URL Pattern | Data |
|------|-------------|------|
| Meeting Detail | `MeetingDetail.aspx?LEGID={id}&GID=485` | Documents, item list |
| Action Details | Popup from meeting page | Individual votes |
| Legislation Detail | `LegislationDetail.aspx?ID={id}` | Full item summary |

---

### 3. Phoenix.gov City Clerk Page

**URL:** `https://www.phoenix.gov/administration/departments/cityclerk/programs-services/city-council-meetings.html`

**Pros:**
- Official city source
- YouTube video links (directly to youtube.com)
- Clean public interface
- Pagination via URL parameter (predictable)

**Cons:**
- JavaScript-rendered (dynamic table)
- Limited meeting details
- No individual agenda items
- Requires browser automation (Playwright)
- "See More" button must be clicked to reveal video links
- Container-to-video matching is unreliable with automated scraping

**Available Data:**
- Meeting dates (format: "Jan 3, 2024")
- Meeting type (Formal Meeting, Policy Session, etc.)
- Document links (Agenda, Minutes) - in expanded view
- Video links (YouTube URLs) - in expanded view

**Page Structure:**
```
URL: ...city-council-meetings.html?offsetdynamic-table={offset}&limitdynamic-table=10

+----------------------------------------------------------+
| Meeting Table (10 items per page)                         |
+----------------------------------------------------------+
| Jan 3, 2024 | Formal Meeting | [See More]                |
|   (expanded view after clicking See More):               |
|   +----------------------------------------------------+ |
|   | Agenda: [link]  Minutes: [link]  Video: [YT link]  | |
|   +----------------------------------------------------+ |
+----------------------------------------------------------+
| Jan 10, 2024 | Policy Session | [See More]               |
+----------------------------------------------------------+
```

**Pagination:**
- 10 meetings per page
- Offset parameter: `offsetdynamic-table=0`, `10`, `20`, etc.
- Q1 2024 Formal Meetings are approximately at offsets 130-180

---

### 4. YouTube Channel

**Channel:** City of Phoenix AZ (`@cityofphoenixaz`)
**Channel ID:** `x7FQNzOFCbtExt_gRub9JQ`

**RSS Feed URL:** `https://www.youtube.com/feeds/videos.xml?channel_id=x7FQNzOFCbtExt_gRub9JQ`

**Pros:**
- Direct video links
- Consistent URL pattern
- Public access
- RSS feed available (no API key needed)

**Cons:**
- RSS feed only returns last ~15 videos (not useful for historical data)
- Direct web scraping blocked by YouTube
- Requires matching video to meeting date via title parsing
- Title format varies: "City Council Formal Meeting January 3, 2024"
- No structured API without YouTube Data API key
- WebFetch tools blocked from youtube.com domain

**URL Patterns:**
- Standard: `https://www.youtube.com/watch?v={video_id}`
- Live stream: `https://www.youtube.com/live/{video_id}?si={tracking_id}`

**Video Title Format (Formal Meetings):**
```
City Council Formal Meeting {Month} {Day}, {Year}
Example: "City Council Formal Meeting January 3, 2024"
```

**Date Extraction Regex:**
```python
r'(january|february|march|...|december)[,\s]+(\d{1,2})[,\s]+(\d{4})'
```

---

## Recommended Extraction Strategy

Based on the comparison, the optimal approach combines methods:

| Data Category | Primary Source | Fallback |
|---------------|----------------|----------|
| Meeting metadata | Legistar API | Website |
| Agenda items | Legistar API | Website |
| Document URLs | Legistar Website | Phoenix.gov |
| Individual votes | Legistar Website | None |
| Item summaries | Legistar Website | None |
| Video links | Phoenix.gov (manual/semi-auto) | YouTube RSS (recent only) |

### Implementation Priority

1. **Legistar API First** - Get all structured data (fast, reliable)
2. **Legistar Website** - Supplement with document URLs, individual votes, summaries (slower, complete)
3. **Phoenix.gov** - Best source for video links (has YouTube URLs in expanded meeting details)
4. **YouTube RSS** - Only useful for recent videos (last ~15 uploads)

---

## Data Coverage Summary

| Source | Meeting Data | Item Data | Votes | Documents | Video |
|--------|--------------|-----------|-------|-----------|-------|
| Legistar API | ✅ Full | ✅ Full | ⚠️ Tally only | ❌ | ⚠️ Timestamp |
| Legistar Website | ✅ Full | ✅ Full | ✅ Individual | ✅ Full | ⚠️ External link |
| Phoenix.gov | ✅ Basic | ❌ | ❌ | ✅ Limited | ✅ |
| YouTube | ⚠️ Title only | ❌ | ❌ | ❌ | ✅ |

---

## Technical Requirements

| Method | Requirements | Difficulty |
|--------|--------------|------------|
| Legistar API | `requests` library | Easy |
| Legistar Website | Playwright, browser automation | Medium-Hard |
| Phoenix.gov | Playwright (dynamic content) | Medium-Hard |
| YouTube RSS | `requests` + XML parsing | Easy |
| YouTube Direct | YouTube Data API key | Medium |

---

## Lessons Learned

### Video Link Extraction (January 2025)

#### What Worked

1. **YouTube RSS Feed** - Simple and reliable for recent videos
   - URL: `https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}`
   - Returns structured XML with video IDs, titles, and publish dates
   - No authentication required
   - Fast response times

2. **Phoenix.gov Manual Navigation** - Most reliable for historical videos
   - Pagination is predictable via URL parameters
   - Video links are YouTube URLs (not internal phoenix.gov/phxtv links)
   - Each meeting has a "See More" button that reveals documents and video
   - Manual collection via browser is more reliable than automated scraping

3. **Date Matching Strategy**
   - Convert CSV dates (YYYY-MM-DD) to Phoenix.gov format ("Jan 3, 2024")
   - Match on both date AND "Formal Meeting" text to avoid Policy Sessions
   - Use exact date matching, not fuzzy matching

#### What Didn't Work

1. **Direct YouTube Scraping**
   - WebFetch tools are blocked from youtube.com domain
   - Browser automation on YouTube is complex and unreliable

2. **YouTube RSS for Historical Data**
   - RSS feed only returns last ~15 videos
   - Q1 2024 meetings are too old to appear in RSS feed
   - Would need YouTube Data API for historical searches

3. **Fully Automated Phoenix.gov Scraping**
   - Container-to-video matching was unreliable
   - CSS selectors (`.cmp-dynamic-table__data-row`) didn't consistently match
   - Clicking "See More" reveals video in a table, but finding the RIGHT table for the RIGHT meeting was problematic
   - Multiple expanded sections can cause video URL mix-ups

#### Recommended Approach for Video Links

**For Recent Meetings (last 2-3 weeks):**
```python
# Use YouTube RSS feed
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=x7FQNzOFCbtExt_gRub9JQ"
# Parse XML, extract video IDs, match to meeting dates via title
```

**For Historical Meetings:**
1. Navigate to Phoenix.gov meetings page with appropriate offset
2. Manually click "See More" for each target meeting
3. Copy YouTube URL from expanded section
4. Semi-automated approach is more reliable than fully automated

**Video URLs Found (Q1 2024):**
| Meeting Date | YouTube URL |
|--------------|-------------|
| 2024-01-03 | https://www.youtube.com/live/2pYatm9O8M8 |
| 2024-01-24 | https://www.youtube.com/watch?v=DXpLUWRvuaI |
| 2024-02-07 | https://www.youtube.com/watch?v=yBL6eaE3iYo |
| 2024-02-21 | https://www.youtube.com/watch?v=04GOmfa2UkM |
| 2024-03-06 | https://www.youtube.com/watch?v=JU5JtxQUxwM |
| 2024-03-20 | https://www.youtube.com/watch?v=HPBZRrGZ8PE |

---

## Scripts Reference

| Script | Purpose | Data Sources |
|--------|---------|--------------|
| `fetch_2024_data.py` | Basic API-only extraction | Legistar API |
| `fetch_2024_data_enhanced.py` | Full extraction with votes/summaries | Legistar API + Website |
| `fetch_youtube_videos.py` | Video link extraction | YouTube RSS + Phoenix.gov |

---

## Output Files

| File | Contents | Rows |
|------|----------|------|
| `phoenix_council_2024_Q1.csv` | Basic API data | ~600 |
| `phoenix_council_2024_Q1_enhanced.csv` | With individual votes, summaries | 639 |
| `phoenix_council_2024_Q1_enhanced_with_videos.csv` | With YouTube video URLs | 639 |

