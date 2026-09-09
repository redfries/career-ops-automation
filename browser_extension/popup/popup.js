const SERVER_URL = "http://127.0.0.1:8765";

let currentJobData = {
  company: "",
  role: "",
  url: "",
  jd_text: ""
};

let currentEvaluation = null;
let currentTailorResult = null;
let existingApplication = null;
let toastTimeout = null;

// UI Elements
const statusIndicator = document.getElementById("statusIndicator");
const statusText = document.getElementById("statusText");
const companyInput = document.getElementById("companyInput");
const roleInput = document.getElementById("roleInput");
const urlSnippet = document.getElementById("urlSnippet");
const jobStatusPill = document.getElementById("jobStatusPill");

// Toast
const toastNotification = document.getElementById("toastNotification");
const toastIcon = document.getElementById("toastIcon");
const toastMessage = document.getElementById("toastMessage");

// Sections
const existingAppSection = document.getElementById("existingAppSection");
const stage1Section = document.getElementById("stage1Section");
const stage2Section = document.getElementById("stage2Section");
const stage3Section = document.getElementById("stage3Section");
const loadingSection = document.getElementById("loadingSection");
const loadingText = document.getElementById("loadingText");

// Existing Section Elements
const existingBanner = document.getElementById("existingAppBanner");
const existingBannerIcon = document.getElementById("existingBannerIcon");
const existingBannerTitle = document.getElementById("existingBannerTitle");
const existingBannerSub = document.getElementById("existingBannerSub");
const existingScoreVal = document.getElementById("existingScoreVal");
const existingArchetypeBadge = document.getElementById("existingArchetypeBadge");
const existingLifecycleBadge = document.getElementById("existingLifecycleBadge");
const existingMatchedCount = document.getElementById("existingMatchedCount");
const existingMatchedKeywords = document.getElementById("existingMatchedKeywords");
const existingOpenPdfBtn = document.getElementById("existingOpenPdfBtn");
const existingOpenFolderBtn = document.getElementById("existingOpenFolderBtn");
const existingAutofillBtn = document.getElementById("existingAutofillBtn");
const existingCopyAnswersBtn = document.getElementById("existingCopyAnswersBtn");
const existingSubmissionGate = document.getElementById("existingSubmissionGate");
const existingReceiptInput = document.getElementById("existingReceiptInput");
const existingMarkAppliedBtn = document.getElementById("existingMarkAppliedBtn");
const existingAppliedNotice = document.getElementById("existingAppliedNotice");
const existingReceiptDisplay = document.getElementById("existingReceiptDisplay");
const forceRetailorLink = document.getElementById("forceRetailorLink");

// Stage 1
const checkFitBtn = document.getElementById("checkFitBtn");

// Stage 2
const scoreVal = document.getElementById("scoreVal");
const archetypeBadge = document.getElementById("archetypeBadge");
const matchedCount = document.getElementById("matchedCount");
const matchedKeywordsEl = document.getElementById("matchedKeywords");
const missingKeywordsEl = document.getElementById("missingKeywords");
const missingBlock = document.getElementById("missingBlock");
const applyConfirmBtn = document.getElementById("applyConfirmBtn");
const skipBtn = document.getElementById("skipBtn");

// Stage 3
const applicationIdText = document.getElementById("applicationIdText");
const openPdfBtn = document.getElementById("openPdfBtn");
const openFolderBtn = document.getElementById("openFolderBtn");
const autofillBtn = document.getElementById("autofillBtn");
const copyAnswersBtn = document.getElementById("copyAnswersBtn");
const receiptInput = document.getElementById("receiptInput");
const markAppliedBtn = document.getElementById("markAppliedBtn");
const appliedSuccessNotice = document.getElementById("appliedSuccessNotice");

const reloadJobBtn = document.getElementById("reloadJobBtn");

// 1. Toast Notification Utility
function showToast(msg, icon = "✨", durationMs = 2600) {
  if (toastTimeout) clearTimeout(toastTimeout);
  toastIcon.innerText = icon;
  toastMessage.innerText = msg;
  toastNotification.classList.remove("hidden");

  toastTimeout = setTimeout(() => {
    toastNotification.classList.add("hidden");
  }, durationMs);
}

// 2. Check Local Hub Server Connection
async function checkServerHealth() {
  try {
    const res = await fetch(`${SERVER_URL}/api/health`, { method: "GET" });
    if (res.ok) {
      statusIndicator.className = "status-badge status-online";
      statusText.innerText = "Hub Online";
      return true;
    }
  } catch (err) {
    statusIndicator.className = "status-badge status-offline";
    statusText.innerText = "Hub Offline";
  }
  return false;
}

// 3. Render Skill Chips
function renderKeywords(container, keywords, isMatch) {
  container.innerHTML = "";
  if (!keywords || keywords.length === 0) {
    container.innerHTML = `<span class="chip ${isMatch ? 'chip-match' : 'chip-missing'}">None</span>`;
    return;
  }
  keywords.forEach(kw => {
    const chip = document.createElement("span");
    chip.className = `chip ${isMatch ? 'chip-match' : 'chip-missing'}`;
    chip.innerText = kw;
    container.appendChild(chip);
  });
}

// 4. Check If Application Already Exists (Smart Deduplication & State Recovery)
async function checkExistingApplication(url, company, role) {
  try {
    const res = await fetch(`${SERVER_URL}/api/check-job`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, company, role })
    });

    const data = await res.json();
    if (data.exists && data.application) {
      existingApplication = data.application;
      currentTailorResult = data.application;
      renderExistingApplication(data.application);
      return true;
    }
  } catch (err) {
    console.error("Check existing error:", err);
  }
  return false;
}

// 5. Render Existing Application Section
function renderExistingApplication(app) {
  const isSubmitted = app.status === "submitted";

  if (isSubmitted) {
    jobStatusPill.className = "job-pill pill-applied";
    jobStatusPill.innerText = "Submitted";

    existingBanner.className = "existing-banner banner-submitted";
    existingBannerIcon.innerText = "✅";
    existingBannerTitle.innerText = "Application Submitted & Tracked";
    existingBannerSub.innerText = app.submitted_at ? `Submitted on ${app.submitted_at.slice(0, 10)}` : "Recorded in SQLite & Notion";

    existingSubmissionGate.classList.add("hidden");
    existingAppliedNotice.classList.remove("hidden");
    existingReceiptDisplay.innerText = `Receipt: ${app.submission_receipt || "DIRECT-SUBMIT"}`;
  } else {
    jobStatusPill.className = "job-pill pill-found";
    jobStatusPill.innerText = "Tailored";

    existingBanner.className = "existing-banner banner-prepared";
    existingBannerIcon.innerText = "⚡";
    existingBannerTitle.innerText = "Tailored Application Ready";
    existingBannerSub.innerText = "Resume & screener answers ready in folder.";

    existingSubmissionGate.classList.remove("hidden");
    existingAppliedNotice.classList.add("hidden");
  }

  existingScoreVal.innerText = `${Math.round(app.ats_score || 88)}%`;
  existingArchetypeBadge.innerText = (app.archetype || "GENERAL").toUpperCase();
  existingLifecycleBadge.innerText = (app.status || "PREPARED").toUpperCase();
  existingMatchedCount.innerText = (app.matched_keywords || []).length;
  renderKeywords(existingMatchedKeywords, app.matched_keywords, true);

  // Switch display
  existingAppSection.classList.remove("hidden");
  stage1Section.classList.add("hidden");
  stage2Section.classList.add("hidden");
  stage3Section.classList.add("hidden");

  showToast("Loaded existing tailored application!", "⚡");
}

// 6. Ensure Content Script is active in active tab (auto-inject on demand)
async function ensureContentScriptReady(tabId) {
  try {
    const isAlive = await new Promise((resolve) => {
      chrome.tabs.sendMessage(tabId, { action: "PING" }, (resp) => {
        if (chrome.runtime.lastError || !resp || resp.status !== "alive") {
          resolve(false);
        } else {
          resolve(true);
        }
      });
    });

    if (!isAlive) {
      await chrome.scripting.executeScript({
        target: { tabId: tabId, allFrames: true },
        files: ["content_scripts/extractor.js"]
      });
      await new Promise(r => setTimeout(r, 150));
    }
    return true;
  } catch (err) {
    console.warn("[Career-Ops] Script injection notice:", err);
    return false;
  }
}

// 7. Fetch Job Info from Active Tab & Auto-Detect
async function fetchActiveTabJobInfo() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;

    urlSnippet.innerText = tab.url || "Active tab";
    currentJobData.url = tab.url;

    // Ensure content script is active in the page
    await ensureContentScriptReady(tab.id);

    chrome.tabs.sendMessage(tab.id, { action: "GET_JOB_INFO" }, async (response) => {
      if (chrome.runtime.lastError || !response) {
        // Fallback: check with URL alone
        await checkExistingApplication(tab.url, "", "");
        return;
      }

      currentJobData = response;
      companyInput.value = response.company || "";
      roleInput.value = response.role || "";

      // Immediately check if this job already exists in our system!
      const exists = await checkExistingApplication(response.url, response.company, response.role);
      if (!exists) {
        jobStatusPill.className = "job-pill pill-new";
        jobStatusPill.innerText = "New Job";
        existingAppSection.classList.add("hidden");
        stage1Section.classList.remove("hidden");
      }
    });
  } catch (err) {
    console.error("Tab info error:", err);
  }
}

// 8. ACTION: Open PDF (Directly in a new Chrome Tab + OS launch)
async function triggerOpenPdf(targetResult, btnElement) {
  if (!targetResult || !targetResult.pdf_path) {
    showToast("No resume PDF found for this job", "⚠️");
    return;
  }

  const labelSpan = btnElement ? btnElement.querySelector(".btn-label") : null;
  const originalLabel = labelSpan ? labelSpan.innerText : "View PDF (Tab)";
  if (labelSpan) labelSpan.innerText = "Opening...";

  const pdfUrl = `${SERVER_URL}/api/pdf?path=${encodeURIComponent(targetResult.pdf_path)}`;
  
  // 1. Open immediately in a new Chrome tab for 100% visible render
  try {
    chrome.tabs.create({ url: pdfUrl });
  } catch (e) {
    window.open(pdfUrl, "_blank");
  }

  // 2. Also signal backend to open OS file viewer if registered
  fetch(`${SERVER_URL}/api/open-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pdf_path: targetResult.pdf_path })
  }).catch(() => {});

  if (labelSpan) labelSpan.innerText = "Opened in Tab!";
  showToast("Opened resume PDF in a new tab!", "📄");

  setTimeout(() => {
    if (labelSpan) labelSpan.innerText = originalLabel;
  }, 2200);
}

// 9. ACTION: Open Application Folder in Windows Explorer
async function triggerOpenFolder(targetResult, btnElement) {
  if (!targetResult || !targetResult.bundle_dir) {
    showToast("Application folder path not found", "⚠️");
    return;
  }

  const labelSpan = btnElement ? btnElement.querySelector(".btn-label") : null;
  const originalLabel = labelSpan ? labelSpan.innerText : "Open Folder";
  if (labelSpan) labelSpan.innerText = "Opening...";

  try {
    const res = await fetch(`${SERVER_URL}/api/open-folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bundle_dir: targetResult.bundle_dir })
    });

    const data = await res.json();
    if (data.success) {
      if (labelSpan) labelSpan.innerText = "Opened Explorer!";
      showToast("Opened folder in Windows Explorer!", "📁");
    } else {
      if (labelSpan) labelSpan.innerText = "Folder Missing";
      showToast("Could not open folder on disk", "⚠️");
    }
  } catch (err) {
    if (labelSpan) labelSpan.innerText = "Error";
    showToast("Failed to connect to local server", "⚠️");
  }

  setTimeout(() => {
    if (labelSpan) labelSpan.innerText = originalLabel;
  }, 2200);
}

// 10. ACTION: 1-Click Form Autofill
async function triggerAutofill(targetResult, btnElement) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) return;

  const labelSpan = btnElement ? btnElement.querySelector(".btn-label") : null;
  const originalLabel = labelSpan ? labelSpan.innerText : "Autofill Form";
  if (labelSpan) labelSpan.innerText = "Filling...";

  const defaultProfile = {
    candidate: {
      name: "Shabaaz Hussain Shaik",
      first_name: "Shabaaz",
      last_name: "Hussain Shaik",
      email: "theshabaaz@outlook.com",
      phone: "+966 50 269 8140",
      links: {
        linkedin: "https://www.linkedin.com/in/redfries/",
        github: "https://github.com/redfries",
        portfolio: "https://infinitys.me"
      }
    }
  };

  // Ensure content script is active and ready
  await ensureContentScriptReady(tab.id);

  chrome.tabs.sendMessage(tab.id, {
    action: "AUTOFILL",
    profile: defaultProfile,
    screener_answers: targetResult ? targetResult.screener_answers : null
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.warn("Autofill message error:", chrome.runtime.lastError);
    }

    if (response && response.count > 0) {
      if (labelSpan) labelSpan.innerText = `Filled ${response.count} Fields!`;
      showToast(`Autofilled ${response.count} form fields!`, "✨");
    } else if (response && response.count === 0) {
      if (labelSpan) labelSpan.innerText = "No Fields Matched";
      showToast("Fields already filled or custom layout", "ℹ️");
    } else {
      if (labelSpan) labelSpan.innerText = "Reconnect Required";
      showToast("Please refresh the job page to connect extension", "⚠️");
    }

    setTimeout(() => {
      if (labelSpan) labelSpan.innerText = originalLabel;
    }, 2200);
  });
}

// 10. ACTION: Copy Screener Answers to Clipboard
function triggerCopyAnswers(targetResult, btnElement) {
  if (!targetResult || !targetResult.screener_answers) {
    showToast("No screener answers generated yet", "⚠️");
    return;
  }

  const labelSpan = btnElement ? btnElement.querySelector(".btn-label") : null;
  const originalLabel = labelSpan ? labelSpan.innerText : "Copy Answers";

  const answers = targetResult.screener_answers;
  const formatted = `[TECHNICAL SUMMARY]:\n${answers.technical_summary || ''}\n\n[WORK AUTHORIZATION]:\n${answers.work_authorization || ''}\n\n[EXPERIENCE]:\n${answers.years_experience || ''}\n\n[NOTICE PERIOD]:\n${answers.notice_period || ''}\n\n[PORTFOLIO]:\n${answers.portfolio_links || ''}`;

  navigator.clipboard.writeText(formatted).then(() => {
    if (labelSpan) labelSpan.innerText = "Copied!";
    showToast("Screener answers copied to clipboard!", "📋");
  }).catch(() => {
    showToast("Clipboard copy failed", "⚠️");
  });

  setTimeout(() => {
    if (labelSpan) labelSpan.innerText = originalLabel;
  }, 2200);
}

// 11. ACTION: Mark as Applied
async function triggerMarkApplied(targetResult, receiptInputEl, markBtnEl, successNoticeEl, receiptDisplayEl) {
  const appId = targetResult.id || targetResult.application_id;
  if (!appId) {
    showToast("Application ID missing", "⚠️");
    return;
  }

  const receiptVal = receiptInputEl ? receiptInputEl.value.trim() : "";
  markBtnEl.disabled = true;
  markBtnEl.innerText = "Saving Submission...";

  try {
    const res = await fetch(`${SERVER_URL}/api/mark-applied`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        application_id: appId,
        receipt: receiptVal
      })
    });

    const data = await res.json();
    if (data.success) {
      markBtnEl.innerText = "✅ Submitted & Recorded!";
      markBtnEl.style.background = "#15803d";
      jobStatusPill.className = "job-pill pill-applied";
      jobStatusPill.innerText = "Submitted";

      if (successNoticeEl) successNoticeEl.classList.remove("hidden");
      if (receiptDisplayEl) receiptDisplayEl.innerText = `Receipt: ${data.receipt}`;

      showToast("Application logged as SUBMITTED in SQLite & Notion!", "🎉");
    } else {
      markBtnEl.disabled = false;
      markBtnEl.innerText = "Retry Mark Applied";
      showToast(`Save failed: ${data.error || 'Unknown error'}`, "⚠️");
    }
  } catch (err) {
    markBtnEl.disabled = false;
    markBtnEl.innerText = "Retry Mark Applied";
    showToast(`Connection error: ${err.message}`, "⚠️");
  }
}

// --- EVENT LISTENERS ---

// Existing Application Buttons
existingOpenPdfBtn.addEventListener("click", () => triggerOpenPdf(existingApplication || currentTailorResult, existingOpenPdfBtn));
existingOpenFolderBtn.addEventListener("click", () => triggerOpenFolder(existingApplication || currentTailorResult, existingOpenFolderBtn));
existingAutofillBtn.addEventListener("click", () => triggerAutofill(existingApplication || currentTailorResult, existingAutofillBtn));
existingCopyAnswersBtn.addEventListener("click", () => triggerCopyAnswers(existingApplication || currentTailorResult, existingCopyAnswersBtn));
existingMarkAppliedBtn.addEventListener("click", () => triggerMarkApplied(
  existingApplication || currentTailorResult,
  existingReceiptInput,
  existingMarkAppliedBtn,
  existingAppliedNotice,
  existingReceiptDisplay
));

// Force Re-tailor link (Allows user to deliberately recreate)
forceRetailorLink.addEventListener("click", (e) => {
  e.preventDefault();
  existingAppSection.classList.add("hidden");
  stage1Section.classList.remove("hidden");
  showToast("Re-tailoring mode active.", "🔄");
});

// STAGE 1: Check Fit & Score (Preview only - zero DB clutter)
checkFitBtn.addEventListener("click", async () => {
  const isOnline = await checkServerHealth();
  if (!isOnline) {
    alert("Career-Ops local server is offline!\nRun: python scripts/local_server.py");
    return;
  }

  currentJobData.company = companyInput.value.trim() || "Target Employer";
  currentJobData.role = roleInput.value.trim() || "AI Engineer";

  stage1Section.classList.add("hidden");
  loadingText.innerText = "Extracting keywords & calculating ATS match...";
  loadingSection.classList.remove("hidden");

  try {
    const res = await fetch(`${SERVER_URL}/api/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: currentJobData.company,
        role: currentJobData.role,
        jd_text: currentJobData.jd_text,
        focus: "auto"
      })
    });

    const data = await res.json();
    loadingSection.classList.add("hidden");

    if (!data.success) {
      alert("Evaluation failed: " + (data.error || "Unknown"));
      stage1Section.classList.remove("hidden");
      return;
    }

    currentEvaluation = data;

    // Render Stage 2 (Score & Decision)
    scoreVal.innerText = `${Math.round(data.ats_score)}%`;
    archetypeBadge.innerText = (data.archetype || "GENERAL").toUpperCase();
    matchedCount.innerText = (data.matched_keywords || []).length;

    renderKeywords(matchedKeywordsEl, data.matched_keywords, true);

    if (data.missing_keywords && data.missing_keywords.length > 0) {
      missingBlock.classList.remove("hidden");
      renderKeywords(missingKeywordsEl, data.missing_keywords, false);
    } else {
      missingBlock.classList.add("hidden");
    }

    stage2Section.classList.remove("hidden");

  } catch (err) {
    loadingSection.classList.add("hidden");
    stage1Section.classList.remove("hidden");
    showToast(`Connection error: ${err.message}`, "⚠️");
  }
});

// STAGE 2: Skip Button
skipBtn.addEventListener("click", () => {
  stage2Section.classList.add("hidden");
  stage1Section.classList.remove("hidden");
});

// STAGE 2: I Want to Apply! (Compile tailored resume)
applyConfirmBtn.addEventListener("click", async () => {
  stage2Section.classList.add("hidden");
  loadingText.innerText = "Tailoring resume & compiling ATS PDF via Edge...";
  loadingSection.classList.remove("hidden");

  try {
    const res = await fetch(`${SERVER_URL}/api/tailor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: currentJobData.company,
        role: currentJobData.role,
        url: currentJobData.url,
        jd_text: currentJobData.jd_text,
        sync: true
      })
    });

    const data = await res.json();
    loadingSection.classList.add("hidden");

    if (!data.success) {
      alert("Tailoring failed: " + (data.error || "Unknown"));
      stage2Section.classList.remove("hidden");
      return;
    }

    currentTailorResult = data;
    applicationIdText.innerText = data.application_id;

    // Show Stage 3
    stage3Section.classList.remove("hidden");
    jobStatusPill.className = "job-pill pill-found";
    jobStatusPill.innerText = "Tailored";

    showToast("Resume compiled & ready to apply!", "🚀");

  } catch (err) {
    loadingSection.classList.add("hidden");
    stage2Section.classList.remove("hidden");
    showToast(`Compilation error: ${err.message}`, "⚠️");
  }
});

// Stage 3 Buttons
openPdfBtn.addEventListener("click", () => triggerOpenPdf(currentTailorResult, openPdfBtn));
openFolderBtn.addEventListener("click", () => triggerOpenFolder(currentTailorResult, openFolderBtn));
autofillBtn.addEventListener("click", () => triggerAutofill(currentTailorResult, autofillBtn));
copyAnswersBtn.addEventListener("click", () => triggerCopyAnswers(currentTailorResult, copyAnswersBtn));
markAppliedBtn.addEventListener("click", () => triggerMarkApplied(
  currentTailorResult,
  receiptInput,
  markAppliedBtn,
  appliedSuccessNotice,
  null
));

// Rescan Page
reloadJobBtn.addEventListener("click", (e) => {
  e.preventDefault();
  fetchActiveTabJobInfo();
  showToast("Rescanned active browser tab", "🔄");
});

document.addEventListener("DOMContentLoaded", () => {
  checkServerHealth();
  fetchActiveTabJobInfo();
});
