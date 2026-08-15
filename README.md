# WDGWARS WiGLE CSV merger

Combine multiple WiGLE CSV exports into one upload-ready file for WDGWARS.

Place `merge_wigle_csv.py` in the directory containing your `.wigle.csv` exports,
then run:

```bash
python3 merge_wigle_csv.py
```

The script combines every `*.wigle.csv` file in that directory into
a timestamped file such as `merged_20260813_171530.wigle.csv`. It keeps the
WiGLE metadata and column header only once, checks that all files have compatible
columns, and never includes earlier merged outputs when you run it again. After
the merged file is safely written, the source CSV files are automatically
deleted.

To merge without deleting the source files, use:

```bash
python3 merge_wigle_csv.py --keep-source-files
```

To remove rows that are exactly identical, use:

```bash
python3 merge_wigle_csv.py --deduplicate
```

You can also select files or change the output name:

```bash
python3 merge_wigle_csv.py trip1.wigle.csv trip2.wigle.csv -o upload.wigle.csv
```
