# Database Schema Options for City Council Voting Data

**Created**: 2026-01-18
**Purpose**: Compare 3 database schema approaches for civic transparency voting data
**Based On**: CityVotes PostgreSQL schema, Shared Data Schema (API contract), Phoenix Data Collection workflow

---

## Table of Contents

1. [Research Context](#research-context)
2. [Option A: Multi-City Flexible](#option-a-multi-city-flexible-schema)
3. [Option B: Hybrid (Recommended)](#option-b-hybrid-schema-recommended)
4. [Option C: Fully Separated](#option-c-fully-separated-maximum-normalization)
5. [Comparison Matrix](#comparison-matrix)
6. [Recommendations](#recommendations)

---

## Research Context

### City Differences (Santa Ana vs Phoenix)

| Aspect | Santa Ana | Phoenix |
|--------|-----------|---------|
| Council Size | 7 members | 9 members (8 districts + Mayor) |
| Districts | Wards 1-6 + Mayor | Districts 1-8 + Mayor |
| Vice Mayor | Rotating/appointed | District 1 (currently) |
| Meeting Types | regular, special | Formal, Work Session, Special |
| Data Source | Legistar API | Legistar API |
| Vote Types | Aye/No/Abstain/Absent/Recused | Yes/No/Absent/Consent/Voice Vote |

### Data Volume Comparison

| Metric | Santa Ana (1 year) | Phoenix (10 years) |
|--------|-------------------|-------------------|
| Meetings | ~22 | ~480 |
| Agenda Items | ~437 | ~30,000 |
| Individual Votes | ~3,059 | ~270,000 |
| Council Members (all time) | ~10 | ~25 |

### Source Documents

1. **DATABASE_SCHEMA_REPORT.md** (CityVotes) - Production PostgreSQL schema for Santa Ana
2. **SHARED_DATA_SCHEMA.md** - TypeScript/Pydantic API contract for frontend
3. **DATA_COLLECTION_WORKFLOW.md** - Phoenix CSV structure from Legistar

---

## Option A: Multi-City Flexible Schema

### Overview

Configurable schema that adapts to different city council structures. Uses a `cities` configuration table to define city-specific settings like vote types, meeting types, and council size.

### Entity Relationship Diagram

```
┌─────────────┐
│   cities    │ ◄── Configuration per city
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────────────┐     ┌──────────────────────┐
│  council_members    │────►│ council_member_terms │
└──────────┬──────────┘     └──────────────────────┘
           │                           │
           │ 1:N                       │ (optional FK)
           ▼                           ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  meetings   │────►│ agenda_items│────►│    votes     │
└─────────────┘ 1:N └─────────────┘ 1:N └──────┬───────┘
                                              │ 1:N
                                              ▼
                                       ┌──────────────┐
                                       │ member_votes │
                                       └──────────────┘

┌─────────────┐     ┌──────────────┐
│  sessions   │────►│ session_data │
└─────────────┘ 1:N └──────────────┘
```

### Tables (11)

#### Configuration Table

```sql
-- Cities table stores per-city configuration
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    city_key VARCHAR(50) UNIQUE NOT NULL,    -- 'phoenix', 'santa_ana'
    name VARCHAR(100) NOT NULL,               -- 'Phoenix'
    display_name VARCHAR(150),                -- 'Phoenix, AZ'
    state VARCHAR(2) DEFAULT 'AZ',
    total_seats INTEGER NOT NULL,             -- 9 for Phoenix, 7 for Santa Ana
    has_districts BOOLEAN DEFAULT TRUE,
    vote_choices JSON,                        -- ["Yes","No","Absent"] or ["Aye","Nay","Abstain","Recused"]
    meeting_types JSON,                       -- ["Formal","Work Session"] or ["regular","special"]
    primary_color VARCHAR(7),                 -- '#1f4e79' for dashboard theming
    secondary_color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example data
INSERT INTO cities (city_key, name, display_name, total_seats, vote_choices, meeting_types, primary_color)
VALUES
    ('phoenix', 'Phoenix', 'Phoenix, AZ', 9,
     '["Yes","No","Absent","Consent","Voice Vote"]',
     '["Formal","Work Session","Special"]',
     '#660000'),
    ('santa_ana', 'Santa Ana', 'Santa Ana, CA', 7,
     '["Aye","Nay","Abstain","Absent","Recused"]',
     '["regular","special","joint_housing","emergency"]',
     '#1f4e79');
```

#### Core Tables

```sql
-- Council members with city association
CREATE TABLE council_members (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    member_key VARCHAR(50) NOT NULL,          -- URL-safe ID: 'kate-gallego'
    full_name VARCHAR(150) NOT NULL,
    short_name VARCHAR(50),                   -- For CSV matching: 'Gallego'
    title VARCHAR(50),                        -- Current title
    is_active BOOLEAN DEFAULT TRUE,
    photo_url TEXT,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (city_id, member_key)
);

-- Term history with flexible district handling
CREATE TABLE council_member_terms (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES council_members(id),
    position VARCHAR(50) NOT NULL,            -- 'Mayor', 'Vice Mayor', 'Council Member'
    district INTEGER,                         -- NULL for Mayor, 1-8 for Phoenix, 1-6 for Santa Ana
    term_start DATE NOT NULL,
    term_end DATE,                            -- NULL if currently serving
    election_date DATE,
    appointment_type VARCHAR(20) DEFAULT 'elected',  -- 'elected', 'appointed', 'interim'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (appointment_type IN ('elected', 'appointed', 'interim'))
);

-- Meetings with city association
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,        -- Validated against city's meeting_types
    meeting_year INTEGER GENERATED ALWAYS AS (strftime('%Y', meeting_date)) STORED,
    meeting_month INTEGER GENERATED ALWAYS AS (strftime('%m', meeting_date)) STORED,
    start_time TIME,
    end_time TIME,
    location VARCHAR(255),
    agenda_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (city_id, meeting_date, meeting_type)
);

-- Agenda items
CREATE TABLE agenda_items (
    id INTEGER PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    item_number VARCHAR(20),                  -- '1', '38', '27.A'
    title TEXT NOT NULL,
    description TEXT,
    section VARCHAR(50),                      -- 'CONSENT', 'BUSINESS', 'PUBLIC_HEARING'
    matter_type VARCHAR(100),                 -- 'Ordinance', 'Resolution', 'License - Liquor'
    department VARCHAR(150),
    recommended_action TEXT,
    fiscal_impact TEXT,
    is_public_hearing BOOLEAN DEFAULT FALSE,
    is_consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (meeting_id, item_number)
);

-- Vote records (one per agenda item)
CREATE TABLE votes (
    id INTEGER PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    outcome VARCHAR(20) NOT NULL,             -- 'PASS', 'FAIL', 'TIE', 'CONTINUED', 'REMOVED'
    ayes INTEGER DEFAULT 0,
    noes INTEGER DEFAULT 0,
    abstain INTEGER DEFAULT 0,
    absent INTEGER DEFAULT 0,
    recusal INTEGER DEFAULT 0,
    tally VARCHAR(20),                        -- '7-2', '8-1' (denormalized for display)
    motion_by INTEGER REFERENCES council_members(id),
    seconded_by INTEGER REFERENCES council_members(id),
    action_name VARCHAR(100),                 -- 'approved', 'adopted', 'referred'
    action_text TEXT,
    vote_number INTEGER DEFAULT 1,            -- For items with multiple votes
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual member votes
CREATE TABLE member_votes (
    id INTEGER PRIMARY KEY,
    vote_id INTEGER NOT NULL REFERENCES votes(id),
    member_id INTEGER NOT NULL REFERENCES council_members(id),
    term_id INTEGER REFERENCES council_member_terms(id),  -- Which term they were serving
    vote_choice VARCHAR(20) NOT NULL,         -- Validated against city's vote_choices
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (vote_id, member_id)
);
```

#### Web App Tables

```sql
-- User sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                      -- UUID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);

-- Uploaded data per session
CREATE TABLE session_data (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    city_id INTEGER NOT NULL REFERENCES cities(id),
    original_filename VARCHAR(255),
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON,                            -- Original uploaded JSON
    processed_data JSON,                      -- Pre-calculated summaries
    vote_count INTEGER,
    UNIQUE (session_id, city_id)
);
```

### Key Indexes

```sql
CREATE INDEX idx_council_members_city ON council_members(city_id);
CREATE INDEX idx_council_members_active ON council_members(city_id, is_active);
CREATE INDEX idx_meetings_city_date ON meetings(city_id, meeting_date DESC);
CREATE INDEX idx_meetings_year ON meetings(city_id, meeting_year);
CREATE INDEX idx_agenda_items_meeting ON agenda_items(meeting_id);
CREATE INDEX idx_votes_agenda_item ON votes(agenda_item_id);
CREATE INDEX idx_member_votes_vote ON member_votes(vote_id);
CREATE INDEX idx_member_votes_member ON member_votes(member_id);
```

### Sample Queries

```sql
-- Get all Phoenix council members currently serving
SELECT cm.full_name, ct.position, ct.district
FROM council_members cm
JOIN council_member_terms ct ON cm.id = ct.member_id
JOIN cities c ON cm.city_id = c.id
WHERE c.city_key = 'phoenix'
  AND ct.term_end IS NULL;

-- Get voting history for a member (any city)
SELECT m.meeting_date, ai.title, mv.vote_choice
FROM member_votes mv
JOIN votes v ON mv.vote_id = v.id
JOIN agenda_items ai ON v.agenda_item_id = ai.id
JOIN meetings m ON ai.meeting_id = m.id
WHERE mv.member_id = 1
ORDER BY m.meeting_date DESC;
```

### Pros

- **One codebase serves multiple cities** - Deploy once, configure per city
- **API/website adapts** based on `city_key` in URL (`/api/phoenix/votes`)
- **Vote types configurable** per city via JSON
- **Dashboard theming** via `primary_color`/`secondary_color`
- **Matches CityVotes production design** - Proven at scale

### Cons

- More complex queries (must filter by `city_id`)
- Configuration overhead for new cities
- Some NULL fields (district for at-large members)
- Requires PostgreSQL for best performance (JSON, generated columns)

### Best For

- **CityVotes-style platform** - Multiple cities, one deployment
- SaaS civic transparency tools
- Regional government comparisons
- Organizations tracking multiple jurisdictions

---

## Option B: Hybrid Schema (RECOMMENDED)

### Overview

Strategic denormalization for a single city (Phoenix) with pre-computed analytics tables. Optimized for read-heavy public transparency website with fast dashboard queries.

### Entity Relationship Diagram

```
┌─────────────────────┐     ┌──────────────────┐
│  council_members    │────►│  council_terms   │
└──────────┬──────────┘     └──────────────────┘
           │
           │ referenced by
           ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  meetings   │────►│ agenda_items│────►│    votes     │
└─────────────┘ 1:N └─────────────┘ 1:N └──────────────┘
                                        (DENORMALIZED:
                                         member_name,
                                         district)

┌──────────────┐     ┌──────────────┐
│ matter_types │     │ action_types │
└──────────────┘     └──────────────┘
      (lookup)             (lookup)

PRE-COMPUTED ANALYTICS:
┌─────────────────────┐  ┌────────────────────┐  ┌──────────────┐
│ member_yearly_stats │  │ split_vote_summary │  │ member_pairs │
└─────────────────────┘  └────────────────────┘  └──────────────┘
```

### Tables (10)

#### Core Tables

```sql
-- Council members (person identity)
CREATE TABLE council_members (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    current_district INTEGER,                 -- NULL for Mayor
    current_title VARCHAR(50),                -- 'Mayor', 'Vice Mayor', 'Council Member'
    is_active BOOLEAN DEFAULT TRUE,
    photo_url TEXT,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Term history for roster changes
CREATE TABLE council_terms (
    id INTEGER PRIMARY KEY,
    council_member_id INTEGER NOT NULL REFERENCES council_members(id),
    district INTEGER,                         -- NULL for Mayor
    title VARCHAR(50) NOT NULL,               -- 'Mayor', 'Vice Mayor', 'D1', 'D2', etc.
    start_date DATE NOT NULL,
    end_date DATE,                            -- NULL if currently serving
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meetings
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY,
    meeting_date DATE NOT NULL UNIQUE,
    meeting_type VARCHAR(50) DEFAULT 'Formal',
    year INTEGER,
    quarter INTEGER,
    body_name VARCHAR(150) DEFAULT 'City Council Formal Meeting',
    video_url TEXT,
    agenda_url TEXT,
    minutes_url TEXT,
    results_url TEXT,
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agenda items with denormalized matter_type
CREATE TABLE agenda_items (
    id INTEGER PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    file_number VARCHAR(20),                  -- '24-0123'
    item_number VARCHAR(20),                  -- '1', '38'
    title TEXT NOT NULL,
    description TEXT,
    matter_type VARCHAR(100),                 -- DENORMALIZED: 'Ordinance', 'Resolution' (string, not FK)
    index_name VARCHAR(50),                   -- 'District 1', 'Citywide'
    is_consent BOOLEAN DEFAULT FALSE,
    passed BOOLEAN,                           -- TRUE, FALSE, NULL (no vote)
    tally VARCHAR(20),                        -- '7-2' (denormalized)
    action VARCHAR(100),                      -- 'approved', 'adopted'
    action_text TEXT,
    mover_id INTEGER REFERENCES council_members(id),
    seconder_id INTEGER REFERENCES council_members(id),
    detail_url TEXT,
    meeting_date DATE,                        -- DENORMALIZED for fast filtering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (meeting_id, item_number)
);

-- Individual votes with DENORMALIZED member info
CREATE TABLE votes (
    id INTEGER PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    council_member_id INTEGER NOT NULL REFERENCES council_members(id),

    -- DENORMALIZED: Snapshot of member info at time of vote
    member_name VARCHAR(100) NOT NULL,        -- 'Kate Gallego'
    member_title VARCHAR(50),                 -- 'Mayor'
    district INTEGER,                         -- NULL for Mayor, 1-8 for districts

    vote VARCHAR(20) NOT NULL,                -- 'Yes', 'No', 'Absent', 'Consent', 'Voice Vote'
    meeting_date DATE,                        -- DENORMALIZED for fast filtering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (agenda_item_id, council_member_id)
);
```

#### Lookup Tables

```sql
-- Matter types for filtering/categorization
CREATE TABLE matter_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),                     -- 'Legislative', 'Administrative', 'Ceremonial'
    description TEXT
);

-- Action types for filtering
CREATE TABLE action_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_positive BOOLEAN,                      -- TRUE for 'approved', FALSE for 'denied'
    description TEXT
);
```

#### Pre-computed Analytics Tables

```sql
-- Member statistics by year (refresh after imports)
CREATE TABLE member_yearly_stats (
    id INTEGER PRIMARY KEY,
    council_member_id INTEGER NOT NULL REFERENCES council_members(id),
    year INTEGER NOT NULL,
    total_votes INTEGER DEFAULT 0,
    yes_count INTEGER DEFAULT 0,
    no_count INTEGER DEFAULT 0,
    absent_count INTEGER DEFAULT 0,
    consent_count INTEGER DEFAULT 0,
    attendance_rate REAL,                     -- (total - absent) / total
    yes_rate REAL,                            -- yes / (yes + no)
    participation_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (council_member_id, year)
);

-- Split vote summary (non-unanimous votes)
CREATE TABLE split_vote_summary (
    id INTEGER PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    meeting_date DATE,
    yes_count INTEGER,
    no_count INTEGER,
    margin INTEGER,                           -- yes_count - no_count
    no_voters JSON,                           -- ["Jim Waring", "Debra Stark"]
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Member pair agreement rates
CREATE TABLE member_pairs (
    id INTEGER PRIMARY KEY,
    member1_id INTEGER NOT NULL REFERENCES council_members(id),
    member2_id INTEGER NOT NULL REFERENCES council_members(id),
    year INTEGER,
    total_shared_votes INTEGER,
    agreements INTEGER,
    disagreements INTEGER,
    agreement_rate REAL,                      -- agreements / total_shared_votes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (member1_id, member2_id, year)
);
```

### Key Indexes

```sql
CREATE INDEX idx_meetings_date ON meetings(meeting_date DESC);
CREATE INDEX idx_meetings_year ON meetings(year);
CREATE INDEX idx_agenda_items_meeting ON agenda_items(meeting_id);
CREATE INDEX idx_agenda_items_date ON agenda_items(meeting_date);
CREATE INDEX idx_votes_agenda ON votes(agenda_item_id);
CREATE INDEX idx_votes_member ON votes(council_member_id);
CREATE INDEX idx_votes_member_date ON votes(council_member_id, meeting_date);
CREATE INDEX idx_votes_vote ON votes(vote);
CREATE INDEX idx_member_stats_member_year ON member_yearly_stats(council_member_id, year);
CREATE INDEX idx_split_votes_date ON split_vote_summary(meeting_date DESC);
```

### Full-Text Search (SQLite FTS5)

```sql
-- Virtual table for agenda item search
CREATE VIRTUAL TABLE agenda_items_fts USING fts5(
    title,
    description,
    file_number,
    content='agenda_items',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER agenda_items_ai AFTER INSERT ON agenda_items BEGIN
    INSERT INTO agenda_items_fts(rowid, title, description, file_number)
    VALUES (new.id, new.title, new.description, new.file_number);
END;

-- Search example
SELECT ai.meeting_date, ai.file_number, ai.title, ai.tally
FROM agenda_items_fts fts
JOIN agenda_items ai ON fts.rowid = ai.id
WHERE agenda_items_fts MATCH 'zoning AND housing'
ORDER BY ai.meeting_date DESC;
```

### Analytics Refresh Script

```sql
-- Refresh member_yearly_stats after data import
INSERT OR REPLACE INTO member_yearly_stats
    (council_member_id, year, total_votes, yes_count, no_count, absent_count,
     consent_count, attendance_rate, yes_rate)
SELECT
    council_member_id,
    strftime('%Y', meeting_date) AS year,
    COUNT(*) AS total_votes,
    SUM(CASE WHEN vote = 'Yes' THEN 1 ELSE 0 END) AS yes_count,
    SUM(CASE WHEN vote = 'No' THEN 1 ELSE 0 END) AS no_count,
    SUM(CASE WHEN vote = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
    SUM(CASE WHEN vote = 'Consent' THEN 1 ELSE 0 END) AS consent_count,
    1.0 - (1.0 * SUM(CASE WHEN vote = 'Absent' THEN 1 ELSE 0 END) / COUNT(*)) AS attendance_rate,
    CASE WHEN SUM(CASE WHEN vote IN ('Yes','No') THEN 1 ELSE 0 END) > 0
         THEN 1.0 * SUM(CASE WHEN vote = 'Yes' THEN 1 ELSE 0 END) /
              SUM(CASE WHEN vote IN ('Yes','No') THEN 1 ELSE 0 END)
         ELSE NULL END AS yes_rate
FROM votes
GROUP BY council_member_id, strftime('%Y', meeting_date);
```

### Sample Queries

```sql
-- Member voting history (fast: 1 JOIN)
SELECT ai.meeting_date, ai.title, v.vote
FROM votes v
JOIN agenda_items ai ON v.agenda_item_id = ai.id
WHERE v.council_member_id = 1
ORDER BY ai.meeting_date DESC
LIMIT 100;

-- Split votes in 2024 (uses pre-computed table)
SELECT ai.title, svs.yes_count, svs.no_count, svs.no_voters
FROM split_vote_summary svs
JOIN agenda_items ai ON svs.agenda_item_id = ai.id
WHERE svs.year = 2024
ORDER BY svs.margin ASC;

-- Member agreement rates (uses pre-computed table)
SELECT cm1.full_name AS member1, cm2.full_name AS member2, mp.agreement_rate
FROM member_pairs mp
JOIN council_members cm1 ON mp.member1_id = cm1.id
JOIN council_members cm2 ON mp.member2_id = cm2.id
WHERE mp.year = 2024
ORDER BY mp.agreement_rate DESC;
```

### Pros

- **Fast queries** (1-3 JOINs for most operations)
- **Pre-computed analytics** for sub-100ms dashboard
- **Roster changes captured** in vote snapshot (denormalized member_name/district)
- **SQLite compatible** - No PostgreSQL required, simple deployment
- **Simple to understand** and maintain
- **FTS5 full-text search** built-in

### Cons

- Single city only (Phoenix-specific)
- Data redundancy in votes table (member_name repeated)
- Must refresh analytics tables after imports
- Less flexible for schema evolution

### Best For

- **Phoenix City Council project** - Single city focus
- Read-heavy transparency websites
- SQLite deployment (Vercel, Cloudflare, etc.)
- Small team / solo developer

---

## Option C: Fully Separated (Maximum Normalization)

### Overview

Every entity in its own table with full referential integrity via foreign keys. No denormalization, no data redundancy. Follows strict Third Normal Form (3NF).

### Entity Relationship Diagram

```
LOOKUP TABLES:
┌────────────┐  ┌──────────────┐  ┌──────────────┐
│ vote_types │  │ matter_types │  │ action_types │
└────────────┘  └──────────────┘  └──────────────┘
       │                │                │
       │     ┌──────────────────┐        │
       │     │  meeting_types   │        │
       │     └──────────────────┘        │
       │                │                │
       │     ┌──────────────────┐        │
       │     │     bodies       │        │
       │     └──────────────────┘        │
       │                │                │
       │     ┌──────────────────┐        │
       │     │     indexes      │        │
       │     └──────────────────┘        │
       │                                 │
CORE TABLES:                             │
┌─────────────────────┐     ┌──────────────────────┐
│  council_members    │────►│ council_member_terms │
└──────────┬──────────┘     └──────────┬───────────┘
           │                           │
           │    FK                  FK │
           ▼                           ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  meetings   │────►│ agenda_items│────►│ vote_records │
│  (FK body,  │ 1:N │  (FK matter,│ 1:N │  (FK action) │
│   FK type)  │     │   FK index) │     └──────┬───────┘
└─────────────┘     └─────────────┘            │ 1:N
                                               ▼
                                        ┌──────────────┐
                                        │ member_votes │
                                        │ (FK member,  │
                                        │  FK term,    │
                                        │  FK vote_type)
                                        └──────────────┘
```

### Tables (14)

#### Lookup Tables

```sql
-- Vote type reference
CREATE TABLE vote_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,         -- 'Yes', 'No', 'Absent', 'Abstain', 'Recused'
    counts_as_present BOOLEAN NOT NULL,       -- Yes/No count as present, Absent doesn't
    result_category VARCHAR(20),              -- 'support', 'oppose', 'non_vote'
    display_order INTEGER
);

INSERT INTO vote_types (name, counts_as_present, result_category, display_order) VALUES
    ('Yes', TRUE, 'support', 1),
    ('No', TRUE, 'oppose', 2),
    ('Abstain', TRUE, 'non_vote', 3),
    ('Absent', FALSE, 'non_vote', 4),
    ('Recused', FALSE, 'non_vote', 5),
    ('Consent', TRUE, 'support', 6),
    ('Voice Vote', TRUE, 'support', 7);

-- Matter type reference
CREATE TABLE matter_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),                     -- 'Legislative', 'Administrative', 'Ceremonial'
    description TEXT
);

-- Action type reference
CREATE TABLE action_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_positive BOOLEAN,                      -- TRUE for 'approved', FALSE for 'denied'
    description TEXT
);

-- Meeting type reference
CREATE TABLE meeting_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,         -- 'Formal', 'Work Session', 'Special'
    description TEXT
);

-- Body reference (City Council, Housing Authority, etc.)
CREATE TABLE bodies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    short_name VARCHAR(50),
    description TEXT
);

-- Index reference (District 1-8, Citywide)
CREATE TABLE indexes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,         -- 'District 1', 'Citywide'
    sort_order INTEGER
);
```

#### Core Tables

```sql
-- Council members (person identity only)
CREATE TABLE council_members (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    suffix VARCHAR(20),                       -- 'Jr.', 'III'
    email VARCHAR(255),
    phone VARCHAR(20),
    photo_url TEXT,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Term history (tracks every position change)
CREATE TABLE council_member_terms (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES council_members(id),
    position VARCHAR(50) NOT NULL,            -- 'Mayor', 'Vice Mayor', 'Council Member'
    district INTEGER,                         -- NULL for at-large positions
    term_start DATE NOT NULL,
    term_end DATE,                            -- NULL if currently serving
    election_date DATE,
    appointment_type VARCHAR(20) DEFAULT 'elected',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (appointment_type IN ('elected', 'appointed', 'interim')),
    CHECK (term_end IS NULL OR term_end > term_start)
);

-- Meetings with FK to body and type
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY,
    body_id INTEGER NOT NULL REFERENCES bodies(id),
    meeting_type_id INTEGER NOT NULL REFERENCES meeting_types(id),
    meeting_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(255),
    agenda_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (body_id, meeting_date, meeting_type_id)
);

-- Agenda items with FK to matter_type and index
CREATE TABLE agenda_items (
    id INTEGER PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    matter_type_id INTEGER REFERENCES matter_types(id),
    index_id INTEGER REFERENCES indexes(id),
    file_number VARCHAR(20),
    item_number VARCHAR(20),
    title TEXT NOT NULL,
    description TEXT,
    section VARCHAR(50),
    department VARCHAR(150),
    recommended_action TEXT,
    fiscal_impact TEXT,
    is_public_hearing BOOLEAN DEFAULT FALSE,
    is_consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (meeting_id, item_number)
);

-- Vote records (one per agenda item, or per distinct vote)
CREATE TABLE vote_records (
    id INTEGER PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    action_type_id INTEGER REFERENCES action_types(id),
    outcome VARCHAR(20) NOT NULL,             -- 'PASS', 'FAIL', 'TIE', 'CONTINUED'
    ayes INTEGER DEFAULT 0,
    noes INTEGER DEFAULT 0,
    abstain INTEGER DEFAULT 0,
    absent INTEGER DEFAULT 0,
    recusal INTEGER DEFAULT 0,
    motion_by_id INTEGER REFERENCES council_members(id),
    seconded_by_id INTEGER REFERENCES council_members(id),
    action_text TEXT,
    vote_number INTEGER DEFAULT 1,            -- For items with multiple votes
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (outcome IN ('PASS', 'FAIL', 'TIE', 'CONTINUED', 'REMOVED'))
);

-- Individual member votes with full FK relationships
CREATE TABLE member_votes (
    id INTEGER PRIMARY KEY,
    vote_record_id INTEGER NOT NULL REFERENCES vote_records(id),
    council_member_id INTEGER NOT NULL REFERENCES council_members(id),
    council_term_id INTEGER REFERENCES council_member_terms(id),  -- Which term they were serving
    vote_type_id INTEGER NOT NULL REFERENCES vote_types(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (vote_record_id, council_member_id)
);
```

#### Web App Tables

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);

CREATE TABLE session_data (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    original_filename VARCHAR(255),
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON,
    processed_data JSON,
    vote_count INTEGER
);
```

### Key Indexes

```sql
CREATE INDEX idx_terms_member ON council_member_terms(member_id);
CREATE INDEX idx_terms_dates ON council_member_terms(term_start, term_end);
CREATE INDEX idx_terms_active ON council_member_terms(member_id) WHERE term_end IS NULL;

CREATE INDEX idx_meetings_date ON meetings(meeting_date DESC);
CREATE INDEX idx_meetings_body ON meetings(body_id);

CREATE INDEX idx_agenda_meeting ON agenda_items(meeting_id);
CREATE INDEX idx_agenda_matter ON agenda_items(matter_type_id);
CREATE INDEX idx_agenda_index ON agenda_items(index_id);

CREATE INDEX idx_votes_agenda ON vote_records(agenda_item_id);
CREATE INDEX idx_votes_outcome ON vote_records(outcome);

CREATE INDEX idx_member_votes_record ON member_votes(vote_record_id);
CREATE INDEX idx_member_votes_member ON member_votes(council_member_id);
CREATE INDEX idx_member_votes_term ON member_votes(council_term_id);
CREATE INDEX idx_member_votes_type ON member_votes(vote_type_id);
```

### Sample Queries

```sql
-- Member voting history (requires 5+ JOINs)
SELECT
    cm.first_name || ' ' || cm.last_name AS member_name,
    vt.name AS vote,
    ai.title AS item,
    m.meeting_date,
    mt.name AS meeting_type
FROM member_votes mv
JOIN vote_records vr ON mv.vote_record_id = vr.id
JOIN agenda_items ai ON vr.agenda_item_id = ai.id
JOIN meetings m ON ai.meeting_id = m.id
JOIN meeting_types mt ON m.meeting_type_id = mt.id
JOIN council_members cm ON mv.council_member_id = cm.id
JOIN vote_types vt ON mv.vote_type_id = vt.id
WHERE cm.id = 1
ORDER BY m.meeting_date DESC;

-- Get active members for a specific date
SELECT
    cm.first_name || ' ' || cm.last_name AS name,
    ct.position,
    ct.district
FROM council_member_terms ct
JOIN council_members cm ON ct.member_id = cm.id
WHERE ct.term_start <= '2024-01-15'
  AND (ct.term_end IS NULL OR ct.term_end >= '2024-01-15');

-- Vote breakdown by type
SELECT
    vt.name AS vote_type,
    vt.result_category,
    COUNT(*) AS count
FROM member_votes mv
JOIN vote_types vt ON mv.vote_type_id = vt.id
GROUP BY vt.id, vt.name, vt.result_category
ORDER BY count DESC;
```

### Materialized Views (PostgreSQL)

```sql
-- Pre-computed meeting summary
CREATE MATERIALIZED VIEW mv_meeting_summary AS
SELECT
    m.id AS meeting_id,
    m.meeting_date,
    COUNT(DISTINCT ai.id) AS total_items,
    COUNT(DISTINCT vr.id) AS total_votes,
    SUM(CASE WHEN vr.outcome = 'PASS' THEN 1 ELSE 0 END) AS passed,
    SUM(CASE WHEN vr.outcome = 'FAIL' THEN 1 ELSE 0 END) AS failed,
    ROUND(100.0 * SUM(CASE WHEN vr.outcome = 'PASS' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(DISTINCT vr.id), 0), 1) AS pass_rate
FROM meetings m
LEFT JOIN agenda_items ai ON m.id = ai.meeting_id
LEFT JOIN vote_records vr ON ai.id = vr.agenda_item_id
GROUP BY m.id, m.meeting_date;

-- Refresh command
REFRESH MATERIALIZED VIEW mv_meeting_summary;
```

### Pros

- **Full referential integrity** - No orphan records, database enforces consistency
- **No data redundancy** - Update member name in one place
- **Flexible** - Easy to add new vote types, meeting types, bodies
- **Audit trail** - Foreign keys preserve complete history
- **Schema evolution** - Add tables/columns without breaking existing queries
- **Standardized** - Matches academic database design principles

### Cons

- **Complex queries** (5-7 JOINs for common operations)
- **Slower performance** without materialized views
- **More development effort** (~3x vs hybrid)
- **Requires PostgreSQL** for materialized views and advanced indexing
- **Import complexity** - Must resolve all FKs during import

### Best For

- Enterprise systems with strict data governance
- Systems requiring complete audit trails
- Multi-user admin systems with concurrent writes
- Projects expected to grow significantly in scope
- Government/compliance environments

---

## Comparison Matrix

| Criteria | Option A (Multi-City) | Option B (Hybrid) | Option C (Separated) |
|----------|----------------------|-------------------|---------------------|
| **Tables** | 11 | 10 | 14 |
| **Cities Supported** | Multiple | Single (Phoenix) | Single |
| **Referential Integrity** | High | Partial | Full |
| **Query Complexity** | 3-5 JOINs | 1-3 JOINs | 5-7 JOINs |
| **Dashboard Performance** | Good | Excellent | Slow without views |
| **Roster Change Tracking** | Excellent | Good | Excellent |
| **Import Complexity** | Medium | Low | High |
| **Schema Evolution** | Excellent | Good | Excellent |
| **Development Effort** | 2x | 1x (baseline) | 3x |
| **Best Database** | PostgreSQL | SQLite | PostgreSQL |
| **Code Reuse** | High (multi-city) | Low (Phoenix only) | Medium |
| **Full-Text Search** | PostgreSQL GIN | SQLite FTS5 | PostgreSQL GIN |
| **Analytics** | Materialized Views | Pre-computed Tables | Materialized Views |

---

## Recommendations

### For Phoenix City Council Project: **Option B (Hybrid)**

**Rationale:**
- Single city focus (no need for multi-city complexity)
- Read-heavy transparency website (rare writes after import)
- SQLite deployment (Vercel, Cloudflare, simple hosting)
- Pre-computed analytics for fast dashboard (<100ms)
- Solo developer / small team

### For Future CityVotes Expansion: **Option A (Multi-City)**

**When to choose:**
- Planning to add more cities (Santa Ana, Tucson, etc.)
- Building a SaaS civic transparency platform
- Need per-city configuration (vote types, colors)
- Have PostgreSQL infrastructure

### For Enterprise/Government Deployment: **Option C (Separated)**

**When to choose:**
- Strict audit/compliance requirements
- Multiple admin users with concurrent access
- Data governance policies require full integrity
- Schema expected to evolve significantly
- Have dedicated database admin

---

## Implementation Notes

### CSV Column Mapping (Phoenix)

| CSV Column | Option A | Option B | Option C |
|------------|----------|----------|----------|
| MeetingDate | meetings.meeting_date | meetings.meeting_date | meetings.meeting_date |
| Kate Gallego (Mayor) | member_votes.vote_choice | votes.vote | member_votes → vote_types |
| EventItemTally | votes.tally | agenda_items.tally | vote_records (computed) |
| MatterTypeName | agenda_items.matter_type | agenda_items.matter_type | agenda_items → matter_types |
| ActionName | votes.action_name | agenda_items.action | vote_records → action_types |

### Roster Change Example (Kate Gallego: D8 → Mayor)

**Option B (Hybrid):**
```sql
-- council_terms table
INSERT INTO council_terms (council_member_id, district, title, start_date, end_date)
VALUES
    (1, 8, 'D8', '2014-01-01', '2018-05-29'),
    (1, NULL, 'Mayor', '2019-03-21', NULL);

-- Each vote stores snapshot
INSERT INTO votes (agenda_item_id, council_member_id, member_name, member_title, district, vote)
VALUES (123, 1, 'Kate Gallego', 'Mayor', NULL, 'Yes');  -- 2024 vote as Mayor
```

---

*Document created: 2026-01-18*
*Based on: DATABASE_SCHEMA_REPORT.md (CityVotes), SHARED_DATA_SCHEMA.md, DATA_COLLECTION_WORKFLOW.md*
