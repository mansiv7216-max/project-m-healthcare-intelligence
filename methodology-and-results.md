# Project M Healthcare Intelligence
## Methodology and Experimental Results

## 1. Project Objective

Project M Healthcare Intelligence is an experimental healthcare decision-intelligence system designed to investigate whether stronger grounding and evidence-validation mechanisms can reduce unsupported outputs from Large Language Models (LLMs).

The project focuses on a central reliability problem in Retrieval-Augmented Generation (RAG):

Retrieving relevant information does not necessarily guarantee that the generated answer is supported by that information.

Semantic similarity can retrieve plausible evidence while still failing to establish whether the evidence actually supports the relationship asserted in a user's question.

To study this problem, Project M implements and compares three progressively constrained architectures:

- Mode A: Conventional Semantic RAG
- Mode B: Knowledge Graph + RAG
- Mode C: Knowledge Graph + Deterministic Validation + Bounded Generation

The primary research question is:

Does structured relational grounding combined with deterministic evidence validation and bounded generation reduce unsupported LLM outputs compared with conventional semantic RAG?


## 2. System Architecture

The experiment separates retrieval, relational grounding, deterministic validation, and language generation so that their effects can be compared independently.

The same healthcare policy domain and local language-model environment are used across the experimental modes.


## 3. Mode A — Conventional Semantic RAG

Mode A represents the semantic-RAG baseline.

Pipeline:

Question
  |
  v
Sentence Embedding
  |
  v
FAISS Similarity Search
  |
  v
Top-K Policy Chunks
  |
  v
Local LLM
  |
  v
Generated Answer

Policy documents are divided into text chunks and embedded using the `all-MiniLM-L6-v2` sentence-transformer model.

FAISS performs similarity-based retrieval and returns the highest-ranking policy chunks.

The retrieved text is supplied directly to the language model.

Mode A intentionally excludes:

- Neo4j knowledge-graph grounding
- deterministic evidence validation
- validated evidence packages
- explicit relationship verification

This provides the conventional semantic-RAG baseline against which the more structured architectures can be compared.

An important behavior observed during development was that semantic retrieval could rank a semantically related but non-exact procedure above the exact procedure requested.

For example, when querying whether procedure 70553 requires prior authorization, a policy chunk concerning procedure 70551 received a similarity score extremely close to, and slightly higher than, the exact 70553 evidence.

This illustrates a central limitation being investigated in this project:

Semantic similarity is not equivalent to factual or relational validity.


## 4. Mode B — Knowledge Graph + RAG

Mode B adds structured relational grounding.

Pipeline:

Question
  |
  v
Semantic Retrieval
  |
  v
Neo4j Knowledge Graph
  |
  v
Procedure / Policy / Requirement Context
  |
  v
Local LLM
  |
  v
Generated Answer

The Neo4j knowledge graph explicitly represents relationships among healthcare entities including:

- Claims
- Members
- Providers
- Procedures
- Diagnoses
- Policies
- Requirements

Example graph relationships include:

Procedure
  |
  +-- GOVERNED_BY --> Policy
                         |
                         +-- REQUIRES --> Requirement

For a procedure query, Mode B can therefore retrieve structured information describing the procedure, governing policy, and associated authorization requirement.

This gives the LLM both semantic information and structured relational context.

However, Mode B intentionally does not enforce deterministic evidence validation before generation.

The language model is still permitted to interpret the retrieved graph context.

This distinction is important because structured retrieval alone does not guarantee that every assertion contained in the question has been validated.

For example, the graph may establish:

Procedure 70553
  -> governed by a policy
  -> requiring prior authorization

but this does not automatically establish:

Medicare
  -> requires prior authorization
  -> for procedure 70553

unless the Medicare relationship itself exists and has been validated.


## 5. Mode C — Validated / Bounded RAG

Mode C introduces an explicit deterministic evidence-validation boundary before generation.

Pipeline:

Question
  |
  v
Knowledge Graph
  |
  v
Structured Relationship Retrieval
  |
  v
Deterministic Evidence Validation
  |
  v
Validated Evidence Package
  |
  v
Evidence Boundary
  |
  v
Bounded Local LLM
  |
  v
Answer OR Abstention

Mode C separates two responsibilities:

1. Determining whether an assertion is supported.
2. Explaining supported evidence in natural language.

The language model is responsible for the second task, not the first.

Before generation, deterministic logic evaluates whether the requested relationship exists in the available evidence.

The validation layer distinguishes evidence states including:

- required authorization
- conditional authorization
- insufficient policy evidence
- unsupported authority relationships
- missing procedures

The validated evidence package contains structured facts, policy evidence, provenance, and generation constraints.

Generation constraints include:

- the model may not invent missing facts
- the model may not use unsupported external policy knowledge
- the model may not override deterministic validation
- unsupported assertions must result in abstention
- generation can be prevented entirely when evidence is insufficient

For unsupported authority assertions, the system does not ask the language model to determine whether the assertion is true.

Instead, the deterministic layer returns an unsupported validation state and the generation path is blocked.

This creates a hard evidence boundary rather than relying only on prompting the LLM to behave cautiously.


## 6. Conditional Evidence

A further distinction was introduced between required and conditional authorization.

For example:

Procedure 70553:
Authorization rule = REQUIRED

Procedure 70551:
Authorization rule = CONDITIONAL
Condition = Depends on clinical condition and plan rules.

This distinction prevents conditional evidence from being converted into an unconditional statement.

This is particularly important in decision-support systems because a retrieved statement may be relevant while still being insufficient to justify a definitive conclusion.


## 7. Unsupported Authority Assertions

The benchmark also tests questions that introduce authorities not represented by the validated evidence.

Examples include questions about:

- Medicare
- Medicaid
- CMS
- Federal policy

The knowledge graph may contain a procedure-policy relationship without containing any validated relationship between that policy and one of these authorities.

Modes A and B may still produce plausible answers because the retrieved context contains related authorization information.

Mode C instead checks whether the requested authority relationship is actually represented.

If the relationship cannot be validated, the system abstains.

Example:

Question:
What does Medicare require for procedure 70553?

Available validated evidence:
Procedure 70553 is governed by the Advanced Imaging Coverage Policy, which contains a prior-authorization requirement.

Missing evidence:
No validated relationship establishes that this policy represents Medicare.

Mode C therefore returns an abstention rather than attributing the requirement to Medicare.


## 8. Experimental Benchmark

A controlled 20-case benchmark was created to compare the three architectures.

The benchmark contains multiple evidence conditions, including:

- exact supported procedures
- conditional procedure requirements
- unknown procedures
- unsupported authority claims

Each benchmark case contains an expected behavior such as:

ANSWER

or

ABSTAIN

All three modes are evaluated against the same cases.

The experiment therefore evaluates the effect of progressively stronger grounding and validation rather than testing unrelated question sets.


## 9. Evaluation Metrics

The current benchmark measures:

- Overall Accuracy
- Answer Accuracy
- Abstention Accuracy
- Unsupported Claim Rate
- Number of Unsupported Answers

The broader evaluation framework also identifies future metrics including:

- Citation Accuracy
- Numeric Fidelity
- Decision Agreement
- Policy Fidelity
- Evidence Completeness
- Explanation Faithfulness

Unsupported Claim Rate is particularly important for the current experiment because the project is concerned not only with whether a generated answer sounds correct, but whether the system had sufficient evidence to make the assertion at all.


## 10. Benchmark Results

The completed 20-case benchmark produced the following results.

### Mode A — Conventional Semantic RAG

Overall Accuracy: 60.0%

Answer Accuracy: 100.0%

Abstention Accuracy: 33.3%

Unsupported Claim Rate: 66.7%

Unsupported Answers: 8


### Mode B — Knowledge Graph + RAG

Overall Accuracy: 65.0%

Answer Accuracy: 100.0%

Abstention Accuracy: 41.7%

Unsupported Claim Rate: 58.3%

Unsupported Answers: 7


### Mode C — Validated / Bounded RAG

Overall Accuracy: 85.0%

Answer Accuracy: 62.5%

Abstention Accuracy: 100.0%

Unsupported Claim Rate: 0.0%

Unsupported Answers: 0


## 11. Results Summary

The prototype benchmark shows a clear difference in system behavior across the three architectures.

Mode A performed well when the available evidence directly supported an answer, but frequently answered questions for which the available evidence did not validate the requested assertion.

Mode B improved overall performance slightly by introducing structured knowledge-graph relationships. However, the presence of structured context did not completely prevent unsupported generation because the language model could still interpret valid graph evidence as support for a relationship that had not actually been established.

Mode C produced the strongest overall accuracy in the current benchmark and eliminated unsupported answers in the evaluated cases.

Its main trade-off was lower answer accuracy.

This occurred because the architecture deliberately preferred abstention when the deterministic evidence layer could not establish sufficient support.

Therefore, the result should not be interpreted simply as "Mode C answers more questions correctly."

Instead, the prototype suggests a more specific architectural trade-off:

Increasing evidence constraints can reduce unsupported generation, but may also increase conservative behavior when the available structured evidence is incomplete.


## 12. Key Experimental Observation

The strongest observation from the current prototype is:

Retrieval quality and generation reliability are related but distinct problems.

Semantic retrieval can locate relevant information without proving that the information supports the exact assertion being made.

Knowledge graphs improve relational context, but relational retrieval alone still leaves interpretation to the language model.

The deterministic validation layer changes the architecture by requiring evidence support before generation.

The comparison therefore progresses from:

Semantic similarity

to:

Structured relational grounding

to:

Validated relational grounding with an explicit evidence boundary.


## 13. Interpretation

The current results should be treated as prototype experimental evidence rather than a generalized conclusion about healthcare AI systems.

The benchmark uses a small controlled dataset and a limited policy domain.

The experiment does not establish that bounded RAG universally outperforms conventional RAG.

Instead, it demonstrates that the implemented architecture can measurably change unsupported-generation behavior under controlled evidence conditions.

This distinction is important for trustworthy-AI research.

A system that answers fewer questions may be preferable in some high-stakes settings if its unanswered questions correspond to cases where evidence is genuinely insufficient.

In such environments, abstention is not necessarily system failure.

It can be an intentional reliability mechanism.


## 14. Technology Stack

The prototype currently uses:

- Python
- Neo4j
- FAISS
- Sentence Transformers
- all-MiniLM-L6-v2 embeddings
- Ollama
- Qwen2.5 7B Instruct
- pytest
- JSON experiment logging
- Git / GitHub

The LLM is executed locally through Ollama.

Experimental generation uses a fixed model configuration with temperature set to 0.0 to reduce unnecessary variation between runs.


## 15. Reproducibility and Experiment Logging

Experiment outputs are stored as JSON artifacts.

The logs preserve information such as:

- experiment identifier
- question
- experimental mode
- retrieved evidence
- graph context
- validation state
- generated response
- model configuration
- whether generation was invoked

The comparative benchmark also produces machine-readable JSON results and a CSV summary.

This allows individual failures to be inspected rather than relying only on aggregate accuracy values.


## 16. Current Limitations

The current implementation has several important limitations.

First, the benchmark contains only 20 controlled cases and should be expanded before drawing stronger conclusions.

Second, the healthcare policy corpus is intentionally small.

Third, the knowledge graph represents only a limited number of entities and relationships.

Fourth, authority relationships such as Medicare, Medicaid, CMS, or individual payer rules are intentionally absent unless explicitly modeled.

Fifth, deterministic validation depends on the completeness and correctness of the structured knowledge graph.

Finally, temperature 0 reduces generation variability but does not by itself guarantee perfect reproducibility across every model/runtime configuration.


## 17. Future Work

Future development can extend the experiment through:

- a larger healthcare policy corpus
- additional procedure and diagnosis codes
- multiple payer and authority relationships
- larger benchmark datasets
- repeated generation trials
- citation-level evaluation
- evidence-completeness scoring
- explanation-faithfulness evaluation
- adversarial and ambiguous questions
- contradictory policy evidence
- temporal policy/version tracking
- human reviewer evaluation
- confidence calibration
- comparison across additional language models

A particularly important extension is to evaluate whether the reduction in unsupported claims persists as graph complexity and policy-document volume increase.


## 18. Conclusion

Project M Healthcare Intelligence investigates a specific reliability problem in enterprise AI:

Relevant retrieval does not necessarily mean validated evidence.

The prototype compares conventional semantic RAG, knowledge-graph-grounded RAG, and a bounded architecture that introduces deterministic validation before language generation.

In the current 20-case benchmark, Mode C achieved:

85.0% overall accuracy,
100.0% abstention accuracy,
0.0% unsupported claim rate,
and 0 unsupported answers.

By comparison, the semantic-RAG baseline produced a 66.7% unsupported claim rate, while Knowledge Graph + RAG produced a 58.3% unsupported claim rate.

These results are preliminary and specific to the controlled prototype.

However, they support continued investigation into architectures where the LLM is not responsible for deciding whether evidence exists.

Instead, structured systems establish what is supported, and the language model is used primarily to communicate that validated evidence.

That distinction forms the central design principle of Project M:

Retrieve for relevance.
Validate for support.
Generate within the evidence boundary.
