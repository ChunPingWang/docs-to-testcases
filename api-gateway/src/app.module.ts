import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import configuration from './config/configuration';
import { ProjectsModule } from './modules/projects/projects.module';
import { DocumentsModule } from './modules/documents/documents.module';
import { FeaturesModule } from './modules/features/features.module';
import { QaModule } from './modules/qa/qa.module';
import { FinetuneModule } from './modules/finetune/finetune.module';
import { SettingsModule } from './modules/settings/settings.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
    }),
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        url: config.get<string>('database.url'),
        autoLoadEntities: true,
        synchronize: false, // Using init-db.sql for schema
      }),
    }),
    ProjectsModule,
    DocumentsModule,
    FeaturesModule,
    QaModule,
    FinetuneModule,
    SettingsModule,
  ],
})
export class AppModule {}
