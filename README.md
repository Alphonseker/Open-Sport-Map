# Open Sport Map

An open-source mapping platform for locating freely accessible sports facilities near a specific address or location (street workout areas, football fields, basketball courts, multi-sport courts, running tracks, etc.).

## Technical stack
- **Data Source :** OpenStreetMap (Overpass API)
- **Base Spatiale :** PostgreSQL 16 + PostGIS
- **Backend :** Python
- **Frontend (Web):** MapLibre GL JS

## Quick Start (Local)

### 1. Start the PostGIS spatial database
```bash
docker compose up -d
```

## Project Evolution

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

