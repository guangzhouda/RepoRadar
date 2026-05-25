// Demo payload used when the static page is opened without the local API.
(function (global) {
  "use strict";

  const sampleIdeas = {
    zh: "我想做一个把 EPUB/PDF 转成 TTS 音频，并生成同步字幕的工具。",
    en: "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles.",
  };

  const samplePayload = {
    phase: "frontend-demo",
    idea: sampleIdeas.zh,
    queries: ["epub pdf tts subtitle synchronized", "audiobook generator subtitle sync"],
    candidates: [
      {
        full_name: "denizsafak/abogen",
        url: "https://github.com/denizsafak/abogen",
        description_i18n: {
          zh: "从 EPUB、PDF 和文本生成有声书，并输出同步字幕。",
          en: "Generates audiobooks from EPUB, PDF, and text files, with synchronized subtitles.",
        },
        stars: 4545,
        forks: 288,
        language: "Python",
        license: "MIT",
        topics: ["audiobook", "TTS", "subtitle", "EPUB", "PDF"],
        pushed_at: "2026-05-24T12:27:28Z",
        relevance_score: 1,
        decision: "keep",
        rationale_i18n: {
          zh: "直接匹配 EPUB/PDF 转 TTS 和同步字幕需求。",
          en: "Directly matches the EPUB/PDF to TTS workflow and synchronized-subtitle requirement.",
        },
        skill_card: {
          repo: "denizsafak/abogen",
          name: "abogen",
          summary_i18n: {
            zh: "从 EPUB、PDF 和文本生成有声书，并输出同步字幕。",
            en: "Generates audiobooks from EPUB, PDF, and text files, with synchronized subtitles.",
          },
          categories_i18n: {
            zh: ["文本转语音", "有声书生成", "字幕同步"],
            en: ["text-to-speech", "audiobook generation", "subtitle synchronization"],
          },
          input_formats: ["EPUB", "PDF", "TXT", "Markdown", "SRT"],
          output_formats: ["WAV", "FLAC", "MP3", "OPUS", "M4B", "SRT"],
          interfaces: ["CLI", "Web", "API"],
          core_capabilities_i18n: {
            zh: ["文本转语音生成", "多格式电子书输入", "同步字幕生成", "按章节输出有声书", "批量队列处理"],
            en: [
              "text-to-speech generation",
              "multi-format ebook input",
              "synchronized subtitle generation",
              "chapter-based audiobook output",
              "batch queue processing",
            ],
          },
          optional_capabilities_i18n: {
            zh: ["LLM 文本规范化", "Audiobookshelf 集成", "GPU 加速"],
            en: ["LLM text normalization", "Audiobookshelf integration", "GPU acceleration"],
          },
          model_providers: ["Kokoro", "Supertonic"],
          deployment_i18n: {
            zh: ["pip", "docker", "自托管"],
            en: ["pip", "docker", "self-hosted"],
          },
          suitable_for_i18n: {
            zh: ["有声书生成", "内容创作", "无障碍阅读"],
            en: ["audiobook generation", "content creation", "accessible reading"],
          },
          not_supported_i18n: {
            zh: ["扫描 PDF OCR", "非英文词级字幕"],
            en: ["scanned-PDF OCR", "non-English word-level subtitles"],
          },
          limitations_i18n: {
            zh: ["词级字幕仅支持英文", "暂不支持扫描 PDF 的 OCR", "AMD GPU 加速依赖 Linux ROCm"],
            en: [
              "word-level subtitles are English-only",
              "scanned-PDF OCR is not supported",
              "AMD GPU acceleration depends on Linux ROCm",
            ],
          },
          evidence: [
            {
              source: "README.md",
              quote: "Supports dragging in ePub, PDF, text, Markdown, or subtitle files.",
              confidence: 0.95,
            },
          ],
          confidence: 0.9,
        },
      },
      {
        full_name: "lukaszliniewicz/Pandrator",
        url: "https://github.com/lukaszliniewicz/Pandrator",
        description_i18n: {
          zh: "将 PDF/EPUB 转成有声书，也支持字幕或视频配音工作流。",
          en: "Converts PDF/EPUB content into audiobooks and supports subtitle or dubbing workflows.",
        },
        stars: 561,
        forks: 41,
        language: "Python",
        license: "AGPL-3.0",
        topics: ["audiobook", "PDF", "EPUB", "subtitle", "dubbing"],
        pushed_at: "2026-05-22T02:08:17Z",
        relevance_score: 1,
        decision: "keep",
        rationale_i18n: {
          zh: "工作流相似，但当前演示未生成能力卡。",
          en: "The workflow is similar, but this demo run did not generate a skill card.",
        },
      },
      {
        full_name: "BoltzmannEntropy/MimikaStudio",
        url: "https://github.com/BoltzmannEntropy/MimikaStudio",
        description_i18n: {
          zh: "本地优先的有声书转换工具，具备 TTS 和声音克隆信号。",
          en: "A local-first audiobook conversion tool with TTS and voice-cloning signals.",
        },
        stars: 571,
        forks: 78,
        language: "Dart",
        license: "GPL-3.0",
        topics: ["audiobook", "TTS", "voice cloning"],
        pushed_at: "2026-04-01T10:38:10Z",
        relevance_score: 0.6,
        decision: "review",
        rationale_i18n: {
          zh: "字幕同步证据较弱，建议人工复核。",
          en: "Subtitle synchronization evidence is weak, so manual review is recommended.",
        },
      },
    ],
  };

  global.RepoRadarSampleData = {
    sampleIdeas,
    samplePayload,
  };
})(window);
