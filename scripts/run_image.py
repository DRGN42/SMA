#!/usr/bin/env python3
"""Generate images per chunk using a ComfyUI HTTP endpoint (Flux workflow)."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_ENDPOINT = "http://localhost:8188"


@dataclass(frozen=True)
class ImageConfig:
    endpoint: str
    workflow_path: Path
    output_dir: Path
    prompt_node_id: str
    negative_node_id: str


def load_workflow(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def set_prompt(workflow: dict[str, Any], node_id: str, text: str) -> None:
    node = workflow.get(node_id)
    if not isinstance(node, dict):
        raise KeyError(f"Node {node_id} not found in workflow")
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        raise KeyError(f"Node {node_id} missing inputs")
    inputs["text"] = text


def queue_prompt(workflow: dict[str, Any], endpoint: str) -> dict[str, Any]:
    response = requests.post(
        f"{endpoint}/prompt",
        json={"prompt": workflow},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def fetch_history(prompt_id: str, endpoint: str) -> dict[str, Any]:
    response = requests.get(f"{endpoint}/history/{prompt_id}", timeout=120)
    response.raise_for_status()
    return response.json()


def find_latest_image(history: dict[str, Any]) -> dict[str, Any] | None:
    outputs = history.get("outputs", {})
    for _, output in outputs.items():
        images = output.get("images", [])
        if images:
            return images[-1]
    return None


def download_image(endpoint: str, image_meta: dict[str, Any]) -> bytes:
    params = {
        "filename": image_meta.get("filename"),
        "subfolder": image_meta.get("subfolder", ""),
        "type": image_meta.get("type", "output"),
    }
    response = requests.get(f"{endpoint}/view", params=params, timeout=120)
    response.raise_for_status()
    return response.content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images for poem chunks using ComfyUI",
    )
    parser.add_argument("parsed_prompts", help="Path to LLM parsed prompts JSON")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("COMFY_ENDPOINT", DEFAULT_ENDPOINT),
        help="ComfyUI HTTP endpoint",
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Path to ComfyUI workflow JSON",
    )
    parser.add_argument(
        "--output-dir",
        default="data/images",
        help="Directory for generated images",
    )
    parser.add_argument(
        "--prompt-node-id",
        default=os.environ.get("COMFY_PROMPT_NODE", "6"),
        help="Node ID for positive prompt text",
    )
    parser.add_argument(
        "--negative-node-id",
        default=os.environ.get("COMFY_NEGATIVE_NODE", "7"),
        help="Node ID for negative prompt text",
    )
    parser.add_argument(
        "--output",
        help="Optional manifest JSON path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.parsed_prompts)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompts = json.loads(input_path.read_text(encoding="utf-8"))
    chunk_prompts = prompts.get("chunk_prompts", [])

    config = ImageConfig(
        endpoint=args.endpoint,
        workflow_path=Path(args.workflow),
        output_dir=output_dir,
        prompt_node_id=args.prompt_node_id,
        negative_node_id=args.negative_node_id,
    )

    base_workflow = load_workflow(config.workflow_path)
    manifest_images: list[dict[str, Any]] = []
    stem = input_path.stem

    for chunk in chunk_prompts:
        index = chunk.get("index")
        positive = chunk.get("prompt", "")
        negative = chunk.get("negative_prompt", "")
        if not positive:
            continue

        workflow = json.loads(json.dumps(base_workflow))
        set_prompt(workflow, config.prompt_node_id, positive)
        set_prompt(workflow, config.negative_node_id, negative)

        queued = queue_prompt(workflow, config.endpoint)
        prompt_id = queued.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return prompt_id")

        history = fetch_history(prompt_id, config.endpoint)
        entry = history.get(prompt_id, {})
        image_meta = find_latest_image(entry) if entry else None
        if not image_meta:
            raise RuntimeError(f"No image found for prompt {prompt_id}")

        image_bytes = download_image(config.endpoint, image_meta)
        filename = f"{stem}__chunk{int(index):03d}.png"
        image_path = output_dir / filename
        image_path.write_bytes(image_bytes)

        manifest_images.append(
            {
                "index": index,
                "prompt": positive,
                "negative_prompt": negative,
                "file": image_path.name,
                "prompt_id": prompt_id,
            }
        )

    manifest = {
        "source_json": input_path.name,
        "output_dir": str(output_dir),
        "workflow": str(config.workflow_path),
        "prompt_node_id": config.prompt_node_id,
        "negative_node_id": config.negative_node_id,
        "images": manifest_images,
    }
    output_path = Path(args.output) if args.output else output_dir / f"{stem}.images.json"
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Images generated")
    print(f"  Input JSON:  {input_path}")
    print(f"  Output dir:  {output_dir}")
    print(f"  Manifest:    {output_path}")
    print(f"  Files:       {len(manifest_images)}")


if __name__ == "__main__":
    main()
