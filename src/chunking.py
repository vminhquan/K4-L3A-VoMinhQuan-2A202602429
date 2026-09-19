from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on sentence terminators while preserving them
        raw_sentences = re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(group).strip()
            if chunk_str:
                chunks.append(chunk_str)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            # Fallback: hard split by chunk_size when no separators remain
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        if sep not in current_text:
            return self._split(current_text, next_seps)

        parts = current_text.split(sep)
        pieces: list[str] = []
        for part in parts:
            if not part:
                continue
            if len(part) > self.chunk_size:
                pieces.extend(self._split(part, next_seps))
            else:
                pieces.append(part)

        # Merge adjacent pieces back together up to chunk_size
        chunks: list[str] = []
        current = ""
        for piece in pieces:
            if not current:
                current = piece
            elif len(current) + len(sep) + len(piece) <= self.chunk_size:
                current = current + sep + piece
            else:
                chunks.append(current)
                current = piece
        if current:
            chunks.append(current)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        overlap = max(0, int(chunk_size * 0.1))
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from Markdown text if present."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


class HeadingChunker:
    """
    Custom chunker designed for university regulations and policies.
    Splits text by Markdown headings (e.g. '## Điều ...') and attaches
    the heading to each chunk to preserve regulatory context.
    """

    def __init__(self, chunk_size: int = 500, heading_pattern: str = r"^##\s+") -> None:
        self.chunk_size = max(1, chunk_size)
        self.heading_pattern = heading_pattern

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        clean_text = strip_frontmatter(text)
        lines = clean_text.splitlines()

        sections: list[tuple[str, list[str]]] = []
        current_heading = ""
        current_lines: list[str] = []

        for line in lines:
            if re.match(self.heading_pattern, line):
                if current_lines or current_heading:
                    sections.append((current_heading, current_lines))
                current_heading = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines or current_heading:
            sections.append((current_heading, current_lines))

        chunks: list[str] = []
        fallback_chunker = RecursiveChunker(chunk_size=self.chunk_size)

        for heading, body_lines in sections:
            body = "\n".join(body_lines).strip()
            if not body:
                if heading:
                    chunks.append(heading)
                continue

            full_section = f"{heading}\n\n{body}".strip() if heading else body
            if len(full_section) <= self.chunk_size:
                chunks.append(full_section)
            else:
                sub_chunks = fallback_chunker.chunk(body)
                for sc in sub_chunks:
                    header_prefix = f"[{heading.lstrip('#').strip()}] " if heading else ""
                    if len(header_prefix) + len(sc) <= self.chunk_size:
                        chunks.append(f"{header_prefix}{sc}")
                    else:
                        chunks.append(sc)

        return chunks

