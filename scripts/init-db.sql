CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename        VARCHAR(500) NOT NULL,
    original_name   VARCHAR(500) NOT NULL,
    file_path       VARCHAR(1000) NOT NULL,
    file_type       VARCHAR(50) NOT NULL,
    file_size       BIGINT NOT NULL,
    mime_type       VARCHAR(100),
    status          VARCHAR(50) DEFAULT 'uploaded',
    chunk_count     INTEGER DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_status ON documents(status);

CREATE TABLE document_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content_preview VARCHAR(500),
    section_title   VARCHAR(500),
    heading_path    VARCHAR(1000),
    page_number     INTEGER,
    token_count     INTEGER,
    chroma_id       VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);

CREATE TABLE features (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id     UUID REFERENCES documents(id) ON DELETE SET NULL,
    name            VARCHAR(500) NOT NULL,
    description     TEXT,
    file_path       VARCHAR(1000) NOT NULL,
    gherkin_content TEXT NOT NULL,
    status          VARCHAR(50) DEFAULT 'draft',
    review_notes    TEXT,
    reviewed_by     VARCHAR(255),
    reviewed_at     TIMESTAMPTZ,
    tags            TEXT[],
    scenario_count  INTEGER DEFAULT 0,
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_features_project ON features(project_id);
CREATE INDEX idx_features_status ON features(status);

CREATE TABLE scenarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id      UUID NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    name            VARCHAR(500) NOT NULL,
    type            VARCHAR(50) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    gherkin_content TEXT NOT NULL,
    tags            TEXT[],
    has_examples    BOOLEAN DEFAULT FALSE,
    example_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scenarios_feature ON scenarios(feature_id);

CREATE TABLE generated_code (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id      UUID NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    language        VARCHAR(20) NOT NULL,
    framework       VARCHAR(50) NOT NULL,
    file_path       VARCHAR(1000) NOT NULL,
    code_content    TEXT NOT NULL,
    file_type       VARCHAR(50),
    status          VARCHAR(50) DEFAULT 'generated',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_generated_code_feature ON generated_code(feature_id);

CREATE TABLE finetune_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status          VARCHAR(50) DEFAULT 'pending',
    model_name      VARCHAR(255),
    training_file   VARCHAR(1000),
    validation_file VARCHAR(1000),
    config          JSONB DEFAULT '{}',
    metrics         JSONB DEFAULT '{}',
    training_pairs  INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE qa_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    context_chunks  JSONB,
    model_used      VARCHAR(255),
    response_time   INTEGER,
    rating          SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_qa_project ON qa_history(project_id);
