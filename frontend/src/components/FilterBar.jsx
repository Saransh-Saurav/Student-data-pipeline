import SectionHeader from "./SectionHeader.jsx";
import Icon from "./Icon.jsx";

export default function FilterBar({ minTotal, onMinTotalChange, maxPossible, onExport, shortlistCount }) {
  return (
    <section className="card">
      <SectionHeader
        step={4}
        title="Minimum Total Score filter"
        subtitle="Updates the shortlist below live as you move the slider. Debarred students are always excluded."
      />
      <div className="filter-row">
        <div className="slider-track-wrap">
          <input
            type="range"
            min={0}
            max={maxPossible}
            value={minTotal}
            onChange={(e) => onMinTotalChange(Number(e.target.value))}
            style={{ "--fill": `${(minTotal / maxPossible) * 100}%` }}
          />
        </div>
        <div className="filter-value-badge">
          <input
            type="number"
            min={0}
            max={maxPossible}
            value={minTotal}
            onChange={(e) => onMinTotalChange(Number(e.target.value) || 0)}
            className="filter-number"
          />
          <span className="muted">/ {maxPossible}</span>
        </div>
        <button className="btn btn-icon" onClick={onExport} disabled={shortlistCount === 0}>
          <Icon name="download" size={15} /> Export shortlist ({shortlistCount})
        </button>
      </div>
    </section>
  );
}
