import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CROSSWALK_PATH = BASE_DIR / "unmatched_uk_crosswalk.csv"
OUTPUT_PATH = BASE_DIR / "remaining_unmatched_uk_after_exact.csv"


def main():
    with CROSSWALK_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    remaining = [row for row in rows if row.get("match_type") != "exact_name_and_district"]

    fieldnames = rows[0].keys() if rows else []
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    print(f"Wrote {len(remaining)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
