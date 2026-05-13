import psycopg2
conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
cur = conn.cursor()
# Get a building in phase 1
cur.execute("SELECT ST_X(ST_Centroid(geom)), ST_Y(ST_Centroid(geom)) FROM compliance.buildings WHERE phase_id = 1 LIMIT 1")
lon, lat = cur.fetchone()
print(f"Sample building at: {lon}, {lat}")

# Calculate tile coordinates for zoom 15
import math
zoom = 15
lat_rad = math.radians(lat)
n = 2.0 ** zoom
xtile = int((lon + 180.0) / 360.0 * n)
ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
print(f"Tile coordinates (z,x,y): {zoom}, {xtile}, {ytile}")

# Test the MVT query
sql = """
WITH bounds AS (SELECT ST_TileEnvelope(%s, %s, %s) AS geom),
mvtgeom AS (
    SELECT ST_AsMVTGeom(ST_Transform(b.geom, 3857), bounds.geom) AS geom,
           b.building_id, b.municipality, b.properties->>'STREETNAME' as streetname,
           CASE WHEN b.is_compliant THEN 'ممتثل' ELSE 'غير ممتثل' END as compliance_status
    FROM compliance.buildings b, bounds
    WHERE b.phase_id = 1 
      AND ST_Intersects(b.geom, ST_Transform(bounds.geom, 4326))
)
SELECT ST_AsMVT(mvtgeom.*, 'buildings') FROM mvtgeom;
"""
cur.execute(sql, (zoom, xtile, ytile))
mvt = cur.fetchone()[0]
print(f"MVT size: {len(mvt)} bytes")
conn.close()
