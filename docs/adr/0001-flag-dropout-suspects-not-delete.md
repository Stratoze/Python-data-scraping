# Flag Dropout Suspects instead of deleting them

In `mat`, 38 students have a Final Grade (G3) of 0, and all 38 also have 0 recorded Absences, with a mean G1 of about 7.5. A real grade of 0/20 after that G1 is implausible; the consistent reading is "did not sit the final exam / left school, absences not recorded". We keep these rows, mark them with the Anomaly Flag `dropout_suspect`, and report every headline statistic twice: on all students and on `exclude_dropout`. Conclusions are drawn from `exclude_dropout`.

## Considered options

- **Delete the rows**: hides a real phenomenon (students leaving school) and cannot be undone by a reader.
- **Keep them unflagged**: the zeros flip the Absences–G3 correlation from r = −0.213 to +0.034 and hide the real effect.

## Consequences

- `cleaned_students*.csv` contain the Dropout Suspects; any analysis must filter `dropout_suspect` explicitly.
- The label is an inference, not confirmed by the schools. The sensitivity analysis (report section 6.1) shows the Absences conclusion holds with or without this assumption.
