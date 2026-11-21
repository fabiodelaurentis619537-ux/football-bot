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
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "1BJWap1sBu7fJt4a5_tQtd9FWYEEweb_5njOWZFBUyJJTt_CPxfQotiQKJLdjs-6yCbJKTV2uJkTPQLZ4JjY_4l7FFA_P3lqWR5Wf7RA1zkdY7W9qH5lC70JyKKseInXNzudev8en6yCNGVXgWqG_nKYrMevsTvW9_VOS55Nfx-jhRzO6fTT4x-CmoMImTtRqpdVeLHnyPI5j2IuXcYFb5U_CH59WfA4Uq2OTFbhandHp_EGvvs49mJEs4aHKKjCQghhw0SWJewyP900jLfSTFKh3Zs-MTgb2vUjkMFU_4Xya5Z4Aiufy3m1GigtP9-tfCaJcqMjdnfGfG2lYG8jIyh1meVeiHCs=")

ALTERVISTA_URL = os.getenv("ALTERVISTA_URL", "https://meteocerignola.altervista.org/PROGRAVITA/RICEVI.php")

# FILTRI AMMESSI (solo partite in corso)
ALLOWED_FILTERS = ["ESPERIMENTO", "GOLVEL1TULTRA", "VIADIMEZZO"]

# FILTRI BLOCCATI (del 1' minuto)
BLOCKED_FILTERS = ["Sblocco", "SblHT"]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_telegram():
    print("[*] Attesa di sicurezza (15 secondi)...", flush=True)
    await asyncio.sleep(15)

    print("[*] Connessione a Telegram in corso...", flush=True)
    try:
        await client.connect()
        is_auth = await client.is_user_authorized()
        print(f"[+] Connesso con successo a Telegram! Autorizzato: {is_auth}", flush=True)

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

            # 1. Scarta se contiene i filtri del 1' minuto
            for blocked in BLOCKED_FILTERS:
                if blocked.lower() in text.lower():
                    print(f"[x] Scartato da [{chat_name}]: filtro escluso ({blocked})", flush=True)
                    return

            # 2. Controlla se è un messaggio di match alert
            is_match = "Live Match Alert" in text or "Dangerous Attacks" in text or "Over:" in text
            if not is_match:
                return

            # 3. Verifica se appartiene a uno dei filtri live ammessi
            has_allowed_filter = any(f.lower() in text.lower() for f in ALLOWED_FILTERS)
            if not has_allowed_filter:
                print(f"[x] Scartato da [{chat_name}]: non appartiene ai filtri live ammessi", flush=True)
                return

            print(f"[!] SEGNALE CALCIO RILEVATO da [{chat_name}]!", flush=True)
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
    print("[*] Spegnimento container, disconnessione pulita da Telegram...", flush=True)
    task.cancel()
    if client.is_connected():
        await client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {
        "status": "online",
        "altervista_url": ALTERVISTA_URL,
        "connected": client.is_connected()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("cloud_listener:app", host="0.0.0.0", port=port)
