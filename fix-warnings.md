# Plan: Fix the 88 Dependabot Security Warnings

## Progress status

Work is happening on branch `fix-dependabot-warnings`.

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | npm `site/` criticals (convict, handlebars) | DONE |
| Phase 2 | npm `slides/` + leftover `site/` moderates | DONE |
| Phase 3 | pip `notebook_validation/` (mlflow group) | not started |
| Phase 4 | pip `auto_scripts/` | not started |
| Phase 5 | pip `populate_aircraft_db/` | not started |
| Phase 6 | verify, single PR, dismiss no-fix alerts | not started |

Notes from the completed work:
- `site/`: `npm audit fix` cleared all 6 reported vulnerabilities (2 critical, 1 high, 3 moderate) with no `--force` needed. Antora build (`npm run build`) still produces site output cleanly. Lock file changed only at the transitive level; top-level Antora versions untouched.
- `slides/`: `npm audit fix` cleared all 7 vulnerabilities (4 high, 3 moderate) with no `--force` needed. The patched `@marp-team/marp-cli` binary loads and runs. Note the `build:html` script finds no `.md` source files in the input dirs (they hold only PDFs/PNGs today), so it prints usage and emits nothing new. This is a pre-existing repo state, not a regression from the dependency bump.

## What is going on

GitHub Dependabot found 88 open vulnerability alerts on the default branch: 4 critical, 31 high, 46 moderate, 7 low. They live in six dependency files across two ecosystems:

| Dependency file | Ecosystem | What it is | Alerts |
|---|---|---|---|
| `site/package-lock.json` | npm | Antora docs site builder | critical + high + moderate |
| `slides/package-lock.json` | npm | Marp slide builder | high + moderate |
| `workshop-setup/notebook_validation/uv.lock` | pip | Notebook validation + agent modules (pulls in mlflow) | critical + high + moderate + low |
| `workshop-setup/auto_scripts/uv.lock` | pip | Databricks setup CLI | high + moderate + low |
| `workshop-setup/populate_aircraft_db/uv.lock` | pip | Neo4j data loader (pulls in pypdf, torch, transformers) | medium + low |
| `workshop-setup/verify/uv.lock` | pip | GDS verify CLI | none |

The important thing to understand: almost every alert is a **transitive** dependency, meaning a package we never asked for directly that got pulled in by something we did ask for. For example `convict` and `handlebars` come in through Antora, and `pypdf`, `torch`, and `mlflow`'s many sub-packages come in through `neo4j-graphrag` and `mlflow`.

Because they are transitive and our direct version constraints are loose (mostly `>=`), the fix for the large majority is simply to **regenerate the lock files** so they pull the patched versions. Only a couple of cases need a direct version bump by hand.

This is workshop and tooling code, not an internet-facing production service, so the real-world risk is low. The goal here is to get the alert count to zero cleanly without breaking the setup scripts, the data loader, or the docs build.

## Guiding approach

1. Do the work on a branch, not on `main`.
2. Fix one dependency file per step so each change is easy to verify and roll back.
3. After each file, rebuild or run the affected tool to confirm nothing broke.
4. Start with the critical alerts, then high, then moderate and low.
5. Push and watch the Dependabot count drop after each phase.

## Phase 1: Critical alerts (npm site, 4 criticals) — DONE

All four critical alerts are in the docs site builder: `convict` (2) and `handlebars` (1 critical, plus high/moderate/low), pulled in through Antora.

Steps:
1. `cd site`
2. Run `npm audit` to see the full tree and confirm which direct dependency pulls in `convict` and `handlebars`.
3. Run `npm audit fix`. This rewrites `package-lock.json` to patched transitive versions without touching the top-level Antora versions.
4. If any criticals remain, run `npm audit fix --force` cautiously, then check whether it bumped Antora itself to a new major version.
5. Rebuild the site: `npm run build` and confirm it produces output with no errors.

Patched targets for reference: `convict` 6.2.5, `handlebars` 4.7.9.

Why first: critical severity, and the docs site is self-contained, so the blast radius is small.

## Phase 2: Remaining npm (slides + leftover site) — DONE

`slides/package-lock.json` has high and moderate alerts, all transitive through `@marp-team/marp-cli`: `@xmldom/xmldom`, `basic-ftp`, `tmp`, `ws`, `postcss`, `ip-address`.

`site/package-lock.json` will likely have moderate alerts left after Phase 1: `picomatch`, `qs`, `follow-redirects`.

Steps:
1. `cd slides && npm audit fix`, then run the slide build (`npm run build:html`) to confirm Marp still renders.
2. Back in `site`, run `npm audit fix` again to clear remaining moderates.
3. If a transitive fix is blocked because the top-level tool pins an old version, update the top-level package (`@marp-team/marp-cli` in slides, the `@antora/*` packages in site) to its latest version and re-run the build.

Patched targets: `@xmldom/xmldom` 0.9.10, `basic-ftp` 5.3.1, `tmp` 0.2.6, `ws` 8.20.1, `postcss` 8.5.10, `picomatch` 4.0.4, `qs` 6.15.2, `follow-redirects` 1.16.0, `ip-address` 10.1.1.

## Phase 3: Python notebook_validation (largest pip group)

This file has the most pip alerts, including the critical/high `mlflow` ones. Most come in transitively through `mlflow`: `GitPython`, `pillow`, `Mako`, `pyasn1`, `urllib3`, `starlette`, `requests`, `idna`, `cryptography`. The `mlflow` alerts themselves need a direct bump because the current floor is too low.

Steps:
1. Edit `workshop-setup/notebook_validation/pyproject.toml`: change `mlflow>=2.10.0` to `mlflow>=3.11.1`. (The high/critical `mlflow` fixes land in the 3.11 line.)
2. `cd workshop-setup/notebook_validation && uv lock --upgrade`. This regenerates `uv.lock` with patched versions of all the transitive packages at once.
3. `uv sync` to install.
4. Confirm the validation scripts and agent modules still import and run.

One known constraint: mlflow 3.11 may require a newer minimum Python or pull a heavier dependency set. If `uv lock --upgrade` reports a conflict, note it and decide whether to pin mlflow at the highest 3.11.x that resolves cleanly.

Patched targets: `mlflow` 3.11.1, `GitPython` 3.1.50, `pillow` 12.2.0, `Mako` 1.3.12, `pyasn1` 0.6.3, `urllib3` 2.7.0, `starlette` 1.0.1, `requests` 2.33.0, `idna` 3.15, `cryptography` 46.0.7.

## Phase 4: Python auto_scripts

High and moderate alerts here are all transitive through `databricks-sdk`: `urllib3`, `cryptography`, `pyasn1`, `requests`, `idna`, `Pygments`, plus the direct-ish `python-dotenv`.

Steps:
1. `cd workshop-setup/auto_scripts && uv lock --upgrade`.
2. `uv sync`.
3. Run the existing checks: `uv run ruff check .`, `uv run mypy src/`, and a dry run of `uv run databricks-setup --help` to confirm the CLI loads.

If `python-dotenv` does not move past 1.2.2 on the lock upgrade, bump its floor in `pyproject.toml` from `>=1.0.0` to `>=1.2.2`.

Patched targets: `urllib3` 2.7.0, `cryptography` 46.0.7, `pyasn1` 0.6.3, `requests` 2.33.0, `idna` 3.15, `Pygments` 2.20.0, `python-dotenv` 1.2.2.

## Phase 5: Python populate_aircraft_db

Medium and low alerts, all transitive through `neo4j-graphrag` and its ML extras: `pypdf` (the big one, ~15 alerts), `transformers`, `torch`, `idna`, `python-dotenv`, `Pygments`.

Steps:
1. `cd workshop-setup/populate_aircraft_db && uv lock --upgrade`.
2. `uv sync`.
3. Run a smoke test: `uv run populate-aircraft-db --help`, and if a Neo4j instance is available, `verify`.

Two items need a judgment call:
- **torch** (low, `<=2.12.0`): Dependabot lists no patched version yet. Leave it, note it, and let the next torch release clear it.
- **transformers** (medium): the listed fix is `5.0.0rc3`, a release candidate. Pulling a major-version RC into a workshop loader is risky. Prefer to wait for the stable 5.0.0, or dismiss this one alert as "no safe fix yet" rather than force an RC.

Patched targets: `pypdf` 6.10.2, `idna` 3.15, `python-dotenv` 1.2.2, `Pygments` 2.20.0.

## Phase 6: Verify and close out

1. Confirm `workshop-setup/verify/uv.lock` has no alerts (it does not today, but a shared transitive bump may touch it; if so, run `uv lock --upgrade` there too).
2. Open a single pull request with all six lock files (and the two `pyproject.toml` edits).
3. Merge to the default branch.
4. Re-check the Dependabot page. Expect the count to drop to zero except for the handful with no safe upstream fix (torch, possibly transformers).
5. For each remaining alert that has no safe fix, dismiss it in the Dependabot UI with the reason "no patch available" or "fix is a pre-release," so the dashboard reflects reality.

## After the cleanup: prevent the backlog from returning

1. Add a `.github/dependabot.yml` so Dependabot opens version-bump pull requests automatically going forward, one config block per ecosystem and directory (npm in `site/` and `slides/`, pip in the four `workshop-setup/*` dirs).
2. Consider grouping the updates weekly so they arrive as a small number of PRs rather than a flood.

## Quick reference: counts by file

- `site/package-lock.json`: convict (2 critical), handlebars (critical/high/moderate/low), picomatch, qs, follow-redirects
- `slides/package-lock.json`: @xmldom/xmldom (5), basic-ftp (4), tmp, ws, postcss, ip-address
- `notebook_validation/uv.lock`: pypdf (7), GitPython (5), pillow (5), mlflow (critical+high+moderate), urllib3, Mako, pyasn1, starlette, requests, idna, cryptography, transformers
- `auto_scripts/uv.lock`: urllib3, cryptography, pyasn1, requests, idna, Pygments, python-dotenv
- `populate_aircraft_db/uv.lock`: pypdf (15), transformers, torch, idna, python-dotenv, Pygments
- `verify/uv.lock`: none
