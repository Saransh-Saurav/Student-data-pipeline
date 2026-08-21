import { useState } from "react";

const PAGE_SIZE = 50;

export default function StudentTable({ students, onToggleStatus, showStatusColumn = true }) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(students.length / PAGE_SIZE));
  const clampedPage = Math.min(page, pageCount - 1);
  const pageStudents = students.slice(clampedPage * PAGE_SIZE, clampedPage * PAGE_SIZE + PAGE_SIZE);

  return (
    <div>
      <div className="table-wrapper">
        <table className="student-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Gender</th>
              <th>Grade</th>
              <th>Math</th>
              <th>Science</th>
              <th>English</th>
              <th>Total</th>
              {showStatusColumn && <th>Status</th>}
            </tr>
          </thead>
          <tbody>
            {pageStudents.map((s) => (
              <tr key={s.id} className={s.Status === "Debarred" ? "row-debarred" : ""}>
                <td>{s.Name}</td>
                <td>{s.Gender}</td>
                <td>{s.Grade}</td>
                <td>{s.Math}</td>
                <td>{s.Science}</td>
                <td>{s.English}</td>
                <td className="cell-total">{s.Total}</td>
                {showStatusColumn && (
                  <td>
                    <button
                      className={`status-toggle ${s.Status === "Active" ? "status-active" : "status-debarred"}`}
                      onClick={() => onToggleStatus(s.id, s.Status === "Active" ? "Debarred" : "Active")}
                      title="Click to toggle Active/Debarred"
                    >
                      {s.Status}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {students.length === 0 && <p className="muted table-empty">No students match.</p>}
      </div>
      {students.length > 0 && (
        <div className="pagination">
          <button className="btn-secondary" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={clampedPage === 0}>
            Prev
          </button>
          <span>
            Page {clampedPage + 1} of {pageCount} &middot; {students.length} row{students.length === 1 ? "" : "s"}
          </span>
          <button
            className="btn-secondary"
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            disabled={clampedPage >= pageCount - 1}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
