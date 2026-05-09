import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_PATH = BASE_DIR / "data" / "ARDECO_change_1961_2024_simplified.geojson"
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_TEMPLATE = "ARDECO_change_1961_2024_part{index}.geojson"
PARTS = 3


def main():
    with SOURCE_PATH.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)

    features = geojson.get("features", [])
    total = len(features)
    chunk_size = (total + PARTS - 1) // PARTS

    for i in range(PARTS):
        start = i * chunk_size
        end = min(start + chunk_size, total)
        part_features = features[start:end]
        part_geojson = {
            "type": "FeatureCollection",
            "name": f"{geojson.get('name', 'ARDECO_change_1961_2024_simplified')}_part{i + 1}",
            "features": part_features,
        }
        output_path = OUTPUT_DIR / OUTPUT_TEMPLATE.format(index=i + 1)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(part_geojson, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"Wrote part {i + 1}: {len(part_features)} features -> {output_path}")


if __name__ == "__main__":
    main()
