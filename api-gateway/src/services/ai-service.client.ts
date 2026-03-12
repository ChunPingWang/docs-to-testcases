import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { AxiosInstance } from 'axios';

@Injectable()
export class AiServiceClient {
  private client: AxiosInstance;

  constructor(private configService: ConfigService) {
    const baseURL = this.configService.get<string>('aiService.url');
    this.client = axios.create({ baseURL, timeout: 300000 });
  }

  async processDocument(data: {
    document_id: string;
    file_path: string;
    file_type: string;
    project_id: string;
  }) {
    const resp = await this.client.post('/ai/documents/process', data);
    return resp.data;
  }

  async deleteDocumentEmbeddings(documentId: string, projectId: string) {
    const resp = await this.client.delete(
      `/ai/documents/${documentId}?project_id=${projectId}`,
    );
    return resp.data;
  }

  async askQuestion(data: {
    project_id: string;
    question: string;
    model_name?: string;
  }) {
    const resp = await this.client.post('/ai/qa/ask/sync', data);
    return resp.data;
  }

  getAskStreamUrl() {
    return `${this.configService.get<string>('aiService.url')}/ai/qa/ask`;
  }

  async generateTestCases(data: {
    project_id: string;
    document_id?: string;
    feature_description?: string;
    include_positive?: boolean;
    include_negative?: boolean;
    include_api_tests?: boolean;
    include_e2e_tests?: boolean;
  }) {
    const resp = await this.client.post('/ai/generate/test-cases', data);
    return resp.data;
  }

  async generateTestCode(data: {
    gherkin_content: string;
    language: string;
    project_id: string;
    context_query?: string;
  }) {
    const resp = await this.client.post('/ai/generate/test-code', data);
    return resp.data;
  }

  async prepareFinetuneData(data: { project_id: string }) {
    const resp = await this.client.post('/ai/finetune/prepare', data);
    return resp.data;
  }

  async startFinetune(data: { project_id: string; config?: object }) {
    const resp = await this.client.post('/ai/finetune/start', data);
    return resp.data;
  }

  async getFinetuneStatus(jobId: string) {
    const resp = await this.client.get(`/ai/finetune/${jobId}/status`);
    return resp.data;
  }

  async getHealth() {
    const resp = await this.client.get('/ai/health');
    return resp.data;
  }
}
