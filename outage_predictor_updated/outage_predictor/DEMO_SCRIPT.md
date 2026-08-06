# Voltix demo video script (max 1:30)

One heads-up before you record: your deliverables list says "2 mins demo
video," but you asked for a max of 1:30. This script is timed to 1:30. If
you'd rather use the full 2 minutes, the extra 30 seconds is easy to add —
I've marked one optional beat below you could expand.

**This version leads with the live NERC Band data panel** (Step 3 of the
app) instead of the old "representative seed registry" caveat beat — that
panel is your strongest, most current rebuttal to "the data isn't up to
date," so it earns the screen time. Pick a street/area you've confirmed
gets a real feeder match (Benin, Abuja, Ikeja, Eko, Ibadan, Jos, Kaduna,
or Kano give you the best odds — see DATA_NOTES.md for coverage).

Total runtime: 90 seconds. Timestamps are cumulative.

---

**[0:00-0:12] Hook + what it is**

(Screen: Voltix app, State/Street picker visible)

"This is Voltix — it predicts electricity outage risk across Nigeria,
covering all eleven electricity distribution companies nationwide, built on
real regulatory data from NERC — including filings from 2025 and 2026, not
just the historical training window."

**[0:12-0:28] Show the core flow**

(Screen: pick a state, e.g. Kano, then pick a street/area)

"You pick a state, then a street or area — this maps straight to the real
DisCo that serves it. Let's check a street in Kano."

(Select date, hit predict)

"Pick a date, and Voltix returns a risk probability, backed by a model
trained on real NERC operational data."

**[0:28-0:50] The live Band data panel — the money shot**

(Screen: Step 3 confirmation panel, showing the real feeder match)

"But here's what's new. This isn't just a historical prediction — Voltix
also pulls the *live* official service commitment for this exact feeder,
straight from NERC's 2025 regulatory orders: the current Band, the
guaranteed minimum daily hours, cited to the actual government filing. So
you get the model's historical read, and the regulator's current
commitment, side by side."

**[0:50-1:05] Explain the model briefly**

(Screen: probability gauge + trend chart)

"Since there's no public outage log for Nigeria, the historical model
learns from a proxy signal — drops in energy received or spikes in losses,
relative to each DisCo's own trend — using only past months to predict, so
there's no leakage."

**[1:05-1:20] Show the evaluation panel — proof it works**

(Screen: evaluation panel)

"On held-out test data, it beats a naive baseline — 0.60 F1 versus 0.51 —
a real improvement over just guessing 'same as last month.'"

**[OPTIONAL beat if extending to 2:00 — insert here, ~15-20 sec]**

(Screen: scroll to methodology panel, or pick a future date)

"The app is upfront about its limits too — for dates beyond the training
data, it labels this a Seasonal Risk Estimate rather than faking a
forecast, and the street registry is stated as a representative seed, not
an exhaustive address book — right in the app, not buried in a report."

**[1:20-1:30] Close**

(Screen: back to home/logo)

"Voltix — nationwide, current, honest about its limits, and built to
scale. Thanks for watching."

---

## Recording notes

- Practice the flow once before recording — the state-then-street selection
  and the prediction call both take a couple seconds to render; leave room
  for that in your pacing rather than talking over dead air.
- Pick a DisCo/area combo you've already tested locally so both the
  prediction *and* the live Band match render cleanly. Best odds: Benin,
  Abuja, Ikeja, Eko, Ibadan, Jos, Kaduna, or Kano (these have full,
  feeder-level 2025 NERC data — see DATA_NOTES.md). Avoid leading with
  Enugu or Yola for the money-shot beat since their data is real but
  thinner; fine to use them if a specific street doesn't match, the app's
  fallback message still looks intentional, not broken.
- If you're being scored on the "nationwide" and "current data" points
  specifically, make sure the Band panel (with its NERC citation visible)
  stays on screen long enough to actually read — that single screen is
  your answer to "the data ends in 2022."

## If you don't already have a screen recorder

Any of these work for a 90-second capture with narration:
- **Windows:** Xbox Game Bar (Win+G) — built in, free.
- **Mac:** QuickTime Player → File → New Screen Recording — built in, free.
- **Either OS, browser-based, no install:** Loom (loom.com) free tier.
- **More control (multi-take, editing):** OBS Studio (obsproject.com), free and cross-platform.

Record a couple of takes — the first one is almost always the one where you
talk over the loading spinner.
