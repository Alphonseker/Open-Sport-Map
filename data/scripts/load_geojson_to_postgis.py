import argparse
import json
import logging
from pathlib import Path
import psycopg

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_CONFIG = {
    "dbname": "open_sport_map",
    "user": "spotter",
    "password": "spotter_password",
    "host": "localhost",
    "port": 5433
}

def load_and_insert_facilities(geojson_path: Path):
    if not geojson_path.exists():
        logging.error(f"File not found: {geojson_path}")
        return

    logging.info(f"Reading GeoJSON file: {geojson_path}...")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    features = geojson_data.get("features", [])
    if not features:
        logging.warning("No features found in the GeoJSON file.")
        return

    records = []
    for feat in features:
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = coords[0], coords[1]
        wkt_geom = f"SRID=4326;POINT({lon} {lat})"

        records.append((
            "osm",
            str(props.get("osm_id")),
            props.get("name"),
            props.get("sport"),
            props.get("surface"),
            props.get("access"),
            props.get("lit"),
            wkt_geom
        ))

    insert_query = """
    INSERT INTO facilities (source, source_id, name, sport, surface, access, lit, geom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))
    ON CONFLICT (source, source_id) DO UPDATE SET
        name = EXCLUDED.name,
        sport = EXCLUDED.sport,
        surface = EXCLUDED.surface,
        access = EXCLUDED.access,
        lit = EXCLUDED.lit,
        geom = EXCLUDED.geom;
    """

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_query, records)
            conn.commit()
        logging.info(f"Success: {len(records)} facilities inserted/updated in PostGIS.")

    except Exception as e:
        logging.error(f"Failed to insert into database: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest normalized GeoJSON into PostGIS.")
    parser.add_argument("-i", "--input", type=Path, default=Path("data/processed/facilities.geojson"), help="Path to the GeoJSON file to insert into PostGIS")
    args = parser.parse_args()
    
    load_and_insert_facilities(args.input)