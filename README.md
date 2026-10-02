# **Open Sport Map**

An open-source mapping platform for locating freely accessible sports facilities near a specific address or location (street workout areas, football fields, basketball courts, multi-sport courts, running tracks, etc.).

## **Technical stack**
- **Data Source :** OpenStreetMap ([Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API))
- **Base Spatiale :** PostgreSQL 16 + PostGIS
- **Backend :** Python
- **Frontend (Web):** [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)

## **Project Roadmap**

```
V1
       │
- [x] OSM data
- [x] PostgreSQL/PostGIS
- [x] Python API
- [x] web map
- [x] geographical research
- [x] sport filters
       │
       ▼
V1.5
       │
- [ ] Augment dataset
- [ ] RES Data (for France data)
- [ ] sources merging
- [ ] data clean up (no more private POI)
       │
       ▼
V2
       │
- [ ] facility photos
```

## **Quick Start (Local)**

### **1. Prerequisites**
- Docker Desktop installed and running
- Python 3.11 or more installed

### **2. Environment Setup**

Create and activate the isolated Python virtual evironment, on Windows Powershell:
```bash
python -m venv .venv
```
```bash
.venv\Scripts\Activate.ps1
```
Install project dependencies:
```bash
pip install -r requirements.txt
```

### **3. Start Spacial Database***
Start the PostgreSQL/PostGIS container and initialize the schema:

```bash
docker-compose up -d
```
```bash
Get-Content backend/sql/init.sql | docker exec -i open_sport_map_db psql -U spotter -d open_sport_map
```

> [!NOTE]
> Please note that the PostGIS container will launch on port 5433

### **4. Run the data pipeline**

```bash
python data/scripts/fetch_osm_data.py
python data/scripts/clean_osm_data.py
python data/scripts/load_geojson_to_postgis.py
```

## **Step-by-Step Achitecture**

### **1. OSM data ETL pipeline**
#### **1.1 Fetch data - python scrip**t

Retrieving ```node``` (isolated point of interests) and ```wa y``` (polygons and surfaces) that have tags we are looking for:<br>
- ```leisure=pitch```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=pitch)*</sub>
- ```leisure=fitness_station```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=fitness_station)*</sub>
- ```leisure=track```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=track)*</sub>

Thequery uses ``out center tags;`` to automatically calculate the centroid coordinates for polygons (``way``), simplifying point ingestion.

Using Overpass Turbo, we can get a preview of the data we are retrieving ! See a short example [here](https://overpass-turbo.eu/s/2wZq), and hit the "Execute" button.

*see [Overpass Query Language Documentation](https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide) for more global details.*

Execute the python script at the root of the project: <br>
```bash
python data/scripts/fetch_osm_data.py
```
We now have the sport features data of the selected area, stored in: ``open-sport-map\data\raw\osm_sample.json``

#### **1.2 Clean data - python script**

We clean the retrieved data with a python script, formatting to GeoJSON. <br>
```bash
python data/scripts/clean_osm_data.py
```

Output data is stored at ``data/processed/facilities.geojson``, and we can visualize it on [geojson.io](https://geojson.io) website, by dragging the GeoJSON in the page !

### **2. Spatial Storage Layer (PostgreSQL + PostGIS)**

#### **2.1 Table Setup**

The spatial storage layer relies on **PostgreSQL 16** with the **PostGIS** extension. Geospatial coordinates are converted and indexed as native geometry points in the standard **WGS 84 (EPSG:4326)** coordinate reference system.

**Table: `facilities`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Internal unique identifier |
| `source` | `VARCHAR(50)` | `NOT NULL` | Data provider (e.g. `osm`, `res_france`) |
| `source_id` | `VARCHAR(100)` | `NOT NULL` | Original identifier within the source platform |
| `name` | `VARCHAR(255)` | | Facility name (if available) |
| `sport` | `VARCHAR(100)` | | Normalized sport category (`basketball`, `fitness`, etc.) |
| `surface` | `VARCHAR(100)` | | Surface material (`asphalt`, `rubber`, `grass`...) |
| `access` | `VARCHAR(50)` | | Access permission (`yes`, `public`, `private`...) |
| `lit` | `VARCHAR(50)` | | Night lighting status (`yes`, `no`, `unknown`) |
| `geom` | `GEOMETRY(Point, 4326)` | `NOT NULL` | Point geometry in WGS 84 |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Record insertion timestamp |

<br>

**Spatial Indexing & Constraints:**
- `CONSTRAINT unique_source_record UNIQUE (source, source_id)`: Prevents duplicate imports from the same provider while allowing multi-source deduplication.
- `CREATE INDEX idx_facilities_geom ON facilities USING GIST (geom)`: Generalized Search Tree (GiST) spatial index for sub-millisecond bounding box and radius queries (`ST_DWithin`).

#### **2.2 Ingesting GeoJSON (``load_geojson_to_postgis.py``)**

We parse our GeoJSON data file and we use `psycopg` to insert batch records into PostGIS:

```bash
python data/scripts/load_geojson_to_postgis.py
```

#### **2.3 Verify and test the content of the table**

#### **2.3.1 Verify the content of the table**

See the total number of lines and a preview of the data:

```powershell
docker exec -it open_sport_map_db psql -U spotter -d open_sport_map -c "
SELECT 
    id, 
    source_id, 
    name, 
    sport, 
    surface, 
    ST_AsText(geom) AS coordinates 
FROM facilities 
LIMIT 5;
"
```

- `ST_AsText(geom)` convert the internal binary format of PostGIS into readable text `Point (lon lat)`

#### **2.3.2 Test a proximity spacial request**

In this section we will try the powerful function `ST_DWithin`:
For the experiment, we select a random point in the center of Valenciennes (french city).
- longitude: 3.523
- latitude:  50.358

We try to find facilities within 800 meters from our point, sorted by proximity with the exact ditsance calculated:

```bash
docker exec -it open_sport_map_db psql -U spotter -d open_sport_map -c "
SELECT 
    name,
    sport,
    surface,
    ROUND(ST_Distance(geom::geography, ST_MakePoint(3.523, 50.358)::geography)) AS distance_meters
FROM facilities
WHERE ST_DWithin(geom::geography, ST_MakePoint(3.523, 50.358)::geography, 800)
ORDER BY distance_meters ASC;
"
```

- `ST_MakePoint(lon, lat)` create a geometrical point
- `::geography` converts WGS 84 geometry (in degrees) to spherical geography. This allows PostGIS to calculate distances directly in **actual meters on the Earth** instead of angular units.
- `ST_DWithin(..., 800)` filters results withi 800 meter distance
- `ST_Distance(...)` work out the exact distance

### **3. Backend API Layer (FastAPI)**

The API bridges the PostGIS spatial database and the web interface, exposing endpoints that directly return RFC 7946 GeoJSON collections.

#### **3.1 Start the Server**

Run Uvicorn from the project root with hot-reload enabled:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- **API Base URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`

#### **3.2 Endpoints**

#### **3.2.1. Radius Search (`GET /api/v1/facilities/nearby`)**
Searches for facilities within a given distance from a central geographic point.

- **Query Parameters:**
  - `lat`: Latitude in decimal degrees (-90 to 90).
  - `lon`: Longitude in decimal degrees (-180 to 180).
  - `radius` (default: `1000`): Search radius in meters (50 to 10 000 m).
  - `sport`: Filter by sport name (e.g.: basketball, fitness).
- **Spatial Mechanism:** PostGIS `ST_DWithin` evaluated on spherical `geography` types with `ST_Distance` calculation.

#### **3.2.2. Bounding Box Viewport (`GET /api/v1/facilities/bbox`)**
Retrieves all facilities located within the current map viewport as the user pans or zooms.

- **Query Parameters:**
  - `min_lon`, `min_lat`: South-West bounding coordinate.
  - `max_lon`, `max_lat`: North-East bounding coordinate.
  - `sport`: Sport type filter.
- **Spatial Mechanism:** Evaluates envelope intersections using `ST_MakeEnvelope` and the high-speed spatial overlap operator `&&` powered by the GiST index.

### **4. Web Map (Frontend)**

The frontend is an interactive single-page application built with **MapLibre GL JS**, an open-source WebGL-accelerated mapping engine. It consumes the FastAPI backend directly, dynamically fetching and displaying GeoJSON data according to the current map view.

#### **4.1 How It Works**

- **Vector Rendering:** Renders map tiles and data points natively on the client GPU for high-frame-rate navigation.
- **Dynamic Bounding Box Ingestion:** Whenever the user pans or zooms, the map calculates its bounding coordinates (`min_lon`, `min_lat`, `max_lon`, `max_lat`) and queries the `/api/v1/facilities/bbox` endpoint.
- **Categorical Styling:** Facilities are visually classified by sport type (e.g. basketball, fitness, soccer, running) using dedicated color schemes.
- **Popups & Geolocation:** Clicking on any point displays detailed facility metadata (name, surface material, lighting status). A "Locate me" control triggers HTML5 browser geolocation to pan directly to the user's location.

#### **4.2 Running the Frontend Locally**

1. Ensure the backend API is running on port 8000:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

2. Open a separate terminal, navigate to the `frontend/` directory, and start a local HTTP server:
```bash
cd frontend
python -m http.server 3000
```

3. Open your browser and access the interactive map at:
   **`http://localhost:3000`**