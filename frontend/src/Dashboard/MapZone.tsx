import { MapContainer, TileLayer, Rectangle } from "react-leaflet";

interface MapZoneProps {
  zone: {
    minlat: number;
    minlon: number;
    maxlat: number;
    maxlon: number;
  };
  mapColor?: string;   // Couleur de remplissage de la zone
  mapBorder?: string;  // Couleur du contour
}

export default function MapZone({ 
  zone, 
  mapColor = "#A8D5BA",   // vert clair par défaut
  mapBorder = "#E0E5E8"   // gris clair par défaut
}: MapZoneProps) {
  // Vérification des valeurs pour éviter les undefined
  if (
    zone.minlat == null ||
    zone.minlon == null ||
    zone.maxlat == null ||
    zone.maxlon == null
  ) {
    return null;
  }

  // Définir les bounds sous forme de tableau de coordonnées [ [lat, lon], [lat, lon] ]
  const bounds: [[number, number], [number, number]] = [
    [zone.minlat, zone.minlon],
    [zone.maxlat, zone.maxlon]
  ];

  // Calculer le centre pour centrer la carte
  const center: [number, number] = [
    (zone.minlat + zone.maxlat) / 2,
    (zone.minlon + zone.maxlon) / 2
  ];

  return (
    <MapContainer style={{ height: 400, width: "100%" }} center={center} zoom={13}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Rectangle 
        bounds={bounds} 
        pathOptions={{ 
          color: mapBorder,   // couleur du contour
          fillColor: mapColor, // couleur de remplissage
          fillOpacity: 0.5,
          weight: 2
        }} 
      />
    </MapContainer>
  );
}
