# Phoenix City Council Database Schema Plan

## Overview

This document outlines the SQL database schema for storing Phoenix City Council meeting data retrieved from the Legistar API.

---

## Schema Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Bodies      │     │     Events      │     │   EventItems    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ BodyId (PK)     │◄────│ EventBodyId(FK) │     │ EventItemId(PK) │
│ BodyName        │     │ EventId (PK)    │◄────│ EventId (FK)    │
│ BodyTypeId (FK) │     │ EventDate       │     │ MatterId (FK)   │
└─────────────────┘     │ EventTime       │     │ AgendaNumber    │
        ▲               └─────────────────┘     │ ConsentFlag(FK) │
        │                                       └─────────────────┘
┌─────────────────┐                                     │
│    BodyTypes    │     ┌─────────────────┐            │
├─────────────────┤     │     Matters     │◄───────────┘
│ BodyTypeId (PK) │     ├─────────────────┤
│ BodyTypeName    │     │ MatterId (PK)   │
└─────────────────┘     │ MatterTypeId(FK)│
                        │ MatterStatusId  │
                        │ IndexId (FK)    │
                        └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MatterTypes   │     │  MatterStatuses │     │     Indexes     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ MatterTypeId(PK)│     │MatterStatusId(PK│     │ IndexId (PK)    │
│ MatterTypeName  │     │MatterStatusName │     │ IndexName       │
└─────────────────┘     └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Persons      │     │   VoteTypes     │     │    Actions      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ PersonId (PK)   │     │ VoteTypeId (PK) │     │ ActionId (PK)   │
│ PersonFullName  │     │ VoteTypeName    │     │ ActionName      │
│ District        │     └─────────────────┘     └─────────────────┘
└─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│    RollCalls    │     │  ConsentTypes   │
├─────────────────┤     ├─────────────────┤
│ RollCallId (PK) │     │ ConsentFlag(PK) │
│ EventItemId(FK) │     │ ConsentName     │
│ PersonId (FK)   │     │ Description     │
│ VoteTypeId (FK) │     └─────────────────┘
└─────────────────┘
```

---

## Reference/Lookup Tables

### ConsentTypes
Indicates whether an agenda item was part of a consent agenda.

| Column | Type | Description |
|--------|------|-------------|
| ConsentFlag | INTEGER | Primary Key (0 or 1) |
| ConsentName | VARCHAR(50) | Display name |
| Description | VARCHAR(255) | Full description |

**Data:**

| ConsentFlag | ConsentName | Description |
|-------------|-------------|-------------|
| 1 | Consent | Part of the consent agenda, passed as a group |
| 0 | Regular | Discussed and voted on individually |

```sql
CREATE TABLE ConsentTypes (
    ConsentFlag INTEGER PRIMARY KEY,
    ConsentName VARCHAR(50) NOT NULL,
    Description VARCHAR(255)
);

INSERT INTO ConsentTypes (ConsentFlag, ConsentName, Description) VALUES
(1, 'Consent', 'Part of the consent agenda, passed as a group'),
(0, 'Regular', 'Discussed and voted on individually');
```

---

### BodyTypes
Categories for organizational bodies.

| Column | Type | Description |
|--------|------|-------------|
| BodyTypeId | INTEGER | Primary Key |
| BodyTypeName | VARCHAR(100) | Name of body type |

**Data:**

| BodyTypeId | BodyTypeName |
|------------|--------------|
| 42 | Primary Legislative Body |
| 43 | Budget Hearing |
| 49 | Department |
| 56 | Policy |
| 58 | Subcommittee |
| 59 | General Information Packet |
| 60 | Subcommittee General Information Packet |
| 61 | Planning Board or Commission |

```sql
CREATE TABLE BodyTypes (
    BodyTypeId INTEGER PRIMARY KEY,
    BodyTypeName VARCHAR(100) NOT NULL
);

INSERT INTO BodyTypes (BodyTypeId, BodyTypeName) VALUES
(42, 'Primary Legislative Body'),
(43, 'Budget Hearing'),
(49, 'Department'),
(56, 'Policy'),
(58, 'Subcommittee'),
(59, 'General Information Packet'),
(60, 'Subcommittee General Information Packet'),
(61, 'Planning Board or Commission');
```

---

### VoteTypes
Types of votes a council member can cast.

| Column | Type | Description |
|--------|------|-------------|
| VoteTypeId | INTEGER | Primary Key |
| VoteTypeName | VARCHAR(50) | Vote name |
| VoteTypeResult | INTEGER | 0=neutral, 1=affirmative, 2=negative |

**Data:**

| VoteTypeId | VoteTypeName | VoteTypeResult |
|------------|--------------|----------------|
| 16 | Conflict | 0 |
| 17 | Yes | 1 |
| 18 | Present | 0 |
| 19 | Abstain Yes | 1 |
| 23 | Telephonic | 0 |
| 24 | No | 2 |
| 25 | Absent | 0 |

```sql
CREATE TABLE VoteTypes (
    VoteTypeId INTEGER PRIMARY KEY,
    VoteTypeName VARCHAR(50) NOT NULL,
    VoteTypeResult INTEGER NOT NULL
);

INSERT INTO VoteTypes (VoteTypeId, VoteTypeName, VoteTypeResult) VALUES
(16, 'Conflict', 0),
(17, 'Yes', 1),
(18, 'Present', 0),
(19, 'Abstain Yes', 1),
(23, 'Telephonic', 0),
(24, 'No', 2),
(25, 'Absent', 0);
```

---

### Actions
Types of actions that can be taken on matters.

| Column | Type | Description |
|--------|------|-------------|
| ActionId | INTEGER | Primary Key |
| ActionName | VARCHAR(100) | Action name |

**Data:**

| ActionId | ActionName |
|----------|------------|
| 362 | referred |
| 363 | adopted |
| 365 | recommended for approval |
| 366 | recommended for denial |
| 367 | approved as amended |
| 368 | amended |
| 370 | withdrawn |
| 372 | introduced on first reading |
| 373 | received and filed |
| 375 | tabled |

```sql
CREATE TABLE Actions (
    ActionId INTEGER PRIMARY KEY,
    ActionName VARCHAR(100) NOT NULL
);

INSERT INTO Actions (ActionId, ActionName) VALUES
(362, 'referred'),
(363, 'adopted'),
(365, 'recommended for approval'),
(366, 'recommended for denial'),
(367, 'approved as amended'),
(368, 'amended'),
(370, 'withdrawn'),
(372, 'introduced on first reading'),
(373, 'received and filed'),
(375, 'tabled');
```

---

### MatterTypes
Categories for legislation and agenda items.

| Column | Type | Description |
|--------|------|-------------|
| MatterTypeId | INTEGER | Primary Key |
| MatterTypeName | VARCHAR(100) | Matter type name |
| MatterTypeCategory | VARCHAR(50) | Grouping category |

**Data:**

| MatterTypeId | MatterTypeName | MatterTypeCategory |
|--------------|----------------|-------------------|
| 63 | Information Only | Administrative |
| 64 | Information and Discussion | Administrative |
| 65 | Minutes | Administrative |
| 66 | Liquor | Licensing |
| 67 | Bingo | Licensing |
| 68 | Off-Track Betting | Licensing |
| 69 | Special Event | Licensing |
| 70 | Board & Commission | Legislative |
| 71 | Consent Action | Legislative |
| 72 | Formal Action | Legislative |
| 73 | Resolution | Legislative |
| 74 | Payment Ordinance | Legislative |
| 75 | Petition | Public Engagement |
| 76 | Discussion and Possible Action | Public Engagement |
| 77 | Public Hearing (Non-Zoning) | Public Engagement |
| 78 | Suspension of the Rules | Legislative |
| 79 | Ordinance-G | Legislative |
| 80 | Ordinance-S | Legislative |
| 81 | Zoning Appeal | Zoning |
| 82 | Zoning Abandonment | Zoning |
| 83 | Zoning Modification of Stipulations | Zoning |
| 84 | Zoning Ordinance | Zoning |
| 85 | Zoning Public Hearing Only | Zoning |
| 86 | Zoning Plat | Zoning |
| 87 | Zoning Ratification | Zoning |
| 88 | Zoning Text and Specific Plan Amendments | Zoning |
| 89 | Zoning Continuances and Withdrawals | Zoning |
| 90 | Zoning Waiver Request | Zoning |
| 91 | Zoning GPA and Companion Rezoning Cases | Zoning |
| 92 | Zoning Ordinance & Public Hearing | Zoning |

```sql
CREATE TABLE MatterTypes (
    MatterTypeId INTEGER PRIMARY KEY,
    MatterTypeName VARCHAR(100) NOT NULL,
    MatterTypeCategory VARCHAR(50)
);
```

---

### Indexes (Districts)
Geographic classifications for matters.

| Column | Type | Description |
|--------|------|-------------|
| IndexId | INTEGER | Primary Key |
| IndexName | VARCHAR(50) | District/area name |

**Data:**

| IndexId | IndexName |
|---------|-----------|
| 207 | District 1 |
| 208 | District 2 |
| 209 | District 3 |
| 210 | District 4 |
| 211 | District 5 |
| 212 | District 6 |
| 213 | District 7 |
| 214 | Citywide |
| 215 | District 8 |
| 216 | Out of City |

```sql
CREATE TABLE Indexes (
    IndexId INTEGER PRIMARY KEY,
    IndexName VARCHAR(50) NOT NULL
);

INSERT INTO Indexes (IndexId, IndexName) VALUES
(207, 'District 1'),
(208, 'District 2'),
(209, 'District 3'),
(210, 'District 4'),
(211, 'District 5'),
(212, 'District 6'),
(213, 'District 7'),
(214, 'Citywide'),
(215, 'District 8'),
(216, 'Out of City');
```

---

### MatterStatuses
Workflow statuses for matters.

| Column | Type | Description |
|--------|------|-------------|
| MatterStatusId | INTEGER | Primary Key |
| MatterStatusName | VARCHAR(100) | Status name |
| MatterStatusCategory | VARCHAR(50) | Grouping (Initial, In Process, Final) |

**Key Statuses:**

| MatterStatusId | MatterStatusName | MatterStatusCategory |
|----------------|------------------|---------------------|
| 80 | Agenda Ready | Initial |
| - | Continued | In Process |
| - | Withdrawn from Agenda | In Process |
| - | Passed | Final - Positive |
| - | Approved | Final - Positive |
| - | Adopted | Final - Positive |
| - | Failed | Final - Negative |
| - | Not Heard | Other |

```sql
CREATE TABLE MatterStatuses (
    MatterStatusId INTEGER PRIMARY KEY,
    MatterStatusName VARCHAR(100) NOT NULL,
    MatterStatusCategory VARCHAR(50)
);
```

---

## Entity Tables

### Bodies
Committees, councils, and organizational groups.

| Column | Type | Description |
|--------|------|-------------|
| BodyId | INTEGER | Primary Key |
| BodyName | VARCHAR(200) | Name of the body |
| BodyTypeId | INTEGER | FK to BodyTypes |
| BodyActiveFlag | INTEGER | 1=active, 0=inactive |

```sql
CREATE TABLE Bodies (
    BodyId INTEGER PRIMARY KEY,
    BodyName VARCHAR(200) NOT NULL,
    BodyTypeId INTEGER REFERENCES BodyTypes(BodyTypeId),
    BodyActiveFlag INTEGER DEFAULT 1
);
```

---

### Persons
Council members and staff.

| Column | Type | Description |
|--------|------|-------------|
| PersonId | INTEGER | Primary Key |
| PersonFirstName | VARCHAR(100) | First name |
| PersonLastName | VARCHAR(100) | Last name |
| PersonFullName | VARCHAR(200) | Full display name |
| PersonEmail | VARCHAR(200) | Email address |
| District | VARCHAR(50) | District represented (if council member) |
| PersonActiveFlag | INTEGER | 1=active, 0=inactive |

```sql
CREATE TABLE Persons (
    PersonId INTEGER PRIMARY KEY,
    PersonFirstName VARCHAR(100),
    PersonLastName VARCHAR(100),
    PersonFullName VARCHAR(200) NOT NULL,
    PersonEmail VARCHAR(200),
    District VARCHAR(50),
    PersonActiveFlag INTEGER DEFAULT 1
);
```

**Current Council Members:**

| PersonId | PersonFullName | District |
|----------|----------------|----------|
| 199 | Kate Gallego | Mayor |
| 1772 | Ann O'Brien | District 1 (Vice Mayor) |
| 192 | Jim Waring | District 2 |
| 841 | Debra Stark | District 3 |
| 195 | Laura Pastor | District 4 |
| 1617 | Betty Guardado | District 5 |
| 2023 | Kevin Robinson | District 6 |
| 2293 | Anna Hernandez | District 7 |
| 2022 | Kesha Hodge Washington | District 8 |

---

### Events
Meetings scheduled by bodies.

| Column | Type | Description |
|--------|------|-------------|
| EventId | INTEGER | Primary Key |
| EventBodyId | INTEGER | FK to Bodies |
| EventDate | DATE | Meeting date |
| EventTime | VARCHAR(20) | Meeting time |
| EventLocation | VARCHAR(200) | Location/venue |
| EventInSiteURL | VARCHAR(500) | Legistar detail page URL |
| EventAgendaFile | VARCHAR(500) | URL to agenda PDF |
| EventMinutesFile | VARCHAR(500) | URL to minutes PDF |
| EventVideoPath | VARCHAR(500) | URL to video recording |

```sql
CREATE TABLE Events (
    EventId INTEGER PRIMARY KEY,
    EventBodyId INTEGER REFERENCES Bodies(BodyId),
    EventDate DATE NOT NULL,
    EventTime VARCHAR(20),
    EventLocation VARCHAR(200),
    EventInSiteURL VARCHAR(500),
    EventAgendaFile VARCHAR(500),
    EventMinutesFile VARCHAR(500),
    EventVideoPath VARCHAR(500)
);
```

---

### Matters
Legislation, resolutions, ordinances, and other official items.

| Column | Type | Description |
|--------|------|-------------|
| MatterId | INTEGER | Primary Key |
| MatterFile | VARCHAR(50) | File number (e.g., "25-2424") |
| MatterTitle | VARCHAR(500) | Title/description |
| MatterTypeId | INTEGER | FK to MatterTypes |
| MatterStatusId | INTEGER | FK to MatterStatuses |
| MatterBodyId | INTEGER | FK to Bodies |
| IndexId | INTEGER | FK to Indexes (district) |
| MatterRequester | VARCHAR(200) | Requesting department |
| MatterIntroDate | DATE | Introduction date |
| MatterAgendaDate | DATE | Scheduled agenda date |
| MatterPassedDate | DATE | Date passed |
| MatterEnactmentNumber | VARCHAR(100) | Ordinance/Resolution number |
| MatterNotes | TEXT | Internal notes |

```sql
CREATE TABLE Matters (
    MatterId INTEGER PRIMARY KEY,
    MatterFile VARCHAR(50),
    MatterTitle VARCHAR(500),
    MatterTypeId INTEGER REFERENCES MatterTypes(MatterTypeId),
    MatterStatusId INTEGER REFERENCES MatterStatuses(MatterStatusId),
    MatterBodyId INTEGER REFERENCES Bodies(BodyId),
    IndexId INTEGER REFERENCES Indexes(IndexId),
    MatterRequester VARCHAR(200),
    MatterIntroDate DATE,
    MatterAgendaDate DATE,
    MatterPassedDate DATE,
    MatterEnactmentNumber VARCHAR(100),
    MatterNotes TEXT
);
```

---

### EventItems
Individual agenda items within a meeting.

| Column | Type | Description |
|--------|------|-------------|
| EventItemId | INTEGER | Primary Key |
| EventId | INTEGER | FK to Events |
| MatterId | INTEGER | FK to Matters (nullable) |
| EventItemAgendaNumber | VARCHAR(20) | Agenda item number |
| EventItemTitle | VARCHAR(500) | Title/description |
| EventItemConsent | INTEGER | FK to ConsentTypes |
| EventItemPassedFlag | INTEGER | 1=passed, 0=failed, null=no vote |
| EventItemTally | VARCHAR(20) | Vote tally (e.g., "7-2") |
| ActionId | INTEGER | FK to Actions |
| ActionText | TEXT | Motion/action description |
| MoverId | INTEGER | FK to Persons |
| SeconderId | INTEGER | FK to Persons |
| EventItemAgendaNote | TEXT | Public agenda notes |
| EventItemMinutesNote | TEXT | Notes from minutes |
| EventItemVideo | VARCHAR(500) | Video timestamp link |

```sql
CREATE TABLE EventItems (
    EventItemId INTEGER PRIMARY KEY,
    EventId INTEGER REFERENCES Events(EventId),
    MatterId INTEGER REFERENCES Matters(MatterId),
    EventItemAgendaNumber VARCHAR(20),
    EventItemTitle VARCHAR(500),
    EventItemConsent INTEGER REFERENCES ConsentTypes(ConsentFlag),
    EventItemPassedFlag INTEGER,
    EventItemTally VARCHAR(20),
    ActionId INTEGER REFERENCES Actions(ActionId),
    ActionText TEXT,
    MoverId INTEGER REFERENCES Persons(PersonId),
    SeconderId INTEGER REFERENCES Persons(PersonId),
    EventItemAgendaNote TEXT,
    EventItemMinutesNote TEXT,
    EventItemVideo VARCHAR(500)
);
```

---

### RollCalls
Individual votes by council members on event items.

| Column | Type | Description |
|--------|------|-------------|
| RollCallId | INTEGER | Primary Key |
| EventItemId | INTEGER | FK to EventItems |
| PersonId | INTEGER | FK to Persons |
| VoteTypeId | INTEGER | FK to VoteTypes |

```sql
CREATE TABLE RollCalls (
    RollCallId INTEGER PRIMARY KEY,
    EventItemId INTEGER REFERENCES EventItems(EventItemId),
    PersonId INTEGER REFERENCES Persons(PersonId),
    VoteTypeId INTEGER REFERENCES VoteTypes(VoteTypeId)
);
```

---

### MatterAttachments
Documents attached to matters.

| Column | Type | Description |
|--------|------|-------------|
| MatterAttachmentId | INTEGER | Primary Key |
| MatterId | INTEGER | FK to Matters |
| AttachmentName | VARCHAR(200) | File name |
| AttachmentURL | VARCHAR(500) | URL to document |

```sql
CREATE TABLE MatterAttachments (
    MatterAttachmentId INTEGER PRIMARY KEY,
    MatterId INTEGER REFERENCES Matters(MatterId),
    AttachmentName VARCHAR(200),
    AttachmentURL VARCHAR(500)
);
```

---

### MatterSponsors
Sponsors of matters.

| Column | Type | Description |
|--------|------|-------------|
| MatterSponsorId | INTEGER | Primary Key |
| MatterId | INTEGER | FK to Matters |
| PersonId | INTEGER | FK to Persons |
| SponsorSequence | INTEGER | Order of sponsors |

```sql
CREATE TABLE MatterSponsors (
    MatterSponsorId INTEGER PRIMARY KEY,
    MatterId INTEGER REFERENCES Matters(MatterId),
    PersonId INTEGER REFERENCES Persons(PersonId),
    SponsorSequence INTEGER
);
```

---

## Sample Queries

### Get all agenda items for a meeting with vote details
```sql
SELECT
    e.EventDate,
    b.BodyName,
    ei.EventItemAgendaNumber,
    ei.EventItemTitle,
    ct.ConsentName,
    ei.EventItemTally,
    a.ActionName,
    ei.ActionText
FROM EventItems ei
JOIN Events e ON ei.EventId = e.EventId
JOIN Bodies b ON e.EventBodyId = b.BodyId
LEFT JOIN ConsentTypes ct ON ei.EventItemConsent = ct.ConsentFlag
LEFT JOIN Actions a ON ei.ActionId = a.ActionId
WHERE e.EventDate = '2025-11-19'
ORDER BY ei.EventItemAgendaNumber;
```

### Get voting record for a council member
```sql
SELECT
    e.EventDate,
    ei.EventItemTitle,
    vt.VoteTypeName
FROM RollCalls rc
JOIN EventItems ei ON rc.EventItemId = ei.EventItemId
JOIN Events e ON ei.EventId = e.EventId
JOIN VoteTypes vt ON rc.VoteTypeId = vt.VoteTypeId
JOIN Persons p ON rc.PersonId = p.PersonId
WHERE p.PersonFullName = 'Laura Pastor'
ORDER BY e.EventDate DESC;
```

### Get all matters by district
```sql
SELECT
    m.MatterFile,
    m.MatterTitle,
    mt.MatterTypeName,
    i.IndexName
FROM Matters m
JOIN MatterTypes mt ON m.MatterTypeId = mt.MatterTypeId
JOIN Indexes i ON m.IndexId = i.IndexId
WHERE i.IndexName = 'District 4'
ORDER BY m.MatterIntroDate DESC;
```

---

## Notes

- All IDs match the Legistar API IDs for easy data synchronization
- Foreign keys enforce referential integrity
- Text fields use appropriate lengths based on observed API data
- The schema supports both the flat CSV export format and normalized relational queries

---

## Version History

| Date | Version | Notes |
|------|---------|-------|
| 2026-01-16 | 1.0 | Initial schema plan |
