from fastapi import FastAPI
import socket

app = FastAPI()

# Identify which container is responding
HOSTNAME = socket.gethostname()

@app.get("/heartbeat")
def heartbeat():
    return {"status": "alive", "server": HOSTNAME}

@app.get("/{key}")
def handle_key(key: str):
    return {
        "message": f"Key '{key}' was handled by server {HOSTNAME}"
    }
