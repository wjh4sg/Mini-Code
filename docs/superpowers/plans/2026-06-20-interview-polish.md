# MiniCode Interview Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the completed MiniCode MVP into a public, evidence-rich GitHub portfolio project without changing its product scope.

**Architecture:** Keep the Python application unchanged except for runtime-memory repository hygiene. Add repository-native CI, documentation, and SVG presentation assets, then publish metadata and a release through GitHub.

**Tech Stack:** Python 3.10+, `unittest`, GitHub Actions, Markdown, SVG, GitHub CLI.

---

### Task 1: Keep Runtime Memory Out of Git

**Files:**
- Modify: `.gitignore`
- Delete: `data/memory.json`
- Create: `data/memory.example.json`
- Modify: `tests/test_cli_acceptance.py`

- [ ] Add a failing acceptance assertion that repeated CLI runs leave no tracked `data/memory.json` change.
- [ ] Run `python -m unittest tests.test_cli_acceptance -v` and confirm failure.
- [ ] Ignore `data/memory.json`, replace the tracked file with `data/memory.example.json`, and make the test restore/remove runtime memory according to its initial existence.
- [ ] Re-run the focused test and confirm it passes.
- [ ] Commit with `chore: keep runtime memory out of git`.

### Task 2: Add CI and Portfolio Documentation

**Files:**
- Create: `.github/workflows/tests.yml`
- Create: `docs/demo.svg`
- Modify: `README.md`
- Modify: `tests/test_cli_acceptance.py`

- [ ] Add failing README/repository assertions for the real clone URL, badges, demo visual, interview talking points, no placeholders, and CI workflow.
- [ ] Run the focused test and confirm failure.
- [ ] Add a Python 3.10/3.11/3.12 workflow running compileall and unittest.
- [ ] Create a terminal-style SVG from verified CLI output.
- [ ] Update README badges, links, evidence, visual, and interview section.
- [ ] Run focused and full tests.
- [ ] Commit with `docs: polish MiniCode for interviews`.

### Task 3: Publish the Interview-Ready Repository

**Files:**
- No application files.

- [ ] Push `codex/interview-polish`.
- [ ] Open a pull request to `main`.
- [ ] Verify GitHub Actions succeeds.
- [ ] Merge the pull request.
- [ ] Change repository visibility to public.
- [ ] Add repository topics: `coding-agent`, `python`, `cli`, `llm`, `developer-tools`, `ai-agent`.
- [ ] Create GitHub release `v0.1.1` from `main`.
- [ ] Verify the public repository, workflow, and release URLs.
