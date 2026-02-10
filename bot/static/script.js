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
