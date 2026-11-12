# Issue Tracker: Local Markdown

Issues, implementation tasks, and specs for **Pipeline Dự báo Điểm & Chiều hướng Xăng Platts Singapore Mogas 95 (Naive, XGBoost, LSTM, GRU)** theo `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` live as local markdown files under `.scratch/traditional-pipeline/` so all engineering skills (`/to-spec`, `/to-tickets`, `/wayfinder`, `/implement`, `/code-review`, etc.) work seamlessly without requiring external CLI authentication.

## Conventions (Local Markdown — Active Default)

- **Feature directory**: `.scratch/traditional-pipeline/`
- **Specification**: `.scratch/traditional-pipeline/spec.md`
- **Issue tracker directory**: `.scratch/traditional-pipeline/issues/`
- **Ticket naming convention**: `NN-<slug>.md` (e.g., `01-data-audit-and-dataset.md`), numbered sequentially starting from `01`. Never combine tickets into a single file.
- **Triage state**: Recorded as a `Status:` line near the top of each issue file (see `docs/agents/triage-labels.md` for canonical role strings: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
- **Comments and conversation history**: Append to the bottom of the file under a `## Comments` heading.

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/traditional-pipeline/issues/` named `NN-<slug>.md` (e.g. `01-data-audit-and-dataset.md`), ensuring the directory exists.

## When a skill says "fetch the relevant ticket"

Read the file at `.scratch/traditional-pipeline/issues/<NN>-<slug>.md`. The user or skill will pass the path or issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket:

- **Map**: `.scratch/traditional-pipeline/map.md` (holds the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `.scratch/traditional-pipeline/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research` / `prototype` / `grilling` / `task`); a `Status:` line records `open` / `claimed` / `resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/traditional-pipeline/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
