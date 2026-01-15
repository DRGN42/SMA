"""
Text chunker for splitting poems into TTS-friendly segments.
"""
from typing import List
import re
import logging

from core.entities import Poem, Chunk
from core.interfaces import IChunkerProvider

logger = logging.getLogger(__name__)


class TextChunker(IChunkerProvider):
    """
    Splits poem text into chunks suitable for TTS and video segments.
    
    Strategies:
    - By line (default): Each non-empty line becomes a chunk
    - By stanza: Empty lines separate stanzas
    - By character limit: Lines grouped to not exceed max_chars
    """
    
    CHARS_PER_SECOND = 12  # Average speaking rate
    
    def __init__(self, strategy: str = "line"):
        self.strategy = strategy
    
    def chunk_poem(self, poem: Poem, max_chars: int = 100) -> List[Chunk]:
        """Split poem text into chunks."""
        text = poem.text.strip()
        
        if self.strategy == "stanza":
            return self._chunk_by_stanza(text)
        elif self.strategy == "chars":
            return self._chunk_by_chars(text, max_chars)
        else:
            return self._chunk_by_line(text)
    
    def _chunk_by_line(self, text: str) -> List[Chunk]:
        """Split by individual lines."""
        lines = text.split("\n")
        chunks = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            chunk = Chunk(
                index=len(chunks),
                text=line,
                pause_after_ms=self._calculate_pause(line),
                estimated_duration_sec=len(line) / self.CHARS_PER_SECOND
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} line-based chunks")
        return chunks
    
    def _chunk_by_stanza(self, text: str) -> List[Chunk]:
        """Split by stanzas (separated by empty lines)."""
        stanzas = re.split(r"\n\s*\n", text)
        chunks = []
        
        for stanza in stanzas:
            stanza = stanza.strip()
            if not stanza:
                continue
            
            chunk = Chunk(
                index=len(chunks),
                text=stanza,
                pause_after_ms=800,
                estimated_duration_sec=len(stanza) / self.CHARS_PER_SECOND
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} stanza-based chunks")
        return chunks
    
    def _chunk_by_chars(self, text: str, max_chars: int) -> List[Chunk]:
        """Split by character limit, grouping lines."""
        lines = text.split("\n")
        chunks = []
        current_lines = []
        current_length = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_lines:
                    chunk_text = "\n".join(current_lines)
                    chunks.append(Chunk(
                        index=len(chunks),
                        text=chunk_text,
                        pause_after_ms=600,
                        estimated_duration_sec=len(chunk_text) / self.CHARS_PER_SECOND
                    ))
                    current_lines = []
                    current_length = 0
                continue
            
            if current_length + len(line) + 1 > max_chars and current_lines:
                chunk_text = "\n".join(current_lines)
                chunks.append(Chunk(
                    index=len(chunks),
                    text=chunk_text,
                    pause_after_ms=self._calculate_pause(chunk_text),
                    estimated_duration_sec=len(chunk_text) / self.CHARS_PER_SECOND
                ))
                current_lines = []
                current_length = 0
            
            current_lines.append(line)
            current_length += len(line) + 1
        
        if current_lines:
            chunk_text = "\n".join(current_lines)
            chunks.append(Chunk(
                index=len(chunks),
                text=chunk_text,
                pause_after_ms=self._calculate_pause(chunk_text),
                estimated_duration_sec=len(chunk_text) / self.CHARS_PER_SECOND
            ))
        
        logger.info(f"Created {len(chunks)} character-limited chunks (max {max_chars})")
        return chunks
    
    def _calculate_pause(self, text: str) -> int:
        """Calculate pause duration based on text ending."""
        text = text.strip()
        if not text:
            return 300
        
        last_char = text[-1]
        if last_char in ".!?":
            return 600
        elif last_char in ",;:":
            return 400
        else:
            return 300
