#!/usr/bin/env python3
"""Prepare video assembly assets (concat list + subtitles) for ffmpeg."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoConfig:
    seconds_per_image: float
    resolution: str
    fps: int
    audio_format: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_concat_list(images: list[dict[str, Any]], output_dir: Path, seconds: float) -> Path:
    concat_path = output_dir / "images.concat.txt"
    lines: list[str] = []
    for image in images:
        filename = image.get("file")
        if not filename:
            continue
        lines.append(f"file '{(output_dir / filename).as_posix()}'")
        lines.append(f"duration {seconds}")
    if lines:
        lines.append(lines[-2].replace("file ", "file "))
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat_path


def build_audio_concat(audio_files: list[dict[str, Any]], audio_dir: Path, audio_format: str) -> Path:
    concat_path = audio_dir / "audio.concat.txt"
    lines = [f"file '{(audio_dir / f['file']).as_posix()}'" for f in audio_files if f.get("file")]
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat_path


def build_subtitles(chunks: list[dict[str, Any]], output_dir: Path, seconds: float) -> Path:
    srt_path = output_dir / "subtitles.srt"
    entries: list[str] = []
    current = 0.0

    for idx, chunk in enumerate(chunks, start=1):
        start = current
        end = current + seconds
        text = chunk.get("text", "").strip()
        if not text:
            current = end
            continue
        entries.append(str(idx))
        entries.append(f"{format_timestamp(start)} --> {format_timestamp(end)}")
        entries.append(text)
        entries.append("")
        current = end

    srt_path.write_text("\n".join(entries), encoding="utf-8")
    return srt_path


def format_timestamp(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare ffmpeg assets for video assembly",
    )
    parser.add_argument("chunked_json", help="Path to chunked poem JSON")
    parser.add_argument("images_manifest", help="Path to images manifest JSON")
    parser.add_argument("tts_manifest", help="Path to TTS manifest JSON")
    parser.add_argument(
        "--output-dir",
        default="data/video",
        help="Directory for video assembly assets",
    )
    parser.add_argument(
        "--seconds-per-image",
        type=float,
        default=4.0,
        help="Duration per image if no timing is provided",
    )
    parser.add_argument(
        "--resolution",
        default="1080x1920",
        help="Target resolution (e.g. 1080x1920)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second",
    )
    parser.add_argument(
        "--audio-format",
        default="wav",
        help="Audio format (wav, mp3)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunked = load_json(Path(args.chunked_json))
    images_manifest = load_json(Path(args.images_manifest))
    tts_manifest = load_json(Path(args.tts_manifest))

    config = VideoConfig(
        seconds_per_image=args.seconds_per_image,
        resolution=args.resolution,
        fps=args.fps,
        audio_format=args.audio_format,
    )

    images = images_manifest.get("images", [])
    audio_files = tts_manifest.get("audio_files", [])
    chunks = chunked.get("chunks", [])

    concat_list = build_concat_list(images, Path(images_manifest.get("output_dir", "data/images")), config.seconds_per_image)
    audio_concat = build_audio_concat(audio_files, Path(tts_manifest.get("output_dir", "data/audio")), config.audio_format)
    subtitles = build_subtitles(chunks, output_dir, config.seconds_per_image)

    commands = {
        "images_to_video": (
            "ffmpeg -y -f concat -safe 0 -i "
            f"{concat_list.as_posix()} -r {config.fps} -s {config.resolution} "
            "-pix_fmt yuv420p video.mp4"
        ),
        "audio_concat": (
            "ffmpeg -y -f concat -safe 0 -i "
            f"{audio_concat.as_posix()} -c copy narration.{config.audio_format}"
        ),
        "mux": (
            "ffmpeg -y -i video.mp4 -i narration."
            f"{config.audio_format} -c:v copy -c:a aac final.mp4"
        ),
        "burn_subtitles": "ffmpeg -y -i final.mp4 -vf subtitles=subtitles.srt final_subtitled.mp4",
    }

    manifest = {
        "chunked_json": Path(args.chunked_json).name,
        "images_manifest": Path(args.images_manifest).name,
        "tts_manifest": Path(args.tts_manifest).name,
        "output_dir": str(output_dir),
        "seconds_per_image": config.seconds_per_image,
        "resolution": config.resolution,
        "fps": config.fps,
        "assets": {
            "images_concat": str(concat_list),
            "audio_concat": str(audio_concat),
            "subtitles": str(subtitles),
        },
        "commands": commands,
    }

    manifest_path = output_dir / "video_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Video assembly assets prepared")
    print(f"  Output dir: {output_dir}")
    print(f"  Manifest:   {manifest_path}")
    print("  Next: Run the ffmpeg commands in the manifest to render the video")


if __name__ == "__main__":
    main()
