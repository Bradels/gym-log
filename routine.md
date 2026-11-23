# Workout routine

From the personal trainer. Each weight is the target for the **top set**, meaning the heaviest
working set. Two numbers are a range to work within or up to (e.g. 20 → 25 kg). No set or rep
targets were given, so leave reps out unless the user says them (no `reps_assumed`).

Use these exercise names exactly when logging, so each exercise groups together on the page and
matches what the trainer wrote.

## Upper day

| Exercise | Top set |
|---|---|
| Flat bench | 20–25 kg |
| Seated cable row | 90–110 kg |
| Lat pulldown | 50–55 kg |
| Cable lateral raise | 2.5 kg |
| Triceps pushdown | 17.5 kg |

## Lower day

| Exercise | Top set |
|---|---|
| RDL | 5–10 kg |
| Single-leg press | 40–50 kg per side |
| Calf raise | 30 kg |
| Goblet squat | 10–12 kg |

## Full body day

| Exercise | Top set |
|---|---|
| Rack pull | 20–25 kg |
| Single-leg press | 40–50 kg per side |
| Incline machine | 30–32.5 kg |
| Rear delt fly | 2.5 kg |
| Cable biceps curl | 15–17.5 kg |

## Extra (no day given)

| Exercise | Top set |
|---|---|
| Single-arm dumbbell row | 16–18 kg |

## Nutrition and cardio targets

From the personal trainer, 20 Nov 2026. The page reads these from `data/targets.json`, so keep the
two in sync. Starting on fairly high calories: mostly whole foods, but
still eat the foods you enjoy. Body weight is weighed in daily and the plan gets adjusted from the trend.

| Daily | Target |
|---|---|
| Energy | 2,800 kcal (±100) |
| Protein | 180 g |
| Carbs | 300–340 g |
| Fat | 70–80 g |
| Water | 3+ L |
| Weigh-in | Every day |

| Weekly | Target |
|---|---|
| 10,000 steps | 3–4 days |
| Incline walk or cardio of choice | 2 × 30–40 min |

## Food notes

Use these when suggesting meals or snacks.

- **Can't eat bananas.**
- **Doesn't like eggs or avocado.** Eggs are fine on wholegrain toast with baked beans or plenty of tomato sauce.
- **Cooks for one, with as little mess as possible.** Eats whatever gets cooked, so size recipes to one serve.
  No air fryer; oven and microwave only; minimal chopping. The one-tray foil-parcel chicken
  (fillets on frozen veg, sauce on top, sealed in foil, 200°C for ~30 min, microwave rice cups) is the go-to; it's pinned in `data/recipes.json` with its variations.
  Packs often come bigger than one serve: cook about 600 g raw and keep the rest for the next day.

### Staples (use these numbers so entries stay consistent)

| Item | kcal | Protein | Carbs | Fat | Sugar | Source |
|---|---|---|---|---|---|---|
| YoP Zero yoghurt, 160 g tub (peach & mango, tropical, berry harvest) | 88 | 10.6 g | 9 g | 0.5 g | 8.6 g | label (peach & mango) |
| Nescafé Caramel Latte sachet, no added sugar | 72 | 1 g | 12 g | 2 g | 9 g | box energy; macros estimated |
| Each teaspoon of sugar | 16 | 0 | 4 g | 0 | 4 g | estimate |
| Splash of full-cream milk (~30 ml) | 20 | 1 g | 2 g | 1 g | 2 g | estimate |
| John West tuna in springwater, 95 g can | 80 | 19 g | 0 | 1 g | 0 | estimate |
| Dairy Farmers Protein Smoothie+ 400 ml | 240 | 30 g | 20 g | 4 g | 18 g | protein from label |
| Birds Eye Steamfresh baby potatoes & veg, 200 g steam bag (2 per pack) | 125 | 4 g | 18 g | 3.5 g | 4 g | estimate |
| Shredded tasty cheese, ~30 g (⅓ cup) | 120 | 7.5 g | 0 | 10 g | 0 | estimate |
| SunRice jasmine rice cup, 125 g | 200 | 3.5 g | 42 g | 1.5 g | 0 | estimate |

## Logging conventions

Log weights the same way the trainer writes them, so they can be compared directly:

- **Single-leg press:** log the weight **per side**, and put "per side" in `--notes`.
- **Dumbbells and kettlebells** (goblet squat, single-arm dumbbell row): log the weight of **one** dumbbell.
- **Barbell lifts** (RDL is confirmed barbell): the trainer's numbers **don't include the bar**.
  Log the total weight of the plates loaded (both sides together, bar excluded), and put
  "plates only, excl. bar" in `--notes`.
- **Flat bench, rack pull:** not yet confirmed whether these are barbell or dumbbell. If the photo
  shows a barbell, use the barbell rule above. If it shows dumbbells, use the dumbbell rule.
