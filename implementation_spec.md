# LeetCode Spaced Repetition CLI — Final v1 Spec

## Overview

Personal CLI tool that tracks solved LeetCode problems and schedules reviews using fixed spaced repetition intervals. Single-user, local-only, JSON-backed. Standard library only.

---

## Storage

- **Path:** `~/.leetcode-tracker/problems.json`
- **Format:** JSON array of problem objects
- **Auto-created** on first `add` if directory/file doesn't exist
- **Dates:** `YYYY-MM-DD` strings, local time

---

## Problem Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | **Unique key** — case-insensitive dedup, stored as entered |
| `pattern` | string | yes | Auto-lowercased and stripped |
| `date_solved` | string | yes | `YYYY-MM-DD`, defaults to today |
| `next_review` | string | yes | Computed automatically |
| `review_stage` | int | yes | `0–3`, starts at `0` |
| `difficulty` | string | no | e.g., "easy", "medium", "hard" |
| `url` | string | no | LeetCode problem URL |
| `notes` | string | no | Personal notes |

---

## Review Logic

### Intervals

| Stage | Interval |
|---|---|
| 0 | 2 days |
| 1 | 7 days |
| 2 | 14 days |
| 3 | 30 days |

### Outcomes

| Outcome | Definition | Stage Change | Next Review |
|---|---|---|---|
| `easy` | Could solve again with confidence | `min(stage + 1, 3)` | `today + intervals[new_stage]` |
| `struggled` | Got it eventually, but shaky/slow/needed hints | unchanged | `today + 3 days` |
| `failed` | Could not solve without the answer | reset to `0` | `today + 1 day` |

Stage 3 + easy = stays at stage 3, next review in 30 days (cycles indefinitely).

---

## Commands

### `add`

Interactive prompts:

```
  Add a new problem

  Title: Two Sum
  Pattern: hash map
  Difficulty (optional): easy
  URL (optional): https://leetcode.com/problems/two-sum
  Notes (optional):

  ✓ Added "Two Sum" — first review on 2026-03-23
```

- Title is required — error with message if duplicate (case-insensitive)
- Pattern is required — auto-lowercased, stripped
- Optional fields skip on empty Enter
- `date_solved` = today (no prompt)
- `review_stage` = 0, `next_review` = today + 2 days

### `today`

Shows due problems (`next_review <= today`), sorted by `next_review` ascending:

```
  Due today (3 problems)

  1. Two Sum
     hash map · stage 0 · due today

  2. Valid Anagram
     hash map · stage 1 · 2 days overdue

  3. Merge Intervals
     intervals · stage 2 · due today

  Run `leet review` to start reviewing.
```

Empty state:

```
  Nothing due today. You're all caught up.
```

### `review`

Cycles through due problems one at a time. For each:

```
  Review (1 of 3)

  Two Sum
  Pattern: hash map · Stage: 0 · Difficulty: easy
  URL: https://leetcode.com/problems/two-sum

  How did it go? (easy / struggled / failed / quit)
  > easy

  ✓ Stage 0 → 1 · Next review: 2026-03-28
```

- Prompts for `easy`, `struggled`, `failed`, or `quit`
- Invalid input re-prompts (no crash)
- `quit` stops the session, unreviewed problems stay due
- **Saves to JSON after each review** (safe against Ctrl+C)
- End of session:

```
  Session complete. Reviewed 3 of 3 problems.
```

Or if quit early:

```
  Session paused. Reviewed 1 of 3 problems.
  Remaining problems are still due.
```

No problems due:

```
  Nothing to review. All caught up.
```

### `list`

Shows all tracked problems, sorted by `next_review` ascending:

```
  All problems (5 tracked)

  Title              Pattern       Stage  Next Review  Difficulty
  ─────────────────────────────────────────────────────────────────
  Two Sum            hash map      1      2026-03-28   easy
  Valid Anagram      hash map      0      2026-03-22   easy
  Merge Intervals    intervals     2      2026-04-04   medium
  3Sum               two pointers  3      2026-04-20   medium
  LRU Cache          design        0      2026-03-23   hard
```

Empty state:

```
  No problems tracked yet. Run `leet add` to get started.
```

---

## CLI Entry Point

Single script: `leet.py`

```
python leet.py add
python leet.py today
python leet.py review
python leet.py list
```

Uses `argparse` with subcommands. No external dependencies — standard library only (`argparse`, `json`, `datetime`, `os`, `pathlib`).

---

## CLI UX Principles

- **Clean spacing:** One blank line between logical sections, no walls of text
- **Minimal chrome:** Use `✓` for confirmations, `·` as a light separator, `─` for table rules — nothing heavier
- **Readable prompts:** Clear labels, one question at a time, obvious defaults
- **Consistent structure:** Every command prints a header, content, then optional footer/hint
- **Friendly empty states:** Never crash or print nothing — always a short, helpful message
- **No color dependencies:** Output should be readable without color support; color is a nice-to-have enhancement (e.g., ANSI codes for stage or outcome), not a requirement
- **No clutter:** No version banners, no ASCII art, no verbose logging

---

## Edge Cases

| Case | Behavior |
|---|---|
| Duplicate title on `add` | Error: `"Two Sum" already exists.` |
| `struggled` at stage 0 | Stage stays 0, review in 3 days |
| `failed` at stage 0 | Stage stays 0, review in 1 day |
| `easy` at stage 3 | Stage stays 3, review in 30 days |
| Empty problem list | Friendly message per command |
| Missing JSON file | Created on first `add`; other commands say "no problems yet" |
| Ctrl+C during `review` | Already-saved reviews persist; current problem unchanged |
| Invalid review input | Re-prompt, don't crash |

---

## Explicitly NOT in v1

- No `weak` command (defer; can add `--pattern` filter to `list` later)
- No `review_history` tracking
- No `status` field
- No `delete` / `edit` commands (edit JSON by hand)
- No email notifications
- No external dependencies or database
- No TUI framework / curses
- No tests (optional, your call)
