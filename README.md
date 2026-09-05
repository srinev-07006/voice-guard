# VoiceGuard 🛡️
> **Smart India Hackathon 2026** | Problem Statement 26104: AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks.

## Project Overview
VoiceGuard is a real-time deepfake voice defense system designed to intercept, analyze, and flag AI-generated audio during live telephonic and VoIP communications. Built to operate under strict sub-second latency constraints, this MVP utilizes a decoupled processing architecture:

*   **The Fast Path (Acoustic Detection):** Captures live audio in 2-4 second sliding windows[cite: 2], passing raw data to a Wav2Vec2 transformer to instantly identify synthetic speech artifacts.
*   **The Slow Path (Context & Intent):** Asynchronously transcribes the audio stream to detect urgent social engineering patterns, combining context with the acoustic score to trigger actionable, explainable alerts.
*   **Privacy by Design:** Audio is processed dynamically in volatile memory, ensuring adherence to data protection frameworks like the DPDP Act 2023[cite: 2].

---

## Core Tech Stack
*   **Frontend:** React, Tailwind CSS, WebRTC (Live Call Simulation).
*   **Backend Transport:** Python, FastAPI, WebSockets (Continuous, low-latency streaming).
*   **Machine Learning:** PyTorch, Hugging Face `pipeline` (`Hemgg/Deepfake-audio-detection`), `faster-whisper`.
*   **Signal Processing:** `librosa`, `soundfile` (16kHz mono normalization).

---

## Quickstart Guide
Follow these steps to initialize the machine learning environment and launch the backend detection server.

1.  **Clone the Repository:** Pull the source code to your local machine.
2.  **Initialize the Environment:** Create a virtual environment using `python -m venv sih_env`.
3.  **Activate the Environment:** Run `sih_env\Scripts\activate` (Windows) or `source sih_env/bin/activate` (Mac/Linux).
4.  **Install Dependencies:** Execute `pip install -r requirements.txt`.
5.  **Cache the Model:** Run `python detector.py` to download and load the initial Hugging Face weights into memory.
6.  **Start the Server:** Launch the FastAPI backend using `uvicorn server:app --reload`.
