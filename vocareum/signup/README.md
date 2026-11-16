# Student sign-up: event export to Vocareum enrollment CSVs

`prepare_vocareum_enrollment.py` turns an event RSVP export into CSV files that Vocareum can import to enroll students.

## What it does

- **Input:** The input is an event export CSV. It needs `First Name`, `Last Name` and `Email` columns. Any other columns are ignored.
- **Grouping:** Each student lands in one of four groups by email domain: `neo4j_email`, `personal_email`, `work_email` or `school_email`.
- **Batching:** Each group is split into balanced files of 20 to 30 students. `--target-batch-size` sets the preferred size, from 20 through 30.
- **Output:** Each file uses the Vocareum headers `Email,ID,Name`. A `README.txt` in the output folder lists every file and its count.
- **Checks:** The script stops on a malformed or duplicate email. It also refuses to write into an output folder that already exists.

## Run it

Run from the repository root. The script needs only `uv` and Python 3.11 or later.

Try it on the bundled sample first:

```bash
uv run vocareum/signup/prepare_vocareum_enrollment.py
```

That reads `vocareum/signup/sample-event-export.csv` and writes `vocareum/signup/vocareum-enrollment-sample/`. Delete that folder before running the sample again.

For a real event, save the export into `vocareum/signup/` and pass both paths:

```bash
uv run vocareum/signup/prepare_vocareum_enrollment.py \
  --source vocareum/signup/<event-export>.csv \
  --output-dir vocareum/signup/vocareum-enrollment-<event-date>
```

Then import each CSV in the output folder into the Vocareum course.

## Keep attendee data out of git

Real exports hold names and emails. `.gitignore` ignores every CSV in this folder and every `vocareum-enrollment-*/` folder. Only `enroll-students.csv` and `sample-event-export.csv` are tracked. Both contain fake data.
