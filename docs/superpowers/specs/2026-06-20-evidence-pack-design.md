# MiniCode Evidence Pack Design

## Goal

Strengthen MiniCode's interview evidence without changing v0.1.1 runtime
behavior.

## Deliverables

- four real Mock-mode CLI output excerpts in the README;
- a standalone architecture SVG suitable for GitHub and interview slides;
- the complete MiniCode MVP SPEC v0.1.1 archived at
  `docs/spec-v0.1.1.md`;
- corrected GitHub Release notes with real Markdown newlines.

## Evidence rules

README examples must come from current CLI execution against
`examples/sample_project`. Long code-search process sections may be shortened
with an explicit omission marker, but task type, representative tool calls,
analysis headings, risk result, and memory behavior must remain faithful.

The architecture image must reflect the implemented modules and distinguish
`app_root` from `workspace`.

The archived SPEC is copied verbatim from the user-approved source document.
No runtime code, routing behavior, safety policy, or output contract changes in
this pass.

## Verification

- repository presentation tests assert all four demo headings and assets exist;
- XML parsing validates the architecture SVG;
- README examples match the four supported skill names;
- full Python tests and GitHub Actions pass;
- Release notes render as actual Markdown paragraphs and lists.
