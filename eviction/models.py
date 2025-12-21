from sqlalchemy import Column, Integer, String, Float, BigInteger, ForeignKey, Text, Boolean, DateTime
from geoalchemy2 import Geometry
from db import Base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

class EvictionAudit(Base):
    __tablename__ = "eviction_audit"

    id = Column(Integer, primary_key=True, index=True)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    evicted_cities_count = Column(Integer, default=0)
    status = Column(String, default="success")  # ou "failed"
    message = Column(String, nullable=True)      # message optionnel pour debug

class City(Base):
    __tablename__ = "cities"

    id = Column(BigInteger, primary_key=True)
    name_fr = Column(String, nullable=False)
    name_ar = Column(String)

    minlat = Column(Float)
    minlon = Column(Float)
    maxlat = Column(Float)
    maxlon = Column(Float)

    pois_count = Column(Integer, default=0)
    last_access_at = Column(DateTime)
    access_count = Column(Integer, default=0) # per 30 days
    is_evicted = Column(Boolean, default=False)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    pois = relationship("Poi", back_populates="city")

class Poi(Base):
    __tablename__ = "pois"

    id = Column(BigInteger, primary_key=True, index=True)
    city_id = Column(BigInteger, ForeignKey("cities.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    addr_city = Column(String, nullable=True)
    addr_full = Column(String, nullable=True)
    name = Column(String, nullable=False)
    operator = Column(String, nullable=True)
    type = Column(String, nullable=True)      # valeur du POI, ex: "pharmacy"
    category = Column(String, nullable=True)  # catégorie(s), ex: "amenity,healthcare"

    # Relation optionnelle pour accéder facilement à la ville
    city = relationship("City", back_populates="pois")