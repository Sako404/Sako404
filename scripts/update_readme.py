#!/usr/bin/env python3
"""
Regenerates the "Currently Building" and "Latest Projects" sections of
README.md from the live GitHub API, using only the stdlib and the
default GITHUB_TOKEN (no personal token, no third-party dependency).

Source of truth: README.md itself. Everything between a pair of
`<!-- NAME:START -->` / `<!-- NAME:END -->` markers is generated and
overwritten on every run; everything else is hand-written and left alone.

Only public, non-fork, non-archived repositories can appear here — the
GITHUB_TOKEN issued to this workflow is scoped to this one repository,
so the GitHub API calls below physically cannot see private repos
belonging to this account, even by accident.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request

USER = "Sako404"
SELF_REPO = "Sako404"

# Repos that exist publicly but don't belong on the profile (off-brand,
# not a real project, etc). Edit this list, not the workflow, to curate.
EXCLUDE_REPOS = {"IPTV"}

BUILDING_LIMIT = 5
LATEST_LIMIT = 5
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

API_ROOT = "https://api.github.com"


def api_get(path: str):
    token = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(f"{API_ROOT}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "sako404-profile-readme-bot")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repos() -> list[dict]:
    repos = api_get(f"/users/{USER}/repos?per_page=100&sort=created&direction=desc")
    return [r for r in repos if not r["fork"] and not r["archived"]]


def fetch_recent_push_repo_names() -> list[str]:
    events = api_get(f"/users/{USER}/events/public")
    names: list[str] = []
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        name = event["repo"]["name"].removeprefix(f"{USER}/")
        if name not in names:
            names.append(name)
    return names


def is_wanted(name: str) -> bool:
    return name != SELF_REPO and name not in EXCLUDE_REPOS


def format_list(names: list[str], repo_by_name: dict[str, dict], limit: int) -> str:
    picked = [n for n in names if is_wanted(n)][:limit]
    if not picked:
        return "_Nothing to show right now — check back soon._"
    lines = []
    for name in picked:
        repo = repo_by_name.get(name)
        url = repo["html_url"] if repo else f"https://github.com/{USER}/{name}"
        desc = (repo.get("description") if repo else None) or "No description provided."
        lines.append(f"- [{name}]({url}) — {desc}")
    return "\n".join(lines)


def splice(content: str, marker: str, replacement: str) -> str:
    pattern = re.compile(
        rf"(<!-- {marker}:START -->\n).*?(\n<!-- {marker}:END -->)",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise SystemExit(f"Markers for {marker} not found in README.md")
    return pattern.sub(lambda m: m.group(1) + replacement + m.group(2), content)


def main() -> None:
    repos = fetch_repos()
    repo_by_name = {r["name"]: r for r in repos}

    latest_names = [r["name"] for r in repos]
    building_names = fetch_recent_push_repo_names()

    building_md = format_list(building_names, repo_by_name, BUILDING_LIMIT)
    latest_md = format_list(latest_names, repo_by_name, LATEST_LIMIT)

    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    content = splice(content, "CURRENTLY-BUILDING", building_md)
    content = splice(content, "LATEST-PROJECTS", latest_md)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md sections regenerated.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"GitHub API error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
