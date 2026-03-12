export default () => ({
  database: {
    url: process.env.DATABASE_URL || 'postgresql://appuser:apppass@localhost:5432/docstest',
  },
  aiService: {
    url: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  },
  upload: {
    dir: process.env.UPLOAD_DIR || './data/uploads',
  },
  features: {
    dir: process.env.FEATURES_DIR || './data/features',
  },
  generatedTests: {
    dir: process.env.GENERATED_TESTS_DIR || './data/generated-tests',
  },
});
