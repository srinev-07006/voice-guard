// Supabase Route Protection and Auth Integration
// TODO: Replace with your actual Supabase URL and Anon Key
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';

const supabase = window.supabase ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;

// Route Protection: verify active session
async function checkAuthSession() {
    if (!supabase) {
        console.error('Supabase client failed to load.');
        return;
    }
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error || !session) {
        // No active session, redirect to index.html immediately
        window.location.href = 'index.html';
        return;
    }

    // Display the signed-in user's email in the sidebar
    const userEmailEl = document.getElementById('userEmail');
    if (userEmailEl && session.user) {
        userEmailEl.innerText = session.user.email;
    }
}

// Perform session verification immediately
checkAuthSession();

// Sign out handler
async function handleLogout() {
    if (!supabase) return;
    await supabase.auth.signOut();
    window.location.href = 'index.html';
}

// Listen for auth state changes (e.g., if token expires or user logs out)
if (supabase) {
    supabase.auth.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_OUT' || !session) {
            window.location.href = 'index.html';
        }
    });
}

// VoiceGuard Dashboard JavaScript
let mediaRecorder;
let socket;
let isRecording = false;
let sessionStartTime = null;
let detectionLog = [];
let latencyMeasurements = [];
let statsInterval;

// DOM Elements
const recordBtn = document.getElementById('recordBtn');
const scoreDisplay = document.getElementById('scoreDisplay');
const statusBadge = document.getElementById('statusBadge');
const progressCircle = document.getElementById('progressCircle');
const actionDisplay = document.getElementById('actionDisplay');
const recommendationDisplay = document.getElementById('recommendationDisplay');
const reasonDisplay = document.getElementById('reasonDisplay');
const contextDisplay = document.getElementById('contextDisplay');
const decisionPanel = document.getElementById('decisionPanel');
const sidebarStatus = document.getElementById('sidebarStatus');
const waveform = document.getElementById('waveform');
const totalCalls = document.getElementById('totalCalls');
const highRiskCount = document.getElementById('highRiskCount');
const avgLatency = document.getElementById('avgLatency');
const uptime = document.getElementById('uptime');
const logTableBody = document.getElementById('logTableBody');
const currentTime = document.getElementById('currentTime');

// Update current time
function updateCurrentTime() {
    const now = new Date();
    currentTime.innerText = now.toLocaleTimeString();
}
setInterval(updateCurrentTime, 1000);
updateCurrentTime();

// Connect to FastAPI WebSocket
function connectWebSocket() {
    socket = new WebSocket('ws://127.0.0.1:8000/ws/audio');

    socket.onopen = () => {
        console.log('✅ Connected to VoiceGuard Engine');
        updateConnectionStatus(true);
    };

    socket.onclose = () => {
        console.log('❌ Connection closed. Retrying...');
        updateConnectionStatus(false);
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };

    // Handle incoming AI Risk Scores
    socket.onmessage = (event) => {
        const startTime = Date.now();
        const data = JSON.parse(event.data);

        if (data.status === 'success') {
            const latency = Date.now() - startTime;
            latencyMeasurements.push(latency);

            processDetectionResult(data);
            updateStatistics();
            addToDetectionLog(data);
        }
    };
}

function updateConnectionStatus(connected) {
    if (connected) {
        sidebarStatus.innerHTML = `
            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span class="text-green-400">Connected</span>
        `;
    } else {
        sidebarStatus.innerHTML = `
            <div class="w-2 h-2 bg-red-500 rounded-full"></div>
            <span class="text-gray-400">Disconnected</span>
        `;
    }
}

function processDetectionResult(data) {
    const percentage = Math.round(data.risk_score * 100);

    // Update score display
    scoreDisplay.innerText = percentage + '%';

    // Update circular progress
    const circumference = 2 * Math.PI * 88;
    const offset = circumference - (percentage / 100) * circumference;
    progressCircle.style.strokeDashoffset = offset;

    // Update decision ladder
    actionDisplay.innerText = data.action;
    recommendationDisplay.innerText = data.recommendation;
    reasonDisplay.innerText = data.reason_code;

    // Update context display
    if (data.context_flagged) {
        contextDisplay.innerHTML = `
            <span class="text-yellow-400 flex items-center">
                <i class="fa-solid fa-exclamation-triangle mr-2"></i>
                Urgent keywords detected
            </span>
        `;
    } else {
        contextDisplay.innerHTML = `
            <span class="text-gray-400">No urgent keywords detected</span>
        `;
    }

    // Apply color scheme based on risk level
    updateRiskVisualization(data.risk_level, percentage);
}

function updateRiskVisualization(riskLevel, percentage) {
    // Reset classes
    decisionPanel.className = 'p-4 bg-gray-900 rounded-lg border-l-4';
    progressCircle.classList.remove('stroke-green-500', 'stroke-yellow-500', 'stroke-red-500');

    if (riskLevel === 'HIGH') {
        decisionPanel.classList.add('border-red-500', 'bg-red-900', 'bg-opacity-10');
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-red-600 text-white animate-pulse';
        statusBadge.innerText = '🚨 SYNTHETIC AUDIO DETECTED';
        actionDisplay.className = 'text-2xl font-bold text-red-500';
        progressCircle.setAttribute('stroke', '#ef4444');

        // Update waveform to red
        document.querySelectorAll('.waveform-bar').forEach(bar => {
            bar.style.background = 'linear-gradient(180deg, #ef4444 0%, #dc2626 100%)';
        });

    } else if (riskLevel === 'MEDIUM') {
        decisionPanel.classList.add('border-yellow-500', 'bg-yellow-900', 'bg-opacity-10');
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-yellow-600 text-white';
        statusBadge.innerText = '⚠️ ELEVATED RISK';
        actionDisplay.className = 'text-2xl font-bold text-yellow-500';
        progressCircle.setAttribute('stroke', '#eab308');

        // Update waveform to yellow
        document.querySelectorAll('.waveform-bar').forEach(bar => {
            bar.style.background = 'linear-gradient(180deg, #eab308 0%, #ca8a04 100%)';
        });

    } else {
        decisionPanel.classList.add('border-green-500', 'bg-green-900', 'bg-opacity-10');
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-green-600 text-white';
        statusBadge.innerText = '✓ GENUINE CALLER';
        actionDisplay.className = 'text-2xl font-bold text-green-500';
        progressCircle.setAttribute('stroke', '#10b981');

        // Update waveform to green
        document.querySelectorAll('.waveform-bar').forEach(bar => {
            bar.style.background = 'linear-gradient(180deg, #10b981 0%, #059669 100%)';
        });
    }
}

function updateStatistics() {
    // Total calls
    totalCalls.innerText = detectionLog.length;

    // High risk count
    const highRisk = detectionLog.filter(log => log.risk_level === 'HIGH').length;
    highRiskCount.innerText = highRisk;

    // Average latency
    if (latencyMeasurements.length > 0) {
        const avg = latencyMeasurements.reduce((a, b) => a + b, 0) / latencyMeasurements.length;
        avgLatency.innerText = Math.round(avg) + 'ms';
    }

    // Session uptime
    if (sessionStartTime) {
        const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        uptime.innerText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
}

function addToDetectionLog(data) {
    const timestamp = new Date().toLocaleTimeString();
    const percentage = Math.round(data.risk_score * 100);

    const logEntry = {
        timestamp,
        risk_score: percentage,
        risk_level: data.risk_level,
        action: data.action,
        context_flagged: data.context_flagged,
        ...data
    };

    detectionLog.push(logEntry);

    // Keep only last 50 entries
    if (detectionLog.length > 50) {
        detectionLog.shift();
    }

    // Save to localStorage
    localStorage.setItem('voiceguard_log', JSON.stringify(detectionLog));

    // Update table
    updateLogTable();
}

function updateLogTable() {
    if (detectionLog.length === 0) {
        logTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-8 text-gray-500">No detections yet. Start a call to begin monitoring.</td>
            </tr>
        `;
        return;
    }

    // Show last 10 entries in reverse order (newest first)
    const recentLogs = detectionLog.slice(-10).reverse();

    logTableBody.innerHTML = recentLogs.map(log => {
        const riskColor = log.risk_level === 'HIGH' ? 'text-red-400' :
                         log.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400';

        const contextIcon = log.context_flagged ?
            '<i class="fa-solid fa-exclamation-triangle text-yellow-400"></i>' :
            '<i class="fa-solid fa-check text-gray-500"></i>';

        return `
            <tr class="border-b border-gray-700 hover:bg-gray-700">
                <td class="py-3">${log.timestamp}</td>
                <td class="py-3 font-mono ${riskColor}">${log.risk_score}%</td>
                <td class="py-3">
                    <span class="px-2 py-1 rounded text-xs font-semibold ${
                        log.risk_level === 'HIGH' ? 'bg-red-600' :
                        log.risk_level === 'MEDIUM' ? 'bg-yellow-600' : 'bg-green-600'
                    }">${log.risk_level}</span>
                </td>
                <td class="py-3">${log.action}</td>
                <td class="py-3 text-center">${contextIcon}</td>
            </tr>
        `;
    }).join('');
}

function clearLog() {
    if (confirm('Clear all detection logs?')) {
        detectionLog = [];
        localStorage.removeItem('voiceguard_log');
        updateLogTable();
        updateStatistics();
    }
}

// Toggle Audio Capture
recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        try {
            // Request Microphone Access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            isRecording = true;
            sessionStartTime = Date.now();

            // Enable waveform animation
            waveform.style.opacity = '1';

            // Create a loop to record distinct 2.5s chunks
            const recordLoop = () => {
                if (!isRecording) return;

                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                        socket.send(event.data);
                    }
                };

                mediaRecorder.start();

                // Stop and restart every 2.5 seconds
                setTimeout(() => {
                    if (isRecording) {
                        mediaRecorder.stop();
                        recordLoop();
                    }
                }, 2500);
            };

            recordLoop();

            // Update Button UI
            recordBtn.innerHTML = '<i class="fa-solid fa-stop mr-2"></i><span>Stop Call</span>';
            recordBtn.classList.remove('from-blue-600', 'to-blue-500', 'hover:from-blue-500', 'hover:to-blue-400');
            recordBtn.classList.add('from-red-600', 'to-red-500', 'hover:from-red-500', 'hover:to-red-400', 'animate-pulse');

            // Start uptime counter
            statsInterval = setInterval(updateStatistics, 1000);

        } catch (err) {
            alert('Microphone access is required. Please grant permission and try again.');
            console.error('Microphone access error:', err);
        }
    } else {
        // Stop Recording
        isRecording = false;
        if (mediaRecorder) mediaRecorder.stop();
        if (statsInterval) clearInterval(statsInterval);

        // Reset UI
        recordBtn.innerHTML = '<i class="fa-solid fa-microphone mr-2"></i><span>Start Call</span>';
        recordBtn.classList.remove('from-red-600', 'to-red-500', 'hover:from-red-500', 'hover:to-red-400', 'animate-pulse');
        recordBtn.classList.add('from-blue-600', 'to-blue-500', 'hover:from-blue-500', 'hover:to-blue-400');

        // Dim waveform
        waveform.style.opacity = '0.3';
    }
});

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();

    // Wire up the sign out button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Load previous log from localStorage
    const savedLog = localStorage.getItem('voiceguard_log');
    if (savedLog) {
        detectionLog = JSON.parse(savedLog);
        updateLogTable();
        updateStatistics();
    }

    // Dim waveform initially
    waveform.style.opacity = '0.3';
});
