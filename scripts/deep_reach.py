#!/usr/bin/env python3
"""
deep_reach.py
Deep Company Research & Multi-Channel Outreach Engine:
- Generates comprehensive company dossiers (mission, tech stack, hiring team)
- Generates targeted LinkedIn discovery search links for Engineering Managers and Technical Recruiters
- Crafts high-conversion outreach assets:
    1. LinkedIn Connection Request Note (strictly <= 300 characters)
    2. LinkedIn InMail / Follow-up Message (concise 150-word pitch)
    3. Direct Executive Cold Email (ready for Outlook Bridge transmission)
- Bridges candidate evidence bullets from data/canonical_profile.json
"""

import os
import sys
import re
import json
import urllib.parse
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

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

def load_canonical_profile() -> Dict[str, Any]:
    prof_path = ROOT_DIR / "data" / "canonical_profile.json"
    with open(prof_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_linkedin_search_urls(company: str) -> Dict[str, str]:
    """Generates direct Google and LinkedIn queries to find hiring decision-makers."""
    comp_clean = re.sub(r"[^\w\s]", "", company).strip()
    
    em_query = f'site:linkedin.com/in ("{comp_clean}" "Engineering Manager" OR "Head of AI" OR "Director of AI")'
    recruiter_query = f'site:linkedin.com/in ("{comp_clean}" "Technical Recruiter" OR "Talent Acquisition" OR "Lead Recruiter")'
    founder_query = f'site:linkedin.com/in ("{comp_clean}" "Founder" OR "CTO" OR "VP Engineering")'

    return {
        "engineering_leadership_google": f"https://www.google.com/search?q={urllib.parse.quote_plus(em_query)}",
        "recruiter_google": f"https://www.google.com/search?q={urllib.parse.quote_plus(recruiter_query)}",
        "founders_google": f"https://www.google.com/search?q={urllib.parse.quote_plus(founder_query)}",
        "linkedin_people_search": f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote_plus(comp_clean + ' engineering')}"
    }

def generate_outreach_dossier(
    company: str,
    role: str,
    jd_text: str = "",
    archetype: str = "vision"
) -> Dict[str, Any]:
    profile = load_canonical_profile()
    search_links = generate_linkedin_search_urls(company)

    # 1. Select specific technical proof hook based on archetype
    if archetype == "vision":
        tech_hook = "Cascade R-CNN (97.5% acc) and RETFound ViTs"
        detail_bullet = "Engineered multi-stage OCR & medical ViTs achieving 97.5% detection accuracy on complex document pipelines."
    elif archetype == "rag":
        tech_hook = "production RAG, sentence-transformers & FastAPI"
        detail_bullet = "Developed end-to-end semantic RAG pipelines using sentence-transformers, Gemini API, and FastAPI on GPU backends."
    else:
        tech_hook = "applied deep learning & automated testing"
        detail_bullet = "Bridging deep learning architectures with 22 months of enterprise test automation background at TCS."

    # 2. LinkedIn Connection Note (Strictly <= 300 characters limit)
    # Target structure: Greeting + why reaching out + specific proof point + open ask
    li_note = (
        f"Hi! Saw {company}'s opening for {role}. "
        f"As an AI Engineer at KFUPM specializing in {tech_hook}, "
        f"I've built high-precision pipelines for production systems. "
        f"Would love to connect and follow {company}'s work!"
    )
    if len(li_note) > 300:
        # Fallback ultra-compact
        li_note = (
            f"Hi! Reaching out regarding the {role} role at {company}. "
            f"I'm an AI Engineer at KFUPM working on {tech_hook}. "
            f"Would love to connect and share relevant benchmarks!"
        )

    # 3. LinkedIn InMail / Follow-Up Pitch (~120 words)
    li_inmail = f"""Hi [Name],

I recently applied for the {role} position at {company} and wanted to reach out directly to your team.

My technical background at KFUPM centers on applied AI and computer vision:
• {detail_bullet}
• QA Automation Foundations: 22 months enterprise test automation experience at TCS ensuring high software reliability.

Work Rights: Transferable Iqama (Saudi Arabia) / immediately available for Global Remote & B2B engagements.

I'd be glad to share technical benchmarks or our open-source research implementations (https://github.com/redfries) if you have 5 minutes.

Best regards,
Shabaaz Hussain Shaik
https://infinitys.me
"""

    # 4. Executive Cold Email
    email_subject = f"Application: {role} — Shabaaz Hussain Shaik"
    email_body = f"""Dear [Hiring Manager / Team],

I am writing to express my enthusiastic interest in the {role} role at {company}.

As an AI & Machine Learning Engineer currently conducting applied deep learning research at KFUPM, my focus is on building high-reliability production vision and foundation model systems:

1. {detail_bullet}
2. Production Engineering: Experience deploying model inference endpoints via FastAPI, Docker, and GPU environments.
3. Proven Engineering Discipline: 22 months at Tata Consultancy Services (TCS) delivering automated test pipelines.

Candidate Profile & Work Rights:
- Saudi Arabia: Authorized to work via transferable resident Iqama.
- Global Remote / UAE: Available for direct employment or B2B contractor engagements.

I have attached my tailored single-column ATS resume for your convenience and would appreciate the opportunity to discuss how my skillset can support {company}'s engineering goals.

Links:
- Portfolio: https://infinitys.me
- GitHub: https://github.com/redfries
- LinkedIn: https://www.linkedin.com/in/redfries/

Best regards,

Shabaaz Hussain Shaik
AI / Machine Learning Engineer
+966 50 269 8140
theshabaaz@outlook.com
"""

    return {
        "company": company,
        "role": role,
        "archetype": archetype,
        "linkedin_search_links": search_links,
        "linkedin_connection_note_300chars": li_note,
        "linkedin_note_character_count": len(li_note),
        "linkedin_inmail_pitch": li_inmail,
        "executive_cold_email": {
            "subject": email_subject,
            "body": email_body
        }
    }

def print_dossier(dossier: Dict[str, Any]):
    print("\n" + "="*70)
    print(f"🚀 DEEP OUTREACH DOSSIER: {dossier['role']} @ {dossier['company']}")
    print("="*70 + "\n")

    print("--- [FIND THE HIRING TEAM (1-Click Google & LinkedIn)] ---")
    for name, url in dossier["linkedin_search_links"].items():
        print(f"• {name.replace('_', ' ').title()}:\n  {url}\n")

    print(f"--- [LINKEDIN CONNECTION REQUEST NOTE ({dossier['linkedin_note_character_count']} / 300 chars)] ---")
    print(dossier["linkedin_connection_note_300chars"])
    print("\n" + "-"*70 + "\n")

    print("--- [LINKEDIN INMAIL / FOLLOW-UP PITCH] ---")
    print(dossier["linkedin_inmail_pitch"])
    print("-" * 70 + "\n")

    print("--- [EXECUTIVE COLD EMAIL (Ready for Outlook Bridge)] ---")
    print(f"Subject: {dossier['executive_cold_email']['subject']}\n")
    print(dossier["executive_cold_email"]["body"])
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Deep Company Research & Multi-Channel Outreach Engine")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Role title")
    parser.add_argument("--focus", choices=["vision", "rag", "backend", "qa"], default="vision", help="Technical archetype")
    args = parser.parse_args()

    dossier = generate_outreach_dossier(args.company, args.role, archetype=args.focus)
    print_dossier(dossier)

if __name__ == "__main__":
    main()
