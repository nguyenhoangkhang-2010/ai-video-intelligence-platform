import re


class TextChunker:

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        return [chunk for chunk, _, _ in self.chunk_with_spans(text)]

    def chunk_with_spans(self, text: str) -> list[tuple[str, int, int]]:
        """
        Same chunks as `chunk`, each with the half-open range of word
        positions [start, end) it covers in the whitespace-split text.
        The word positions are what lets a chunk be mapped back to the
        time it was spoken (see ai.embedding.timing).
        """
        if not text or not text.strip():
            return []

        normalized_text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        words = normalized_text.split()

        if not words:
            return []

        chunks = []
        start = 0

        step = self.chunk_size - self.overlap

        while start < len(words):
            end = min(
                start + self.chunk_size,
                len(words),
            )

            chunk = " ".join(
                words[start:end]
            )

            if chunk:
                chunks.append((chunk, start, end))

            if end >= len(words):
                break

            start += step

        return chunks