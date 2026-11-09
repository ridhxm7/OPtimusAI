import os
import json
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load API key directly from the .env file
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    override=True
)

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot.db")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


# Create database table
def init_db():

    with sqlite3.connect(DB_PATH) as con:

        con.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sources TEXT NOT NULL DEFAULT '[]'
            )
        """)

        # Add sources column to an existing database
        columns = [
            row[1] for row in con.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        ]

        if "sources" not in columns:
            con.execute(
                "ALTER TABLE messages ADD COLUMN sources TEXT NOT NULL DEFAULT '[]'"
            )

        con.commit()


# Retrieve previous messages
def get_history(limit=30):

    with sqlite3.connect(DB_PATH) as con:

        rows = con.execute(
            """SELECT role, content, created_at, sources
               FROM messages ORDER BY id DESC LIMIT ?""",
            (limit,)
        ).fetchall()

    history = []

    for row in reversed(rows):

        try:
            sources = json.loads(row[3])
        except (TypeError, json.JSONDecodeError):
            sources = []

        history.append({
            "role": row[0],
            "content": row[1],
            "created_at": row[2],
            "sources": sources
        })

    return history


# Save messages and their sources
def save_message(role, content, sources=None):

    with sqlite3.connect(DB_PATH) as con:

        con.execute(
            """INSERT INTO messages(role, content, created_at, sources)
               VALUES (?, ?, ?, ?)""",
            (
                role,
                content,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(sources or [])
            )
        )

        con.commit()
def ask_gemini(user_message, history):

    if not GEMINI_API_KEY:
        return "Gemini API key is not configured.", []

    try:
        from ddgs import DDGS
        from google import genai

    except ImportError as exc:
        print("Package error:", repr(exc))
        return "Required Python package is missing.", []

    # STEP 1: Search the web
    print("Searching the web...")
    try:

        results = DDGS(timeout=20).text(
            user_message,
            region="in-en",
            max_results=5,
            backend="auto"
        )
        print("Search successful!")
        print("Sources found:", len(results))
    except Exception as exc:
        print("Search error:", repr(exc))
        return (
            "Web search failed. Please try again.",
            []
        )

    if not results:

        return (
            "No search results found. Please rephrase your question.",
            []
        )

    sources = []
    search_information = ""

    # Collect search results
    for result in results:

        url = result.get("href", "")
        title = result.get("title", "Website")
        description = result.get("body", "")

        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https"):
            continue

        if not parsed_url.netloc:
            continue

        number = len(sources) + 1

        sources.append({
            "number": number,
            "title": title,
            "url": url
        })

        search_information += (
            f"\n[{number}] {title}\n"
            f"URL: {url}\n"
            f"Information: {description}\n"
        )

    if not sources:

        return (
            "I couldn't find reliable sources for this question.",
            []
        )

    print("Search completed. Sources found:", len(sources))

    # STEP 2: Prepare information for Gemini
    prompt = f"""
    You are a source-based chatbot.

    Use ONLY the following web search results to answer.

    Rules:
    1. Do not invent facts or use unsupported information.
    2. Prefer official websites, government sources,
       universities and trusted publications.
    3. Add source numbers like [1] after factual claims.
    4. If information is insufficient, say that
       the answer cannot be verified.
    5. Never invent website links or sources.

    WEB SEARCH RESULTS:

    {search_information}

    USER QUESTION:

    {user_message}
    """

    # STEP 3: Connect to Gemini
    print("Sending question to Gemini...")

    try:

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt)
        answer = response.text or ""

    except Exception as exc:

        print("Gemini API error:", repr(exc))

        return (
            "Gemini took too long to respond or encountered an API error. Please try again.",
            []
        )

    if not answer:

        return "Gemini could not generate an answer.", []

    print("Gemini response received.")

    # STEP 4: Check citations
    has_citation = any(
        f"[{source['number']}]" in answer
        for source in sources
    )

    if not has_citation:

        return (
            "I couldn't generate an answer with verifiable citations.",
            []
        )

    return answer.strip(), sources


# Display chatbot webpage
@app.route("/")
def index():
    return render_template("index.html")


# Retrieve previous conversation
@app.get("/api/history")
def history():
    return jsonify(get_history())


# Receive question and generate answer
@app.post("/api/chat")
def chat():

    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > 4000:
        return jsonify({
            "error": "Message is too long. Keep it under 4000 characters."
        }), 400

    old_history = get_history()

    save_message("user", message)

    answer, sources = ask_gemini(message, old_history)

    # Save answer and sources
    save_message("assistant", answer, sources)

    return jsonify({
        "reply": answer,
        "sources": sources
    })


# Clear conversation
@app.post("/api/clear")
def clear():

    with sqlite3.connect(DB_PATH) as con:

        con.execute("DELETE FROM messages")

        con.commit()

    return jsonify({"success": True})


if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )