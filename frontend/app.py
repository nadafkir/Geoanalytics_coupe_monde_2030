# app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

# =========================
# CONFIG
# =========================
load_dotenv(dotenv_path="../.env")  # adapte le chemin si besoin

API_BASE = os.getenv("API_BASE")
DENSITY_COMBINED = os.getenv("DENSITY_COMBINED")
ACCESSIBILITY_SCORE = os.getenv("ACCESSIBILITY_SCORE")

st.set_page_config(
    page_title="DIMA MAGHRIB Analytics",
    page_icon="🇲🇦",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("DIMA MAGHRIB")
st.subheader("Préparer le Maroc de demain, pas juste pour la Coupe du Monde.")

# =========================
# SESSION STATE INITIALIZATION
# =========================
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False
if 'df_filtered' not in st.session_state:
    st.session_state.df_filtered = pd.DataFrame()  # initialise vide

# =========================
# SIDEBAR – PARAMÈTRES
# =========================
st.sidebar.header("📍 Paramètres de la zone")
city_id = st.sidebar.number_input("ID de la ville", min_value=1, value=18227425)
zone_type = st.sidebar.radio("Type de zone", ["Cercle", "Rectangle"])

params = {"city_id": city_id}

if zone_type == "Cercle":
    lat = st.sidebar.number_input("Latitude centre", format="%.6f", value=33.57)
    lon = st.sidebar.number_input("Longitude centre", format="%.6f", value=-7.60)
    radius = st.sidebar.number_input("Rayon (m)", min_value=100, value=800)
    params.update({"lat": lat, "lon": lon, "radius_m": radius})
else:
    minlat = st.sidebar.number_input("Latitude min", format="%.6f")
    minlon = st.sidebar.number_input("Longitude min", format="%.6f")
    maxlat = st.sidebar.number_input("Latitude max", format="%.6f")
    maxlon = st.sidebar.number_input("Longitude max", format="%.6f")
    params.update({"minlat": minlat, "minlon": minlon, "maxlat": maxlat, "maxlon": maxlon})

# =========================
# BOUTON LANCER ANALYSE
# =========================
if st.sidebar.button("🚀 Lancer l’analyse"):
    st.session_state.run_analysis = True

# =========================
# LANCER ANALYSE
# =========================
if st.session_state.run_analysis:
    with st.spinner("Analyse en cours..."):
        # -------------------------
        # API CALLS
        # -------------------------
        print(DENSITY_COMBINED, API_BASE)
        density_combined = requests.get(f"{API_BASE}{DENSITY_COMBINED}", params=params).json()
        access = requests.get(f"{API_BASE}{ACCESSIBILITY_SCORE}", params=params).json()
        # -------------------------
        # EXTRACTION – DENSITY COMBINED
        # -------------------------
        city = density_combined["city_density"]
        area = density_combined["area_density"]
        city_p = density_combined["city_pondered_density"]
        area_p = density_combined["pondered_density"]

        city_name = city["name_fr"]

        # --- ZONE
        zone_surface = area["zone"]["surface_km2"]
        zone_msg = area["zone"]["zone_msg"]
        nb_pois = area["metrics"]["nb_pois"]
        density_area = area["metrics"]["density"]
        density_p_area = area_p["metrics"]["densite_ponderee"]

        # --- VILLE (référence)
        density_city = city["metrics"]["density"]
        density_p_city = city_p["metrics"]["densite_ponderee"]

        # -------------------------
        # ACCESSIBILITÉ
        # -------------------------
        access_score = access["metrics"]["access_mobility"]["score_raw"]
        network_score = access["metrics"]["network_density"]["score_raw"]
        reach_score = access["metrics"]["reachability_service"]["score_raw"]

        access_cat = access["metrics"]["access_mobility"]["scores_categories"]
        network_cat = access["metrics"]["network_density"]["scores_categories"]
        effets_cat = area_p["metrics"]["effets_categories"]

        # =========================
        # KPIs – ZONE
        # =========================
        st.markdown("## 🎯 Zone analysée")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📏 Surface (km²)", f"{zone_surface:.2f}")
        k2.metric("📍 POIs", nb_pois)
        k3.metric("🌐 Densité réelle", f"{density_area:.2f}")
        k4.metric("🛠️ Densité pondérée", f"{density_p_area:.2f}")
        st.markdown(f"**ℹ️ Zone :** *{zone_msg}*")

        # =========================
        # KPIs – ACCESSIBILITÉ
        # =========================
        st.markdown("## 🚶 Accessibilité & services")
        a1, a2, a3 = st.columns(3)
        a1.metric("🚶 Access Mobility", f"{access_score:.2f}")
        a2.metric("🛣️ Network Density", f"{network_score:.2f}")
        a3.metric("🎯 Reachability", f"{reach_score:.0f}")

        # =========================
        # KPIs – VILLE
        # =========================
        st.markdown("## 🌆 Référence ville")
        c1, c2 = st.columns(2)
        c1.metric("🌆 Densité ville", f"{density_city:.2f}")
        c2.metric("🧠 Densité pondérée ville", f"{density_p_city:.2f}")

        # =========================
        # HISTOGRAMME – Effets catégories
        # =========================
        st.markdown("## 📊 Effet des catégories – Zone vs Ville")
        effets_zone = {k: v for k, v in area_p["metrics"]["effets_categories"].items() if v > 0}
        effets_ville = {k: city_p["metrics"]["effets_categories"].get(k, 0) for k in effets_zone.keys()}

        if effets_zone:
            df_effets = pd.DataFrame({
                "Catégorie": list(effets_zone.keys()),
                "Zone": list(effets_zone.values()),
                "Ville": list(effets_ville.values())
            })

            fig_effets = px.bar(
                df_effets,
                x="Catégorie",
                y="Zone",
                text="Zone",
                color="Catégorie",
                color_discrete_sequence=px.colors.sequential.Tealgrn,
                height=450
            )

            fig_effets.add_scatter(
                x=df_effets["Catégorie"],
                y=df_effets["Ville"],
                mode="lines+markers",
                name="Ville",
                line=dict(color="#fc770a", width=2),
                marker=dict(size=8)
            )

            fig_effets.update_layout(
                yaxis_title="Effet (score pondéré / km²)",
                xaxis_title="Catégorie",
                margin=dict(t=30, b=80, l=20, r=20),
                showlegend=True
            )

            fig_effets.update_traces(
                texttemplate="%{text:.3f}",
                textposition="outside",
                selector=dict(type="bar")
            )

            st.plotly_chart(fig_effets, use_container_width=True, key="hist_effets_zone_ville")
        else:
            st.info("Aucune donnée d'effet par catégorie.")

        # =========================
        # PIE CHARTS
        # =========================
        st.markdown("## 🍩 Répartition par catégories")
        palette = px.colors.sequential.Tealgrn + px.colors.sequential.Blues
        col1, col2 = st.columns(2)

        # Access Mobility
        access_cat_filtered = {k: v for k, v in access_cat.items() if v > 0}
        with col1:
            st.markdown("#### 🚶 Access Mobility")
            if access_cat_filtered:
                df_access = pd.DataFrame(access_cat_filtered.items(), columns=["Catégorie", "Score"])
                fig_access = px.pie(df_access, names="Catégorie", values="Score", hole=0.55,
                                    color_discrete_sequence=palette)
                st.plotly_chart(fig_access, use_container_width=True, key="pie_access")
            else:
                st.info("Aucune donnée d’accessibilité.")

        # Network Density
        network_cat_filtered = {k: v for k, v in network_cat.items() if v > 0}
        with col2:
            st.markdown("#### 🛣️ Network Density")
            if network_cat_filtered:
                df_network = pd.DataFrame(network_cat_filtered.items(), columns=["Catégorie", "Score"])
                fig_network = px.pie(df_network, names="Catégorie", values="Score", hole=0.55,
                                     color_discrete_sequence=palette)
                st.plotly_chart(fig_network, use_container_width=True, key="pie_network")
            else:
                st.info("Aucune donnée de network density.")

        # =========================
# RÉCUPÉRATION DES POIs
# =========================
if st.session_state.run_analysis:
    response = requests.get(f"{API_BASE}/pois", params={"city_id": city_id})
    pois_list = response.json().get("pois", [])

    if pois_list:
        df_pois = pd.DataFrame(pois_list)

        # FILTRES
        with st.expander("🔍 Filtres POIs", expanded=True):
            # --- Catégories ---
            categories = df_pois["category"].dropna().unique().tolist()
            if 'select_all_cat' not in st.session_state:
                st.session_state.select_all_cat = True
            select_all_cat = st.checkbox("Tout sélectionner les catégories", value=st.session_state.select_all_cat, key="select_all_cat")
            if select_all_cat:
                selected_categories = categories
            else:
                selected_categories = st.multiselect(
                    "Choisir les catégories",
                    options=categories,
                    default=categories[:1],
                    key="selected_categories"
                )

            # --- Types ---
            types = df_pois["type"].dropna().unique().tolist()
            if 'select_all_type' not in st.session_state:
                st.session_state.select_all_type = True
            select_all_type = st.checkbox("Tout sélectionner les types", value=st.session_state.select_all_type, key="select_all_type")
            if select_all_type:
                selected_types = types
            else:
                selected_types = st.multiselect(
                    "Choisir les types",
                    options=types,
                    default=types[:1],
                    key="selected_types"
                )

            # --- Limite d'affichage ---
            limit = st.number_input(
                "Nombre de POIs à afficher",
                min_value=1,
                max_value=len(df_pois),
                value=min(20, len(df_pois)),
                key="limit_pois"
            )

        # APPLIQUER FILTRES
        df_filtered = df_pois[
            (df_pois["category"].isin(selected_categories)) &
            (df_pois["type"].isin(selected_types))
        ].head(limit)

        st.session_state.df_filtered = df_filtered
    else:
        st.session_state.df_filtered = pd.DataFrame()

# =========================
# TABLE DES POIs
# =========================
st.markdown("## 🗂️ Liste des POIs")
df_table = st.session_state.df_filtered
if not df_table.empty:
    st.dataframe(
        df_table.style.set_properties(**{
            'background-color': '#f9f9f9',
            'color': '#0d3b66',
            'border-color': '#ccc'
        }),
        use_container_width=True
    )
else:
    st.info("Aucun POI à afficher pour cette zone. Cliquez sur '🚀 Lancer l’analyse' pour charger les POIs.")

# =========================
# CARTE DES POIs
# =========================
st.markdown("## 🗺️ Carte des POIs")
if not df_table.empty:
    # Colonnes par défaut si manquantes
    for col in ['category', 'name', 'type']:
        if col not in df_table.columns:
            df_table[col] = 'Inconnu' if col != 'name' else 'Sans nom'

    # Centre de la carte
    center_lat = df_table["lat"].mean()
    center_lon = df_table["lon"].mean()

    fig_map = px.scatter_mapbox(
        df_table,
        lat="lat",
        lon="lon",
        color="category",
        hover_data={"name": True, "type": True, "lat": True, "lon": True},
        height=600,
        zoom=10,
        mapbox_style="carto-positron"
    )

    fig_map.update_layout(
        mapbox=dict(center=dict(lat=center_lat, lon=center_lon)),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Aucun POI à afficher sur la carte.")
