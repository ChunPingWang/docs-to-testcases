import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  OneToMany,
  JoinColumn,
} from 'typeorm';
import { Project } from '../../projects/entities/project.entity';
import { GeneratedCode } from '../../code-generation/entities/generated-code.entity';

@Entity('features')
export class Feature {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'project_id' })
  projectId: string;

  @Column({ name: 'document_id', nullable: true })
  documentId: string;

  @Column({ length: 500 })
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ name: 'file_path', length: 1000 })
  filePath: string;

  @Column({ name: 'gherkin_content', type: 'text' })
  gherkinContent: string;

  @Column({ length: 50, default: 'draft' })
  status: string;

  @Column({ name: 'review_notes', type: 'text', nullable: true })
  reviewNotes: string;

  @Column({ name: 'reviewed_by', length: 255, nullable: true })
  reviewedBy: string;

  @Column({ name: 'reviewed_at', type: 'timestamptz', nullable: true })
  reviewedAt: Date;

  @Column({ type: 'text', array: true, nullable: true })
  tags: string[];

  @Column({ name: 'scenario_count', default: 0 })
  scenarioCount: number;

  @Column({ default: 1 })
  version: number;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @ManyToOne(() => Project, (p) => p.features, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'project_id' })
  project: Project;

  @OneToMany(() => GeneratedCode, (gc) => gc.feature)
  generatedCode: GeneratedCode[];
}
