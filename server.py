import io
import json
import os
import tempfile
import librosa
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from detector import VoiceCloneDetector
import soundfile as sf

# Note to Team Domino: To use FULL memory-only processing, install pydub
# pip install pydub
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

# Initialize the FastAPI app
app = FastAPI(title="VoiceGuard API", version="1.0.0")

# Allow the React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Initializing VoiceGuard ML Engine...")
detector = VoiceCloneDetector()

# ==========================================
# 1 & 2: CONTEXT ENRICHMENT & STT ENGINE
# ==========================================

class IndicSTTEngine:
    """
    Simulates a Real-Time Indic Speech-To-Text pipeline.
    In production, this could wrap Bhashini APIs or Whisper-tiny specifically fine-tuned for diverse Indian Accents.
    """
    def transcribe(self, audio_data: np.ndarray) -> str:
        # Dummy behavior: returning a static transcript for demonstration purposes.
        return "I need to do an urgent transfer right now to a new beneficiary."

indic_stt = IndicSTTEngine()

def evaluate_context(transcript_text: str, transaction_metadata: dict = None) -> bool:
    """
    Uses Speech-to-Text and contextual metadata (amount, origin) to flag social engineering.
    """
    # High-risk social engineering keywords
    urgent_keywords = ["urgent", "transfer", "password", "beneficiary", "immediately", "otp", "pin"]
    text_lower = transcript_text.lower()
    keyword_flag = any(keyword in text_lower for keyword in urgent_keywords)

    # Metadata Enrichment logic
    if transaction_metadata:
        is_large_transfer = transaction_metadata.get("amount", 0) > 50000
        is_unknown_device = transaction_metadata.get("device_recognized", True) == False
        # If it's a large transfer from an unknown device, it's inherently suspicious
        if is_large_transfer and is_unknown_device:
            return True

    return keyword_flag

# ==========================================
# 3: ALERTING & CONFIGURABLE WORKFLOWS
# ==========================================

class WorkflowManager:
    """
    Centralized configuration for how the Decision Ladder resolves and alerts.
    """
    def __init__(self):
        self.thresholds = {
            "high": 0.70,
            "medium": 0.40
        }
        self.alerts_enabled = True

    def dispatch_alert(self, decision: dict, log: dict):
        if not self.alerts_enabled: return
        print(f"🔔 DISPATCHING CRITICAL ALERT via SMS/Email to Branch Manager: {decision['action']}")
        print(f"Logs: {json.dumps(log)}")

workflow_mgr = WorkflowManager()

def get_decision_ladder(risk_score: float, context_flagged: bool):
    """
    Fuses the multi-layer acoustic score and contextual intent into the 3-tier Decision Ladder.
    """
    if risk_score > workflow_mgr.thresholds["high"]:
        return {
            "risk_level": "HIGH",
            "action": "HOLD",
            "recommendation": "Pause transaction. Dispatch secondary out-of-band MFA verification.",
            "reason_code": "SYNTHETIC_ACOUSTIC_ANOMALY"
        }
    elif risk_score > workflow_mgr.thresholds["medium"] or (risk_score > 0.20 and context_flagged):
        return {
            "risk_level": "MEDIUM",
            "action": "VERIFY",
            "recommendation": "Prompt caller with dynamic historical security questions.",
            "reason_code": "ELEVATED_RISK_PROFILE"
        }
    else:
         return {
            "risk_level": "LOW",
            "action": "CONTINUE",
            "recommendation": "Proceed with standard operations.",
            "reason_code": "CLEAN_AUDIO_PROFILE"
        }

# ==========================================
# 4 & 5: REST API ENDPOINTS (ENTERPRISE APP INTEGRATION)
# ==========================================

class WorkflowConfigRequest(BaseModel):
    high_threshold: float
    medium_threshold: float
    alerts_enabled: bool

@app.post("/api/v1/workflows/config")
def update_workflow(config: WorkflowConfigRequest):
    """
    Allows enterprise admins to configure threshold triggers dynamically.
    """
    workflow_mgr.thresholds["high"] = config.high_threshold
    workflow_mgr.thresholds["medium"] = config.medium_threshold
    workflow_mgr.alerts_enabled = config.alerts_enabled
    return {"status": "success", "message": "Workflow thresholds updated securely."}

@app.post("/api/v1/analyze")
async def analyze_audio_rest(background_tasks: BackgroundTasks):
    """
    Placeholder REST endpoint for synchronous SDK integration.
    Expects multipart/form-data.
    """
    return {"status": "success", "message": "REST generic handler active. (Implemented in WS below)"}

@app.get("/")
def read_root():
    return {"status": "VoiceGuard Backend is running live with Multi-Layer Security."}


# ==========================================
# WEBSOCKET ENDPOINT (REAL-TIME STREAMING)
# ==========================================

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 Frontend connected to WebSocket API.")

    # Metadata can be established upon connection payload
    transaction_metadata = {"amount": 75000, "device_recognized": False}
    # Pretend a bank customer is on the line
    speaker_id = "cxo_user_123"

    try:
        while True:
            # 1. Receive incoming raw audio bytes
            audio_bytes = await websocket.receive_bytes()

            audio_data = None
            sr = 16000

            # 4. Privacy Module: In-Memory Zero-Disk Storage (if pydub is installed)
            if HAS_PYDUB:
                try:
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
                    audio_segment = audio_segment.set_frame_rate(sr).set_channels(1)
                    samples = audio_segment.get_array_of_samples()
                    audio_data = np.array(samples).astype(np.float32) / 32768.0
                except Exception as e:
                    print(f"Pydub memory processing failed: {e}. Falling back to tempfile.")

            # Fallback for systems without FFMPEG bound nicely to pydub
            if audio_data is None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                    temp_audio.write(audio_bytes)
                    temp_path = temp_audio.name
                try:
                    audio_data, sr = librosa.load(temp_path, sr=16000, mono=True)
                finally:
                    # SECURE COMPLIANCE: Erase physical trace instantly
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            try:
                # 2. Context Enrichment via STT
                live_transcript = indic_stt.transcribe(audio_data)
                context_flag = evaluate_context(live_transcript, transaction_metadata)

                payload = {"raw": audio_data, "sampling_rate": sr}

                # 3. Multi-Layer Inference (Wav2Vec2, Prosody, Vector Comparison)
                analysis_report = detector.analyze_audio(payload, speaker_id=speaker_id)

                if analysis_report is not None:
                    # 4. Risk Fusion Engine
                    risk_score = analysis_report["final_risk_score"]
                    decision = get_decision_ladder(risk_score, context_flag)

                    # 5. Alerting & Feature-Only Logging
                    if decision["risk_level"] == "HIGH":
                        workflow_mgr.dispatch_alert(decision, analysis_report["compliance_log"])

                    # 6. Dispatch operator-ready payload to the dashboard
                    await websocket.send_json({
                        "status": "success",
                        "risk_score": float(risk_score),
                        "is_synthetic": risk_score > 0.5,
                        "context_flagged": context_flag,
                        "acoustic_model_score": float(analysis_report["acoustic_model_score"]),
                        "speaker_mismatch": float(analysis_report["speaker_mismatch"]),
                        **decision
                    })
                else:
                    await websocket.send_json({"status": "error", "message": "Detection failed."})

            except Exception as e:
                print(f"⚠️ Audio decoding error: {e}")
                await websocket.send_json({"status": "error", "message": "Audio format error. Waiting for next chunk."})

    except WebSocketDisconnect:
        print("🔴 Frontend disconnected.")