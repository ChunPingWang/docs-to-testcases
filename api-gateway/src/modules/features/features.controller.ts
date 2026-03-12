import {
  Controller,
  Get,
  Post,
  Put,
  Patch,
  Delete,
  Body,
  Param,
  Res,
} from '@nestjs/common';
import type { Response } from 'express';
import { FeaturesService } from './features.service';
import {
  UpdateFeatureDto,
  UpdateFeatureStatusDto,
  GenerateTestCasesDto,
  GenerateCodeDto,
} from './dto/feature.dto';

@Controller()
export class FeaturesController {
  constructor(private readonly service: FeaturesService) {}

  @Get('projects/:projectId/features')
  findByProject(@Param('projectId') projectId: string) {
    return this.service.findByProject(projectId);
  }

  @Post('projects/:projectId/generate')
  generateTestCases(
    @Param('projectId') projectId: string,
    @Body() dto: GenerateTestCasesDto,
  ) {
    return this.service.generateTestCases(projectId, dto);
  }

  @Get('features/:id')
  findOne(@Param('id') id: string) {
    return this.service.findOne(id);
  }

  @Put('features/:id')
  update(@Param('id') id: string, @Body() dto: UpdateFeatureDto) {
    return this.service.update(id, dto);
  }

  @Patch('features/:id/status')
  updateStatus(@Param('id') id: string, @Body() dto: UpdateFeatureStatusDto) {
    return this.service.updateStatus(id, dto);
  }

  @Post('features/:id/generate-code')
  generateCode(@Param('id') id: string, @Body() dto: GenerateCodeDto) {
    return this.service.generateCode(id, dto);
  }

  @Get('features/:id/code')
  getCode(@Param('id') id: string) {
    return this.service.getCode(id);
  }

  @Get('features/:id/download')
  async download(@Param('id') id: string, @Res() res: Response) {
    const { filePath, fileName } = await this.service.download(id);
    res.download(filePath, fileName);
  }

  @Delete('features/:id')
  remove(@Param('id') id: string) {
    return this.service.remove(id);
  }
}
