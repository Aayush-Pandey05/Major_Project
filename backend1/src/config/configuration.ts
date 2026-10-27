import * as path from 'path';

export default () => ({
  port: parseInt(process.env.BACKEND1_PORT || '3001', 10),
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000',
  backend2Url: process.env.BACKEND2_URL || 'http://localhost:8000',
  databaseUrl: process.env.DATABASE_URL || '',
  directUrl: process.env.DIRECT_URL || '',
  internalToken: process.env.INTERNAL_SERVICE_TOKEN || 'dev-internal-secret-token',
  uploadsDir: process.env.UPLOADS_DIR || path.resolve(__dirname, '../../storage/uploads'),
  resultsDir: process.env.RESULTS_DIR || path.resolve(__dirname, '../../storage/generated-results'),
  maxUploadSizeMb: parseInt(process.env.MAX_UPLOAD_SIZE_MB || '50', 10),
});
