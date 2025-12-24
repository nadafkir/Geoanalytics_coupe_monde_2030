# app/routers/pois.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.db import get_db
from app.models import Poi, City
from app.schemas import POIResponse
from app.routers.metrics.utils import validate_zone, compute_area_km2, distance_m, circle_area_km2
from app.ETL.osm_extractor_pois import (
    extract_pois,
    store_pois,
    check_existing_pois
)
from app.routers.eviction_util import increment_city_access

router = APIRouter()

@router.get("/pois")
def get_pois_area(
    city_id: int,
    minlat: Optional[float] = None,
    minlon: Optional[float] = None,
    maxlat: Optional[float] = None,
    maxlon: Optional[float] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_m: Optional[float] = None,
    category: Optional[str] = None,
    type_value: Optional[str] = None,
    limit: Optional[int] = Query(None, description="Nombre maximum de POIs à retourner"),
    db: Session = Depends(get_db)
):
    # 1) Vérifier la ville
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    # 2) Extraire les POIs si nécessaire
    if db.query(Poi).filter(Poi.city_id == city_id).count() == 0:
        pois_data = extract_pois(city_id)
        if pois_data:
            store_pois(db, pois_data)

    # --- Cercle ---
    if lat is not None and lon is not None and radius_m is not None:
        area_km2 = circle_area_km2(lat, lon, radius_m)
        pois = [
            p for p in db.query(Poi).filter(Poi.city_id == city_id).all()
            if distance_m(lat, lon, p.lat, p.lon) <= radius_m
        ]
        zone_msg = f"Cercle de {radius_m}m autour du point fourni."
        zone_info = {"center_lat": lat, "center_lon": lon, "radius_m": radius_m, "surface_km2": round(area_km2, 4)}

    # --- Rectangle / Triangle ---
    elif any(v is not None for v in [minlat, minlon, maxlat, maxlon]):
        minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
            city.minlat, city.minlon, city.maxlat, city.maxlon,
            minlat, minlon, maxlat, maxlon
        )
        if minlat is None:
            raise HTTPException(status_code=400, detail=zone_msg)

        area_km2 = compute_area_km2(minlat, minlon, maxlat, maxlon)
        pois_query = db.query(Poi).filter(Poi.city_id == city_id)
        
        if minlat is not None and maxlat is not None:
            pois_query = pois_query.filter(Poi.lat >= minlat, Poi.lat <= maxlat)
        if minlon is not None and maxlon is not None:
            pois_query = pois_query.filter(Poi.lon >= minlon, Poi.lon <= maxlon)
        
        pois = pois_query.all()
        zone_info = {"minlat": minlat, "minlon": minlon, "maxlat": maxlat, "maxlon": maxlon, "surface_km2": round(area_km2, 4)}

    # --- Ville entière ---
    else:
        minlat, minlon, maxlat, maxlon = city.minlat, city.minlon, city.maxlat, city.maxlon
        area_km2 = compute_area_km2(minlat, minlon, maxlat, maxlon)
        pois = db.query(Poi).filter(
            Poi.city_id == city_id,
            Poi.lat >= minlat, Poi.lat <= maxlat,
            Poi.lon >= minlon, Poi.lon <= maxlon
        ).all()
        zone_msg = "Entire city"
        zone_info = {"minlat": minlat, "minlon": minlon, "maxlat": maxlat, "maxlon": maxlon, "surface_km2": round(area_km2, 4)}

    # --- FILTRES CATÉGORIE ET TYPE ---
    if category:
        categories = [c.strip() for c in category.split(",")]
        pois = [p for p in pois if p.category in categories]

    if type_value:
        types = [t.strip() for t in type_value.split(",")]
        pois = [p for p in pois if getattr(p, "type", None) in types]

    # --- LIMIT ---
    if limit:
        pois = pois[:limit]

    increment_city_access(db, city_id)

    # --- Préparer le retour ---
    pois_list = [
        {
            "name": p.name,
            "addresse": p.addr_city,
            "type": getattr(p, "type", "node"),
            "category": p.category,
            "lat": p.lat,
            "lon": p.lon
        }
        for p in pois
    ]

    return {
        "city_id": city.id,
        "name_fr": city.name_fr,
        "name_ar": getattr(city, "name_ar", ""),
        "zone": zone_info | {"zone_msg": zone_msg},
        "count_pois": len(pois_list),
        "pois": pois_list
    }


@router.get("/nearest_pois")
def get_nearest_pois(
    city_id: int,
    lat: float,
    lon: float,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    limit: int = 10
):
    # Vérifier que la ville existe
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    # Vérifier si la ville a des POIs, sinon extraire et stocker
    if not check_existing_pois(db, city_id):
        pois_data = extract_pois(city_id)
        if pois_data:
            store_pois(db, pois_data)
        else:
            return {"message": "Aucun POI trouvé pour cette ville.", "pois": []}

    # Récupérer tous les POIs (filtrés par catégorie si besoin)
    query = db.query(Poi).filter(Poi.city_id == city_id)
    if category:
        query = query.filter(Poi.category.contains(category))
    
    if limit:
        query = query.limit(limit)
    
    pois = query.all()

    # Calculer la distance en mètres pour chaque POI
    pois_list = []
    for p in pois:
        dist = distance_m(lat, lon, p.lat, p.lon)
        pois_list.append({
            "name": p.name,
            "addresse":p.addr_city,
            "type": getattr(p, "type", "node"),
            "category": p.category,
            "lat": p.lat,
            "lon": p.lon,
            "distance_in_metre": round(dist, 1)
        })

    # Trier les POIs par distance et limiter le nombre
    pois_list = sorted(pois_list, key=lambda x: x["distance_in_metre"])[:limit]
    increment_city_access(db, city_id)
    return {
        "city_name_fr": city.name_fr,
        "city_name_ar": getattr(city, "name_ar", ""),
        "count_pois": len(pois_list),
        "pois": pois_list
    }