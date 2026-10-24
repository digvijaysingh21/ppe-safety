# Roadmap

Eleven phases, built one at a time, each ending in a **gate** you must pass before moving on. The complete file list for every phase lives in [PHASE_MANIFEST.md](PHASE_MANIFEST.md) and is generated from `scripts/repo_manifest.py`, so what you read here, what the tree shows and what gets scaffolded always agree.

---

## How every phase works

### Phase kickoff ritual (before any code)

```bash
python scripts/repo_manifest.py phase N      # 1. Read: every file and folder this phase creates
python scripts/repo_manifest.py scaffold N   # 2. Scaffold: create all stubs, none missing
git add -A && git commit -m "chore: scaffold phase N"   # 3. Commit the empty skeleton
```

Then fill the files **one at a time, in the build order given for the phase**. The skeleton first, code second: you always know what the finished phase looks like and nothing is forgotten.

### The learn-by-doing loop (every task inside a phase)

| Step | What happens | Why |
|---|---|---|
| 1. Concept | Short explanation: what it is, why it exists, when to use it, when not to | You understand before typing |
| 2. Predict | You write down what you expect to happen | Surfaces wrong mental models |
| 3. Build | Implement from scratch in small runnable steps | Builds real skill |
| 4. Verify | Tests, or comparison with a reference library | Proves it is correct |
| 5. Reflect | Log in `EXPERIMENTS.md`, `DECISIONS.md`, `WHAT_FAILED.md` | Becomes your write-up |
| 6. Check | A few questions in your own words before advancing | Confirms understanding |
| 7. Commit | Conventional commit, PR, CI green | Habit of shipping |

### Phase exit gate

A phase is done only when: all manifest files are filled (or explicitly deferred with a reason), CI is green, the phase deliverables below exist, the logs are updated, and you can answer the phase's interview questions without notes.

---

## Timeline

| Phase | Name | Weeks (estimate) | New files |
|---|---|---|---|
| 0 | Foundations and framing | 1 | 48 |
| 1 | Data engineering and annotation | 2 | 33 |
| 2 | Baseline, evaluation harness, experiment tracking | 1.5 | 25 |
| 3 | Model improvement and error analysis | 2 | 23 |
| 4 | Video intelligence: tracking, rules, privacy | 2 | 33 |
| 5 | Optimization and export | 1 | 16 |
| 6 | Serving, services, product surface (as 6A and 6B) | 2.5 | 67 |
| 7 | ML testing and CI/CD | 1 | 14 |
| 8 | Observability, monitoring, feedback loop | 1.5 | 34 |
| 9 | Cloud, Kubernetes, safe rollout | 2 | 37 |
| 10 | Launch: demo, write-ups, interview kit | 1 | 8 |
| | **Total** | **about 17-18 weeks** | **338** |

This is larger than the first rough estimate because the scope now includes the full platform (services, CI/CD, observability, cloud). Learning-by-doing may run slower than the estimate; **depth over speed**. Colab/Kaggle session limits mostly affect Phases 2, 3 and 5.

**If time gets tight, the minimum strong path** is Phases 0-5, then 6A, then 10: a well-evaluated model, tracking and rules, an exported and benchmarked detector, a working API and alert path, and a demo. Phases 7-9 are what make it an MLOps platform; do them if you can, in that order.

---

## Phase 0: Foundations and framing

**Goal:** a repo and a plan that a team could join tomorrow.
**Concepts (what, why, when):** what a PRD is and why cost of errors drives everything; trunk-based Git and why not GitFlow; why `src/` layout; pre-commit hooks; what CI does; Docker base images.
**Build order:** `.gitignore`, `pyproject.toml`, `Makefile` -> `core/config.py`, `core/types.py`, `core/logging.py`, `core/exceptions.py` -> tests -> `.pre-commit-config.yaml` -> `ci.yml` -> `docker/Dockerfile.base` -> `docs/PRD.md` -> `notebooks/00_env_check.ipynb`.
**Deliverables:** PRD with assumed numbers marked; green CI on the skeleton; env check on Colab and Kaggle.
**Exit gate:** a fresh clone runs `make setup && make test` successfully.
**Interview unlocked:** "How did you define success before building?"

## Phase 1: Data engineering and annotation

**Goal:** a trustworthy, versioned dataset with an honest split.
**Concepts:** data-centric AI (why data beats model tweaks); labeling guidelines and inter-annotator agreement; foundation-model pre-labeling; class unification across sources; group-aware splits; leakage; label noise; data contracts; DVC; dataset licensing.
**Build order:** `LICENSES.md` -> `download.py` -> `convert.py` -> `unify_classes.py` -> `validate.py` + schema tests -> `split.py` + leakage tests -> `leakage_audit.py` -> `LABELING_GUIDELINE.md` + CVAT setup -> `prelabel.py` -> `agreement.py` -> `label_noise.py` -> `stats.py` + EDA notebook -> `dvc.yaml`, `params.yaml` -> `data-ci.yml` -> freeze `data-v1`.
**Deliverables:** `data-v1` with changelog and datasheet; your own footage annotated; golden set frozen and hash-checked.
**Exit gate:** leakage audit passes; contracts pass in CI; a teammate could rebuild the dataset with `dvc repro`.
**Interview unlocked:** "How did you avoid leakage?" "How did you handle label quality?"

## Phase 2: Baseline, evaluation harness, experiment tracking

**Goal:** one honest number, produced by code you understand.
**Concepts:** anchor-based vs anchor-free; IoU, GIoU, DIoU, CIoU; NMS vs Soft-NMS; FPN/PAN necks; focal loss; precision, recall, AP, mAP (derive it by hand); why a baseline comes first; experiment tracking.
**Build order:** `iou.py` + tests -> `nms.py` + tests -> `metrics.py` + tests vs `pycocotools` -> `seed.py` -> `detector.py` + `yolo_detector.py` -> `tracking.py` (MLflow) -> `train.py`, `trainers/yolo.py`, `callbacks.py` -> `evaluate.py`, `report.py` -> baseline run on Colab -> first `model_card.md` draft -> `EXPERIMENTS.md` row.
**Deliverables:** baseline metrics (mAP, per-class AP, PR curves, confusion matrix); evaluation code verified against a reference.
**Exit gate:** your mAP equals the reference library's within tolerance; baseline reproducible from config and seed.
**Interview unlocked:** "Explain mAP." "Why IoU variants?" "Why a baseline?"

## Phase 3: Model improvement and error analysis

**Goal:** earn every improvement with evidence and know why it worked.
**Concepts:** error analysis (miss, false alarm, localization, classification); slices; small-object techniques (resolution, P2 head, SAHI); augmentation (mosaic, mixup, copy-paste, weather, low light); imbalance and hard-negative mining; Optuna; mixed precision and EMA; distillation; calibration; model-family comparison; writing an ADR.
**Build order:** `slices.py` + `error_analysis.py` -> look at failures (notebook) -> `augment.py` -> `hard_negatives.py` -> P2/resolution configs -> `sahi_detector.py` -> Faster R-CNN and RT-DETR trainers -> `tune.py` -> `calibration.py` -> `distill.py` -> `synthetic.py` -> ablation table -> `adr/0002`.
**Deliverables:** ablation table; slice report; chosen model with a written justification; updated model card.
**Exit gate:** the chosen model beats baseline with the improvement explained by error analysis, not luck; failed ideas logged in `WHAT_FAILED.md`.
**Interview unlocked:** "Why this model over a simpler one?" "What did not work?"

## Phase 4: Video intelligence: tracking, rules, privacy

**Goal:** turn per-frame boxes into trustworthy per-person alerts.
**Concepts:** tracking-by-detection; Kalman filters; Hungarian matching; ByteTrack's two-pass idea; why policy is deterministic; geometry (point-in-polygon); state machines with timers; PPE-to-person association; privacy by design; tracking metrics; business metrics; cost-based thresholds.
**Build order:** `zones.py` + tests -> `ppe_association.py` + tests -> `state_machine.py` + tests -> `events.py` -> `kalman.py` -> `association.py` -> `bytetrack.py` + tests -> `engine.py` -> `overlay.py` -> `pipeline/runner.py` -> `blur.py` -> `tracking_metrics.py`, `business_metrics.py`, `thresholds.py` -> offline integration test -> `PRIVACY_AND_COMPLIANCE.md` -> `adr/0003`.
**Deliverables:** an offline pipeline that turns a video into violation events with blurred evidence; IDF1 and business metrics on labeled video.
**Exit gate:** on replayed labeled video, false alerts per camera per day and missed-violation rate are measured against PRD targets.
**Interview unlocked:** "How do you count a violation once?" "Why rules instead of ML for policy?"

## Phase 5: Optimization and export

**Goal:** meet the latency and cost budget without losing accuracy you cannot afford.
**Concepts:** ONNX; TensorRT; FP16; INT8 post-training quantization, calibration data, QAT as fallback; parity checking; honest benchmarking (warm-up, percentiles, per-hardware); batching effects.
**Build order:** `to_onnx.py` -> `parity_check.py` + test -> `onnx_detector.py` -> `benchmark_latency.py` -> `to_tensorrt.py`, `trt_detector.py` -> `quantize.py` -> accuracy-vs-latency table -> `BENCHMARKS.md`.
**Deliverables:** benchmark table: format x hardware x batch size with p50/p95/p99, FPS and mAP delta.
**Exit gate:** chosen runtime format meets the p95 budget with an acceptable mAP delta, with numbers recorded per GPU.
**Interview unlocked:** "How did you speed it up and what did you lose?"

## Phase 6: Serving, services, product surface

Largest phase. Run it as two halves, each with its own exit gate.

**6A: Backend.** `messaging/`, `video/capture.py`, `frame_sampler.py`, `clip_writer.py`, `models/registry.py`, API (db, routers, migrations), inference service with batcher, stream worker, alert worker, `docker-compose.yml`, `mediamtx.yml`, `replay_video.py`. Gate: fake RTSP clip produces exactly one alert end to end; killing a worker or Redis does not lose events.
**6B: Product surface.** Dashboard pages (overview, events, cameras and zones, review queue), `seed_demo_data.py`, integration tests, `retention.py`. Gate: a reviewer can open an alert, see blurred evidence and mark it true or false.

**Concepts:** microservices boundaries; Redis Streams and consumer groups; idempotency; backpressure and bounded queues; dynamic batching (and why it raises throughput); async I/O; FastAPI; SQLAlchemy and Alembic; expand-then-contract migrations; health probes; graceful shutdown; Next.js data fetching.
**Interview unlocked:** "What happens when the model server is slow?" "How do you avoid duplicate alerts?" "Custom batcher vs Triton?"

## Phase 7: ML testing and CI/CD

**Goal:** make bad changes impossible to merge or ship unnoticed.
**Concepts:** the ML testing pyramid; golden-set regression; behavioral tests; slice regression; promotion gates; image build and scanning; staging deploy and smoke tests; two release trains (app and model).
**Build order:** `gate.yaml` + `gate.py` -> golden-set and behavioral tests -> `check_eval_gate.py` -> `model-ci.yml` -> `build-images.yml` -> `security.yml` -> `dependabot.yml` -> `cd-staging.yml` -> `promote_model.py`.
**Deliverables:** PRs that fail on a regression, with a readable gate report; images built and scanned on merge.
**Exit gate:** deliberately submit a worse model and watch the gate reject it; deliberately break a dependency and see the scan catch it.
**Interview unlocked:** "How do you stop a bad model reaching production?"

## Phase 8: Observability, monitoring, feedback loop

**Goal:** know the system is working and correct, and feed what you learn back in.
**Concepts:** metrics, logs, traces; SLOs and error budgets; drift types and why drift is not degradation; delayed labels; alert design and fatigue; active learning; continuous training; runbooks.
**Build order:** `observability/metrics.py` -> instrument services -> Prometheus, Alertmanager, Grafana, Loki, OTel configs -> `docker-compose.obs.yml` -> dashboards -> `tracing.py` -> `drift.py` + tests -> `sampler.py` + tests -> `export_to_cvat.py`, `feedback_ingest.py` -> Prefect flows -> `retrain.yml` -> runbooks.
**Deliverables:** three dashboards; alert rules tested by breaking things on purpose; one full loop: review verdicts to new dataset version to challenger.
**Exit gate:** kill a camera, add latency, shift brightness: each produces the expected alert or drift signal.
**Interview unlocked:** "How do you know it still works next month?"

## Phase 9: Cloud, Kubernetes, safe rollout

**Goal:** deploy like a production team and be able to undo it.
**Concepts:** containers to Kubernetes (Deployments, Services, HPA, probes, node pools, NetworkPolicy); Terraform; managed services; shadow, canary, blue-green and rollback; load testing; cost modeling.
**Build order:** pick cloud and set budget alerts -> Terraform modules -> Kustomize base then overlays -> secrets via secret manager -> deploy staging -> `locustfile.py` -> shadow inference -> Argo Rollouts canary and analysis -> `cd-prod.yml` -> rehearse rollback -> `COST_MODEL.md` -> `adr/0005`.
**Deliverables:** staging and production environments from code; load-test report; rollback rehearsal; cost per 1,000 frames and per camera per month.
**Exit gate:** a bad challenger is caught in shadow or canary and rolled back automatically.
**Interview unlocked:** "How would you scale it 100x?" "How do you roll out a model safely?"

## Phase 10: Launch: demo, write-ups, interview kit

**Goal:** make the work legible to someone who has five minutes.
**Build order:** final `model_card.md` -> `RESULTS.md` (with honest limitations) -> Hugging Face Space demo (`demo/`) -> `demo.gif` and architecture image -> `BLOG_POST.md` -> `INTERVIEW_PREP.md` -> README final pass (real numbers, live link).
**Deliverables:** public demo link, blog post, final README, interview sheet with your five hardest questions answered.
**Exit gate:** someone unfamiliar can understand what it does, why it is built this way, and reproduce a result from the README in under an hour.

---

## Cross-cutting tracks (apply in every phase)

| Track | What you do each phase |
|---|---|
| Docs | Update the relevant doc, `CHANGELOG.md`, and your `docs/theory/pN_*.md` notes |
| Logs | `EXPERIMENTS.md` rows, `WHAT_FAILED.md` entries, `DECISIONS.md` / ADRs |
| Tests | Tests with every behavior; CI stays green |
| Standards | [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) definition of done |
| Model card | Add what the phase taught you about intended use and limits |
| Honesty | Numbers have sources; assumptions are labeled; failures are published |

## Risks to the plan

| Risk | Mitigation |
|---|---|
| Colab/Kaggle limits slow training | Checkpoint and resume, smaller models and subsets for iteration, move long runs to cloud credits |
| Dataset license or availability changes | Record and re-check in Phase 1; keep a copy of converted data per `data-vN` where licenses allow |
| Scope creep (gloves, re-ID, segmentation) | v1 scope frozen in PRD; extras tracked as v2 issues |
| Cloud credits expire or limits differ | Do Phase 9 last, set budget alerts, keep a local k3s/kind path as backup |
| Own footage hard to obtain | Start collecting early in Phase 1; fall back to carefully chosen public video with documented licenses |
