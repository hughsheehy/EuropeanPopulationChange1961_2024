import json
import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.hybrid.merged.geojson"
ARDECO_CSV_PATH = BASE_DIR / "ARDECO_Local_Population_Time-Series–1961-2024.csv"
UK_CROSSWALK_PATH = BASE_DIR / "unmatched_uk_crosswalk.csv"
UK_WARD_GEOJSON_PATH = BASE_DIR / "WD_MAY_2025_UK_BGC_V2_-6160789691130864750.geojson"
OUTPUT_DIR = BASE_DIR.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "ARDECO_change_1961_2024_simplified.geojson"

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

TOLERANCE = 0.0
DECIMALS = 7


def round_point(point: list[float]) -> list[float]:
    return [round(point[0], DECIMALS), round(point[1], DECIMALS)]


def perpendicular_distance_sq(point, start, end):
    x, y = point
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return (x - x1) ** 2 + (y - y1) ** 2
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return (x - proj_x) ** 2 + (y - proj_y) ** 2


def douglas_peucker(points, tolerance_sq):
    if len(points) <= 2:
        return points

    start = points[0]
    end = points[-1]
    max_dist = -1.0
    index = 0

    for i in range(1, len(points) - 1):
        dist = perpendicular_distance_sq(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            index = i

    if max_dist > tolerance_sq:
        left = douglas_peucker(points[: index + 1], tolerance_sq)
        right = douglas_peucker(points[index:], tolerance_sq)
        return left[:-1] + right

    return [start, end]


def dedupe_consecutive(points):
    if not points:
        return points
    deduped = [points[0]]
    for point in points[1:]:
        if point != deduped[-1]:
            deduped.append(point)
    return deduped


def simplify_ring(ring):
    if TOLERANCE <= 0:
      return [round_point(p) for p in ring]
    if len(ring) <= 4:
        return [round_point(p) for p in ring]

    closed = ring[0] == ring[-1]
    work = ring[:-1] if closed else ring[:]
    work = [round_point(p) for p in work]
    work = dedupe_consecutive(work)

    if len(work) <= 3:
        simplified = work
    else:
        simplified = douglas_peucker(work + [work[0]], TOLERANCE * TOLERANCE)[:-1]

    if len(simplified) < 3:
        simplified = work[:3]

    closed_ring = simplified + [simplified[0]]
    if len(closed_ring) < 4:
        closed_ring = work[:3] + [work[0]]

    return closed_ring


def simplify_polygon(coords):
    return [simplify_ring(ring) for ring in coords]


def simplify_geometry(geometry):
    if geometry is None:
        return None

    gtype = geometry.get("type")
    coords = geometry.get("coordinates")

    if gtype == "Polygon":
        return {"type": "Polygon", "coordinates": simplify_polygon(coords)}
    if gtype == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [simplify_polygon(polygon) for polygon in coords],
        }
    return geometry


def latest_available_point(source_props: dict):
    available = [(year, source_props.get(field)) for field, year in POP_FIELDS if source_props.get(field) is not None]
    return available[-1] if available else (None, None)


def load_ardeco_rows() -> dict[str, dict]:
    rows = {}
    with ARDECO_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            cleaned = {}
            for key, value in row.items():
                if key.startswith("pop_"):
                    cleaned[key] = int(value) if value else None
                else:
                    cleaned[key] = value or None
            rows[row["gisco_id"]] = cleaned
    return rows


def load_exact_uk_crosswalk() -> list[dict]:
    with UK_CROSSWALK_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [row for row in rows if row.get("match_type") == "exact_name_and_district" and row.get("wd25cd")]


def load_uk_ward_features() -> dict[str, dict]:
    with UK_WARD_GEOJSON_PATH.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)
    return {feature["properties"].get("WD25CD"): feature for feature in geojson.get("features", [])}


def build_properties(source_props: dict) -> dict | None:
    pop_1961 = source_props.get("pop_1961")
    latest_year, latest_pop = latest_available_point(source_props)
    if pop_1961 in (None, 0) or latest_pop is None or latest_year is None:
        return None

    pct_change = round(((latest_pop - pop_1961) / pop_1961) * 100, 4)
    props = {
        "gisco_id": source_props.get("gisco_id"),
        "lau_name": source_props.get("LAU_NAME") or source_props.get("lau_name"),
        "country_code": source_props.get("N0_code") or source_props.get("CNTR_CODE"),
        "nuts3_code": source_props.get("N3_code"),
        "pct_change_1961_latest": pct_change,
        "latest_year": latest_year,
        "latest_pop": latest_pop,
        "geometry_source": source_props.get("geometry_source") or "gisco"
    }

    for field, _year in POP_FIELDS:
        props[field] = source_props.get(field)

    return props


def main():
    ardeco_rows = load_ardeco_rows()
    with SOURCE_PATH.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)

    output_features = []
    existing_ids = set()
    for feature in geojson.get("features", []):
        props = build_properties(feature.get("properties", {}))
        if props is None:
            continue
        existing_ids.add(props["gisco_id"])

        output_features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": simplify_geometry(feature.get("geometry")),
            }
        )

    uk_crosswalk = load_exact_uk_crosswalk()
    uk_ward_features = load_uk_ward_features()
    fallback_added = 0
    for row in uk_crosswalk:
        ardeco_id = row["ardeco_gisco_id"]
        if ardeco_id in existing_ids:
            continue

        ardeco_props = ardeco_rows.get(ardeco_id)
        ward_feature = uk_ward_features.get(row["wd25cd"])
        if not ardeco_props or not ward_feature:
            continue

        fallback_source_props = dict(ardeco_props)
        fallback_source_props["LAU_NAME"] = row["wd25nm"] or row["legacy_name"]
        fallback_source_props["geometry_source"] = "wd_may_2025_exact_crosswalk"

        props = build_properties(fallback_source_props)
        if props is None:
            continue

        output_features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": simplify_geometry(ward_feature.get("geometry")),
            }
        )
        existing_ids.add(ardeco_id)
        fallback_added += 1

    output = {
        "type": "FeatureCollection",
        "name": "ARDECO_change_1961_latest_simplified",
        "features": output_features,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {len(output_features)} features to {OUTPUT_PATH}")
    print(f"Added exact UK fallback features: {fallback_added}")


if __name__ == "__main__":
    main()
