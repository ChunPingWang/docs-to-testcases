import { Controller, Post, Get, Body, Param } from '@nestjs/common';
import { AiServiceClient } from '../../services/ai-service.client';

class FinetuneConfigDto {
  config?: Record<string, any>;
}

@Controller()
export class FinetuneController {
  constructor(private readonly aiClient: AiServiceClient) {}

  @Post('projects/:projectId/finetune/prepare')
  prepareData(@Param('projectId') projectId: string) {
    return this.aiClient.prepareFinetuneData({ project_id: projectId });
  }

  @Post('projects/:projectId/finetune/start')
  start(
    @Param('projectId') projectId: string,
    @Body() dto: FinetuneConfigDto,
  ) {
    return this.aiClient.startFinetune({
      project_id: projectId,
      config: dto.config,
    });
  }

  @Get('finetune-jobs/:jobId/status')
  getStatus(@Param('jobId') jobId: string) {
    return this.aiClient.getFinetuneStatus(jobId);
  }
}
