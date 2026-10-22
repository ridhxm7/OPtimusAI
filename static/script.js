// Get the HTML elements that the JavaScript will control
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const clearButton = document.getElementById("clearChat");
const newChatButton = document.getElementById("newChat");

function removeWelcome() {
  const welcome = document.getElementById("welcome");
  if (welcome) welcome.remove();
}

function addMessage(role, text) {
  removeWelcome();

  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "YOU" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return row;
}

function setLoading(loading) {
  sendButton.disabled = loading;
  input.disabled = loading;
  sendButton.textContent = loading ? "…" : "➤";
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const history = await response.json();
    if (history.length) {
      removeWelcome();
      history.forEach(m => addMessage(m.role, m.content));
    }
  } catch (e) {
    console.error(e);
  }
}

async function sendMessage(text) {
  text = text.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";
  input.style.height = "auto";
  setLoading(true);

  const typing = document.createElement("div");
  typing.className = "message-row assistant";
  typing.innerHTML = '<div class="avatar">AI</div><div class="bubble typing">Thinking…</div>';
  messagesEl.appendChild(typing);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await response.json();
    typing.remove();

    if (!response.ok) {
      addMessage("assistant", data.error || "Something went wrong.");
    } else {
      addMessage("assistant", data.reply);
    }
  } catch (e) {
    typing.remove();
    addMessage("assistant", "Unable to reach the server. Make sure Flask is running.");
  } finally {
    setLoading(false);
    input.focus();
  }
}

form.addEventListener("submit", e => {
  e.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
});

document.querySelectorAll(".suggestions button").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.textContent));
});

async function clearConversation() {
  if (!confirm("Clear the entire conversation?")) return;
  await fetch("/api/clear", {method: "POST"});
  messagesEl.innerHTML = `
    <div id="welcome" class="welcome">
      <div class="welcome-icon">✦</div>
      <h2>How can I help you?</h2>
      <p>Ask me anything about programming, studies, projects, or general topics.</p>
    </div>`;
}

clearButton.addEventListener("click", clearConversation);
newChatButton.addEventListener("click", clearConversation);

loadHistory();
input.focus();
