import os
import requests
from datetime import datetime, timezone, timedelta
from scipy.stats import poisson

THE_ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SPORTS = [
    "soccer_japan_j_league",
    "soccer_korea_kleague1",
    "soccer_brazil_campeonato",
    "soccer_sweden_allsvenskan",
    "soccer_usa_mls",
    "soccer_australia_aleague",
]

TEAM_CN = {
    "Bucheon FC 1995": "富川1995",
    "FC Seoul": "首爾FC",
    "FC Anyang": "安養FC",
    "Gwangju FC": "光州FC",
    "Jeonbuk Hyundai Motors": "全北現代",
    "Daejeon Citizen": "大田市民",
    "Jeju United FC": "濟州聯",
    "Jeju United": "濟州聯",
    "Gangwon FC": "江原FC",
    "Ulsan Hyundai FC": "蔚山現代",
    "Ulsan HD": "蔚山現代",
    "Incheon United": "仁川聯",
    "Pohang Steelers": "浦項制鐵",
    "Suwon Samsung Bluewings": "水原三星",
    "Daegu FC": "大邱FC",
    "Gimcheon Sangmu": "金泉尚武",
    "Suwon FC": "水原FC",
}

LEAGUE_EXPECTED = {
    "K League 1": 2.60,
    "J1 League": 2.50,
    "Brazil Serie A": 2.75,
    "Allsvenskan": 2.70,
    "MLS": 2.85,
    "A-League": 2.65,
}

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("缺少 Telegram 設定")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=15)
        print("Telegram 狀態:", r.status_code)
    except Exception as e:
        print("Telegram 錯誤:", e)

def calc_poisson(expected, line=2.5):
    over = 1 - poisson.cdf(int(line), expected)
    under = poisson.cdf(int(line), expected)
    return over, under

def calc_ev(prob, odds):
    if not odds or odds <= 1:
        return 0.0
    return round((prob * (odds - 1) - (1 - prob)) * 100, 1)

def get_odds_for_sport(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": THE_ODDS_API_KEY,
        "regions": "eu,uk",
        "markets": "totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"{sport_key} 狀態: {r.status_code}")
        if r.status_code == 200:
            return r.json
