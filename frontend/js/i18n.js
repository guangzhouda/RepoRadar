// Frontend display-language helpers and localized field selection.
(function (global) {
  "use strict";

  const dictionaries = {
    zh: {
      "action.cancel": "取消",
      "action.copyJson": "复制 JSON",
      "action.exportMarkdown": "导出 Markdown",
      "action.loadSample": "填入示例",
      "action.refreshReport": "刷新报告",
      "action.generateReport": "生成报告",
      "action.openDirectory": "打开目录",
      "action.rerun": "重新分析",
      "action.run": "开始分析",
      "action.viewSkillCard": "查看能力卡",
      "action.testCompletion": "测试补全",
      "action.testConnection": "测试连接",
      "action.clearCache": "清理缓存",
      "action.showOriginal": "原文",
      "action.translate": "翻译",
      "candidate.noDescription": "暂无描述。",
      "candidate.original": "原文",
      "decision.keep": "保留",
      "decision.reject": "排除",
      "decision.review": "待复核",
      "decision.unreviewed": "未评审",
      "detail.back": "返回候选列表",
      "detail.capabilityProfile": "能力画像",
      "detail.confidence": "置信度 {value}",
      "detail.coreCapabilities": "核心能力",
      "detail.evidence": "证据",
      "detail.limitations": "限制",
      "detail.noEvidence": "暂无证据",
      "detail.noEvidenceBody": "该候选尚未生成能力卡或缺少证据片段。",
      "detail.noLimitations": "暂无限制信息。",
      "detail.noOptionalCapabilities": "暂无可选能力。",
      "detail.noSkillCard": "暂无能力卡。",
      "detail.optionalCapabilities": "可选能力",
      "detail.scoreBreakdown": "评分拆解",
      "field.cardLimit": "能力卡数量",
      "field.extractCards": "生成能力卡",
      "field.idea": "项目想法",
      "field.language": "显示语言",
      "field.maxRepos": "候选数量",
      "field.queryMode": "搜索策略",
      "field.reviewMode": "候选评审",
      "field.useCache": "使用缓存",
      "filter.all": "全部",
      "filter.keep": "保留",
      "filter.reject": "排除",
      "filter.review": "待复核",
      "heading.analyze": "开源复用分析工作台",
      "heading.currentCandidate": "当前候选",
      "heading.runConfig": "运行配置",
      "heading.runEnvironment": "运行环境",
      "heading.runtimeChecks": "运行检查",
      "heading.cache": "缓存",
      "heading.report": "RepoRadar 调研报告",
      "heading.settings": "设置",
      "heading.skillCard": "仓库能力卡",
      "label.activity": "活跃度",
      "label.apiBase": "API 地址",
      "label.categories": "类别",
      "label.cacheDir": "缓存目录",
      "label.collectionCache": "仓库采集缓存",
      "label.deployment": "部署",
      "label.docs": "文档",
      "label.inputs": "输入",
      "label.interfaces": "接口",
      "label.language": "语言",
      "label.license": "License",
      "label.modelProviders": "模型提供方",
      "label.model": "模型",
      "label.provider": "Provider",
      "label.outputs": "输出",
      "label.overall": "综合",
      "label.recentLiveSmoke": "最近 live smoke",
      "label.recentReportExport": "最近报告导出",
      "label.relevance": "相关性",
      "label.reuse": "复用性",
      "label.searchCache": "搜索缓存",
      "label.score": "评分",
      "label.skillCardCache": "能力卡缓存",
      "label.stars": "Stars",
      "label.status": "状态",
      "label.streaming": "流式响应",
      "label.tests": "测试",
      "label.timeout": "超时",
      "label.updated": "更新",
      "label.version": "版本",
      "log.analysisComplete": "分析完成：返回 {count} 个候选仓库",
      "log.analysisFailed": "分析失败：{message}",
      "log.apiFailed": "本地 API 调用失败：{message}",
      "log.callAnalyze": "正在调用本地 API：/api/analyze",
      "log.callReport": "正在生成报告：/api/report",
      "log.demoCandidates": "已载入 3 个演示候选仓库。",
      "log.demoMode": "当前通过 file:// 打开，未连接本地后端，使用演示数据。",
      "log.demoQueries": "已生成演示搜索策略。",
      "log.demoReport": "已生成演示报告。",
      "log.localizationComplete": "显示文本已翻译。",
      "log.localizationFailed": "显示文本翻译失败：{message}",
      "log.localizationSkipped": "未执行显示文本翻译：{reason}",
      "log.reportComplete": "报告已生成",
      "log.reportFailed": "报告生成失败：{message}",
      "log.startServerHint": "请确认已运行：py -3.14 scripts\\serve_frontend.py",
      "nav.analyze": "分析",
      "nav.reports": "报告",
      "nav.settings": "设置",
      "option.disabled": "关闭",
      "option.llm": "LLM",
      "option.rules": "规则",
      "report.candidates": "3. 候选总览",
      "report.capabilities": "5. 能力对比",
      "report.conclusion": "8. 结论",
      "report.generatedAt": "生成时间",
      "report.idea": "1. 用户想法",
      "report.implementationSignals": "6. 实现信号",
      "report.missingSkillCards": "以下候选未生成能力卡：{repos}。",
      "report.noCandidates": "暂无候选仓库。",
      "report.noCapabilityCards": "当前没有可用于能力对比的能力卡。请提高能力卡数量或重新分析。",
      "report.noQueries": "暂无搜索策略。",
      "report.noSignalCards": "当前没有可用于实现信号对比的能力卡。请提高能力卡数量或重新分析。",
      "report.noSkillCards": "当前分析没有生成能力卡。请启用“生成能力卡”并重新分析。",
      "report.queries": "2. 搜索策略",
      "report.recommendationFallback": "先完成仓库搜索和能力卡抽取，再判断是否自研。",
      "report.reuse": "7. 复用与自研",
      "report.skillCards": "4. Top 项目能力卡",
      "report.topCandidate": "Top 候选：{repo}，当前展示评分 {score}。",
      "report.unavailableCapabilities": "该候选未生成能力卡，无法列出可复用模块。",
      "report.unavailableGaps": "该候选未生成能力卡，无法列出差异化机会。",
      "report.reusableModules": "可复用模块：{items}。",
      "report.gaps": "差异化机会：{items}。",
      "report.reuseHigh": "重复造轮子风险较高，建议先评估复用或 fork。",
      "report.reuseLow": "需要更多证据，建议人工复核后再决策。",
      "report.recommendReuse": "优先复用或 fork {repo}，再针对缺口做人工复核。",
      "report.recommendReview": "暂不直接复用 {repo}，建议继续扩展搜索或人工复核关键能力。",
      "section.candidates": "候选仓库",
      "section.projectResearch": "项目调研",
      "section.runningAnalysis": "分析中",
      "section.reportNav": "报告目录",
      "section.reviewedCandidates": "已评审 {count} 个匹配项目",
      "section.setupIntro": "输入一个项目想法，快速得到 GitHub 候选、能力卡、评分和复用建议。",
      "section.settingsIntro": "这里展示当前本地运行配置。真实密钥只从 .env 或环境变量读取，界面不会完整显示。",
      "status.apiChecking": "检查中",
      "status.apiConnected": "已连接",
      "status.apiDemo": "演示模式",
      "status.apiUnavailable": "不可用",
      "status.apiUnhealthy": "异常",
      "status.available": "可运行",
      "status.enabled": "已启用",
      "status.githubAnonymous": "匿名/无 Token",
      "status.githubPending": "待检测",
      "status.githubToken": "Token 已配置",
      "status.llmConfigured": "已配置",
      "status.llmIncomplete": "未完整配置",
      "status.llmPending": "待检测",
      "status.noSkillCard": "未生成能力卡",
      "status.notConnected": "未连接",
      "status.notExtracted": "未抽取",
      "status.passed": "通过",
      "status.pendingReport": "尚未生成",
      "status.success": "成功",
      "status.translating": "翻译中",
      "status.unknown": "未知",
      "step.capabilityCard": "能力卡",
      "step.candidateReview": "候选评审",
      "step.githubSearch": "GitHub 搜索",
      "step.queryStrategy": "生成搜索策略",
      "step.report": "报告",
      "table.coreCapabilities": "核心能力",
      "table.decision": "决策",
      "table.deployment": "部署",
      "table.docs": "文档",
      "table.inputs": "输入",
      "table.interfaces": "接口",
      "table.model": "模型",
      "table.notSupported": "不支持",
      "table.outputs": "输出",
      "table.repo": "仓库",
      "table.review": "评审",
      "table.score": "评分",
      "table.suitableFor": "适合场景",
      "ui.apiDemoHint": "当前通过本地文件打开，只能使用演示数据。要连接后端，请运行 py -3.14 scripts\\serve_frontend.py 后访问 http://127.0.0.1:8787/。",
      "ui.apiLiveHint": "已连接本地后端。开始分析会调用现有 Python 服务、GitHub provider 和 LLM provider。",
      "ui.apiLoadingHint": "正在检测本地后端连接。",
      "value.modelFromEnv": "来自 .env",
      "ui.apiMissingHint": "无法连接本地 API。请确认已运行 py -3.14 scripts\\serve_frontend.py。",
    },
    en: {
      "action.cancel": "Cancel",
      "action.copyJson": "Copy JSON",
      "action.exportMarkdown": "Export Markdown",
      "action.generateReport": "Generate Report",
      "action.loadSample": "Load Sample",
      "action.openDirectory": "Open Directory",
      "action.refreshReport": "Refresh Report",
      "action.rerun": "Run Again",
      "action.run": "Start Analysis",
      "action.viewSkillCard": "View Skill Card",
      "action.testCompletion": "Test Completion",
      "action.testConnection": "Test Connection",
      "action.clearCache": "Clear Cache",
      "action.showOriginal": "Original",
      "action.translate": "Translate",
      "candidate.noDescription": "No description.",
      "candidate.original": "Original",
      "decision.keep": "Keep",
      "decision.reject": "Reject",
      "decision.review": "Review",
      "decision.unreviewed": "Unreviewed",
      "detail.back": "Back to candidates",
      "detail.capabilityProfile": "Capability Profile",
      "detail.confidence": "Confidence {value}",
      "detail.coreCapabilities": "Core Capabilities",
      "detail.evidence": "Evidence",
      "detail.limitations": "Limitations",
      "detail.noEvidence": "No evidence",
      "detail.noEvidenceBody": "This candidate has no skill card or evidence snippet yet.",
      "detail.noLimitations": "No limitation details.",
      "detail.noOptionalCapabilities": "No optional capabilities.",
      "detail.noSkillCard": "No skill card yet.",
      "detail.optionalCapabilities": "Optional Capabilities",
      "detail.scoreBreakdown": "Score Breakdown",
      "field.cardLimit": "Skill Cards",
      "field.extractCards": "Generate skill cards",
      "field.idea": "Project Idea",
      "field.language": "Display Language",
      "field.maxRepos": "Candidates",
      "field.queryMode": "Search Strategy",
      "field.reviewMode": "Candidate Review",
      "field.useCache": "Use cache",
      "filter.all": "All",
      "filter.keep": "Keep",
      "filter.reject": "Reject",
      "filter.review": "Review",
      "heading.analyze": "Open-source reuse analysis workbench",
      "heading.currentCandidate": "Current Candidate",
      "heading.runConfig": "Run Configuration",
      "heading.runEnvironment": "Runtime Environment",
      "heading.runtimeChecks": "Runtime Checks",
      "heading.cache": "Cache",
      "heading.report": "RepoRadar Research Report",
      "heading.settings": "Settings",
      "heading.skillCard": "Repository Skill Card",
      "label.activity": "Activity",
      "label.apiBase": "API Base",
      "label.categories": "Categories",
      "label.cacheDir": "Cache directory",
      "label.collectionCache": "Repository collection cache",
      "label.deployment": "Deployment",
      "label.docs": "Docs",
      "label.inputs": "Inputs",
      "label.interfaces": "Interfaces",
      "label.language": "Language",
      "label.license": "License",
      "label.modelProviders": "Model providers",
      "label.model": "Model",
      "label.provider": "Provider",
      "label.outputs": "Outputs",
      "label.overall": "Overall",
      "label.recentLiveSmoke": "Recent live smoke",
      "label.recentReportExport": "Recent report export",
      "label.relevance": "Relevance",
      "label.reuse": "Reuse",
      "label.searchCache": "Search cache",
      "label.score": "Score",
      "label.skillCardCache": "Skill-card cache",
      "label.stars": "Stars",
      "label.status": "Status",
      "label.streaming": "Streaming",
      "label.tests": "Tests",
      "label.timeout": "Timeout",
      "label.updated": "Updated",
      "label.version": "Version",
      "log.analysisComplete": "Analysis complete: {count} candidates returned",
      "log.analysisFailed": "Analysis failed: {message}",
      "log.apiFailed": "Local API call failed: {message}",
      "log.callAnalyze": "Calling local API: /api/analyze",
      "log.callReport": "Generating report: /api/report",
      "log.demoCandidates": "Loaded 3 demo candidate repositories.",
      "log.demoMode": "Opened via file://, local backend is not connected. Using demo data.",
      "log.demoQueries": "Demo search strategy generated.",
      "log.demoReport": "Demo report generated.",
      "log.localizationComplete": "Display text localized.",
      "log.localizationFailed": "Display localization failed: {message}",
      "log.localizationSkipped": "Display localization was skipped: {reason}",
      "log.reportComplete": "Report generated",
      "log.reportFailed": "Report generation failed: {message}",
      "log.startServerHint": "Confirm that py -3.14 scripts\\serve_frontend.py is running",
      "nav.analyze": "Analyze",
      "nav.reports": "Reports",
      "nav.settings": "Settings",
      "option.disabled": "Off",
      "option.llm": "LLM",
      "option.rules": "Rules",
      "report.candidates": "3. Candidate Overview",
      "report.capabilities": "5. Capability Comparison",
      "report.conclusion": "8. Conclusion",
      "report.generatedAt": "Generated At",
      "report.idea": "1. User Idea",
      "report.implementationSignals": "6. Implementation Signals",
      "report.missingSkillCards": "Skill cards were not generated for: {repos}.",
      "report.noCandidates": "No candidate repositories.",
      "report.noCapabilityCards": "No generated skill cards are available for capability comparison. Increase the skill-card limit or rerun.",
      "report.noQueries": "No search queries.",
      "report.noSignalCards": "No generated skill cards are available for implementation signals. Increase the skill-card limit or rerun.",
      "report.noSkillCards": "This analysis did not generate skill cards. Enable skill-card generation and rerun.",
      "report.queries": "2. Search Strategy",
      "report.recommendationFallback": "Search repositories and extract skill cards before deciding whether to build.",
      "report.reuse": "7. Reuse vs Build",
      "report.skillCards": "4. Top Project Skill Cards",
      "report.topCandidate": "Top candidate: {repo}, shown score {score}.",
      "report.unavailableCapabilities": "This candidate has no skill card, so reusable modules cannot be listed.",
      "report.unavailableGaps": "This candidate has no skill card, so differentiation gaps cannot be listed.",
      "report.reusableModules": "Reusable modules: {items}.",
      "report.gaps": "Differentiation opportunities: {items}.",
      "report.reuseHigh": "The duplicate-build risk is high. Evaluate reuse or fork first.",
      "report.reuseLow": "More evidence is needed. Review manually before deciding.",
      "report.recommendReuse": "Prefer reusing or forking {repo}, then manually review remaining gaps.",
      "report.recommendReview": "Do not directly reuse {repo} yet. Expand search or manually review key capabilities.",
      "section.candidates": "Candidate Repositories",
      "section.projectResearch": "Project Research",
      "section.runningAnalysis": "Analyzing",
      "section.reportNav": "Report Contents",
      "section.reviewedCandidates": "{count} matching projects reviewed",
      "section.setupIntro": "Enter a project idea to get GitHub candidates, skill cards, scores, and reuse guidance.",
      "section.settingsIntro": "This page shows the local runtime configuration. Real secrets are read only from .env or environment variables and are never fully displayed.",
      "status.apiChecking": "Checking",
      "status.apiConnected": "Connected",
      "status.apiDemo": "Demo mode",
      "status.apiUnavailable": "Unavailable",
      "status.apiUnhealthy": "Unhealthy",
      "status.available": "Available",
      "status.enabled": "Enabled",
      "status.githubAnonymous": "Anonymous/no token",
      "status.githubPending": "Pending",
      "status.githubToken": "Token configured",
      "status.llmConfigured": "Configured",
      "status.llmIncomplete": "Incomplete",
      "status.llmPending": "Pending",
      "status.noSkillCard": "No skill card",
      "status.notConnected": "Not connected",
      "status.notExtracted": "Not extracted",
      "status.passed": "Passed",
      "status.pendingReport": "Not generated",
      "status.success": "Success",
      "status.translating": "Translating",
      "status.unknown": "Unknown",
      "step.capabilityCard": "Skill Cards",
      "step.candidateReview": "Candidate Review",
      "step.githubSearch": "GitHub Search",
      "step.queryStrategy": "Build Search Strategy",
      "step.report": "Report",
      "table.coreCapabilities": "Core Capabilities",
      "table.decision": "Decision",
      "table.deployment": "Deployment",
      "table.docs": "Docs",
      "table.inputs": "Inputs",
      "table.interfaces": "Interfaces",
      "table.model": "Model",
      "table.notSupported": "Not Supported",
      "table.outputs": "Outputs",
      "table.repo": "Repo",
      "table.review": "Review",
      "table.score": "Score",
      "table.suitableFor": "Suitable For",
      "ui.apiDemoHint": "This page is opened from a local file and can only use demo data. To connect the backend, run py -3.14 scripts\\serve_frontend.py and visit http://127.0.0.1:8787/.",
      "ui.apiLiveHint": "Connected to the local backend. Analysis will call the existing Python services, GitHub provider, and LLM provider.",
      "ui.apiLoadingHint": "Checking local backend connection.",
      "value.modelFromEnv": "From .env",
      "ui.apiMissingHint": "Cannot connect to the local API. Confirm that py -3.14 scripts\\serve_frontend.py is running.",
    },
  };

  let currentLanguage = "zh";

  function normalizeLanguage(language) {
    return language === "en" ? "en" : "zh";
  }

  function setLanguage(language) {
    currentLanguage = normalizeLanguage(language);
    document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
    applyStaticLabels(document);
  }

  function getLanguage() {
    return currentLanguage;
  }

  function t(key, params) {
    const dictionary = dictionaries[currentLanguage] || dictionaries.zh;
    const template = dictionary[key] || dictionaries.zh[key] || key;
    return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, name) => {
      if (!params || params[name] === undefined || params[name] === null) {
        return "";
      }
      return String(params[name]);
    });
  }

  function applyStaticLabels(root) {
    root.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = t(element.dataset.i18n);
    });
  }

  function decisionLabel(decision) {
    return t(`decision.${decision || "unreviewed"}`);
  }

  function localizeFromSources(sources, fields, fallback) {
    const objects = sources.filter((source) => source && typeof source === "object");
    for (const source of objects) {
      for (const field of fields) {
        const localized = localizedScalar(source, field, currentLanguage);
        if (localized) {
          return { text: localized, isOriginal: false };
        }
      }
    }
    for (const source of objects) {
      for (const field of fields) {
        const value = asText(source[field]);
        if (value) {
          return { text: value, isOriginal: isOriginalForLanguage(value, currentLanguage) };
        }
      }
    }
    return { text: fallback || "", isOriginal: false };
  }

  function localizeList(source, field) {
    if (!source || typeof source !== "object") {
      return [];
    }
    const exact = source[`${field}_${currentLanguage}`];
    if (Array.isArray(exact)) {
      return exact.filter(Boolean).map(String);
    }
    const i18n = source[`${field}_i18n`] || source[`${field}_localized`];
    if (i18n && typeof i18n === "object" && Array.isArray(i18n[currentLanguage])) {
      return i18n[currentLanguage].filter(Boolean).map(String);
    }
    const values = source[field];
    return Array.isArray(values) ? values.filter(Boolean).map(String) : [];
  }

  function localizedScalar(source, field, language) {
    const direct = asText(source[`${field}_${language}`]);
    if (direct) {
      return direct;
    }
    const i18n = source[`${field}_i18n`] || source[`${field}_localized`];
    if (i18n && typeof i18n === "object") {
      return asText(i18n[language]);
    }
    return "";
  }

  function asText(value) {
    return typeof value === "string" && value.trim() ? value.trim() : "";
  }

  function isOriginalForLanguage(value, language) {
    if (language === "zh") {
      return /[A-Za-z]/.test(value) && !/[\u3400-\u9FFF]/.test(value);
    }
    return /[\u3400-\u9FFF]/.test(value);
  }

  global.RepoRadarI18n = {
    applyStaticLabels,
    decisionLabel,
    getLanguage,
    localizeFromSources,
    localizeList,
    setLanguage,
    t,
  };
})(window);
