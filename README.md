# Food Verse AI — Multimodal Food Intelligence Agent

A beginner-friendly React + FastAPI starter project inspired by the provided project brief. It includes five modules: food recognition/nutrition, freshness guidance, hygiene inspection, recipe generation, and personalized meal planning.

## Requirements
- Windows 10/11
- Python 3.12.x (Python 3.12.10 is fine)
- Node.js 20 or newer (LTS recommended)
- VS Code
- Optional: a Groq API key for live AI responses (https://console.groq.com/keys)

## Quick start (Windows)
1. Extract `food-verse-ai.zip` to a folder such as `C:\Users\YOUR_NAME\Downloads\food-verse-ai`.
2. Open that folder in VS Code: **File → Open Folder**.
3. Open **Terminal → New Terminal**. Make sure the terminal is at the project root (where `README.md` is located).
4. Run these commands one at a time:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

5. (Optional but recommended for AI) Open `backend/.env`, paste your Groq API key after `GROQ_API_KEY=`, and save it. Do not share this key or commit it to GitHub.
6. Start the backend in this terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

7. Open a **second terminal** in VS Code and run:

```powershell
cd frontend
npm install
npm run dev
```

8. Open the local URL Vite prints, usually `http://localhost:5173`.

## If PowerShell blocks activation
You do **not** need to activate the virtual environment. The commands above call `.venv\Scripts\python.exe` directly, which avoids the PowerShell execution-policy issue you encountered.

## AI mode and limitations
- Without `GROQ_API_KEY`, the app runs in **Demo mode** and returns clearly labelled sample responses so you can test the interface.
- With a valid Groq API key, supported text and image tasks use the configured Groq vision-capable model. Model availability may change; if the selected model is unavailable for your account, update `GROQ_MODEL` in `backend/.env` to a vision-capable model available in your Groq console.
- Food calorie and nutrition values are estimates, not medical advice. Image-only freshness checks cannot prove that food is safe to eat. Hygiene monitoring is a prototype, not a certified compliance system.

## Project structure
```text
food-verse-ai/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       └── styles.css
├── .gitignore
└── README.md
```

## Troubleshooting
- **`ModuleNotFoundError: backend`**: run Uvicorn from the project root, not from `frontend` or `backend`.
- **Port 8000 is busy**: stop the old server with `Ctrl+C`, or use `--port 8001` and change `API_BASE` in `frontend/src/App.jsx`.
- **`npm` is not recognized**: install Node.js LTS, then close and reopen VS Code.
- **AI returns a key/model error**: check `backend/.env`, confirm the key is valid, and confirm `GROQ_MODEL` is available to your account.
