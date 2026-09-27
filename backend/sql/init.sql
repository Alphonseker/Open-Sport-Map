-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create facilities table supporting multi-source data
CREATE TABLE IF NOT EXISTS facilities (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL DEFAULT 'osm',
    source_id VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    sport VARCHAR(100),
    surface VARCHAR(100),
    access VARCHAR(50),
    lit VARCHAR(50),
    geom GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_source_record UNIQUE (source, source_id)
);

-- GiST spatial index for high-performance geo-queries
CREATE INDEX IF NOT EXISTS idx_facilities_geom ON facilities USING GIST (geom);