import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import * as path from 'path';
import * as fs from 'fs';
import { Feature } from './entities/feature.entity';
import { GeneratedCode } from '../code-generation/entities/generated-code.entity';
import { AiServiceClient } from '../../services/ai-service.client';
import {
  UpdateFeatureDto,
  UpdateFeatureStatusDto,
  GenerateTestCasesDto,
  GenerateCodeDto,
} from './dto/feature.dto';

@Injectable()
export class FeaturesService {
  constructor(
    @InjectRepository(Feature)
    private featureRepo: Repository<Feature>,
    @InjectRepository(GeneratedCode)
    private codeRepo: Repository<GeneratedCode>,
    private aiClient: AiServiceClient,
    private configService: ConfigService,
  ) {}

  async findByProject(projectId: string): Promise<Feature[]> {
    return this.featureRepo.find({
      where: { projectId },
      order: { createdAt: 'DESC' },
    });
  }

  async findOne(id: string): Promise<Feature> {
    const feature = await this.featureRepo.findOne({
      where: { id },
      relations: ['generatedCode'],
    });
    if (!feature) throw new NotFoundException('Feature not found');
    return feature;
  }

  async generateTestCases(
    projectId: string,
    dto: GenerateTestCasesDto,
  ): Promise<Feature[]> {
    const result = await this.aiClient.generateTestCases({
      project_id: projectId,
      document_id: dto.documentId,
      feature_description: dto.featureDescription,
      include_positive: dto.includePositive ?? true,
      include_negative: dto.includeNegative ?? true,
      include_api_tests: dto.includeApiTests ?? true,
      include_e2e_tests: dto.includeE2eTests ?? true,
    });

    const featuresDir = this.configService.get<string>('features.dir') || '/data/features';
    const projectDir = path.join(featuresDir, projectId);
    fs.mkdirSync(projectDir, { recursive: true });

    const saved: Feature[] = [];

    for (const generated of result.features) {
      const safeName = generated.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '');
      const fileName = `${safeName}.feature`;
      const filePath = path.join(projectDir, fileName);

      fs.writeFileSync(filePath, generated.gherkin_content, 'utf-8');

      const feature = this.featureRepo.create({
        projectId,
        documentId: dto.documentId || undefined,
        name: generated.name,
        filePath,
        gherkinContent: generated.gherkin_content,
        status: 'draft',
        tags: generated.tags,
        scenarioCount: generated.scenario_count,
      });

      saved.push(await this.featureRepo.save(feature));
    }

    return saved;
  }

  async update(id: string, dto: UpdateFeatureDto): Promise<Feature> {
    const feature = await this.findOne(id);

    if (dto.gherkinContent) {
      feature.gherkinContent = dto.gherkinContent;
      feature.version += 1;
      // Update file on disk
      fs.writeFileSync(feature.filePath, dto.gherkinContent, 'utf-8');
    }
    if (dto.name) feature.name = dto.name;
    if (dto.description) feature.description = dto.description;

    return this.featureRepo.save(feature);
  }

  async updateStatus(
    id: string,
    dto: UpdateFeatureStatusDto,
  ): Promise<Feature> {
    const feature = await this.findOne(id);
    feature.status = dto.status;
    if (dto.reviewNotes) feature.reviewNotes = dto.reviewNotes;
    if (dto.reviewedBy) feature.reviewedBy = dto.reviewedBy;
    if (
      dto.status === 'approved' ||
      dto.status === 'rejected' ||
      dto.status === 'in_review'
    ) {
      feature.reviewedAt = new Date();
    }
    return this.featureRepo.save(feature);
  }

  async generateCode(id: string, dto: GenerateCodeDto) {
    const feature = await this.findOne(id);

    const result = await this.aiClient.generateTestCode({
      gherkin_content: feature.gherkinContent,
      language: dto.language,
      project_id: feature.projectId,
      context_query: feature.name,
    });

    const testsDir = this.configService.get<string>('generatedTests.dir') || '/data/generated-tests';
    const codeDir = path.join(testsDir, dto.language, feature.projectId);
    fs.mkdirSync(codeDir, { recursive: true });

    const savedFiles: GeneratedCode[] = [];

    for (const file of result.files) {
      const filePath = path.join(codeDir, file.filename);
      const fileDir = path.dirname(filePath);
      fs.mkdirSync(fileDir, { recursive: true });
      fs.writeFileSync(filePath, file.content, 'utf-8');

      const code = this.codeRepo.create({
        featureId: feature.id,
        language: dto.language,
        framework: result.framework,
        filePath,
        codeContent: file.content,
        fileType: file.file_type,
      });
      savedFiles.push(await this.codeRepo.save(code));
    }

    await this.featureRepo.update(id, { status: 'code_generated' });

    return { feature: await this.findOne(id), files: savedFiles };
  }

  async getCode(id: string): Promise<GeneratedCode[]> {
    return this.codeRepo.find({
      where: { featureId: id },
      order: { createdAt: 'DESC' },
    });
  }

  async remove(id: string): Promise<void> {
    const feature = await this.findOne(id);
    if (fs.existsSync(feature.filePath)) {
      fs.unlinkSync(feature.filePath);
    }
    await this.featureRepo.remove(feature);
  }

  async download(id: string): Promise<{ filePath: string; fileName: string }> {
    const feature = await this.findOne(id);
    return {
      filePath: feature.filePath,
      fileName: path.basename(feature.filePath),
    };
  }
}
