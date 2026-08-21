export default function FilterBar({ minTotal, onMinTotalChange, maxPossible, onExport, shortlistCount }) {
  return (
    <section className="card">
      <h2>4. Minimum Total Score filter</h2>
      <div className="filter-row">
        <input
          type="range"
          min={0}
          max={maxPossible}
          value={minTotal}
          onChange={(e) => onMinTotalChange(Number(e.target.value))}
        />
        <input
          type="number"
          min={0}
          max={maxPossible}
          value={minTotal}
          onChange={(e) => onMinTotalChange(Number(e.target.value) || 0)}
          className="filter-number"
        />
        <button className="btn" onClick={onExport} disabled={shortlistCount === 0}>
          Export shortlist ({shortlistCount}) as CSV
        </button>
      </div>
      <p className="muted">Updates the shortlist below live as you move the slider. Debarred students are always excluded.</p>
    </section>
  );
}
