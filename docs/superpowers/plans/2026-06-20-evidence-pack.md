# MiniCode Evidence Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add verifiable interview evidence to MiniCode without modifying runtime behavior.

**Architecture:** Generate documentation from the existing CLI and approved SPEC, store visual assets under `docs/`, and validate repository presentation through the existing acceptance tests.

**Tech Stack:** Markdown, SVG, Python `unittest`, GitHub Actions, GitHub CLI.

---

### Task 1: Archive Product Evidence

- [ ] Add failing presentation assertions for four demo outputs,
  `docs/architecture.svg`, and `docs/spec-v0.1.1.md`.
- [ ] Run the focused test and confirm failure.
- [ ] Capture current Mock CLI output for all four skills.
- [ ] Add concise faithful excerpts to README.
- [ ] Add architecture SVG and complete SPEC archive.
- [ ] Run focused and full tests.
- [ ] Commit documentation changes.

### Task 2: Publish and Correct Release Notes

- [ ] Push a documentation branch and open a PR.
- [ ] Verify Python 3.10–3.12 CI succeeds.
- [ ] Merge the PR.
- [ ] Replace v0.1.1 Release notes using a Markdown file with real newlines.
- [ ] Verify public README assets, SPEC, and rendered Release body.
