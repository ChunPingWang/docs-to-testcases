import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  UseInterceptors,
  UploadedFile,
  UploadedFiles,
} from '@nestjs/common';
import { FileInterceptor, FilesInterceptor } from '@nestjs/platform-express';
import { DocumentsService } from './documents.service';

@Controller()
export class DocumentsController {
  constructor(private readonly service: DocumentsService) {}

  @Get('projects/:projectId/documents')
  findByProject(@Param('projectId') projectId: string) {
    return this.service.findByProject(projectId);
  }

  @Get('documents/:id')
  findOne(@Param('id') id: string) {
    return this.service.findOne(id);
  }

  @Get('documents/:id/status')
  async getStatus(@Param('id') id: string) {
    const doc = await this.service.findOne(id);
    return { id: doc.id, status: doc.status, chunkCount: doc.chunkCount };
  }

  @Post('projects/:projectId/documents')
  @UseInterceptors(FilesInterceptor('files', 10))
  async upload(
    @Param('projectId') projectId: string,
    @UploadedFiles() files: Express.Multer.File[],
  ) {
    const results: any[] = [];
    for (const file of files) {
      const doc = await this.service.upload(projectId, file);
      results.push(doc);
    }
    return results;
  }

  @Post('documents/:id/reprocess')
  reprocess(@Param('id') id: string) {
    return this.service.reprocess(id);
  }

  @Delete('documents/:id')
  remove(@Param('id') id: string) {
    return this.service.remove(id);
  }
}
