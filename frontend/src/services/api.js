const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function fetchCustomers() {
  const res = await fetch(`${API_BASE_URL}/api/customers`);
  if (!res.ok) throw new Error('Failed to fetch customers');
  return await res.json();
}

export async function createCustomer(data) {
  const res = await fetch(`${API_BASE_URL}/api/customers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create customer');
  return await res.json();
}

export async function startConversation(customerId, initialLanguage = 'English') {
  const res = await fetch(`${API_BASE_URL}/api/conversations/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, initial_language: initialLanguage }),
  });
  if (!res.ok) throw new Error('Failed to start conversation');
  return await res.json();
}

export async function sendMessage(conversationId, message, language = 'English') {
  const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, language }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return await res.json();
}

export async function endConversation(conversationId) {
  const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Failed to end conversation');
  return await res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${API_BASE_URL}/api/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return await res.json();
}

export async function fetchLeads() {
  const res = await fetch(`${API_BASE_URL}/api/leads`);
  if (!res.ok) throw new Error('Failed to fetch leads');
  return await res.json();
}

export async function fetchActions() {
  const res = await fetch(`${API_BASE_URL}/api/actions`);
  if (!res.ok) throw new Error('Failed to fetch actions');
  return await res.json();
}

export async function executeAction(actionId) {
  const res = await fetch(`${API_BASE_URL}/api/actions/${actionId}/execute`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to execute action');
  return await res.json();
}

export async function fetchCallbacks() {
  const res = await fetch(`${API_BASE_URL}/api/callbacks`);
  if (!res.ok) throw new Error('Failed to fetch callbacks');
  return await res.json();
}

export default {
  checkBackendHealth,
  fetchCustomers,
  createCustomer,
  startConversation,
  sendMessage,
  endConversation,
  fetchConversations,
  fetchLeads,
  fetchActions,
  executeAction,
  fetchCallbacks,
};
