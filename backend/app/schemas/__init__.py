from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import datetime

# --- Workspace ---
class WorkspaceBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    slug: Optional[str] = None

class WorkspaceResponse(WorkspaceBase):
    id: str
    slug: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    repository_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# --- Repository ---
class RepositoryImportGit(BaseModel):
    workspace_id: str
    name: str
    git_url: str
    branch: Optional[str] = "main"

class RepositoryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    source_type: str
    remote_url: Optional[str]
    default_branch: str
    is_analyzed: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    active_revision_id: Optional[str] = None
    summary_stats: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

# --- Analysis Job ---
class AnalysisJobResponse(BaseModel):
    id: str
    repository_id: str
    revision_id: Optional[str]
    status: str
    current_stage: str
    progress_percentage: int
    stage_logs: List[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- Code and Symbols ---
class SymbolResponse(BaseModel):
    id: str
    file_id: str
    name: str
    qualified_name: str
    kind: str
    signature: Optional[str] = None
    docstring: Optional[str] = None
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    visibility: str
    decorators: List[str] = []
    parameters: List[Dict[str, Any]] = []
    return_type: Optional[str] = None
    file_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SourceFileResponse(BaseModel):
    id: str
    revision_id: str
    path: str
    file_name: str
    extension: str
    language: str
    size_bytes: int
    lines_of_code: int
    ast_parse_status: str
    imports_count: int
    symbols_count: int
    layer: str

    model_config = ConfigDict(from_attributes=True)

class FileContentResponse(BaseModel):
    file_path: str
    language: str
    lines_of_code: int
    content: str
    symbols: List[SymbolResponse]

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str # "directory" or "file"
    language: Optional[str] = None
    size: Optional[int] = None
    lines: Optional[int] = None
    symbols_count: Optional[int] = None
    children: Optional[List["FileTreeNode"]] = None

# --- Dependency Graph ---
class GraphNode(BaseModel):
    id: str
    label: str
    type: str # "file", "symbol", "module", "layer"
    kind: Optional[str] = None
    path: Optional[str] = None
    layer: Optional[str] = "General"
    metrics: Dict[str, Any] = Field(default_factory=dict) # in_degree, out_degree, centrality

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str # "imports", "calls", "inherits", "contains"
    relationship: str
    certainty: str # "confirmed", "inferred", "unresolved"
    source_line: Optional[int] = 1

class DependencyGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, Any]
    cycles: List[List[str]] = []

# --- Search ---
class SearchQuery(BaseModel):
    query: str
    search_type: str = "all" # all, symbol, file, fulltext, regex
    language: Optional[str] = None
    layer: Optional[str] = None
    limit: int = 50

class SearchResultItem(BaseModel):
    type: str # "symbol", "file", "fulltext"
    title: str
    subtitle: Optional[str] = None
    file_path: str
    start_line: int
    end_line: int
    language: str
    score: float
    excerpt: Optional[str] = None
    symbol_kind: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]

# --- AI Assistant ---
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class EvidenceItem(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = None
    snippet: str
    explanation: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    created_at: datetime.datetime
    evidence: List[EvidenceItem] = []

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime.datetime
    messages: List[MessageResponse] = []

# --- Change Impact ---
class ChangeImpactRequest(BaseModel):
    symbol_id: Optional[str] = None
    file_path: Optional[str] = None
    symbol_name: Optional[str] = None
    diff_text: Optional[str] = None
    depth: int = 3

class DependentItem(BaseModel):
    id: str
    name: str
    type: str
    file_path: str
    depth: int
    relationship: str
    reason: str

class ChangeImpactResponse(BaseModel):
    target_name: str
    target_path: str
    blast_radius_depth: int
    summary: str
    direct_dependents: List[DependentItem]
    transitive_dependents: List[DependentItem]
    affected_tests: List[Dict[str, Any]]
    candidate_review_areas: List[str]
    graph_blast_radius: Dict[str, Any]

# --- Security & Code Quality ---
class FindingResponse(BaseModel):
    id: str
    file_path: str
    line_number: int
    end_line_number: Optional[int]
    tool: str
    rule_id: str
    severity: str
    message: str
    code_snippet: Optional[str]
    is_dismissed: bool
    dismissed_reason: Optional[str]

class DismissFindingRequest(BaseModel):
    dismissed: bool = True
    reason: Optional[str] = None

# --- Revision Comparison ---
class RevisionCompareRequest(BaseModel):
    base_revision_id: str
    target_revision_id: str

class RevisionCompareResponse(BaseModel):
    base_commit: str
    target_commit: str
    changed_files: List[Dict[str, Any]]
    added_symbols: List[SymbolResponse]
    removed_symbols: List[SymbolResponse]
    modified_symbols: List[Dict[str, Any]]
    edge_diff: Dict[str, Any]
    impacted_modules: List[str]
    related_tests: List[str]

# --- Architecture Report ---
class ArchitectureReportResponse(BaseModel):
    repository_name: str
    analyzed_commit: str
    analyzed_at: datetime.datetime
    metrics: Dict[str, Any]
    languages: Dict[str, int]
    layers: Dict[str, List[str]]
    entry_points: List[Dict[str, Any]]
    central_modules: List[Dict[str, Any]]
    circular_dependencies: List[List[str]]
    security_summary: Dict[str, int]
    limitations: List[str]
    markdown_report: str
