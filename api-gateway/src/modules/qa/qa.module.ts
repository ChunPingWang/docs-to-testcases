import { Module } from '@nestjs/common';
import { QaController } from './qa.controller';
import { AiServiceClient } from '../../services/ai-service.client';

@Module({
  controllers: [QaController],
  providers: [AiServiceClient],
})
export class QaModule {}
