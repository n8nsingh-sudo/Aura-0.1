from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder
from aura.learning.sources.github_scanner import GitHubScanner
from aura.learning.sources.web_scraper import WebScraper
from aura.learning.sources.youtube_transcriber import YouTubeTranscriber


class UniversalIngestor:
    def __init__(self, memory: MemoryFabric, embedder: Embedder):
        self.github = GitHubScanner(memory, embedder)
        self.web = WebScraper(memory, embedder)
        self.youtube = YouTubeTranscriber(memory, embedder)

    def ingest(self, url: str) -> dict:
        url = url.strip()

        if "github.com" in url:
            return self.github.scan_repo(url)

        elif "youtube.com" in url or "youtu.be" in url:
            return self.youtube.transcribe(url)

        elif url.startswith("http"):
            return self.web.scrape(url)

        else:
            return {"success": False, "error": f"Cannot handle URL: {url}"}

    def ingest_batch(self, urls: list) -> list:
        return [self.ingest(url) for url in urls]
