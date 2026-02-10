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

async function loadMemoryChat(key) {
    const res = await fetch('/api/memory/view/' + encodeURIComponent(key));
    if (res.status === 403) return showLockScreen();
    
    const data = await res.json();
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    document.getElementById('chat-header-title').innerText = key;
    
    if (data.messages) {
        data.messages.forEach(msg => {
            const el = document.createElement('div');
            el.className = `chat-bubble ${msg.role}`;
            
            if (msg.role === 'assistant') {
                el.innerHTML = `
                    <div style="display:flex; align-items:flex-start; gap:10px;">
                        <img src="/static/logo.jpeg" style="width:30px; min-width:30px; height:30px; border-radius:50%; object-fit:cover; border: 1px solid rgba(255,255,255,0.2);">
                        <div>${msg.content}</div>
                    </div>`;
            } else {
                el.innerText = msg.content;
            }
            container.appendChild(el);
        });
    }
    container.scrollTop = container.scrollHeight;
}

function showLockScreen() {
    document.getElementById('memory-lock-screen').style.display = 'flex';
    document.getElementById('memory-viewer').style.display = 'none';
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
        const statusEl = document.getElementById('bot-status');
        if(statusEl) {
            statusEl.innerText = data.status.toUpperCase();
            statusEl.style.color = data.status === 'running' ? 'var(--success)' : 'var(--danger)';
        }
    } catch(e) {
        console.error("Status check failed", e);
    }
}

// Poll status every 5 seconds
setInterval(checkStatus, 5000);
