import { IsString, IsOptional, IsArray, IsIn } from 'class-validator';

export class UpdateFeatureDto {
  @IsString()
  @IsOptional()
  gherkinContent?: string;

  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsOptional()
  description?: string;
}

export class UpdateFeatureStatusDto {
  @IsString()
  @IsIn(['draft', 'in_review', 'approved', 'rejected', 'code_generated'])
  status: string;

  @IsString()
  @IsOptional()
  reviewNotes?: string;

  @IsString()
  @IsOptional()
  reviewedBy?: string;
}

export class GenerateTestCasesDto {
  @IsString()
  @IsOptional()
  documentId?: string;

  @IsString()
  @IsOptional()
  featureDescription?: string;

  includePositive?: boolean;
  includeNegative?: boolean;
  includeApiTests?: boolean;
  includeE2eTests?: boolean;
}

export class GenerateCodeDto {
  @IsString()
  @IsIn(['python', 'javascript'])
  language: string;
}
