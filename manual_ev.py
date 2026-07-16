import os
from scipy.stats import poisson

def calc_poisson(expected, line=2.5):
    over = 1 - poisson.cdf(int(line), expected)
    under = poisson.cdf(int(line), expected)
    return over, under

def calc_ev(prob, odds):
    if odds <= 1:
        return -100
    return round((prob * (odds - 1) - (1 - prob)) * 100, 1)

def main():
    print("=" * 50)
    print("阿晴 手動 EV 計算器（HKJC 水專用）")
    print("=" * 50)
    
    home = input("主隊名稱（中文或英文）: ").strip()
    away = input("客隊名稱: ").strip()
    
    try:
        expected = float(input("預期總入球（例如 2.6，唔知就輸入 2.55）: ") or 2.55)
        line = float(input("大細線（通常 2.5）: ") or 2.5)
        over_odds = float(input("HKJC 大球賠率: "))
        under_odds = float(input("HKJC 小球賠率: "))
    except:
        print("輸入有誤，請重新運行")
        return
    
    over_p, under_p = calc_poisson(expected, line)
    over_ev = calc_ev(over_p, over_odds)
    under_ev = calc_ev(under_p, under_odds)
    
    print("\n" + "=" * 50)
    print(f"對賽：{home} vs {away}")
    print(f"預期總入球：{expected}")
    print(f"大細線：{line}")
    print("-" * 50)
    print(f"大球概率：{over_p*100:.1f}%")
    print(f"HKJC 大球水：{over_odds}  →  EV = {over_ev:+.1f}")
    print()
    print(f"小球概率：{under_p*100:.1f}%")
    print(f"HKJC 小球水：{under_odds} →  EV = {under_ev:+.1f}")
    print("=" * 50)
    
    if over_ev > 3:
        print("→ 大球有 value，可以考慮")
    elif under_ev > 3:
        print("→ 小球有 value，可以考慮")
    else:
        print("→ 兩邊 EV 都唔高，謹慎")

if __name__ == "__main__":
    main()
