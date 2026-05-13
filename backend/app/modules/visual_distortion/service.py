from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import re
from app.modules.visual_distortion.models import VisualDistortionReport

class VisualDistortionService:
    PRIORITY_ROADS = [
        'طريق المطار', 'طريق الملك فهد', 'طريق الملك خالد', 'طريق الملك عبدالله',
        'طريق الأمير سلطان', 'طريق ابها الخميس', 'ابها-الخميس', 'طريق الحزام',
        'طريق الفن', 'شارع الفن', 'طريق المحالة', 'جامعة الملك خالد'
    ]

    @classmethod
    def _get_roads_clause(cls):
        conditions = " OR ".join([f"r.name ILIKE '%{name}%'" for name in cls.PRIORITY_ROADS])
        return f"""
            EXISTS (
                SELECT 1 FROM compliance.roads r
                WHERE ST_DWithin(visual_distortion.visual_distortion_reports.geom, r.geom, 0.001)
                AND ({conditions})
            )
        """

    @classmethod
    def _apply_filters(cls, base_sql: str, municipality: str = "all", params: dict = None):
        if params is None: params = {}
        where_clauses = [cls._get_roads_clause()]
        
        if municipality != "all":
            where_clauses.append("municipality = :mun")
            params["mun"] = municipality
            
        if " WHERE " in base_sql.upper():
            sql = base_sql + " AND " + " AND ".join(where_clauses)
        else:
            sql = base_sql + " WHERE " + " AND ".join(where_clauses)
            
        return sql, params

    @classmethod
    def _get_fake_history_cte(cls, municipality: str = "all"):
        roads_filter = cls._get_roads_clause()
        mun_filter = "AND municipality = :mun" if municipality != "all" else ""
        return f'''
            SELECT 
                municipality, classification_name, management_group, report_status, assignment_date,
                LAG(report_status) OVER (
                    PARTITION BY municipality, classification_name, ROUND(longitude::numeric, 4), ROUND(latitude::numeric, 4) 
                    ORDER BY assignment_date
                ) as prev_status
            FROM visual_distortion.visual_distortion_reports
            WHERE {roads_filter} {mun_filter}
        '''

    @staticmethod
    def get_municipalities(db: Session):
        query = db.query(VisualDistortionReport.municipality).distinct().filter(VisualDistortionReport.municipality.isnot(None))
        return sorted([m[0] for m in query.all() if m[0]])

    @staticmethod
    def get_kpis(db: Session, municipality: str = "all"):
        sql = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE management_group = 'Regulatory & Policy') as policy,
                COUNT(*) FILTER (WHERE management_group = 'Resource & Funding') as resource,
                COUNT(*) FILTER (WHERE report_status = 'مغلق') as closed
            FROM visual_distortion.visual_distortion_reports
        """
        sql, params = VisualDistortionService._apply_filters(sql, municipality)
        result = db.execute(text(sql), params).fetchone()
        
        total = result[0] or 0
        policy = int(result[1] or 0)
        resource = int(result[2] or 0)
        total_closed = int(result[3] or 0)
        
        fake_result = VisualDistortionService.get_fake_closures_kpi(db, municipality)
        fake_count = fake_result.get("fake_closures", 0)

        validated_closed = max(0, total_closed - fake_count)
        completion_rate = round((validated_closed / total) * 100, 1) if total > 0 else 0

        return {
            "total": total, "policy": policy, "resource": resource,
            "completion_rate": completion_rate, "integrity_gap": fake_count
        }

    @staticmethod
    def get_points(db: Session, municipality: str = "all"):
        sql = """
            SELECT id, municipality, report_status as status, classification_name as classification, 
                   management_group as group, report_number, ST_AsGeoJSON(geom) as geom_geojson
            FROM visual_distortion.visual_distortion_reports
        """
        sql, params = VisualDistortionService._apply_filters(sql, municipality)
        sql += " ORDER BY assignment_date DESC LIMIT 2000"
        results = db.execute(text(sql), params).fetchall()
        
        return [{
            "id": r.id, "municipality": r.municipality, "status": r.status,
            "classification": r.classification, "group": r.group, "report_number": r.report_number,
            "geom_geojson": json.loads(r.geom_geojson) if r.geom_geojson else None
        } for r in results]

    @staticmethod
    def get_fake_closures_kpi(db: Session, municipality: str = "all"):
        cte = VisualDistortionService._get_fake_history_cte(municipality)
        query = f"WITH location_history AS ({cte}) SELECT COUNT(*) FROM location_history WHERE prev_status = 'مغلق' AND report_status != 'مغلق آليا'"
        params = {"mun": municipality} if municipality != "all" else {}
        fake_count = db.execute(text(query), params).scalar() or 0
        return {"fake_closures": int(fake_count)}

    @staticmethod
    def get_classifications(db: Session, municipality: str = "all"):
        sql, params = VisualDistortionService._apply_filters(
            "SELECT classification_name, COUNT(*) as count, management_group FROM visual_distortion.visual_distortion_reports WHERE classification_name IS NOT NULL",
            municipality
        )
        sql += " GROUP BY classification_name, management_group ORDER BY count DESC LIMIT 10"
        results = db.execute(text(sql), params).fetchall()
        return [{"name": r[0], "count": r[1], "group": r[2]} for r in results]

    @staticmethod
    def get_top_municipalities(db: Session):
        sql, _ = VisualDistortionService._apply_filters(
            "SELECT municipality, COUNT(*) as count FROM visual_distortion.visual_distortion_reports WHERE municipality IS NOT NULL"
        )
        sql += " GROUP BY municipality ORDER BY count DESC LIMIT 5"
        results = db.execute(text(sql)).fetchall()
        return [{"name": r[0], "count": r[1]} for r in results]

    @staticmethod
    def get_worst_fake_closures_locations(db: Session, municipality: str = "all"):
        cte = VisualDistortionService._get_fake_history_cte(municipality)
        query = f"""
            WITH location_history AS ({cte})
            SELECT municipality, classification_name, management_group, COUNT(*) as fake_count
            FROM location_history WHERE prev_status = 'مغلق' AND report_status != 'مغلق آليا'
            GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 5
        """
        params = {"mun": municipality} if municipality != "all" else {}
        results = db.execute(text(query), params).fetchall()
        return [{"municipality": r[0], "classification": r[1], "group": r[2], "recurrences": r[3]} for r in results]

    @staticmethod
    def get_status_breakdown(db: Session, municipality: str = "all"):
        sql, params = VisualDistortionService._apply_filters(
            "SELECT report_status as status, COUNT(*) as count FROM visual_distortion.visual_distortion_reports",
            municipality
        )
        sql += " GROUP BY report_status"
        results = db.execute(text(sql), params).fetchall()
        return [{"status": r.status, "count": r.count} for r in results]

    @staticmethod
    def get_bounds(db: Session, municipality: str = "all"):
        sql, params = VisualDistortionService._apply_filters(
            "SELECT ST_Extent(geom) FROM visual_distortion.visual_distortion_reports",
            municipality
        )
        result = db.execute(text(sql), params).scalar()
        if not result: return None
        match = re.match(r'BOX\(([\d.-]+) ([\d.-]+),([\d.-]+) ([\d.-]+)\)', result)
        if match:
            min_lon, min_lat, max_lon, max_lat = map(float, match.groups())
            return [[min_lon, min_lat], [max_lon, max_lat]]
        return None

    @staticmethod
    def get_monthly_performance(db: Session, municipality: str = "all"):
        sql, params = VisualDistortionService._apply_filters(
            "SELECT TO_CHAR(assignment_date, 'YYYY-MM') as month, COUNT(*) as count FROM visual_distortion.visual_distortion_reports",
            municipality
        )
        sql += " GROUP BY 1 ORDER BY 1"
        results = db.execute(text(sql), params).fetchall()
        return [{"month": r[0], "count": r[1]} for r in results]

    @staticmethod
    def get_fake_closures_drilldown(db: Session, municipality: str, classification: str):
        query = text('''
            SELECT MAX(report_number) as report_number, COUNT(*) as count
            FROM visual_distortion.visual_distortion_reports
            WHERE municipality = :mun AND classification_name = :cls
            GROUP BY ROUND(longitude::numeric, 3), ROUND(latitude::numeric, 3)
            HAVING COUNT(*) > 1 AND SUM(CASE WHEN report_status = 'مغلق' THEN 1 ELSE 0 END) > 0
            ORDER BY count DESC LIMIT 100
        ''')
        results = db.execute(query, {"mun": municipality, "cls": classification}).fetchall()
        return [{"report_number": r[0], "count": r[1]} for r in results]

    @staticmethod
    def get_municipality_grid_stats(db: Session):
        roads_filter = VisualDistortionService._get_roads_clause()
        cte = VisualDistortionService._get_fake_history_cte()
        sql = f"""
            WITH municipality_stats AS (
                SELECT municipality, COUNT(*) as total_reports, AVG(longitude) as lon, AVG(latitude) as lat
                FROM visual_distortion.visual_distortion_reports
                WHERE municipality IS NOT NULL AND {roads_filter} GROUP BY municipality
            ),
            fake_closure_stats AS (
                SELECT municipality, COUNT(*) as fake_count
                FROM ({cte}) sub WHERE prev_status = 'مغلق' AND report_status != 'مغلق آليا' GROUP BY municipality
            )
            SELECT m.municipality, m.total_reports, COALESCE(f.fake_count, 0) as fake_count, m.lon, m.lat
            FROM municipality_stats m LEFT JOIN fake_closure_stats f ON m.municipality = f.municipality
        """
        results = db.execute(text(sql)).fetchall()
        return [{
            "municipality": r[0], "total": r[1], "fake_count": r[2],
            "score": round((r[2] / r[1] * 100), 2) if r[1] > 0 else 0, "center": [r[3], r[4]]
        } for r in results]

    @staticmethod
    def get_dashboard_summary(db: Session, municipality: str = "all"):
        kpis = VisualDistortionService.get_kpis(db, municipality)
        points = VisualDistortionService.get_points(db, municipality)
        classifications = VisualDistortionService.get_classifications(db, municipality)
        status_breakdown = VisualDistortionService.get_status_breakdown(db, municipality)
        monthly_performance = VisualDistortionService.get_monthly_performance(db, municipality)
        worst_locations = VisualDistortionService.get_worst_fake_closures_locations(db, municipality)
        top_muns = VisualDistortionService.get_top_municipalities(db) if municipality == "all" else []
            
        return {
            "kpis": kpis, "points": points, "classifications": classifications,
            "status_breakdown": [{"name": s["status"], "count": s["count"]} for s in status_breakdown],
            "monthly_performance": monthly_performance, "worst_locations": worst_locations,
            "top_municipalities": top_muns
        }

