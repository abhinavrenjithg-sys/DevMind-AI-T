import type {
  Workspace,
  Repository,
  AnalysisJob,
  SourceFile,
  FileTreeNode,
  FileContentResponse,
  SymbolItem,
  DependencyGraphResponse,
  SearchResultItem,
  MessageItem,
  ConversationItem,
  ChangeImpactResponse,
  FindingItem,
  ArchitectureReportResponse
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorText = await res.text();
    let detail = errorText;
    try {
      const parsed = JSON.parse(errorText);
      detail = parsed.detail || errorText;
    } catch {
      // Keep errorText
    }
    throw new Error(detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Workspaces
  async getWorkspaces(): Promise<Workspace[]> {
    return fetchJson(`${API_BASE}/workspaces/`);
  },
  async createWorkspace(name: string, description?: string): Promise<Workspace> {
    return fetchJson(`${API_BASE}/workspaces/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description })
    });
  },

  // Repositories
  async getRepositories(workspaceId?: string): Promise<Repository[]> {
    const url = workspaceId
      ? `${API_BASE}/repositories/?workspace_id=${encodeURIComponent(workspaceId)}`
      : `${API_BASE}/repositories/`;
    return fetchJson(url);
  },
  async getRepository(repoId: string): Promise<Repository> {
    return fetchJson(`${API_BASE}/repositories/${repoId}`);
  },
  async importGitRepo(workspaceId: string, name: string, gitUrl: string, branch = 'main'): Promise<Repository> {
    return fetchJson(`${API_BASE}/repositories/import-git`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId, name, git_url: gitUrl, branch })
    });
  },
  async uploadZipRepo(workspaceId: string, name: string, file: File): Promise<Repository> {
    const formData = new FormData();
    formData.append('workspace_id', workspaceId);
    formData.append('name', name);
    formData.append('file', file);
    return fetchJson(`${API_BASE}/repositories/upload-zip`, {
      method: 'POST',
      body: formData
    });
  },
  async deleteRepository(repoId: string): Promise<void> {
    await fetchJson(`${API_BASE}/repositories/${repoId}`, { method: 'DELETE' });
  },

  // Analysis
  async startAnalysis(repoId: string): Promise<AnalysisJob> {
    return fetchJson(`${API_BASE}/analysis/jobs/${repoId}`, { method: 'POST' });
  },
  async getJobStatus(jobId: string): Promise<AnalysisJob> {
    return fetchJson(`${API_BASE}/analysis/jobs/${jobId}`);
  },
  async getLatestJob(repoId: string): Promise<AnalysisJob> {
    return fetchJson(`${API_BASE}/analysis/jobs/repo/${repoId}`);
  },

  // Code Explorer
  async getFiles(revisionId: string, layer?: string, language?: string): Promise<SourceFile[]> {
    const params = new URLSearchParams();
    if (layer) params.append('layer', layer);
    if (language) params.append('language', language);
    return fetchJson(`${API_BASE}/code/files/${revisionId}?${params.toString()}`);
  },
  async getFileTree(revisionId: string): Promise<FileTreeNode[]> {
    return fetchJson(`${API_BASE}/code/tree/${revisionId}`);
  },
  async getFileContent(revisionId: string, path: string): Promise<FileContentResponse> {
    return fetchJson(`${API_BASE}/code/file-content/${revisionId}?path=${encodeURIComponent(path)}`);
  },
  async getSymbols(revisionId: string, kind?: string, query?: string): Promise<SymbolItem[]> {
    const params = new URLSearchParams();
    if (kind) params.append('kind', kind);
    if (query) params.append('query', query);
    return fetchJson(`${API_BASE}/code/symbols/${revisionId}?${params.toString()}`);
  },

  // Dependency Graph
  async getDependencyGraph(revisionId: string, nodeType = 'file', relationship = 'all'): Promise<DependencyGraphResponse> {
    const params = new URLSearchParams({ node_type: nodeType, relationship });
    return fetchJson(`${API_BASE}/graph/${revisionId}?${params.toString()}`);
  },

  // Search
  async search(
    revisionId: string,
    query: string,
    searchType = 'all',
    language?: string,
    layer?: string
  ): Promise<{ query: string; total_results: number; results: SearchResultItem[] }> {
    return fetchJson(`${API_BASE}/search/${revisionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, search_type: searchType, language, layer })
    });
  },

  // AI Assistant
  async askQuestion(revisionId: string, question: string, conversationId?: string): Promise<MessageItem> {
    return fetchJson(`${API_BASE}/ai/${revisionId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, conversation_id: conversationId })
    });
  },
  async getConversations(revisionId: string): Promise<ConversationItem[]> {
    return fetchJson(`${API_BASE}/ai/${revisionId}/conversations`);
  },

  // Change Impact
  async analyzeImpact(
    revisionId: string,
    symbolId?: string,
    symbolName?: string,
    filePath?: string,
    depth = 3
  ): Promise<ChangeImpactResponse> {
    return fetchJson(`${API_BASE}/impact/${revisionId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol_id: symbolId, symbol_name: symbolName, file_path: filePath, depth })
    });
  },

  // Security & Quality
  async getFindings(revisionId: string, severity?: string, tool?: string, includeDismissed = false): Promise<FindingItem[]> {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (tool) params.append('tool', tool);
    if (includeDismissed) params.append('include_dismissed', 'true');
    return fetchJson(`${API_BASE}/security/${revisionId}/findings?${params.toString()}`);
  },
  async dismissFinding(findingId: string, dismissed: boolean, reason?: string): Promise<FindingItem> {
    return fetchJson(`${API_BASE}/security/findings/${findingId}/dismiss`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dismissed, reason })
    });
  },

  // Compare Revisions
  async compareRevisions(baseRevisionId: string, targetRevisionId: string) {
    return fetchJson(`${API_BASE}/compare/revisions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_revision_id: baseRevisionId, target_revision_id: targetRevisionId })
    });
  },

  // Architecture Report
  async getArchitectureReport(revisionId: string): Promise<ArchitectureReportResponse> {
    return fetchJson(`${API_BASE}/reports/${revisionId}/architecture`);
  }
};
