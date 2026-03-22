#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path


# --- Storage ---

DATA_DIR = Path.home() / ".leetcode-tracker"
DATA_FILE = DATA_DIR / "problems.json"

INTERVALS = {0: 2, 1: 7, 2: 14, 3: 30}


def load_problems():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save_problems(problems):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(problems, f, indent=2)


# --- Review logic ---

def next_review_date(stage):
    return (date.today() + timedelta(days=INTERVALS[stage])).isoformat()


def apply_outcome(problem, outcome):
    today = date.today()
    stage = problem["review_stage"]

    if outcome == "easy":
        new_stage = min(stage + 1, 3)
        problem["review_stage"] = new_stage
        problem["next_review"] = (today + timedelta(days=INTERVALS[new_stage])).isoformat()
        return f"Stage {stage} → {new_stage} · Next review: {problem['next_review']}"

    elif outcome == "struggled":
        problem["next_review"] = (today + timedelta(days=3)).isoformat()
        return f"Stage unchanged ({stage}) · Next review: {problem['next_review']}"

    elif outcome == "failed":
        problem["review_stage"] = 0
        problem["next_review"] = (today + timedelta(days=1)).isoformat()
        return f"Stage reset to 0 · Next review: {problem['next_review']}"


# --- Commands ---

def cmd_add(args):
    problems = load_problems()
    existing_titles = {p["title"].lower() for p in problems}

    print()
    print("  Add a new problem")
    print()

    title = input("  Title: ").strip()
    if not title:
        print("\n  Title is required.")
        return
    if title.lower() in existing_titles:
        print(f'\n  "{title}" already exists.')
        return

    pattern = input("  Pattern: ").strip().lower()
    if not pattern:
        print("\n  Pattern is required.")
        return

    difficulty = input("  Difficulty (optional): ").strip().lower() or None
    url = input("  URL (optional): ").strip() or None
    notes = input("  Notes (optional): ").strip() or None

    today = date.today().isoformat()
    review_date = (date.today() + timedelta(days=INTERVALS[0])).isoformat()

    problem = {
        "title": title,
        "pattern": pattern,
        "date_solved": today,
        "next_review": review_date,
        "review_stage": 0,
    }
    if difficulty:
        problem["difficulty"] = difficulty
    if url:
        problem["url"] = url
    if notes:
        problem["notes"] = notes

    problems.append(problem)
    save_problems(problems)

    print(f'\n  ✓ Added "{title}" — first review on {review_date}')
    print()


def cmd_today(args):
    problems = load_problems()
    today = date.today()

    due = [p for p in problems if date.fromisoformat(p["next_review"]) <= today]
    due.sort(key=lambda p: p["next_review"])

    print()

    if not due:
        print("  Nothing due today. You're all caught up.")
        print()
        return

    print(f"  Due today ({len(due)} problem{'s' if len(due) != 1 else ''})")

    for i, p in enumerate(due, 1):
        days_overdue = (today - date.fromisoformat(p["next_review"])).days
        if days_overdue == 0:
            due_str = "due today"
        elif days_overdue == 1:
            due_str = "1 day overdue"
        else:
            due_str = f"{days_overdue} days overdue"

        print()
        print(f"  {i}. {p['title']}")
        print(f"     {p['pattern']} · stage {p['review_stage']} · {due_str}")

    print()
    print("  Run `leet review` to start reviewing.")
    print()


def cmd_review(args):
    problems = load_problems()
    today = date.today()

    due = [p for p in problems if date.fromisoformat(p["next_review"]) <= today]
    due.sort(key=lambda p: p["next_review"])

    print()

    if not due:
        print("  Nothing to review. All caught up.")
        print()
        return

    total = len(due)
    reviewed = 0

    for i, problem in enumerate(due, 1):
        print(f"  Review ({i} of {total})")
        print()
        print(f"  {problem['title']}")

        meta_parts = [problem["pattern"], f"Stage: {problem['review_stage']}"]
        if "difficulty" in problem:
            meta_parts.append(f"Difficulty: {problem['difficulty']}")
        print(f"  Pattern: {' · '.join(meta_parts)}")

        if "url" in problem:
            print(f"  URL: {problem['url']}")
        if "notes" in problem:
            print(f"  Notes: {problem['notes']}")

        print()

        while True:
            outcome = input("  How did it go? (easy / struggled / failed / quit)\n  > ").strip().lower()
            if outcome in ("easy", "struggled", "failed", "quit"):
                break
            print("  Please enter easy, struggled, failed, or quit.")

        if outcome == "quit":
            print()
            print(f"  Session paused. Reviewed {reviewed} of {total} problems.")
            print("  Remaining problems are still due.")
            print()
            return

        result_msg = apply_outcome(problem, outcome)

        # Find and update the problem in the full list, then save immediately
        for p in problems:
            if p["title"] == problem["title"]:
                p["review_stage"] = problem["review_stage"]
                p["next_review"] = problem["next_review"]
                break
        save_problems(problems)

        reviewed += 1
        print(f"\n  ✓ {result_msg}")
        print()

    print(f"  Session complete. Reviewed {reviewed} of {total} problems.")
    print()


def cmd_list(args):
    problems = load_problems()

    print()

    if not problems:
        print("  No problems tracked yet. Run `leet add` to get started.")
        print()
        return

    sorted_problems = sorted(problems, key=lambda p: p["next_review"])

    print(f"  All problems ({len(problems)} tracked)")
    print()

    col_title = max(len(p["title"]) for p in problems)
    col_title = max(col_title, 5)
    col_pattern = max(len(p["pattern"]) for p in problems)
    col_pattern = max(col_pattern, 7)

    header = (
        f"  {'Title':<{col_title}}  {'Pattern':<{col_pattern}}  "
        f"{'Stage':<5}  {'Next Review':<11}  Difficulty"
    )
    rule = "  " + "─" * (len(header) - 2)

    print(header)
    print(rule)

    for p in sorted_problems:
        difficulty = p.get("difficulty", "")
        print(
            f"  {p['title']:<{col_title}}  {p['pattern']:<{col_pattern}}  "
            f"{p['review_stage']:<5}  {p['next_review']:<11}  {difficulty}"
        )

    print()


def cmd_notify(args):
    problems = load_problems()
    today = date.today()

    due = [p for p in problems if date.fromisoformat(p["next_review"]) <= today]

    if not due:
        return

    count = len(due)
    title = "LeetCode Review Due"
    body = f"{count} problem{'s' if count != 1 else ''} due today. Run `leet today` to see them."

    subprocess.run(
        ["osascript", "-e", f'display notification "{body}" with title "{title}"'],
        check=False,
    )


# --- Entry point ---

def main():
    parser = argparse.ArgumentParser(
        prog="leet",
        description="LeetCode spaced repetition tracker",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add", help="Add a new problem")
    subparsers.add_parser("today", help="Show problems due today")
    subparsers.add_parser("review", help="Review due problems")
    subparsers.add_parser("list", help="List all tracked problems")
    subparsers.add_parser("notify", help="Send a macOS notification if problems are due")

    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "today": cmd_today,
        "review": cmd_review,
        "list": cmd_list,
        "notify": cmd_notify,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
