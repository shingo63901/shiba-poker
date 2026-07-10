"""檢定結果的統一容器與報表輸出。

所有檢定函數都回傳 :class:`TestResult`，內容比照 Excel「資料分析」報表：
敘述統計、統計量、自由度、單尾/雙尾 p 值、臨界值，外加白話結論與前提警示。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


def fmt(x, dp: int | None = None) -> str:
    """數值格式化：極端值用科學記號，其餘保留 6 位有效數字。"""
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    if dp is not None:
        return f"{x:.{dp}f}"
    ax = abs(x)
    if ax != 0 and (ax < 1e-3 or ax >= 1e6):
        return f"{x:.4e}"
    return f"{float(f'{x:.6g}'):g}"


def fmt_p(p) -> str:
    if p is None:
        return "—"
    p = min(max(p, 0.0), 1.0)
    return "< 0.0001" if p < 1e-4 else f"{p:.4f}"


def conclude(p: float, alpha: float, sig_text: str, ns_text: str) -> str:
    ptxt = fmt_p(p)
    ptxt = f"p {ptxt}" if ptxt.startswith("<") else f"p = {ptxt}"
    if p < alpha:
        return f"✅ 拒絕 H₀（{ptxt} < α = {alpha}）→ {sig_text}"
    return f"⬜ 無法拒絕 H₀（{ptxt} ≥ α = {alpha}）→ {ns_text}"


@dataclass
class TestResult:
    """單一檢定的完整結果。

    Attributes:
        name: 檢定名稱（對應 Excel 資料分析項目名）。
        stat_symbol: 統計量符號（t、F、χ²）。
        statistic: 檢定統計量數值。
        df: 自由度（呈現用字串，如 "9" 或 "df₁=2, df₂=12"）。
        p_value: 用於下結論的 p 值（依 tail 選定單尾或雙尾）。
        alpha: 顯著水準。
        tail: "two"（雙尾）、"one"（單尾）或 "right"（卡方/ANOVA 固定右尾）。
        hypothesis: (H₀, H₁) 敘述。
        details: 報表明細列（label → 數值或字串），比照 Excel 輸出欄位。
        tables: 附表（敘述統計、ANOVA 表、期望次數…），值為 DataFrame。
        conclusion: 白話結論。
        warnings: 前提假設或資料品質警示。
    """

    name: str
    stat_symbol: str
    statistic: float
    df: str
    p_value: float
    alpha: float
    tail: str = "two"
    hypothesis: tuple[str, str] = ("", "")
    details: dict = field(default_factory=dict)
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    conclusion: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def significant(self) -> bool:
        """p 值是否小於 α（差異顯著）。"""
        return self.p_value < self.alpha

    def __str__(self) -> str:
        bar = "═" * 58
        lines = [bar, f"  {self.name}", bar]
        if self.hypothesis[0]:
            lines.append(f"H₀: {self.hypothesis[0]}    H₁: {self.hypothesis[1]}    α = {self.alpha}")
        for title, table in self.tables.items():
            lines += ["", f"[{title}]", table.to_string()]
        lines.append("")
        lines.append(f"{self.stat_symbol} 統計量 = {fmt(self.statistic)}    自由度 = {self.df}")
        for k, v in self.details.items():
            lines.append(f"{k}: {fmt(v)}")
        lines += ["", f"結論: {self.conclusion}"]
        for w in self.warnings:
            lines.append(f"⚠ {w}")
        lines.append(bar)
        return "\n".join(lines)

    def summary_frame(self) -> pd.DataFrame:
        """把報表明細整理成單欄 DataFrame（供 Excel 輸出）。"""
        rows: list[tuple[str, str]] = [
            ("檢定", self.name),
            ("H₀", self.hypothesis[0]),
            ("H₁", self.hypothesis[1]),
            ("α", str(self.alpha)),
            (f"{self.stat_symbol} 統計量", fmt(self.statistic)),
            ("自由度", self.df),
        ]
        rows += [(k, fmt(v)) for k, v in self.details.items()]
        rows.append(("結論", self.conclusion))
        for i, w in enumerate(self.warnings, 1):
            rows.append((f"警示 {i}", w))
        return pd.DataFrame(rows, columns=["項目", "值"])

    def to_excel(self, path: str) -> None:
        """輸出 Excel 報告：摘要一張工作表，各附表各一張。"""
        with pd.ExcelWriter(path, engine="openpyxl") as xw:
            self.summary_frame().to_excel(xw, sheet_name="檢定摘要", index=False)
            for title, table in self.tables.items():
                # Excel 工作表名稱長度上限 31、不可含特殊字元
                sheet = title.translate(str.maketrans("", "", "[]:*?/\\"))[:31]
                table.to_excel(xw, sheet_name=sheet)
