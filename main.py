import os
import requests
from datetime import datetime

# ========== 設定 ==========
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """發送訊息到 Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print("Telegram 訊息發送成功！")
            return True
        else:
            print(f"Telegram 發送失敗: {r.text}")
            return False
    except Exception as e:
        print(f"Telegram 錯誤: {e}")
        return False

def get_football_events():
    """從 odds-api.io 攞足球賽事"""
    url = "https://api.odds-api.io/v3/events"
    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "limit": 15
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"API 錯誤: {r.status_code}")
            return []
    except Exception as e:
        print(f"抓取失敗: {e}")
        return []

def main():
    print("=== 阿晴足球 Value 分析開始 ===")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not ODDS_API_KEY:
        print("錯誤：沒有 ODDS_API_KEY")
        return
    
    events = get_football_events()
    print(f"成功攞到 {len(events)} 場賽事")
    
    # 組裝訊息
    message = f"""⚽ <b>阿晴 Value 分析報告</b>
時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ 系統運作正常！
成功連接到 Odds API
今次抓到 <b>{len(events)}</b> 場足球賽事

之後會加入完整 Poisson + EV 計算 + 2串1 分析。
而家係測試階段。"""
    
    print(message)
    send_telegram(message)
    print("=== 分析完成 ===")

if __name__ == "__main__":
    main()
