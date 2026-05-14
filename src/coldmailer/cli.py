from __future__ import annotations

import argparse
from pathlib import Path

from .campaign import send_campaign
from .config import CampaignConfig, load_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send personalized cold emails from a CSV file.")
    parser.add_argument("--env", default=".env", help="Path to an env file. Defaults to .env.")
    parser.add_argument("--contacts", help="Path to contacts CSV.")
    parser.add_argument("--template", help="Path to body template.")
    parser.add_argument("--subject", help="Subject template.")
    parser.add_argument("--attachment", help="Optional attachment path.")
    parser.add_argument("--batch-limit", type=int, help="Maximum contacts to process in one run.")
    parser.add_argument("--send", action="store_true", help="Actually send emails. Omit for dry run.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    load_env_file(Path(args.env))
    config = CampaignConfig.from_env()

    if args.contacts:
        config = config.with_updates(contacts_csv=Path(args.contacts))
    if args.template:
        config = config.with_updates(body_template=Path(args.template))
    if args.subject:
        config = config.with_updates(subject_template=args.subject)
    if args.attachment:
        config = config.with_updates(attachment_path=Path(args.attachment))
    if args.batch_limit:
        config = config.with_updates(batch_limit=args.batch_limit)

    try:
        send_campaign(config, dry_run=not args.send)
    except Exception as exc:
        parser.exit(1, f"Error: {exc}\n")

    return 0
