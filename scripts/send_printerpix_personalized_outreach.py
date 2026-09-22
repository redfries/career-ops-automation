"""
scripts/send_printerpix_personalized_outreach.py
Personalized Recruiter & Team Outreach for Printerpix Associate AI Engineer Role
"""

import os
import sys
import json
import shutil
import datetime
from pathlib import Path
import resend

# 1. Load .env
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
SENDER = os.getenv("RESEND_SENDER", "Shabaaz Hussain Shaik <shabaaz@infinitys.me>")
REPLY_TO = os.getenv("REPLY_TO_EMAIL", "theshabaaz@outlook.com")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RESUME_PDF = WORKSPACE_ROOT / "my-resume" / "resume.pdf"
APP_DIR = WORKSPACE_ROOT / "applications" / "2026-09-17_printerpix_associate_ai_engineer"
APP_DIR.mkdir(parents=True, exist_ok=True)

# Copy resume to app bundle for archival
dest_pdf = APP_DIR / "resume.pdf"
if RESUME_PDF.exists() and not dest_pdf.exists():
    shutil.copy2(RESUME_PDF, dest_pdf)


def build_html(salutation, body_paragraphs):
    body_html = "".join(f"<p>{p}</p>" for p in body_paragraphs)
    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; color: #1a1a1a; line-height: 1.6; max-width: 620px;">
  <p>{salutation},</p>
  {body_html}
  <p style="margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 16px;">
    Best regards,<br>
    <strong style="color: #0f172a;">Shabaaz Hussain Shaik</strong><br>
    <span style="color: #475569; font-size: 14px;">AI &amp; Machine Learning Engineer</span><br>
    <span style="color: #64748b; font-size: 13px;">Phone: +966 50 269 8140</span><br>
    <span style="font-size: 13px; margin-top: 6px; display: inline-block;">
      <a href="https://infinitys.me" style="color: #0b57d0; text-decoration: none;">Portfolio: infinitys.me</a> &bull; 
      <a href="https://www.linkedin.com/in/redfries/" style="color: #0b57d0; text-decoration: none;">LinkedIn</a> &bull; 
      <a href="https://github.com/redfries" style="color: #0b57d0; text-decoration: none;">GitHub</a>
    </span>
  </p>
</div>"""
    return html


# Targets configuration
OUTREACH_TARGETS = [
    {
        "name": "John Poole",
        "role": "Talent Acquisition & HR Lead",
        "to": ["john.poole@printerpix.com", "j.poole@syncoms.co.uk"],
        "subject": "Application: Associate AI Engineer (Dubai) - Shabaaz Hussain Shaik",
        "salutation": "Hi John",
        "paragraphs": [
            "I recently submitted my application for the <strong>Associate AI Engineer</strong> position in Dubai and wanted to introduce myself directly.",
            "I am completing my Master's in AI at KFUPM, where I design end-to-end applied deep learning and vision systems, backed by 22 months of commercial software automation experience at TCS. My recent hands-on focus centers on building <strong>Agentic AI workflows (LangGraph, CrewAI)</strong>, LLM API integrations (Claude/OpenAI), and Model Context Protocol (MCP) implementations.",
            "I noticed Printerpix's high-velocity mission to build autonomous marketing intelligence and dynamic personalization workflows. I thrive in hands-on building environments where rapid MVP prototyping meets production rigor.",
            "I am readily available for the Dubai role. I have attached my 2-page resume for your review, and you can also explore my code and projects on my portfolio: <a href='https://infinitys.me' style='color: #0b57d0;'>infinitys.me</a>.",
            "Thank you for your time and consideration. I would welcome the opportunity to discuss how I can hit the ground running with the team."
        ]
    },
    {
        "name": "Ali Ridha Jaffar",
        "role": "EVP - Growth & Digital Marketing",
        "to": ["ali.jaffar@printerpix.com", "a.jaffar@syncoms.co.uk"],
        "subject": "Associate AI Engineer application & Marketing AI Workflows - Shabaaz Hussain Shaik",
        "salutation": "Hi Ali",
        "paragraphs": [
            "I saw that Printerpix is aggressively scaling its AI engineering footprint in Dubai to transform digital marketing and personalized customer engagement into autonomous agentic workflows.",
            "I recently applied for the <strong>Associate AI Engineer</strong> position on your team. My background combines an AI Master's from KFUPM with real-world engineering experience: developing multi-agent systems, integrating LLM APIs for dynamic content generation, and implementing semantic retrieval with vector databases.",
            "Seeing Printerpix adopt cutting-edge architectures like <strong>Model Context Protocol (MCP)</strong> and <strong>LangGraph</strong> to drive hyper-personalized D2C marketing is genuinely exciting—it's exactly where I focus my work.",
            "I have attached my resume and would love to share how I can help accelerate your marketing intelligence pipelines. My portfolio and code are also available at <a href='https://infinitys.me' style='color: #0b57d0;'>infinitys.me</a>.",
            "I would be glad to connect whenever your schedule allows."
        ]
    },
    {
        "name": "Samad Sayed",
        "role": "AI Engineer (Dubai)",
        "to": ["samad.sayed@printerpix.com"],
        "subject": "Associate AI Engineer application / Connecting on AI Agents at Printerpix - Shabaaz",
        "salutation": "Hi Samad",
        "paragraphs": [
            "I came across your work building LLM-powered agents and AI automation systems at Printerpix in Dubai, and wanted to reach out.",
            "I just applied for the <strong>Associate AI Engineer</strong> opening on the team. I'm finishing my Master's in AI at KFUPM, focusing on agentic orchestration (LangGraph/CrewAI), prompt engineering with tool execution, and vector-backed RAG systems.",
            "It's really refreshing to see Printerpix pushing production-grade Agentic AI and MCP in e-commerce rather than just generic analytics.",
            "I've attached my resume and would love to connect with you, hear about your experience on the team, and share some of the agent pipelines I've been building (portfolio: <a href='https://infinitys.me' style='color: #0b57d0;'>infinitys.me</a>).",
            "Hope to connect!"
        ]
    },
    {
        "name": "Ahmed Khan",
        "role": "AI & Software Delivery Engineer (Dubai)",
        "to": ["ahmed.khan@printerpix.com"],
        "subject": "Associate AI Engineer application / Agentic Workflows at Printerpix - Shabaaz",
        "salutation": "Hi Ahmed",
        "paragraphs": [
            "I noticed your focus on agentic workflows, Claude Code, and RAG systems at Printerpix Dubai, and wanted to send a quick hello.",
            "I recently applied for the <strong>Associate AI Engineer</strong> role. My technical background is in applied AI (Master's at KFUPM) and software automation (TCS), with current work focused on LLM tool use, LangGraph orchestration, and Model Context Protocol (MCP) workflows.",
            "I'd love to connect with fellow engineers building real-world AI pipelines at Printerpix. I’ve attached my resume, and my portfolio/repos are up at <a href='https://infinitys.me' style='color: #0b57d0;'>infinitys.me</a>.",
            "Looking forward to connecting!"
        ]
    }
]


def run_outreach():
    print(f"[*] Starting personalized outreach dispatch for Printerpix...")
    print(f"[*] Sender: {SENDER}")
    print(f"[*] Reply-To: {REPLY_TO}")
    print(f"[*] Attached Resume: {RESUME_PDF} (exists: {RESUME_PDF.exists()})")

    with open(RESUME_PDF, "rb") as f:
        pdf_bytes = list(f.read())
    
    attachments = [{
        "filename": "Shabaaz_Hussain_Shaik_Resume.pdf",
        "content": pdf_bytes
    }]

    receipts = []

    for target in OUTREACH_TARGETS:
        name = target["name"]
        recipients = target["to"]
        subject = target["subject"]
        html = build_html(target["salutation"], target["paragraphs"])

        print(f"\n---> Dispatching to {name} ({recipients})...")
        try:
            params = {
                "from": SENDER,
                "to": recipients,
                "reply_to": REPLY_TO,
                "subject": subject,
                "html": html,
                "attachments": attachments
            }
            res = resend.Emails.send(params)
            email_id = res.get("id") if isinstance(res, dict) else getattr(res, "id", None)
            print(f"[SUCCESS] Dispatched to {name}! Resend ID: {email_id}")

            receipt = {
                "recipient_name": name,
                "recipient_role": target["role"],
                "to": recipients,
                "subject": subject,
                "sent_at": datetime.datetime.now().isoformat(),
                "resend_id": email_id,
                "dashboard_url": f"https://resend.com/emails/{email_id}",
                "status": "DELIVERED"
            }
            receipts.append(receipt)

        except Exception as e:
            print(f"[ERROR] Failed to send to {name}: {e}")
            receipts.append({
                "recipient_name": name,
                "to": recipients,
                "error": str(e),
                "status": "FAILED"
            })

    receipt_file = APP_DIR / "email_sent_receipts.json"
    with open(receipt_file, "w", encoding="utf-8") as f:
        json.dump(receipts, f, indent=2)

    print(f"\n[DONE] All outreach attempts completed. Receipt saved to {receipt_file}")


if __name__ == "__main__":
    run_outreach()
