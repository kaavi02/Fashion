// API Client & Session Management
const API_BASE = '/api';

function getSessionId() {
  let sid = localStorage.getItem('vogue_session_id');
  if (!sid) {
    sid = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem('vogue_session_id', sid);
  }
  return sid;
}

function getAuthToken() {
  return localStorage.getItem('vogue_token');
}

function setAuth(token, user) {
  localStorage.setItem('vogue_token', token);
  localStorage.setItem('vogue_user', JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem('vogue_token');
  localStorage.removeItem('vogue_user');
}

function getCurrentUser() {
  const u = localStorage.getItem('vogue_user');
  try {
    return u ? JSON.parse(u) : null;
  } catch (e) {
    return null;
  }
}

async function apiFetch(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const errorMsg = data.detail || 'An unexpected error occurred';
    throw new Error(errorMsg);
  }
  return data;
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'success' ? 'bg-dark text-white' : type === 'danger' ? 'bg-danger text-white' : 'bg-primary text-white';
  
  toast.className = `toast align-items-center ${bgClass} border-0 show shadow-lg mb-2`;
  toast.role = 'alert';
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2 py-2 px-3">
        <i class="bi ${type === 'success' ? 'bi-check-circle-fill text-success' : 'bi-info-circle-fill'}"></i>
        <span>${message}</span>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}
