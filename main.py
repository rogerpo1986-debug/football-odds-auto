import os
import requests
from datetime import datetime
from scipy.stats import poisson

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def to_cn(name):
    return name

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
            print("A-League 抓到", len(data), "場")
            if len(data) > 0:
                return data
    except Exception as e:
        print("A-League 失敗:", e)

    # fallback
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/events",
            params={
                "apiKey": ODDS_API_KEY,
                "sport": "football",
                "limit": 40,
                "status": "pending"
            },
            timeout=15
        )
        if r.status_code == 200:
            events = r.json()
            filtered = []
            for e in events:
                league_name = ""
                if isinstance(e.get("league"), dict):
                    league_name = (e["league"].get("name", "") + " " + e["league"].get("slug", "")).lower()
                if "australia" in league_name or "a-league" in league_name:
                    filtered.append(e)
            print("Fallback 有", len(filtered), "場")
            return filtered
    except Exception as e:
        print("Fallback 失敗:", e)
    return []

def get_odds(event_id):
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "eventId": event_id,
                "bookmakers": "Pinnacle,Bet365,Unibet,SingBet"
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("抓賠率失敗:", e)
    return None

def extract_ou_25(odds_data):
    if not odds_data or "bookmakers" not in odds_data:
        return None, None, None

    best_over = None
    best_under = None
    best_book = None

    for bookie, markets in odds_data.get("bookmakers", {}).items():
        for market in markets:
            name = str(market.get("name", "")).lower()
            if "total" in name or "over" in name or "under" in name:
                for odd in market.get("odds", []):
                    line = odd.get("hdp") or odd.get("max") or odd.get("point") or odd.get("total")
                    try:
                        if line is not None and abs(float(line) - 2.5) < 0.05:
                            over = float(odd.get("over", 0) or 0)
                            under = float(odd.get("under", 0) or 0)
                            if over > 1.01 and under > 1.01:
                                if best_over is None or over > best_over:
                                    best_over = over
                                    best_under = under
                                    best_book = bookie
                    except:
                        continue
    return best_over, best_under, best_book

def main():
    print("=== 開始 ===")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    events = get_events()
    message = "⚽ 阿晴 Value 分析報告\n時間: " + now + "\n\n"
    message += "✅ 抓到 " + str(len(events)) + " 場賽事\n\n"
    
    analyzed = 0
    value_count = 0
    
    for event in events[:8]:
        home = event.get("home", "Home")
        away = event.get("away", "Away")
        event_id = event.get("id")
        league = ""
        if isinstance(event.get("league"), dict):
            league = event["league"].get("name", "")
        
        expected = 2.55
        over_p, under_p = calc_poisson(expected)
        
        odds_data = get_odds(event_id) if event_id else None
        over_odds, under_odds, book = extract_ou_25(odds_data) if odds_data else (None, None, None)
        
        message += "📌 " + home + " vs " + away + "\n"
        if league:
            message += "聯賽: " + league + "\n"
        message += "預期總入: " + str(expected) + "\n"
        
        if over_odds and under_odds:
            over_ev = calc_ev(over_p, over_odds)
            under_ev = calc_ev(under_p, under_odds)
            message += "大球 " + str(round(over_p*100,1)) + "% | " + str(over_odds) + " (" + str(book) + ") | EV " + str(over_ev) + "\n"
            message += "小球 " + str(round(under_p*100,1)) + "% | " + str(under_odds) + " (" + str(book) + ") | EV " + str(under_ev) + "\n"
            if over_ev > 5 or under_ev > 5:
                message += "🔥 有 Value！\n"
                value_count += 1
            analyzed += 1
        else:
            message += "暫無 2.5 真實大細水\n"
        message += "\n"
    
    message += "成功分析真實賠率: " + str(analyzed) + " 場\n"
    message += "發現潛在 Value: " + str(value_count) + " 場\n"
    message += "阿晴繼續優化中"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
