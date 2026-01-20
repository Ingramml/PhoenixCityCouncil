# CityVotes Database Progression Strategy

A comprehensive guide for scaling the CityVotes database from 1 city to 50+ cities on PostgreSQL/BigQuery.

---

## Executive Summary

| Attribute | Value |
|-----------|-------|
| **Target Platform** | PostgreSQL (transactional) + BigQuery (analytics at scale) |
| **Goal** | Multi-city civic transparency platform |
| **Recommended Schema** | Option A (Multi-City Flexible) from DATABASE_SCHEMA_OPTIONS.md |
| **Total Phases** | 4 scaling phases |

---

## Quick Reference: Scaling Phases

| Phase | Cities | Data Volume | Key Infrastructure |
|-------|--------|-------------|-------------------|
| **Phase 1: Foundation** | 1-5 | <500K rows | Standard PostgreSQL, Materialized views |
| **Phase 2: Growth** | 5-20 | 500K-2M rows | Table partitioning, Connection pooling, Read replicas |
| **Phase 3: Scale** | 20-50 | 2M-10M rows | PostgreSQL + BigQuery hybrid |
| **Phase 4: Enterprise** | 50+ | 10M+ rows | Regional sharding, Redis caching |

---

## PHASE 1: Foundation (1-5 Cities)

**Infrastructure:** Standard PostgreSQL deployment, Materialized views for analytics
**Data Volume:** <500K member_votes rows
**Tables:** 11 core tables + 1 materialized view

### Phase 1 Tables

---

#### 1. cities

**Purpose:** Store configuration for each city including visual theming and voting rules

```sql
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    city_key VARCHAR(50) UNIQUE NOT NULL,    -- 'phoenix', 'santa_ana'
    name VARCHAR(100) NOT NULL,               -- 'Phoenix, AZ'
    state VARCHAR(2) NOT NULL,                -- 'AZ'
    total_seats INTEGER NOT NULL,             -- 9
    vote_choices JSONB DEFAULT '["Yes","No","Absent","Abstain"]',
    meeting_types JSONB DEFAULT '["Formal Meeting","Policy Session"]',
    legistar_client VARCHAR(50),              -- API client name
    primary_color VARCHAR(7),                 -- '#003366'
    secondary_color VARCHAR(7),               -- '#FFD700'
    timezone VARCHAR(50) DEFAULT 'America/Phoenix',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_key | VARCHAR(50) | URL-friendly unique identifier |
| name | VARCHAR(100) | Full display name with state |
| state | VARCHAR(2) | Two-letter state code |
| total_seats | INTEGER | Number of council seats |
| vote_choices | JSONB | Allowed vote options for this city |
| meeting_types | JSONB | Types of meetings this city holds |
| legistar_client | VARCHAR(50) | Legistar API client name |
| primary_color | VARCHAR(7) | Hex color for theming |
| secondary_color | VARCHAR(7) | Secondary hex color |
| timezone | VARCHAR(50) | City timezone |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 2. council_members

**Purpose:** Store all council members across all cities

```sql
CREATE TABLE council_members (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    full_name VARCHAR(100) NOT NULL,
    photo_url TEXT,
    bio TEXT,
    party_affiliation VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(city_id, full_name)
);
CREATE INDEX idx_council_members_city ON council_members(city_id);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_id | INTEGER | Foreign key to cities |
| full_name | VARCHAR(100) | Member's full name |
| photo_url | TEXT | URL to headshot photo |
| bio | TEXT | Biography text |
| party_affiliation | VARCHAR(50) | Political party (if applicable) |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 3. council_member_terms

**Purpose:** Track position changes over time (Mayor, Vice Mayor, district changes)

```sql
CREATE TABLE council_member_terms (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES council_members(id),
    position VARCHAR(50) NOT NULL,            -- 'Mayor', 'Council Member'
    district INTEGER,                          -- NULL for Mayor
    term_start DATE NOT NULL,
    term_end DATE,                             -- NULL if currently serving
    appointment_type VARCHAR(20) DEFAULT 'elected',
    is_current BOOLEAN GENERATED ALWAYS AS (term_end IS NULL) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_terms_member ON council_member_terms(member_id);
CREATE INDEX idx_terms_current ON council_member_terms(is_current) WHERE is_current = true;
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| member_id | INTEGER | Foreign key to council_members |
| position | VARCHAR(50) | Position title (Mayor, Vice Mayor, etc.) |
| district | INTEGER | District number (NULL for at-large positions) |
| term_start | DATE | When this term began |
| term_end | DATE | When term ended (NULL if current) |
| appointment_type | VARCHAR(20) | 'elected', 'appointed', 'interim' |
| is_current | BOOLEAN | Generated column: true if term_end is NULL |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 4. meetings

**Purpose:** Store all council meetings with video/document links

```sql
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,        -- 'Formal Meeting'
    legistar_event_id INTEGER,
    legistar_url TEXT,
    agenda_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    meeting_year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM meeting_date)) STORED,
    meeting_month INTEGER GENERATED ALWAYS AS (EXTRACT(MONTH FROM meeting_date)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(city_id, meeting_date, meeting_type)
);
CREATE INDEX idx_meetings_city_date ON meetings(city_id, meeting_date DESC);
CREATE INDEX idx_meetings_year ON meetings(city_id, meeting_year);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_id | INTEGER | Foreign key to cities |
| meeting_date | DATE | Date of the meeting |
| meeting_type | VARCHAR(50) | Type of meeting |
| legistar_event_id | INTEGER | Legistar event identifier |
| legistar_url | TEXT | URL to Legistar meeting page |
| agenda_url | TEXT | URL to agenda PDF |
| minutes_url | TEXT | URL to minutes PDF |
| video_url | TEXT | URL to video recording |
| meeting_year | INTEGER | Generated: extracted year |
| meeting_month | INTEGER | Generated: extracted month |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 5. agenda_items

**Purpose:** Store every item on every agenda with full text descriptions

```sql
CREATE TABLE agenda_items (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    item_number VARCHAR(20),                  -- '1', '2a', 'CONSENT-1'
    title TEXT NOT NULL,
    description TEXT,
    matter_type VARCHAR(50),                  -- 'Ordinance', 'Resolution'
    file_number VARCHAR(50),                  -- 'ORD-2024-001'
    is_consent BOOLEAN DEFAULT FALSE,
    legistar_item_id INTEGER,
    detail_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_agenda_items_meeting ON agenda_items(meeting_id);
CREATE INDEX idx_agenda_items_consent ON agenda_items(meeting_id, is_consent);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| meeting_id | INTEGER | Foreign key to meetings |
| item_number | VARCHAR(20) | Agenda item number |
| title | TEXT | Item title |
| description | TEXT | Full description/summary |
| matter_type | VARCHAR(50) | Type (Ordinance, Resolution, etc.) |
| file_number | VARCHAR(50) | Official file number |
| is_consent | BOOLEAN | True if on consent agenda |
| legistar_item_id | INTEGER | Legistar item identifier |
| detail_url | TEXT | URL to item detail page |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 6. votes

**Purpose:** Store aggregate vote results for each agenda item

```sql
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    action_name VARCHAR(100),                 -- 'Approved', 'Denied'
    action_text TEXT,                         -- Full motion text
    passed BOOLEAN,
    tally VARCHAR(20),                        -- '7-0', '5-2-1'
    mover_id INTEGER REFERENCES council_members(id),
    seconder_id INTEGER REFERENCES council_members(id),
    vote_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agenda_item_id)
);
CREATE INDEX idx_votes_agenda ON votes(agenda_item_id);
CREATE INDEX idx_votes_passed ON votes(passed);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| agenda_item_id | INTEGER | Foreign key to agenda_items |
| action_name | VARCHAR(100) | Result (Approved, Denied, etc.) |
| action_text | TEXT | Full motion text |
| passed | BOOLEAN | True if item passed |
| tally | VARCHAR(20) | Vote count (e.g., '7-0') |
| mover_id | INTEGER | Member who made motion |
| seconder_id | INTEGER | Member who seconded |
| vote_date | TIMESTAMPTZ | When vote occurred |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 7. member_votes

**Purpose:** Store individual council member votes (Yes/No/Absent per person per item)

```sql
CREATE TABLE member_votes (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER NOT NULL REFERENCES votes(id),
    member_id INTEGER NOT NULL REFERENCES council_members(id),
    vote_choice VARCHAR(20) NOT NULL,         -- 'Yes', 'No', 'Absent', 'Abstain'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(vote_id, member_id)
);
CREATE INDEX idx_member_votes_vote ON member_votes(vote_id);
CREATE INDEX idx_member_votes_member ON member_votes(member_id);
CREATE INDEX idx_member_votes_choice ON member_votes(vote_choice);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| vote_id | INTEGER | Foreign key to votes |
| member_id | INTEGER | Foreign key to council_members |
| vote_choice | VARCHAR(20) | How member voted |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 8. documents

**Purpose:** Store attachments and supporting documents for agenda items

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    document_type VARCHAR(50),                -- 'Staff Report', 'Attachment'
    title VARCHAR(255),
    url TEXT NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_documents_agenda ON documents(agenda_item_id);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| agenda_item_id | INTEGER | Foreign key to agenda_items |
| document_type | VARCHAR(50) | Type of document |
| title | VARCHAR(255) | Document title |
| url | TEXT | URL to download document |
| file_size | INTEGER | File size in bytes |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### 9. categories

**Purpose:** Classify agenda items for filtering and analytics

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),    -- NULL = global category
    name VARCHAR(100) NOT NULL,               -- 'Transportation', 'Housing'
    parent_id INTEGER REFERENCES categories(id),
    display_order INTEGER DEFAULT 0,
    UNIQUE(city_id, name)
);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_id | INTEGER | NULL for global, or city-specific |
| name | VARCHAR(100) | Category name |
| parent_id | INTEGER | Self-reference for hierarchy |
| display_order | INTEGER | Sort order |

---

#### 10. agenda_item_categories

**Purpose:** Many-to-many relationship between items and categories

```sql
CREATE TABLE agenda_item_categories (
    agenda_item_id INTEGER NOT NULL REFERENCES agenda_items(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    PRIMARY KEY (agenda_item_id, category_id)
);
```

| Field | Type | Description |
|-------|------|-------------|
| agenda_item_id | INTEGER | Foreign key to agenda_items |
| category_id | INTEGER | Foreign key to categories |

---

#### 11. data_sync_log

**Purpose:** Track data collection runs for debugging and monitoring

```sql
CREATE TABLE data_sync_log (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    sync_type VARCHAR(50) NOT NULL,           -- 'api', 'scrape', 'manual'
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running',     -- 'running', 'success', 'failed'
    records_processed INTEGER DEFAULT 0,
    error_message TEXT
);
CREATE INDEX idx_sync_log_city ON data_sync_log(city_id, started_at DESC);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_id | INTEGER | Foreign key to cities |
| sync_type | VARCHAR(50) | Type of sync operation |
| started_at | TIMESTAMPTZ | When sync started |
| completed_at | TIMESTAMPTZ | When sync finished |
| status | VARCHAR(20) | Current status |
| records_processed | INTEGER | Number of records processed |
| error_message | TEXT | Error details if failed |

---

### Phase 1 Materialized Views

#### mv_member_voting_summary

**Purpose:** Pre-computed voting statistics for dashboards

```sql
CREATE MATERIALIZED VIEW mv_member_voting_summary AS
SELECT
    cm.id AS member_id,
    cm.city_id,
    cm.full_name,
    cmt.position,
    cmt.district,
    COUNT(mv.id) AS total_votes,
    COUNT(*) FILTER (WHERE mv.vote_choice = 'Yes') AS yes_votes,
    COUNT(*) FILTER (WHERE mv.vote_choice = 'No') AS no_votes,
    COUNT(*) FILTER (WHERE mv.vote_choice = 'Absent') AS absent_count,
    EXTRACT(YEAR FROM m.meeting_date) AS vote_year
FROM council_members cm
JOIN council_member_terms cmt ON cm.id = cmt.member_id AND cmt.is_current
JOIN member_votes mv ON cm.id = mv.member_id
JOIN votes v ON mv.vote_id = v.id
JOIN agenda_items ai ON v.agenda_item_id = ai.id
JOIN meetings m ON ai.meeting_id = m.id
GROUP BY cm.id, cm.city_id, cm.full_name, cmt.position, cmt.district, EXTRACT(YEAR FROM m.meeting_date);

CREATE UNIQUE INDEX idx_mv_member_summary ON mv_member_voting_summary(member_id, vote_year);
```

**Refresh Command:**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_member_voting_summary;
```

---

## PHASE 2: Growth (5-20 Cities)

**Infrastructure:** Table partitioning by city_id, Connection pooling (PgBouncer), Read replicas
**Data Volume:** 500K-2M member_votes rows
**Trigger:** 5+ cities OR 1M member_votes rows

### Phase 2 Schema Changes

#### Partitioned member_votes (replaces Phase 1 table)

**Purpose:** Partition by city for query performance

```sql
-- Drop old table and recreate as partitioned
CREATE TABLE member_votes (
    id SERIAL,
    city_id INTEGER NOT NULL,                 -- Added for partitioning
    vote_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    vote_choice VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (city_id, id)
) PARTITION BY HASH (city_id);

-- Create partitions (one per city or group)
CREATE TABLE member_votes_p0 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE member_votes_p1 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE member_votes_p2 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE member_votes_p3 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE member_votes_p4 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE member_votes_p5 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE member_votes_p6 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE member_votes_p7 PARTITION OF member_votes FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Indexes on partitioned table
CREATE INDEX idx_member_votes_vote ON member_votes(vote_id);
CREATE INDEX idx_member_votes_member ON member_votes(member_id);
CREATE INDEX idx_member_votes_choice ON member_votes(vote_choice);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| city_id | INTEGER | **NEW** - Added for partitioning |
| vote_id | INTEGER | Foreign key to votes |
| member_id | INTEGER | Foreign key to council_members |
| vote_choice | VARCHAR(20) | How member voted |
| created_at | TIMESTAMPTZ | Record creation timestamp |

---

#### Partitioned meetings

**Purpose:** Partition meetings for time-based queries

```sql
CREATE TABLE meetings (
    id SERIAL,
    city_id INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,
    legistar_event_id INTEGER,
    legistar_url TEXT,
    agenda_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    meeting_year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM meeting_date)) STORED,
    meeting_month INTEGER GENERATED ALWAYS AS (EXTRACT(MONTH FROM meeting_date)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (meeting_date, id),
    UNIQUE(city_id, meeting_date, meeting_type)
) PARTITION BY RANGE (meeting_date);

-- Create yearly partitions
CREATE TABLE meetings_2023 PARTITION OF meetings
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE meetings_2024 PARTITION OF meetings
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE meetings_2025 PARTITION OF meetings
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE meetings_2026 PARTITION OF meetings
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

---

### Phase 2 New Tables

#### 12. api_cache

**Purpose:** Cache API responses to reduce load and improve response times

```sql
CREATE TABLE api_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    response_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_api_cache_expires ON api_cache(expires_at);
CREATE INDEX idx_api_cache_city ON api_cache(city_id);
```

| Field | Type | Description |
|-------|------|-------------|
| cache_key | VARCHAR(255) | Unique cache key (primary key) |
| city_id | INTEGER | City this cache belongs to |
| response_data | JSONB | Cached JSON response |
| created_at | TIMESTAMPTZ | When cached |
| expires_at | TIMESTAMPTZ | When cache expires |

**Cache Cleanup Job:**
```sql
DELETE FROM api_cache WHERE expires_at < NOW();
```

---

#### 13. query_metrics

**Purpose:** Monitor slow queries for optimization decisions

```sql
CREATE TABLE query_metrics (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64),
    query_pattern TEXT,
    avg_duration_ms NUMERIC(10,2),
    call_count INTEGER DEFAULT 1,
    last_called TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_query_metrics_hash ON query_metrics(query_hash);
CREATE INDEX idx_query_metrics_duration ON query_metrics(avg_duration_ms DESC);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| query_hash | VARCHAR(64) | Hash of normalized query |
| query_pattern | TEXT | Parameterized query pattern |
| avg_duration_ms | NUMERIC(10,2) | Average execution time |
| call_count | INTEGER | Number of times executed |
| last_called | TIMESTAMPTZ | Most recent execution |

---

### Phase 2 Infrastructure

#### PgBouncer Configuration

```ini
[databases]
cityvotes = host=localhost port=5432 dbname=cityvotes

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 50
min_pool_size = 10
reserve_pool_size = 5
```

#### Read Replica Setup

```
Primary (Write): pg-primary.cityvotes.com:5432
Replica (Read):  pg-replica.cityvotes.com:5432

Dashboard/Analytics queries -> Replica
API writes/real-time reads -> Primary
```

---

### Phase 2 Migration: Handling Schema Differences

When migrating from Phase 1 to Phase 2, the key challenge is converting existing non-partitioned tables to partitioned tables while handling structural differences (e.g., adding `city_id` to `member_votes`).

#### Step-by-Step Migration for member_votes

**Problem:** Phase 1 `member_votes` lacks `city_id`, but Phase 2 needs it for partitioning.

**Solution:** Derive `city_id` through the join path: `member_votes` → `votes` → `agenda_items` → `meetings` → `city_id`

```sql
-- Step 1: Create the new partitioned table
CREATE TABLE member_votes_new (
    id SERIAL,
    city_id INTEGER NOT NULL,
    vote_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    vote_choice VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (city_id, id)
) PARTITION BY HASH (city_id);

-- Create partitions
CREATE TABLE member_votes_new_p0 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE member_votes_new_p1 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE member_votes_new_p2 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE member_votes_new_p3 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE member_votes_new_p4 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE member_votes_new_p5 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE member_votes_new_p6 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE member_votes_new_p7 PARTITION OF member_votes_new FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Step 2: Migrate data with city_id derived from join path
INSERT INTO member_votes_new (id, city_id, vote_id, member_id, vote_choice, created_at)
SELECT
    mv.id,
    m.city_id,          -- Derived through joins
    mv.vote_id,
    mv.member_id,
    mv.vote_choice,
    mv.created_at
FROM member_votes mv
JOIN votes v ON mv.vote_id = v.id
JOIN agenda_items ai ON v.agenda_item_id = ai.id
JOIN meetings m ON ai.meeting_id = m.id;

-- Step 3: Create indexes on new table
CREATE INDEX idx_member_votes_new_vote ON member_votes_new(vote_id);
CREATE INDEX idx_member_votes_new_member ON member_votes_new(member_id);
CREATE INDEX idx_member_votes_new_choice ON member_votes_new(vote_choice);

-- Step 4: Swap tables (during maintenance window)
BEGIN;
ALTER TABLE member_votes RENAME TO member_votes_old;
ALTER TABLE member_votes_new RENAME TO member_votes;
COMMIT;

-- Step 5: Drop old table after verification
-- DROP TABLE member_votes_old;
```

#### Step-by-Step Migration for meetings

**Problem:** Phase 1 `meetings` uses simple PRIMARY KEY, Phase 2 partitions by `meeting_date`.

**Solution:** Recreate with composite primary key including partition column.

```sql
-- Step 1: Create the new partitioned table
CREATE TABLE meetings_new (
    id SERIAL,
    city_id INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,
    legistar_event_id INTEGER,
    legistar_url TEXT,
    agenda_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    meeting_year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM meeting_date)) STORED,
    meeting_month INTEGER GENERATED ALWAYS AS (EXTRACT(MONTH FROM meeting_date)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (meeting_date, id),
    UNIQUE(city_id, meeting_date, meeting_type)
) PARTITION BY RANGE (meeting_date);

-- Create yearly partitions (adjust years as needed)
CREATE TABLE meetings_new_2020 PARTITION OF meetings_new
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE meetings_new_2021 PARTITION OF meetings_new
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE meetings_new_2022 PARTITION OF meetings_new
    FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE meetings_new_2023 PARTITION OF meetings_new
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE meetings_new_2024 PARTITION OF meetings_new
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE meetings_new_2025 PARTITION OF meetings_new
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE meetings_new_2026 PARTITION OF meetings_new
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Step 2: Migrate existing data
INSERT INTO meetings_new (id, city_id, meeting_date, meeting_type, legistar_event_id,
                          legistar_url, agenda_url, minutes_url, video_url, created_at)
SELECT id, city_id, meeting_date, meeting_type, legistar_event_id,
       legistar_url, agenda_url, minutes_url, video_url, created_at
FROM meetings;

-- Step 3: Create indexes
CREATE INDEX idx_meetings_new_city_date ON meetings_new(city_id, meeting_date DESC);
CREATE INDEX idx_meetings_new_year ON meetings_new(city_id, meeting_year);

-- Step 4: Swap tables
BEGIN;
ALTER TABLE meetings RENAME TO meetings_old;
ALTER TABLE meetings_new RENAME TO meetings;
COMMIT;

-- Step 5: Update foreign keys in agenda_items
-- (agenda_items.meeting_id references meetings.id)
-- Foreign key should still work since id values are preserved
```

#### Handling agenda_items Differences

**Key insight:** `agenda_items` references `meetings` via `meeting_id`. Since we preserve the `meetings.id` values during migration, the foreign key relationship remains intact.

**No structural changes required** for `agenda_items` in Phase 2. The table remains as-is because:
1. It doesn't need partitioning at this scale
2. Foreign key to `meetings` still works (we preserved IDs)
3. Queries filter by `meeting_id`, which now routes to the correct partition

#### Migration Summary Table

| Table | Phase 1 → Phase 2 Changes | Migration Complexity |
|-------|--------------------------|---------------------|
| `member_votes` | Add `city_id`, partition by HASH | Medium - requires join to derive city_id |
| `meetings` | Change PK, partition by RANGE(date) | Medium - preserves IDs, adjusts PK |
| `agenda_items` | No changes | None - FK still works |
| `votes` | No changes | None - FK still works |
| `council_members` | No changes | None |
| `cities` | No changes | None |

#### Zero-Downtime Migration Strategy

For production environments, use this approach:

```sql
-- 1. Create new tables alongside existing
-- 2. Set up triggers to dual-write to both tables
CREATE OR REPLACE FUNCTION dual_write_member_votes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO member_votes_new (city_id, vote_id, member_id, vote_choice, created_at)
    SELECT m.city_id, NEW.vote_id, NEW.member_id, NEW.vote_choice, NEW.created_at
    FROM votes v
    JOIN agenda_items ai ON v.agenda_item_id = ai.id
    JOIN meetings m ON ai.meeting_id = m.id
    WHERE v.id = NEW.vote_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER member_votes_dual_write
AFTER INSERT ON member_votes
FOR EACH ROW EXECUTE FUNCTION dual_write_member_votes();

-- 3. Backfill historical data
-- 4. Verify counts match
-- 5. Switch application to new tables
-- 6. Remove triggers and drop old tables
```

---

## PHASE 3: Scale (20-50 Cities)

**Infrastructure:** PostgreSQL + BigQuery hybrid, Real-time in PG / Analytics in BQ
**Data Volume:** 2M-10M member_votes rows
**Trigger:** 20+ cities OR 5M member_votes rows

### BigQuery Tables (Analytics Warehouse)

#### bq_fact_votes

**Purpose:** Denormalized fact table for fast analytics queries

```sql
-- BigQuery SQL
CREATE TABLE cityvotes.bq_fact_votes (
    vote_id INT64 NOT NULL,
    city_key STRING NOT NULL,
    city_name STRING,
    meeting_date DATE NOT NULL,
    meeting_year INT64,
    meeting_month INT64,
    meeting_quarter INT64,
    meeting_type STRING,
    agenda_item_id INT64,
    item_number STRING,
    item_title STRING,
    matter_type STRING,
    is_consent BOOL,
    action_name STRING,
    passed BOOL,
    tally STRING,
    member_id INT64,
    member_name STRING,
    position STRING,
    district INT64,
    vote_choice STRING,
    mover_name STRING,
    seconder_name STRING,
    _synced_at TIMESTAMP
)
PARTITION BY DATE(meeting_date)
CLUSTER BY city_key, member_id;
```

| Field | Type | Description |
|-------|------|-------------|
| vote_id | INT64 | PostgreSQL vote.id |
| city_key | STRING | City identifier |
| city_name | STRING | City display name |
| meeting_date | DATE | Date of meeting |
| meeting_year | INT64 | Year extracted |
| meeting_month | INT64 | Month extracted |
| meeting_quarter | INT64 | Quarter (1-4) |
| meeting_type | STRING | Type of meeting |
| agenda_item_id | INT64 | PostgreSQL agenda_item.id |
| item_number | STRING | Agenda item number |
| item_title | STRING | Item title |
| matter_type | STRING | Type of matter |
| is_consent | BOOL | On consent agenda |
| action_name | STRING | Vote result |
| passed | BOOL | Did item pass |
| tally | STRING | Vote tally |
| member_id | INT64 | PostgreSQL council_member.id |
| member_name | STRING | Member full name |
| position | STRING | Member position |
| district | INT64 | Member district |
| vote_choice | STRING | How member voted |
| mover_name | STRING | Who made motion |
| seconder_name | STRING | Who seconded |
| _synced_at | TIMESTAMP | When synced to BigQuery |

---

#### bq_dim_members

**Purpose:** Slowly changing dimension for council member history

```sql
CREATE TABLE cityvotes.bq_dim_members (
    member_id INT64 NOT NULL,
    city_key STRING NOT NULL,
    full_name STRING NOT NULL,
    position STRING,
    district INT64,
    term_start DATE,
    term_end DATE,
    is_current BOOL,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    _synced_at TIMESTAMP
);
```

| Field | Type | Description |
|-------|------|-------------|
| member_id | INT64 | PostgreSQL council_member.id |
| city_key | STRING | City identifier |
| full_name | STRING | Member name |
| position | STRING | Position title |
| district | INT64 | District number |
| term_start | DATE | Term start date |
| term_end | DATE | Term end date |
| is_current | BOOL | Currently serving |
| valid_from | TIMESTAMP | SCD2: when record became valid |
| valid_to | TIMESTAMP | SCD2: when record ended |
| _synced_at | TIMESTAMP | When synced |

---

#### bq_aggregate_daily

**Purpose:** Pre-aggregated daily statistics for dashboards

```sql
CREATE TABLE cityvotes.bq_aggregate_daily (
    date DATE NOT NULL,
    city_key STRING NOT NULL,
    total_meetings INT64,
    total_items INT64,
    total_votes INT64,
    consent_items INT64,
    regular_items INT64,
    items_passed INT64,
    items_failed INT64,
    unanimous_votes INT64,
    _computed_at TIMESTAMP
)
PARTITION BY date;
```

| Field | Type | Description |
|-------|------|-------------|
| date | DATE | Aggregation date |
| city_key | STRING | City identifier |
| total_meetings | INT64 | Meetings on this date |
| total_items | INT64 | Agenda items |
| total_votes | INT64 | Votes taken |
| consent_items | INT64 | Consent agenda items |
| regular_items | INT64 | Regular agenda items |
| items_passed | INT64 | Items that passed |
| items_failed | INT64 | Items that failed |
| unanimous_votes | INT64 | Unanimous votes |
| _computed_at | TIMESTAMP | When aggregation ran |

---

### Phase 3 PostgreSQL Additions

#### 14. bq_sync_state

**Purpose:** Track BigQuery synchronization status

```sql
CREATE TABLE bq_sync_state (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    city_id INTEGER REFERENCES cities(id),
    last_sync_at TIMESTAMPTZ,
    last_sync_id BIGINT,
    sync_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    UNIQUE(table_name, city_id)
);
CREATE INDEX idx_bq_sync_status ON bq_sync_state(sync_status);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| table_name | VARCHAR(100) | BigQuery table name |
| city_id | INTEGER | City being synced |
| last_sync_at | TIMESTAMPTZ | Last successful sync |
| last_sync_id | BIGINT | Last synced record ID |
| sync_status | VARCHAR(20) | pending, running, success, failed |
| error_message | TEXT | Error details if failed |

---

#### 15. feature_flags

**Purpose:** Control feature rollout per city

```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_name VARCHAR(100) NOT NULL,
    city_id INTEGER REFERENCES cities(id),    -- NULL = global
    is_enabled BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(flag_name, city_id)
);
CREATE INDEX idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX idx_feature_flags_city ON feature_flags(city_id);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| flag_name | VARCHAR(100) | Feature flag name |
| city_id | INTEGER | NULL for global, city-specific otherwise |
| is_enabled | BOOLEAN | Whether feature is enabled |
| metadata | JSONB | Additional configuration |
| created_at | TIMESTAMPTZ | When flag was created |

---

### Phase 3 Data Sync Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   PostgreSQL    │────▶│   Fivetran   │────▶│   BigQuery  │
│   (Source)      │     │   (ETL)      │     │   (Target)  │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                                          │
         │                                          │
         ▼                                          ▼
┌─────────────────┐                        ┌─────────────┐
│   API Layer     │                        │  Dashboard  │
│   (Real-time)   │                        │ (Analytics) │
└─────────────────┘                        └─────────────┘
```

**Sync Schedule:**
- `bq_fact_votes`: Every 15 minutes (incremental)
- `bq_dim_members`: Daily (full refresh)
- `bq_aggregate_daily`: Daily at 2 AM (full refresh)

---

## PHASE 4: Enterprise (50+ Cities)

**Infrastructure:** Regional sharding, Dedicated analytics DW, Redis caching
**Data Volume:** 10M+ member_votes rows
**Trigger:** 50+ cities OR 10M member_votes rows

### Regional Shard Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Central Database                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ shard_map   │  │ regional_   │  │ cities (config) │ │
│  │             │  │ aggregates  │  │                 │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
           │                │                │
    ┌──────┘                │                └──────┐
    ▼                       ▼                       ▼
┌───────────┐        ┌───────────┐        ┌───────────┐
│  US West  │        │ US Central│        │  US East  │
│  Shard    │        │  Shard    │        │  Shard    │
│           │        │           │        │           │
│ Phoenix   │        │ Chicago   │        │ New York  │
│ Santa Ana │        │ Dallas    │        │ Miami     │
│ Seattle   │        │ Denver    │        │ Boston    │
└───────────┘        └───────────┘        └───────────┘
```

---

#### Shard Mapping Table (Central DB)

**Purpose:** Route queries to correct regional database

```sql
CREATE TABLE shard_map (
    city_id INTEGER PRIMARY KEY,
    city_key VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,              -- 'us_west', 'us_east', 'us_central'
    shard_host VARCHAR(255) NOT NULL,         -- 'pg-west.cityvotes.com'
    shard_port INTEGER DEFAULT 5432,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_shard_map_region ON shard_map(region);
CREATE INDEX idx_shard_map_active ON shard_map(is_active) WHERE is_active = true;
```

| Field | Type | Description |
|-------|------|-------------|
| city_id | INTEGER | City identifier (primary key) |
| city_key | VARCHAR(50) | City key for routing |
| region | VARCHAR(20) | Geographic region |
| shard_host | VARCHAR(255) | Database hostname |
| shard_port | INTEGER | Database port |
| is_active | BOOLEAN | Whether shard is accepting traffic |
| created_at | TIMESTAMPTZ | When mapping created |

**Example Data:**
```sql
INSERT INTO shard_map (city_id, city_key, region, shard_host) VALUES
(1, 'phoenix', 'us_west', 'pg-west.cityvotes.com'),
(2, 'santa_ana', 'us_west', 'pg-west.cityvotes.com'),
(3, 'new_york', 'us_east', 'pg-east.cityvotes.com'),
(4, 'chicago', 'us_central', 'pg-central.cityvotes.com');
```

---

#### Regional Aggregates (Central DB)

**Purpose:** Cross-region summary without querying all shards

```sql
CREATE TABLE regional_aggregates (
    id SERIAL PRIMARY KEY,
    region VARCHAR(20) NOT NULL,
    metric_date DATE NOT NULL,
    cities_count INTEGER,
    total_meetings INTEGER,
    total_votes INTEGER,
    total_member_votes INTEGER,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(region, metric_date)
);
CREATE INDEX idx_regional_agg_date ON regional_aggregates(metric_date DESC);
```

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Auto-incrementing primary key |
| region | VARCHAR(20) | Region name |
| metric_date | DATE | Date of metrics |
| cities_count | INTEGER | Number of cities in region |
| total_meetings | INTEGER | Total meetings across region |
| total_votes | INTEGER | Total votes across region |
| total_member_votes | INTEGER | Total member votes |
| computed_at | TIMESTAMPTZ | When aggregation ran |

---

### Phase 4 New Tables (Per Shard)

#### 16. audit_log

**Purpose:** Track all data changes for compliance

```sql
CREATE TABLE audit_log (
    id BIGSERIAL,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL,              -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (changed_at, id)
) PARTITION BY RANGE (changed_at);

-- Monthly partitions
CREATE TABLE audit_log_2024_01 PARTITION OF audit_log
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE audit_log_2024_02 PARTITION OF audit_log
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- Continue for each month...

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(table_name, record_id);
```

| Field | Type | Description |
|-------|------|-------------|
| id | BIGSERIAL | Auto-incrementing ID |
| table_name | VARCHAR(100) | Table that changed |
| record_id | INTEGER | Primary key of changed record |
| action | VARCHAR(10) | INSERT, UPDATE, or DELETE |
| old_data | JSONB | Previous values (for UPDATE/DELETE) |
| new_data | JSONB | New values (for INSERT/UPDATE) |
| changed_by | VARCHAR(100) | User/system that made change |
| changed_at | TIMESTAMPTZ | When change occurred |

**Audit Trigger Example:**
```sql
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

---

#### 17. rate_limits

**Purpose:** API rate limiting per client

```sql
CREATE TABLE rate_limits (
    api_key VARCHAR(64) PRIMARY KEY,
    client_name VARCHAR(100),
    requests_per_minute INTEGER DEFAULT 60,
    requests_per_day INTEGER DEFAULT 10000,
    current_minute_count INTEGER DEFAULT 0,
    current_day_count INTEGER DEFAULT 0,
    last_request_at TIMESTAMPTZ,
    minute_reset_at TIMESTAMPTZ,
    day_reset_at TIMESTAMPTZ
);
CREATE INDEX idx_rate_limits_client ON rate_limits(client_name);
```

| Field | Type | Description |
|-------|------|-------------|
| api_key | VARCHAR(64) | API key (primary key) |
| client_name | VARCHAR(100) | Client identifier |
| requests_per_minute | INTEGER | Minute rate limit |
| requests_per_day | INTEGER | Daily rate limit |
| current_minute_count | INTEGER | Requests this minute |
| current_day_count | INTEGER | Requests today |
| last_request_at | TIMESTAMPTZ | Last request time |
| minute_reset_at | TIMESTAMPTZ | When minute counter resets |
| day_reset_at | TIMESTAMPTZ | When day counter resets |

---

### Phase 4 Redis Cache Schema

```
# Key Patterns and TTLs

# City configuration (TTL: 1 hour)
city:{city_key}:config           -> JSON city configuration
SET city:phoenix:config '{"name":"Phoenix","seats":9,...}' EX 3600

# Current members (TTL: 1 hour)
city:{city_key}:members:current  -> JSON array of current members
SET city:phoenix:members:current '[{"id":1,"name":"Kate Gallego",...}]' EX 3600

# Member voting stats (TTL: 15 minutes)
member:{member_id}:stats:{year}  -> JSON voting statistics
SET member:1:stats:2024 '{"yes":450,"no":25,"absent":15}' EX 900

# Meeting vote data (TTL: 5 minutes)
meeting:{meeting_id}:votes       -> JSON full vote data
SET meeting:123:votes '[{"item":"1","passed":true,...}]' EX 300

# API response cache (TTL: varies)
api:cache:{endpoint_hash}        -> Cached API response
SET api:cache:abc123 '{"data":[...]}' EX 60
```

**Redis Configuration:**
```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## Threshold Triggers Summary

| Metric | Threshold | Action Required |
|--------|-----------|-----------------|
| Cities | 5 | Add partitioning (Phase 2) |
| Cities | 20 | Add BigQuery (Phase 3) |
| Cities | 50 | Regional sharding (Phase 4) |
| member_votes rows | 1M | Partitioning (Phase 2) |
| member_votes rows | 5M | BigQuery analytics (Phase 3) |
| member_votes rows | 10M | Full warehouse (Phase 4) |
| Concurrent users | 100 | Read replicas (Phase 2) |
| Concurrent users | 1000 | Redis caching (Phase 4) |

---

## Data Volume Projections

**Per city per year:**
- Meetings: ~24
- Agenda items: ~500
- Votes: ~500
- Member votes: ~4,500

### Projected member_votes Rows

| Cities | Year 1 | Year 5 | Year 10 |
|--------|--------|--------|---------|
| 1 | 4,500 | 22,500 | 45,000 |
| 5 | 22,500 | 112,500 | 225,000 |
| 10 | 45,000 | 225,000 | 450,000 |
| 20 | 90,000 | 450,000 | 900,000 |
| 50 | 225,000 | 1,125,000 | 2,250,000 |

### Phase Triggers by Timeline

| Year | Cities | Rows | Recommended Phase |
|------|--------|------|-------------------|
| 1 | 1-5 | 4.5K-22.5K | Phase 1 |
| 2 | 5-10 | 45K-90K | Phase 2 |
| 3 | 10-20 | 135K-270K | Phase 2 |
| 5 | 20-30 | 450K-675K | Phase 3 |
| 10 | 50+ | 2.25M+ | Phase 4 |

---

## Cost Forecasting by Phase

This section provides formulas and estimates for forecasting infrastructure costs at each scaling phase.

### Cost Variables

| Variable | Description | How to Measure |
|----------|-------------|----------------|
| **Storage (GB)** | Total database size | `SELECT pg_database_size('cityvotes') / 1024^3` |
| **Rows** | Total member_votes count | `SELECT COUNT(*) FROM member_votes` |
| **QPS** | Queries per second | Application metrics / pg_stat_statements |
| **MAU** | Monthly active users | Application analytics |
| **Cities** | Number of cities | `SELECT COUNT(*) FROM cities` |

### Storage Estimation Formula

```
Storage per city per year ≈ 15 MB
  - meetings:        24 rows × 500 bytes   = 12 KB
  - agenda_items:   500 rows × 1 KB        = 500 KB
  - votes:          500 rows × 300 bytes   = 150 KB
  - member_votes: 4,500 rows × 100 bytes   = 450 KB
  - documents:      200 rows × 500 bytes   = 100 KB
  - indexes & overhead:                    ≈ 14 MB

Total Storage = Cities × Years × 15 MB
```

**Example:** 20 cities × 5 years = 1.5 GB raw data

---

### Phase 1 Cost Forecast (1-5 Cities)

**Infrastructure Options:**

| Provider | Service | Specs | Monthly Cost |
|----------|---------|-------|--------------|
| **Supabase** | Free Tier | 500 MB, 2 GB bandwidth | $0 |
| **Supabase** | Pro | 8 GB, 50 GB bandwidth | $25 |
| **Railway** | Postgres | 1 GB RAM, 1 GB storage | $5-20 |
| **Render** | Postgres | 1 GB RAM, 1 GB storage | $7 |
| **AWS RDS** | db.t3.micro | 1 vCPU, 1 GB RAM, 20 GB | $15-25 |
| **GCP Cloud SQL** | db-f1-micro | Shared vCPU, 0.6 GB RAM | $10-15 |
| **DigitalOcean** | Basic | 1 vCPU, 1 GB RAM, 10 GB | $15 |

**Cost Formula (Phase 1):**
```
Monthly Cost = PostgreSQL hosting + Backup storage

Estimated Range: $0 - $25/month
```

**Recommended for Phase 1:** Supabase Pro ($25/mo) or Railway ($5-20/mo)

---

### Phase 2 Cost Forecast (5-20 Cities)

**Infrastructure Components:**

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **Primary DB** | AWS RDS db.t3.small | 2 vCPU, 2 GB RAM, 50 GB | $30-50 |
| **Read Replica** | AWS RDS db.t3.small | 2 vCPU, 2 GB RAM | $25-40 |
| **PgBouncer** | EC2 t3.micro or included | Connection pooling | $0-10 |
| **Backup Storage** | S3 | 10 GB automated backups | $2-5 |

**Alternative Managed Options:**

| Provider | Service | Monthly Cost |
|----------|---------|--------------|
| **Supabase** | Pro + Read Replicas | $25 + $50 = $75 |
| **PlanetScale** | Scaler | $29 (MySQL, not PG) |
| **Neon** | Scale | $69 (serverless PG) |
| **CrunchyData** | Hobby | $25 |
| **AWS RDS** | Multi-AZ t3.small | $60-100 |

**Cost Formula (Phase 2):**
```
Monthly Cost = Primary DB + Read Replica + Connection Pooling + Backups

Estimated Range: $50 - $150/month
```

**Recommended for Phase 2:** AWS RDS with read replica ($75-100/mo) or Supabase Pro + replica ($75/mo)

---

### Phase 3 Cost Forecast (20-50 Cities)

**Infrastructure Components:**

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **Primary DB** | AWS RDS db.t3.medium | 2 vCPU, 4 GB RAM, 100 GB | $70-100 |
| **Read Replica** | AWS RDS db.t3.medium | 2 vCPU, 4 GB RAM | $50-80 |
| **BigQuery** | On-demand | Storage + Queries | $20-100 |
| **Data Sync** | Fivetran/Airbyte | ETL pipeline | $0-100 |
| **Backup/DR** | S3 + snapshots | 50 GB | $5-15 |

**BigQuery Cost Breakdown:**

| Metric | Pricing | Typical Usage | Monthly Cost |
|--------|---------|---------------|--------------|
| **Storage** | $0.02/GB/month | 5 GB | $0.10 |
| **Active Storage** | $0.04/GB/month | 2 GB | $0.08 |
| **Queries** | $6.25/TB scanned | 100 GB/month | $0.63 |
| **Streaming Inserts** | $0.05/GB | 1 GB/month | $0.05 |

**BigQuery Total:** ~$1-5/month for typical CityVotes usage (very cost-effective!)

**ETL Pipeline Options:**

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Fivetran** | None | $1/MAR (Monthly Active Row) |
| **Airbyte Cloud** | None | $0.15/credit |
| **Airbyte Self-Hosted** | Free | $0 (compute costs only) |
| **Stitch** | None | $100/month base |
| **Custom Script** | Free | $0 (compute costs only) |

**Cost Formula (Phase 3):**
```
Monthly Cost = Primary DB + Read Replica + BigQuery + ETL + Backups

BigQuery Cost = (Storage_GB × $0.02) + (Query_TB × $6.25)
ETL Cost = Fivetran MAR × $1 OR Airbyte self-hosted ($0)

Estimated Range: $150 - $400/month
```

**Recommended for Phase 3:**
- Database: AWS RDS db.t3.medium + replica ($150/mo)
- Analytics: BigQuery on-demand ($5-20/mo)
- ETL: Airbyte self-hosted on EC2 t3.micro ($10/mo) or Fivetran ($50-100/mo)
- **Total: $165 - $280/month**

---

### Phase 4 Cost Forecast (50+ Cities)

**Infrastructure Components:**

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **Central DB** | AWS RDS db.t3.medium | Routing/config | $70-100 |
| **Regional Shard (×3)** | AWS RDS db.t3.medium | Data per region | $210-300 |
| **Redis Cluster** | ElastiCache | 2 nodes, cache.t3.small | $50-80 |
| **BigQuery** | On-demand | Analytics warehouse | $50-200 |
| **ETL Pipeline** | Fivetran/Airbyte | Multi-source sync | $100-300 |
| **Load Balancer** | AWS ALB | API routing | $20-30 |
| **Monitoring** | Datadog/CloudWatch | Observability | $50-100 |

**Regional Shard Sizing:**

| Region | Cities | Storage | Instance | Monthly Cost |
|--------|--------|---------|----------|--------------|
| US West | 20 | 30 GB | db.t3.medium | $70-100 |
| US East | 20 | 30 GB | db.t3.medium | $70-100 |
| US Central | 10 | 15 GB | db.t3.small | $40-60 |

**Redis Sizing:**

| Cache Size | Instance | Nodes | Monthly Cost |
|------------|----------|-------|--------------|
| 1 GB | cache.t3.micro | 2 | $25 |
| 2 GB | cache.t3.small | 2 | $50 |
| 6 GB | cache.t3.medium | 2 | $130 |

**Cost Formula (Phase 4):**
```
Monthly Cost = Central DB + (Shards × Shard Cost) + Redis + BigQuery + ETL + Monitoring

Shard Cost = Instance + Storage + Backup
Redis Cost = Node Cost × Nodes × Regions

Estimated Range: $500 - $1,200/month
```

**Recommended for Phase 4:**
- Central: RDS db.t3.medium ($80/mo)
- 3 Regional Shards: RDS db.t3.medium × 3 ($240/mo)
- Redis: ElastiCache t3.small × 2 ($50/mo)
- BigQuery: On-demand ($100/mo)
- ETL: Airbyte self-hosted ($30/mo compute)
- Monitoring: CloudWatch + basic alerts ($30/mo)
- **Total: $530 - $800/month**

---

### Cost Summary by Phase

| Phase | Cities | Monthly Cost | Cost per City |
|-------|--------|--------------|---------------|
| **Phase 1** | 1-5 | $0 - $25 | $0 - $5 |
| **Phase 2** | 5-20 | $50 - $150 | $2.50 - $7.50 |
| **Phase 3** | 20-50 | $150 - $400 | $3 - $8 |
| **Phase 4** | 50+ | $500 - $1,200 | $10 - $24 |

### Annual Cost Projection

| Phase | Low Estimate | High Estimate |
|-------|--------------|---------------|
| **Phase 1** | $0/year | $300/year |
| **Phase 2** | $600/year | $1,800/year |
| **Phase 3** | $1,800/year | $4,800/year |
| **Phase 4** | $6,000/year | $14,400/year |

---

### Cost Optimization Tips

**Phase 1:**
- Use Supabase free tier for development
- Upgrade to Pro only when approaching limits

**Phase 2:**
- Use Reserved Instances (1-year) for 30-40% savings
- Schedule read replica scale-down during off-hours
- Use PgBouncer to reduce connection overhead

**Phase 3:**
- Use BigQuery on-demand pricing (cheaper for < 1TB/month queries)
- Set up BigQuery slots only if query volume exceeds 100 TB/month
- Self-host Airbyte instead of Fivetran for 50-80% savings
- Use materialized views to reduce repeated query costs

**Phase 4:**
- Reserved Instances for all production databases
- Spot instances for ETL/batch processing
- Redis cluster auto-scaling during traffic spikes
- Data lifecycle policies to archive old audit logs

---

### Cost Monitoring Queries

**PostgreSQL Storage:**
```sql
-- Total database size
SELECT pg_size_pretty(pg_database_size('cityvotes'));

-- Table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

**BigQuery Usage:**
```sql
-- Query costs (last 30 days)
SELECT
    user_email,
    SUM(total_bytes_billed) / POW(1024, 4) AS tb_billed,
    SUM(total_bytes_billed) / POW(1024, 4) * 6.25 AS estimated_cost_usd
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_email;
```

**Row Growth Rate:**
```sql
-- Monthly growth rate
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*) AS new_rows
FROM member_votes
WHERE created_at > NOW() - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;
```

---

## Migration Checklist

### Phase 1 → Phase 2
- [ ] Set up PgBouncer connection pooling
- [ ] Create read replica
- [ ] Add city_id to member_votes
- [ ] Convert member_votes to partitioned table
- [ ] Convert meetings to partitioned table
- [ ] Create api_cache table
- [ ] Create query_metrics table
- [ ] Update application connection strings

### Phase 2 → Phase 3
- [ ] Set up BigQuery dataset
- [ ] Create BigQuery tables
- [ ] Configure Fivetran/Airbyte sync
- [ ] Create bq_sync_state table
- [ ] Create feature_flags table
- [ ] Update dashboards to use BigQuery
- [ ] Test incremental sync

### Phase 3 → Phase 4
- [ ] Provision regional database servers
- [ ] Create shard_map table in central DB
- [ ] Create regional_aggregates table
- [ ] Migrate city data to regional shards
- [ ] Create audit_log tables per shard
- [ ] Create rate_limits table
- [ ] Set up Redis cluster
- [ ] Update API routing logic
- [ ] Test cross-region queries

---

## Related Documents

- [DATABASE_SCHEMA_OPTIONS.md](DATABASE_SCHEMA_OPTIONS.md) - Detailed Option A schema
- [DATA_COLLECTION_WORKFLOW.md](DATA_COLLECTION_WORKFLOW.md) - Data collection process
