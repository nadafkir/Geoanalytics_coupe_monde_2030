import { useState } from "react";

export default function ControlsPanel({ onRun }: { onRun: (params: any) => void }) {
  const [cityId, setCityId] = useState<number>(0);
  const [minlat, setMinlat] = useState<number | undefined>();
  const [minlon, setMinlon] = useState<number | undefined>();
  const [maxlat, setMaxlat] = useState<number | undefined>();
  const [maxlon, setMaxlon] = useState<number | undefined>();
  const [lat, setLat] = useState<number | undefined>();
  const [lon, setLon] = useState<number | undefined>();
  const [radius, setRadius] = useState<number>(800);

  const handleRun = () => {
    if (lat && lon) {
      onRun({ city_id: cityId, lat, lon, radius_m: radius });
    } else {
      onRun({ city_id: cityId, minlat, minlon, maxlat, maxlon });
    }
  };

  return (
    <div style={{ marginBottom: 20 }}>
      <input type="number" placeholder="City ID" value={cityId} onChange={e => setCityId(Number(e.target.value))} />
      <h5>Option Zone Rectangle :</h5>
      <input type="number" placeholder="Min Lat" onChange={e => setMinlat(Number(e.target.value))} />
      <input type="number" placeholder="Min Lon" onChange={e => setMinlon(Number(e.target.value))} />
      <input type="number" placeholder="Max Lat" onChange={e => setMaxlat(Number(e.target.value))} />
      <input type="number" placeholder="Max Lon" onChange={e => setMaxlon(Number(e.target.value))} />
      <h5>Ou Cercle :</h5>
      <input type="number" placeholder="Lat" onChange={e => setLat(Number(e.target.value))} />
      <input type="number" placeholder="Lon" onChange={e => setLon(Number(e.target.value))} />
      <input type="number" placeholder="Rayon (m)" value={radius} onChange={e => setRadius(Number(e.target.value))} />
      <button onClick={handleRun}>Run Analysis</button>
    </div>
  );
}
