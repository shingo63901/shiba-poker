"""變異數分析：單因子、雙因子（無重複／重複試驗）。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import TestResult, conclude, fmt_p


def _anova_row(source: str, ss: float, df: int, ms_error: float, df_error: int, alpha: float) -> dict:
    ms = ss / df
    F = ms / ms_error
    p = float(stats.f.sf(F, df, df_error))
    return {
        "變源": source, "SS": ss, "df": df, "MS": ms,
        "F": F, "P 值": p, "臨界值": stats.f.ppf(1 - alpha, df, df_error),
    }


def anova_oneway(groups, alpha: float = 0.05) -> TestResult:
    """單因子變異數分析（對應 Excel「單因子變異數分析」）。

    什麼情形下使用？
        比較三組以上平均：三種製程參數水準、多台機、多家供應商。
        不可用多次 t 檢定取代——兩兩比較會使整體型一錯誤率膨脹（3 組約 14%）。

    如何使用？
        F = MS組間/MS組內；H₀: 各組平均全相等。p < α → 至少一組不同，
        接著用 posthoc.tukey_hsd 找出是哪幾組。

    前提假設：
        各組獨立、常態、變異數同質（可用 assumptions 模組檢查）。
        兩組時與等變異 t 檢定等價（F = t²）。

    Args:
        groups: dict（組名 → 數列）或數列的 list。各組樣本數可不同，每組至少 2 筆。
        alpha: 顯著水準。
    """
    if not isinstance(groups, dict):
        groups = {f"第{i + 1}組": g for i, g in enumerate(groups)}
    data = {name: np.asarray(g, dtype=float) for name, g in groups.items()}
    if len(data) < 2:
        raise ValueError("至少需要 2 組資料")
    if any(len(g) < 2 for g in data.values()):
        raise ValueError("每組至少需要 2 筆資料")

    all_values = np.concatenate(list(data.values()))
    N, k = len(all_values), len(data)
    gm = all_values.mean()
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in data.values())
    ssw = sum(((g - g.mean()) ** 2).sum() for g in data.values())
    dfb, dfw = k - 1, N - k

    row = _anova_row("組間", ssb, dfb, ssw / dfw, dfw, alpha)
    table = pd.DataFrame(
        [
            row,
            {"變源": "組內", "SS": ssw, "df": dfw, "MS": ssw / dfw},
            {"變源": "總和", "SS": ssb + ssw, "df": N - 1},
        ]
    ).set_index("變源")

    desc = pd.DataFrame(
        {name: {"平均數": g.mean(), "變異數": g.var(ddof=1), "觀察值個數": len(g)} for name, g in data.items()}
    )
    p = row["P 值"]

    return TestResult(
        name="單因子變異數分析（One-Way ANOVA）",
        stat_symbol="F",
        statistic=row["F"],
        df=f"df₁={dfb}, df₂={dfw}",
        p_value=p,
        alpha=alpha,
        tail="right",
        hypothesis=("各組平均全相等", "至少一組平均不同"),
        details={"P 值": p, "臨界值 F(α)": row["臨界值"]},
        tables={"敘述統計": desc, "ANOVA 表": table},
        conclusion=conclude(
            p, alpha,
            "各組平均不全相等——因子有顯著影響。請比較各組平均找出最佳水準，"
            "並以事後檢定（posthoc.tukey_hsd）確認哪幾組間有差異。",
            "尚無足夠證據說各組平均有差異。",
        ),
    )


def anova_twoway(data, alpha: float = 0.05,
                 factor_a: str = "A", factor_b: str = "B", value: str = "y") -> TestResult:
    """雙因子變異數分析（對應 Excel「雙因子變異數分析：無重複試驗／重複試驗」）。

    什麼情形下使用？
        同時評估兩個因子（溫度×壓力、操作員×機台）對品質特性的影響。
        - 每組合 1 筆 → 無重複試驗：只能檢定主效果（隨機集區設計）。
        - 每組合 r ≥ 2 筆（平衡）→ 重複試驗：可額外檢定「交互作用」，
          是製程窗口優化的關鍵資訊。依資料自動判斷。

    如何使用？
        以長格式輸入（每筆觀測一列：因子A水準、因子B水準、數值）。
        判讀順序（重複試驗）：先看交互作用——顯著時主效果不能單獨解讀，
        應直接比較「各組合平均」選最佳組合。

    前提假設：
        各觀測獨立、誤差常態且變異數同質；重複試驗需平衡設計（每格次數相同）。
        無重複試驗隱含「無交互作用」假設。

    Args:
        data: 長格式資料。DataFrame（欄名由 factor_a/factor_b/value 指定），
            或 (a, b, y) tuple 的 list。
        alpha: 顯著水準。
        factor_a: 因子 A 的欄名。
        factor_b: 因子 B 的欄名。
        value: 數值欄名。
    """
    if isinstance(data, pd.DataFrame):
        df_long = data[[factor_a, factor_b, value]].copy()
    else:
        df_long = pd.DataFrame(data, columns=[factor_a, factor_b, value])
    df_long[value] = df_long[value].astype(float)

    counts = df_long.groupby([factor_a, factor_b], sort=False)[value].count()
    A = df_long[factor_a].unique()
    B = df_long[factor_b].unique()
    ra, cb = len(A), len(B)
    if ra < 2 or cb < 2:
        raise ValueError("因子 A 與因子 B 各至少需要 2 個水準")
    if len(counts) != ra * cb:
        raise ValueError("有因子組合缺少資料，請補齊所有 A×B 組合")
    if counts.nunique() != 1:
        raise ValueError(f"每個組合的重複次數必須相同（平衡設計），目前為 {sorted(counts.unique())}")

    rep = int(counts.iloc[0])
    N = len(df_long)
    y = df_long[value].to_numpy()
    gm = y.mean()
    a_mean = df_long.groupby(factor_a, sort=False)[value].mean()
    b_mean = df_long.groupby(factor_b, sort=False)[value].mean()
    ss_a = cb * rep * ((a_mean - gm) ** 2).sum()
    ss_b = ra * rep * ((b_mean - gm) ** 2).sum()
    ss_t = ((y - gm) ** 2).sum()

    cell_mean = df_long.groupby([factor_a, factor_b], sort=False)[value].mean()
    pivot = cell_mean.unstack().reindex(index=A, columns=B)

    if rep == 1:  # 無重複試驗
        ss_e = ss_t - ss_a - ss_b
        df_e = (ra - 1) * (cb - 1)
        ms_e = ss_e / df_e
        rows = [
            _anova_row(f"因子 A（{factor_a}）", ss_a, ra - 1, ms_e, df_e, alpha),
            _anova_row(f"因子 B（{factor_b}）", ss_b, cb - 1, ms_e, df_e, alpha),
            {"變源": "誤差", "SS": ss_e, "df": df_e, "MS": ms_e},
        ]
        mode = "無重複試驗"
        p_map = {"因子 A": rows[0]["P 值"], "因子 B": rows[1]["P 值"]}
    else:  # 重複試驗
        ss_cell = rep * ((cell_mean - gm) ** 2).sum()
        ss_ab = ss_cell - ss_a - ss_b
        ss_e = ss_t - ss_cell
        df_e = ra * cb * (rep - 1)
        ms_e = ss_e / df_e
        rows = [
            _anova_row(f"因子 A（{factor_a}）", ss_a, ra - 1, ms_e, df_e, alpha),
            _anova_row(f"因子 B（{factor_b}）", ss_b, cb - 1, ms_e, df_e, alpha),
            _anova_row("交互作用 A×B", ss_ab, (ra - 1) * (cb - 1), ms_e, df_e, alpha),
            {"變源": "誤差（組內）", "SS": ss_e, "df": df_e, "MS": ms_e},
        ]
        mode = f"重複試驗（每組合 {rep} 筆）"
        p_map = {"因子 A": rows[0]["P 值"], "因子 B": rows[1]["P 值"], "交互作用 A×B": rows[2]["P 值"]}

    rows.append({"變源": "總和", "SS": ss_t, "df": N - 1})
    table = pd.DataFrame(rows).set_index("變源")

    p_min = min(p_map.values())
    sig_items = [k for k, v in p_map.items() if v < alpha]
    if sig_items:
        def _ptxt(v: float) -> str:
            s = fmt_p(v)
            return f"p {s}" if s.startswith("<") else f"p = {s}"

        text = f"顯著項目：{'、'.join(f'{k}（{_ptxt(p_map[k])}）' for k in sig_items)}。"
        if "交互作用 A×B" in sig_items:
            text += ("交互作用顯著 → 兩因子效果互相牽動，主效果不能單獨解讀，"
                     "請直接比較「各組合平均」表，選擇最佳的參數組合。")
        elif rep > 1:
            text += "交互作用不顯著 → 可分別解讀 A、B 主效果，依各水準平均選擇最佳條件。"
        else:
            text += "顯著的因子對品質特性有真實影響，請依水準平均值選擇最佳條件。"
    else:
        text = ""
    ns_text = "各項皆不顯著，尚無證據顯示這兩個因子影響量測值。"

    stat_row = rows[0]
    return TestResult(
        name=f"雙因子變異數分析：{mode}",
        stat_symbol="F",
        statistic=stat_row["F"],
        df=f"df誤差={df_e}",
        p_value=p_min,
        alpha=alpha,
        tail="right",
        hypothesis=("各因子（與交互作用）無效果", "至少一項有效果"),
        details={f"{k} 的 P 值": v for k, v in p_map.items()},
        tables={"各組合平均": pivot, "ANOVA 表": table},
        conclusion=conclude(p_min, alpha, text or "有顯著項目。", ns_text),
        warnings=[] if rep > 1 else ["無重複試驗無法估計交互作用；若懷疑有交互作用，請安排重複量測。"],
    )
