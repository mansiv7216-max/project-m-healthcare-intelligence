# Project M Trust and Grounding Framework

## Purpose

Project M is an enterprise healthcare decision-intelligence prototype designed to investigate whether structured relational grounding, deterministic validation, and bounded retrieval-augmented generation can reduce unsupported outputs in healthcare claims-oriented AI systems.

The central principle is:

> Retrieval does not imply correctness.

A semantically relevant document may still be outdated, incomplete, conflicting, or insufficient to support a claim-related determination. Project M therefore separates evidence retrieval, evidence validation, decision logic, and language generation.

---

## Trust Boundary

The large language model is not treated as the authoritative claims decision engine.

Project M separates the workflow into four layers:

1. Evidence retrieval
2. Evidence verification
3. Deterministic decision logic
4. LLM-based explanation

The LLM may explain verified evidence and decisions, but it must not independently invent claim facts, policy requirements, thresholds, or coverage rules.

---

## Authoritative Evidence

Claim-related decisions should rely only on approved and traceable evidence.

For the current prototype, authoritative evidence includes:

- Member eligibility status
- Provider network status
- Procedure code
- Diagnosis code
- Prior authorization status
- Applicable policy
- Policy requirements
- Verified healthcare knowledge-graph relationships

Future source records should include provenance metadata such as:

- `source_id`
- `source_type`
- `source_version`
- `effective_date`
- `last_updated`
- `verification_status`

Unverified sources must not silently influence an authoritative determination.

---

## Structured Facts Before Free Text

Structured claim facts should be retrieved from deterministic systems or the knowledge graph whenever possible.

Examples include:

- Claim identifier
- Member identifier
- Provider identifier
- Procedure code
- Diagnosis code
- Claim amount
- Eligibility status
- Network status
- Prior authorization status

The LLM must not infer these values from unstructured text when verified structured values are available.

---

## Evidence Completeness

A claim should not receive a definitive determination unless the minimum required evidence is available.

Depending on the procedure and policy, required evidence may include:

- Active member eligibility
- Provider network status
- Procedure code
- Diagnosis
- Applicable policy
- Policy requirement
- Prior authorization status

Missing required evidence should result in abstention rather than inference.

---

## Abstention Rules

Project M must support explicit non-decision states.

Examples include:

- `INSUFFICIENT_EVIDENCE`
- `SOURCE_CONFLICT`
- `MANUAL_REVIEW_REQUIRED`

The system should prefer abstention over an unsupported or speculative determination.

---

## Policy Applicability

A retrieved policy is not automatically considered applicable.

Policy applicability should consider:

- Procedure
- Diagnosis
- Plan type
- Effective date
- Policy version
- Member eligibility
- Network requirements
- Authorization requirements

A correct answer based on an expired or unrelated policy is still considered incorrect.

---

## Source Conflict Detection

Conflicting authoritative evidence must be detected before generation.

Examples:

- Graph indicates prior authorization is present while another verified source indicates it is missing.
- Provider network status differs across authoritative systems.
- Multiple policy versions apply to the same date of service.

Conflicts should produce a review state rather than allowing the LLM to resolve the conflict independently.

---

## Numeric and Factual Grounding

Generated responses must not introduce unsupported factual values.

This includes:

- Dollar amounts
- Coverage thresholds
- Dates
- Percentages
- Procedure codes
- Diagnosis codes
- Policy requirements
- Authorization requirements

Material factual statements must be traceable to retrieved evidence.

---

## Confidence Framework

Confidence should not be treated as an LLM-generated opinion.

Project M confidence should instead reflect measurable evidence characteristics such as:

- Evidence completeness
- Source authority
- Source consistency
- Policy applicability
- Retrieval quality
- Relationship confidence
- Validation status

The final confidence score should be produced by deterministic logic wherever possible.

---

## Bounded Generation

The LLM receives a bounded evidence package.

Its role is to:

- Explain verified evidence
- Summarize decision rationale
- Present citations
- Translate structured evidence into readable language

Its role is not to independently determine coverage.

The LLM must not use unsupported external knowledge when producing a claim explanation.

---

## Post-Generation Validation

Generated responses should be validated before being returned to the user.

Validation should check for:

- Unsupported factual claims
- Incorrect numeric values
- Invalid citations
- Missing citations
- Policy mismatches
- Contradictions with verified evidence
- Contradictions with deterministic decision results

If validation fails, the response should be rejected, regenerated, or routed for manual review.

---

## Experimental Comparison

Project M will eventually compare three architectures:

### A. Semantic Vector RAG

Traditional semantic retrieval using vector similarity.

### B. Knowledge Graph + RAG

Semantic retrieval augmented with structured entity and relationship context.

### C. Knowledge Graph + Deterministic Validation + Bounded RAG

Structured retrieval, evidence verification, deterministic decision logic, and constrained generation.

The goal is to evaluate whether progressively stronger grounding reduces unsupported generation.

---

## Evaluation Dimensions

The following metrics will be used in later experiments:

| Metric | Description |
|---|---|
| Unsupported Claim Rate | Percentage of generated statements not supported by retrieved evidence |
| Citation Accuracy | Whether cited evidence actually supports the generated statement |
| Numeric Fidelity | Whether amounts, codes, dates, and other values match source data |
| Decision Agreement | Agreement between generated output and deterministic baseline |
| Abstention Accuracy | Whether the system correctly refuses to answer when evidence is insufficient |
| Policy Fidelity | Whether the correct policy and version were applied |
| Evidence Completeness | Whether required decision inputs were available |
| Explanation Faithfulness | Whether the explanation accurately reflects the evidence and decision logic |

---

## Design Principle

Project M is not designed to maximize answer generation.

It is designed to maximize traceability, evidence quality, and defensible decision support.

When evidence is insufficient, the system should say so.
