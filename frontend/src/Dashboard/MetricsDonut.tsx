import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

interface MetricsDonutProps {
  title: string;
  data: Record<string, number>; // scores par catégorie
  colors?: string[];            // ajout pour pouvoir passer des couleurs personnalisées
}

export default function MetricsDonut({ title, data, colors }: MetricsDonutProps) {
  // Transformer data en tableau compatible Recharts
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));

  // Définir les couleurs : utiliser celles passées en props ou défaut
  const chartColors = colors || ['#4CAF50','#FFC107','#03A9F4','#FF5722','#9C27B0'];

  if (!chartData.length) return null; // aucun data => rien afficher

  return (
    <div style={{ width: 250, height: 250 }}>
      <h4 style={{ textAlign: "center", marginBottom: 10 }}>{title}</h4>
      <PieChart width={300} height={300}>
  <Pie
    data={chartData}
    dataKey="value"
    nameKey="name"
    cx="50%"
    cy="50%"
    outerRadius={100}  // légèrement réduit si les labels dépassent
    label
  >
    {chartData.map((_, index) => (
      <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
    ))}
  </Pie>
  <Tooltip />
  <Legend verticalAlign="bottom" height={36}/>
</PieChart>

    </div>
  );
}
