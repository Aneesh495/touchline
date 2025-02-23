# Datasets

Touchline uses public, permitted data sources. This document records what each is,
how it is acquired, and its licensing posture. Dataset licenses are the data
provider's; read them before redistribution. The repository does not redistribute
provider data; it stores acquired bytes under the git-ignored `data/` tree.

## StatsBomb / Hudl open data

- Source: https://github.com/hudl/open-data
- Content: competitions, matches, on-ball events, and 360 freeze frames for a
  subset of matches.
- Access: raw JSON over HTTPS from the repository's raw content host.
- Coordinate frame: 120x80, origin at a corner, y increasing downward. Touchline
  maps this to its canonical attacking frame in `parse.statsbomb`.
- Use: the event-level and spatial-context depth of the project.
- Licensing: governed by the StatsBomb open-data user agreement. Attribution is
  required; redistribution of the raw data is not performed here.

Verified during the build: the competitions file parses to 80 competitions, with
360 availability detected per competition-season.

## football-data.co.uk

- Source: https://www.football-data.co.uk/data.php
- Content: historical CSV result files for the major leagues with per-match
  statistics (shots, shots on target, corners, fouls, cards) where available.
- Access: CSV over HTTPS, by division and season code (e.g. `2223/E0.csv`).
- Use: match-level breadth across the five leagues.
- Columns: documented at football-data.co.uk/notes.txt and encoded in
  `parse.football_data_uk`.

## football-data.org (reference)

- Source: https://www.football-data.org/coverage
- Content: fixtures and results across competitions behind a tiered API.
- Posture: access tiers and rate limits must be checked before use; the ingest
  budget is designed to respect them. Not pulled by default in this build.

## openfootball (reference)

- Source: openfootball project data.
- Posture: available as an additional match-level source; not required for the
  current build.

## Acquisition discipline

All acquisition goes through `ingest.acquire.Acquirer`, which enforces a request
budget, stores a checksum and attribution per file, and records the provider
revision marker so unchanged files are not re-fetched. No credentials are used and
no access restriction is bypassed.
