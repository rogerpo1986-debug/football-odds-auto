import os
import requests
from datetime import datetime
from scipy.stats import poisson

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("缺少 TELEGRAM 設定")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
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
        return 0
    return round((prob * (odds - 1) - (1 - prob)) * 100, 1)

def main():
    print("=== 開始分析 ===")
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    message = f"""⚽ <b>阿晴 Value 分析報告</b>
時間: {now}

"""
    
    # 抓賽事
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/events",
            params={"apiKey": ODDS_API_KEY, "sport": "football", "limit": 8},
            timeout=15
        )
        events = r.json() if r.status_code == 200 else []
    except:
        events = []
    
    message += f"✅ 成功抓到 <b>{len(events)}</b> 場足球賽事\n\n"
    
    if not events:
        message += "暫時無賽事數據，下個鐘再試。"
        send_telegram(message)
        return
    
    # 示範分析前幾場（用固定 expected 做測試）
    for i, event in enumerate(events[:5]):
        home = event.get("home", "主隊")
        away = event.get("away", "客隊")
        league = event.get("league", {}).get("name", "") if isinstance(event.get("league"), dict) else ""
        
        # 示範 expected total（之後會改真實）
        expected = 2.60 + (i * 0.1)
        
        over_p, under_p = calc_poisson(expected)
        
        # 示範賠率（之後會抓真實）
        over_odds = 1.90
        under_odds = 1.95
        
        over_ev = calc_ev(over_p, over_odds)
        under_ev = calc_ev(under_p, under_odds)
        
        message += f"📌 <b>{home} vs {away}</b>\n"
        if league:
            message += f"聯賽: {league}\n"
        message += f"預期總入球: {expected:.2f}\n"
        message += f"大球概率 {over_p*100:.1f}% | EV {over_ev:+.1f}\n"
        message += f"小球概率 {under_p*100:.1f}% | EV {under_ev:+.1f}\n\n"
    
    message += "（而家用示範數據測試系統運作）\n"
    message += "阿晴會繼續優化真實賠率抓取 ♡"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
