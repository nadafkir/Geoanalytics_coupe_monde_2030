from pydantic import BaseModel
from typing import Optional

class CityResponse(BaseModel):
    id: int
    name_fr: str  # correspond à `City.name_fr` dans SQLAlchemy
    # name_ar: str
    class Config:
        orm_mode = True

class POIResponse(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    category: Optional[str] = None
    # addr_full: Optional[str] = None
    lat: float   # correspond à `Poi.lat`
    lon: float   # correspond à `Poi.lon`
    city: Optional[CityResponse] = None

    class Config:
        orm_mode = True
