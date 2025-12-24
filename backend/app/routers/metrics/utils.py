from geopy.distance import geodesic
from typing import Optional, Tuple
from app.models import City
from math import radians, cos, sin, sqrt
import math

def validate_zone(
    city_minlat: float, city_minlon: float,
    city_maxlat: float, city_maxlon: float,
    minlat: Optional[float], minlon: Optional[float],
    maxlat: Optional[float], maxlon: Optional[float]
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str]:
    """
    Valide et ajuste les coordonnées de la zone selon les limites de la ville.
    - Si toutes les 4 coordonnées sont fournies : limitation aux bornes de la ville.
    - Si une seule coordonnée manque : on applique la règle du triangle.
    - Si plus d'une coordonnée manque : retourne None et message d'erreur.
    """
    missing = [v is None for v in (minlat, minlon, maxlat, maxlon)].count(True)

    if missing > 1:
        return None, None, None, None, "Too many coordinates missing to compute area."

    elif missing == 1:
        # Application du triangle
        if minlat is None:
            minlat = city_minlat
        if maxlat is None:
            maxlat = city_maxlat
        if minlon is None:
            minlon = city_minlon
        if maxlon is None:
            maxlon = city_maxlon
        return minlat, minlon, maxlat, maxlon, "Triangle area applied due to one missing coordinate."

    # Toutes les 4 coordonnées fournies -> on force dans les limites de la ville
    minlat = max(city_minlat, minlat)
    minlon = max(city_minlon, minlon)
    maxlat = min(city_maxlat, maxlat)
    maxlon = min(city_maxlon, maxlon)
    
    if minlat == maxlat or minlon == maxlon:
        return None, None, None, None, "Coordinates are identical, resulting in zero area."

    return minlat, minlon, maxlat, maxlon, "Rectangle area adjusted to city limits."

def compute_area_km2(minlat, minlon, maxlat, maxlon):
    """
    Calcule la surface d'une zone en km².
    - Rectangle si toutes les coordonnées sont présentes
    - Triangle approximatif si une seule coordonnée est manquante
    - Retourne None si trop de coordonnées manquantes
    """
    coords = [minlat, minlon, maxlat, maxlon]
    missing = sum(c is None for c in coords)

    # Rectangle complet
    if missing == 0:
        width = geodesic((minlat, minlon), (minlat, maxlon)).km
        height = geodesic((minlat, minlon), (maxlat, minlon)).km
        surface = width * height
        return surface

    # Triangle approximatif
    elif missing == 1:
        known_lat = maxlat if maxlat is not None else minlat
        known_lon = maxlon if maxlon is not None else minlon
        width = geodesic((minlat, minlon), (minlat, known_lon)).km
        height = geodesic((minlat, minlon), (known_lat, minlon)).km
        return 0.5 * width * height

    # Trop de coordonnées manquantes
    else:
        return None

def circle_area_km2(lat: float, lon: float, radius_m: float) -> float:
    # Calcul de la distance en degrés approximative
    delta_lat = radius_m / 1000 / 111  # 1 degré latitude ≈ 111 km
    delta_lon = radius_m / 1000 / (111 * abs(math.cos(math.radians(lat))) + 1e-8)

    # Coordonnées des points extrêmes
    minlat, maxlat = lat - delta_lat, lat + delta_lat
    minlon, maxlon = lon - delta_lon, lon + delta_lon

    # Largeur et hauteur en km
    width = geodesic((lat, minlon), (lat, maxlon)).km
    height = geodesic((minlat, lon), (maxlat, lon)).km

    # Surface approximative du cercle comme rectangle
    surface = width * height
    return surface

def distance_m(lat1, lon1, lat2, lon2):
    R = 6371000  # rayon de la Terre en mètres
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    x = (lon2_rad - lon1_rad) * cos((lat1_rad + lat2_rad)/2)
    y = lat2_rad - lat1_rad
    return R * sqrt(x*x + y*y)


