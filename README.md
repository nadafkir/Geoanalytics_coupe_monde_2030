# 🌍 GeoAnalytics API
## Analyse géospatiale de l’accessibilité et de la densité urbaine

---

## 📌 Présentation générale

**GeoAnalytics** est une API d’analyse urbaine basée sur les **données géospatiales** et les **Points d’Intérêt (POIs)** issus d’OpenStreetMap.

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

### Éléments analysés
1. **Une ville** (limites géographiques connues)
2. **Des POIs** (services et infrastructures)
3. **Une zone ou un point**
4. **Des métriques calculées automatiquement**

### Modes d’analyse

| Mode | Description |
|----|----|
| Zone | Rectangle géographique |
| Rayon | Cercle autour d’un point |

> Le mode est détecté automatiquement selon les paramètres fournis.

---

## 🗂️ Architecture du projet

