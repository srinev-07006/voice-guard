# VoiceGuard - Quick Start Guide 🚀

## 🎯 For Judges & Evaluators

This is a **complete web-based solution** for the Smart India Hackathon 2026 Problem Statement 26104: **AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks**.

---

## ⚡ 3-Minute Setup

### Step 1: Start the Backend (2 minutes)

```bash
# Navigate to project directory
cd voice-guard

# Create virtual environment (first time only)
python -m venv sih_env

# Activate environment
# Windows:
sih_env\Scripts\activate
# Mac/Linux:
source sih_env/bin/activate

# Install dependencies (first time only - takes ~1-2 minutes)
pip install -r requirements.txt

# Start the server
python -m uvicorn server:app --reload
```

**✅ You should see:** `Uvicorn running on http://127.0.0.1:8000`

---

### Step 2: Open the Web App (30 seconds)

1. Open your web browser (Chrome or Edge recommended)
2. Navigate to the project folder
3. Double-click **`dashboard.html`** OR open **`index.html`** (redirects automatically)

**Alternative:** Right-click → Open with → Chrome/Edge

---

### Step 3: Start Monitoring (30 seconds)

1. Click the **"Start Call"** button
2. Grant microphone permissions when prompted
3. Speak into your microphone
4. Watch real-time detection in action! 🎉

---

## 📱 Application Features

### 5 Complete Pages:

1. **Dashboard** - Real-time monitoring with live risk scores
2. **Analytics** - Charts, graphs, and performance metrics
3. **History** - Complete searchable log with CSV export
4. **Settings** - Customize thresholds and preferences
5. **About** - Full documentation and tech details

---

## 🎨 What You'll See

### When Audio is Genuine (Low Risk):
- 🟢 Green circular progress indicator
- "GENUINE CALLER" badge
- "CONTINUE" action recommendation
- Risk score: 0-40%

### When Audio is Suspicious (Medium Risk):
- 🟡 Yellow indicators
- "ELEVATED RISK" badge
- "VERIFY" action (prompt security questions)
- Risk score: 40-70%

### When Deepfake Detected (High Risk):
- 🔴 Red indicators with animation
- "SYNTHETIC AUDIO DETECTED" badge
- "HOLD" action (require secondary verification)
- Risk score: >70%

---

## 🔍 Testing the System

### Test with Normal Speech:
1. Click "Start Call"
2. Speak naturally: *"Hello, this is a test call"*
3. Observe the risk score (typically LOW)

### Test with Synthesized Audio:
1. Play any AI-generated voice from another device near your mic
2. Watch the system flag it as HIGH risk
3. Check the detection log for details

---

## 📊 Key Metrics to Observe

- **Latency:** Sub-second detection (<500ms)
- **Accuracy:** Wav2Vec2 model with high precision
- **Privacy:** Zero audio storage (DPDP Act 2023 compliant)
- **Responsiveness:** Real-time UI updates via WebSocket

---

## 🛠️ Troubleshooting

### "Backend Disconnected" message?
→ Ensure Python server is running (`python -m uvicorn server:app --reload`)

### Microphone not working?
→ Check browser permissions (click lock icon in address bar)

### Page not loading?
→ Try opening `dashboard.html` directly instead of `index.html`

### High CPU usage?
→ This is normal - ML model is processing audio in real-time

---

## 📁 Project Structure

```
voice-guard/
├── dashboard.html      ← Main interface (START HERE)
├── analytics.html      ← Statistics & charts
├── history.html        ← Detection logs
├── settings.html       ← Configuration
├── about.html          ← Documentation
├── js/                 ← JavaScript logic
├── server.py           ← FastAPI backend
├── detector.py         ← ML inference
└── requirements.txt    ← Python packages
```

---

## 🎯 Demo Flow (2 minutes)

1. **Show Dashboard** - Live monitoring interface
2. **Start Call** - Begin real-time detection
3. **Speak/Test** - Demonstrate detection in action
4. **View Analytics** - Show charts and statistics
5. **Check History** - Browse detection logs
6. **Export Data** - Download CSV report
7. **Show Settings** - Customizable thresholds
8. **About Page** - Technical documentation

---

## 💡 Technical Highlights

- ✅ **Sub-second latency** (Real-time requirement met)
- ✅ **Privacy-first** (No audio files saved to disk)
- ✅ **Production-ready UI** (Professional dark theme)
- ✅ **Scalable architecture** (WebSocket + FastAPI)
- ✅ **AI-powered** (Wav2Vec2 transformer model)
- ✅ **Decision support** (3-tier operator guidance)
- ✅ **Complete solution** (5 integrated pages)

---

## 📞 Support

For technical issues during evaluation:
1. Check that Python server is running
2. Verify browser console for errors (F12)
3. Ensure microphone permissions granted
4. Try restarting both server and browser

---

## 🏆 Team Domino

**Smart India Hackathon 2026**  
Problem Statement 26104

Built with Python, FastAPI, PyTorch, HTML5, JavaScript, and ❤️

---

**Ready to prevent voice cloning attacks!** 🛡️
