const API_BASE = "http://localhost:8000";

/* ---------------- STATE ---------------- */
let state = {
    sessionId: null,
    threadId: null,
    mode: "init", // init | start | resume | closed
    isProcessing: false,
    messages: []
};

const STORAGE_KEY = "nco_chat_state";

/* ---------------- DOM ---------------- */
const messagesDiv = document.getElementById("messages");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const loader = document.getElementById("loading-indicator");
const coldLoader = document.getElementById("coldstart-indicator");
const form = document.getElementById("chat-form");

/* ---------------- STORAGE ---------------- */
function saveState() {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadState() {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    
    state.sessionId = parsed.sessionId;
    state.threadId = parsed.threadId;
    state.mode = parsed.mode;
    state.messages = parsed.messages || [];

    state.isProcessing = false;
}

/* ---------------- API ---------------- */
async function apiCall(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API_BASE}${path}`, {
            headers: {
                "Content-Type": "application/json",
                "Session-Id": state.sessionId || ""
            },
            ...options
        });
    } catch {
        throw { detail: "NETWORK_ERROR", error_message: "Network error" };
    }

    if (!response.ok) {
        let body = {};
        try {
            body = await response.json();
        } catch {}

        throw {
            detail: body.detail,
            error_message: body.error_message || "Request failed"
        };
    }

    return response.json();
}

/* ---------------- ERROR HANDLER ---------------- */
function handleError(err) {

    console.error(err);    
    state.isProcessing = false;
    loader.classList.add("hidden");
    saveState();

    const category = err.detail.detail;
    const message = err.detail.error_message || "Unexpected error";

    switch (category) {
        case "INVALID_SESSION_ID":
        case "MISSING_HEADER":
            systemMessage("Session expired. Close this tab and start in a new tab.")
            break;

        case "INVALID_THREAD_ID":
        case "THREAD_ID_NOT_FOUND":
        case "THREAD_ID_ALREADY_EXISTS":
            systemMessage(message);
            enableInput(false);
            newChatBtn.classList.remove("hidden");
            break;

        case "CLOSED_THREAD":
            state.mode = "closed";
            enableInput(false);
            newChatBtn.classList.remove("hidden");
            systemMessage(message || "This chat is closed.");
            saveState();
            break;

        case "DATABASE_ERROR":
            systemMessage(message);
            break;

        default:
            // network / unknown
            coldLoader.classList.remove("hidden");
            systemMessage(message);
    }
}

/* ---------------- SESSION ---------------- */
async function initSession() {
    try {
        coldLoader.classList.remove("hidden");

        const data = await apiCall("/create-new-session", {
            method: "POST"
        });

        state.sessionId = data.session_id;
        state.threadId = data.thread_id;
        state.mode = "start";
        state.messages = [];

        saveState();
        clearMessages();
        systemMessage("Session created. Describe the job role.");
        enableInput(true);
    } catch (e) {
        handleError(e);
    }
    finally {
        coldLoader.classList.add("hidden");
    }
}

/* ---------------- CHAT ---------------- */
async function sendMessage(text) {

    if (state.mode === "closed") {
        systemMessage("This chat is closed. Please start a new chat.");
        newChatBtn.classList.remove("hidden");
        return;
    }

    addMessage("user", text);
    setProcessing(true);

    try {
        const endpoint = state.mode === "resume" ? "/resume" : "/start";

        const data = await apiCall(endpoint, {
            method: "PUT",
            body: JSON.stringify({
                thread_id: state.threadId,
                user_message: text
            })
        });

        addMessage("bot", data.result);

        if (data.status === "MORE_INFO") {
            state.mode = "resume";
            newChatBtn.classList.remove("hidden");
        } else {
            console.log("chat status:", data.status);
            state.mode = "closed";
            enableInput(false);
            newChatBtn.classList.remove("hidden");
        }

        saveState();
    } catch (e) {
        handleError(e);
    } finally {
        setProcessing(false);
    }
}


/* ---------------- UI ---------------- */
function renderMessage(role, text) {
    const div = document.createElement("div");
    div.className = `message ${role}-message`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addMessage(role, text) {
    state.messages.push({ role, content: text });
    saveState();

    renderMessage(role, text);
}

function systemMessage(text) {
    addMessage("system", text);
}

function clearMessages() {
    messagesDiv.innerHTML = "";
}

function enableInput(on) {
    input.disabled = !on;
    sendBtn.disabled = !on;
}

function setProcessing(on) {
    state.isProcessing = on;
    loader.classList.toggle("hidden", !on);
    enableInput(!on);
}

/* ---------------- EVENTS ---------------- */
form.addEventListener("submit", e => {
    e.preventDefault();
    if (!input.value || state.isProcessing) return;
    sendMessage(input.value.trim());
    input.value = "";
});

newChatBtn.addEventListener("click", async () => {
    try {
        setProcessing(false);

        const data = await apiCall("/create-new-chat", {
            method: "POST"
        });
        state.threadId = data.thread_id;
        state.mode = "start";
        state.messages = [];
        saveState();
        clearMessages();
        systemMessage("New chat started.");
        enableInput(true);
        newChatBtn.classList.add("hidden");
    } catch (e) {
        handleError(e);
    }
});


window.addEventListener("DOMContentLoaded", () => {
    loadState();
    clearMessages();
    if (state.sessionId) {
        state.messages.forEach(m => renderMessage(m.role, m.content));
        enableInput(state.mode !== "closed");
        if (state.mode !== "start" ) {
            newChatBtn.classList.remove("hidden");
        }
        if (state.mode === "start" && state.messages.length > 1) {
            newChatBtn.classList.remove("hidden");
        }
    } else {
        initSession();
    }
});