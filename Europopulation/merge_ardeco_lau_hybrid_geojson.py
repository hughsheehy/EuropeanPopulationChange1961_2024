import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.csv"
NON_UK_GEOJSON_PATH = BASE_DIR / "LAU_RG_01M_2021_4326.geojson"
UK_GEOJSON_PATH = BASE_DIR / "LAU_RG_01M_2011_4326.geojson"
OUTPUT_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.hybrid.merged.geojson"


def load_population_rows(csv_path: Path) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    non_uk_rows: dict[str, dict[str, object]] = {}
    uk_rows: dict[str, dict[str, object]] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            gisco_id = row["gisco_id"]
            cleaned: dict[str, object] = {}
            for key, value in row.items():
                if key.startswith("pop_"):
                    cleaned[key] = int(value) if value else None
                else:
                    cleaned[key] = value or None

            if gisco_id.startswith("UK"):
                uk_rows[f"UK_{gisco_id[2:]}"] = cleaned
            else:
                non_uk_rows[gisco_id] = cleaned

    return non_uk_rows, uk_rows


def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def merge_features(
    features: list[dict],
    population_by_id: dict[str, dict[str, object]],
    keep_country: str | None = None,
) -> tuple[list[dict], int, int]:
    merged_features: list[dict] = []
    matched = 0
    unmatched = 0

    for feature in features:
        properties = feature.setdefault("properties", {})
        gisco_id = properties.get("gisco_id") or properties.get("GISCO_ID")
        if not isinstance(gisco_id, str):
            unmatched += 1
            continue

        if keep_country is not None and not gisco_id.startswith(keep_country):
            continue
        if keep_country is None and gisco_id.startswith("UK"):
            continue

        population = population_by_id.get(gisco_id)
        if population is None:
            unmatched += 1
            continue

        properties["gisco_id"] = gisco_id
        properties.update(population)
        merged_features.append(feature)
        matched += 1

    return merged_features, matched, unmatched


def main() -> None:
    non_uk_population, uk_population = load_population_rows(CSV_PATH)
    non_uk_geojson = load_geojson(NON_UK_GEOJSON_PATH)
    uk_geojson = load_geojson(UK_GEOJSON_PATH)

    non_uk_features, non_uk_matched, non_uk_unmatched = merge_features(
        non_uk_geojson.get("features", []),
        non_uk_population,
        keep_country=None,
    )
    uk_features, uk_matched, uk_unmatched = merge_features(
        uk_geojson.get("features", []),
        uk_population,
        keep_country="UK",
    )

    hybrid_geojson = {
        "type": "FeatureCollection",
        "name": "ARDECO_LAU_HYBRID_2021_NON_UK_2011_UK",
        "features": non_uk_features + uk_features,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(hybrid_geojson, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"Non-UK matched features: {non_uk_matched}")
    print(f"Non-UK unmatched geometry features: {non_uk_unmatched}")
    print(f"UK matched features: {uk_matched}")
    print(f"UK unmatched geometry features: {uk_unmatched}")
    print(f"Total matched features: {non_uk_matched + uk_matched}")
    print(f"Wrote: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
