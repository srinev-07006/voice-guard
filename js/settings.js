// VoiceGuard Settings JavaScript

const defaultSettings = {
    highThreshold: 70,
    mediumThreshold: 40,
    contextBoost: true,
    chunkDuration: 2.5,
    noiseSuppression: true,
    echoCancellation: true,
    browserNotifications: false,
    audioAlerts: false,
    logAll: true,
    dataRetention: 30,
    serverUrl: 'ws://127.0.0.1:8000/ws/audio'
};

// Load settings from localStorage
function loadSettings() {
    const saved = localStorage.getItem('voiceguard_settings');
    const settings = saved ? JSON.parse(saved) : defaultSettings;

    // Apply to UI
    document.getElementById('highThreshold').value = settings.highThreshold;
    document.getElementById('highThresholdValue').innerText = settings.highThreshold + '%';

    document.getElementById('mediumThreshold').value = settings.mediumThreshold;
    document.getElementById('mediumThresholdValue').innerText = settings.mediumThreshold + '%';

    document.getElementById('contextBoost').checked = settings.contextBoost;
    document.getElementById('chunkDuration').value = settings.chunkDuration;
    document.getElementById('noiseSuppression').checked = settings.noiseSuppression;
    document.getElementById('echoCancellation').checked = settings.echoCancellation;
    document.getElementById('browserNotifications').checked = settings.browserNotifications;
    document.getElementById('audioAlerts').checked = settings.audioAlerts;
    document.getElementById('logAll').checked = settings.logAll;
    document.getElementById('dataRetention').value = settings.dataRetention;
    document.getElementById('serverUrl').value = settings.serverUrl;
}

function saveSettings() {
    const settings = {
        highThreshold: parseInt(document.getElementById('highThreshold').value),
        mediumThreshold: parseInt(document.getElementById('mediumThreshold').value),
        contextBoost: document.getElementById('contextBoost').checked,
        chunkDuration: parseFloat(document.getElementById('chunkDuration').value),
        noiseSuppression: document.getElementById('noiseSuppression').checked,
        echoCancellation: document.getElementById('echoCancellation').checked,
        browserNotifications: document.getElementById('browserNotifications').checked,
        audioAlerts: document.getElementById('audioAlerts').checked,
        logAll: document.getElementById('logAll').checked,
        dataRetention: parseInt(document.getElementById('dataRetention').value),
        serverUrl: document.getElementById('serverUrl').value
    };

    // Validate thresholds
    if (settings.mediumThreshold >= settings.highThreshold) {
        alert('Medium threshold must be lower than high threshold');
        return;
    }

    localStorage.setItem('voiceguard_settings', JSON.stringify(settings));

    // Request browser notification permission if enabled
    if (settings.browserNotifications && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // Show success message
    showNotification('Settings saved successfully!', 'success');
}

function resetDefaults() {
    if (confirm('Reset all settings to default values?')) {
        localStorage.setItem('voiceguard_settings', JSON.stringify(defaultSettings));
        loadSettings();
        showNotification('Settings reset to defaults', 'success');
    }
}

function clearAllData() {
    if (confirm('This will permanently delete all settings, logs, and cached data. Continue?')) {
        localStorage.clear();
        showNotification('All local data cleared', 'success');
        setTimeout(() => {
            location.reload();
        }, 1500);
    }
}

async function testConnection() {
    const serverUrl = document.getElementById('serverUrl').value;

    showNotification('Testing connection...', 'info');

    try {
        const ws = new WebSocket(serverUrl);

        ws.onopen = () => {
            showNotification('✓ Connection successful!', 'success');
            ws.close();
        };

        ws.onerror = () => {
            showNotification('✗ Connection failed. Check server URL and ensure backend is running.', 'error');
        };

        // Timeout after 5 seconds
        setTimeout(() => {
            if (ws.readyState !== WebSocket.OPEN && ws.readyState !== WebSocket.CLOSED) {
                ws.close();
                showNotification('✗ Connection timeout', 'error');
            }
        }, 5000);

    } catch (error) {
        showNotification('✗ Invalid WebSocket URL', 'error');
    }
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-4 rounded-lg shadow-lg z-50 transition-all ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' : 'bg-blue-600'
    }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="fa-solid ${
                type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'
            }"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Update threshold display values in real-time
document.getElementById('highThreshold').addEventListener('input', (e) => {
    document.getElementById('highThresholdValue').innerText = e.target.value + '%';
});

document.getElementById('mediumThreshold').addEventListener('input', (e) => {
    document.getElementById('mediumThresholdValue').innerText = e.target.value + '%';
});

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});
