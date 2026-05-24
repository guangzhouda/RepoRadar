const sampleIdea = "我想做一个把 EPUB/PDF 转成 TTS 音频，并生成同步字幕的工具。";

const sampleCandidates = [
  {
    fullName: "denizsafak/abogen",
    description: "从 EPUB、PDF 和文本生成有声书，并输出同步字幕。",
    decision: "keep",
    score: 0.974,
    relevance: 1,
    reuse: 1,
    docs: 0.968,
    stars: 4545,
    language: "Python",
    updated: "5月24日",
  },
  {
    fullName: "lukaszliniewicz/Pandrator",
    description: "将 PDF/EPUB 转成有声书，也支持字幕或视频配音工作流。",
    decision: "keep",
    score: 0.716,
    relevance: 1,
    reuse: 0.25,
    docs: 0,
    stars: 561,
    language: "Python",
    updated: "5月22日",
  },
  {
    fullName: "BoltzmannEntropy/MimikaStudio",
    description: "本地优先的有声书转换工具，具备 TTS 和声音克隆信号。",
    decision: "review",
    score: 0.582,
    relevance: 0.6,
    reuse: 0.25,
    docs: 0,
    stars: 571,
    language: "Dart",
    updated: "4月1日",
  },
];

const scoreRows = [
  ["综合", 0.974],
  ["相关性", 1],
  ["成熟度", 0.886],
  ["活跃度", 1],
  ["复用性", 1],
  ["文档", 0.968],
  ["许可证", 1],
];

const logs = [
  "正在生成 GitHub 搜索策略",
  "搜索策略通过：epub pdf tts subtitle synchronized",
  "GitHub 搜索返回 3 个标准化候选",
  "候选评审批次 1/1 已完成",
  "正在采集 denizsafak/abogen 的 README.md 和 pyproject.toml",
  "正在以 300s 超时流式抽取仓库能力卡",
];

const decisionLabels = {
  keep: "保留",
  review: "待复核",
  reject: "排除",
};

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
  return `<span class="badge ${badgeClass}">${decisionLabels[decision] || decision}</span>`;
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
    recommendation: "优先复用或 fork denizsafak/abogen，再针对缺口做人工复核。",
  };
  navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));
}

function downloadMarkdown() {
  const markdown = `# RepoRadar 调研报告

## 结论

优先复用或 fork denizsafak/abogen，再针对缺口做人工复核。
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
    if (target) {
      setView(target);
    }
  });
});

document.querySelector("#run-analysis").addEventListener("click", showRun);
document.querySelector("#load-sample").addEventListener("click", () => {
  document.querySelector("#idea-input").value = sampleIdea;
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
