import overpy
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import Poi

# Clés considérées comme catégories OSM
CATEGORY_KEYS = [
    "amenity", "tourism", "leisure", "shop", "public_transport", "highway",
    "railway", "healthcare", "emergency", "education", "sport", "man_made",
    "historic", "natural", "office", "barrier"
]

# ------------------------------------------
# 0️⃣ Vérifier si des POIs existent déjà dans la DB
# ------------------------------------------
def check_existing_pois(db: Session, city_id: int, category: Optional[str] = None, type_value: Optional[str] = None) -> bool:
    """
    Vérifie si des POIs existent déjà en base pour les filtres donnés.
    Retourne True si au moins un POI existe, False sinon.
    """
    query = db.query(Poi).filter(Poi.city_id == city_id)
    
    # Construction dynamique des filtres
    filters = []
    
    if category:
        # Recherche exacte ou partielle (si category contient plusieurs valeurs séparées par des virgules)
        category_conditions = []
        categories = [c.strip() for c in category.split(',')]
        for cat in categories:
            category_conditions.append(Poi.category.contains(cat))
        filters.append(or_(*category_conditions))
    
    if type_value:
        filters.append(Poi.type == type_value)
    
    # Appliquer tous les filtres avec AND
    if filters:
        query = query.filter(and_(*filters))
    
    # Compter les résultats
    count = query.count()
    return count > 0

# ------------------------------------------
# 1️⃣ Construction dynamique de la requête
# ------------------------------------------
def build_query(city_id: int, category: Optional[str] = None, type_value: Optional[str] = None) -> str:
    area_id = 3600000000 + city_id
    filters = []

    # Aucun filtre → toutes les catégories
    if category is None and type_value is None:
        filters = [f'node(area.searchArea)["{key}"];' for key in CATEGORY_KEYS]
    else:
        if category:
            filters.append(f'node(area.searchArea)["{category}"];')

        if type_value:
            if category:
                # type dans la catégorie spécifique
                filters.append(f'node(area.searchArea)["{category}"="{type_value}"];')
            else:
                # type dans toutes les catégories possibles
                for key in CATEGORY_KEYS:
                    filters.append(f'node(area.searchArea)["{key}"="{type_value}"];')

    filters_str = "\n".join(filters)
    query = f"""
    [out:json][timeout:300];
    area({area_id})->.searchArea;
    (
        {filters_str}
    );
    out tags geom;
    """
    return query

# ------------------------------------------
# 2️⃣ Extraction des POIs depuis Overpass
# ------------------------------------------
def extract_pois(city_id: int, category: Optional[str] = None, type: Optional[str] = None) -> List[dict]:
    api = overpy.Overpass()
    query = build_query(city_id, category, type)

    try:
        result = api.query(query)
        print(f"POIs récupérés pour ville {city_id} : {len(result.nodes)}")
    except Exception as e:
        print("Erreur Overpass :", e)
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

        type_value = list(types_values)[0] if types_values else None
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
            "type": type_value,
            "category": category_str
        })
    return pois

# ------------------------------------------
# 3️⃣ Stockage des POIs dans la DB
# ------------------------------------------
def store_pois(db: Session, pois: List[dict]):
    """
    Stocke les POIs dans la base de données.
    """
    if not pois:
        print("Aucun POI à stocker.")
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
    print(f"{stored_count}/{len(pois)} POIs insérés ✔️")
    
    return stored_count