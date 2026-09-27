# Prompt Register — CloudServe Intelligent Support System

This directory houses the version-controlled prompt templates used across system execution and evaluation.

| Prompt ID | File | Category | Serves Requirement | Version | Description |
|-----------|------|----------|--------------------|---------|-------------|
| PR-01 | `build/classify_prompt.txt` | Build | FR-02, A3 | 1.0 | Intent classification across 22 classes + urgency detection |
| PR-02 | `build/guardrails_prompt.txt` | Build | FR-06, A7 | 1.0 | Detection of PII, security redlines, compliance, and mandatory escalations |
| PR-03 | `build/generate_prompt.txt` | Build | FR-05, A6 | 1.0 | Grounded answer drafting with mandatory passage citations |
| PR-04 | `evaluation/eval_judge_prompt.txt` | Evaluation | FR-10, A10 | 1.0 | LLM-as-a-judge rubric evaluating citation precision and hallucination prevention |
