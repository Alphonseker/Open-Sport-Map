# Open Sport Map

An open-source mapping platform for locating freely accessible sports facilities near a specific address or location (street workout areas, football fields, basketball courts, multi-sport courts, running tracks, etc.).




## Stack Technique
- **Data Source :** OpenStreetMap (Overpass API)
- **Base Spatiale :** PostgreSQL 16 + PostGIS
- **Backend :** Python
- **Frontend (Web):** MapLibre GL JS

## Quick Start (Local)

### 1. Start the PostGIS spatial database
```bash
docker compose up -d