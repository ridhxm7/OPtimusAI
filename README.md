# AI Chatbot - Flask + Gemini

A complete college/MCA-level AI chatbot web application using Flask, SQLite, HTML/CSS/JavaScript, and Google's Gemini API.

## Features
- Modern ChatGPT-style interface
- Gemini AI responses
- SQLite chat history
- Clear conversation
- Loading indicator
- Enter-to-send and Shift+Enter for a new line
- Responsive layout
- API key stored in `.env`
- Basic error handling

## Requirements
- Python 3.10+
- Internet connection
- A Gemini API key

## Setup - macOS/Linux

Open Terminal inside this project folder:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace:

```text
PASTE_YOUR_GEMINI_API_KEY_HERE
```

with your real API key.

Then run:

```bash
python3 app.py
```

Open:

http://127.0.0.1:5000

## Setup - Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Then open:

http://127.0.0.1:5000

## Important
Never upload `.env` or your real API key to GitHub.

If you get a Gemini model/API error, check the API key and set `GEMINI_MODEL` in `.env` to a model available to your API account.

## Project modules

- `app.py` - Flask server, API routes, SQLite storage, Gemini integration
- `templates/index.html` - chatbot UI
- `static/style.css` - UI styling
- `static/script.js` - frontend chat logic
- `chatbot.db` - created automatically when the app starts

## API endpoints

GET `/api/history`
Returns saved messages.

POST `/api/chat`
Body:
```json
{"message":"Hello"}
```

POST `/api/clear`
Deletes saved chat messages.
