const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore -- no JSON body
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/api/upload`, { method: "POST", body: formData });
  return handle(res);
}

export async function fetchStudents() {
  const res = await fetch(`${API_URL}/api/students`);
  return handle(res);
}

export async function updateStatus(id, status) {
  const res = await fetch(`${API_URL}/api/students/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  return handle(res);
}
