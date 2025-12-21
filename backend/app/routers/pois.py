# app/routers/pois.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.db import get_db
from app.models import Poi, City
from app.schemas import POIResponse
from app.routers.metrics.utils import validate_zone, compute_area_km2, distance_m
from app.ETL.osm_extractor_pois import (
    extract_pois,
    store_pois,
    check_existing_pois
)
from app.routers.eviction_util import increment_city_access


router = APIRouter()


@router.get("/pois", response_model=List[dict])
def get_all_pois(db: Session = Depends(get_db), limit: Optional[int] = Query(None, description="Nombre maximum de POIs à retourner")):
    """
    Retourne tous les POIs présents dans la base de données, sans filtre,
    ou jusqu'à un nombre maximum si 'limit' est spécifié.
    """
    query = db.query(Poi)

    if limit:
        query = query.limit(limit)

    pois = query.all()

    pois_list = [
        {
            "city_id": p.city_id,
            "name": p.name,
            "addresse":p.addr_city,
            "type": getattr(p, "type", "node"),
            "category": p.category,
            "lat": p.lat,
            "lon": p.lon
        }
        for p in pois
    ]
    return pois_list

@router.get("/pois_area")
def get_pois_area(
    city_id: int,
    minlat: Optional[float] = None,
    minlon: Optional[float] = None,
    maxlat: Optional[float] = None,
    maxlon: Optional[float] = None,
    category: Optional[str] = None,
    type_value: Optional[str] = None,
    limit: Optional[int] = Query(None, description="Nombre maximum de POIs à retourner"),
    db: Session = Depends(get_db)
):

    # 1) Récupérer la ville
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    # 2) Si aucune zone fournie, prendre toute la ville
    if minlat is None or minlon is None or maxlat is None or maxlon is None:
        minlat = city.minlat
        minlon = city.minlon
        maxlat = city.maxlat
        maxlon = city.maxlon
        zone_msg = "Entire city"
    else:
        # 3) Valider la zone
        minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
            city.minlat, city.minlon, city.maxlat, city.maxlon,
            minlat, minlon, maxlat, maxlon
        )
        if minlat is None:
            raise HTTPException(status_code=400, detail=zone_msg)

    # 4) Vérifier si des POIs existent pour cette ville
    if db.query(Poi).filter(Poi.city_id == city_id).count() == 0:
        pois_data = extract_pois(city_id)
        if pois_data:
            store_pois(db, pois_data)

    # 5) Filtrer les POIs selon la zone
    query = db.query(Poi).filter(
        Poi.city_id == city_id,
        Poi.lat >= minlat, Poi.lat <= maxlat,
        Poi.lon >= minlon, Poi.lon <= maxlon
    )

    # 6) Filtrer par catégorie si fourni
    if category:
        for cat in category.split(","):
            query = query.filter(Poi.category.contains(cat.strip()))

    # 7) Filtrer par type si fourni
    if type_value:
        query = query.filter(Poi.type == type_value)
    
    if limit:
       query = query.limit(limit)

    pois = query.all()
    increment_city_access(db, city_id)
    # 8) Préparer la liste finale
    pois_list = [
        {
            "name": p.name,
            "addresse":p.addr_city,
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
        "zone": {
            "minlat": minlat,
            "minlon": minlon,
            "maxlat": maxlat,
            "maxlon": maxlon,
            "area_type": zone_msg
        },
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