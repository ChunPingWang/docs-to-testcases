import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import * as path from 'path';
import * as fs from 'fs';
import { Document } from './entities/document.entity';
import { AiServiceClient } from '../../services/ai-service.client';

@Injectable()
export class DocumentsService {
  constructor(
    @InjectRepository(Document)
    private repo: Repository<Document>,
    private aiClient: AiServiceClient,
    private configService: ConfigService,
  ) {}

  async findByProject(projectId: string): Promise<Document[]> {
    return this.repo.find({
      where: { projectId },
      order: { createdAt: 'DESC' },
    });
  }

  async findOne(id: string): Promise<Document> {
    const doc = await this.repo.findOne({ where: { id } });
    if (!doc) throw new NotFoundException('Document not found');
    return doc;
  }

  async upload(
    projectId: string,
    file: Express.Multer.File,
  ): Promise<Document> {
    const uploadDir = this.configService.get<string>('upload.dir') || '/data/uploads';
    const docDir = path.join(uploadDir, projectId);
    fs.mkdirSync(docDir, { recursive: true });

    // Multer (busboy) decodes filenames as latin1 by default; re-decode as UTF-8
    const originalName = Buffer.from(file.originalname, 'latin1').toString('utf8');
    const ext = path.extname(originalName).toLowerCase().slice(1);
    const filename = `${Date.now()}-${originalName}`;
    const filePath = path.join(docDir, filename);

    fs.writeFileSync(filePath, file.buffer);

    const doc = this.repo.create({
      projectId,
      filename,
      originalName,
      filePath,
      fileType: ext,
      fileSize: file.size,
      mimeType: file.mimetype,
      status: 'uploaded',
    });

    const saved = await this.repo.save(doc);

    // Trigger async processing
    this.processDocument(saved).catch((err) => {
      console.error(`Failed to process document ${saved.id}:`, err);
    });

    return saved;
  }

  private async processDocument(doc: Document): Promise<void> {
    try {
      await this.repo.update(doc.id, { status: 'processing' });

      const result = await this.aiClient.processDocument({
        document_id: doc.id,
        file_path: doc.filePath,
        file_type: doc.fileType,
        project_id: doc.projectId,
      });

      await this.repo.update(doc.id, {
        status: 'processed',
        chunkCount: result.chunk_count,
      });
    } catch (err) {
      await this.repo.update(doc.id, {
        status: 'error',
        errorMessage: err.message || String(err),
      });
    }
  }

  async reprocess(id: string): Promise<Document> {
    const doc = await this.findOne(id);
    this.processDocument(doc).catch((err) => {
      console.error(`Failed to reprocess document ${id}:`, err);
    });
    return doc;
  }

  async remove(id: string): Promise<void> {
    const doc = await this.findOne(id);
    try {
      await this.aiClient.deleteDocumentEmbeddings(doc.id, doc.projectId);
    } catch {
      // Ignore if embeddings don't exist
    }
    if (fs.existsSync(doc.filePath)) {
      fs.unlinkSync(doc.filePath);
    }
    await this.repo.remove(doc);
  }
}
