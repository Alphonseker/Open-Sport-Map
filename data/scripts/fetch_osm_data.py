import json
import logging # Standard logging module for logging messages displayed to the console
from pathlib import Path
import requests # HTTP library for making requests to the Overpass API

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Target area: city name to search within
CITY_NAME = "Valenciennes"

# Overpass QL Query:
# We look for sports pitches, fitness stations, and athletics tracks within the city area.
# 'out center;' calculates a center point for ways/polygons.
OVERPASS_QUERY = f"""
[out:json][timeout:30];
area["name"="{CITY_NAME}"]["admin_level"="8"]->.searchArea;
(
  node["leisure"="pitch"](area.searchArea);
  way["leisure"="pitch"](area.searchArea);

  node["leisure"="fitness_station"](area.searchArea);
  way["leisure"="fitness_station"](area.searchArea);

  node["leisure"="track"](area.searchArea);
  way["leisure"="track"](area.searchArea);
);
out center tags;
"""

def fetch_sports_facilities() -> dict:
    logging.info(f"Querying Overpass API for facilities in {CITY_NAME}...")
    response = requests.post(
        OVERPASS_URL,
        data={"data": OVERPASS_QUERY},
        headers={"User-Agent": "OpenSportMap/0.1"}
    )
    response.raise_for_status()
    return response.json()

def save_raw_data(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"Raw data saved to {output_path} ({len(data.get('elements', []))} elements found)")

if __name__ == "__main__":
    raw_data = fetch_sports_facilities()
    target_file = Path("data/raw/osm_sample.json")
    save_raw_data(raw_data, target_file)