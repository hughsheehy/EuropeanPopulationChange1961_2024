import csv
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.csv"
DEFAULT_GEOJSON_PATH = BASE_DIR / "LAU_RG_01M_2021_4326.geojson"
DEFAULT_OUTPUT_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.lau2021.merged.geojson"


def load_population_rows(csv_path: Path) -> dict[str, dict[str, object]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: dict[str, dict[str, object]] = {}
        for row in reader:
            gisco_id = row["gisco_id"]
            cleaned: dict[str, object] = {}
            for key, value in row.items():
                if key.startswith("pop_"):
                    cleaned[key] = int(value) if value else None
                else:
                    cleaned[key] = value or None
            rows[gisco_id] = cleaned
    return rows


def main() -> None:
    geojson_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_GEOJSON_PATH
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    population_by_id = load_population_rows(CSV_PATH)

    with geojson_path.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)

    matched = 0
    unmatched = 0

    for feature in geojson.get("features", []):
        properties = feature.setdefault("properties", {})
        gisco_id = properties.get("gisco_id") or properties.get("GISCO_ID")
        population = population_by_id.get(gisco_id)
        if population is None:
            unmatched += 1
            continue
        properties["gisco_id"] = gisco_id
        properties.update(population)
        matched += 1

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(geojson, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"Matched features: {matched}")
    print(f"Unmatched features: {unmatched}")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
