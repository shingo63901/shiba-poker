"""F 檢定：兩個常態母體變異數的檢定。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import TestResult, conclude, fmt, fmt_p


def _describe(samples: dict[str, np.ndarray]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            name: {
                "平均數": x.mean(),
                "變異數": x.var(ddof=1),
                "標準差": x.std(ddof=1),
                "觀察值個數": len(x),
            }
            for name, x in samples.items()
        }
    )


def f_test(sample1, sample2, alpha: float = 0.05, tail: str = "two") -> TestResult:
    """F 檢定：兩個常態母體變異數的檢定（對應 Excel 同名項目）。

    什麼情形下使用？
        - 驗證改善後製程的「變異（穩定度）」是否縮小——Cpk 提升往往來自變異縮小。
        - 兩獨立樣本 t 檢定前的前置判斷：變異數相等 → 等變異 t；不等 → Welch t。

    如何使用？
        改善前後各收集一組獨立樣本，統計量 F = s₁²/s₂²（df₁ = n₁−1、df₂ = n₂−1）。
        H₀: σ₁² = σ₂²。p < α → 變異數顯著不同。

    前提假設：
        兩組獨立、母體近似常態。F 檢定對非常態敏感，偏態資料建議改用
        Levene 檢定（見 assumptions.check_equal_variance）。

    Args:
        sample1: 第一組樣本（例：改善前）。
        sample2: 第二組樣本（例：改善後）。
        alpha: 顯著水準。
        tail: "two" 檢驗變異數是否不同；"one" 檢驗 σ₁² > σ₂²
            （單尾方向須在收資料前決定）。
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("兩組各至少需要 2 筆資料")

    v1, v2 = x1.var(ddof=1), x2.var(ddof=1)
    df1, df2 = len(x1) - 1, len(x2) - 1
    F = v1 / v2
    cdf = stats.f.cdf(F, df1, df2)
    p_one_obs = (1 - cdf) if F >= 1 else cdf  # Excel 報表的單尾 p（依觀察方向）
    p_two = min(2 * p_one_obs, 1.0)
    p = (1 - cdf) if tail == "one" else p_two

    crit_right = stats.f.ppf(1 - alpha, df1, df2)
    crit_lo = stats.f.ppf(alpha / 2, df1, df2)
    crit_hi = stats.f.ppf(1 - alpha / 2, df1, df2)

    sig = (
        f"兩組變異數有顯著差異（{'變數1 變異較大' if v1 > v2 else '變數2 變異較大'}）。"
        "若變數1=改善前且 s₁²>s₂²，代表改善後製程更穩定；"
        "後續獨立樣本 t 檢定請用「不等變異（Welch）」版本。"
    )
    ns = "尚無足夠證據說兩組變異數不同；後續獨立樣本 t 檢定可用「等變異」版本。"

    return TestResult(
        name="F 檢定：兩個常態母體變異數的檢定",
        stat_symbol="F",
        statistic=F,
        df=f"df₁={df1}, df₂={df2}",
        p_value=p,
        alpha=alpha,
        tail=tail,
        hypothesis=("σ₁² = σ₂²", "σ₁² > σ₂²" if tail == "one" else "σ₁² ≠ σ₂²"),
        details={
            "P(F<=f) 單尾（Excel 報表值）": fmt_p(p_one_obs),
            "P 值（雙尾：變異數是否不同）": fmt_p(p_two),
            "臨界值 單尾右 F(α)": crit_right,
            "臨界值 雙尾區間": f"[{fmt(crit_lo)}, {fmt(crit_hi)}]",
        },
        tables={"敘述統計": _describe({"變數1": x1, "變數2": x2})},
        conclusion=conclude(p, alpha, sig, ns),
    )
