# Voltix — Model Evaluation Results

Generated from `app/model/eval_results.joblib`, produced by `src/train_model.py`.

## Test setup

- Test set size: 88 samples (held out from the most recent ~20% of months,
  time-based split — not random — so the model is genuinely being evaluated
  on data that comes after everything it trained on)
- Actual positive (high-risk) rate in the test set: 38.6%

## Voltix model (logistic regression, lagged features only)

- Precision: 0.655
- Recall: 0.559
- F1 score: 0.603
- Accuracy: 0.716
- Brier score: 0.188 (calibration quality — lower is better; measures how
  close the predicted probabilities are to the actual outcomes, not just
  whether the final yes/no call was right)

## Naive baseline (predict "same as last month")

- Precision: 0.475
- Recall: 0.559
- F1 score: 0.514
- Accuracy: 0.591

## What this means

The trained model beats the naive baseline on precision (+0.180), F1
(+0.089), and accuracy (+0.125). Recall is tied at 0.559 — the model isn't
catching more true high-risk months than "assume nothing changed," but it's
catching the same number with far fewer false alarms (that's what the
precision gain reflects). Net effect: the model is a real improvement over
the naive baseline, not noise, though recall is the metric with the most
room left to improve — a useful thing to name honestly in the capstone
report's Results section rather than only citing the F1 gain.

## Where these numbers come from, and how to regenerate them

Run `python src/train_model.py` from the `outage_predictor/` folder. This
retrains the model on `data/processed/master_discos_monthly.csv`, evaluates
it on the same time-based held-out split, and overwrites the four files in
`app/model/`, including `eval_results.joblib` (the source for this file).
