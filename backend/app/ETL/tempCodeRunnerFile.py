import requests
from shapely.geometry import shape, Point, Polygon
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app.models import City, District, POI

# ---- CONFIG ----
CITY_NAME = "Rabat"
CITY_ADMIN_LEVEL = 8  # selon ce que tu veux
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# ---- UTILS ----
def create_city_if_not_exists(db: Session):
    city = db.query(City).filter(City.name == CITY_NAME).first()
    if city:
        return city
    # Exemple: geom vide pour l'instant, tu peux remplacer par la vraie géométrie
    city = City(name=CITY_NAME, admin_level=CITY_ADMIN_LEVEL, geom=None, population=0)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city

def create_district_if_not_exists(db: Session, city: City, name: str, geom=None):
    district = db.query(District).filter(District.name == name, District.city_id == city.id).first()
    if district:
        return district
    district = District(name=name, city_id=city.id, geom=geom)
    db.add(district)
    db.commit()
    db.refresh(district)
    return district

def fetch_pois(city_name: str):
    """Récupère les POIs depuis OpenStreetMap via Overpass API"""
    query = f"""
    [out:json][timeout:25];
    area["name"="{city_name}"][admin_level=8];
    (
      node["amenity"](area);
      node["tourism"](area);
      node["leisure"](area);
      node["shop"](area);
    );
    out body;
    """
    response = requests.post(OVERPASS_URL, data=query)
    response.raise_for_status()
    data = response.json()
    pois = []
    for elem in data.get("elements", []):
        name = elem.get("tags", {}).get("name")
        if not name:
            continue
        pois.append({
            "name": name,
            "type": elem.get("tags", {}).get("amenity") or elem.get("tags", {}).get("tourism") or elem.get("tags", {}).get("leisure") or elem.get("tags", {}).get("shop"),
            "category": elem.get("tags", {}).get("amenity") or elem.get("tags", {}).get("tourism") or elem.get("tags", {}).get("leisure") or elem.get("tags", {}).get("shop"),
            "latitude": elem.get("lat"),
            "longitude": elem.get("lon"),
        })
    return pois

def assign_district_to_poi(db: Session, poi_data: dict, city: City):
    """Assigne un district en fonction du point, si possible"""
    point = Point(poi_data["longitude"], poi_data["latitude"])
    districts = db.query(District).filter(District.city_id == city.id).all()
    for district in districts:
        if district.geom and point.within(district.geom):
            return district.id
    return None  # si aucun district ne correspond

def create_poi_if_not_exists(db: Session, poi_data: dict, city: City):
    # Vérification doublons: même nom + lat + lon
    existing = db.query(POI).filter(
        POI.name == poi_data["name"],
        POI.latitude == poi_data["latitude"],
        POI.longitude == poi_data["longitude"],
        POI.city_id == city.id
    ).first()
    if existing:
        return existing
    
    district_id = assign_district_to_poi(db, poi_data, city)
    poi = POI(
        name=poi_data["name"],
        type=poi_data["type"] or "Unknown",
        category=poi_data["category"] or "Unknown",
        latitude=poi_data["latitude"],
        longitude=poi_data["longitude"],
        city_id=city.id,
        district_id=district_id,
        geom=f'SRID=4326;POINT({poi_data["longitude"]} {poi_data["latitude"]})'
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)
    return poi

# ---- SCRIPT PRINCIPAL ----
def main():
    db = SessionLocal()
    
    # 1. Création de la ville
    city = create_city_if_not_exists(db)
    
    # 2. (Optionnel) création des districts manuellement ou depuis shapefile
    # Exemple rapide: on crée un district fictif
    district = create_district_if_not_exists(db, city, "District Central", geom=None)
    
    # 3. Récupération des POIs
    pois_data = fetch_pois(CITY_NAME)
    print(f"Nombre de POIs récupérés: {len(pois_data)}")
    
    # 4. Insertion dans la BDD
    for poi_data in pois_data:
        poi = create_poi_if_not_exists(db, poi_data, city)
        print(f"POI ajouté: {poi.name}")

if __name__ == "__main__":
    main()
