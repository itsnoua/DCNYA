from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.modules.compliance.service import GeoService

router = APIRouter()

@router.get("/buildings/tiles/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int, phase_id: int = 1, db: Session = Depends(get_db)):
    tile_data = GeoService.get_buildings_mvt(db, z, x, y, phase_id)
    from fastapi import Response
    return Response(content=tile_data, media_type="application/x-protobuf")

@router.get("/municipalities")
def get_municipalities(phase_id: int = None, db: Session = Depends(get_db)):
    return GeoService.get_municipalities(db, phase_id)

@router.get("/streets")
def get_streets(municipality: str, phase_id: int = None, db: Session = Depends(get_db)):
    return GeoService.get_streets_by_municipality(db, municipality, phase_id)

@router.get("/kpis")
def get_kpis(phase_id: int, municipality: str = "all", street: str = "all", db: Session = Depends(get_db)):
    try:
        kpis = GeoService.get_kpis(db, phase_id, municipality, street)
        kpis["period_stats"] = GeoService.get_period_stats(db, phase_id, municipality)
        return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kpis/history")
def get_kpis_history(phase_id: int, municipality: str = "all", db: Session = Depends(get_db)):
    history = GeoService.get_growth_history(db, phase_id, municipality)
    stats = GeoService.get_period_stats(db, phase_id, municipality)
    return {"history": history, "stats": stats}

@router.get("/points")
def get_points(phase_id: int, municipality: str = "all", street: str = "all", db: Session = Depends(get_db)):
    return GeoService.get_dynamic_points(db, phase_id, municipality, street)

@router.get("/bounds")
def get_bounds(phase_id: int, municipality: str = "all", street: str = "all", db: Session = Depends(get_db)):
    return {"bounds": GeoService.get_bounds(db, phase_id, municipality, street)}

@router.get("/roads")
def get_roads(phase_id: int, municipality: str, street: str, db: Session = Depends(get_db)):
    return GeoService.get_road_geometry(db, phase_id, municipality, street)

@router.get("/priority-roads")
def get_priority_roads(phase_id: int, db: Session = Depends(get_db)):
    return GeoService.get_priority_roads(db, phase_id)

@router.get("/phase-metadata")
def get_phase_metadata(phase_id: int, municipality: str = "all", street: str = "all", db: Session = Depends(get_db)):
    """يرجع نطاق تواريخ البيانات وآخر تحديث من قاعدة البيانات لمرحلة معينة مع الفلترة."""
    return GeoService.get_phase_metadata(db, phase_id, municipality, street)
