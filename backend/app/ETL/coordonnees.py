import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import requests
import overpy
from app.db import SessionLocal
from app.models import City
from sqlalchemy.orm import Session


OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def update_cities_bounds():
    """
    Met à jour les colonnes minlat, minlon, maxlat, maxlon
    pour toutes les villes existantes dans la table 'cities',
    en utilisant directement les bounds renvoyés par Overpass.
    """
    db: Session = SessionLocal()
    city_ids = [c.id for c in db.query(City.id).all()]
    db.close()

    if not city_ids:
        print("Pas de villes dans la DB pour mettre à jour.")
        return

    print(f"Nombre de villes à mettre à jour : {len(city_ids)}")

    CHUNK_SIZE = 50
    for i in range(0, len(city_ids), CHUNK_SIZE):
        chunk_ids = city_ids[i:i+CHUNK_SIZE]
        ids_str = ",".join(map(str, chunk_ids))

        query = f"""
        [out:json][timeout:180];
        relation(id:{ids_str});
        out geom tags;
        """

        response = requests.post(OVERPASS_URL, data={'data': query})
        data = response.json()

        db: Session = SessionLocal()
        for element in data.get('elements', []):
            rel_id = element['id']
            bounds = element.get('bounds')
            if not bounds:
                print(f"Ignoré : relation {rel_id} sans bounds")
                continue

            city = db.query(City).filter(City.id == rel_id).first()
            if city:
                city.minlat = bounds['minlat']
                city.minlon = bounds['minlon']
                city.maxlat = bounds['maxlat']
                city.maxlon = bounds['maxlon']
                print(f"Mise à jour : {city.name_fr} -> [{city.minlat}, {city.minlon}, {city.maxlat}, {city.maxlon}]")

        db.commit()
        db.close()

    print("Mise à jour terminée ✔️")

if __name__ == "__main__":
    update_cities_bounds()
