const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export async function listDocuments() {
  const r = await fetch(`${API_BASE}/documents`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function uploadDocument(file) {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${API_BASE}/documents/upload`, { method:'POST', body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getDocument(id) {
  const r = await fetch(`${API_BASE}/documents/${id}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteDocument(id) {
  const r = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function runAnalysis(docId) {
  const r = await fetch(`${API_BASE}/analysis/run/${docId}`, { method:'POST' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getAnalysis(id) {
  const r = await fetch(`${API_BASE}/analysis/${id}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteAnalysis(id) {
  const r = await fetch(`${API_BASE}/analysis/${id}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listAnalysesByDoc(docId) {
  const r = await fetch(`${API_BASE}/analysis/by-document/${docId}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
