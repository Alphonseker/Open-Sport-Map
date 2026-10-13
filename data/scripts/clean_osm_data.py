import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compute_centroid(geometry: dict) -> list[float]:
    """Calculates a [lon, lat] centroid for Point, Polygon, or MultiPolygon."""
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if geom_type == "Point":
        return coords

    if geom_type == "Polygon":
        # Exterior ring is coords[0]
        ring = coords[0]
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        return [sum(lons) / len(lons), sum(lats) / len(lats)]

    if geom_type == "MultiPolygon":
        # Average of the exterior ring of the first polygon
        ring = coords[0][0]
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        return [sum(lons) / len(lons), sum(lats) / len(lats)]

    return None

def normalise_feature(raw_item: dict, index: int) -> dict:
    """Normalises an item coming either from Overpass JSON or raw Osmium GeoJSON."""
    # 1. Extraction of properties / tags
    if "properties" in raw_item:  # GeoJSON feature (from Osmium)
        props = raw_item.get("properties", {})
        osm_id = props.get("@id") or raw_item.get("id") or props.get("id")
        geometry = raw_item.get("geometry", {})
        centroid = compute_centroid(geometry)

        # ID extraction with fallback to auto-generated ID
        osm_id = (
            props.get("@id")
            or raw_item.get("id")
            or props.get("id")
            or props.get("osm_id")
        )
        if not osm_id:
            osm_id = f"auto_{index}"

    else:  # Overpass element
        props = raw_item.get("tags", {})
        osm_id = raw_item.get("id")
        if "center" in raw_item:
            centroid = [raw_item["center"]["lon"], raw_item["center"]["lat"]]
        elif "lon" in raw_item and "lat" in raw_item:
            centroid = [raw_item["lon"], raw_item["lat"]]
        else:
            centroid = None

    if not centroid or not osm_id:
        return None

    # 2. Tag normalisation
    leisure = props.get("leisure")
    sport = props.get("sport")

    if not sport:
        if leisure == "fitness_station":
            sport = "fitness"
        elif leisure == "track":
            sport = "running"
        elif leisure == "pitch":
            sport = "multisport"
        else:
            sport = "unknown"

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [round(centroid[0], 6), round(centroid[1], 6)]
        },
        "properties": {
            "osm_id": str(osm_id),
            "name": props.get("name"),
            "sport": sport.lower() if sport else None,
            "surface": props.get("surface"),
            "access": props.get("access", "public"),
            "lit": props.get("lit", "unknown")
        }
    }

def clean_data(input_path: Path, output_path: Path):
    if not input_path.exists():
        logging.error(f"File not found: {input_path}")
        return

    logging.info(f"Reading and cleaning from: {input_path}")
    raw_features = []

    # Handle both full JSON and line-delimited JSON
    with open(input_path, "r", encoding="utf-8") as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "{":
            try:
                data = json.load(f)
                if "features" in data:
                    raw_features = data["features"]
                elif "elements" in data:
                    raw_features = data["elements"]
            except json.JSONDecodeError:
                f.seek(0)
                raw_features = [json.loads(line) for line in f if line.strip()]
        else:
            raw_features = [json.loads(line) for line in f if line.strip()]

    cleaned_features = []
    seen_ids = set()

    for idx, item in enumerate(raw_features):
        feat = normalise_feature(item, idx)
        if feat:
            osm_id = feat["properties"]["osm_id"]
            if osm_id not in seen_ids:
                seen_ids.add(osm_id)
                cleaned_features.append(feat)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    geojson_out = {
        "type": "FeatureCollection",
        "features": cleaned_features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_out, f, ensure_ascii=False, indent=2)

    logging.info(f"{len(cleaned_features)} facilities cleaned and saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and normalise raw OSM sports facility data.")
    parser.add_argument("-i", "--input", type=Path, default=Path("data/raw/osm_sample.json"), help="Path to the raw source file")
    parser.add_argument("-o", "--output", type=Path, default=Path("data/processed/facilities.geojson"), help="Path to the output GeoJSON file")
    
    args = parser.parse_args()
    clean_data(args.input, args.output)