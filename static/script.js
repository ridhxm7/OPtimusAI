// Get HTML elements
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const clearButton = document.getElementById("clearChat");
const newChatButton = document.getElementById("newChat");


// Remove welcome screen
function removeWelcome() {

    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }
}


// Display messages and sources
function addMessage(role, text, sources = []) {

    removeWelcome();

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "YOU" : "AI";

    const messageBody = document.createElement("div");

    messageBody.style.display = "flex";
    messageBody.style.flexDirection = "column";
    messageBody.style.gap = "8px";
    messageBody.style.minWidth = "0";
    messageBody.style.maxWidth = "min(760px, 78%)";

    if (role === "assistant") {
        messageBody.style.flex = "1";
    }

    // Display answer
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    bubble.style.maxWidth = "100%";

    messageBody.appendChild(bubble);

    // Display sources below the answer
    if (role === "assistant" && sources.length > 0) {

        const sourceBox = document.createElement("div");

        sourceBox.style.fontSize = "13px";
        sourceBox.style.display = "flex";
        sourceBox.style.flexDirection = "column";
        sourceBox.style.gap = "5px";

        const heading = document.createElement("strong");
        heading.textContent = "Sources:";

        sourceBox.appendChild(heading);

        sources.forEach(source => {

            const link = document.createElement("a");

            link.href = source.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";

            link.textContent =
                `[${source.number}] ${source.title}`;

            sourceBox.appendChild(link);

        });

        messageBody.appendChild(sourceBox);
    }

    row.appendChild(avatar);
    row.appendChild(messageBody);

    messagesEl.appendChild(row);

    messagesEl.scrollTop = messagesEl.scrollHeight;
}


// Loading button
function setLoading(loading) {

    sendButton.disabled = loading;
    input.disabled = loading;

    sendButton.textContent = loading ? "…" : "➤";
}


// Load previous messages
async function loadHistory() {

    try {

        const response = await fetch("/api/history");

        const history = await response.json();

        if (history.length) {

            removeWelcome();

            history.forEach(message => {

                addMessage(
                    message.role,
                    message.content,
                    message.sources || []
                );

            });
        }

    } catch (e) {

        console.error(e);

    }
}


// Send message to Flask
async function sendMessage(text) {

    text = text.trim();

    if (!text) return;

    addMessage("user", text);

    input.value = "";
    input.style.height = "auto";

    setLoading(true);

    const typing = document.createElement("div");

    typing.className = "message-row assistant";

    typing.innerHTML =
        '<div class="avatar">AI</div><div class="bubble typing">Searching...</div>';

    messagesEl.appendChild(typing);

    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text
            })

        });

        const data = await response.json();

        typing.remove();

        if (!response.ok) {

            addMessage(
                "assistant",
                data.error || "Something went wrong."
            );

        } else {

            addMessage(
                "assistant",
                data.reply,
                data.sources || []
            );

        }

    } catch (e) {

        typing.remove();

        addMessage(
            "assistant",
            "Unable to reach the server. Make sure Flask is running."
        );

    } finally {

        setLoading(false);

        input.focus();
    }
}


// Submit message
form.addEventListener("submit", e => {

    e.preventDefault();

    sendMessage(input.value);

});


// Enter to send message
input.addEventListener("keydown", e => {

    if (e.key === "Enter" && !e.shiftKey) {

        e.preventDefault();

        form.requestSubmit();

    }

});


// Automatically adjust textarea
input.addEventListener("input", () => {

    input.style.height = "auto";

    input.style.height =
        Math.min(input.scrollHeight, 150) + "px";

});


// Suggested questions
document.querySelectorAll(".suggestions button").forEach(button => {

    button.addEventListener("click", () => {

        sendMessage(button.textContent);

    });

});


// Clear conversation
async function clearConversation() {

    if (!confirm("Clear the entire conversation?")) return;

    await fetch("/api/clear", {
        method: "POST"
    });

    messagesEl.innerHTML = `
        <div id="welcome" class="welcome">
            <div class="welcome-icon">✦</div>
            <h2>How can I help you?</h2>
            <p>Ask me anything about programming, studies, projects, or general topics.</p>
        </div>
    `;
}


clearButton.addEventListener("click", clearConversation);

newChatButton.addEventListener("click", clearConversation);


// Start chatbot
loadHistory();

input.focus();