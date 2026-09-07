# VoiceGuard 🛡️
> **Smart India Hackathon 2026** | Problem Statement 26104: AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks.

## Project Overview
VoiceGuard is a real-time deepfake voice defense system designed to intercept, analyze, and flag AI-generated audio during live telephonic and VoIP communications. Built to operate under strict sub-second latency constraints, this MVP utilizes a decoupled processing architecture and a dynamic risk-scoring engine.

### Key Features
*   **The Fast Path (Acoustic Detection):** Captures live audio from the browser in sliding 2.5-second windows, passing raw data to a Wav2Vec2 transformer to instantly identify synthetic speech artifacts.
*   **The Slow Path (Context & Intent):** Evaluates the conversational context for urgent social engineering patterns (e.g., "urgent transfer"), combining intent with the acoustic score to build a holistic threat profile.
*   **Safe Decision Ladder:** Fuses multiple signals into actionable, operator-ready alerts categorized into three tiers:
    *   🟢 **LOW:** Continue (Clean Audio Profile)
    *   🟡 **MEDIUM:** Verify (Elevated Risk Profile)
    *   🔴 **HIGH:** Hold (Synthetic Acoustic Anomaly)
*   **Privacy by Design:** Audio is streamed via WebSockets and processed dynamically in volatile RAM (`io.BytesIO`). No raw `.wav` files are ever saved to disk, ensuring strict adherence to the DPDP Act 2023.

---

## Core Tech Stack
*   **Frontend:** Vanilla HTML5, JavaScript (MediaRecorder API), Tailwind CSS (via CDN for rapid UI).
*   **Backend Transport:** Python, FastAPI, WebSockets (Continuous, low-latency streaming).
*   **Machine Learning:** PyTorch, Hugging Face `pipeline` (`Hemgg/Deepfake-audio-detection`).
*   **Signal Processing:** `librosa`, `soundfile` (16kHz mono normalization).

---

## Quickstart Guide

### 1. Backend Setup (Inference Engine)
Follow these steps to initialize the machine learning environment and launch the continuous detection server.

1.  **Clone the Repository:** Pull the source code to your local machine.
2.  **Initialize the Environment:** 
    ```bash
    python -m venv sih_env
    ```
3.  **Activate the Environment:** 
    *   Windows: `sih_env\Scripts\activate`
    *   Mac/Linux: `source sih_env/bin/activate`
4.  **Install Dependencies:** 
    ```bash
    pip install -r requirements.txt
    ```
5.  **Start the Server:** Launch the FastAPI WebSocket backend.
    ```bash
    python -m uvicorn server:app --reload
    ```

### 2. Frontend Setup (Live Dashboard)
Because the MVP frontend is built for maximum speed and zero-configuration, there is no build step required.

1.  Ensure your FastAPI server is running on `127.0.0.1:8000`.
2.  Locate the `index.html` file in your project directory.
3.  Double-click `index.html` to open it in any modern browser (Chrome/Edge recommended).
4.  Click **Start Call**, grant microphone permissions, and watch the real-time detection engine work!