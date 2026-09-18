"""卡方檢定：適合度（goodness of fit）與獨立性（列聯表）。

Excel 的「資料分析」工具箱沒有卡方項目，需使用 CHISQ.TEST 函數；
本模組直接輸出統計量、自由度、p 值與期望次數表。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import TestResult, conclude

_MIN_EXPECTED = 5.0


def _low_expected_warning(expected: np.ndarray) -> list[str]:
    if (expected < _MIN_EXPECTED).any():
        return [
            f"有期望次數 < {_MIN_EXPECTED:g} 的格子（最小 {expected.min():.2f}），"
            "卡方近似可能不準確；建議合併類別，或改用 Fisher 精確檢定。"
        ]
    return []


def chi_square_gof(observed, expected, alpha: float = 0.05, rescale: bool = True) -> TestResult:
    """卡方適合度檢定：類別計數的分布是否符合期望分布。

    什麼情形下使用？
        資料是「類別的計數」：改善後各缺陷類型的件數分布是否改變？
        是否仍符合歷史比例？

    如何使用？
        χ² = Σ(O−E)²/E，df = k−1。永遠是右尾檢定。
        p < α → 觀察分布與期望分布顯著不同。

    前提假設：
        各觀察值獨立、輸入為「次數」；每格期望次數建議 ≥ 5（不足時自動警示）。

    Args:
        observed: 觀察次數 O。
        expected: 期望次數 E；也可輸入比例（rescale=True 時會依觀察總數等比換算）。
        alpha: 顯著水準。
        rescale: 期望總數與觀察總數不同時，是否自動等比換算。
    """
    O = np.asarray(observed, dtype=float)
    E = np.asarray(expected, dtype=float)
    if len(O) < 2:
        raise ValueError("至少需要 2 個類別")
    if len(O) != len(E):
        raise ValueError(f"觀察與期望的類別數必須相同（目前 {len(O)} vs {len(E)}）")
    if (E <= 0).any():
        raise ValueError("期望次數必須為正值")

    scaled = False
    if rescale and not np.isclose(O.sum(), E.sum()):
        E = E * O.sum() / E.sum()
        scaled = True

    chi2 = float(((O - E) ** 2 / E).sum())
    df = len(O) - 1
    p = float(stats.chi2.sf(chi2, df))

    table = pd.DataFrame({"觀察次數 O": O, "期望次數 E": E, "(O−E)²/E": (O - E) ** 2 / E})
    table.index = [f"類別{i + 1}" for i in range(len(O))]

    res = TestResult(
        name="卡方適合度檢定",
        stat_symbol="χ²",
        statistic=chi2,
        df=str(df),
        p_value=p,
        alpha=alpha,
        tail="right",
        hypothesis=("觀察分布 = 期望分布", "觀察分布 ≠ 期望分布"),
        details={"P 值（右尾）": p, "臨界值 χ²(α)": stats.chi2.ppf(1 - alpha, df)},
        tables={"觀察與期望次數": table},
        conclusion=conclude(p, alpha, "觀察分布與期望分布顯著不同（分布已改變）。",
                            "尚無足夠證據說分布不符合期望。"),
        warnings=_low_expected_warning(E),
    )
    if scaled:
        res.warnings.append("期望值總數與觀察值不同，已依觀察總數等比換算。")
    return res


def chi_square_independence(table, alpha: float = 0.05) -> TestResult:
    """卡方獨立性檢定：兩個類別變數是否相關（列聯表）。

    什麼情形下使用？
        缺陷類型是否與班別/機台有關？「改善前後 × 良/不良」的 2×2 表
        正是改善前後不良率比較的標準做法。

    如何使用？
        期望次數 E = 列合計 × 行合計 ÷ 總計（自動計算），
        χ² = Σ(O−E)²/E，df = (列數−1)(行數−1)。p < α → 兩變數不獨立（有關聯）。

    前提假設：
        各觀察值獨立、輸入為「次數」；每格期望次數建議 ≥ 5。

    Args:
        table: 列聯表。可為 DataFrame（列/行名沿用）或 2D 陣列。
        alpha: 顯著水準。
    """
    if isinstance(table, pd.DataFrame):
        obs = table.astype(float)
    else:
        arr = np.asarray(table, dtype=float)
        obs = pd.DataFrame(
            arr,
            index=[f"列{i + 1}" for i in range(arr.shape[0])],
            columns=[f"行{j + 1}" for j in range(arr.shape[1])],
        )
    if obs.shape[0] < 2 or obs.shape[1] < 2:
        raise ValueError("列聯表至少需要 2 列 × 2 行")

    O = obs.to_numpy()
    row_sum = O.sum(axis=1, keepdims=True)
    col_sum = O.sum(axis=0, keepdims=True)
    N = O.sum()
    E = row_sum @ col_sum / N

    chi2 = float(((O - E) ** 2 / E).sum())
    df = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    p = float(stats.chi2.sf(chi2, df))

    expected = pd.DataFrame(E, index=obs.index, columns=obs.columns)

    return TestResult(
        name="卡方獨立性檢定（列聯表）",
        stat_symbol="χ²",
        statistic=chi2,
        df=str(df),
        p_value=p,
        alpha=alpha,
        tail="right",
        hypothesis=("兩變數獨立（無關聯）", "兩變數不獨立（有關聯）"),
        details={
            "總次數 N": N,
            "P 值（右尾）": p,
            "臨界值 χ²(α)": stats.chi2.ppf(1 - alpha, df),
        },
        tables={"觀察次數": obs, "期望次數": expected.round(2)},
        conclusion=conclude(
            p, alpha,
            "兩個類別變數不獨立（有關聯）。若列為改善前/後、行為良/不良，"
            "代表改善前後的不良率有顯著差異。",
            "尚無足夠證據說兩變數有關聯。",
        ),
        warnings=_low_expected_warning(E),
    )
