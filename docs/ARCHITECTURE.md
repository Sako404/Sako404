# Architecture

This is the GitHub profile README repository for `Sako404` — it renders at
[github.com/Sako404](https://github.com/Sako404). Structure and reasoning:

## Single README, marker-based generation

`README.md` is the only source file for the page content — there's no
separate `README.gtpl` template. The "Currently building" and "Latest
projects" sections are wrapped in HTML comment markers
(`<!-- NAME:START -->` / `<!-- NAME:END -->`); everything else is
hand-written. `.github/workflows/update-readme.yml` runs
`scripts/update_readme.py` on a daily schedule, which rewrites only the
content between the markers and leaves the rest of the file untouched.

A two-file gtpl/README split (as used by some profile READMEs) was
considered and rejected here: the generated content is two short bullet
lists, not a full-page template, so a regex splice into one file is
simpler with no loss of clarity, and the raw markdown stays fully
readable without running anything.

## No personal access token

Both workflows use the default `GITHUB_TOKEN` that GitHub Actions issues
per run. This is enough for everything here: reading this account's
public repositories and public events, and pushing a commit back to this
one repository. It's also a safety property, not just a convenience —
`GITHUB_TOKEN` is scoped to this repository and cannot see private repos
belonging to the account, so the generator physically cannot leak a
private project onto the public profile.

The trade-off: `github-metrics.svg` renders with `base: ""` (default
stat cards disabled) and only the contribution calendar plugin enabled,
because org-level and cross-repo metrics plugins need a personal token
with broader scopes. If richer metrics are wanted later, that requires
deliberately creating a PAT secret — a decision left to the repo owner,
not made automatically by this tooling.

## Curation, not full automation

`scripts/update_readme.py` has one hardcoded list, `EXCLUDE_REPOS`, for
public repos that exist but don't belong on the profile (e.g. a raw
playlist file repo). Everything else — which repos appear, in what
order — is derived live from the GitHub API. Pinned repositories (the
row GitHub renders above this README) are not managed by this repo at
all: GitHub has no supported API for setting them, so that stays a
manual, occasional action in the GitHub UI.
