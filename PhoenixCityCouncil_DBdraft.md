# Phoenix City Council Database Schema

## Purpose

This database powers a public transparency website for Phoenix City Council voting records. It enables citizens to:

1. **Track Council Member Voting Patterns** - See how each member votes over time
2. **Search Legislation** - Find items by keyword, type, district, or outcome
3. **Identify Controversial Votes** - Surface non-unanimous and close votes
4. **Compare Members** - See where council members agree or disagree
5. **Monitor Attendance** - Track absences and participation rates
6. **Access Meeting Videos** - Link directly to YouTube recordings

**Data Scope:** 10 years of Phoenix City Council Formal Meetings (2015-2025)

**Estimated Volume:**
- ~480 meetings
- ~30,000 agenda items
- ~270,000 individual votes
- ~25 council members across all terms

---

## Table Descriptions

### Reference Tables

These tables store lookup values and rarely change.

---

#### `council_members`

**Purpose:** Master list of all council members who have served during the data period.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| first_name | VARCHAR(50) | First name |
| last_name | VARCHAR(50) | Last name |
| full_name | VARCHAR(100) | Display name (e.g., "Kate Gallego") |
| display_name | VARCHAR(100) | Name with title (e.g., "Kate Gallego (Mayor)") |
| district | VARCHAR(10) | Current/last district (for quick reference) |
| photo_url | VARCHAR(500) | URL to official photo |
| bio | TEXT | Biography text |
| created_at | TIMESTAMP | Record creation timestamp |

**Notes:**
- One row per person, regardless of how many terms they served
- District changes are tracked in `council_terms`, not here
- `display_name` is denormalized for UI convenience

**Example Data:**
```
id | full_name          | district
1  | Kate Gallego       | NULL (Mayor)
2  | Jim Waring         | D2
3  | Sal DiCiccio       | D6
```

---

#### `council_terms`

**Purpose:** Tracks when each council member held each position. Handles promotions (Councilmember → Vice Mayor → Mayor) and district changes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| council_member_id | INTEGER | FK to council_members |
| district | VARCHAR(10) | "D1" through "D8", or NULL for Mayor |
| title | VARCHAR(50) | "Mayor", "Vice Mayor", "Councilmember" |
| start_date | DATE | When term began |
| end_date | DATE | When term ended (NULL if current) |

**Notes:**
- A member can have multiple terms (re-election, position change)
- Kate Gallego has two terms: D8 Councilmember (2014-2018), then Mayor (2019-present)
- Vice Mayor is typically the D1 representative but can change
- Used to determine which members were active for any given meeting date

**Example Data:**
```
id | council_member_id | district | title         | start_date | end_date
1  | 1                 | D8       | Councilmember | 2014-01-01 | 2018-05-29
2  | 1                 | NULL     | Mayor         | 2019-03-21 | NULL
3  | 7                 | D6       | Councilmember | 2009-01-01 | 2022-12-31
```

---

#### `matter_types`

**Purpose:** Categorizes agenda items by their legislative type.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(50) | Type name |
| description | TEXT | Explanation of this type |

**Common Values:**
- Ordinance - City laws
- Resolution - Formal decisions
- Minutes - Approval of previous meeting minutes
- Communication - Reports and announcements
- Report - Staff or committee reports
- Appointment - Board/commission appointments

---

#### `action_types`

**Purpose:** Standardizes the outcomes of votes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(50) | Action name |
| is_positive | BOOLEAN | TRUE for approval actions |

**Common Values:**
- approved (positive)
- adopted (positive)
- denied (negative)
- withdrawn (neutral)
- continued (neutral)
- referred (neutral)

---

### Core Data Tables

These tables store the actual meeting and voting data.

---

#### `meetings`

**Purpose:** One row per City Council meeting. Contains meeting-level metadata and document URLs.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| meeting_date | DATE | Date of meeting |
| meeting_type | VARCHAR(30) | "Formal", "Policy Session", "Special" |
| body_name | VARCHAR(100) | Full body name from API |
| year | INTEGER | Computed from meeting_date |
| quarter | INTEGER | Computed from meeting_date (1-4) |
| legistar_url | VARCHAR(500) | Link to Legistar meeting page |
| agenda_url | VARCHAR(500) | PDF agenda document |
| minutes_url | VARCHAR(500) | PDF minutes document |
| results_url | VARCHAR(500) | PDF voting results document |
| video_url | VARCHAR(500) | YouTube video URL |
| item_count | INTEGER | Number of agenda items (denormalized) |
| created_at | TIMESTAMP | Record creation |
| updated_at | TIMESTAMP | Last update |

**Notes:**
- Primary focus is "Formal" meetings where votes occur
- `year` and `quarter` are computed columns for efficient filtering
- Video URL comes from Phoenix.gov or YouTube RSS feed
- ~24 formal meetings per year (every 2 weeks, roughly)

**Key Queries This Supports:**
- List all meetings in a year
- Find meetings with video
- Get meeting documents

---

#### `agenda_items`

**Purpose:** Individual items on meeting agendas. This is where legislation details and vote outcomes are stored.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| meeting_id | INTEGER | FK to meetings |
| matter_type_id | INTEGER | FK to matter_types |
| file_number | VARCHAR(20) | Official file ID (e.g., "20-0123") |
| agenda_number | VARCHAR(20) | Position on agenda (e.g., "5", "CONSENT-3") |
| title | TEXT | Short title/description |
| description | TEXT | Full item summary |
| index_name | VARCHAR(50) | "District 1", "Citywide", etc. |
| is_consent | BOOLEAN | TRUE if consent agenda item |
| passed | BOOLEAN | TRUE if item passed |
| tally | VARCHAR(20) | Vote count (e.g., "7-0", "8-1") |
| action_type_id | INTEGER | FK to action_types |
| action_text | TEXT | Full motion text |
| mover_id | INTEGER | FK to council_members who made motion |
| seconder_id | INTEGER | FK to council_members who seconded |
| mover_name | VARCHAR(100) | Denormalized mover name |
| seconder_name | VARCHAR(100) | Denormalized seconder name |
| agenda_note | TEXT | Notes from agenda |
| minutes_note | TEXT | Notes from minutes |
| file_detail_url | VARCHAR(500) | Legistar detail page URL |
| sort_order | INTEGER | Order on agenda |
| created_at | TIMESTAMP | Record creation |

**Notes:**
- `file_number` is the primary identifier for legislation (e.g., "24-0456")
- `is_consent` = TRUE means item passed without individual roll call
- `tally` format is typically "Yes-No" or "Yes-No-Abstain"
- Mover/seconder names are denormalized for display efficiency
- ~50-150 items per meeting

**Key Queries This Supports:**
- Search items by keyword
- Filter by matter type
- Find items by district
- Track specific legislation across meetings

---

#### `votes`

**Purpose:** Individual council member votes on each agenda item. The most granular voting data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agenda_item_id | INTEGER | FK to agenda_items |
| council_member_id | INTEGER | FK to council_members |
| term_id | INTEGER | FK to council_terms (optional) |
| vote | VARCHAR(20) | "Yes", "No", "Absent", "Abstain", "Consent" |
| meeting_date | DATE | Denormalized for query efficiency |
| member_name | VARCHAR(100) | Denormalized member name |
| district | VARCHAR(10) | Denormalized district |
| created_at | TIMESTAMP | Record creation |

**Vote Values:**
- **Yes** - Voted in favor
- **No** - Voted against
- **Absent** - Not present for vote
- **Abstain** - Present but did not vote
- **Consent** - Passed on consent agenda (no individual roll call)
- **Voice Vote** - Passed by voice vote (no recorded roll call)

**Notes:**
- ~9 votes per agenda item (one per council member)
- Denormalized fields (meeting_date, member_name, district) improve query performance
- `term_id` links to the specific term active at vote time
- This is the largest table (~270K rows for 10 years)

**Key Queries This Supports:**
- Member voting record
- Who voted No on an item
- Attendance tracking
- Voting pattern analysis

---

### Analytics Tables

Pre-computed aggregations for dashboard performance.

---

#### `member_stats`

**Purpose:** Yearly voting statistics per council member. Pre-calculated to avoid expensive queries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| council_member_id | INTEGER | FK to council_members |
| year | INTEGER | Year of statistics |
| total_votes | INTEGER | Total voting opportunities |
| yes_votes | INTEGER | Count of Yes votes |
| no_votes | INTEGER | Count of No votes |
| absent_count | INTEGER | Count of absences |
| abstain_count | INTEGER | Count of abstentions |
| consent_votes | INTEGER | Count of consent items |
| attendance_rate | DECIMAL(5,2) | Percentage present |
| yes_rate | DECIMAL(5,2) | Percentage Yes (of non-consent) |
| updated_at | TIMESTAMP | Last calculation time |

**Notes:**
- Refreshed after each data import
- One row per member per year
- Enables instant dashboard loading

---

#### `controversial_votes`

**Purpose:** Flags agenda items with non-unanimous votes for quick filtering.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agenda_item_id | INTEGER | FK to agenda_items |
| yes_count | INTEGER | Number of Yes votes |
| no_count | INTEGER | Number of No votes |
| absent_count | INTEGER | Number absent |
| is_split_vote | BOOLEAN | TRUE if any No votes |
| is_close_vote | BOOLEAN | TRUE if margin ≤ 2 |

**Notes:**
- Only populated for items with recorded votes
- `is_split_vote` helps surface controversial items
- `is_close_vote` identifies narrow margins (e.g., 5-4)

---

## Database Views

Pre-defined queries for common access patterns.

---

#### `v_vote_details`

**Purpose:** Flattened view joining votes with all related context. Primary view for most queries.

**Joins:** votes → agenda_items → meetings → council_members → council_terms → matter_types → action_types

**Use Cases:**
- Member voting history
- Item vote breakdown
- Search results

---

#### `v_member_yearly_summary`

**Purpose:** Aggregated voting statistics by member and year.

**Output:** member_id, full_name, year, total_votes, yes_votes, no_votes, absences, attendance_pct

**Use Cases:**
- Member profile summary
- Year-over-year comparison

---

#### `v_split_votes`

**Purpose:** Lists all non-unanimous votes with who voted No.

**Output:** meeting_date, file_number, title, tally, passed, no_voters, absent_members

**Use Cases:**
- "Controversial Votes" page
- Finding dissents

---

## Indexes

Strategic indexes for query performance.

| Table | Index | Purpose |
|-------|-------|---------|
| meetings | meeting_date | Date range queries |
| meetings | year, quarter | Dashboard filters |
| agenda_items | meeting_id | Get items for meeting |
| agenda_items | file_number | Legislation lookup |
| agenda_items | is_consent | Filter consent items |
| votes | agenda_item_id | Get votes for item |
| votes | council_member_id | Member voting record |
| votes | meeting_date | Date range queries |
| votes | council_member_id, vote | Vote type analysis |

---

## Data Flow

```
CSV Files (per quarter/year)
        │
        ▼
┌─────────────────────┐
│  Import Script      │
│  (csv_to_db.py)     │
│                     │
│  1. Parse CSV       │
│  2. Match members   │
│  3. Insert meetings │
│  4. Insert items    │
│  5. Insert votes    │
│  6. Update stats    │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  SQLite Database    │
│  (~70 MB)           │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Website Backend    │
│  (API queries)      │
└─────────────────────┘
```

---

## CSV to Database Mapping

| CSV Column | Database Table | Database Column |
|------------|----------------|-----------------|
| MeetingDate | meetings | meeting_date |
| MeetingType | meetings | meeting_type |
| BodyName | meetings | body_name |
| EventInSiteURL | meetings | legistar_url |
| EventAgendaFile | meetings | agenda_url |
| EventMinutesFile | meetings | minutes_url |
| ResultsURL | meetings | results_url |
| EventItemVideo | meetings | video_url |
| MatterTypeName | agenda_items | matter_type_id (lookup) |
| AgendaItemNumber | agenda_items | agenda_number |
| AgendaItemTitle | agenda_items | title |
| AgendaItemDescription | agenda_items | description |
| EventItemConsent | agenda_items | is_consent |
| EventItemPassedFlag | agenda_items | passed |
| EventItemTally | agenda_items | tally |
| IndexName | agenda_items | index_name |
| ActionName | agenda_items | action_type_id (lookup) |
| ActionText | agenda_items | action_text |
| Mover | agenda_items | mover_name, mover_id (lookup) |
| Seconder | agenda_items | seconder_name, seconder_id (lookup) |
| FileNumber | agenda_items | file_number |
| FileDetailURL | agenda_items | file_detail_url |
| Kate Gallego (Mayor) | votes | vote (member lookup) |
| Jim Waring (D2) | votes | vote (member lookup) |
| ... (all member columns) | votes | vote (member lookup) |

---

## Council Member Roster by Era

### 2020 Roster
| District | Member |
|----------|--------|
| Mayor | Kate Gallego |
| D1 (Vice Mayor) | Thelda Williams |
| D2 | Jim Waring |
| D3 | Debra Stark |
| D4 | Laura Pastor |
| D5 | Betty Guardado |
| D6 | Sal DiCiccio |
| D7 | Michael Nowakowski |
| D8 | Carlos Garcia |

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

### 2025 Roster
| District | Member |
|----------|--------|
| D7 | Anna Hernandez (replaced Ansari) |

---

## Implementation Notes

### Database Choice: SQLite
- Simple deployment (single file)
- Sufficient for ~300K rows
- Easy backup (copy file)
- Can migrate to PostgreSQL if needed

### Import Strategy
- Process one CSV file at a time
- Upsert logic to handle re-imports
- Match council members by name fuzzy matching
- Validate data before commit

### Performance Targets
- Member profile load: < 200ms
- Search results: < 500ms
- Dashboard aggregations: < 100ms (from pre-computed stats)
