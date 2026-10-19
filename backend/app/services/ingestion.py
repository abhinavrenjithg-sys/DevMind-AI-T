import os
import zipfile
import shutil
import urllib.parse
import ipaddress
import socket
from pathlib import Path
from typing import Dict, Any, Optional
import git

from app.core.config import settings

class IngestionSecurityError(Exception):
    pass

class RepositoryIngestionService:
    def __init__(self):
        settings.ensure_directories()

    def validate_git_url(self, url: str) -> None:
        """
        Validates git URL and prevents Server-Side Request Forgery (SSRF).
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise IngestionSecurityError("Only HTTP and HTTPS git URLs are supported.")

        hostname = parsed.hostname
        if not hostname:
            raise IngestionSecurityError("Invalid repository URL hostname.")

        # Block localhost and private IPs
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
        if hostname.lower() in blocked_hosts:
            raise IngestionSecurityError("Access to internal hostnames is prohibited.")

        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                raise IngestionSecurityError("Access to internal or private IP addresses is blocked.")
        except socket.gaierror:
            pass # DNS lookup will fail at clone time if unresolvable

    def clone_git_repository(self, url: str, repo_id: str, branch: Optional[str] = "main") -> Dict[str, Any]:
        """
        Safely clones a public Git repository and extracts commit hash.
        """
        self.validate_git_url(url)
        target_dir = settings.REPOS_DIR / repo_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            cloned_repo = git.Repo.clone_from(
                url,
                str(target_dir),
                depth=1,
                branch=branch if branch else None,
                env={"GIT_TERMINAL_PROMPT": "0"}
            )
            commit_hash = cloned_repo.head.commit.hexsha
            commit_msg = cloned_repo.head.commit.message.strip()
            author = cloned_repo.head.commit.author.name
            committed_at = cloned_repo.head.commit.committed_datetime

            return {
                "local_path": str(target_dir),
                "commit_hash": commit_hash,
                "commit_message": commit_msg,
                "author": author,
                "committed_at": committed_at,
                "branch_name": branch or "main"
            }
        except Exception as e:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise IngestionSecurityError(f"Failed to clone repository: {e}")

    def extract_zip_archive(self, zip_path: Path, repo_id: str) -> Dict[str, Any]:
        """
        Safely extracts an uploaded repository ZIP with Zip Slip and decompression bomb protection.
        """
        target_dir = settings.REPOS_DIR / repo_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)

        total_uncompressed_bytes = 0
        total_files = 0
        max_bytes = 200 * 1024 * 1024  # 200MB max uncompressed
        max_files = 10000

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.infolist():
                    total_files += 1
                    total_uncompressed_bytes += member.file_size

                    if total_files > max_files:
                        raise IngestionSecurityError(f"Archive exceeds maximum file count limit of {max_files}.")
                    if total_uncompressed_bytes > max_bytes:
                        raise IngestionSecurityError(f"Archive exceeds maximum uncompressed size of {max_bytes / (1024*1024):.0f}MB.")

                    # Zip Slip protection
                    extracted_path = (target_dir / member.filename).resolve()
                    if not str(extracted_path).startswith(str(target_dir.resolve())):
                        raise IngestionSecurityError(f"Malicious archive entry detected: {member.filename}")

                # Extract safely
                zf.extractall(target_dir)

            # If the zip contained a single top-level directory (standard GitHub zip download), normalize it
            items = [p for p in target_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
            if len(items) == 1 and not any(p.is_file() for p in target_dir.iterdir()):
                single_sub = items[0]
                for sub_item in single_sub.iterdir():
                    shutil.move(str(sub_item), str(target_dir))
                shutil.rmtree(single_sub, ignore_errors=True)

            return {
                "local_path": str(target_dir),
                "commit_hash": "ZIP-" + repo_id[:8],
                "commit_message": "Manual ZIP repository upload",
                "author": "Local User",
                "branch_name": "main"
            }
        except Exception as e:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise IngestionSecurityError(f"Failed to extract ZIP archive: {e}")
        finally:
            if zip_path.exists():
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
