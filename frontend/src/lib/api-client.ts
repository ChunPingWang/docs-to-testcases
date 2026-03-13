import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api',
  timeout: 300000,
});

// ── Projects ──────────────────────────────────────────
export const getProjects = () => api.get('/projects').then((r) => r.data);
export const getProject = (id: string) => api.get(`/projects/${id}`).then((r) => r.data);
export const createProject = (data: { name: string; description?: string }) =>
  api.post('/projects', data).then((r) => r.data);
export const updateProject = (id: string, data: { name?: string; description?: string }) =>
  api.put(`/projects/${id}`, data).then((r) => r.data);
export const deleteProject = (id: string) => api.delete(`/projects/${id}`);

// ── Documents ─────────────────────────────────────────
export const getDocuments = (projectId: string) =>
  api.get(`/projects/${projectId}/documents`).then((r) => r.data);
export const getDocumentStatus = (id: string) =>
  api.get(`/documents/${id}/status`).then((r) => r.data);
export const uploadDocuments = (projectId: string, files: File[]) => {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));
  return api.post(`/projects/${projectId}/documents`, formData).then((r) => r.data);
};
export const deleteDocument = (id: string) => api.delete(`/documents/${id}`);

// ── Features (Test Cases) ─────────────────────────────
export const getFeatures = (projectId: string) =>
  api.get(`/projects/${projectId}/features`).then((r) => r.data);
export const getFeature = (id: string) =>
  api.get(`/features/${id}`).then((r) => r.data);
export const updateFeature = (id: string, data: { gherkinContent?: string; name?: string }) =>
  api.put(`/features/${id}`, data).then((r) => r.data);
export const updateFeatureStatus = (
  id: string,
  data: { status: string; reviewNotes?: string; reviewedBy?: string },
) => api.patch(`/features/${id}/status`, data).then((r) => r.data);
export const deleteFeature = (id: string) => api.delete(`/features/${id}`);

// ── Generation ────────────────────────────────────────
export const generateTestCases = (
  projectId: string,
  data: {
    documentId?: string;
    featureDescription?: string;
    includePositive?: boolean;
    includeNegative?: boolean;
    includeApiTests?: boolean;
    includeE2eTests?: boolean;
  },
) => api.post(`/projects/${projectId}/generate`, data).then((r) => r.data);

export const generateTestCode = (featureId: string, language: string) =>
  api.post(`/features/${featureId}/generate-code`, { language }).then((r) => r.data);

export const getGeneratedCode = (featureId: string) =>
  api.get(`/features/${featureId}/code`).then((r) => r.data);

// ── Q&A ───────────────────────────────────────────────
export const askQuestionSync = (projectId: string, question: string) =>
  api.post(`/projects/${projectId}/qa/sync`, { question }).then((r) => r.data);

export const askQuestionStream = (projectId: string, question: string) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';
  return fetch(`${baseUrl}/projects/${projectId}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
};

// ── Fine-tune ─────────────────────────────────────────
export const prepareFinetuneData = (projectId: string) =>
  api.post(`/projects/${projectId}/finetune/prepare`).then((r) => r.data);
export const startFinetune = (projectId: string, config?: object) =>
  api.post(`/projects/${projectId}/finetune/start`, { config }).then((r) => r.data);
export const getFinetuneStatus = (jobId: string) =>
  api.get(`/finetune-jobs/${jobId}/status`).then((r) => r.data);

// ── Settings ─────────────────────────────────────────
export const getSettings = () => api.get('/settings').then((r) => r.data);
export const updateSettings = (data: Record<string, unknown>) =>
  api.put('/settings', data).then((r) => r.data);
export const resetSettings = () => api.post('/settings/reset').then((r) => r.data);
export const getHealthStatus = () => api.get('/settings/health').then((r) => r.data);
export const getAvailableModels = () => api.get('/settings/models').then((r) => r.data);

export default api;
