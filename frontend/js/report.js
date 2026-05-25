// Report preview and Markdown rendering for normalized frontend candidates.
(function (global) {
  "use strict";

  const i18n = global.RepoRadarI18n;
  const formatters = global.RepoRadarFormatters;

  function renderReportDocument(payload, candidates, options) {
    const idea = payload.idea || options?.idea || "";
    const queries = Array.isArray(payload.queries) ? payload.queries : [];
    const topCandidate = candidates[0];
    const html = `
      <section id="report-idea">
        <h2>${escape(i18n.t("report.idea"))}</h2>
        <p>${escape(idea)}</p>
      </section>
      <section id="report-queries">
        <h2>${escape(i18n.t("report.queries"))}</h2>
        <div class="query-row">${renderQueries(queries)}</div>
      </section>
      <section id="report-candidates">
        <h2>${escape(i18n.t("report.candidates"))}</h2>
        ${renderCandidateTable(candidates)}
      </section>
      <section id="report-skill-cards">
        <h2>${escape(i18n.t("report.skillCards"))}</h2>
        ${renderSkillCardSummary(candidates)}
      </section>
      <section id="report-capabilities">
        <h2>${escape(i18n.t("report.capabilities"))}</h2>
        ${renderCapabilityTable(candidates)}
      </section>
      <section id="report-signals">
        <h2>${escape(i18n.t("report.implementationSignals"))}</h2>
        ${renderSignalTable(candidates)}
      </section>
      <section id="report-reuse">
        <h2>${escape(i18n.t("report.reuse"))}</h2>
        ${renderReuseAnalysis(topCandidate)}
      </section>
      <section id="report-recommendation">
        <h2>${escape(i18n.t("report.conclusion"))}</h2>
        <div class="recommendation">${escape(buildRecommendation(topCandidate))}</div>
      </section>
    `;
    return {
      html,
      markdown: buildFrontendMarkdown(payload, candidates, idea),
    };
  }

  function renderQueries(queries) {
    if (!queries.length) {
      return `<span>${escape(i18n.t("report.noQueries"))}</span>`;
    }
    return queries.map((query) => `<code>${escape(query)}</code>`).join("");
  }

  function renderCandidateTable(candidates) {
    if (!candidates.length) {
      return `<p>${escape(i18n.t("report.noCandidates"))}</p>`;
    }
    const rows = candidates
      .map(
        (candidate) => `<tr>
          <td>${escape(candidate.fullName)}</td>
          <td>${decisionBadge(candidate.decision)}</td>
          <td>${escape(candidate.rationale || i18n.t("status.notExtracted"))}</td>
          <td>${candidate.score.toFixed(3)}</td>
          <td>${candidate.reuse.toFixed(3)}</td>
          <td>${candidate.docs.toFixed(3)}</td>
        </tr>`,
      )
      .join("");
    return `<table class="report-table">
      <thead><tr><th>${escape(i18n.t("table.repo"))}</th><th>${escape(i18n.t("table.decision"))}</th><th>${escape(i18n.t("table.review"))}</th><th>${escape(i18n.t("table.score"))}</th><th>${escape(i18n.t("label.reuse"))}</th><th>${escape(i18n.t("table.docs"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  function renderSkillCardSummary(candidates) {
    const cards = candidates.filter((candidate) => candidate.hasSkillCard);
    const missingNote = renderMissingSkillCardNote(candidates);
    if (!cards.length) {
      return `<p class="report-note">${escape(i18n.t("report.noSkillCards"))}</p>${missingNote}`;
    }
    return (
      cards
        .slice(0, 3)
        .map((candidate) => {
          return `<article class="inline-skill">
            <strong>${escape(candidate.fullName)}</strong>
            <span>${escape(i18n.t("label.inputs"))}: ${escape(cardList(candidate, "input_formats"))}</span>
            <span>${escape(i18n.t("label.outputs"))}: ${escape(cardList(candidate, "output_formats"))}</span>
            <span>${escape(i18n.t("label.interfaces"))}: ${escape(cardList(candidate, "interfaces"))}</span>
          </article>`;
        })
        .join("") + missingNote
    );
  }

  function renderCapabilityTable(candidates) {
    const cards = candidates.filter((candidate) => candidate.hasSkillCard);
    if (!cards.length) {
      return `<p class="report-note">${escape(i18n.t("report.noCapabilityCards"))}</p>${renderMissingSkillCardNote(candidates)}`;
    }
    const rows = cards
      .map(
        (candidate) => `<tr>
          <td>${escape(candidate.fullName)}</td>
          <td>${escape(cardList(candidate, "input_formats"))}</td>
          <td>${escape(cardList(candidate, "output_formats"))}</td>
          <td>${escape(cardList(candidate, "interfaces"))}</td>
          <td>${escape(cardList(candidate, "core_capabilities", 3))}</td>
          <td>${escape(cardList(candidate, "limitations", 2))}</td>
        </tr>`,
      )
      .join("");
    return `<table class="report-table">
      <thead><tr><th>${escape(i18n.t("table.repo"))}</th><th>${escape(i18n.t("table.inputs"))}</th><th>${escape(i18n.t("table.outputs"))}</th><th>${escape(i18n.t("table.interfaces"))}</th><th>${escape(i18n.t("table.coreCapabilities"))}</th><th>${escape(i18n.t("detail.limitations"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>${renderMissingSkillCardNote(candidates)}`;
  }

  function renderSignalTable(candidates) {
    const cards = candidates.filter((candidate) => candidate.hasSkillCard);
    if (!cards.length) {
      return `<p class="report-note">${escape(i18n.t("report.noSignalCards"))}</p>${renderMissingSkillCardNote(candidates)}`;
    }
    const rows = cards
      .map(
        (candidate) => `<tr>
          <td>${escape(candidate.fullName)}</td>
          <td>${escape(cardList(candidate, "model_providers"))}</td>
          <td>${escape(cardList(candidate, "deployment"))}</td>
          <td>${escape(cardList(candidate, "suitable_for"))}</td>
          <td>${escape(cardList(candidate, "not_supported"))}</td>
        </tr>`,
      )
      .join("");
    return `<table class="report-table">
      <thead><tr><th>${escape(i18n.t("table.repo"))}</th><th>${escape(i18n.t("table.model"))}</th><th>${escape(i18n.t("table.deployment"))}</th><th>${escape(i18n.t("table.suitableFor"))}</th><th>${escape(i18n.t("table.notSupported"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>${renderMissingSkillCardNote(candidates)}`;
  }

  function renderReuseAnalysis(candidate) {
    if (!candidate) {
      return `<p>${escape(i18n.t("report.recommendationFallback"))}</p>`;
    }
    const lines = [
      i18n.t("report.topCandidate", {
        repo: candidate.fullName,
        score: candidate.score.toFixed(3),
      }),
    ];
    if (candidate.hasSkillCard) {
      lines.push(i18n.t("report.reusableModules", { items: cardList(candidate, "core_capabilities", 4) }));
      lines.push(i18n.t("report.gaps", { items: cardList(candidate, "not_supported", 4) }));
    } else {
      lines.push(i18n.t("report.unavailableCapabilities"));
      lines.push(i18n.t("report.unavailableGaps"));
    }
    lines.push(candidate.score >= 0.75 ? i18n.t("report.reuseHigh") : i18n.t("report.reuseLow"));
    return `<ul>${lines.map((line) => `<li>${escape(line)}</li>`).join("")}</ul>`;
  }

  function buildRecommendation(candidate) {
    if (!candidate) {
      return i18n.t("report.recommendationFallback");
    }
    if (candidate.score >= 0.75) {
      return i18n.t("report.recommendReuse", { repo: candidate.fullName });
    }
    return i18n.t("report.recommendReview", { repo: candidate.fullName });
  }

  function buildFrontendMarkdown(payload, candidates, idea) {
    const lines = [
      "# RepoRadar",
      "",
      `## ${i18n.t("report.idea").replace(/^\d+\.\s*/, "")}`,
      "",
      idea,
      "",
      `## ${i18n.t("report.queries").replace(/^\d+\.\s*/, "")}`,
      "",
      ...(payload.queries || []).map((query) => `- \`${query}\``),
      "",
      `## ${i18n.t("report.candidates").replace(/^\d+\.\s*/, "")}`,
      "",
      `| ${i18n.t("table.repo")} | ${i18n.t("table.decision")} | ${i18n.t("table.score")} | ${i18n.t("table.review")} |`,
      "| --- | --- | ---: | --- |",
      ...candidates.map(
        (candidate) =>
          `| ${candidate.fullName} | ${i18n.decisionLabel(candidate.decision)} | ${candidate.score.toFixed(3)} | ${candidate.rationale || ""} |`,
      ),
      "",
      `## ${i18n.t("report.conclusion").replace(/^\d+\.\s*/, "")}`,
      "",
      buildRecommendation(candidates[0]),
    ];
    return lines.join("\n") + "\n";
  }

  function renderMissingSkillCardNote(candidates) {
    const missing = candidates.filter((candidate) => !candidate.hasSkillCard).map((candidate) => candidate.fullName);
    if (!missing.length) {
      return "";
    }
    return `<p class="report-note">${escape(i18n.t("report.missingSkillCards", { repos: missing.join(", ") }))}</p>`;
  }

  function cardList(candidate, field, limit) {
    return formatters.joinList(formatters.localizedCardList(candidate, field), {
      limit: limit || 5,
      missing: i18n.t("status.notExtracted"),
    });
  }

  function decisionBadge(decision) {
    const badgeClass = decision === "keep" ? "badge-success" : decision === "reject" ? "badge-reject" : "badge-warn";
    return `<span class="badge ${badgeClass}">${escape(i18n.decisionLabel(decision))}</span>`;
  }

  function escape(value) {
    return formatters.escapeHtml(value);
  }

  global.RepoRadarReport = {
    buildRecommendation,
    renderReportDocument,
  };
})(window);
