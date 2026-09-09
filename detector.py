import librosa
import numpy as np
from transformers import pipeline
import json
from scipy.spatial.distance import cosine

class VoiceCloneDetector:
    def __init__(self):
        print("Loading AI models into memory... (This takes a moment)")
        # 1. Acoustic/Spectral Model (Wav2Vec2)
        self.pipe = pipeline(
            "audio-classification",
            model="Hemgg/Deepfake-audio-detection"
        )

        # 2. Mock Vector Database for Cross-Session Speaker Verification
        # In production, this would be Milvus or Faiss, storing embedded voice prints of authenticated users.
        self.historical_profiles = {
            # Dummy MFCC mean profile for a legitimate "Account Owner"
            "cxo_user_123": np.random.uniform(-10, 10, 20)
        }

        # Warmup flag to track if model has been warmed up
        self._is_warmed_up = False

        print("Models loaded successfully!")
        # Warm up the model during startup so early detections are fast
        self._warmup()

    def _warmup(self):
        """Warmup the model on a small audio sample to avoid delay on first real detection."""
        if self._is_warmed_up:
            return

        print("Warming up audio detection model...")
        try:
            # Create a small dummy audio signal (0.5 seconds at 16kHz)
            dummy_audio = np.zeros(8000, dtype=np.float32)
            dummy_payload = {"raw": dummy_audio, "sampling_rate": 16000}

            # Run a dummy inference to trigger model warmup
            _ = self.pipe(dummy_payload)

            self._is_warmed_up = True
            print("Model warmup complete.")
        except Exception as e:
            print(f"Model warmup failed: {e}")
            self._is_warmed_up = True  # Don't retry warmup

    def extract_prosody_and_features(self, audio_data, sr):
        """
        Extracts prosody attributes (pitch, rhythm, spectral signatures)
        and computes MFCCs for speaker verification.
        """
        # Fast path for very short or near-silent audio chunks to avoid heavy DSP calculations
        if len(audio_data) < 1000 or np.max(np.abs(audio_data)) < 1e-4:
            return {
                "pitch_variation": 0.0,
                "tempo": 0.0,
                "spectral_centroid_mean": 0.0,
                "mfcc_vector": np.zeros(20),
                "anonymized_spectral_log": [0.0] * 10
            }

        # Prosody: Fundamental Frequency (Pitch) Variation
        # Using a smaller n_fft / hop_length or sub-sampling for faster processing on real-time chunks
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr, hop_length=512)
        pitch_variations = pitch_contour = pitches[pitches > 0]
        pitch_std = np.std(pitch_contour) if len(pitch_contour) > 0 else 0

        # Prosody: Speech Rhythm (Tempo)
        try:
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sr)
            tempo_val = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        except Exception:
            tempo_val = 0.0

        # Spectral Artifacts (Phase & Spectral Centroid)
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
        centroid_mean = np.mean(spectral_centroids)

        # Speaker Embeddings (MFCCs as proxy for embedding vector)
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=20)
        mfcc_mean = np.mean(mfccs, axis=1)

        return {
            "pitch_variation": float(pitch_std),
            "tempo": tempo_val,
            "spectral_centroid_mean": float(centroid_mean),
            "mfcc_vector": mfcc_mean,
            # Feature-only log (anonymized array without reverse-synthesizable raw audio)
            "anonymized_spectral_log": spectral_centroids[:10].tolist()
        }

    def cross_session_check(self, speaker_id, mfcc_vector):
        """
        Calculates cosine similarity between incoming audio features and the known historical profile.
        Returns a score from 0.0 (exact match) to 1.0 (completely different).
        """
        if speaker_id not in self.historical_profiles:
            return 0.5 # Unknown speaker, neutral match

        known_profile = self.historical_profiles[speaker_id]
        distance = cosine(known_profile, mfcc_vector)
        return float(distance)

    def analyze_audio(self, audio_input, speaker_id=None):
        """
        Multi-Layer Authenticity Analysis:
        1. Deepfake Acoustic Artifacts (Wav2Vec2)
        2. Prosody & Rhythm Analysis (Librosa)
        3. Cross-session consistency (Verification)
        """
        try:
            if isinstance(audio_input, str):
                audio_data, sampling_rate = librosa.load(audio_input, sr=16000, mono=True)
            else:
                audio_data = audio_input["raw"]
                sampling_rate = audio_input["sampling_rate"]

            payload = {"raw": audio_data, "sampling_rate": sampling_rate}

            # 1. Pipeline inference
            results = self.pipe(payload)

            # Base acoustic score from Wav2Vec2
            base_score = 0.0
            synthetic_keywords = ['fake', 'spoof', 'ai', 'synthetic']
            for result in results:
                if any(k in result['label'].lower() for k in synthetic_keywords):
                    base_score = result['score']
                    break

            # 2. Extract Prosody and DSP Features
            features = self.extract_prosody_and_features(audio_data, sampling_rate)

            # Simulated heuristic: AI generated TTS often has very low pitch variance and perfectly uniform tempo.
            # If pitch variance is unnaturally flat (< 2.0), increase fake probability.
            prosody_penalty = 0.0
            if features["pitch_variation"] > 0 and features["pitch_variation"] < 2.0:
                prosody_penalty += 0.15

            # 3. Cross-Session Verification
            speaker_mismatch_penalty = 0.0
            if speaker_id:
                distance = self.cross_session_check(speaker_id, features["mfcc_vector"])
                # If distance > 0.4, it doesn't sound like the registered speaker (voice cloning attack)
                if distance > 0.4:
                    speaker_mismatch_penalty += 0.20

            # 4. Feature-Only Logging Compliance (Saves metadata without raw audio files)
            compliance_log = {
                "timestamp_ms": "live_stream",
                "pitch_std": features["pitch_variation"],
                "rhythm_tempo": features["tempo"],
                "spectral_hash": hash(tuple(features["anonymized_spectral_log"]))
            }

            final_risk_score = min(1.0, base_score + prosody_penalty + speaker_mismatch_penalty)

            return {
                "final_risk_score": final_risk_score,
                "acoustic_model_score": base_score,
                "prosody_penalty": prosody_penalty,
                "speaker_mismatch": speaker_mismatch_penalty,
                "compliance_log": compliance_log
            }

        except Exception as e:
            print(f"Error processing audio: {e}")
            return None


if __name__ == "__main__":
    detector = VoiceCloneDetector()
    test_audio = r"D:\Projects\VoiceGuard\audios\real\sample2.wav"

    analysis = detector.analyze_audio(test_audio, speaker_id="cxo_user_123")
    if analysis:
        print(f"⚠️ Multi-Layer Risk Score: {analysis['final_risk_score'] * 100:.2f}%")
        print(f"Details: {json.dumps(analysis, indent=2)}")
    else:
        print("Analysis failed.")