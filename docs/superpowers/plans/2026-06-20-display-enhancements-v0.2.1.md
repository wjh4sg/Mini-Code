# MiniCode v0.2.1 Display Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a documentation-only presentation upgrade backed by one real Alibaba Cloud `deepseek-v4-flash` run.

**Architecture:** Keep the Agent and CLI behavior unchanged. Capture one real run through the existing OpenAI-compatible client, store a sanitized transcript, add repository-native SVG/docs, then update version metadata and README links under acceptance tests.

**Tech Stack:** Python 3.10 standard library, unittest, Markdown, SVG, setuptools/TOML, Alibaba Cloud Model Studio OpenAI-compatible API.

---

### Task 1: Lock the presentation contract

**Files:**
- Modify: `tests/test_cli_acceptance.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_minicode_cli.py`

- [x] Add assertions for version `0.2.1`, the three new documentation assets, README links, the real model name, required structured headings, and absence of secret/path markers.
- [x] Run `python -m unittest tests.test_cli_acceptance tests.test_packaging tests.test_minicode_cli -v`.
- [x] Confirm failure because version `0.2.1` and the new assets do not exist.

### Task 2: Capture and document the real run

**Files:**
- Create: `docs/real-llm-example.md`
- Create: `docs/cli-showcase.svg`
- Create: `docs/spec-v0.2.0.md`

- [x] Temporarily map `DASHSCOPE_API_KEY` to `MINICODE_API_KEY`, set the Alibaba Cloud compatible endpoint and `deepseek-v4-flash`, and run the fixed feature-planning query.
- [x] Reject the result if it contains the Mock fallback marker or a model-call failure.
- [x] Sanitize local absolute paths and record the command, date, execution trace, and model output in `docs/real-llm-example.md`.
- [x] Add a static terminal SVG showing existing `--help`, `doctor`, and permission-denial behavior.
- [x] Add the concise v0.2.0 delta specification inheriting the v0.1.1 safety boundary.

### Task 3: Integrate, version, and verify

**Files:**
- Modify: `README.md`
- Modify: `minicode_cli.py`
- Modify: `pyproject.toml`
- Modify: `docs/architecture.svg`

- [x] Update current version references to `0.2.1`.
- [x] Add the CLI showcase, doctor output, real-model excerpt, and links to the complete transcript and v0.2.0 delta spec.
- [x] Run focused tests and make them pass.
- [x] Run `python -m compileall -q .` and `python -m unittest discover -v`.
- [x] Perform an editable-install smoke test for `minicode --version` and `minicode doctor`.
- [x] Scan tracked changes for API keys, authorization headers, and machine-specific paths.
- [x] Commit the completed v0.2.1 presentation upgrade.
