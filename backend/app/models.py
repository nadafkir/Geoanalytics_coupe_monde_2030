from sqlalchemy import Column, Integer, String, Float, BigInteger, ForeignKey, Text
from geoalchemy2 import Geometry
from app.db import Base
from sqlalchemy.orm import relationship


class City(Base):
    __tablename__ = "cities"

    id = Column(BigInteger, primary_key=True)
    name_fr = Column(String, nullable=False)   # Nom en français
    name_ar = Column(String, nullable=True) 

    # Géométrie MULTIPOLYGON en SRID 4326

    minlat = Column(Float, nullable=True)   
    minlon = Column(Float, nullable=True)
    maxlat = Column(Float, nullable=True)
    maxlon = Column(Float, nullable=True)

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