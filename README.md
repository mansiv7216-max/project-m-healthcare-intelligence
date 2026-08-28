# Project M — Healthcare Intelligence

### Evaluating Semantic RAG, Knowledge-Graph Grounding, and Bounded Generation for Reliable Healthcare AI

Project M is an experimental healthcare decision-intelligence prototype designed to investigate a specific problem:

> **Does stronger evidence grounding reduce unsupported LLM-generated claims?**

Retrieval-Augmented Generation (RAG) can provide an LLM with relevant documents, but retrieval alone does not guarantee that the generated answer is supported by the retrieved evidence.

This project compares three progressively constrained architectures:

1. **Mode A — Conventional Semantic RAG**
2. **Mode B — Knowledge Graph + RAG**
3. **Mode C — Knowledge Graph + Deterministic Validation + Bounded Generation**

The objective is not to build an automated healthcare claims adjudication system. The project is a controlled research prototype for studying **grounding, evidence validation, abstention, provenance, and unsupported generation** in AI-assisted decision workflows.

---

## Research Question

The central research question is:

> **Does structured relational grounding combined with deterministic evidence validation and bounded generation reduce unsupported LLM outputs compared with conventional semantic RAG?**

The experiment focuses on an important distinction:

**Retrieval is not verification.**

A semantically relevant document may still contain evidence referring to a different procedure, policy condition, authority, or relationship.

An LLM can therefore produce a plausible answer even when the evidence does not support the exact assertion being made.

Project M tests whether an explicit validation layer can reduce this behavior.

---

# Architecture

## Mode A — Conventional Semantic RAG

Mode A represents a conventional semantic retrieval pipeline.

```text
Question
   ↓
MiniLM Embedding
   ↓
FAISS Similarity Search
   ↓
Top-K Policy Chunks
   ↓
Local LLM
   ↓
Generated Answer
```

### Components

- Sentence Transformers
- `all-MiniLM-L6-v2`
- FAISS vector similarity search
- Local Qwen2.5 7B Instruct generation through Ollama

Mode A intentionally does **not** use:

- Neo4j
- deterministic validation
- graph traversal
- validated evidence boundaries

This provides the semantic-RAG baseline.

---

## Mode B — Knowledge Graph + RAG

Mode B adds structured relational grounding.

```text
Question
   ↓
Semantic Retrieval
   +
Neo4j Knowledge Graph
   ↓
Procedure / Policy / Requirement Context
   ↓
Local LLM
   ↓
Generated Answer
```

The knowledge graph explicitly represents relationships such as:

```text
Procedure
   ↓ GOVERNED_BY
Policy
   ↓ REQUIRES
Requirement
```

This allows generation to receive both semantic document context and structured relationships.

However, Mode B still allows the LLM to interpret the retrieved evidence.

It does not enforce deterministic evidence validation before generation.

---

## Mode C — Validated / Bounded RAG

Mode C introduces an explicit evidence-validation boundary.

```text
Question
   ↓
Knowledge Graph
   ↓
Structured Relationship Retrieval
   ↓
Deterministic Evidence Validation
   ↓
Validated Evidence Package
   ↓
Evidence Boundary
   ↓
Bounded Local LLM
   ↓
Answer or Abstention
```

Before generation, the system determines whether the requested assertion is actually supported.

Examples include:

- procedure → policy relationships
- policy → authorization requirements
- conditional versus required authorization
- missing policy evidence
- unsupported authority relationships

If the relationship cannot be validated, generation can be prevented entirely.

```text
Unsupported assertion
        ↓
Deterministic validator
        ↓
Generation invoked: False
        ↓
ABSTAIN
```

This makes abstention an architectural behavior rather than solely an LLM prompt instruction.

---

# Knowledge Graph

Neo4j is used to model structured healthcare relationships.

Current graph entities include:

- Claim
- Member
- Provider
- Procedure
- Diagnosis
- Policy
- Requirement

Example relationships include:

```text
Member ──FILED────────────→ Claim

Claim ───PERFORMED_BY─────→ Provider

Claim ───USES_PROCEDURE───→ Procedure

Claim ───HAS_DIAGNOSIS────→ Diagnosis

Procedure ─GOVERNED_BY────→ Policy

Policy ───REQUIRES────────→ Requirement
```

The graph allows relational evidence to be retrieved directly instead of requiring the LLM to infer every relationship from semantically similar text.

---

# Deterministic Evidence Validation

Mode C contains a deterministic validation layer between retrieval and generation.

For example, authorization evidence may distinguish:

```text
REQUIRED
```

from:

```text
CONDITIONAL
```

A conditional rule can preserve information such as:

```text
Depends on clinical condition and plan rules.
```

This prevents a conditional requirement from automatically being transformed into a universal statement such as:

```text
Procedure X always requires prior authorization.
```

The evidence layer also detects unsupported assertions.

For example, the graph may validate:

```text
Procedure 70553
    ↓
Advanced Imaging Coverage Policy
    ↓
Prior Authorization
```

but this does **not** establish:

```text
Medicare
    ↓
Procedure 70553
```

If an authority relationship has not been validated, Mode C abstains instead of allowing the LLM to infer it.

---

# Evidence Boundary

Validated evidence packages contain:

- verified claim facts
- policy evidence
- deterministic decision results
- provenance
- evidence completeness
- generation constraints

Generation constraints include:

```text
may_change_baseline_decision = false
may_invent_missing_facts = false
may_use_external_policy_knowledge = false
must_cite_policy = true
must_abstain_if_evidence_incomplete = true
```

The LLM therefore acts primarily as an **explanation layer over validated evidence**, rather than as the authority responsible for establishing facts.

---

# Experimental Evaluation

A controlled **20-case synthetic benchmark** was created to compare all three architectures.

The benchmark includes cases involving:

- exact supported procedures
- conditional authorization requirements
- unsupported authorities
- unknown procedures
- missing policy evidence
- semantically similar procedure codes
- required abstention

The same local generation model is used across the architectures to reduce model choice as an experimental variable.

### Generation Model

```text
Qwen2.5 7B Instruct
Temperature: 0.0
Runtime: Ollama
```

---

# Benchmark Results

| Metric | Mode A | Mode B | Mode C |
|---|---:|---:|---:|
| Overall Accuracy | 60.0% | 65.0% | **85.0%** |
| Answer Accuracy | **100.0%** | **100.0%** | 62.5% |
| Abstention Accuracy | 33.3% | 41.7% | **100.0%** |
| Unsupported Claim Rate | 66.7% | 58.3% | **0.0%** |
| Unsupported Answers | 8 | 7 | **0** |

---

# Interpretation

The prototype produced a clear difference between answering correctly when evidence exists and knowing when **not to answer**.

Modes A and B achieved high answer accuracy on answerable cases but frequently answered questions for which the available evidence did not establish the requested relationship.

Mode C behaved more conservatively.

Within this 20-case synthetic benchmark:

- overall accuracy increased from **60% in Mode A to 85% in Mode C**
- abstention accuracy increased from **33.3% to 100%**
- unsupported claim rate decreased from **66.7% to 0%**
- unsupported answers decreased from **8 to 0**

These results do **not** establish that bounded RAG eliminates hallucination generally.

They demonstrate that, within this controlled prototype, deterministic evidence validation prevented a class of unsupported assertions that semantic retrieval and graph grounding alone did not prevent.

---

# An Important Retrieval Observation

During development, semantic retrieval exposed one of the motivating problems for the experiment.

For the query:

```text
Does procedure 70553 require prior authorization?
```

semantic retrieval returned a chunk discussing procedure **70551** slightly above the exact **70553** evidence.

The two passages were semantically similar because both discussed imaging procedures and prior authorization.

However:

```text
semantic similarity ≠ relational correctness
```

Rather than tuning this behavior out of Mode A, it was retained as part of the baseline architecture.

This illustrates why retrieval quality alone may be insufficient when exact entity and policy relationships matter.

---

# Evaluation Metrics

The broader evaluation framework considers:

- Unsupported Claim Rate
- Citation Accuracy
- Numeric Fidelity
- Decision Agreement
- Abstention Accuracy
- Policy Fidelity
- Evidence Completeness
- Explanation Faithfulness

The current v1 benchmark primarily focuses on answer correctness, abstention behavior, and unsupported generation.

See:

```text
docs/evaluation-framework.md
docs/trust-framework.md
```

for the research framing.

---

# Repository Structure

```text
project-m-healthcare-intelligence/
│
├── app/
│   ├── generation/
│   │   ├── mode_a_generator.py
│   │   ├── mode_b_generator.py
│   │   └── mode_c_generator.py
│   │
│   ├── graph/
│   │   ├── connection.py
│   │   └── queries.py
│   │
│   ├── retrieval/
│   │   └── semantic_retriever.py
│   │
│   └── services/
│       ├── claims_service.py
│       ├── context_service.py
│       ├── decision_service.py
│       └── evidence_service.py
│
├── data/
│   ├── evaluation/
│   │   └── rag_evaluation_cases.json
│   ├── policies/
│   │   └── imaging_policy.txt
│   ├── claims.csv
│   ├── members.csv
│   └── providers.csv
│
├── docs/
│   ├── evaluation-framework.md
│   └── trust-framework.md
│
├── scripts/
│   ├── run_comparative_evaluation.py
│   ├── run_mode_a_evaluation.py
│   └── seed_neo4j.py
│
├── tests/
│   ├── test_decision_service.py
│   ├── test_evidence_service.py
│   └── test_semantic_retriever.py
│
├── experiment_logs/
├── requirements.txt
└── README.md
```

---

# Technology Stack

### AI / Retrieval

- Python
- Sentence Transformers
- MiniLM embeddings
- FAISS
- Qwen2.5 7B Instruct
- Ollama

### Knowledge Graph

- Neo4j
- Cypher

### Evaluation

- Pytest
- JSON experiment artifacts
- CSV benchmark summaries
- deterministic validation logic

---

# Running the Project

## 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Start Ollama

The project expects a local Ollama instance.

```bash
ollama serve
```

Pull the generation model if required:

```bash
ollama pull qwen2.5:7b-instruct
```

## 4. Start Neo4j

Start the local Neo4j database and configure the required connection credentials.

The current graph database used during development is:

```text
projectm
```

## 5. Seed the knowledge graph

```bash
PYTHONPATH=. python scripts/seed_neo4j.py
```

## 6. Run tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

## 7. Run the comparative benchmark

```bash
PYTHONPATH=. python scripts/run_comparative_evaluation.py
```

Experiment artifacts are written to:

```text
experiment_logs/
```

---

# Research Limitations

This repository should be interpreted as a research prototype rather than a production healthcare system.

Current limitations include:

### Synthetic benchmark

The current evaluation contains only 20 controlled cases.

The results should therefore not be generalized to real healthcare claims populations.

### Limited policy corpus

The current policy corpus is intentionally small and designed to expose specific grounding and validation behaviors.

### Simplified knowledge graph

Real healthcare policy relationships involve significantly more dimensions, including:

- plan-specific coverage
- jurisdiction
- effective dates
- diagnosis combinations
- clinical criteria
- provider contracts
- authorization history
- payer-specific rules

These are not fully represented in v1.

### Single local LLM

The benchmark currently uses one local generation model.

Model-level comparisons are outside the current experimental scope.

### Prototype metrics

The current benchmark emphasizes unsupported claims and abstention.

A larger study would require more extensive measurement of citation correctness, calibration, explanation faithfulness, retrieval recall, and inter-rater evaluation.

---

# Future Work

Potential extensions include:

- larger controlled evaluation datasets
- real-world public healthcare policy documents
- temporal policy validity
- authority and payer relationships
- claim-level provenance chains
- automated citation verification
- confidence calibration
- human-in-the-loop verification
- multi-model evaluation
- repeated-run robustness testing
- statistical significance testing
- policy contradiction detection
- expanded graph schemas
- retrieval and generation ablation studies

These extensions are intentionally left outside the v1 prototype so the current experiment remains focused on the effect of evidence validation and bounded generation.

---

# Project Status

**v1 Research Prototype — Implementation Complete**

Current implementation includes:

```text
✓ Semantic RAG baseline
✓ Knowledge-graph-grounded RAG
✓ Deterministic evidence validation
✓ Bounded generation
✓ Explicit abstention
✓ Provenance tracking
✓ 20-case comparative benchmark
✓ Experiment logging
✓ Automated tests
```

---

## Disclaimer

Project M uses synthetic/sample healthcare data and simplified policy relationships for research and educational experimentation.

It is **not a clinical decision system, claims adjudication system, or medical advice tool**, and its outputs should not be used to make real healthcare coverage or treatment decisions.
