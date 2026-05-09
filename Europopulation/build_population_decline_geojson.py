import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.hybrid.merged.geojson"
OUTPUT_PATH = BASE_DIR / "ARDECO_population_decline_map.geojson"
POP_FIELDS = [
    ("pop_1961", 1961),
    ("pop_1971", 1971),
    ("pop_1981", 1981),
    ("pop_1991", 1991),
    ("pop_2001", 2001),
    ("pop_2011", 2011),
    ("pop_2021", 2021),
    ("pop_2024", 2024),
]


def compute_population_metrics(properties: dict) -> dict:
    series = [(year, properties.get(field)) for field, year in POP_FIELDS if properties.get(field) is not None]
    if not series:
        return {
            "earliest_year": None,
            "earliest_pop": None,
            "latest_year": None,
            "latest_pop": None,
            "population_change": None,
            "population_decline_pct": None,
        }

    earliest_year, earliest_pop = series[0]
    latest_year, latest_pop = series[-1]
    change = latest_pop - earliest_pop
    decline_pct = None
    if earliest_pop not in (None, 0):
        decline_pct = round(((earliest_pop - latest_pop) / earliest_pop) * 100, 4)

    return {
        "earliest_year": earliest_year,
        "earliest_pop": earliest_pop,
        "latest_year": latest_year,
        "latest_pop": latest_pop,
        "population_change": change,
        "population_decline_pct": decline_pct,
    }


def main() -> None:
    with SOURCE_PATH.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)

    reduced_features = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        metrics = compute_population_metrics(props)
        reduced_features.append(
            {
                "type": "Feature",
                "properties": {
                    "gisco_id": props.get("gisco_id"),
                    "country_code": props.get("N0_code") or props.get("CNTR_CODE"),
                    "nuts3_code": props.get("N3_code"),
                    "lau_name": props.get("LAU_NAME"),
                    **metrics,
                },
                "geometry": feature.get("geometry"),
            }
        )

    output = {
        "type": "FeatureCollection",
        "name": "ARDECO_population_decline_map",
        "features": reduced_features,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {len(reduced_features)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
