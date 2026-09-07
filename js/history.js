// VoiceGuard Call History JavaScript
let detectionLog = [];
let filteredLog = [];
let currentPage = 1;
const recordsPerPage = 20;

// Load data from localStorage
function loadHistory() {
    const savedLog = localStorage.getItem('voiceguard_log');
    if (savedLog) {
        detectionLog = JSON.parse(savedLog);
        filteredLog = [...detectionLog];
    }
    updateTable();
}

function updateTable() {
    const tbody = document.getElementById('historyTableBody');
    const totalRecords = document.getElementById('totalRecords');
    const showingRange = document.getElementById('showingRange');

    totalRecords.innerText = filteredLog.length;

    if (filteredLog.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-12 text-gray-500">
                    <i class="fa-solid fa-inbox text-4xl mb-3 block"></i>
                    No records found matching your criteria.
                </td>
            </tr>
        `;
        showingRange.innerText = '0';
        return;
    }

    // Pagination
    const startIdx = (currentPage - 1) * recordsPerPage;
    const endIdx = Math.min(startIdx + recordsPerPage, filteredLog.length);
    const pageData = filteredLog.slice(startIdx, endIdx).reverse(); // Newest first

    showingRange.innerText = `${startIdx + 1}-${endIdx}`;

    tbody.innerHTML = pageData.map((log, idx) => {
        const id = filteredLog.length - startIdx - idx;
        const riskColor = log.risk_level === 'HIGH' ? 'text-red-400' :
                         log.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400';

        const contextIcon = log.context_flagged ?
            '<span class="px-2 py-1 bg-yellow-600 rounded text-xs"><i class="fa-solid fa-exclamation-triangle mr-1"></i>Flagged</span>' :
            '<span class="px-2 py-1 bg-gray-700 rounded text-xs text-gray-400">Clear</span>';

        return `
            <tr class="border-b border-gray-700 hover:bg-gray-700 transition cursor-pointer" onclick="showDetails(${id - 1})">
                <td class="py-4 px-6 font-mono text-gray-500">#${String(id).padStart(4, '0')}</td>
                <td class="py-4 px-6">${log.timestamp}</td>
                <td class="py-4 px-6 font-mono font-bold ${riskColor}">${log.risk_score}%</td>
                <td class="py-4 px-6">
                    <span class="px-2 py-1 rounded text-xs font-semibold ${
                        log.risk_level === 'HIGH' ? 'bg-red-600' :
                        log.risk_level === 'MEDIUM' ? 'bg-yellow-600' : 'bg-green-600'
                    }">${log.risk_level}</span>
                </td>
                <td class="py-4 px-6 font-semibold">${log.action}</td>
                <td class="py-4 px-6 text-gray-400 max-w-xs truncate">${log.recommendation}</td>
                <td class="py-4 px-6">${contextIcon}</td>
                <td class="py-4 px-6 font-mono text-xs text-blue-400">${log.reason_code}</td>
            </tr>
        `;
    }).join('');
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const riskFilter = document.getElementById('filterRisk').value;
    const contextFilter = document.getElementById('filterContext').value;

    filteredLog = detectionLog.filter(log => {
        // Search filter
        const matchesSearch = !searchTerm ||
            log.timestamp.toLowerCase().includes(searchTerm) ||
            log.action.toLowerCase().includes(searchTerm) ||
            log.reason_code.toLowerCase().includes(searchTerm) ||
            log.recommendation.toLowerCase().includes(searchTerm);

        // Risk filter
        const matchesRisk = riskFilter === 'all' || log.risk_level === riskFilter;

        // Context filter
        const matchesContext = contextFilter === 'all' ||
            log.context_flagged.toString() === contextFilter;

        return matchesSearch && matchesRisk && matchesContext;
    });

    currentPage = 1;
    updateTable();
}

function nextPage() {
    const maxPage = Math.ceil(filteredLog.length / recordsPerPage);
    if (currentPage < maxPage) {
        currentPage++;
        updateTable();
    }
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        updateTable();
    }
}

function exportHistory() {
    if (detectionLog.length === 0) {
        alert('No data to export');
        return;
    }

    // Create CSV content
    const headers = ['ID', 'Timestamp', 'Risk Score', 'Risk Level', 'Action', 'Recommendation', 'Context Flagged', 'Reason Code'];
    const rows = detectionLog.map((log, idx) => [
        idx + 1,
        log.timestamp,
        log.risk_score + '%',
        log.risk_level,
        log.action,
        `"${log.recommendation}"`,
        log.context_flagged ? 'Yes' : 'No',
        log.reason_code
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voiceguard_history_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function clearHistory() {
    if (confirm('This will permanently delete all call history. Continue?')) {
        localStorage.removeItem('voiceguard_log');
        detectionLog = [];
        filteredLog = [];
        updateTable();
    }
}

function showDetails(index) {
    const log = detectionLog[index];
    alert(`Call Details #${index + 1}\n\n` +
          `Timestamp: ${log.timestamp}\n` +
          `Risk Score: ${log.risk_score}%\n` +
          `Risk Level: ${log.risk_level}\n` +
          `Action: ${log.action}\n` +
          `Recommendation: ${log.recommendation}\n` +
          `Context Flagged: ${log.context_flagged ? 'Yes' : 'No'}\n` +
          `Reason Code: ${log.reason_code}`);
}

// Event listeners
document.getElementById('searchInput').addEventListener('input', applyFilters);
document.getElementById('filterRisk').addEventListener('change', applyFilters);
document.getElementById('filterContext').addEventListener('change', applyFilters);

// Refresh data every 5 seconds
setInterval(() => {
    loadHistory();
}, 5000);

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});
