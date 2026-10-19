from pathlib import Path
from typing import Dict, List, Any

class ArchitectureInferer:
    """
    Transparently categorizes files and symbols into architectural layers
    based on naming conventions, directory structure, imports, and declarations.
    """

    LAYERS = [
        "Presentation",
        "API / Controller",
        "Business / Service",
        "Data / Model",
        "Core / Infrastructure",
        "Test"
    ]

    def infer_file_layer(self, file_path: str, imports: List[Dict[str, Any]], symbols: List[Dict[str, Any]]) -> tuple[str, str]:
        path_lower = file_path.lower()
        parts = [p.lower() for p in Path(file_path).parts]

        # 1. Tests
        if any(p.startswith("test") or p.endswith("_test.py") or p.endswith(".test.ts") or p.endswith(".spec.ts") for p in parts) or "tests" in parts or "__tests__" in parts:
            return "Test", "File is located in a test directory or matches test file pattern."

        # 2. Presentation / UI
        if any(p in ("components", "views", "pages", "templates", "ui", "frontend") for p in parts) or file_path.endswith((".tsx", ".jsx", ".vue", ".css", ".html")):
            return "Presentation", "File defines UI views, components, or frontend markup."

        # 3. API / Controller
        if any(p in ("api", "controllers", "routes", "routers", "endpoints") for p in parts) or "main.py" in parts:
            return "API / Controller", "File handles HTTP requests, routes, or API endpoints."

        # 4. Data / Model
        if any(p in ("models", "schemas", "entities", "database", "alembic", "migrations", "repositories", "db") for p in parts):
            return "Data / Model", "File defines data structures, database schemas, ORM models, or migrations."

        # 5. Core / Infrastructure
        if any(p in ("core", "config", "middleware", "auth", "security", "infra", "utils", "helpers", "common", "lib") for p in parts):
            return "Core / Infrastructure", "File provides configuration, utilities, authentication, or infrastructure services."

        # 6. Business / Service
        if any(p in ("services", "domain", "usecases", "workflows", "tasks", "jobs", "managers") for p in parts):
            return "Business / Service", "File encapsulates business workflows and domain operations."

        # Heuristic check on symbols
        for s in symbols:
            name_lower = s["name"].lower()
            if "service" in name_lower or "manager" in name_lower or "handler" in name_lower:
                return "Business / Service", f"Symbol '{s['name']}' suggests business service logic."
            if "model" in name_lower or "schema" in name_lower or "table" in name_lower:
                return "Data / Model", f"Symbol '{s['name']}' suggests data modeling."

        return "Business / Service", "Default application logic."

    def generate_overview(self, files_with_layers: List[Dict[str, Any]], cycles: List[List[str]]) -> Dict[str, Any]:
        layer_distribution: Dict[str, int] = {layer: 0 for layer in self.LAYERS}
        layer_files: Dict[str, List[str]] = {layer: [] for layer in self.LAYERS}

        for f in files_with_layers:
            layer = f.get("layer", "Core / Infrastructure")
            if layer not in layer_distribution:
                layer_distribution[layer] = 0
                layer_files[layer] = []
            layer_distribution[layer] += 1
            layer_files[layer].append(f["path"])

        return {
            "layer_counts": layer_distribution,
            "layer_files": layer_files,
            "total_layers": len([k for k, v in layer_distribution.items() if v > 0]),
            "circular_dependency_warning": len(cycles) > 0,
            "cycle_count": len(cycles)
        }
