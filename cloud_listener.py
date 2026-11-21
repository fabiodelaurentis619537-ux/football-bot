import asyncio
import os
import uvicorn
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from parser import parse_football_signal

API_ID = int(os.getenv("TELEGRAM_API_ID", "32460540"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "6264fe26dc85fdc4bca5bcf051af54e1")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "1BJWap1sBuzx2R5NYMlsZI6FqG88Tv1gAq7ylA5I5TNyvsxjQ5w5o6dmjotINV10FPjFF5pVr04u9G90GWpjefT9Vkobtvi6hWZ03p9UgXrfXb_BBXimLNNDqavG6FAqG-jwwJpSxBcpMfdmvVMMYHOG7NMpdvgHh95xXJFy7B-8TcfJAYaDTbN6N_5oRxaKBYTsmKaNq1ZK7iJxXet16GSWGhuPmlC1JIUz-rj5v0oXh11D8iPXZx38gwty1eqYI0UfA9AOGYJ8ykYxXbRsLK5ZP7xn90CeYISXFfCKiXJBwX3zE4qzgrVUZOfGDSzLZJwLrJKnzgXHz_bFMYtqSlIeL_WUPS5k=")

ALTERVISTA_URL = os.getenv("ALTERVISTA_URL", "https://meteocerignola.altervista.org/PROGRAVITA/RICEVI.php")

# FILTRI AMMESSI (solo a partita in corso)
ALLOWED_FILTERS = ["ESPERIMENTO", "GOLVEL1TULTRA", "VIADIMEZZO"]

# FILTRI ESCLUSI (quelli del 1' minuto)
BLOCKED_FILTERS = ["Sblocco", "SblHT"]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_telegram():
    print("[*] Attesa di sicurezza (15 secondi) per chiusura sessioni precedenti...", flush=True)
    await asyncio.sleep(15)

    print("[*] Connessione a Telegram in corso...", flush=True)
    try:
        await client.connect()
        is_auth = await client.is_user_authorized()
        print(f"[+] Connesso a Telegram con successo! Autorizzato: {is_auth}", flush=True)

        @client.on(events.NewMessage)
        async def handler(event):
            text = event.raw_text or ""
            if not text:
                return

            try:
                chat = await event.get_chat()
                chat_name = getattr(chat, 'title', None) or getattr(chat, 'username', None) or getattr(chat, 'first_name', 'Chat')
            except Exception:
                chat_name = "Chat"

            # 1. Scarta categoricamente se contiene i filtri del 1' minuto
            for blocked in BLOCKED_FILTERS:
                if blocked.lower() in text.lower():
                    print(f"[x] Scartato da [{chat_name}]: filtro escluso ({blocked})", flush=True)
                    return

            # 2. Controlla se è un messaggio di match alert valido
            is_match = "Live Match Alert" in text or "Dangerous Attacks" in text or "Over:" in text
            if not is_match:
                return

            # 3. Verifica che appartenga a uno dei filtri live ammessi
            has_allowed_filter = any(f.lower() in text.lower() for f in ALLOWED_FILTERS)
            if not has_allowed_filter:
                print(f"[x] Scartato da [{chat_name}]: non è tra i 4 filtri live ammessi", flush=True)
                return

            # Se ha superato tutti i controlli, è un segnale live valido!
            print(f"[!] SEGNALE LIVE VALIDO RILEVATO da [{chat_name}]!", flush=True)
            parsed = parse_football_signal(text)
            try:
                res = requests.post(ALTERVISTA_URL, json=parsed, timeout=10)
                print(f"[+] Inviato ad Altervista: {res.status_code} - {res.text}", flush=True)
            except Exception as e:
                print(f"[-] Errore invio ad Altervista: {e}", flush=True)

        await client.run_until_disconnected()
    except Exception as e:
        print(f"[-] Errore Telethon: {e}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_telegram())
    yield
    print("[*] Spegnimento container, disconnessione da Telegram...", flush=True)
    task.cancel()
    if client.is_connected():
        await client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {
        "status": "online",
        "altervista_url": ALTERVISTA_URL,
        "allowed_filters": ALLOWED_FILTERS,
        "blocked_filters": BLOCKED_FILTERS
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("cloud_listener:app", host="0.0.0.0", port=port)
