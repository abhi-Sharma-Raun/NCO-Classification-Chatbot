const API_BASE = "http://localhost:8000";

// Internal State
let currentState = {
    sessionId: null,
    threadId: null,
    mode: "initializing", // 'initializing', 'start', 'resume', 'closed'
    isProcessing: false,
    messages: [] // We now store messages to restore them on refresh
};

// DOM Elements
const messagesDiv = document.getElementById('messages');
const inputField = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const loadingIndicator = document.getElementById('loading-indicator');

// --- Initialization ---

window.addEventListener('DOMContentLoaded', async () => {
    loadStateFromStorage();
    
    if (currentState.sessionId) {
        // Restore existing session
        restoreUI();
    } else {
        // Create new session
        await initSession();
    }
});

function saveStateToStorage() {
    sessionStorage.setItem('nco_chat_state', JSON.stringify({
        sessionId: currentState.sessionId,
        threadId: currentState.threadId,
        mode: currentState.mode,
        messages: currentState.messages
    }));
}

function loadStateFromStorage() {
    const saved = sessionStorage.getItem('nco_chat_state');
    if (saved) {
        const parsed = JSON.parse(saved);
        currentState.sessionId = parsed.sessionId;
        currentState.threadId = parsed.threadId;
        currentState.mode = parsed.mode;
        currentState.messages = parsed.messages || [];
    }
}

function restoreUI() {
    clearMessages();
    
    // Re-render history
    if (currentState.messages.length > 0) {
        currentState.messages.forEach(msg => addMessageToDOM(msg.role, msg.content));
    } else {
         addMessageToDOM('system', 'Session restored.');
    }

    // Set UI state based on mode
    if (currentState.mode === 'closed') {
        enableInput(false);
        toggleNewChatButton(true);
    } else {
        enableInput(true);
        toggleNewChatButton(false);
    }
}


async function initSession() {
    try {
        const response = await fetch(`${API_BASE}/create-new-session`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error("Failed to create session");
        
        const data = await response.json();
        
        // Update State
        currentState.sessionId = data.session_id;
        currentState.threadId = data.thread_id;
        currentState.mode = 'start';
        currentState.messages = []; // Clear history for new session
        
        saveStateToStorage();
        
        // Update UI
        clearMessages();
        addMessage('system', 'Session created. Please describe the job role.');
        enableInput(true);
        
    } catch (error) {
        addMessage('system', `Error: ${error.message}. Please refresh.`);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const text = inputField.value.trim();
    if (!text || currentState.isProcessing) return;
    
    // Update State & UI
    addMessage('user', text);
    inputField.value = '';
    setInputProcessing(true);

    try {
        let endpoint = "";
        
        if (currentState.mode === 'start') {
            endpoint = '/start';
        } else if (currentState.mode === 'resume') {
            endpoint = '/resume';
        } else {
            throw new Error("Chat is closed");
        }

        const payload = {
            thread_id: currentState.threadId,
            user_message: text
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Session-Id': currentState.sessionId },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "API Error");
        }

        const data = await response.json();
        
        // Handle Response
        addMessage('bot', data.result);
        
        // Update Mode based on Status
        if (data.status === 'MORE_INFO') {
            currentState.mode = 'resume';
            toggleNewChatButton(true); 
        } else if (data.status === 'MATCH_FOUND') {
            currentState.mode = 'closed';
            toggleNewChatButton(true);
            enableInput(false);
        }
        
        saveStateToStorage();

    } catch (error) {
        addMessage('system', `Error: ${error.message}`);
    } finally {
        if (currentState.mode !== 'closed') {
            setInputProcessing(false);
        }
    }
}

async function startNewChat() {
    if (!currentState.sessionId) return;
    
    setInputProcessing(true);
    
    try {
        const response = await fetch(`${API_BASE}/create-new-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Session-Id': currentState.sessionId }
        });

        if (!response.ok) throw new Error("Failed to start new chat");

        const data = await response.json();
        
        // Update State
        currentState.threadId = data.thread_id;
        currentState.mode = 'start';
        currentState.messages = []; // Clear history
        
        saveStateToStorage();
        
        // Reset UI
        clearMessages();
        addMessage('system', 'New chat started.');
        enableInput(true);
        toggleNewChatButton(false);
        inputField.focus();
        
    } catch (error) {
        addMessage('system', `Error starting new chat: ${error.message}`);
    } finally {
        setInputProcessing(false);
    }
}

// --- UI Helpers ---

// Split into two: addMessage (logic) and addMessageToDOM (visual)
function addMessage(role, text) {
    // 1. Add to state history
    currentState.messages.push({ role, content: text });
    saveStateToStorage(); // Sync immediately
    
    // 2. Add to Visuals
    addMessageToDOM(role, text);
}

function addMessageToDOM(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    
    if (role === 'user') {
        msgDiv.classList.add('user-message');
        msgDiv.textContent = text;
    } else if (role === 'bot') {
        msgDiv.classList.add('bot-message');
        // Simple markdown replacement
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        msgDiv.innerHTML = formattedText; 
    } else {
        msgDiv.classList.add('system-message');
        msgDiv.textContent = text;
    }
    
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
}

function clearMessages() {
    messagesDiv.innerHTML = '';
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function setInputProcessing(processing) {
    currentState.isProcessing = processing;
    if (processing) {
        loadingIndicator.classList.remove('hidden');
        sendBtn.disabled = true;
        inputField.disabled = true;
    } else {
        loadingIndicator.classList.add('hidden');
        sendBtn.disabled = false;
        inputField.disabled = false;
        inputField.focus();
    }
}

function enableInput(enabled) {
    inputField.disabled = !enabled;
    sendBtn.disabled = !enabled;
    if (enabled) inputField.focus();
}

function toggleNewChatButton(show) {
    if (show) {
        newChatBtn.classList.remove('hidden');
    } else {
        newChatBtn.classList.add('hidden');
    }
}