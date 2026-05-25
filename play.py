"""Enterprise Linux Mastery Game — CLI client.

Usage:
    # 1. Start the backend in one terminal:
    #    cd backend && uvicorn main:app --reload
    # 2. In another terminal:
    python play.py
"""

from __future__ import annotations

import argparse
import sys
import textwrap

import requests

API = "http://127.0.0.1:8000"
LEVELS = ["entry", "operator", "engineer", "sre"]


def banner():
    print("=" * 64)
    print(" ENTERPRISE LINUX MASTERY GAME ".center(64, "="))
    print(" Local-first. AI-mentored. Sandboxed. ".center(64, " "))
    print("=" * 64)


def pick_level() -> str:
    print("\nLevels:")
    for i, l in enumerate(LEVELS, 1):
        print(f"  {i}. {l}")
    while True:
        raw = input("Pick a level number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(LEVELS):
            return LEVELS[int(raw) - 1]
        if raw.lower() in LEVELS:
            return raw.lower()
        print("Invalid choice. Try again.")


def start_mission(user_id: str, level: str) -> dict:
    r = requests.post(f"{API}/mission/start", json={"user_id": user_id, "level": level}, timeout=30)
    if r.status_code != 200:
        print(f"\n[backend error {r.status_code}] {r.text}")
        sys.exit(1)
    return r.json()


def run_command(command: str, setup_script: str | None) -> dict:
    r = requests.post(
        f"{API}/mission/run",
        json={"command": command, "setup_script": setup_script},
        timeout=60,
    )
    return r.json()


def finish_mission(user_id: str, level: str, scenario: dict, attempts: list[dict]) -> dict:
    r = requests.post(
        f"{API}/mission/finish",
        json={
            "user_id": user_id,
            "level": level,
            "scenario": scenario,
            "attempts": attempts,
        },
        timeout=180,
    )
    return r.json()


def ask_mentor(level: str, issue: str) -> dict:
    r = requests.post(
        f"{API}/mentor/help",
        json={"level": level, "issue": issue},
        timeout=120,
    )
    return r.json()


def render_intro(intro: str):
    print()
    print("\n".join(textwrap.wrap(intro, 70, replace_whitespace=False)))
    print()
    print("Commands: type a shell command, or one of:")
    print("  /hint    — ask the mentor for a Socratic hint")
    print("  /done    — submit your attempts for grading")
    print("  /quit    — give up and exit")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="player1")
    parser.add_argument("--level", default=None, choices=LEVELS)
    args = parser.parse_args()

    banner()

    try:
        requests.get(API, timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"\nCan't reach backend at {API}.")
        print("Start it first:  cd backend && uvicorn main:app --reload")
        sys.exit(1)

    level = args.level or pick_level()
    print(f"\nStarting mission for {args.user} @ level={level}...")

    mission = start_mission(args.user, level)
    scenario = mission["scenario"]
    render_intro(mission["intro"])

    attempts: list[dict] = []
    while True:
        try:
            raw = input(f"[{level}] $ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if raw == "/quit":
            print("Giving up. No grade recorded.")
            return
        if raw == "/hint":
            recap = "; ".join(a["command"] for a in attempts) or "(nothing yet)"
            hint = ask_mentor(level, recap)
            print(f"\n  mentor: {hint.get('hint', hint.get('raw', '...'))}")
            if hint.get("next_step"):
                print(f"  focus area: {hint['next_step']}\n")
            continue
        if raw == "/done":
            break

        result = run_command(raw, setup_script=scenario.get("setup_script"))
        if result.get("stdout"):
            print(result["stdout"], end="" if result["stdout"].endswith("\n") else "\n")
        if result.get("stderr"):
            print(f"[stderr] {result['stderr']}", end="" if result["stderr"].endswith("\n") else "\n")
        print(f"[exit {result.get('exit_code', '?')}]\n")
        attempts.append(result)

    if not attempts:
        print("No commands attempted. Exiting.")
        return

    print("\nGrading...\n")
    final = finish_mission(args.user, level, scenario, attempts)
    grade = final.get("grade", {})
    print("=" * 64)
    print(f" RESULT ".center(64, "="))
    print("=" * 64)
    if "raw" in grade:
        print(grade["raw"])
    else:
        print(f"  Verdict:     {grade.get('verdict', '?')}")
        print(f"  Solved:      {grade.get('solved', '?')}")
        print(f"  Score:       {grade.get('score', '?')}/100")
        print(f"  Correctness: {grade.get('correctness', '?')}/10")
        print(f"  Safety:      {grade.get('safety', '?')}/10")
        print(f"  Efficiency:  {grade.get('efficiency', '?')}/10")
        print()
        coaching = grade.get("coaching", "")
        if coaching:
            print("  Coaching:")
            for line in textwrap.wrap(coaching, 60):
                print(f"    {line}")
        missed = grade.get("missed_concepts") or []
        if missed:
            print(f"\n  Missed concepts: {', '.join(missed)}")
    print("=" * 64)


if __name__ == "__main__":
    main()
