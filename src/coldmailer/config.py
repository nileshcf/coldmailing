from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


@dataclass(frozen=True)
class CampaignConfig:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    sender_name: str
    contacts_csv: Path
    subject_template: str
    body_template: Path
    attachment_path: Path | None
    progress_file: Path
    batch_limit: int
    min_delay_seconds: int
    max_delay_seconds: int
    sender_title: str
    sender_phone: str
    sender_linkedin: str
    sender_github: str
    sender_portfolio: str
    role: str
    value_proposition: str
    ask: str

    @classmethod
    def from_env(cls) -> "CampaignConfig":
        attachment = os.getenv("ATTACHMENT_PATH", "").strip()
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=env_int("SMTP_PORT", 587),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            sender_email=os.getenv("SENDER_EMAIL", "your.email@example.com"),
            sender_name=os.getenv("SENDER_NAME", "Your Name"),
            contacts_csv=Path(os.getenv("CONTACTS_CSV", "examples/contacts.csv")),
            subject_template=os.getenv("SUBJECT_TEMPLATE", "Intro for {company}"),
            body_template=Path(os.getenv("BODY_TEMPLATE", "templates/default.txt")),
            attachment_path=Path(attachment) if attachment else None,
            progress_file=Path(os.getenv("PROGRESS_FILE", "progress/campaign_progress.txt")),
            batch_limit=env_int("BATCH_LIMIT", 25),
            min_delay_seconds=env_int("MIN_DELAY_SECONDS", 30),
            max_delay_seconds=env_int("MAX_DELAY_SECONDS", 90),
            sender_title=os.getenv("SENDER_TITLE", "Your Role"),
            sender_phone=os.getenv("SENDER_PHONE", ""),
            sender_linkedin=os.getenv("SENDER_LINKEDIN", ""),
            sender_github=os.getenv("SENDER_GITHUB", ""),
            sender_portfolio=os.getenv("SENDER_PORTFOLIO", ""),
            role=os.getenv("ROLE", "a relevant role"),
            value_proposition=os.getenv(
                "VALUE_PROPOSITION",
                "I bring practical experience and can contribute quickly to engineering teams.",
            ),
            ask=os.getenv("ASK", "Would you be open to a short conversation?"),
        )

    def with_updates(self, **updates: object) -> "CampaignConfig":
        return replace(self, **updates)

    def validate_for_send(self) -> None:
        missing = [
            name
            for name, value in {
                "SMTP_USERNAME": self.smtp_username,
                "SMTP_PASSWORD": self.smtp_password,
                "SENDER_EMAIL": self.sender_email,
                "SENDER_NAME": self.sender_name,
            }.items()
            if not value or value in {"your.email@example.com", "your-app-password", "Your Name"}
        ]
        if missing:
            raise ValueError(f"Missing required send configuration: {', '.join(missing)}")
