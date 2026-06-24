# 17. Agent Tooling Runbook

> Purpose: before building or debugging by hand, check whether an already verified local tool, Codex Skill, GitHub workflow, or MCP connector can do the job safely. This keeps velocity high without skipping gates.
> Checked: 2026-06-24. Sources: OpenAI Codex docs, MCP specification, Google SRE postmortem culture, ADR practice, existing sajugen harnesses.

## 1. Start order for every agent task

Use this order before code changes.

1. Read the local project rules: `AGENTS.md`, `CLAUDE.md`, `.claude/rules/00-immutable.md`, `sajugen/STATE.md`, `docs/14-tone-spec.md`, `docs/16-quality-incident-ledger.md`.
2. Check the available Codex Skills for the task category. Use GitHub Skills for PR/CI/review work before hand-writing `gh` flows.
3. Check repo-native tools before external tools:
   - final read-only gate: `./.venv/Scripts/python.exe scripts/hrun.py --profile harness/profiles/local/personal_h153.yml --profile harness/profiles/local/gunghap_h153.yml`
   - plan gate: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/ai-harness.ps1 -Stage Plan -Task handoff/current/task.md`
   - contract tests: `./.venv/Scripts/python.exe -m pytest tests/test_ai_harness_contract.py -q`
   - targeted tests before full tests.
4. If a known blocker appears, use the playbook in section 4 before retrying the same command.
5. Use MCP only after the security checklist in section 5 passes.
6. Build custom code only when no existing skill, repo tool, or safe MCP covers the task.

## 2. Current usable tools

| Need | Use first | Notes |
|---|---|---|
| PR summary, review orientation, changed files | `github:github` Skill or GitHub connector | Prefer connector metadata over scraping UI. |
| Address PR review comments | `github:gh-address-comments` Skill | Use when unresolved threads or review state matter. |
| Failing GitHub Actions | `github:gh-fix-ci` Skill | Only useful when checks exist. This repo often has no Actions checks. |
| Publish local changes | `github:yeet` Skill | Still follow sajugen approval rules before commit/push. |
| Sajugen final validation | `scripts/hrun.py` | Read-only by default. Required final evidence. |
| AI plan review | `scripts/ai-harness.ps1` | Claude/Codex token use only on real Plan runs, not DryRun. |
| PDF rendering issue | Playwright guard + `sajugen/render/verify.py` | Separate sandbox probe noise from actual PDF failure. |
| Repeated quality incident | `docs/16-quality-incident-ledger.md` | Add regression test or gate before relying on memory. |

## 3. Tool choice rules

Use the smallest capable tool.

- Prefer deterministic code and tests for calculation, gates, PDF verification, and secret/PII checks.
- Prefer Skills for reusable workflows and "how to do this repo task" knowledge.
- Prefer MCP/connectors only for external systems that are already trusted and scoped.
- Do not use an LLM to invent calculations, customer context, dates, names, or evidence.
- Do not let a successful plan replace final `hrun` evidence.

## 4. Blocker playbooks

### API connection failure

1. Record whether the command ran in sandbox or outside sandbox.
2. Check auth and network separately from code.
3. If token usage is zero, treat it as environment/auth/network, not model behavior.
4. Retry only once after the environment cause is addressed.

### PLAN_VERDICT=BLOCK

1. Read `plan-verdict.json` and `codex-plan-review.json`.
2. Fix the task file or validation plan first.
3. Do not implement code while the plan gate is BLOCK.
4. Re-run DryRun before another real Plan run.

### pytest hang

Run in this order. Do not wait hours on a blind full run.

```powershell
./.venv/Scripts/python.exe -m pytest tests/ -vv -s --maxfail=1
./.venv/Scripts/python.exe -m pytest tests/ -q --durations=20 --durations-min=1
./.venv/Scripts/python.exe -m pytest tests/ -q -o faulthandler_timeout=300
```

If `pytest-timeout` is installed later, use `--timeout=300 --timeout-method=thread` for stack traces.

### Playwright sandbox failure

1. Check whether the failure came from the sandbox probe.
2. If it is probe-only in Codex sandbox, use the existing guard result.
3. If actual PDF generation fails outside sandbox, inspect `render/verify.py` output and the rendered artifact.

### Quality complaint

1. Identify the exact customer axis: question, timing horizon, relationship mode, asset/child/risk axis, or tone.
2. Check `docs/16-quality-incident-ledger.md` for prior incidents.
3. Add or update a regression test before changing prose templates.
4. Verify with targeted tests, then `hrun`.

## 5. MCP adoption checklist

Default for this repo remains "MCP MVP 0" unless all items pass.

- The tool is from an official or trusted source.
- The task cannot be solved by repo-native tools or installed Skills.
- No customer PII, birth data, `.env`, `data/`, local profiles, or generated PDFs are sent.
- Scope is read-only unless the operator explicitly approves the write.
- The tool exposes clear schemas and outputs that can be validated.
- First run is a minimal dry-run/read-only query.
- A fallback path exists if the server is unavailable.

## 6. When to create a new Codex Skill

Create a personal Skill only after the workflow repeats at least three times or requires a long checklist that agents keep forgetting.

Candidate skill: `sajugen-workflow`.

Initial contents should include:

- required starting reads
- hrun and ai-harness command order
- quality incident lookup
- PR/merge checklist
- PDF/LLM approval boundaries
- common blocker playbooks from this document

Keep the Skill short and link back to this runbook and project docs instead of copying every rule.

## 7. References checked

- OpenAI Codex Skills: https://developers.openai.com/codex/skills
- OpenAI Codex MCP: https://developers.openai.com/codex/mcp
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- MCP tools specification: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Google SRE postmortem culture: https://sre.google/sre-book/postmortem-culture/
- ADR practice: https://github.com/architecture-decision-record/architecture-decision-record

Applied conclusions:

- Codex exposes Skills, MCP/connectors, shell, web search, AGENTS.md, permissions, and GitHub integration as separate tool/config surfaces.
- MCP tools are model-controlled external-system calls; tool annotations are not trusted unless they come from trusted servers, and structured outputs still need client validation.
- Recurring failures should become written preventive actions, not memory-dependent reminders.
- Important tooling decisions should record context, decision, and consequences.
