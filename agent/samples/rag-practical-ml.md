# Retrieval-Augmented Generation (RAG)

## Grounding language models with external knowledge

Large language models generate fluent answers from patterns learned during training, but their internal knowledge can be outdated, incomplete, or difficult to verify. **Retrieval-Augmented Generation (RAG)** adds a search step: the system retrieves relevant evidence from a trusted collection and gives that evidence to the model before it answers.

### Learning goals

After this lesson, you should be able to:

- explain why retrieval can make an LLM application more useful and auditable;
- design a basic RAG pipeline from documents to grounded answers;
- choose sensible chunking, retrieval, and prompting strategies;
- evaluate retrieval quality separately from answer quality; and
- diagnose common RAG failure modes.

---

## 1. The core idea

A standard LLM answers from the information represented in its parameters. A RAG system instead combines two components:

1. **Retriever:** finds passages that are likely to contain evidence for the user's question.
2. **Generator:** produces an answer conditioned on the question and the retrieved passages.

The basic inference flow is:

> user question → retrieve top-k passages → assemble a grounded prompt → generate answer with citations

RAG does not make a model automatically truthful. It gives the model better evidence and gives the application a way to show where an answer came from.

---

## 2. Offline indexing pipeline

Before users can search a collection, the documents must be prepared.

1. **Collect and clean:** load PDFs, webpages, notes, or database records; remove navigation noise and duplicated text.
2. **Chunk:** split documents into passages small enough to retrieve precisely but large enough to preserve meaning.
3. **Represent:** compute an embedding for each chunk, or create a lexical search index such as BM25.
4. **Store metadata:** keep source, title, section, date, permissions, and a stable document identifier.
5. **Index:** write the vectors and metadata to a searchable store.

Chunking is a modeling decision. Very small chunks may lose context; very large chunks may contain too much irrelevant text. Start with structure-aware chunks based on headings and paragraphs, then tune using retrieval evaluation.

---

## 3. Online question-answering pipeline

At query time, the system performs these steps:

1. Normalize or rewrite the question when necessary.
2. Retrieve candidate chunks using dense, lexical, or hybrid search.
3. Optionally rerank the candidates with a stronger relevance model.
4. Select a small evidence set that fits the context window.
5. Prompt the LLM to answer only from the supplied evidence.
6. Return the answer together with source references.

```python
def answer(question, index, llm, k=5):
    candidates = index.search(question, top_k=20)
    evidence = rerank(question, candidates)[:k]
    prompt = build_grounded_prompt(question, evidence)
    response = llm.generate(prompt)
    return response, sources(evidence)
```

This separation is useful in practice: retrieval can be improved without changing the generator, and generation can be improved without rebuilding the index.

---

## 4. Retrieval choices

### Lexical retrieval

Methods such as BM25 work well when exact terms matter: names, identifiers, formulas, and domain vocabulary.

### Dense retrieval

Embedding search can match semantically similar language even when the query and document use different words.

### Hybrid retrieval

Combining lexical and dense scores is often a strong baseline because the two approaches fail in different ways.

### Reranking

A reranker reads the query and each candidate together, then produces a more precise relevance score. It costs more computation, so it is normally applied only to a small candidate set.

---

## 5. Grounded prompting

A useful RAG prompt makes the evidence boundary explicit:

```text
You are a course assistant. Answer the question using only the sources below.
If the sources do not contain enough information, say what is missing.
Cite the source identifiers that support each important claim.

Sources:
[S1] ...
[S2] ...

Question: ...
```

Good application behavior includes refusing unsupported claims, preserving source identifiers, and separating retrieved evidence from user-provided instructions. Retrieved documents are data, not trusted system instructions.

---

## 6. Evaluate the pipeline in two stages

### Retrieval evaluation

Create a small set of realistic questions with known relevant passages. Measure whether relevant evidence appears near the top using metrics such as **Recall@k**, **MRR**, or **nDCG**.

### Answer evaluation

Given the retrieved evidence, evaluate:

- **Correctness:** does the answer address the question accurately?
- **Faithfulness:** are the claims supported by the supplied sources?
- **Completeness:** does it cover the important parts of the answer?
- **Citation quality:** do citations point to the passages that support the claims?
- **Abstention:** does the system admit when evidence is insufficient?

Always inspect retrieval first. A generator cannot reliably recover information that was never retrieved.

---

## 7. Common failure modes

| Failure | Typical cause | Practical response |
|---|---|---|
| Relevant document is never found | weak query, poor chunking, missing index data | inspect Recall@k; add hybrid search or query expansion |
| Right document, wrong passage | chunks are too large or boundaries are poor | use headings and overlap; rerank passages |
| Answer ignores good evidence | prompt is vague or context is noisy | reduce context; require evidence-bound claims |
| Confident unsupported answer | no abstention rule | require “insufficient evidence” behavior and test it |
| Stale answer | index is not refreshed | add document timestamps and an update pipeline |
| Private data is exposed | permissions are checked too late | filter by access rights before retrieval |
| Retrieved prompt injection | documents contain malicious instructions | isolate content, sanitize inputs, and treat sources as untrusted data |

---

## 8. Practical ML exercise

Build a small RAG baseline over a set of course notes.

1. Prepare 20–50 documents and store source metadata.
2. Implement a chunking strategy and record its parameters.
3. Build one lexical or dense retriever.
4. Write ten questions with expected supporting passages.
5. Measure Recall@5 and inspect every failed query.
6. Add one improvement—hybrid retrieval, reranking, or better chunking—and compare results.
7. Generate answers with citations and manually label correctness and faithfulness.

**Discussion question:** If the final answer is wrong, how can you determine whether retrieval, prompt construction, or generation caused the failure?

---

## Takeaways

- RAG connects an LLM to external, updateable, and inspectable knowledge.
- A reliable system separates indexing, retrieval, context construction, and generation.
- Hybrid retrieval plus reranking is a useful practical baseline.
- Retrieval quality and answer quality must be measured separately.
- Citations, abstention, access control, and prompt-injection defenses are part of the system—not optional extras.
