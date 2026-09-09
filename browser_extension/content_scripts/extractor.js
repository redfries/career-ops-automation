/**
 * extractor.js - Career-Ops Content Script
 * Auto-detects Job Title, Company, and Job Description from Greenhouse, Lever, Ashby,
 * LinkedIn, Bayt, Workday, and generic web pages.
 * Handles React/Remix-compatible 1-click form autofill using candidate profile context.
 */

function cleanText(text) {
  if (!text) return "";
  return text.replace(/\s+/g, " ").trim();
}

// React / Remix / Modern Framework Native Value Setter
function setNativeValue(element, value) {
  if (!element) return;
  const prototype = Object.getPrototypeOf(element);
  const valueSetter = Object.getOwnPropertyDescriptor(element, "value")?.set;
  const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;

  if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
    prototypeValueSetter.call(element, value);
  } else if (valueSetter) {
    valueSetter.call(element, value);
  } else {
    element.value = value;
  }

  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
  element.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Enter" }));
  element.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Enter" }));
}

function extractJobData() {
  const url = window.location.href;
  const hostname = window.location.hostname.toLowerCase();
  let company = "";
  let role = "";
  let jdText = "";

  // 1. Check if user has explicitly selected text on the page
  const selectedText = window.getSelection().toString().trim();

  // 2. Greenhouse (Legacy + New Remix/Job-Boards UI)
  if (hostname.includes("greenhouse.io") || hostname.includes("grnh.se")) {
    const titleEl = document.querySelector(".job__title") || document.querySelector(".app-title") || document.querySelector("h1.app-title") || document.querySelector("h1");
    const companyEl = document.querySelector(".company-name") || document.querySelector("span.company-name");
    const contentEl = document.querySelector(".job__description") || document.querySelector(".job-post-container") || document.querySelector("#content") || document.querySelector(".content");

    role = titleEl ? titleEl.innerText : "";
    company = companyEl ? companyEl.innerText.replace(/^at\s+/i, "") : "";
    jdText = contentEl ? contentEl.innerText : "";

    // On modern Greenhouse boards (e.g. job-boards.greenhouse.io/company/jobs/id), company is in title
    if (!company) {
      const titleMatch = document.title.match(/at\s+([^|\-–]+)/i);
      if (titleMatch) {
        company = titleMatch[1].trim();
      } else {
        const pathParts = window.location.pathname.split("/").filter(Boolean);
        if (pathParts.length > 0) {
          company = pathParts[0].replace(/jobs$/i, "").replace(/[-_]/g, " ").trim();
        }
      }
    }
  }
  // 3. Lever
  else if (hostname.includes("lever.co")) {
    const titleEl = document.querySelector(".posting-headline h2") || document.querySelector("h2");
    const companyEl = document.querySelector(".main-header-logo img") || document.querySelector(".posting-categories");
    const contentEl = document.querySelector(".section-wrapper") || document.querySelector(".posting-page");

    role = titleEl ? titleEl.innerText : "";
    company = companyEl ? (companyEl.alt || companyEl.innerText || "") : "";
    jdText = contentEl ? contentEl.innerText : "";
  }
  // 4. Ashby
  else if (hostname.includes("ashbyhq.com")) {
    const titleEl = document.querySelector("h1");
    const contentEl = document.querySelector("div[class*='_container_']") || document.querySelector("main");

    role = titleEl ? titleEl.innerText : "";
    company = window.location.pathname.split("/")[1] || "";
    jdText = contentEl ? contentEl.innerText : "";
  }
  // 5. LinkedIn
  else if (hostname.includes("linkedin.com")) {
    const titleEl = document.querySelector("h1.top-card-layout__title") || document.querySelector(".job-details-jobs-unified-top-card__job-title");
    const companyEl = document.querySelector("a.topcard__org-name-link") || document.querySelector(".job-details-jobs-unified-top-card__company-name");
    const contentEl = document.querySelector(".show-more-less-html__markup") || document.querySelector("#job-details");

    role = titleEl ? titleEl.innerText : "";
    company = companyEl ? companyEl.innerText : "";
    jdText = contentEl ? contentEl.innerText : "";
  }
  // 6. Bayt
  else if (hostname.includes("bayt.com")) {
    const titleEl = document.querySelector("h1") || document.querySelector("#job_title");
    const companyEl = document.querySelector("a[href*='/company/']") || document.querySelector(".t-nowrap");
    const contentEl = document.querySelector(".t-break-words") || document.querySelector(".job-description");

    role = titleEl ? titleEl.innerText : "";
    company = companyEl ? companyEl.innerText : "";
    jdText = contentEl ? contentEl.innerText : "";
  }

  // Generic Fallback
  if (!role) {
    const h1 = document.querySelector("h1");
    role = h1 ? h1.innerText : document.title;
  }
  if (!company) {
    const metaCompany = document.querySelector("meta[property='og:site_name']") || document.querySelector("meta[name='author']");
    company = metaCompany ? metaCompany.content : "";
    if (!company) {
      const parts = document.title.split(/[-–|]/);
      if (parts.length > 1) {
        company = parts[parts.length - 1].trim();
      }
    }
  }
  if (!jdText) {
    const article = document.querySelector("article") || document.querySelector("main") || document.body;
    jdText = article ? article.innerText : "";
  }

  if (selectedText.length > 50) {
    jdText = selectedText;
  }

  return {
    url: url,
    company: cleanText(company),
    role: cleanText(role),
    jd_text: jdText.trim()
  };
}

// Get rich identifier string for any input element
function getElementIdentifier(el) {
  let labelText = "";
  if (el.id) {
    try {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl) labelText += " " + lbl.innerText;
    } catch (e) {}
  }

  const parentLabel = el.closest("label");
  if (parentLabel) labelText += " " + parentLabel.innerText;

  const labelledBy = el.getAttribute("aria-labelledby");
  if (labelledBy) {
    labelledBy.split(/\s+/).forEach(id => {
      try {
        const lblEl = document.getElementById(id);
        if (lblEl) labelText += " " + lblEl.innerText;
      } catch (e) {}
    });
  }

  // Container context (e.g. .field, .form-group)
  const container = el.closest(".field, .form-group, div[class*='field'], div[class*='input'], div[class*='form']");
  if (container) {
    const header = container.querySelector("label, .label, legend, span[class*='label']");
    if (header) labelText += " " + header.innerText;
  }

  const autocomplete = el.getAttribute("autocomplete") || "";
  const ariaLabel = el.getAttribute("aria-label") || "";
  const placeholder = el.getAttribute("placeholder") || "";
  const name = el.name || "";
  const id = el.id || "";

  return `${id} ${name} ${placeholder} ${ariaLabel} ${autocomplete} ${labelText}`.toLowerCase();
}

// 1-Click Form Autofill Engine
function autofillForm(profile, screenerAnswers) {
  let filledCount = 0;
  const cand = profile?.candidate || {};
  const links = cand.links || {};

  const fieldRules = [
    // Preferred Name (Must come before first_name)
    {
      predicate: (id) => id.includes("preferred") || id.includes("nickname"),
      value: cand.first_name || "Shabaaz"
    },
    // First Name
    {
      predicate: (id) => (
        id.includes("first_name") || id.includes("firstname") || id.includes("first name") ||
        id.includes("given-name") || id.includes("given name") || id.includes("fname")
      ) && !id.includes("last"),
      value: cand.first_name || "Shabaaz"
    },
    // Last Name
    {
      predicate: (id) => (
        id.includes("last_name") || id.includes("lastname") || id.includes("last name") ||
        id.includes("family-name") || id.includes("family name") || id.includes("surname") || id.includes("lname")
      ),
      value: cand.last_name || "Hussain Shaik"
    },
    // Full Name (Only when not first or last name)
    {
      predicate: (id) => (
        id.includes("full_name") || id.includes("fullname") || id.includes("candidate_name") || id.includes("your name")
      ) && !id.includes("first") && !id.includes("last"),
      value: cand.name || "Shabaaz Hussain Shaik"
    },
    // Email
    {
      predicate: (id) => id.includes("email") || id.includes("e-mail") || id.includes("mail"),
      value: cand.email || "theshabaaz@outlook.com"
    },
    // Phone
    {
      predicate: (id) => id.includes("phone") || id.includes("mobile") || id.includes("telephone") || id.includes("cell"),
      value: cand.phone || "+966 50 269 8140"
    },
    // LinkedIn
    {
      predicate: (id) => id.includes("linkedin") || id.includes("linked in"),
      value: links.linkedin || "https://www.linkedin.com/in/redfries/"
    },
    // GitHub
    {
      predicate: (id) => id.includes("github") || id.includes("git hub"),
      value: links.github || "https://github.com/redfries"
    },
    // Website / Portfolio
    {
      predicate: (id) => id.includes("portfolio") || id.includes("website") || id.includes("personal site") || id.includes("personal url"),
      value: links.portfolio || "https://infinitys.me"
    },
    // City / Location
    {
      predicate: (id) => (id.includes("city") || id.includes("location") || id.includes("address")) && !id.includes("relocate"),
      value: "Dhahran, Saudi Arabia"
    },
    // Country
    {
      predicate: (id) => id.includes("country"),
      value: "Saudi Arabia"
    },
    // Education: School
    {
      predicate: (id) => id.includes("school") || id.includes("university") || id.includes("college") || id.includes("institution"),
      value: "King Fahd University of Petroleum & Minerals (KFUPM)"
    },
    // Education: Degree
    {
      predicate: (id) => id.includes("degree"),
      value: "Master of Science in Artificial Intelligence"
    },
    // Education: Discipline / Major
    {
      predicate: (id) => id.includes("discipline") || id.includes("major"),
      value: "Artificial Intelligence"
    },
    // Education: Start Year
    {
      predicate: (id) => id.includes("start date year") || id.includes("start-year"),
      value: "2024"
    },
    // Education: End Year / Graduation
    {
      predicate: (id) => id.includes("end date year") || id.includes("end-year") || id.includes("graduation year"),
      value: "2026"
    },
    // US Work Authorization screener question
    {
      predicate: (id) => id.includes("authorized to work") || id.includes("legally authorized"),
      value: "Yes"
    },
    // Sponsorship screener question
    {
      predicate: (id) => id.includes("sponsorship") || id.includes("require sponsorship"),
      value: "No"
    },
    // Relocation screener question
    {
      predicate: (id) => id.includes("relocate") || id.includes("located in"),
      value: "Yes"
    },
    // Licensure question
    {
      predicate: (id) => id.includes("licensure") || id.includes("license"),
      value: "No"
    }
  ];

  const elements = Array.from(document.querySelectorAll("input, textarea, select"));

  elements.forEach(el => {
    // Skip hidden or file upload elements
    if (el.type === "hidden" || el.type === "file") return;

    const identifier = getElementIdentifier(el);

    for (const rule of fieldRules) {
      if (rule.predicate(identifier)) {
        if (!el.value || el.value.trim() === "" || el.value.trim() === "0") {
          if (el.tagName === "SELECT") {
            // Find matching option
            const targetVal = rule.value.toLowerCase();
            const option = Array.from(el.options).find(opt => 
              opt.text.toLowerCase().includes(targetVal) || opt.value.toLowerCase().includes(targetVal)
            );
            if (option) {
              el.value = option.value;
              el.dispatchEvent(new Event("change", { bubbles: true }));
              filledCount++;
            }
          } else {
            setNativeValue(el, rule.value);
            filledCount++;
          }
        }
        break;
      }
    }

    // Custom Screener Answers in Textareas
    if (el.tagName === "TEXTAREA" && screenerAnswers) {
      if (screenerAnswers.technical_summary && (
        identifier.includes("summary") || identifier.includes("about you") ||
        identifier.includes("cover") || identifier.includes("experience") ||
        identifier.includes("pitch") || identifier.includes("tell us")
      )) {
        if (!el.value || el.value.trim() === "") {
          setNativeValue(el, screenerAnswers.technical_summary);
          filledCount++;
        }
      }
    }
  });

  return filledCount;
}

// Runtime message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "PING") {
    sendResponse({ status: "alive" });
    return true;
  }

  if (request.action === "GET_JOB_INFO") {
    const jobData = extractJobData();
    sendResponse(jobData);
    return true;
  }

  if (request.action === "AUTOFILL") {
    const count = autofillForm(request.profile, request.screener_answers);
    sendResponse({ success: true, count: count });
    return true;
  }

  return true;
});
