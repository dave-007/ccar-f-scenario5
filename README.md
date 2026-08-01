# Scenario 5: Claude Code for CI/CD

CCAR-F exam prep. A GitHub Actions workflow that runs Claude Code headlessly
on every PR: code review with a structured, gating verdict, then test
generation suggestions.

## The bugs under test

`app/pricing.py` has two intentional bugs that the existing tests
(`tests/test_pricing.py`) do **not** catch:

1. **Tax applied before discount** — `calculate_total` multiplies by
   `(1 + tax_rate)` first, then by `(1 - discount)`. Real invoicing applies
   the discount to the subtotal first, so this overcharges tax on the
   discounted amount.
2. **Off-by-one discount tier** — `bulk_discount_rate` uses `>` instead of
   `>=`, so a cart with exactly 10 or 20 items misses the discount tier it
   should qualify for.

The point: `pytest` passes locally because coverage is thin. The CI review
step is there to catch what the test suite doesn't.

## Key `claude -p` flags (verified against CLI v2.1.212, docs.claude.com → code.claude.com)

| Flag | Why |
|---|---|
| `--bare` | Skips auto-discovery of hooks/skills/plugins/MCP servers/CLAUDE.md. Docs call this "the recommended mode for scripted and SDK calls" — a teammate's local config or the repo's own `.mcp.json` can't silently change CI behavior between runs. |
| `-p "<prompt>"` / `--print` | Non-interactive mode; prompt is a positional arg (stdin also works, piped in as extra context, capped at 10MB). |
| `--output-format json` | Structured stdout. The model's response text comes back as a **plain string** under `.result` — not a nested object. Parse with `jq -r '.result'`. |
| `--allowedTools "Read"` | Pre-approves specific tools. On its own this does **not** block everything else. |
| `--disallowedTools "Bash,Write,Edit"` | Pairs with `--allowedTools` to actually exclude tools that could mutate the checkout or run arbitrary shell in CI. |
| `--permission-mode dontAsk` | Auto-denies anything not explicitly allowed and never blocks waiting for input. **Left at the `default` mode, a headless run with no TTY will hang until the CI job times out** — this is a real reported failure mode (anthropics/claude-code#52506), not a hypothetical. Always set this explicitly in CI. |

## Official GitHub Action vs. a raw `claude -p` step

Anthropic maintains **`anthropics/claude-code-action@v1`**, which wraps the
CLI with GitHub-specific plumbing: `@claude`-mention handling, GitHub App
token exchange, and a PR-creation flow. It's the right tool when you want
Claude to respond to mentions/comments on demand.

This workflow instead calls the CLI directly in a `run:` step. For a **fixed
rule that runs on every PR** (not mention-triggered), that's equally valid —
it's literally the pattern shown in Claude Code's own headless-mode docs —
and it keeps full control over the JSON schema, the pass/fail gate, and
exactly what gets posted back to the PR.

## Design: review gates test generation

The workflow runs in this order:
1. **Review** → structured JSON `{"verdict": "pass"|"block", ...}`
2. **Gate** on `verdict` via `$GITHUB_OUTPUT`
3. **Test generation** only runs `if: steps.gate.outputs.verdict == 'pass'` —
   no point suggesting tests for code the review already flagged
4. **Post comment** always runs, with either full results or a "skipped"
   note for the tests section
5. **Fail the build** (`exit 1`) if the verdict was `block` — this is what
   actually gates the PR, not just informs it

## Known limitation: the gate can edit itself

Because this uses the `pull_request` trigger (not `pull_request_target`), GitHub
reads the workflow file **from the PR's own head branch**, not from `main`. That
means a PR can modify `.github/workflows/claude-ci.yml` and have its own review
logic evaluate itself in the same run — confirmed live: PR #1 in this repo did
exactly that, and Claude's own review flagged it as a medium-severity finding.

The "correct" fix is `pull_request_target`, which pins the workflow file to the
base branch — but that trigger runs with base-branch secrets available even for
untrusted forks, which is a well-known way to leak secrets if you're not careful
about what gets checked out and executed. Retrofitting that safely is out of
scope for this demo; for a real team repo, workflow file changes should require
a human reviewer regardless of what the automated verdict says.

## Try it

```bash
git checkout -b test/trigger-review
# edit app/pricing.py or tests/test_pricing.py
git commit -am "test: trigger claude-ci workflow"
git push -u origin test/trigger-review
gh pr create --fill
```

Watch the Actions tab, then check the PR for Claude's comment.
