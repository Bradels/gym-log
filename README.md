# Gym log

A low-friction workout, body-weight and food log. Photos and messages are sent to Claude,
which reads them, logs the result in `data/log.json`, and pushes. GitHub Pages then publishes
the log as a page (`index.html`) with each day's food and training measured against the
trainer's targets (`data/targets.json`) and Claude's notes (`data/notes.json`).
Photos stay in the repo (`_photos/`) and are never published on the site.

Numbers are read off photos, so they're best guesses rather than precise records.

- `CLAUDE.md`: how Claude logs entries
- `scripts/log.py`: adds, edits and deletes entries, and resizes and strips metadata from photos
- `routine.md`, `reference/machines.md`: the routine, and how to read each machine
