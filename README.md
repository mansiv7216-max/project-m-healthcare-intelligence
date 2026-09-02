# Project M: Healthcare Decision Intelligence

### Evidence-grounded AI for healthcare claims decision support

Project M is an experimental healthcare AI system investigating a specific reliability problem:

> **If an AI system retrieves relevant information, does that necessarily make its final answer supported by the available evidence?**

The project compares three progressively constrained architectures: conventional semantic RAG, knowledge-graph-grounded RAG, and evidence-bounded generation with deterministic validation.

Rather than treating retrieval relevance as equivalent to decision reliability, Project M separates **retrieval, evidence validation, deterministic decision logic, and language generation**.

> **Retrieve for relevance. Validate for support. Generate within the evidence boundary.**

---

## Why This Project

Healthcare claims decisions may depend on information distributed across policy documents, member eligibility, provider status, procedure requirements, prior authorization, and clinical context.

A conventional RAG pipeline can retrieve semantically relevant text, but relevant retrieval alone does not establish that sufficient evidence exists for a particular conclusion.

Project M was built to explore that distinction.

The prototype asks:

1. How does conventional semantic RAG behave when evidence is incomplete?
2. Does adding structured knowledge-graph grounding reduce unsupported claims?
3. What changes when evidence is deterministically validated before language generation?
4. Can the system abstain instead of generating a conclusion when required evidence is missing?

---

## Experimental Architecture

Project M evolved through three modes.

### Mode A — Semantic RAG Baseline

```text
Question
   ↓
Semantic Retrieval
   ↓
Retrieved Context
   ↓
Local LLM
   ↓
Generated Answer
```

Mode A establishes the conventional retrieval-augmented generation baseline.

### Mode B — Knowledge Graph + RAG

```text
Question
   ↓
Semantic Retrieval
   +
Neo4j Graph Retrieval
   ↓
Graph-Grounded Context
   ↓
Local LLM
   ↓
Generated Answer
```

Mode B introduces structured relationships between healthcare entities and policy requirements using Neo4j.

### Mode C — Evidence-Bounded Generation

```text
Question / Claim
       ↓
Semantic + Graph Retrieval
       ↓
Structured Evidence Package
       ↓
Deterministic Evidence Validation
       ↓
Baseline Decision Logic
       ↓
Evidence Complete?
     ↙             ↘
   YES              NO
    ↓                ↓
Bounded LLM       Abstain
Generation
    ↓
Assertion Validation
    ↓
Final Supported Output
```

Mode C changes the responsibility of the language model.

The LLM is not responsible for deciding whether evidence exists. Structured services establish what is supported first, and generation is constrained to communicate within that evidence boundary.

---

## Controlled Benchmark

The current prototype was evaluated on a **20-case controlled benchmark** designed to expose failures involving missing, incomplete, or unsupported evidence.

| Metric | Mode C |
|---|---:|
| Overall accuracy | **85.0%** |
| Abstention accuracy | **100.0%** |
| Unsupported claim rate | **0.0%** |
| Unsupported answers | **0** |

For comparison, within the same controlled prototype:

| Architecture | Unsupported claim rate |
|---|---:|
| Semantic RAG | **66.7%** |
| Knowledge Graph + RAG | **58.3%** |
| Evidence-Bounded Mode C | **0.0%** |

These results are **preliminary and specific to the current 20-case benchmark**. They should not be interpreted as evidence of production-level healthcare performance or generalization to larger datasets.

The result instead motivates continued investigation into architectures where evidence validation occurs independently of language generation.

---

## Key Observation

The experiment exposed an important distinction:

```text
Relevant retrieval ≠ validated evidence
Validated evidence ≠ unrestricted generation
```

Graph grounding improved access to structured relationships, but the prototype still produced unsupported claims in some cases.

The largest behavioral change occurred when deterministic evidence validation was introduced before generation and the model was required to abstain when evidence was incomplete.

This suggests a broader design question for enterprise AI systems:

> **Should the LLM determine whether evidence exists, or should that responsibility belong to a separately auditable validation layer?**

Project M explores the second approach.

---

## Evidence Validation

Mode C constructs a validated evidence package containing structured claim context such as:

- member eligibility
- provider network status
- procedure information
- diagnosis context
- prior-authorization status
- graph-derived policy requirements
- deterministic baseline decision
- evidence completeness state

Generation is then constrained by explicit rules:

- use only the validated evidence package
- do not invent missing facts
- do not introduce external policy knowledge
- do not alter the deterministic baseline decision
- abstain when required evidence is incomplete

Generated assertions are subsequently checked against the supplied evidence.

---

## Technology Stack

- **Python** — application and evaluation logic
- **Neo4j** — healthcare knowledge graph and relationship grounding
- **Ollama** — local model runtime
- **Qwen2.5 7B Instruct** — bounded local language generation
- **Semantic retrieval** — Mode A retrieval baseline
- **Deterministic validation services** — evidence and decision controls
- **JSON / CSV experiment artifacts** — reproducible evaluation outputs

Generation experiments use temperature `0.0` to reduce variability.

---

## Repository Structure

```text
project-m-healthcare-intelligence/
│
├── app/
│   ├── generation/        # Generation modes including Mode C
│   ├── graph/             # Neo4j graph integration
│   └── services/          # Evidence and decision services
│
├── data/                  # Controlled prototype data
├── docs/                  # Architecture and supporting documentation
├── experiment_logs/       # Curated representative experiment artifacts
├── scripts/               # Benchmark and execution scripts
├── tests/                 # Retrieval and grounding tests
│
├── methodology-and-results.md
├── requirements.txt
└── README.md
```

---

## Methodology and Results

The complete experimental methodology, benchmark design, evaluation criteria, limitations, and detailed results are documented in:

**[Methodology and Results](./methodology-and-results.md)**

The repository also retains selected machine-readable experiment artifacts so individual outputs can be inspected rather than relying only on aggregate metrics.

---

## Current Limitations

Project M is a controlled research prototype, not a clinical or claims-adjudication system.

Current limitations include:

- only 20 controlled benchmark cases
- intentionally small healthcare policy corpus
- limited knowledge-graph entities and relationships
- no comprehensive Medicare, Medicaid, CMS, or payer authority hierarchy
- deterministic validation depends on the completeness and correctness of structured knowledge
- evaluation has not yet included human reviewers
- results have not been validated across multiple language models
- temperature `0.0` reduces variability but does not guarantee identical behavior across every runtime

These limitations intentionally constrain the claims that can be made from the current results.

---

## Future Research

Potential extensions include:

- larger benchmark datasets
- larger healthcare policy corpora
- additional procedure and diagnosis codes
- multiple payer and authority relationships
- evidence-completeness scoring
- contradictory evidence detection
- citation-level evaluation
- explanation-faithfulness evaluation
- adversarial and ambiguous queries
- temporal policy/version tracking
- human-review evaluation
- confidence calibration
- comparison across additional language models

A particularly important next question is whether the observed reduction in unsupported claims persists as graph complexity and policy-document volume increase.

---

## Project Status

**Version:** Experimental v1.0  
**Status:** Controlled prototype and comparative evaluation

Project M is intended as an exploration of reliability boundaries in enterprise AI, particularly the distinction between retrieving relevant information and establishing sufficient evidence for a supported decision.

---

## Disclaimer

This project uses synthetic/controlled prototype data and is intended solely for research, education, and portfolio demonstration.

It does **not** provide medical advice, insurance coverage determinations, or production healthcare decision support.# project-m-healthcare-intelligence
Design an enterprise AI platform that transforms fragmented healthcare policies, claims documentation, clinical guidelines, and operational SOPs into a unified knowledge graph supporting explainable decision-making.
