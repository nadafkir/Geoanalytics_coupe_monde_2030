import sys
import os

# Ajouter la racine du projet au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import overpy
from app.db import SessionLocal
from app.models import City
from sqlalchemy.orm import Session


def get_relation_bounds(rel):
    """
    Retourne directement la bounding box fournie par Overpass (minlat, minlon, maxlat, maxlon).
    Ne fait aucun calcul.
    """
    if hasattr(rel, "bounds") and rel.bounds:
        return rel.bounds.min_lat, rel.bounds.min_lon, rel.bounds.max_lat, rel.bounds.max_lon
    # Si pour une raison quelconque il n'y a pas de bounds
    return None, None, None, None


def extract_cities_maroc():
    api = overpy.Overpass()
    area_id = 3600000000 + 3630439  # ID OSM Maroc (relation 3630439)

    query = f"""
    [out:json][timeout:180];
    area({area_id})->.maroc;

    relation["boundary"="administrative"]["admin_level"="6"](area.maroc);
    out tags bounds;
    """

    result = api.query(query)
    print(f"Nombre de communes récupérées : {len(result.relations)}")

    cities = []

    for rel in result.relations:
        # On prend juste la bbox fournie par Overpass
        minlat, minlon, maxlat, maxlon = get_relation_bounds(rel)

        name_fr = rel.tags.get("name:fr")
        name_ar = rel.tags.get("name:ar")  # Peut être None

        # On insère uniquement si id, name_fr et bounds existent
        if rel.id is not None and name_fr and minlat is not None:
            cities.append({
                "id": rel.id,
                "name_fr": name_fr,
                "name_ar": name_ar,
                "minlat": minlat,
                "minlon": minlon,
                "maxlat": maxlat,
                "maxlon": maxlon,
            })
        else:
            print(f"Ignoré : relation sans ID, name_fr ou bounds -> {rel.tags}")

    return cities


def insert_cities_to_db(cities: list):
    db: Session = SessionLocal()

    for c in cities:
        existing = db.query(City).filter(City.id == c["id"]).first()
        if existing:
            continue

        city = City(
            id=c["id"],
            name_fr=c["name_fr"],
            name_ar=c["name_ar"],
            minlat=c["minlat"],
            minlon=c["minlon"],
            maxlat=c["maxlat"],
            maxlon=c["maxlon"]
        )

        print(f"Ajout : {city.name_fr} | {city.name_ar} | {city.minlat}|{city.minlon}")
        db.add(city)

    db.commit()
    db.close()


def main():
    print("Extraction des communes du Maroc…")
    cities = extract_cities_maroc()

    print("Insertion dans la base…")
    insert_cities_to_db(cities)

    print("Terminé ✔️")


if __name__ == "__main__":
    main()
