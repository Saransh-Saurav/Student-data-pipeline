import Icon from "./Icon.jsx";

export default function StatsCards({ stats }) {
  const cards = [
    ["users", "Shortlisted", stats.count],
    ["trend-up", "Average total", stats.avg],
    ["target", "Highest total", stats.max],
    ["target", "Lowest total", stats.min],
  ];

  return (
    <div className="stats-row">
      {cards.map(([icon, label, value], i) => (
        <div className="stat-card" key={label + i}>
          <div className="stat-icon">
            <Icon name={icon} size={16} />
          </div>
          <div className="stat-value">{value}</div>
          <div className="stat-label">{label}</div>
        </div>
      ))}
    </div>
  );
}
