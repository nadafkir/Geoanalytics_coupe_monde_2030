# app/routers/metrics/batch.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.routers.metrics.metric_manager import MetricManager
from app.models import Poi, City


router = APIRouter(prefix="/metrics", tags=["Batch Metrics"])

@router.get("/density")
def metrics_for_city(
    city_id: int = Query(..., description="ID of the city to calculate metrics for"),
    minlat: Optional[float] = Query(None, description="Minimum latitude of the zone"),
    minlon: Optional[float] = Query(None, description="Minimum longitude of the zone"),
    maxlat: Optional[float] = Query(None, description="Maximum latitude of the zone"),
    maxlon: Optional[float] = Query(None, description="Maximum longitude of the zone"),
    db: Session = Depends(get_db)
):
    """
    Calculate all important metrics for a city or a specific zone within the city.
    - If no zone is provided, metrics are calculated for the whole city.
    - If zone is provided, coordinates are validated against city limits.
    """
    metric_mgr = MetricManager(db)
    density_value, zone_msg = metric_mgr.density(city_id, minlat, minlon, maxlat, maxlon)

    if density_value is None:
        return {
            "city_id": city_id,
            "zone": {
                "minlat": minlat,
                "minlon": minlon,
                "maxlat": maxlat,
                "maxlon": maxlon
            },
            "metrics": {},
            "message": zone_msg
        }

    return {
        "city_id": city_id,
        "zone": {
            "minlat": minlat,
            "minlon": minlon,
            "maxlat": maxlat,
            "maxlon": maxlon
        },
        "metrics": {
            "density": density_value
        },
        "message": zone_msg
    }

@router.get("/density_pondered")
def get_density_pondered(
    city_id: int = Query(..., description="ID de la ville"),
    minlat: float = Query(None, description="Latitude minimale de la zone"),
    minlon: float = Query(None, description="Longitude minimale de la zone"),
    maxlat: float = Query(None, description="Latitude maximale de la zone"),
    maxlon: float = Query(None, description="Longitude maximale de la zone"),
    db: Session = Depends(get_db)
):
    """
    Calcule la densité pondérée pour une ville ou une zone spécifique.
    """
    metric_mgr = MetricManager(db)
    result = metric_mgr.density_pondered(
        city_id=city_id,
        minlat=minlat,
        minlon=minlon,
        maxlat=maxlat,
        maxlon=maxlon
    )
    return result

# @router.get("/access_mobility")
# def access_mobility(
#     city_id: int = Query(..., description="ID de la ville"),
#     lat: Optional[float] = Query(None, description="Latitude du point"),
#     lon: Optional[float] = Query(None, description="Longitude du point"),
#     minlat: Optional[float] = Query(None, description="Latitude minimale de la zone"),
#     minlon: Optional[float] = Query(None, description="Longitude minimale de la zone"),
#     maxlat: Optional[float] = Query(None, description="Latitude maximale de la zone"),
#     maxlon: Optional[float] = Query(None, description="Longitude maximale de la zone"),
#     radius_m: int = Query(800, description="Rayon en mètres pour calculer l'accessibility"),
#     db: Session = Depends(get_db)
# ):
#     """
#     Calcule le score Access Mobility pour une ville ou une zone spécifique.
#     """
#     metric_mgr = MetricManager(db)
    
#     # Appelle la méthode compute_access_mobility dans MetricManager
#     result = metric_mgr.compute_access_mobility(
#         city_id=city_id,
#         lat=lat,
#         lon=lon,
#         minlat=minlat,
#         minlon=minlon,
#         maxlat=maxlat,
#         maxlon=maxlon,
#         radius_m=radius_m
#     )
    
#     return result
@router.get("/accessibility_score")
def accessibility_score(
    city_id: int = Query(...),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    minlat: Optional[float] = Query(None),
    minlon: Optional[float] = Query(None),
    maxlat: Optional[float] = Query(None),
    maxlon: Optional[float] = Query(None),
    radius_m: int = Query(800),
    db: Session = Depends(get_db)
):
    metric_mgr = MetricManager(db)

    result = metric_mgr.compute_all_metrics(
        city_id=city_id,
        lat=lat,
        lon=lon,
        minlat=minlat,
        minlon=minlon,
        maxlat=maxlat,
        maxlon=maxlon,
        radius_m=radius_m
    )

    return result
