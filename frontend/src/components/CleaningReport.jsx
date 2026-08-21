export default function CleaningReport({ report }) {
  if (!report) return null;

  const marksInvalidTotal = Object.values(report.marks_invalid || {}).reduce((a, b) => a + b, 0);

  const items = [
    ["Rows read", report.rows_in],
    ["Rows kept", report.rows_out],
    ["Exact duplicates removed", report.exact_duplicates_removed],
    ["Names normalized", report.names_normalized],
    ["Gender values unrecognized", report.gender_unmapped],
    ["Invalid grades", report.grade_invalid],
    ["Invalid/unparseable marks", marksInvalidTotal],
    ["Totals recalculated & corrected", report.totals_corrected],
    ["Rows flagged incomplete", report.rows_incomplete],
  ];

  return (
    <section className="card">
      <h2>2. Cleaning report</h2>
      <div className="report-grid">
        {items.map(([label, value]) => (
          <div className="report-item" key={label}>
            <div className="report-value">{value}</div>
            <div className="report-label">{label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
