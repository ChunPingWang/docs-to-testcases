import { Controller, Get, Put, Post, Body } from '@nestjs/common';
import { AiServiceClient } from '../../services/ai-service.client';

@Controller('settings')
export class SettingsController {
  constructor(private readonly aiClient: AiServiceClient) {}

  @Get()
  async getSettings() {
    return this.aiClient.getSettings();
  }

  @Put()
  async updateSettings(@Body() body: Record<string, unknown>) {
    return this.aiClient.updateSettings(body);
  }

  @Post('reset')
  async resetSettings() {
    return this.aiClient.resetSettings();
  }

  @Get('health')
  async getHealth() {
    return this.aiClient.getHealth();
  }

  @Get('models')
  async getModels() {
    return this.aiClient.getModels();
  }
}
