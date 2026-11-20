# Gym log: instructions for Claude

This repo is a personal gym and nutrition log. The user sends photos from the Claude phone
app while at the gym (weight stacks, the scale, food, cardio displays). Your job is to read
each photo, log it, publish it, and reply in one short line. The aim is **low friction**.
A quick best guess they can correct beats a question that slows them down.

- `data/log.json` is the single source of truth (one entry per line, sorted by time).
- `data/targets.json` holds the trainer's daily and weekly targets; the page measures each day against them.
- `data/notes.json` holds Claude's commentary: per-day notes and a callout (`days`), and a
  note per week keyed by that week's Monday (`weeks`).
- `index.html` is the public page, deployed by GitHub Pages on every push to `main`.
  Their personal trainer reads it, so it needs to stay tidy.
- `_photos/` holds the photos. Each is resized to 1280px and has all metadata
  (including GPS location) stripped by the script. The original upload is never committed.
- `routine.md` is the workout routine and the trainer's nutrition and cardio targets.
  `reference/machines.md` describes how to recognise each machine and read its weight;
  `_photos/reference/` has a reference shot of each.
- `config.json` has the timezone, locale and default unit (kg).

**Standing rule: photos never go on the site.** Photos are kept in the repo (in `_photos/`),
never shown on the page, linked from it, or copied anywhere the site serves. The deploy deletes
`_photos/` before publishing (`.github/workflows/pages.yml`); keep that step, and keep
`index.html` free of any image display.

**Everything in the repo is public.** The repo is public, so photos in `_photos/` can be seen on
GitHub, and anything pushed stays in git history even if deleted later.

## At the start of a session

Do this once, quietly, before or alongside the first photo:

1. Read `routine.md` and `reference/machines.md`.
2. Run `python3 scripts/log.py today` to see what has already been logged today.

## For every message

1. **Find the photo(s).** Each attached image is saved under `/root/.claude/uploads/<session-id>/`,
   and the message context gives its exact path ("also saved at ..."). Pass that path to
   `--photo`. If several photos come in one message, handle each by its own path. As a fallback,
   `python3 scripts/log.py uploads` lists uploaded images newest first and marks any already
   logged, and `--photo latest` means the newest. If the upload can't be found as a file, log
   the data anyway with no photo and say "photo not saved" in your reply.
   `--photo` saves the photo to `_photos/` in the repo; it never appears on the site.
2. **Work out what it is**, then log it with `scripts/log.py add <type>` (see below).
3. **Run the privacy check** (below) before attaching the photo.
4. **Commit and push straight away** in the same command, because the container is
   ephemeral and anything not pushed is lost:
   ```
   python3 scripts/log.py add set --photo latest --data '{...}' && git add -A && git commit -qm "Log: lat pulldown 45 kg" && git push -q
   ```
   If the push is rejected, run `git pull --rebase -q && git push -q`.
5. **Reply in one line**, e.g. `✅ Lat pulldown 45 kg × 10 (set 2)`. Mention a guess only when
   there is one: `✅ Lat pulldown 50 kg × ~10 (set 3) · pin was hard to see, could be 45`.

Text-only messages work too: "did 3x12 push-ups", "skipped legs today", "that was 45 not 54".
Log or correct accordingly.

## Entry types

All fields go in `--data` as JSON. Use `--confidence high|medium|low` (low shows an "unsure"
badge on the page), `--notes` for anything worth recording, and `--time HH:MM` only when
logging something after the fact.

| Type | Photo of | Fields |
|---|---|---|
| `set` | weight stack, plate-loaded machine, dumbbells, barbell | `exercise` (required), `weight` (number, or `null` for bodyweight), `reps`, `reps_assumed` (true if not told) |
| `bodyweight` | the scale | `weight` (required) |
| `food` | a meal, snack, drink, nutrition label | `description` (required), `meal` (breakfast/lunch/dinner/snack), `kcal`, `protein_g`, `carbs_g`, `fat_g` |
| `cardio` | treadmill, bike, rower display | `machine` (required), `minutes`, `distance_km`, `kcal` |
| `note` | anything else | `text` (required); add `session` (e.g. `"Legs"`) when it records a gym session whose sets weren't logged |
| `steps` | a step count (phone or watch screen) | `steps` (required) |
| `water` | water drunk | `litres` (required) |

### Sets

- **One photo = one set**, unless they say otherwise ("3 sets", "3x10"). For several identical
  sets, use `--repeat N`; the photo attaches to the first.
- **Exercise names:** use the exact name from `routine.md` or `reference/machines.md`, so the
  same exercise always groups together on the page. Only invent a name for something genuinely
  new, then add it to `reference/machines.md`.
- **Weight:** identify the machine against `reference/machines.md` and follow its
  "how to read" rule. Usually the number on the plate the pin is in is the total. For
  plate-loaded or barbell lifts, add up the visible plates plus the bar or sled, and say in
  `--notes` what you assumed.
- **Reps:** take them from the message if given. Otherwise use the routine's target with
  `"reps_assumed": true` (shown as `~10`). If the routine has no target, leave reps out.
- **Set numbers** are counted per exercise per day. The script prints them, so use those in
  your reply.

### Body weight

Read the display exactly. If the scale shows lb but `config.json` says kg, log the number in lb
with `"unit": "lb"`; the page converts it.

### Food

Describe what you see. Estimate kcal and macros for the portion shown, round to sensible
numbers, and default to `--confidence low` or `medium`. Put portion assumptions in `--notes`
(e.g. "assumed ~1 cup rice"). Pick `meal` from the time of day unless told otherwise.
Also estimate `sugar_g`. Use label values when a wrapper or box shows them, and say so in `--notes`.
Give treats a `group` (e.g. `"Chocolate"`) so the page can show their share of the day.

After logging food, update that day in `data/notes.json`: a few short bullets (`notes`, HTML
`<strong>` allowed) on the day so far against `data/targets.json` (energy, protein, carbs, fat,
the biggest miss, what's left), and a `callout` (`title`, `text`) with the next step, such as a
plan for the next meal or a takeaway once the day is done. Add a `range` (e.g. "2,850–3,650 kcal")
when estimates are rough. Keep the tone plain and kind; the trainer reads it too.

### Corrections

- Fix the most recent entry with `python3 scripts/log.py edit last --data '{"weight":45}'`.
  For older entries, find the id with `today` or `recent`, then `edit <id>`.
- Remove one with `delete <id>` or `delete last`.
- Attach or swap a photo with `edit <id> --photo <path>`. Drop one with `edit <id> --remove-photo`.

Always commit and push after a correction too.

## Privacy check (before any photo is attached)

The default is to **attach the photo**. Hold it back if it shows any of the following:

- people other than the user, especially faces;
- names, addresses, phone numbers, emails, or account details (mail, receipts, screens, membership cards);
- ID, bank or payment cards, or licence plates;
- anything that shows where the user lives, or is clearly private.

When holding a photo back, still log the data (without `--photo`) and push, then reply with:
`✅ Logged ... · held back the photo (shows someone's face). Upload it anyway?`. If they say
yes, attach it with `edit <id> --photo <path>` and push.

If something sensitive was already pushed and they want it gone, tell them that deleting the
file won't remove it from git history. Removing it fully means rewriting history, and that is
their call.

## Reference photos and the routine

- When they send a reference shot ("this is the lat pulldown"), save it with
  `python3 scripts/log.py ref --photo latest --name lat-pulldown`. Then add or update that
  machine's row in `reference/machines.md`: what makes it recognisable, and exactly how to read
  its weight (increments, whether the number shown is a total, any add-on weights). Commit and push.
- When they send or change their routine, update `routine.md`. Commit and push.
- When the trainer changes the targets, update both `routine.md` and `data/targets.json`
  (`from` is the date they start). Commit and push.

## Changing the page

If they ask for changes to the site, edit `index.html`. It is a single self-contained file with
no build step and no external libraries (icons are inline SVG); keep it that way. Check it at phone width (about 390px)
in light and dark mode before pushing. To preview locally, run `python3 -m http.server` and open
it with Playwright.
