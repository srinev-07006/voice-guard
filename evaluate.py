"""
VoiceGuard Evaluation Harness
=============================
Runs the detector against all labeled audio files and reports:
  - Per-file risk scores and classification
  - Confusion matrix
  - Precision, Recall, F1, Accuracy
  - Layer-by-layer score breakdown

Usage:
    python evaluate.py                    # run full evaluation
    python evaluate.py --threshold 0.5    # custom decision threshold
    python evaluate.py --verbose          # print per-file details
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path

import numpy as np

from detector import VoiceCloneDetector


AUDIO_DIR = Path(__file__).parent / "audios"
THRESHOLD = 0.50  # default: score > threshold → classified as fake


def discover_samples(audio_dir: Path):
    """Find labeled audio files under audio_dir/real/ and audio_dir/fake/."""
    samples = []
    for label_dir, ground_truth in [("real", 0), ("fake", 1)]:
        folder = audio_dir / label_dir
        if not folder.exists():
            print(f"⚠ Directory not found: {folder}")
            continue
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in (".wav", ".mp3", ".flac", ".ogg", ".webm"):
                samples.append((str(f), ground_truth, f.name, label_dir))
    return samples


def run_evaluation(threshold: float, verbose: bool):
    print("=" * 65)
    print("  VoiceGuard Detection Accuracy Evaluation")
    print("=" * 65)

    samples = discover_samples(AUDIO_DIR)
    if not samples:
        print("❌ No audio samples found. Place files in audios/real/ and audios/fake/.")
        sys.exit(1)

    print(f"\nFound {len(samples)} labeled audio files:")
    for path, gt, name, label in samples:
        print(f"  {'🔴 FAKE' if gt else '🟢 REAL'} — {label}/{name}")

    print(f"\nDecision threshold: {threshold}")
    print("\nLoading detector...\n")
    detector = VoiceCloneDetector()

    results = []
    total_time = 0.0

    print("\n" + "-" * 65)
    for path, ground_truth, name, label in samples:
        start = time.time()
        analysis = detector.analyze_audio(path, speaker_id="cxo_user_123")
        elapsed = time.time() - start
        total_time += elapsed

        if analysis is None:
            print(f"  ❌ FAILED — {label}/{name}")
            continue

        risk = analysis["final_risk_score"]
        predicted = 1 if risk > threshold else 0
        correct = predicted == ground_truth

        results.append({
            "file": f"{label}/{name}",
            "ground_truth": ground_truth,
            "predicted": predicted,
            "risk_score": risk,
            "acoustic": analysis["acoustic_model_score"],
            "spectral": analysis.get("spectral_anomaly_score", 0),
            "prosody": analysis.get("prosody_score", 0),
            "speaker_dist": analysis.get("speaker_distance", 0),
            "confidence": analysis.get("confidence", 1.0),
            "snr_db": analysis.get("audio_quality", {}).get("snr_db", 0),
            "correct": correct,
            "latency_ms": elapsed * 1000,
        })

        icon = "✅" if correct else "❌"
        truth_label = "FAKE" if ground_truth else "REAL"
        pred_label = "FAKE" if predicted else "REAL"
        print(
            f"  {icon} {label}/{name:15s} "
            f"truth={truth_label:4s}  pred={pred_label:4s}  "
            f"risk={risk:.3f}  acoustic={analysis['acoustic_model_score']:.3f}  "
            f"spectral={analysis.get('spectral_anomaly_score', 0):.3f}  "
            f"prosody={analysis.get('prosody_score', 0):.3f}  "
            f"[{elapsed*1000:.0f}ms]"
        )

    print("-" * 65)

    if not results:
        print("\n❌ No results to analyze.")
        sys.exit(1)

    # ── Metrics ──────────────────────────────────────────────────
    gts = [r["ground_truth"] for r in results]
    preds = [r["predicted"] for r in results]

    tp = sum(1 for g, p in zip(gts, preds) if g == 1 and p == 1)
    tn = sum(1 for g, p in zip(gts, preds) if g == 0 and p == 0)
    fp = sum(1 for g, p in zip(gts, preds) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(gts, preds) if g == 1 and p == 0)

    accuracy  = (tp + tn) / max(len(results), 1)
    precision = tp / max(tp + fp, 1)
    recall    = tp / max(tp + fn, 1)
    f1        = 2 * precision * recall / max(precision + recall, 1e-10)

    print(f"\n{'=' * 65}")
    print(f"  RESULTS SUMMARY  (threshold = {threshold})")
    print(f"{'=' * 65}")
    print(f"\n  Confusion Matrix:")
    print(f"                    Predicted REAL    Predicted FAKE")
    print(f"    Actual REAL         {tn:3d}               {fp:3d}")
    print(f"    Actual FAKE         {fn:3d}               {tp:3d}")
    print()
    print(f"  Accuracy:   {accuracy:.2%}  ({tp+tn}/{len(results)})")
    print(f"  Precision:  {precision:.2%}  (of predicted fakes, how many were truly fake)")
    print(f"  Recall:     {recall:.2%}  (of actual fakes, how many did we catch)")
    print(f"  F1 Score:   {f1:.2%}")
    print()
    print(f"  Avg latency:  {total_time / len(results) * 1000:.0f} ms / sample")
    print(f"  Total time:   {total_time:.1f}s for {len(results)} samples")
    print()

    # ── Layer contribution summary ───────────────────────────────
    if verbose:
        print(f"\n  Per-Layer Score Averages:")
        for layer in ["acoustic", "spectral", "prosody", "speaker_dist"]:
            vals_real = [r[layer] for r in results if r["ground_truth"] == 0]
            vals_fake = [r[layer] for r in results if r["ground_truth"] == 1]
            avg_real = np.mean(vals_real) if vals_real else 0
            avg_fake = np.mean(vals_fake) if vals_fake else 0
            sep = abs(avg_fake - avg_real)
            print(f"    {layer:15s}  real_avg={avg_real:.3f}  fake_avg={avg_fake:.3f}  separation={sep:.3f}")
        print()

    # ── Save results to JSON ─────────────────────────────────────
    report_path = Path(__file__).parent / "evaluation_report.json"
    report = {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "avg_latency_ms": total_time / len(results) * 1000,
        "samples": results,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  📊 Full report saved to: {report_path}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoiceGuard Detection Accuracy Evaluation")
    parser.add_argument("--threshold", type=float, default=THRESHOLD,
                        help=f"Risk score threshold for fake classification (default: {THRESHOLD})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed per-layer analysis")
    args = parser.parse_args()

    run_evaluation(args.threshold, args.verbose)
