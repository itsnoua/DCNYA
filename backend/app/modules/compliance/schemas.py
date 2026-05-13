from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime

class PhaseCreate(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class DynamicPointCreate(BaseModel):
    name: str
    phase_id: int
    municipality: Optional[str] = None # الحقل الجديد
    status: str = "active"
    details: Optional[Dict[str, Any]] = None
    geom_geojson: Dict[str, Any]  # Expecting GeoJSON Point geometry

class DynamicPointUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    geom_geojson: Optional[Dict[str, Any]] = None

class DynamicPointResponse(BaseModel):
    id: int
    name: str
    phase_id: int
    municipality: Optional[str] = None # الحقل الجديد
    status: str = "active"
    details: Optional[Dict[str, Any]] = None
    updated_at: datetime
    geom_geojson: Dict[str, Any]

class BuildingResponse(BaseModel):
    id: int
    building_id: str
    phase_id: int
    municipality: Optional[str]
    properties: Optional[Dict[str, Any]]
    geom_geojson: Dict[str, Any]
