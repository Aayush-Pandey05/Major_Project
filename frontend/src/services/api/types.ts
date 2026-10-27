export interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  planIntent?: string;
  structuredData?: SynthesizedResponse;
  createdAt: string;
}

export interface ChatSession {
  id: string;
  anonymousSessionId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages?: ChatMessage[];
}

export interface ColumnProfile {
  column_name: string;
  data_type: string;
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  is_numeric: boolean;
  sample_values: (string | null)[];
}

export interface NumericalStats {
  mean: number;
  std: number;
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
}

export interface DatasetProfile {
  file_name: string;
  sha256: string;
  row_count: number;
  column_count: number;
  duplicate_row_count: number;
  columns: ColumnProfile[];
  identified_date_columns: string[];
  candidate_target_columns: string[];
  numerical_summary: Record<string, NumericalStats>;
  preview_rows: Record<string, any>[];
}

export interface Dataset {
  id: string;
  anonymousSessionId: string;
  originalFilename: string;
  storedFilename: string;
  filePath: string;
  sha256Checksum: string;
  rowCount: number;
  columnCount: number;
  metadataJson: DatasetProfile;
  createdAt: string;
}

export interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
}

export interface TableSchema {
  table_name: string;
  columns: TableColumn[];
  primary_key: string[];
}

export interface DataSourceMetadata {
  id: string;
  name: string;
  type: string;
  sanitizedUrl: string;
  createdAt: string;
}

export interface ProgressEvent {
  step: string;
  agent: string;
  status: string;
  message: string;
  timestamp: number;
}

export interface ChartSpecification {
  chart_id: string;
  chart_type: 'line' | 'bar' | 'scatter' | 'heatmap' | 'histogram';
  title: string;
  figure: {
    data: any[];
    layout: Record<string, any>;
  };
  description?: string;
}

export interface SynthesizedResponse {
  answer: string;
  summary: string;
  key_findings: string[];
  tables: Array<{
    title: string;
    columns?: string[];
    rows: Record<string, any>[];
  }>;
  charts: ChartSpecification[];
  metrics: Record<string, any>;
  evidence: string[];
  limitations: string[];
  warnings: string[];
}

export interface AgentRunResult {
  sessionId: string;
  planIntent: string;
  targetAgents: string[];
  progressEvents: ProgressEvent[];
  response: SynthesizedResponse;
  executionTimeMs: number;
}

export interface SystemHealth {
  status: string;
  backend1: {
    service: string;
    databaseConnected: boolean;
    persistenceMode: string;
  };
  backend2: {
    status: string;
    service?: string;
    version?: string;
    models?: Record<string, boolean>;
    openai_configured?: boolean;
    error?: string;
  };
  timestamp: string;
}

export interface ApiError {
  message: string;
  statusCode?: number;
  details?: any;
}
