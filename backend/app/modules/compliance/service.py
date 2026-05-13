from sqlalchemy import func, distinct, text, exists, or_
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
import json
import re
import collections
from datetime import datetime, timedelta
from app.modules.compliance.models import Phase, Building, DynamicPoint, Road

class GeoService:
    """الخدمة الجغرافية الأساسية لمعالجة وتحليل البيانات المكانية."""

    PRIORITY_ROADS = [
        "طريق المطار", "طريق الملك فهد", "طريق الملك خالد", "طريق الملك عبدالله",
        "طريق الأمير سلطان", "طريق ابها الخميس", "ابها-الخميس", "طريق الحزام",
        "شارع الفن", "طريق الفن", "طريق المحالة", "جامعة الملك خالد"
    ]

    @classmethod
    def _get_phase3_filter(cls, model):
        """مرشح المرحلة الثالثة (أنسنة المدن) بناءً على القرب من الطرق الرئيسية."""
        return exists().where(Road.geom.ST_DWithin(model.geom, 0.001)).where(
            or_(*[Road.name.ilike(f"%{r}%") for r in cls.PRIORITY_ROADS])
        )

    @classmethod
    def _apply_common_filters(cls, query, model, phase_id, municipality="all", street="all"):
        if municipality != "all":
            query = query.filter(model.municipality == municipality)
        
        if phase_id == 3:
            query = query.filter(cls._get_phase3_filter(model))
            if street != "all":
                street_col = func.json_extract_path_text(Building.properties, 'STREETNAME') if model == Building else None
                if street_col: query = query.filter(street_col == street)
        else:
            if phase_id: query = query.filter(model.phase_id == phase_id)
            if street != "all":
                street_col = func.json_extract_path_text(Building.properties, 'STREETNAME') if model == Building else None
                if street_col: query = query.filter(street_col == street)
        return query

    @staticmethod
    def _parse_date(date_str):
        if not date_str: return None
        clean_date = str(date_str).strip().split(' ')[0]
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try: return datetime.strptime(clean_date, fmt)
            except ValueError: continue
        return None

    @staticmethod
    def get_buildings_mvt(db: Session, z: int, x: int, y: int, phase_id: int = 1):
        roads_conditions = " OR ".join([f"r.name ILIKE '%{r}%'" for r in GeoService.PRIORITY_ROADS])
        sql = f"""
        WITH bounds AS (
            SELECT ST_TileEnvelope(:z, :x, :y) AS geom_3857,
                   ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326) AS geom_4326
        ),
        mvtgeom AS (
            SELECT ST_AsMVTGeom(ST_Transform(ST_MakeValid(b.geom), 3857), bounds.geom_3857) AS geom,
                   b.building_id, b.municipality, 
                   COALESCE(b.properties->>'STREETNAME', 'غير محدد') as streetname,
                   CASE WHEN b.is_compliant THEN 'ممتثل' ELSE 'غير ممتثل' END as compliance_status
            FROM compliance.buildings b, bounds
            WHERE (:phase_id = 3 OR b.phase_id = :phase_id) 
              AND b.geom && bounds.geom_4326
              AND ST_Intersects(b.geom, bounds.geom_4326)
              AND (:phase_id != 3 OR EXISTS (
                    SELECT 1 FROM compliance.roads r 
                    WHERE ST_DWithin(b.geom, r.geom, 0.001) AND ({roads_conditions})
              ))
        )
        SELECT ST_AsMVT(mvtgeom.*, 'buildings') FROM mvtgeom;
        """
        result = db.execute(text(sql), {"z": z, "x": x, "y": y, "phase_id": phase_id}).scalar()
        return result if result else b''

    @staticmethod
    def get_municipalities(db: Session, phase_id: int = None):
        if phase_id == 3:
            target_muns = ["أبها", "خميس مشيط", "أحد رفيدة"]
            query = db.query(Building.municipality).distinct().filter(Building.municipality.in_(target_muns))
            return sorted([m[0] for m in query.all() if m[0]])
        
        query = db.query(Building.municipality).distinct().filter(Building.municipality.isnot(None))
        if phase_id: query = query.filter(Building.phase_id == phase_id)
        return sorted([m[0] for m in query.all() if m[0]])

    @staticmethod
    def get_streets_by_municipality(db: Session, municipality: str, phase_id: int = None):
        street_col = func.json_extract_path_text(Building.properties, 'STREETNAME')
        query = db.query(street_col).distinct().filter(Building.properties.isnot(None))
        
        if municipality and municipality != "all":
            query = query.filter(Building.municipality == municipality)
            
        if phase_id == 3:
            filters = [street_col.ilike(f"%{s}%") for s in GeoService.PRIORITY_ROADS]
            query = query.filter(or_(*filters))
        elif phase_id:
            query = query.filter(Building.phase_id == phase_id)

        return sorted([s[0] for s in query.all() if s[0] and s[0] != 'null'])

    @staticmethod
    def get_kpis(db: Session, phase_id: int, municipality: str = "all", street: str = "all"):
        # 1. Target
        target_q = GeoService._apply_common_filters(db.query(func.count(Building.id)), Building, phase_id, municipality, street)
        total_target = target_q.scalar() or 0

        # 2. Total Issued
        total_issued_q = db.query(func.count(distinct(DynamicPoint.id))).filter(DynamicPoint.is_relevant == True)
        total_issued_q = GeoService._apply_common_filters(total_issued_q, DynamicPoint, phase_id, municipality)
        
        if street != "all":
            total_issued_q = total_issued_q.filter(exists().where(Building.properties['STREETNAME'].astext == street).where(func.ST_DWithin(DynamicPoint.geom, Building.geom, 0.000045)))
        
        total_issued = total_issued_q.scalar() or 0

        # 3. Linked
        compliant_q = db.query(func.count(distinct(Building.id)))
        compliant_q = GeoService._apply_common_filters(compliant_q, Building, phase_id, municipality, street)
        
        point_exists = exists().where(func.ST_DWithin(Building.geom, DynamicPoint.geom, 0.000045)).where(DynamicPoint.is_relevant == True)
        if phase_id != 3: point_exists = point_exists.where(DynamicPoint.phase_id == phase_id)
        
        compliant_q = compliant_q.filter(point_exists)
        total_linked = compliant_q.scalar() or 0

        return {
            "target": total_target, "total": total_issued, "issued": total_linked, 
            "spatial_gap": max(0, total_issued - total_linked), "pending": total_target - total_linked, 
            "coverage": round((total_linked / total_target * 100), 1) if total_target > 0 else 0.0,
            "spatial_match_percent": round((total_linked / total_issued * 100), 1) if total_issued > 0 else 0.0,
            "linked_certs": total_linked
        }

    @staticmethod
    def get_bounds(db: Session, phase_id: int, municipality: str = "all", street: str = "all"):
        try:
            query = GeoService._apply_common_filters(db.query(func.ST_Extent(Building.geom)), Building, phase_id, municipality, street)
            extent = query.scalar()
            if not extent: return None
            match = re.match(r'BOX\(([\d.-]+) ([\d.-]+),([\d.-]+) ([\d.-]+)\)', extent)
            if match:
                min_lon, min_lat, max_lon, max_lat = map(float, match.groups())
                return [[min_lon, min_lat], [max_lon, max_lat]]
        except Exception as e:
            print(f"Bounds Error: {e}"); return None

    @staticmethod
    def get_dynamic_points(db: Session, phase_id: int = None, municipality: str = "all", street: str = "all"):
        query = db.query(DynamicPoint).filter(DynamicPoint.is_relevant == True)
        query = GeoService._apply_common_filters(query, DynamicPoint, phase_id, municipality)
        
        if street != "all":
            query = query.filter(exists().where(Building.properties['STREETNAME'].astext == street).where(func.ST_DWithin(DynamicPoint.geom, Building.geom, 0.0005)))
        
        points = query.all()
        return [{
            "id": p.id, "name": p.name, "municipality": p.municipality, "status": p.status, "details": p.details,
            "geom_geojson": json.loads(json.dumps(to_shape(p.geom).__geo_interface__))
        } for p in points]

    @staticmethod
    def get_road_geometry(db: Session, phase_id: int, municipality: str, street_name: str):
        roads = db.query(Road).filter(Road.phase_id == phase_id, Road.municipality == municipality, Road.name == street_name).all()
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "geometry": json.loads(json.dumps(to_shape(r.geom).__geo_interface__)), "properties": {"id": r.road_id, "name": r.name}
            } for r in roads]
        } if roads else None

    @staticmethod
    def get_priority_roads(db: Session, phase_id: int):
        filters = [Road.name.ilike(f"%{term}%") for term in GeoService.PRIORITY_ROADS]
        roads = db.query(Road).filter(or_(*filters)).all()
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "geometry": json.loads(json.dumps(to_shape(r.geom).__geo_interface__)), 
                "properties": {"id": r.road_id, "name": r.name, "municipality": r.municipality}
            } for r in roads]
        }

    @staticmethod
    def get_growth_history(db: Session, phase_id: int, municipality: str = "all"):
        query = db.query(DynamicPoint.details).filter(DynamicPoint.is_relevant == True)
        query = GeoService._apply_common_filters(query, DynamicPoint, phase_id, municipality)
        
        points = query.all()
        daily_counts = collections.defaultdict(int)
        for p in points:
            dt = GeoService._parse_date(p[0].get('startDate') if p[0] else None)
            if dt: daily_counts[dt.date()] += 1
                
        if not daily_counts: return {"labels": [], "current": [], "previous": []}
        latest_date = max(daily_counts.keys())
        start_current = latest_date - timedelta(days=(latest_date.weekday() - 5) % 7)
        start_prev = start_current - timedelta(days=7)
        days_ar = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        return {
            "labels": days_ar,
            "current": [daily_counts.get(start_current + timedelta(days=i), 0) for i in range(7)],
            "previous": [daily_counts.get(start_prev + timedelta(days=i), 0) for i in range(7)]
        }

    @staticmethod
    def get_period_stats(db: Session, phase_id: int, municipality: str = "all"):
        query = db.query(DynamicPoint.details).filter(DynamicPoint.is_relevant == True)
        query = GeoService._apply_common_filters(query, DynamicPoint, phase_id, municipality)
            
        points = query.all()
        daily_counts = collections.defaultdict(int)
        for p in points:
            dt = GeoService._parse_date(p[0].get('startDate') if p[0] else None)
            if dt: daily_counts[dt.date()] += 1

        if not daily_counts: return {"weekly_growth": 0, "prev_week": 0, "current_week": 0, "quarter_total": 0}
        latest_date = max(daily_counts.keys())
        start_of_curr = latest_date - timedelta(days=latest_date.weekday())
        start_of_prev = start_of_curr - timedelta(days=7)
        curr_total = sum(v for k, v in daily_counts.items() if k >= start_of_curr)
        prev_total = sum(v for k, v in daily_counts.items() if start_of_prev <= k < start_of_curr)
        growth = round(((curr_total - prev_total) / prev_total * 100), 1) if prev_total > 0 else 100.0
        return {"weekly_growth": growth, "current_week": curr_total, "prev_week": prev_total, "quarter_total": sum(daily_counts.values())}

    @staticmethod
    def get_phase_metadata(db: Session, phase_id: int, municipality: str = "all", street: str = "all"):
        try:
            upd_q = GeoService._apply_common_filters(db.query(func.max(DynamicPoint.updated_at)), DynamicPoint, phase_id, municipality)
            res_q = GeoService._apply_common_filters(db.query(DynamicPoint.details['startDate']), DynamicPoint, phase_id, municipality)
            
            if phase_id == 3 and street != "all":
                point_street_filter = exists().where(Building.geom.ST_DWithin(DynamicPoint.geom, 0.0005)).where(Building.properties['STREETNAME'].astext == street)
                upd_q, res_q = upd_q.filter(point_street_filter), res_q.filter(point_street_filter)

            last_upd = upd_q.scalar() or datetime.now()
            dates = [d for d in [GeoService._parse_date(r[0]) for r in res_q.all()] if d]

            if not dates:
                return {"date_range": "لا توجد بيانات", "last_update": f"{last_upd.day}/{last_upd.month}/{last_upd.year}", "start_month": 0}

            min_d, max_d = min(dates), max(dates)
            return {
                "start_month": min_d.month, "start_year": min_d.year, "end_month": max_d.month, "end_year": max_d.year,
                "today_day": last_upd.day, "today_month": last_upd.month, "today_year": last_upd.year,
                "last_update": f"{last_upd.day}/{last_upd.month}/{last_upd.year}"
            }
        except Exception as e:
            print(f"Metadata Error: {e}"); now = datetime.now()
            return {"date_range": "خطأ", "last_update": f"{now.day}/{now.month}/{now.year}", "start_month": 0}

