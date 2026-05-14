# Cold Mailer

A small Python CLI for sending personalized cold emails from a CSV contact list.

The repository is intentionally generic: no private contacts, resumes, sender emails, or app passwords are committed. Configure your own campaign locally with `.env`.

## Features

- CSV-based campaign input
- Plain-text email templates with placeholders
- Dry-run mode by default
- Optional attachment support
- Batch limits, randomized delays, and progress tracking
- Flexible CSV column names such as `Email`, `Email address`, `Name`, `First name`, `Company`, and `Organization`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your SMTP details and sender profile.

## Contact CSV

Use `examples/contacts.csv` as the simplest format reference:

```csv
email,name,company,title
alex@example.com,Alex Morgan,Example Co,Recruiter
```

Private CSVs should stay in `data/`, `contacts/`, or another ignored folder.

Additional sample files in `examples/` mirror common export formats:

- `hr_contacts.csv`
- `generic_hr_india_emails.csv`
- `final_hr_emails_campaign.csv`
- `bulk-sample-2150391.csv`

## Templates

Edit `templates/default.txt`. Template placeholders can use:

- Contact fields: `{email}`, `{name}`, `{first_name}`, `{company}`, `{title}`
- Sender fields: `{sender_name}`, `{sender_title}`, `{sender_phone}`, `{sender_linkedin}`, `{sender_github}`, `{sender_portfolio}`
- Campaign fields: `{role}`, `{value_proposition}`, `{ask}`

## Dry Run

Dry-run mode prints the messages without sending:

```powershell
python main.py --contacts examples/contacts.csv
```

## Send

After checking the dry run:

```powershell
python main.py --send --contacts data/my_contacts.csv --attachment resumes/resume.pdf
```

The CLI records successful sends in `progress/campaign_progress.txt` and resumes from that index next time.

## Safety Notes

- Never commit `.env`, real contact lists, resumes, or progress files.
- Use provider-approved SMTP credentials such as Gmail app passwords.
- Respect local email laws and platform policies. Include honest sender details and a simple opt-out line.
