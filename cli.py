from __future__ import annotations

import argparse
import logging

from config.loader import load_config
from pipelines.poem_to_video import run_poem_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Poem Bot CLI")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("command", choices=["run-once", "run-scheduled"], default="run-once")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(args.config)

    if args.command == "run-once":
        run_poem_pipeline(config, dry_run=args.dry_run)
    else:
        logging.info("Scheduler stub. Verwende n8n für Cron-Trigger.")


if __name__ == "__main__":
    main()
