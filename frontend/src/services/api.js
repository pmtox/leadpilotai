const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  ?? (import.meta.env.DEV ? 'http://localhost:8000' : '');

function apiFetch(path, options = {}) {
  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
  });
}

export async function checkBackendHealth() {
  try {
    const res = await apiFetch('/health');
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function fetchAuthStatus() {
  const res = await apiFetch('/api/auth/status');
  if (!res.ok) throw new Error('Failed to check sign-in configuration');
  return await res.json();
}

export async function fetchCurrentUser() {
  const res = await apiFetch('/api/auth/me');
  if (res.status === 401) return null;
  if (!res.ok) throw new Error('Failed to load your profile');
  return await res.json();
}

export async function updateProfile(data) {
  const res = await apiFetch('/api/auth/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Failed to update your profile');
  }
  return await res.json();
}

export async function logout() {
  const res = await apiFetch('/api/auth/logout', { method: 'POST' });
  if (!res.ok) throw new Error('Failed to sign out');
  return await res.json();
}

export function googleLoginUrl() {
  return `${API_BASE_URL}/api/auth/google`;
}

export async function fetchCustomers() {
  const res = await apiFetch('/api/customers');
  if (!res.ok) throw new Error('Failed to fetch customers');
  return await res.json();
}

export async function createCustomer(data) {
  const res = await apiFetch('/api/customers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create customer');
  return await res.json();
}

export async function startConversation(customerId, initialLanguage = 'English') {
  const res = await apiFetch('/api/conversations/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, initial_language: initialLanguage }),
  });
  if (!res.ok) throw new Error('Failed to start conversation');
  return await res.json();
}

export async function sendMessage(conversationId, message, language = 'English') {
  const res = await apiFetch(`/api/conversations/${conversationId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, language }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return await res.json();
}

export async function sendAudioMessage(conversationId, audioBlob, filename, language = 'English') {
  const formData = new FormData();
  formData.append('file', audioBlob, filename);
  formData.append('language', language);

  const res = await apiFetch(`/api/conversations/${conversationId}/audio`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Audio request failed (HTTP ${res.status})`);
  }
  return await res.json();
}

export async function endConversation(conversationId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Failed to end conversation');
  return await res.json();
}

export async function fetchConversations() {
  const res = await apiFetch('/api/conversations');
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return await res.json();
}

export async function fetchLeads() {
  const res = await apiFetch('/api/leads');
  if (!res.ok) throw new Error('Failed to fetch leads');
  return await res.json();
}

export async function fetchActions() {
  const res = await apiFetch('/api/actions');
  if (!res.ok) throw new Error('Failed to fetch actions');
  return await res.json();
}

export async function executeAction(actionId, consentConfirmed = false) {
  const res = await apiFetch(`/api/actions/${actionId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consent_confirmed: consentConfirmed }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Failed to execute action');
  }
  return await res.json();
}

export async function fetchCallbacks() {
  const res = await apiFetch('/api/callbacks');
  if (!res.ok) throw new Error('Failed to fetch callbacks');
  return await res.json();
}

export default {
  checkBackendHealth,
  fetchAuthStatus,
  fetchCurrentUser,
  updateProfile,
  logout,
  googleLoginUrl,
  fetchCustomers,
  createCustomer,
  startConversation,
  sendMessage,
  sendAudioMessage,
  endConversation,
  fetchConversations,
  fetchLeads,
  fetchActions,
  executeAction,
  fetchCallbacks,
};
