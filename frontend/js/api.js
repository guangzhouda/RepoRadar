// Local API access for the dependency-free frontend.
(function (global) {
  "use strict";

  function isApiMode() {
    return global.location.protocol === "http:" || global.location.protocol === "https:";
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

  async function checkHealth() {
    const response = await fetch("/api/health");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }

  global.RepoRadarApi = {
    checkHealth,
    isApiMode,
    requestJson,
  };
})(window);
