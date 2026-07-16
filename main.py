import os
import requests
from datetime import datetime
from scipy.stats import poisson

# ========== 設定 ==========
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("缺少 TELEGRAM 設定")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 200:
            print("Telegram 發送成功！")
            return True
        else:
            print(f"Telegram 失敗: {r.text}")
            return False
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def calculate_over_under_prob(expected_total, line=2.5):
    over_prob = 1 - poisson.cdf(int(line), expected_total)
    under_prob = poisson.cdf(int(line), expected_total)
    return over_prob, under_prob

def calculate_ev(prob, odds):
    if odds <= 1:
        return -100
    return (prob * (odds - 1) * 100) - ((1 - prob) * 100)

def get_events():
    url = "https://api.odds-api.io/v3/events"
    params = {
        "apiKey": ODDS_API_KEY,
        "sport": "football",
        "limit": 10
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []

def get_odds_for_event(event_id):
    url = "https://api.odds-api.io/v3/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "eventId": event_id,
        "bookmakers": "Pinnacle,Bet365,SingBet"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def main():
    print("=== 阿晴足球 Value 分析開始 ===")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not ODDS_API_KEY:
        print("錯誤：沒有 ODDS_API_KEY")
        return
    
    events = get_events()
    print(f"成功攞到 {len(events)} 場賽事")
    
    message = f"""⚽ <b>阿晴 Value 分析報告</b>
時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ 系統正常
抓到 <b>{len(events)}</b> 場足球賽事

"""
    
    analyzed = 0
    for event in events[:4]:
        home = event.get("home", "Home")
        away = event.get("away", "Away")
        event_id = event.get("id")
        
        if not event_id:
            continue
            
        odds_data = get_odds_for_event(event_id)
        if not odds_data:
            continue
            
        # 暫時用示範 expected total（之後會換成真實數據）
        expected_total = 2.65
        
        over_prob, under_prob = calculate_over_under_prob(expected_total, 2.5)
        
        over_odds = None
        under_odds = None
        
        bookmakers = odds_data.get("bookmakers", {})
        for bookie, markets in bookmakers.items():
            for market in markets:
                if market.get("name") in ["Totals", "Over/Under", "Goals Over/Under"]:
                    for odd in market.get("odds", []):
                        if str(odd.get("hdp")) == "2.5" or str(odd.get("point")) == "2.5":
                            try:
                                over_odds = float(odd.get("over", 0))
                                under_odds = float(odd.get("under", 0))
                            except:
                                pass
                            break
            if over_odds:
                break
        
        if over_odds and under_odds and over_odds > 1 and under_odds > 1:
            over_ev = calculate_ev(over_prob, over_odds)
            under_ev = calculate_ev(under_prob, under_odds)
            
            message += f"📌 <b>{home} vs {away}</b>\n"
            message += f"預期總入: {expected_total:.2f}\n"
            message += f"大球: {over_prob*100:.1f}% | 賠率 {over_odds:.2f} | EV {over_ev:+.1f}\n"
            message += f"小球: {under_prob*100:.1f}% | 賠率 {under_odds:.2f} | EV {under_ev:+.1f}\n\n"
            analyzed += 1
    
    if analyzed == 0:
        message += "今次未搵到適合分析嘅比賽（可能 API 暫時無 Over/Under 數據）。\n系統仍然正常。"
    else:
        message += f"成功分析 {analyzed} 場。\n（而家用示範數據，之後會換成真實球隊 expected goals）"
    
    message += "\n\n阿晴繼續優化中 ♡"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
