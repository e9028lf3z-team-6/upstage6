const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

function getHeaders() {
  const token = localStorage.getItem('token');
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { ...getHeaders(), ...options.headers };
  const r = await fetch(url, { ...options, headers });
  if (!r.ok) {
    if (r.status === 401) {
      localStorage.removeItem('token');
      // Optional: redirect to login or refresh page
    }
    throw new Error(await r.text());
  }
  return r.json();
}

export async function listDocuments() {
  return request('/documents');
}

export async function uploadDocument(file) {
  const fd = new FormData();
  fd.append('file', file);
  return request('/documents/upload', { method:'POST', body: fd });
}

export async function getDocument(id) {
  return request(`/documents/${id}`);
}

export async function updateDocument(id, updates) {
  return request(`/documents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
}

export async function deleteDocument(id) {
  return request(`/documents/${id}`, { method: 'DELETE' });
}

export async function runAnalysis(docId, options = {}) {
  const payload = {};
  if (typeof options.personaCount === 'number') {
    payload.persona_count = options.personaCount;
  }
  if (typeof options.creativeFocus === 'boolean') {
    payload.creative_focus = options.creativeFocus;
  }
  const hasPayload = Object.keys(payload).length > 0;
  return request(`/analysis/run/${docId}`, {
    method: 'POST',
    ...(hasPayload
      ? {
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }
      : {}),
  });
}

export async function getAnalysis(id) {
  return request(`/analysis/${id}`);
}

export async function deleteAnalysis(id) {
  return request(`/analysis/${id}`, { method: 'DELETE' });
}

export async function listAnalysesByDoc(docId) {
  return request(`/analysis/by-document/${docId}`);
}

// Auth related
export async function getMe() {
  return request('/auth/me');
}

export function logout() {
  localStorage.removeItem('token');
  window.location.href = '/';
}
