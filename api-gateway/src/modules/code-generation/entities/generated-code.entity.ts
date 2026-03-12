import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Feature } from '../../features/entities/feature.entity';

@Entity('generated_code')
export class GeneratedCode {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'feature_id' })
  featureId: string;

  @Column({ length: 20 })
  language: string;

  @Column({ length: 50 })
  framework: string;

  @Column({ name: 'file_path', length: 1000 })
  filePath: string;

  @Column({ name: 'code_content', type: 'text' })
  codeContent: string;

  @Column({ name: 'file_type', length: 50, nullable: true })
  fileType: string;

  @Column({ length: 50, default: 'generated' })
  status: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @ManyToOne(() => Feature, (f) => f.generatedCode, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'feature_id' })
  feature: Feature;
}
