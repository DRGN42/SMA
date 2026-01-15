"""
Text-to-Speech provider using Edge TTS (free, high quality).
Also includes fallback options.
"""
import logging
from pathlib import Path
from typing import List, Optional
import asyncio
import edge_tts

from core.entities import Chunk, AudioSegment
from core.interfaces import ITTSProvider

logger = logging.getLogger(__name__)


class HiggsAudioProvider(ITTSProvider):
    """TTS using Edge TTS with German voice."""
    
    def __init__(
        self,
        voice: str = "de-DE-ConradNeural",
        default_voice_sample: Optional[Path] = None
    ):
        self.voice = voice
        self.default_voice_sample = default_voice_sample
    
    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_sample: Optional[Path] = None
    ) -> AudioSegment:
        """Generate speech audio from text."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use edge-tts
        asyncio.run(self._generate_audio(text, output_path))
        
        # Get duration
        duration = self._get_audio_duration(output_path)
        
        return AudioSegment(
            chunk_index=-1,
            file_path=str(output_path),
            duration_sec=duration
        )
    
    async def _generate_audio(self, text: str, output_path: Path):
        """Generate audio using edge-tts."""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))
    
    def synthesize_chunks(
        self,
        chunks: List[Chunk],
        output_dir: Path,
        voice_sample: Optional[Path] = None
    ) -> List[AudioSegment]:
        """Generate audio for all chunks with cumulative timing."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        segments = []
        current_time = 0.0
        
        for chunk in chunks:
            filename = f"{chunk.index:04d}.mp3"
            output_path = output_dir / filename
            
            segment = self.synthesize(
                text=chunk.text,
                output_path=output_path,
                voice_sample=voice_sample
            )
            
            segment.chunk_index = chunk.index
            segment.start_time_sec = current_time
            
            pause_sec = chunk.pause_after_ms / 1000.0
            current_time += segment.duration_sec + pause_sec
            
            segments.append(segment)
            logger.info(f"Generated audio {chunk.index + 1}/{len(chunks)}")
        
        return segments
    
    def _get_audio_duration(self, path: Path) -> float:
        """Get duration of audio file in seconds."""
        try:
            from pydub import AudioSegment as PydubSegment
            audio = PydubSegment.from_file(str(path))
            return len(audio) / 1000.0
        except Exception as e:
            logger.warning(f"Could not get duration: {e}")
            return 3.0  # Default estimate
