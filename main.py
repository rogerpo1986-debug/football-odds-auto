import os
import requests
from datetime import datetime
from scipy.stats import poisson

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TEAM_CN = {
    "Manchester United": "曼聯", "Liverpool": "利物浦", "Arsenal": "阿仙奴",
    "Chelsea": "車路士", "Manchester City": "曼城", "Tottenham": "熱刺",
    "Barcelona": "巴塞隆拿", "Real Madrid": "皇家馬德里", "Bayern Munich": "拜仁慕尼黑",
    "Juventus": "祖雲達斯", "Inter": "國際米蘭", "AC Milan": "AC米蘭",
    "Paris Saint Germain": "巴黎聖日耳門", "PSG": "巴黎聖日耳門",
}

def to_cn(name):
    return TEAM_CN.get(name, name)

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

def get_events():
    """優先抓澳洲 A-League，失敗就用 fallback"""
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/events",
            params={
                "apiKey": ODDS_API_KEY,
                "sport": "football",
                "league": "australia-a-league",
                "limit": 20,
                "status": "pending"
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            print(f"A-League 直接抓到 {len(data)} 場")
            if len(data) > 0:
                return data
    except Exception as e:
        print("A-League 直接抓失敗:", e)

    # Fallback
    return get_events_fallback()

def get_events_fallback():
    """抓全部再過濾澳洲相關"""
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/events",
            params={
                "apiKey": ODDS_API_KEY,
                "sport": "football",
                "
