document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    // Default load
});

function switchTab(tabId) {
    // UI Update
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    document.querySelector(`li[onclick="switchTab('${tabId}')"]`).classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');

    // Data Load
    if (tabId === 'logs') fetchLogs();
    if (tabId === 'prompt') loadPrompt();
    if (tabId === 'badwords') loadBadwords();
    if (tabId === 'fun') loadFun();
    if (tabId === 'settings') loadSettings();
}

async function fetchStats() {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('group-count').innerText = data.groups;
}

async function fetchLogs() {
    const res = await fetch('/api/logs');
    const data = await res.json();
    const container = document.getElementById('log-container');
    container.innerText = data.logs.join('');
    container.scrollTop = container.scrollHeight;
}

// Prompt Handles
async function loadPrompt() {
    const res = await fetch('/api/data/prompt');
    const data = await res.json();
    document.getElementById('prompt-editor').value = data.content;
}

async function savePrompt() {
    const content = document.getElementById('prompt-editor').value;
    await fetch('/api/data/prompt', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content})
    });
    alert('Prompt saved!');
}

// Badwords Handles
async function loadBadwords() {
    const res = await fetch('/api/data/badwords');
    const data = await res.json();
    document.getElementById('badwords-editor').value = data.content;
}

async function saveBadwords() {
    const content = document.getElementById('badwords-editor').value;
    await fetch('/api/data/badwords', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content})
    });
    alert('Badwords saved!');
}

// Fun Handles
async function loadFun() {
    const res = await fetch('/api/data/fun');
    const data = await res.json();
    document.getElementById('roasts-editor').value = JSON.stringify(data.roasts || [], null, 4);
    document.getElementById('motivations-editor').value = JSON.stringify(data.motivations || [], null, 4);
}

async function saveFun() {
    try {
        const roasts = JSON.parse(document.getElementById('roasts-editor').value);
        const motivations = JSON.parse(document.getElementById('motivations-editor').value);
        
        await fetch('/api/data/fun', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({roasts, motivations})
        });
        alert('Fun settings saved!');
    } catch (e) {
        alert('Invalid JSON! Please check your syntax.');
    }
}

// --- Memory Functions ---
async function unlockMemory() {
    const pwd = document.getElementById('memory-password').value;
    const res = await fetch('/api/memory/auth', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password: pwd})
    });
    const data = await res.json();
    
    if (data.success) {
        document.getElementById('memory-lock-screen').style.display = 'none';
        document.getElementById('memory-viewer').style.display = 'flex';
        document.getElementById('memory-controls').style.display = 'flex';
        loadMemoryList();
    } else {
        alert('Incorrect Password');
    }
}

async function loadMemoryList() {
    const res = await fetch('/api/memory/list');
    if (res.status === 403) return showLockScreen();
    
    const data = await res.json();
    const listContainer = document.getElementById('memory-list-container');
    listContainer.innerHTML = '';
    
    if (data.chats) {
        data.chats.forEach(chat => {
            const el = document.createElement('div');
            el.className = 'memory-item';
            el.innerHTML = `<i class="fa-solid fa-comments"></i> <div><strong>${chat.key}</strong><br><small>${chat.updated}</small></div>`;
            el.onclick = () => loadMemoryChat(chat.key);
            listContainer.appendChild(el);
        });
    }
}

let currentMemoryKey = null;
let currentMessages = [];
let selectedMessages = new Set();

async function loadMemoryChat(key) {
    currentMemoryKey = key;
    selectedMessages.clear();
    updateDeleteSelectedState();
    
    const res = await fetch('/api/memory/view/' + encodeURIComponent(key));
    if (res.status === 403) return showLockScreen();
    
    const data = await res.json();
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    document.getElementById('chat-header-title').innerText = key;
    document.getElementById('memory-actions').style.display = 'flex';
    
    // Reset view modes
    document.getElementById('chat-messages').style.display = 'flex';
    document.getElementById('memory-editor-container').style.display = 'none';
    
    // Store data for editor and deletion
    currentMessages = data.messages || [];
    // document.getElementById('memory-json-editor').value = JSON.stringify(currentMessages, null, 4);
    
    if (currentMessages) {
        currentMessages.forEach((msg, index) => {
            const el = document.createElement('div');
            el.className = `chat-bubble ${msg.role}`;
            el.dataset.index = index;
            el.onclick = () => toggleMessageSelection(index, el);
            
            if (msg.role === 'assistant') {
                el.innerHTML = `
                    <div style="display:flex; align-items:flex-start; gap:10px; pointer-events: none;">
                        <img src="/static/logo.jpeg" style="width:30px; min-width:30px; height:30px; border-radius:50%; object-fit:cover; border: 1px solid rgba(255,255,255,0.2);">
                        <div>
                            <div>${msg.content}</div>
                            <small style="opacity:0.5; font-size:0.7rem; display:block; margin-top:2px;">${msg.timestamp || ''}</small>
                        </div>
                    </div>`;
            } else {
                el.innerHTML = `<div>${msg.content}</div>
                                <small style="opacity:0.5; font-size:0.7rem; display:block; margin-top:5px; text-align:right;">${msg.timestamp || ''}</small>`;
            }
            container.appendChild(el);
        });
    }
    container.scrollTop = container.scrollHeight;
}

function toggleMessageSelection(index, el) {
    if (selectedMessages.has(index)) {
        selectedMessages.delete(index);
        el.classList.remove('selected');
    } else {
        selectedMessages.add(index);
        el.classList.add('selected');
    }
    updateDeleteSelectedState();
}

function updateDeleteSelectedState() {
    const btn = document.getElementById('btn-delete-selected');
    if (selectedMessages.size > 0) {
        btn.style.display = 'inline-block';
        btn.innerHTML = `<i class="fa-solid fa-eraser"></i> Delete Selected (${selectedMessages.size})`;
    } else {
        btn.style.display = 'none';
    }
}

async function deleteSelectedMessages() {
    if (selectedMessages.size === 0) return;
    if (!confirm(`Delete ${selectedMessages.size} selected messages?`)) return;

    // Filter out messages where index is in selectedMessages
    const newMessages = currentMessages.filter((_, index) => !selectedMessages.has(index));
    
    // Save updated list
    try {
        const res = await fetch('/api/memory/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: currentMemoryKey, messages: newMessages})
        });
        
        const data = await res.json();
        if (data.success) {
            // Reload chat to reflect changes
            loadMemoryChat(currentMemoryKey);
        } else {
            alert('Error deleting: ' + data.error);
        }
    } catch (e) {
        alert('Internal Error: ' + e);
    }
}


function createNewMemory() {
    const key = prompt("Enter new Group ID or Unique Key (e.g. -100123456789):");
    if (!key) return;
    
    currentMemoryKey = key;
    document.getElementById('chat-header-title').innerText = key + " (New)";
    document.getElementById('chat-messages').style.display = 'none';
    document.getElementById('memory-editor-container').style.display = 'flex';
    document.getElementById('memory-actions').style.display = 'none'; // Hide delete until saved
    
    // Default template
    const timeNow = new Date().toISOString().slice(0, 19).replace('T', ' ');
    currentMessages = [
        {"role": "system", "content": "You are ZUZU Bot.", "timestamp": timeNow},
        {"role": "user", "content": "Hello!", "timestamp": timeNow},
        {"role": "assistant", "content": "Hi there! How can I help?", "timestamp": timeNow}
    ];
    renderEditorList();
}

function toggleEditMemory() {
    const visualView = document.getElementById('chat-messages');
    const editorView = document.getElementById('memory-editor-container');
    
    if (visualView.style.display === 'none') {
        visualView.style.display = 'flex';
        editorView.style.display = 'none';
    } else {
        visualView.style.display = 'none';
        editorView.style.display = 'flex';
        currentPage = 1; // Reset to page 1
        renderEditorList(); // Render visual editor on open
    }
}

// Visual Editor Functions
let currentPage = 1;
const itemsPerPage = 10;

function renderEditorList() {
    const listContainer = document.getElementById('visual-editor-list');
    const paginationContainer = document.getElementById('editor-pagination');
    
    listContainer.innerHTML = '';
    paginationContainer.innerHTML = '';
    
    const totalPages = Math.ceil(currentMessages.length / itemsPerPage) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const itemsToShow = currentMessages.slice(start, end);

    itemsToShow.forEach((msg, idx) => {
        const globalIndex = start + idx;
        const div = document.createElement('div');
        div.className = 'editor-item';
        div.innerHTML = `
            <div class="editor-header">
                <select class="editor-role-select" onchange="updateMessageRole(${globalIndex}, this.value)">
                    <option value="system" ${msg.role === 'system' ? 'selected' : ''}>System</option>
                    <option value="user" ${msg.role === 'user' ? 'selected' : ''}>User</option>
                    <option value="assistant" ${msg.role === 'assistant' ? 'selected' : ''}>Assistant</option>
                </select>
                <div style="font-size: 0.8rem; opacity: 0.5;">#${globalIndex + 1} <span style="margin-left: 5px;">${msg.timestamp || ''}</span></div>
                <button class="btn-delete-item" onclick="deleteEditorMessage(${globalIndex})"><i class="fa-solid fa-trash"></i></button>
            </div>
            <textarea class="editor-content-area" oninput="autoResize(this); updateMessageContent(${globalIndex}, this.value)">${msg.content}</textarea>
        `;
        listContainer.appendChild(div);
        
        // Auto-resize initial render
        const textarea = div.querySelector('textarea');
        setTimeout(() => autoResize(textarea), 0);
    });

    // Pagination Controls
    paginationContainer.innerHTML = `
        <button onclick="changePage(-1)" class="btn-micro" ${currentPage === 1 ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}><i class="fa-solid fa-chevron-left"></i></button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button onclick="changePage(1)" class="btn-micro" ${currentPage === totalPages ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}><i class="fa-solid fa-chevron-right"></i></button>
    `;
}

function changePage(delta) {
    currentPage += delta;
    renderEditorList();
    document.getElementById('visual-editor-list').scrollTop = 0;
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
}

function updateMessageRole(index, newRole) {
    currentMessages[index].role = newRole;
}

function updateMessageContent(index, newContent) {
    currentMessages[index].content = newContent;
}

function deleteEditorMessage(index) {
    currentMessages.splice(index, 1);
    renderEditorList();
}

function addEditorMessage() {
    const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
    currentMessages.push({role: 'user', content: '', timestamp: timestamp});
    // Go to last page
    const totalPages = Math.ceil(currentMessages.length / itemsPerPage) || 1;
    currentPage = totalPages;
    renderEditorList();
    
    // Scroll to bottom
    const container = document.getElementById('visual-editor-list');
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
        // Focus the last textarea
        const inputs = container.querySelectorAll('textarea');
        if (inputs.length > 0) inputs[inputs.length - 1].focus();
    }, 50);
}

async function saveMemory() {
    try {
        // currentMessages is now directly updated by the visual inputs
        if (!currentMemoryKey) {
            alert("Error: No key selected");
            return;
        }
        
        const res = await fetch('/api/memory/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: currentMemoryKey, messages: currentMessages})
        });
        
        const data = await res.json();
        if (data.success) {
            alert('Memory saved successfully!');
            loadMemoryList();
            loadMemoryChat(currentMemoryKey); // Refresh view
        } else {
            alert('Error saving: ' + data.error);
        }
    } catch (e) {
        alert('Internal Error: ' + e);
    }
}

async function deleteMemory() {
    if (!currentMemoryKey) return;
    if (!confirm(`Are you sure you want to delete memory for: ${currentMemoryKey}? This cannot be undone.`)) return;
    
    const res = await fetch('/api/memory/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key: currentMemoryKey})
    });
    
    const data = await res.json();
    if (data.success) {
        alert('Memory deleted.');
        document.getElementById('chat-header-title').innerText = "Select a chat";
        document.getElementById('chat-messages').innerHTML = '';
        document.getElementById('memory-actions').style.display = 'none';
        document.getElementById('memory-editor-container').style.display = 'none';
        document.getElementById('chat-messages').style.display = 'flex';
        currentMemoryKey = null;
        loadMemoryList();
    } else {
        alert('Error deleting: ' + data.error);
    }
}


function showLockScreen() {
    document.getElementById('memory-lock-screen').style.display = 'flex';
    document.getElementById('memory-viewer').style.display = 'none';
    document.getElementById('memory-controls').style.display = 'none';
}

// --- Control Functions ---
async function restartBot() {
    if(!confirm("Are you sure you want to restart the bot process?")) return;
    
    try {
        const res = await fetch('/api/control/restart', {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            alert("Restart signal sent. Bot should reboot in a few seconds.");
            checkStatus();
        } else {
            alert("Error: " + data.message);
        }
    } catch(e) {
        alert("Request failed: " + e);
    }
}

async function checkStatus() {
    try {
        const res = await fetch('/api/control/status');
        const data = await res.json();
        const startBtn = document.getElementById('btn-toggle-bot');
        const statusEl = document.getElementById('bot-status');

        const isRunning = data.status === 'running';

        // Update Status Text
        if(statusEl) {
            statusEl.innerText = data.status.toUpperCase();
            statusEl.style.color = isRunning ? 'var(--success)' : 'var(--danger)';
        }

        // Update Toggle Button
        if (startBtn) {
            if (isRunning) {
                startBtn.style.background = 'rgba(239, 68, 68, 0.15)';
                startBtn.style.color = 'var(--danger)';
                startBtn.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                startBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Bot';
                startBtn.onclick = stopBot;
            } else {
                startBtn.style.background = 'rgba(16, 185, 129, 0.15)';
                startBtn.style.color = 'var(--success)';
                startBtn.style.border = '1px solid rgba(16, 185, 129, 0.3)';
                startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Bot';
                startBtn.onclick = startBot;
            }
        }

    } catch(e) {
        console.error("Status check failed", e);
    }
}

async function toggleBot() {
    // This is just a placeholder, the button's onclick is updated dynamically
    // But in case it hasn't loaded yet:
    await checkStatus();
}

// Poll status every 5 seconds
setInterval(checkStatus, 5000);

async function forceCommitMemory() {
    if (!confirm("Are you sure you want to force save all memory from cache to disk? This might be needed if the bot is running but data isn't showing up yet.")) return;
    try {
        const res = await fetch('/api/memory/commit', {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            alert(data.message);
        } else {
            alert("Error: " + data.error);
        }
    } catch(e) {
        alert("Request failed: " + e);
    }
}

async function refreshMemory() {
    await loadMemoryList();
    if (currentMemoryKey) {
        await loadMemoryChat(currentMemoryKey);
    }
}

async function stopBot() {
    if(!confirm("Are you sure you want to stop the bot process?")) return;
    try {
        const res = await fetch('/api/control/stop', {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            alert("Bot stopped.");
            checkStatus();
        } else {
            alert("Error: " + data.message);
        }
    } catch(e) {
        alert("Request failed: " + e);
    }
}

async function startBot() {
    try {
        const res = await fetch('/api/control/start', {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            alert("Bot start signal sent.");
            checkStatus();
        } else {
            alert("Error: " + data.message);
        }
    } catch(e) {
        alert("Request failed: " + e);
    }
}

// --- Live Graphs ---
let liveGraphInterval = null;
let systemChart = null;

async function loadMemoryRangeGraph() {
    try {
        const res = await fetch('/api/memory/range-stats');
        const data = await res.json();
        const el = document.getElementById('memoryRangeGraph');
        if (!el) return;
        
        const ctx = el.getContext('2d');
        if (window.memoryRangeChart) window.memoryRangeChart.destroy();
        
        window.memoryRangeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Messages',
                    data: data.counts,
                    borderColor: 'rgba(139,92,246,1)',
                    backgroundColor: 'rgba(139,92,246,0.2)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 2,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    } catch(e) { console.error("Error loading memory graph:", e); }
}

async function updateSystemGraph() {
    try {
        const res = await fetch('/api/stats/system');
        const data = await res.json();
        const el = document.getElementById('systemGraph');
        if (!el) return;

        if (!systemChart) {
             const ctx = el.getContext('2d');
             systemChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(30).fill(''),
                    datasets: [
                        { label: 'CPU %', data: Array(30).fill(0), borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', tension: 0.4, pointRadius: 0, fill: true },
                        { label: 'RAM %', data: Array(30).fill(0), borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', tension: 0.4, pointRadius: 0, fill: true }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: { 
                        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                        x: { display: false }
                    }
                }
             });
        }

        // Update Data
        const chartData = systemChart.data;
        chartData.datasets[0].data.push(data.cpu);
        chartData.datasets[0].data.shift();
        
        chartData.datasets[1].data.push(data.memory_percent);
        chartData.datasets[1].data.shift();
        
        systemChart.update();
        
    } catch(e) { console.error("Error updating system graph:", e); }
}

function startLiveGraphs() {
    loadMemoryRangeGraph(); // Load once
    // Update system graph every 2 seconds
    liveGraphInterval = setInterval(() => {
        updateSystemGraph();
    }, 2000);
}

// Hook into DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Chart.js to load if script is async
    const checkChart = setInterval(() => {
        if (typeof Chart !== 'undefined') {
            clearInterval(checkChart);
            startLiveGraphs();
        }
    }, 100);
    setTimeout(() => clearInterval(checkChart), 5000); // Stop checking after 5s
});

// --- Settings ---
async function loadSettings() {
    try {
        const res = await fetch('/api/env');
        const data = await res.json();
        const container = document.getElementById('env-editor-container');
        container.innerHTML = '';
        
        if (data.vars) {
            data.vars.forEach(v => addEnvRow(v.key, v.value));
        }
    } catch(e) {
        alert("Error loading settings: " + e);
    }
}

function addEnvRow(key, value) {
    const container = document.getElementById('env-editor-container');
    const div = document.createElement('div');
    div.style.cssText = "display:flex; gap:1rem; align-items:center;";
    div.innerHTML = `
        <input type="text" placeholder="KEY" value="${key || ''}" class="env-key" style="flex:1; padding:0.8rem; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:white; font-family:monospace;">
        <span style="color:var(--text-secondary);">=</span>
        <input type="text" placeholder="VALUE" value="${value || ''}" class="env-value" style="flex:2; padding:0.8rem; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:white; font-family:monospace;">
        <button onclick="this.parentElement.remove()" style="background:var(--danger); padding:0.8rem; aspect-ratio:1;"><i class="fa-solid fa-trash"></i></button>
    `;
    container.appendChild(div);
}

function addEnvVar() {
    addEnvRow("", "");
}

async function saveSettings() {
    if(!confirm("Saving changes will require a bot restart. Continue?")) return;
    
    const rows = document.querySelectorAll('#env-editor-container > div');
    const vars = [];
    rows.forEach(row => {
        const key = row.querySelector('.env-key').value.trim();
        const value = row.querySelector('.env-value').value.trim();
        if(key) vars.push({key, value});
    });
    
    try {
        const res = await fetch('/api/env', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({vars})
        });
        const data = await res.json();
        if(data.success) {
            alert(data.message);
        } else {
            alert("Error: " + data.error);
        }
    } catch(e) {
        alert("Error saving: " + e);
    }
}

// Global Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    // Check for Ctrl+S or Cmd+S
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault(); // Stop browser from saving HTML file
        
        // Find active tab
        const activeTab = document.querySelector('.tab-content.active');
        if (!activeTab) return;
        
        switch(activeTab.id) {
            case 'tab-prompt':
                savePrompt();
                break;
            case 'tab-badwords':
                saveBadwords();
                break;
            case 'tab-fun':
                saveFun();
                break;
            case 'tab-settings':
                saveSettings();
                break;
            case 'tab-memory':
                // Only save if the editor container is visible/active
                const editor = document.getElementById('memory-editor-container');
                if (editor && editor.style.display !== 'none' && editor.offsetParent !== null) {
                    saveMemory();
                }
                break;
        }
    }
});
