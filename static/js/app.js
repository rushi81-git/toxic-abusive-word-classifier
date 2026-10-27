/**
 * app.js - SafeChat NLP: Production Web Application Client Logic
 * Handles real-time Socket.IO events, interactive NLP diagnostics,
 * dual-user simulation, and syllabus proofs.
 */

// Application State
const state = {
  activeTab: 'chat',
  activeTier: 'premium',
  activeSender: 'User A',
  socket: null,
  isTypingTimeout: null,
  messages: [],
  selectedMessage: null
};

// Preset Scenarios
const PRESETS = {
  workplace: "Hey John, your update is complete garbage! I will hurt you today.",
  gaming: "You are a total idiot and a worthless moron.",
  threat: "I will hurt you today for ruining my account.",
  scam: "I hate everything about this scam company.",
  clean: "Great job team, let's schedule our design sync tomorrow morning."
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initSocket();
  initTabs();
  initWarmupPing();
  initEventListeners();
});

// -------------------------------------------------------------
// 1. Socket.IO & Latency Rule #3 (Ping Wakeup)
// -------------------------------------------------------------
function initWarmupPing() {
  const statusText = document.getElementById('status-text');
  const statusDot = document.getElementById('status-dot');
  const t0 = performance.now();

  fetch('/ping')
    .then(res => res.json())
    .then(data => {
      const rtt = Math.round(performance.now() - t0);
      statusText.innerText = `Online (${rtt}ms RTT)`;
      statusDot.style.background = 'var(--accent-emerald)';
      statusDot.style.boxShadow = '0 0 8px var(--accent-emerald)';
    })
    .catch(() => {
      statusText.innerText = 'Connecting to RAM...';
      statusDot.style.background = 'var(--accent-amber)';
    });
}

function initSocket() {
  const statusText = document.getElementById('status-text');
  const statusDot = document.getElementById('status-dot');

  try {
    state.socket = io({ reconnectionAttempts: 5 });

    state.socket.on('connect', () => {
      statusText.innerText = 'Engine Ready (<25ms)';
      statusDot.style.background = 'var(--accent-emerald)';
    });

    state.socket.on('disconnect', () => {
      statusText.innerText = 'Reconnecting...';
      statusDot.style.background = 'var(--accent-amber)';
    });

    state.socket.on('receive_message', (data) => {
      handleIncomingMessage(data);
    });

    state.socket.on('user_typing', (data) => {
      handleUserTyping(data);
    });

    state.socket.on('chat_cleared', () => {
      state.messages = [];
      const container = document.getElementById('chat-messages');
      if (container) container.innerHTML = '';
      resetInspector();
    });
  } catch (err) {
    console.warn('[SafeChat] Socket.IO initialization fallback to REST', err);
  }
}

// -------------------------------------------------------------
// 2. Tab Navigation
// -------------------------------------------------------------
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      switchTab(target);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });
}

// -------------------------------------------------------------
// 3. Tier & Persona Controls
// -------------------------------------------------------------
function toggleTier() {
  const toggleBtn = document.getElementById('tier-toggle');
  const label = document.getElementById('tier-label');
  const icon = document.getElementById('tier-icon');

  if (state.activeTier === 'premium') {
    state.activeTier = 'free';
    toggleBtn.classList.add('free-mode');
    label.innerText = 'FREE TIER: [BEEP] MASK';
    icon.innerText = '🛡️';
  } else {
    state.activeTier = 'premium';
    toggleBtn.classList.remove('free-mode');
    label.innerText = 'PREMIUM: AI DE-ESCALATE';
    icon.innerText = '⚡';
  }
}

function setSender(sender) {
  state.activeSender = sender;
  document.getElementById('chip-user-a').classList.toggle('active', sender === 'User A');
  document.getElementById('chip-user-b').classList.toggle('active', sender === 'User B');
}

// -------------------------------------------------------------
// 4. Presets & Quick Scenarios
// -------------------------------------------------------------
function loadPreset(key) {
  const text = PRESETS[key] || '';
  const chatInput = document.getElementById('msg-input');
  const sandboxInput = document.getElementById('sandbox-input');

  if (chatInput) {
    chatInput.value = text;
    chatInput.focus();
  }
  if (sandboxInput) {
    sandboxInput.value = text;
    runSandboxAnalysis();
  }
}

// -------------------------------------------------------------
// 5. Chat Interaction & Sending
// -------------------------------------------------------------
function initEventListeners() {
  const chatForm = document.getElementById('chat-form');
  const msgInput = document.getElementById('msg-input');

  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      sendChatMessage();
    });
  }

  if (msgInput) {
    msgInput.addEventListener('input', () => {
      emitTyping();
    });
  }
}

function emitTyping() {
  if (!state.socket || !state.socket.connected) return;
  state.socket.emit('typing', { sender: state.activeSender });
}

function handleUserTyping(data) {
  const bar = document.getElementById('typing-bar');
  const userSpan = document.getElementById('typing-user');
  if (!bar || !userSpan) return;

  userSpan.innerText = data.sender;
  bar.style.display = 'flex';

  clearTimeout(state.isTypingTimeout);
  state.isTypingTimeout = setTimeout(() => {
    bar.style.display = 'none';
  }, 1500);
}

function sendChatMessage() {
  const input = document.getElementById('msg-input');
  const text = input.value.trim();
  if (!text) return;

  const payload = {
    sender: state.activeSender,
    message: text,
    tier: state.activeTier
  };

  if (state.socket && state.socket.connected) {
    state.socket.emit('send_message', payload);
  } else {
    // REST API fallback
    fetch('/api/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => handleIncomingMessage(data))
      .catch(err => console.error('Send error:', err));
  }

  input.value = '';
}

function clearChat() {
  if (state.socket && state.socket.connected) {
    state.socket.emit('clear_chat');
  } else {
    state.messages = [];
    document.getElementById('chat-messages').innerHTML = '';
    resetInspector();
  }
}

// -------------------------------------------------------------
// 6. Asymmetric Message Rendering
// -------------------------------------------------------------
function handleIncomingMessage(msg) {
  state.messages.push(msg);
  renderMessageBubble(msg);
  updateInspector(msg);
}

function renderMessageBubble(msg) {
  const chatContainer = document.getElementById('chat-messages');
  if (!chatContainer) return;

  const isMe = msg.sender === state.activeSender;
  const isToxic = msg.is_toxic;

  // Asymmetric Presentation Rule:
  // - Sender sees their typed raw text (unfiltered).
  // - Receiver sees the polite de-escalated or beep-masked output!
  const displayText = isMe ? msg.original_message : msg.final_message;

  let bubbleStyleClass = 'clean-bubble';
  let pillClass = 'pill-clean';
  let pillText = 'CLEAN PASS';

  if (msg.action_taken === 'premium_de_escalated') {
    bubbleStyleClass = 'premium-bubble';
    pillClass = 'pill-premium';
    pillText = isMe ? 'SENT (ORIGINAL RAW)' : 'AI DE-ESCALATED';
  } else if (msg.action_taken === 'free_beep_masked') {
    bubbleStyleClass = 'free-bubble';
    pillClass = 'pill-free';
    pillText = isMe ? 'SENT (UNFILTERED)' : '[BEEP] REDACTED';
  }

  const scorePct = (msg.toxicity_score * 100).toFixed(1);
  const toxicClass = isToxic ? 'toxic-red' : 'toxic-green';

  const row = document.createElement('div');
  row.className = `msg-row ${isMe ? 'me' : 'partner'}`;

  row.innerHTML = `
    <div class="msg-meta">
      <span class="msg-sender-name">${escapeHtml(msg.sender)} ${isMe ? '(You)' : '(Partner)'}</span>
      <span>•</span>
      <span>${msg.tier_applied.toUpperCase()}</span>
    </div>
    <div class="bubble-card ${bubbleStyleClass}" onclick="selectMessage(${state.messages.length - 1})">
      <div class="bubble-header">
        <span class="action-pill ${pillClass}">${pillText}</span>
        <span class="bubble-latency">${msg.server_compute_ms}ms compute</span>
      </div>
      <div class="bubble-content">${escapeHtml(displayText)}</div>
      
      ${isToxic ? `
        <div class="asymmetric-indicator ${isMe ? 'sender-notice' : 'receiver-notice'}">
          ${isMe ? '🛡️ You see your typed text. Partner receives the de-escalated version.' : '🛡️ De-escalated prior to delivery.'}
        </div>
      ` : ''}

      <div class="bubble-footer">
        <span class="toxicity-badge ${toxicClass}">Toxicity: ${scorePct}%</span>
        <span class="click-hint">🔍 Tap to inspect NLP</span>
      </div>
    </div>
  `;

  chatContainer.appendChild(row);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// -------------------------------------------------------------
// 7. Side Diagnostic Inspector
// -------------------------------------------------------------
function selectMessage(index) {
  const msg = state.messages[index];
  if (msg) updateInspector(msg);
}

function updateInspector(msg) {
  state.selectedMessage = msg;

  // Toxicity Score
  const scorePct = (msg.toxicity_score * 100).toFixed(1);
  const scoreVal = document.getElementById('inspect-score-val');
  const scoreBar = document.getElementById('inspect-score-bar');
  const latencyVal = document.getElementById('inspect-latency');

  if (scoreVal) scoreVal.innerText = `${scorePct}%`;
  if (latencyVal) latencyVal.innerText = `${msg.server_compute_ms}ms`;

  if (scoreBar) {
    scoreBar.style.width = `${scorePct}%`;
    scoreBar.style.background = msg.is_toxic 
      ? 'linear-gradient(90deg, #f59e0b 0%, #f43f5e 100%)' 
      : 'linear-gradient(90deg, #10b981 0%, #38bdf8 100%)';
  }

  // Preprocessing
  const prepVal = document.getElementById('inspect-preprocessed');
  if (prepVal && msg.preprocessing) {
    prepVal.innerText = `"${msg.preprocessing.stemmed || 'None'}"`;
  }

  // Transformations
  const transformContainer = document.getElementById('inspect-transformations');
  if (transformContainer) {
    if (msg.transformations && msg.transformations.length > 0) {
      transformContainer.innerHTML = `
        <table class="transform-table">
          <thead>
            <tr><th>Original</th><th>POS Tag</th><th>Replacement</th></tr>
          </thead>
          <tbody>
            ${msg.transformations.map(t => `
              <tr>
                <td style="color: #f43f5e; font-weight: 600;">${escapeHtml(t.original)}</td>
                <td style="color: #a855f7;">${escapeHtml(t.pos_tag)} (${escapeHtml(t.pos_desc)})</td>
                <td style="color: #10b981; font-weight: 600;">${escapeHtml(t.replacement)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } else {
      transformContainer.innerHTML = '<span style="font-size:11px; color:#64748b;">No toxic keywords detected (Clean pass).</span>';
    }
  }

  // Named Entities (spaCy)
  const nerContainer = document.getElementById('inspect-ner');
  if (nerContainer) {
    if (msg.ner_targets && msg.ner_targets.length > 0) {
      nerContainer.innerHTML = msg.ner_targets.map(ner => `
        <span class="chip-tag chip-ner">${escapeHtml(ner[0])} <b style="opacity:0.7">[${escapeHtml(ner[1])}]</b></span>
      `).join('');
    } else {
      nerContainer.innerHTML = '<span style="font-size:11px; color:#64748b;">No named entities found.</span>';
    }
  }

  // POS Tags (NLTK)
  const posContainer = document.getElementById('inspect-pos');
  if (posContainer) {
    if (msg.pos_tags && msg.pos_tags.length > 0) {
      posContainer.innerHTML = msg.pos_tags.slice(0, 12).map(pos => `
        <span class="chip-tag chip-pos" title="${escapeHtml(pos[2] || pos[1])}">${escapeHtml(pos[0])} (${escapeHtml(pos[1])})</span>
      `).join('');
    } else {
      posContainer.innerHTML = '<span style="font-size:11px; color:#64748b;">None</span>';
    }
  }
}

function resetInspector() {
  document.getElementById('inspect-score-val').innerText = '0%';
  document.getElementById('inspect-score-bar').style.width = '0%';
  document.getElementById('inspect-latency').innerText = '0ms';
  document.getElementById('inspect-preprocessed').innerText = 'None';
  document.getElementById('inspect-transformations').innerHTML = '<span style="font-size:11px; color:#64748b;">Awaiting message...</span>';
  document.getElementById('inspect-ner').innerHTML = '<span style="font-size:11px; color:#64748b;">None</span>';
  document.getElementById('inspect-pos').innerHTML = '<span style="font-size:11px; color:#64748b;">None</span>';
}

// -------------------------------------------------------------
// 8. Sandbox & Deep Inspector Tab
// -------------------------------------------------------------
function runSandboxAnalysis() {
  const input = document.getElementById('sandbox-input');
  const text = input ? input.value.trim() : '';
  if (!text) return;

  const btn = document.getElementById('sandbox-run-btn');
  if (btn) btn.innerText = 'Analyzing...';

  fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, tier: 'premium', sender: 'Sandbox' })
  })
    .then(res => res.json())
    .then(data => {
      renderSandboxResults(data);
      if (btn) btn.innerText = 'Run NLP Analysis';
    })
    .catch(err => {
      console.error(err);
      if (btn) btn.innerText = 'Run NLP Analysis';
    });
}

function renderSandboxResults(data) {
  const rawPreview = document.getElementById('preview-raw');
  const freePreview = document.getElementById('preview-free');
  const premPreview = document.getElementById('preview-premium');
  const sandboxScore = document.getElementById('sandbox-score');
  const sandboxBar = document.getElementById('sandbox-score-bar');
  const sandboxLatency = document.getElementById('sandbox-latency');

  if (rawPreview) rawPreview.innerText = data.original_message;
  if (freePreview) freePreview.innerText = data.free_masked_message || data.final_message;
  if (premPreview) premPreview.innerText = data.premium_de_escalated_message || data.final_message;

  const pct = (data.toxicity_score * 100).toFixed(1);
  if (sandboxScore) sandboxScore.innerText = `${pct}%`;
  if (sandboxLatency) sandboxLatency.innerText = `${data.server_compute_ms}ms compute`;
  if (sandboxBar) {
    sandboxBar.style.width = `${pct}%`;
    sandboxBar.style.background = data.is_toxic 
      ? 'linear-gradient(90deg, #f59e0b 0%, #f43f5e 100%)' 
      : 'linear-gradient(90deg, #10b981 0%, #38bdf8 100%)';
  }

  // Preprocessing breakdown
  const cleanTokens = document.getElementById('sandbox-clean-text');
  const stemTokens = document.getElementById('sandbox-stemmed-text');
  if (cleanTokens && data.preprocessing) cleanTokens.innerText = data.preprocessing.cleaned;
  if (stemTokens && data.preprocessing) stemTokens.innerText = data.preprocessing.stemmed;

  // POS & NER in sandbox
  const posCloud = document.getElementById('sandbox-pos-cloud');
  if (posCloud && data.pos_tags) {
    posCloud.innerHTML = data.pos_tags.map(p => `
      <span class="chip-tag chip-pos" title="${escapeHtml(p[2] || p[1])}">${escapeHtml(p[0])} <b style="opacity:0.7">(${escapeHtml(p[1])})</b></span>
    `).join('');
  }

  const nerCloud = document.getElementById('sandbox-ner-cloud');
  if (nerCloud && data.ner_targets) {
    nerCloud.innerHTML = data.ner_targets.length > 0 
      ? data.ner_targets.map(n => `<span class="chip-tag chip-ner">${escapeHtml(n[0])} [${escapeHtml(n[1])}]</span>`).join('')
      : '<span style="font-size:12px; color:#64748b;">No named entities detected.</span>';
  }
}

// -------------------------------------------------------------
// 9. CYK Syntax Tree Parser (Topic 7)
// -------------------------------------------------------------
function parseSyntaxTree() {
  const input = document.getElementById('cyk-input');
  const output = document.getElementById('tree-output');
  const text = input ? input.value.trim() : 'service is garbage';

  if (!output) return;
  output.innerText = 'Parsing chart syntax tree...';

  fetch('/api/parse-tree', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sentence: text })
  })
    .then(res => res.json())
    .then(data => {
      if (data.parsed && data.trees.length > 0) {
        output.innerText = data.trees.join('\n\n');
      } else {
        output.innerText = `No complete parse tree found for input: "${data.sentence}"\n\nRule Note: ${data.note || 'Try: service is garbage | product is clean | work is subpar'}`;
      }
    })
    .catch(err => {
      output.innerText = 'Error running parser: ' + err.message;
    });
}

// -------------------------------------------------------------
// 10. Utilities
// -------------------------------------------------------------
function copyCode(btn) {
  const codeBlock = btn.parentElement.querySelector('code');
  if (!codeBlock) return;
  navigator.clipboard.writeText(codeBlock.innerText).then(() => {
    const original = btn.innerText;
    btn.innerText = 'Copied!';
    setTimeout(() => { btn.innerText = original; }, 1500);
  });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}
