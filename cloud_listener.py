# cloud_listener.py
import asyncio
import os
import uvicorn
import requests
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from parser import parse_football_signal

# Configurazioni da variabili d'ambiente (o valori di default)
API_ID = int(os.getenv("TELEGRAM_API_ID", "32460540"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "6264fe26dc85fdc4bca5bcf051af54e1")
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "1BJWap1sBu1iP0muFkdzEylLHw6IKQRk2s5LoIotc33k7q121xjn0tBzXajTogij-3qxNRtibNbzetXRkVZp2OgPavL9HXntwGvwa4EWSsxc6UV54Ovff1kcNAUzBqXVbv4-TjtyujppDO137neiluGmS-pQqNTUZ4kNvxNdZCyijpk4XzvNscR6exLalSIVrmFiCJgEA4GLkvHExgP8gGLDYGwlfI9JXw6D0rW5xXK_ezBpQCSyHqZlEyIfcBkIpnojHPk9JHscrxzrtjl2-NHsxHYWbQRATkIrEDY8Y7RZsPkMVVrvIS7v_zZmdhP_09IcNp49vTK6cmHKlBXj_7z_YMpOevmU=")

# URL del tuo Altervista dove inviare i dati
ALTERVISTA_URL = os.getenv("ALTERVISTA_URL", "https://meteocerignola.altervista.org/ricevi.php")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "segreto_calcio_2026")

# Chat target opzionale (lasciare vuoto per ascoltare tutte o impostare il nome/username del bot)
TARGET_CHAT = os.getenv("TARGET_CHAT", "")

# Server web fittizio per soddisfare il free-tier di Render/Koyeb
app = FastAPI()

@app.get("/")
def home():
    return {"status": "online", "message": "Telegram Football Cloud Listener è attivo 24/7!"}

async def start_telegram():
    if not SESSION_STRING:
        print("[!] ATTENZIONE: TELEGRAM_SESSION non impostata. Il listener non può connettersi.")
        return

    print("[*] Avvio connessione Telethon con Session String...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("[+] Connesso con successo a Telegram 24/7!")

    @client.on(events.NewMessage)
    async def handler(event):
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', '') or ''
        chat_username = getattr(chat, 'username', '') or ''

        if TARGET_CHAT and (TARGET_CHAT not in chat_title) and (TARGET_CHAT not in chat_username):
            return

        text = event.raw_text or ""
        # Verifica parole chiave del segnale calcio
        if "Live Match Alert" in text or "Dangerous Attacks" in text or "Over:" in text:
            print(f"[!] Ricevuto segnale per: {text.splitlines()[2] if len(text.splitlines()) > 2 else 'Match'}")
            parsed = parse_football_signal(text)

            # Invia i dati ad Altervista
            try:
                res = requests.post(
                    ALTERVISTA_URL,
                    json=parsed,
                    headers={"X-Auth-Token": SECRET_TOKEN},
                    timeout=10
                )
                print(f"[+] Dati inviati ad Altervista: {res.status_code}")
            except Exception as e:
                print(f"[-] Errore invio ad Altervista: {e}")

    await client.run_until_disconnected()

@app.on_event("startup")
def startup():
    asyncio.create_task(start_telegram())

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("cloud_listener:app", host="0.0.0.0", port=port)
