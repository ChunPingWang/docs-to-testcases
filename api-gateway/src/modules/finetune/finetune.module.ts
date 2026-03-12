import { Module } from '@nestjs/common';
import { FinetuneController } from './finetune.controller';
import { AiServiceClient } from '../../services/ai-service.client';

@Module({
  controllers: [FinetuneController],
  providers: [AiServiceClient],
})
export class FinetuneModule {}
