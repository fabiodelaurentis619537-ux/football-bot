# parser.py
import re

def parse_football_signal(text: str) -> dict:
    """
    Estrae tutte le statistiche, squadre, quote e punteggio
    dal messaggio Telegram del bot di alert.
    """
    data = {
        "raw_text": text,
        "filter": None,
        "league": None,
        "home_team": None,
        "away_team": None,
        "home_rank": None,
        "away_rank": None,
        "minute": None,
        "score_home": None,
        "score_away": None,
        "market": "First Half Goals 0.5",
        "odds_over": None,
        "odds_under": None,
        "odds_1_start": None,
        "odds_x_start": None,
        "odds_2_start": None,
        "odds_1_live": None,
        "odds_x_live": None,
        "odds_2_live": None,
        "shots_on_home": 0,
        "shots_off_home": 0,
        "shots_on_away": 0,
        "shots_off_away": 0,
        "corners_home": 0,
        "corners_away": 0,
        "attacks_home": 0,
        "attacks_away": 0,
        "possession_home": 50,
        "possession_away": 50
    }

    # 1. Filtro
    m = re.search(r"Filter:\s*([^\n\r]+)", text, re.IGNORECASE)
    if m:
        data["filter"] = m.group(1).strip()

    # 2. Campionato / Nazione
    m = re.search(r"(?:[^\w\n\r]*)([A-Za-z\s]+:-\s*[^\n\r]+)", text)
    if m:
        data["league"] = m.group(1).strip()

    # 3. Squadre e ranking es: Al Jazira U19 (4) 🆚 Ajman U19 (11)
    m = re.search(r"([^\n\r]+?)(?:\s*\((\d+)\))?\s*🆚\s*([^\n\r]+?)(?:\s*\((\d+)\))?(?:\r?\n|$)", text)
    if m:
        data["home_team"] = m.group(1).strip()
        data["home_rank"] = m.group(2) if m.group(2) else None
        data["away_team"] = m.group(3).strip()
        data["away_rank"] = m.group(4) if m.group(4) else None

    # 4. Minuto e Punteggio: ⏱ 18' | ⚽️ 0–0
    m = re.search(r"⏱\s*(\d+)['\s]*\|\s*⚽️?\s*(\d+)[\s–\-]+(\d+)", text)
    if m:
        data["minute"] = int(m.group(1))
        data["score_home"] = int(m.group(2))
        data["score_away"] = int(m.group(3))

    # 5. Over / Under (First Half Goals)
    m = re.search(r"Over:\s*([\d\.]+)\s*\|\s*Under:\s*([\d\.]+)", text, re.IGNORECASE)
    if m:
        data["odds_over"] = float(m.group(1))
        data["odds_under"] = float(m.group(2))

    # 6. Quote Bet365 Start & Live: Start :- 1.53 | 4.50 | 4.20
    m = re.search(r"Start\s*:-\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)", text)
    if m:
        data["odds_1_start"] = float(m.group(1))
        data["odds_x_start"] = float(m.group(2))
        data["odds_2_start"] = float(m.group(3))

    m = re.search(r"Live\s*:-\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)", text)
    if m:
        data["odds_1_live"] = float(m.group(1))
        data["odds_x_live"] = float(m.group(2))
        data["odds_2_live"] = float(m.group(3))

    # 7. Tiri: 🏠 0 : 2 | 🛫 0 : 1
    m = re.search(r"🏠\s*(\d+)\s*:\s*(\d+)\s*\|\s*🛫\s*(\d+)\s*:\s*(\d+)", text)
    if m:
        data["shots_on_home"] = int(m.group(1))
        data["shots_off_home"] = int(m.group(2))
        data["shots_on_away"] = int(m.group(3))
        data["shots_off_away"] = int(m.group(4))

    # 8. Corner: 🏠 2 | 🛫 0
    # Cerchiamo dopo la parola Corners
    corners_block = re.search(r"Corners[\s\S]*?🏠\s*(\d+)\s*\|\s*🛫\s*(\d+)", text, re.IGNORECASE)
    if corners_block:
        data["corners_home"] = int(corners_block.group(1))
        data["corners_away"] = int(corners_block.group(2))

    # 9. Attacchi pericolosi: 🏠 11 | 🛫 4
    attacks_block = re.search(r"Dangerous Attacks[\s\S]*?🏠\s*(\d+)\s*\|\s*🛫\s*(\d+)", text, re.IGNORECASE)
    if attacks_block:
        data["attacks_home"] = int(attacks_block.group(1))
        data["attacks_away"] = int(attacks_block.group(2))

    # 10. Possesso: 🏠 82 | 🛫 18
    poss_block = re.search(r"Possession[\s\S]*?🏠\s*(\d+)\s*\|\s*🛫\s*(\d+)", text, re.IGNORECASE)
    if poss_block:
        data["possession_home"] = int(poss_block.group(1))
        data["possession_away"] = int(poss_block.group(2))

    return data
