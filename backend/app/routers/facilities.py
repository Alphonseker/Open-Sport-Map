import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.database import get_db_cursor

router = APIRouter(prefix="/api/v1/facilities", tags=["Facilities"])

@router.get("/nearby")
def get_nearby_facilities(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    radius: int = Query(1000, ge=50, le=10000, description="Search radius in meters (max 10 km)"),
    sport: Optional[str] = Query(None, description="Optional sport filter (e.g. basketball, fitness)")
):
    """
    Search for sports facilities within a given radius using PostGIS spatial indexing.
    Returns a standardized RFC 7946 GeoJSON FeatureCollection.
    """
    # Base spatial SQL query using ST_DWithin on spherical geography
    query = """
    SELECT 
        id,
        source,
        source_id,
        name,
        sport,
        surface,
        access,
        lit,
        ROUND(ST_Distance(geom::geography, ST_MakePoint(%s, %s)::geography)) AS distance_meters,
        ST_AsGeoJSON(geom)::json AS geojson_geom
    FROM facilities
    WHERE ST_DWithin(geom::geography, ST_MakePoint(%s, %s)::geography, %s)
    """
    params = [lon, lat, lon, lat, radius]

    # Optional sport filtering
    if sport:
        query += " AND LOWER(sport) LIKE LOWER(%s)"
        params.append(f"%{sport}%")

    query += " ORDER BY distance_meters ASC LIMIT 50;"

    try:
        with get_db_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        # Build GeoJSON FeatureCollection response
        features = []
        for row in rows:
            features.append({
                "type": "Feature",
                "geometry": row["geojson_geom"],
                "properties": {
                    "id": row["id"],
                    "source": row["source"],
                    "source_id": row["source_id"],
                    "name": row["name"],
                    "sport": row["sport"],
                    "surface": row["surface"],
                    "access": row["access"],
                    "lit": row["lit"],
                    "distance_meters": row["distance_meters"]
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

@router.get("/bbox")
def get_facilities_in_bbox(
    min_lon: float = Query(..., ge=-180.0, le=180.0, description="Minimum longitude (West)"),
    min_lat: float = Query(..., ge=-90.0, le=90.0, description="Minimum latitude (South)"),
    max_lon: float = Query(..., ge=-180.0, le=180.0, description="Maximum longitude (East)"),
    max_lat: float = Query(..., ge=-90.0, le=90.0, description="Maximum latitude (North)"),
    sport: Optional[str] = Query(None, description="Optional sport filter")
):
    """
    Retrieve facilities inside a bounding box envelope.
    Uses PostGIS spatial index operator (&&) with ST_MakeEnvelope.
    """
    if min_lon >= max_lon or min_lat >= max_lat:
        raise HTTPException(
            status_code=400,
            detail="Invalid bounding box: min coordinates must be strictly less than max coordinates."
        )

    # ST_MakeEnvelope(minX, minY, maxX, maxY, srid)
    # The '&&' operator leverages the GiST index directly for maximum lookup speed
    query = """
    SELECT 
        id,
        source,
        source_id,
        name,
        sport,
        surface,
        access,
        lit,
        ST_AsGeoJSON(geom)::json AS geojson_geom
    FROM facilities
    WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
    """
    params = [min_lon, min_lat, max_lon, max_lat]

    if sport:
        query += " AND LOWER(sport) LIKE LOWER(%s)"
        params.append(f"%{sport}%")

    query += " LIMIT 200;"

    try:
        with get_db_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        features = [
            {
                "type": "Feature",
                "geometry": row["geojson_geom"],
                "properties": {
                    "id": row["id"],
                    "source": row["source"],
                    "source_id": row["source_id"],
                    "name": row["name"],
                    "sport": row["sport"],
                    "surface": row["surface"],
                    "access": row["access"],
                    "lit": row["lit"]
                }
            }
            for row in rows
        ]

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")