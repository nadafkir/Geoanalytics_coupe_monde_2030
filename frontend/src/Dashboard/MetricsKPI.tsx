interface MetricsKPIProps {
  title: string;
  value: number | string;
  color?: string;       // couleur du texte
  background?: string;  // couleur de fond du KPI
}

export default function MetricsKPI({ title, value, color = "#2E7D32", background = "#FFFFFF" }: MetricsKPIProps) {
  return (
    <div
      style={{
        flex: "1 1 150px",
        minWidth: 150,
        background: background,
        color: color,
        borderRadius: 8,
        padding: 15,
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        transition: "transform 0.2s",
        cursor: "default"
      }}
      onMouseEnter={e => (e.currentTarget.style.transform = "scale(1.05)")}
      onMouseLeave={e => (e.currentTarget.style.transform = "scale(1)")}
    >
      <span style={{ fontSize: 14, fontWeight: 500, marginBottom: 5 }}>{title}</span>
      <span style={{ fontSize: 24, fontWeight: 700 }}>{value}</span>
    </div>
  );
}
