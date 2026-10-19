export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  updated_at: string;
  repository_count: number;
}

export interface Repository {
  id: string;
  workspace_id: string;
  name: string;
  source_type: 'git_url' | 'zip_upload';
  remote_url?: string;
  default_branch: string;
  is_analyzed: boolean;
  created_at: string;
  updated_at: string;
  active_revision_id?: string;
  summary_stats?: {
    total_files: number;
    total_loc: number;
    total_size_bytes: number;
    total_symbols: number;
    total_edges: number;
    total_findings: number;
    languages: Record<string, number>;
    frameworks: string[];
    entry_points: string[];
    cycle_count: number;
    layers: Record<string, number>;
  };
}

export interface AnalysisJob {
  id: string;
  repository_id: string;
  revision_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_stage: string;
  progress_percentage: number;
  stage_logs: Array<{
    stage: string;
    message: string;
    progress: number;
    timestamp: string;
  }>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface SourceFile {
  id: string;
  revision_id: string;
  path: string;
  file_name: string;
  extension: string;
  language: string;
  size_bytes: number;
  lines_of_code: number;
  ast_parse_status: string;
  imports_count: number;
  symbols_count: number;
  layer: string;
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: 'directory' | 'file';
  language?: string;
  size?: number;
  lines?: number;
  symbols_count?: number;
  children?: FileTreeNode[];
}

export interface SymbolItem {
  id: string;
  file_id: string;
  name: string;
  qualified_name: string;
  kind: string;
  signature?: string;
  docstring?: string;
  start_line: number;
  end_line: number;
  start_col: number;
  end_col: number;
  visibility: string;
  decorators: string[];
  parameters: Array<{ name: string; type?: string }>;
  return_type?: string;
  file_path?: string;
}

export interface FileContentResponse {
  file_path: string;
  language: string;
  lines_of_code: number;
  content: string;
  symbols: SymbolItem[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'symbol' | 'module';
  kind?: string;
  path?: string;
  layer?: string;
  metrics: {
    in_degree?: number;
    out_degree?: number;
    centrality?: number;
    pagerank?: number;
  };
  [key: string]: any;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  relationship: string;
  certainty: string;
  source_line?: number;
}

export interface DependencyGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    cycle_count: number;
  };
  cycles: string[][];
}

export interface SearchResultItem {
  type: 'symbol' | 'file' | 'fulltext';
  title: string;
  subtitle?: string;
  file_path: string;
  start_line: number;
  end_line: number;
  language: string;
  score: number;
  excerpt?: string;
  symbol_kind?: string;
}

export interface EvidenceItem {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol_name?: string;
  snippet: string;
  explanation?: string;
}

export interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  created_at: string;
  evidence: EvidenceItem[];
}

export interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
  messages: MessageItem[];
}

export interface DependentItem {
  id: string;
  name: string;
  type: string;
  file_path: string;
  depth: number;
  relationship: string;
  reason: string;
}

export interface ChangeImpactResponse {
  target_name: string;
  target_path: string;
  blast_radius_depth: number;
  summary: string;
  direct_dependents: DependentItem[];
  transitive_dependents: DependentItem[];
  affected_tests: Array<{
    test_file: string;
    target_dependent: string;
    depth: number;
  }>;
  candidate_review_areas: string[];
  graph_blast_radius: {
    direct_count: number;
    transitive_count: number;
    test_count: number;
  };
}

export interface FindingItem {
  id: string;
  file_path: string;
  line_number: number;
  end_line_number?: number;
  tool: string;
  rule_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  message: string;
  code_snippet?: string;
  is_dismissed: boolean;
  dismissed_reason?: string;
}

export interface ArchitectureReportResponse {
  repository_name: string;
  analyzed_commit: string;
  analyzed_at: string;
  metrics: {
    total_files: number;
    total_loc: number;
    total_symbols: number;
    total_edges: number;
  };
  languages: Record<string, number>;
  layers: Record<string, string[]>;
  entry_points: Array<{ path: string }>;
  central_modules: Array<{
    path: string;
    in_degree: number;
    out_degree: number;
    centrality: number;
  }>;
  circular_dependencies: string[][];
  security_summary: Record<string, number>;
  limitations: string[];
  markdown_report: string;
}
