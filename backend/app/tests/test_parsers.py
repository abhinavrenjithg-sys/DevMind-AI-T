import pytest
from app.analysis.python_parser import PythonCodeParser
from app.analysis.typescript_parser import TypeScriptCodeParser
from app.analysis.dependency_resolver import DependencyResolver
from app.analysis.graph_engine import GraphEngine
from app.ai.citation_validator import CitationValidator
from app.services.ingestion import RepositoryIngestionService, IngestionSecurityError

def test_python_code_parser():
    parser = PythonCodeParser()
    code = """
import os
from .utils import helper, format_data

@decorator_one
def process_data(items: list, verbose: bool = False) -> int:
    \"\"\"Process raw data items.\"\"\"
    total = len(items)
    helper(total)
    return total

class DataProcessor(BaseHandler):
    def run(self):
        process_data([])
"""
    result = parser.parse_file(code, "app/processor.py")
    assert result["status"] == "parsed"
    assert len(result["imports"]) >= 2
    assert any(imp["name"] == "helper" for imp in result["imports"])
    assert any(imp["is_relative"] for imp in result["imports"])

    symbols = {s["qualified_name"]: s for s in result["symbols"]}
    assert "process_data" in symbols
    assert symbols["process_data"]["kind"] == "function"
    assert "int" in (symbols["process_data"]["return_type"] or "")
    assert "decorator_one" in symbols["process_data"]["decorators"]

    assert "DataProcessor" in symbols
    assert symbols["DataProcessor"]["kind"] == "class"
    assert "DataProcessor.run" in symbols

def test_typescript_code_parser():
    parser = TypeScriptCodeParser()
    code = """
import { useState, useEffect } from 'react';
import { ApiClient } from '../services/api';

export interface UserProfile {
    id: string;
    username: string;
}

export function fetchUserProfile(userId: string): Promise<UserProfile> {
    ApiClient.get(`/users/${userId}`);
    return Promise.resolve({ id: userId, username: "dev" });
}

export const renderHeader = () => {
    console.log("Rendering header");
};
"""
    result = parser.parse_file(code, "src/components/User.tsx")
    assert result["status"] == "parsed"
    assert len(result["imports"]) >= 2

    symbols = {s["name"]: s for s in result["symbols"]}
    assert "UserProfile" in symbols
    assert symbols["UserProfile"]["kind"] == "interface"
    assert "fetchUserProfile" in symbols
    assert symbols["fetchUserProfile"]["kind"] == "function"
    assert "renderHeader" in symbols

def test_dependency_resolver():
    files = [
        {"id": "f1", "path": "app/services/user_service.py", "language": "python"},
        {"id": "f2", "path": "app/models/user.py", "language": "python"},
    ]
    parsed_results = {
        "app/services/user_service.py": {
            "symbols": [{"name": "get_user", "qualified_name": "get_user", "kind": "function", "start_line": 5, "end_line": 10}],
            "imports": [{"module": "..models.user", "name": "User", "is_relative": True, "level": 2, "line": 2}],
            "calls": [{"name": "User", "line": 7}]
        },
        "app/models/user.py": {
            "symbols": [{"name": "User", "qualified_name": "User", "kind": "class", "start_line": 1, "end_line": 15, "parameters": []}],
            "imports": [],
            "calls": []
        }
    }
    resolver = DependencyResolver(files, parsed_results)
    edges = resolver.resolve_dependencies()

    assert len(edges) > 0
    # Should resolve relative import from user_service to models/user
    import_edges = [e for e in edges if e["relationship"] == "import"]
    assert any(e["target_name"] == "app/models/user.py" for e in import_edges)

def test_graph_engine_and_cycles():
    files = [
        {"id": "A", "path": "A.py", "file_name": "A.py", "lines_of_code": 10},
        {"id": "B", "path": "B.py", "file_name": "B.py", "lines_of_code": 20},
        {"id": "C", "path": "C.py", "file_name": "C.py", "lines_of_code": 30},
    ]
    symbols = []
    # Create cycle: A -> B -> C -> A
    edges = [
        {"source_id": "A", "source_name": "A", "source_type": "file", "target_id": "B", "target_name": "B", "target_type": "file", "relationship": "import"},
        {"source_id": "B", "source_name": "B", "source_type": "file", "target_id": "C", "target_name": "C", "target_type": "file", "relationship": "import"},
        {"source_id": "C", "source_name": "C", "source_type": "file", "target_id": "A", "target_name": "A", "target_type": "file", "relationship": "import"},
    ]
    engine = GraphEngine(files, symbols, edges)
    metrics = engine.calculate_metrics()
    assert metrics["A"]["in_degree"] == 1
    assert metrics["A"]["out_degree"] == 1

    cycles = engine.detect_cycles()
    assert len(cycles) == 1
    assert set(cycles[0]) == {"A.py", "B.py", "C.py"}

    # Test reverse blast radius: if C changes, who is impacted? B depends on C, A depends on B
    blast = engine.get_blast_radius("C", max_depth=3)
    direct_ids = {d["id"] for d in blast["direct_dependents"]}
    assert "B" in direct_ids
    transitive_ids = {t["id"] for t in blast["transitive_dependents"]}
    assert "A" in transitive_ids

def test_citation_validator():
    files = [
        {"path": "app/core/auth.py", "lines_of_code": 50},
        {"path": "app/api/login.py", "lines_of_code": 80}
    ]
    validator = CitationValidator(files)
    text = "Authentication tokens are verified in [app/core/auth.py:10-25] and processed in [app/api/login.py:40]."
    _, verified = validator.validate_citations(text, [])

    assert len(verified) == 2
    assert verified[0]["file_path"] == "app/core/auth.py"
    assert verified[0]["start_line"] == 10
    assert verified[0]["end_line"] == 25
    assert verified[1]["file_path"] == "app/api/login.py"
    assert verified[1]["start_line"] == 40
    assert verified[1]["end_line"] == 40

def test_ingestion_security_ssrf():
    svc = RepositoryIngestionService()
    # Localhost and private IPs must be blocked
    with pytest.raises(IngestionSecurityError):
        svc.validate_git_url("http://localhost:8080/repo.git")

    with pytest.raises(IngestionSecurityError):
        svc.validate_git_url("http://127.0.0.1/evil.git")

    with pytest.raises(IngestionSecurityError):
        svc.validate_git_url("file:///etc/passwd")
