"""問答式檢定選擇指引（對應 HTML 版首頁的流程圖）。"""
from __future__ import annotations


def _ask(question: str, options: dict[str, str]) -> str:
    print(f"\n{question}")
    for key, text in options.items():
        print(f"  [{key}] {text}")
    while True:
        ans = input("請輸入選項: ").strip()
        if ans in options:
            return ans
        print(f"請輸入 {'/'.join(options)} 其中之一")


def run_advisor() -> str:
    """互動式引導：回答幾個問題，告訴你該用哪個檢定與對應指令。

    Returns:
        建議的檢定名稱。
    """
    print("═" * 50)
    print("  檢定選擇指引：驗證製程改善的有效性")
    print("═" * 50)

    q1 = _ask(
        "Q1. 你的資料型態？",
        {"1": "連續數值（尺寸、良率、時間、強度…）",
         "2": "類別計數（缺陷類型件數、良/不良品數…）"},
    )
    if q1 == "2":
        q = _ask(
            "Q2. 你想檢驗什麼？",
            {"1": "一組類別計數是否符合期望分布（如缺陷組成是否改變）",
             "2": "兩個類別變數是否相關（如改善前後 × 良/不良、缺陷 × 班別）"},
        )
        rec = ("卡方適合度檢定", "pv chi-gof") if q == "1" else ("卡方獨立性檢定", "pv chi-ind")
    else:
        q2 = _ask(
            "Q2. 你想比較「平均值」還是「變異（穩定度）」？",
            {"1": "變異（改善後是否更穩定）", "2": "平均值"},
        )
        if q2 == "1":
            rec = ("F 檢定（兩個常態母體變異數）", "pv f")
        else:
            q3 = _ask(
                "Q3. 要比較幾組？",
                {"1": "兩組：同一批對象改善前後各量一次（成對）",
                 "2": "兩組：改善前後各抽一批（獨立樣本）",
                 "3": "三組以上（多水準/多機台/多供應商）",
                 "4": "同時考慮兩個因子（如溫度 × 壓力）"},
            )
            if q3 == "1":
                rec = ("成對 t 檢定", "pv t-paired")
            elif q3 == "2":
                q4 = _ask(
                    "Q4. 兩組變異數是否相等？（可先跑 pv f 檢定確認）",
                    {"1": "相等（F 檢定不顯著）", "2": "不相等或不確定"},
                )
                rec = (("等變異 t 檢定", "pv t-equal") if q4 == "1"
                       else ("不等變異 t 檢定（Welch）", "pv t-welch"))
            elif q3 == "3":
                rec = ("單因子 ANOVA（顯著後接 Tukey HSD 事後比較）", "pv anova1")
            else:
                rec = ("雙因子 ANOVA（每組合重複多次可檢定交互作用）", "pv anova2")

    print("\n" + "═" * 50)
    print(f"👉 建議使用：{rec[0]}")
    print(f"   指令範例：{rec[1]} --help（或 pv demo 看範例輸出）")
    print("═" * 50)
    return rec[0]
