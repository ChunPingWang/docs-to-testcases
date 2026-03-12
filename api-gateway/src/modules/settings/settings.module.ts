import { Module } from '@nestjs/common';
import { SettingsController } from './settings.controller';
import { AiServiceClient } from '../../services/ai-service.client';

@Module({
  controllers: [SettingsController],
  providers: [AiServiceClient],
})
export class SettingsModule {}
