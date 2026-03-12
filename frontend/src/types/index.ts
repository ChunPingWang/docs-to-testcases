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
