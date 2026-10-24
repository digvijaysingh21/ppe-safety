# System Design

The design document a product team would write before building, and the one interviewers ask for. It answers four questions: **what are we building, how will it behave at scale, why these choices, and what breaks.**

> Status: Phase 0 baseline. Numbers marked *assumed* are hypotheses we will replace with measurements. Dataset names, licenses and library versions must be re-checked when the phase that uses them starts.

---

## 1. Summary

A real-time system that watches camera streams on industrial and construction sites, detects workers missing required PPE (helmet, vest in v1), tracks them over time, applies configurable zone-and-duration rules, and raises evidence-backed alerts. Humans review alerts; their verdicts feed retraining.

**One-sentence value:** fewer accidents and cheaper audits, without drowning safety officers in false alarms.

## 2. Goals and non-goals

| Goals (v1) | Non-goals (v1) |
|---|---|
| Detect person, helmet, vest on fixed cameras | Gloves, goggles, harness (v2: small, hard objects) |
| Alert on "no helmet in restricted zone for more than 5 s" | Face recognition or identifying workers (explicitly avoided) |
| Evidence (blurred snapshot and clip) with every alert | Moving or body-worn cameras |
| Review UI whose verdicts become training data | Near-miss prediction between vehicles and people (v2) |
| Reproducible training, gated promotion, safe rollout, monitoring | Multi-camera person re-identification (v2) |
| Run locally with Docker, deploy to managed Kubernetes | Multi-region active-active |

## 3. Requirements

### 3.1 Functional

| ID | Requirement |
|---|---|
| F1 | Ingest N RTSP streams and recorded files; reconnect automatically |
| F2 | Detect person, helmet, vest per sampled frame |
| F3 | Track persons across frames; count one violation per person-episode, not per frame |
| F4 | Evaluate per-camera zone polygons and violation rules from configuration |
| F5 | Emit idempotent violation events; store snapshot and clip with faces blurred |
| F6 | Notify via Slack, email or webhook with cooldown and rate limits |
| F7 | API and dashboard for cameras, zones, events, acknowledgement and review |
| F8 | Reviewer verdicts stored and exportable as labels |
| F9 | Model versions selectable by alias; shadow and canary supported |

### 3.2 Non-functional (targets are *assumed* until measured)

| Area | Target | How we verify |
|---|---|---|
| Per-frame inference latency | p95 under 100 ms on the target GPU | `benchmark_latency.py`, Prometheus histogram |
| Event-to-notification latency | p95 under 3 s after the violation is confirmed | End-to-end test with fake RTSP |
| Throughput | 20 cameras at 10 FPS on one GPU (200 FPS aggregate) | Locust and replay load test |
| Alert quality | At most N false alerts per camera per day (N set in PRD); missed-violation rate below target | Replay on labeled video and reviewer feedback |
| Availability | Camera or worker failure never stops other cameras; staging target 99.5% | Chaos checks: kill a worker, kill Redis |
| Privacy | No unblurred face is persisted; retention enforced | Automated test and retention job |
| Reproducibility | Any model rebuilt from git SHA + data version + config + seed | `dvc repro`, MLflow tags |
| Cost | Reported as cost per 1,000 frames and per camera per month | `COST_MODEL.md` |

## 4. Capacity estimation

Back-of-envelope, so decisions rest on arithmetic. All inputs *assumed*.

| Quantity | Calculation | Result |
|---|---|---|
| Compressed stream bandwidth | 20 cameras x 2-4 Mbps (1080p H.264) | 40-80 Mbps into the site gateway |
| Decoded 1080p frame | 1920 x 1080 x 3 bytes | about 6.2 MB per frame |
| Decoded rate per camera at full FPS | 6.2 MB x 30 | about 190 MB/s, so **decode and downscale next to the camera, never ship raw frames** |
| Model input frame | 640 x 640 x 3 | about 1.2 MB, or about 80 KB as JPEG |
| Inference load | 20 cameras x 10 FPS | 200 frames/s |
| Events | A few per camera per hour in a busy site | Tens of events per hour; queue and DB are nowhere near a bottleneck |
| Evidence storage | 10 s clip about 3 MB x events per day x retention days | Dominated by retention policy, not events |

**Conclusion:** the GPU and the video decode are the scarce resources. Events, DB and queue are cheap. This is why the design puts effort into frame sampling, batching, decoding location and quantization, and almost none into scaling the database.

### 4.1 Scaling 100x (the interview question)

| Bottleneck at 2,000 cameras | Remedy |
|---|---|
| 20,000 FPS inference | Many GPU replicas behind the batcher, INT8 TensorRT, lower sampling FPS for calm scenes, or push inference to edge devices on site |
| Decode CPU | Hardware decode (NVDEC), decode at the edge, one worker per site |
| Single Redis | Redis Cluster, or Kafka if multi-consumer replay and long retention become requirements |
| Postgres writes | Still modest; add read replicas and partition `violation_event` by month |
| Evidence storage | Tiered storage and shorter retention for low-severity events |
| Operations | Per-site sharding, fleet management for edge devices, per-site config rollout |
| Cost | Autoscale on queue lag, spot/preemptible instances for training, scale-to-zero staging |

---

## 5. Key design decisions

Each row is also recorded as an ADR in `docs/adr/` once decided with evidence.

| Decision | Chosen | Alternatives considered | Why | Switch when |
|---|---|---|---|---|
| Detector family | One-stage YOLO baseline, compared against Faster R-CNN and RT-DETR | Two-stage only; transformer only | Real-time budget, mature export tooling, strong small-model accuracy. Decision is made by Phase 3 ablations, not preference | Faster R-CNN if recall on tiny objects matters more than latency; RT-DETR if NMS-free end-to-end output simplifies deployment and accuracy wins |
| Detector license | Check before committing | Ultralytics YOLO is AGPL-3.0 with a separate commercial license | Product companies review licenses. Fine for a portfolio, a blocker for closed-source commercial use | Use Apache-licensed detectors (RT-DETR reference implementations, YOLOX, RTMDet) if commercial distribution is the goal. Verify current terms |
| Perception vs policy | ML for perception, **deterministic rules** for policy | End-to-end ML that outputs "violation" | Rules are auditable, editable per site and explainable to a safety auditor; ML failures are isolated to perception | An ML classifier over tracks if policies become too complex to express as rules |
| Tracking | ByteTrack | DeepSORT, BoT-SORT, OC-SORT | Fixed cameras, no appearance network needed; uses low-score boxes in a second pass, which helps under occlusion | DeepSORT/BoT-SORT when people re-appear after long occlusions or cameras move |
| Inference architecture | Central inference service with **dynamic micro-batching** | Model embedded in every stream worker; Triton from day one | Higher GPU utilization, independent scaling, model swap, and easy **shadow mode** (send frames to two models). We build a simple batcher first to learn why batching works | Triton when we need multiple models, ensembles, multi-framework support, or production-grade batching and metrics out of the box |
| Runtime format | ONNX, then TensorRT FP16; INT8 only if accuracy holds | PyTorch eager; OpenVINO on CPU | ONNX is portable; TensorRT gives the best NVIDIA throughput | OpenVINO or ONNX Runtime CPU for CPU-only edge targets |
| Event bus | Redis Streams | Kafka, RabbitMQ, direct HTTP | Hundreds of events per second at most; consumer groups, acks, replay; already in the stack | Kafka for multi-team consumers, very long replay, or cross-region |
| Primary store | PostgreSQL (+ pgvector later for similar-event search) | MongoDB, time-series DB | Relational integrity for cameras, zones, events, reviews; idempotency via unique constraints | A time-series store for raw metrics (Prometheus already covers this) |
| Evidence store | Object storage (S3-compatible, MinIO locally) | Postgres blobs, disk | Cheap, lifecycle rules for retention, signed URLs | |
| Orchestration (CT) | DVC pipeline for data/training reproducibility + Prefect for scheduled flows | Airflow, Kubeflow | Light, Python-native, fits a solo builder; same concepts as heavier tools | Airflow or Kubeflow if a platform team already runs them |
| Experiment tracking | MLflow (tracking + registry with aliases) | W&B | Self-hostable, registry included | W&B for team collaboration features |
| Config | YAML validated by pydantic | Hydra | Fewer moving parts, typed, easy to read for beginners | Hydra when sweeps and config composition dominate |
| Rollout | Shadow, then canary with automated analysis, rollback by alias | Big-bang, blue-green | ML failures are statistical, not crashes; you need real traffic evidence | Blue-green for pure app changes with no model change |

---

## 6. Algorithms: when to use what, and why

### 6.1 Detector families

| Family | Idea | Strength | Weakness | Use when |
|---|---|---|---|---|
| Faster R-CNN (two-stage, anchor-based) | Propose regions, then classify and refine | High accuracy, good on small objects | Slow, more complex to deploy | Offline auditing, accuracy ceiling reference |
| YOLO (one-stage, anchor-free in recent versions) | Predict boxes and classes in one pass | Fast, easy to train and export | Needs NMS; small objects need tuning | Real-time default |
| RT-DETR (transformer) | Set prediction with attention, no NMS | End-to-end output, strong accuracy | Heavier, slower to converge, newer tooling | When NMS tuning is a pain point or accuracy wins in ablation |

### 6.2 IoU and its variants (and why the loss changed)

| Variant | Adds | Fixes | Use |
|---|---|---|---|
| IoU | Overlap ratio | Baseline | Matching, metrics |
| GIoU | Penalty for empty space in the enclosing box | Gradient when boxes do not overlap | Training loss, early |
| DIoU | Center-distance penalty | Faster convergence | Training loss and DIoU-NMS |
| CIoU | Aspect-ratio consistency | Shape alignment | Common YOLO box loss |

We implement IoU, GIoU, DIoU and CIoU from scratch in Phase 2 and compare them with a library implementation in unit tests.

### 6.3 Suppression

| Method | Behavior | Use when |
|---|---|---|
| NMS | Drop boxes overlapping a higher-scoring box above an IoU threshold | Default |
| Soft-NMS | Decay scores of overlapping boxes instead of deleting | Crowded scenes where workers stand close |
| NMS-free (RT-DETR) | Model outputs a set; no suppression | Simplifies deployment |

### 6.4 Loss and imbalance

Helmets and vests are far rarer than background. We handle imbalance with, in order of preference: better data and hard-negative mining, class-weighted sampling, then focal loss. Focal loss down-weights easy negatives so training focuses on hard examples; use it when the model is swamped by easy background, not as a first resort.

### 6.5 Small objects (gloves in v2, distant helmets in v1)

| Technique | Cost | Use when |
|---|---|---|
| Higher input resolution | More compute | First thing to try |
| P2 head (extra high-resolution detection layer) | Slightly more compute | Objects under about 32 px |
| SAHI / tiling at inference | Multiplies inference cost | Very high-resolution frames with tiny objects; usually too slow for real-time, great for offline audit |
| Better labels and crops of small objects | Human time | Often the biggest win |

### 6.6 Tracking

ByteTrack: Kalman filter predicts each person's next box; Hungarian algorithm matches detections to tracks by IoU; **low-confidence detections get a second matching pass**, which keeps tracks alive through partial occlusion. We implement the Kalman filter and association from scratch in Phase 4 to understand it, then compare with the library.

### 6.7 Quantization

| Format | Speed | Accuracy risk | Notes |
|---|---|---|---|
| FP32 | Baseline | None | Reference |
| FP16 | Large speedup on tensor-core GPUs | Usually negligible | Default deployment format |
| INT8 post-training (PTQ) | Further speedup | Needs representative calibration data; can hurt small objects | Try after FP16; keep only if the accuracy-vs-latency table says so |
| INT8 quantization-aware training (QAT) | Same speed as PTQ | Lowest accuracy loss | Use only if PTQ loses too much accuracy |

### 6.8 Thresholds and calibration

The alert threshold is a **business decision**, not a model default. We choose it on the validation set by minimizing expected cost (cost of a miss times misses plus cost of a false alarm times false alarms) subject to a cap on false alerts per camera per day. Confidence scores from detectors are usually miscalibrated; we measure reliability and apply calibration where it helps threshold stability across cameras.

---

## 7. Data design

| Topic | Decision |
|---|---|
| Sources | SH17, Pictor-PPE, Roboflow Universe sets, plus **your own footage** (the part that is yours alone) |
| Licensing | Every source recorded in `docs/data/LICENSES.md` before use; Roboflow sets vary widely, so check each |
| Class unification | One class map in `configs/data/classes.yaml`; each source mapped explicitly, unmapped labels dropped with a log |
| Annotation | CVAT, labeling guideline with examples and edge cases, inter-annotator agreement on a shared subset, label QA pass |
| Pre-labeling | Grounding DINO / YOLO-World / SAM generate draft boxes; humans correct. We measure correction time to quantify savings |
| Splits | **Group-aware by camera, site or video**, never by random frame; consecutive frames are near-duplicates and random splits leak |
| Golden set | Frozen, hand-verified, from your own footage and cameras never seen in training; read-only; used only for gating and final reporting |
| Versioning | DVC for data, git tags `data-vN`, `DATASET_CHANGELOG.md` for human-readable history |
| Validation | Pandera contracts: boxes in range, valid class ids, no corrupt images, no cross-split near-duplicates |

## 8. Evaluation design

| Level | Metrics | Purpose |
|---|---|---|
| Model | mAP@0.5, mAP@0.5:0.95, per-class AP, PR curves, confusion matrix | Detector quality |
| Slices | Same metrics by object size, lighting, occlusion, camera angle, site | Find where it fails and for whom |
| Tracking | MOTA, IDF1, ID switches | Tracker quality, since ID switches create duplicate alerts |
| System | End-to-end alert precision and recall on labeled video replay | Does the whole pipeline do the job |
| Business | False alerts per camera per day, missed-violation rate, alert-to-acknowledge rate | What the customer feels |
| Runtime | p50/p95/p99 latency, FPS, GPU memory, cost per 1,000 frames | Can we afford it |

Protocol: train on train, select on val, **report once on test**, gate on golden. We never tune on the golden set.

## 9. Failure modes and mitigations

| Failure | Effect | Mitigation | Detected by |
|---|---|---|---|
| Camera drops or RTSP stalls | Blind spot | Reconnect with exponential backoff; `camera_offline` alert after N minutes | Frames-per-second gauge per camera |
| Night, rain, glare, new camera angle | Accuracy drops silently | Slice evaluation, augmentation, input-drift monitors, per-camera detection-rate baseline | Drift and detection-rate dashboards |
| Track ID switch | Duplicate or lost alert | Grace periods, dedup key in the Alert Worker, tracking metrics in eval | ID-switch rate in replay tests |
| Alert flood | Safety officers ignore the system | Cooldown, per-camera rate limit, threshold by cost, reviewer feedback loop | False-alert rate from reviews |
| Inference service down | No detections | Readiness probes, replicas, circuit breaker in worker, buffered retry then drop with a metric | Error rate, queue depth |
| GPU out of memory | Crashes under load | Bounded batch size, backpressure, load test before release | OOM counter, restarts |
| Redis down | Events lost | Local spool on worker, replay when back; Redis persistence on | Publish-error counter |
| Postgres down | Events cannot be stored | Messages stay unacked in the stream; retried | Consumer lag |
| Bad model released | Many false or missed alerts | Gate, shadow, canary with automated rollback | Canary analysis |
| Labeler disagreement or noisy labels | Ceiling on accuracy | Agreement metric, cleanlab audit, guideline updates | Agreement score, noise report |
| Dataset leakage | Inflated metrics | Group splits, near-duplicate audit, golden set | Leakage audit in CI |
| Clock skew between machines | Wrong durations | Use frame timestamps for rule timers, NTP on hosts | Timestamp-gap checks |

## 10. Security, privacy and compliance

| Concern | Control |
|---|---|
| Worker privacy | Face blur before any persistence; no face recognition; evidence access logged |
| Data retention | Configurable per site; automated deletion job; documented in `PRIVACY_AND_COMPLIANCE.md` |
| Secrets | Never in git; `.env.example` documents names; cloud secret manager in production; `detect-secrets` pre-commit |
| Network | Default-deny Kubernetes NetworkPolicies, TLS at ingress, internal services not exposed |
| AuthN/Z | API keys or JWT, role separation: viewer, reviewer, admin |
| Supply chain | Pinned dependencies, `pip-audit`, image scanning, SBOM optional, signed images optional |
| On-prem vs cloud | Documented trade-off: video leaving the site raises legal and bandwidth cost; edge inference with events-only upload is the privacy-preferred option |
| Jurisdiction | Workplace-monitoring and data-protection rules vary by country (for example India's DPDP Act); note assumptions and get real advice before a real deployment |

## 11. Reliability patterns used

- **Backpressure:** bounded queues between decode and inference; when full, drop oldest frames and count drops (stale frames are worthless in real time).
- **Idempotency:** unique `idempotency_key` per event so retries are safe.
- **Retries with limits and a dead-letter stream** (`violations.dlq`) for poison messages.
- **Health probes:** liveness (process alive), readiness (model loaded, dependencies reachable), startup (slow model load).
- **Graceful shutdown:** finish in-flight events, flush clips, ack messages.
- **Timeouts everywhere** on network calls.

## 12. Latency budget (assumed, to be measured)

| Stage | Budget |
|---|---|
| Decode + resize | 10 ms |
| Network to inference | 5 ms |
| Queue + batch wait | 15 ms |
| Model forward | 30 ms |
| Postprocess + NMS | 5 ms |
| Tracking + rules | 5 ms |
| **Total per frame** | **about 70 ms, under the 100 ms p95 target** |

Event notification adds queue, DB write and the notifier call, about 1-3 s.

## 13. Assumptions and open questions

1. Fixed cameras at 1080p, 10 processed FPS. If cameras move, tracking and zone logic change.
2. "No helmet" is judged from the person's head region; sitting workers, hoods and caps need labeling-guideline rules.
3. Which sites and lighting conditions your own footage will cover decides how far the golden set generalizes.
4. Detector license and commercial plans are undecided (see section 5).
5. Cloud choice (GCP or Azure) is deferred to Phase 9 and depends on available free credits and their terms.

## 14. Interview angle

| Question | Where the answer lives |
|---|---|
| Why this model over a simpler one? | Phase 2 baseline vs Phase 3 ablations, `adr/0002` |
| How did you avoid leakage? | Section 7, `leakage_audit.py`, golden set |
| What broke in production? | `WHAT_FAILED.md` and runbooks |
| How would you scale it 100x? | Section 4.1 |
| How do you know it still works next month? | `OBSERVABILITY.md`, drift and review feedback |
| How do you ship a new model safely? | `adr/0005`, `DEPLOYMENT.md` rollout section |
