import { useMemo, useState } from "react";
import UploadPanel from "./components/UploadPanel.jsx";
import CleaningReport from "./components/CleaningReport.jsx";
import FilterBar from "./components/FilterBar.jsx";
import StatsCards from "./components/StatsCards.jsx";
import StudentTable from "./components/StudentTable.jsx";
import SectionHeader from "./components/SectionHeader.jsx";
import Icon from "./components/Icon.jsx";
import { uploadDataset, updateStatus } from "./api.js";
import { downloadCsv } from "./utils/csv.js";

export default function App() {
  const [students, setStudents] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusError, setStatusError] = useState(null);
  const [search, setSearch] = useState("");
  const [minTotal, setMinTotal] = useState(0);

  const maxPossible = 300; // 3 subjects x 100 marks

  async function handleUpload(file) {
    setLoading(true);
    setError(null);
    try {
      const body = await uploadDataset(file);
      setStudents(body.students);
      setReport(body.report);
      setMinTotal(0);
      setSearch("");
    } catch (err) {
      setError(err.message || "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleStatus(id, newStatus) {
    setStatusError(null);
    // Optimistic update -- the shortlist below must react instantly.
    setStudents((prev) => prev.map((s) => (s.id === id ? { ...s, Status: newStatus } : s)));
    try {
      await updateStatus(id, newStatus);
    } catch (err) {
      setStatusError(`Could not save status change: ${err.message}. Reverted.`);
      setStudents((prev) =>
        prev.map((s) => (s.id === id ? { ...s, Status: newStatus === "Active" ? "Debarred" : "Active" } : s))
      );
    }
  }

  const searchedStudents = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return students;
    return students.filter((s) => (s.Name || "").toLowerCase().includes(term));
  }, [students, search]);

  const shortlist = useMemo(
    () => students.filter((s) => s.Status === "Active" && Number(s.Total) >= minTotal),
    [students, minTotal]
  );

  const stats = useMemo(() => {
    if (shortlist.length === 0) return { count: 0, avg: "-", min: "-", max: "-" };
    const totals = shortlist.map((s) => Number(s.Total));
    const sum = totals.reduce((a, b) => a + b, 0);
    return {
      count: shortlist.length,
      avg: (sum / totals.length).toFixed(1),
      min: Math.min(...totals),
      max: Math.max(...totals),
    };
  }, [shortlist]);

  function handleExport() {
    const stamp = new Date().toISOString().slice(0, 10);
    downloadCsv(shortlist, `shortlist_min${minTotal}_${stamp}.csv`);
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo" aria-hidden="true">SP</div>
        <div>
          <h1>Student Data Pipeline &amp; UI</h1>
          <p className="muted">Upload a raw student CSV/XLSX, clean it automatically, filter a live shortlist, and export it.</p>
          <div className="tech-pills">
            <span className="tech-pill">React</span>
            <span className="tech-pill">FastAPI</span>
            <span className="tech-pill">pandas</span>
          </div>
        </div>
      </header>

      <UploadPanel onUpload={handleUpload} loading={loading} error={error} />

      {report && <CleaningReport report={report} />}

      {students.length > 0 && (
        <>
          <section className="card">
            <SectionHeader step={3} title={`Cleaned dataset (${students.length} students)`} />
            <div className="search-wrap">
              <Icon name="search" size={15} className="search-icon" />
              <input
                type="text"
                placeholder="Search by name…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="search-input"
              />
            </div>
            <StudentTable students={searchedStudents} onToggleStatus={handleToggleStatus} />
            {statusError && <p className="error">{statusError}</p>}
          </section>

          <FilterBar
            minTotal={minTotal}
            onMinTotalChange={setMinTotal}
            maxPossible={maxPossible}
            onExport={handleExport}
            shortlistCount={shortlist.length}
          />

          <section className="card">
            <SectionHeader step={5} title="Live shortlist" />
            <StatsCards stats={stats} />
            <StudentTable students={shortlist} onToggleStatus={handleToggleStatus} />
          </section>
        </>
      )}
    </div>
  );
}
