// Initialize Socket.IO
const socket = io();

// DOM Elements
const phoneNumberInput = document.getElementById('phoneNumber');
const callButton = document.getElementById('callButton');
const callStatus = document.getElementById('callStatus');
const englishAgents = document.getElementById('englishAgents');
const spanishAgents = document.getElementById('spanishAgents');
const callHistory = document.getElementById('callHistory');

// ==================== CALL INITIATION ====================

callButton.addEventListener('click', async () => {
    const phoneNumber = phoneNumberInput.value.trim();
    
    if (!phoneNumber) {
        showStatus('Please enter a phone number', 'error');
        return;
    }
    
    // Basic validation
    if (!/^\+?\d{10,15}$/.test(phoneNumber.replace(/\s/g, ''))) {
        showStatus('Please enter a valid phone number', 'error');
        return;
    }
    
    callButton.disabled = true;
    callButton.textContent = 'Calling...';
    showStatus('Initiating call...', 'success');
    
    try {
        const response = await fetch('/call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ to_number: phoneNumber })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus(data.message, 'success');
            phoneNumberInput.value = '';
            
            // Refresh call history after a delay
            setTimeout(loadCallHistory, 2000);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Network error: ${error.message}`, 'error');
    } finally {
        callButton.disabled = false;
        callButton.textContent = 'Start Call';
    }
});

function showStatus(message, type) {
    callStatus.textContent = message;
    callStatus.className = `status-message ${type}`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        callStatus.className = 'status-message';
    }, 5000);
}

// ==================== AGENT DASHBOARD ====================

function renderAgents(agents, container) {
    if (!agents || agents.length === 0) {
        container.innerHTML = '<p class="loading">No agents available</p>';
        return;
    }
    
    container.innerHTML = agents.map(agent => `
        <div class="agent-card ${agent.available ? 'available' : 'busy'}">
            <span class="agent-status ${agent.available ? 'available' : 'busy'}">
                ${agent.available ? 'Available' : 'Busy'}
            </span>
            <div class="agent-info">
                <strong>ID:</strong> ${agent.id}
            </div>
            <div class="agent-info">
                <strong>Phone:</strong> ${agent.phone}
            </div>
            <div class="agent-info">
                <strong>Total Calls:</strong> ${agent.total_calls}
            </div>
            <div class="agent-info">
                <strong>Avg Duration:</strong> ${formatDuration(agent.avg_duration)}
            </div>
            <div class="agent-info">
                <strong>Avg Rating:</strong> ${agent.avg_rating > 0 ? agent.avg_rating + '/4' : 'N/A'}
            </div>
            <div class="agent-info">
                <strong>Priority Score:</strong> ${agent.priority}
            </div>
        </div>
    `).join('');
}

function formatDuration(seconds) {
    if (seconds === 0) return '0s';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

async function loadAgentStats() {
    try {
        const response = await fetch('/api/agent-stats');
        const data = await response.json();
        
        renderAgents(data.english, englishAgents);
        renderAgents(data.spanish, spanishAgents);
    } catch (error) {
        console.error('Error loading agent stats:', error);
    }
}

// ==================== CALL HISTORY ====================

async function loadCallHistory() {
    try {
        const response = await fetch('/api/call-history');
        const calls = await response.json();
        
        if (!calls || calls.length === 0) {
            callHistory.innerHTML = '<p class="loading">No call history yet</p>';
            return;
        }
        
        callHistory.innerHTML = calls.map(call => `
            <div class="call-entry">
                <p><strong>Customer:</strong> ${call.customer}</p>
                <p><strong>Language:</strong> ${call.language || 'N/A'}</p>
                <p><strong>Agent ID:</strong> ${call.agent_id || 'N/A'}</p>
                <p><strong>Duration:</strong> ${call.duration ? formatDuration(call.duration) : 'N/A'}</p>
                <p><strong>Status:</strong> ${call.status}</p>
                <p><strong>Time:</strong> ${call.start_time ? new Date(call.start_time).toLocaleString() : 'N/A'}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading call history:', error);
    }
}

// ==================== SOCKET.IO EVENTS ====================

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('agent_status_update', (data) => {
    console.log('Agent status update received');
    renderAgents(data.english, englishAgents);
    renderAgents(data.spanish, spanishAgents);
});

// ==================== INITIALIZATION ====================

// Load initial data
loadAgentStats();
loadCallHistory();

// Refresh call history every 30 seconds
setInterval(loadCallHistory, 30000);

// Refresh agent stats every 10 seconds (as backup to socket updates)
setInterval(loadAgentStats, 10000);

console.log('Dashboard initialized');
