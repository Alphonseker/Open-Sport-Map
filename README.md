# **Open Sport Map**

An open-source mapping platform for locating freely accessible sports facilities near a specific address or location (street workout areas, football fields, basketball courts, multi-sport courts, running tracks, etc.).

## **Technical stack**
- **Data Source :** OpenStreetMap ([Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API))
- **Base Spatiale :** PostgreSQL 16 + PostGIS
- **Backend :** Python
- **Frontend (Web):** [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)

## **Quick Start (Local)**

## **Project Evolution in the Future**

```
V1
│
├── OSM data
├── PostgreSQL/PostGIS
├── Python API
├── web map
├── geographical research
└── sport filters
       │
       ▼
V1.5
│
├── Data ES
├── sources merging
└── data clean up (no more private POI)
       │
       ▼
V2
│
├── users
├── quality of sport infrastructure
├── photos
└── contributions
```

## **Whole Process Explanation**

### **1. OSM data ETL segment**
#### **1.1 Fetch data - python scrip**t

Retrieving ```node``` (isolated point of interests) and ```way``` (polygons and surfaces) that have tags we are looking for:<br>
- ```leisure=pitch```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=pitch)*</sub>
- ```leisure=fitness_station```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=fitness_station)*</sub>
- ```leisure=track```<sub>*[more info](https://wiki.openstreetmap.org/wiki/Tag:leisure=track)*</sub>

Using Overpass Turbo, we can get a preview of the data we are retrieving ! See a short example [here](https://overpass-turbo.eu/s/2wZq), and hot the "Execute" button.

*see [Overpass Query Language Documentation](https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide) for more global details*

Execute the python script at the root of the project with the command: <br>
```bash
python data/scripts/fetch_osm_data.py
```
We now have the sport features data of the selected area, stored in: ``open-sport-map\data\raw\osm_sample.json``

#### **1.2 Clean data - python script**

We clean the retrieved data with a python script, formatting to GeoJSON. <br>
```bash
python data/scripts/clean_osm_data.py
```

We can visualize the cleaned data on [geojson.io](https://geojson.io) website, by dragging the GeoJSOnon the page !

#### **1.3 Setup PostGIS**

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

> **Spatial Indexing & Constraints:**
> - `CONSTRAINT unique_source_record UNIQUE (source, source_id)`: Prevents duplicate imports from the same provider while allowing multi-source deduplication.
> - `CREATE INDEX idx_facilities_geom ON facilities USING GIST (geom)`: Generalized Search Tree (GiST) spatial index for sub-millisecond bounding box and radius queries (`ST_DWithin`).

Then we use a python script to load the GeoJSON data into the indexed table PostGIS.