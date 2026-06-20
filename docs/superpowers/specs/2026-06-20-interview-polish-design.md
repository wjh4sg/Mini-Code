# MiniCode Interview Polish Design

## Goal

Make the completed MiniCode MVP suitable for a recruiter or interviewer to
evaluate directly from GitHub, without expanding the v0.1.1 product scope.

## Chosen approach

Use a minimal engineering-polish pass:

- add GitHub Actions for Python 3.10, 3.11, and 3.12;
- improve the README with real repository links, badges, proof points, a
  terminal-style demo image, and interview talking points;
- keep runtime task history out of Git while retaining a committed example;
- publish the repository, add focused topics, and create a v0.1.1 release.

This is preferred over building a separate portfolio website or adding new
agent capabilities because the project already demonstrates its core technical
story. The remaining gap is evidence and presentation, not functionality.

## Runtime data

`data/memory.json` becomes a generated runtime file and is ignored by Git.
`data/memory.example.json` remains committed as the documented empty structure.
`MemoryWriter` continues to create `data/memory.json` automatically.

Tests must restore or remove runtime memory after CLI acceptance runs so the
working tree remains clean.

## Continuous integration

Add one GitHub Actions workflow that runs on pushes and pull requests to main.
The matrix covers Python 3.10, 3.11, and 3.12 and executes:

```text
python -m compileall -q .
python -m unittest discover -v
```

No dependency-install step is required because MiniCode uses the standard
library.

## README presentation

The README will:

- use the real clone URL;
- display Python, test, license, and release badges;
- show an actual terminal-style demo visual;
- summarize the architecture and safety boundary near the top;
- include verified test counts and four demo commands;
- add a concise “interview talking points” section.

The demo visual is a repository-native SVG based on real CLI output, not an
invented product UI.

## Repository metadata

After the documentation PR is merged:

- change visibility from private to public;
- add topics such as `coding-agent`, `python`, `cli`, `llm`, and
  `developer-tools`;
- create a `v0.1.1` GitHub release from main.

## Verification

- all local tests pass;
- CI workflow syntax is valid YAML and runs successfully on GitHub;
- repeated CLI acceptance tests leave no tracked changes;
- README contains no placeholders;
- the public repository and release are reachable without authentication.
