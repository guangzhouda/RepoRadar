// Browser entry point: state, event wiring, and DOM updates.
(function (global) {
  "use strict";

  const api = global.RepoRadarApi;
  const candidateViews = global.RepoRadarCandidateViews;
  const formatters = global.RepoRadarFormatters;
  const i18n = global.RepoRadarI18n;
  const report = global.RepoRadarReport;
  const sample = global.RepoRadarSampleData;

  const views = new Map(
    ["analyze", "detail", "reports", "settings"].map((name) => [name, document.querySelector(`#view-${name}`)]),
  );
  const navButtons = document.querySelectorAll("[data-nav]");
  const idleLayout = document.querySelector(".analyze-layout");
  const runLayout = document.querySelector(".run-layout");
  const resultsLayout = document.querySelector(".results-layout");
  const runLog = document.querySelector("#run-log");
  const reportDocument = document.querySelector("#report-document");
  const reportGeneratedAt = document.querySelector("#report-generated-at");
  const reportRunId = document.querySelector("#report-run-id");
  const languageSelect = document.querySelector("#display-language");
  const runTitle = document.querySelector("#run-title");

  let currentPayload = formatters.clonePayload(sample.samplePayload);
  let descriptionStates = new Map();
  let currentCandidates = normalizeCandidateViewModels();
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
    runTitle.textContent = currentIdeaTitle();
    if (api.isApiMode()) {
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
      i18n.t("log.demoMode"),
      i18n.t("log.demoQueries"),
      i18n.t("log.demoCandidates"),
      i18n.t("log.demoReport"),
    ];
    demoLogs.forEach((message, index) => {
      global.setTimeout(() => appendLog(message), 180 * index);
    });
    global.setTimeout(() => {
      currentPayload = formatters.clonePayload(sample.samplePayload);
      currentPayload.idea = currentIdeaTitle();
      descriptionStates = new Map();
      currentCandidates = normalizeCandidateViewModels();
      selectedCandidate = currentCandidates[0];
      backendMarkdown = "";
      renderReport();
      showResults();
    }, 900);
  }

  async function runLiveAnalysis() {
    activeController = new AbortController();
    appendLog(i18n.t("log.callAnalyze"));
    try {
      const payload = buildAnalyzeRequest();
      const response = await api.requestJson("/api/analyze", payload, activeController.signal);
      if (!response.ok) {
        appendLog(i18n.t("log.analysisFailed", { message: response.error || i18n.t("status.unknown") }));
        return;
      }

      currentPayload = response.payload;
      descriptionStates = new Map();
      currentCandidates = normalizeCandidateViewModels();
      selectedCandidate = currentCandidates[0];
      appendLog(i18n.t("log.analysisComplete", { count: currentCandidates.length }));
      appendLocalizationStatus(currentPayload);

      appendLog(i18n.t("log.callReport"));
      const reportResponse = await api.requestJson("/api/report", { payload: currentPayload }, activeController.signal);
      backendMarkdown = reportResponse.ok ? reportResponse.markdown || "" : "";
      appendLog(
        reportResponse.ok
          ? i18n.t("log.reportComplete")
          : i18n.t("log.reportFailed", { message: reportResponse.error || i18n.t("status.unknown") }),
      );
      renderReport();
      showResults();
    } catch (error) {
      if (error.name !== "AbortError") {
        appendLog(i18n.t("log.apiFailed", { message: error.message }));
        appendLog(i18n.t("log.startServerHint"));
      }
    } finally {
      activeController = null;
    }
  }

  function buildAnalyzeRequest() {
    return {
      idea: currentIdeaTitle(),
      max_repos: formatters.numberValue("#max-repos", 3),
      max_queries: 6,
      query_mode: document.querySelector("#query-mode").value,
      review_mode: document.querySelector("#review-mode").value,
      extract_cards: document.querySelector("#extract-cards").checked,
      card_limit: formatters.numberValue("#card-limit", 1),
      card_decision: "keep",
      no_cache: !document.querySelector("#use-cache").checked,
      offline: false,
      display_language: i18n.getLanguage(),
    };
  }

  function appendLog(message) {
    const line = document.createElement("div");
    const locale = i18n.getLanguage() === "zh" ? "zh-CN" : "en-US";
    line.textContent = `[${new Date().toLocaleTimeString(locale)}] ${message}`;
    runLog.appendChild(line);
  }

  function appendLocalizationStatus(payload) {
    if (payload.localization_error) {
      appendLog(i18n.t("log.localizationFailed", { message: payload.localization_error }));
      return;
    }
    if (payload.localization_status === "translated") {
      appendLog(i18n.t("log.localizationComplete"));
      return;
    }
    if (payload.localization_status === "skipped_llm_not_configured") {
      appendLog(i18n.t("log.localizationSkipped", { reason: i18n.t("status.llmIncomplete") }));
    }
  }

  function currentIdeaTitle() {
    return document.querySelector("#idea-input").value.trim() || sample.sampleIdeas[i18n.getLanguage()];
  }

  function renderTable() {
    candidateViews.renderTable(currentCandidates, selectedCandidate?.fullName || "", currentFilter, {
      onDescriptionToggle: toggleCandidateDescription,
      onSelect: selectCandidate,
    });
  }

  function selectCandidate(fullName) {
    selectedCandidate = currentCandidates.find((candidate) => candidate.fullName === fullName) || currentCandidates[0];
    if (!selectedCandidate) {
      return;
    }
    candidateViews.renderSummary(selectedCandidate);
    candidateViews.renderDetail(selectedCandidate);
    renderTable();
  }

  function refreshCandidateDisplay() {
    const selectedName = selectedCandidate?.fullName || "";
    currentCandidates = normalizeCandidateViewModels();
    selectedCandidate = currentCandidates.find((candidate) => candidate.fullName === selectedName) || currentCandidates[0];
    if (!selectedCandidate) {
      renderTable();
      return;
    }
    candidateViews.renderSummary(selectedCandidate);
    candidateViews.renderDetail(selectedCandidate);
    renderTable();
    renderReport();
  }

  function normalizeCandidateViewModels() {
    const candidates = formatters.normalizeCandidates(currentPayload);
    candidates.forEach(applyDescriptionState);
    return candidates;
  }

  function applyDescriptionState(candidate) {
    const state = descriptionStates.get(candidate.fullName) || {};
    const language = i18n.getLanguage();
    const original = originalDescription(candidate.raw);
    const translated = localizedDescription(candidate.raw, language);
    if (state.mode === "original" && original) {
      candidate.description = original;
      candidate.descriptionIsOriginal = isOriginalForLanguage(original, language);
    }
    candidate.descriptionAction = descriptionAction(original, translated, state, language);
  }

  function descriptionAction(original, translated, state, language) {
    if (!original || !["zh", "en"].includes(language)) {
      return { visible: false };
    }
    if (state.loading) {
      return { visible: true, disabled: true, label: i18n.t("status.translating") };
    }
    if (state.mode === "original") {
      return { visible: Boolean(translated || needsTranslation(original, language)), label: i18n.t("action.translate") };
    }
    if (translated) {
      return { visible: true, label: i18n.t("action.showOriginal") };
    }
    if (needsTranslation(original, language)) {
      return { visible: true, label: i18n.t("action.translate"), title: state.error || "" };
    }
    return { visible: false };
  }

  async function toggleCandidateDescription(fullName) {
    const raw = findPayloadCandidate(fullName);
    if (!raw) {
      return;
    }

    const language = i18n.getLanguage();
    const original = originalDescription(raw);
    const translated = localizedDescription(raw, language);
    const state = descriptionStates.get(fullName) || {};

    if (state.mode === "original" && translated) {
      descriptionStates.set(fullName, { mode: "translated" });
      refreshCandidateDisplay();
      return;
    }

    if (state.mode !== "original" && translated) {
      descriptionStates.set(fullName, { mode: "original" });
      refreshCandidateDisplay();
      return;
    }

    if (!api.isApiMode()) {
      descriptionStates.set(fullName, { ...state, error: i18n.t("ui.apiMissingHint") });
      refreshCandidateDisplay();
      return;
    }

    descriptionStates.set(fullName, { ...state, loading: true, error: "" });
    refreshCandidateDisplay();
    try {
      const response = await api.localizeText(original, language);
      if (!response.ok) {
        throw new Error(response.error || i18n.t("status.unknown"));
      }
      setDescriptionTranslation(raw, language, response.text);
      descriptionStates.set(fullName, { mode: "translated" });
    } catch (error) {
      descriptionStates.set(fullName, { ...state, error: error.message });
    }
    refreshCandidateDisplay();
  }

  function findPayloadCandidate(fullName) {
    return (currentPayload.candidates || []).find((candidate) => {
      return (candidate.full_name || candidate.fullName || "") === fullName;
    });
  }

  function originalDescription(raw) {
    return typeof raw?.description === "string" ? raw.description.trim() : "";
  }

  function localizedDescription(raw, language) {
    const direct = typeof raw?.[`description_${language}`] === "string" ? raw[`description_${language}`].trim() : "";
    if (direct) {
      return direct;
    }
    const i18nMap = raw?.description_i18n || raw?.description_localized;
    if (i18nMap && typeof i18nMap === "object" && typeof i18nMap[language] === "string") {
      return i18nMap[language].trim();
    }
    return "";
  }

  function setDescriptionTranslation(raw, language, text) {
    if (!raw.description_i18n || typeof raw.description_i18n !== "object" || Array.isArray(raw.description_i18n)) {
      raw.description_i18n = {};
    }
    raw.description_i18n[language] = text;
  }

  function needsTranslation(text, language) {
    const hasCjk = /[\u3400-\u9FFF]/.test(text);
    return language === "zh" ? !hasCjk : hasCjk;
  }

  function isOriginalForLanguage(text, language) {
    return language === "zh" ? /[A-Za-z]/.test(text) && !/[\u3400-\u9FFF]/.test(text) : /[\u3400-\u9FFF]/.test(text);
  }

  function renderReport() {
    const idea = currentPayload.idea || currentIdeaTitle();
    const locale = i18n.getLanguage() === "zh" ? "zh-CN" : "en-US";
    reportGeneratedAt.textContent = new Date().toLocaleString(locale);
    reportRunId.textContent = api.isApiMode() ? `run_${Date.now()}` : "demo";
    const rendered = report.renderReportDocument(currentPayload, currentCandidates, { idea });
    reportDocument.innerHTML = rendered.html;
    frontendMarkdown = rendered.markdown;
  }

  function copyReportJson() {
    navigator.clipboard?.writeText(JSON.stringify(currentPayload, null, 2));
  }

  function downloadMarkdown() {
    const markdown = frontendMarkdown || backendMarkdown || "";
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
    if (!api.isApiMode()) {
      apiStatus.textContent = i18n.t("status.apiDemo");
      githubStatus.textContent = i18n.t("status.notConnected");
      llmStatus.textContent = i18n.t("status.notConnected");
      hint.textContent = i18n.t("ui.apiDemoHint");
      return;
    }
    try {
      const health = await api.checkHealth();
      apiStatus.textContent = health.ok ? i18n.t("status.apiConnected") : i18n.t("status.apiUnhealthy");
      githubStatus.textContent = health.github_token_present
        ? i18n.t("status.githubToken")
        : i18n.t("status.githubAnonymous");
      llmStatus.textContent =
        health.llm_configured && health.llm_key_present ? i18n.t("status.llmConfigured") : i18n.t("status.llmIncomplete");
      hint.textContent = i18n.t("ui.apiLiveHint");
    } catch (_error) {
      apiStatus.textContent = i18n.t("status.apiUnavailable");
      githubStatus.textContent = i18n.t("status.unknown");
      llmStatus.textContent = i18n.t("status.unknown");
      hint.textContent = i18n.t("ui.apiMissingHint");
    }
  }

  function onLanguageChange() {
    i18n.setLanguage(languageSelect.value);
    currentCandidates = normalizeCandidateViewModels();
    selectedCandidate = currentCandidates.find((candidate) => candidate.fullName === selectedCandidate?.fullName) || currentCandidates[0];
    refreshOptionLabels();
    renderTable();
    if (selectedCandidate) {
      selectCandidate(selectedCandidate.fullName);
    }
    renderReport();
    checkApiHealth();
  }

  function refreshOptionLabels() {
    document.querySelector('#query-mode option[value="llm"]').textContent = i18n.t("option.llm");
    document.querySelector('#query-mode option[value="rules"]').textContent = i18n.t("option.rules");
    document.querySelector('#review-mode option[value="llm"]').textContent = i18n.t("option.llm");
    document.querySelector('#review-mode option[value="none"]').textContent = i18n.t("option.disabled");
  }

  function bindEvents() {
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
      document.querySelector("#idea-input").value = sample.sampleIdeas[i18n.getLanguage()];
    });
    document.querySelector("#cancel-run").addEventListener("click", showIdle);
    document.querySelector("#rerun-analysis").addEventListener("click", showRun);
    document.querySelector("#open-detail").addEventListener("click", () => setView("detail"));
    document.querySelector("#copy-json").addEventListener("click", copyReportJson);
    document.querySelector("#export-markdown").addEventListener("click", downloadMarkdown);
    document.querySelector("#refresh-report").addEventListener("click", renderReport);
    languageSelect.addEventListener("change", onLanguageChange);

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
  }

  function boot() {
    i18n.setLanguage(languageSelect.value);
    refreshOptionLabels();
    bindEvents();
    checkApiHealth();
    renderTable();
    selectCandidate(currentCandidates[0].fullName);
    renderReport();
    setView("analyze");
  }

  boot();
})(window);
