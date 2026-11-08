# Issue Tracker: Local Markdown (Active) & GitHub Issues (Optional)

Issues, refactoring plans, and specs for restructuring `petro95_workflow_team` (SPAFS V5.2 — Hướng 4) live as local markdown files under `.scratch/` by default so all engineering skills (`/to-spec`, `/to-tickets`, `/wayfinder`, `/implement`, `/improve-codebase-architecture`) work immediately without requiring external CLI authentication.

> **Note on GitHub Issues:** This repository has a GitHub remote (`git@github.com:LeNam123456/petro95_workflow_team.git`), but `gh` CLI is currently unauthenticated (`gh auth login` not yet run). Once authenticated, you can switch this file to the GitHub CLI workflow below if you prefer tracking issues on GitHub.

## Conventions (Local Markdown — Active Default)

- **One feature / restructuring effort per directory**: `.scratch/<feature-slug>/` (e.g., `.scratch/reorg-huong-4/`)
- **The spec**: `.scratch/<feature-slug>/spec.md`
- **Implementation issues**: one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` (never a single combined tickets file)
- **Triage state**: recorded as a `Status:` line near the top of each issue file (see `docs/agents/triage-labels.md` for canonical role strings)
- **Comments and conversation history**: append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket:

- **Map**: `.scratch/<effort>/map.md` (holds the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research` / `prototype` / `grilling` / `task`); a `Status:` line records `open` / `claimed` / `resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
