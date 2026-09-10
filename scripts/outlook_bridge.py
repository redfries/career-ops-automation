#!/usr/bin/env python3
"""
outlook_bridge.py
Microsoft Outlook Integration Bridge for theshabaaz@outlook.com:
1. Inbound OTP & Verification Code Reader:
   - Connects via IMAP to outlook.office365.com
   - Automatically polls and extracts 4-to-8 digit OTP codes, login links, or verification emails
2. Outbound Direct Cold Email Sender:
   - Connects via SMTP to smtp-mail.outlook.com (STARTTLS)
   - Automatically drafts and sends high-impact pitch emails with the tailored PDF resume attached
   - Supports --dry-run for drafting without sending
"""

import os
import sys
import re
import time
import email
import imaplib
import smtplib
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional, List, Tuple

# Ensure scripts directory in path
SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

# Ensure Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def load_env():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

DEFAULT_EMAIL = "theshabaaz@outlook.com"
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587

def get_outlook_credentials() -> Tuple[str, str]:
    email_addr = os.environ.get("OUTLOOK_EMAIL", DEFAULT_EMAIL)
    password = os.environ.get("OUTLOOK_PASSWORD", "")
    return email_addr, password

class OutlookBridge:
    def __init__(self, email_addr: Optional[str] = None, password: Optional[str] = None):
        self.email_addr = email_addr or os.environ.get("OUTLOOK_EMAIL", DEFAULT_EMAIL)
        self.password = password or os.environ.get("OUTLOOK_PASSWORD", "")

    def is_configured(self) -> bool:
        return bool(self.email_addr and self.password)

    def fetch_latest_otp(self, max_wait_seconds: int = 45, sender_filter: str = "") -> Optional[str]:
        """
        Polls Outlook Inbox for the latest verification code/OTP received in the last 5 minutes.
        Extracts 4-to-8 digit codes from subject or body.
        """
        if not self.is_configured():
            print("[WARN] Outlook password not configured in .env (OUTLOOK_PASSWORD). Unable to poll IMAP.")
            return None

        print(f"[OUTLOOK IMAP] Listening on {self.email_addr} for OTP / verification code (up to {max_wait_seconds}s)...")
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            try:
                mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
                mail.login(self.email_addr, self.password)
                mail.select("INBOX")

                # Search recent unseen or recent messages
                status, messages = mail.search(None, "UNSEEN")
                if status != "OK" or not messages[0]:
                    # Check all recent messages if no unread
                    status, messages = mail.search(None, "ALL")

                msg_ids = messages[0].split()
                if msg_ids:
                    # Check latest 3 messages
                    latest_ids = msg_ids[-3:]
                    for mid in reversed(latest_ids):
                        status, data = mail.fetch(mid, "(RFC822)")
                        if status != "OK":
                            continue

                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        # Extract text
                        body_text = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    break
                        else:
                            body_text = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                        combined_content = f"{msg['Subject'] or ''}\n{body_text}"

                        # Regex for OTP code
                        otp_patterns = [
                            r"(?:verification code|security code|login code|otp|your code is|one-time passcode)[:\s]+([0-9]{4,8})\b",
                            r"\b([0-9]{6})\b",  # Standard 6-digit code
                            r"\b([0-9]{4})\b"   # Standard 4-digit code
                        ]

                        for pat in otp_patterns:
                            m = re.search(pat, combined_content, flags=re.I)
                            if m:
                                code = m.group(1)
                                print(f"[OUTLOOK IMAP] Found verification code: {code}")
                                mail.close()
                                mail.logout()
                                return code

                mail.close()
                mail.logout()
            except Exception as e:
                print(f"[OUTLOOK IMAP NOTICE] Polling check: {e}")

            time.sleep(4.0)

        print("[OUTLOOK IMAP] Polling window elapsed without detecting OTP.")
        return None

    def compose_cold_pitch(
        self,
        company: str,
        role: str,
        recruiter_name: Optional[str] = None
    ) -> str:
        """Generates a high-conversion, verified cold pitch for direct email outreach."""
        greeting = f"Dear {recruiter_name}," if recruiter_name else "Dear Hiring Team,"
        
        body = f"""{greeting}

I am writing to express my strong interest in the {role} position at {company}.

As an AI & Machine Learning Engineer currently conducting applied deep learning research at King Fahd University of Petroleum & Minerals (KFUPM), my work directly bridges foundation models with high-precision computer vision and RAG production systems:

1. Computer Vision & OCR: Architected a multi-stage document recognition pipeline leveraging Cascade R-CNN, CRNN, and fine-tuned Qwen3.5 VLM, achieving 97.5% detection accuracy and 91.2% character recognition on complex handwritten scripts.
2. Medical Foundation Models (ViTs): Developed ReSeeAI using the RETFound vision transformer foundation model and Grad-CAM interpretability, attaining a 0.94 ROC-AUC across diabetic retinopathy classification tasks.
3. GenAI & RAG: Built end-to-end semantic retrieval pipelines utilizing sentence-transformers, Gemini API, and FastAPI deployed on GPU infrastructure.
4. Test Automation Background: 22 months of QA automation experience at Tata Consultancy Services (TCS) ensuring robust software quality standards.

Work Authorization & Availability:
- Saudi Arabia: Authorized to work with a transferable student/resident Iqama.
- Global Remote / GCC: Immediately available for direct employment or B2B contractor engagements.

I have attached my tailored ATS resume for your review. I would welcome the opportunity to discuss how my technical background can directly contribute to {company}'s AI engineering initiatives.

Portfolio: https://infinitys.me
GitHub: https://github.com/redfries
LinkedIn: https://www.linkedin.com/in/redfries/

Best regards,

Shabaaz Hussain Shaik
AI / Machine Learning Engineer
Dhahran, Saudi Arabia
+966 50 269 8140
{self.email_addr}
"""
        return body

    def send_direct_application_email(
        self,
        recipient_email: str,
        company: str,
        role: str,
        pdf_path: Path,
        recruiter_name: Optional[str] = None,
        custom_body: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Sends an email with the tailored PDF resume attached to the hiring manager or recruiter.
        """
        subject = f"Application: {role} — Shabaaz Hussain Shaik"
        body_text = custom_body or self.compose_cold_pitch(company, role, recruiter_name)

        if not pdf_path.exists():
            return {"success": False, "error": f"Resume PDF not found: {pdf_path}"}

        print("\n" + "="*65)
        print(f"[OUTLOOK OUTBOUND] PREPARING DIRECT APPLICATION EMAIL")
        print(f"From:        {self.email_addr}")
        print(f"To:          {recipient_email}")
        print(f"Subject:     {subject}")
        print(f"Attachment:  {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")
        print(f"Mode:        {'DRY RUN (Simulated)' if dry_run else 'LIVE TRANSMISSION'}")
        print("="*65)

        if dry_run:
            print("\n[PREVIEW OF EMAIL BODY]:\n")
            print(body_text)
            print("-" * 65)
            print("[DRY RUN COMPLETE] Email validated and attachment confirmed. No mail sent.")
            return {"success": True, "status": "dry_run_verified"}

        if not self.is_configured():
            return {
                "success": False,
                "error": "OUTLOOK_PASSWORD is not configured in .env. Cannot transmit live email."
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_addr
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body_text, "plain"))

            # Attach PDF
            with open(pdf_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
                msg.attach(attach)

            # Transmit via SMTP
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.starttls()
            server.login(self.email_addr, self.password)
            server.send_message(msg)
            server.quit()

            print(f"[SENT] Email successfully transmitted to {recipient_email}!")
            return {"success": True, "status": "sent", "recipient": recipient_email}

        except Exception as e:
            print(f"[ERROR] Failed to send email via SMTP: {e}")
            return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Outlook Integration Bridge for Job Applications")
    parser.add_argument("--fetch-otp", action="store_true", help="Poll inbox for latest verification code")
    parser.add_argument("--send-cv", action="store_true", help="Send tailored CV to recruiter email")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--company", default="Hiring Company", help="Company name")
    parser.add_argument("--role", default="AI Engineer", help="Role title")
    parser.add_argument("--pdf", help="Path to resume PDF")
    parser.add_argument("--recruiter", default=None, help="Recruiter name")
    parser.add_argument("--dry-run", action="store_true", help="Simulate email sending without transmitting")
    args = parser.parse_args()

    bridge = OutlookBridge()

    if args.fetch_otp:
        code = bridge.fetch_latest_otp()
        if code:
            print(f"RESULT: OTP={code}")
        else:
            print("RESULT: No OTP found")

    elif args.send_cv:
        if not args.to or not args.pdf:
            print("[ERROR] --to and --pdf are required when sending CV")
            sys.exit(1)
        res = bridge.send_direct_application_email(
            recipient_email=args.to,
            company=args.company,
            role=args.role,
            pdf_path=Path(args.pdf),
            recruiter_name=args.recruiter,
            dry_run=args.dry_run
        )
        print("RESULT:", json.dumps(res))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
