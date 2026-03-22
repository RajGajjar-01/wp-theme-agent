# Comprehensive Playbook for Verifying, Validating, and Continuously Assuring AI Agents

## Executive summary
A pragmatic, defensible verification and validation (V&V) program for AI agents combines: (1) rigorous component‑level tests (unit/property/fuzzing), (2) structured integration and end‑to‑end evaluations (including RAG/tool‑use traces), (3) adversarial and chaos‑style robustness testing, and (4) continuous production observability with human‑in‑the‑loop feedback and automated CI/CD gates. Implementing such a lifecycle reduces incidents and accelerates reliable delivery, but requires explicit metrics, clear instrumentation, reproducible datasets, and governance controls across the toolchain. The sections below provide an actionable methodology, concrete test templates and thresholds supported by the literature and vendor guidance, mappings to widely used tools, CI/CD patterns, and reusable artifacts that can be applied immediately.

## 1. High‑level V&V lifecycle and governing principles
- Adopt a three‑axis approach: pre‑deployment simulation and offline validation, runtime observability and continuous evaluation, and iterative improvement informed by production signals and human review. This three‑axis approach reduces incidents relative to ad‑hoc testing and supports ongoing drift detection [1].  
- Treat agent evaluation as probabilistic and behavior‑based rather than purely deterministic; adopt metrics and human judgment where outputs are subjective or non‑deterministic [1], [2].  
- Instrument the full agent trace (inputs, intermediate steps, tool calls, retrieved context, final output) to enable reproducible audits and component‑level scoring [3], [4].  

Sources: [1], [2], [3], [4]

## 2. Verification & validation framework (component → integration → system)
A layered testing framework maps test types to system scope and expected guarantees.

### 2.1 Component (Unit) level
Goal: verify individual modules (LLM calls, retriever, tool adapters, memory, prompt templates).
- Unit tests: deterministic checks for wrappers, input/output schema, prompt formatting, and tool call argument validation; automated generation of additional test cases via AI‑assisted unit testing where available [5], [6].  
- Property/spec‑based tests: express universal properties (e.g., “tool output must be syntactically valid JSON” or “retriever must return at least N docs when corpus size > M”) and generate large input sets to find edge cases using PBT/fuzzing patterns [7], [8], [9], [10], [11].  
- Fast feedback: property tests should run quickly and be incorporated in pre‑merge CI jobs; agents can assist in test generation for high coverage when safe to do so [5], [6], [11].

Sources: [5], [6], [7], [8], [9], [10], [11]

### 2.2 Integration level
Goal: verify interactions between components (retrieval→LLM→tool→external API), including correctness of data flows and side effects.
- Integration tests: validate step sequencing, tool‑invocation correctness, argument mapping, and failure handling (retry/compensating actions). Use sandboxed integrations for external services to assert idempotency and data integrity before production rollout [12], [13].  
- Workflow/step‑level testing: isolate and test individual steps (retriever, planner, executor) with controlled traces to simplify debugging [4].  
- Synthetic simulations: run workflows in simulated environments for multi‑step tasks to expose composition errors [1], [4].

Sources: [12], [13], [4], [1]

### 2.3 System / end‑to‑end level
Goal: validate complete agent behavior on representative end‑user tasks including multi‑turn consistency and goal achievement.
- End‑to‑end tests and scenario simulations: evaluate full trajectories, sequence of actions, and business outcomes using golden datasets and success criteria (task success, action correctness, user satisfaction) [1], [14].  
- Regression suites: capture golden traces and enforce metrics (e.g., similarity thresholds) to detect semantic regressions [15].  
- Multi‑turn and long‑horizon behavior: test for conversational state stability and drift across turns (intent preservation, hallucination propagation) using dedicated regression scenarios [16].  

Sources: [1], [14], [15], [16]

## 3. Adversarial, safety, and robustness testing
- Red‑teaming/adversarial prompt testing: use structured red‑team exercises to find jailbreaks, prompt injections, bias, toxicity, and hallucination triggers with iterative attack enhancement, execution, and scoring against defined metrics [17], [18], [19], [20].  
- Retrieval/Citation attacks: systematically probe retrieval→generation pipelines for unsafe or misleading citations using adversarial query generation strategies [21].  
- Security testing: integrate AI‑specific security tests (prompt injection, model inversion) into the pipeline, and treat agent identities in IAM systems with the same rigor as human actors for authentication and continuous monitoring [22], [1].  
- Chaos and stress testing: run chaos experiments that exercise scale, cascading failures, and abnormal inputs to expose runaways and interaction failures—AI‑driven chaos engines have demonstrated substantial reductions in unexpected failures when integrated with observability [23], [24].  

Sources: [17], [18], [19], [21], [22], [23], [24]

## 4. Continuous validation in CI/CD and production
- Continuous AI evaluation pipelines (CAIP): replace or augment traditional CI with pipelines that rerun behavioral, safety, and regression tests on model or dataset changes, and provide an auditable trail [25], [26].  
- Canary, shadow, A/B testing: begin with shadowing and canary traffic (1% → 100% ramp) and move to controlled A/B splits (5–10% after offline gates) with explicit rollback triggers for latency, cost, or safety regressions [27], [28], [29].  
- Human‑in‑the‑loop gates: use approval flows, interrupt/resume patterns, or human‑as‑tool integrations for high‑risk decisions and to collect labels for continuous improvement [30], [31].  
- Production continuous evaluation: evaluate real traffic in real‑time for drift, quality, and safety, and feed human annotation queues for triage and model updates [3], [32].

Sources: [25], [26], [27], [28], [29], [30], [31], [3], [32]

## 5. Concrete evaluation metrics, definitions, and measurement methods
Below are component and system metrics, precise intent, and measurement notes with suggested thresholds only where evidence provides them.

### 5.1 Retrieval metrics
- Context recall: fraction of relevant documents included in retrieved set; OpenAI recommends context recall ≥ 0.85 for some scenarios [33].  
- Context precision: fraction of retrieved documents that are relevant; OpenAI suggests context precision > 0.7 in guidance [33].  
Measurement: use labeled relevance judgments or automatic proxies (embedding similarity thresholds) and report both per‑query and aggregate percentiles.

Source: [33]

### 5.2 Generation / RAG metrics
- Faithfulness / factuality (hallucination rate): fraction of generated assertions not grounded in provided context or external knowledge; measure via human labels, LLM judges, or hybrid checks (RAGAS and TruLens use triad metrics for groundedness) [34], [35].  
- Answer relevancy / correctness: semantic match between generated answer and golden answer; OpenAI suggests ≥ 70% positively rated answers as a quality baseline in some contexts [33].  
Measurement: combine reference‑based metrics (BLEU/ROUGE where applicable), LLM‑as‑judge scoring, and human review; RAGAS defines component metrics (context_relevancy, context_recall, faithfulness, answer_relevancy) for RAG pipelines [34].

Sources: [34], [33], [35]

### 5.3 Tool‑invocation correctness and plan adherence
- Tool call accuracy: correctness of tool selection and correctness of tool arguments; measure by comparing observed tool calls to expected ones and by end‑state verification for side effects [33], [35].  
- Plan‑Action alignment: evaluates whether an agent executed its planned actions; TruLens describes Goal‑Plan‑Action alignment scoring for traces [35].

Source: [35], [33]

### 5.4 Consistency, calibration, and confidence
- Calibration: relationship between model confidence (probabilities or calibrated scores) and observed accuracy; measure reliability diagrams and expected calibration error on held‑out tasks. (Evidence indicates calibration checks are part of evaluation best practices but does not provide numeric thresholds.) [1], [3]

Sources: [1], [3]

### 5.5 Latency, throughput, and cost
- Latency percentiles (P95, time‑to‑first‑token), throughput, and token cost per request; monitor these metrics in production and use them as A/B or canary rollback criteria [36], [27].  
Measurement: collect per‑trace timings (first token, tail latency) and per‑trace token usage.

Source: [36], [27]

### 5.6 Robustness to distribution shift and regression
- Semantic regression detection: use similarity scores and reference comparisons; one example flagged outliers below 0.68 similarity in an LLM regression tutorial, and classification regression suites often enforce ≥ 90% accuracy thresholds where appropriate [15], [37].  
Measurement: periodic re‑evaluation on curated drift datasets and production slices.

Sources: [15], [37]

### 5.7 Safety, privacy, and bias
- Toxicity, PII leakage, prompt injection detection: configure alerts and automated checks for these classes of failures and integrate them into CI/CD gates and production monitoring [38], [39].  
Measurement: automated detectors for PII/toxicity and human review queues for ambiguous cases.

Sources: [38], [39]

### 5.8 Example threshold guidance (evidence‑backed)
- Context recall ≥ 0.85; context precision > 0.7; ≥ 70% positively rated answers (OpenAI guidance) [33].  
- Regression test similarity threshold: 0.68 flagged as outlier in one tutorial [15].  
- Classification regression baseline: 90% accuracy used as an enforcement example in one tutorial [37].  
Use these as starting baselines and adapt to domain risk and business requirements.

Sources: [33], [15], [37]

## 6. Concrete test strategies, templates, and example cases
- Unit test template: assert prompt templates produce valid JSON output; mock LLM and tool adapters to return deterministic responses; run property tests generating 1,000+ inputs for schema invariants (use PBT/fuzzing where possible) [7], [11].  
- Integration test template: replay a trace where retriever returns a known doc, assert correct tool selection and correct API argument values, then assert end state via sandboxed side‑effects [12], [13].  
- End‑to‑end scenario template: golden dataset of multi‑turn tasks where success criteria are explicit (task success boolean, number of steps, user satisfaction score); run both offline and shadowed online to validate behavior before full rollout [1], [14].  
- Adversarial test cases: curated jailbreaks, prompt injection probes, and retrieval‑poisoning prompts; use red‑team generation workflows (attack→enhance→execute→score) [17], [18], [19].  
- RAG test suite: separate retrieval and generation tests—measure context_precision, context_recall, faithfulness, and answer_relevancy per RAGAS guidance [34].  
- Voice/multimodal cases: regression test voice‑agent intent stability and ASR/NLU changes since small ASR shifts cascade into different dialogue outcomes [40].  

Sources: [7], [11], [12], [13], [1], [14], [17], [18], [19], [34], [40]

## 7. Tooling map: which platform for which tasks (strengths, caveats, integration notes)
Each tool below is mapped to evaluation/observability tasks and practical integration patterns. All entries reference vendor documentation or primary repos.

- LangSmith (LangChain): end‑to‑end evaluation, traces (step/trajectory), CI/CD integration with pytest/GitHub Actions, RAG separation of retrieval vs generation quality, annotation queues for human review, offline and online evaluation support [3].  
  Use for: CI gating, offline dataset testing, agent trajectory analysis. Integration: Python API, GitHub Actions examples; supports custom evaluators.

Source: [3]

- Langfuse: detailed trace/span observability (Gantt charts), latency/cost/token dashboards, OpenTelemetry support and self‑host options with token redaction, manual ratings and A/B testing features [36], [5].  
  Use for: production trace capture, latency/cost monitoring, prompt management. Integration: SDKs for Python/JS, OpenTelemetry instrumentation.

Sources: [36], [5]

- TruLens: open‑source trace evaluation, Goal‑Plan‑Action scoring, RAG Triad (context relevance, answer relevance, groundedness), OpenTelemetry integration and feedback/scoring functions [35].  
  Use for: chain‑aware scoring, plan‑action alignment, trace pre‑processing. Integration: Python SDK and trace ingestion.

Source: [35]

- OpenAI Evals: standardized datasets, templates for question answering, model‑graded evaluations, and guidance with suggested numeric thresholds for retrieval/generation metrics [33], [41].  
  Use for: reference and model‑graded evals, CI test templates. Integration: pip install evals and local runs or custom model endpoints.

Sources: [33], [41]

- DeepEval / Deepchecks: research‑backed metrics for task completion, tool correctness, plan adherence; synthetic dataset generation and CI integration hooks [35].  
  Use for: synthetic test generation at scale, rich metric catalog, CI automation. Integration: callback handlers for LangChain, instrumentation via decorators.

Source: [35]

- RAGAS / Ragas: component‑level RAG metrics (context_relevancy, context_recall, faithfulness, answer_relevancy) and end‑to‑end metrics for citation accuracy [34].  
  Use for: RAG pipelines where separation of retrieval and generation scoring is required. Integration: metric catalog and LLM‑based reference‑free scoring.

Source: [34]

- Arize: composite dashboards, drift detection, agent execution tree visualization, and alerting for pass rates, hallucination, and toxicity trends [35].  
  Use for: production monitoring and long‑term trend analysis; integrates with model diagnostics. Integration: ingest traces and metrics for dashboards.

Source: [35]

- Giskard: automated hallucination detection, factuality checks, bias/robustness tests, and CI integration for conversational agents [35].  
  Use for: automated tests for groundedness, business‑rule conformity, and CI gating. Integration: dataset generation and test execution in pipelines.

Source: [35]

Notes on integration patterns: instrument agent runtimes to emit OpenTelemetry spans or platform SDK traces, centralize trace storage, and connect evaluation pipelines to CI (pre‑merge) and monitoring (post‑deploy) to close feedback loops [36], [3], [35].

Sources: [36], [3], [35]

## 8. Observability, monitoring, alerting, and remediation playbooks
- Instrumentation: capture full trace per user request (prompt, retrieved context, tool calls, intermediate reasoning, model outputs, tokens, latencies, error states) using OpenTelemetry or SDKs provided by observability platforms [36], [3], [35].  
- Dashboards & alerts: expose key signals—P95 latency, avg tokens per request, hallucination rate, context precision/recall, tool‑call error rate, safety alerts (toxicity/PII). Configure threshold‑based alerts and anomaly detectors for drift [36], [35], [42].  
- Remediation loops: automated rollback on canary failures, human fallback for high‑risk outputs, and feedback ingestion pipelines that convert human labels into labeled datasets for retraining or prompt/policy updates [27], [30], [32].  
- Incident playbook example: (1) automated alert triggers investigation with trace id; (2) triage using trace explorer to determine root cause (retriever vs model vs tool); (3) isolate by switching traffic to previous model or enabling safe fallback; (4) log remediation actions and create post‑mortem; (5) feed labeled failure into regression suite [27], [3], [32].

Sources: [36], [35], [27], [30], [32], [42]

## 9. Governance, security, privacy, auditability, and reproducibility
- Governance controls: enforce identity and access management for agent identities and tool integrations; require consent checks and data‑handling workflows when agents process regulated data (GDPR/HIPAA/KYC contexts require special controls) [22], [1].  
- Auditability & lineage: retain trace logs that capture context and intermediate steps to enable audits and explainability; use annotation queues and human labels to document decision rationale [3], [32].  
- Privacy & token redaction: adopt token redaction and selective logging for PII/PHI in traces; platforms like Langfuse support token redaction for privacy protection [36].  
- Reproducibility: store deterministic evaluation datasets, seed RNGs for synthetic tests where applicable, and preserve golden traces for regression testing and audit [15], [3].

Sources: [22], [1], [36], [15], [3]

## 10. Practical CI/CD patterns and example configs
- Pre‑merge checks: run unit, property, integration, and fast end‑to‑end offline evaluations; block merges when critical thresholds (e.g., retrieval recall, tool‑call accuracy) fall below defined gates [3], [25].  
- Pre‑deploy pipelines: run full scenario suites and adversarial red‑team tests in staging; use shadow deployments to compare live performance without user exposure [27], [3].  
- Post‑deploy pipelines: enable online evaluation of a sample or all traffic, human annotation queues for flagged traces, and automated rollback on safety or latency regressions [3], [27], [32].  
- Example pattern: GitHub Actions job that runs LangSmith offline evaluation against a labeled dataset, fails build if key metrics drop; follow with a staging deployment that uses shadow traffic and Langfuse tracing before canary promotion [3], [36].

Sources: [3], [27], [36], [25]

## 11. Reusable artifacts and templates
Provided below are evidence‑supported artifacts to adopt immediately.

### 11.1 Minimal evaluation checklist (pre‑release)
- Unit tests for prompt formatting and tool adapters [5].  
- Property tests for schema invariants and retriever behavior [7].  
- Offline RAG evaluation (context precision/recall, faithfulness) using RAGAS or platform evaluators [34].  
- Red‑team basic probe pass/fail list for prompt injection and basic jailbreaks [17].  
- Shadow deployment + Langfuse/TruLens traces for staging traffic [36], [35].  

Sources: [5], [7], [34], [17], [36], [35]

### 11.2 Risk assessment matrix (example dimensions)
- Axes: likelihood (low/med/high) × impact (low/med/high). Risk categories: hallucination, PII leakage, wrong tool action, denial of service (runaway calls), biased output. Map mitigations: human‑in‑loop, automatic filters, access controls, rollback. (Matrix design is supported as a practice across guidance though no single numeric table is prescribed by sources) [1], [38].

Sources: [1], [38]

### 11.3 CI test config template (conceptual)
- Stage 1 (pre‑merge): run unit/property tests, fail on critical assertion. (LangSmith supports pytest integration.) [3], [7]  
- Stage 2 (staging): run offline dataset end‑to‑end evaluations and RAGAS metrics; spin up shadow deployment. [34], [3]  
- Stage 3 (production): canary 1% → 5–10% → 100% with automated rollback triggers for latency/cost/safety metrics. [27], [3]

Sources: [3], [7], [34], [27]

### 11.4 Sample test suites and datasets
- Golden multi‑turn workflows for end‑to‑end success tests (store as JSONL for reproducibility). [14], [15]  
- RAG retrieval relevance sets (queries with labeled relevant docs) for context_recall and context_precision tests [34].  
- Adversarial prompt catalog and evolving attack set from red‑team exercises used in CI [17], [18].

Sources: [14], [15], [34], [17], [18]

## 12. Variation by agent type and hosting
- RAG / retrieval‑augmented agents: prioritize retrieval metrics (context_recall/precision), citation accuracy, and RAG‑specific faithfulness checks; use RAGAS and Ragas metrics for component separation [34].  
- Tool‑using agents: emphasize tool‑call correctness, argument validation, idempotency tests, and sandboxed integration tests before production [12], [33].  
- Multi‑agent systems: require modular testing, golden datasets for end‑to‑end scenarios, and continuously updated golden datasets for regression across interacting agents [25], [26].  
- Multimodal and voice agents: include ASR/NLU regression testing and multimodal synchronization tests (audio/video) because small ASR/NLU shifts can cascade into dialogue failures [40], [14].  
- Hosting models (self‑hosted vs hosted APIs): adapt testing to access patterns—self‑hosted allows deeper instrumentation and possibly formal verification for certain components; hosted APIs rely more on trace‑level instrumentation and external observability [3], [35], [21].  

Sources: [34], [12], [25], [26], [40], [14], [3], [35], [21]

## 13. Formal/spec techniques and evidence limitations
- Formal specification is applicable to some agent subdomains (temporal behavior, certain robotics/vision pipelines), and formal languages like Temporal Logic are used when precise behavior must be guaranteed; however scalability and applicability vary by domain and component [41], [42], [43], [44].  
- Evidence shows promising advances (abstraction/refinement and provable robustness for generative models) but also highlights scalability challenges for large vision and agent systems [44], [43]. Use formal methods selectively for the highest‑risk components where tractable.

Sources: [41], [42], [43], [44]

## 14. Evidence gaps
- There is limited prescriptive, domain‑agnostic numeric thresholds for many metrics; available thresholds are example‑based (OpenAI examples and tutorials) rather than universal [33], [15], [37].  
- Formal verification for large multimodal LLM agents is noted as promising but with scalability challenges; the evidence does not provide turnkey formal verification recipes for typical LLM agent stacks [44], [43].  
- Comparative empirical studies showing exact tradeoffs between different observability stacks under identical workloads are not present in the provided evidence.

Sources: [33], [15], [37], [44], [43]

## 15. Recommended next steps (practical roadmap)
1. Instrument traces end‑to‑end using OpenTelemetry or platform SDKs (Langfuse/TruLens) and capture token/latency/tool calls immediately [36], [35].  
2. Establish pre‑merge CI: unit + property tests, and integrate LangSmith offline evaluations for regression gating [3], [7].  
3. Build RAG component tests with labeled retrieval sets and run RAGAS metrics to separate retrieval vs generation failures [34].  
4. Run structured red‑team exercises and add discovered attacks to the CI adversarial suite; integrate automated PII/toxicity checks [17], [38].  
5. Deploy shadowed canaries with online evaluation and human annotation queues (LangSmith/TruLens) and define rollback triggers for latency/cost/safety [3], [35], [27].  
6. Iterate: convert human labels into retraining/finetuning or prompt/policy updates and re‑run evaluation pipelines (CAIP) on every model/dataset change [25], [32].

Sources: [36], [35], [3], [7], [34], [17], [38], [27], [25], [32]

## References
[1] https://getmaxim.ai/articles/a-comprehensive-guide-to-testing-and-evaluating-ai-agents-in-production/  
[2] https://datagrid.com/blog/4-frameworks-test-non-deterministic-ai-agents  
[3] https://langchain.com/langsmith/evaluation  
[4] https://getmaxim.ai/articles/exploring-effective-testing-frameworks-for-ai-agents-in-real-world-scenarios/  
[5] https://sparkco.ai/blog/mastering-unit-testing-for-ai-agents-a-deep-dive  
[6] https://tricentis.com/learn/ai-unit-testing  
[7] https://kiro.dev/blog/property-based-testing/  
[8] https://kiro.dev/docs/specs/correctness/  
[9] https://digitalcommons.dartmouth.edu/dissertations/420/  
[10] https://andrewhead.info/assets/pdf/pbt-in-practice.pdf  
[11] https://red.anthropic.com/2026/property-based-testing/  
[12] https://getknit.dev/blog/integrations-for-ai-agents  
[13] https://mabl.com/blog/ai-agent-frameworks-end-to-end-test-automation  
[14] https://toloka.ai/blog/ai-agent-evaluation-methodologies-challenges-and-emerging-standards/  
[15] https://evidentlyai.com/blog/llm-regression-testing-tutorial  
[16] https://getmaxim.ai/articles/5-strategies-for-a-b-testing-for-ai-agent-deployment/  
[17] https://cobalt.io/learning-center/what-is-ai-red-teaming  
[18] https://confident-ai.com/blog/red-teaming-llms-a-step-by-step-guide  
[19] https://youtube.com/watch?v=dkpJVdZm394  
[20] https://obsidiansecurity.com/blog/ai-security-testing  
[21] https://arxiv.org/html/2510.09689v2  
[22] https://vouched.id/learn/blog/verify-ai-agent-guide  
[23] https://iaeme.com/MasterAdmin/Journal_uploads/IJRCAIT/VOLUME_7_ISSUE_2/IJRCAIT_07_02_140.pdf  
[24] https://redhat.com/en/blog/supercharging-chaos-testing-using-ai  
[25] https://medium.com/@gunashekarr11/continuous-ai-evaluation-pipelines-caip-the-future-replacing-traditional-ci-for-ai-models-e2f4a56f6f93  
[26] https://medium.com/@bhargavaparv/trust-at-scale-regression-testing-multi-agent-systems-in-continuous-deployment-environments-99dfcc5872e9  
[27] https://getmaxim.ai/articles/5-strategies-for-a-b-testing-for-ai-agent-deployment/  
[28] https://qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models  
[29] https://blog.christianposta.com/deploy/blue-green-deployments-a-b-testing-and-canary-releases/  
[30] https://dev.to/camelai/agents-with-human-in-the-loop-everything-you-need-to-know-3fo5  
[31] https://comet.com/site/blog/human-in-the-loop/  
[32] https://labelstud.io/learningcenter/how-to-set-up-ai-evaluation-pipelines-in-a-machine-learning-workflow/  
[33] https://developers.openai.com/api/docs/guides/evaluation-best-practices/  
[34] https://docs.ragas.io/en/stable/concepts/metrics/overview/  
[35] https://langchain.com/articles/llm-observability-tools  
[36] https://langfuse.com/docs/observability/overview  
[37] https://evidentlyai.com/blog/llm-regression-testing-tutorial  
[38] https://obsidiansecurity.com/blog/ai-security-testing  
[39] https://noveum.ai/en/blog/how-to-monitor-ai-agents-in-production  
[40] https://hamming.ai/blog/ai-voice-agent-regression-testing  
[41] https://jdeshmukh.github.io/teaching/cs699-fm-for-robotics-spring-2021/Papers/FormalSpecificationAndVerificationOfRobotsSurvey-LuckcuckEtAl.pdf  
[42] https://tencentcloud.com/techpedia/126446  
[43] https://mitras.ece.illinois.edu/research/2024/Vision_survey.pdf  
[44] https://theory.stanford.edu/~barrett/pubs/WTR+23.pdf

## 16. Code Examples for Agent Evaluation

### 16.1 LangSmith Agent Evaluation Snippets

### Run Intent Classifier and Evaluation Experiment in Python

Source: https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/tutorials/agents.mdx

This Python code snippet defines an asynchronous function to run an intent classifier node within a graph and then proceeds to run an evaluation experiment using the Langsmith client. It specifies the data to use, the evaluator function, and experiment parameters like the prefix and concurrency. The results are converted to a Pandas DataFrame.

```python
# Target function for running the relevant step
async def run_intent_classifier(inputs: dict) -> dict:
    # Note that we can access and run the intent_classifier node of our graph directly.
    command = await graph.nodes["intent_classifier"].ainvoke(inputs)
    return {"route": command.goto}


# Run evaluation
experiment_results = await client.aevaluate(
    run_intent_classifier,
    data=dataset_name,
    evaluators=[correct],
    experiment_prefix="sql-agent-gpt4o-intent-classifier",
    max_concurrency=4,
)
experiment_results.to_pandas()
```

--------------------------------

### Define and Run Evaluation in Python

Source: https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/tutorials/agents.mdx

This code defines a custom evaluation function `correct` to check if the model's predicted route matches the reference output. It then sets up an asynchronous function `run_intent_classifier` to invoke the model's intent classifier node. Finally, it uses the `aevaluate` method to run the experiment, applying the custom evaluator to the dataset.

```python
def correct(outputs: dict, reference_outputs: dict) -> bool:
    """Check if the agent chose the correct route."""
    return outputs["route"] == reference_outputs["route"]

# Target function for running the relevant step
async def run_intent_classifier(inputs: dict) -> dict:
    # Note that we can access and run the intent_classifier node of our graph directly.
    command = await graph.nodes['intent_classifier'].ainvoke(inputs)
    return {"route": command.goto}

# Run evaluation
experiment_results = await client.aevaluate(
    run_intent_classifier,
    data=dataset_name,
    evaluators=[correct],
    experiment_prefix="sql-agent-gpt4o-intent-classifier",
    max_concurrency=4,
)
```

--------------------------------

### Run Evaluation Experiment (Python)

Source: https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/index.mdx

This Python code snippet shows how to initiate an evaluation experiment in LangSmith using the `client.evaluate` method. It specifies the target function, dataset, evaluators, and experiment prefix.

```python
# After running the evaluation, a link will be provided to view the results in langsmith
experiment_results = client.evaluate(
    target,
    data="Sample dataset",
    evaluators=[
        correctness_evaluator,
        # can add multiple evaluators here
    ],
    experiment_prefix="first-eval-in-langsmith",
    max_concurrency=2,
)
```

--------------------------------

### Run LangSmith Evaluation with OpenAI Model (Python)

Source: https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/tutorials/evaluation.mdx

This code demonstrates how to run an evaluation using LangSmith's `client.evaluate` method. It takes a target function, dataset name, a list of evaluators, and an experiment prefix. The `ls_target` function and a dataset named `dataset_name` are assumed to be defined.

```python
client.evaluate(
    ls_target, # Your AI system
    data=dataset_name, # The data to predict and grade over
    evaluators=[concision, correctness], # The evaluators to score the results
    experiment_prefix="openai-4o-mini", # A prefix for your experiment names to easily identify them
)
```

--------------------------------

### Execute Evaluation Job: Python

Source: https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/tutorials/agents.mdx

This Python code snippet demonstrates how to execute an evaluation job using the LangSmith client. It calls `client.aevaluate`, specifying the target function (`run_graph`), the dataset (`dataset_name`), the evaluator function (`final_answer_correct`), an experiment prefix, and other parameters like `num_repetitions` and `max_concurrency`. The results are then converted to a pandas DataFrame.

```python
experiment_results = await client.aevaluate(
    run_graph,
    data=dataset_name,
    evaluators=[final_answer_correct],
    experiment_prefix="sql-agent-gpt4o-e2e",
    num_repetitions=1,
    max_concurrency=4,
)
experiment_results.to_pandas()
```

### 16.2 Langfuse Agent Evaluation Snippets

### LLM-as-a-Judge Agent Evaluation with Langfuse

Source: https://github.com/langfuse/langfuse-docs/blob/main/cookbook/example_evaluating_openai_agents.ipynb

Demonstrates setting up an agent with web search capabilities and tracing its execution through Langfuse. The agent processes a query and outputs are logged for evaluation. This example shows how to use Langfuse spans to capture agent input/output for downstream LLM-based judgment.

```python
# Example: Checking if the agent's output is toxic or not.
from agents import Agent, Runner, WebSearchTool

# Define your agent with the web search tool
agent = Agent(
    name="WebSearchAgent",
    instructions="You are an agent that can search the web.",
    tools=[WebSearchTool()]
)

input_query = "Is eating carrots good for the eyes?"

# Run agent
with langfuse.start_as_current_observation(as_type="span", name="OpenAI-Agent-Trace") as span:
    # Run your agent with a query
    result = Runner.run_sync(agent, input_query)

    # Set input and output on the root observation
    span.update(
        input=input_query,
        output=result.final_output,
    )
```

--------------------------------

### Run Model-based Evaluations with Python SDK

Source: https://github.com/langfuse/langfuse-docs/blob/main/pages/blog/update-2023-09.mdx

This Python code demonstrates how to perform model-based evaluations on production data using the Langfuse SDK. It fetches generations based on a specified name, applies a custom evaluation function (e.g., `hallucination_eval`) to each generation's prompt and completion, and then records the resulting score and reasoning back into Langfuse. This enables integrating external evaluation libraries for comprehensive LLM application analysis.

```python
from langfuse import Langfuse

langfuse = Langfuse(LF_PUBLIC_KEY, LF_SECRET_KEY)
generations = langfuse.get_generations(name="my_generation_name").data

for generation in generations:
    # import function from an eval library, see docs for details
    eval = hallucination_eval(
      generation.prompt,
      generation.completion
    )

    langfuse.score(
      name="hallucination",
      traceId=generation.trace_id,
      observationId=generation.id,
      value=eval["score"],
      comment=eval['reasoning']
    )
```

--------------------------------

### Run Experiment with Langfuse Dataset Runner

Source: https://github.com/langfuse/langfuse-docs/blob/main/cookbook/example_langgraph_agents.ipynb

Executes the task function against a Langfuse dataset using the experiment runner SDK. Handles concurrent execution, automatic tracing, and evaluation. The runner processes each dataset item through the task function and returns aggregated results that can be formatted and compared across multiple experiment runs.

```python
# Fetch dataset and run experiment
dataset = langfuse.get_dataset('qa-dataset_langgraph-agent')

result = dataset.run_experiment(
    name="run_gpt-4o",
    description="My first run",
    task=my_task,
    metadata={"model": "gpt-4o"}
)
 
# Flush the langfuse client to ensure all data is sent to the server at the end of the experiment run
langfuse.flush()
print(result.format())
```

--------------------------------

### Run Experiment with Remote Dataset and LLM-as-a-Judge in Python

Source: https://github.com/langfuse/langfuse-docs/blob/main/pages/blog/2025-10-21-testing-llm-applications.mdx

Demonstrates how to fetch a remote dataset from Langfuse, define a task function that calls an LLM, and run an experiment with automatic LLM-as-a-judge evaluation. The evaluator is configured in the Langfuse UI and runs automatically during experiment execution. Results including scores and reasoning are tracked and visible in the Langfuse dashboard.

```python
import pytest
from langfuse import get_client, Langfuse

@pytest.fixture
def langfuse_client() -> Langfuse:
    return get_client()

def test_with_remote_dataset(langfuse_client: Langfuse):
    """Test using a dataset stored in Langfuse with LLM-as-a-judge evaluation"""
    
    # Fetch dataset from Langfuse
    dataset = langfuse_client.get_dataset("geography-questions")
    
    def task(*, item, **kwargs):
        question = item.input
        response = OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}]
        )
        return response.choices[0].message.content
    
    # Run experiment - Langfuse automatically applies configured evaluators
    result = dataset.run_experiment(
        name="Geography Test with Remote Dataset",
        description="Testing geography QA with LLM-as-a-judge",
        task=task
    )
    
    # The LLM-as-a-judge evaluator runs automatically in Langfuse
    # Results are visible in the Langfuse UI
    langfuse_client.flush()
```

--------------------------------

### Run Experiment on Langfuse Dataset (Python SDK, JS/TS SDK, Langchain)

Source: https://github.com/langfuse/langfuse-docs/blob/main/pages/changelog/2023-09-25-datasets.mdx

This code demonstrates how to iterate through a Langfuse dataset, execute an LLM application function for each item, and link the resulting execution trace (observation) back to the dataset item. It also illustrates how to optionally score the output using a custom evaluation function to compare different runs. This process is crucial for systematically benchmarking and evaluating new iterations of an LLM application using the Langfuse SDKs and Langchain integration.

```python
dataset = langfuse.get_dataset("<dataset_name>")

for item in dataset.items:
    # execute application function and get Langfuse parent observation (span/generation/event, and other observation types: see /docs/observability/features/observation-types)
    # output also returned as it is used to evaluate the run
    generation, output = my_llm_application.run(item.input)

    # link the execution trace to the dataset item and give it a run_name
    item.link(generation, "<run_name>")

    # optionally, evaluate the output to compare different runs more easily
    generation.score(
        name="<example_eval>",
        # any float value
        value=my_eval_fn(
            item.input,
            output,
            item.expected_output
        )
    )
```

```ts
const dataset = await langfuse.getDataset("<dataset_name>");

for (const item of dataset.items) {
  // execute application function and get Langfuse parent observation (span/generation/event, and other observation types: see /docs/observability/features/observation-types)
  // output also returned as it is used to evaluate the run
  const [generation, output] = await myLlmApplication.run(item.input);

  // link the execution trace to the dataset item and give it a run_name
  await item.link(generation, "<run_name>");

  // optionally, evaluate the output to compare different runs more easily
  generation.score({
    name: "<score_name>",
    value: myEvalFunction(item.input, output, item.expectedOutput),
  });
}
```

```python
dataset = langfuse.get_dataset("<dataset_name>")

for item in dataset.items:
    # Langchain calback handler that automatically links the execution trace to the dataset item
    handler = item.get_langchain_handler(run_name="<run_name>")

    # Execute application and pass custom handler
    my_langchain_chain.run(item.input, callbacks=[handler])
```
