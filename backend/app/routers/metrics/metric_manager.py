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

    # Si aucune zone n'est fournie, utiliser les limites de la ville
    if minlat is None or minlon is None or maxlat is None or maxlon is None:
        minlat = city.minlat
        minlon = city.minlon
        maxlat = city.maxlat
        maxlon = city.maxlon
        zone_msg = "Entire city"
    else:
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
    density_value = len(pois) / area_km2 if area_km2 > 0 else 0

    # Retour structuré avec city, zone et metrics
    return {
        "city_id": city.id,
        "name_fr": city.name_fr,
        "name_ar": city.name_ar,
        "zone": {
            "minlat": minlat,
            "minlon": minlon,
            "maxlat": maxlat,
            "maxlon": maxlon
        },
        "metrics": {
            "density": round(density_value, 4),
            "surface_km2": round(area_km2, 4),
            "nb_pois": len(pois),
            "zone_msg": zone_msg
        }
    }


  
  def density_pondered(self, city_id: int, minlat=None, minlon=None, maxlat=None, maxlon=None):
    # Récupérer la ville
    city = self.db.query(City).filter(City.id == city_id).first()
    if not city:
        return None, "City not found."

    # Si aucune zone n'est fournie, utiliser les limites de la ville
    if minlat is None or minlon is None or maxlat is None or maxlon is None:
        minlat = city.minlat
        minlon = city.minlon
        maxlat = city.maxlat
        maxlon = city.maxlon
        zone_msg = "Entire city"
    else:
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
        "shop": 0.08, "healthcare": 0.10, "emergency": 0.10, "leisure": 0.06,
        "railway": 0.08, "highway": 0.08, "education": 0.09,
        "office": 0.07, "tourism": 0.07, "historic": 0.05,
        "barrier": 0.03, "man_made": 0.04, "sport": 0.05
    }

    # Score pondéré par catégorie
    score_par_cat = {cat: 0.0 for cat in weights}

    for p in pois:
        cats = p.category.split(",") if p.category else []
        if not cats:
            continue

        valid_cats = [c for c in cats if c in weights]
        if not valid_cats:
            continue

        max_cat = max(valid_cats, key=lambda c: weights[c])
        max_w = round(weights[max_cat], 4)
        score_par_cat[max_cat] = round(score_par_cat.get(max_cat, 0) + max_w, 4)

    # Calcul de la densité pondérée
    score_total = sum(score_par_cat.values())
    densite_ponderee = score_total / area_km2 if area_km2 > 0 else 0

    # Effets par catégorie (proportion)
    effets = (
        {cat: round(score / score_total, 4) for cat, score in score_par_cat.items()}
        if score_total > 0
        else {cat: 0 for cat in score_par_cat}
    )

    # Retour structuré avec city, zone et metrics
    return {
        "city_id": city.id,
        "name_fr": city.name_fr,
        "name_ar": city.name_ar,
        "zone": {
            "minlat": minlat,
            "minlon": minlon,
            "maxlat": maxlat,
            "maxlon": maxlon,
            "surface_km2": round(area_km2, 4),
            "zone_msg": zone_msg
        },
        "metrics": {
            "unité": "score pondere/km2",
            "densite_ponderee": round(densite_ponderee, 4),
            "score_total": round(score_total, 4),
            "scores_categories": {cat: round(score, 4) for cat, score in score_par_cat.items()},
            "effets_categories": effets,
        }
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
    """
    Calcul du score d'accessibilité mobilité.

    - mode: "zone" ou "radius"
    - pois: liste de POIs
    - lat/lon: centre pour le mode rayon
    - minlat/minlon/maxlat/maxlon: zone pour le mode zone
    - radius_m: rayon en mètres pour le mode rayon
    """

    # Poids par catégorie générale
    weights = {
        "public_transport": 0.15, "railway": 0.13, "highway": 0.10,
        "healthcare": 0.09, "education": 0.08, "shop": 0.07, "emergency": 0.10,
        "amenity": 0.06, "leisure": 0.05, "sport": 0.04,
        "office": 0.05, "tourism": 0.05, "historic": 0.03,
        "natural": 0.01, "man_made": 0.02, "barrier": 0.0
    }

    # Poids spécifiques pour certains sous-types
    subtype_weights = {
        "taxi": 0.12,
        "bicycle_rental": 0.10,
        "car_rental": 0.10,
        "charging_station": 0.09,
        "fuel": 0.08
        # ajouter ici d'autres sous-types si nécessaire
    }

    # Initialisation des scores par catégorie
    score_par_cat = {cat: 0.0 for cat in weights}

    for poi in pois:
        # ---- MODE ZONE ----
        if mode == "zone":
            if not (minlat <= poi.lat <= maxlat and minlon <= poi.lon <= maxlon):
                continue
            decay = 1.0

        # ---- MODE RAYON ----
        else:
            dist = distance_m(lat, lon, poi.lat, poi.lon)
            if dist > radius_m:
                continue
            decay = math.exp(-dist / radius_m)

        # Gestion des catégories et sous-types
        if poi.category:
            cats = poi.category.split(",")
            best_cat = None
            best_weight = 0.0

            for c in cats:
                w = subtype_weights.get(c, weights.get(c, 0))  # priorité au sous-type
                if w > best_weight:
                    best_weight = w
                    best_cat = c

            if best_cat:
                score_par_cat[best_cat] += round(best_weight * decay, 4)

    # Calcul score global
    score_raw = round(sum(score_par_cat.values()), 4)

    return {
        "score_raw": score_raw,
        "scores_categories": {cat: round(score, 4) for cat, score in score_par_cat.items()}
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
    import math

    # Poids des catégories existantes
    weights = {
        "public_transport": 0.1,
        "railway": 0.1,
        "highway": 0.1,
    }

    # POIs amenity à inclure avec un poids de 0.01
    amenity_types = [
        "taxi", "car_rental", "bicycle_rental", "bicycle_repair_station",
        "vehicle_impound", "fuel", "charging_station", 
        "parking", "parking_entrance", "parking_space", "vehicle_inspection"
    ]
    for amenity in amenity_types:
        weights[amenity] = 0.01

    # Initialisation des scores par catégorie
    score_par_cat = {cat: 0.0 for cat in weights}

    for poi in pois:
        # Vérification si le POI est dans la zone ou le rayon
        if mode == "zone":
            if not (minlat <= poi.lat <= maxlat and minlon <= poi.lon <= maxlon):
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
        types = set()

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

            if poi.type:
                types.update(poi.type.split(","))
        return {
            "score_raw": len(types),
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
