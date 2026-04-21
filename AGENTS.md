# AGENTS.md

This repository builds a local research knowledge forest from papers on `translate.icydev.cn`.

## Scope

- Treat `translate.icydev.cn` as a read-only source.
- Keep `outputs/papers/` as the local normalized knowledge base.
- Treat `outputs/meta/`, `outputs/papers/`, `outputs/raw/`, `outputs/fetch/`, and `outputs/site/` as generated artifacts that can be rebuilt locally.
- Default to Chinese for human-facing summaries and labels, but keep paper titles, venue names, method names, dataset names, and URLs in their original form.

## Repository Map

- `scripts/`: stdlib-only Python entrypoints for fetch, canonical assembly, registry rebuild, site-derived build, and site rendering.
- `references/`: schema and rendering contracts. Read these before changing record structure or output shape.
- `outputs/meta/`: per-paper agent-native meta artifacts used before final paper assembly.
- `outputs/papers/`: normalized per-paper JSON records kept for local analysis and site generation.
- `outputs/raw/`: raw staged payloads fetched from the translate service.
- `outputs/fetch/`: fetch manifests such as `latest-fetch.json`.
- `outputs/site/`: generated Markdown/HTML reading site.
- `state/`: local runtime state such as the dedupe registry.
- `agents/openai.yaml`: agent-facing metadata for this repo.
- `SKILL.md`: higher-level workflow guidance for the Codex skill version of this project.

## Working Rules

- Run commands from the repository root so relative paths in scripts keep working.
- Prefer updating schemas and output contracts in `references/` before changing multiple scripts.
- Do not hand-edit generated files under `outputs/site/` unless you are debugging the renderer.
- Do not invent paper claims, benchmarks, or metadata that are not grounded in the fetched payload.
- If a payload is incomplete, keep the record partial instead of filling gaps with guesses.

## Standard Workflow

1. Fetch new candidate papers when needed:

```bash
python3 scripts/fetch_translate_papers.py \
  --registry state/paper_registry.json \
  --manifest outputs/fetch/latest-fetch.json \
  --raw-dir outputs/raw \
  --limit 20
```

2. Write or update normalized paper records in `outputs/papers/` following:

- `references/paper-schema.md`
- `references/analysis-rubric.md`
- `references/meta-contract.md`

Before running the assembler, ensure the current `extractor-config.json` version has already been used to write `outputs/meta/<paper-id>.json` for each target paper via the repo-local `extract-paper-meta` skill.

Preferred command:

```bash
python3 scripts/normalize_papers.py \
  --raw-dir outputs/raw \
  --meta-dir outputs/meta \
  --papers-dir outputs/papers
```

3. Rebuild the registry:

```bash
python3 scripts/build_registry.py \
  --papers-dir outputs/papers \
  --registry state/paper_registry.json
```

4. Build site-derived payloads:

```bash
python3 scripts/build_site_derivatives.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site
```

5. Rebuild the Markdown site:

```bash
python3 scripts/render_markdown_site.py \
  --papers-dir outputs/papers \
  --site-dir outputs/site
```

6. Rebuild the HTML dashboard:

```bash
python3 scripts/render_html_dashboard.py \
  --site-index-json outputs/site/site-index.json \
  --output outputs/site/index.html
```

## Commit Guidance

- Usually commit: `scripts/`, `references/`, `agents/`, `SKILL.md`, `AGENTS.md`.
- Usually do not commit: `outputs/meta/`, `outputs/papers/`, `outputs/raw/`, `outputs/fetch/`, `outputs/site/`, `state/paper_registry.json`, caches, editor files, or virtualenvs.
- If you change the normalized paper schema or rendering contract, update the relevant file in `references/` in the same change.

## Verification

- For script changes, run the smallest affected command from the workflow above.
- For local-only changes in `outputs/papers/`, at minimum rebuild site derivatives and the site to catch schema drift before relying on generated outputs.
- Keep JSON pretty-printed with UTF-8 and trailing newlines, matching the existing scripts.
