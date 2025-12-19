# 🌍 GeoAnalytics API
## Analyse géospatiale de l’accessibilité et de la densité urbaine

---

## 📌 Présentation générale

**GeoAnalytics** est une API mmarocaine d’analyse urbaine basée sur les **données géospatiales** et les **Points d’Intérêt (POIs)** issus d’OpenStreetMap dans le Maroc.

Elle permet d’évaluer objectivement :
- la **densité urbaine**
- la **densité pondérée par type de service**
- l’**accessibilité et la mobilité**
- la **connectivité réseau**
- la **diversité des services accessibles**

Les analyses peuvent être effectuées :
- sur **une zone géographique**
- autour d’**un point précis avec un rayon**

---

## 🎯 Objectifs du projet

- Fournir un **outil d’aide à la décision urbaine**
- Évaluer l’attractivité d’un quartier ou d’une zone
- Servir de base à :
  - des dashboards
  - des applications cartographiques
  - des modèles d’intelligence artificielle
  - des projets académiques (PFE, recherche)

---

## 👥 Public cible

- Urbanistes & collectivités
- Entrepreneurs & investisseurs
- Data analysts & chercheurs
- Développeurs SIG
- Étudiants en ingénierie / data / IA

---

## 🧠 Principe général (vue non technique)

### Éléments utilisés dans l'analyse
1. **Une ville** (limites géographiques connues)
2. **Des POIs** (services et infrastructures)
3. **Une zone ou un point**
4. **Des métriques calculées automatiquement**

### Modes d’analyse

| Mode | Description |
|----|----|
| Zone | Rectangle ou triangle géographique |
| Rayon | Cercle autour d’un point (lat, lon) d'un rayon : 800m |

> Le mode est détecté automatiquement selon les paramètres fournis.

---

## 🗂️ Architecture du projet
app/
├── main.py
├── models.py
├── db.py
│
├── routers/
│ ├── pois.py
│ └── metrics/
│ ├── batch.py
│ ├── metric_manager.py
│ └── utils.py
│
└── ETL/
└── osm_extractor_pois.py


Relation :
- une ville possède plusieurs POIs

---

## 📐 Fonctions géographiques (`utils.py`)

### `validate_zone`

Valide et ajuste la zone demandée :
> 4 coordonnées (maxlat, maxlon)(minlat, minlon) => rectangle => zone_message Rectangle area adjusted to city limits.
> 3 coordonnées (manque d un seul coordonnée) => triangle => zone message : Triangle area applied due to one missing coordinate.
> sinon => Erreur => zone_message : Too many coordinates missing to compute area.

👉 Rend l’API robuste face aux erreurs utilisateur.

---


### `compute_area_km2`

Calcule une surface **réaliste en km²** :
- rectangle → largeur × hauteur
- triangle → ½ × largeur × hauteur

Les distances sont calculées via **géodésie réelle** c'est à dire La distance entre deux points est calculée en tenant compte de la forme réelle de la Terre (sphérique), et non comme si la Terre était plate.

---

### `distance_m`

Calcule la distance en mètres entre deux points GPS  
On projette localement la Terre sur un plan → c’est comme “aplatir” un petit morceau de la surface terrestre.
Puis on calcule la distance sur ce plan, en corrigeant la longitude par le cosinus de la latitude moyenne.
Cette fonction retourne une distance en metre (m) car on a utilisé le rayon de la terre R = 6371000.

---

## ⚙️ MetricManager – cœur analytique

Le fichier `metric_manager.py` centralise **toute la logique métier**.

---

## 📊 Métriques disponibles

### 1️⃣ Densité simple ( unité : score / km2)

densité = nombre de POIs / surface (km²)

➡️ Mesure brute du niveau d’équipement.

Interpratation :
- Plus la densité est élevée → plus la zone est riche en POIs.
- Ne tient pas compte de l’importance relative des POIs.
  
---

### 2️⃣ Densité pondérée ( unité : score ponderé / km2 )

Chaque catégorie possède un **poids stratégique**.

Exemples :
- healthcare → élevé
- transport → élevé
- naturel → faible

Principe :
- un POI peut avoir plusieurs catégories ( par exemple un pois en fes "jean de la fontaine" qui a comme categories : "amenity, education" car education est lié a l'amenity)
- seule la plus importante est retenue
- le score est normalisé par surface

Résultat :
- densité pondérée
- score total
- contribution par catégorie
- effet relatif (%) par type

Interpratation :
- Plus la densité pondérée est élevée → plus la zone est riche en POIs importants selon les poids des catégories.

---

### 3️⃣ Access mobility

Objectif: 
Le score calculé dans le mode rayon est conçu pour évaluer la mobilité d’une personne dans une zone donnée, c’est-à-dire la capacité de se déplacer facilement grâce aux POIs environnants (transports, railway, highway …).
Score_raw = poids_categorie * decay = poids_categorie * exp(-d / R )

- Mode rayon → score avec décroissance exponentielle => Plus un service est proche, plus il compte. decay = exp(-d / R )
- Mode zone → score direct decay = 1
- 
Pourquoi on utilise decroissance exponentielle dans le cas d'un mode rayon ? 
- Zone : on n'a pas comment pondérer selon la distance?
- Rayon : 
  - On considère tous les POIs situés dans un rayon autour d’un point central (par exemple 800 m autour de la maison ou du bureau).
  - Les POIs très proches sont plus utiles pour se déplacer rapidement et facilement, tandis que ceux situés à la limite du rayon sont moins accessibles.m
  - Pour refléter cette réalité urbaine, on applique une décroissance exponentielle : decay = exp(-d / R ) avec R = 800m
  - Plus un service est proche, plus il compte.

Le choix des poids de chaque categorie : 

-Les POIs de transport (public_transport, railway, highway) ont des poids élevés, car ils sont essentiels pour se déplacer librement dans la ville.
- Les autres POIs (healthcare, education, leisure, etc.) ont des bons poids à modérés : ils contribuent indirectement à la mobilité, car la proximité des services réduit la distance à parcourir.
- Même s’ils ne sont pas directement liés à la mobilité, leur présence contribue indirectement à la capacité de se déplacer
- Les POIs moins pertinents (natural, man_made) ont un poids faible, tandis que les barrières (barrier) sont ignorées, car elles n’améliorent pas la mobilité.
  
---

### 4️⃣ Densité réseau

Analyse uniquement :
- "public_transport"
- "railway"
- "highway"

➡️ Indicateur de connectivité urbaine.

---

### 5️⃣ Accessibilité des services

Compte le **nombre des types distinctes accessibles** depuis un point donné ou dans une zone spécifique (catégorie inclut plusieurs types) .

➡️ Mesure la diversité fonctionnelle d’une zone.

---

### 6️⃣ Score global d’accessibilité

La fonction `compute_all_metrics` :
- détecte automatiquement le mode
- calcule la surface
- appelle toutes les métriques
- retourne un JSON unifié

Parfait pour :
- dashboards
- visualisations cartographiques
- IA & scoring urbain

---

## 🌐 Endpoints API

### 📌 Metrics

| Endpoint | Description | exemple d'url |
|-------|------------|------------|
| `/metrics/density` | Densité simple | exemple : /metrics/density?city_id=4818907&minlat=34.88&minlon=-2.37&maxlat=35.00&maxlon=-2.28 |
| `/metrics/density_pondered` | Densité pondérée | exemple : /metrics/density_pondered?city_id=4818907&minlat=34.88&minlon=-2.37&maxlat=35.00&maxlon=-2.28 |
| `/metrics/accessibility_score` | Score global | exemple : /metrics/accessibility_score?city_id=4818907&lat=34.95&lon=-2.33&radius_m=800 |

vous pouvez calculer la densité - densité pondérée pour la ville toute entiere 

---

### 📍 POIs

| Endpoint | Description | exemple de url |
|-------|------------|------------|
| `/pois` | Tous les POIs dans la base de données | exemple: /pois|
| `/pois_area` | POIs dans une ville ou dans une zone d'une ville | exemple : /pois_area?city_id=4818907&minlat=34.88&minlon=-2.37&maxlat=35.00&maxlon=-2.28&category=public_transport OU /pois_area?city_id=4818907&category=public_transport|
| `/nearest_pois` | POIs les plus proches à un point | exemple : /nearest_pois?city_id=4818907&lat=34.95&lon=-2.30&category=public_transport&limit=5|

- &limit= nbr de pois que vous voulez afficher 
---

## 🔒 Robustesse du système

- Extraction automatique depuis OpenStreetMap dans le cas si la base de données ne contient pas les pois d'une ville demandée, alors on ne stocke que les POIs réellement nécessaires, la base de données ne devient pas inutilement volumineuse j ai comme avantages : Base légère au départ, Dynamique et flexible, Garantie de disponibilité
- Mise en cache en base de données
- Validation des entrées utilisateur 
- Calculs géographiques réalistes
- Architecture modulaire et extensible

---

## 🔮 Perspectives d’évolution

- Polygones urbains complexes
- Heatmaps interactives
- Machine Learning (attractivité urbaine)
- Scoring immobilier
- Frontend cartographique (Leaflet / Mapbox)

---

## 👩‍💻 Auteure

**Nada Afkir**  
Étudiante ingénieure en transformation digitale & intelligence artificielle  
📍 Maroc  

---

## 🏁 Conclusion

**GeoAnalytics** est une API d’analyse urbaine avancée,
conçue pour transformer des données géographiques brutes
en **indicateurs décisionnels exploitables**.

Elle constitue une base solide pour :
- des projets académiques
- des applications professionnelles
- des systèmes intelligents d’aide à la décision
