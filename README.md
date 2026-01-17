# Phoenix City Council Data

A comprehensive data collection and analysis project for Phoenix City Council voting records.

## Overview

This project collects, processes, and stores voting data from Phoenix City Council Formal Meetings. The goal is to build a public transparency database covering 10 years of council voting history (2015-2025).

## Data Sources

| Source | Data | Method |
|--------|------|--------|
| [Legistar API](https://webapi.legistar.com/v1/phoenix) | Meeting metadata, agenda items, vote tallies | REST API |
| [Legistar Website](https://phoenix.legistar.com) | Individual votes, document URLs | Playwright scraping |
| [Phoenix.gov](https://www.phoenix.gov/cityclerk) | YouTube video links | Manual/semi-automated |
| YouTube RSS | Recent video links | XML parsing |

## Data Collected

- **Meetings**: Date, type, document URLs, video links
- **Agenda Items**: File number, title, description, vote tally, action
- **Individual Votes**: How each council member voted on each item
- **Council Members**: Name, district, term dates

## Project Structure

```
PhoenixCityCouncil/
├── Scripts
│   ├── fetch_2020_data_enhanced.py    # Q1 2020 data collection
│   ├── fetch_2024_data_enhanced.py    # 2024 data collection
│   ├── fetch_2024_data.py             # Basic API-only fetch
│   └── fetch_youtube_videos.py        # Video URL extraction
│
├── Data (CSV)
│   ├── phoenix_council_2020_Q1_enhanced.csv
│   └── phoenix_council_2024_Q1_enhanced.csv
│
├── Documentation
│   ├── DATA_COLLECTION_WORKFLOW.md    # Step-by-step workflow
│   ├── DATA_EXTRACTION_COMPARISON.md  # Source comparison
│   ├── OPERATIONAL_MODES.md           # Backlog vs incremental
│   ├── OPTIMIZATION_RECOMMENDATIONS.md
│   ├── SCRAPING_PROCESS.md            # Technical details
│   ├── PhoenixCityCouncil_DBdraft.md  # Database schema
│   └── CLAUDE_USAGE_GUIDE.md          # AI assistant usage
│
└── README.md
```

## Quick Start

### Prerequisites

```bash
pip install requests playwright
playwright install chromium
```

### Collect Q1 2024 Data

```bash
# Basic API data
python fetch_2024_data.py

# Enhanced with individual votes
python fetch_2024_data_enhanced.py --start-month 1 --end-month 4
```

### Collect Q1 2020 Data

```bash
python fetch_2020_data_enhanced.py --start-month 1 --end-month 4
```

## Output CSV Format

| Column | Description |
|--------|-------------|
| MeetingDate | Date (YYYY-MM-DD) |
| FileNumber | Legislation ID (e.g., "24-0123") |
| AgendaItemTitle | Item title |
| EventItemTally | Vote count (e.g., "7-0") |
| EventItemVideo | YouTube video URL |
| Kate Gallego (Mayor) | Individual vote |
| ... | (all 9 council members) |

See [SCRAPING_PROCESS.md](SCRAPING_PROCESS.md) for full column list.

## Council Members

### 2024 Roster
| District | Member |
|----------|--------|
| Mayor | Kate Gallego |
| D1 (Vice Mayor) | Ann O'Brien |
| D2 | Jim Waring |
| D3 | Debra Stark |
| D4 | Laura Pastor |
| D5 | Betty Guardado |
| D6 | Kevin Robinson |
| D7 | Yassamin Ansari |
| D8 | Kesha Hodge Washington |

### 2020 Roster (Different Members)
| District | Member |
|----------|--------|
| D1 (Vice Mayor) | Thelda Williams |
| D6 | Sal DiCiccio |
| D7 | Michael Nowakowski |
| D8 | Carlos Garcia |

## Database Schema

See [PhoenixCityCouncil_DBdraft.md](PhoenixCityCouncil_DBdraft.md) for the full database schema designed to support:
- Member voting history
- Controversial vote tracking
- Attendance statistics
- Legislation search

## Data Collection Status

| Period | Status | Rows | Video Coverage |
|--------|--------|------|----------------|
| Q1 2020 | ✅ Complete | 636 | 84% (5/6 meetings) |
| Q1 2024 | ✅ Complete | 639 | 100% (6/6 meetings) |

## License

This project collects publicly available government data for transparency purposes.

## Contributing

Contributions welcome! See the documentation files for technical details on the data collection process.
