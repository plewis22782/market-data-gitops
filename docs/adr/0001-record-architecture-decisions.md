# 1. Record architecture decisions

Date: 2026-11-09 · Status: accepted

## Context
Decisions about tooling and standards outlive the conversation where they were made. Six months
from now, "why k3d and not k3s on the host?" needs an answer that doesn't depend on memory.

## Decision
Every decision that changes how the platform is built, deployed or operated gets a short ADR in
`docs/adr/`, numbered, in the Nygard format (context, decision, consequences). ADRs are immutable
once accepted; a change of mind is a new ADR that supersedes the old one.

## Consequences
Reviewers see the reasoning in the same PR as the change. Superseded ADRs stay in the history.
