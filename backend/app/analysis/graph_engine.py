import networkx as nx
from typing import Dict, List, Any, Optional, Set, Tuple

class GraphEngine:
    def __init__(self, files: List[Dict[str, Any]], symbols: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        self.files = files
        self.symbols = symbols
        self.edges = edges
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        # 1. Add file nodes
        for f in self.files:
            file_id = f.get("id") or f["path"]
            if not file_id:
                continue
            self.graph.add_node(
                file_id,
                label=f["file_name"],
                type="file",
                path=f["path"],
                layer=f.get("layer", "General"),
                lines=f.get("lines_of_code", 0)
            )

        # 2. Add symbol nodes
        for s in self.symbols:
            sym_id = s.get("id") or f"{s.get('file_path', '')}::{s.get('qualified_name', s.get('name', 'sym'))}"
            if not sym_id:
                continue
            self.graph.add_node(
                sym_id,
                label=s["name"],
                type="symbol",
                kind=s.get("kind", "symbol"),
                path=s.get("file_path"),
                layer=s.get("layer", "General"),
                signature=s.get("signature")
            )

        # 3. Add edges
        for idx, e in enumerate(self.edges):
            u = e["source_id"]
            v = e["target_id"]
            if not u or not v:
                continue
            if not self.graph.has_node(u):
                self.graph.add_node(u, label=e["source_name"], type=e["source_type"])
            if not self.graph.has_node(v):
                self.graph.add_node(v, label=e["target_name"], type=e["target_type"])

            edge_key = f"e_{idx}"
            self.graph.add_edge(
                u, v,
                key=edge_key,
                relationship=e.get("relationship", "references"),
                certainty=e.get("certainty", "confirmed"),
                source_line=e.get("source_line", 1)
            )

    def calculate_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculates node metrics: in-degree, out-degree, degree centrality, PageRank.
        """
        metrics: Dict[str, Dict[str, Any]] = {}
        if not self.graph.nodes:
            return metrics

        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        try:
            centrality = nx.degree_centrality(self.graph)
        except Exception:
            centrality = {n: 0.0 for n in self.graph.nodes}

        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85, max_iter=100)
        except Exception:
            pagerank = {n: 0.0 for n in self.graph.nodes}

        for n in self.graph.nodes:
            metrics[n] = {
                "in_degree": in_degrees.get(n, 0),
                "out_degree": out_degrees.get(n, 0),
                "centrality": round(centrality.get(n, 0.0), 4),
                "pagerank": round(pagerank.get(n, 0.0), 4)
            }
        return metrics

    def detect_cycles(self) -> List[List[str]]:
        """
        Identifies dependency cycles using strongly connected components (SCC).
        """
        cycles: List[List[str]] = []
        try:
            sccs = nx.strongly_connected_components(self.graph)
            for comp in sccs:
                if len(comp) > 1:
                    cycles.append([
                        self.graph.nodes[n].get("label", n) for n in comp
                    ])
        except Exception:
            pass
        return cycles

    def get_blast_radius(self, node_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Computes forward and reverse reachability for change impact analysis.
        Reverse: which nodes depend on this node (will break if this node changes).
        Forward: which nodes this node depends on.
        """
        if not self.graph.has_node(node_id):
            return {
                "direct_dependents": [],
                "transitive_dependents": [],
                "dependencies": [],
                "depth_reached": 0
            }

        # Reverse graph to traverse callers/dependents
        reversed_g = self.graph.reverse()
        
        direct_dependents = []
        for pred in reversed_g.successors(node_id):
            node_data = self.graph.nodes[pred]
            edge_data = self.graph.get_edge_data(pred, node_id, {})
            direct_dependents.append({
                "id": pred,
                "name": node_data.get("label", pred),
                "type": node_data.get("type", "unknown"),
                "file_path": node_data.get("path", ""),
                "depth": 1,
                "relationship": edge_data.get("relationship", "calls"),
                "reason": f"Directly {edge_data.get('relationship', 'references')} target"
            })

        # BFS for transitive dependents up to max_depth
        transitive_dependents = []
        visited = {node_id}
        for d in direct_dependents:
            visited.add(d["id"])

        current_level = [d["id"] for d in direct_dependents]
        for depth in range(2, max_depth + 1):
            next_level = []
            for curr in current_level:
                for successor in reversed_g.successors(curr):
                    if successor not in visited:
                        visited.add(successor)
                        next_level.append(successor)
                        node_data = self.graph.nodes[successor]
                        edge_data = self.graph.get_edge_data(successor, curr, {})
                        transitive_dependents.append({
                            "id": successor,
                            "name": node_data.get("label", successor),
                            "type": node_data.get("type", "unknown"),
                            "file_path": node_data.get("path", ""),
                            "depth": depth,
                            "relationship": edge_data.get("relationship", "references"),
                            "reason": f"Transitively reaches target at depth {depth}"
                        })
            current_level = next_level
            if not current_level:
                break

        return {
            "direct_dependents": direct_dependents,
            "transitive_dependents": transitive_dependents
        }

    def to_react_flow(self, filter_type: Optional[str] = None, filter_relationship: Optional[str] = None) -> Dict[str, Any]:
        """
        Serializes graph to React Flow compatible nodes and edges format.
        """
        metrics = self.calculate_metrics()
        nodes = []
        edges = []

        valid_node_ids = set()

        for n, data in self.graph.nodes(data=True):
            ntype = data.get("type", "file")
            if filter_type and ntype != filter_type and filter_type != "all":
                continue

            valid_node_ids.add(n)
            nodes.append({
                "id": str(n),
                "label": data.get("label", str(n)),
                "type": ntype,
                "kind": data.get("kind"),
                "path": data.get("path"),
                "layer": data.get("layer", "General"),
                "metrics": metrics.get(n, {})
            })

        for u, v, data in self.graph.edges(data=True):
            if u not in valid_node_ids or v not in valid_node_ids:
                continue
            rel = data.get("relationship", "references")
            if filter_relationship and rel != filter_relationship and filter_relationship != "all":
                continue

            edges.append({
                "id": f"{u}->{v}",
                "source": str(u),
                "target": str(v),
                "label": rel,
                "relationship": rel,
                "certainty": data.get("certainty", "confirmed"),
                "source_line": data.get("source_line", 1)
            })

        cycles = self.detect_cycles()

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "cycle_count": len(cycles)
            },
            "cycles": cycles
        }
