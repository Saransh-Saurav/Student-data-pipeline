export default function StatsCards({ stats }) {
  const cards = [
    ["Shortlisted", stats.count],
    ["Average total", stats.avg],
    ["Highest total", stats.max],
    ["Lowest total", stats.min],
  ];

  return (
    <div className="stats-row">
      {cards.map(([label, value]) => (
        <div className="stat-card" key={label}>
          <div className="stat-value">{value}</div>
          <div className="stat-label">{label}</div>
        </div>
      ))}
    </div>
  );
}
