# Open Sport Map

An open-source mapping platform for locating freely accessible sports facilities near a specific address or location (street workout areas, football fields, basketball courts, multi-sport courts, running tracks, etc.).

## Technical stack
- **Data Source :** OpenStreetMap ([Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API))
- **Base Spatiale :** PostgreSQL 16 + PostGIS
- **Backend :** Python
- **Frontend (Web):** [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)

## Quick Start (Local)

## Project Evolution in the Future

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
└── data clean up
       │
       ▼
V2
│
├── users
├── quality of sport infrastructure
├── photos
└── contributions
```

## Whole Process Explanations for me to remember

### 1. Fetch OSM data - python script

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