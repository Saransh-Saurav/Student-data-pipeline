import SectionHeader from "./SectionHeader.jsx";
import Icon from "./Icon.jsx";

// Three kinds of number, each read differently:
// - "info"   : a plain count, no good/bad meaning (rows in/out)
// - "fixed"  : the pipeline successfully corrected something -- always a
//              good outcome, colored the same whether it's 0 or 500
// - "attention": something the pipeline could NOT resolve on its own and
//              is surfacing for a human to look at -- calm green at 0,
//              amber the moment it's non-zero
function buildItems(report) {
  const marksInvalidTotal = Object.values(report.marks_invalid || {}).reduce((a, b) => a + b, 0);
  return [
    { label: "Rows read", value: report.rows_in, kind: "info" },
    { label: "Rows kept", value: report.rows_out, kind: "info" },
    { label: "Exact duplicates removed", value: report.exact_duplicates_removed, kind: "fixed" },
    { label: "Names normalized", value: report.names_normalized, kind: "fixed" },
    { label: "Totals recalculated & corrected", value: report.totals_corrected, kind: "fixed" },
    { label: "Gender values unrecognized", value: report.gender_unmapped, kind: "attention" },
    { label: "Invalid grades", value: report.grade_invalid, kind: "attention" },
    { label: "Invalid/unparseable marks", value: marksInvalidTotal, kind: "attention" },
    { label: "Rows flagged incomplete", value: report.rows_incomplete, kind: "attention" },
  ];
}

function TileIcon({ kind, value }) {
  if (kind === "info") return <Icon name="target" size={14} />;
  if (kind === "fixed") return <Icon name="wrench" size={14} />;
  return value > 0 ? <Icon name="alert" size={14} /> : <Icon name="check" size={14} />;
}

export default function CleaningReport({ report }) {
  if (!report) return null;

  const items = buildItems(report);
  const needsAttention = items.filter((i) => i.kind === "attention").reduce((sum, i) => sum + i.value, 0);

  return (
    <section className="card">
      <SectionHeader
        step={2}
        title="Cleaning report"
        subtitle="Exactly what the pipeline changed -- nothing here is a guess."
        right={
          needsAttention > 0 ? (
            <span className="summary-pill summary-pill-warning">
              <Icon name="alert" size={13} /> {needsAttention} row{needsAttention === 1 ? "" : "s"} flagged for review
            </span>
          ) : (
            <span className="summary-pill summary-pill-good">
              <Icon name="check-circle" size={13} /> No unresolved issues
            </span>
          )
        }
      />
      <div className="report-grid">
        {items.map((item) => (
          <div className={`report-item report-item-${item.kind}${item.kind === "attention" && item.value > 0 ? " report-item-warn" : ""}`} key={item.label}>
            <div className="report-item-icon">
              <TileIcon kind={item.kind} value={item.value} />
            </div>
            <div>
              <div className="report-value">{item.value}</div>
              <div className="report-label">{item.label}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
