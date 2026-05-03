const chat = document.getElementById("chat");
const form = document.getElementById("command-form");
const input = document.getElementById("command-input");
const voiceBtn = document.getElementById("voice-btn");
const tipButtons = document.querySelectorAll(".tip");
const actionButtons = document.querySelectorAll(".action-btn");
const refreshStatusBtn = document.getElementById("refresh-status-btn");
const clearHistoryBtn = document.getElementById("clear-history-btn");
const clearMemoryBtn = document.getElementById("clear-memory-btn");

const statusBadge = document.getElementById("status-badge");
const timeValue = document.getElementById("time-value");
const voiceInputValue = document.getElementById("voice-input-value");
const voiceOutputValue = document.getElementById("voice-output-value");
const historyCountValue = document.getElementById("history-count-value");
const memoryPreview = document.getElementById("memory-preview");
const motd = document.getElementById("motd");
const capabilityList = document.getElementById("capability-list");
const historyList = document.getElementById("history-list");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
const STORAGE_KEY = "jarvis-web-state";

function getStoredState() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) {
            return { memory: "", history: [] };
        }
        const parsed = JSON.parse(raw);
        return {
            memory: typeof parsed.memory === "string" ? parsed.memory : "",
            history: Array.isArray(parsed.history) ? parsed.history : [],
        };
    } catch (error) {
        return { memory: "", history: [] };
    }
}

function saveStoredState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function addMessage(role, text) {
    const article = document.createElement("article");
    article.className = `message ${role}`;

    const speaker = document.createElement("span");
    speaker.className = "speaker";
    speaker.textContent = role === "user" ? "You" : "Jarvis";

    const body = document.createElement("p");
    body.textContent = text;

    article.append(speaker, body);
    chat.appendChild(article);
    chat.scrollTop = chat.scrollHeight;
}

function renderCapabilities(capabilities = []) {
    capabilityList.innerHTML = "";
    capabilities.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        capabilityList.appendChild(li);
    });
}

function renderHistory(history = []) {
    historyList.innerHTML = "";
    if (!history.length) {
        const empty = document.createElement("div");
        empty.className = "history-item";
        empty.innerHTML = "<strong>No history</strong><span>Recent commands will appear here.</span>";
        historyList.appendChild(empty);
        return;
    }

    history.slice().reverse().slice(0, 8).forEach((entry) => {
        const item = document.createElement("div");
        item.className = "history-item";

        const command = document.createElement("strong");
        command.textContent = entry.command;

        const response = document.createElement("span");
        response.textContent = entry.response;

        item.append(command, response);
        historyList.appendChild(item);
    });
}

function applyStatus(status) {
    const state = getStoredState();
    if (!status) {
        return;
    }

    statusBadge.textContent = String(status.assistant || "unknown").toUpperCase();
    timeValue.textContent = status.time || "--:--";
    voiceInputValue.textContent = status.voice_input || "unknown";
    voiceOutputValue.textContent = status.voice_output || "unknown";
    historyCountValue.textContent = String(state.history.length);
    memoryPreview.textContent = state.memory || "No memory stored";
    motd.textContent = status.motd || "Awaiting status feed.";
    renderCapabilities(status.capabilities || []);
}

function updateStateAfterResponse(message, response, data) {
    const state = getStoredState();

    if (data.action === "set_memory") {
        state.memory = data.payload?.memory || "";
    }

    if (data.action === "clear_memory") {
        state.memory = "";
    }

    if (data.action === "clear_history") {
        state.history = [];
    } else {
        state.history.push({
            command: message,
            response,
            timestamp: new Date().toISOString(),
        });
        state.history = state.history.slice(-30);
    }

    saveStoredState(state);
    renderHistory(state.history);
    historyCountValue.textContent = String(state.history.length);
    memoryPreview.textContent = state.memory || "No memory stored";
    return state;
}

function runClientAction(action, payload = {}) {
    if (action === "open_url" && payload.url) {
        window.open(payload.url, payload.target || "_blank", "noopener");
    }
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

async function loadStatus() {
    try {
        const data = await fetchJson("/api/status");
        applyStatus(data);
    } catch (error) {
        motd.textContent = "Status link unavailable. Refresh when the server is stable.";
    }
}

function loadLocalState() {
    const state = getStoredState();
    renderHistory(state.history);
    historyCountValue.textContent = String(state.history.length);
    memoryPreview.textContent = state.memory || "No memory stored";
}

async function sendCommand(message, shouldSpeak = true) {
    addMessage("user", message);
    input.value = "";

    try {
        const state = getStoredState();
        const data = await fetchJson("/api/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message,
                client_state: {
                    memory: state.memory,
                    history: state.history,
                },
            }),
        });

        addMessage("jarvis", data.response);
        runClientAction(data.action, data.payload);
        const nextState = updateStateAfterResponse(message, data.response, data);

        if (data.payload && data.payload.status) {
            applyStatus(data.payload.status);
        } else {
            await loadStatus();
        }

        if (shouldSpeak && synth) {
            const utterance = new SpeechSynthesisUtterance(data.response);
            synth.cancel();
            synth.speak(utterance);
        }

        return nextState;
    } catch (error) {
        addMessage("jarvis", "I could not reach the local server. Make sure Jarvis is running.");
        return null;
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) {
        return;
    }
    await sendCommand(message);
});

tipButtons.forEach((button) => {
    button.addEventListener("click", () => {
        input.value = button.textContent.trim();
        input.focus();
    });
});

actionButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        const command = button.dataset.command;
        if (command) {
            await sendCommand(command, false);
        }
    });
});

refreshStatusBtn.addEventListener("click", async () => {
    await loadStatus();
    addMessage("jarvis", "Status panels refreshed.");
});

clearHistoryBtn.addEventListener("click", async () => {
    const state = getStoredState();
    state.history = [];
    saveStoredState(state);
    renderHistory([]);
    historyCountValue.textContent = "0";
    addMessage("jarvis", "Command history cleared in this browser.");
});

clearMemoryBtn.addEventListener("click", async () => {
    const state = getStoredState();
    state.memory = "";
    saveStoredState(state);
    memoryPreview.textContent = "No memory stored";
    addMessage("jarvis", "Memory cache cleared in this browser.");
    await loadStatus();
});

voiceBtn.addEventListener("click", () => {
    if (!SpeechRecognition) {
        addMessage("jarvis", "Voice input is not supported in this browser. You can still type commands.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    voiceBtn.disabled = true;
    voiceBtn.textContent = "Listening...";

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        await sendCommand(transcript);
    };

    recognition.onerror = () => {
        addMessage("jarvis", "I could not hear clearly. Please try again or type the command.");
    };

    recognition.onend = () => {
        voiceBtn.disabled = false;
        voiceBtn.textContent = "Talk";
    };

    recognition.start();
});

loadLocalState();
loadStatus();
