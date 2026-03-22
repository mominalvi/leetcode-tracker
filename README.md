# leetcode-tracker

A personal CLI tool for tracking LeetCode problems and scheduling reviews using spaced repetition. Local-only, no dependencies, JSON-backed.

## How it works

When you solve a problem, you add it. The tool schedules review sessions at increasing intervals (2 → 7 → 14 → 30 days) based on how well you did each time. A daily macOS notification reminds you when problems are due.

## Commands

```
python3 leet.py add       # Log a newly solved problem
python3 leet.py today     # See what's due today
python3 leet.py review    # Work through due problems one by one
python3 leet.py list      # See all tracked problems
python3 leet.py notify    # Fire a macOS notification if anything is due (used by launchd)
```

## Review outcomes

| Outcome | What it means | Next review |
|---|---|---|
| `easy` | Solved confidently | Stage advances, +7–30 days |
| `struggled` | Got it but shaky | Stage unchanged, +3 days |
| `failed` | Couldn't solve it | Reset to stage 0, +1 day |

## Setup

No install needed. Just run the commands above. Data is stored in `~/.leetcode-tracker/problems.json`.

### Daily reminders (macOS)

A `launchd` agent fires `leet notify` every morning at 9am — or on next wake if your Mac was asleep. To set it up:

1. Copy `leet.py` to `~/.leetcode-tracker/leet.py`
2. Copy `com.mominalvi.leetcode-notify.plist` to `~/Library/LaunchAgents/`
3. Run: `launchctl load ~/Library/LaunchAgents/com.mominalvi.leetcode-notify.plist`
