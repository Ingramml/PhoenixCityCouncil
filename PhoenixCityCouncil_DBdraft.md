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

## Website Query Requirements

Before designing the schema, we identified the key queries the website needs to support:

| Query Type | Description | Performance Target |
|------------|-------------|-------------------|
| Member Voting History | All votes by a member in a date range | < 200ms |
| Legislation Search | Full-text search on titles and descriptions | < 500ms |
| Split Vote Finder | List all non-unanimous votes | < 100ms |
| Member Comparison | Agreement rate between any two members | < 100ms |
| Attendance Stats | Absence rate per member per year | < 100ms |
| Meeting Browser | Paginated list with filters | < 200ms |
| Item Detail | Full item with all votes | < 100ms |

---

## Handling Council Member Roster Changes

A critical design challenge is that council membership changes over time:

**Position Changes:**
- Kate Gallego: D8 Councilmember (2014-2018) → Mayor (2019-present)
- Members can become Vice Mayor (typically D1 but not always)

**District Replacements (2020 vs 2024):**
| District | 2020 | 2024 |
|----------|------|------|
| D1 (Vice Mayor) | Thelda Williams | Ann O'Brien |
| D6 | Sal DiCiccio | Kevin Robinson |
| D7 | Michael Nowakowski | Yassamin Ansari |
| D8 | Carlos Garcia | Kesha Hodge Washington |

**Solution:** Separate `council_members` (person) from `council_terms` (position + dates)

```
council_members (one row per person)
    │
    └── council_terms (multiple rows per person)
            - Which district?
            - What title? (Mayor, Vice Mayor, Councilmember)
            - When? (start_date, end_date)
```

This allows accurate historical queries: "Who was the D6 representative when item 20-0456 was voted on?"

---

## Schema Options Comparison

Three design approaches with different trade-offs:

### Option A: Fully Normalized (3NF)

**Structure:** 12+ tables with full referential integrity

```
vote_types ─┐
            │
matter_types─┤
            │
action_types─┼─► agenda_items ◄── meetings
            │         │
districts ──┘         │
                      ▼
council_members ─► council_terms ─► votes
```

**Pros:**
- Maximum data integrity (FK constraints everywhere)
- No redundancy (each fact stored once)
- Easy to add new vote types, matter types, etc.
- Clean API design

**Cons:**
- Complex queries (5-7 JOINs for common operations)
- Slower performance without careful optimization
- Higher development time
- Complex CSV import (must resolve all FKs)

**Best For:** Enterprise systems with strict governance, long-term projects

---

### Option B: Hybrid/Pragmatic (RECOMMENDED)

**Structure:** 8-10 tables with strategic denormalization

```
                    ┌─────────────┐
                    │  meetings   │
                    └──────┬──────┘
                           │
┌─────────────┐     ┌──────▼──────┐     ┌─────────────────┐
│matter_types │────►│agenda_items │◄────│ council_members │
└─────────────┘     │ + denorm    │     │ + current_title │
                    └──────┬──────┘     └────────┬────────┘
                           │                     │
                    ┌──────▼──────┐     ┌────────▼────────┐
                    │   votes     │     │  council_terms  │
                    │ + denorm    │     └─────────────────┘
                    └─────────────┘

Pre-computed: member_stats, split_vote_summary, member_pairs
```

**Pros:**
- Fast common queries (1-2 JOINs instead of 5-7)
- Maintains core referential integrity
- Pre-computed analytics for instant dashboards
- Full-text search built-in
- Balanced complexity

**Cons:**
- Some data redundancy (~20% storage overhead)
- Must sync denormalized fields on updates
- Analytics tables need refresh triggers

**Best For:** Read-heavy websites, dashboard applications, SQLite deployments

---

### Option C: Flattened/Simple

**Structure:** 5-6 tables, votes stored as JSON

```
meetings ──► agenda_items (with votes_json column)
                  │
                  ▼
              votes (optional, derived from JSON)

council_roster (flat: year + district + name)
member_stats (pre-computed)
```

**Pros:**
- Simple schema (5-6 tables)
- Fast CSV import (direct mapping)
- Self-contained records
- Quick development

**Cons:**
- No referential integrity
- Name inconsistencies cause problems
- Hard to evolve schema
- Limited analytics capability

**Best For:** Prototypes, read-only archives, static site generators

---

### Comparison Matrix

| Factor | Option A | Option B | Option C |
|--------|----------|----------|----------|
| Tables | 12+ | 8-10 | 5-6 |
| JOINs per Query | 4-7 | 1-3 | 0-1 |
| Data Integrity | Excellent | Good | Poor |
| Query Performance | Requires tuning | Optimized | Fast for simple |
| Storage Size | Smallest | +20% | +30% |
| Development Time | Longest | Medium | Shortest |
| Schema Evolution | Easy | Medium | Difficult |

---

## Recommended Schema: Option B (Hybrid)

Based on the website requirements and SQLite deployment, Option B provides the best balance.

---

## Reference Tables

### `vote_types`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(20) | 'Yes', 'No', 'Absent', 'Abstain', 'Consent', 'Voice Vote' |
| result_category | VARCHAR(10) | 'affirmative', 'negative', 'neutral' |
| counts_as_present | BOOLEAN | TRUE except for 'Absent' |

### `matter_types`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(100) | 'Ordinance-S', 'Resolution', 'License - Liquor', etc. |
| category | VARCHAR(50) | 'Legislative', 'Licensing', 'Zoning', 'Administrative' |

### `action_types`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(100) | 'approved', 'adopted', 'denied', 'continued', 'referred' |
| is_positive | BOOLEAN | TRUE for approval actions |

---

## Entity Tables

### `council_members`

**Purpose:** Master list of all council members. One row per person.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| first_name | VARCHAR(50) | First name |
| last_name | VARCHAR(50) | Last name |
| full_name | VARCHAR(100) | Display name (e.g., "Kate Gallego") |
| current_district | VARCHAR(10) | Current/most recent district (denormalized) |
| current_title | VARCHAR(50) | Current title (denormalized) |
| display_name | VARCHAR(150) | Name with title (e.g., "Kate Gallego (Mayor)") |
| is_active | BOOLEAN | TRUE if currently serving |
| photo_url | VARCHAR(500) | URL to official photo |
| bio | TEXT | Biography text |
| created_at | TIMESTAMP | Record creation timestamp |

**Notes:**
- One row per person, regardless of terms served
- `current_*` fields denormalized for UI display
- Historical positions tracked in `council_terms`

---

### `council_terms`

**Purpose:** Tracks when each member held each position.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| council_member_id | INTEGER | FK to council_members |
| district | VARCHAR(10) | 'D1' through 'D8', or NULL for Mayor |
| title | VARCHAR(50) | 'Mayor', 'Vice Mayor', 'Councilmember' |
| start_date | DATE | When term began |
| end_date | DATE | When term ended (NULL if current) |

**Example Data:**
```
id | member_id | district | title         | start_date | end_date
1  | 1         | D8       | Councilmember | 2014-01-01 | 2018-05-29
2  | 1         | NULL     | Mayor         | 2019-03-21 | NULL
3  | 7         | D6       | Councilmember | 2009-01-01 | 2022-12-31
```

**Key Query - Who represented a district on a specific date:**
```sql
SELECT cm.full_name, ct.title
FROM council_terms ct
JOIN council_members cm ON ct.council_member_id = cm.id
WHERE ct.district = 'D6'
  AND ct.start_date <= '2020-03-04'
  AND (ct.end_date IS NULL OR ct.end_date >= '2020-03-04');
```

---

## Core Data Tables

### `meetings`

**Purpose:** One row per City Council meeting.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| meeting_date | DATE | Date of meeting |
| meeting_type | VARCHAR(30) | 'Formal', 'Policy Session', 'Special' |
| body_name | VARCHAR(200) | Full body name from API |
| year | INTEGER | Computed: YEAR(meeting_date) |
| quarter | INTEGER | Computed: 1-4 |
| legistar_url | VARCHAR(500) | Link to Legistar meeting page |
| agenda_url | VARCHAR(500) | PDF agenda document |
| minutes_url | VARCHAR(500) | PDF minutes document |
| results_url | VARCHAR(500) | PDF voting results document |
| video_url | VARCHAR(500) | YouTube video URL |
| item_count | INTEGER | Number of agenda items (denormalized) |
| created_at | TIMESTAMP | Record creation |
| updated_at | TIMESTAMP | Last update |

**Notes:**
- Primary focus is 'Formal' meetings where votes occur
- `year` and `quarter` computed for efficient filtering
- ~24 formal meetings per year

---

### `agenda_items`

**Purpose:** Individual items on meeting agendas.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| meeting_id | INTEGER | FK to meetings |
| matter_type_id | INTEGER | FK to matter_types |
| action_type_id | INTEGER | FK to action_types |
| matter_type_name | VARCHAR(100) | Denormalized type name |
| action_name | VARCHAR(100) | Denormalized action name |
| file_number | VARCHAR(20) | Official file ID (e.g., "24-0123") |
| agenda_number | VARCHAR(20) | Position on agenda |
| title | TEXT | Short title/description |
| description | TEXT | Full item summary |
| index_name | VARCHAR(50) | 'District 1', 'Citywide', etc. |
| is_consent | BOOLEAN | TRUE if consent agenda item |
| passed | BOOLEAN | TRUE if item passed |
| tally | VARCHAR(20) | Vote count (e.g., "7-0", "8-1") |
| action_text | TEXT | Full motion text |
| mover_id | INTEGER | FK to council_members |
| seconder_id | INTEGER | FK to council_members |
| mover_name | VARCHAR(100) | Denormalized mover name |
| seconder_name | VARCHAR(100) | Denormalized seconder name |
| agenda_note | TEXT | Notes from agenda |
| minutes_note | TEXT | Notes from minutes |
| file_detail_url | VARCHAR(500) | Legistar detail page URL |
| meeting_date | DATE | Denormalized for query efficiency |
| sort_order | INTEGER | Order on agenda |
| created_at | TIMESTAMP | Record creation |

**Notes:**
- `file_number` is the primary legislation identifier
- ~50-150 items per meeting
- Denormalized fields avoid JOINs for display

---

### `votes`

**Purpose:** Individual council member votes on each agenda item.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agenda_item_id | INTEGER | FK to agenda_items |
| council_member_id | INTEGER | FK to council_members |
| vote_type_id | INTEGER | FK to vote_types |
| vote | VARCHAR(20) | 'Yes', 'No', 'Absent', etc. (denormalized) |
| meeting_date | DATE | Denormalized for query efficiency |
| member_name | VARCHAR(100) | Denormalized member name |
| district | VARCHAR(10) | Member's district at time of vote |
| created_at | TIMESTAMP | Record creation |

**Unique Constraint:** (agenda_item_id, council_member_id)

**Vote Values:**
- **Yes** - Voted in favor
- **No** - Voted against
- **Absent** - Not present for vote
- **Abstain** - Present but did not vote
- **Consent** - Passed on consent agenda (no individual roll call)
- **Voice Vote** - Passed by voice vote (no recorded roll call)

**Notes:**
- ~9 votes per agenda item (one per council member)
- Largest table (~270K rows for 10 years)
- Denormalized fields enable fast filtering

---

## Analytics Tables (Pre-computed)

### `member_yearly_stats`

**Purpose:** Pre-calculated voting statistics per member per year.

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
- Enables instant dashboard loading

---

### `split_vote_summary`

**Purpose:** Pre-computed list of non-unanimous votes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agenda_item_id | INTEGER | FK to agenda_items |
| meeting_date | DATE | Meeting date |
| file_number | VARCHAR(20) | Legislation ID |
| title | TEXT | Item title |
| yes_count | INTEGER | Number of Yes votes |
| no_count | INTEGER | Number of No votes |
| absent_count | INTEGER | Number absent |
| margin | INTEGER | yes_count - no_count |
| no_voters | TEXT | Comma-separated names who voted No |
| is_close_vote | BOOLEAN | TRUE if margin <= 2 |

**Notes:**
- Only populated for items with recorded roll call votes
- Enables instant "controversial votes" page loading

---

### `member_pairs`

**Purpose:** Pre-computed agreement rates between member pairs.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| member1_id | INTEGER | FK to council_members |
| member2_id | INTEGER | FK to council_members |
| year | INTEGER | Year of comparison |
| shared_votes | INTEGER | Votes where both participated |
| agreements | INTEGER | Same vote cast |
| disagreements | INTEGER | Different votes cast |
| agreement_rate | DECIMAL(5,2) | Percentage agreement |
| updated_at | TIMESTAMP | Last calculation |

---

## Full-Text Search

```sql
-- SQLite FTS5 virtual table for legislation search
CREATE VIRTUAL TABLE agenda_items_fts USING fts5(
    title,
    description,
    file_number,
    content='agenda_items',
    content_rowid='id'
);
```

**Usage:**
```sql
SELECT ai.meeting_date, ai.file_number, ai.title, ai.tally
FROM agenda_items_fts fts
JOIN agenda_items ai ON fts.rowid = ai.id
WHERE agenda_items_fts MATCH 'zoning AND housing'
ORDER BY ai.meeting_date DESC;
```

---

## Database Views

### `v_vote_details`

**Purpose:** Flattened view joining votes with all related context.

**Joins:** votes → agenda_items → meetings → council_members

**Use Cases:**
- Member voting history
- Item vote breakdown
- Search results

---

### `v_member_yearly_summary`

**Purpose:** Aggregated voting statistics by member and year.

**Output:** member_id, full_name, year, total_votes, yes_votes, no_votes, absences, attendance_pct

**Use Cases:**
- Member profile summary
- Year-over-year comparison

---

### `v_split_votes`

**Purpose:** Lists all non-unanimous votes with who voted No.

**Output:** meeting_date, file_number, title, tally, passed, no_voters, absent_members

**Use Cases:**
- "Controversial Votes" page
- Finding dissents

---

## Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| meetings | meeting_date | Date range queries |
| meetings | year, quarter | Dashboard filters |
| agenda_items | meeting_id | Get items for meeting |
| agenda_items | file_number | Legislation lookup |
| agenda_items | meeting_date | Date filtering |
| agenda_items | index_name | District filtering |
| agenda_items | is_consent | Filter consent items |
| votes | agenda_item_id | Get votes for item |
| votes | council_member_id | Member voting record |
| votes | meeting_date | Date range queries |
| votes | vote | Vote type filtering |
| votes | (council_member_id, meeting_date) | Member history |
| votes | (council_member_id, vote) | Vote type analysis |
| member_yearly_stats | (council_member_id, year) | Stats lookup |
| split_vote_summary | meeting_date | Chronological listing |

---

## Sample Queries

### 1. Member Voting History (< 200ms)

```sql
SELECT
    v.meeting_date,
    ai.title,
    ai.file_number,
    v.vote,
    ai.tally,
    ai.passed
FROM votes v
JOIN agenda_items ai ON v.agenda_item_id = ai.id
WHERE v.member_name = 'Laura Pastor'
  AND v.meeting_date >= '2024-01-01'
ORDER BY v.meeting_date DESC, ai.sort_order;
```

### 2. Find Split Votes (< 100ms, uses pre-computed)

```sql
SELECT
    meeting_date,
    file_number,
    title,
    yes_count || '-' || no_count as tally,
    no_voters
FROM split_vote_summary
WHERE no_count > 0
ORDER BY meeting_date DESC
LIMIT 50;
```

### 3. Member Comparison (< 100ms, uses pre-computed)

```sql
SELECT
    cm1.full_name as member1,
    cm2.full_name as member2,
    mp.agreement_rate,
    mp.shared_votes,
    mp.agreements
FROM member_pairs mp
JOIN council_members cm1 ON mp.member1_id = cm1.id
JOIN council_members cm2 ON mp.member2_id = cm2.id
WHERE mp.year = 2024
ORDER BY mp.agreement_rate ASC;
```

### 4. Attendance Rate

```sql
SELECT
    member_name,
    COUNT(*) as total_opportunities,
    SUM(CASE WHEN vote != 'Absent' THEN 1 ELSE 0 END) as present_count,
    ROUND(100.0 * SUM(CASE WHEN vote != 'Absent' THEN 1 ELSE 0 END) / COUNT(*), 1) as attendance_pct
FROM votes
WHERE meeting_date >= '2024-01-01'
GROUP BY council_member_id, member_name
ORDER BY attendance_pct DESC;
```

### 5. Items by District

```sql
SELECT
    ai.meeting_date,
    ai.file_number,
    ai.title,
    ai.tally,
    ai.passed
FROM agenda_items ai
WHERE ai.index_name = 'District 5'
  AND ai.meeting_date >= '2024-01-01'
ORDER BY ai.meeting_date DESC;
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
| MatterTypeName | agenda_items | matter_type_id (lookup), matter_type_name |
| AgendaItemNumber | agenda_items | agenda_number |
| AgendaItemTitle | agenda_items | title |
| AgendaItemDescription | agenda_items | description |
| EventItemConsent | agenda_items | is_consent |
| EventItemPassedFlag | agenda_items | passed |
| EventItemTally | agenda_items | tally |
| IndexName | agenda_items | index_name |
| ActionName | agenda_items | action_type_id (lookup), action_name |
| ActionText | agenda_items | action_text |
| Mover | agenda_items | mover_name, mover_id (lookup) |
| Seconder | agenda_items | seconder_name, seconder_id (lookup) |
| FileNumber | agenda_items | file_number |
| FileDetailURL | agenda_items | file_detail_url |
| Kate Gallego (Mayor) | votes | vote (create row per member) |
| Jim Waring (D2) | votes | vote (create row per member) |
| ... (all member columns) | votes | vote (create row per member) |

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

## Data Flow

```
CSV Files (per quarter/year)
        │
        ▼
┌─────────────────────────┐
│  Import Script          │
│  (csv_to_db.py)         │
│                         │
│  1. Parse CSV           │
│  2. Upsert meetings     │
│  3. Upsert agenda_items │
│  4. Upsert votes        │
│  5. Match member names  │
│  6. Refresh analytics   │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│  SQLite Database        │
│  (~70-100 MB)           │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│  Website Backend        │
│  (API queries)          │
└─────────────────────────┘
```

---

## Implementation Notes

### Database Choice: SQLite
- Simple deployment (single file)
- Sufficient for ~300K rows
- Easy backup (copy file)
- FTS5 built-in for search
- Can migrate to PostgreSQL if needed

### Import Strategy
- Process one CSV file at a time
- Upsert logic to handle re-imports
- Match council members by fuzzy name matching
- Validate data before commit
- Refresh analytics tables after import

### Performance Targets
- Member profile load: < 200ms
- Search results: < 500ms
- Dashboard aggregations: < 100ms (from pre-computed stats)
- Item detail with votes: < 100ms

### Analytics Refresh
After each import, run:
1. Rebuild `member_yearly_stats` for affected years
2. Rebuild `split_vote_summary` for new items
3. Rebuild `member_pairs` for affected years
4. Rebuild FTS index for new items
