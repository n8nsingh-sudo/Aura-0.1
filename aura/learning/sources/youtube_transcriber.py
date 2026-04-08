import re
from aura.memory.fabric import MemoryFabric
from aura.learning.embedder import Embedder

try:
    from youtube_transcript_api import YouTubeTranscriptApi

    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False


class YouTubeTranscriber:
    def __init__(self, memory: MemoryFabric, embedder: Embedder):
        self.memory = memory
        self.embedder = embedder

    def _extract_video_id(self, url: str) -> str:
        patterns = [
            r"youtu\.be/([^&\n?#]+)",
            r"youtube\.com/watch\?v=([^&\n?#]+)",
            r"youtube\.com/embed/([^&\n?#]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url

    def transcribe(self, video_url: str) -> dict:
        if not YOUTUBE_AVAILABLE:
            return {"success": False, "error": "youtube-transcript-api not installed"}

        print(f"Transcribing: {video_url}")
        video_id = self._extract_video_id(video_url)

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            return {"success": False, "error": str(e), "video_id": video_id}

        full_text = " ".join([item["text"] for item in transcript_list])

        chunks = self._chunk_transcript(full_text, chunk_size=800)

        for i, chunk in enumerate(chunks):
            doc_id = f"youtube:{video_id}:chunk{i}"

            self.memory.remember(
                content=chunk,
                memory_type="knowledge",
                topic=f"youtube_video:{video_id}",
                source=f"https://youtube.com/watch?v={video_id}",
            )

            self.embedder.embed_and_store(
                text=chunk,
                doc_id=doc_id,
                metadata={"source": "youtube", "video_id": video_id, "chunk": i},
            )

        return {
            "success": True,
            "video_id": video_id,
            "total_words": len(full_text.split()),
            "chunks_stored": len(chunks),
        }

    def _chunk_transcript(self, text: str, chunk_size: int = 800) -> list:
        words = text.split()
        return [
            " ".join(words[i : i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
