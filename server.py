import io
import json
import librosa
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from detector import VoiceCloneDetector

# Initialize the FastAPI app
app = FastAPI(title="VoiceGuard API")

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
    
    try:
        while True:
            # 1. Receive incoming raw audio bytes
            audio_bytes = await websocket.receive_bytes()
            
            # MVP SIMULATION: In a full build, the frontend sends a JSON with both audio and live transcript.
            # Here, we mock a transcript that flags a "transfer" to prove the contextual logic works.
            mock_transcript = "I need to do an urgent transfer right now."
            context_flag = evaluate_context(mock_transcript)
            
            # 2. Process entirely in volatile memory
            audio_buffer = io.BytesIO(audio_bytes)
            
            try:
                # 3. Load and format to 16kHz mono. 
                # (Note: librosa handles standard WAV headers. We will ensure the React app sends compatible blobs).
                audio_data, sr = librosa.load(audio_buffer, sr=16000, mono=True)
                payload = {"raw": audio_data, "sampling_rate": sr}
                
                # 4. Fast Path inference (Acoustic Artifacts)
                risk_score = detector.analyze_audio(payload)
                
                if risk_score is not None:
                    # 5. Risk Fusion Engine (Acoustic + Context)
                    decision = get_decision_ladder(risk_score, context_flag)
                    
                    # 6. Dispatch operator-ready payload
                    await websocket.send_json({
                        "status": "success",
                        "risk_score": float(risk_score),
                        "is_synthetic": risk_score > 0.5,
                        "context_flagged": context_flag,
                        **decision
                    })
                else:
                    await websocket.send_json({"status": "error", "message": "Detection failed."})
                    
            except Exception as e:
                print(f"⚠️ Audio decoding error: {e}")
                await websocket.send_json({"status": "error", "message": "Audio format error. Waiting for next chunk."})

    except WebSocketDisconnect:
        print("🔴 Frontend disconnected.")