#!/usr/bin/env python3
"""Single source of truth for the repository layout.

Every file and folder in the project is declared once, below, with the phase
in which it is created and a one-line purpose. Everything else (the folder
tree, the per-phase file lists, the scaffold stubs) is generated from it,
so the docs can never drift away from the plan.

Usage
-----
    python scripts/repo_manifest.py tree                 # full annotated tree
    python scripts/repo_manifest.py phase 3              # everything Phase 3 creates
    python scripts/repo_manifest.py scaffold 3           # create empty stubs for Phase 3
    python scripts/repo_manifest.py scaffold 3 --dry-run # preview, create nothing
    python scripts/repo_manifest.py docs                 # regenerate the two generated docs

Phase kickoff ritual: `phase N` (read it) -> `scaffold N` (create stubs) ->
commit the stubs -> only then start filling files in, one at a time.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PHASE_NAMES: dict[int, str] = {
    0: "Foundations and framing",
    1: "Data engineering and annotation",
    2: "Baseline, evaluation harness and experiment tracking",
    3: "Model improvement and error analysis",
    4: "Video intelligence: tracking, rules and privacy",
    5: "Optimization and export",
    6: "Serving, services and the product surface",
    7: "ML testing and CI/CD",
    8: "Observability, monitoring and the feedback loop",
    9: "Cloud, Kubernetes and safe rollout",
    10: "Launch: demo, write-ups and interview kit",
}

# (path, phase, purpose). A trailing "/" means "folder with no tracked files yet".
MANIFEST: list[tuple[str, int, str]] = []


def add(phase: int, items: list[tuple[str, str]]) -> None:
    for path, why in items:
        MANIFEST.append((path, phase, why))


# --------------------------------------------------------------------------- #
# PHASE 0 - Foundations and framing
# --------------------------------------------------------------------------- #
add(0, [
    ("README.md", "Front door: what, why, how, architecture, results"),
    ("LICENSE", "Open-source license"),
    ("CONTRIBUTING.md", "Setup, branching, commits and PR flow"),
    ("CHANGELOG.md", "Release notes (Keep a Changelog format)"),
    ("Makefile", "One-command shortcuts: setup, lint, test, train, serve"),
    ("pyproject.toml", "Package metadata, dependencies, ruff/mypy/pytest config"),
    (".gitignore", "Keeps data, weights, secrets and caches out of Git"),
    (".dockerignore", "Keeps the Docker build context small"),
    (".editorconfig", "Consistent whitespace across editors"),
    (".env.example", "Documented environment variables (never real secrets)"),
    (".pre-commit-config.yaml", "ruff, mypy, detect-secrets, nbstripout on every commit"),
    (".github/CODEOWNERS", "Who must review which paths"),
    (".github/pull_request_template.md", "PR checklist including ML-specific checks"),
    (".github/ISSUE_TEMPLATE/bug_report.md", "Structured bug reports"),
    (".github/ISSUE_TEMPLATE/feature_request.md", "Structured feature requests"),
    (".github/workflows/ci.yml", "PR pipeline v1: lint, type-check, unit tests"),
    ("docs/PRD.md", "Product requirements: users, scope, cost of errors, metrics"),
    ("docs/DESIGN.md", "System design: requirements, scale, failure modes, trade-offs"),
    ("docs/ARCHITECTURE.md", "Component, runtime, ML-lifecycle and deployment diagrams"),
    ("docs/FOLDER_STRUCTURE.md", "Generated: complete annotated tree"),
    ("docs/ROADMAP.md", "Phases, learning goals, exit gates"),
    ("docs/PHASE_MANIFEST.md", "Generated: every file and folder, per phase"),
    ("docs/GIT_STRATEGY.md", "Branching, commits, tags, releases, data/model versioning"),
    ("docs/CICD.md", "CI, CD and continuous-training pipelines"),
    ("docs/ML_PIPELINE.md", "Data-to-model pipeline stages, contracts and gates"),
    ("docs/DEPLOYMENT.md", "Docker, Kubernetes, cloud, rollout and rollback"),
    ("docs/OBSERVABILITY.md", "Metrics, logs, traces, drift, dashboards, alerts"),
    ("docs/ENGINEERING_STANDARDS.md", "Clean-code, performance and testing rules"),
    ("docs/EXPERIMENTS.md", "Table of every training run and what changed"),
    ("docs/WHAT_FAILED.md", "Honest log of what did not work and why"),
    ("docs/DECISIONS.md", "Index of architecture decisions"),
    ("docs/adr/0001-record-architecture-decisions.md", "Why we keep ADRs"),
    ("docs/assets/", "Diagrams, screenshots, demo media"),
    ("scripts/repo_manifest.py", "This file: layout source of truth and scaffolder"),
    ("scripts/setup_dev.sh", "Create venv, install deps, install pre-commit hooks"),
    ("notebooks/00_env_check.ipynb", "Verify Colab/Kaggle GPU, CUDA and library versions"),
    ("docker/Dockerfile.base", "Slim Python base image shared by services"),
    ("src/ppe/__init__.py", "Package root"),
    ("src/ppe/py.typed", "Marks the package as typed"),
    ("src/ppe/version.py", "Single version string"),
    ("src/ppe/core/__init__.py", "Core package"),
    ("src/ppe/core/config.py", "Typed settings (pydantic-settings), YAML + env loading"),
    ("src/ppe/core/logging.py", "Structured JSON logging (structlog)"),
    ("src/ppe/core/types.py", "Shared dataclasses: Frame, Detection, Track, ViolationEvent"),
    ("src/ppe/core/exceptions.py", "Domain-specific exception hierarchy"),
    ("tests/__init__.py", "Test package"),
    ("tests/conftest.py", "Shared fixtures"),
    ("tests/unit/test_config.py", "Config loading and validation tests"),
    ("tests/unit/test_types.py", "Core dataclass tests"),
])

# --------------------------------------------------------------------------- #
# PHASE 1 - Data engineering and annotation
# --------------------------------------------------------------------------- #
add(1, [
    ("params.yaml", "DVC-tracked parameters (split seeds, thresholds, dataset version)"),
    ("dvc.yaml", "Data pipeline DAG: download -> convert -> validate -> split -> build"),
    (".dvcignore", "Files DVC should skip"),
    (".dvc/config", "DVC remote storage configuration"),
    ("configs/data/dataset.yaml", "Sources, paths, license flags per dataset"),
    ("configs/data/classes.yaml", "Unified class map across all datasets"),
    ("configs/data/splits.yaml", "Split policy: by camera/site/video, ratios, seed"),
    ("configs/data/validation.yaml", "Data-contract rules (bbox ranges, class ids, dedup)"),
    ("annotation/README.md", "How to run CVAT / Label Studio and import/export"),
    ("annotation/cvat_labels.json", "Label schema loaded into CVAT"),
    ("docs/data/LICENSES.md", "License and attribution of every dataset"),
    ("docs/data/LABELING_GUIDELINE.md", "What counts as helmet/vest/person, edge cases, examples"),
    ("docs/data/DATASET_CHANGELOG.md", "What changed between dataset versions and why"),
    ("docs/data/datasheet.md", "Datasheet for the dataset (composition, biases, limits)"),
    ("docs/theory/p1_data_and_annotation.md", "Teaching notes: data-centric AI, labels, leakage"),
    ("src/ppe/data/__init__.py", "Data package"),
    ("src/ppe/data/download.py", "Fetch public datasets, verify checksums"),
    ("src/ppe/data/convert.py", "VOC/COCO/Roboflow formats -> YOLO format"),
    ("src/ppe/data/unify_classes.py", "Map every source's labels onto the unified classes"),
    ("src/ppe/data/prelabel.py", "Auto-label with Grounding DINO / SAM for human correction"),
    ("src/ppe/data/cvat_io.py", "Import/export annotations to and from CVAT"),
    ("src/ppe/data/validate.py", "Pandera schemas and data-contract checks"),
    ("src/ppe/data/split.py", "Group-aware splits by camera/site/video"),
    ("src/ppe/data/leakage_audit.py", "Near-duplicate and group-overlap detection across splits"),
    ("src/ppe/data/label_noise.py", "cleanlab-based label-error finder"),
    ("src/ppe/data/agreement.py", "Inter-annotator agreement (IoU-matched kappa)"),
    ("src/ppe/data/stats.py", "Class balance, box-size and scene statistics"),
    ("scripts/download_data.sh", "One-command dataset download"),
    ("notebooks/01_eda.ipynb", "Exploratory data analysis"),
    ("tests/data/test_schema.py", "Schema contract tests"),
    ("tests/data/test_labels.py", "Label sanity tests (bbox bounds, class ids)"),
    ("tests/unit/test_split_no_leakage.py", "Proves no group appears in two splits"),
    ("tests/fixtures/", "Tiny sample dataset for fast tests"),
    (".github/workflows/data-ci.yml", "Validates data changes on pull requests"),
    ("data/raw/", "Untouched downloads (DVC-tracked, not in Git)"),
    ("data/interim/", "Converted and unified labels (DVC-tracked)"),
    ("data/processed/", "Final train/val/test in YOLO format (DVC-tracked)"),
    ("data/external/", "Third-party reference data (DVC-tracked)"),
    ("data/golden/", "Frozen, hand-verified test set from your own footage"),
])

# --------------------------------------------------------------------------- #
# PHASE 2 - Baseline, evaluation harness, experiment tracking
# --------------------------------------------------------------------------- #
add(2, [
    ("docker/Dockerfile.train", "CUDA training image, same deps as Colab/Kaggle"),
    ("configs/train/baseline_yolo.yaml", "Baseline YOLO training run"),
    ("configs/eval/eval.yaml", "Evaluation settings: IoU thresholds, conf, NMS"),
    ("src/ppe/core/seed.py", "Fix all random seeds for reproducibility"),
    ("src/ppe/evaluation/__init__.py", "Evaluation package"),
    ("src/ppe/evaluation/iou.py", "IoU, GIoU, DIoU, CIoU written from scratch"),
    ("src/ppe/evaluation/nms.py", "NMS and Soft-NMS written from scratch"),
    ("src/ppe/evaluation/metrics.py", "Precision/recall, AP, mAP computation"),
    ("src/ppe/evaluation/evaluate.py", "Run a model on a split and produce metrics"),
    ("src/ppe/evaluation/report.py", "Metric tables, PR curves, confusion matrix"),
    ("src/ppe/models/__init__.py", "Models package"),
    ("src/ppe/models/detector.py", "Detector interface (Protocol) every model implements"),
    ("src/ppe/models/yolo_detector.py", "YOLO implementation of the interface"),
    ("src/ppe/training/__init__.py", "Training package"),
    ("src/ppe/training/train.py", "Config-driven training entry point"),
    ("src/ppe/training/callbacks.py", "Logging and checkpoint callbacks"),
    ("src/ppe/training/tracking.py", "MLflow helpers: params, metrics, artifacts"),
    ("src/ppe/training/trainers/__init__.py", "Trainer implementations"),
    ("src/ppe/training/trainers/yolo.py", "YOLO trainer wrapper"),
    ("notebooks/02_baseline_colab.ipynb", "Run baseline on Colab/Kaggle"),
    ("docs/theory/p2_detection_fundamentals.md", "Anchors, IoU, NMS, FPN/PAN, focal loss, mAP"),
    ("docs/model_card.md", "Model card, started at baseline and updated every phase"),
    ("tests/unit/test_iou.py", "IoU variants vs known values"),
    ("tests/unit/test_nms.py", "NMS and Soft-NMS behavior tests"),
    ("tests/unit/test_metrics.py", "AP/mAP against reference implementation"),
    ("artifacts/", "Model weights and run outputs (gitignored, MLflow/DVC-tracked)"),
])

# --------------------------------------------------------------------------- #
# PHASE 3 - Model improvement and error analysis
# --------------------------------------------------------------------------- #
add(3, [
    ("configs/train/yolo11s_p2.yaml", "Small-object variant: higher resolution and P2 head"),
    ("configs/train/rtdetr.yaml", "RT-DETR transformer baseline"),
    ("configs/train/frcnn.yaml", "Faster R-CNN two-stage baseline"),
    ("configs/train/augmentation.yaml", "Augmentation recipes for ablations"),
    ("configs/train/optuna_space.yaml", "Hyperparameter search space"),
    ("configs/train/distill.yaml", "Teacher-student distillation settings"),
    ("configs/eval/slices.yaml", "Slice definitions: size, lighting, occlusion, camera"),
    ("src/ppe/data/augment.py", "Augmentation pipeline (mosaic, mixup, copy-paste, weather)"),
    ("src/ppe/data/torch_dataset.py", "PyTorch Dataset for non-YOLO trainers"),
    ("src/ppe/data/hard_negatives.py", "Hard-negative mining"),
    ("src/ppe/data/synthetic.py", "Synthetic data experiment (copy-paste, generated scenes)"),
    ("src/ppe/models/sahi_detector.py", "Sliced inference wrapper for small objects"),
    ("src/ppe/training/trainers/rtdetr.py", "RT-DETR trainer"),
    ("src/ppe/training/trainers/frcnn.py", "Faster R-CNN trainer"),
    ("src/ppe/training/tune.py", "Optuna hyperparameter search"),
    ("src/ppe/training/distill.py", "Distill a larger model into a smaller one"),
    ("src/ppe/evaluation/slices.py", "Per-slice metrics"),
    ("src/ppe/evaluation/error_analysis.py", "Categorize failures: miss, false alarm, localization"),
    ("src/ppe/evaluation/calibration.py", "Confidence calibration and reliability diagrams"),
    ("notebooks/03_error_analysis.ipynb", "Look at failures, decide what to fix"),
    ("docs/theory/p3_improving_detectors.md", "When to change data, model, resolution or loss"),
    ("docs/adr/0002-detector-family.md", "Evidence-based choice of detector family"),
    ("tests/unit/test_augment.py", "Augmentations keep boxes valid"),
])

# --------------------------------------------------------------------------- #
# PHASE 4 - Video intelligence: tracking, rules, privacy
# --------------------------------------------------------------------------- #
add(4, [
    ("configs/tracking/bytetrack.yaml", "Tracker thresholds and buffers"),
    ("configs/rules/zones.example.yaml", "Example restricted-zone polygons per camera"),
    ("configs/rules/violations.yaml", "Violation definitions: type, duration, cooldown"),
    ("src/ppe/tracking/__init__.py", "Tracking package"),
    ("src/ppe/tracking/base.py", "Tracker interface"),
    ("src/ppe/tracking/kalman.py", "Kalman filter motion model from scratch"),
    ("src/ppe/tracking/association.py", "IoU cost matrix and Hungarian matching"),
    ("src/ppe/tracking/bytetrack.py", "ByteTrack implementation"),
    ("src/ppe/rules/__init__.py", "Rule engine package"),
    ("src/ppe/rules/zones.py", "Polygons, point-in-polygon, zone membership"),
    ("src/ppe/rules/ppe_association.py", "Match helmet/vest boxes to person boxes"),
    ("src/ppe/rules/state_machine.py", "Per-track violation lifecycle with timers"),
    ("src/ppe/rules/engine.py", "Applies rules to tracked detections each frame"),
    ("src/ppe/rules/events.py", "ViolationEvent construction and dedup keys"),
    ("src/ppe/privacy/__init__.py", "Privacy package"),
    ("src/ppe/privacy/blur.py", "Face detection and blurring before storage"),
    ("src/ppe/video/__init__.py", "Video package"),
    ("src/ppe/video/overlay.py", "Draw boxes, tracks, zones on frames"),
    ("src/ppe/pipeline/__init__.py", "Offline pipeline package"),
    ("src/ppe/pipeline/runner.py", "detect -> track -> rules on a video file"),
    ("src/ppe/evaluation/tracking_metrics.py", "MOTA, IDF1, ID switches"),
    ("src/ppe/evaluation/business_metrics.py", "False alerts per camera per day, missed-violation rate"),
    ("src/ppe/evaluation/thresholds.py", "Pick thresholds by cost of errors"),
    ("notebooks/04_rules_demo.ipynb", "Watch the rule engine on sample video"),
    ("docs/theory/p4_tracking_and_rules.md", "Tracking by detection, why deterministic rules"),
    ("docs/PRIVACY_AND_COMPLIANCE.md", "Face blur, retention, on-prem vs cloud, worker consent"),
    ("docs/adr/0003-tracker-choice.md", "ByteTrack vs DeepSORT decision"),
    ("tests/unit/test_zones.py", "Geometry tests"),
    ("tests/unit/test_state_machine.py", "Violation lifecycle and timer tests"),
    ("tests/unit/test_association.py", "PPE-to-person matching tests"),
    ("tests/unit/test_tracking.py", "Tracker behavior and ID-switch tests"),
    ("tests/integration/test_pipeline_offline.py", "End-to-end offline pipeline on a sample clip"),
    ("tests/fixtures/sample_clip.mp4", "Short labeled clip for integration tests"),
])

# --------------------------------------------------------------------------- #
# PHASE 5 - Optimization and export
# --------------------------------------------------------------------------- #
add(5, [
    ("configs/export/onnx.yaml", "ONNX export settings"),
    ("configs/export/tensorrt.yaml", "TensorRT engine settings, FP16"),
    ("configs/export/quantization.yaml", "INT8 calibration settings"),
    ("src/ppe/export/__init__.py", "Export package"),
    ("src/ppe/export/to_onnx.py", "PyTorch -> ONNX"),
    ("src/ppe/export/to_tensorrt.py", "ONNX -> TensorRT engine"),
    ("src/ppe/export/quantize.py", "FP16 and INT8 post-training quantization"),
    ("src/ppe/export/parity_check.py", "Prove exported model matches the original"),
    ("src/ppe/models/onnx_detector.py", "ONNX Runtime detector"),
    ("src/ppe/models/trt_detector.py", "TensorRT detector"),
    ("scripts/export_model.py", "CLI for export and parity check"),
    ("scripts/benchmark_latency.py", "Latency and throughput benchmark: p50/p95/p99, FPS"),
    ("notebooks/05_tensorrt_colab.ipynb", "TensorRT and INT8 on a Colab GPU"),
    ("docs/BENCHMARKS.md", "Accuracy-vs-latency table per format and hardware"),
    ("docs/theory/p5_optimization_and_quantization.md", "FP16, INT8, PTQ vs QAT, batching"),
    ("tests/model/test_export_parity.py", "ONNX output matches PyTorch within tolerance"),
])

# --------------------------------------------------------------------------- #
# PHASE 6 - Serving, services, product surface
# --------------------------------------------------------------------------- #
add(6, [
    ("configs/serving/inference.yaml", "Model alias, batch size, timeouts"),
    ("configs/serving/ingest.yaml", "Camera sources, FPS sampling, reconnect policy"),
    ("configs/serving/alerts.yaml", "Cooldowns, channels, rate limits"),
    ("configs/env/dev.yaml", "Dev environment settings"),
    ("configs/env/staging.yaml", "Staging environment settings"),
    ("configs/env/prod.yaml", "Production environment settings"),
    ("src/ppe/video/capture.py", "RTSP/file reader with reconnect and backoff"),
    ("src/ppe/video/frame_sampler.py", "Frame skipping and timestamping"),
    ("src/ppe/video/clip_writer.py", "Evidence clip and snapshot writer"),
    ("src/ppe/privacy/retention.py", "Retention job: delete expired clips and rows"),
    ("src/ppe/models/registry.py", "Load model by MLflow alias and version"),
    ("src/ppe/models/triton_client.py", "Optional Triton Inference Server client"),
    ("src/ppe/messaging/__init__.py", "Messaging package"),
    ("src/ppe/messaging/streams.py", "Redis Streams producer/consumer helpers"),
    ("src/ppe/messaging/schemas.py", "Message schemas shared by services"),
    ("services/api/Dockerfile", "API image"),
    ("services/api/app/__init__.py", "API package"),
    ("services/api/app/main.py", "FastAPI app factory and middleware"),
    ("services/api/app/deps.py", "Dependency injection"),
    ("services/api/app/auth.py", "API-key / JWT auth"),
    ("services/api/app/schemas.py", "Request/response models"),
    ("services/api/app/db/__init__.py", "DB package"),
    ("services/api/app/db/models.py", "SQLAlchemy models: cameras, zones, events, feedback"),
    ("services/api/app/db/session.py", "Async session management"),
    ("services/api/app/routers/__init__.py", "Routers package"),
    ("services/api/app/routers/cameras.py", "Camera CRUD"),
    ("services/api/app/routers/zones.py", "Zone CRUD"),
    ("services/api/app/routers/events.py", "Violation events query and acknowledge"),
    ("services/api/app/routers/feedback.py", "Reviewer verdicts (true/false alert)"),
    ("services/api/app/routers/models.py", "Active model info"),
    ("services/api/app/routers/health.py", "Liveness and readiness probes"),
    ("services/api/alembic.ini", "Migration config"),
    ("services/api/alembic/env.py", "Migration environment"),
    ("services/api/alembic/versions/0001_init.py", "Initial schema"),
    ("services/stream_worker/Dockerfile", "Stream worker image"),
    ("services/stream_worker/main.py", "Per-camera process entry"),
    ("services/stream_worker/pipeline.py", "decode -> infer -> track -> rules -> publish"),
    ("services/inference/Dockerfile", "GPU inference image"),
    ("services/inference/main.py", "Inference API (gRPC/HTTP)"),
    ("services/inference/batcher.py", "Dynamic micro-batching across cameras"),
    ("services/inference/schemas.py", "Inference request/response models"),
    ("services/alert_worker/Dockerfile", "Alert worker image"),
    ("services/alert_worker/worker.py", "Consume events, dedup, persist, notify"),
    ("services/alert_worker/dedup.py", "Cooldown and duplicate suppression"),
    ("services/alert_worker/notifiers/__init__.py", "Notifier package"),
    ("services/alert_worker/notifiers/base.py", "Notifier interface"),
    ("services/alert_worker/notifiers/slack.py", "Slack notifier"),
    ("services/alert_worker/notifiers/webhook.py", "Generic webhook notifier"),
    ("services/alert_worker/notifiers/email.py", "Email notifier"),
    ("services/dashboard/Dockerfile", "Dashboard image"),
    ("services/dashboard/package.json", "Next.js dependencies"),
    ("services/dashboard/next.config.js", "Next.js config"),
    ("services/dashboard/src/app/page.tsx", "Overview: live status and KPIs"),
    ("services/dashboard/src/app/events/page.tsx", "Violation event list and detail"),
    ("services/dashboard/src/app/cameras/page.tsx", "Camera and zone management"),
    ("services/dashboard/src/app/review/page.tsx", "Human review queue (feeds active learning)"),
    ("services/dashboard/src/lib/api.ts", "Typed API client"),
    ("docker/docker-compose.yml", "Core stack: api, workers, inference, redis, postgres, minio"),
    ("docker/docker-compose.dev.yml", "Dev overrides: hot reload, mounted code"),
    ("docker/mediamtx.yml", "Local RTSP test server config"),
    ("scripts/replay_video.py", "Loop a video file as a fake RTSP camera"),
    ("scripts/seed_demo_data.py", "Seed cameras, zones and sample events"),
    ("docs/theory/p6_serving_systems.md", "Batching, queues, backpressure, idempotency"),
    ("docs/adr/0004-serving-stack.md", "Custom micro-batcher vs Triton decision"),
    ("tests/integration/test_api.py", "API contract tests"),
    ("tests/integration/test_alert_flow.py", "Event -> dedup -> persist -> notify"),
    ("tests/integration/test_stream_to_event.py", "Fake RTSP -> event, end to end"),
])

# --------------------------------------------------------------------------- #
# PHASE 7 - ML testing and CI/CD
# --------------------------------------------------------------------------- #
add(7, [
    ("configs/eval/gate.yaml", "Promotion thresholds a candidate model must pass"),
    ("src/ppe/evaluation/gate.py", "Compare candidate vs champion against the gate"),
    ("scripts/check_eval_gate.py", "CLI used by CI to pass or fail a candidate"),
    ("scripts/promote_model.py", "Move MLflow alias: challenger -> champion"),
    ("tests/model/test_golden_set.py", "Regression test on the frozen golden set"),
    ("tests/model/test_behavioral.py", "Invariance and directional behavior tests"),
    ("tests/model/test_slice_regression.py", "No critical slice may regress"),
    ("tests/data/test_golden_integrity.py", "Golden set hash must not change"),
    (".github/workflows/model-ci.yml", "Evaluates candidate models and enforces the gate"),
    (".github/workflows/build-images.yml", "Build, scan and push images tagged by git SHA"),
    (".github/workflows/cd-staging.yml", "Deploy to staging and run smoke + replay tests"),
    (".github/workflows/security.yml", "pip-audit, trivy, secret scanning"),
    (".github/dependabot.yml", "Automated dependency update PRs"),
    ("docs/theory/p7_ml_testing_and_cicd.md", "Testing pyramid for ML, gates, CI vs CD vs CT"),
])

# --------------------------------------------------------------------------- #
# PHASE 8 - Observability, monitoring, feedback loop
# --------------------------------------------------------------------------- #
add(8, [
    ("monitoring/prometheus/prometheus.yml", "Scrape config"),
    ("monitoring/prometheus/alert_rules.yml", "SLO and model-health alert rules"),
    ("monitoring/alertmanager/alertmanager.yml", "Alert routing and severities"),
    ("monitoring/grafana/provisioning/datasources/datasources.yml", "Prometheus and Loki datasources"),
    ("monitoring/grafana/provisioning/dashboards/dashboards.yml", "Dashboard auto-loading"),
    ("monitoring/grafana/dashboards/system_health.json", "Latency, throughput, GPU, queues"),
    ("monitoring/grafana/dashboards/model_quality.json", "Confidence, detection rates, drift"),
    ("monitoring/grafana/dashboards/business_kpis.json", "Violations, false-alert rate, acknowledgement"),
    ("monitoring/loki/loki-config.yml", "Log storage"),
    ("monitoring/promtail/promtail-config.yml", "Log shipping"),
    ("monitoring/otel/otel-collector.yml", "OpenTelemetry collector for traces"),
    ("docker/docker-compose.obs.yml", "Observability stack overlay"),
    ("configs/monitoring/drift.yaml", "Drift metrics, windows and thresholds"),
    ("configs/monitoring/sampling.yaml", "Active-learning sampling rules"),
    ("src/ppe/observability/__init__.py", "Observability package"),
    ("src/ppe/observability/metrics.py", "Prometheus metrics definitions"),
    ("src/ppe/observability/tracing.py", "OpenTelemetry setup"),
    ("src/ppe/observability/drift.py", "Input and prediction drift (Evidently)"),
    ("src/ppe/active_learning/__init__.py", "Active learning package"),
    ("src/ppe/active_learning/sampler.py", "Select low-confidence and disputed frames"),
    ("src/ppe/active_learning/export_to_cvat.py", "Push selected frames to CVAT"),
    ("src/ppe/active_learning/feedback_ingest.py", "Pull reviewer verdicts into the dataset"),
    ("pipelines/__init__.py", "Pipelines package"),
    ("pipelines/flows/data_refresh_flow.py", "Prefect flow: new labels -> new dataset version"),
    ("pipelines/flows/retrain_flow.py", "Prefect flow: train -> evaluate -> gate -> register"),
    ("pipelines/flows/evaluation_flow.py", "Scheduled re-evaluation on golden set"),
    ("pipelines/flows/drift_check_flow.py", "Scheduled drift report and trigger"),
    (".github/workflows/retrain.yml", "Manual/scheduled trigger of the CT pipeline"),
    ("docs/runbooks/high_false_alert_rate.md", "What to do when reviewers reject many alerts"),
    ("docs/runbooks/camera_offline.md", "What to do when a camera stops delivering frames"),
    ("docs/runbooks/drift_detected.md", "What to do when drift fires"),
    ("docs/theory/p8_monitoring_and_drift.md", "Drift vs degradation, delayed labels, SLOs"),
    ("tests/unit/test_drift.py", "Drift metric tests"),
    ("tests/unit/test_sampler.py", "Active-learning sampler tests"),
])

# --------------------------------------------------------------------------- #
# PHASE 9 - Cloud, Kubernetes, safe rollout
# --------------------------------------------------------------------------- #
add(9, [
    ("infra/terraform/main.tf", "Root module: network, cluster, registry, storage, DB"),
    ("infra/terraform/variables.tf", "Inputs"),
    ("infra/terraform/outputs.tf", "Outputs"),
    ("infra/terraform/backend.tf", "Remote state"),
    ("infra/terraform/modules/network/main.tf", "VPC/VNet and subnets"),
    ("infra/terraform/modules/k8s_cluster/main.tf", "Managed Kubernetes with CPU and GPU node pools"),
    ("infra/terraform/modules/registry/main.tf", "Container registry"),
    ("infra/terraform/modules/storage/main.tf", "Object storage for clips, datasets, artifacts"),
    ("infra/terraform/envs/staging.tfvars", "Staging values"),
    ("infra/terraform/envs/prod.tfvars", "Production values"),
    ("deploy/k8s/base/kustomization.yaml", "Base resource list"),
    ("deploy/k8s/base/namespace.yaml", "Namespace"),
    ("deploy/k8s/base/configmap.yaml", "Non-secret config"),
    ("deploy/k8s/base/secrets.example.yaml", "Secret shape (real secrets via secret manager)"),
    ("deploy/k8s/base/api.yaml", "API Deployment and Service"),
    ("deploy/k8s/base/stream-worker.yaml", "Stream worker Deployment"),
    ("deploy/k8s/base/inference.yaml", "GPU inference Deployment and Service"),
    ("deploy/k8s/base/alert-worker.yaml", "Alert worker Deployment"),
    ("deploy/k8s/base/dashboard.yaml", "Dashboard Deployment and Service"),
    ("deploy/k8s/base/redis.yaml", "Redis (or managed service reference)"),
    ("deploy/k8s/base/postgres.yaml", "Postgres (or managed service reference)"),
    ("deploy/k8s/base/hpa.yaml", "Autoscaling on queue lag and GPU utilization"),
    ("deploy/k8s/base/ingress.yaml", "Ingress and TLS"),
    ("deploy/k8s/base/networkpolicy.yaml", "Default-deny network policies"),
    ("deploy/k8s/overlays/staging/kustomization.yaml", "Staging patches"),
    ("deploy/k8s/overlays/prod/kustomization.yaml", "Production patches"),
    ("deploy/k8s/rollouts/canary-rollout.yaml", "Argo Rollouts canary with steps"),
    ("deploy/k8s/rollouts/analysis-template.yaml", "Automated metric checks that promote or roll back"),
    ("deploy/k8s/shadow/shadow-inference.yaml", "Shadow model receiving mirrored traffic"),
    (".github/workflows/cd-prod.yml", "Approval-gated production deploy"),
    ("scripts/smoke_test.sh", "Post-deploy health and flow check"),
    ("scripts/rollback.sh", "One-command rollback"),
    ("tests/load/locustfile.py", "Load test: p50/p95/p99 under camera count"),
    ("docs/COST_MODEL.md", "Cost per 1,000 frames and per camera per month"),
    ("docs/runbooks/model_rollback.md", "How and when to roll back a model"),
    ("docs/adr/0005-rollout-strategy.md", "Shadow, canary and rollback decision"),
    ("docs/theory/p9_rollout_and_cloud.md", "Shadow vs canary vs blue-green, K8s basics, cost control"),
])

# --------------------------------------------------------------------------- #
# PHASE 10 - Launch
# --------------------------------------------------------------------------- #
add(10, [
    ("demo/app.py", "Public demo (Gradio) for Hugging Face Spaces"),
    ("demo/requirements.txt", "Demo dependencies"),
    ("demo/README.md", "Space metadata and usage"),
    ("docs/RESULTS.md", "Final results, ablations, benchmarks, honest limitations"),
    ("docs/INTERVIEW_PREP.md", "Why this model, leakage, what broke, scale 100x"),
    ("docs/BLOG_POST.md", "Write-up: architecture, decisions, trade-offs"),
    ("docs/assets/architecture.png", "Exported architecture diagram"),
    ("docs/assets/demo.gif", "Short demo recording"),
])


# --------------------------------------------------------------------------- #
# Machinery
# --------------------------------------------------------------------------- #
def _check_unique() -> None:
    seen: set[str] = set()
    for path, _, _ in MANIFEST:
        if path in seen:
            raise SystemExit(f"duplicate manifest path: {path}")
        seen.add(path)


def _build_tree(entries: list[tuple[str, int, str]]) -> dict:
    root: dict = {}
    for path, phase, why in entries:
        parts = path.rstrip("/").split("/")
        cur = root
        for i, part in enumerate(parts):
            last = i == len(parts) - 1
            node = cur.setdefault(part, {"meta": None, "kids": {}, "dir": False})
            if not last or path.endswith("/"):
                node["dir"] = True
            if last:
                node["meta"] = (phase, why)
            cur = node["kids"]
    return root


def _min_phase(node: dict) -> int:
    phases = [node["meta"][0]] if node["meta"] else []
    phases += [_min_phase(k) for k in node["kids"].values()]
    return min(phases)


def render_tree(entries: list[tuple[str, int, str]] | None = None) -> str:
    tree = _build_tree(entries or MANIFEST)
    lines: list[str] = ["ppe-safety/"]

    def walk(kids: dict, prefix: str) -> None:
        items = sorted(kids.items(), key=lambda kv: (not kv[1]["dir"], kv[0].lower()))
        for i, (name, node) in enumerate(items):
            last = i == len(items) - 1
            branch = "└── " if last else "├── "
            label = name + ("/" if node["dir"] else "")
            if node["meta"]:
                note = f"[P{node['meta'][0]}] {node['meta'][1]}"
            else:
                note = f"[P{_min_phase(node)}]"
            lines.append(f"{prefix}{branch}{label:<46} # {note}")
            walk(node["kids"], prefix + ("    " if last else "│   "))

    walk(tree, "")
    return "\n".join(lines)


def folders_first_created_in(phase: int) -> list[str]:
    first: dict[str, int] = {}
    for path, ph, _ in MANIFEST:
        parts = path.rstrip("/").split("/")
        dirs = ["/".join(parts[: i + 1]) for i in range(len(parts) - 1)]
        if path.endswith("/"):
            dirs.append("/".join(parts))
        for d in dirs:
            first[d] = min(first.get(d, ph), ph)
    return sorted(d + "/" for d, ph in first.items() if ph == phase)


def phase_entries(phase: int) -> list[tuple[str, int, str]]:
    return sorted((e for e in MANIFEST if e[1] == phase), key=lambda e: e[0])


def render_phase(phase: int) -> str:
    entries = phase_entries(phase)
    files = [e for e in entries if not e[0].endswith("/")]
    out = [f"PHASE {phase}: {PHASE_NAMES[phase]}",
           f"{len(files)} files, {len(folders_first_created_in(phase))} new folders", ""]
    out.append("New folders:")
    out += [f"  {d}" for d in folders_first_created_in(phase)] or ["  (none)"]
    out.append("")
    out.append("Files:")
    out += [f"  {p:<58} {why}" for p, _, why in files]
    return "\n".join(out)


_NO_STUB = {".png", ".gif", ".mp4", ".ico", ".jpg"}


def _stub(path: str, phase: int, why: str) -> str | None:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in _NO_STUB:
        return None
    if p.name == "py.typed":
        return ""
    note = f"{why} (Phase {phase} stub)"
    if suffix == ".py":
        return f'"""{why}.\n\nPhase {phase} stub: created by scripts/repo_manifest.py scaffold.\n"""\n'
    if suffix == ".md":
        title = p.stem.replace("_", " ").replace("-", " ")
        return f"# {title}\n\n> Phase {phase}: {why}\n\n_TODO: fill in during Phase {phase}._\n"
    if suffix == ".json":
        return "{}\n"
    if suffix == ".ipynb":
        nb = {"cells": [{"cell_type": "markdown", "metadata": {},
                         "source": [f"# {p.stem}\n", f"Phase {phase}: {why}"]}],
              "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        return json.dumps(nb, indent=1) + "\n"
    if suffix in {".ts", ".tsx", ".js"}:
        return f"// {note}\n"
    if suffix == ".xml":
        return f"<!-- {note} -->\n"
    if suffix == ".sh":
        return f"#!/usr/bin/env bash\n# {note}\nset -euo pipefail\n"
    return f"# {note}\n"


def scaffold(phase: int, root: Path, dry_run: bool) -> None:
    created = skipped = 0
    for path, ph, why in phase_entries(phase):
        target = root / path
        if path.endswith("/"):
            print(f"{'would mkdir' if dry_run else 'mkdir'}  {path}")
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists():
            skipped += 1
            print(f"exists    {path}")
            continue
        body = _stub(path, ph, why)
        if body is None:
            print(f"skip      {path} (binary asset, add it yourself)")
            continue
        print(f"{'would create' if dry_run else 'create'}  {path}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        created += 1
    print(f"\nPhase {phase}: {created} created, {skipped} already existed.")


def write_docs(root: Path) -> None:
    files_total = sum(1 for p, _, _ in MANIFEST if not p.endswith("/"))
    header = ("<!-- GENERATED by scripts/repo_manifest.py. "
              "Edit the MANIFEST there, then run: python scripts/repo_manifest.py docs -->\n\n")

    tree_md = (
        header + "# Folder structure\n\n"
        "Every file and folder in the finished project, with the phase `[P#]` in which it is created.\n"
        f"Total: **{files_total} tracked files** across **{len(PHASE_NAMES)} phases**.\n\n"
        "Folders marked `DVC-tracked` or `gitignored` exist on disk but their contents are not in Git.\n\n"
        "```text\n" + render_tree() + "\n```\n\n"
        "## Why this layout\n\n"
        "| Top-level | Responsibility | Why it is separate |\n|---|---|---|\n"
        "| `src/ppe/` | Importable library: data, training, evaluation, tracking, rules, export | "
        "One tested codebase shared by research notebooks and production services |\n"
        "| `services/` | Deployable processes (API, stream worker, inference, alert worker, dashboard) | "
        "Each scales, fails and deploys independently; each has its own Dockerfile |\n"
        "| `configs/` | YAML for data, training, eval, serving, environments | "
        "Behavior changes without code changes; every run reproducible from a file |\n"
        "| `pipelines/` | Orchestrated flows (retrain, refresh, drift check) | "
        "Continuous training lives apart from library code |\n"
        "| `monitoring/` | Prometheus, Grafana, Loki, OTel config | Observability as code |\n"
        "| `infra/`, `deploy/` | Terraform and Kubernetes manifests | Infrastructure as code, reviewed like code |\n"
        "| `docker/` | Compose files and base images | Local-to-cloud parity |\n"
        "| `tests/` | unit, data, model, integration, load | Matches the ML testing pyramid |\n"
        "| `docs/` | PRD, design, ADRs, runbooks, theory notes | Decisions and teaching notes live with the code |\n"
    )
    (root / "docs" / "FOLDER_STRUCTURE.md").write_text(tree_md, encoding="utf-8")

    parts = [header + "# Phase manifest\n\n"
             "The complete list of files and folders created in each phase. "
             "At the start of a phase we read its section here, scaffold the stubs, "
             "commit them, and only then start filling files in one at a time.\n\n"
             "```bash\npython scripts/repo_manifest.py phase N      # read\n"
             "python scripts/repo_manifest.py scaffold N   # create stubs\n```\n"]
    parts.append("| Phase | Name | New files | New folders |\n|---|---|---|---|")
    for n, name in PHASE_NAMES.items():
        nf = sum(1 for p, ph, _ in MANIFEST if ph == n and not p.endswith("/"))
        parts.append(f"| {n} | {name} | {nf} | {len(folders_first_created_in(n))} |")
    parts.append("")
    for n, name in PHASE_NAMES.items():
        parts.append(f"## Phase {n}: {name}\n")
        folders = folders_first_created_in(n)
        parts.append("**New folders:** " + (", ".join(f"`{d}`" for d in folders) or "none") + "\n")
        parts.append("| File | Purpose |\n|---|---|")
        for p, _, why in phase_entries(n):
            if not p.endswith("/"):
                parts.append(f"| `{p}` | {why} |")
        parts.append("")
    (root / "docs" / "PHASE_MANIFEST.md").write_text("\n".join(parts), encoding="utf-8")
    print("wrote docs/FOLDER_STRUCTURE.md and docs/PHASE_MANIFEST.md")


def main() -> int:
    _check_unique()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tree")
    p_phase = sub.add_parser("phase")
    p_phase.add_argument("n", type=int, choices=sorted(PHASE_NAMES))
    p_sc = sub.add_parser("scaffold")
    p_sc.add_argument("n", type=int, choices=sorted(PHASE_NAMES))
    p_sc.add_argument("--root", default=".")
    p_sc.add_argument("--dry-run", action="store_true")
    p_docs = sub.add_parser("docs")
    p_docs.add_argument("--root", default=".")
    args = ap.parse_args()

    if args.cmd == "tree":
        print(render_tree())
    elif args.cmd == "phase":
        print(render_phase(args.n))
    elif args.cmd == "scaffold":
        scaffold(args.n, Path(args.root), args.dry_run)
    elif args.cmd == "docs":
        write_docs(Path(args.root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
