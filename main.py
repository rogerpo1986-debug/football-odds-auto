import os
import requests
from datetime import datetime
from scipy.stats import poisson

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 常見中文隊名（之後可繼續加）
TEAM_CN = {
    "Manchester United": "曼聯", "Liverpool": "利物浦", "Arsenal": "阿仙奴",
    "Chelsea": "車路士", "Manchester City": "曼城", "Tottenham": "熱刺",
    "Barcelona": "巴塞隆拿", "Real Madrid": "皇家馬德里", "Bayern Munich": "拜仁慕尼黑",
    "Juventus": "祖雲達斯", "Inter": "國際米蘭", "AC Milan": "AC米蘭",
    "Paris Saint Germain": "巴黎聖日耳門", "PSG": "巴黎聖日耳門",
    "Newcastle United": "紐卡素", "Bournemouth": "般尼茅夫",
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
    """只抓有機會有大細水嘅賽事"""
    try:
        r = requests.get(
            "https://api.odds-api.io/v3/events",
            params={
                "apiKey": ODDS_API_KEY,
                "sport": "football",
                "limit": 15,
                "status": "pending"
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
        print("Events 錯誤:", r.status_code, r.text[:200])
    except Exception as e:
        print("抓賽事失敗:", e)
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
    """更強嘅 2.5 大細提取"""
    if not odds_data or "bookmakers" not in odds_data:
        return None, None, None

    best_over = None
    best_under = None
    best_book = None

    for bookie, markets in odds_data.get("bookmakers", {}).items():
        for market in markets:
            name = str(market.get("name", "")).lower()
            if "total" in name or "over" in name or "under" in name or "goals" in name:
                for odd in market.get("odds", []):
                    # 嘗試多種欄位名
                    line = odd.get("hdp") or odd.get("max") or odd.get("point") or odd.get("total") or odd.get("line")
                    try:
                        if line is not None and abs(float(line) - 2.5) < 0.05:
                            over = float(odd.get("over", 0) or 0)
                            under = float(odd.get("under", 0) or 0)
                            if over > 1.01 and under > 1.01:
                                # 優先保留較高水
                                if best_over is None or over > best_over:
                                    best_over = over
                                    best_under = under
                                    best_book = bookie
                    except:
                        continue
    return best_over, best_under, best_book

def main():
    print("=== 阿晴真實版分析開始 ===")
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    message = f"""⚽ <b>阿晴 Value 分析報告</b>
時間: {now}

"""
    
    events = get_events()
    message += f"✅ 抓到 <b>{len(events)}</b> 場待賽賽事\n\n"
    
    analyzed = 0
    value_count = 0
    
    for event in events[:8]:  # 限制數量避免超過免費額度
        home = event.get("home", "Home")
        away = event.get("away", "Away")
        event_id = event.get("id")
        league = ""
        if isinstance(event.get("league"), dict):
            league = event["league"].get("name", "")
        
        home_cn = to_cn(home)
        away_cn = to_cn(away)
        
        # 暫時仍然用固定 expected（下一步會改真實）
        expected = 2.55
        
        over_p, under_p = calc_poisson(expected)
        
        odds_data = get_odds(event_id) if event_id else None
        over_odds, under_odds, book = extract_ou_25(odds_data) if odds_data else (None, None, None)
        
        message += f"📌 <b>{home_cn} vs {away_cn}</b>\n"
        if league:
            message += f"聯賽: {league}\n"
        message += f"預期總入: {expected:.2f}\n"
        
        if over_odds and under_odds:
            over_ev = calc_ev(over_p, over_odds)
            under_ev = calc_ev(under_p, under_odds)
            
            message += f"大球 {over_p*100:.1f}% | {over_odds:.2f} ({book}) | EV {over_ev:+.1f}\n"
            message += f"小球 {under_p*100:.1f}% | {under_odds:.2f} ({book}) | EV {under_ev:+.1f}\n"
            
            if over_ev > 5 or under_ev > 5:
                message += "🔥 有 Value！\n"
                value_count += 1
            analyzed += 1
        else:
            message += "暫無 2.5 真實大細水\n"
        
        message += "\n"
    
    message += f"成功分析真實賠率: {analyzed} 場\n"
    message += f"發現潛在 Value: {value_count} 場\n"
    message += "（下一步會加入真實 Expected Goals）\n"
    message += "阿晴繼續優化中 ♡"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
