# Deploy Jarvis To Vercel

## What changed

This version of Jarvis is web-first.

- Commands like `google python`, `youtube lo-fi`, and `open github.com` now trigger browser actions.
- Memory and command history are stored in the browser with `localStorage`, so they work on Vercel without writing files on the server.
- Desktop-only actions like opening Notepad or closing local apps are intentionally not supported in the deployed web app.
- The interface is now built with React and compiled into `static/react`.

## Deploy steps

1. Install the Vercel CLI if needed:

```bash
npm i -g vercel
```

2. In this project folder, run:

```bash
npm install
npm run build
vercel
```

3. For production deployment:

```bash
npm run build
vercel --prod
```

## Supported web commands

- `open github.com`
- `open youtube`
- `google python flask tutorial`
- `youtube synthwave mix`
- `wikipedia alan turing`
- `weather in Delhi`
- `top news`
- `what is 24 multiplied by 8`
- `remember that ship on monday`
- `what do you remember`
- `system status`

## Important limitation

Vercel cannot control the user's computer, open local desktop apps, or kill Windows processes. That is why the deployed app focuses on browser-safe actions.
