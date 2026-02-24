## Bot Viewer (Prismarine Viewer)

This repo now includes a `viewer` Docker service using `prismarine-viewer` to watch a Mineflayer bot in your browser.

Start server + viewer:

```bash
docker compose up --build server viewer
```

Open:

```text
http://localhost:3000
```

If port `3000` is already in use, choose another host port:

```bash
VIEWER_HOST_PORT=3001 docker compose up --build server viewer
```
