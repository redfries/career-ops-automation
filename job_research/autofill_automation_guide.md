# Autofill Automation Guide: 1-Click Low-Maintenance Job Applications

This guide explains how to set up and operate a zero-maintenance, 1-click application autofill pipeline that works across **Greenhouse, Lever, Ashby, Workday, SmartRecruiters, and Taleo** without writing or maintaining web scrapers/bots.

---

## 1. Why Browser Extension Autofill Beats Headless Bots

| Feature | Headless Script / Selenium Bot | Browser Extension Autofill (Simplify Copilot) |
| :--- | :--- | :--- |
| **Maintenance** | **High** (Breaks weekly when website HTML updates) | **Zero** (Maintained by engineering teams) |
| **Ban / Flag Risk** | **High** (Cloudflare blocks, LinkedIn flags accounts) | **Zero** (Runs inside your authenticated browser) |
| **Accuracy on Tricky Questions** | **Poor** (Hallucinates visa sponsorship, salary, years of exp) | **100% Controlled** (Pre-populated from your master profile) |
| **Speed per Application** | 10–30s (when it works) | **10–15 seconds total** (1 click + 5s glance + submit) |

---

## 2. Step-by-Step Setup (Takes 3 Minutes)

### Step 1: Install Simplify Copilot
1. Open Chrome, Edge, or Brave.
2. Go to the Chrome Web Store: search for **Simplify Copilot** (or visit [simplify.jobs/copilot](https://simplify.jobs/copilot)).
3. Click **Add to Chrome / Edge**.
4. Pin the extension icon to your browser toolbar.

### Step 2: Populate Your Simplify Profile
Open the extension popup and copy-paste values from [ats_form_master_profile.md](file:///c:/Users/lords/OneDrive/Documents/resume/job_research/ats_form_master_profile.md) (or [ats_profile.json](file:///c:/Users/lords/OneDrive/Documents/resume/job_research/ats_profile.json)):

1. **Personal Information**:
   * Name: `Shabaaz Hussain Shaik`
   * Preferred: `Shabaaz`
   * Email: `theshabaaz@outlook.com`
   * Phone: `+966 50 269 8140`
   * Location: `Dhahran, Saudi Arabia`
   * Links: Website (`https://infinitys.me`), GitHub (`https://github.com/redfries`), LinkedIn (`https://www.linkedin.com/in/redfries/`).

2. **Education**:
   * Master of Science in AI, KFUPM (GPA: 3.5, Expected: 2026).
   * Bachelor of Technology in CSE, JNTUA (GPA: 7.5, 2022).

3. **Experience**:
   * KFUPM Graduate TA (2024–Present).
   * TCS Systems Engineer (Python Automation, 2022–2023).

4. **Upload Resume**:
   * Upload `Shabaaz_Resume.pdf` (found at the root of this workspace).

5. **Work Authorization**:
   * Authorized in Saudi Arabia: `Yes` (No sponsorship required / Transferable Iqama).
   * Authorized in India: `Yes` (Citizen).
   * Global Remote Contractor: `Yes`.

---

## 3. The 15-Second Application Routine

Once installed, whenever you click an ATS application link from [active_application_tracker.md](file:///c:/Users/lords/OneDrive/Documents/resume/job_research/active_application_tracker.md):

```text
[1. Open Job Link] ➔ [2. Click "Autofill with Simplify"] ➔ [3. Review Custom Fields] ➔ [4. Click Submit]
```

1. **Open the direct ATS link**:
   * On Greenhouse, Lever, Ashby, or Workday, you will see a small **"Autofill with Simplify"** badge appear on the page.
2. **Click the button**:
   * In 1 second, it fills First Name, Last Name, Email, Phone, LinkedIn, GitHub, Portfolio, Education, Work History, and attaches your PDF resume.
3. **Glance at custom screener questions (5 seconds)**:
   * If the ATS asks for salary, refer to the [ats_form_master_profile.md](file:///c:/Users/lords/OneDrive/Documents/resume/job_research/ats_form_master_profile.md) cheat sheet.
   * If it asks an essay prompt ("Why this company?"), copy the pre-baked template from the master profile or ask the `job-hunter-firecrawl` skill to generate a tailored 2-sentence snippet.
4. **Hit Submit**:
   * Application is logged directly in your tracker.

---

## 4. Complementary Tools for Link Sourcing & Tracking

* **Simplify Jobs Tracker / Teal**:
  * Automatically detects submitted applications and logs the company, title, and date in a personal dashboard.
* **Firecrawl Skill (`job-hunter-firecrawl`)**:
  * Run on-demand directly in your editor to uncover fresh, unindexed direct ATS openings across Saudi Arabia, UAE, and Remote before they get flooded on LinkedIn.
