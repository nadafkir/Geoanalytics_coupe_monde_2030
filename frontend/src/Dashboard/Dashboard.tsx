import { useState } from "react";
import ControlsPanel from "./ControlPanel";
import MapZone from "./MapZone";
import MetricsKPI from "./MetricsKPI";
import MetricsDonut from "./MetricsDonut";

import {
  fetchDensity,
  fetchWeightedDensity,
  fetchAccessibility
} from "../services/geoanalyticsApi";

export default function Dashboard() {
  const [zoneData, setZoneData] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async (params: any) => {
    setLoading(true);
    setError(null);
    setZoneData(params);

    try {
      const densityData = await fetchDensity(params);
      const weightedData = await fetchWeightedDensity(params);
      const accessData = await fetchAccessibility(params);

      if (!densityData?.metrics || !weightedData?.metrics || !accessData?.metrics) {
        setError("Les données sont manquantes.");
        setMetrics(null);
      } else {
        setMetrics({
          density: densityData.metrics,
          weighted: weightedData.metrics,
          access: accessData.metrics
        });
      }
    } catch (err) {
      console.error(err);
      setError("Erreur lors de l'analyse des données.");
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: "Arial, sans-serif", background: "#F0F2F5", minHeight: "100vh", padding: 20 }}>
      {/* Header */}
      <h1 style={{ textAlign: "center", marginBottom: 20, color: "#2E7D32" }}>GeoAnalytics Dashboard</h1>

      {/* Controls */}
      <ControlsPanel onRun={runAnalysis} />

      {/* Loader / Error */}
      {loading && <p style={{ textAlign: "center", marginTop: 20 }}>Analyse en cours...</p>}
      {error && <p style={{ textAlign: "center", marginTop: 20, color: "red" }}>{error}</p>}

      {/* Map */}
      {zoneData ? (
        <div style={{ marginTop: 20, borderRadius: 8, overflow: "hidden", boxShadow: "0 2px 10px rgba(0,0,0,0.1)" }}>
          <MapZone 
            zone={zoneData} 
            mapColor="#FFFFFF"   // carte blanche
            mapBorder="#E0E0E0" // contour gris clair
          />
        </div>
      ) : (
        <p style={{ textAlign: "center", marginTop: 20 }}>Sélectionnez une zone pour afficher la carte</p>
      )}

      {/* KPI Section */}
      {metrics && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 20, marginTop: 30 }}>
            {[
              { title: "Densité (POIs/km²)", value: metrics.density?.density || 0 },
              { title: "Surface (km²)", value: metrics.density?.surface_km2 || 0 },
              { title: "Nombre de POIs", value: metrics.density?.nb_pois || 0 },
              { title: "Densité pondérée", value: metrics.weighted?.densite_ponderee || 0 },
              { title: "Score mobilité", value: metrics.access?.access_mobility?.score_raw || 0 },
              { title: "Reachabilité", value: metrics.access?.reachability_service?.score_raw || 0 },
              { title: "Network Density", value: metrics.access?.network_density?.score_raw || 0 }
            ].map((kpi, idx) => (
              <MetricsKPI 
                key={idx} 
                title={kpi.title} 
                value={kpi.value} 
                color="#2E7D32" // texte vert
                background="#FFFFFF" // fond blanc
              />
            ))}
          </div>

          {/* Donuts Section */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 30, marginTop: 40 }}>
          <MetricsDonut title="Access Mobility" data={metrics.access?.access_mobility?.scores_categories || {}} colors={['#4CAF50','#FFC107','#03A9F4','#FF5722','#9C27B0']} />
          <MetricsDonut title="Network Density" data={metrics.access?.network_density?.scores_categories || {}} colors={['#4CAF50','#FFC107','#03A9F4','#FF5722','#9C27B0']} />
          <MetricsDonut title="Reachability" data={metrics.access?.reachability_service?.scores_categories || {}} colors={['#4CAF50','#FFC107','#03A9F4','#FF5722','#9C27B0']} />
          </div>
        </>
      )}
    </div>
  );
}
