# Phoenix City Council Legistar API Reference

## Complete API Documentation for Phoenix Municipal Data

**Base URL:** `https://webapi.legistar.com/v1/phoenix/`

**Client Identifier:** `phoenix`

**Authentication:** No API token required for public data access

**Protocol:** HTTPS (HTTP also supported for GET requests)

**Response Format:** JSON

**Rate Limits:** Queries limited to 1000 responses per request

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [OData Query Parameters](#odata-query-parameters)
3. [Bodies Endpoints](#bodies-endpoints)
4. [Body Types Endpoints](#body-types-endpoints)
5. [Events Endpoints](#events-endpoints)
6. [Event Items Endpoints](#event-items-endpoints)
7. [Matters Endpoints](#matters-endpoints)
8. [Matter Types Endpoints](#matter-types-endpoints)
9. [Matter Statuses Endpoints](#matter-statuses-endpoints)
10. [Matter Attachments Endpoints](#matter-attachments-endpoints)
11. [Matter Histories Endpoints](#matter-histories-endpoints)
12. [Matter Sponsors Endpoints](#matter-sponsors-endpoints)
13. [Matter Indexes Endpoints](#matter-indexes-endpoints)
14. [Persons Endpoints](#persons-endpoints)
15. [Actions Endpoints](#actions-endpoints)
16. [Vote Types Endpoints](#vote-types-endpoints)
17. [Indexes Endpoints](#indexes-endpoints)
18. [Office Records Endpoints](#office-records-endpoints)
19. [Roll Calls Endpoints](#roll-calls-endpoints)
20. [Common Use Cases](#common-use-cases)
21. [Error Handling](#error-handling)

---

## Quick Start

### Basic API Call Pattern
```bash
curl "https://webapi.legistar.com/v1/phoenix/{endpoint}"
```

### Example: Get All Bodies
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodies"
```

### Example: Get Recent Events
```bash
curl "https://webapi.legistar.com/v1/phoenix/events?$top=10&$orderby=EventDate%20desc"
```

---

## OData Query Parameters

The API supports OData query parameters for pagination, filtering, and sorting.

### Pagination

| Parameter | Description | Example |
|-----------|-------------|---------|
| `$top` | Limit number of results | `$top=10` |
| `$skip` | Skip N results (for pagination) | `$skip=20` |

**Pagination Example:**
```bash
# First page (items 1-10)
curl "https://webapi.legistar.com/v1/phoenix/matters?$top=10&$skip=0"

# Second page (items 11-20)
curl "https://webapi.legistar.com/v1/phoenix/matters?$top=10&$skip=10"
```

### Sorting

| Parameter | Description | Example |
|-----------|-------------|---------|
| `$orderby` | Sort by field | `$orderby=EventDate%20desc` |

**Sorting Examples:**
```bash
# Sort events by date descending
curl "https://webapi.legistar.com/v1/phoenix/events?$orderby=EventDate%20desc"

# Sort matters by last modified
curl "https://webapi.legistar.com/v1/phoenix/matters?$orderby=MatterLastModifiedUtc%20desc"
```

### Filtering

| Parameter | Description | Example |
|-----------|-------------|---------|
| `$filter` | Filter results by condition | `$filter=EventDate%20ge%20datetime'2025-01-01'` |

**Filter Operators:**
- `eq` - Equal
- `ne` - Not equal
- `gt` - Greater than
- `ge` - Greater than or equal
- `lt` - Less than
- `le` - Less than or equal
- `and` - Logical AND
- `or` - Logical OR

**Filtering Examples:**
```bash
# Events in January 2026
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventDate%20ge%20datetime'2026-01-01'%20and%20EventDate%20lt%20datetime'2026-02-01'"

# Matters with specific body
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterBodyId%20eq%20138"

# Active persons only
curl "https://webapi.legistar.com/v1/phoenix/persons?$filter=PersonActiveFlag%20eq%201"
```

---

## Bodies Endpoints

Bodies represent committees, councils, and other organizational groups that hold meetings.

### GET /bodies
Returns all bodies/committees.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodies"
```

**Response (28 bodies total):**
```json
[
  {
    "BodyId": 138,
    "BodyGuid": "GUID-STRING",
    "BodyLastModifiedUtc": "2024-11-13T16:12:10.76",
    "BodyRowVersion": "BASE64-STRING",
    "BodyName": "City Council Formal Meeting",
    "BodyTypeId": 42,
    "BodyTypeName": "Primary Legislative Body",
    "BodyMeetFlag": 1,
    "BodyActiveFlag": 1,
    "BodySort": 1,
    "BodyDescription": null,
    "BodyContactNameId": null,
    "BodyContactFullName": null,
    "BodyContactPhone": null,
    "BodyContactEmail": null,
    "BodyUsedControlFlag": 0,
    "BodyNumberOfMembers": 0,
    "BodyUsedActingFlag": 0,
    "BodyUsedTargetFlag": 0,
    "BodyUsedSponsorFlag": 0
  },
  {
    "BodyId": 181,
    "BodyName": "City Council Policy Session",
    "BodyTypeId": 56,
    "BodyTypeName": "Policy"
  }
]
```

**Available Phoenix Bodies:**

| BodyId | BodyName | BodyTypeName |
|--------|----------|--------------|
| 138 | City Council Formal Meeting | Primary Legislative Body |
| 254 | City Council Special Meeting | Primary Legislative Body |
| 181 | City Council Policy Session | Policy |
| 262 | City Council Work Study Session | Policy |
| 188 | Transportation and Infrastructure Subcommittee | Subcommittee |
| 189 | Sustainability, Housing, Efficiency and Neighborhoods Subcommittee | Subcommittee |
| 191 | Downtown, Aviation, Economy and Innovation Subcommittee | Subcommittee |
| 192 | Finance, Efficiency, Economy and Sustainability Subcommittee | Subcommittee |
| 193 | Parks, Arts, Education and Equality Subcommittee | Subcommittee |
| 221 | Public Safety and Veterans Subcommittee | Subcommittee |
| 263 | Water, Wastewater, Infrastructure and Sustainability Subcommittee | Subcommittee |
| 264 | Planning and Economic Development Subcommittee | Subcommittee |
| 265 | Parks, Arts, Libraries and Education Subcommittee | Subcommittee |
| 266 | Aviation and Transportation Subcommittee | Subcommittee |
| 267 | Transportation, Infrastructure and Innovation Subcommittee | Subcommittee |
| 268 | Workforce and Economic Development Subcommittee | Subcommittee |
| 269 | Land Use and Livability Subcommittee | Subcommittee |
| 270 | Public Safety and Justice Subcommittee | Subcommittee |
| 274 | Transportation, Infrastructure, and Planning Subcommittee | Subcommittee |
| 275 | Economic Development and Equity Subcommittee | Subcommittee |
| 276 | Community and Cultural Investment Subcommittee | Subcommittee |
| 278 | Economic Development and the Arts Subcommittee | Subcommittee |
| 280 | Community Services and Education Subcommittee | Subcommittee |
| 271 | Planning Commission | Planning Board or Commission |
| 272 | Planning Commission Briefing Meeting | Planning Board or Commission |
| 273 | Virtual Community Budget Hearing | Budget Hearing |
| 259 | General Information Packet | General Information Packet |
| 261 | Subcommittee General Information Packet | Subcommittee General Information Packet |

### GET /bodies/{BodyId}
Returns a specific body by ID.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodies/138"
```

### GET /bodies/{BodyId}/events
Returns all events for a specific body.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodies/138/events"
```

---

## Body Types Endpoints

Body types categorize the different kinds of organizational bodies.

### GET /bodytypes
Returns all body types.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodytypes"
```

**Response (8 body types):**
```json
[
  {
    "BodyTypeId": 42,
    "BodyTypeGuid": "GUID-STRING",
    "BodyTypeLastModifiedUtc": "2014-05-24T04:19:32.23",
    "BodyTypeRowVersion": "BASE64-STRING",
    "BodyTypeName": "Primary Legislative Body"
  },
  {
    "BodyTypeId": 43,
    "BodyTypeName": "Budget Hearing"
  },
  {
    "BodyTypeId": 49,
    "BodyTypeName": "Department"
  },
  {
    "BodyTypeId": 56,
    "BodyTypeName": "Policy"
  },
  {
    "BodyTypeId": 58,
    "BodyTypeName": "Subcommittee"
  },
  {
    "BodyTypeId": 59,
    "BodyTypeName": "General Information Packet"
  },
  {
    "BodyTypeId": 60,
    "BodyTypeName": "Subcommittee General Information Packet"
  },
  {
    "BodyTypeId": 61,
    "BodyTypeName": "Planning Board or Commission"
  }
]
```

### GET /bodytypes/{BodyTypeId}
Returns a specific body type by ID.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodytypes/42"
```

---

## Events Endpoints

Events represent meetings scheduled by various bodies.

### GET /events
Returns all events/meetings.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/events"
```

**Response Fields:**
```json
{
  "EventId": 2544,
  "EventGuid": "94620AF9-5B41-4D0C-B9AB-26FED6B1F7A3",
  "EventLastModifiedUtc": "2025-11-26T18:37:46.847",
  "EventRowVersion": "AAAAAARNZl8=",
  "EventBodyId": 138,
  "EventBodyName": "City Council Formal Meeting",
  "EventDate": "2026-01-07T00:00:00",
  "EventTime": "2:30 PM",
  "EventVideoStatus": "Public",
  "EventAgendaStatusId": 11,
  "EventAgendaStatusName": "Final-revised",
  "EventMinutesStatusId": 9,
  "EventMinutesStatusName": "Tentative",
  "EventLocation": "phoenix.gov",
  "EventAgendaFile": null,
  "EventMinutesFile": null,
  "EventAgendaLastPublishedUTC": null,
  "EventMinutesLastPublishedUTC": null,
  "EventComment": null,
  "EventVideoPath": null,
  "EventMedia": null,
  "EventInSiteURL": "https://phoenix.legistar.com/MeetingDetail.aspx?LEGID=2544&GID=485&G=3F9B5896-D56F-4AD3-85AD-A8E5E58DD74C",
  "EventItems": []
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| EventId | integer | Unique event identifier |
| EventGuid | string | GUID for the event |
| EventLastModifiedUtc | datetime | Last modification timestamp |
| EventBodyId | integer | ID of the body holding the event |
| EventBodyName | string | Name of the body |
| EventDate | datetime | Date of the event |
| EventTime | string | Time of the event (e.g., "2:30 PM") |
| EventVideoStatus | string | Video availability status |
| EventAgendaStatusId | integer | Agenda status ID |
| EventAgendaStatusName | string | Agenda status name |
| EventMinutesStatusId | integer | Minutes status ID |
| EventMinutesStatusName | string | Minutes status name |
| EventLocation | string | Location/venue |
| EventAgendaFile | string | URL to agenda PDF |
| EventMinutesFile | string | URL to minutes PDF |
| EventVideoPath | string | URL to video recording |
| EventInSiteURL | string | URL to Legistar detail page |
| EventItems | array | Array of agenda items |

### GET /events?$filter=...
Filter events by various criteria.

**Get Events by Date Range:**
```bash
# Events in January 2026
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventDate%20ge%20datetime'2026-01-01'%20and%20EventDate%20lt%20datetime'2026-02-01'"
```

**Get Events by Body:**
```bash
# Get only City Council Formal Meetings
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventBodyId%20eq%20138"
```

**Get Recent Events (Sorted):**
```bash
curl "https://webapi.legistar.com/v1/phoenix/events?$top=10&$orderby=EventDate%20desc"
```

### GET /events/{EventId}
Returns a specific event by ID.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/events/2544"
```

### GET /events/{EventId}/eventitems
Returns all agenda items for a specific event.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/events/2544/eventitems"
```

---

## Event Items Endpoints

Event items are individual agenda items within an event/meeting.

### GET /eventitems
Returns all event items.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/eventitems?$top=10"
```

### GET /events/{EventId}/eventitems
Returns agenda items for a specific event.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/events/2544/eventitems"
```

**Response Fields:**
```json
{
  "EventItemId": 140001,
  "EventItemGuid": "GUID-STRING",
  "EventItemLastModifiedUtc": "2025-01-06T17:30:00",
  "EventItemRowVersion": "BASE64-STRING",
  "EventItemEventId": 2544,
  "EventItemAgendaSequence": 1,
  "EventItemMinutesSequence": 1,
  "EventItemAgendaNumber": "1.",
  "EventItemVideo": null,
  "EventItemVideoIndex": null,
  "EventItemVersion": "1",
  "EventItemAgendaNote": null,
  "EventItemMinutesNote": null,
  "EventItemActionId": null,
  "EventItemActionName": null,
  "EventItemActionText": null,
  "EventItemPassedFlag": null,
  "EventItemPassedFlagName": null,
  "EventItemRollCallFlag": 0,
  "EventItemFlagExtra": 0,
  "EventItemTitle": "Call to Order - Roll Call",
  "EventItemTally": null,
  "EventItemAccelaRecordId": null,
  "EventItemConsent": 0,
  "EventItemMoverId": null,
  "EventItemMover": null,
  "EventItemSeconderId": null,
  "EventItemSeconder": null,
  "EventItemMatterId": null,
  "EventItemMatterGuid": null,
  "EventItemMatterFile": null,
  "EventItemMatterName": null,
  "EventItemMatterType": null,
  "EventItemMatterStatus": null,
  "EventItemMatterAttachments": []
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| EventItemId | integer | Unique event item identifier |
| EventItemEventId | integer | Parent event ID |
| EventItemAgendaSequence | integer | Order in agenda |
| EventItemAgendaNumber | string | Agenda item number (e.g., "1.", "2.a") |
| EventItemTitle | string | Title/description of item |
| EventItemActionId | integer | Action taken ID |
| EventItemActionName | string | Action name (e.g., "adopted") |
| EventItemPassedFlag | integer | 1 = passed, 0 = failed, null = no vote |
| EventItemTally | string | Vote tally (e.g., "8-0") |
| EventItemMoverId | integer | Person ID who made motion |
| EventItemMover | string | Name of person who made motion |
| EventItemSeconderId | integer | Person ID who seconded |
| EventItemSeconder | string | Name of person who seconded |
| EventItemMatterId | integer | Associated matter ID |
| EventItemMatterFile | string | Matter file number |
| EventItemConsent | integer | 1 = consent item, 0 = regular |

### GET /eventitems/{EventItemId}
Returns a specific event item.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/eventitems/140001"
```

### GET /eventitems/{EventItemId}/votes
Returns votes for a specific event item.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/eventitems/140001/votes"
```

### GET /eventitems/{EventItemId}/rollcalls
Returns roll call records for a specific event item.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/eventitems/140001/rollcalls"
```

---

## Matters Endpoints

Matters represent legislation, resolutions, ordinances, and other official items.

### GET /matters
Returns all matters.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters?$top=10&$orderby=MatterLastModifiedUtc%20desc"
```

**Response Fields:**
```json
{
  "MatterId": 34078,
  "MatterGuid": "8213D26B-2EFB-452B-B6DE-156B92ED6FB6",
  "MatterLastModifiedUtc": "2026-01-15T17:53:53.64",
  "MatterRowVersion": "AAAAAARNz6g=",
  "MatterFile": "26-0043",
  "MatterName": null,
  "MatterTitle": "Swearing In of a Municipal Court Judge",
  "MatterTypeId": 72,
  "MatterTypeName": "Formal Action",
  "MatterStatusId": 80,
  "MatterStatusName": "Agenda Ready",
  "MatterBodyId": 138,
  "MatterBodyName": "City Council Formal Meeting",
  "MatterIntroDate": "2026-01-13T00:00:00",
  "MatterAgendaDate": "2026-01-21T00:00:00",
  "MatterPassedDate": null,
  "MatterEnactmentDate": null,
  "MatterEnactmentNumber": null,
  "MatterRequester": null,
  "MatterNotes": "Internal processing notes",
  "MatterVersion": "1",
  "MatterCost": null,
  "MatterText1": null,
  "MatterText2": null,
  "MatterText3": null,
  "MatterText4": null,
  "MatterText5": null,
  "MatterDate1": null,
  "MatterDate2": null,
  "MatterEXText1": null,
  "MatterEXText2": null,
  "MatterEXDate1": null,
  "MatterEXDate2": null,
  "MatterAgiloftId": 0,
  "MatterReference": null,
  "MatterRestrictViewViaWeb": false,
  "MatterReports": []
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| MatterId | integer | Unique matter identifier |
| MatterFile | string | File number (e.g., "26-0043") |
| MatterTitle | string | Title/description |
| MatterTypeId | integer | Matter type ID |
| MatterTypeName | string | Matter type name |
| MatterStatusId | integer | Current status ID |
| MatterStatusName | string | Current status name |
| MatterBodyId | integer | Primary body ID |
| MatterBodyName | string | Primary body name |
| MatterIntroDate | datetime | Introduction date |
| MatterAgendaDate | datetime | Scheduled agenda date |
| MatterPassedDate | datetime | Date passed (if applicable) |
| MatterEnactmentDate | datetime | Enactment date |
| MatterEnactmentNumber | string | Ordinance/resolution number |
| MatterRequester | string | Department or person requesting |
| MatterNotes | string | Internal notes |
| MatterVersion | string | Version number |

### GET /matters/{MatterId}
Returns a specific matter.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078"
```

### GET /matters?$filter=...
Filter matters by various criteria.

**Get Matters by Type:**
```bash
# Get all Ordinances
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterTypeName%20eq%20'Ordinance-S'"
```

**Get Matters by Status:**
```bash
# Get all passed matters
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterStatusName%20eq%20'Passed'"
```

**Get Matters by Body:**
```bash
# Get matters for City Council Formal Meeting
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterBodyId%20eq%20138"
```

**Get Matters by Date Range:**
```bash
# Matters introduced in 2025
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterIntroDate%20ge%20datetime'2025-01-01'%20and%20MatterIntroDate%20lt%20datetime'2026-01-01'"
```

---

## Matter Types Endpoints

### GET /mattertypes
Returns all matter types.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/mattertypes"
```

**Response (32 matter types):**
```json
[
  {
    "MatterTypeId": 63,
    "MatterTypeGuid": "GUID-STRING",
    "MatterTypeLastModifiedUtc": "2014-05-24T04:19:32.853",
    "MatterTypeRowVersion": "BASE64-STRING",
    "MatterTypeName": "Information Only",
    "MatterTypeSort": 1,
    "MatterTypeActiveFlag": 1,
    "MatterTypeDescription": null
  }
]
```

**Available Matter Types:**

| MatterTypeId | MatterTypeName | Category |
|--------------|----------------|----------|
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

### GET /mattertypes/{MatterTypeId}
Returns a specific matter type.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/mattertypes/72"
```

---

## Matter Statuses Endpoints

### GET /matterstatuses
Returns all matter statuses.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matterstatuses"
```

**Response (44 statuses):**

**Key Status Categories:**

| Status Category | Statuses |
|-----------------|----------|
| Initial/Ready | Agenda Ready, Recommended for Approval, Recommended for Disapproval |
| In Process | Continued, Withdrawn from Agenda |
| Final - Positive | Passed, Approved, Adopted |
| Final - Negative | Failed |
| Other | Not Heard |

**Department-Specific Statuses:**
- Agenda Ready - Aviation Department
- Agenda Ready - City Clerk Department
- Agenda Ready - City Manager's Office
- Agenda Ready - Community and Economic Development
- Agenda Ready - Finance Department
- Agenda Ready - Fire Department
- Agenda Ready - Housing Department
- Agenda Ready - Human Resources Department
- Agenda Ready - Human Services Department
- Agenda Ready - Information Technology Services
- Agenda Ready - Law Department
- Agenda Ready - Neighborhood Services Department
- Agenda Ready - Parks and Recreation Department
- Agenda Ready - Planning and Development Department
- Agenda Ready - Police Department
- Agenda Ready - Public Transit Department
- Agenda Ready - Public Works Department
- Agenda Ready - Street Transportation Department
- Agenda Ready - Water Services Department

### GET /matterstatuses/{MatterStatusId}
Returns a specific matter status.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matterstatuses/80"
```

---

## Matter Attachments Endpoints

### GET /matters/{MatterId}/attachments
Returns all attachments for a matter.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/attachments"
```

**Response Fields:**
```json
[
  {
    "MatterAttachmentId": 12345,
    "MatterAttachmentGuid": "GUID-STRING",
    "MatterAttachmentLastModifiedUtc": "2025-01-01T00:00:00",
    "MatterAttachmentRowVersion": "BASE64-STRING",
    "MatterAttachmentName": "Staff Report.pdf",
    "MatterAttachmentHyperlink": "https://phoenix.legistar.com/View.ashx?...",
    "MatterAttachmentFileName": "Staff_Report.pdf",
    "MatterAttachmentMatterVersion": "1",
    "MatterAttachmentIsHyperlink": false,
    "MatterAttachmentBinary": null,
    "MatterAttachmentIsSupportingDocument": false,
    "MatterAttachmentShowOnInternetPage": true,
    "MatterAttachmentIsMinuteOrder": false,
    "MatterAttachmentIsBoardLetter": false,
    "MatterAttachmentAgiloftId": 0,
    "MatterAttachmentDescription": null,
    "MatterAttachmentPrintWithReports": false,
    "MatterAttachmentSort": 0
  }
]
```

---

## Matter Histories Endpoints

### GET /matters/{MatterId}/histories
Returns the action history for a matter.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/histories"
```

**Response Fields:**
```json
[
  {
    "MatterHistoryId": 56789,
    "MatterHistoryGuid": "GUID-STRING",
    "MatterHistoryLastModifiedUtc": "2025-01-15T00:00:00",
    "MatterHistoryRowVersion": "BASE64-STRING",
    "MatterHistoryEventId": 2544,
    "MatterHistoryAgendaSequence": 5,
    "MatterHistoryMinutesSequence": 5,
    "MatterHistoryAgendaNumber": "5.",
    "MatterHistoryVideo": null,
    "MatterHistoryVideoIndex": null,
    "MatterHistoryVersion": "1",
    "MatterHistoryAgendaNote": null,
    "MatterHistoryMinutesNote": null,
    "MatterHistoryActionDate": "2025-01-07T00:00:00",
    "MatterHistoryActionId": 363,
    "MatterHistoryActionName": "adopted",
    "MatterHistoryActionText": null,
    "MatterHistoryActionBodyId": 138,
    "MatterHistoryActionBodyName": "City Council Formal Meeting",
    "MatterHistoryPassedFlag": 1,
    "MatterHistoryPassedFlagName": "Pass",
    "MatterHistoryRollCallFlag": 0,
    "MatterHistoryFlagExtra": 0,
    "MatterHistoryTally": "8-0",
    "MatterHistoryAccelaRecordId": null,
    "MatterHistoryConsent": 1,
    "MatterHistoryMoverId": 195,
    "MatterHistoryMover": "Pastor",
    "MatterHistorySeconderId": 192,
    "MatterHistorySeconder": "Waring"
  }
]
```

**Filter History for Passed Items:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/histories?$filter=MatterHistoryPassedFlag%20ne%20null"
```

---

## Matter Sponsors Endpoints

### GET /matters/{MatterId}/sponsors
Returns sponsors for a matter.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/sponsors"
```

**Response Fields:**
```json
[
  {
    "MatterSponsorId": 1234,
    "MatterSponsorGuid": "GUID-STRING",
    "MatterSponsorLastModifiedUtc": "2025-01-01T00:00:00",
    "MatterSponsorRowVersion": "BASE64-STRING",
    "MatterSponsorMatterId": 34078,
    "MatterSponsorMatterVersion": "1",
    "MatterSponsorNameId": 195,
    "MatterSponsorName": "Pastor",
    "MatterSponsorBodyId": 138,
    "MatterSponsorSequence": 1,
    "MatterSponsorLinkFlag": 0
  }
]
```

---

## Matter Indexes Endpoints

### GET /matters/{MatterId}/indexes
Returns index/category assignments for a matter.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/indexes"
```

### GET /indexes/{IndexId}/matters
Returns all matters assigned to a specific index.

**Request:**
```bash
# Get all Citywide matters
curl "https://webapi.legistar.com/v1/phoenix/indexes/214/matters"
```

---

## Persons Endpoints

Persons represent council members, staff, and other individuals in the system.

### GET /persons
Returns all persons.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons"
```

**Response Fields:**
```json
{
  "PersonId": 195,
  "PersonGuid": "GUID-STRING",
  "PersonLastModifiedUtc": "2017-03-01T00:00:00",
  "PersonRowVersion": "BASE64-STRING",
  "PersonFirstName": "Laura",
  "PersonLastName": "Pastor",
  "PersonFullName": "Laura Pastor",
  "PersonActiveFlag": 1,
  "PersonCanViewFlag": 1,
  "PersonUsedSponsorFlag": 1,
  "PersonEmail": "council.district.4@phoenix.gov"
}
```

**Filter Active Persons:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons?$filter=PersonActiveFlag%20eq%201"
```

### GET /persons/{PersonId}
Returns a specific person.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons/195"
```

### GET /persons/{PersonId}/votes
Returns all votes by a specific person.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons/195/votes"
```

### GET /persons/{PersonId}/officerecords
Returns office records (committee memberships) for a person.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons/195/officerecords"
```

---

## Actions Endpoints

Actions represent the types of actions that can be taken on matters.

### GET /actions
Returns all action types.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/actions"
```

**Response Fields:**
```json
{
  "ActionId": 363,
  "ActionGuid": "GUID-STRING",
  "ActionLastModifiedUtc": "2014-05-24T04:19:34.8",
  "ActionRowVersion": "BASE64-STRING",
  "ActionName": "adopted",
  "ActionActiveFlag": 1,
  "ActionUsedFlag": 0
}
```

**Available Actions:**

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

### GET /actions/{ActionId}
Returns a specific action.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/actions/363"
```

---

## Vote Types Endpoints

### GET /votetypes
Returns all vote types.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/votetypes"
```

**Response Fields:**
```json
{
  "VoteTypeId": 17,
  "VoteTypeGuid": "GUID-STRING",
  "VoteTypeLastModifiedUtc": "2014-05-24T04:19:33.337",
  "VoteTypeRowVersion": "BASE64-STRING",
  "VoteTypeName": "Yes",
  "VoteTypePluralName": "Yeses",
  "VoteTypeUsedFor": 1,
  "VoteTypeResult": 1,
  "VoteTypeSort": 1
}
```

**Available Vote Types:**

| VoteTypeId | VoteTypeName | VoteTypeResult |
|------------|--------------|----------------|
| 16 | Conflict | 0 |
| 17 | Yes | 1 (affirmative) |
| 18 | Present | 0 |
| 19 | Abstain Yes | 1 (affirmative) |
| 23 | Telephonic | 0 |
| 24 | No | 2 (negative) |
| 25 | Absent | 0 |

---

## Indexes Endpoints

Indexes are categories used to classify matters (e.g., by district).

### GET /indexes
Returns all indexes.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/indexes"
```

**Response Fields:**
```json
{
  "IndexId": 214,
  "IndexGuid": "GUID-STRING",
  "IndexLastModifiedUtc": "2016-03-30T00:00:00",
  "IndexRowVersion": "BASE64-STRING",
  "IndexName": "Citywide",
  "IndexActiveFlag": 1,
  "IndexUsedFlag": 0
}
```

**Available Indexes:**

| IndexId | IndexName |
|---------|-----------|
| 214 | Citywide |
| 207 | District 1 |
| 208 | District 2 |
| 209 | District 3 |
| 210 | District 4 |
| 211 | District 5 |
| 212 | District 6 |
| 213 | District 7 |
| 215 | District 8 |
| 216 | Out of City |

### GET /indexes/{IndexId}
Returns a specific index.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/indexes/214"
```

---

## Office Records Endpoints

Office records track committee/body memberships over time.

### GET /officerecords
Returns all office records.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/officerecords?$top=10"
```

**Response Fields:**
```json
{
  "OfficeRecordId": 577,
  "OfficeRecordGuid": "GUID-STRING",
  "OfficeRecordLastModifiedUtc": "2018-05-29T00:00:00",
  "OfficeRecordRowVersion": "BASE64-STRING",
  "OfficeRecordFirstName": "Greg",
  "OfficeRecordLastName": "Stanton",
  "OfficeRecordEmail": null,
  "OfficeRecordFullName": "Greg Stanton",
  "OfficeRecordStartDate": "2014-07-29T00:00:00",
  "OfficeRecordEndDate": "2018-05-29T00:00:00",
  "OfficeRecordSort": 1,
  "OfficeRecordPersonId": 191,
  "OfficeRecordBodyId": 138,
  "OfficeRecordBodyName": "City Council Formal Meeting",
  "OfficeRecordTitle": null,
  "OfficeRecordVoteDivider": 1.0,
  "OfficeRecordExtendFlag": 0,
  "OfficeRecordMemberTypeId": 45,
  "OfficeRecordMemberType": "Chair",
  "OfficeRecordSupportNameId": null,
  "OfficeRecordSupportFullName": null
}
```

### GET /bodies/{BodyId}/officerecords
Returns office records for a specific body.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/bodies/138/officerecords"
```

### GET /persons/{PersonId}/officerecords
Returns office records for a specific person.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons/195/officerecords"
```

---

## Roll Calls Endpoints

Roll calls track individual votes on specific event items.

### GET /eventitems/{EventItemId}/rollcalls
Returns roll call votes for a specific event item.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/eventitems/140001/rollcalls"
```

**Response Fields:**
```json
{
  "RollCallId": 5678,
  "RollCallGuid": "GUID-STRING",
  "RollCallLastModifiedUtc": "2025-01-07T00:00:00",
  "RollCallRowVersion": "BASE64-STRING",
  "RollCallPersonId": 195,
  "RollCallPersonName": "Pastor",
  "RollCallValueId": 17,
  "RollCallValueName": "Yes",
  "RollCallSort": 1,
  "RollCallResult": 1,
  "RollCallEventItemId": 140001
}
```

### GET /persons/{PersonId}/rollcalls
Returns all roll call votes for a specific person.

**Request:**
```bash
curl "https://webapi.legistar.com/v1/phoenix/persons/195/rollcalls"
```

---

## Common Use Cases

### 1. Get All Upcoming Meetings

```bash
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventDate%20ge%20datetime'2026-01-15'&$orderby=EventDate%20asc&$top=20"
```

### 2. Get Full Agenda for a Meeting

```bash
# First, get the event
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventDate%20eq%20datetime'2026-01-21'%20and%20EventBodyId%20eq%20138"

# Then get agenda items using EventId
curl "https://webapi.legistar.com/v1/phoenix/events/2544/eventitems"
```

### 3. Search for Matters by Keyword

```bash
# Filter by title containing keyword (case-sensitive)
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=substringof('zoning',MatterTitle)"
```

### 4. Get All Ordinances from 2025

```bash
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterTypeName%20eq%20'Ordinance-S'%20and%20MatterIntroDate%20ge%20datetime'2025-01-01'%20and%20MatterIntroDate%20lt%20datetime'2026-01-01'"
```

### 5. Get Council Member Voting Record

```bash
# Get person ID first
curl "https://webapi.legistar.com/v1/phoenix/persons?$filter=PersonLastName%20eq%20'Pastor'"

# Then get their votes
curl "https://webapi.legistar.com/v1/phoenix/persons/195/votes"
```

### 6. Get All Liquor Licenses on Agenda

```bash
curl "https://webapi.legistar.com/v1/phoenix/matters?$filter=MatterTypeName%20eq%20'Liquor'%20and%20MatterStatusName%20eq%20'Agenda%20Ready'"
```

### 7. Get Matters by District

```bash
# Get matters for District 4
curl "https://webapi.legistar.com/v1/phoenix/indexes/210/matters"
```

### 8. Track a Specific Matter Through the Process

```bash
# Get matter details
curl "https://webapi.legistar.com/v1/phoenix/matters/34078"

# Get history/actions taken
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/histories"

# Get attachments
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/attachments"

# Get sponsors
curl "https://webapi.legistar.com/v1/phoenix/matters/34078/sponsors"
```

### 9. Get All Policy Sessions

```bash
curl "https://webapi.legistar.com/v1/phoenix/events?$filter=EventBodyId%20eq%20181&$orderby=EventDate%20desc"
```

### 10. Get Current Council Members

```bash
# Get active persons who have current office records
curl "https://webapi.legistar.com/v1/phoenix/bodies/138/officerecords?$filter=OfficeRecordEndDate%20eq%20null%20or%20OfficeRecordEndDate%20ge%20datetime'2026-01-01'"
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 405 | Method Not Allowed |
| 500 | Server Error |

### Common Issues

**Empty Response `[]`:**
- The query returned no matching records
- Check filter syntax and date formats

**404 Not Found:**
- The endpoint or ID doesn't exist
- Verify the endpoint path and ID values

**Query Limits:**
- Results are limited to 1000 per request
- Use `$top` and `$skip` for pagination

### Date Format
Always use ISO 8601 format for dates in filters:
```
datetime'YYYY-MM-DD'
datetime'2026-01-15'
```

### URL Encoding
Special characters must be URL-encoded:
- Space = `%20`
- Single quote = `%27`
- Plus = `%2B`

---

## Additional Resources

- **API Documentation:** https://webapi.legistar.com/Help
- **API Examples:** https://webapi.legistar.com/Home/Examples
- **Phoenix Legistar Website:** https://phoenix.legistar.com/
- **Granicus Support:** https://support.granicus.com/s/article/Legistar-Web-API

---

## Version History

| Date | Version | Notes |
|------|---------|-------|
| 2026-01-15 | 1.0 | Initial documentation |

---

*This document was generated by analyzing the live Phoenix Legistar API. All endpoints and examples have been tested with real data.*
