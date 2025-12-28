const API_BASE = "http://localhost:8000";

// Internal State
const currentState = {
    sessionId: null,
    threadId: null,
    mode: "initializing", // 'initializing', 'start', 'resume', 'closed'
    isProcessing: false
};

// DOM Elements
const messagesDiv = document.getElementById('messages');
const inputField = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const loadingIndicator = document.getElementById('loading-indicator');

// --- Initialization ---

window.addEventListener('DOMContentLoaded', async () => {
    await initSession();
});

async function initSession() {
    try {
        const response = await fetch(`${API_BASE}/create-new-session`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error("Failed to create session");
        
        const data = await response.json();
        
        // Save to state
        currentState.sessionId = data.session_id;
        currentState.threadId = data.thread_id;
        currentState.mode = 'start';
        
        // Update UI
        clearMessages();
        addMessage('system', 'Session created. Please describe the job role.');
        enableInput(true);
        
    } catch (error) {
        addMessage('system', `Error: ${error.message}. Please refresh.`);
    }
}

// --- Core Logic ---

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const text = inputField.value.trim();
    if (!text || currentState.isProcessing) return;
    
    // Add User Message to UI
    addMessage('user', text);
    inputField.value = '';
    setInputProcessing(true);

    try {
        let endpoint = "";
        
        // Determine Endpoint based on Mode
        if (currentState.mode === 'start') {
            endpoint = '/start';
        } else if (currentState.mode === 'resume') {
            endpoint = '/resume';
        } else {
            throw new Error("Chat is closed");
        }

        // Prepare Request Body (session_id in body as requested)
        const payload = {
            session_id: currentState.sessionId,
            thread_id: currentState.threadId,
            user_message: text
        };

        // Call API
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "API Error");
        }

        const data = await response.json();
        
        // Handle Response
        addMessage('bot', data.result);
        
        // Update State based on Status
        if (data.status === 'MORE_INFO') {
            currentState.mode = 'resume';
            toggleNewChatButton(true); // Allow restart if stuck
        } else if (data.status === 'MATCH_FOUND') {
            currentState.mode = 'closed';
            toggleNewChatButton(true);
            enableInput(false); // Disable input on success
        }

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
        // Query param for create-new-chat as per api.py wrapper logic
        const response = await fetch(`${API_BASE}/create-new-chat?session_id=${currentState.sessionId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error("Failed to start new chat");

        const data = await response.json();
        
        // Update State
        currentState.threadId = data.thread_id;
        currentState.mode = 'start';
        
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

function addMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    
    if (role === 'user') {
        msgDiv.classList.add('user-message');
    } else if (role === 'bot') {
        msgDiv.classList.add('bot-message');
        // Render simple Markdown (bolding)
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        msgDiv.innerHTML = text; // Be careful with XSS in production, strictly for this project
    } else {
        msgDiv.classList.add('system-message');
        msgDiv.textContent = text;
    }

    if(role !== 'bot') msgDiv.textContent = text; // Safety for user/system input
    
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