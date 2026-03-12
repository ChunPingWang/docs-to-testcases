import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Feature } from './entities/feature.entity';
import { GeneratedCode } from '../code-generation/entities/generated-code.entity';
import { FeaturesController } from './features.controller';
import { FeaturesService } from './features.service';
import { AiServiceClient } from '../../services/ai-service.client';

@Module({
  imports: [TypeOrmModule.forFeature([Feature, GeneratedCode])],
  controllers: [FeaturesController],
  providers: [FeaturesService, AiServiceClient],
  exports: [FeaturesService],
})
export class FeaturesModule {}
