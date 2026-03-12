export interface Project {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  documents?: Document[];
  features?: Feature[];
}

export interface Document {
  id: string;
  projectId: string;
  filename: string;
  originalName: string;
  filePath: string;
  fileType: string;
  fileSize: number;
  mimeType: string;
  status: string;
  chunkCount: number;
  errorMessage?: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Feature {
  id: string;
  projectId: string;
  documentId?: string;
  name: string;
  description?: string;
  filePath: string;
  gherkinContent: string;
  status: string;
  reviewNotes?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  tags: string[];
  scenarioCount: number;
  version: number;
  createdAt: string;
  updatedAt: string;
  generatedCode?: GeneratedCode[];
}

export interface GeneratedCode {
  id: string;
  featureId: string;
  language: string;
  framework: string;
  filePath: string;
  codeContent: string;
  fileType: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface QaMessage {
  role: 'user' | 'assistant';
  content: string;
  contextChunks?: Array<{
    text: string;
    metadata: Record<string, any>;
    relevance_score: number;
  }>;
}

export interface ModelSettings {
  llm_model: string;
  embedding_model: string;
  temperature_qa: number;
  temperature_test_case: number;
  temperature_test_code: number;
  temperature_finetune: number;
  max_tokens_qa: number;
  max_tokens_test_case: number;
  max_tokens_test_code: number;
  max_tokens_finetune: number;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
}

export interface HealthStatus {
  status: string;
  ollama_connected: boolean;
  chroma_connected: boolean;
  models_available: string[];
}
