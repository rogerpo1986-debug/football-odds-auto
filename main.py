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

# 中文隊名
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

# 聯賽預期總入球（之後可再細分）
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
            return r.json()
        else:
            print(f"錯誤: {r.text[:200]}")
    except Exception as e:
        print(f"抓 {sport_key} 失敗:", e)
    return []

def extract_ou_25(bookmakers):
    best_over = None
    best_under = None
    best_book = None

    for book in bookmakers:
        book_name = book.get("title", book.get("key", ""))
        for market in book.get("markets", []):
            if market.get("key") == "totals":
                for outcome in market.get("outcomes", []):
                    point = outcome.get("point")
                    if point is not None and abs(float(point) - 2.5) < 0.05:
                        name = outcome.get("name", "").lower()
                        price = float(outcome.get("price", 0))
                        if name == "over" and price > 1.01:
                            if best_over is None or price > best_over:
                                best_over = price
                                best_book = book_name
                        elif name == "under" and price > 1.01:
                            if best_under is None or price > best_under:
                                best_under = price
                                best_book = book_name
    return best_over, best_under, best_book

def get_expected(sport_title):
    """根據聯賽名稱攞預期總入球"""
    for key, value in LEAGUE_EXPECTED.items():
        if key.lower() in sport_title.lower():
            return value
    return 2.55  # 預設

def main():
    print("=== The Odds API 分析開始 ===")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = f"⚽ 阿晴 Value 分析報告 (The Odds API)\n時間: {now}\n\n"
    
    all_matches = []
    
    for sport in SPORTS:
        data = get_odds_for_sport(sport)
        if data:
            all_matches.extend(data)
    
    message += f"✅ 總共抓到 {len(all_matches)} 場有大細水嘅賽事\n\n"
    
    analyzed = 0
    value_count = 0
    
    for match in all_matches[:10]:
        home_en = match.get("home_team", "Home")
        away_en = match.get("away_team", "Away")
        home = TEAM_CN.get(home_en, home_en)
        away = TEAM_CN.get(away_en, away_en)
        sport_title = match.get("sport_title", "")
        
        commence = match.get("commence_time", "")
        time_str = ""
        if commence:
            try:
                dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                hk_time = dt.astimezone(timezone(timedelta(hours=8)))
                time_str = hk_time.strftime("%m-%d %H:%M")
            except:
                time_str = commence[:16]
        
        # 真實一點嘅預期入球
        expected = get_expected(sport_title)
        
        over_p, under_p = calc_poisson(expected)
        
        over_odds, under_odds, book = extract_ou_25(match.get("bookmakers", []))
        
        message += f"📌 {home} vs {away}\n"
        if time_str:
            message += f"時間: {time_str} (HKT)\n"
        if sport_title:
            message += f"聯賽: {sport_title}\n"
        message += f"預期總入: {expected:.2f}\n"
        
        if over_odds and under_odds:
            over_ev = calc_ev(over_p, over_odds)
            under_ev = calc_ev(under_p, under_odds)
            
            message += f"大球 {round(over_p*100,1)}% | {over_odds} ({book}) | EV {over_ev:+.1f}\n"
            message += f"小球 {round(under_p*100,1)}% | {under_odds} ({book}) | EV {under_ev:+.1f}\n"
            
            if over_ev > 5 or under_ev > 5:
                message += "🔥 有 Value！\n"
                value_count += 1
            analyzed += 1
        else:
            message += "暫無 2.5 真實大細水\n"
        
        message += "\n"
    
    message += f"成功分析真實賠率: {analyzed} 場\n"
    message += f"發現潛在 Value: {value_count} 場\n"
    message += "阿晴繼續優化中"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
