from __future__ import annotations

import csv
import mimetypes
import random
import smtplib
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from .config import CampaignConfig
from .templates import render_template

EMAIL_ALIASES = ("email", "email address", "e-mail", "recipient")
NAME_ALIASES = ("name", "full name", "first name", "first_name")
COMPANY_ALIASES = ("company", "organization", "organisation")
TITLE_ALIASES = ("title", "job title", "position")


@dataclass(frozen=True)
class Contact:
    email: str
    name: str
    first_name: str
    company: str
    title: str
    raw: dict[str, str]


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace("_", " ")


def _first_value(row: dict[str, str], aliases: tuple[str, ...], default: str = "") -> str:
    normalized = {
        _normalize_header(key): (value or "").strip()
        for key, value in row.items()
        if key is not None
    }
    for alias in aliases:
        value = normalized.get(alias)
        if value:
            return value
    return default


def load_contacts(path: Path) -> list[Contact]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        contacts = []
        seen_emails = set()

        for row in reader:
            email = _first_value(row, EMAIL_ALIASES)
            if not email:
                continue

            normalized_email = email.lower()
            if normalized_email in seen_emails:
                continue
            seen_emails.add(normalized_email)

            name = _first_value(row, NAME_ALIASES, "there")
            first_name = name.split()[0] if name and name != "there" else "there"
            contacts.append(
                Contact(
                    email=email,
                    name=name,
                    first_name=first_name,
                    company=_first_value(row, COMPANY_ALIASES, "your company"),
                    title=_first_value(row, TITLE_ALIASES),
                    raw={
                        key.strip(): (value or "").strip()
                        for key, value in row.items()
                        if key is not None
                    },
                )
            )

    return contacts


def read_progress(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return 0


def write_progress(path: Path, index: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(index), encoding="utf-8")


def template_values(config: CampaignConfig, contact: Contact) -> dict[str, str]:
    values = {
        "email": contact.email,
        "name": contact.name,
        "first_name": contact.first_name,
        "company": contact.company,
        "title": contact.title,
        "sender_name": config.sender_name,
        "sender_title": config.sender_title,
        "sender_phone": config.sender_phone,
        "sender_linkedin": config.sender_linkedin,
        "sender_github": config.sender_github,
        "sender_portfolio": config.sender_portfolio,
        "role": config.role,
        "value_proposition": config.value_proposition,
        "ask": config.ask,
    }
    values.update({key: value for key, value in contact.raw.items() if key not in values})
    return values


def build_message(config: CampaignConfig, contact: Contact, body_template: str) -> EmailMessage:
    values = template_values(config, contact)
    message = EmailMessage()
    message["Subject"] = render_template(config.subject_template, values)
    message["From"] = f"{config.sender_name} <{config.sender_email}>"
    message["To"] = contact.email
    message.set_content(render_template(body_template, values))

    if config.attachment_path:
        attachment_path = config.attachment_path
        content_type, _ = mimetypes.guess_type(attachment_path.name)
        maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
        message.add_attachment(
            attachment_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment_path.name,
        )

    return message


def send_campaign(config: CampaignConfig, dry_run: bool) -> int:
    if not config.contacts_csv.exists():
        raise FileNotFoundError(f"Contacts CSV not found: {config.contacts_csv}")
    if not config.body_template.exists():
        raise FileNotFoundError(f"Body template not found: {config.body_template}")
    if config.attachment_path and not config.attachment_path.exists():
        raise FileNotFoundError(f"Attachment not found: {config.attachment_path}")

    if not dry_run:
        config.validate_for_send()

    contacts = load_contacts(config.contacts_csv)
    start_index = read_progress(config.progress_file)
    body_template = config.body_template.read_text(encoding="utf-8")
    selected_contacts = contacts[start_index : start_index + config.batch_limit]

    if not selected_contacts:
        print("No contacts left to process.")
        return 0

    sent_count = 0
    smtp = None
    try:
        if not dry_run:
            smtp = smtplib.SMTP(config.smtp_host, config.smtp_port)
            smtp.starttls()
            smtp.login(config.smtp_username, config.smtp_password)

        for offset, contact in enumerate(selected_contacts):
            current_index = start_index + offset
            message = build_message(config, contact, body_template)

            if dry_run:
                print(f"\n--- DRY RUN [{current_index + 1}/{len(contacts)}] {contact.email} ---")
                print(f"Subject: {message['Subject']}")
                print(message.get_content())
            else:
                smtp.send_message(message)
                write_progress(config.progress_file, current_index + 1)
                sent_count += 1
                print(f"[{current_index + 1}/{len(contacts)}] Sent to {contact.email}")

                if offset < len(selected_contacts) - 1:
                    delay = random.randint(config.min_delay_seconds, config.max_delay_seconds)
                    time.sleep(delay)
    finally:
        if smtp:
            smtp.quit()

    if dry_run:
        print(f"\nDry run complete. Previewed {len(selected_contacts)} message(s).")
        return len(selected_contacts)

    print(f"\nCampaign run complete. Sent {sent_count} message(s).")
    return sent_count
