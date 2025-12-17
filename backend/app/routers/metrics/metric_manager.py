# app/routers/metrics/metric_manager.py
from sqlalchemy.orm import Session
from typing import Optional
from app.models import Poi, City
from app.ETL.osm_extractor_pois import extract_pois, store_pois, check_existing_pois
from app.routers.metrics.utils import validate_zone, compute_area_km2, distance_m
import math

class MetricManager:
  def __init__(self, db: Session):
        self.db = db

  def density(self, city_id: int, minlat=None, minlon=None, maxlat=None, maxlon=None):
        # Récupérer la ville
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            return None, "City not found."

        # Vérifier et ajuster la zone
        minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
            city.minlat, city.minlon, city.maxlat, city.maxlon,
            minlat, minlon, maxlat, maxlon
        )
        if minlat is None:
            return None, zone_msg  # trop de coordonnées manquantes

        # Vérifier si des POIs existent déjà
        if not check_existing_pois(self.db, city_id):
            pois_data = extract_pois(city_id)
            if pois_data:
                store_pois(self.db, pois_data)
            else:
                return 0, "No POIs found even after extraction."

        # Filtrer les POIs
        pois = self.db.query(Poi).filter(
            Poi.city_id == city_id,
            Poi.lat >= minlat,
            Poi.lat <= maxlat,
            Poi.lon >= minlon,
            Poi.lon <= maxlon
        ).all()
        if not pois:
            return 0, "No POIs found in the selected area."

        # Calcul de la surface et densité
        area_km2 = compute_area_km2(minlat, minlon, maxlat, maxlon)
        density_value = len(pois) / area_km2

        return density_value, zone_msg
 
  def density_pondered(self, city_id: int, minlat=None, minlon=None, maxlat=None, maxlon=None):
        # Récupérer la ville
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            return None, "City not found."

        # Vérifier et ajuster la zone
        minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
            city.minlat, city.minlon, city.maxlat, city.maxlon,
            minlat, minlon, maxlat, maxlon
        )
        if minlat is None:
            return None, zone_msg

        # Vérifier si des POIs existent déjà
        if not check_existing_pois(self.db, city_id):
            pois_data = extract_pois(city_id)
            if pois_data:
                store_pois(self.db, pois_data)
            else:
                return 0, "No POIs found even after extraction."

        # Filtrer les POIs
        pois = self.db.query(Poi).filter(
            Poi.city_id == city_id,
            Poi.lat >= minlat,
            Poi.lat <= maxlat,
            Poi.lon >= minlon,
            Poi.lon <= maxlon
        ).all()
        if not pois:
            return 0, "No POIs found in the selected area."

        # Calcul de la surface
        area_km2 = compute_area_km2(minlat, minlon, maxlat, maxlon)

        # Poids normalisés des catégories
        weights = {
            "public_transport": 0.09, "natural": 0.02, "amenity": 0.09,
            "shop": 0.08, "healthcare": 0.10, "leisure": 0.06,
            "railway": 0.08, "highway": 0.08, "education": 0.09,
            "office": 0.07, "tourism": 0.07, "historic": 0.05,
            "barrier": 0.03, "man_made": 0.04, "sport": 0.05
        }

        # Score pondéré par catégorie
        score_par_cat = {cat: 0 for cat in weights}
        for p in pois:
            cats = p.category.split(",") if p.category else []
            if not cats:
                continue
            max_w = max([weights.get(c, 0) for c in cats])
            max_cat = max(cats, key=lambda c: weights.get(c, 0))
            score_par_cat[max_cat] += max_w

        score_total = sum(score_par_cat.values())
        densite_ponderee = score_total / area_km2 if area_km2 > 0 else 0
        effets = {cat: score / score_total for cat, score in score_par_cat.items()} if score_total > 0 else {cat: 0 for cat in score_par_cat}

        return {
            "densite_ponderee": densite_ponderee,
            "score_total": score_total,
            "scores_categories": score_par_cat,
            "effets_categories": effets,
            "surface_km2": area_km2,
            "zone_msg": zone_msg
        }

  def compute_access_mobility(
        self,
        pois,
        mode,
        lat=None,
        lon=None,
        minlat=None,
        minlon=None,
        maxlat=None,
        maxlon=None,
        radius_m=800
    ):
        weights = {
            "public_transport": 0.15, "railway": 0.13, "highway": 0.10,
            "healthcare": 0.09, "education": 0.08, "shop": 0.07,
            "amenity": 0.06, "leisure": 0.05, "sport": 0.04,
            "office": 0.05, "tourism": 0.05, "historic": 0.03,
            "natural": 0.01, "man_made": 0.02, "barrier": 0.0
        }

        score_par_cat = {cat: 0.0 for cat in weights}

        for poi in pois:
            # ---- MODE ZONE ----
            if mode == "zone":
                if not (
                    minlat <= poi.lat <= maxlat and
                    minlon <= poi.lon <= maxlon
                ):
                    continue
                decay = 1.0

            # ---- MODE RAYON ----
            else:
                dist = distance_m(lat, lon, poi.lat, poi.lon)
                if dist > radius_m:
                    continue
                decay = math.exp(-dist / radius_m)

            if poi.category:
                cats = poi.category.split(",")
                best_cat = max(cats, key=lambda c: weights.get(c, 0))
                score_par_cat[best_cat] += weights[best_cat] * decay

        return {
            "score_raw": round(sum(score_par_cat.values()), 3),
            "scores_categories": score_par_cat
        }


  def compute_network_density(
        self,
        pois,
        mode,
        lat=None,
        lon=None,
        minlat=None,
        minlon=None,
        maxlat=None,
        maxlon=None,
        radius_m=800
    ):
        weights = {
            "public_transport": 0.1,
            "railway": 0.1,
            "highway": 0.1
        }

        score_par_cat = {cat: 0.0 for cat in weights}

        for poi in pois:
            if mode == "zone":
                if not (
                    minlat <= poi.lat <= maxlat and
                    minlon <= poi.lon <= maxlon
                ):
                    continue
                decay = 1.0
            else:
                dist = distance_m(lat, lon, poi.lat, poi.lon)
                if dist > radius_m:
                    continue
                decay = math.exp(-dist / radius_m)

            if poi.category:
                cats = [c for c in poi.category.split(",") if c in weights]
                if cats:
                    score_par_cat[cats[0]] += weights[cats[0]] * decay

        return {
            "score_raw": round(sum(score_par_cat.values()), 3),
            "scores_categories": score_par_cat
        }

  def compute_service_reachability(
        self,
        pois,
        mode,
        lat=None,
        lon=None,
        minlat=None,
        minlon=None,
        maxlat=None,
        maxlon=None,
        radius_m=800
    ):
        categories = set()

        for poi in pois:
            if mode == "zone":
                if not (
                    minlat <= poi.lat <= maxlat and
                    minlon <= poi.lon <= maxlon
                ):
                    continue
            else:
                if distance_m(lat, lon, poi.lat, poi.lon) > radius_m:
                    continue

            if poi.category:
                categories.update(poi.category.split(","))

        return {
            "score_raw": len(categories),
            "categories_count": len(categories)
        }

  def compute_all_metrics(
        self,
        city_id: int,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        minlat: Optional[float] = None,
        minlon: Optional[float] = None,
        maxlat: Optional[float] = None,
        maxlon: Optional[float] = None,
        radius_m: int = 800
    ):
        # 1️⃣ Ville
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            return {"error": "City not found."}

        # 2️⃣ Déterminer le mode
        mode = "radius" if lat is not None and lon is not None else "zone"

        # 3️⃣ Validation zone (UNIQUEMENT pour ZONE)
        if mode == "zone":
            minlat, minlon, maxlat, maxlon, zone_msg = validate_zone(
                city.minlat, city.minlon, city.maxlat, city.maxlon,
                minlat, minlon, maxlat, maxlon
            )
            if minlat is None:
                return {"error": zone_msg}
        else:
            zone_msg = f"Cercle de {radius_m}m autour du point fourni."

        # 4️⃣ POIs
        if not check_existing_pois(self.db, city_id):
            pois_data = extract_pois(city_id)
            if pois_data:
                store_pois(self.db, pois_data)
            else:
                return {"error": "No POIs found even after extraction."}

        pois = self.db.query(Poi).filter(Poi.city_id == city_id).all()
        if not pois:
            return {"error": "No POIs available."}

        # 5️⃣ Surface
        if mode == "zone":
            area_km2 = compute_area_km2(minlat, minlon, maxlat, maxlon)
        else:
            area_km2 = math.pi * (radius_m / 1000) ** 2

        # 6️⃣ Metrics
        return {
            "city": {
                "name_fr": city.name_fr,
                "name_ar": city.name_ar,
                "surface_km2": round(area_km2, 3),
                "zone_msg": zone_msg
            },
            "metrics": {
                "access_mobility": self.compute_access_mobility(
                    pois, mode, lat, lon, minlat, minlon, maxlat, maxlon, radius_m
                ),
                "network_density": self.compute_network_density(
                    pois, mode, lat, lon, minlat, minlon, maxlat, maxlon, radius_m
                ),
                "reachability_service": self.compute_service_reachability(
                    pois, mode, lat, lon, minlat, minlon, maxlat, maxlon, radius_m
                )
            }
        }
