"""Reuse this repository's route representation; convert WGS84 to local NED."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "pc-control"))
from mission_intelligence import Point, parse_route, distance, MissionDatabase, route_report

RADIUS = 6371000.0


def coordinate(lat, lon):
    return (math.isfinite(lat) and math.isfinite(lon) and
            -89 < lat < 89 and -180 <= lon <= 180 and (lat, lon) != (0, 0))


def ned(point, home):
    """Small-area tangent approximation, restricted to 100 m missions."""
    delta_lon = (point.lon - home[1] + 180) % 360 - 180
    return (math.radians(point.lat - home[0]) * RADIUS,
            math.radians(delta_lon) * RADIUS * math.cos(math.radians(home[0])),
            -point.alt)


def offset(home, north, east, altitude):
    return Point(home[0] + math.degrees(north / RADIUS),
                 (home[1] + math.degrees(east / (RADIUS * math.cos(math.radians(home[0])))) + 180) % 360 - 180,
                 altitude)


def validate(points, home):
    if not coordinate(*home):
        raise ValueError("Invalid home coordinate (polar regions unsupported)")
    if not 2 <= len(points) <= 20:
        raise ValueError("Route requires 2..20 waypoints")
    for p in points:
        if not coordinate(p.lat, p.lon) or not math.isfinite(p.alt) or not 5 <= p.alt <= 30:
            raise ValueError("Invalid coordinate or altitude outside 5..30 m")
        if distance(*home, p.lat, p.lon) > 100:
            raise ValueError("Waypoint exceeds 100 m home radius")
    if distance(*home, points[0].lat, points[0].lon) > 30:
        raise ValueError("First waypoint exceeds 30 m from home")
    legs = [distance(a.lat, a.lon, b.lat, b.lon) for a, b in zip(points, points[1:])]
    if any(d < 2 for d in legs) or sum(legs) > 500:
        raise ValueError("Leg must be >=2 m and route length <=500 m")
    return [ned(p, home) for p in points]


def load(path, home, fences=None, terrain=None, home_elevation=None):
    points = parse_route(Path(path).read_text(encoding="utf-8-sig"))
    targets = validate(points, home)
    if terrain and (home_elevation is None or not math.isfinite(home_elevation)):
        raise ValueError("Terrain checks require finite --home-elevation (same datum as terrain)")
    # Check approach and return as well as the original mission legs.
    checked = [Point(*home, points[0].alt), *points, Point(*home, points[-1].alt)]
    db = MissionDatabase(":memory:")
    try:
        if fences:
            db.import_json(fences)
        if terrain:
            db.import_terrain_csv(terrain)
        errors = route_report(checked, db, home_elevation_m=home_elevation if terrain else None)
        if errors:
            raise ValueError("; ".join(errors))
    finally:
        db.close()
    return targets
