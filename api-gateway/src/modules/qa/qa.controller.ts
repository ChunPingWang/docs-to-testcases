import { Controller, Post, Get, Body, Param, Res, Req } from '@nestjs/common';
import type { Response, Request } from 'express';
import axios from 'axios';
import { AiServiceClient } from '../../services/ai-service.client';

class AskQuestionDto {
  question: string;
  modelName?: string;
}

@Controller()
export class QaController {
  constructor(private readonly aiClient: AiServiceClient) {}

  @Post('projects/:projectId/qa')
  async askQuestion(
    @Param('projectId') projectId: string,
    @Body() dto: AskQuestionDto,
    @Res() res: Response,
  ) {
    // Proxy SSE stream from AI service
    const streamUrl = this.aiClient.getAskStreamUrl();

    const response = await axios.post(
      streamUrl,
      {
        project_id: projectId,
        question: dto.question,
        model_name: dto.modelName,
      },
      { responseType: 'stream' },
    );

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');

    response.data.pipe(res);
  }

  @Post('projects/:projectId/qa/sync')
  async askQuestionSync(
    @Param('projectId') projectId: string,
    @Body() dto: AskQuestionDto,
  ) {
    return this.aiClient.askQuestion({
      project_id: projectId,
      question: dto.question,
      model_name: dto.modelName,
    });
  }
}
