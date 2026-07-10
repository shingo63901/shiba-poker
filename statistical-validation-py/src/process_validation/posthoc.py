"""事後多重比較：Tukey HSD。

ANOVA 只回答「是否至少一組不同」；顯著之後用 Tukey HSD 找出
「是哪幾組之間不同」，且整體型一錯誤率仍控制在 α。
Excel 資料分析工具箱沒有這個功能。
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from scipy import stats


def tukey_hsd(groups: dict, alpha: float = 0.05) -> pd.DataFrame:
    """Tukey HSD 兩兩比較（單因子 ANOVA 顯著後使用）。

    Args:
        groups: 組名 → 數列（與 anova_oneway 相同的輸入）。
        alpha: 家族錯誤率（整體型一錯誤率）。

    Returns:
        DataFrame：每一對組合的平均差、信賴區間、p 值與是否顯著。
        信賴區間不含 0（p < α）代表該兩組平均有顯著差異。
    """
    names = list(groups.keys())
    data = [np.asarray(groups[n], dtype=float) for n in names]
    if len(data) < 2:
        raise ValueError("至少需要 2 組資料")

    res = stats.tukey_hsd(*data)
    ci = res.confidence_interval(confidence_level=1 - alpha)

    rows = []
    for i, j in itertools.combinations(range(len(names)), 2):
        p = res.pvalue[i, j]
        rows.append({
            "比較": f"{names[i]} − {names[j]}",
            "平均差": data[i].mean() - data[j].mean(),
            f"CI 下限({1 - alpha:.0%})": ci.low[i, j],
            f"CI 上限({1 - alpha:.0%})": ci.high[i, j],
            "p 值": p,
            "顯著": "✅" if p < alpha else "—",
        })
    return pd.DataFrame(rows).set_index("比較")
