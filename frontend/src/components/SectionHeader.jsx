export default function SectionHeader({ step, title, subtitle, right }) {
  return (
    <div className="section-header">
      <span className="step-badge">{step}</span>
      <div className="section-header-text">
        <h2>{title}</h2>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {right && <div className="section-header-right">{right}</div>}
    </div>
  );
}
