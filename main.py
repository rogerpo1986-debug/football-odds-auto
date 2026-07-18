import os
import requests
from datetime import datetime, timezone, timedelta
from scipy.stats import poisson
from collections import defaultdict

THE_ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SPORTS = [
    "soccer_japan_j_league",
    "soccer_korea_kleague1",
    "soccer_brazil_campeonato",
    "soccer_sweden_allsvenskan",
    "soccer_usa_mls",
    "soccer_australia_a_league",   # 澳洲A聯賽
    "soccer_a_league",             # 另一種寫法
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga",
    "soccer_finland_veikkausliiga",
    "soccer_argentina_primera_division",
    "soccer_mexico_ligamx",
    "soccer_efl_champ",
    "soccer_russia_premier_league",
    "soccer_uruguay_primera_division",
    "soccer_scotland_premiership",
    "soccer_brazil_serie_b",
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
    "Inter Miami CF": "邁阿密國際",
    "Chicago Fire": "芝加哥火焰",
    "San Jose Earthquakes": "聖荷西地震",
    "Orlando City SC": "奧蘭多城",
    "FC Cincinnati": "辛辛那提",
    "Vancouver Whitecaps FC": "溫哥華白帽",
    "Bahia": "巴伊亞",
    "Chapecoense": "沙佩科恩塞",
    "Viking FK": "維京",
    "Sandefjord": "桑德菲jord",
    "Monterrey": "蒙特雷",
    "Santos Laguna": "桑托斯拉古納",
    "FC Copenhagen": "哥本哈根",
    "Lyngby": "林比",
    "Bodo/Glimt": "博德閃耀",
    "Fredrikstad FK": "腓特烈斯塔",
    "HamKam": "漢坎",
}

LEAGUE_CN = {
    "K League 1": "韓國K聯賽",
    "J1 League": "日本J1",
    "Brazil Serie A": "巴西甲組",
    "Allsvenskan": "瑞典超",
    "MLS": "美國大聯盟",
    "A-League": "澳洲A聯賽",
    "Eliteserien": "挪威超",
    "Superliga": "丹麥超",
    "Veikkausliiga": "芬蘭聯賽",
    "Primera División": "阿根廷甲",
    "Liga MX": "墨西哥聯賽",
    "Championship": "英冠",
    "Russia Premier League": "俄羅斯超",
    "Uruguay Primera Division": "烏拉圭甲組",
    "Scotland Premiership": "蘇格蘭超",
    "Brazil Serie B": "巴西乙組",
}

LEAGUE_EXPECTED = {
    "K League 1": 2.60,
    "J1 League": 2.50,
    "Brazil Serie A": 2.75,
    "Allsvenskan": 2.70,
    "MLS": 2.85,
    "A-League": 2.65,
    "Eliteserien": 2.70,
    "Superliga": 2.65,
    "Veikkausliiga": 2.55,
    "Primera División": 2.40,
    "Liga MX": 2.60,
    "Championship": 2.55,
    "Russia Premier League": 2.60,
    "Uruguay Primera Division": 2.45,
    "Scotland Premiership": 2.80,
    "Brazil Serie B": 2.40,
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
            return []
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
    for key, value in LEAGUE_EXPECTED.items():
        if key.lower() in sport_title.lower():
            return value
    return 2.55

def get_league_cn(sport_title):
    for key, value in LEAGUE_CN.items():
        if key.lower() in sport_title.lower():
            return value
    return sport_title

def main():
    print("=== 多聯賽版 ===")
    now = datetime.now(timezone.utc)
    now_hk = now.astimezone(timezone(timedelta(hours=8)))
    message = f"⚽ 阿晴 Value 精選報告（未來2天）\n時間: {now_hk.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    max_time = now + timedelta(hours=48)
    
    all_matches = []
    for sport in SPORTS:
        data = get_odds_for_sport(sport)
        if data:
            all_matches.extend(data)
    
    league_dict = defaultdict(list)
    
    for match in all_matches:
        commence = match.get("commence_time", "")
        if not commence:
            continue
        
        try:
            match_time = datetime.fromisoformat(commence.replace("Z", "+00:00"))
            if match_time > max_time or match_time < now:
                continue
        except:
            continue
        
        home_en = match.get("home_team", "Home")
        away_en = match.get("away_team", "Away")
        home = TEAM_CN.get(home_en, home_en)
        away = TEAM_CN.get(away_en, away_en)
        sport_title = match.get("sport_title", "")
        league_cn = get_league_cn(sport_title)
        
        hk_time = match_time.astimezone(timezone(timedelta(hours=8)))
        time_str = hk_time.strftime("%m-%d %H:%M")
        
        expected = get_expected(sport_title)
        over_p, under_p = calc_poisson(expected)
        over_odds, under_odds, book = extract_ou_25(match.get("bookmakers", []))
        
        if not over_odds or not under_odds:
            continue
        
        over_ev = calc_ev(over_p, over_odds)
        under_ev = calc_ev(under_p, under_odds)
        
        max_ev = max(over_ev, under_ev)
        if max_ev < 3:
            continue
        
        league_dict[league_cn].append({
            "home": home,
            "away": away,
            "time": time_str,
            "expected": expected,
            "over_p": over_p,
            "under_p": under_p,
            "over_odds": over_odds,
            "under_odds": under_odds,
            "over_ev": over_ev,
            "under_ev": under_ev,
            "max_ev": max_ev
        })
    
    total_value = sum(len(v) for v in league_dict.values())
    message += f"✅ 未來2天內發現 {total_value} 場有 Value（EV ≥ +3）\n\n"
    
    if not league_dict:
        message += "而家暫時冇發現有 Value 嘅場次\n"
    else:
        for league, matches in league_dict.items():
            matches.sort(key=lambda x: x["max_ev"], reverse=True)
            top_matches = matches[:3]
            
            message += f"【{league}】共 {len(matches)} 場\n"
            
            for item in top_matches:
                message += f"📌 {item['home']} vs {item['away']}\n"
                message += f"時間: {item['time']} (HKT)\n"
                message += f"預期: {item['expected']:.2f} | 大 {item['over_odds']} (EV{item['over_ev']:+.1f}) | 細 {item['under_odds']} (EV{item['under_ev']:+.1f})\n"
                if item['over_ev'] >= 3:
                    message += "🔥 大球\n"
                if item['under_ev'] >= 3:
                    message += "🔥 小球\n"
                message += "\n"
            
            message += "────────\n"
    
    message += "阿晴精選報告完"
    
    print(message)
    send_telegram(message)
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
