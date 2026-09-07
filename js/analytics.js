// VoiceGuard Analytics JavaScript
let detectionLog = [];
let riskDistributionChart, timelineChart, performanceChart;

// Load data from localStorage
function loadData() {
    const savedLog = localStorage.getItem('voiceguard_log');
    if (savedLog) {
        detectionLog = JSON.parse(savedLog);
    }
    updateAnalytics();
}

function updateAnalytics() {
    if (detectionLog.length === 0) {
        // Show empty state
        document.getElementById('totalProcessed').innerText = '0';
        document.getElementById('detectionRate').innerText = '0%';
        document.getElementById('avgConfidence').innerText = '0%';
        document.getElementById('falsePositiveRate').innerText = '--';
        document.getElementById('lowRiskCount').innerText = '0';
        document.getElementById('mediumRiskCount').innerText = '0';
        document.getElementById('highRiskCountAnalytics').innerText = '0';
        return;
    }

    // Calculate summary statistics
    const total = detectionLog.length;
    const highRisk = detectionLog.filter(log => log.risk_level === 'HIGH').length;
    const mediumRisk = detectionLog.filter(log => log.risk_level === 'MEDIUM').length;
    const lowRisk = detectionLog.filter(log => log.risk_level === 'LOW').length;

    const detectionRate = ((highRisk / total) * 100).toFixed(1);
    const avgScore = detectionLog.reduce((sum, log) => sum + log.risk_score, 0) / total;

    // Update summary cards
    document.getElementById('totalProcessed').innerText = total;
    document.getElementById('detectionRate').innerText = detectionRate + '%';
    document.getElementById('avgConfidence').innerText = Math.round(avgScore) + '%';
    document.getElementById('falsePositiveRate').innerText = '--';

    // Update risk level counts
    document.getElementById('lowRiskCount').innerText = lowRisk;
    document.getElementById('mediumRiskCount').innerText = mediumRisk;
    document.getElementById('highRiskCountAnalytics').innerText = highRisk;

    // Update charts
    updateRiskDistributionChart();
    updateTimelineChart();
    updatePerformanceChart();
}

function updateRiskDistributionChart() {
    const ctx = document.getElementById('riskDistributionChart').getContext('2d');

    // Group by risk score ranges
    const ranges = {
        '0-20': 0,
        '21-40': 0,
        '41-60': 0,
        '61-80': 0,
        '81-100': 0
    };

    detectionLog.forEach(log => {
        const score = log.risk_score;
        if (score <= 20) ranges['0-20']++;
        else if (score <= 40) ranges['21-40']++;
        else if (score <= 60) ranges['41-60']++;
        else if (score <= 80) ranges['61-80']++;
        else ranges['81-100']++;
    });

    if (riskDistributionChart) {
        riskDistributionChart.destroy();
    }

    riskDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(ranges),
            datasets: [{
                label: 'Number of Detections',
                data: Object.values(ranges),
                backgroundColor: [
                    '#10b981',
                    '#84cc16',
                    '#eab308',
                    '#f97316',
                    '#ef4444'
                ],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#9ca3af',
                        stepSize: 1
                    },
                    grid: {
                        color: '#374151'
                    }
                },
                x: {
                    ticks: {
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateTimelineChart() {
    const ctx = document.getElementById('timelineChart').getContext('2d');

    // Take last 20 entries for timeline
    const recentData = detectionLog.slice(-20);
    const labels = recentData.map((log, idx) => `#${idx + 1}`);
    const scores = recentData.map(log => log.risk_score);

    if (timelineChart) {
        timelineChart.destroy();
    }

    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score %',
                data: scores,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: '#374151'
                    }
                },
                x: {
                    ticks: {
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updatePerformanceChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');

    const low = detectionLog.filter(log => log.risk_level === 'LOW').length;
    const medium = detectionLog.filter(log => log.risk_level === 'MEDIUM').length;
    const high = detectionLog.filter(log => log.risk_level === 'HIGH').length;

    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk', 'Medium Risk', 'High Risk'],
            datasets: [{
                data: [low, medium, high],
                backgroundColor: [
                    '#10b981',
                    '#eab308',
                    '#ef4444'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#9ca3af',
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// Refresh data every 5 seconds
setInterval(() => {
    loadData();
}, 5000);

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadData();
});
