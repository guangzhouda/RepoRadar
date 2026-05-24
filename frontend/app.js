const sampleIdea = "我想做一个把 EPUB/PDF 转成 TTS 音频，并生成同步字幕的工具。";

const samplePayload = {
  phase: "frontend-demo",
  idea: sampleIdea,
  queries: [
    "epub pdf tts subtitle synchronized",
    "audiobook generator subtitle sync",
  ],
  candidates: [
    {
      full_name: "denizsafak/abogen",
      url: "https://github.com/denizsafak/abogen",
      description: "从 EPUB、PDF 和文本生成有声书，并输出同步字幕。",
      stars: 4545,
      forks: 288,
      language: "Python",
      license: "MIT",
      topics: ["有声书", "TTS", "字幕", "EPUB", "PDF"],
      pushed_at: "2026-05-24T12:27:28Z",
      relevance_score: 1,
      decision: "keep",
      rationale: "直接匹配 EPUB/PDF 转 TTS 和同步字幕需求。",
      skill_card: {
        repo: "denizsafak/abogen",
        name: "abogen",
        summary: "从 EPUB、PDF 和文本生成有声书，并输出同步字幕。",
        categories: ["文本转语音", "有声书生成", "字幕同步"],
        input_formats: ["EPUB", "PDF", "TXT", "Markdown", "SRT"],
        output_formats: ["WAV", "FLAC", "MP3", "OPUS", "M4B", "SRT"],
        interfaces: ["CLI", "Web", "API"],
        core_capabilities: ["文本转语音生成", "多格式电子书输入", "同步字幕生成", "按章节输出有声书", "批量队列处理"],
        optional_capabilities: ["LLM 文本规范化", "Audiobookshelf 集成", "GPU 加速"],
        model_providers: ["Kokoro", "Supertonic"],
        deployment: ["pip", "docker", "自托管"],
        suitable_for: ["有声书生成", "内容创作", "无障碍阅读"],
        not_supported: ["扫描 PDF OCR", "非英文词级字幕"],
        limitations: ["词级字幕仅支持英文", "暂不支持扫描 PDF 的 OCR", "AMD GPU 加速依赖 Linux ROCm"],
        evidence: [
          {
            source: "README.md",
            quote: "支持拖入 ePub、PDF、文本、Markdown 或字幕文件。",
            confidence: 0.95,
          },
        ],
        confidence: 0.9,
      },
    },
    {
      full_name: "lukaszliniewicz/Pandrator",
      url: "https://github.com/lukaszliniewicz/Pandrator",
      description: "将 PDF/EPUB 转成有声书，也支持字幕或视频配音工作流。",
      stars: 561,
      forks: 41,
      language: "Python",
      license: "AGPL-3.0",
      topics: ["有声书", "PDF", "EPUB", "字幕", "配音"],
      pushed_at: "2026-05-22T02:08:17Z",
      relevance_score: 1,
      decision: "keep",
      rationale: "工作流相似，但当前演示未生成能力卡。",
    },
    {
      full_name: "BoltzmannEntropy/MimikaStudio",
      url: "https://github.com/BoltzmannEntropy/MimikaStudio",
      description: "本地优先的有声书转换工具，具备 TTS 和声音克隆信号。",
      stars: 571,
      forks: 78,
      language: "Dart",
      license: "GPL-3.0",
      topics: ["有声书", "TTS", "声音克隆"],
      pushed_at: "2026-04-01T10:38:10Z",
      relevance_score: 0.6,
      decision: "review",
      rationale: "字幕同步证据较弱，建议人工复核。",
    },
  ],
};

const decisionLabels = {
  keep: "保留",
  review: "待复核",
  reject: "排除",
  unreviewed: "未评审",
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
const reportDocument = document.querySelector("#report-document");
const reportGeneratedAt = document.querySelector("#report-generated-at");
const reportRunId = document.querySelector("#report-run-id");
let currentPayload = clonePayload(samplePayload);
let currentCandidates = normalizeCandidates(currentPayload);
let selectedCandidate = currentCandidates[0];
let currentFilter = "all";
let activeController = null;
let backendMarkdown = "";
let frontendMarkdown = "";

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
  if (target === "reports") {
    renderReport();
  }
}

function showIdle() {
  idleLayout.hidden = false;
  runLayout.hidden = true;
  resultsLayout.hidden = true;
  if (activeController) {
    activeController.abort();
    activeController = null;
  }
}

function showRun() {
  idleLayout.hidden = true;
  runLayout.hidden = false;
  resultsLayout.hidden = true;
  runLog.innerHTML = "";
  if (isApiMode()) {
    runLiveAnalysis();
  } else {
    runDemoAnalysis();
  }
}

function showResults() {
  idleLayout.hidden = true;
  runLayout.hidden = true;
  resultsLayout.hidden = false;
  renderTable();
  selectCandidate(selectedCandidate?.fullName || currentCandidates[0]?.fullName || "");
}

function runDemoAnalysis() {
  const demoLogs = [
    "当前通过 file:// 打开，未连接本地后端，使用演示数据。",
    "已生成演示搜索策略。",
    "已载入 3 个演示候选仓库。",
    "已生成演示报告。",
  ];
  demoLogs.forEach((message, index) => {
    window.setTimeout(() => appendLog(message), 180 * index);
  });
  window.setTimeout(() => {
    currentPayload = clonePayload(samplePayload);
    currentPayload.idea = document.querySelector("#idea-input").value.trim() || sampleIdea;
    currentCandidates = normalizeCandidates(currentPayload);
    selectedCandidate = currentCandidates[0];
    backendMarkdown = "";
    renderReport();
    showResults();
  }, 900);
}

async function runLiveAnalysis() {
  activeController = new AbortController();
  appendLog("正在调用本地 API：/api/analyze");
  try {
    const payload = buildAnalyzeRequest();
    const response = await requestJson("/api/analyze", payload, activeController.signal);
    if (!response.ok) {
      appendLog(`分析失败：${response.error || "未知错误"}`);
      return;
    }

    currentPayload = response.payload;
    currentCandidates = normalizeCandidates(currentPayload);
    selectedCandidate = currentCandidates[0];
    appendLog(`分析完成：返回 ${currentCandidates.length} 个候选仓库`);

    appendLog("正在生成报告：/api/report");
    const reportResponse = await requestJson("/api/report", { payload: currentPayload }, activeController.signal);
    backendMarkdown = reportResponse.ok ? reportResponse.markdown || "" : "";
    appendLog(reportResponse.ok ? "报告已生成" : `报告生成失败：${reportResponse.error || "未知错误"}`);
    renderReport();
    showResults();
  } catch (error) {
    if (error.name !== "AbortError") {
      appendLog(`本地 API 调用失败：${error.message}`);
      appendLog("请确认已运行：py -3.14 scripts\\serve_frontend.py");
    }
  } finally {
    activeController = null;
  }
}

function buildAnalyzeRequest() {
  const queryMode = document.querySelector("#query-mode").value === "规则" ? "rules" : "llm";
  const reviewMode = document.querySelector("#review-mode").value === "关闭" ? "none" : "llm";
  return {
    idea: document.querySelector("#idea-input").value.trim(),
    max_repos: numberValue("#max-repos", 3),
    max_queries: 6,
    query_mode: queryMode,
    review_mode: reviewMode,
    extract_cards: document.querySelector("#extract-cards").checked,
    card_limit: numberValue("#card-limit", 1),
    card_decision: "keep",
    no_cache: !document.querySelector("#use-cache").checked,
    offline: false,
  };
}

async function requestJson(path, body, signal) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  const parsed = await response.json();
  if (!response.ok) {
    throw new Error(parsed.error || `HTTP ${response.status}`);
  }
  return parsed;
}

function appendLog(message) {
  const line = document.createElement("div");
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  runLog.appendChild(line);
}

function normalizeCandidates(payload) {
  const rawCandidates = Array.isArray(payload?.candidates) ? payload.candidates : [];
  return rawCandidates.map((raw) => {
    const card = raw.skill_card || {};
    const score = numeric(raw.score, raw.overall_score, raw.relevance_score, card.confidence, 0);
    return {
      raw,
      card,
      fullName: raw.full_name || raw.fullName || "",
      url: raw.url || "",
      description: raw.description || card.summary || "暂无描述。",
      decision: raw.decision || "unreviewed",
      rationale: raw.rationale || raw.reject_reason || "",
      score,
      relevance: numeric(raw.relevance_score, score),
      reuse: card.repo ? 1 : 0,
      docs: card.confidence ? Number(card.confidence) : 0,
      stars: Number(raw.stars || 0),
      language: raw.language || "未知",
      updated: formatDate(raw.pushed_at || raw.updated || raw.updatedAt || ""),
      topics: Array.isArray(raw.topics) ? raw.topics : [],
    };
  });
}

function renderTable() {
  const rows = currentCandidates.filter((candidate) => currentFilter === "all" || candidate.decision === currentFilter);
  repoTableBody.innerHTML = "";
  if (!rows.length) {
    repoTableBody.innerHTML = `<tr><td colspan="6">暂无候选仓库。</td></tr>`;
    return;
  }
  rows.forEach((candidate) => {
    const row = document.createElement("tr");
    row.className = candidate.fullName === selectedCandidate?.fullName ? "is-selected" : "";
    row.innerHTML = `
      <td>
        <div class="repo-name">
          <strong>${escapeHtml(candidate.fullName)}</strong>
          <span>${escapeHtml(candidate.description)}</span>
        </div>
      </td>
      <td>${decisionBadge(candidate.decision)}</td>
      <td>${candidate.score.toFixed(3)}</td>
      <td>${candidate.stars.toLocaleString()}</td>
      <td>${escapeHtml(candidate.language)}</td>
      <td>${escapeHtml(candidate.updated)}</td>
    `;
    row.addEventListener("click", () => selectCandidate(candidate.fullName));
    repoTableBody.appendChild(row);
  });
}

function decisionBadge(decision) {
  const badgeClass = decision === "keep" ? "badge-success" : decision === "reject" ? "badge-reject" : "badge-warn";
  return `<span class="badge ${badgeClass}">${escapeHtml(decisionLabels[decision] || decision)}</span>`;
}

function selectCandidate(fullName) {
  selectedCandidate = currentCandidates.find((candidate) => candidate.fullName === fullName) || currentCandidates[0];
  if (!selectedCandidate) {
    return;
  }
  document.querySelector("#selected-repo-name").textContent = selectedCandidate.fullName;
  document.querySelector("#selected-repo-summary").textContent = selectedCandidate.description;
  document.querySelector("#selected-overall").textContent = selectedCandidate.score.toFixed(3);
  document.querySelector("#selected-relevance").textContent = selectedCandidate.relevance.toFixed(3);
  document.querySelector("#selected-reuse").textContent = selectedCandidate.reuse.toFixed(3);
  document.querySelector("#selected-docs").textContent = selectedCandidate.docs.toFixed(3);
  renderDetail(selectedCandidate);
  renderTable();
}

function renderDetail(candidate) {
  const card = candidate.card || {};
  document.querySelector("#detail-title").textContent = candidate.fullName;
  document.querySelector("#detail-repo-url").textContent = candidate.url.replace(/^https?:\/\//, "") || candidate.fullName;
  document.querySelector("#detail-repo-description").textContent = candidate.description;
  document.querySelector(".confidence-pill").textContent = `置信度 ${numeric(card.confidence, 0).toFixed(3)}`;
  document.querySelector("#detail-tags").innerHTML = [candidate.language, candidate.raw.license, ...candidate.topics]
    .filter(Boolean)
    .slice(0, 6)
    .map((tag) => `<span>${escapeHtml(tag)}</span>`)
    .join("");
  renderScoreList(candidate);
  renderEvidence(card);
  renderSkillProperties(card);
  renderList("#core-capabilities", card.core_capabilities, ["暂无能力卡。"]);
  renderList("#optional-capabilities", card.optional_capabilities, ["暂无可选能力。"]);
  renderList("#limitations-list", card.limitations || card.not_supported, ["暂无限制信息。"]);
}

function renderScoreList(candidate) {
  const scoreRows = [
    ["综合", candidate.score],
    ["相关性", candidate.relevance],
    ["复用性", candidate.reuse],
    ["文档", candidate.docs],
    ["Stars", Math.min(candidate.stars / 5000, 1)],
  ];
  const scoreList = document.querySelector("#score-list");
  scoreList.innerHTML = "";
  scoreRows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "score-row";
    row.innerHTML = `
      <span>${escapeHtml(label)}</span>
      <div class="score-bar" aria-hidden="true"><span style="width: ${Math.round(value * 100)}%"></span></div>
      <strong>${value.toFixed(3)}</strong>
    `;
    scoreList.appendChild(row);
  });
}

function renderEvidence(card) {
  const evidence = Array.isArray(card.evidence) ? card.evidence[0] : null;
  const container = document.querySelector("#detail-evidence");
  if (!evidence) {
    container.innerHTML = "<span>暂无证据</span><blockquote>该候选尚未生成能力卡或缺少证据片段。</blockquote>";
    return;
  }
  container.innerHTML = `
    <span>${escapeHtml(evidence.source || "unknown")}</span>
    <blockquote>${escapeHtml(evidence.quote || "")}</blockquote>
    <strong>置信度 ${numeric(evidence.confidence, 0).toFixed(2)}</strong>
  `;
}

function renderSkillProperties(card) {
  const rows = [
    ["类别", joinList(card.categories)],
    ["输入", joinList(card.input_formats)],
    ["输出", joinList(card.output_formats)],
    ["接口", joinList(card.interfaces)],
    ["模型提供方", joinList(card.model_providers)],
    ["部署", joinList(card.deployment)],
  ];
  document.querySelector("#skill-properties").innerHTML = rows
    .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
}

function renderList(selector, items, fallback) {
  const values = Array.isArray(items) && items.length ? items : fallback;
  document.querySelector(selector).innerHTML = values.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderReport() {
  const idea = currentPayload.idea || document.querySelector("#idea-input").value.trim() || sampleIdea;
  const queries = Array.isArray(currentPayload.queries) ? currentPayload.queries : [];
  const candidates = currentCandidates;
  const topCandidate = candidates[0];
  reportGeneratedAt.textContent = new Date().toLocaleString();
  reportRunId.textContent = isApiMode() ? `run_${Date.now()}` : "demo";
  reportDocument.innerHTML = `
    <section id="report-idea">
      <h2>1. 用户想法</h2>
      <p>${escapeHtml(idea)}</p>
    </section>
    <section id="report-queries">
      <h2>2. 搜索策略</h2>
      <div class="query-row">${renderQueries(queries)}</div>
    </section>
    <section id="report-candidates">
      <h2>3. 候选总览</h2>
      ${renderCandidateTable(candidates)}
    </section>
    <section id="report-skill-cards">
      <h2>4. Top 项目能力卡</h2>
      ${renderSkillCardSummary(candidates)}
    </section>
    <section id="report-capabilities">
      <h2>5. 能力对比</h2>
      ${renderCapabilityTable(candidates)}
    </section>
    <section id="report-signals">
      <h2>6. 实现信号</h2>
      ${renderSignalTable(candidates)}
    </section>
    <section id="report-reuse">
      <h2>7. 复用与自研</h2>
      ${renderReuseAnalysis(topCandidate)}
    </section>
    <section id="report-recommendation">
      <h2>8. 结论</h2>
      <div class="recommendation">${escapeHtml(buildRecommendation(topCandidate))}</div>
    </section>
  `;
  frontendMarkdown = buildFrontendMarkdown();
}

function renderQueries(queries) {
  if (!queries.length) {
    return "<span>暂无搜索策略。</span>";
  }
  return queries.map((query) => `<code>${escapeHtml(query)}</code>`).join("");
}

function renderCandidateTable(candidates) {
  if (!candidates.length) {
    return "<p>暂无候选仓库。</p>";
  }
  const rows = candidates
    .map(
      (candidate) => `<tr>
        <td>${escapeHtml(candidate.fullName)}</td>
        <td>${decisionBadge(candidate.decision)}</td>
        <td>${escapeHtml(candidate.rationale || "暂无评审说明")}</td>
        <td>${candidate.score.toFixed(3)}</td>
        <td>${candidate.reuse.toFixed(3)}</td>
        <td>${candidate.docs.toFixed(3)}</td>
      </tr>`,
    )
    .join("");
  return `<table class="report-table">
    <thead><tr><th>仓库</th><th>决策</th><th>评审</th><th>评分</th><th>复用</th><th>文档</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderSkillCardSummary(candidates) {
  const cards = candidates.filter((candidate) => candidate.card?.repo);
  if (!cards.length) {
    return "<p>当前分析没有生成能力卡。请启用“生成能力卡”并重新分析。</p>";
  }
  return cards
    .slice(0, 3)
    .map((candidate) => {
      const card = candidate.card;
      return `<article class="inline-skill">
        <strong>${escapeHtml(candidate.fullName)}</strong>
        <span>输入：${escapeHtml(joinList(card.input_formats))}</span>
        <span>输出：${escapeHtml(joinList(card.output_formats))}</span>
        <span>接口：${escapeHtml(joinList(card.interfaces))}</span>
      </article>`;
    })
    .join("");
}

function renderCapabilityTable(candidates) {
  const rows = candidates
    .map((candidate) => {
      const card = candidate.card || {};
      return `<tr>
        <td>${escapeHtml(candidate.fullName)}</td>
        <td>${escapeHtml(joinList(card.input_formats))}</td>
        <td>${escapeHtml(joinList(card.output_formats))}</td>
        <td>${escapeHtml(joinList(card.interfaces))}</td>
        <td>${escapeHtml(joinList(card.core_capabilities, 3))}</td>
        <td>${escapeHtml(joinList(card.limitations || card.not_supported, 2))}</td>
      </tr>`;
    })
    .join("");
  return `<table class="report-table">
    <thead><tr><th>仓库</th><th>输入</th><th>输出</th><th>接口</th><th>核心能力</th><th>限制</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderSignalTable(candidates) {
  const rows = candidates
    .map((candidate) => {
      const card = candidate.card || {};
      return `<tr>
        <td>${escapeHtml(candidate.fullName)}</td>
        <td>${escapeHtml(joinList(card.model_providers))}</td>
        <td>${escapeHtml(joinList(card.deployment))}</td>
        <td>${escapeHtml(joinList(card.suitable_for))}</td>
        <td>${escapeHtml(joinList(card.not_supported))}</td>
      </tr>`;
    })
    .join("");
  return `<table class="report-table">
    <thead><tr><th>仓库</th><th>模型</th><th>部署</th><th>适合场景</th><th>不支持</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderReuseAnalysis(candidate) {
  if (!candidate) {
    return "<p>暂无候选，无法生成复用分析。</p>";
  }
  const card = candidate.card || {};
  return `<ul>
    <li>Top 候选：${escapeHtml(candidate.fullName)}，当前展示评分 ${candidate.score.toFixed(3)}。</li>
    <li>可复用模块：${escapeHtml(joinList(card.core_capabilities, 4))}。</li>
    <li>差异化机会：${escapeHtml(joinList(card.not_supported || card.limitations, 4))}。</li>
    <li>${candidate.score >= 0.75 ? "重复造轮子风险较高，建议先评估复用或 fork。" : "需要更多证据，建议人工复核后再决策。"}</li>
  </ul>`;
}

function buildRecommendation(candidate) {
  if (!candidate) {
    return "先完成仓库搜索和能力卡抽取，再判断是否自研。";
  }
  if (candidate.score >= 0.75) {
    return `优先复用或 fork ${candidate.fullName}，再针对缺口做人工复核。`;
  }
  return `暂不直接复用 ${candidate.fullName}，建议继续扩展搜索或人工复核关键能力。`;
}

function buildFrontendMarkdown() {
  const idea = currentPayload.idea || sampleIdea;
  const lines = [
    "# RepoRadar 调研报告",
    "",
    "## 用户想法",
    "",
    idea,
    "",
    "## 搜索策略",
    "",
    ...(currentPayload.queries || []).map((query) => `- \`${query}\``),
    "",
    "## 候选总览",
    "",
    "| 仓库 | 决策 | 评分 | 评审 |",
    "| --- | --- | ---: | --- |",
    ...currentCandidates.map((candidate) => `| ${candidate.fullName} | ${decisionLabels[candidate.decision] || candidate.decision} | ${candidate.score.toFixed(3)} | ${candidate.rationale || ""} |`),
    "",
    "## 结论",
    "",
    buildRecommendation(currentCandidates[0]),
  ];
  return lines.join("\n") + "\n";
}

function copyReportJson() {
  navigator.clipboard?.writeText(JSON.stringify(currentPayload, null, 2));
}

function downloadMarkdown() {
  const markdown = frontendMarkdown || backendMarkdown || buildFrontendMarkdown();
  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "reporadar-report.md";
  link.click();
  URL.revokeObjectURL(url);
}

function scrollReportSection(sectionId, trigger) {
  document.querySelectorAll(".report-link").forEach((item) => item.classList.toggle("is-active", item === trigger));
  document.querySelector(`#${sectionId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function checkApiHealth() {
  const apiStatus = document.querySelector("#api-status");
  const githubStatus = document.querySelector("#github-status");
  const llmStatus = document.querySelector("#llm-status");
  const hint = document.querySelector("#api-mode-hint");
  if (!isApiMode()) {
    apiStatus.textContent = "演示模式";
    githubStatus.textContent = "未连接";
    llmStatus.textContent = "未连接";
    hint.textContent = "当前通过本地文件打开，只能使用演示数据。要连接后端，请运行 py -3.14 scripts\\serve_frontend.py 后访问 http://127.0.0.1:8787/。";
    return;
  }
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    apiStatus.textContent = health.ok ? "已连接" : "异常";
    githubStatus.textContent = health.github_token_present ? "Token 已配置" : "匿名/无 Token";
    llmStatus.textContent = health.llm_configured && health.llm_key_present ? "已配置" : "未完整配置";
    hint.textContent = "已连接本地后端。开始分析会调用现有 Python 服务、GitHub provider 和 LLM provider。";
  } catch (_error) {
    apiStatus.textContent = "不可用";
    githubStatus.textContent = "未知";
    llmStatus.textContent = "未知";
    hint.textContent = "无法连接本地 API。请确认已运行 py -3.14 scripts\\serve_frontend.py。";
  }
}

function isApiMode() {
  return window.location.protocol === "http:" || window.location.protocol === "https:";
}

function numberValue(selector, fallback) {
  const value = Number(document.querySelector(selector).value);
  return Number.isFinite(value) ? value : fallback;
}

function numeric(...values) {
  for (const value of values) {
    const number = Number(value);
    if (Number.isFinite(number)) {
      return Math.max(0, Math.min(number, 1));
    }
  }
  return 0;
}

function formatDate(value) {
  if (!value) {
    return "未知";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

function joinList(items, limit = 5) {
  if (!Array.isArray(items) || !items.length) {
    return "未知";
  }
  return items.slice(0, limit).join("、");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function clonePayload(payload) {
  return JSON.parse(JSON.stringify(payload));
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
document.querySelector("#refresh-report").addEventListener("click", renderReport);

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("is-active", item === button));
    renderTable();
  });
});

document.querySelectorAll("[data-section]").forEach((button) => {
  button.addEventListener("click", () => scrollReportSection(button.dataset.section, button));
});

checkApiHealth();
renderTable();
selectCandidate(currentCandidates[0].fullName);
renderReport();
setView("analyze");
