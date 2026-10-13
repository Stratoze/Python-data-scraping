# Risk Group rule never uses the Final Grade (G3)

The Risk Group (`classify_risk`) is meant as an early warning, so it may only use information available before the final exam: Intermediate Grades (G1, G2), Failures and Absences. The first version used G3 itself, which made its precision/recall meaningless (it was grading the answer with the answer). The rule now is: high = G2 < 10 or Failures ≥ 2; medium = G1 < 10 or Failures ≥ 1 or Absences high; low otherwise.

Because the thresholds were chosen while looking at `mat`, the headline quality numbers are the ones from the strict Holdout on `por` (students not present in `mat`), not the in-sample numbers.

## Considered options

- **Two tiers (high / not high)**: rejected after measuring that medium students fail several times more often than low students, also on the Holdout (Fisher test significant). Three tiers map to three actions: intervene / monitor / no action.
- **Tuning the medium criteria further**: three alternatives all gave 5–10% fail rates; kept the original to avoid overfitting.

## Consequences

- A test (`test_risk_rule_ignores_final_grade`) guards that changing G3 never changes the Risk Group.
- `avg_grade` (contains G3) must not be used as a predictor; `avg_g1g2` is the early-prediction alternative.
