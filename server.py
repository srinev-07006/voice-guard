import io
import json
import os
import tempfile
import librosa
import numpy as np
from collections import deque
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from detector import VoiceCloneDetector

# Initialize the FastAPI app
app = FastAPI(title="VoiceGuard API")

# Allow the frontend to communicate with this backend
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
# MVP RISK FUSION & CONTEXT ENGINE
# ==========================================

def evaluate_context(transcript_text: str) -> bool:
    """
    Simulates the Slow Path (Whisper + LLM). 
    Flags transcripts containing high-risk social engineering urgency.
    """
    urgent_keywords = ["urgent", "transfer", "password", "beneficiary", "immediately", "account"]
    text_lower = transcript_text.lower()
    return any(keyword in text_lower for keyword in urgent_keywords)

def get_decision_ladder(risk_score: float, context_flagged: bool):
    """
    Fuses the acoustic score and contextual intent into the 3-tier Decision Ladder.
    """
    if risk_score > 0.70:
        return {
            "risk_level": "HIGH",
            "action": "HOLD",
            "recommendation": "Pause transaction. Require secondary out-of-band verification.",
            "reason_code": "SYNTHETIC_ACOUSTIC_ANOMALY"
        }
    elif risk_score > 0.40 or (risk_score > 0.20 and context_flagged):
        return {
            "risk_level": "MEDIUM",
            "action": "VERIFY",
            "recommendation": "Prompt caller with dynamic security questions or trigger callback.",
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
# WEBSOCKET ENDPOINT
# ==========================================

@app.get("/")
def read_root():
    return {"status": "VoiceGuard Backend is running live."}

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 Frontend connected to WebSocket.")
    
    # Temporal smoothing queue (stores the last 3 chunks to prevent erratic jumps)
    score_history = deque(maxlen=3)
    
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            
            mock_transcript = "I need to do an urgent transfer right now."
            context_flag = evaluate_context(mock_transcript)
            
            # Secure Temporary Processing (DPDP Act Compliant)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
            
            try:
                # Load and format to exactly 16kHz mono
                audio_data, sr = librosa.load(temp_path, sr=16000, mono=True)
                os.remove(temp_path)
                
                # Voice Activity Detection (VAD): Filter out background silence
                volume = np.mean(np.abs(audio_data))
                if volume < 0.005:
                    # If it's just silence/noise, default to a safe baseline score
                    risk_score = 0.05
                else:
                    payload = {"raw": audio_data, "sampling_rate": sr}
                    raw_score = detector.analyze_audio(payload)
                    risk_score = raw_score if raw_score is not None else 0.05
                
                # Apply Temporal Smoothing (Rolling Average)
                score_history.append(float(risk_score))
                smoothed_score = sum(score_history) / len(score_history)
                
                # Risk Fusion Engine (Acoustic + Context)
                decision = get_decision_ladder(smoothed_score, context_flag)
                
                # Dispatch operator-ready payload to the dashboard
                await websocket.send_json({
                    "status": "success",
                    "risk_score": float(smoothed_score),
                    "is_synthetic": smoothed_score > 0.5,
                    "context_flagged": context_flag,
                    **decision
                })
                    
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"⚠️ Audio decoding error: {e}")
                await websocket.send_json({"status": "error", "message": "Audio format error. Waiting for next chunk."})

    except WebSocketDisconnect:
        print("🔴 Frontend disconnected.")