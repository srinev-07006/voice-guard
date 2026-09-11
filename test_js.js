const fs = require('fs');

// simulate a call
const detectionLog = [{
    timestamp: "12:00:00",
    risk_score: 55,
    risk_level: "MEDIUM",
    action: "VERIFY",
    context_flagged: false,
    reason_code: "foo",
    recommendation: "bar"
}];

console.log("Analytics.js sanity check:");
const total = detectionLog.length;
const highRisk = detectionLog.filter(log => log.risk_level === 'HIGH').length;
const mediumRisk = detectionLog.filter(log => log.risk_level === 'MEDIUM').length;
const lowRisk = detectionLog.filter(log => log.risk_level === 'LOW').length;

const detectionRate = ((highRisk / total) * 100).toFixed(1);
const avgScore = detectionLog.reduce((sum, log) => sum + (Number(log.risk_score) || 0), 0) / total;

console.log(total, highRisk, mediumRisk, lowRisk, detectionRate, avgScore);
