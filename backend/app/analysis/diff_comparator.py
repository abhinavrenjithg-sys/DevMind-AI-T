from typing import Dict, List, Any

class RevisionComparator:
    """
    Compares two analyzed repository revisions to determine code and structural changes.
    """

    def compare_revisions(
        self,
        base_rev: Dict[str, Any],
        target_rev: Dict[str, Any]
    ) -> Dict[str, Any]:
        base_files = {f["path"]: f for f in base_rev.get("files", [])}
        target_files = {f["path"]: f for f in target_rev.get("files", [])}

        changed_files = []
        for path, tf in target_files.items():
            if path not in base_files:
                changed_files.append({"path": path, "change_type": "added", "lines": tf.get("lines_of_code", 0)})
            elif tf.get("lines_of_code") != base_files[path].get("lines_of_code"):
                changed_files.append({"path": path, "change_type": "modified", "lines_diff": tf.get("lines_of_code", 0) - base_files[path].get("lines_of_code", 0)})

        for path, bf in base_files.items():
            if path not in target_files:
                changed_files.append({"path": path, "change_type": "deleted", "lines": bf.get("lines_of_code", 0)})

        # Compare symbols
        base_syms = {s["qualified_name"]: s for s in base_rev.get("symbols", [])}
        target_syms = {s["qualified_name"]: s for s in target_rev.get("symbols", [])}

        added_symbols = [s for q, s in target_syms.items() if q not in base_syms]
        removed_symbols = [s for q, s in base_syms.items() if q not in target_syms]

        modified_symbols = []
        for q, ts in target_syms.items():
            if q in base_syms:
                bs = base_syms[q]
                if ts.get("signature") != bs.get("signature") or ts.get("return_type") != bs.get("return_type"):
                    modified_symbols.append({
                        "name": ts["name"],
                        "qualified_name": q,
                        "old_signature": bs.get("signature"),
                        "new_signature": ts.get("signature"),
                        "file_path": ts.get("file_path")
                    })

        # Impacted modules
        impacted_modules = sorted(list({f["path"] for f in changed_files if not f["path"].lower().startswith("test")}))
        related_tests = sorted(list({f["path"] for f in changed_files if "test" in f["path"].lower()}))

        return {
            "base_commit": base_rev.get("commit_hash", "base"),
            "target_commit": target_rev.get("commit_hash", "target"),
            "changed_files": changed_files,
            "added_symbols": added_symbols,
            "removed_symbols": removed_symbols,
            "modified_symbols": modified_symbols,
            "edge_diff": {
                "base_edge_count": len(base_rev.get("edges", [])),
                "target_edge_count": len(target_rev.get("edges", []))
            },
            "impacted_modules": impacted_modules,
            "related_tests": related_tests
        }
