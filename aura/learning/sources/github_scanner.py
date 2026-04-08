import os
import subprocess
import tempfile
from pathlib import Path
from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder
from aura import config

CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".md"}


class GitHubScanner:
    def __init__(self, memory: MemoryFabric, embedder: Embedder):
        self.memory = memory
        self.embedder = embedder

    def scan_repo(self, repo_url: str) -> dict:
        print(f"Scanning repo: {repo_url}")
        stats = {"files_read": 0, "knowledge_stored": 0, "errors": 0}

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmp_dir],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                print(f"Clone failed: {result.stderr}")
                stats["errors"] += 1
                return stats

            for file_path in Path(tmp_dir).rglob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix not in CODE_EXTENSIONS:
                    continue
                if file_path.stat().st_size > 100_000:
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if not content.strip():
                        continue

                    relative_path = str(file_path.relative_to(tmp_dir))
                    topic = f"code:{repo_url}:{relative_path}"

                    self.memory.remember(
                        content=content[:2000],
                        memory_type="knowledge",
                        topic=topic,
                        source=repo_url,
                    )

                    doc_id = f"{repo_url}:{relative_path}".replace("/", "_")[:100]
                    self.embedder.embed_and_store(
                        text=content[:500],
                        doc_id=doc_id,
                        metadata={"source": repo_url, "path": relative_path},
                    )

                    stats["files_read"] += 1
                    stats["knowledge_stored"] += 1

                except Exception as e:
                    stats["errors"] += 1

        print(f"Scan complete: {stats}")
        return stats

    def scan_multiple(self, repo_urls: list) -> dict:
        total_stats = {"files_read": 0, "knowledge_stored": 0, "errors": 0}
        for url in repo_urls:
            stats = self.scan_repo(url)
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        return total_stats
