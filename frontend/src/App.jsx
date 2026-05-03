import { useEffect, useRef, useState } from "react";

const STORAGE_KEY = "jarvis-react-state";
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const quickCommands = [
  { label: "System", caption: "Health snapshot", command: "system status" },
  { label: "Weather", caption: "Mumbai conditions", command: "can u tell me the mumbai temperature" },
  { label: "Cricket", caption: "Live score lookup", command: "tell me live cricket score" },
  { label: "Research", caption: "Virat Kohli summary", command: "can you tell me who is virat kohli" },
  { label: "News", caption: "Top headlines", command: "top news" },
  { label: "YouTube", caption: "Open web action", command: "open youtube" }
];

const starterPrompts = [
  "can you tell me who is virat kohli",
  "tell me live cricket score",
  "can u tell me the mumbai temperature",
  "and what about chennai",
  "what is 24 multiplied by 8"
];

const capabilityFallback = [
  "Natural voice-style question answering",
  "Context-aware follow-up weather queries",
  "Live cricket score browser actions",
  "Memory and recent-command session recall"
];

const defaultSettings = {
  aiEnabled: false,
  speakResponses: true,
  openLinksInNewTab: true,
  responseMode: "balanced"
};

function readStoredState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { memory: "", history: [], settings: defaultSettings };
    }
    const parsed = JSON.parse(raw);
    return {
      memory: typeof parsed.memory === "string" ? parsed.memory : "",
      history: Array.isArray(parsed.history) ? parsed.history : [],
      settings: {
        ...defaultSettings,
        ...(parsed.settings || {})
      }
    };
  } catch {
    return { memory: "", history: [], settings: defaultSettings };
  }
}

function App() {
  const initialState = readStoredState();
  const synth = window.speechSynthesis;
  const chatRef = useRef(null);

  const [memory, setMemory] = useState(initialState.memory);
  const [history, setHistory] = useState(initialState.history);
  const [settings, setSettings] = useState(initialState.settings);
  const [messages, setMessages] = useState(() => {
    const seed = initialState.history.slice(-8).flatMap((entry) => [
      { role: "user", text: entry.command },
      { role: "jarvis", text: entry.response, card: entry.card || null }
    ]);

    return seed.length
      ? seed
      : [
          {
            role: "jarvis",
            text: "Jarvis control plane is online. Ask naturally for weather, biographies, scores, search, news, and browser actions.",
            card: null
          }
        ];
  });
  const [input, setInput] = useState("");
  const [status, setStatus] = useState({
    assistant: "online",
    time: "--:--",
    date: "--",
    ai_available: false,
    voice_input: SpeechRecognition ? "browser-supported" : "unavailable",
    voice_output: "browser-supported",
    history_count: initialState.history.length,
    memory: initialState.memory || "No memory stored",
    motd: "Ready.",
    capabilities: capabilityFallback
  });
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        memory,
        history,
        settings
      })
    );
  }, [memory, history, settings]);

  useEffect(() => {
    void loadStatus();
  }, []);

  useEffect(() => {
    if (!chatRef.current) {
      return;
    }
    chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }
    const timer = window.setTimeout(() => setToast(""), 2400);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function loadStatus() {
    try {
      const response = await fetch("/api/status");
      const data = await response.json();
      setStatus((prev) => ({
        ...prev,
        ...data,
        history_count: history.length,
        memory: memory || "No memory stored"
      }));
    } catch {
      setToast("Status refresh failed");
    }
  }

  function speak(text) {
    if (!synth || !settings.speakResponses) {
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    synth.cancel();
    synth.speak(utterance);
  }

  function runClientAction(action, payload = {}) {
    if (action === "open_url" && payload.url) {
      const target = settings.openLinksInNewTab ? "_blank" : "_self";
      window.open(payload.url, target, settings.openLinksInNewTab ? "noopener" : undefined);
    }
  }

  async function sendCommand(command, { speakBack = true } = {}) {
    const trimmed = command.trim();
    if (!trimmed || isSending) {
      return;
    }

    setIsSending(true);
    setMessages((prev) => [...prev, { role: "user", text: trimmed, card: null }]);

    try {
      const response = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          client_state: { memory, history, settings }
        })
      });

      const data = await response.json();
      const card = data.payload?.card || null;
      setMessages((prev) => [...prev, { role: "jarvis", text: data.response, card }]);
      runClientAction(data.action, data.payload || {});

      setHistory((prev) => {
        if (data.action === "clear_history") {
          return [];
        }
        return [
          ...prev,
          {
            command: trimmed,
            response: data.response,
            card,
            timestamp: new Date().toISOString()
          }
        ].slice(-30);
      });

      if (data.action === "set_memory") {
        setMemory(data.payload?.memory || "");
      }

      if (data.action === "clear_memory") {
        setMemory("");
      }

      if (data.payload?.status) {
        setStatus((prev) => ({
          ...prev,
          ...data.payload.status,
          history_count: data.action === "clear_history" ? 0 : history.length + 1,
          memory:
            data.action === "set_memory"
              ? data.payload?.memory || "No memory stored"
              : data.action === "clear_memory"
                ? "No memory stored"
                : memory || "No memory stored"
        }));
      } else {
        await loadStatus();
      }

      if (speakBack) {
        speak(data.response);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "jarvis", text: "I could not reach the backend right now. Please try again.", card: null }
      ]);
    } finally {
      setInput("");
      setIsSending(false);
    }
  }

  function handleVoice() {
    if (!SpeechRecognition) {
      setToast("Voice input is not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      await sendCommand(transcript);
    };

    recognition.onerror = () => {
      setToast("Could not hear clearly");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  }

  function clearHistory() {
    setHistory([]);
    setMessages([{ role: "jarvis", text: "Conversation cleared. Control plane ready for a new task.", card: null }]);
    setStatus((prev) => ({ ...prev, history_count: 0 }));
    setToast("History cleared");
  }

  function clearMemory() {
    setMemory("");
    setStatus((prev) => ({ ...prev, memory: "No memory stored" }));
    setToast("Memory cleared");
  }

  const recentHistory = history.slice(-5).reverse();
  const capabilityItems = status.capabilities?.length ? status.capabilities : capabilityFallback;

  return (
    <div className="app-shell">
      <div className="grid-layer" />
      <div className="glow glow-left" />
      <div className="glow glow-right" />
      <div className="floating-objects" aria-hidden="true">
        <div className="float-gyroscope gyro-a">
          <span className="gyro-core" />
          <span className="gyro-ring g1" />
          <span className="gyro-ring g2" />
          <span className="gyro-ring g3" />
        </div>
        <div className="float-cube cube-a">
          <span />
          <span />
          <span />
        </div>
        <div className="float-pyramid pyramid-a">
          <span className="pyramid-glow" />
        </div>
        <div className="float-prism prism-a">
          <span className="prism-face pf-1" />
          <span className="prism-face pf-2" />
          <span className="prism-face pf-3" />
        </div>
        <div className="float-helix helix-a">
          <span className="helix-node hn-1" />
          <span className="helix-node hn-2" />
          <span className="helix-node hn-3" />
          <span className="helix-line" />
        </div>
      </div>

      <header className="masthead">
        <div className="brand-cluster">
          <div className="brand-mark">
            <span className="brand-core" />
            <span className="brand-ring ring-one" />
            <span className="brand-ring ring-two" />
          </div>
          <div>
            <p className="overline">Jarvis Control Plane</p>
            <h1>High-signal assistant workspace</h1>
            <p className="lead">
              A browser-based AI cockpit for live answers, contextual follow-ups, memory, web actions, and voice-first interaction.
            </p>
          </div>
        </div>

        <div className="masthead-actions">
          <div className="status-rail">
            <span className="status-dot" />
            <span className="status-label">{status.assistant}</span>
          </div>
          <button className="ghost-button" onClick={() => void loadStatus()}>
            Refresh status
          </button>
        </div>
      </header>

      <section className="hero-grid">
        <div className="hero-card">
          <div className="hero-copy">
            <span className="panel-kicker">Mission Summary</span>
            <h2>Professional UI with a real tech-console feel</h2>
            <p>
              Designed for natural commands, quick scanning, and a stronger engineering-product aesthetic without looking noisy or amateur.
            </p>
          </div>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => void sendCommand("system status", { speakBack: false })}>
              Run system check
            </button>
            <button className="ghost-button" onClick={() => void sendCommand("help", { speakBack: false })}>
              Inspect capabilities
            </button>
          </div>
        </div>

        <div className="telemetry-card">
          <span className="panel-kicker">Live Telemetry</span>
          <div className="telemetry-art" aria-hidden="true">
            <div className="telemetry-node node-1" />
            <div className="telemetry-node node-2" />
            <div className="telemetry-beam" />
          </div>
          <div className="telemetry-grid">
            <StatusTile label="Time" value={status.time} />
            <StatusTile label="Voice In" value={status.voice_input} />
            <StatusTile label="Voice Out" value={status.voice_output} />
            <StatusTile label="AI Ready" value={status.ai_available ? "enabled" : "waiting"} />
          </div>
        </div>
      </section>

      <main className="dashboard">
        <aside className="left-column">
          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Quick Actions</span>
            </div>
            <div className="command-grid">
              {quickCommands.map((item) => (
                <button
                  key={item.command}
                  className="command-card"
                  onClick={() => void sendCommand(item.command, { speakBack: false })}
                >
                  <strong>{item.label}</strong>
                  <span>{item.caption}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Memory Cache</span>
              <button className="inline-button" onClick={clearMemory}>
                Clear
              </button>
            </div>
            <div className="memory-card">{memory || "No memory stored"}</div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Prompt Deck</span>
            </div>
            <div className="prompt-list">
              {starterPrompts.map((prompt) => (
                <button key={prompt} className="prompt-card" onClick={() => setInput(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="center-column">
          <section className="panel conversation-panel">
            <div className="panel-header conversation-header">
              <div>
                <span className="panel-kicker">Conversation Stream</span>
                <p className="subtle-copy">Natural requests, voice prompts, and multi-step follow-ups.</p>
              </div>
              <button className="inline-button" onClick={clearHistory}>
                Reset
              </button>
            </div>

            <div ref={chatRef} className="chat-list">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`message-row ${message.role}`}>
                  <div className="message-meta">{message.role === "user" ? "You" : "Jarvis"}</div>
                  <div className="message-card">
                    <p>{message.text}</p>
                    {message.card ? <ResultCard card={message.card} /> : null}
                  </div>
                </div>
              ))}
            </div>

            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault();
                void sendCommand(input);
              }}
            >
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Try: can you tell me who is Virat Kohli, tell me live cricket score, or can u tell me the Mumbai temperature"
                rows={4}
              />
              <div className="composer-footer">
                <p className="subtle-copy">{status.motd}</p>
                <div className="composer-actions">
                  <button
                    type="button"
                    className={`ghost-button ${isListening ? "is-listening" : ""}`}
                    onClick={handleVoice}
                  >
                    {isListening ? "Listening..." : "Talk"}
                  </button>
                  <button type="submit" className="primary-button" disabled={isSending}>
                    {isSending ? "Processing..." : "Send Command"}
                  </button>
                </div>
              </div>
            </form>
          </section>

          <section className="panel systems-canvas">
            <div className="panel-header">
              <span className="panel-kicker">Systems Canvas</span>
              <span className="canvas-tag">live motion</span>
            </div>
            <div className="canvas-stage" aria-hidden="true">
              <div className="canvas-radar">
                <span className="radar-ring rr-1" />
                <span className="radar-ring rr-2" />
                <span className="radar-ring rr-3" />
                <span className="radar-sweep" />
                <span className="radar-core" />
              </div>

              <div className="data-column dc-1"><span /></div>
              <div className="data-column dc-2"><span /></div>
              <div className="data-column dc-3"><span /></div>
              <div className="data-column dc-4"><span /></div>

              <div className="signal-orb so-1" />
              <div className="signal-orb so-2" />
              <div className="signal-orb so-3" />

              <div className="signal-line sl-1" />
              <div className="signal-line sl-2" />
              <div className="signal-line sl-3" />

              <div className="floating-plate fp-1" />
              <div className="floating-plate fp-2" />
              <div className="floating-plate fp-3" />
            </div>
            <div className="canvas-footer">
              <div className="canvas-stat">
                <strong>Realtime Visual Layer</strong>
                <span>Animated objects and telemetry now fill unused space so the layout stays active.</span>
              </div>
              <div className="canvas-stat">
                <strong>Motion System</strong>
                <span>Radar sweep, floating plates, signal orbs, and data towers create a more alive control-plane feel.</span>
              </div>
            </div>
          </section>
        </section>

        <aside className="right-column">
          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Settings</span>
            </div>
            <div className="settings-list">
              <label className="setting-row">
                <div>
                  <strong>AI answers</strong>
                  <span>Use a real model when an API key is configured.</span>
                </div>
                <input
                  type="checkbox"
                  checked={settings.aiEnabled}
                  onChange={(event) =>
                    setSettings((prev) => ({ ...prev, aiEnabled: event.target.checked }))
                  }
                />
              </label>

              <label className="setting-row">
                <div>
                  <strong>Speak responses</strong>
                  <span>Read Jarvis answers aloud in the browser.</span>
                </div>
                <input
                  type="checkbox"
                  checked={settings.speakResponses}
                  onChange={(event) =>
                    setSettings((prev) => ({ ...prev, speakResponses: event.target.checked }))
                  }
                />
              </label>

              <label className="setting-row">
                <div>
                  <strong>Open links in new tab</strong>
                  <span>Keep the control plane open while actions launch.</span>
                </div>
                <input
                  type="checkbox"
                  checked={settings.openLinksInNewTab}
                  onChange={(event) =>
                    setSettings((prev) => ({ ...prev, openLinksInNewTab: event.target.checked }))
                  }
                />
              </label>

              <label className="setting-select">
                <span>Response style</span>
                <select
                  value={settings.responseMode}
                  onChange={(event) =>
                    setSettings((prev) => ({ ...prev, responseMode: event.target.value }))
                  }
                >
                  <option value="concise">Concise</option>
                  <option value="balanced">Balanced</option>
                  <option value="detailed">Detailed</option>
                </select>
              </label>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Capabilities</span>
            </div>
            <div className="capability-list">
              {capabilityItems.map((item) => (
                <div key={item} className="capability-card">
                  {item}
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Recent Activity</span>
            </div>
            <div className="history-list">
              {recentHistory.length ? (
                recentHistory.map((entry) => (
                  <div key={entry.timestamp} className="history-card">
                    <strong>{entry.command}</strong>
                    <span>{entry.response}</span>
                  </div>
                ))
              ) : (
                <div className="history-card empty-card">
                  <span>No command history yet.</span>
                </div>
              )}
            </div>
          </section>
        </aside>
      </main>

      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  );
}

function StatusTile({ label, value }) {
  return (
    <div className="status-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ResultCard({ card }) {
  const { type, data } = card;

  if (type === "weather") {
    return (
      <div className="result-card weather-card">
        <strong>{data.city}</strong>
        <div className="result-pill">{data.temperature}</div>
        <span>{data.condition}</span>
      </div>
    );
  }

  if (type === "summary" || type === "ai") {
    return (
      <div className="result-card summary-card">
        <strong>{data.title || "Answer"}</strong>
        <span>{data.summary || data.description}</span>
      </div>
    );
  }

  if (type === "news") {
    return (
      <div className="result-card news-card">
        <strong>Headline Snapshot</strong>
        <ul>
          {(data.items || []).slice(0, 3).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    );
  }

  if (type === "calculation") {
    return (
      <div className="result-card calc-card">
        <strong>Calculation</strong>
        <span>{data.expression}</span>
        <div className="result-pill">{data.result}</div>
      </div>
    );
  }

  if (type === "sports" || type === "action") {
    return (
      <div className="result-card action-card-ui">
        <strong>{data.title}</strong>
        <span>{data.description}</span>
        <div className="result-pill">{data.cta}</div>
      </div>
    );
  }

  if (type === "status") {
    return (
      <div className="result-card status-card-ui">
        <strong>Assistant Status</strong>
        <span>{data.mode} mode</span>
        <div className="result-grid-mini">
          <div>{data.time}</div>
          <div>{data.date}</div>
        </div>
      </div>
    );
  }

  return null;
}

export default App;
