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

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_telegram():
    # Attesa di sicurezza per permettere al vecchio server di disconnettersi completamente
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

            print(f"[DEBUG] Ricevuto da [{chat_name}]: {text[:35].strip()}...", flush=True)

            if "Live Match Alert" in text or "Dangerous Attacks" in text or "Over:" in text:
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
        "telegram_connected": client.is_connected()
    }

@app.get("/test")
def test_send():
    sample_text = """⚽️ Live Match Alert – Filter: VIADIMEZZO2,0
🇦🇪   United Arab Emirates :- U19 League
Al Jazira U19 (4) 🆚 Ajman U19 (11)
⏱ 18' | ⚽️ 0–0

⚽ First Half Goals 0.5 (Live)
Over: 1.4 | Under: 2.75

💰 Odds (Bet365) - Home | Draw | Away
Start :- 1.53 | 4.50 | 4.20
Live :- 1.44 | 4.50 | 6.00

🎯 Shots (On : Off)
🏠 0 : 2 | 🛫 0 : 1

🏁 Corners
🏠 2 | 🛫 0

⚡️ Dangerous Attacks
🏠 11 | 🛫 4

📊 Possession
🏠 82 | 🛫 18"""
    parsed = parse_football_signal(sample_text)
    try:
        res = requests.post(ALTERVISTA_URL, json=parsed, timeout=10)
        return {"status": "ok", "altervista_code": res.status_code, "altervista_response": res.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("cloud_listener:app", host="0.0.0.0", port=port)
