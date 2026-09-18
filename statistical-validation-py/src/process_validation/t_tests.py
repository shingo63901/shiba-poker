"""三種 t 檢定：成對、等變異、不等變異（Welch）。"""
from __future__ import annotations

import numpy as np
from scipy import stats

from .f_test import _describe
from .result import TestResult, conclude, fmt_p


def _t_result(
    name: str,
    x1: np.ndarray,
    x2: np.ndarray,
    t: float,
    df: float,
    alpha: float,
    tail: str,
    delta0: float,
    extra: dict,
    sig_text: str,
    ns_text: str,
    df_display: str | None = None,
    describe: bool = True,
) -> TestResult:
    """t 檢定共同的報表組裝：單/雙尾 p、臨界值、結論。"""
    p_one = 1 - stats.t.cdf(abs(t), df)  # 依觀察方向的單尾
    p_two = min(2 * p_one, 1.0)
    p = p_one if tail == "one" else p_two
    details = dict(extra)
    details.update(
        {
            "P(T<=t) 單尾": fmt_p(p_one),
            "臨界值：單尾": stats.t.ppf(1 - alpha, df),
            "P(T<=t) 雙尾": fmt_p(p_two),
            "臨界值：雙尾": stats.t.ppf(1 - alpha / 2, df),
        }
    )
    warnings = []
    if tail == "one":
        warnings.append("單尾 p 值以觀察到的差異方向計算；單尾方向應在收資料前決定。")
    return TestResult(
        name=name,
        stat_symbol="t",
        statistic=t,
        df=df_display or f"{df:g}",
        p_value=p,
        alpha=alpha,
        tail=tail,
        hypothesis=(f"μ₁−μ₂ = {delta0:g}", f"μ₁−μ₂ {'>' if tail == 'one' else '≠'} {delta0:g}"),
        details=details,
        tables={"敘述統計": _describe({"變數1": x1, "變數2": x2})} if describe else {},
        conclusion=conclude(p, alpha, sig_text, ns_text),
        warnings=warnings,
    )


def t_test_paired(sample1, sample2, alpha: float = 0.05, mu0: float = 0.0, tail: str = "two") -> TestResult:
    """成對 t 檢定（對應 Excel「t 檢定：成對母體平均數差異檢定」）。

    什麼情形下使用？
        「同一批對象」改善前後各量測一次、資料一一配對：同 10 台設備調機前後、
        同一批樣品前後量測。可扣除個體差異，檢定力通常高於獨立兩樣本 t 檢定。

    如何使用？
        兩欄資料逐筆配對、筆數相同。對差值 d = x₁−x₂ 做單樣本 t 檢定：
        t = (d̄−μ₀) / (s_d/√n)，df = n−1。H₀: μ_d = μ₀（通常 0）。

    前提假設：
        差值近似常態（n ≥ 30 可放寬）；配對必須真實存在，
        兩批不同產品應改用獨立兩樣本 t 檢定。

    Args:
        sample1: 改善前（與 sample2 逐筆配對）。
        sample2: 改善後。
        alpha: 顯著水準。
        mu0: H₀ 假設的平均差（預設 0）。
        tail: "two" 雙尾；"one" 單尾（依觀察方向）。
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    if len(x1) != len(x2):
        raise ValueError(f"成對檢定需筆數相同（目前 {len(x1)} vs {len(x2)}）")
    if len(x1) < 2:
        raise ValueError("至少需要 2 對資料")

    d = x1 - x2
    n = len(d)
    md, sd = d.mean(), d.std(ddof=1)
    t = (md - mu0) / (sd / np.sqrt(n))
    r = float(np.corrcoef(x1, x2)[0, 1])

    return _t_result(
        "t 檢定：成對母體平均數差異檢定",
        x1, x2, t, n - 1, alpha, tail, mu0,
        extra={"皮爾森相關係數": r, "平均差 d̄": md, "差的標準差 s_d": sd, "假設的均數差": mu0},
        sig_text=f"改善前後平均有顯著差異（平均差 {md:g}，{'變數1 較大' if md > 0 else '變數2 較大'}）。",
        ns_text=f"尚無足夠證據說改善前後平均不同（平均差 {md:g} 可能只是隨機波動）。",
    )


def t_test_equal_var(sample1, sample2, alpha: float = 0.05, delta0: float = 0.0, tail: str = "two") -> TestResult:
    """兩獨立樣本 t 檢定—假設變異數相等（對應 Excel 同名項目）。

    什麼情形下使用？
        改善前抽一批、改善後另抽一批（非同一對象），且 F 檢定顯示
        兩組變異數無顯著差異。

    如何使用？
        合併變異數 s_p² = [(n₁−1)s₁²+(n₂−1)s₂²]/(n₁+n₂−2)，
        t = (x̄₁−x̄₂−Δ₀)/√(s_p²(1/n₁+1/n₂))，df = n₁+n₂−2。

    前提假設：
        兩組獨立、近似常態、變異數相等。不確定變異數是否相等時，
        直接用 t_test_welch 較穩健。

    Args:
        delta0: H₀ 假設的均數差 Δ₀，可設非 0（驗證「至少改善某幅度」）。
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("兩組各至少需要 2 筆資料")

    n1, n2 = len(x1), len(x2)
    v1, v2 = x1.var(ddof=1), x2.var(ddof=1)
    sp2 = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
    t = (x1.mean() - x2.mean() - delta0) / np.sqrt(sp2 * (1 / n1 + 1 / n2))

    diff = x1.mean() - x2.mean()
    return _t_result(
        "t 檢定：兩個母體平均數差的檢定（假設變異數相等）",
        x1, x2, t, n1 + n2 - 2, alpha, tail, delta0,
        extra={"Pooled 變異數 s_p²": sp2, "假設的均數差 Δ₀": delta0},
        sig_text=f"兩組平均值有顯著差異（x̄₁−x̄₂ = {diff:g}）。",
        ns_text="尚無足夠證據說兩組平均不同。",
    )


def t_test_welch(sample1, sample2, alpha: float = 0.05, delta0: float = 0.0, tail: str = "two") -> TestResult:
    """兩獨立樣本 t 檢定—假設變異數不相等，Welch（對應 Excel 同名項目）。

    什麼情形下使用？
        F 檢定顯示兩組變異數不同（製程改善常同時改變平均與變異）；
        或兩組樣本數差距大、不確定變異數是否相等時的安全預設——
        即使變異數其實相等，Welch 的結論也幾乎不受影響。

    如何使用？
        t = (x̄₁−x̄₂−Δ₀)/√(s₁²/n₁+s₂²/n₂)，自由度以 Welch–Satterthwaite
        公式估計（非整數；Excel 會四捨五入為整數，兩者 p 值差異極小）。

    前提假設：
        兩組獨立、母體近似常態；不要求變異數相等。
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("兩組各至少需要 2 筆資料")

    n1, n2 = len(x1), len(x2)
    v1, v2 = x1.var(ddof=1), x2.var(ddof=1)
    se2 = v1 / n1 + v2 / n2
    t = (x1.mean() - x2.mean() - delta0) / np.sqrt(se2)
    df = se2**2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))

    diff = x1.mean() - x2.mean()
    return _t_result(
        "t 檢定：兩個母體平均數差的檢定（假設變異數不相等）",
        x1, x2, t, df, alpha, tail, delta0,
        extra={"Welch 自由度（精確）": df, "Excel 取整自由度": round(df), "假設的均數差 Δ₀": delta0},
        sig_text=f"兩組平均值有顯著差異（x̄₁−x̄₂ = {diff:g}）。",
        ns_text="尚無足夠證據說兩組平均不同。",
        df_display=f"{df:.4f}",
    )
