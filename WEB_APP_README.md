# VoiceGuard Web Application 🛡️

> **Smart India Hackathon 2026** | Problem Statement 26104: AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks

## 🎯 Project Overview

VoiceGuard is a comprehensive web-based real-time deepfake voice defense system designed to intercept, analyze, and flag AI-generated audio during live telephonic and VoIP communications. The application provides an intuitive interface for security operators to monitor calls and receive instant alerts about potential voice cloning attacks.

### 🌟 Key Features

- **Real-Time Monitoring Dashboard** - Live detection with instant risk scoring
- **Advanced Analytics** - Comprehensive charts and statistics
- **Complete Call History** - Searchable, filterable detection logs with CSV export
- **Customizable Settings** - Adjustable thresholds and notification preferences
- **Privacy-First Design** - DPDP Act 2023 compliant, no audio storage
- **Decision Ladder System** - Three-tier risk categorization (LOW/MEDIUM/HIGH)
- **Context-Aware Analysis** - Social engineering keyword detection
- **Professional UI/UX** - Dark theme, responsive design, real-time visualizations

---

## 📁 Project Structure

```
voice-guard/
├── dashboard.html          # Main monitoring dashboard
├── analytics.html          # Analytics & performance metrics
├── history.html           # Complete call history with filters
├── settings.html          # Configuration & preferences
├── about.html             # Project information & documentation
├── index.html             # Entry point (redirects to dashboard)
│
├── js/
│   ├── dashboard.js       # Dashboard logic & WebSocket handling
│   ├── analytics.js       # Charts & statistics
│   ├── history.js         # Log management & export
│   └── settings.js        # Settings persistence
│
├── server.py              # FastAPI WebSocket backend
├── detector.py            # ML inference engine (Wav2Vec2)
├── requirements.txt       # Python dependencies
├── gemchat.pdf           # Problem statement document
└── README.md             # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** installed
- **Modern web browser** (Chrome, Edge, Firefox)
- **Microphone access** enabled
- **~2GB RAM** for ML model

### Backend Setup

1. **Create Virtual Environment**
   ```bash
   python -m venv sih_env
   ```

2. **Activate Environment**
   - Windows: `sih_env\Scripts\activate`
   - Mac/Linux: `source sih_env/bin/activate`

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Server**
   ```bash
   python -m uvicorn server:app --reload
   ```

   The server will start on `http://127.0.0.1:8000`

### Frontend Setup

**Zero Configuration Required!** The frontend is pure HTML/CSS/JavaScript.

1. Ensure the backend server is running
2. Open `index.html` in your browser (or navigate to `dashboard.html` directly)
3. Click **"Start Call"** and grant microphone permissions
4. Start monitoring!

---

## 🎨 Application Pages

### 1. Dashboard (`dashboard.html`)
**Main monitoring interface with:**
- Real-time risk score display with circular progress
- Live audio waveform visualization
- Decision ladder recommendations
- Connection status indicator
- Session statistics (total calls, high risk count, latency, uptime)
- Recent detection log table

### 2. Analytics (`analytics.html`)
**Performance insights with:**
- Risk score distribution chart
- Detection timeline graph
- Risk level breakdown (Low/Medium/High)
- Model performance metrics
- Summary statistics

### 3. Call History (`history.html`)
**Complete detection archive with:**
- Searchable log table
- Risk level and context filters
- Pagination for large datasets
- CSV export functionality
- Detailed call information

### 4. Settings (`settings.html`)
**Customizable configuration:**
- Detection threshold adjustment (High/Medium risk)
- Audio processing options (chunk duration, noise suppression)
- Notification preferences (browser alerts, audio alerts)
- Privacy & data retention settings
- Backend connection configuration
- Connection testing tool

### 5. About (`about.html`)
**Project documentation:**
- Feature overview
- Decision ladder explanation
- Technology stack details
- System architecture diagram
- Privacy & compliance information
- Team information

---

## 🔧 How It Works

### System Architecture

```
┌─────────────────┐
│   Browser UI    │  ← User Interface (HTML/CSS/JS)
│  (MediaRecorder)│
└────────┬────────┘
         │ WebSocket (2.5s audio chunks)
         ▼
┌─────────────────┐
│  FastAPI Server │  ← server.py (WebSocket endpoint)
│   (Python)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Inference   │  ← detector.py (Wav2Vec2 model)
│  (PyTorch)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Risk Fusion     │  ← Acoustic + Context Analysis
│ Decision Ladder │
└────────┬────────┘
         │ JSON Response
         ▼
┌─────────────────┐
│  Dashboard UI   │  ← Real-time updates
└─────────────────┘
```

### Detection Pipeline

1. **Audio Capture** - Browser captures 2.5s audio chunks (16kHz mono)
2. **Streaming** - WebSocket sends audio to backend in real-time
3. **Preprocessing** - Audio normalized and converted via librosa
4. **AI Inference** - Wav2Vec2 model analyzes acoustic patterns
5. **Context Analysis** - Transcript analyzed for social engineering keywords
6. **Risk Fusion** - Scores combined into Decision Ladder recommendation
7. **UI Update** - Dashboard displays risk level and operator instructions

### Decision Ladder

| Risk Level | Score Range | Action | Meaning |
|------------|-------------|--------|---------|
| 🟢 **LOW** | 0-40% | CONTINUE | Clean audio profile, proceed normally |
| 🟡 **MEDIUM** | 40-70% or context flagged | VERIFY | Elevated risk, prompt security questions |
| 🔴 **HIGH** | >70% | HOLD | Synthetic detected, require out-of-band verification |

---

## ⚙️ Configuration

### Detection Thresholds

Default thresholds can be adjusted in Settings:

```javascript
{
  highThreshold: 70,      // High risk trigger (%)
  mediumThreshold: 40,    // Medium risk trigger (%)
  contextBoost: true      // Elevate score when urgent keywords detected
}
```

### Backend URL

Update WebSocket endpoint in Settings if running on different host:

```
Default: ws://127.0.0.1:8000/ws/audio
```

### Data Retention

Choose how long detection logs are stored in browser localStorage:
- Session only (cleared on browser close)
- 7 / 30 / 90 days

---

## 🔒 Privacy & Security

### DPDP Act 2023 Compliance

✅ **Zero Persistent Storage** - Audio processed in RAM only (`io.BytesIO`)  
✅ **No File Saves** - No .wav files written to disk  
✅ **Local Processing** - All inference happens locally  
✅ **Secure Transport** - WebSocket encryption  
✅ **User Control** - Explicit permission required for microphone access

### Data Flow

1. Audio captured → Streamed to server
2. Server processes in memory → Immediately deleted after inference
3. Only metadata (score, timestamp, action) stored locally in browser
4. User can clear all data anytime from Settings

---

## 📊 Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 90+ | ✅ Full | Recommended |
| Edge 90+ | ✅ Full | Recommended |
| Firefox 88+ | ✅ Full | Supported |
| Safari 14+ | ⚠️ Limited | WebM encoding issues |

**Requirements:**
- JavaScript enabled
- WebSocket support
- MediaRecorder API support
- localStorage enabled

---

## 🐛 Troubleshooting

### "Backend Disconnected" Error

**Solution:**
1. Check if Python server is running: `python -m uvicorn server:app --reload`
2. Verify URL in Settings matches server address
3. Check firewall/antivirus not blocking port 8000

### "Microphone Access Denied"

**Solution:**
1. Click lock icon in browser address bar
2. Grant microphone permissions
3. Refresh page and try again

### High CPU Usage

**Solution:**
1. Increase chunk duration in Settings (2.5s → 3.0s)
2. Close unnecessary browser tabs
3. Ensure adequate RAM available for ML model

### No Detections Showing

**Solution:**
1. Verify WebSocket connection is green
2. Check browser console for errors (F12)
3. Test with actual speech (model needs voice input)
4. Ensure "Log All Detections" is enabled in Settings

---

## 🚀 Deployment

### Local Deployment (Development)

Already covered in Getting Started section above.

### Production Deployment

1. **Update CORS settings** in `server.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **Use production ASGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8000
   ```

3. **Serve static files** via Nginx/Apache

4. **Enable HTTPS** for secure WebSocket (wss://)

5. **Update frontend** WebSocket URL in `settings.js`

---

## 📈 Performance Metrics

- **Latency:** <500ms per detection (sub-second requirement met)
- **Throughput:** ~0.4 detections/second (2.5s windows)
- **Model Size:** ~400MB (Wav2Vec2)
- **RAM Usage:** ~1.5-2GB during inference
- **Browser Memory:** ~50-100MB for UI

---

## 🎓 Technology Stack

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Tailwind CSS (via CDN)
- Chart.js (analytics visualizations)
- Font Awesome (icons)
- MediaRecorder API (audio capture)
- WebSocket API (real-time communication)

### Backend
- Python 3.8+
- FastAPI (WebSocket server)
- PyTorch (ML framework)
- Transformers (Hugging Face)
- librosa (audio processing)
- soundfile (audio I/O)

### AI Model
- **Hemgg/Deepfake-audio-detection**
- Based on Wav2Vec2 transformer
- Fine-tuned for synthetic voice detection
- Source: Hugging Face Model Hub

---

## 📝 Future Enhancements

- [ ] Multi-language support
- [ ] Real-time transcript display (Whisper integration)
- [ ] Advanced analytics (ROC curves, confusion matrix)
- [ ] Email/SMS alert integration
- [ ] Multi-user dashboard with authentication
- [ ] API endpoints for integration with call center systems
- [ ] Model fine-tuning interface
- [ ] Export detection reports (PDF)

---

## 👥 Team Domino

**Smart India Hackathon 2026**  
Problem Statement 26104

For questions, suggestions, or collaboration:
- GitHub: [Repository Link]
- Email: team.domino@sih2026.in

---

## 📄 License

This project was developed for Smart India Hackathon 2026.  
© 2026 Team Domino. All Rights Reserved.

---

## 🙏 Acknowledgments

- Smart India Hackathon organizing committee
- Hugging Face for model hosting
- FastAPI community
- Open source contributors

---

**Built with ❤️ for a safer digital voice ecosystem**
