# Resume & Professional Profile Guidelines

This document serves as the comprehensive, authoritative guide for writing, editing, and formatting the resume and professional profiles (LinkedIn, portfolio) for **Shabaaz Hussain Shaik**.

---

## 1. Core Philosophy & Tone Rules

- **Authentic & Genuine**: Never exaggerate or use fake/over-embellished claims. Always own contributions honestly.
- **Collaborative Framing**: Frame accomplishments as teamwork rather than claiming sole creation where appropriate (e.g., *"Collaborated with the facilities team..."* instead of *"established the first centralized registry"*).
- **Direct & Simple Phrasing**: Keep text simple, clear, and easy to read. Avoid convoluted corporate jargon or complicated formula flexing.
- **Avoid AI Writing Tells ("AI-isms")**:
  - Strictly adhere to the principles from the global `avoid-ai-writing` skill (`~/.gemini/config/skills/avoid-ai-writing/`).
  - Cut hollow intensifiers (*genuinely*, *truly*, *delve*, *testament*, *tapestry*).
  - Avoid forced triads / rule-of-three ("adjective, adjective, and adjective").
  - Avoid excessive bolding or unnecessary em-dashes (`—`).
  - Maintain a natural, direct, human developer voice.

---

## 2. Targeted Roles & Position Title

- **Target Roles**: AI Engineer, Machine Learning Engineer.
- **Header Subtitle**: `AI Engineer · Machine Learning Engineer`
- **Explicit Exclusion**: Omit "Software Engineer" from the position header to maintain a tight, specialized focus on AI/ML.

---

## 3. Behavioral & Professional Traits Integration Matrix

The resume and profiles naturally weave in key candidate evaluation traits:

| Trait | Resume & Profile Implementation |
| :--- | :--- |
| **Attitude & Drive** | Demonstrated proactive enthusiasm for AI via dedicated focus on AI Agents, Codex, Claude Code, and personal research projects built out of curiosity. |
| **Cultural Fit (Collaborative)** | Phrased with clear collaborative markers: *"Collaborated with the facilities team"*, *"Collaborated closely with cross-functional development teams"*. No victim mentality. |
| **Learning Agility** | Highlighted quick adoption of advanced tools/models (Tosca Vision AI for Citrix UI, Qwen3.5 VLM, RETFound foundation model, Gemini, Modal GPU). |
| **Ability to Understand & Implement** | Proven by building complete working systems end-to-end (FastAPI backend, Streamlit/web frontends, LoRA fine-tuning, sentence embeddings, Modal GPU deployment). |
| **Leadership Ability** | Highlighted via Teaching Assistantship at KFUPM (grading, leading tutorial sessions for CS undergraduates) and event volunteer coordination for 200+ attendees. |
| **Diligence & Ownership** | Owned end-to-end defect lifecycle management, zero critical defects reaching production, standardizing templates to prevent formatting errors. |
| **Customer First, Self Second** | Direct daily client status reporting at TCS, ensuring transparency and alignment with global client stakeholders. |
| **Technical Skills & Aesthetic** | Clean visual hierarchy, modern typography (Source Sans Pro regular weight for ~20% thicker text legibility), well-distributed skill categories. |
| **Model Prompting & Internal Chain of Thought** | Explicitly documented prompt template design and evaluating model response alignment against user interest profiles. |

---

## 4. Section-by-Section Resume Content & Formatting

### Page Layout & Font Styling
- **Class File**: `awesome-cv.cls`
- **Typography**: Body text weight set to regular (`\sourcesanspro`) instead of light (`\sourcesansprolight`) for a ~20% thicker, highly legible print and screen appearance.

### About Me / Skills Distribution
Organized into 6 distinct, balanced categories:
1. **AI / Machine Learning**: Deep Learning, Computer Vision, NLP, Vision Transformers, PyTorch, scikit-learn, LLMs, LoRA Fine-Tuning
2. **Software & Web Development**: Python, JavaScript, HTML/CSS, SQL, FastAPI, Streamlit *(Note: React/Vite explicitly removed)*
3. **Developer Tools**: Git, Linux, Jupyter, Docker, Modal GPU, MS Excel
4. **Creative Tools**: Adobe Photoshop, Adobe Lightroom, Canva
5. **AI Interests**: AI Agents & LLMs, Codex, Computer Vision, Agentic Systems, Claude Code *(Note: Open Source AI removed; Codex added)*
6. **Languages**: Fluent in English, Telugu, Urdu; Conversational in Arabic *(Positioned at the very bottom)*

### Work Experience

#### Data Analyst, Asset Management (Part-time) — KFUPM (Jan 2025 – Apr 2026 | Dhahran, Saudi Arabia)
- *Bullet 1*: Collaborated with the facilities team to consolidate fragmented physical inventory records into a structured Excel database, assisting in the registry cleanup.
- *Bullet 2*: Created simple pivot-table dashboards to help track asset status (new, in-use, decommissioned) across university departments.
- *Bullet 3*: Reconciled procurement records against active inventory using basic formulas to identify mismatches and reporting errors.
- *Bullet 4*: Assisted in preparing monthly asset reports for management to support planning and procurement decisions.
- *Bullet 5*: Standardized data-entry templates for the team to ensure consistency and minimize manual formatting errors.

#### QA Engineer — Tata Consultancy Services (TCS) (Feb 2022 – Dec 2023 | Hyderabad, India)
- *Bullet 1*: Automated UI regression tests for Salesforce applications using Tosca, significantly reducing manual regression cycles.
- *Bullet 2*: Conducted manual functional testing and exploratory testing for new features, ensuring zero critical defects reached production.
- *Bullet 3*: Collaborated closely with cross-functional development teams and business analysts to analyze requirements and design comprehensive test scenarios.
- *Bullet 4*: Leveraged Tosca Vision AI to scan visual elements inside Citrix virtualized environments, resolving complex automation challenges.
- *Bullet 5*: Managed defect lifecycle end-to-end, tracking issues in qTest and reporting daily status updates directly to global clients.

### Projects

#### Personalized Reading Experience (Masters Research Project · KFUPM)
- Built a full-stack AI reading assistant that semantically highlights relevant sentences in research PDFs against a user-defined interest profile — no keyword matching, pure embedding similarity.
- Fused multi-source profile representations using weighted-mean sentence embeddings with `all-mpnet-base-v2`.
- Integrated per-sentence LLM explanations via Google Gemini, surfacing *why* each sentence was flagged as relevant.
- Designed structured prompt templates for Gemini and evaluated model response alignment against user interest profiles.
- Deployed on Modal GPU infrastructure; FastAPI backend, web frontend — supports both GPU and CPU inference paths transparently.

#### Arabic Cheque OCR (Masters Research Project · KFUPM)
- Engineered a three-stage pipeline (detect, read, cross-validate) for numeric and handwritten monetary fields on Arabic bank cheques.
- Achieved 97.5% field detection accuracy (Cascade R-CNN with ResNet-50 + FPN) and 87.79% exact-match digit accuracy (custom CRNN + BiLSTM + CTC).
- Fine-tuned Qwen3.5-0.8B vision-language model with LoRA for handwritten Arabic legal-text OCR.
- Deployed a live Streamlit demo on Modal (A10G GPU).

#### ReSeeAI — AI-Based Retinal Disease Detection (AI Research Project · KFUPM BRAIN Lab)
- Fine-tuned RETFound (ViT-Large-Patch16) retinal foundation model for disease detection on fundus and OCT imaging datasets.
- Reached 92% accuracy on fundus and 94% on OCT via full fine-tuning.
- Integrated Grad-CAM visualizations to surface which retinal regions drive predictions, supporting clinical interpretability.

### Education

#### Master in Artificial Intelligence — King Fahd University of Petroleum & Minerals (KFUPM) (Aug 2024 – Present | Dhahran, Saudi Arabia)
- GPA: 3.5 / 4.0
- Specialized coursework in Deep Learning, Computer Vision, and Natural Language Processing.
- Conducted research projects in medical computer vision (retinal disease detection) and Arabic legal-document OCR.
- Served as a Teaching Assistant (TA), grading assignments and conducting tutorial sessions for undergraduate computer science courses.

#### Bachelor of Technology in Computer Science & Engineering — JNTUA (2018 – 2022 | India)
- GPA: 7.5 / 10

### Extracurricular Activities

#### Quantum Computing Symposium (Event Volunteer · KFUPM 2025)
- Assisted in organizing guest speaker sessions and coordinating venue logistics for over 200 participants.
- Guided attendees, managed registration booths, and supported the technical setup for presentations.

#### Inter-College Wrestling Championship (1st Place Champion · JNTUA 2021)
- Won 1st Place representing the college in the lightweight division, demonstrating dedication, focus, and physical discipline.

---

## 5. LinkedIn Profile & Banner Strategy

### Headline Style Options
- `Decentralization | AI & Machine Learning Engineer | Masters at KFUPM | Building at 🔗 infinitys.me`
- `AI & Machine Learning Engineer // Building at infinitys.me // MS Candidate @ KFUPM`

### About Section (Natural, Direct, Human Tone)
- Keep it concise, natural, and free of AI cliché words.
- Explicitly feature live portfolio links (`infinitys.me`).

### Banner Graphic Guidelines
- **Background**: Soft deep charcoal gray (`#16161a`).
- **Style**: Ultra-minimalist vector line-art (e.g., thin white infinity loop or node architecture diagram).
- **Responsive Layout**: Align graphics to the **far right / top right** so content is never obscured by profile pictures on desktop or cropped out on mobile screens.

---

## 6. Global Avoid AI Writing Integration

The global skill `avoid-ai-writing` (`~/.gemini/config/skills/avoid-ai-writing/SKILL.md`) is installed machine-wide. When generating or auditing prose:
- Prefer concrete nouns and direct verbs over meta-commentary ("a testament to", "delve into").
- Avoid AI structural patterns ("It's not X — it's Y", multi-negation reveals).
- Keep formatting clean, avoiding decorative emojis in headers or repetitive list structures.
