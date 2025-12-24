# app/routers/metrics/batch.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.routers.metrics.metric_manager import MetricManager
from app.models import Poi, City
from app.routers.eviction_util import increment_city_access

router = APIRouter(prefix="/metrics", tags=["Batch Metrics"])

@router.get("/density_combined") # pour envoyer une seule requete:  backend 1x-> <-x1 frontend 
def get_density_combined_full(
    city_id: int = Query(..., description="ID de la ville"),
    # Zone rectangle / triangle
    minlat: Optional[float] = None,
    minlon: Optional[float] = None,
    maxlat: Optional[float] = None,
    maxlon: Optional[float] = None,
    # Cercle
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_m: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Retourne un dictionnaire combinant :
    - densité de la ville entière
    - densité d'une zone spécifique (rectangle/triangle ou cercle)
    - densité pondérée (score/km²)
    """
    manager = MetricManager(db)

    # 1️⃣ Densité ville entière
    try:
        city_density = manager.density(city_id)
    except Exception as e:
        city_density = {"error": str(e)}

    # 2️⃣ Densité zone
    try:
        if lat is not None and lon is not None and radius_m is not None:
            area_density = manager.density(city_id, lat=lat, lon=lon, radius_m=radius_m)
        else:
            area_density = manager.density(city_id, minlat=minlat, minlon=minlon, maxlat=maxlat, maxlon=maxlon)
    except Exception as e:
        area_density = {"error": str(e)}

    # 3️⃣ Densité pondérée
    try:
        city_pondered_density = manager.density_pondered(city_id)
    except Exception as e:
        city_pondered_density = {"error": str(e)}

    try:
        if lat is None and lon is None and radius_m is None:
            pondered_density = manager.density_pondered(city_id, minlat=minlat, minlon=minlon, maxlat=maxlat, maxlon=maxlon)
        else:
            pondered_density = manager.density_pondered(city_id, lat=lat, lon=lon, radius_m=radius_m)

            # Pour l'instant, densité pondérée uniquement sur rectangle/triangle
    except Exception as e:
        pondered_density = {"error": str(e)}

    return {
        "city_density": city_density,
        "area_density": area_density,
        "city_pondered_density": city_pondered_density,
        "pondered_density": pondered_density
    }

@router.get("/density")
def get_density_area(
    city_id: int = Query(..., description="ID de la ville"),
    # Zone rectangle / triangle
    minlat: Optional[float] = Query(None, description="Latitude minimale de la zone"),
    minlon: Optional[float] = Query(None, description="Longitude minimale de la zone"),
    maxlat: Optional[float] = Query(None, description="Latitude maximale de la zone"),
    maxlon: Optional[float] = Query(None, description="Longitude maximale de la zone"),
    # Cercle
    lat: Optional[float] = Query(None, description="Latitude du centre pour un cercle"),
    lon: Optional[float] = Query(None, description="Longitude du centre pour un cercle"),
    radius_m: Optional[float] = Query(None, description="Rayon en mètres pour un cercle"),
    db: Session = Depends(get_db)
):
    """
    Retourne la densité de POIs pour une zone spécifique.
    Supporte :
    - Rectangle ou triangle (minlat, minlon, maxlat, maxlon)
    - Cercle (lat, lon, radius_m)
    """
    manager = MetricManager(db)

    try:
        if lat is not None and lon is not None and radius_m is not None:
            # Cercle
            result = manager.density(city_id, lat=lat, lon=lon, radius_m=radius_m)
        else:
            # Rectangle ou triangle
            result = manager.density(city_id, minlat=minlat, minlon=minlon, maxlat=maxlat, maxlon=maxlon)
    except Exception as e:
        result = {"error": str(e)}

    return result


@router.get("/density_pondered")
def get_density_pondered(
    city_id: int = Query(..., description="ID de la ville"),
    minlat: float = Query(None, description="Latitude minimale de la zone"),
    minlon: float = Query(None, description="Longitude minimale de la zone"),
    maxlat: float = Query(None, description="Latitude maximale de la zone"),
    maxlon: float = Query(None, description="Longitude maximale de la zone"),
    lat: float = Query(None, description="Latitude du centre du cercle"),
    lon: float = Query(None, description="Longitude du centre du cercle"),
    radius_m: float = Query(None, description="Rayon du cercle en mètres"),
    db: Session = Depends(get_db)
):
    """
    Calcule la densité pondérée pour :
    - une zone rectangle/triangle (minlat, minlon, maxlat, maxlon)
    - ou un cercle (lat, lon, radius_m)
    """
    metric_mgr = MetricManager(db)
    
    result = metric_mgr.density_pondered(
        city_id=city_id,
        minlat=minlat,
        minlon=minlon,
        maxlat=maxlat,
        maxlon=maxlon,
        lat=lat,
        lon=lon,
        radius_m=radius_m
    )
    
    return result

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
    test_incr= increment_city_access(db, city_id)
    return result
