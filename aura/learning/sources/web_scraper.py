import httpx
from bs4 import BeautifulSoup
from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder


class WebScraper:
    def __init__(self, memory: MemoryFabric, embedder: Embedder):
        self.memory = memory
        self.embedder = embedder
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; AURA-Agent/1.0)"}

    def scrape(self, url: str) -> dict:
        print(f"Scraping: {url}")

        try:
            response = httpx.get(
                url,
                headers=self.headers,
                timeout=30,
                follow_redirects=True,
                verify=False,
            )
            response.raise_for_status()
        except Exception as e:
            return {"success": False, "error": str(e)}

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else url

        main = soup.find("article") or soup.find("main") or soup.find("body")
        content = main.get_text(separator="\n", strip=True) if main else ""

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        clean_content = "\n".join(lines)

        if len(clean_content) < 100:
            return {"success": False, "error": "Not enough content found"}

        chunks = self._chunk_text(clean_content, chunk_size=1000)

        for i, chunk in enumerate(chunks):
            doc_id = f"web:{url}:chunk{i}".replace("/", "_")[:100]

            self.memory.remember(
                content=chunk,
                memory_type="knowledge",
                topic=f"web:{title_text}",
                source=url,
            )

            self.embedder.embed_and_store(
                text=chunk,
                doc_id=doc_id,
                metadata={"source": url, "title": title_text, "chunk": i},
            )

        return {
            "success": True,
            "title": title_text,
            "chunks_stored": len(chunks),
            "url": url,
        }

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list:
        words = text.split()
        chunks = []
        step = int(chunk_size * 0.8)

        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks
