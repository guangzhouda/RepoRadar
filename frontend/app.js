const sampleCandidates = [
  {
    fullName: "denizsafak/abogen",
    description: "Generate audiobooks from EPUBs, PDFs and text with synchronized captions.",
    decision: "keep",
    score: 0.974,
    relevance: 1,
    reuse: 1,
    docs: 0.968,
    stars: 4545,
    language: "Python",
    updated: "May 24",
  },
  {
    fullName: "lukaszliniewicz/Pandrator",
    description: "Turn PDFs and EPUBs into audiobooks; subtitles or videos into dubbed videos.",
    decision: "keep",
    score: 0.716,
    relevance: 1,
    reuse: 0.25,
    docs: 0,
    stars: 561,
    language: "Python",
    updated: "May 22",
  },
  {
    fullName: "BoltzmannEntropy/MimikaStudio",
    description: "Local-first audiobook converter with TTS and voice cloning signals.",
    decision: "review",
    score: 0.582,
    relevance: 0.6,
    reuse: 0.25,
    docs: 0,
    stars: 571,
    language: "Dart",
    updated: "Apr 01",
  },
];

const scoreRows = [
  ["Overall", 0.974],
  ["Relevance", 1],
  ["Maturity", 0.886],
  ["Activity", 1],
  ["Reuse", 1],
  ["Docs", 0.968],
  ["License", 1],
];

const logs = [
  "planning queries with llm provider",
  "query accepted: epub pdf tts subtitle synchronized",
  "github search returned 3 normalized candidates",
  "review batch 1/1 completed",
  "collecting README.md and pyproject.toml for denizsafak/abogen",
  "streaming skill card extraction with 300s timeout",
];

const views = new Map(
  ["analyze", "detail", "reports", "settings"].map((name) => [name, document.querySelector(`#view-${name}`)]),
);

const navButtons = document.querySelectorAll("[data-nav]");
const idleLayout = document.querySelector(".analyze-layout");
const runLayout = document.querySelector(".run-layout");
const resultsLayout = document.querySelector(".results-layout");
const repoTableBody = document.querySelector("#repo-table-body");
const runLog = document.querySelector("#run-log");
let selectedCandidate = sampleCandidates[0];
let currentFilter = "all";
let runTimer = 0;

function setView(name) {
  const target = views.get(name) ? name : "analyze";
  views.forEach((view, viewName) => {
    view.classList.toggle("is-active", viewName === target);
  });
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.nav === target);
  });
  if (target === "analyze" && resultsLayout.hidden) {
    showIdle();
  }
}

function showIdle() {
  idleLayout.hidden = false;
  runLayout.hidden = true;
  resultsLayout.hidden = true;
  clearTimeout(runTimer);
}

function showRun() {
  idleLayout.hidden = true;
  runLayout.hidden = false;
  resultsLayout.hidden = true;
  runLog.innerHTML = "";
  logs.forEach((message, index) => {
    window.setTimeout(() => appendLog(message), 240 * index);
  });
  clearTimeout(runTimer);
  runTimer = window.setTimeout(showResults, 1700);
}

function showResults() {
  idleLayout.hidden = true;
  runLayout.hidden = true;
  resultsLayout.hidden = false;
  clearTimeout(runTimer);
  renderTable();
  selectCandidate(selectedCandidate.fullName);
}

function appendLog(message) {
  const line = document.createElement("div");
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  runLog.appendChild(line);
}

function renderTable() {
  const rows = sampleCandidates.filter((candidate) => currentFilter === "all" || candidate.decision === currentFilter);
  repoTableBody.innerHTML = "";
  rows.forEach((candidate) => {
    const row = document.createElement("tr");
    row.className = candidate.fullName === selectedCandidate.fullName ? "is-selected" : "";
    row.innerHTML = `
      <td>
        <div class="repo-name">
          <strong>${candidate.fullName}</strong>
          <span>${candidate.description}</span>
        </div>
      </td>
      <td>${decisionBadge(candidate.decision)}</td>
      <td>${candidate.score.toFixed(3)}</td>
      <td>${candidate.stars.toLocaleString()}</td>
      <td>${candidate.language}</td>
      <td>${candidate.updated}</td>
    `;
    row.addEventListener("click", () => selectCandidate(candidate.fullName));
    repoTableBody.appendChild(row);
  });
}

function decisionBadge(decision) {
  const badgeClass = decision === "keep" ? "badge-success" : decision === "reject" ? "badge-reject" : "badge-warn";
  return `<span class="badge ${badgeClass}">${decision}</span>`;
}

function selectCandidate(fullName) {
  selectedCandidate = sampleCandidates.find((candidate) => candidate.fullName === fullName) || sampleCandidates[0];
  document.querySelector("#selected-repo-name").textContent = selectedCandidate.fullName;
  document.querySelector("#selected-repo-summary").textContent = selectedCandidate.description;
  document.querySelector("#selected-overall").textContent = selectedCandidate.score.toFixed(3);
  document.querySelector("#selected-relevance").textContent = selectedCandidate.relevance.toFixed(3);
  document.querySelector("#selected-reuse").textContent = selectedCandidate.reuse.toFixed(3);
  document.querySelector("#selected-docs").textContent = selectedCandidate.docs.toFixed(3);
  renderTable();
}

function renderScoreList() {
  const scoreList = document.querySelector("#score-list");
  scoreList.innerHTML = "";
  scoreRows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "score-row";
    row.innerHTML = `
      <span>${label}</span>
      <div class="score-bar" aria-hidden="true"><span style="width: ${Math.round(value * 100)}%"></span></div>
      <strong>${value.toFixed(3)}</strong>
    `;
    scoreList.appendChild(row);
  });
}

function copyReportJson() {
  const payload = {
    idea: document.querySelector("#idea-input").value.trim(),
    candidates: sampleCandidates,
    recommendation: "Prefer reuse or fork of denizsafak/abogen first.",
  };
  navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));
}

function downloadMarkdown() {
  const markdown = `# RepoRadar Research Report

## Recommendation

Prefer reuse or fork of denizsafak/abogen first, then validate gaps with manual review.
`;
  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "reporadar-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.nav;
    if (target === "reports") {
      setView("reports");
    } else if (target) {
      setView(target);
    }
  });
});

document.querySelector("#run-analysis").addEventListener("click", showRun);
document.querySelector("#load-sample").addEventListener("click", () => {
  document.querySelector("#idea-input").value =
    "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles.";
});
document.querySelector("#cancel-run").addEventListener("click", showIdle);
document.querySelector("#rerun-analysis").addEventListener("click", showRun);
document.querySelector("#open-detail").addEventListener("click", () => setView("detail"));
document.querySelector("#copy-json").addEventListener("click", copyReportJson);
document.querySelector("#export-markdown").addEventListener("click", downloadMarkdown);

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("is-active", item === button));
    renderTable();
  });
});

renderScoreList();
renderTable();
setView("analyze");
