// Client-side CSV export: the shortlist the user is looking at (already
// filtered by min-score and Active status) is exported directly from
// in-memory state, so "Export" is instant and never re-fetches or re-cleans.
const COLUMNS = ["id", "Name", "Gender", "Grade", "Math", "Science", "English", "Total", "Status"];

function escapeCell(value) {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function studentsToCsv(students) {
  const header = COLUMNS.join(",");
  const rows = students.map((s) => COLUMNS.map((c) => escapeCell(s[c])).join(","));
  return [header, ...rows].join("\n");
}

export function downloadCsv(students, filename) {
  const csv = studentsToCsv(students);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
