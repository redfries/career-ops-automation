"""
scripts/send_resend_email.py
Automated Application & Recruiter Outreach Mailer via Resend API
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path
import resend

# Load .env file automatically
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    print("[!] ERROR: RESEND_API_KEY not found in environment or .env file.")
    sys.exit(1)

resend.api_key = RESEND_API_KEY


def build_email_html(candidate_name, role_title, company_name, pitch_text, links=None):
    """Formats a clean, natural, human email (no AI badges, no marketing cards)."""
    portfolio_link = links.get("portfolio", "https://infinitys.me") if links else "https://infinitys.me"
    linkedin_link = links.get("linkedin", "https://www.linkedin.com/in/redfries/") if links else "https://www.linkedin.com/in/redfries/"
    github_link = links.get("github", "https://github.com/redfries") if links else "https://github.com/redfries"

    # Human-like, clean, neat email layout without cards or borders
    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #1a1a1a; line-height: 1.6; max-width: 600px;">
  <p>Hi {company_name} Team,</p>

  <p>I noticed the {role_title} role at {company_name} and wanted to reach out directly to introduce myself.</p>

  <p>{pitch_text}</p>

  <p>I have attached my resume for your review. You can also explore my research projects and code on my portfolio: <a href="{portfolio_link}" style="color: #0b57d0; text-decoration: underline;">{portfolio_link}</a>.</p>

  <p>I am based in Dhahran with a transferable Iqama and available immediately. I would welcome the opportunity to discuss how my background aligns with your engineering goals.</p>

  <p style="margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 16px;">
    Best regards,<br>
    <strong style="color: #0f172a;">{candidate_name}</strong><br>
    <span style="color: #475569; font-size: 14px;">AI &amp; Automation Engineer</span><br>
    <span style="color: #64748b; font-size: 13px;">Dhahran, Saudi Arabia &bull; +966 50 269 8140</span><br>
    <span style="font-size: 13px; margin-top: 6px; display: inline-block;">
      <a href="{portfolio_link}" style="color: #0b57d0; text-decoration: none;">Portfolio</a> &bull; 
      <a href="{linkedin_link}" style="color: #0b57d0; text-decoration: none;">LinkedIn</a> &bull; 
      <a href="{github_link}" style="color: #0b57d0; text-decoration: none;">GitHub</a>
    </span>
  </p>
</div>"""
    return html


def send_email(to_email, subject, body_html, sender=None, resume_pdf_path=None):
    """Sends an email via Resend API with optional PDF resume attachment."""
    # Default sender: onboarding@resend.dev (or verified custom domain)
    if not sender:
        sender = os.getenv("RESEND_SENDER", "Shabaaz Hussain Shaik <onboarding@resend.dev>")

    attachments = []
    if resume_pdf_path and os.path.exists(resume_pdf_path):
        print(f"[*] Attaching resume from: {resume_pdf_path}")
        with open(resume_pdf_path, "rb") as f:
            pdf_bytes = list(f.read())
        
        attachments.append({
            "filename": os.path.basename(resume_pdf_path),
            "content": pdf_bytes
        })

    # Route all replies directly to your real Outlook or Gmail inbox
    reply_to = os.getenv("REPLY_TO_EMAIL", "theshabaaz@outlook.com")

    params = {
        "from": sender,
        "to": [to_email] if isinstance(to_email, str) else to_email,
        "reply_to": reply_to,
        "subject": subject,
        "html": body_html,
    }
    if attachments:
        params["attachments"] = attachments

    print(f"[*] Sending email via Resend API to: {to_email}...")
    try:
        response = resend.Emails.send(params)
        email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
        print(f"[SUCCESS] Email successfully dispatched! Resend ID: {email_id}")
        return response
    except Exception as e:
        print(f"[!] Resend delivery failed: {e}")
        raise


def send_from_application_bundle(bundle_dir, to_email=None, sender=None, force=False):
    """Loads application_package.json and sends tailored application email."""
    bundle_path = Path(bundle_dir)
    pkg_file = bundle_path / "application_package.json"
    job_file = bundle_path / "job_details.json"
    receipt_file = bundle_path / "email_sent_receipt.json"

    if not pkg_file.exists():
        raise FileNotFoundError(f"Missing application_package.json in {bundle_dir}")

    # Deduplication Guard: Prevent accidental duplicate emails to the same recruiter
    if receipt_file.exists() and not force:
        with open(receipt_file, "r", encoding="utf-8") as rf:
            prev_receipt = json.load(rf)
        print(f"[!] SAFETY GUARD: An email was already sent from this bundle to {prev_receipt.get('to')} on {prev_receipt.get('sent_at')}!")
        print("[!] To send anyway, pass the --force flag.")
        return None

    with open(pkg_file, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    job_title = "AI / ML Engineer"
    company_name = "Hiring Team"
    if job_file.exists():
        with open(job_file, "r", encoding="utf-8") as f:
            job = json.load(f)
            job_title = job.get("title", job_title)
            company_name = job.get("company", company_name)

    candidate = pkg.get("candidate", {})
    candidate_name = candidate.get("full_name", "Shabaaz Hussain Shaik")
    links = candidate.get("links", {})
    
    pitch = pkg.get("pitch_answers", {}).get("cover_letter_snippet")
    if not pitch:
        pitch = "I am excited to submit my application for this role. My technical background in applied machine learning, computer vision, and automation makes me a strong fit."

    subject = f"Application: {job_title} - {candidate_name}"
    html = build_email_html(candidate_name, job_title, company_name, pitch, links)
    
    resume_pdf = pkg.get("resume_path")
    if not resume_pdf or not os.path.exists(resume_pdf):
        local_pdf = bundle_path / "resume.pdf"
        if local_pdf.exists():
            resume_pdf = str(local_pdf)

    # Default recipient for testing if none provided
    target_to = to_email if to_email else "studioinfinitys@gmail.com"
    response = send_email(target_to, subject, html, sender=sender, resume_pdf_path=resume_pdf)
    email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)

    # Save receipt to prevent duplicate sending
    with open(receipt_file, "w", encoding="utf-8") as rf:
        json.dump({
            "sent_at": datetime.datetime.now().isoformat(),
            "to": target_to,
            "sender": sender or os.getenv("RESEND_SENDER", "Shabaaz Hussain Shaik <shabaaz@infinitys.me>"),
            "subject": subject,
            "resend_id": email_id
        }, rf, indent=2)

    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send automated emails using Resend API")
    parser.add_argument("--test", action="store_true", help="Send a test verification email")
    parser.add_argument("--app-dir", type=str, help="Path to tailored application bundle folder")
    parser.add_argument("--to", type=str, default="studioinfinitys@gmail.com", help="Recipient email address")
    parser.add_argument("--sender", type=str, help="Custom from address (e.g. shabaaz@infinitys.me)")
    parser.add_argument("--force", action="store_true", help="Force resend even if bundle was already sent")

    args = parser.parse_args()

    if args.test:
        test_pdf = Path("applications/2026-09-17_innovationteam_4464989568/resume.pdf")
        pdf_path = str(test_pdf) if test_pdf.exists() else None
        html = build_email_html(
            "Shabaaz Hussain Shaik",
            "Junior AI Engineer",
            "InnovationTeam",
            "As an AI Engineer completing my Master's in AI at KFUPM with verified industry experience in Python automation, I bring direct hands-on expertise in applied deep learning and computer vision."
        )
        send_email(args.to, "Application: Junior AI Engineer - Shabaaz Hussain Shaik", html, sender=args.sender, resume_pdf_path=pdf_path)
    elif args.app_dir:
        send_from_application_bundle(args.app_dir, to_email=args.to, sender=args.sender, force=args.force)
    else:
        parser.print_help()
