import librosa
import numpy as np
from transformers import pipeline
import json
from scipy.spatial.distance import cosine
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class VoiceCloneDetector:
    """
    Multi-layer deepfake voice detection engine.

    Detection layers:
      1. Ensemble acoustic classification (multiple Wav2Vec2 / Whisper-based models)
      2. Spectral artifact analysis (HNR, spectral flux, rolloff, ZCR)
      3. Prosody analysis (pitch variation, jitter, shimmer, tempo regularity)
      4. Speaker embedding verification (ECAPA-TDNN via speechbrain)
      5. Calibrated weighted score fusion
    """

    # --------------- Fusion Weights (tuned per-layer) ---------------
    # These should ideally be learned from a validation set via logistic
    # regression, but hand-tuned defaults already beat the naive sum.
    FUSION_WEIGHTS = {
        "ensemble_acoustic":  0.50,   # primary signal
        "spectral_artifacts": 0.18,   # catches vocoder fingerprints
        "prosody":            0.12,   # TTS regularity
        "speaker_mismatch":   0.20,   # voice cloning identity check
    }

    def __init__(self):
        print("Loading AI models into memory... (This takes a moment)")

        # ── 1. Ensemble Acoustic Models ──────────────────────────────
        # Two independently trained deepfake detectors.  Their errors are
        # only weakly correlated, so averaging boosts effective accuracy.
        self.models = []

        print("  → Loading primary model (Hemgg/Deepfake-audio-detection)...")
        self.models.append(pipeline(
            "audio-classification",
            model="Hemgg/Deepfake-audio-detection",
        ))

        # Second model: a different architecture / training set for diversity
        try:
            print("  → Loading secondary model (mrm8488/wav2vec2-large-xlsr-53-fake-speech-detection)...")
            self.models.append(pipeline(
                "audio-classification",
                model="mrm8488/wav2vec2-large-xlsr-53-fake-speech-detection",
            ))
        except Exception as e:
            print(f"  ⚠ Secondary model unavailable ({e}); running single-model mode.")

        # ── 2. Speaker Embedding Model (ECAPA-TDNN) ─────────────────
        self.speaker_model = None
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            print("  → Loading speaker embedding model (ECAPA-TDNN)...")
            self.speaker_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                run_opts={"device": "cpu"},
            )
        except Exception as e:
            print(f"  ⚠ Speaker embedding model unavailable ({e}); using MFCC fallback.")

        # ── 3. Voice Print Store ────────────────────────────────────
        # In production: Milvus / Faiss backed by enrolled embeddings.
        # For demo, we store a random 192-dim mock profile.
        embedding_dim = 192 if self.speaker_model else 20
        self.historical_profiles = {
            "cxo_user_123": np.random.uniform(-1, 1, embedding_dim),
        }

        self._is_warmed_up = False
        print("Models loaded successfully!")
        self._warmup()

    # ================================================================
    # Warmup
    # ================================================================
    def _warmup(self):
        """Run a throwaway inference so first real call isn't slow."""
        if self._is_warmed_up:
            return
        print("Warming up audio detection model...")
        try:
            dummy = np.zeros(8000, dtype=np.float32)
            payload = {"raw": dummy, "sampling_rate": 16000}
            for model in self.models:
                _ = model(payload)
            self._is_warmed_up = True
            print("Model warmup complete.")
        except Exception as e:
            print(f"Model warmup failed: {e}")
            self._is_warmed_up = True

    # ================================================================
    # Audio Pre-processing & Quality Check
    # ================================================================
    @staticmethod
    def preprocess_audio(audio_data, sr):
        """
        Normalize, trim silence, and estimate signal quality.
        Returns (processed_audio, quality_info).
        """
        # DC offset removal
        audio_data = audio_data - np.mean(audio_data)

        # Peak normalization to [-1, 1]
        peak = np.max(np.abs(audio_data))
        if peak > 0:
            audio_data = audio_data / peak

        # Trim leading/trailing silence
        trimmed, _ = librosa.effects.trim(audio_data, top_db=25)
        if len(trimmed) < 1600:  # less than 0.1s at 16kHz
            trimmed = audio_data  # keep original if trim removed too much

        # SNR estimation (signal vs noise floor from quietest 10%)
        frame_energies = librosa.feature.rms(y=trimmed, frame_length=512, hop_length=256)[0]
        sorted_energies = np.sort(frame_energies)
        noise_floor = np.mean(sorted_energies[:max(1, len(sorted_energies) // 10)])
        signal_level = np.mean(sorted_energies[-max(1, len(sorted_energies) // 4):])
        snr_db = 20 * np.log10(signal_level / max(noise_floor, 1e-10))

        quality = {
            "snr_db": float(snr_db),
            "duration_s": len(trimmed) / sr,
            "clipped": bool(np.sum(np.abs(audio_data) > 0.99) > len(audio_data) * 0.01),
            "is_low_quality": bool(snr_db < 5.0),
        }

        return trimmed, quality

    # ================================================================
    # 1. Ensemble Acoustic Scoring
    # ================================================================
    def ensemble_acoustic_score(self, audio_data, sr):
        """
        Average deepfake probability across all loaded models.
        Returns (mean_fake_score, per_model_scores).
        """
        payload = {"raw": audio_data, "sampling_rate": sr}
        synthetic_keywords = ['fake', 'spoof', 'ai', 'synthetic', 'deepfake']
        model_scores = []

        for model in self.models:
            try:
                results = model(payload)
                fake_score = 0.0
                for r in results:
                    if any(k in r['label'].lower() for k in synthetic_keywords):
                        fake_score = r['score']
                        break
                model_scores.append(fake_score)
            except Exception as e:
                print(f"  ⚠ Model inference error: {e}")

        if not model_scores:
            return 0.0, []

        # Weighted average — first model (primary) gets slight extra weight
        if len(model_scores) == 1:
            return model_scores[0], model_scores

        weights = [0.55, 0.45] + [0.3] * (len(model_scores) - 2)
        weights = np.array(weights[:len(model_scores)])
        weights /= weights.sum()
        mean_score = float(np.dot(weights, model_scores))
        return mean_score, model_scores

    # ================================================================
    # 2. Spectral Artifact Analysis
    # ================================================================
    @staticmethod
    def extract_spectral_artifacts(audio_data, sr):
        """
        Extract features that vocoder-generated audio often gets wrong:
          - Harmonic-to-Noise Ratio (HNR)
          - Spectral flux irregularity
          - Spectral rolloff consistency
          - Zero-crossing rate statistics
          - Spectral bandwidth variance
        Returns a dict of features and a scalar anomaly score [0, 1].
        """
        if len(audio_data) < 2048:
            return {"anomaly_score": 0.0}

        n_fft = 2048
        hop = 512

        # Spectral flux (frame-to-frame change in magnitude spectrum)
        S = np.abs(librosa.stft(audio_data, n_fft=n_fft, hop_length=hop))
        flux = np.sqrt(np.sum(np.diff(S, axis=1) ** 2, axis=0))
        flux_cv = np.std(flux) / max(np.mean(flux), 1e-10)  # coefficient of variation

        # Spectral rolloff — should have natural variation
        rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr, hop_length=hop)[0]
        rolloff_cv = np.std(rolloff) / max(np.mean(rolloff), 1e-10)

        # Zero-crossing rate — vocoders produce unnaturally smooth waveforms
        zcr = librosa.feature.zero_crossing_rate(audio_data, frame_length=n_fft, hop_length=hop)[0]
        zcr_mean = np.mean(zcr)

        # Spectral bandwidth — TTS often has narrower bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sr, hop_length=hop)[0]
        bw_cv = np.std(bandwidth) / max(np.mean(bandwidth), 1e-10)

        # Spectral centroid variation
        centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sr, hop_length=hop)[0]
        centroid_cv = np.std(centroid) / max(np.mean(centroid), 1e-10)

        # Harmonic-to-Noise Ratio proxy via harmonic/percussive decomposition
        y_harmonic, y_percussive = librosa.effects.hpss(audio_data)
        harmonic_energy = np.sum(y_harmonic ** 2)
        total_energy = np.sum(audio_data ** 2) + 1e-10
        hnr_ratio = harmonic_energy / total_energy

        # Anomaly scoring: synthetic speech tends to have
        #   - very low spectral flux variation (too smooth)
        #   - very consistent rolloff / bandwidth (lacks natural variation)
        #   - abnormally high HNR (too clean, no natural noise)
        #   - unnaturally low ZCR (oversmoothed waveform)
        anomaly_signals = []

        # Flux too uniform → suspicious
        if flux_cv < 0.35:
            anomaly_signals.append(0.3)
        elif flux_cv < 0.50:
            anomaly_signals.append(0.1)

        # Rolloff too uniform → suspicious
        if rolloff_cv < 0.08:
            anomaly_signals.append(0.25)
        elif rolloff_cv < 0.15:
            anomaly_signals.append(0.1)

        # Bandwidth too uniform → suspicious
        if bw_cv < 0.10:
            anomaly_signals.append(0.2)

        # HNR too high (> 0.95 means barely any noise — unnatural)
        if hnr_ratio > 0.97:
            anomaly_signals.append(0.25)
        elif hnr_ratio > 0.93:
            anomaly_signals.append(0.1)

        anomaly_score = min(1.0, sum(anomaly_signals))

        return {
            "anomaly_score": float(anomaly_score),
            "flux_cv": float(flux_cv),
            "rolloff_cv": float(rolloff_cv),
            "zcr_mean": float(zcr_mean),
            "bandwidth_cv": float(bw_cv),
            "centroid_cv": float(centroid_cv),
            "hnr_ratio": float(hnr_ratio),
        }

    # ================================================================
    # 3. Prosody Analysis
    # ================================================================
    @staticmethod
    def extract_prosody_features(audio_data, sr):
        """
        Multi-dimensional prosody analysis beyond simple pitch variance.
        TTS/VC systems often produce speech that is too rhythmically regular.
        """
        if len(audio_data) < 4000:
            return {"prosody_score": 0.0, "pitch_variation": 0.0, "tempo": 0.0}

        # --- Pitch analysis ---
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr, hop_length=512)
        voiced = pitches[pitches > 0]
        pitch_std = float(np.std(voiced)) if len(voiced) > 0 else 0.0
        pitch_mean = float(np.mean(voiced)) if len(voiced) > 0 else 0.0

        # Pitch range ratio (natural speech has wider pitch excursions)
        if len(voiced) > 2:
            pitch_range = float(np.percentile(voiced, 95) - np.percentile(voiced, 5))
            pitch_range_norm = pitch_range / max(pitch_mean, 1.0)
        else:
            pitch_range_norm = 0.0

        # --- Jitter (pitch perturbation) ---
        # Natural speech has micro-variations between consecutive pitch periods
        if len(voiced) > 2:
            diffs = np.abs(np.diff(voiced))
            jitter = float(np.mean(diffs) / max(np.mean(voiced), 1e-10))
        else:
            jitter = 0.0

        # --- Shimmer (amplitude perturbation) ---
        rms = librosa.feature.rms(y=audio_data, frame_length=512, hop_length=256)[0]
        if len(rms) > 2:
            shimmer = float(np.mean(np.abs(np.diff(rms))) / max(np.mean(rms), 1e-10))
        else:
            shimmer = 0.0

        # --- Tempo regularity ---
        try:
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sr)
            tempo_val = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        except Exception:
            tempo_val = 0.0

        # --- Speech rate regularity (onset intervals) ---
        onsets = librosa.onset.onset_detect(y=audio_data, sr=sr, hop_length=512)
        if len(onsets) > 2:
            intervals = np.diff(onsets)
            rhythm_cv = float(np.std(intervals) / max(np.mean(intervals), 1e-10))
        else:
            rhythm_cv = 0.0

        # Score: TTS tends to have low jitter, low shimmer, uniform rhythm
        prosody_signals = []

        # Very flat pitch → suspicious
        if 0.0 < pitch_std < 5.0:
            prosody_signals.append(0.25)
        elif pitch_std < 15.0:
            prosody_signals.append(0.10)

        # Very narrow pitch range → suspicious
        if 0.0 < pitch_range_norm < 0.15:
            prosody_signals.append(0.15)

        # Unusually low jitter → suspicious (too perfect)
        if 0.0 < jitter < 0.005:
            prosody_signals.append(0.20)
        elif jitter < 0.015:
            prosody_signals.append(0.08)

        # Unusually low shimmer → suspicious
        if 0.0 < shimmer < 0.05:
            prosody_signals.append(0.15)

        # Very regular rhythm → suspicious
        if 0.0 < rhythm_cv < 0.15:
            prosody_signals.append(0.15)

        prosody_score = min(1.0, sum(prosody_signals))

        return {
            "prosody_score": float(prosody_score),
            "pitch_variation": pitch_std,
            "pitch_range_norm": pitch_range_norm,
            "jitter": jitter,
            "shimmer": shimmer,
            "tempo": tempo_val,
            "rhythm_cv": rhythm_cv,
        }

    # ================================================================
    # 4. Speaker Embedding Verification
    # ================================================================
    def get_speaker_embedding(self, audio_data, sr):
        """
        Extract a speaker embedding vector.
        Uses ECAPA-TDNN (192-dim) if available, falls back to MFCC (20-dim).
        """
        if self.speaker_model is not None:
            try:
                import torch
                # speechbrain expects a torch tensor
                waveform = torch.tensor(audio_data).unsqueeze(0).float()
                embedding = self.speaker_model.encode_batch(waveform)
                return embedding.squeeze().detach().numpy()
            except Exception as e:
                print(f"  ⚠ Speaker embedding failed ({e}); using MFCC fallback.")

        # MFCC fallback
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=20)
        return np.mean(mfccs, axis=1)

    def cross_session_check(self, speaker_id, audio_data, sr):
        """
        Compare incoming audio against the stored voice print.
        Returns (distance, is_mismatch).
        """
        if speaker_id not in self.historical_profiles:
            return 0.5, False  # unknown speaker, neutral

        embedding = self.get_speaker_embedding(audio_data, sr)
        known = self.historical_profiles[speaker_id]

        # If dimensions don't match (model changed), skip check
        if len(embedding) != len(known):
            return 0.5, False

        distance = float(cosine(known, embedding))
        # Threshold: cosine distance > 0.35 indicates speaker mismatch
        is_mismatch = distance > 0.35
        return distance, is_mismatch

    # ================================================================
    # 5. Calibrated Score Fusion
    # ================================================================
    def fuse_scores(self, acoustic_score, spectral_score, prosody_score,
                    speaker_distance, is_mismatch, quality_info):
        """
        Weighted fusion with quality-aware confidence adjustment.
        """
        w = self.FUSION_WEIGHTS

        # Speaker mismatch maps distance → penalty score
        speaker_score = min(1.0, speaker_distance * 1.5) if is_mismatch else 0.0

        raw_fused = (
            w["ensemble_acoustic"]  * acoustic_score +
            w["spectral_artifacts"] * spectral_score +
            w["prosody"]            * prosody_score +
            w["speaker_mismatch"]   * speaker_score
        )

        # Confidence discount for low-quality audio (noisy / clipped)
        confidence = 1.0
        if quality_info.get("is_low_quality"):
            confidence *= 0.75
        if quality_info.get("clipped"):
            confidence *= 0.85

        # Apply sigmoid-like calibration to push scores away from 0.5
        # (makes the score more decisive)
        calibrated = 1.0 / (1.0 + np.exp(-8.0 * (raw_fused - 0.45)))
        final = float(calibrated * confidence)

        return {
            "final_risk_score": round(final, 4),
            "raw_fused_score": round(float(raw_fused), 4),
            "confidence": round(confidence, 4),
        }

    # ================================================================
    # Main Analysis Entry Point
    # ================================================================
    def analyze_audio(self, audio_input, speaker_id=None):
        """
        Multi-Layer Authenticity Analysis:
          1. Audio preprocessing & quality check
          2. Ensemble acoustic classification
          3. Spectral artifact detection
          4. Prosody analysis
          5. Speaker verification
          6. Calibrated weighted fusion
        """
        try:
            # --- Load audio ---
            if isinstance(audio_input, str):
                audio_data, sampling_rate = librosa.load(audio_input, sr=16000, mono=True)
            else:
                audio_data = audio_input["raw"]
                sampling_rate = audio_input["sampling_rate"]

            # --- 1. Preprocess ---
            audio_clean, quality_info = self.preprocess_audio(audio_data, sampling_rate)

            # --- 2. Ensemble acoustic ---
            acoustic_score, per_model = self.ensemble_acoustic_score(audio_clean, sampling_rate)

            # --- 3. Spectral artifacts ---
            spectral = self.extract_spectral_artifacts(audio_clean, sampling_rate)

            # --- 4. Prosody ---
            prosody = self.extract_prosody_features(audio_clean, sampling_rate)

            # --- 5. Speaker verification ---
            speaker_dist, is_mismatch = 0.5, False
            if speaker_id:
                speaker_dist, is_mismatch = self.cross_session_check(
                    speaker_id, audio_clean, sampling_rate
                )

            # --- 6. Score fusion ---
            fusion = self.fuse_scores(
                acoustic_score,
                spectral["anomaly_score"],
                prosody["prosody_score"],
                speaker_dist,
                is_mismatch,
                quality_info,
            )

            # --- Compliance log (feature-only, no raw audio) ---
            compliance_log = {
                "timestamp_ms": "live_stream",
                "pitch_std": prosody["pitch_variation"],
                "rhythm_tempo": prosody["tempo"],
                "snr_db": quality_info["snr_db"],
                "spectral_hash": hash(tuple(
                    [spectral.get("flux_cv", 0), spectral.get("hnr_ratio", 0)]
                )),
            }

            return {
                # Primary output
                "final_risk_score": fusion["final_risk_score"],
                "acoustic_model_score": acoustic_score,

                # Detailed layer scores
                "per_model_scores": per_model,
                "spectral_anomaly_score": spectral["anomaly_score"],
                "prosody_score": prosody["prosody_score"],
                "speaker_mismatch": float(is_mismatch),
                "speaker_distance": speaker_dist,

                # Quality
                "audio_quality": quality_info,
                "confidence": fusion["confidence"],
                "raw_fused_score": fusion["raw_fused_score"],

                # Layer details (for dashboard drill-down)
                "spectral_details": {
                    k: v for k, v in spectral.items() if k != "anomaly_score"
                },
                "prosody_details": {
                    k: v for k, v in prosody.items()
                    if k not in ("prosody_score", "pitch_variation", "tempo")
                },

                # Compliance
                "compliance_log": compliance_log,
            }

        except Exception as e:
            print(f"Error processing audio: {e}")
            import traceback
            traceback.print_exc()
            return None


# ====================================================================
# CLI test
# ====================================================================
if __name__ == "__main__":
    detector = VoiceCloneDetector()

    print("\n" + "=" * 60)
    print("Testing with REAL audio samples")
    print("=" * 60)
    for label, path in [
        ("REAL sample1", r"D:\Projects\VoiceGuard\audios\real\sample.wav"),
        ("REAL sample2", r"D:\Projects\VoiceGuard\audios\real\sample2.wav"),
        ("FAKE sample1", r"D:\Projects\VoiceGuard\audios\fake\sample.wav"),
        ("FAKE sample2", r"D:\Projects\VoiceGuard\audios\fake\sample2.wav"),
    ]:
        print(f"\n--- {label} ---")
        analysis = detector.analyze_audio(path, speaker_id="cxo_user_123")
        if analysis:
            score_pct = analysis['final_risk_score'] * 100
            emoji = "🔴" if score_pct > 70 else "🟡" if score_pct > 40 else "🟢"
            print(f"  {emoji} Risk Score: {score_pct:.1f}%")
            print(f"     Acoustic: {analysis['acoustic_model_score']:.3f}")
            print(f"     Spectral: {analysis['spectral_anomaly_score']:.3f}")
            print(f"     Prosody:  {analysis['prosody_score']:.3f}")
            print(f"     Speaker:  {analysis['speaker_distance']:.3f} (mismatch={bool(analysis['speaker_mismatch'])})")
            print(f"     Quality:  SNR={analysis['audio_quality']['snr_db']:.1f}dB, confidence={analysis['confidence']:.2f}")
        else:
            print("  ❌ Analysis failed.")
