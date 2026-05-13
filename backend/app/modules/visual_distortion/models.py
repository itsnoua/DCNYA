from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from geoalchemy2 import Geometry
from app.core.database import Base

class VisualDistortionReport(Base):
    __tablename__ = "visual_distortion_reports"
    __table_args__ = {'schema': 'visual_distortion'}

    id = Column(Integer, primary_key=True, index=True)
    municipality = Column(String, index=True)
    report_number = Column(String, unique=True, index=True)
    crm_report_number = Column(String, index=True, nullable=True)
    visit_number = Column(String, index=True, nullable=True)
    report_status = Column(String, index=True)
    visit_status = Column(String, nullable=True)
    
    assignment_date = Column(Date, nullable=True)
    closing_date = Column(Date, nullable=True)
    
    longitude = Column(Float)
    latitude = Column(Float)
    geom = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    
    classification_name = Column(String, index=True)
    management_group = Column(String, index=True)
    sub_category = Column(String, index=True)
    domain_name = Column(String, index=True, nullable=True)
    closing_status = Column(String, index=True)
    
    last_observation_date = Column(DateTime, nullable=True)
    first_observation_date = Column(DateTime, nullable=True)
