# Claude Usage Guide: Effective Prompting Patterns

This guide documents efficient ways to interact with Claude based on lessons learned from this project.

---

## Table of Contents

1. [TodoWrite Tool - Task Tracking](#1-todowrite-tool---task-tracking)
2. [Task Tool - Subagents for Exploration](#2-task-tool---subagents-for-exploration)
3. [Parallel Tool Calls](#3-parallel-tool-calls)
4. [AskUserQuestion Tool - Structured Decisions](#4-askuserquestion-tool---structured-decisions)
5. [EnterPlanMode - Design & Architecture](#5-enterplanmode---design--architecture)
6. [Batch Operations](#6-batch-operations)
7. [Efficient Data Entry](#7-efficient-data-entry)

---

## 1. TodoWrite Tool - Task Tracking

**Purpose:** Track multi-step tasks, show progress, prevent missed steps.

### When to Use
- Tasks with 3+ distinct steps
- Long-running operations
- Projects spanning multiple conversation turns

### Example Prompts

**❌ Inefficient (no tracking):**
```
Run the Q1 2020 data collection
```

**✅ Efficient (with task breakdown):**
```
Run Q1 2020 data collection. Track these steps:
1. Fetch events from API
2. Create 2020-specific script with correct roster
3. Run scraper for all Q1 meetings
4. Verify output CSV structure
5. Add video URLs when I provide them
6. Final validation
```

**Another Example:**

**❌ Inefficient:**
```
Set up the database
```

**✅ Efficient:**
```
Set up the database with these tracked steps:
1. Create schema SQL file
2. Create council_members reference data
3. Create import script
4. Test with Q1 2024 data
5. Validate row counts
```

### What You'll See

Claude will create a todo list and update it as work progresses:
```
☐ Fetch events from API
☐ Create 2020-specific script
☐ Run scraper
...
```

Then as work proceeds:
```
✓ Fetch events from API (6 events found)
● Create 2020-specific script (in progress)
☐ Run scraper
...
```

---

## 2. Task Tool - Subagents for Exploration

**Purpose:** Delegate research and exploration to specialized agents.

### When to Use
- Searching codebase for patterns
- Exploring unfamiliar code
- Research that might require multiple searches

### Example Prompts

**❌ Inefficient (manual searching):**
```
Search for where council member names are defined
```
(May require multiple Grep/Glob calls back and forth)

**✅ Efficient (delegate to Explore agent):**
```
Use the Explore agent to find all places where council member names
are defined or mapped across the codebase. Look for:
- Name arrays/lists
- Name mappings between API and display format
- Any year-specific roster definitions
```

**Another Example:**

**❌ Inefficient:**
```
How does the video URL scraping work?
```

**✅ Efficient:**
```
Use the Explore agent to analyze how video URL scraping works:
- Find all Phoenix.gov scraping code
- Identify the YouTube URL extraction logic
- Document the date matching approach
- Note any error handling patterns
```

### Explore Agent Use Cases

| Task | Prompt Pattern |
|------|----------------|
| Find implementations | "Use Explore agent to find all implementations of X" |
| Understand flow | "Use Explore agent to trace the data flow from X to Y" |
| Find patterns | "Use Explore agent to find all error handling patterns" |
| Compare approaches | "Use Explore agent to compare how 2020 vs 2024 scripts handle X" |

---

## 3. Parallel Tool Calls

**Purpose:** Execute independent operations simultaneously.

### When to Use
- Multiple file reads
- Multiple independent searches
- Multiple data updates that don't depend on each other

### Example Prompts

**❌ Inefficient (sequential):**
```
Read the 2020 script
```
(wait)
```
Now read the 2024 script
```
(wait)
```
Now compare them
```

**✅ Efficient (parallel):**
```
Read both fetch_2020_data_enhanced.py and fetch_2024_data_enhanced.py
in parallel, then compare the council member rosters.
```

**Another Example:**

**❌ Inefficient:**
```
Check if Q1 2020 CSV exists
```
(wait)
```
Check if Q1 2024 CSV exists
```

**✅ Efficient:**
```
Check in parallel:
1. Does phoenix_council_2020_Q1_enhanced.csv exist?
2. Does phoenix_council_2024_Q1_enhanced.csv exist?
3. What are the row counts for each?
```

**Explicit Parallel Request:**
```
Run these searches IN PARALLEL:
- Grep for "COUNCIL_MEMBERS" in all Python files
- Grep for "NAME_MAPPING" in all Python files
- Glob for all *_enhanced.py files
```

---

## 4. AskUserQuestion Tool - Structured Decisions

**Purpose:** Get clear answers to ambiguous situations with structured options.

### When Claude Should Use This
- Ambiguous requirements
- Multiple valid approaches
- Confirming assumptions

### Example Situations

**Situation: Ambiguous video URL assignment**

Instead of Claude asking in plain text:
> "The video Or3bGzmned4 is currently assigned to Jan 29. Should I move it to Feb 5?"

Claude should use AskUserQuestion:
```
Question: "Which date should have video Or3bGzmned4?"
Options:
- January 29, 2020 (currently assigned)
- February 5, 2020 (you mentioned)
- Other date
```

**Situation: Schema design choice**

Instead of Claude guessing:
> "I'll use SQLite for the database."

Claude should ask:
```
Question: "Which database should I use?"
Options:
- SQLite (simple, single file, good for <1M rows)
- PostgreSQL (robust, better for production)
- Keep as CSV files (no database)
```

### How to Request This Behavior

```
When you have questions about my preferences, use the structured
question tool instead of asking in plain text. Give me clear options
to choose from.
```

---

## 5. EnterPlanMode - Design & Architecture

**Purpose:** Plan complex implementations before writing code.

### When to Use
- Database schema design
- New feature implementation
- Refactoring existing code
- Any task with architectural decisions

### Example Prompts

**❌ Inefficient (jump straight to implementation):**
```
Create the database schema
```

**✅ Efficient (plan first):**
```
Enter plan mode to design the database schema. Consider:
- What queries will the website need?
- How to handle council member roster changes over time?
- What should be normalized vs denormalized?
- Present 2-3 schema options before implementing
```

**Another Example:**

**❌ Inefficient:**
```
Create the incremental update script
```

**✅ Efficient:**
```
Enter plan mode to design the incremental update script:
1. Review existing backlog script structure
2. Identify what changes for incremental mode
3. Determine how to detect new/changed meetings
4. Plan the merge strategy for existing CSV
5. Present the approach for approval before coding
```

### Plan Mode Benefits

| Benefit | Description |
|---------|-------------|
| Exploration first | Claude reads relevant files before designing |
| Options presented | You see alternatives before commitment |
| Approval required | Nothing written until you approve |
| Context gathered | Questions asked upfront, not during implementation |

---

## 6. Batch Operations

**Purpose:** Reduce round-trips by combining related operations.

### When to Use
- Adding multiple similar items
- Making same change to multiple files
- Running multiple validations

### Example Prompts

**❌ Inefficient (one at a time):**
```
Add video for Jan 8: https://youtu.be/1YQ40-SUAXE
```
(wait)
```
Add video for Jan 29: https://youtu.be/Or3bGzmned4
```
(wait)
```
Add video for Feb 5: https://youtu.be/A7yAWlsPiLA
```

**✅ Efficient (batch):**
```
Add all these videos to phoenix_council_2020_Q1_enhanced.csv:

| Date | Video URL |
|------|-----------|
| 2020-01-08 | https://youtu.be/1YQ40-SUAXE |
| 2020-01-29 | https://youtu.be/Or3bGzmned4 |
| 2020-02-05 | https://youtu.be/A7yAWlsPiLA |
| 2020-03-04 | https://youtu.be/J5EpAHk3DQM |
| 2020-03-18 | https://youtu.be/xfxH1qk6XHQ |

Update all in a single operation, then show summary.
```

**Another Batch Example:**

**❌ Inefficient:**
```
Check row count for Q1 2020
```
(wait)
```
Check row count for Q1 2024
```
(wait)
```
Check video coverage for both
```

**✅ Efficient:**
```
For both Q1 2020 and Q1 2024 CSVs, show in a single summary:
- Total row count
- Number of meetings
- Video coverage (rows with video / total)
- Column count
```

---

## 7. Efficient Data Entry

**Purpose:** Provide data in formats that enable single-pass processing.

### Structured Data Entry

**❌ Hard to parse:**
```
jan 8 2020 is 1YQ40-SUAXE and then jan 29 has Or3bGzmned4,
oh and feb 5 is A7yAWlsPiLA
```

**✅ Easy to parse (table format):**
```
| Date | Video ID |
|------|----------|
| 2020-01-08 | 1YQ40-SUAXE |
| 2020-01-29 | Or3bGzmned4 |
| 2020-02-05 | A7yAWlsPiLA |
```

**✅ Easy to parse (key-value format):**
```
2020-01-08: https://youtu.be/1YQ40-SUAXE
2020-01-29: https://youtu.be/Or3bGzmned4
2020-02-05: https://youtu.be/A7yAWlsPiLA
```

**✅ Easy to parse (JSON format):**
```json
{
  "2020-01-08": "https://youtu.be/1YQ40-SUAXE",
  "2020-01-29": "https://youtu.be/Or3bGzmned4",
  "2020-02-05": "https://youtu.be/A7yAWlsPiLA"
}
```

### Corrections and Updates

**❌ Ambiguous:**
```
Actually the feb 5 one is wrong
```

**✅ Clear:**
```
Correction: 2020-02-05 video should be A7yAWlsPiLA (not Or3bGzmned4)
```

**✅ Even better (with context):**
```
Correction needed:
- Current: 2020-02-05 has Or3bGzmned4
- Should be: 2020-02-05 should have A7yAWlsPiLA
- Note: Or3bGzmned4 belongs to 2020-01-29
```

---

## Quick Reference Card

### Starting a Session

```
I'm working on [PROJECT]. Today I need to:
1. [Task 1]
2. [Task 2]
3. [Task 3]

Use TodoWrite to track progress. Ask structured questions when
you need clarification. Use Explore agent for codebase research.
```

### Providing Batch Data

```
Here's the data to add (process all at once):

| Column1 | Column2 | Column3 |
|---------|---------|---------|
| value1  | value2  | value3  |
| value4  | value5  | value6  |
```

### Requesting Planning

```
Enter plan mode for [TASK]. Before implementing:
1. Explore relevant existing code
2. Identify key decisions needed
3. Present options for my approval
```

### Requesting Parallel Operations

```
Run IN PARALLEL:
- [Operation 1]
- [Operation 2]
- [Operation 3]
```

### Requesting Structured Questions

```
When you need my input on choices, use AskUserQuestion with
clear options rather than open-ended questions.
```

---

## Summary: Prompt Patterns

| Goal | Pattern |
|------|---------|
| Track multi-step work | "Track these steps: 1. X 2. Y 3. Z" |
| Explore codebase | "Use Explore agent to find/analyze X" |
| Multiple operations | "Run IN PARALLEL: X, Y, Z" |
| Get structured input | Claude uses AskUserQuestion tool |
| Plan before building | "Enter plan mode for X" |
| Batch data entry | Provide as table or key-value list |
| Clear corrections | "Correction: [current] should be [new]" |

---

## Checklist Before Starting Complex Tasks

- [ ] Have I broken the task into trackable steps?
- [ ] Can any research be delegated to Explore agent?
- [ ] Is there batch data I can provide all at once?
- [ ] Should Claude plan before implementing?
- [ ] Have I specified preferences that would otherwise require questions?
