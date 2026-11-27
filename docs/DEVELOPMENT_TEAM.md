# Development team and independent review

This is a coordination protocol, not a running agent service or a claim that a
team has been recruited. One person can cover several roles; review independence
must be reported honestly. Assistants propose patches within a human-approved
task. They do not authorize themselves, change production, or approve releases.

## Responsibilities

| Role | Owns | Acceptance evidence |
| --- | --- | --- |
| Technical coordinator | Scope, issue ownership, dependencies, integration order | Agreed acceptance criteria, bounded task, reviewable PR |
| Architecture | Contracts, dependency boundaries, compatibility decisions | Small decision record, alternatives and migration risk |
| Backend / Python | Evaluator, CLI and input diagnostics | Synthetic regressions, unchanged gates and report contract |
| Frontend / JavaScript | Browser port, accessibility and UI state | Python parity, generated HTML freshness, relevant browser checks |
| Testing reviewer | Independently designed counterexamples and reproduction | Commands and outcomes against the exact proposed content |
| Security reviewer | Trust boundaries, provenance and unsupported claims | Scoped evidence assessment; unknowns stay unverified |
| DevOps | Portable CI, packaging and artifact provenance | Least permissions, platform checks, no implicit publication |
| Research / documentation | User trials, references and limitations | Reproducible public examples and accurate attribution |

## Claim and scope a task

1. Read the issue, assignments, recent comments and open PRs. State the problem,
   proposed files, acceptance tests and exclusions in a short public outline.
2. A maintainer acknowledges coordination; lack of a formal assignee does not
   override a contributor's existing public claim. Ask before parallel work.
3. Use one task branch from current main. The coordinator records dependencies
   before splitting work. No simultaneous ownership of the same file without an
   agreed integration order. Prefer sequential work to unnecessary assistants.
4. Post a meaningful progress update if work is delayed. After seven days without
   an update, ask whether the contributor is still working before reassigning;
   do not silently remove their work or promise deadlines on their behalf.
5. #29 is browser CI wiring, #30 artifact version assertions, #31 offline Markdown
   checking, and #37 genuine independent evidence review. Internal preparation
   does not claim or complete those tasks. #8 is a voluntary user trial.

## Definition of done

- The problem is reproduced or the documentation gap is identified concretely.
- A minimal diff meets explicit acceptance criteria; behavior changes include a
  failing-before/passing-after regression and a compatibility note.
- Full Python regressions and both CLI examples pass; a critical rejection at
  zero threshold remains rejected. Component checks follow
  [CONTRIBUTING.md](../CONTRIBUTING.md). Record environment blocks explicitly.
- Reports, test logs and CI refer to the actual source SHA or a recorded identical
  tree. A PR run is not evidence of a later main run. Check all relevant jobs,
  including failures allowed by a parent pipeline.
- An independent reviewer checks the diff and reproduces the important result;
  they should add a counterexample selected without the author's answer key.
  If no reviewer is available, leave the PR awaiting review. CI does not fill that role.
- External credits and limitations are retained; no secrets or unrelated edits.
- Maintainer acceptance, merge and publication are separate decisions. A merged
  change needs main CI before reporting successful integration.

## Review and conflicts

Proposal and verification are separate steps. The reviewer records what they
personally ran, what they inferred, and what remains unchecked. Do not treat two
prompts to the same assistant as two independent reviewers. Use least-privilege
repository access; credentials and protected environments stay with the owner.

Fetch main before final review. If it changed, inspect the delta. Resolve conflicts
on the task branch with a normal merge commit when coordination calls for a
refresh; never force-push another person's branch. For README or changelog conflicts,
retain both relevant contributions and dates, then verify links and claims. Rerun
affected checks after resolution. Stop and coordinate if intent is ambiguous.

## Handoff template

Copy this into a PR description or the task's continuation record:

```text
Task / issue / author / reviewer:
Base SHA / proposed SHA / branch:
Problem and evidence:
Acceptance criteria and exclusions:
Files changed and files owned by others:
Commands, tool versions, exits and CI links:
Before/after result; unverified assumptions:
Compatibility, security limits and contributor credits:
Remaining blockers / next owner and concrete action:
Merge / deployment / publication authorization (if any):
```

## Decision record

For a significant tradeoff, add a short section to the task record: date, context,
decision, rejected alternatives, evidence, consequences and conditions for revisiting.
Routine edits need no separate architecture document. The first decisions for this
work are recorded in [engineering continuity](ENGINEERING_COMMUNITY_HANDOFF.md).

See [AGENTS.md](../AGENTS.md) for assistant constraints and
[the architecture map](ARCHITECTURE.md) for component boundaries.
