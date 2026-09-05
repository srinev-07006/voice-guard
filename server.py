import io
import librosa
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from detector import VoiceCloneDetector


app = FastAPI(title="VoiceGuard API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print("Initializing VoiceGuard ML Engine...")
detector = VoiceCloneDetector()

@app.get("/")
def read_root():
    return {"status": "VoiceGuard Backend is running live."}

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 Frontend connected to WebSocket.")
    
    try:
        while True:
            # 1. Receive raw audio bytes from the live call (React frontend)
            audio_bytes = await websocket.receive_bytes()
            
            # 2. Process entirely in volatile memory (DPDP Act Compliance)
            audio_buffer = io.BytesIO(audio_bytes)
            
            try:
                # 3. Load and format to exactly 16kHz mono for the model
                audio_data, sr = librosa.load(audio_buffer, sr=16000, mono=True)
                payload = {"raw": audio_data, "sampling_rate": sr}
                
                # 4. Pass the pre-processed array to the Fast Path model
                risk_score = detector.analyze_audio(payload)
                
                # 5. Instantly send the score back to the frontend UI
                if risk_score is not None:
                    await websocket.send_json({
                        "status": "success",
                        "risk_score": float(risk_score),
                        "is_synthetic": risk_score > 0.5  # Basic threshold flag
                    })
                else:
                    await websocket.send_json({"status": "error", "message": "Detection failed."})
                    
            except Exception as e:
                print(f"⚠️ Audio decoding error: {e}")
                await websocket.send_json({"status": "error", "message": str(e)})

    except WebSocketDisconnect:
        print("🔴 Frontend disconnected.")