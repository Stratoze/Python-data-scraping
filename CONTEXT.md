# Student Performance

Analysis of factors influencing final grades in secondary education mathematics.

## Language

**Final Grade (G3)**:
Year-end grade on a 0-20 scale; the prediction target.
_Avoid_: final score, result

**Pass**:
G3 >= 10. Binary outcome derived from Final Grade.
_Avoid_: succeed, cleared

**Intermediate Grades (G1, G2)**:
First- and second-period grades on a 0-20 scale.
_Avoid_: midterm, mid score

**Studytime**:
Weekly study time bucket 1-4 (<2h, 2-5h, 5-10h, >10h).
_Avoid_: study hours, learning time

**Absences**:
Count of school absences. Bucketed low 0-3 / medium 4-9 / high >=10.
_Avoid_: truancy, missing days

**Failures**:
Count of past class failures (0-3). Distinct from Absences.
_Avoid_: repeats, fails

**Risk Group**:
Learning-risk segment: low / medium / high, derived from Intermediate Grades, Failures and Absences.
_Avoid_: risk level, danger group
