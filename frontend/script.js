const thread = document.getElementById("chat-thread");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const submitBtn = document.getElementById("chat-submit");
const chipRow = document.getElementById("chip-row");

function scrollToBottom() {
  thread.scrollTop = thread.scrollHeight;
}

function addUserMessage(text) {
  const el = document.createElement("div");
  el.className = "msg msg-user";
  el.innerHTML = `<p></p>`;
  el.querySelector("p").textContent = text;
  thread.appendChild(el);
  scrollToBottom();
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInline(line) {
  line = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  line = line.replace(/__(.+?)__/g, "<strong>$1</strong>");
  line = line.replace(/\*(.+?)\*/g, "<em>$1</em>");
  line = line.replace(/(?<!\w)_(.+?)_(?!\w)/g, "<em>$1</em>");
  return line;
}

function renderMarkdownLite(text) {
  const lines = escapeHtml(text).split("\n");
  let html = "";
  let listType = null;

  const closeList = () => {
    if (listType) { html += listType === "ul" ? "</ul>" : "</ol>"; listType = null; }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (line === "") { closeList(); continue; }

    const heading = line.match(/^#{1,6}\s+(.*)/);
    const bullet = line.match(/^[-*•]\s+(.*)/);
    const numbered = line.match(/^\d+\.\s+(.*)/);

    if (heading) {
      closeList();
      html += `<div class="msg-heading">${renderInline(heading[1])}</div>`;
    } else if (bullet) {
      if (listType !== "ul") { closeList(); html += "<ul>"; listType = "ul"; }
      html += `<li>${renderInline(bullet[1])}</li>`;
    } else if (numbered) {
      if (listType !== "ol") { closeList(); html += "<ol>"; listType = "ol"; }
      html += `<li>${renderInline(numbered[1])}</li>`;
    } else {
      closeList();
      html += `<p>${renderInline(line)}</p>`;
    }
  }
  closeList();
  return html;
}

function addAssistantMessage(text, sources, images) {
  const el = document.createElement("div");
  el.className = "msg msg-assistant";
  const contentEl = document.createElement("div");
  contentEl.className = "msg-content";
  contentEl.innerHTML = renderMarkdownLite(text);
  el.appendChild(contentEl);

  if (images && images.length > 0) {
    const imagesEl = document.createElement("div");
    imagesEl.className = "answer-images";
    images.slice(0, 3).forEach((path) => {
      const img = document.createElement("img");
      img.src = `${API_BASE_URL}/images/${path}`;
      img.alt = "Diagram from the manual";
      img.loading = "lazy";
      img.className = "answer-image";
      img.addEventListener("click", () => window.open(img.src, "_blank"));
      imagesEl.appendChild(img);
    });
    el.appendChild(imagesEl);
  }

  if (sources && sources.length > 0) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "sources";
    const seen = new Set();
    sources.forEach((s) => {
      const key = `${s.manual} p${s.page}`;
      if (seen.has(key)) return;
      seen.add(key);
      const tag = document.createElement("span");
      tag.className = "source-tag";
      tag.textContent = key;
      sourcesEl.appendChild(tag);
    });
    el.appendChild(sourcesEl);
  }

  thread.appendChild(el);
  scrollToBottom();
}

function addLoadingMessage() {
  const el = document.createElement("div");
  el.className = "msg msg-assistant msg-loading";
  el.id = "loading-msg";
  el.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  thread.appendChild(el);
  scrollToBottom();
  return el;
}

async function askQuestion(question) {
  addUserMessage(question);
  const chips = document.getElementById("chip-row");
  if (chips) chips.remove();

  input.value = "";
  input.disabled = true;
  submitBtn.disabled = true;
  const loadingEl = addLoadingMessage();

  try {
    const res = await fetch(`${API_BASE_URL}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    loadingEl.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      addAssistantMessage(
        err.detail || "Something went wrong reaching the assistant. Is the backend running and indexed?",
        []
      );
      return;
    }

    const data = await res.json();
    addAssistantMessage(data.answer, data.sources, data.images);
  } catch (e) {
    loadingEl.remove();
    addAssistantMessage(
      `Couldn't reach the backend at ${API_BASE_URL}. Make sure it's running (see README) and that this page's API_BASE_URL in config.js points at it.`,
      []
    );
  } finally {
    input.disabled = false;
    submitBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  askQuestion(q);
});

chipRow.addEventListener("click", (e) => {
  if (e.target.classList.contains("chip")) {
    askQuestion(e.target.textContent);
  }
});

async function checkHealth() {
  const dot = document.getElementById("status-dot");
  const statusText = document.getElementById("stat-status");
  const manualsEl = document.getElementById("stat-manuals");
  const chunksEl = document.getElementById("stat-chunks");

  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    const data = await res.json();
    if (data.status === "ok") {
      dot.className = "dot ok";
      statusText.lastChild.textContent = "Ready";
      chunksEl.textContent = data.chunks_indexed;
      manualsEl.textContent = "Indexed";
    } else {
      dot.className = "dot err";
      statusText.lastChild.textContent = "Not indexed yet";
      chunksEl.textContent = "0";
      manualsEl.textContent = "—";
    }
  } catch (e) {
    dot.className = "dot err";
    statusText.lastChild.textContent = "Backend offline";
    manualsEl.textContent = "—";
    chunksEl.textContent = "—";
  }
}

checkHealth();