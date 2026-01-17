# Operational Modes: Backlog vs. Incremental Data Collection

This document outlines two distinct workflows for Phoenix City Council data collection:
1. **Backlog Mode** - Initial bulk historical data load
2. **Incremental Mode** - Ongoing updates for recent/upcoming meetings

---

## Overview

| Mode | Purpose | Frequency | Speed Priority | Data Completeness |
|------|---------|-----------|----------------|-------------------|
| **Backlog** | Initial historical load | One-time | Lower (thoroughness matters) | Maximum |
| **Incremental** | Ongoing updates | Daily/Weekly | Higher (efficiency matters) | Recent data only |

---

## Mode 1: Backlog (Historical Data Build)

### Purpose
- Build complete historical database from scratch
- Fill in all past meetings for a given period (e.g., 2020-2024)
- Get ALL data points including individual votes and summaries
- Run once per historical period

### Characteristics
- **Speed**: Can run overnight or over multiple days
- **Completeness**: Scrape everything including item summaries
- **Error handling**: Retry failed items, log for manual review
- **Output**: Complete CSV files per quarter/year

### Recommended Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ BACKLOG MODE: Historical Data Collection                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Define date range                                   │
│   - Start date (e.g., 2020-01-01)                          │
│   - End date (e.g., 2024-12-31)                            │
│   - Body type: Formal Meetings (EventBodyId = 138)          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: API Bulk Load (Fast)                                │
│   - Fetch all events in date range                          │
│   - Fetch all event items for each event                    │
│   - Store raw JSON for backup                               │
│   - ~5-10 minutes for 4 years of data                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Website Scraping (Slow - run overnight)             │
│   - Process one quarter at a time                           │
│   - Scrape document URLs                                    │
│   - Scrape individual votes from Action Details             │
│   - Scrape item summaries (optional, adds hours)            │
│   - ~45-60 min per quarter                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Video Links (Semi-manual)                           │
│   - Use Phoenix.gov for historical videos                   │
│   - Collect video URLs per meeting                          │
│   - ~10 min per quarter                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Validation & Merge                                  │
│   - Verify row counts match expected meetings               │
│   - Check for missing votes, broken URLs                    │
│   - Merge quarterly files into master database              │
└─────────────────────────────────────────────────────────────┘
```

### Commands for Backlog Mode

```bash
# Activate environment
source venv/bin/activate

# Process each quarter separately (more manageable)

# Q1 2024
python fetch_2024_data_enhanced.py --start-month 1 --end-month 4 \
  --output phoenix_council_2024_Q1_enhanced.csv --scrape-summaries

# Q2 2024
python fetch_2024_data_enhanced.py --start-month 4 --end-month 7 \
  --output phoenix_council_2024_Q2_enhanced.csv --scrape-summaries

# Q3 2024
python fetch_2024_data_enhanced.py --start-month 7 --end-month 10 \
  --output phoenix_council_2024_Q3_enhanced.csv --scrape-summaries

# Q4 2024
python fetch_2024_data_enhanced.py --start-month 10 --end-month 13 \
  --output phoenix_council_2024_Q4_enhanced.csv --scrape-summaries

# Add video links to each
python fetch_youtube_videos.py --csv phoenix_council_2024_Q1_enhanced.csv --update-csv
# Repeat for each quarter
```

### Backlog Script Enhancements Needed

```python
# Add to fetch_2024_data_enhanced.py:

# 1. Progress tracking with checkpoint/resume
--checkpoint-file backlog_progress.json

# 2. Raw JSON backup
--save-raw-json raw_data/

# 3. Error logging
--error-log backlog_errors.csv

# 4. Year parameter (not just 2024)
--year 2023
```

### Time Estimates for Full Backlog

| Year | Meetings | API Time | Scrape Time | Video Time | Total |
|------|----------|----------|-------------|------------|-------|
| 2024 | ~24 | 5 min | 3-4 hours | 40 min | ~5 hours |
| 2023 | ~24 | 5 min | 3-4 hours | 40 min | ~5 hours |
| 2022 | ~24 | 5 min | 3-4 hours | 40 min | ~5 hours |
| 2021 | ~24 | 5 min | 3-4 hours | 40 min | ~5 hours |
| 2020 | ~24 | 5 min | 3-4 hours | 40 min | ~5 hours |
| **Total** | ~120 | 25 min | 15-20 hours | 3+ hours | **~25 hours** |

**Recommendation**: Run backlog overnight in batches.

---

## Mode 2: Incremental (Recent/Upcoming Meetings)

### Purpose
- Keep data current with minimal effort
- Fetch recent meetings (past 2 weeks)
- Fetch upcoming/scheduled meetings
- Run regularly (daily or weekly)

### Characteristics
- **Speed**: Must complete in minutes, not hours
- **Completeness**: Essential data only (skip slow summaries)
- **Smart updates**: Only fetch new/changed meetings
- **Output**: Append to or update existing database

### Recommended Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ INCREMENTAL MODE: Recent/Upcoming Updates                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Determine update window                             │
│   - Recent: Past 14 days (meetings that may have new data)  │
│   - Upcoming: Next 30 days (scheduled meetings)             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Check existing data                                 │
│   - Load current CSV/database                               │
│   - Identify meetings already processed                     │
│   - Skip meetings with complete data                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Fast API fetch                                      │
│   - Get events in update window                             │
│   - Get event items for new/updated meetings                │
│   - ~30 seconds                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Selective scraping (only if meeting occurred)       │
│   - Skip upcoming meetings (no votes yet)                   │
│   - Scrape votes only for completed meetings                │
│   - Skip summaries (optional, run weekly if needed)         │
│   - ~5-10 min for 1-2 meetings                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Video links (recent only)                           │
│   - Use YouTube RSS (has last ~15 videos)                   │
│   - Automatic matching by date                              │
│   - ~30 seconds                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Merge updates                                       │
│   - Upsert new rows into master CSV/database                │
│   - Update existing rows with new data                      │
│   - Log changes for audit trail                             │
└─────────────────────────────────────────────────────────────┘
```

### Incremental Script (New)

```bash
# New script: fetch_incremental.py

# Daily update - fast, essential data only
python fetch_incremental.py --mode daily

# Weekly update - more thorough
python fetch_incremental.py --mode weekly --include-summaries

# Custom window
python fetch_incremental.py --days-back 14 --days-forward 30
```

### Key Differences from Backlog

| Aspect | Backlog | Incremental |
|--------|---------|-------------|
| Date range | Historical (months/years) | Rolling window (days/weeks) |
| Meetings processed | All in range | Only new/changed |
| Scrape summaries | Yes (complete data) | No (speed priority) |
| Video source | Phoenix.gov (manual) | YouTube RSS (automatic) |
| Sleep times | Standard (reliability) | Reduced (speed) |
| Error handling | Log and continue | Retry immediately |
| Run frequency | Once | Daily/Weekly |
| Expected runtime | Hours | Minutes |

---

## Data Sources by Mode

### Backlog Mode Sources

| Data | Source | Notes |
|------|--------|-------|
| Meeting list | Legistar API | Full date range query |
| Agenda items | Legistar API | All items per meeting |
| Individual votes | Legistar Website | Scrape Action Details popups |
| Document URLs | Legistar Website | From meeting page header |
| Item summaries | Legistar Website | Navigate to each item detail page |
| Video links | Phoenix.gov | Manual collection required |

### Incremental Mode Sources

| Data | Source | Notes |
|------|--------|-------|
| Meeting list | Legistar API | Rolling window query |
| Agenda items | Legistar API | Only new meetings |
| Individual votes | Legistar Website | Only for completed meetings |
| Document URLs | Legistar Website | Quick extraction |
| Item summaries | Skip | Add in weekly batch if needed |
| Video links | YouTube RSS | Automatic for recent videos |

---

## Proposed Script Structure

### Option A: Single Script with Modes

```bash
# fetch_data.py with mode flag

# Backlog mode
python fetch_data.py --mode backlog --year 2024 --quarter Q1

# Incremental mode
python fetch_data.py --mode incremental --days-back 14
```

### Option B: Separate Scripts (Recommended)

```
scripts/
├── fetch_backlog.py        # Historical bulk load
├── fetch_incremental.py    # Recent/upcoming updates
├── fetch_youtube_videos.py # Video link utility
└── merge_data.py           # Combine/update CSV files
```

**Recommendation**: Separate scripts are cleaner and easier to maintain.

---

## Incremental Script Requirements

### Core Features

```python
# fetch_incremental.py

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['daily', 'weekly'], default='daily')
    parser.add_argument('--days-back', type=int, default=14)
    parser.add_argument('--days-forward', type=int, default=30)
    parser.add_argument('--master-csv', required=True, help='Existing CSV to update')
    parser.add_argument('--include-summaries', action='store_true')
    args = parser.parse_args()

    # 1. Calculate date window
    start_date = datetime.now() - timedelta(days=args.days_back)
    end_date = datetime.now() + timedelta(days=args.days_forward)

    # 2. Load existing data
    existing_meetings = load_existing_csv(args.master_csv)

    # 3. Fetch new/updated meetings from API
    meetings = fetch_meetings_in_window(start_date, end_date)

    # 4. Filter to only process new or incomplete meetings
    to_process = filter_new_meetings(meetings, existing_meetings)

    # 5. For each meeting that has occurred:
    for meeting in to_process:
        if meeting['date'] <= datetime.now():
            # Scrape votes (fast mode - reduced sleeps)
            votes = scrape_meeting_votes_fast(meeting)

    # 6. Get video URLs from YouTube RSS (recent only)
    video_urls = fetch_youtube_rss_videos()

    # 7. Merge updates into master CSV
    merge_updates(args.master_csv, new_data)
```

### Speed Optimizations for Incremental Mode

```python
# Reduced wait times for incremental mode
INCREMENTAL_CONFIG = {
    'page_load_wait': 0.5,      # vs 2.0 in backlog
    'popup_wait': 0.3,          # vs 0.8 in backlog
    'between_meetings': 0.3,    # vs 1.0 in backlog
    'wait_strategy': 'domcontentloaded',  # vs 'networkidle'
}
```

---

## Scheduling Recommendations

### Backlog (One-Time)

```bash
# Run overnight or on weekend
nohup python fetch_backlog.py --year 2024 > backlog_2024.log 2>&1 &
```

### Incremental (Recurring)

```bash
# Daily cron job (6 AM)
0 6 * * * cd /path/to/project && ./venv/bin/python fetch_incremental.py --mode daily

# Weekly cron job (Sunday 2 AM) - more thorough
0 2 * * 0 cd /path/to/project && ./venv/bin/python fetch_incremental.py --mode weekly --include-summaries
```

---

## Implementation Priority

### Phase 1: Backlog Script Improvements
1. Add year/quarter parameters to existing script
2. Add checkpoint/resume capability
3. Add raw JSON backup
4. Test with 2023 data

### Phase 2: Create Incremental Script
1. Build `fetch_incremental.py` with rolling window
2. Implement fast mode (reduced sleeps)
3. Add YouTube RSS integration
4. Add CSV merge/upsert logic

### Phase 3: Automation
1. Set up cron jobs for incremental updates
2. Add error alerting (email/Slack)
3. Add data validation checks

---

## Output File Strategy

### Backlog Files (Archived)
```
data/
├── backlog/
│   ├── 2020/
│   │   ├── phoenix_council_2020_Q1.csv
│   │   ├── phoenix_council_2020_Q2.csv
│   │   └── ...
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   └── 2024/
```

### Master File (Current)
```
data/
├── phoenix_council_master.csv      # All historical + recent
├── phoenix_council_master.csv.bak  # Backup before update
└── update_log.csv                  # Audit trail of changes
```

### Incremental Updates
```
data/
├── incremental/
│   ├── update_2025-01-17.csv       # Daily update files
│   ├── update_2025-01-18.csv
│   └── ...
```
