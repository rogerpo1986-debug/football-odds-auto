import os
import requests
from datetime import datetime
from scipy.stats import poisson

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 常見隊中文映射（之後可以加多）
TEAM_CN = {
    "Manchester United": "曼聯",
    "Liverpool": "利物浦",
    "Arsenal": "阿仙奴",
    "Chelsea": "車路士",
    "Manchester City": "曼城",
    "Tottenham": "熱刺",
    "Barcelona": "巴塞隆拿",
    "Real Madrid": "皇家馬德里",
    "Bayern Munich": "拜仁慕尼黑",
    "Juventus": "祖雲達斯",
    "Inter": "國際米蘭",
    "AC Milan": "AC米蘭",
    "Paris Saint Germain": "巴黎聖日耳門",
    "PSG": "巴黎聖日耳門",
    "Newcastle United": "紐卡素",
    "Bournemouth": "般尼茅夫",
    "Konyaspor": "科尼亞士邦",
    "FC Zorya Luhansk": "佐里亞",
}

def to_cn(name):
    return TEAM_CN.get(name, name)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=15)
    except:
        pass

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
        r = requests.get("https://api.odds-api.io/v3/events",
                         params={"apiKey": ODDS_API_KEY, "sport": "football", "limit": 12},
                         timeout=15)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_odds(event_id):
    try:
        r = requests.get("https://api.odds-api.io/v3/odds",
                         params={"apiKey": ODDS_API_KEY, "eventId": event_id,
                                 "bookmakers": "Pinnacle,Bet365,SingBet,Unibet"},
                         timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def extract_ou_25(odds_data):
    if not odds_data or "bookmakers" not in odds_data:
        return None, None
    for bookie, markets in odds_data.get("bookmakers", {}).items():
        for market in markets:
            name = str(market.get("name", "")).lower()
            if "total" in name or "over" in name or "under" in name:
                for odd in market.get("odds", []):
                    line = odd.get("hdp") or odd.get("max") or odd.get("point") or odd.get("total")
                    try:
                        if abs(float(line) - 2.5) < 0.01:
                            over = float(odd.get("over", 0))
                            under = float(odd.get("under", 0))
                            if over > 1.01 and under > 1.01:
                                return over, under
                    except:
                        continue
    return None, None

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message = f"""⚽ <b>阿晴 Value 分析報告</b>
時間: {now}

"""
    events = get_events()
    message += f"✅ 抓到 <b>{len(events)}</b> 場賽事\n\n"
    
    analyzed = 0
    for event in events[:6]:
        home = event.get("home", "Home")
        away = event.get("away", "Away")
        event_id = event.get("id")
        league = event.get("league", {}).get("name", "") if isinstance(event.get("league"), dict) else ""
        
        home_cn = to_cn(home)
        away_cn = to_cn(away)
        
        expected = 2.55  # 暫時固定，之後用真實數據
        over_p, under_p = calc_poisson(expected)
        
        odds_data = get_odds(event_id) if event_id else None
        over_odds, under_odds = extract_ou_25(odds_data) if odds_data else (None, None)
        
        message += f"📌 <b>{home_cn} vs {away_cn}</b>\n"
        if league:
            message += f"聯賽: {league}\n"
        message += f"預期總入: {expected:.2f}\n"
        
        if over_odds and under_odds:
            over_ev = calc_ev(over_p, over_odds)
            under_ev = calc_ev(under_p, under_odds)
            message += f"大球 {over_p*100:.1f}% | 真實賠率 {over_odds:.2f} | EV {over_ev:+.1f}\n"
            message += f"小球 {under_p*100:.1f}% | 真實賠率 {under_odds:.2f} | EV {under_ev:+.1f}\n"
            analyzed += 1
        else:
            message += f"大球 {over_p*100:.1f}% | 小球 {under_p*100:.1f}% （暫無真實2.5賠率）\n"
        message += "\n"
    
    message += f"成功用真實賠率: {analyzed} 場\n"
    message += "（expected 暫時固定，中文隊名常見隊會轉）\n"
    message += "阿晴繼續優化 ♡"
    
    send_telegram(message)
    print("完成")

if __name__ == "__main__":
    main()
