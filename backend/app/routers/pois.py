# app/routers/pois.py
from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter()


@router.get("/pois", response_model=List[POIResponse])
def get_pois(db: Session = Depends(get_db)):
    pois = db.query(Poi).all()
    return pois

@router.get("/pois_area")
def get_pois_zone(
    city_id: int,
    minlat: Optional[float] = None,
    minlon: Optional[float] = None,
    maxlat: Optional[float] = None,
    maxlon: Optional[float] = None,
    category: Optional[str] = None,
    type_value: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # 1) Récupérer la ville
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    # 2) Valider et ajuster la zone
    minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
        city.minlat, city.minlon, city.maxlat, city.maxlon,
        minlat, minlon, maxlat, maxlon
    )
    if minlat is None:
        raise HTTPException(status_code=400, detail=zone_msg)

    # 3) Vérifier si des POIs existent déjà pour la ville
    pois_existants = db.query(Poi).filter(Poi.city_id == city_id).count()
    if pois_existants == 0:
        # Extraction depuis Overpass si aucun POI
        pois_data = extract_pois(city_id)
        if pois_data:
            store_pois(db, pois_data)
        else:
            # Toujours aucun POI après extraction
            return {
                "city_name_fr": city.name_fr,
                "city_name_ar": getattr(city, "name_ar", ""),
                "area_type": zone_msg,
                "pois": [],
                "count_pois": 0,
                "message": "Aucun POI trouvé pour cette ville même après extraction."
            }

    # 4) Filtrer les POIs selon la zone
    query = db.query(Poi).filter(
        Poi.city_id == city_id,
        Poi.lat >= minlat, Poi.lat <= maxlat,
        Poi.lon >= minlon, Poi.lon <= maxlon
    )

    # 5) Filtre par catégorie si fourni
    if category:
        # Supporte plusieurs catégories séparées par virgule
        for cat in category.split(","):
            query = query.filter(Poi.category.contains(cat.strip()))

    # 6) Filtre par type si fourni
    if type_value:
        query = query.filter(Poi.type == type_value)

    pois = query.all()

    # 7) Préparer la liste de POIs
    pois_list = [
        {
            "name": p.name,
            "type": getattr(p, "type", "node"),
            "category": p.category,
            "lat": p.lat,
            "lon": p.lon
        }
        for p in pois
    ]

    return {
        "city_name_fr": city.name_fr,
        "city_name_ar": getattr(city, "name_ar", ""),
        "area_type": zone_msg,
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

    pois = query.all()

    # Calculer la distance en mètres pour chaque POI
    pois_list = []
    for p in pois:
        dist = distance_m(lat, lon, p.lat, p.lon)
        pois_list.append({
            "name": p.name,
            "type": getattr(p, "type", "node"),
            "category": p.category,
            "lat": p.lat,
            "lon": p.lon,
            "distance_in_metre": round(dist, 1)
        })

    # Trier les POIs par distance et limiter le nombre
    pois_list = sorted(pois_list, key=lambda x: x["distance_in_metre"])[:limit]

    return {
        "city_name_fr": city.name_fr,
        "city_name_ar": getattr(city, "name_ar", ""),
        "count_pois": len(pois_list),
        "pois": pois_list
    }