# Architecture

How the system is put together, how data and decisions flow through it, and how a model gets from an experiment to production. All diagrams are [Mermaid](https://mermaid.js.org/) and render on GitHub.

> Status: design baseline (Phase 0). Components are built phase by phase; see [ROADMAP.md](ROADMAP.md). Numbers marked *assumed* are hypotheses to be measured, not results.

**Contents**
1. [System at a glance](#1-system-at-a-glance)
2. [Runtime flow of one violation](#2-runtime-flow-of-one-violation)
3. [What happens to one frame](#3-what-happens-to-one-frame)
4. [Violation state machine](#4-violation-state-machine)
5. [ML lifecycle: the loop that makes it a product](#5-ml-lifecycle-the-loop-that-makes-it-a-product)
6. [Data pipeline DAG](#6-data-pipeline-dag)
7. [Model lifecycle and registry](#7-model-lifecycle-and-registry)
8. [CI / CD / CT overview](#8-ci--cd--ct-overview)
9. [Deployment topology](#9-deployment-topology)
10. [Contracts: events, tables, APIs, interfaces](#10-contracts)

---

## 1. System at a glance

```mermaid
flowchart LR
  subgraph SITE["Site"]
    CAM["IP cameras (RTSP)"]
  end

  subgraph RUNTIME["Runtime services"]
    SW["Stream Worker: decode, sample, track, rules"]
    INF["Inference Service: GPU, dynamic batching"]
    BUS[("Redis Streams: violation events")]
    AW["Alert Worker: dedup, persist, notify"]
    API["API: FastAPI"]
    DASH["Dashboard: Next.js"]
  end

  subgraph STATE["State"]
    PG[("PostgreSQL: cameras, zones, events, feedback")]
    OBJ[("Object storage: blurred clips and snapshots")]
    REG[("MLflow registry and artifacts")]
  end

  subgraph OBS["Observability"]
    PROM["Prometheus"]
    LOKI["Loki"]
    OTEL["OpenTelemetry traces"]
    GRAF["Grafana and Alertmanager"]
  end

  subgraph LOOP["Learning loop"]
    REVIEW["Human review queue"]
    AL["Active-learning sampler"]
    CVAT["CVAT annotation"]
    CT["Continuous-training flow"]
  end

  CAM --> SW
  SW -- "preprocessed frames" --> INF
  INF -- "detections" --> SW
  SW -- "violation events" --> BUS
  BUS --> AW
  AW --> PG
  AW --> OBJ
  AW -- "Slack, email, webhook" --> NOTIFY["Safety officer"]
  API --> PG
  DASH --> API
  INF -. "loads model by alias" .-> REG
  SW & INF & AW & API -. "metrics, logs, traces" .-> PROM & LOKI & OTEL
  PROM & LOKI & OTEL --> GRAF
  DASH --> REVIEW
  REVIEW --> PG
  SW -. "low-confidence frames" .-> AL
  AL --> CVAT
  PG -- "verdicts" --> AL
  CVAT --> CT
  CT -- "new challenger model" --> REG
```

**Reading the diagram**

| Piece | One-line job | Why it is its own component |
|---|---|---|
| Stream Worker | Pull a camera, decode, sample frames, track people, apply rules | CPU-bound, one per camera or small group; a crashing camera must not take down others |
| Inference Service | Run the detector on batches of frames from many cameras | Expensive GPU is shared; batching raises throughput; model can be swapped, shadowed or rolled back without touching workers |
| Redis Streams | Durable queue of violation events with consumer groups | Decouples detection speed from notification speed; survives alert-worker restarts |
| Alert Worker | Deduplicate, store evidence, notify | Slow, failure-prone I/O (Slack, email) is isolated from the real-time path |
| API + Dashboard | Configure cameras and zones, browse events, review alerts | Humans interact here; reviews become training labels |
| MLflow | Experiments, artifacts, model versions and aliases | Single place that says which model is `champion` |
| Learning loop | Reviews and low-confidence frames flow back to labeling and retraining | This loop is what separates a product from a one-off model |

---

## 2. Runtime flow of one violation

```mermaid
sequenceDiagram
  autonumber
  participant C as Camera
  participant W as Stream Worker
  participant I as Inference Service
  participant B as Redis Streams
  participant A as Alert Worker
  participant S as Postgres and Object storage
  participant N as Notifier
  participant D as Dashboard

  C->>W: RTSP video
  loop every sampled frame (about 10 per second, assumed)
    W->>W: decode, resize, keep blurred ring buffer
    W->>I: frame tensor + camera_id + timestamp
    I-->>W: boxes, classes, scores
    W->>W: track, match helmet and vest to person, check zone
  end
  Note over W: person without helmet in restricted zone for more than 5 s
  W->>B: XADD violation_event (idempotency key)
  B->>A: consume (consumer group)
  A->>A: dedup by camera, zone, track and violation type, apply cooldown
  A->>S: write event row, save blurred snapshot and clip
  A->>N: send alert with evidence link
  A->>B: XACK
  D->>S: via API, list and open event
  D->>S: reviewer marks true or false alert
```

**Delivery guarantee.** At-least-once from the bus, made effectively-once by the idempotency key (`camera_id + track_id + violation_type + start_ts`) enforced by a unique constraint in Postgres. Retried messages never produce double alerts.

---

## 3. What happens to one frame

```mermaid
flowchart TD
  A["Grab frame from RTSP"] --> B{"Sample this frame?"}
  B -- "no, skip" --> A
  B -- "yes" --> C["Resize and letterbox to model input"]
  C --> D["Push blurred copy to evidence ring buffer"]
  C --> E["Send to Inference Service"]
  E --> F["Detector: person, helmet, vest boxes"]
  F --> G["Confidence threshold and NMS"]
  G --> H["Tracker: assign stable track IDs"]
  H --> I["Match helmet and vest boxes to each person"]
  I --> J["Zone check: is the person inside a restricted zone?"]
  J --> K["Per-track state machine updates timers"]
  K --> L{"Violation confirmed?"}
  L -- "no" --> A
  L -- "yes" --> M["Emit ViolationEvent and flush clip"]
  M --> A
```

**Why each step exists**

| Step | Why | Alternative and when to prefer it |
|---|---|---|
| Frame sampling | Safety events last seconds; 10 FPS is enough and cuts GPU cost about 3x vs 30 FPS | Full FPS only if tracking breaks on fast motion |
| Letterbox resize | Keeps aspect ratio so boxes are not distorted | Stretch resize is faster but hurts accuracy on non-square frames |
| Blur before buffering | Privacy by design: unblurred faces never reach disk | Store raw only if legally required and access-controlled |
| NMS | Removes duplicate boxes for one object | NMS-free models (RT-DETR) skip it; Soft-NMS helps crowded scenes |
| Tracker | Turns per-frame boxes into per-person timelines so we count one violation, not 50 frames | Skip tracking only for single-frame audits |
| Deterministic rules | Auditable and configurable per site; compliance teams need to know why an alert fired | An ML classifier over tracks only if rules cannot express the policy |

---

## 4. Violation state machine

One instance per tracked person per violation type. Timers use frame timestamps, not wall-clock, so replays and tests are deterministic.

```mermaid
stateDiagram-v2
  [*] --> Compliant
  Compliant --> Candidate: missing PPE seen inside zone
  Candidate --> Compliant: PPE seen or left zone (grace period)
  Candidate --> Violating: missing PPE persists for min_duration
  Violating --> Alerted: emit event once
  Alerted --> Cooldown: cooldown timer starts
  Cooldown --> Violating: still violating after cooldown (re-alert)
  Cooldown --> Compliant: compliant for reset_duration
  Alerted --> Lost: track disappears
  Lost --> Compliant: timeout, close event
```

Design notes: a short **grace period** absorbs one-frame detector flicker; **cooldown** prevents alert floods; **Lost** handling stops a track-ID switch from creating a brand-new violation immediately (the dedup key in the Alert Worker is the second line of defense).

---

## 5. ML lifecycle: the loop that makes it a product

```mermaid
flowchart LR
  P["Problem framing: PRD, cost of errors"] --> D["Data: collect, license, annotate, version"]
  D --> V["Validate: schema, leakage, label noise"]
  V --> T["Train: config-driven, tracked"]
  T --> E["Evaluate: mAP, slices, business metrics"]
  E --> G{"Passes gate vs champion?"}
  G -- "no" --> X["Error analysis: fix data, labels or model"]
  X --> D
  G -- "yes" --> R["Register as challenger"]
  R --> SH["Shadow: real traffic, no alerts"]
  SH --> CA["Canary: small share of cameras"]
  CA --> PR["Production champion"]
  PR --> M["Monitor: drift, KPIs, reviews"]
  M --> AL["Active learning: pick hard frames"]
  AL --> D
```

The two loops to remember: the **inner loop** (train, evaluate, error-analyze, fix data) runs daily during development; the **outer loop** (production, monitor, label, retrain) runs for the life of the product.

---

## 6. Data pipeline DAG

Implemented as a DVC pipeline (`dvc.yaml`), so `dvc repro` rebuilds only what changed.

```mermaid
flowchart LR
  S1["download"] --> S2["convert to YOLO format"]
  S2 --> S3["unify classes"]
  S3 --> S4["prelabel with Grounding DINO and SAM"]
  S4 --> S5["human correction in CVAT"]
  S5 --> S6["validate: Pandera contracts"]
  S6 --> S7["label-noise audit: cleanlab"]
  S7 --> S8["group-aware split by camera or site"]
  S8 --> S9["leakage audit"]
  S9 --> S10["build train, val, test"]
  S10 --> S11["freeze and tag: data-vN"]
  GOLD["Own footage: golden set"] --> S6
  GOLD -. "never in train" .-> S11
```

---

## 7. Model lifecycle and registry

MLflow aliases (not the deprecated stages) mark where a model version is in its life.

```mermaid
stateDiagram-v2
  [*] --> Registered: training run passes basic checks
  Registered --> Challenger: passes eval gate vs champion
  Challenger --> Shadow: deployed mirrored, no user impact
  Shadow --> Canary: shadow metrics acceptable
  Canary --> Champion: canary analysis passes
  Canary --> Rejected: analysis fails, auto rollback
  Shadow --> Rejected: disagreement or latency too high
  Champion --> Previous: replaced by newer champion
  Previous --> Champion: rollback
  Rejected --> [*]
```

Registered model name: `ppe-detector`. Aliases: `challenger`, `champion`, `previous`. Every version carries tags: `git_sha`, `data_version`, `config_path`, `seed`, `gate_report_uri`.

---

## 8. CI / CD / CT overview

```mermaid
flowchart TD
  PR["Pull request"] --> CI["CI: lint, types, unit and data tests, image build, security scan"]
  CI --> MRG["Merge to main"]
  MRG --> BLD["Build and push images tagged by git SHA"]
  BLD --> STG["Deploy to staging"]
  STG --> SMK["Smoke test and replay-video test"]
  SMK --> APR{"Manual approval"}
  APR --> CAN["Canary in production"]
  CAN --> ANA{"Automated analysis"}
  ANA -- "healthy" --> FULL["Full rollout"]
  ANA -- "unhealthy" --> RB["Automatic rollback"]

  TRG["Trigger: drift alert, weekly schedule, N new reviewed labels"] --> CT["CT: refresh data, train, evaluate"]
  CT --> GATE{"Eval gate"}
  GATE -- "pass" --> CH["Register challenger, start shadow"]
  GATE -- "fail" --> RPT["Report, no promotion"]
```

Details and file-level breakdown: [CICD.md](CICD.md).

---

## 9. Deployment topology

```mermaid
flowchart TB
  subgraph DEV["Local: Docker Compose"]
    D1["api, stream_worker, inference (CPU), alert_worker, dashboard"]
    D2["redis, postgres, minio, mediamtx fake RTSP, MLflow"]
  end

  subgraph CLOUD["Cloud: managed Kubernetes (GKE or AKS, chosen in Phase 9)"]
    subgraph CPUPOOL["CPU node pool"]
      K1["stream-worker Deployment, HPA on queue lag"]
      K2["api, alert-worker, dashboard"]
    end
    subgraph GPUPOOL["GPU node pool"]
      K3["inference Deployment, TensorRT, HPA on GPU utilization"]
      K4["shadow-inference (mirrored traffic)"]
    end
    K5["Argo Rollouts: canary and analysis"]
    K6["Prometheus, Grafana, Loki, OTel collector"]
  end

  subgraph MANAGED["Managed services"]
    M1[("Managed Postgres")]
    M2[("Redis")]
    M3[("Object storage")]
    M4[("Container registry")]
    M5[("MLflow and artifact store")]
  end

  DEV -. "same images, different config" .-> CLOUD
  CPUPOOL --> MANAGED
  GPUPOOL --> M5
  GH["GitHub Actions"] --> M4
  GH --> K5
  TF["Terraform"] --> CLOUD
  TF --> MANAGED
```

Edge variant (documented, not built in v1): the same stream worker and an ONNX/TensorRT detector on a Jetson running Docker, publishing events to the cloud bus. TensorRT engines are built on the target device because they are tied to GPU architecture and TensorRT version.

---

## 10. Contracts

### 10.1 ViolationEvent (message on the `violations` stream)

```json
{
  "event_id": "01J8Z4M2Q7...",
  "idempotency_key": "cam-03:trk-182:no_helmet:2026-11-02T09:14:07Z",
  "camera_id": "cam-03",
  "zone_id": "zone-crane-radius",
  "violation_type": "no_helmet",
  "track_id": 182,
  "started_at": "2026-11-02T09:14:07Z",
  "confirmed_at": "2026-11-02T09:14:12Z",
  "duration_s": 5.2,
  "confidence": 0.87,
  "bbox_xyxy": [412, 188, 530, 460],
  "model": {"name": "ppe-detector", "version": "14", "alias": "champion"},
  "evidence": {"snapshot_uri": "s3://.../evt.jpg", "clip_uri": "s3://.../evt.mp4", "blurred": true},
  "schema_version": 1
}
```

### 10.2 Database tables (PostgreSQL)

```mermaid
erDiagram
  CAMERA ||--o{ ZONE : has
  CAMERA ||--o{ VIOLATION_EVENT : produces
  ZONE ||--o{ VIOLATION_EVENT : contains
  VIOLATION_EVENT ||--o{ REVIEW : receives
  MODEL_VERSION ||--o{ VIOLATION_EVENT : detected_by

  CAMERA {
    string id PK
    string name
    string rtsp_url_ref
    string site
    bool enabled
  }
  ZONE {
    string id PK
    string camera_id FK
    json polygon
    string rule_set
  }
  VIOLATION_EVENT {
    string id PK
    string idempotency_key UK
    string camera_id FK
    string zone_id FK
    string violation_type
    float confidence
    timestamp confirmed_at
    string model_version FK
    string status
  }
  REVIEW {
    string id PK
    string event_id FK
    string verdict
    string reviewer
    timestamp reviewed_at
  }
  MODEL_VERSION {
    string id PK
    string mlflow_run_id
    string alias
  }
```

RTSP credentials are never stored in the table; `rtsp_url_ref` points to the secret manager.

### 10.3 API surface (FastAPI, `/api/v1`)

| Method and path | Purpose |
|---|---|
| `GET/POST/PATCH /cameras` | Manage cameras |
| `GET/POST/PUT /cameras/{id}/zones` | Draw and edit restricted zones |
| `GET /events?camera=&type=&from=&to=&status=` | Query violations |
| `POST /events/{id}/ack` | Acknowledge an alert |
| `POST /events/{id}/review` | Reviewer verdict: `true_positive`, `false_positive`, `unsure` |
| `GET /review/queue` | Next items for human review (disputed and low-confidence first) |
| `GET /models/active` | Champion, challenger and shadow versions |
| `GET /healthz`, `GET /readyz` | Liveness and readiness |
| `GET /metrics` | Prometheus scrape endpoint |

### 10.4 Internal interfaces (Python `Protocol`s in `src/ppe`)

| Interface | Methods | Implementations |
|---|---|---|
| `Detector` | `predict(frames) -> list[list[Detection]]` | `YoloDetector`, `OnnxDetector`, `TrtDetector`, `SahiDetector`, `TritonClient` |
| `Tracker` | `update(detections, ts) -> list[Track]` | `ByteTracker` (and optionally DeepSORT) |
| `FrameSource` | `read() -> Frame` | RTSP capture, video file, replay |
| `Notifier` | `send(event) -> None` | Slack, webhook, email |
| `EventBus` | `publish(event)`, `consume(group)` | Redis Streams |

Programming against interfaces is what lets us swap YOLO for RT-DETR, or Redis for Kafka, by changing config and one class, not the pipeline.

### 10.5 Naming conventions

| Thing | Convention | Example |
|---|---|---|
| MLflow experiment | `ppe/<phase>` | `ppe/p3-ablations` |
| MLflow run | `<model>-<variant>-<imgsz>-<aug>` | `yolo11s-p2-960-aug2` |
| DVC dataset tag | `data-vN` | `data-v3` |
| App release tag | `vMAJOR.MINOR.PATCH` | `v0.6.0` |
| Image tag | git SHA and, on release, version | `ghcr.io/<user>/ppe-api:3f9c2ab` |
| Redis streams | `violations`, `violations.dlq` | |
| Prometheus metrics | `ppe_<component>_<name>_<unit>` | `ppe_inference_latency_seconds` |
