// Shared frontend normalization and formatting helpers.
(function (global) {
  "use strict";

  const i18n = global.RepoRadarI18n;

  function normalizeCandidates(payload) {
    const rawCandidates = Array.isArray(payload?.candidates) ? payload.candidates : [];
    return rawCandidates.map((raw) => {
      const card = raw.skill_card && typeof raw.skill_card === "object" ? raw.skill_card : {};
      const score = numeric(raw.score, raw.overall_score, raw.relevance_score, card.confidence, 0);
      const description = i18n.localizeFromSources(
        [raw, card],
        ["description", "summary"],
        i18n.t("candidate.noDescription"),
      );
      const rationale = i18n.localizeFromSources([raw], ["rationale", "reject_reason"], "");
      const hasSkillCard = Boolean(card.repo);
      return {
        raw,
        card,
        hasSkillCard,
        skillCardError: raw.skill_card_error || "",
        fullName: raw.full_name || raw.fullName || "",
        url: raw.url || "",
        description: description.text,
        descriptionIsOriginal: description.isOriginal,
        decision: raw.decision || "unreviewed",
        rationale: rationale.text,
        rationaleIsOriginal: rationale.isOriginal,
        score,
        relevance: numeric(raw.relevance_score, score),
        reuse: hasSkillCard ? 1 : 0,
        docs: card.confidence ? Number(card.confidence) : 0,
        stars: Number(raw.stars || 0),
        forks: Number(raw.forks || 0),
        language: raw.language || i18n.t("status.unknown"),
        license: raw.license || "",
        updated: formatDate(raw.pushed_at || raw.updated || raw.updatedAt || ""),
        topics: Array.isArray(raw.topics) ? raw.topics : [],
      };
    });
  }

  function localizedCardList(candidate, field) {
    return i18n.localizeList(candidate?.card || {}, field);
  }

  function localizedCardText(candidate, fields, fallback) {
    return i18n.localizeFromSources([candidate?.card || {}], fields, fallback).text;
  }

  function joinList(items, options) {
    const config = options || {};
    const limit = Number.isFinite(Number(config.limit)) ? Number(config.limit) : 5;
    const missing = config.missing || i18n.t("status.notExtracted");
    const values = Array.isArray(items) ? items.filter(Boolean).map(String) : [];
    if (!values.length) {
      return missing;
    }
    const separator = i18n.getLanguage() === "zh" ? "、" : ", ";
    return values.slice(0, limit).join(separator);
  }

  function formatDate(value) {
    if (!value) {
      return i18n.t("status.unknown");
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    const locale = i18n.getLanguage() === "zh" ? "zh-CN" : "en-US";
    return parsed.toLocaleDateString(locale, { month: "short", day: "numeric" });
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

  global.RepoRadarFormatters = {
    clonePayload,
    escapeHtml,
    joinList,
    localizedCardList,
    localizedCardText,
    normalizeCandidates,
    numberValue,
    numeric,
  };
})(window);
