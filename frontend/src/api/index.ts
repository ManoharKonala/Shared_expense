import api from './client';

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  register: (email: string, name: string, password: string) =>
    api.post('/auth/register', { email, name, password }),

  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getMe: () => api.get('/auth/me'),
};

export const groupsApi = {
  list: () => api.get('/groups'),
  get: (id: string) => api.get(`/groups/${id}`),
  create: (name: string, baseCurrency: string = 'INR') =>
    api.post('/groups', { name, base_currency: baseCurrency }),
  addMember: (groupId: string, userId: string, joinedAt: string) =>
    api.post(`/groups/${groupId}/members`, { user_id: userId, joined_at: joinedAt }),
  removeMember: (groupId: string, userId: string, leftAt: string) =>
    api.delete(`/groups/${groupId}/members/${userId}`, { data: { left_at: leftAt } }),
};

export const expensesApi = {
  list: (groupId: string, params?: Record<string, string>) =>
    api.get(`/groups/${groupId}/expenses`, { params }),
  get: (id: string) => api.get(`/expenses/${id}`),
  create: (groupId: string, data: any) =>
    api.post(`/groups/${groupId}/expenses`, data),
  update: (id: string, data: any) =>
    api.put(`/expenses/${id}`, data),
  delete: (id: string, reason: string) =>
    api.delete(`/expenses/${id}`, { data: { reason } }),
};

export const balancesApi = {
  get: (groupId: string) => api.get(`/groups/${groupId}/balances`),
  getSuggested: (groupId: string) => api.get(`/groups/${groupId}/settlements-suggested`),
  getBreakdown: (userId: string, groupId: string) =>
    api.get(`/balances/${userId}/breakdown`, { params: { group_id: groupId } }),
};

export const settlementsApi = {
  list: (groupId: string) => api.get(`/groups/${groupId}/settlements`),
  create: (groupId: string, data: any) =>
    api.post(`/groups/${groupId}/settlements`, data),
};

export const importsApi = {
  upload: (groupId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/groups/${groupId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getSession: (sessionId: string) => api.get(`/import/${sessionId}`),
  resolveAnomaly: (sessionId: string, anomalyId: string, decision: string) =>
    api.patch(`/import/${sessionId}/anomalies/${anomalyId}`, { decision }),
  finalize: (sessionId: string) => api.post(`/import/${sessionId}/finalize`),
  getReport: (sessionId: string) => api.get(`/import/${sessionId}/report`),
};

export const auditApi = {
  list: (params?: Record<string, any>) => api.get('/audit', { params }),
};

