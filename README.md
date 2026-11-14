# Gym log

A low-friction workout, body-weight and food log. Photos taken at the gym are sent to Claude,
which reads them, logs the result in `data/log.json`, and pushes. GitHub Pages then publishes
the log as a simple page (`index.html`).

Numbers are read off photos, so they're best guesses rather than precise records.

- `CLAUDE.md`: how Claude logs entries
- `scripts/log.py`: adds, edits and deletes entries, and resizes and strips metadata from photos
- `routine.md`, `reference/machines.md`: the routine, and how to read each machine
