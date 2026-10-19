import datetime
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Integer, Boolean, Text, DateTime, ForeignKey, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )

    repositories: Mapped[List["Repository"]] = orm_relationship(
        "Repository", back_populates="workspace", cascade="all, delete-orphan"
    )

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="git_url") # "git_url" or "zip_upload"
    remote_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )

    workspace: Mapped["Workspace"] = orm_relationship("Workspace", back_populates="repositories")
    revisions: Mapped[List["RepositoryRevision"]] = orm_relationship(
        "RepositoryRevision", back_populates="repository", cascade="all, delete-orphan"
    )
    jobs: Mapped[List["AnalysisJob"]] = orm_relationship(
        "AnalysisJob", back_populates="repository", cascade="all, delete-orphan"
    )

class RepositoryRevision(Base):
    __tablename__ = "repository_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    commit_hash: Mapped[str] = mapped_column(String(64), index=True, default="HEAD")
    branch_name: Mapped[str] = mapped_column(String(100), default="main")
    commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    committed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    summary_stats: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    repository: Mapped["Repository"] = orm_relationship("Repository", back_populates="revisions")
    files: Mapped[List["SourceFile"]] = orm_relationship(
        "SourceFile", back_populates="revision", cascade="all, delete-orphan"
    )
    symbols: Mapped[List["Symbol"]] = orm_relationship(
        "Symbol", back_populates="revision", cascade="all, delete-orphan"
    )
    edges: Mapped[List["DependencyEdge"]] = orm_relationship(
        "DependencyEdge", back_populates="revision", cascade="all, delete-orphan"
    )
    findings: Mapped[List["AnalysisFinding"]] = orm_relationship(
        "AnalysisFinding", back_populates="revision", cascade="all, delete-orphan"
    )

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    revision_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True) # pending, running, completed, failed
    current_stage: Mapped[str] = mapped_column(String(50), default="discovery")
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    stage_logs: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    repository: Mapped["Repository"] = orm_relationship("Repository", back_populates="jobs")

class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(600), index=True, nullable=False) # e.g. "src/components/Header.tsx"
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    extension: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="unknown")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    lines_of_code: Mapped[int] = mapped_column(Integer, default=0)
    ast_parse_status: Mapped[str] = mapped_column(String(30), default="parsed") # parsed, failed, skipped
    imports_count: Mapped[int] = mapped_column(Integer, default=0)
    symbols_count: Mapped[int] = mapped_column(Integer, default=0)
    layer: Mapped[str] = mapped_column(String(50), default="General") # UI, API, Business, Data, Core, Utility, Test

    revision: Mapped["RepositoryRevision"] = orm_relationship("RepositoryRevision", back_populates="files")
    symbols: Mapped[List["Symbol"]] = orm_relationship("Symbol", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_source_files_rev_path", "revision_id", "path"),
    )

class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_files.id", ondelete="CASCADE"), index=True)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    qualified_name: Mapped[str] = mapped_column(String(400), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # function, class, method, interface, type_alias, variable
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    start_col: Mapped[int] = mapped_column(Integer, default=0)
    end_col: Mapped[int] = mapped_column(Integer, default=0)
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    decorators: Mapped[List[str]] = mapped_column(JSON, default=list)
    parameters: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    return_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    file: Mapped["SourceFile"] = orm_relationship("SourceFile", back_populates="symbols")
    revision: Mapped["RepositoryRevision"] = orm_relationship("RepositoryRevision", back_populates="symbols")

    __table_args__ = (
        Index("ix_symbols_rev_name", "revision_id", "name"),
    )

class DependencyEdge(Base):
    __tablename__ = "dependency_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(20), default="file") # file, symbol
    source_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(400), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), default="file") # file, symbol, external
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    target_name: Mapped[str] = mapped_column(String(400), nullable=False)
    relationship: Mapped[str] = mapped_column(String(30), default="import") # import, calls, inherits, contains, references
    certainty: Mapped[str] = mapped_column(String(20), default="confirmed") # confirmed, inferred, unresolved
    source_line: Mapped[int] = mapped_column(Integer, default=1)

    revision: Mapped["RepositoryRevision"] = orm_relationship("RepositoryRevision", back_populates="edges")

    __table_args__ = (
        Index("ix_edges_rev_rel", "revision_id", "relationship"),
    )

class AnalysisFinding(Base):
    __tablename__ = "analysis_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String(600), index=True, nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tool: Mapped[str] = mapped_column(String(50), default="ast_rules") # ruff, bandit, ast_rules
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium") # critical, high, medium, low, info
    message: Mapped[str] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    revision: Mapped["RepositoryRevision"] = orm_relationship("RepositoryRevision", back_populates="findings")

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Analysis Session")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )

    messages: Mapped[List["ConversationMessage"]] = orm_relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender: Mapped[str] = mapped_column(String(20), nullable=False) # "user", "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    conversation: Mapped["Conversation"] = orm_relationship("Conversation", back_populates="messages")
    evidence: Mapped[List["EvidenceReference"]] = orm_relationship(
        "EvidenceReference", back_populates="message", cascade="all, delete-orphan"
    )

class EvidenceReference(Base):
    __tablename__ = "evidence_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversation_messages.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String(600), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    message: Mapped["ConversationMessage"] = orm_relationship("ConversationMessage", back_populates="evidence")

class ChangeImpactReport(Base):
    __tablename__ = "change_impact_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_revisions.id", ondelete="CASCADE"), index=True)
    target_symbol_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_symbol_name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_file_path: Mapped[str] = mapped_column(String(600), nullable=False)
    blast_radius_depth: Mapped[int] = mapped_column(Integer, default=3)
    direct_dependents: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    transitive_dependents: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    affected_tests: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    candidate_review_areas: Mapped[List[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
