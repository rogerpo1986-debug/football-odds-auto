import os
import requests
import json
from datetime import datetime
import time

# ========== 設定 ==========
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")  # 之後會加

# 想監控嘅聯賽（之後可以加多）
TARGET_LEAGUES = [
    "japan-j1-league",
    "south-korea-k-league-1",
    "brazil-serie-a",
]

def send_telegram(message):
    """發送訊息到 Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("沒有 TELEGRAM_BOT_TOKEN")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID or "你的ChatID",  # 暫時
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
        print("Telegram 訊息已發送")
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

def get_football_events():
    """從 odds-api.io 攞足球賽事"""
    url = "https://api.odds-api.io/v3/events"
    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "limit": 20
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"API 錯誤: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print(f"抓取賽事失敗: {e}")
        return []

def main():
    print(f"=== 阿晴足球 Value 分析開始 ===")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not ODDS_API_KEY:
        print("錯誤：沒有 ODDS_API_KEY")
        return
    
    events = get_football_events()
    print(f"成功攞到 {len(events)} 場賽事")
    
    # 暫時簡單輸出
    message = f"⚽ 阿晴 Value 分析報告\n時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    message += f"成功連接到 Odds API！\n抓到 {len(events)} 場足球賽事。\n\n"
    message += "系統運作正常！之後會加入完整 Poisson + EV 計算。"
    
    print(message)
    # send_telegram(message)  # 暫時關閉，等 Chat ID 先開
    
    print("=== 分析完成 ===")

if __name__ == "__main__":
    main()
