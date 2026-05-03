# Deploy Jarvis To Vercel

## Current setup

This project is ready for Vercel as a web-first Flask app with a React frontend.

- Flask serves the app from `app.py`
- React is built into `public/react`
- Browser memory and history use `localStorage`
- Desktop-only actions are converted into web-safe fallbacks where possible

## Before you deploy

Build the frontend once so the latest React files are committed:

```bash
npm install
npm run build
```

## Deploy from GitHub

1. Push the latest code to GitHub.
2. In Vercel, choose `Add New Project`.
3. Import the GitHub repo: `Opsitsansh/jarvis-web`.
4. Keep the project root as the repo root.
5. Deploy.

Vercel should detect the Python app automatically from `app.py`.

## Optional environment variables

Add this only if you want real AI answers:

```bash
OPENAI_API_KEY=your_key_here
```

Optional model override:

```bash
OPENAI_MODEL=gpt-5.2
```

## Supported web features

- natural question prompts
- Google, YouTube, Wikipedia, and website actions
- weather, news, time, and date
- cricket score lookup
- browser memory and recent history
- calculations, dice, and coin flip
- optional AI answers when API key is configured

## Important limitation

Vercel cannot control a user's PC, open local desktop apps, close system apps, or act like a Windows-level assistant. This project is designed as a polished browser-based Jarvis experience for resume/demo use.
