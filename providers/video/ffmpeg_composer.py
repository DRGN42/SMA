from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

from providers.base import VideoComposer


class FFMPEGComposer(VideoComposer):
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def compose(
        self,
        image_paths: List[str],
        audio_paths: List[str],
        subtitles_path: str,
        output_path: str,
        music_path: Optional[str] = None,
        fps: int = 30,
    ) -> str:
        output_path = str(output_path)
        temp_dir = Path(output_path).parent
        segments_list = temp_dir / "segments.txt"
        concat_audio = temp_dir / "concatenated_audio.wav"
        self._concat_audio(audio_paths, concat_audio)

        durations = [self._probe_duration(path) for path in audio_paths]
        with segments_list.open("w", encoding="utf-8") as handle:
            for image, duration in zip(image_paths, durations):
                handle.write(f"file '{Path(image).as_posix()}'\n")
                handle.write(f"duration {duration}\n")
            handle.write(f"file '{Path(image_paths[-1]).as_posix()}'\n")

        video_temp = temp_dir / "video_no_audio.mp4"
        zoom_filter = (
            "zoompan=z='min(zoom+0.0008,1.08)':d=1:x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':s=1080x1920,"
            "fps=30"
        )
        subprocess.run(
            [
                self.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(segments_list),
                "-vf",
                zoom_filter,
                "-r",
                str(fps),
                "-pix_fmt",
                "yuv420p",
                str(video_temp),
            ],
            check=True,
        )

        audio_inputs = ["-i", str(concat_audio)]
        filter_complex = []
        if music_path:
            audio_inputs.extend(["-i", str(music_path)])
            filter_complex = ["[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]"]
            audio_map = "[a]"
        else:
            audio_map = "0:a"
        subtitle_filter = ["-vf", f"subtitles={subtitles_path}"]
        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(video_temp),
            *audio_inputs,
            *subtitle_filter,
        ]
        if filter_complex:
            command.extend(["-filter_complex", filter_complex[0], "-map", "0:v", "-map", audio_map])
        command.extend(
            [
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-shortest",
                output_path,
            ]
        )
        subprocess.run(command, check=True)
        return output_path

    def _concat_audio(self, audio_paths: List[str], output_path: Path) -> None:
        list_path = output_path.parent / "audio_list.txt"
        with list_path.open("w", encoding="utf-8") as handle:
            for audio in audio_paths:
                handle.write(f"file '{Path(audio).as_posix()}'\n")
        subprocess.run(
            [
                self.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(output_path),
            ],
            check=True,
        )

    def _probe_duration(self, audio_path: str) -> float:
        result = subprocess.run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                audio_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        return float(payload["format"]["duration"])
