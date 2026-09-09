# Interview Prep — Work Experience

---

## Job 1: Data Analyst, Asset Management — KFUPM (Part-time)

### What you actually did (honest version)
You worked under a facilities manager who had records of old university assets (furniture, equipment). You organized those records in Excel, calculated values, and prepared reports for management.

### How to explain it confidently

**"Tell me about your data analyst role at KFUPM."**
> "It was a part-time role while I was doing my Masters. The facilities team had all their asset data scattered — paper records, partial spreadsheets, nothing centralized. I came in and built a proper Excel-based inventory system, set up pivot dashboards so management could see asset status by department at a glance, and delivered monthly reports. It taught me a lot about how messy real-world data actually is before anyone touches it."

---

### Things to know / learn before the interview

#### Excel
| Topic | Why it matters | Learn it |
|---|---|---|
| Pivot Tables | You built dashboards with them | [Excel Easy - Pivot Tables](https://www.excel-easy.com/data-analysis/pivot-tables.html) |
| VLOOKUP / XLOOKUP | You used for reconciliation | Practice: match two lists and find mismatches |
| SUMIF / COUNTIF | Aggregating by category | Practice: sum assets by department |
| Conditional Formatting | Part of your dashboards | Color-code by status: new / in-use / decommissioned |
| Data Validation | Standardizing entry templates | Dropdown lists to control input |

#### Concepts
- **Data reconciliation** — matching two datasets to find differences (e.g. what was purchased vs. what's in the inventory)
- **Data standardization** — making sure everyone enters data the same way (consistent categories, no typos)
- **Asset lifecycle** — the stages an asset goes through: purchased → in-use → maintenance → decommissioned

#### Likely interview questions
1. *"What tools did you use?"* → Excel (pivot tables, VLOOKUP, SUMIF, conditional formatting)
2. *"What was the biggest challenge?"* → Data was inconsistent and scattered. Had to define a standard schema first before touching the numbers.
3. *"What did management use the reports for?"* → Procurement decisions — whether to buy new furniture or keep existing stock
4. *"Did you use any automation?"* → You can say you used Excel formulas to automate calculations so reports updated automatically when new data was entered

---

---

## Job 2: QA Engineer — Tata Consultancy Services (TCS)

### What you actually did (honest version)
You tested software applications — specifically a Citrix-based app and a Salesforce app — for Takeda Pharmaceutical. You used a tool called **Tosca** for automation and **qTest** for tracking tests. The client was global, so you communicated in English directly with them.

### How to explain it confidently

**"Tell me about your experience at TCS."**
> "I worked as a QA Engineer for about 2.5 years at TCS, on projects for a global pharmaceutical client. One project was automating tests for a Citrix virtualized desktop environment — the tricky part there is that normal automation tools that look for HTML elements don't work inside Citrix, so we used Tosca's Vision AI which works like a human eye — it finds controls based on what they look like on screen. The second project was Salesforce testing across multiple regions. I managed the full defect lifecycle and had direct calls with the global client team for daily status updates."

---

### Things to know / learn before the interview

#### Tosca (Test automation tool by Tricentis)
- **What it is**: An automation testing tool that doesn't rely on code — it uses a model-based approach
- **Vision AI / Image-Based Scan**: Tosca can identify UI elements by how they *look* (position, color, label) instead of HTML properties — critical for Citrix where there is no DOM
- **Self-healing scripts**: When a UI element moves or changes slightly, Tosca adjusts automatically instead of breaking
- **Modules/TestCases/TestSuite**: Tosca organizes tests in a hierarchy — reusable Modules → TestCases → ExecutionLists
- Quick intro: [Tosca Docs](https://documentation.tricentis.com/tosca/latest/en/content/home.htm)

#### qTest (Test management tool by PTC)
- **What it is**: A platform to organize test cases, link them to requirements, and track execution results
- **Key workflow**: Write test cases → link to requirements → execute → log pass/fail → report defects
- You imported Tosca results into qTest so stakeholders could see coverage

#### Salesforce Testing concepts
- **Multi-region releases**: The same app deployed in different countries — each region may have different configurations, so testing is done per-region
- **Automation coverage**: % of test cases automated vs. manual — a key release metric
- **DAR (Defect Acceptance Rate)**: % of defects accepted by the client as valid — a quality metric

#### Agile / Sprint testing
- A sprint is typically 2 weeks
- "In-sprint testing" means you test features in the same sprint they're developed, not after
- You owned E2E (end-to-end) flows — meaning you tested whole user journeys, not just individual screens

#### Defect lifecycle (know this cold)
```
New → Assigned → In Progress → Fixed → Retest → Closed
                                      → Reopen (if not fixed)
```

#### Likely interview questions
1. *"What is Tosca?"* → Model-based automation tool. No coding needed. Vision AI handles virtualized environments like Citrix.
2. *"What's the difference between manual and automation testing?"* → Manual = human runs tests. Automation = scripts run tests. Automation is faster for regression, manual is better for exploratory testing.
3. *"What is regression testing?"* → Re-running existing tests after new changes to make sure nothing broke.
4. *"How did you handle a failing test?"* → Investigate whether it's a real defect or a script issue. Log it if real, fix the script if it's an environment or locator problem.
5. *"Why did you use Vision AI for Citrix?"* → Standard DOM-based locators don't work inside a Citrix virtual desktop. Vision AI identifies controls by visual properties — like a human would — so it works.
6. *"How did you communicate with the client?"* → Daily defect status calls. Reported defect counts, severity, fix progress. Kept it factual and concise.
7. *"What metrics did you report?"* → Automation coverage (%), DAR (defect acceptance rate), defect rejection rate, total defects by severity.

---

## General tips for both jobs
- Speak in **past tense** and use **"I"** — own what you did
- If you don't know an exact number, say **"roughly"** — e.g. "roughly 200 assets tracked" or "around 15–20 test cases per sprint"
- Always end answers with **impact** — "which helped management make faster decisions" / "which reduced manual regression effort"
- It's fine to say "I was part of a team that..." for things you didn't own solo
