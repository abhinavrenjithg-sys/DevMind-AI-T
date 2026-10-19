from typing import Dict, List, Any, Optional
from app.analysis.graph_engine import GraphEngine

class ChangeImpactAnalyzer:
    def __init__(self, graph_engine: GraphEngine, files: List[Dict[str, Any]], symbols: List[Dict[str, Any]]):
        self.graph_engine = graph_engine
        self.files = files
        self.symbols = symbols
        self.file_map = {f.get("id", f["path"]): f for f in files}
        self.symbol_map = {s.get("id", f"{s.get('file_path')}::{s['qualified_name']}"): s for s in symbols}

    def analyze_symbol_impact(self, target_id: str, depth: int = 3) -> Dict[str, Any]:
        """
        Calculates the blast radius of modifying a symbol or file.
        Returns direct dependents, transitive dependents, affected tests, and summary.
        """
        # Resolve target name and path
        target_name = target_id
        target_path = ""
        if target_id in self.symbol_map:
            target_name = self.symbol_map[target_id]["qualified_name"]
            target_path = self.symbol_map[target_id].get("file_path", "")
        elif target_id in self.file_map:
            target_name = self.file_map[target_id]["file_name"]
            target_path = self.file_map[target_id]["path"]

        blast = self.graph_engine.get_blast_radius(target_id, max_depth=depth)

        direct = blast["direct_dependents"]
        transitive = blast["transitive_dependents"]

        # Discover affected test files
        all_affected = direct + transitive
        affected_tests = []
        candidate_review_areas = set()

        for item in all_affected:
            fpath = item.get("file_path", "")
            if not fpath and item["id"] in self.file_map:
                fpath = self.file_map[item["id"]]["path"]

            if "test" in fpath.lower():
                affected_tests.append({
                    "test_file": fpath,
                    "target_dependent": item["name"],
                    "depth": item["depth"]
                })
            else:
                candidate_review_areas.add(fpath)

        summary = (
            f"Modifying '{target_name}' directly impacts {len(direct)} component(s) "
            f"and transitively reaches {len(transitive)} additional component(s) across {depth} dependency levels. "
            f"{len(affected_tests)} test suite(s) require verification."
        )

        return {
            "target_name": target_name,
            "target_path": target_path,
            "blast_radius_depth": depth,
            "summary": summary,
            "direct_dependents": direct,
            "transitive_dependents": transitive,
            "affected_tests": affected_tests,
            "candidate_review_areas": sorted(list(candidate_review_areas))[:15],
            "graph_blast_radius": {
                "direct_count": len(direct),
                "transitive_count": len(transitive),
                "test_count": len(affected_tests)
            }
        }
