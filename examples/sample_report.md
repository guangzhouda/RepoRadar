# RepoRadar Research Report

## User Idea

Build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles.

## Search Strategy

- `epub pdf tts subtitle in:name,description,readme stars:>5 archived:false fork:false`

## Candidate Overview

| Repo | Decision | Score | Relevance | Maturity | Activity | Reuse | Docs | License |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [denizsafak/abogen](https://github.com/denizsafak/abogen) | keep | 0.878 | 0.910 | 0.730 | 1.000 | 0.800 | 0.937 | 1.000 |

## Top Project Skill Cards

### denizsafak/abogen

Converts ebook documents into generated audiobook output with subtitle-oriented evidence.

- Score: `0.878`
- Confidence: `0.840`
- Interfaces: cli
- Inputs: EPUB, PDF
- Outputs: MP3, SRT
- Core capabilities: ebook to speech audio, subtitle generation
- Limitations: PDF extraction quality depends on source documents
- Evidence: `README.md` - "Generate audiobooks from ebook files with subtitles."

## Capability Comparison

| Repo | Inputs | Outputs | Interfaces | Core Capabilities | Limitations |
| --- | --- | --- | --- | --- | --- |
| denizsafak/abogen | EPUB, PDF | MP3, SRT | cli | ebook to speech audio, subtitle generation | PDF extraction quality depends on source documents |

## Reuse vs Build Analysis

- Top candidate: `denizsafak/abogen` with score `0.878`.
- Reuse signals: maturity `0.730`, activity `1.000`, reusability `0.800`.
- Reusable modules: ebook to speech audio, subtitle generation.
- Differentiation opportunities: PDF extraction quality depends on source documents.
- Duplicate-wheel risk is high; inspect integration or fork paths before starting from scratch.

## Recommendation

Prefer reuse or fork of `denizsafak/abogen` first, then validate gaps with manual review.
