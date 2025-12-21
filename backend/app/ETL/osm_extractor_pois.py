import overpy
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import Poi, City
from app.logger import logger  # Import du logger

CATEGORY_KEYS = [
    "amenity", "tourism", "leisure", "shop", "public_transport", "highway",
    "railway", "healthcare", "emergency", "education", "sport", "man_made",
    "historic", "natural", "office", "barrier"
]

def update_city_after_pois_extraction(db: Session, city_id: int):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        logger.warning(f"City {city_id} not found.")
        return

    city.is_evicted = False
    city.pois_count = db.query(Poi).filter(Poi.city_id == city_id).count()
    city.last_access_at = datetime.utcnow()
    city.updated_at = datetime.utcnow()
    db.add(city)
    db.commit()
    logger.info(f"City {city.name_fr} updated after POIs extraction.")

def check_existing_pois(db: Session, city_id: int, category: Optional[str] = None, type_value: Optional[str] = None) -> bool:
    query = db.query(Poi).filter(Poi.city_id == city_id)
    filters = []

    if category:
        category_conditions = []
        for cat in [c.strip() for c in category.split(',')]:
            category_conditions.append(Poi.category.contains(cat))
        filters.append(or_(*category_conditions))
    
    if type_value:
        filters.append(Poi.type == type_value)
    
    if filters:
        query = query.filter(and_(*filters))
    
    count = query.count()
    return count > 0

def build_query(city_id: int, category: Optional[str] = None, type_value: Optional[str] = None) -> str:
    area_id = 3600000000 + city_id
    filters = []

    if category is None and type_value is None:
        filters = [f'node(area.searchArea)["{key}"];' for key in CATEGORY_KEYS]
    else:
        if category:
            filters.append(f'node(area.searchArea)["{category}"];')
        if type_value:
            if category:
                filters.append(f'node(area.searchArea)["{category}"="{type_value}"];')
            else:
                for key in CATEGORY_KEYS:
                    filters.append(f'node(area.searchArea)["{key}"="{type_value}"];')

    filters_str = "\n".join(filters)
    return f"""
    [out:json][timeout:300];
    area({area_id})->.searchArea;
    (
        {filters_str}
    );
    out tags geom;
    """

def extract_pois(city_id: int, category: Optional[str] = None, type_value: Optional[str] = None) -> List[dict]:
    api = overpy.Overpass()
    query = build_query(city_id, category, type_value)

    try:
        result = api.query(query)
        logger.info(f"POIs retrieved for city {city_id}: {len(result.nodes)}")
    except Exception as e:
        logger.error(f"Overpass error for city {city_id}: {e}")
        return []

    pois = []
    for node in result.nodes:
        tags = node.tags
        name = tags.get("name")
        if not name:
            continue

        types_values = set()
        categories = []
        for key in CATEGORY_KEYS:
            if key in tags:
                types_values.add(tags[key])
                categories.append(key)

        type_val = list(types_values)[0] if types_values else None
        category_str = ",".join(categories) if categories else None

        pois.append({
            "id": node.id,
            "city_id": city_id,
            "lat": node.lat,
            "lon": node.lon,
            "addr_city": tags.get("addr:city"),
            "addr_full": tags.get("addr:full"),
            "name": name,
            "operator": tags.get("operator"),
            "type": type_val,
            "category": category_str
        })
    return pois

def store_pois(db: Session, pois: List[dict]):
    if not pois:
        logger.info("No POIs to store.")
        return

    stored_count = 0
    for p in pois:
        existing = db.query(Poi).filter(Poi.id == p["id"]).first()
        if existing:
            p["stored"] = False
            continue

        poi = Poi(**p)
        db.add(poi)
        p["stored"] = True
        stored_count += 1

    db.commit()
    logger.info(f"{stored_count}/{len(pois)} POIs inserted ✔️")
    if pois:
        update_city_after_pois_extraction(db, pois[0]["city_id"])
    return stored_count
