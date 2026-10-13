# `por` is used only for comparison and Holdout; `mat` is the primary Subject

The assignment asks about one cohort, and every headline statistic, chart and regression interpretation is computed on `mat` (mathematics). The `por` file (Portuguese) is used for two things only: replicating the direction of the main correlations, and the out-of-sample Holdout of the frozen Risk Group rule.

Many students appear in both files (358 matched on the 13 merge keys of `student-merge.R`, after dropping keys that repeat inside a file). So `mat` and `por` are not independent samples: the replication is partial, the strict Holdout keeps only `por` students absent from `mat`, and comparing the two Subjects for the same students uses a paired test (`_paired_subjects`), not an independent-groups test.

## Considered options

- **Pool `mat` and `por` into one analysis**: rejected; the same student would be counted twice and the grading scales of the two courses differ (same students score 1.26 points lower in mathematics).

## Consequences

- `cleaned_students.csv` holds both Subjects; `cleaned_students_mat.csv` / `cleaned_students_por.csv` avoid filtering mistakes.
