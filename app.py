import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        con.commit()

def get_history(limit=30):
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT role, content, created_at FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in reversed(rows)]

def save_message(role, content):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO messages(role, content, created_at) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat(timespec="seconds"))
        )
        con.commit()

def ask_gemini(user_message, history):
    if not GEMINI_API_KEY:
        return (
            "Gemini API key is not configured. Add GEMINI_API_KEY to the .env file, "
            "restart the server, and try again."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        contents = []
        for item in history[-20:]:
            role = "model" if item["role"] == "assistant" else "user"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=item["content"])]
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        ))

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a helpful, friendly college-project chatbot. "
                    "Give clear, accurate answers. If the user asks for code, "
                    "format it clearly and explain important parts briefly."
                ),
                temperature=0.7,
                max_output_tokens=1200,
            ),
        )
        text = getattr(response, "text", None)
        if not text:
            return "I couldn't generate a response. Please try again."
        return text.strip()
    except Exception as exc:
        print("Gemini error:", repr(exc))
        return "Sorry, I couldn't connect to Gemini right now. Check your API key, internet connection, and model name."

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/history")
def history():
    return jsonify(get_history())

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Message is too long. Keep it under 4000 characters."}), 400

    history = get_history()
    save_message("user", message)
    answer = ask_gemini(message, history)
    save_message("assistant", answer)

    return jsonify({"reply": answer})

@app.post("/api/clear")
def clear():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM messages")
        con.commit()
    return jsonify({"success": True})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
