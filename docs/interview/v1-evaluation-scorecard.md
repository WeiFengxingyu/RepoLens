# RepoLens V1 Evaluation Scorecard

## 1. Purpose

This scorecard turns the existing Phase 5 and Phase 9 evaluation work into an interview-ready ablation story. It answers three questions:

1. Which capability improves retrieval quality?
2. Which V1 features are measured beyond screenshots?
3. Where are the limits of the current evidence?

## 2. Retrieval Ablation Summary

Source evidence: `docs/phase5-closed-loop-log.md`, section "评测指标记录".

| Strategy | Samples | Hit@5 | MRR | Citation Coverage | Avg Latency | P95 Latency | Avg Tokens | Error Count | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `vector_only` | 50 | 0% | 0.000 | 0% | 0.2 ms | 1 ms | 14.9 est | 0 | Local embedding provider was intentionally unset, proving vector-only degrades transparently instead of silently falling back |
| `bm25_vector` | 50 | 92% | 0.787 | 85.2% | 4.6 ms | 7 ms | 66.4 est | 0 | Strong lexical baseline; best Hit@5 in the recorded local demo |
| `bm25_vector_graph` | 50 | 90% | 0.892 | 84.5% | 9.6 ms | 20 ms | 64.8 est | 0 | Slightly lower Hit@5 than BM25+vector, but higher MRR; graph expansion helps rank related code earlier |

## 3. What The Ablation Shows

| Question | Answer |
| --- | --- |
| Is GraphRAG just a buzzword here? | No. The graph strategy records `graph_count` and graph-expanded evidence, and the demo run improved MRR from 0.787 to 0.892. |
| Why keep BM25 if vector search exists? | The project must work locally without embedding credentials. BM25 provides a deterministic baseline and supports graph expansion seeds. |
| Why not claim graph is always better? | The recorded demo shows a tradeoff: BM25+vector had higher Hit@5, while BM25+vector+graph had better MRR and slightly higher latency. |
| Why is vector-only 0%? | The local release configuration had no embedding provider. This is a useful safety signal, not a quality claim about embeddings in general. |

## 4. V1 Review / Multi-Agent / MCP Metrics

Source evidence: `docs/phase9-v1-benchmark-report.md` and `backend/app/services/v1_benchmark/metrics.py`.

| Metric Group | Metrics | What It Proves | Current Evidence Limit |
| --- | --- | --- | --- |
| Review quality | `risk_hit_rate`, `citation_coverage`, `unsupported_claim_rate`, latency, token count | PR/MR review is evaluated by expected risk and evidence grounding, not just visual output | Dataset is synthetic/offline, not human-labeled production traffic |
| Multi-Agent | risk hit, citation coverage, `dissent_usefulness`, `arbiter_resolution_rate`, `token_overhead_ratio`, latency | Multi-agent work is bounded and measured; dissent and arbiter are first-class outputs | Useful dissent is rule-scored, not yet human-rated |
| MCP reliability | `tool_success_rate`, `permission_denial_correctness`, latency, error count | Tool calls and permission denials are measurable, including disabled safe-check behavior | V1 uses local HTTP JSON-RPC transport, not a public remote MCP service |

## 5. Interview Scorecard

| Interview Claim | Evidence Artifact | How To Defend It |
| --- | --- | --- |
| "I built more than a chatbot over code." | Hybrid retrieval, code graph, evidence citations, Phase 5 metrics | Show the retrieval ablation and explain the BM25/vector/graph tradeoff |
| "The agent is controllable." | MCP registry, permission labels, disabled static check, audit hashes | Show Tool Permissions panel and MCP metrics |
| "The multi-agent layer is not decorative." | Agent sessions, assignments, messages, dissent, Arbiter, token overhead metric | Explain why token/round guards matter and why Arbiter keeps dissent |
| "The platform layer is not GitHub-only." | Change Request Provider and real case matrix | Show GitHub, Gitee, GitLab.com, self-hosted GitLab URL shapes |
| "I know the limits." | This scorecard, real case-study boundary notes | State that V1 benchmark is synthetic/offline and live cases are smoke candidates |

## 6. Next Evaluation Upgrade

If there is time after product packaging, the next best evaluation improvement is a small human-reviewed public PR pack:

- 5 to 10 public PR/MR cases.
- One manually labeled expected risk or "no material risk" outcome per case.
- One expected evidence file list per case.
- One failure note per case.
- No platform writeback.

This is higher value for interviews than adding more product surface area because it converts RepoLens from "feature complete" to "measured on real examples".

