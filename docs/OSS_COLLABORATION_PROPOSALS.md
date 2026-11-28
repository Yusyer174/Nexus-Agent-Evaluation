# Targeted OSS collaboration proposals

Research checkpoint: 2026-11-27. These are **unsent drafts**, not accepted work,
partnerships, adoption or independent validation. Recheck claims, linked PRs and
maintainer guidance before posting or starting. No new upstream issue is needed
for an existing problem. NEXUS remains an optional declaration checker, not a
dependency to promote in unrelated discussions.

## Inspect: review evidence requirements without taking over existing work

Source: [Inspect #6762](https://github.com/UKGovernmentBEIS/inspect_ai/issues/6762),
by `daaain`, and its maintainer response. The author already offers to write the
Docker-host documentation; the maintainer supports useful documentation additions.
Do not duplicate that contribution or implement its companion #6763 controls.
[Inspect's contribution guide](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/CONTRIBUTING.md)
asks contributors to coordinate claims before work.

Potential mutual value: an independent documentation review can help distinguish
configuration, observed behavior and unsupported claims. NEXUS can learn where
its synthetic evidence worksheet is insufficient; Inspect can get a narrowly
scoped review of wording without a new integration dependency. No Docker runs or
host access tests have been performed for this proposal.

Draft for the existing thread, only after checking the author's current PR:

> I would be interested in reviewing the evidence wording in your documentation
> draft, without duplicating your implementation. Could a small review table
> distinguish configured boundary, observed outcome, observation coverage and
> remaining uncertainty? I can review a public synthetic example where a denial
> report is present but the operation record is missing, and flag conclusions
> that should remain unverified. This would be a documentation review only; I
> have not reproduced the host experiments. Would that be useful on your PR?

Acceptance before claiming a contribution: the author/maintainer welcomes the
review, a specific draft revision is identified, and comments cite exact wording
and reproducible public evidence. An offer alone is not a contribution.

## Strands Evals: trace/message error-outcome parity

Source: [Strands Evals #656](https://github.com/strands-agents/evals/issues/656).
It reports a missing `is_error` field on the Session/trace extraction path even
though the message path supplies it. At this checkpoint the issue is open,
unassigned and has no comments. The report includes a synthetic reproduction;
its runtime findings have **not been independently reproduced here**.

Potential mutual value: model-free extractor tests would strengthen upstream
representation parity. The same review discipline helps NEXUS avoid treating
declared success as an observed operation outcome. This does not require adding
Strands or model dependencies to NEXUS.

Draft for the existing issue, after a fresh search for linked fixes:

> I can help with a small, model-free regression matrix for the trace extractor
> and dispatcher. Proposed cases are an explicit error, a successful result,
> an empty-string error whose meaning needs confirmation, equivalent message and
> Session inputs, and an unsupported dispatcher input. I would first reproduce
> the reported discrepancy and follow your ToolResult contract rather than
> infer error state from text content. Is anyone already implementing this, and
> is this test scope useful before I prepare a focused patch?

Before work: inspect the current contribution guide, linked commits and all
matching PRs, reproduce with synthetic objects, and confirm `error=None` versus
`error=""` semantics with upstream. No claim or post has been made. The current
open-PR listing is not a guarantee that a differently named patch does not exist.

## Recruiting genuine evidence review

[NEXUS #37](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/37) already
defines a specialist opportunity; do not create a duplicate recruitment issue.
Offer reviewers [the synthetic worksheet](ISOLATION_REVIEW_PREPARATION.md), ask
for counterexamples rather than approval, and preserve the reviewer's authorship.
The maintainer's prepared material does not complete that independent task.

For Python, JavaScript, DevOps and testing beginners, use the existing bounded
issues [#29](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/29),
[#30](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/30) and
[#31](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/31). Do not send
bulk invitations or imply that a fork, an offer, CI or AI output is adoption.
