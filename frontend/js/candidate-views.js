// Candidate list, summary, and detail rendering for the frontend.
(function (global) {
  "use strict";

  const formatters = global.RepoRadarFormatters;
  const i18n = global.RepoRadarI18n;

  const repoTableBody = document.querySelector("#repo-table-body");
  const resultsTitle = document.querySelector("#results-title");

  function renderTable(candidates, selectedFullName, currentFilter, handlers) {
    const onSelect = typeof handlers === "function" ? handlers : handlers?.onSelect;
    const onDescriptionToggle = typeof handlers === "object" ? handlers.onDescriptionToggle : null;
    const rows = candidates.filter((candidate) => currentFilter === "all" || candidate.decision === currentFilter);
    resultsTitle.textContent = i18n.t("section.reviewedCandidates", { count: candidates.length });
    repoTableBody.innerHTML = "";
    if (!rows.length) {
      repoTableBody.innerHTML = `<tr><td colspan="6">${escape(i18n.t("report.noCandidates"))}</td></tr>`;
      return;
    }

    rows.forEach((candidate) => {
      const row = document.createElement("tr");
      row.className = candidate.fullName === selectedFullName ? "is-selected" : "";
      row.innerHTML = `
        <td>
          <div class="repo-name">
            <strong>${escape(candidate.fullName)}</strong>
            <div class="repo-description">
              <span>${escape(candidate.description)}${sourceChip(candidate.descriptionIsOriginal)}</span>
              ${descriptionActionButton(candidate)}
            </div>
          </div>
        </td>
        <td>${decisionBadge(candidate.decision)}</td>
        <td>${candidate.score.toFixed(3)}</td>
        <td>${candidate.stars.toLocaleString()}</td>
        <td>${escape(candidate.language)}</td>
        <td>${escape(candidate.updated)}</td>
      `;
      const descriptionButton = row.querySelector("[data-description-action]");
      if (descriptionButton && onDescriptionToggle) {
        descriptionButton.addEventListener("click", (event) => {
          event.stopPropagation();
          onDescriptionToggle(candidate.fullName);
        });
      }
      row.addEventListener("click", () => onSelect?.(candidate.fullName));
      repoTableBody.appendChild(row);
    });
  }

  function renderSummary(candidate) {
    document.querySelector("#selected-repo-name").textContent = candidate.fullName;
    document.querySelector("#selected-repo-summary").innerHTML =
      `${escape(candidate.description)}${sourceChip(candidate.descriptionIsOriginal)}`;
    document.querySelector("#selected-overall").textContent = candidate.score.toFixed(3);
    document.querySelector("#selected-relevance").textContent = candidate.relevance.toFixed(3);
    document.querySelector("#selected-reuse").textContent = candidate.reuse.toFixed(3);
    document.querySelector("#selected-docs").textContent = candidate.docs.toFixed(3);
  }

  function renderDetail(candidate) {
    document.querySelector("#detail-title").textContent = candidate.fullName;
    document.querySelector("#detail-repo-url").textContent = candidate.url.replace(/^https?:\/\//, "") || candidate.fullName;
    document.querySelector("#detail-repo-description").innerHTML =
      `${escape(candidate.description)}${sourceChip(candidate.descriptionIsOriginal)}`;
    document.querySelector(".confidence-pill").textContent = i18n.t("detail.confidence", {
      value: formatters.numeric(candidate.card.confidence, 0).toFixed(3),
    });
    document.querySelector("#detail-tags").innerHTML = [candidate.language, candidate.license, ...candidate.topics]
      .filter(Boolean)
      .slice(0, 6)
      .map((tag) => `<span>${escape(tag)}</span>`)
      .join("");
    renderScoreList(candidate);
    renderEvidence(candidate.card);
    renderSkillProperties(candidate);
    renderList("#core-capabilities", cardList(candidate, "core_capabilities"), [i18n.t("detail.noSkillCard")]);
    renderList("#optional-capabilities", cardList(candidate, "optional_capabilities"), [i18n.t("detail.noOptionalCapabilities")]);
    renderList("#limitations-list", cardList(candidate, "limitations", "not_supported"), [i18n.t("detail.noLimitations")]);
  }

  function renderScoreList(candidate) {
    const scoreRows = [
      [i18n.t("label.overall"), candidate.score],
      [i18n.t("label.relevance"), candidate.relevance],
      [i18n.t("label.reuse"), candidate.reuse],
      [i18n.t("label.docs"), candidate.docs],
      [i18n.t("label.stars"), Math.min(candidate.stars / 5000, 1)],
    ];
    const scoreList = document.querySelector("#score-list");
    scoreList.innerHTML = "";
    scoreRows.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "score-row";
      row.innerHTML = `
        <span>${escape(label)}</span>
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
      container.innerHTML = `<span>${escape(i18n.t("detail.noEvidence"))}</span><blockquote>${escape(i18n.t("detail.noEvidenceBody"))}</blockquote>`;
      return;
    }
    container.innerHTML = `
      <span>${escape(evidence.source || i18n.t("status.unknown"))}</span>
      <blockquote>${escape(evidence.quote || "")}</blockquote>
      <strong>${escape(i18n.t("detail.confidence", { value: formatters.numeric(evidence.confidence, 0).toFixed(2) }))}</strong>
    `;
  }

  function renderSkillProperties(candidate) {
    const rows = [
      [i18n.t("label.categories"), joinCardList(candidate, "categories")],
      [i18n.t("label.inputs"), joinCardList(candidate, "input_formats")],
      [i18n.t("label.outputs"), joinCardList(candidate, "output_formats")],
      [i18n.t("label.interfaces"), joinCardList(candidate, "interfaces")],
      [i18n.t("label.modelProviders"), joinCardList(candidate, "model_providers")],
      [i18n.t("label.deployment"), joinCardList(candidate, "deployment")],
    ];
    document.querySelector("#skill-properties").innerHTML = rows
      .map(([label, value]) => `<div><span>${escape(label)}</span><strong>${escape(value)}</strong></div>`)
      .join("");
  }

  function renderList(selector, items, fallback) {
    const values = Array.isArray(items) && items.length ? items : fallback;
    document.querySelector(selector).innerHTML = values.map((item) => `<li>${escape(item)}</li>`).join("");
  }

  function cardList(candidate, primaryField, fallbackField) {
    const primary = formatters.localizedCardList(candidate, primaryField);
    if (primary.length || !fallbackField) {
      return primary;
    }
    return formatters.localizedCardList(candidate, fallbackField);
  }

  function joinCardList(candidate, field) {
    if (!candidate.hasSkillCard) {
      return i18n.t("status.noSkillCard");
    }
    return formatters.joinList(formatters.localizedCardList(candidate, field), {
      missing: i18n.t("status.notExtracted"),
    });
  }

  function decisionBadge(decision) {
    const badgeClass = decision === "keep" ? "badge-success" : decision === "reject" ? "badge-reject" : "badge-warn";
    return `<span class="badge ${badgeClass}">${escape(i18n.decisionLabel(decision))}</span>`;
  }

  function sourceChip(isOriginal) {
    return isOriginal ? ` <em class="source-chip">${escape(i18n.t("candidate.original"))}</em>` : "";
  }

  function descriptionActionButton(candidate) {
    const action = candidate.descriptionAction;
    if (!action?.visible) {
      return "";
    }
    const disabled = action.disabled ? " disabled" : "";
    const title = action.title ? ` title="${escape(action.title)}"` : "";
    return `<button class="inline-action" type="button" data-description-action="${escape(candidate.fullName)}"${disabled}${title}>${escape(action.label)}</button>`;
  }

  function escape(value) {
    return formatters.escapeHtml(value);
  }

  global.RepoRadarCandidateViews = {
    renderDetail,
    renderSummary,
    renderTable,
  };
})(window);
