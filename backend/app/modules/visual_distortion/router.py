from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.modules.visual_distortion.service import VisualDistortionService

router = APIRouter()

@router.get("/municipalities")
def get_municipalities(db: Session = Depends(get_db)):
    return VisualDistortionService.get_municipalities(db)

@router.get("/kpis")
def get_kpis(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_kpis(db, municipality)

@router.get("/points")
def get_points(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_points(db, municipality)

@router.get("/classifications")
def get_classifications(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_classifications(db, municipality)

@router.get("/top-municipalities")
def get_top_municipalities(db: Session = Depends(get_db)):
    return VisualDistortionService.get_top_municipalities(db)

@router.get("/status-breakdown")
def get_status_breakdown(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_status_breakdown(db, municipality)

@router.get("/worst-fake-closures/drilldown")
def get_fake_closures_drilldown(municipality: str, classification: str, db: Session = Depends(get_db)):
    return VisualDistortionService.get_fake_closures_drilldown(db, municipality, classification)

@router.get("/bounds")
def get_bounds(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_bounds(db, municipality)

@router.get("/monthly-performance")
def get_monthly_performance(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_monthly_performance(db, municipality)

@router.get("/fake-closures-kpi")
def get_fake_closures_kpi(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_fake_closures_kpi(db, municipality)

@router.get("/worst-fake-closures")
def get_worst_fake_closures(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_worst_fake_closures_locations(db, municipality)

@router.get("/grid-stats")
def get_grid_stats(db: Session = Depends(get_db)):
    return VisualDistortionService.get_municipality_grid_stats(db)
@router.get("/dashboard-summary")
def get_dashboard_summary(municipality: str = "all", db: Session = Depends(get_db)):
    return VisualDistortionService.get_dashboard_summary(db, municipality)
