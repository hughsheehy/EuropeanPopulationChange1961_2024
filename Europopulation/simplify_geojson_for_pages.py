import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "ARDECO_population_decline_map.geojson"
OUTPUT_DIR = BASE_DIR.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "ARDECO_population_decline_map.simplified.geojson"

TOLERANCE = 0.0035
DECIMALS = 5


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


def main():
    with SOURCE_PATH.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)

    features = geojson.get("features", [])
    simplified_features = []
    for feature in features:
        simplified_features.append(
            {
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": simplify_geometry(feature.get("geometry")),
            }
        )

    output = {
        "type": "FeatureCollection",
        "name": geojson.get("name", "ARDECO_population_decline_map_simplified"),
        "features": simplified_features,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {len(simplified_features)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
