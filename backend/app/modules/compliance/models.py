from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Phase(Base):
    __tablename__ = "phases"
    __table_args__ = {'schema': 'compliance'}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = {'schema': 'compliance'}
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String, index=True)
    phase_id = Column(Integer, ForeignKey("compliance.phases.id"))
    municipality = Column(String, index=True)
    street = Column(String, index=True)
    district = Column(String, index=True)
    properties = Column(JSON, nullable=True)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True))
    is_compliant = Column(Boolean, default=False, index=True)
    
    phase = relationship("Phase")

class DynamicPoint(Base):
    __tablename__ = "dynamic_points"
    __table_args__ = {'schema': 'compliance'}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phase_id = Column(Integer, ForeignKey("compliance.phases.id"))
    municipality = Column(String, index=True)
    street = Column(String, index=True)
    district = Column(String, index=True)
    status = Column(String, default="active")
    details = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geom = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    is_relevant = Column(Boolean, default=True, index=True)

    phase = relationship("Phase")

class Road(Base):
    __tablename__ = "roads"
    __table_args__ = {'schema': 'compliance'}
    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(String, index=True)
    name = Column(String, index=True)
    municipality = Column(String, index=True)
    phase_id = Column(Integer, ForeignKey("compliance.phases.id"))
    geom = Column(Geometry(geometry_type='MULTILINESTRING', srid=4326, spatial_index=True))

    phase = relationship("Phase")
