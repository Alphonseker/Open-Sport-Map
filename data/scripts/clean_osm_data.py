import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

RAW_DATA_PATH = Path("data/raw/osm_sample.json")
OUTPUT_GEOJSON_PATH = Path("data/processed/facilities.geojson")

def extract_coordinates(element: dict) -> tuple[float, float] | None:
    """Extract (longitude, latitude) regardless of whether element is a node or way."""
    if element.get("type") == "node" and "lon" in element and "lat" in element:
        return element["lon"], element["lat"]
    
    if element.get("type") == "way" and "center" in element:
        center = element["center"]
        return center.get("lon"), center.get("lat")
    
    return None

def normalize_sport_tag(tags: dict) -> str:
    """Determine the primary sport category or fallback to leisure type."""
    if "sport" in tags:
        return tags["sport"]
    if tags.get("leisure") == "fitness_station":
        return "fitness"
    if tags.get("leisure") == "track":
        return "running"
    return "multi"

def process_osm_element(element: dict) -> dict | None:
    """Transform an OSM element into a standardized GeoJSON Feature."""
    coords = extract_coordinates(element)
    if not coords or None in coords:
        return None

    tags = element.get("tags", {})
    lon, lat = coords

    # GeoJSON Feature specification (RFC 7946)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "osm_id": element.get("id"),
            "osm_type": element.get("type"),
            "name": tags.get("name", "Unnamed Facility"),
            "leisure": tags.get("leisure", "pitch"),
            "sport": normalize_sport_tag(tags),
            "surface": tags.get("surface", "unknown"),
            "access": tags.get("access", "yes"),
            "lit": tags.get("lit", "unknown")
        }
    }

def clean_and_convert_to_geojson():
    if not RAW_DATA_PATH.exists():
        logging.error(f"Input file not found at {RAW_DATA_PATH}. Run fetch_osm_data.py first.")
        return

    logging.info(f"Loading raw OSM data from {RAW_DATA_PATH}...")
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_content = json.load(f)

    elements = raw_content.get("elements", [])
    features = []

    for el in elements:
        feature = process_osm_element(el)
        if feature:
            features.append(feature)

    geojson_output = {
        "type": "FeatureCollection",
        "features": features
    }

    OUTPUT_GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson_output, f, ensure_ascii=False, indent=2)

    logging.info(f"Successfully processed {len(features)} facilities into {OUTPUT_GEOJSON_PATH}")

if __name__ == "__main__":
    clean_and_convert_to_geojson()