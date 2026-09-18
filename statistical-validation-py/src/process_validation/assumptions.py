"""前提假設檢查：常態性（Shapiro-Wilk）與變異數同質（Levene）。

t 檢定 / F 檢定 / ANOVA 都假設母體近似常態；F 檢定與等變異 t 檢定
另外假設變異數同質。跑正式檢定前先用本模組檢查，違反時換用穩健方法。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def check_normality(samples: dict, alpha: float = 0.05) -> pd.DataFrame:
    """Shapiro-Wilk 常態性檢定（每組各做一次）。

    H₀: 資料來自常態分布。p < α → 顯著偏離常態。
    n < 3 無法檢定；n ≥ 30 時即使輕微偏離，t 檢定/ANOVA 通常仍穩健。

    Args:
        samples: 組名 → 數列。
        alpha: 顯著水準。

    Returns:
        DataFrame：每組的 W 統計量、p 值與判定。
    """
    rows = []
    for name, x in samples.items():
        x = np.asarray(x, dtype=float)
        if len(x) < 3:
            rows.append({"組別": name, "n": len(x), "W": np.nan, "p 值": np.nan, "判定": "樣本數不足"})
            continue
        w, p = stats.shapiro(x)
        rows.append({
            "組別": name, "n": len(x), "W": w, "p 值": p,
            "判定": "近似常態 ✓" if p >= alpha else "偏離常態 ⚠（考慮資料轉換或無母數檢定）",
        })
    return pd.DataFrame(rows).set_index("組別")


def check_equal_variance(samples: dict, alpha: float = 0.05) -> pd.DataFrame:
    """Levene 變異數同質檢定（以中位數為中心，對非常態穩健）。

    H₀: 各組變異數相等。p < α → 變異數不同質：
    兩組比較改用 Welch t 檢定；ANOVA 考慮 Welch ANOVA 或資料轉換。
    比 F 檢定更適合當「前提檢查」用（F 檢定對非常態敏感）。

    Args:
        samples: 組名 → 數列（2 組以上）。
        alpha: 顯著水準。

    Returns:
        單列 DataFrame：Levene 統計量、p 值與判定。
    """
    groups = [np.asarray(x, dtype=float) for x in samples.values()]
    if len(groups) < 2:
        raise ValueError("至少需要 2 組資料")
    stat, p = stats.levene(*groups, center="median")
    return pd.DataFrame(
        [{
            "統計量": stat, "p 值": p,
            "判定": "變異數同質 ✓（可用等變異 t / 一般 ANOVA）" if p >= alpha
            else "變異數不同質 ⚠（兩組改用 Welch t；多組考慮 Welch ANOVA）",
        }],
        index=["Levene 檢定"],
    )
